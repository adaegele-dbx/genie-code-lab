# Hands-On with Genie Code — Lab Design Spec

> Status: design / pre-implementation
> Date: 2026-05-02
> Target environment: Databricks Free Edition
> Target duration: ~47 minutes core (plus optional Bonus section attendees can pick up later)

---

## 1. Purpose

A guided, hands-on lab that walks attendees through Databricks **Genie Code** end-to-end, showing how to use it to accelerate real Databricks work. Attendees leave the session having used Genie Code to:

1. Explore an unfamiliar dataset
2. Build and run a production-shaped ETL pipeline
3. Stand up a Genie space for natural-language Q&A
4. Deploy a small Databricks App
5. Customize Genie Code's behavior with markdown — both via custom instructions and a reusable Skill

The lab follows the same structural conventions as the existing `ai-bi-dashboards-and-genie/` and `lakeflow-jobs-and-ci-cd/` labs in `~/projects/enablement/`.

---

## 2. Audience & assumptions

- **Mixed-experience audience**, leaning toward "familiar with Databricks, new to AI/agentic workflows." Few experienced practitioners; most will be using Genie Code for the first time.
- Attendees self-pace through the notebook with Antony narrating and unblocking.
- Each attendee runs in their own Databricks Free Edition workspace.
- Free Edition constraints that shape the design:
  - 1 SQL warehouse (2X-Small)
  - 1 active Lakeflow Spark Declarative Pipeline per type
  - 1 Databricks App, runs up to 24h after start
  - Unity Catalog enabled by default, single `workspace` catalog

Attendees do **not** need prior exposure to Genie Code, agentic AI, Spark Declarative Pipelines, Genie spaces, or Databricks Apps. They do need basic comfort with running notebook cells.

---

## 3. What attendees build

| Artifact | Where it lives | Built in |
|---|---|---|
| 4 UC tables: `regions`, `business_units`, `sites`, `meter_readings` | `workspace.genie_code_lab` | Setup |
| Lakeflow SDP pipeline producing `daily_site_consumption` (with 2σ-anomaly flag) | `workspace.genie_code_lab` | Part 3a |
| Genie space over the gold table (with joins and SQL Expressions) | Workspace > Genie | Part 3b |
| Two notebooks for instruction diff: `top_consumers_baseline`, `top_consumers_with_instructions` | `/Users/<me>/` | Part 4 |
| `.assistant_instructions.md` user instructions file | `/Users/<me>/` | Part 4 |
| `.assistant/skills/anomaly-triage/SKILL.md` | `/Users/<me>/.assistant/skills/` | Part 5 |
| Managed Genie MCP server registration pointing at the **Energy Operations** space | Genie Code Settings → MCP Servers | Part 6 |

---

## 4. Dataset: industrial IoT energy meter readings (one company, 10 sites)

The scenario throughout the lab: the attendee is on the energy operations team
of a single industrial company that owns 10 physical sites across the US. No
customer table — the operator IS the company. Two dimension tables (`regions`,
`business_units`) sit alongside `sites` to give Genie/EDA meaningful slice-by
axes.

### Schema

`workspace.genie_code_lab.regions` — 5 rows
| Column | Type | Notes |
|---|---|---|
| `region_id` | STRING | PK, e.g. `R-NE` |
| `region_name` | STRING | `Northeast`, `Southeast`, `Midwest`, `West`, `Southwest` |
| `timezone` | STRING | IANA tz, e.g. `America/New_York` |

`workspace.genie_code_lab.business_units` — 5 rows
| Column | Type | Notes |
|---|---|---|
| `business_unit_id` | STRING | PK, e.g. `BU-MFG` |
| `business_unit_name` | STRING | `Manufacturing`, `Logistics & Distribution`, `Corporate & Office`, `R&D / Data Centers`, `Retail Operations` |
| `description` | STRING | one-line BU description |

`workspace.genie_code_lab.sites` — 10 rows
| Column | Type | Notes |
|---|---|---|
| `site_id` | STRING | PK, e.g. `SITE-0001` |
| `site_name` | STRING | descriptive (e.g. `Boston Manufacturing Plant`) |
| `site_type` | STRING | `factory` / `warehouse` / `office` / `data_center` / `retail` |
| `business_unit_id` | STRING | FK → business_units |
| `region_id` | STRING | FK → regions |
| `city` | STRING | |
| `state` | STRING | 2-letter |
| `square_footage` | INT | 18k–300k |
| `installation_date` | DATE | when meter commissioned |
| `voltage_nominal` | INT | 480 |

