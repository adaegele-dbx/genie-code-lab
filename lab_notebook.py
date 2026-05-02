# Databricks notebook source

# MAGIC %md
# MAGIC # Hands-On with Genie Code
# MAGIC ### A 45-50 minute lab
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
# MAGIC | **Setup** | Seed three energy tables, open Genie Code, confirm Agent mode | ~3 min |
# MAGIC | **Part 1** | Genie Code 101 — chat, `@`-references, `Cmd+I`, slash commands | ~4 min |
# MAGIC | **Part 2** | Agent-mode EDA — one prompt, watch it plan and run | ~5 min |
# MAGIC | **Part 3a** | Build & run a **Lakeflow Spark Declarative Pipeline** | ~8 min |
# MAGIC | **Part 3b** | Create a **Genie space** over the gold table | ~5 min |
# MAGIC | **Part 3c** | Deploy a **Databricks App** (Streamlit) showing anomalies | ~7 min |
# MAGIC | **Part 4** | Improve what you built — `/optimize`, `/doc`, "make it incremental" | ~4 min |
# MAGIC | **Part 5** | Customize Genie Code with **custom instructions** | ~5 min |
# MAGIC | **Part 6** | Customize Genie Code with a **Skill** | ~6 min |
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
# MAGIC - **Free Edition limit:** 1 active Databricks App. If you have an old app
# MAGIC   from another lab, delete it before Part 3c.
# MAGIC
# MAGIC > Run each cell with `Shift + Enter` and read the markdown between them —
# MAGIC > the lab instructions live in the markdown.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Setup — Seed the energy data
# MAGIC
# MAGIC The cell below creates `workspace.genie_code_lab` and populates it with
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
# MAGIC SELECT 'regions' AS table_name, COUNT(*) AS row_count FROM workspace.genie_code_lab.regions
# MAGIC UNION ALL
# MAGIC SELECT 'business_units', COUNT(*) FROM workspace.genie_code_lab.business_units
# MAGIC UNION ALL
# MAGIC SELECT 'sites', COUNT(*) FROM workspace.genie_code_lab.sites
# MAGIC UNION ALL
# MAGIC SELECT 'meter_readings', COUNT(*) FROM workspace.genie_code_lab.meter_readings

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
# MAGIC Try each of the following — they're all quick.
# MAGIC
# MAGIC ### 1a. Chat with notebook context
# MAGIC
# MAGIC In the Genie Code panel, ask:
# MAGIC
# MAGIC > *"What is this notebook for?"*
# MAGIC
# MAGIC The current notebook is auto-attached as context — Genie Code can read
# MAGIC the markdown and code cells.
# MAGIC
# MAGIC ### 1b. `@`-reference a table
# MAGIC
# MAGIC In the chat box, type `@` and start typing `meter_readings`. Genie Code
# MAGIC will autocomplete table names from Unity Catalog.  Pick `meter_readings`,
# MAGIC then ask:
# MAGIC
# MAGIC > *"How many rows are in `@meter_readings` and what's the date range?"*
# MAGIC
# MAGIC ### 1c. Inline prompt with `Cmd+I` / `Ctrl+I`
# MAGIC
# MAGIC Click into the empty cell below, then press **`Cmd+I`** (Mac) or
# MAGIC **`Ctrl+I`** (Windows). A prompt box appears inside the cell. Type:
# MAGIC
# MAGIC > *"Show the schema of all four tables in workspace.genie_code_lab as
# MAGIC > one combined SQL output."*
# MAGIC
# MAGIC Press `Enter` to generate, then accept the suggestion to fill the cell.

# COMMAND ----------

