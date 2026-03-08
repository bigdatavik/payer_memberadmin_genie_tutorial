# Databricks notebook source
# MAGIC %md
# MAGIC # Genie Room – Payer Member Administration (One Notebook Setup)
# MAGIC
# MAGIC **Deploy-only setup** — creates the **Genie Room - Payer Member Administration** room: schema (if needed), tables, synthetic data, views, metric view, `config_genie`, and the Genie space.
# MAGIC
# MAGIC - **Catalog:** `humana_payer` (reused). Provide your own catalog if different.
# MAGIC - **Schema:** `genie_memberadmin` (created if not exists, or reused).
# MAGIC - **Not part of the main pipeline** — run manually or via the deployed job.

# COMMAND ----------

# Environment from job parameter (same as main project); used to pick warehouse_id from config.
try:
    _env = dbutils.widgets.get("environment")
except Exception:
    _env = "dev"
dbutils.widgets.dropdown("environment", _env, ["dev", "staging", "prod"], "Environment")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration (edit these and run)

# COMMAND ----------

# ----- Same catalog/schema/warehouse as main project (config.yaml) -----
CATALOG = "humana_payer"
SCHEMA = "genie_memberadmin"
# Warehouse IDs aligned with config.yaml per environment
WAREHOUSE_IDS = {"dev": "148ccb90800933a1", "staging": "6b2808a405a0375a", "prod": "6b2808a405a0375a"}
WAREHOUSE_ID = WAREHOUSE_IDS.get(dbutils.widgets.get("environment"), WAREHOUSE_IDS["dev"])
GENIE_DISPLAY_NAME = "Genie Room - Payer Member Administration"
GENIE_DESCRIPTION = "Query member administration, enrollments, admin events, and utilization with natural language"

# Optional: seed row counts (defaults shown)
NUM_MEMBERS = 200
NUM_PLANS = 10
NUM_COVERAGE_ROWS = 400
NUM_ADMIN_EVENTS = 300
NUM_UTILIZATION_ROWS = 600

# COMMAND ----------

# Derived table/view names (do not edit)
BASE = f"{CATALOG}.{SCHEMA}"
MEMBER_DEMOGRAPHICS_TABLE = f"{BASE}.member_demographics"
PLAN_OPTIONS_TABLE = f"{BASE}.plan_options"
MEMBER_COVERAGE_TABLE = f"{BASE}.member_coverage"
ADMIN_EVENTS_TABLE = f"{BASE}.admin_events"
MEMBER_UTILIZATION_TABLE = f"{BASE}.member_utilization"
MEMBER_COVERAGE_V = f"{BASE}.member_coverage_v"
MEMBER_ADMIN_EVENTS_V = f"{BASE}.member_admin_events_v"
MEMBER_EXPERIENCE_V = f"{BASE}.member_experience_v"
CONFIG_TABLE = f"{BASE}.config_genie"

print(f"Catalog: {CATALOG}, Schema: {SCHEMA}")
print(f"Warehouse: {WAREHOUSE_ID}")
print(f"Genie: {GENIE_DISPLAY_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Use catalog; create schema if not exists, then use schema

# COMMAND ----------

spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"USE SCHEMA {SCHEMA}")
print(f"Using {CATALOG}.{SCHEMA} (schema created or reused)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Create tables (base + config_genie)

# COMMAND ----------

# member_demographics
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {MEMBER_DEMOGRAPHICS_TABLE} (
  member_id STRING,
  first_name STRING,
  last_name STRING,
  region STRING,
  segment STRING,
  created_date DATE
) USING DELTA
""")
print(f"Table {MEMBER_DEMOGRAPHICS_TABLE} OK")

# COMMAND ----------

# plan_options
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {PLAN_OPTIONS_TABLE} (
  plan_id STRING,
  plan_name STRING,
  product_type STRING
) USING DELTA
""")
print(f"Table {PLAN_OPTIONS_TABLE} OK")

# COMMAND ----------

# member_coverage (one row per member-plan-coverage period)
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {MEMBER_COVERAGE_TABLE} (
  member_id STRING,
  plan_id STRING,
  start_date DATE,
  end_date DATE,
  network_ind STRING
) USING DELTA
""")
print(f"Table {MEMBER_COVERAGE_TABLE} OK")

# COMMAND ----------

# admin_events
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {ADMIN_EVENTS_TABLE} (
  event_id STRING,
  member_id STRING,
  event_type STRING,
  event_date DATE,
  channel STRING
) USING DELTA
""")
print(f"Table {ADMIN_EVENTS_TABLE} OK")