`workspace.genie_code_lab.meter_readings` — ~29k rows (10 sites × 30 days × 96 intervals)
| Column | Type | Notes |
|---|---|---|
| `reading_id` | STRING | PK |
| `site_id` | STRING | FK → sites |
| `reading_timestamp` | TIMESTAMP | 15-min interval, last 30 days |
| `kwh_consumed` | DOUBLE | per-interval consumption |
| `kw_demand` | DOUBLE | peak demand in interval |
| `voltage` | DOUBLE | nominally 480 (with ±2% noise) |
| `temperature_c` | DOUBLE | ambient |
| `status` | STRING | `normal` / `warning` / `error` |

### Generation strategy

Use PySpark in `data/setup_tables.py` to generate the data with deterministic seeds. Patterns built into the data so EDA is interesting:

- **Site types vary widely** in absolute consumption (data centers and factories ~10× retail/office)
- **Hourly seasonality** — load peaks 9 am – 6 pm, troughs overnight
- **2 sites are anomalous** with multi-day intentional spikes (`SITE-0005`, `SITE-0010`) — gives Part 3a's 2σ flag something real to find without "seeding mess"
- **~5% warning / ~1% error status** rows scattered across all sites
- Total seed time target: **< 10 seconds** on Free Edition

No NULL pollution, no schema drift, no broken types — the data is clean (per the user direction to not deliberately seed messy artifacts). The only "imperfections" are organic patterns the analyst would naturally explore.

### Naming hygiene

No real or quasi-real customer names anywhere. Site names are descriptive
(`Boston Manufacturing Plant`, `Atlanta Distribution Center`); IDs use
unambiguously-synthetic prefixes (`R-`, `BU-`, `SITE-`, `R-` reading prefix).
Safe for a public repo.

---

## 5. Lab outline (49 min budget)

### Setup — 3 min
- Declare the catalog widget (default `workspace`); seed runs against that catalog.
- Run `%run ./data/setup_tables`; verify row counts.
- Open Genie Code panel **outside this notebook** (workspace home or a fresh
  notebook) so Agent mode doesn't add cells to the lab notebook.
- Confirm Agent mode is **on**.

### Part 1 — Genie Code 101 (4 min)
Ground attendees in the basic surface area before going autonomous.
- **Agent vs Chat:** flip to Chat, ask *"What's the difference between Agent mode and Chat mode in Genie Code?"*, flip back.
- **`@table` reference:** ask *"How many rows are in @meter_readings and what's the date range?"*
- **Slash commands quick tour:** `/findTables energy consumption`, `/findQueries top consumers`, `/explain` on a SQL cell.
- **Feedback affordances:** thumbs-up / thumbs-down (with text), `⋯` → Report a bug.
- **New chat:** show the **+ New chat** button to clear conversation history.

### Part 2 — Agent-mode EDA (5 min)
One prompt, observe the agent.
- Prompt: *"Perform exploratory data analysis on @meter_readings. Join in @sites, @regions, and @business_units as needed. Summarize the most interesting patterns and anomalies as a markdown report at the end."*
- Discussion prompt for the room: *"What did Agent mode do that you would have done differently? Where did it surprise you?"*

### Part 3a — Build & run an SDP pipeline (9 min)
**Goal:** A `daily_site_consumption` gold table with a 2σ-anomaly flag — created entirely by Agent mode.

1. Single prompt that asks Genie Code to: write `pipeline/energy_pipeline.py`, create the pipeline resource, point it at the source, and **not run it yet**.
2. Ask Genie Code to **dry-run** (validate); fix any errors and re-validate.
3. Ask Genie Code to do a **full run** and report when the gold table is populated.
4. Verify table existence and anomaly rows via the SQL cell in the lab notebook.

**Stretch:** ask Genie Code to add a `@dlt.expect_or_drop` for non-negative `kwh_consumed` and re-run.

**Solutions fallback:** `solutions/sample_pipeline.py`.