# Try the inline `Cmd+I` / `Ctrl+I` prompt here.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1d. Slash commands
# MAGIC
# MAGIC In the Genie Code chat box, type `/` to open the slash-command menu.
# MAGIC The full set of commands is documented in the
# MAGIC [Genie Code docs](https://docs.databricks.com/aws/en/notebooks/code-assistant);
# MAGIC try a few now:
# MAGIC
# MAGIC | Command | What to try |
# MAGIC |---------|-------------|
# MAGIC | `/findTables` | `/findTables energy consumption` |
# MAGIC | `/findQueries` | `/findQueries top consumers` |
# MAGIC | `/explain` | Click into the SQL cell from 1c, then run `/explain` |
# MAGIC | `/prettify` | Run on any cell that has working but ugly code |
# MAGIC
# MAGIC ### 1e. Autocomplete
# MAGIC
# MAGIC Click into the empty Python cell below and start typing:
# MAGIC
# MAGIC ```python
# MAGIC df = spark.table("workspace.genie_code_lab.
# MAGIC ```
# MAGIC
# MAGIC You should see Genie Code propose the rest of the line. Press **`Tab`** to
# MAGIC accept. Try a few more lines — autocomplete kicks in continuously as you type.
# MAGIC
# MAGIC ✅ **Part 1 checkpoint:** you've used chat, `@`-references, inline prompts,
# MAGIC slash commands, and autocomplete. Move on.

# COMMAND ----------

