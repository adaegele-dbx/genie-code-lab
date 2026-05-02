# Databricks notebook source

# MAGIC %md
# MAGIC # Genie Code Lab — Data Setup
# MAGIC
# MAGIC Generates four tables in `<catalog>.genie_code_lab` for the Hands-On with
# MAGIC Genie Code lab.  The scenario: you're on the energy operations team of a
# MAGIC single industrial company that owns 10 sites across the US.
# MAGIC
# MAGIC | Table | Rows | Role |
# MAGIC |-------|------|------|
# MAGIC | `regions` | 5 | Dimension — US regions with timezones |
# MAGIC | `business_units` | 5 | Dimension — internal business units |
# MAGIC | `sites` | 10 | Fact-ish — physical sites (FK to regions and business_units) |
# MAGIC | `meter_readings` | ~29k | Fact — 15-minute interval readings over the last 30 days |
# MAGIC
# MAGIC Run this cell once before starting the lab.  It is also called from
# MAGIC `lab_notebook.py` via `%run`.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Catalog Name")
catalog = dbutils.widgets.get("catalog")
schema = "genie_code_lab"
print(f"Using catalog: {catalog}, schema: {schema}")

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
print(f"Schema {catalog}.{schema} is ready.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Regions Table (5 rows)

# COMMAND ----------

import random
from datetime import date, datetime, timedelta, timezone
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType,
    DateType, TimestampType,
)

regions = [
    {"region_id": "R-NE", "region_name": "Northeast", "timezone": "America/New_York"},
    {"region_id": "R-SE", "region_name": "Southeast", "timezone": "America/New_York"},
    {"region_id": "R-MW", "region_name": "Midwest",   "timezone": "America/Chicago"},
    {"region_id": "R-W",  "region_name": "West",      "timezone": "America/Los_Angeles"},
    {"region_id": "R-SW", "region_name": "Southwest", "timezone": "America/Phoenix"},
]

regions_schema = StructType([
    StructField("region_id", StringType()),
    StructField("region_name", StringType()),
    StructField("timezone", StringType()),
])

df_regions = spark.createDataFrame(regions, schema=regions_schema)
df_regions.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{catalog}.{schema}.regions")
print(f"regions: {df_regions.count()} rows written.")

