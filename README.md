# Agent Channel Genie – Payer Member Administration

A **deploy-only** Genie Room setup for **Payer Member Administration** (enrollments, eligibility, admin events, utilization). Use the Databricks Asset Bundle to **deploy to staging**; the job is **not run** by the bundle. Run the notebook manually in the workspace, then complete the room using the included guide.

**GitHub:** [bigdatavik/agent_channel_genie_memberadmin_tutorial](https://github.com/bigdatavik/agent_channel_genie_memberadmin_tutorial) (private)

---

## Deploy to staging (do not run the job)

This repo uses **Databricks Asset Bundles (DABs)** to deploy the Genie setup job to staging only. Deployment **does not run** the job.

1. **Prerequisites:** [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html) installed and authenticated for the staging workspace:
   ```bash
   databricks auth login --profile fevm
   ```
2. **Deploy to staging:**
   ```bash
   cd /path/to/agent_channel_genie_memberadmin_tutorial
   databricks bundle deploy --target staging --profile fevm
   ```
   This uploads the notebook and creates the job **genie_memberadmin_setup_staging** in the workspace. The job is **not** run.
3. **Run the job manually** in Databricks: go to Workflows → Jobs → **genie_memberadmin_setup_staging** → Run now. Or run the notebook **One_Notebook_Genie_Room_Setup.py** from the workspace.
4. **Complete the Genie room** using **[GENIE_ROOM_COMPLETE_GUIDE.md](GENIE_ROOM_COMPLETE_GUIDE.md)** (Joins, Instructions, SQL Expressions, Queries, Benchmarks, explore).

---

## What’s in this repo

| File | Purpose |
|------|--------|
| **One_Notebook_Genie_Room_Setup.py** | Single notebook: creates schema (humana_payer.genie_memberadmin), base tables, views, synthetic data, metric view, and Genie space. Uses environment parameter for warehouse_id. |
| **GENIE_ROOM_COMPLETE_GUIDE.md** | Complete guide: setup, data reference, and how to configure the Genie room (Instructions, Joins, SQL Expressions, Queries, Benchmarks) and explore it. Use after running the notebook. |
| **GENIE_ROOM_PROMPT.md** | Customer prompt: scope, data, modeling (views + Metric Views), and Genie goals for Payer Member Admin. |
| **TABLE_SCHEMA_REFERENCE.md** | Base tables, views, and Metric Views with columns and grain. |
| **databricks.yml** | Bundle definition: staging target and one job (genie_memberadmin_setup). Deploy with `databricks bundle deploy --target staging`. |

---

## Quick start

1. Clone: `git clone https://github.com/bigdatavik/agent_channel_genie_memberadmin_tutorial.git`
2. Deploy: `databricks bundle deploy --target staging --profile fevm` (job is **not** run).
3. In Databricks, run the job **genie_memberadmin_setup_staging** (or the notebook) once.
4. Follow **[GENIE_ROOM_COMPLETE_GUIDE.md](GENIE_ROOM_COMPLETE_GUIDE.md)** to finish configuring and exploring the room.

Default catalog: **humana_payer**. Default schema: **genie_memberadmin**. Replace `YOUR_CATALOG` and `YOUR_SCHEMA` in the guide with these (or your values).

---

## Requirements

- Databricks workspace with Genie and Unity Catalog (staging: fevm profile)
- SQL warehouse for the Genie space (notebook uses warehouse_id per environment from bundle parameter)
- Catalog must exist; schema is created by the notebook if it does not exist
