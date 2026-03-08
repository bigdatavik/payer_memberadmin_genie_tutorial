# Agent Channel Genie – Payer Member Administration

A **deploy-only** Genie Room setup for **Payer Member Administration** (enrollments, eligibility, admin events, utilization). Use the Databricks Asset Bundle to **deploy to staging**; the job is **not run** by the bundle. Run the notebook manually in the workspace, then complete the room using the included guide.

**GitHub:** [bigdatavik/payer_memberadmin_genie_tutorial](https://github.com/bigdatavik/payer_memberadmin_genie_tutorial) (private)

---

## Deploy to staging (do not run the job)

This repo uses **Databricks Asset Bundles (DABs)** to deploy the Genie setup job to staging only. Deployment **does not run** the job.

1. **Prerequisites:** [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html) installed and authenticated. Copy the sample bundle config and set your workspace:
   ```bash
   cp databricks.yml.example databricks.yml
   # Edit databricks.yml: set workspace.host and workspace.profile (and targets.staging.workspace) to your workspace URL and CLI profile.
   databricks auth login --profile YOUR_CLI_PROFILE
   ```
2. **Deploy to staging:**
   ```bash
   cd /path/to/payer_memberadmin_genie_tutorial
   databricks bundle deploy --target staging
   ```
   (Uses the profile from your `databricks.yml`.)
   This uploads the notebook and creates the job **genie_memberadmin_setup_staging** in the workspace. The job is **not** run.
3. **Run the job manually** in Databricks: go to Workflows → Jobs → **genie_memberadmin_setup_staging** → Run now. Or run the notebook **One_Notebook_Genie_Room_Setup.py** from the workspace.
4. **Complete the Genie room** using **[GENIE_ROOM_COMPLETE_GUIDE.md](GENIE_ROOM_COMPLETE_GUIDE.md)** (Joins, Instructions, SQL Expressions, Queries, Benchmarks, explore).

---

## What’s in this repo

| File | Purpose |
|------|--------|
| **One_Notebook_Genie_Room_Setup.py** | Single notebook: creates schema (e.g. YOUR_CATALOG.genie_memberadmin), base tables, views, synthetic data, metric view, and Genie space. Uses environment parameter for warehouse_id. |
| **GENIE_ROOM_COMPLETE_GUIDE.md** | Complete guide: setup, data reference, and how to configure the Genie room (Instructions, Joins, SQL Expressions, Queries, Benchmarks) and explore it. Use after running the notebook. |
| **GENIE_ROOM_PROMPT.md** | Customer prompt: scope, data, modeling (views + Metric Views), and Genie goals for Payer Member Admin. |
| **TABLE_SCHEMA_REFERENCE.md** | Base tables, views, and Metric Views with columns and grain. |
| **databricks.yml.example** | Sample bundle definition (no real host). Copy to `databricks.yml`, set your workspace `host` and `profile`, then run `databricks bundle deploy --target staging`. |

---

## Quick start

1. Clone: `git clone https://github.com/bigdatavik/payer_memberadmin_genie_tutorial.git`
2. Copy and configure: `cp databricks.yml.example databricks.yml` and set your workspace `host` and `profile` in `databricks.yml`.
3. Deploy: `databricks bundle deploy --target staging` (job is **not** run).
4. In Databricks, run the job **genie_memberadmin_setup_staging** (or the notebook) once.
5. Follow **[GENIE_ROOM_COMPLETE_GUIDE.md](GENIE_ROOM_COMPLETE_GUIDE.md)** to finish configuring and exploring the room.

Default schema name: **genie_memberadmin**. Set your catalog in the notebook; replace `YOUR_CATALOG` and `YOUR_SCHEMA` in the guide with your catalog and schema.

---

## Requirements

- Databricks workspace with Genie and Unity Catalog (staging: fevm profile)
- SQL warehouse for the Genie space (notebook uses warehouse_id per environment from bundle parameter)
- Catalog must exist; schema is created by the notebook if it does not exist