spark.sql(f"COMMENT ON TABLE {catalog}.{schema}.regions IS 'Dimension table of US operating regions. Each site rolls up to exactly one region. Use the timezone column to convert UTC reading_timestamp values to local time when reporting.'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.regions ALTER COLUMN region_id COMMENT 'Region primary key (e.g. R-NE)'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.regions ALTER COLUMN region_name COMMENT 'Human-readable region name: Northeast, Southeast, Midwest, West, or Southwest'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.regions ALTER COLUMN timezone COMMENT 'IANA timezone for the region — used to localize UTC reading timestamps'")
print("regions: descriptions added.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Business Units Table (5 rows)

# COMMAND ----------

business_units = [
    {"business_unit_id": "BU-MFG", "business_unit_name": "Manufacturing",
     "description": "Production facilities — factories and assembly plants."},
    {"business_unit_id": "BU-LOG", "business_unit_name": "Logistics & Distribution",
     "description": "Warehouses and distribution centers."},
    {"business_unit_id": "BU-COR", "business_unit_name": "Corporate & Office",
     "description": "Corporate headquarters and office buildings."},
    {"business_unit_id": "BU-RND", "business_unit_name": "R&D / Data Centers",
     "description": "Research labs, engineering campuses, and on-prem data centers."},
    {"business_unit_id": "BU-RTL", "business_unit_name": "Retail Operations",
     "description": "Customer-facing retail flagship locations."},
]

bu_schema = StructType([
    StructField("business_unit_id", StringType()),
    StructField("business_unit_name", StringType()),
    StructField("description", StringType()),
])

df_bus = spark.createDataFrame(business_units, schema=bu_schema)
df_bus.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{catalog}.{schema}.business_units")
print(f"business_units: {df_bus.count()} rows written.")

spark.sql(f"COMMENT ON TABLE {catalog}.{schema}.business_units IS 'Dimension table of internal business units. Every site reports up to one business unit. Useful for grouping consumption analysis by line of business.'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.business_units ALTER COLUMN business_unit_id COMMENT 'Business unit primary key (e.g. BU-MFG)'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.business_units ALTER COLUMN business_unit_name COMMENT 'Human-readable BU name'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.business_units ALTER COLUMN description COMMENT 'One-line description of the kinds of sites that belong to this BU'")
print("business_units: descriptions added.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Sites Table (10 rows)
# MAGIC
# MAGIC Ten sites spread across all 5 regions and all 5 business units.  Mix of
# MAGIC site types (factory, warehouse, office, data_center, retail) so analytical
# MAGIC questions about consumption by site_type are interesting.

# COMMAND ----------

# Hand-picked site list — descriptive names, no company branding.
# Each row: site_id, site_name, site_type, business_unit_id, region_id, city, state, sq_ft, voltage
site_specs = [
    ("SITE-0001", "Boston Manufacturing Plant",     "factory",     "BU-MFG", "R-NE", "Boston",       "MA", 220_000, 480),
    ("SITE-0002", "Atlanta Distribution Center",    "warehouse",   "BU-LOG", "R-SE", "Atlanta",      "GA", 180_000, 480),
    ("SITE-0003", "Chicago Headquarters",           "office",      "BU-COR", "R-MW", "Chicago",      "IL",  90_000, 480),
    ("SITE-0004", "Seattle R&D Campus",             "data_center", "BU-RND", "R-W",  "Seattle",      "WA", 110_000, 480),
    ("SITE-0005", "Phoenix Solar Operations Hub",   "factory",     "BU-MFG", "R-SW", "Phoenix",      "AZ", 250_000, 480),
    ("SITE-0006", "Dallas Distribution Center",     "warehouse",   "BU-LOG", "R-SW", "Dallas",       "TX", 160_000, 480),
    ("SITE-0007", "Portland Retail Flagship",       "retail",      "BU-RTL", "R-W",  "Portland",     "OR",  18_000, 480),
    ("SITE-0008", "Charlotte Office Complex",       "office",      "BU-COR", "R-SE", "Charlotte",    "NC",  60_000, 480),
    ("SITE-0009", "Indianapolis Assembly Plant",    "factory",     "BU-MFG", "R-MW", "Indianapolis", "IN", 300_000, 480),
    ("SITE-0010", "New Jersey Data Center",         "data_center", "BU-RND", "R-NE", "Newark",       "NJ",  80_000, 480),
]

random.seed(43)
sites = []
for site_id, site_name, site_type, bu_id, region_id, city, state, sq_ft, voltage in site_specs:
    install = date.today() - timedelta(days=random.randint(180, 1800))
    sites.append({
        "site_id":           site_id,
        "site_name":         site_name,
        "site_type":         site_type,
        "business_unit_id":  bu_id,
        "region_id":         region_id,
        "city":              city,
        "state":             state,
        "square_footage":    sq_ft,
        "installation_date": install,
        "voltage_nominal":   voltage,
    })

sites_schema = StructType([
    StructField("site_id", StringType()),
    StructField("site_name", StringType()),
    StructField("site_type", StringType()),
    StructField("business_unit_id", StringType()),
    StructField("region_id", StringType()),
    StructField("city", StringType()),
    StructField("state", StringType()),
    StructField("square_footage", IntegerType()),
    StructField("installation_date", DateType()),
    StructField("voltage_nominal", IntegerType()),
])

df_sites = spark.createDataFrame(sites, schema=sites_schema)
df_sites.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{catalog}.{schema}.sites")
print(f"sites: {df_sites.count()} rows written.")

spark.sql(f"COMMENT ON TABLE {catalog}.{schema}.sites IS 'Physical locations operated by the company, each with one installed energy meter. A site rolls up to exactly one business unit and one region. Site type drives expected load profile (factories and data centers consume far more than offices or retail).'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.sites ALTER COLUMN site_id COMMENT 'Site primary key (e.g. SITE-0001)'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.sites ALTER COLUMN site_name COMMENT 'Descriptive site name (city + role)'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.sites ALTER COLUMN site_type COMMENT 'Physical category: factory, warehouse, office, data_center, or retail'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.sites ALTER COLUMN business_unit_id COMMENT 'Foreign key to business_units'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.sites ALTER COLUMN region_id COMMENT 'Foreign key to regions'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.sites ALTER COLUMN city COMMENT 'City the site is located in'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.sites ALTER COLUMN state COMMENT 'Two-letter US state code'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.sites ALTER COLUMN square_footage COMMENT 'Built area in square feet — useful for normalizing consumption (kWh per sq ft)'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.sites ALTER COLUMN installation_date COMMENT 'Date the meter was commissioned at this site'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.sites ALTER COLUMN voltage_nominal COMMENT 'Nominal service voltage at this site'")
print("sites: descriptions added.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Meter Readings Table (~29k rows)
# MAGIC
# MAGIC 30 days × 96 fifteen-minute intervals × 10 sites.  Patterns built in:
# MAGIC - **Hourly seasonality** — 1.5× load during business hours, 0.5× overnight
# MAGIC - **2 anomalous sites** with multi-day spikes — gives Part 3a's anomaly flag something real to find
# MAGIC - **~5% warning / ~1% error status** rows scattered across sites

# COMMAND ----------

random.seed(44)

# Pick 2 anomalous sites deterministically
anomalous_site_ids = {"SITE-0005", "SITE-0010"}  # Phoenix factory, NJ data center
anomaly_windows = {}
for sid in anomalous_site_ids:
    days_ago_start = random.randint(2, 14)
    duration_days = random.randint(1, 3)
    anomaly_windows[sid] = (days_ago_start, days_ago_start - duration_days)
print(f"Anomalous sites: {sorted(anomalous_site_ids)}  windows={anomaly_windows}")

# 30 days of 15-min intervals ending at the most recent quarter-hour
end_dt = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
window_days = 30
n_intervals = window_days * 96  # 96 fifteen-minute intervals per day
timestamps = [end_dt - timedelta(minutes=15 * i) for i in range(n_intervals - 1, -1, -1)]
print(f"Generating readings from {timestamps[0]} to {timestamps[-1]}  ({n_intervals} intervals)")

# Type-level base ranges (kWh per 15-min)
base_kwh_by_type = {
    "office":       (8, 25),
    "retail":       (6, 18),
    "warehouse":    (12, 40),
    "factory":      (25, 80),
    "data_center":  (40, 120),
}

readings = []
reading_id = 1
for s in sites:
    sid = s["site_id"]
    stype = s["site_type"]
    voltage = s["voltage_nominal"]
    lo, hi = base_kwh_by_type[stype]
    site_anomaly = anomaly_windows.get(sid)

    for ts in timestamps:
        hour = ts.hour
        if 9 <= hour < 18:
            season = 1.5
        elif hour >= 22 or hour < 6:
            season = 0.5
        else:
            season = 1.0

        base = random.uniform(lo, hi) * season

        days_ago = (end_dt - ts).days
        anomaly_mult = 1.0
        if site_anomaly is not None:
            start_days, end_days = site_anomaly
            if end_days <= days_ago <= start_days:
                anomaly_mult = random.uniform(3.0, 6.0)

        kwh = round(base * anomaly_mult, 3)
        kw_demand = round(kwh * random.uniform(3.0, 5.0), 3)
        v = round(voltage * random.uniform(0.98, 1.02), 2)
        temp = round(22 + random.uniform(-7, 12), 2)

        roll = random.random()
        if roll < 0.01:
            status = "error"
        elif roll < 0.05:
            status = "warning"
        else:
            status = "normal"

        readings.append({
            "reading_id":        f"R-{reading_id:08d}",
            "site_id":           sid,
            "reading_timestamp": ts,
            "kwh_consumed":      kwh,
            "kw_demand":         kw_demand,
            "voltage":           v,
            "temperature_c":     temp,
            "status":            status,
        })
        reading_id += 1

readings_schema = StructType([
    StructField("reading_id", StringType()),
    StructField("site_id", StringType()),
    StructField("reading_timestamp", TimestampType()),
    StructField("kwh_consumed", DoubleType()),
    StructField("kw_demand", DoubleType()),
    StructField("voltage", DoubleType()),
    StructField("temperature_c", DoubleType()),
    StructField("status", StringType()),
])

df_readings = spark.createDataFrame(readings, schema=readings_schema)
df_readings.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{catalog}.{schema}.meter_readings")
print(f"meter_readings: {df_readings.count()} rows written.")

spark.sql(f"COMMENT ON TABLE {catalog}.{schema}.meter_readings IS 'Raw 15-minute interval meter readings from all sites over the last ~30 days. Each reading captures consumption, peak demand, voltage, ambient temperature, and meter status. This is the source-of-truth fact table for energy analysis.'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.meter_readings ALTER COLUMN reading_id COMMENT 'Unique reading identifier'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.meter_readings ALTER COLUMN site_id COMMENT 'Foreign key to sites'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.meter_readings ALTER COLUMN reading_timestamp COMMENT 'UTC timestamp at the start of the 15-minute interval'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.meter_readings ALTER COLUMN kwh_consumed COMMENT 'Energy consumed during this 15-minute interval, in kilowatt-hours'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.meter_readings ALTER COLUMN kw_demand COMMENT 'Peak instantaneous power draw observed within the interval, in kilowatts'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.meter_readings ALTER COLUMN voltage COMMENT 'Average service voltage observed during the interval'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.meter_readings ALTER COLUMN temperature_c COMMENT 'Ambient temperature in degrees Celsius at the meter'")
spark.sql(f"ALTER TABLE {catalog}.{schema}.meter_readings ALTER COLUMN status COMMENT 'Meter health status for the interval: normal, warning, or error'")
print("meter_readings: descriptions added.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification — Sample Data from Each Table

# COMMAND ----------

for table in ["regions", "business_units", "sites", "meter_readings"]:
    print(f"\n--- {catalog}.{schema}.{table} ---")
    display(spark.table(f"{catalog}.{schema}.{table}").limit(5))
    count = spark.table(f"{catalog}.{schema}.{table}").count()
    print(f"Total rows: {count}")
