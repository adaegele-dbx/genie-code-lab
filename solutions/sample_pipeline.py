# Reference Lakeflow Spark Declarative Pipeline — energy meter ETL
#
# This is the *known-good fallback* for Part 3a of the lab.  Attendees should
# first try to have Genie Code generate this pipeline themselves; this file is
# only here in case the agent's output won't run.
#
# Pipeline shape:
#   meter_readings (raw)  ──>  silver_readings  ──┐
#                                                 ├──>  daily_site_consumption  (gold)
#       sites + regions + business_units          ──┘
#
# Target schema: workspace.genie_code_lab
# Source tables: workspace.genie_code_lab.{meter_readings, sites, regions, business_units}

import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window

CATALOG = "workspace"
SCHEMA = "genie_code_lab"


@dlt.table(
    name="silver_readings",
    comment="Cleaned 15-minute meter readings: error rows dropped, joined with site, region, and business unit metadata.",
)
@dlt.expect_or_drop("non_negative_kwh", "kwh_consumed >= 0")
@dlt.expect("voltage_in_range", "voltage BETWEEN 100 AND 600")
def silver_readings():
    readings = spark.table(f"{CATALOG}.{SCHEMA}.meter_readings")
    sites = spark.table(f"{CATALOG}.{SCHEMA}.sites")
    regions = spark.table(f"{CATALOG}.{SCHEMA}.regions")
    business_units = spark.table(f"{CATALOG}.{SCHEMA}.business_units")

    site_dim = (
        sites
        .join(regions, on="region_id", how="left")
        .join(business_units, on="business_unit_id", how="left")
        .select(
            "site_id",
            "site_type",
            "business_unit_id",
            "business_unit_name",
            "region_id",
            "region_name",
            "voltage_nominal",
            "square_footage",
        )
    )

    return (
        readings
        .filter(F.col("status") != "error")
        .join(site_dim, on="site_id", how="left")
        .withColumn("reading_date", F.to_date("reading_timestamp"))
    )


@dlt.table(
    name="daily_site_consumption",
    comment="Per-site daily energy summary with a 2σ anomaly flag computed over each site's 30-day history. Includes business unit and region for grouping analysis.",
)
def daily_site_consumption():
    silver = dlt.read("silver_readings")

    daily = (
        silver
        .groupBy("site_id", "site_type", "business_unit_id", "business_unit_name",
                 "region_id", "region_name", "reading_date")
        .agg(
            F.round(F.sum("kwh_consumed"), 2).alias("total_kwh"),
            F.round(F.max("kw_demand"), 2).alias("peak_kw"),
            F.round(F.avg("voltage"), 2).alias("avg_voltage"),
            F.sum(F.when(F.col("status") == "warning", 1).otherwise(0)).alias("warning_count"),
        )
    )

    site_window = Window.partitionBy("site_id")
    enriched = (
        daily
        .withColumn("site_mean_kwh", F.avg("total_kwh").over(site_window))
        .withColumn("site_stddev_kwh", F.stddev_pop("total_kwh").over(site_window))
        .withColumn(
            "anomaly_flag",
            F.when(
                F.col("total_kwh") > F.col("site_mean_kwh") + 2 * F.col("site_stddev_kwh"),
                F.lit(True),
            ).otherwise(F.lit(False)),
        )
        .withColumn(
            "deviation_pct",
            F.round(
                (F.col("total_kwh") - F.col("site_mean_kwh")) / F.col("site_mean_kwh") * 100,
                1,
            ),
        )
    )

    return enriched.select(
        "site_id",
        "site_type",
        "business_unit_id",
        "business_unit_name",
        "region_id",
        "region_name",
        "reading_date",
        "total_kwh",
        "peak_kw",
        "avg_voltage",
        "warning_count",
        "site_mean_kwh",
        "site_stddev_kwh",
        "deviation_pct",
        "anomaly_flag",
    )