# COMMAND ----------

# member_utilization (one row per member per month)
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {MEMBER_UTILIZATION_TABLE} (
  member_id STRING,
  period_month DATE,
  portal_logins INT,
  call_count INT,
  claims_count INT,
  claims_dollars DOUBLE
) USING DELTA
""")
print(f"Table {MEMBER_UTILIZATION_TABLE} OK")

# COMMAND ----------

# config_genie
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CONFIG_TABLE} (
  config_key STRING NOT NULL,
  config_value STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  CONSTRAINT config_genie_pk PRIMARY KEY(config_key)
)
USING DELTA
COMMENT 'Configuration for Genie room (e.g. genie_space_id)'
""")
print(f"Table {CONFIG_TABLE} OK")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3b. Create SQL views (member_coverage_v, member_admin_events_v, member_experience_v)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {MEMBER_COVERAGE_V} AS
SELECT c.member_id, c.plan_id, p.plan_name, p.product_type, c.start_date, c.end_date, c.network_ind,
       m.region, m.segment
FROM {MEMBER_COVERAGE_TABLE} c
JOIN {PLAN_OPTIONS_TABLE} p ON c.plan_id = p.plan_id
JOIN {MEMBER_DEMOGRAPHICS_TABLE} m ON c.member_id = m.member_id
""")
print(f"View {MEMBER_COVERAGE_V} OK")

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {MEMBER_ADMIN_EVENTS_V} AS
SELECT e.event_id, e.member_id, e.event_type, e.event_date, e.channel,
       m.region, m.segment
FROM {ADMIN_EVENTS_TABLE} e
JOIN {MEMBER_DEMOGRAPHICS_TABLE} m ON e.member_id = m.member_id
""")
print(f"View {MEMBER_ADMIN_EVENTS_V} OK")

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {MEMBER_EXPERIENCE_V} AS
SELECT u.member_id, u.period_month, u.portal_logins, u.call_count, u.claims_count, u.claims_dollars,
       m.region, m.segment
FROM {MEMBER_UTILIZATION_TABLE} u
JOIN {MEMBER_DEMOGRAPHICS_TABLE} m ON u.member_id = m.member_id
""")
print(f"View {MEMBER_EXPERIENCE_V} OK")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3c. Create metric view (mv_member_experience)

# COMMAND ----------

MV_MEMBER_EXPERIENCE = f"{BASE}.mv_member_experience"
yaml_spec = f"""
version: 1.1
comment: "Member experience: portal, calls, claims by segment and period"
source: {MEMBER_EXPERIENCE_V}
dimensions:
  - name: member_id
    expr: member_id
  - name: period_month
    expr: period_month
  - name: region
    expr: region
  - name: segment
    expr: segment
measures:
  - name: portal_logins_total
    expr: sum(portal_logins)
  - name: call_count_total
    expr: sum(call_count)
  - name: claims_count_total
    expr: sum(claims_count)
  - name: claims_dollars_total
    expr: sum(claims_dollars)
  - name: active_member_months
    expr: count(*)
