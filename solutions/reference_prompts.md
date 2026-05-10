# Reference Prompts

All the prompts the lab suggests, collected in one place for easy copy-paste
during the session. Section numbers match `lab_notebook.py`.

---

## Setup
> Confirm Agent mode is on. Type a quick prompt to test:
>
> *"What tables are available in workspace.genie_code_lab?"*

## Part 1 — Genie Code 101

> Reminder: open your Genie Code thread from **outside** this notebook
> (workspace home page is fine) so Agent mode doesn't add cells here.

Agent vs Chat mode (flip to **Chat** for this one, then back to **Agent**):
> *"What's the difference between Agent mode and Chat mode in Genie Code?"*

`@table` reference (in the chat panel):
> *"How many rows are in `@meter_readings` and what's the date range?"*

Slash commands:
> Type `/` to see the menu. Try:
> - `/findTables energy consumption`
> - `/findQueries top consumers`
> - `/explain` on a SQL cell in some other notebook

Feedback:
> On any response above, click **👍** (useful), **👎** (wrong/unhelpful — say
> why in the free-text box), or use the `⋯` overflow menu to **Report a bug**.

New conversation:
> Click **+ New chat** at the top of the Genie Code panel. The previous
> thread stays in history.

## Part 2 — Agent-mode EDA

> *"Perform exploratory data analysis on `@meter_readings`. Join in
> `@sites`, `@regions`, and `@business_units` as needed. Summarize the
> most interesting patterns and anomalies as a markdown report at the end."*

## Part 3a — Build the SDP pipeline

Create the pipeline (Genie Code does the workspace-side work, not just the file):
> *"Create a Lakeflow Spark Declarative Pipeline named **Energy Anomaly
> Pipeline** in this workspace. It should:
>
>   1. Read `@meter_readings` as a silver table, dropping rows where
>      `status = 'error'`.
>   2. Join to `@sites`, `@regions`, and `@business_units` for site,
>      region, and business unit metadata.
>   3. Produce a daily per-site gold table called
>      `daily_site_consumption` with columns: site_id, site_type,
>      business_unit_id, business_unit_name, region_id, region_name,
>      reading_date, total_kwh, peak_kw, avg_voltage, warning_count.
>   4. Add an `anomaly_flag` column that is `true` when the day's
>      total_kwh is more than 2 standard deviations above that site's
>      30-day mean.
>
> Use `dlt` decorators and PySpark. Place the source file at
> `pipeline/energy_pipeline.py` in the current Git folder. Target catalog
> `workspace`, schema `genie_code_lab`. Use Serverless compute and
> configure the pipeline to point at the source file you just created.
> Do not run it yet."*

Dry-run:
> *"Now dry-run (validate) the Energy Anomaly Pipeline and report any
> errors or warnings. Don't proceed to a full run."*

Full run:
> *"Validation passed — run the Energy Anomaly Pipeline for real. Wait for
> it to finish and tell me when the gold table is populated."*

Stretch:
> *"Add a `@dlt.expect_or_drop` data quality expectation that drops rows
> where `kwh_consumed` is negative."*

## Part 3b — Genie space

Create the space (Agent mode does the creation, not just suggest content):
> *"Create a new Genie space named **Energy Operations**. Include these
> four tables:
>
> - `workspace.genie_code_lab.daily_site_consumption`
> - `workspace.genie_code_lab.sites`
> - `workspace.genie_code_lab.regions`
> - `workspace.genie_code_lab.business_units`
>
> Write a one-paragraph space description focused on energy-anomaly
> investigation. Mention that the `anomaly_flag` column on
> `daily_site_consumption` is the canonical signal for 'unusual usage'
> questions, and that the gold table already carries `business_unit_name`
> and `region_name` so most grouping queries don't need joins."*

Add join relationships:
> *"In the Energy Operations Genie space, add the following join
> relationships:
>
> - `sites.region_id` → `regions.region_id`
> - `sites.business_unit_id` → `business_units.business_unit_id`
> - `daily_site_consumption.site_id` → `sites.site_id`
> - `daily_site_consumption.region_id` → `regions.region_id`
> - `daily_site_consumption.business_unit_id` → `business_units.business_unit_id`"*

Add SQL Expression measures:
> *"Add these SQL Expressions to the Energy Operations Genie space:
>
> 1. **kwh_per_sqft** — daily total_kwh normalized by site square
>    footage. Defined as
>    `daily_site_consumption.total_kwh / sites.square_footage`.
> 2. **deviation_from_baseline_pct** — % deviation from the site's
>    30-day mean. Defined as
>    `(daily_site_consumption.total_kwh - AVG(daily_site_consumption.total_kwh) OVER (PARTITION BY daily_site_consumption.site_id)) / AVG(daily_site_consumption.total_kwh) OVER (PARTITION BY daily_site_consumption.site_id) * 100`.
> 3. **is_anomaly** — boolean shorthand. Defined as
>    `daily_site_consumption.anomaly_flag = true`."*