### Part 3b — Create a Genie space (7 min)
**Goal:** NL Q&A over the gold table, with Genie Code creating the space, joins, and SQL Expressions.

1. Prompt Genie Code to **create the space** named `Energy Operations` with the four tables and a one-paragraph description.
2. Prompt Genie Code to **add five join relationships** (sites→regions, sites→business_units, daily_site_consumption→sites/regions/business_units).
3. Prompt Genie Code to **add three SQL Expression measures**:
   - `kwh_per_sqft` — `total_kwh / square_footage`
   - `deviation_from_baseline_pct` — window-function form: `(total_kwh - AVG(total_kwh) OVER (PARTITION BY site_id)) / AVG(total_kwh) OVER (PARTITION BY site_id) * 100`
   - `is_anomaly` — `anomaly_flag = true`
4. Ask three NL questions in the space:
   - *"Which business unit had the most anomalies last week?"*
   - *"Top 5 sites by kwh_per_sqft in the past 14 days."* (uses the SQL Expression)
   - *"For SITE-XXXX, what's the daily kWh trend and how does it compare to its baseline?"* (uses the deviation expression)

**Solutions fallback:** `solutions/sample_genie_instructions.md`.

### Part 4 — Custom instructions (6 min)
Show how the same prompt produces different results once Genie Code knows your team's preferences. **The diff is persisted by saving each output to its own notebook** so attendees can compare side by side after the lab.

1. **Baseline:** prompt Genie Code to *write a small PySpark function returning top N sites by kWh grouped by business unit, using @daily_site_consumption*, **save it to a new notebook named `top_consumers_baseline` in the user's workspace home folder**, and not run anything.
2. Add `.assistant_instructions.md` from `solutions/sample_assistant_instructions.md`.
3. **After:** re-run the same prompt in a new chat, **save to `top_consumers_with_instructions`**.
4. Diff the two notebooks side by side.

### Part 5 — Custom Skill (6 min)
Show the Skill mechanism — narrowly scoped, auto-triggered.

### Part 6 — MCP server (5 min)
Show the third customization mechanism: registering an MCP server. Use the
Managed Genie MCP server type to expose the **Energy Operations** Genie
space (built in Part 3b) as a callable tool. Then issue a prompt that
exercises the SQL Expressions defined in the space (`kwh_per_sqft`,
`deviation_from_baseline_pct`) — those are not raw columns, so a correct
answer is strong evidence Genie Code routed through the MCP.

UI flow: Genie Code panel → gear icon → MCP Servers tab → + → Genie Space
→ pick "Energy Operations" → Save. MCPs are limited to 20 tools across all
servers; one Genie space = one tool.

Demo prompt: *"Use the Energy Operations Genie space to find the top 3
sites by `kwh_per_sqft` over the last 14 days, and for each one, tell me
its business unit and `deviation_from_baseline_pct` for that period."*

### Bonus — Build more on your own (optional)
Closes the lab with five copy-paste prompts attendees can run on their own
to extend the work. Resource menu:

1. **Databricks App** (Streamlit) — anomaly viewer. Reference fallback in `solutions/sample_app/`.
2. **AI/BI Dashboard** — four widgets (KPI counter, daily bar, stacked bar by BU×site_type, top-10 table) over the gold table.
3. **Lakeflow Job** — schedules the SDP from Part 3a daily at 06:00 UTC with failure email.
4. **Unity Catalog Function** — `get_site_anomalies(site_id, days)` returns ranked anomalies; demonstrates encapsulating analyst logic.
5. **Forecasting model + endpoint** — per-site daily-kWh Prophet (or equivalent), logged via MLflow, served behind an endpoint.

Each item is one Agent-mode prompt. Not part of the timed lab — attendees pick whichever resonates.

