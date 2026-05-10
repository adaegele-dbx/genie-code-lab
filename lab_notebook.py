# Databricks notebook source

# MAGIC %md
# MAGIC # Hands-On with Genie Code
# MAGIC ### A ~47-minute lab
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## What you'll do
# MAGIC
# MAGIC In this lab you'll use **Genie Code** — Databricks' agentic AI assistant —
# MAGIC to take an unfamiliar IoT energy dataset and turn it into a working
# MAGIC analytics stack: a Lakeflow pipeline, a Genie space, and a Databricks App.
# MAGIC Then you'll customize Genie Code itself with markdown so it follows your
# MAGIC team's conventions and workflows.
# MAGIC
# MAGIC | Step | What you'll do | Time |
# MAGIC |------|----------------|------|
# MAGIC | **Setup** | Pick a catalog, seed four energy tables, open Genie Code, confirm Agent mode | ~3 min |
# MAGIC | **Part 1** | Genie Code 101 — agent vs chat, `@`, slash commands, feedback, new chats | ~4 min |
# MAGIC | **Part 2** | Agent-mode EDA — one prompt, watch it plan and run | ~5 min |
# MAGIC | **Part 3a** | Have Genie Code create, dry-run, and run a **Lakeflow SDP** | ~9 min |
# MAGIC | **Part 3b** | Have Genie Code create a **Genie space** with joins and SQL Expressions | ~7 min |
# MAGIC | **Part 4** | Customize Genie Code with **custom instructions** — diff two saved notebooks | ~6 min |
# MAGIC | **Part 5** | Customize Genie Code with a **Skill** | ~6 min |
# MAGIC | **Part 6** | Customize Genie Code with an **MCP server** — register the Genie space and call it | ~5 min |
# MAGIC | **Bonus** | A menu of additional resources to build with Genie Code on your own time | optional |
# MAGIC | **Wrap-up** | Recap and what to try next | ~2 min |
# MAGIC
# MAGIC > **Tip:** Each part is self-contained. If one runs long, skip ahead and
# MAGIC > come back later — every section's checkpoint tells you when you're
# MAGIC > ready to move on.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Prerequisites
# MAGIC
# MAGIC - This notebook is running in a Databricks workspace with **Unity Catalog**
# MAGIC   enabled. (All Free Edition workspaces have UC by default.)
# MAGIC - This repository has been cloned as a **Git Folder** in your workspace
# MAGIC   (`Workspace` → `Create` → `Git folder`).
# MAGIC - You have a **SQL warehouse** running (Free Edition's default 2X-Small is
# MAGIC   plenty).
# MAGIC - **Free Edition limit:** 1 active Databricks App. Only matters if you
# MAGIC   try the **Bonus** App task at the end — delete any old app first.
# MAGIC
# MAGIC > ⚠️ **Free Edition quota:** Free Edition workspaces have a small daily
# MAGIC > compute quota that the SDP pipeline run (Part 3a), the Genie space
# MAGIC > queries, and the deployed app all consume. **It is likely that you will
# MAGIC > run out of quota** before the end of the lab, especially if you re-run
# MAGIC > the pipeline several times. If everything stops responding mid-lab,
# MAGIC > that's almost certainly why — pick up the rest after quota resets
# MAGIC > (typically the next day).
# MAGIC
# MAGIC > 🛑 **Important — run Genie Code conversations OUTSIDE this notebook.**
# MAGIC > Throughout the lab, every Genie Code prompt should be entered in a
# MAGIC > Genie Code thread that is **not anchored to `lab_notebook.py`**. The
# MAGIC > simplest way: open the Genie Code panel from somewhere else (the
# MAGIC > workspace home page, a new untitled notebook, or the SQL editor) and
# MAGIC > keep this notebook open only for reading instructions and running the
# MAGIC > setup/verify cells. If you run conversations from inside this notebook,
# MAGIC > Agent mode will sometimes add cells *to this notebook itself* when
# MAGIC > performing tasks like EDA — making the lab harder to follow on a
# MAGIC > re-run.
# MAGIC
# MAGIC > Run each cell with `Shift + Enter` and read the markdown between them —
# MAGIC > the lab instructions live in the markdown.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Setup — Configure & seed the data
# MAGIC
# MAGIC ### Catalog selection
# MAGIC
# MAGIC By default the lab seeds and reads from the **`workspace`** catalog, which
# MAGIC works on every Databricks Free Edition workspace. If you're running in a
# MAGIC fuller workspace where the `workspace` catalog isn't a good choice (or
# MAGIC where you want to keep lab data isolated), set the `catalog` widget at
# MAGIC the top of this notebook to your preferred catalog name.
# MAGIC
# MAGIC Run the cell below once to declare the widget. The default is `workspace`.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Catalog Name")
catalog = dbutils.widgets.get("catalog")
schema = "genie_code_lab"
print(f"Lab will use: {catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC > 📝 **If you change the catalog from `workspace` to something else,** all
# MAGIC > Genie Code prompts later in this lab that mention `workspace.genie_code_lab`
# MAGIC > should be edited before you paste them — substitute your catalog name.
# MAGIC > The executable SQL cells in this notebook pick up the widget value
# MAGIC > automatically via `${catalog}`, so they need no edits.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Seed the four lab tables
# MAGIC
# MAGIC The cell below creates `${catalog}.genie_code_lab` and populates it with
# MAGIC four tables in a small star schema. Total seed time is typically **a few
# MAGIC seconds**.
# MAGIC
# MAGIC | Table | Rows | Role |
# MAGIC |-------|------|------|
# MAGIC | `regions` | 5 | Dimension — US regions with timezones |
# MAGIC | `business_units` | 5 | Dimension — internal business units |
# MAGIC | `sites` | 10 | Physical sites; foreign keys to `regions` and `business_units` |
# MAGIC | `meter_readings` | ~29k | 15-minute interval readings over the last 30 days |
# MAGIC
# MAGIC The scenario: you're on the energy operations team of an industrial
# MAGIC company that owns 10 sites across the US.  Two of those sites have an
# MAGIC intentional multi-day **consumption spike** — organic anomalies for the
# MAGIC pipeline in Part 3a to find. Nothing about the raw data is deliberately
# MAGIC broken.

# COMMAND ----------

# MAGIC %run ./data/setup_tables

# COMMAND ----------

# MAGIC %md
# MAGIC ### Verify the setup
# MAGIC
# MAGIC The query below should return four rows. If you see different counts,
# MAGIC re-run the setup cell above.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'regions' AS table_name, COUNT(*) AS row_count FROM ${catalog}.genie_code_lab.regions
# MAGIC UNION ALL
# MAGIC SELECT 'business_units', COUNT(*) FROM ${catalog}.genie_code_lab.business_units
# MAGIC UNION ALL
# MAGIC SELECT 'sites', COUNT(*) FROM ${catalog}.genie_code_lab.sites
# MAGIC UNION ALL
# MAGIC SELECT 'meter_readings', COUNT(*) FROM ${catalog}.genie_code_lab.meter_readings

# COMMAND ----------

# MAGIC %md
# MAGIC ### Open Genie Code and turn on Agent mode
# MAGIC
# MAGIC 1. Click the **sparkle icon** in the top-right of the screen — this opens
# MAGIC    the Genie Code panel.
# MAGIC 2. At the bottom of the panel, find the **Agent mode** toggle. Make sure
# MAGIC    it is **on** for the rest of the lab.
# MAGIC 3. Type a quick test prompt to confirm it works:
# MAGIC
# MAGIC    > *"What tables are available in workspace.genie_code_lab?"*
# MAGIC
# MAGIC > **Why Agent mode?** Chat mode answers questions and writes code on
# MAGIC > demand. Agent mode plans multi-step tasks, runs cells on its own, reads
# MAGIC > the outputs, and adapts. Almost everything in this lab needs Agent mode.
# MAGIC
# MAGIC ✅ **Setup checkpoint:** four tables exist, Agent mode is on. Move on.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 1 — Genie Code 101 (4 min)
# MAGIC
# MAGIC Before going autonomous, let's get a feel for the basic surface area.
# MAGIC Remember: open your Genie Code thread from **outside** this notebook
# MAGIC (workspace home page works well) so Agent mode doesn't add cells here.
# MAGIC
# MAGIC ### 1a. Agent mode vs. Chat mode
# MAGIC
# MAGIC At the bottom of the Genie Code panel there's a mode toggle.
# MAGIC
# MAGIC | Mode | What it does | When to use |
# MAGIC |------|--------------|-------------|
# MAGIC | **Chat** | Answers questions and writes code on demand. Doesn't run code. | Quick lookups, "explain this," "write me a function." |
# MAGIC | **Agent** | Plans multi-step tasks, runs code, reads outputs, iterates. | Anything that takes more than one step — EDA, building pipelines, creating apps. |
# MAGIC
# MAGIC Flip to **Chat** mode and ask:
# MAGIC
# MAGIC > *"What's the difference between Agent mode and Chat mode in Genie Code?"*
# MAGIC
# MAGIC Then flip back to **Agent** mode — that's where you'll stay for the
# MAGIC rest of the lab.
# MAGIC
# MAGIC ### 1b. `@`-reference a table
# MAGIC
# MAGIC In the chat box, type `@` and start typing `meter_readings`. Genie Code
# MAGIC will autocomplete table names from Unity Catalog. Pick `meter_readings`,
# MAGIC then ask:
# MAGIC
# MAGIC > *"How many rows are in `@meter_readings` and what's the date range?"*
# MAGIC
# MAGIC The `@` syntax also works for notebooks, files, Genie spaces, and (later
# MAGIC in the lab) skills.
# MAGIC
# MAGIC ### 1c. Slash commands
# MAGIC
# MAGIC In the Genie Code chat box, type `/` to open the slash-command menu.
# MAGIC The full set is documented in the
# MAGIC [Genie Code docs](https://docs.databricks.com/aws/en/notebooks/code-assistant);
# MAGIC try a few now:
# MAGIC
# MAGIC | Command | What to try |
# MAGIC |---------|-------------|
# MAGIC | `/findTables` | `/findTables energy consumption` |
# MAGIC | `/findQueries` | `/findQueries top consumers` |
# MAGIC | `/explain` | Open an existing notebook with a SQL cell, then run `/explain` |
# MAGIC
# MAGIC ### 1d. Provide feedback
# MAGIC
# MAGIC Every Genie Code response has feedback affordances — they're how
# MAGIC Databricks improves the model and how you flag a regression.
# MAGIC
# MAGIC On the response from 1b or 1c:
# MAGIC
# MAGIC 1. Click the **👍 thumbs-up** if the response was useful — optional, but
# MAGIC    valued.
# MAGIC 2. Click the **👎 thumbs-down** if it was wrong or unhelpful. A short
# MAGIC    free-text box appears — say briefly *why* (e.g., "wrong table,"
# MAGIC    "missed the date filter"). The team reads these.
# MAGIC 3. From the response's overflow menu (the `⋯`) you can also **Report a
# MAGIC    bug** — use this when something is broken in a way that goes beyond
# MAGIC    "the answer was wrong" (UI freeze, crash, security issue, etc.).
# MAGIC
# MAGIC ### 1e. Start a new conversation
# MAGIC
# MAGIC Genie Code threads accumulate context, which is usually helpful but
# MAGIC sometimes anchors it to the wrong thing. When you want a clean slate:
# MAGIC
# MAGIC - Click the **+ New chat** button at the top of the Genie Code panel
# MAGIC   (also reachable via the history sidebar)
# MAGIC - The old thread is preserved in history — you can come back to it
# MAGIC
# MAGIC You'll use this several times later in the lab — especially in Part 4
# MAGIC when comparing Genie Code's output before and after adding custom
# MAGIC instructions.
# MAGIC
# MAGIC ✅ **Part 1 checkpoint:** you've experienced both modes, used `@` and
# MAGIC `/` commands, given feedback on a response, and know how to start a
# MAGIC fresh thread. Move on.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 2 — Agent-mode EDA (5 min)
# MAGIC
# MAGIC One prompt, then sit back and watch.
# MAGIC
# MAGIC In the Genie Code chat box, paste this:
# MAGIC
# MAGIC > *"Perform exploratory data analysis on `@meter_readings`. Join in
# MAGIC > `@sites`, `@regions`, and `@business_units` as needed. Summarize the
# MAGIC > most interesting patterns and anomalies as a markdown report at the
# MAGIC > end."*
# MAGIC
# MAGIC As Genie Code runs, watch what it does:
# MAGIC
# MAGIC - It first **plans** a list of steps (you'll see a checklist)
# MAGIC - It **writes and runs cells** in sequence — you'll see new cells appear
# MAGIC   in the notebook
# MAGIC - It **reads cell output** and adapts the next cell based on what it
# MAGIC   found
# MAGIC - At the end it produces a **markdown summary**
# MAGIC
# MAGIC > **Discussion (1 min):** What did Agent mode do that you would have
# MAGIC > done differently? Where did it surprise you — for better or worse?
# MAGIC
# MAGIC > **Stretch:** While the agent works, try
# MAGIC > *"Add a chart of total daily kWh by site_type"* as a follow-up.
# MAGIC
# MAGIC ✅ **Part 2 checkpoint:** Genie Code finished an EDA, wrote a summary,
# MAGIC and you scrolled through what it built. Move on.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 3 — Build with Agent mode (~16 min)
# MAGIC
# MAGIC This is the heart of the lab. You'll build two artifacts back-to-back,
# MAGIC each with a single Agent-mode prompt:
# MAGIC
# MAGIC 1. **3a — A Lakeflow Spark Declarative Pipeline** that produces a daily
# MAGIC    per-site gold table with a 2σ anomaly flag.
# MAGIC 2. **3b — A Genie space** over the gold table for natural-language Q&A.
# MAGIC
# MAGIC Each sub-step has its own checkpoint — don't move on until the previous
# MAGIC artifact ran. Want to also build a Databricks App, dashboard, or
# MAGIC scheduled job? Those are in the **Bonus — On your own** section near
# MAGIC the end of the lab.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Part 3a — Build & run the SDP pipeline (9 min)
# MAGIC
# MAGIC **Goal:** A `daily_site_consumption` table with one row per (site, day)
# MAGIC and an `anomaly_flag` column.
# MAGIC
# MAGIC In this part you'll have Genie Code do **everything** — write the
# MAGIC pipeline source, create the pipeline resource in the workspace, dry-run
# MAGIC it, and then do a full run. You won't click around in the Pipelines UI
# MAGIC yourself.
# MAGIC
# MAGIC > Reminder: if you set the catalog widget at the top of this notebook to
# MAGIC > something other than `workspace`, edit the catalog name in each prompt
# MAGIC > before you paste it.
# MAGIC
# MAGIC #### Step 1 — Have Genie Code create the pipeline
# MAGIC
# MAGIC In the Genie Code chat panel (Agent mode, opened from outside this
# MAGIC notebook), paste:
# MAGIC
# MAGIC > *"Create a Lakeflow Spark Declarative Pipeline named **Energy Anomaly
# MAGIC > Pipeline** in this workspace. It should:*
# MAGIC >
# MAGIC > 1. *Read `@meter_readings` as a silver table, dropping rows where
# MAGIC >    `status = 'error'`.*
# MAGIC > 2. *Join to `@sites`, `@regions`, and `@business_units` for site,
# MAGIC >    region, and business unit metadata.*
# MAGIC > 3. *Produce a daily per-site gold table called
# MAGIC >    `daily_site_consumption` with columns: `site_id`, `site_type`,
# MAGIC >    `business_unit_id`, `business_unit_name`, `region_id`, `region_name`,
# MAGIC >    `reading_date`, `total_kwh`, `peak_kw`, `avg_voltage`, `warning_count`.*
# MAGIC > 4. *Add an `anomaly_flag` column that is `true` when the day's
# MAGIC >    `total_kwh` is more than 2 standard deviations above that site's
# MAGIC >    30-day mean.*
# MAGIC >
# MAGIC > *Use `dlt` decorators and PySpark. Place the source file at
# MAGIC > `pipeline/energy_pipeline.py` in the current Git folder. Target
# MAGIC > catalog `workspace`, schema `genie_code_lab`. Use Serverless compute
# MAGIC > and configure the pipeline to point at the source file you just
# MAGIC > created. Do not run it yet."*
# MAGIC
# MAGIC Agent mode should: (a) write `pipeline/energy_pipeline.py`, (b) create
# MAGIC the pipeline resource and link it to the source file, and (c) report
# MAGIC back with the pipeline URL or name. **It should not run the pipeline
# MAGIC yet** — that's the next step.
# MAGIC
# MAGIC #### Step 2 — Ask Genie Code to dry-run the pipeline
# MAGIC
# MAGIC A dry run (also called *validate*) compiles the pipeline graph,
# MAGIC type-checks the references, and resolves table dependencies without
# MAGIC actually moving data. It's how you catch broken DAGs in a few seconds
# MAGIC instead of waiting for a full run to fail.
# MAGIC
# MAGIC Continue the same Genie Code thread:
# MAGIC
# MAGIC > *"Now dry-run (validate) the Energy Anomaly Pipeline and report any
# MAGIC > errors or warnings. Don't proceed to a full run."*
# MAGIC
# MAGIC If validation fails, ask Genie Code to fix the errors and re-validate.
# MAGIC Repeat until you get a clean validation. Typical fixable issues: column
# MAGIC name typos, missing imports, a `dlt.read` reference that points at a
# MAGIC table that doesn't exist yet.
# MAGIC
# MAGIC #### Step 3 — Ask Genie Code to do a full run
# MAGIC
# MAGIC Once validation is clean:
# MAGIC
# MAGIC > *"Validation passed — run the Energy Anomaly Pipeline for real. Wait
# MAGIC > for it to finish and tell me when the gold table is populated."*
# MAGIC
# MAGIC Cold start can take 30–60 seconds on Free Edition; the actual run
# MAGIC should be quick because the dataset is small. While you wait, glance at
# MAGIC the generated `pipeline/energy_pipeline.py` to see what Agent mode
# MAGIC produced.
# MAGIC
# MAGIC #### Step 4 — Verify the gold table
# MAGIC
# MAGIC Once Genie Code reports the run is done, run the cell below to confirm
# MAGIC the table exists and has anomaly rows.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   COUNT(*)                                         AS total_rows,
# MAGIC   COUNT_IF(anomaly_flag)                           AS anomaly_rows,
# MAGIC   COUNT(DISTINCT site_id)                          AS sites_covered,
# MAGIC   MIN(reading_date)                                AS first_date,
# MAGIC   MAX(reading_date)                                AS last_date
# MAGIC FROM ${catalog}.genie_code_lab.daily_site_consumption

# COMMAND ----------

# MAGIC %md
# MAGIC > **Stretch:** Ask Genie Code to add a `@dlt.expect_or_drop` data quality
# MAGIC > expectation that drops rows where `kwh_consumed` is negative, then
# MAGIC > re-run the pipeline.
# MAGIC
# MAGIC > **Stuck?** If Genie Code's generated pipeline won't run, copy
# MAGIC > `solutions/sample_pipeline.py` into `pipeline/energy_pipeline.py` and
# MAGIC > re-run. The pipeline UI may need to be re-validated to pick it up.
# MAGIC
# MAGIC ✅ **Part 3a checkpoint:** the verify query returns nonzero
# MAGIC `anomaly_rows`. Move on.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Part 3b — Create a Genie space (7 min)
# MAGIC
# MAGIC **Goal:** A natural-language Q&A interface over the gold table, with
# MAGIC join relationships and SQL Expression measures configured — all created
# MAGIC by Genie Code.
# MAGIC
# MAGIC > Reminder: if your catalog isn't `workspace`, substitute your catalog
# MAGIC > name in each prompt before pasting.
# MAGIC
# MAGIC #### Step 1 — Have Genie Code create the space
# MAGIC
# MAGIC In Agent mode, paste:
# MAGIC
# MAGIC > *"Create a new Genie space named **Energy Operations**. Include these
# MAGIC > four tables:
# MAGIC >
# MAGIC > - `workspace.genie_code_lab.daily_site_consumption`
# MAGIC > - `workspace.genie_code_lab.sites`
# MAGIC > - `workspace.genie_code_lab.regions`
# MAGIC > - `workspace.genie_code_lab.business_units`
# MAGIC >
# MAGIC > Write a one-paragraph space description focused on energy-anomaly
# MAGIC > investigation. Mention that the `anomaly_flag` column on
# MAGIC > `daily_site_consumption` is the canonical signal for 'unusual usage'
# MAGIC > questions, and that the gold table already carries `business_unit_name`
# MAGIC > and `region_name` so most grouping queries don't need joins."*
# MAGIC
# MAGIC When Agent mode reports back, open the space and confirm: the four
# MAGIC tables are listed, and the description is in place.
# MAGIC
# MAGIC #### Step 2 — Have Genie Code add join relationships
# MAGIC
# MAGIC Genie spaces let you predefine how tables join so natural-language
# MAGIC questions don't guess. Continue the same thread:
# MAGIC
# MAGIC > *"In the Energy Operations Genie space, add the following join
# MAGIC > relationships:*
# MAGIC >
# MAGIC > - *`sites.region_id` → `regions.region_id`*
# MAGIC > - *`sites.business_unit_id` → `business_units.business_unit_id`*
# MAGIC > - *`daily_site_consumption.site_id` → `sites.site_id`*
# MAGIC > - *`daily_site_consumption.region_id` → `regions.region_id`*
# MAGIC > - *`daily_site_consumption.business_unit_id` → `business_units.business_unit_id`"*
# MAGIC
# MAGIC Open the space's **Joins** tab and verify all five relationships
# MAGIC appear.
# MAGIC
# MAGIC #### Step 3 — Have Genie Code add SQL Expression measures
# MAGIC
# MAGIC SQL Expressions are reusable computed columns/measures defined at the
# MAGIC space level — Genie will use them whenever they're relevant to a user's
# MAGIC question, instead of re-deriving the math each time.
# MAGIC
# MAGIC Continue the thread:
# MAGIC
# MAGIC > *"Add these SQL Expressions to the Energy Operations Genie space:*
# MAGIC >
# MAGIC > 1. ***kwh_per_sqft*** — *daily total_kwh normalized by site square
# MAGIC >    footage. Defined as
# MAGIC >    `daily_site_consumption.total_kwh / sites.square_footage`.*
# MAGIC > 2. ***deviation_from_baseline_pct*** — *% deviation from the site's
# MAGIC >    30-day mean. Defined as
# MAGIC >    `(daily_site_consumption.total_kwh - AVG(daily_site_consumption.total_kwh) OVER (PARTITION BY daily_site_consumption.site_id)) / AVG(daily_site_consumption.total_kwh) OVER (PARTITION BY daily_site_consumption.site_id) * 100`.*
# MAGIC > 3. ***is_anomaly*** — *boolean shorthand. Defined as
# MAGIC >    `daily_site_consumption.anomaly_flag = true`.*"*
# MAGIC
# MAGIC Open the space's **SQL Expressions** tab and verify all three appear.
# MAGIC
# MAGIC #### Step 4 — Ask three NL questions
# MAGIC
# MAGIC Open the Energy Operations space and ask:
# MAGIC
# MAGIC 1. *"Which business unit had the most anomalies last week?"*
# MAGIC 2. *"Top 5 sites by kwh_per_sqft in the past 14 days."*  (this exercises
# MAGIC    the SQL Expression you just added)
# MAGIC 3. Pick a flagged site from the verify query in 3a (any row where
# MAGIC    `anomaly_flag = true`) and ask:
# MAGIC    *"For SITE-XXXX, what's the daily kWh trend and how does it compare
# MAGIC    to its baseline?"*  (this exercises the deviation expression)
# MAGIC
# MAGIC Click **Show generated code** on each answer to see the SQL Genie wrote.
# MAGIC
# MAGIC > **Stuck?** If your space gives bad answers, paste the description and
# MAGIC > tuning hints from `solutions/sample_genie_instructions.md` into the
# MAGIC > space's instructions.
# MAGIC
# MAGIC ✅ **Part 3b checkpoint:** three questions answered, you've seen the
# MAGIC SQL each one generated. Move on.
# MAGIC
# MAGIC ✅ **Part 3 checkpoint:** pipeline runs, Genie space answers
# MAGIC questions. You've built the analytics core — customization comes next.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 4 — Customize Genie Code with custom instructions (6 min)
# MAGIC
# MAGIC Genie Code's defaults are good. Your team's defaults are better.
# MAGIC In this part you'll see how a small markdown file changes Genie Code's
# MAGIC output style for every prompt you give it from then on.
# MAGIC
# MAGIC ### 4a. Run a baseline prompt — save the output to a notebook
# MAGIC
# MAGIC We'll save the baseline output to a notebook so you have something
# MAGIC concrete to diff against later.
# MAGIC
# MAGIC In the Genie Code panel (start a **+ New chat** so prior context doesn't
# MAGIC bleed in), paste:
# MAGIC
# MAGIC > *"Write a small PySpark function that returns the top N sites by
# MAGIC > total kWh for a given month, grouped by business unit. Use
# MAGIC > `@daily_site_consumption`. Save the function to a new notebook in my
# MAGIC > workspace home folder named `top_consumers_baseline` so I can refer
# MAGIC > to it later. Don't run anything."*
# MAGIC
# MAGIC Open the resulting `top_consumers_baseline` notebook. Note: variable
# MAGIC names, comment style, whether it uses type hints, whether it aliases
# MAGIC `pyspark.sql.functions`, whether it uses CTEs vs. subqueries, etc.
# MAGIC We're going to compare.
# MAGIC
# MAGIC ### 4b. Add custom instructions
# MAGIC
# MAGIC 1. Click the **gear icon** at the top of the Genie Code panel.
# MAGIC 2. Under **User instructions**, click **Add instructions file**.
# MAGIC    A new file `.assistant_instructions.md` opens in your home folder
# MAGIC    (`/Users/<your-email>/.assistant_instructions.md`).
# MAGIC 3. Open `solutions/sample_assistant_instructions.md` in this Git folder
# MAGIC    and copy the markdown block (everything inside the fenced code block
# MAGIC    titled `# My Genie Code instructions`).
# MAGIC 4. Paste it into your `.assistant_instructions.md`. Save.
# MAGIC
# MAGIC ### 4c. Re-run the prompt — save to a second notebook
# MAGIC
# MAGIC Open a **+ New chat** in the Genie Code panel (so the previous run
# MAGIC doesn't anchor the response), then paste:
# MAGIC
# MAGIC > *"Write a small PySpark function that returns the top N sites by
# MAGIC > total kWh for a given month, grouped by business unit. Use
# MAGIC > `@daily_site_consumption`. Save the function to a new notebook in my
# MAGIC > workspace home folder named `top_consumers_with_instructions` so I
# MAGIC > can compare it with the baseline. Don't run anything."*
# MAGIC
# MAGIC ### 4d. Diff the two notebooks
# MAGIC
# MAGIC Open `top_consumers_baseline` and `top_consumers_with_instructions`
# MAGIC side by side. You should see, in the second one:
# MAGIC
# MAGIC - Type hints on every function signature
# MAGIC - `pyspark.sql.functions` aliased as `F`
# MAGIC - Google-style docstrings
# MAGIC - CTEs in any embedded SQL instead of nested subqueries
# MAGIC - Only "why" comments, no "what" comments
# MAGIC
# MAGIC > **Why this matters:** instructions persist across every Genie Code
# MAGIC > thread you open, in every notebook. A workspace admin can also place
# MAGIC > a `.assistant_workspace_instructions.md` in the workspace root for
# MAGIC > team-wide rules — the same mechanism, applied to everyone.
# MAGIC
# MAGIC ✅ **Part 4 checkpoint:** two notebooks side by side showing the
# MAGIC before/after.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 5 — Customize Genie Code with a Skill (6 min)
# MAGIC
# MAGIC Custom instructions are global. **Skills** are narrow, reusable
# MAGIC workflows that Agent mode auto-loads when the user's request matches.
# MAGIC In this part you'll create a small "anomaly triage" skill and watch
# MAGIC Agent mode pick it up.
# MAGIC
# MAGIC ### 5a. Create the skill folder
# MAGIC
# MAGIC In the workspace file browser, navigate to your home folder
# MAGIC (`/Users/<your-email>`) and create the path:
# MAGIC
# MAGIC ```
# MAGIC /Users/<your-email>/.assistant/skills/anomaly-triage/SKILL.md
# MAGIC ```
# MAGIC
# MAGIC The `.assistant` folder may not exist yet — create it. Folders that
# MAGIC start with a dot may be hidden by default in the file browser; toggle
# MAGIC **Show hidden** if you don't see it after creating.
# MAGIC
# MAGIC ### 5b. Paste the skill content
# MAGIC
# MAGIC Open `solutions/sample_skill/SKILL.md` in this Git folder and copy its
# MAGIC entire contents (including the YAML frontmatter at the top). Paste into
# MAGIC the new `SKILL.md` file. Save.
# MAGIC
# MAGIC ### 5c. Trigger the skill by intent
# MAGIC
# MAGIC Open a **new thread** in the Genie Code panel. Make sure Agent mode is
# MAGIC still on. Paste:
# MAGIC
# MAGIC > *"Investigate yesterday's energy anomalies and tell me what to look at."*
# MAGIC
# MAGIC Watch the agent's trace. You should see a step that reads something like
# MAGIC **"Used skill: anomaly-triage"** — that's the skill being auto-loaded
# MAGIC because the description matched the user's intent. The agent will then
# MAGIC follow the numbered steps in your `SKILL.md`:
# MAGIC
# MAGIC 1. Pull anomalous rows
# MAGIC 2. Enrich with site, business unit, and region context
# MAGIC 3. Quantify deviation
# MAGIC 4. Cross-reference meter health
# MAGIC 5. Produce a structured markdown report
# MAGIC
# MAGIC ### 5d. (Stretch) Force the skill explicitly
# MAGIC
# MAGIC If the auto-trigger didn't fire, you can `@`-mention the skill:
# MAGIC
# MAGIC > *"Use the @anomaly-triage skill on the last 3 days of anomalies."*
# MAGIC
# MAGIC > **Why this matters:** instructions tell Genie Code *how* to write code.
# MAGIC > Skills tell it *what process to follow* for a specific kind of task.
# MAGIC > Together they let your team encode workflows once and have every team
# MAGIC > member benefit, automatically.
# MAGIC
# MAGIC ✅ **Part 5 checkpoint:** skill triggered, structured report produced.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 6 — Customize Genie Code with an MCP server (5 min)
# MAGIC
# MAGIC Instructions tell Genie Code *how* to write code. Skills tell it *what
# MAGIC process to follow*. **MCP servers** give it access to *new tools and
# MAGIC data sources* — things outside the workspace, or specialized
# MAGIC interfaces (like a tuned Genie space) that should be the canonical
# MAGIC way to answer certain questions.
# MAGIC
# MAGIC In this part you'll register the **Energy Operations** Genie space you
# MAGIC built in Part 3b as a **Managed Genie MCP server**, then issue a
# MAGIC question that Genie Code should route through that MCP rather than
# MAGIC answering with raw SQL of its own.
# MAGIC
# MAGIC ### 6a. Register the Genie space as an MCP server
# MAGIC
# MAGIC 1. Open the Genie Code panel (still outside this notebook).
# MAGIC 2. Click the **gear icon** at the top of the panel.
# MAGIC 3. Open the **MCP Servers** tab.
# MAGIC 4. Click the **+** button to add a server.
# MAGIC 5. Server type: **Genie Space** (a Databricks-managed MCP).
# MAGIC 6. Pick the **Energy Operations** space you created in Part 3b.
# MAGIC 7. Click **Save**.
# MAGIC
# MAGIC The MCP is immediately available — no restart needed. Genie Code's
# MAGIC overall MCP-tool budget is capped at 20 across all servers; one Genie
# MAGIC space counts as one tool.
# MAGIC
# MAGIC > **Why a Genie space MCP and not just SQL?** Your Energy Operations
# MAGIC > space already has tuned descriptions, join relationships, and SQL
# MAGIC > Expressions like `kwh_per_sqft` and `deviation_from_baseline_pct`.
# MAGIC > Routing through the MCP means Genie Code answers using *those* —
# MAGIC > faithful to your team's defined semantics — instead of re-deriving
# MAGIC > the math each time.
# MAGIC
# MAGIC ### 6b. Issue a query that triggers the MCP
# MAGIC
# MAGIC Open a **+ New chat** in the Genie Code panel (Agent mode on). Paste:
# MAGIC
# MAGIC > *"Use the Energy Operations Genie space to find the top 3 sites by
# MAGIC > `kwh_per_sqft` over the last 14 days, and for each one, tell me its
# MAGIC > business unit and `deviation_from_baseline_pct` for that period."*
# MAGIC
# MAGIC Watch the agent's trace. You should see a tool call to the
# MAGIC **Energy Operations Genie Space** MCP — usually surfaced as a step
# MAGIC labeled *"Calling MCP server: Energy Operations"* or similar. The
# MAGIC answer is composed from the MCP's response rather than from a SQL
# MAGIC query Genie Code wrote on its own.
# MAGIC
# MAGIC > **Tip:** Both `kwh_per_sqft` and `deviation_from_baseline_pct` are
# MAGIC > SQL Expressions defined in the Genie space — they don't exist as
# MAGIC > columns in any underlying table. If Genie Code answers correctly,
# MAGIC > that's strong evidence the MCP did the work.
# MAGIC
# MAGIC > **Stretch:** ask a follow-up that mixes MCP and direct-SQL context:
# MAGIC > *"For those top-3 sites, also show me the count of warning rows in
# MAGIC > `@meter_readings` for the same period."* — Genie Code should
# MAGIC > re-use the MCP results for site identity and run direct SQL for the
# MAGIC > warning counts.
# MAGIC
# MAGIC ✅ **Part 6 checkpoint:** Genie space registered as an MCP server,
# MAGIC and you've seen Genie Code call it.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Bonus — Build more on your own
# MAGIC
# MAGIC Five other Databricks resources Genie Code can build for you on top of
# MAGIC the same `daily_site_consumption` gold table. Pick whichever sounds
# MAGIC interesting after the lab. Each one is a single Agent-mode prompt.
# MAGIC
# MAGIC > Reminder: substitute your catalog name in any prompt below if it
# MAGIC > isn't `workspace`. Open the Genie Code panel from outside this
# MAGIC > notebook so Agent mode doesn't write into the lab notebook.
# MAGIC
# MAGIC ### 1. Databricks App (Streamlit)
# MAGIC
# MAGIC One-page anomaly browser. Free Edition allows one running app at a
# MAGIC time — make sure no other app is running first.
# MAGIC
# MAGIC > *"Create and deploy a new Databricks App named **energy-anomaly-viewer**.
# MAGIC > Place source files in `apps/energy-anomaly-viewer/` in the current
# MAGIC > Git folder.*
# MAGIC >
# MAGIC > - *`app.yaml` runs `streamlit run app.py`. Set
# MAGIC >   `DATABRICKS_WAREHOUSE_ID` to my Serverless warehouse's ID (look it
# MAGIC >   up — don't ask me).*
# MAGIC > - *`requirements.txt`: databricks-sdk, databricks-sql-connector,
# MAGIC >   streamlit, pandas.*
# MAGIC > - *`app.py`: a Streamlit page that queries
# MAGIC >   `workspace.genie_code_lab.daily_site_consumption` for rows where
# MAGIC >   `anomaly_flag = true`, with a sortable table (site_name, site_type,
# MAGIC >   business_unit_name, region_name, total_kwh, peak_kw,
# MAGIC >   deviation_pct), a sidebar date-range filter (default last 14
# MAGIC >   days), and a site-type multiselect. Auth via
# MAGIC >   `databricks.sdk.core.Config` on-behalf-of-user.*
# MAGIC >
# MAGIC > *Then create the app resource, point it at that folder, deploy it,
# MAGIC > wait for it to come up, and give me the URL."*
# MAGIC
# MAGIC Reference fallback: `solutions/sample_app/`.
# MAGIC
# MAGIC ### 2. AI/BI Dashboard
# MAGIC
# MAGIC A visual companion to the Genie space. Same data, four widgets.
# MAGIC
# MAGIC > *"Create a new AI/BI dashboard called **Energy Operations Overview**
# MAGIC > backed by `workspace.genie_code_lab.daily_site_consumption`. Add four
# MAGIC > widgets:*
# MAGIC >
# MAGIC > 1. *KPI counter — total anomalies in the last 7 days.*
# MAGIC > 2. *Bar chart — daily anomaly count over the last 30 days.*
# MAGIC > 3. *Stacked bar — anomalies by `business_unit_name` × `site_type`.*
# MAGIC > 4. *Table — top 10 (site, day) rows by `deviation_pct`.*
# MAGIC >
# MAGIC > *Add a global date-range filter and publish the dashboard."*
# MAGIC
# MAGIC ### 3. Lakeflow Job — schedule the pipeline
# MAGIC
# MAGIC Wrap the SDP you built in Part 3a in a job that runs every morning.
# MAGIC
# MAGIC > *"Create a Lakeflow Job named **energy-anomaly-daily** that runs the
# MAGIC > Energy Anomaly Pipeline (built in Part 3a) every day at 06:00 UTC.
# MAGIC > Send a notification to my email on failure. Use Serverless compute."*
# MAGIC
# MAGIC ### 4. Unity Catalog Function
# MAGIC
# MAGIC Encapsulate analyst logic as a callable SQL function that anyone in the
# MAGIC workspace can use.
# MAGIC
# MAGIC > *"Create a Unity Catalog SQL function
# MAGIC > `workspace.genie_code_lab.get_site_anomalies(site_id STRING, days INT)`
# MAGIC > that returns the rows from
# MAGIC > `workspace.genie_code_lab.daily_site_consumption` where the given
# MAGIC > site has `anomaly_flag = true` within the past N days, ordered by
# MAGIC > deviation_pct descending. Add a docstring. Then run a test query
# MAGIC > calling it for `SITE-0005` over 14 days and show me the result."*
# MAGIC
# MAGIC ### 5. Forecasting model + endpoint
# MAGIC
# MAGIC Train a per-site daily-kWh forecast and serve it.
# MAGIC
# MAGIC > *"Train a per-site daily-kWh forecasting model on
# MAGIC > `workspace.genie_code_lab.daily_site_consumption`. Use Prophet (or
# MAGIC > whichever forecasting library you think fits best). Train one model
# MAGIC > per `site_id`, log them as a single MLflow registered model, and
# MAGIC > deploy a serving endpoint that accepts `site_id` and `horizon_days`
# MAGIC > and returns the forecast. Show me sample inference output for two
# MAGIC > sites."*

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Wrap-up (2 min)
# MAGIC
# MAGIC In ~47 minutes you used Genie Code to:
# MAGIC
# MAGIC - **Explore** an unfamiliar dataset with Agent-mode EDA
# MAGIC - **Build & run** a Lakeflow Spark Declarative Pipeline
# MAGIC - **Stand up** a Genie space with joins and SQL Expressions
# MAGIC - **Customize** Genie Code's defaults with custom instructions
# MAGIC - **Encode a workflow** as a reusable Skill
# MAGIC - **Extend Genie Code's reach** by registering the Genie space as an MCP server
# MAGIC
# MAGIC The **Bonus** section above lists five more resources you can build on
# MAGIC top of `daily_site_consumption` whenever you have time — App,
# MAGIC AI/BI dashboard, scheduled Lakeflow Job, UC SQL function, and a
# MAGIC forecasting model.
# MAGIC
# MAGIC ### What to try on your own
# MAGIC
# MAGIC | Try | Where |
# MAGIC |-----|-------|
# MAGIC | `/repairEnvironment` after a failed `pip install` | Any cell after a library failure |
# MAGIC | `/rename` to clean up auto-generated cell names | A messy notebook |
# MAGIC | Genie Code in the **SQL editor** | New SQL queries — same `@`-references work |
# MAGIC | Genie Code in **Catalog Explorer** | Right-click any UC table, pick "Ask Genie" |
# MAGIC | Workspace-level instructions | `Workspace/.assistant_workspace_instructions.md` (admin) |
# MAGIC | Workspace-level skills | `Workspace/.assistant/skills/<name>/SKILL.md` (admin) |
# MAGIC | The `databricks-solutions/ai-dev-kit` repo | Curated Genie Code patterns from Field Engineering |
# MAGIC | **Other MCP server types** (Vector Search, Unity Catalog Functions, Databricks SQL, GitHub) | Settings → MCP Servers — same flow as Part 6 |
# MAGIC
# MAGIC ### References
# MAGIC
# MAGIC - [Genie Code overview](https://docs.databricks.com/aws/en/genie-code/)
# MAGIC - [Use Genie Code](https://docs.databricks.com/aws/en/genie-code/use-genie-code)
# MAGIC - [Custom instructions](https://docs.databricks.com/aws/en/genie-code/instructions)
# MAGIC - [Agent skills](https://docs.databricks.com/aws/en/genie-code/skills)
# MAGIC - [Connect Genie Code to MCP servers](https://docs.databricks.com/aws/en/genie-code/mcp)
# MAGIC - [Slash command reference](https://docs.databricks.com/aws/en/notebooks/code-assistant)
# MAGIC
# MAGIC Thanks for coming! Questions?
