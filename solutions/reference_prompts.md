# Reference Prompts

All the prompts the lab suggests, collected in one place for easy copy-paste
during the session. Section numbers match `lab_notebook.py`.

---

## Setup
> Confirm Agent mode is on. Type a quick prompt to test:
>
> *"What tables are available in workspace.genie_code_lab?"*

## Part 1 — Genie Code 101

Chat (with the lab notebook attached as context):
> *"What is this notebook for?"*

`@table` reference (in the chat panel):
> *"How many rows are in `@meter_readings` and what's the date range?"*

Inline (`Cmd+I` / `Ctrl+I`) in an empty cell:
> *"Show the schema of all four tables in workspace.genie_code_lab as one combined SQL output."*

Slash commands:
> Type `/` to see the menu. Try:
> - `/findTables energy consumption`
> - `/explain` on the SQL cell from above
> - `/findQueries top consumers`

Autocomplete:
> Start typing
> ```python
> df = spark.table("workspace.genie_code_lab.
> ```
> and press `Tab` to accept the inline suggestion.

## Part 2 — Agent-mode EDA

> *"Perform exploratory data analysis on `@meter_readings`. Join in
> `@sites`, `@regions`, and `@business_units` as needed. Summarize the
> most interesting patterns and anomalies as a markdown report at the end."*

## Part 3a — Build the SDP pipeline

> *"In a new file at `pipeline/energy_pipeline.py`, write a Lakeflow
> Spark Declarative Pipeline that:
>
>   1. Reads `@meter_readings` as a silver table, dropping rows where
>      `status = 'error'`.
>   2. Joins to `@sites`, `@regions`, and `@business_units` for site,
>      region, and business unit metadata.
>   3. Produces a daily per-site gold table called
>      `daily_site_consumption` with columns: site_id, site_type,
>      business_unit_id, business_unit_name, region_id, region_name,
>      reading_date, total_kwh, peak_kw, avg_voltage, warning_count.
>   4. Adds an `anomaly_flag` column that is `true` when the day's
>      total_kwh is more than 2 standard deviations above that site's
>      30-day mean.
>
> Use `dlt` decorators and PySpark. Target catalog `workspace`, schema
> `genie_code_lab`."*

Stretch:
> *"Add a `@dlt.expect_or_drop` data quality expectation that drops rows
> where `kwh_consumed` is negative."*

## Part 3b — Genie space

Description seed:
> *"Suggest a one-paragraph description for a Genie space over
> `@daily_site_consumption` focused on energy-anomaly investigation.
> Mention the meaning of the `anomaly_flag` column and that the table
> already carries `business_unit_name` and `region_name` for grouping."*

Test questions:
> 1. *"Which business unit had the most anomalies last week?"*
> 2. *"Show me the top 5 sites by total kWh in the past 14 days."*
> 3. *"For SITE-XXXX, what's the daily kWh trend?"*  (substitute an
>    actual flagged site_id from your data)

## Part 3c — Streamlit app

> *"Replace the contents of `app.py` with a Streamlit page that queries
> `workspace.genie_code_lab.daily_site_consumption` for rows where
> `anomaly_flag = true`. Add a sidebar date-range filter and a sortable
> table that includes site_name, site_type, business_unit_name, and
> region_name. Use the databricks-sql-connector with on-behalf-of-user
> auth via `databricks.sdk.core.Config`. Read `DATABRICKS_WAREHOUSE_ID`
> from the environment."*

Stretch:
> *"Add a bar chart above the table showing the count of anomalies per
> day in the selected date range."*

## Part 4 — Improve what you built

On the pipeline file:
> Use `/optimize` on the daily aggregation function.
> Use `/doc` to add a docstring to the silver_readings table.
> Then chat:
> *"Make the daily_site_consumption table incremental — only reprocess
> the last 7 days, not the full window. Use a streaming source and
> AutoCDC if appropriate."*

## Part 5 — Custom instructions

Baseline (run this first, before adding instructions):
> *"Write a small PySpark function that returns the top N sites by total
> kWh for a given month, grouped by business unit. Use
> `@daily_site_consumption`."*

After pasting `solutions/sample_assistant_instructions.md` into your
`.assistant_instructions.md` file, run the **same** prompt again and
diff the outputs.

## Part 6 — Custom skill

Trigger by intent (no `@`-mention):
> *"Investigate yesterday's energy anomalies and tell me what to look at."*

Genie Code should pick up the `anomaly-triage` skill automatically and
follow the steps. Look for the "Used skill: anomaly-triage" indicator
in the trace.

If it doesn't trigger, force it:
> *"Use the @anomaly-triage skill on the last 3 days of anomalies."*
