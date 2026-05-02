"""Energy anomaly viewer — reference Databricks App for Part 3c of the Genie Code lab.

Lists rows from `workspace.genie_code_lab.daily_site_consumption` where
`anomaly_flag = true`, with a sidebar date-range filter and a daily anomaly
count chart.

This file is a known-good fallback.  Attendees should first try to have
Genie Code generate it; only fall back to this file if their generated
app won't deploy.
"""

import os
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from databricks import sql
from databricks.sdk.core import Config

CATALOG = "workspace"
SCHEMA = "genie_code_lab"


# ---------- connection ----------

cfg = Config()


def _server_hostname() -> str:
    host = cfg.host or ""
    return host.removeprefix("https://").removeprefix("http://")


def get_connection():
    warehouse_id = os.environ["DATABRICKS_WAREHOUSE_ID"]
    return sql.connect(
        server_hostname=_server_hostname(),
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        credentials_provider=lambda: cfg.authenticate,
        _use_arrow_native_complex_types=False,
    )


@st.cache_data(ttl=60)
def query_df(query: str) -> pd.DataFrame:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall_arrow().to_pandas()


# ---------- UI ----------

st.set_page_config(page_title="Energy Anomalies", layout="wide")
st.title("Energy Anomaly Viewer")
st.caption(f"Source: `{CATALOG}.{SCHEMA}.daily_site_consumption`")

with st.sidebar:
    st.header("Filters")
    today = date.today()
    default_start = today - timedelta(days=14)
    date_range = st.date_input("Date range", value=(default_start, today))
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, today

    site_types = query_df(
        f"SELECT DISTINCT site_type FROM {CATALOG}.{SCHEMA}.daily_site_consumption ORDER BY 1"
    )["site_type"].tolist()
    selected_types = st.multiselect("Site type", options=site_types, default=site_types)

# Build filter clauses
type_clause = ""
if selected_types:
    quoted = ", ".join(f"'{t}'" for t in selected_types)
    type_clause = f"AND d.site_type IN ({quoted})"

anomalies_query = f"""
SELECT d.reading_date,
       d.site_id,
       s.site_name,
       d.site_type,
       d.business_unit_name,
       d.region_name,
       s.city,
       s.state,
       d.total_kwh,
       d.peak_kw,
       d.deviation_pct,
       d.warning_count
FROM   {CATALOG}.{SCHEMA}.daily_site_consumption d
JOIN   {CATALOG}.{SCHEMA}.sites s USING (site_id)
WHERE  d.anomaly_flag = TRUE
  AND  d.reading_date BETWEEN '{start_date}' AND '{end_date}'
  {type_clause}
ORDER BY d.reading_date DESC, d.deviation_pct DESC
"""

anomalies_df = query_df(anomalies_query)

# ---------- top-line metrics ----------
col1, col2, col3 = st.columns(3)
col1.metric("Anomalies in range", len(anomalies_df))
col2.metric("Distinct sites flagged", anomalies_df["site_id"].nunique() if not anomalies_df.empty else 0)
col3.metric(
    "Highest deviation",
    f"{anomalies_df['deviation_pct'].max():.0f}%" if not anomalies_df.empty else "—",
)

# ---------- daily count chart ----------
if not anomalies_df.empty:
    daily_counts = (
        anomalies_df.groupby("reading_date").size().reset_index(name="anomaly_count")
    )
    st.subheader("Anomalies per day")
    st.bar_chart(daily_counts.set_index("reading_date")["anomaly_count"])

# ---------- table ----------
st.subheader("Anomaly details")
if anomalies_df.empty:
    st.info("No anomalies in the selected range. Widen the date range or check that the pipeline has run.")
else:
    st.dataframe(anomalies_df, use_container_width=True, hide_index=True)