# Try autocomplete here. Start typing:
#   df = spark.table("workspace.genie_code_lab.

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
# MAGIC ## Part 3 — Build with Agent mode (20 min)
# MAGIC
# MAGIC This is the heart of the lab. You'll build three artifacts back-to-back,
# MAGIC each with a single Agent-mode prompt:
# MAGIC
# MAGIC 1. **3a — A Lakeflow Spark Declarative Pipeline** that produces a daily
# MAGIC    per-site gold table with a 2σ anomaly flag.
# MAGIC 2. **3b — A Genie space** over the gold table for natural-language Q&A.
# MAGIC 3. **3c — A Databricks App** (Streamlit) that lists anomalies with a
# MAGIC    date filter.
# MAGIC
# MAGIC Each sub-step has its own checkpoint — don't move on until the previous
# MAGIC artifact ran.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Part 3a — Build & run the SDP pipeline (8 min)
# MAGIC
# MAGIC **Goal:** A `daily_site_consumption` table with one row per (site, day)
# MAGIC and an `anomaly_flag` column.
# MAGIC
# MAGIC #### Step 1 — Have Genie Code generate the pipeline source
# MAGIC
# MAGIC In the Genie Code chat panel, paste:
# MAGIC
# MAGIC > *"In a new file at `pipeline/energy_pipeline.py`, write a Lakeflow
# MAGIC > Spark Declarative Pipeline that:*
# MAGIC >
# MAGIC > 1. *Reads `@meter_readings` as a silver table, dropping rows where
# MAGIC >    `status = 'error'`.*
# MAGIC > 2. *Joins to `@sites`, `@regions`, and `@business_units` for site,
# MAGIC >    region, and business unit metadata.*
# MAGIC > 3. *Produces a daily per-site gold table called
# MAGIC >    `daily_site_consumption` with columns: `site_id`, `site_type`,
# MAGIC >    `business_unit_id`, `business_unit_name`, `region_id`, `region_name`,
# MAGIC >    `reading_date`, `total_kwh`, `peak_kw`, `avg_voltage`, `warning_count`.*
# MAGIC > 4. *Adds an `anomaly_flag` column that is `true` when the day's
# MAGIC >    `total_kwh` is more than 2 standard deviations above that site's
# MAGIC >    30-day mean.*
# MAGIC >
# MAGIC > *Use `dlt` decorators and PySpark. Target catalog `workspace`, schema
# MAGIC > `genie_code_lab`."*
# MAGIC
# MAGIC Watch Agent mode plan, write the file, and validate it. The result
# MAGIC should be a `pipeline/energy_pipeline.py` file in this Git folder.
# MAGIC
# MAGIC #### Step 2 — Create the pipeline
# MAGIC
# MAGIC 1. In the left sidebar, click **New** → **ETL Pipeline**.
# MAGIC 2. Name it: `Energy Anomaly Pipeline`.
# MAGIC 3. **Source code:** point at `pipeline/energy_pipeline.py` in this Git folder.
# MAGIC 4. **Destination:** catalog `workspace`, schema `genie_code_lab`.
# MAGIC 5. Use **Serverless** compute.
# MAGIC 6. Click **Create**.
# MAGIC
# MAGIC #### Step 3 — Run it
# MAGIC
# MAGIC Click **Start** in the pipeline editor. Cold start can take 30-60 seconds
# MAGIC on Free Edition; the run itself should be quick.
# MAGIC
# MAGIC #### Step 4 — Verify the gold table
# MAGIC
# MAGIC Once the pipeline is green, run the cell below to confirm the table
# MAGIC exists and has anomaly rows.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   COUNT(*)                                         AS total_rows,
# MAGIC   COUNT_IF(anomaly_flag)                           AS anomaly_rows,
# MAGIC   COUNT(DISTINCT site_id)                          AS sites_covered,
# MAGIC   MIN(reading_date)                                AS first_date,
# MAGIC   MAX(reading_date)                                AS last_date
# MAGIC FROM workspace.genie_code_lab.daily_site_consumption

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
# MAGIC ### Part 3b — Create a Genie space (5 min)
# MAGIC
# MAGIC **Goal:** A natural-language Q&A interface over the gold table.
# MAGIC
# MAGIC #### Step 1 — Create the space
# MAGIC
# MAGIC 1. In the left sidebar, click **Genie**.
# MAGIC 2. Click **+ New** → **Genie space**.
# MAGIC 3. Name it: `Energy Operations`.
# MAGIC 4. Add tables:
# MAGIC    - `workspace.genie_code_lab.daily_site_consumption`
# MAGIC    - `workspace.genie_code_lab.sites`
# MAGIC    - `workspace.genie_code_lab.regions`
# MAGIC    - `workspace.genie_code_lab.business_units`
# MAGIC 5. Click **Create**.
# MAGIC
# MAGIC #### Step 2 — Have Genie Code suggest a description
# MAGIC
# MAGIC Back in the notebook, ask Genie Code:
# MAGIC
# MAGIC > *"Suggest a one-paragraph description for a Genie space over
# MAGIC > `@daily_site_consumption` focused on energy-anomaly investigation.
# MAGIC > Mention the meaning of the `anomaly_flag` column and that the table
# MAGIC > already carries `business_unit_name` and `region_name` for grouping."*
# MAGIC
# MAGIC Copy the output into the **Description** field of your Genie space
# MAGIC (top of the space's settings panel). Save.
# MAGIC
# MAGIC #### Step 3 — Ask three NL questions
# MAGIC
# MAGIC In the Genie space chat box, ask:
# MAGIC
# MAGIC 1. *"Which business unit had the most anomalies last week?"*
# MAGIC 2. *"Show me the top 5 sites by total kWh in the past 14 days."*
# MAGIC 3. Pick a flagged site from the verify query in 3a (any row where
# MAGIC    `anomaly_flag = true`) and ask:
# MAGIC    *"For SITE-XXXX, what's the daily kWh trend?"*
# MAGIC
# MAGIC Click **Show generated code** on each answer to see the SQL Genie wrote.
# MAGIC
# MAGIC > **Stuck?** If your space gives bad answers, paste the description and
# MAGIC > tuning hints from `solutions/sample_genie_instructions.md` into the
# MAGIC > space's instructions.
# MAGIC
# MAGIC ✅ **Part 3b checkpoint:** three questions answered, you've seen the
# MAGIC SQL each one generated. Move on.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Part 3c — Deploy a Databricks App (7 min)
# MAGIC
# MAGIC **Goal:** A 1-page Streamlit app that lists anomalous sites with a
# MAGIC date-range filter. Free Edition supports one running app at a time.
# MAGIC
# MAGIC #### Step 1 — Create the app from the Streamlit template
# MAGIC
# MAGIC 1. In the left sidebar, click **Compute** → **Apps** → **Create app**.
# MAGIC 2. Pick the **Streamlit** template.
# MAGIC 3. Name it: `energy-anomaly-viewer`.
# MAGIC 4. Click **Create**.
# MAGIC 5. Once the app is provisioned, click **Edit code** to open the source
# MAGIC    files in the workspace file editor.
# MAGIC
# MAGIC #### Step 2 — Have Genie Code rewrite `app.py`
# MAGIC
# MAGIC With the app's `app.py` open in the file editor, open the Genie Code
# MAGIC panel and prompt:
# MAGIC
# MAGIC > *"Replace the contents of `app.py` with a Streamlit page that queries
# MAGIC > `workspace.genie_code_lab.daily_site_consumption` for rows where
# MAGIC > `anomaly_flag = true`. Add a sidebar date-range filter and a sortable
# MAGIC > table that includes site_name, site_type, business_unit_name, and
# MAGIC > region_name. Use the databricks-sql-connector with on-behalf-of-user
# MAGIC > auth via `databricks.sdk.core.Config`. Read `DATABRICKS_WAREHOUSE_ID`
# MAGIC > from the environment."*
# MAGIC
# MAGIC #### Step 3 — Configure the warehouse env var
# MAGIC
# MAGIC 1. Open `app.yaml` in the file editor.
# MAGIC 2. Add (or update) the `env` block to include your warehouse ID:
# MAGIC
# MAGIC    ```yaml
# MAGIC    command: ["streamlit", "run", "app.py"]
# MAGIC    env:
# MAGIC      - name: "DATABRICKS_WAREHOUSE_ID"
# MAGIC        value: "<paste your warehouse ID here>"
# MAGIC    ```
# MAGIC
# MAGIC    Find your warehouse ID under **SQL warehouses** in the sidebar — copy
# MAGIC    the ID from the URL or the warehouse details panel.
# MAGIC
# MAGIC #### Step 4 — Deploy and open
# MAGIC
# MAGIC 1. Save both files.
# MAGIC 2. From the app page, click **Deploy** (this may take ~30-60 s).
# MAGIC 3. Click the app URL once it's marked "Running".
# MAGIC 4. Verify you see the anomaly list and that the date filter changes the
# MAGIC    rows.
# MAGIC
# MAGIC > **Stretch:** ask Genie Code:
# MAGIC > *"Add a bar chart above the table showing the count of anomalies per
# MAGIC > day in the selected date range."*
# MAGIC
# MAGIC > **Stuck?** Copy the contents of `solutions/sample_app/` (`app.py`,
# MAGIC > `app.yaml`, `requirements.txt`) into your app's source files,
# MAGIC > replacing the warehouse ID placeholder. Re-deploy.
# MAGIC
# MAGIC ✅ **Part 3 checkpoint:** pipeline runs, Genie space answers questions,
# MAGIC app shows anomalies. You've built the analytics stack.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 4 — Improve what you built (4 min)
# MAGIC
# MAGIC Now go back to `pipeline/energy_pipeline.py` and use Genie Code to
# MAGIC sharpen what you have. Try each of the three:
# MAGIC
# MAGIC ### 4a. `/optimize` a function
# MAGIC
# MAGIC Click into the daily aggregation function. In the Genie Code chat box,
# MAGIC type `/optimize` and press Enter. Review the proposed change in the diff
# MAGIC view; **Accept** if it looks good, **Reject** otherwise.
# MAGIC
# MAGIC ### 4b. `/doc` to add docstrings
# MAGIC
# MAGIC Click into the `silver_readings` function. Run `/doc`. A docstring will
# MAGIC be inserted in diff view; accept or reject.
# MAGIC
# MAGIC ### 4c. Make it incremental
# MAGIC
# MAGIC Ask Genie Code:
# MAGIC
# MAGIC > *"Make the daily_site_consumption table incremental — only reprocess
# MAGIC > the last 7 days, not the full window. Use a streaming source if
# MAGIC > appropriate."*
# MAGIC
# MAGIC The agent will rewrite the file. Re-run the pipeline to confirm it still
# MAGIC works (it'll be faster on the second run thanks to the smaller window).
# MAGIC
# MAGIC ✅ **Part 4 checkpoint:** you've used three different "improve" features
# MAGIC on code Genie Code wrote moments ago. Move on.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 5 — Customize Genie Code with custom instructions (5 min)
# MAGIC
# MAGIC Genie Code's defaults are good. Your team's defaults are better.
# MAGIC In this part you'll see how a small markdown file changes Genie Code's
# MAGIC output style for every prompt you give it from then on.
# MAGIC
# MAGIC ### 5a. Run a baseline prompt
# MAGIC
# MAGIC In the Genie Code chat box (open a fresh thread first — bottom-left
# MAGIC corner of the panel, **+ New thread**), paste:
# MAGIC
# MAGIC > *"Write a small PySpark function that returns the top N sites by
# MAGIC > total kWh for a given month, grouped by business unit. Use
# MAGIC > `@daily_site_consumption`."*
# MAGIC
# MAGIC Read what it produces. Note: variable names, comment style, whether it
# MAGIC uses type hints, whether it aliases `pyspark.sql.functions`, whether it
# MAGIC uses CTEs vs. subqueries, etc. **Don't run it yet.** We're going to
# MAGIC compare.
# MAGIC
# MAGIC ### 5b. Add custom instructions
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
# MAGIC ### 5c. Re-run the same prompt
# MAGIC
# MAGIC Open a **new thread** in the Genie Code panel (so the previous run
# MAGIC doesn't anchor the response). Paste the **same baseline prompt** from
# MAGIC 5a:
# MAGIC
# MAGIC > *"Write a small PySpark function that returns the top N sites by
# MAGIC > total kWh for a given month, grouped by business unit. Use
# MAGIC > `@daily_site_consumption`."*
# MAGIC
# MAGIC ### 5d. Diff the outputs
# MAGIC
# MAGIC Compare the two responses. You should see:
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
# MAGIC ✅ **Part 5 checkpoint:** before/after comparison, instructions saved.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 6 — Customize Genie Code with a Skill (6 min)
# MAGIC
# MAGIC Custom instructions are global. **Skills** are narrow, reusable
# MAGIC workflows that Agent mode auto-loads when the user's request matches.
# MAGIC In this part you'll create a small "anomaly triage" skill and watch
# MAGIC Agent mode pick it up.
# MAGIC
# MAGIC ### 6a. Create the skill folder
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
# MAGIC ### 6b. Paste the skill content
# MAGIC
# MAGIC Open `solutions/sample_skill/SKILL.md` in this Git folder and copy its
# MAGIC entire contents (including the YAML frontmatter at the top). Paste into
# MAGIC the new `SKILL.md` file. Save.
# MAGIC
# MAGIC ### 6c. Trigger the skill by intent
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
# MAGIC ### 6d. (Stretch) Force the skill explicitly
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
# MAGIC ✅ **Part 6 checkpoint:** skill triggered, structured report produced.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Wrap-up (2 min)
# MAGIC
# MAGIC In ~50 minutes you used Genie Code to:
# MAGIC
# MAGIC - **Explore** an unfamiliar dataset with Agent-mode EDA
# MAGIC - **Build & run** a Lakeflow Spark Declarative Pipeline
# MAGIC - **Stand up** a Genie space for natural-language Q&A
# MAGIC - **Deploy** a Databricks App
# MAGIC - **Improve** the code with `/optimize`, `/doc`, and chat
# MAGIC - **Customize** Genie Code's defaults with custom instructions
# MAGIC - **Encode a workflow** as a reusable Skill
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
# MAGIC
# MAGIC ### References
# MAGIC
# MAGIC - [Genie Code overview](https://docs.databricks.com/aws/en/genie-code/)
# MAGIC - [Use Genie Code](https://docs.databricks.com/aws/en/genie-code/use-genie-code)
# MAGIC - [Custom instructions](https://docs.databricks.com/aws/en/genie-code/instructions)
# MAGIC - [Agent skills](https://docs.databricks.com/aws/en/genie-code/skills)
# MAGIC - [Slash command reference](https://docs.databricks.com/aws/en/notebooks/code-assistant)
# MAGIC
# MAGIC Thanks for coming! Questions?