1. Create the directory & file: `/Users/<me>/.assistant/skills/anomaly-triage/SKILL.md`
2. Paste the skill content (provided in lab text and `solutions/sample_skill/SKILL.md`):
   ```markdown
   ---
   name: anomaly-triage
   description: Triages anomalous energy-consumption sites by enriching with business-unit and region context, comparing to historical baseline, and proposing 2-3 likely causes.
   ---

   When the user asks to investigate an anomalous site or list of sites:

   1. Pull the rows from `workspace.genie_code_lab.daily_site_consumption` where `anomaly_flag = true` for the requested window.
   2. Use the `business_unit_name` and `region_name` already on the gold table; join `sites` for site_name, city, state, square_footage.
   3. For each anomalous (site, day), use the `deviation_pct` column (already produced by the pipeline).
   4. Group findings by business_unit_name and produce a short markdown report:
      - One-line summary of anomalies found
      - Top 3 sites ranked by deviation
      - For each, propose 2 plausible causes drawing from site_type, square_footage, weather (temperature_c), and recent error counts.
   5. End the report with a "next steps" section suggesting which sites warrant human follow-up.
   ```
3. **Trigger by intent:** prompt *"Investigate yesterday's energy anomalies and tell me what to look at."* — observe Agent mode picking up the skill (Genie Code surfaces "Used skill: anomaly-triage" in its trace).

### Wrap-up (2 min)
- Recap: end-to-end built with one assistant
- Pointers: other slash commands (`/repairEnvironment`, `/prettify`, `/rename`), other surfaces (SQL editor, MLflow, Catalog Explorer), workspace-level instructions for team rollout, the `databricks-solutions/ai-dev-kit` repo for advanced patterns
- Q&A

---

## 6. Repo structure

```
genie-code/
├── README.md                              # overview, prerequisites, structure, lab outline
├── PLAN.md                                # this design doc (kept for future-you)
├── lab_notebook.py                        # central guided notebook — entry point
│
├── data/
│   └── setup_tables.py                    # generates 4 UC tables (regions, business_units, sites, meter_readings)
│
├── pipeline/                              # empty at start; attendees write here in Part 3a
│   └── .gitkeep
│
└── solutions/
    ├── README.md                          # "use these only as fallback"
    ├── sample_pipeline.py                 # reference SDP definition for Part 3a
    ├── sample_genie_instructions.md       # reference Genie space description + tuning for Part 3b
    ├── sample_app/                        # reference Databricks App — used by the Bonus task
    │   ├── app.yaml
    │   └── app.py
    ├── sample_assistant_instructions.md   # reference custom instructions for Part 4
    ├── sample_skill/
    │   └── SKILL.md                       # reference skill for Part 5
    └── reference_prompts.md               # all suggested prompts collected in one place
```

---

## 7. Design choices & rationale

- **Lakeflow SDP over plain notebook ETL**: more realistic for production work, and Genie Code's SDP-generation is one of the more impressive Agent-mode demos. Costs ~2 extra min vs. a raw notebook ETL — worth it.
- **Genie space + app, not a dashboard**: the existing `ai-bi-dashboards-and-genie` lab covers dashboards thoroughly. Apps are newer and more novel; pairing a Genie space with an app shows two different "consumer-facing" surfaces.
- **Agent mode required from Part 2 onward**: the lab is fundamentally about agentic Genie Code. Setup explicitly toggles it on so nobody silently runs Chat-mode through Part 3.
- **Solutions are fallback, not script**: attendees prompt Genie Code in their own words. The solutions folder exists for (a) attendees who fall behind, (b) post-lab study, (c) Antony to lean on if a particular run goes off-rails. The lab text never says "copy this exact code" — it says "ask Genie Code to do X, and if you get stuck, see `solutions/X`."
- **Per-part checkpoints in Part 3**: between 3a → 3b → 3c, the notebook has a "verify before continuing" cell. Slow attendees can resync without dragging the room.
- **Customization (Parts 5 + 6) at the end, not the start**: attendees first need to feel Genie Code's defaults to appreciate why customization matters. The before/after demo only lands if they've internalized the "before."
- **No deliberate broken/messy seed**: per user direction. The lab works with whatever Genie Code produces in real time — a more honest narrative than fixing artificial brokenness.

---