"""

spark.sql(f"""
CREATE OR REPLACE VIEW {MV_MEMBER_EXPERIENCE}
WITH METRICS
LANGUAGE YAML
AS $$
{yaml_spec}
$$
""")
print(f"Metric view {MV_MEMBER_EXPERIENCE} OK")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Seed synthetic data

# COMMAND ----------

import random
from datetime import date, timedelta
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType

random.seed(42)
regions = ["South", "Midwest", "Northeast", "West"]
segments = ["MA", "PDP", "MAPD", "Commercial"]

# COMMAND ----------

# plan_options
n_plans = min(NUM_PLANS, 20)
plan_rows = []
for i in range(n_plans):
    pt = random.choice(["MA", "PDP", "MAPD"])
    plan_rows.append((f"plan_{i:03d}", f"Plan {pt} {i}", pt))
plan_schema = StructType([
    StructField("plan_id", StringType()),
    StructField("plan_name", StringType()),
    StructField("product_type", StringType()),
])
spark.createDataFrame(plan_rows, plan_schema).write.mode("overwrite").saveAsTable(PLAN_OPTIONS_TABLE)
print(f"Wrote {n_plans} rows to {PLAN_OPTIONS_TABLE}")

# COMMAND ----------

# member_demographics
n_members = min(NUM_MEMBERS, 1000)
member_ids = [f"mem_{i:06d}" for i in range(n_members)]
member_rows = []
for i in range(n_members):
    member_rows.append((
        member_ids[i],
        f"First{i}",
        f"Last{i}",
        random.choice(regions),
        random.choice(segments),
        date.today() - timedelta(days=random.randint(100, 1000)),
    ))
member_schema = StructType([
    StructField("member_id", StringType()),
    StructField("first_name", StringType()),
    StructField("last_name", StringType()),
    StructField("region", StringType()),
    StructField("segment", StringType()),
    StructField("created_date", DateType()),
])
spark.createDataFrame(member_rows, member_schema).write.mode("overwrite").saveAsTable(MEMBER_DEMOGRAPHICS_TABLE)
print(f"Wrote {n_members} rows to {MEMBER_DEMOGRAPHICS_TABLE}")

# COMMAND ----------

# member_coverage
plan_ids = [f"plan_{i:03d}" for i in range(n_plans)]
n_cov = min(NUM_COVERAGE_ROWS, 2000)
cov_rows = []
for i in range(n_cov):
    mid = random.choice(member_ids)
    pid = random.choice(plan_ids)
    start = date.today() - timedelta(days=random.randint(30, 700))
    end = start + timedelta(days=random.randint(90, 400))
    cov_rows.append((mid, pid, start, end, random.choice(["Y", "N"])))
cov_schema = StructType([
    StructField("member_id", StringType()),
    StructField("plan_id", StringType()),
    StructField("start_date", DateType()),
    StructField("end_date", DateType()),
    StructField("network_ind", StringType()),
])
spark.createDataFrame(cov_rows, cov_schema).write.mode("overwrite").saveAsTable(MEMBER_COVERAGE_TABLE)
print(f"Wrote {n_cov} rows to {MEMBER_COVERAGE_TABLE}")

# COMMAND ----------

# admin_events
event_types = ["address_change", "id_card_reprint", "plan_change", "termination"]
channels = ["agent", "broker", "direct", "portal"]
n_evt = min(NUM_ADMIN_EVENTS, 1000)
evt_rows = []
for i in range(n_evt):
    evt_rows.append((
        f"evt_{i:06d}",
        random.choice(member_ids),
        random.choice(event_types),
        date.today() - timedelta(days=random.randint(0, 365)),
        random.choice(channels),
    ))
evt_schema = StructType([
    StructField("event_id", StringType()),
    StructField("member_id", StringType()),
    StructField("event_type", StringType()),
    StructField("event_date", DateType()),
    StructField("channel", StringType()),
])
spark.createDataFrame(evt_rows, evt_schema).write.mode("overwrite").saveAsTable(ADMIN_EVENTS_TABLE)
print(f"Wrote {n_evt} rows to {ADMIN_EVENTS_TABLE}")

# COMMAND ----------

# member_utilization
n_util = min(NUM_UTILIZATION_ROWS, 2000)
util_rows = []
for i in range(n_util):
    period = date.today().replace(day=1) - timedelta(days=30 * random.randint(0, 11))
    util_rows.append((
        random.choice(member_ids),
        period,
        random.randint(0, 20),
        random.randint(0, 5),
        random.randint(0, 50),
        round(random.uniform(0, 5000), 2),
    ))
util_schema = StructType([
    StructField("member_id", StringType()),
    StructField("period_month", DateType()),
    StructField("portal_logins", IntegerType()),
    StructField("call_count", IntegerType()),
    StructField("claims_count", IntegerType()),
    StructField("claims_dollars", DoubleType()),
])
spark.createDataFrame(util_rows, util_schema).write.mode("overwrite").saveAsTable(MEMBER_UTILIZATION_TABLE)
print(f"Wrote {n_util} rows to {MEMBER_UTILIZATION_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Create Genie space

# COMMAND ----------

# MAGIC %pip install databricks-sdk --quiet

# COMMAND ----------

import json
import uuid
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# COMMAND ----------

try:
    resp = w.api_client.do("GET", "/api/2.0/genie/spaces")
    for space in resp.get("spaces", []):
        if space.get("title") == GENIE_DISPLAY_NAME:
            old_id = space.get("space_id")
            w.api_client.do("DELETE", f"/api/2.0/genie/spaces/{old_id}")
            print(f"Deleted existing space '{GENIE_DISPLAY_NAME}' ({old_id})")
            break
except Exception as e:
    print(f"Check/delete existing: {e}")

# COMMAND ----------

tables_sorted = sorted(
    [
        {"identifier": MEMBER_DEMOGRAPHICS_TABLE},
        {"identifier": PLAN_OPTIONS_TABLE},
        {"identifier": MEMBER_COVERAGE_TABLE},
        {"identifier": ADMIN_EVENTS_TABLE},
        {"identifier": MEMBER_UTILIZATION_TABLE},
        {"identifier": MEMBER_COVERAGE_V},
        {"identifier": MEMBER_ADMIN_EVENTS_V},
        {"identifier": MEMBER_EXPERIENCE_V},
        {"identifier": MV_MEMBER_EXPERIENCE},
    ],
    key=lambda x: x["identifier"],
)
text_instructions = f"""This space queries Payer Member Administration data. Tables and views in {CATALOG}.{SCHEMA}:
1. member_demographics: member_id, first_name, last_name, region, segment, created_date
2. plan_options: plan_id, plan_name, product_type
3. member_coverage: member_id, plan_id, start_date, end_date, network_ind (one row per member-plan-coverage period)
4. admin_events: event_id, member_id, event_type (address_change, id_card_reprint, plan_change, termination), event_date, channel
5. member_utilization: member_id, period_month, portal_logins, call_count, claims_count, claims_dollars (one row per member per month)
6. member_coverage_v: view joining coverage, plan, and member (region, segment)
7. member_admin_events_v: view of admin events with member region/segment
8. member_experience_v: view of utilization with member region/segment
9. mv_member_experience (metric view): dimensions member_id, period_month, region, segment; measures portal_logins_total, call_count_total, claims_count_total, claims_dollars_total, active_member_months. Prefer for KPIs and rollups.