Test questions:
> 1. *"Which business unit had the most anomalies last week?"*
> 2. *"Top 5 sites by kwh_per_sqft in the past 14 days."*
> 3. *"For SITE-XXXX, what's the daily kWh trend and how does it compare
>    to its baseline?"*  (substitute an actual flagged site_id from your data)

## Part 4 — Custom instructions

Baseline — saves the result to a new notebook:
> *"Write a small PySpark function that returns the top N sites by total
> kWh for a given month, grouped by business unit. Use
> `@daily_site_consumption`. Save the function to a new notebook in my
> workspace home folder named `top_consumers_baseline` so I can refer to
> it later. Don't run anything."*

After pasting `solutions/sample_assistant_instructions.md` into your
`.assistant_instructions.md` file, start a new chat and run:

> *"Write a small PySpark function that returns the top N sites by total
> kWh for a given month, grouped by business unit. Use
> `@daily_site_consumption`. Save the function to a new notebook in my
> workspace home folder named `top_consumers_with_instructions` so I can
> compare it with the baseline. Don't run anything."*

Open the two notebooks side by side and diff them.

## Part 5 — Custom skill

Trigger by intent (no `@`-mention):
> *"Investigate yesterday's energy anomalies and tell me what to look at."*

Genie Code should pick up the `anomaly-triage` skill automatically and
follow the steps. Look for the "Used skill: anomaly-triage" indicator
in the trace.

If it doesn't trigger, force it:
> *"Use the @anomaly-triage skill on the last 3 days of anomalies."*

## Part 6 — MCP server (Genie space)

After registering the Energy Operations Genie space as a Managed Genie MCP
server in Settings → MCP Servers, issue:

> *"Use the Energy Operations Genie space to find the top 3 sites by
> `kwh_per_sqft` over the last 14 days, and for each one, tell me its
> business unit and `deviation_from_baseline_pct` for that period."*

Watch for a tool call to **Energy Operations Genie Space** in the agent
trace. The fact that `kwh_per_sqft` and `deviation_from_baseline_pct`
exist only as SQL Expressions inside the space (not as columns in any
underlying table) is your evidence the MCP did the work.

Stretch — mix MCP and direct SQL:
> *"For those top-3 sites, also show me the count of warning rows in
> `@meter_readings` for the same period."*

## Bonus — Build more on your own

### 1. Databricks App (Streamlit)
> *"Create and deploy a new Databricks App named **energy-anomaly-viewer**.
> Place source files in `apps/energy-anomaly-viewer/` in the current Git
> folder.
>
> - `app.yaml` runs `streamlit run app.py`. Set `DATABRICKS_WAREHOUSE_ID`
>   to my Serverless warehouse's ID (look it up — don't ask me).
> - `requirements.txt`: databricks-sdk, databricks-sql-connector,
>   streamlit, pandas.
> - `app.py`: a Streamlit page that queries
>   `workspace.genie_code_lab.daily_site_consumption` for rows where
>   `anomaly_flag = true`, with a sortable table (site_name, site_type,
>   business_unit_name, region_name, total_kwh, peak_kw, deviation_pct),
>   a sidebar date-range filter (default last 14 days), and a site-type
>   multiselect. Auth via `databricks.sdk.core.Config` on-behalf-of-user.
>
> Create the app resource, point it at that folder, deploy, and give me
> the URL."*

Reference fallback: `solutions/sample_app/`.

### 2. AI/BI Dashboard
> *"Create a new AI/BI dashboard called **Energy Operations Overview**
> backed by `workspace.genie_code_lab.daily_site_consumption`. Add four
> widgets:
>
> 1. KPI counter — total anomalies in the last 7 days.
> 2. Bar chart — daily anomaly count over the last 30 days.
> 3. Stacked bar — anomalies by `business_unit_name` × `site_type`.
> 4. Table — top 10 (site, day) rows by `deviation_pct`.
>
> Add a global date-range filter and publish the dashboard."*

### 3. Lakeflow Job — schedule the pipeline
> *"Create a Lakeflow Job named **energy-anomaly-daily** that runs the
> Energy Anomaly Pipeline (built in Part 3a) every day at 06:00 UTC.
> Send a notification to my email on failure. Use Serverless compute."*

### 4. Unity Catalog Function
> *"Create a Unity Catalog SQL function
> `workspace.genie_code_lab.get_site_anomalies(site_id STRING, days INT)`
> that returns rows from
> `workspace.genie_code_lab.daily_site_consumption` where the given site
> has `anomaly_flag = true` within the past N days, ordered by
> `deviation_pct` descending. Add a docstring. Then run a test query
> calling it for `SITE-0005` over 14 days and show me the result."*

### 5. Forecasting model + endpoint
> *"Train a per-site daily-kWh forecasting model on
> `workspace.genie_code_lab.daily_site_consumption`. Use Prophet (or
> whichever forecasting library fits best). Train one model per
> `site_id`, log them as a single MLflow registered model, and deploy a
> serving endpoint that accepts `site_id` and `horizon_days` and returns
> the forecast. Show me sample inference output for two sites."*