## 8. Risks & mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Agent mode produces non-deterministic output that doesn't match what we expect | High | Lab text uses *intent-based* prompts; never says "the output should be X." Solutions folder has a known-good fallback. |
| Genie Code Agent mode generates a pipeline that doesn't run on first try | Medium | Part 3a's dry-run step catches this before a full run — fixing the agent's own output during validation is itself a teachable moment. `solutions/sample_pipeline.py` is known-good as a last resort. |
| Free Edition serverless cold-start delays Part 3a pipeline run by 30-60 s | Medium | Lab text warns; Part 3a is sized to absorb a 60 s wait. |
| Streamlit app deploy fails (auth, dependencies) — for attendees who try the Bonus App task | Low | `solutions/sample_app/` is known-good and copy-pasteable. Bonus text points attendees there if the agent's deploy fails. |
| `.assistant/skills/` directory path differs slightly across regions/clouds | Low | Lab text references "Genie Code settings → Workspace skills" UI path as the source of truth, not the literal path. |
| Genie space NL questions return wrong SQL on a fresh space | Medium | Solutions/sample_genie_instructions.md has a tested description and instruction set; lab tells attendee to paste this if their first 2 questions fail. |
| Free Edition app limit (1 running) causes attendee to hit a previously-deployed app | Low | Setup checklist tells attendee to delete any other running app before starting. |
| Time overrun on Part 3 | High | Each sub-step has explicit minute budget; stretch tasks are clearly labeled "if time permits." Setup widget defaults the catalog to `workspace`, so Free Edition runs need no extra steps; users running in fuller workspaces just change the widget. |
| Free Edition daily compute quota exhausted before lab end | High | Documented prominently in README + lab notebook prerequisites. Pipeline is sized small (~29k rows) so a single full run is cheap. Re-running the pipeline multiple times is the most likely culprit — lab text discourages it. |

---

## 9. Acceptance criteria

The lab is "done" when:

1. **Setup completes in < 60 s** on a fresh Free Edition workspace from a brand-new git folder clone.
2. **All four UC tables exist** with row counts within ~5% of targets.
3. The **`solutions/sample_pipeline.py`** reference produces a `daily_site_consumption` table with `anomaly_flag = true` rows when run end-to-end.
4. The **`solutions/sample_app/`** reference (used only by the Bonus App task) deploys cleanly on Free Edition Apps and renders the anomaly list.
5. **`solutions/sample_skill/SKILL.md`** triggers when the prompt *"Investigate yesterday's energy anomalies"* is given to Genie Code in Agent mode (verified by the "Used skill" indicator).
6. **A dry-run of the full lab** — Antony or a test attendee runs the entire `lab_notebook.py` core (Setup → Part 6) start-to-finish with Genie Code in Agent mode, hits all checkpoints, and finishes in 47 min ± 5 min. Bonus tasks are not part of acceptance.
7. **README.md** matches the structural pattern of the existing `ai-bi-dashboards-and-genie/README.md`.
8. **No reference to fictitious Genie Code features** — every slash command, capability, and UI element mentioned in the notebook exists in the live Databricks docs as of 2026-05.

---

## 10. Out of scope (explicit non-goals)

- **"Improve what you built" sub-section** (`/optimize`, `/doc`, "make it incremental") — cut after dry-run testing showed no time for it within the 50-minute budget. Keep these slash commands in mind for the wrap-up "what to try on your own" list.
- **AI/BI dashboard creation** — covered by the sibling lab; including it here would dilute focus.
- **MLflow / model serving with Genie Code** — too much surface area for the time budget; mentioned only in the wrap-up.
- **Workspace-level instructions** (`.assistant_workspace_instructions.md`) — Free Edition is single-user; user-level instructions are sufficient for the demo.
- **CI/CD with DABs around the pipeline/app** — that's the `lakeflow-jobs-and-ci-cd` lab's job.
- **Scaffolding more than one Skill** — one is enough to convey the mechanism.
- **Deep Genie space tuning** — covered by the sibling lab; here we just demonstrate creating the space + joins + a few SQL Expressions via Agent mode.
- **Snowflake/Fabric comparisons or competitive framing** — pure product enablement, no competitive content.

---

## 11. Open questions to resolve during implementation

- Final exact row counts (target ~30 / ~80 / ~230k but tune for < 60 s seed).
- Concrete list of anomalous site_ids to mention in lab examples — chosen post-data-generation to be deterministic.
- Exact naming convention for the pipeline target schema (using `workspace.genie_code_lab` to match the sibling lab convention).
- Whether to use `databricks-sql-connector` or `databricks.sdk` in the sample app — pick whatever the current Free Edition Apps Streamlit template uses.