Use these for aggregations and filters. No PHI or carrier names in queries."""

serialized_space = {
    "version": 1,
    "config": {
        "sample_questions": [
            {"id": str(uuid.uuid4()).replace("-", ""), "question": ["How many active members by plan and region?"]},
            {"id": str(uuid.uuid4()).replace("-", ""), "question": ["Where are we seeing the highest churn or terminations?"]},
            {"id": str(uuid.uuid4()).replace("-", ""), "question": ["Which segments have low portal adoption but high call volume?"]},
            {"id": str(uuid.uuid4()).replace("-", ""), "question": ["ID card reprint rate per 1,000 members by plan?"]}
        ]
    },
    "instructions": {
        "text_instructions": [
            {"id": str(uuid.uuid4()).replace("-", ""), "content": [text_instructions]}
        ]
    },
    "data_sources": {
        "tables": tables_sorted
    }
}

payload = {
    "title": GENIE_DISPLAY_NAME,
    "description": GENIE_DESCRIPTION,
    "warehouse_id": WAREHOUSE_ID,
    "serialized_space": json.dumps(serialized_space)
}

response = w.api_client.do("POST", "/api/2.0/genie/spaces", body=payload)
GENIE_SPACE_ID = response.get("space_id")
print(f"Genie Space created: {GENIE_SPACE_ID}")

# COMMAND ----------

# Save genie_space_id to config_genie
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")
spark.sql(f"""
MERGE INTO {CONFIG_TABLE} t
USING (
  SELECT 'genie_space_id' as config_key, '{GENIE_SPACE_ID}' as config_value, current_timestamp() as created_at
) s
ON t.config_key = s.config_key
WHEN MATCHED THEN UPDATE SET t.config_value = s.config_value, t.created_at = s.created_at
WHEN NOT MATCHED THEN INSERT (config_key, config_value, created_at) VALUES (s.config_key, s.config_value, s.created_at)
""")
print(f"Genie space ID saved to {CONFIG_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done
# MAGIC
# MAGIC Next: use **GENIE_ROOM_COMPLETE_GUIDE.md** in this folder to refine the Genie room (Instructions, Joins, UDFs) and explore the room step by step.
# MAGIC
# MAGIC **Manual:** If an app uses this Genie room, grant **Can Run** on this Genie space to the app's service principal (Share → add principal → Can Run).
