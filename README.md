# Hands-On with Genie Code

A 45-50 minute hands-on lab for learning **Genie Code** — Databricks' agentic
AI assistant — by using it to build a working analytics stack on top of an
IoT energy meter dataset.

## What You'll Build

By the end of this lab you will have used Genie Code to:

- **Seed and explore** four Unity Catalog tables in a small star schema:
  `regions`, `business_units`, `sites`, `meter_readings`
- **Build & run a Lakeflow Spark Declarative Pipeline** that produces a
  daily per-site gold table with an anomaly flag
- **Stand up a Genie space** over the gold table for natural-language Q&A
- **Deploy a Databricks App** (Streamlit) that lists anomalous sites with
  a date filter
- **Customize Genie Code** with both `.assistant_instructions.md` (custom
  instructions) and a `SKILL.md` agent skill — and see the before/after
  difference on the same prompt

The scenario throughout: you're on the energy operations team of an
industrial company that owns 10 sites across the US.

## Prerequisites

- A Databricks workspace (Free Edition works)
- Unity Catalog enabled (default on all workspaces)
- A SQL warehouse running (Free Edition's 2X-Small is enough)
- Free Edition users: ensure no other Databricks App is currently running
  (Free Edition allows one)

> ⚠️ **Free Edition quota:** Free Edition workspaces have a small daily
> compute quota that the SDP pipeline run (Part 3a), Genie space queries, and
> the deployed app all consume. **It is likely that you will run out of
> quota** before the end of the lab, especially if you re-run the pipeline
> several times. If everything stops responding mid-lab, that's almost
> certainly why — pick up the rest after quota resets (typically the next
> day).

> 🛑 **Run Genie Code conversations OUTSIDE the lab notebook.** Every Genie
> Code prompt in this lab should be entered from a thread that is not
> anchored to `lab_notebook.py`. Open the Genie Code panel from the workspace
> home, a fresh untitled notebook, or the SQL editor. Otherwise Agent mode
> can add cells *into the lab notebook itself* while performing tasks like
> EDA — making the lab harder to re-run.

## Getting Started

### 1. Clone this repo as a Git Folder in your Databricks workspace

1. In your Databricks workspace, go to **Workspace** in the left sidebar
2. Click **Create** → **Git folder**
3. Paste this repository's URL
4. Click **Create Git folder**

### 2. Open the lab notebook

Navigate to `lab_notebook.py` in the cloned folder and open it. All lab
instructions are inside.

---

## Repository Structure

```
genie-code/
├── README.md                              # This file
├── PLAN.md                                # Full design spec for this lab
├── lab_notebook.py                        # Central guided notebook — START HERE
│
├── data/
│   └── setup_tables.py                    # Generates the 4 UC tables
│
├── pipeline/                              # Empty at start — you'll write here in Part 3a
│   └── .gitkeep
│
└── solutions/                             # Reference fallbacks — only if Genie Code goes off-rails
    ├── README.md
    ├── sample_pipeline.py                 # Reference Lakeflow SDP
    ├── sample_genie_instructions.md       # Reference Genie space description
    ├── sample_app/                        # Reference Streamlit app
    │   ├── app.yaml
    │   ├── app.py
    │   └── requirements.txt
    ├── sample_assistant_instructions.md   # Reference custom instructions
    ├── sample_skill/
    │   └── SKILL.md                       # Reference anomaly-triage skill
    └── reference_prompts.md               # Every suggested prompt in one place
```

## Lab Outline

| Part | Topic | Time |
|------|-------|------|
| **Setup** | Seed 4 tables, open Genie Code, confirm Agent mode | ~3 min |
| **Part 1** | Genie Code 101 — chat, `@`-references, `Cmd+I`, slash commands, autocomplete | ~4 min |
| **Part 2** | Agent-mode EDA — one prompt, observe planning and iteration | ~5 min |
| **Part 3a** | Build & run a Lakeflow Spark Declarative Pipeline | ~8 min |
| **Part 3b** | Create a Genie space and ask 3 NL questions | ~5 min |
| **Part 3c** | Generate and deploy a Databricks App (Streamlit) | ~7 min |
| **Part 4** | Improve what you built — `/optimize`, `/doc`, "make it incremental" | ~4 min |
| **Part 5** | Customize Genie Code with custom instructions — same prompt before vs. after | ~5 min |
| **Part 6** | Customize Genie Code with a Skill — auto-triggered workflow | ~6 min |
| **Wrap-up** | Recap and what to try on your own | ~2 min |

**Total: ~49 minutes**

## Data Model

```
regions ─────┐
             ├──> sites ──> meter_readings   (raw, 15-min interval, 30-day window)
business_units ──┘            │
                              v
                      daily_site_consumption  (gold, built by Part 3a)
```
