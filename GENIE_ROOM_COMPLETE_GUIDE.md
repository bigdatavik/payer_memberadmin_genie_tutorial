# Genie Room – Payer Member Administration – Complete Guide

**Use this guide** to run the notebook, configure the **Genie Room - Payer Member Administration**, and explore it end-to-end.

**Convention:** Replace `YOUR_CATALOG.YOUR_SCHEMA` everywhere with your catalog and schema (e.g. `humana_payer.genie_memberadmin`).

---

## Quick start (4 steps)

1. **Edit** the notebook `One_Notebook_Genie_Room_Setup.py`: set `CATALOG`, `SCHEMA`, and `WAREHOUSE_ID` (defaults: `humana_payer`, `genie_memberadmin`).
2. **Run** the notebook from top to bottom (creates schema, tables, views, data, metric view, Genie space).
3. **Configure** the room in Databricks Genie (Instructions → Text, Joins, SQL Expressions, SQL Queries, Benchmarks) using the sections below.
4. **Explore** the room: start the SQL warehouse, then ask questions in Chat and Agent mode.

---

# Part 1: Run the setup

## 1.1 What you need

- Databricks workspace with Genie and a SQL warehouse.
- In the notebook's top cells, set:
  - **CATALOG** – e.g. `humana_payer` (must already exist).
  - **SCHEMA** – e.g. `genie_memberadmin` (created if it doesn't exist).
  - **WAREHOUSE_ID** – your SQL warehouse ID.

## 1.2 What the notebook creates

- Schema (if not exists), five base tables, three SQL views, synthetic data, metric view `mv_member_experience`, Genie space **Genie Room - Payer Member Administration**, and `config_genie` with the space ID.
- The room is recreated each run (drop + create for this room only); other Genie rooms are untouched.

---

# Part 2: Data at a glance

## 2.1 Base tables

- **member_demographics:** member_id, first_name, last_name, region, segment, created_date
- **plan_options:** plan_id, plan_name, product_type
- **member_coverage:** member_id, plan_id, start_date, end_date, network_ind (one row per member-plan-coverage period)
- **admin_events:** event_id, member_id, event_type, event_date, channel
- **member_utilization:** member_id, period_month, portal_logins, call_count, claims_count, claims_dollars (one row per member per month)

## 2.2 Views

- **member_coverage_v:** member_id, plan_id, plan_name, product_type, start_date, end_date, network_ind, region, segment (join of member_coverage, plan_options, member_demographics)
- **member_admin_events_v:** event_id, member_id, event_type, event_date, channel, region, segment
- **member_experience_v:** member_id, period_month, portal_logins, call_count, claims_count, claims_dollars, region, segment

## 2.3 Metric view

- **mv_member_experience**  
  Dimensions: member_id, period_month, region, segment  
  Measures: portal_logins_total, call_count_total, claims_count_total, claims_dollars_total, active_member_months

## 2.4 How the metric view is used in this room

- The notebook creates **mv_member_experience** on **member_experience_v**. Use it for portal adoption, call volume, claims counts/dollars, and active member months by region or segment.
- Prefer the metric view for common KPIs and rollups; use base tables or views for event-level or coverage-level detail.

---

# Part 3: Configure the Genie room

In Databricks: **SQL → Genie** → open **Genie Room - Payer Member Administration** → **Configure**.

## 3.1 Instructions → Text

Paste into **Instructions → Text** (replace YOUR_CATALOG.YOUR_SCHEMA with e.g. humana_payer.genie_memberadmin):

```
You are querying Payer Member Administration data. This space helps operations, member-services, and product teams explore enrollments, eligibility, admin events (address changes, ID card reprints, plan changes, terminations), and member experience (portal, calls, claims).

Data Sources (YOUR_CATALOG.YOUR_SCHEMA):
- member_demographics, plan_options, member_coverage, admin_events, member_utilization (base tables)
- member_coverage_v, member_admin_events_v, member_experience_v (views)
- mv_member_experience (metric view): dimensions member_id, period_month, region, segment; measures portal_logins_total, call_count_total, claims_count_total, claims_dollars_total, active_member_months. Prefer for KPIs.

Key concepts: event_type in admin_events = address_change, id_card_reprint, plan_change, termination. Channel = agent, broker, direct, portal. Segment/product_type = MA, PDP, MAPD, Commercial.

Query guidelines: (1) Active members by plan/region: use member_coverage_v or member_coverage. (2) Churn/terminations: use member_admin_events_v or admin_events where event_type = termination. (3) Portal vs call volume: use member_experience_v or mv_member_experience. (4) ID card reprint rate: use admin_events where event_type = id_card_reprint, aggregate per plan or per 1k members.

Response style: clear tables/charts; rates as percentages; no PHI or carrier names.
```

## 3.2 Instructions → Joins

**Instructions → Joins → + Add** (use full table names):

- **member_coverage → plan_options** on `member_coverage.plan_id = plan_options.plan_id` (Many to One)
- **member_coverage → member_demographics** on `member_coverage.member_id = member_demographics.member_id` (Many to One)
- **admin_events → member_demographics** on `admin_events.member_id = member_demographics.member_id` (Many to One)
- **member_utilization → member_demographics** on `member_utilization.member_id = member_demographics.member_id` (Many to One)

## 3.3 Instructions → SQL Expressions

**Measures**

- **id_card_reprint_rate_per_1k** (admin_events)  
  **Code:** `ROUND(SUM(CASE WHEN admin_events.event_type = 'id_card_reprint' THEN 1 ELSE 0 END) * 1000.0 / NULLIF(COUNT(DISTINCT admin_events.member_id), 0), 2)`  
  **Synonyms:** ID card reprint rate per 1k, reprint rate per thousand members, ID card reprints per 1000 members  
  **Instructions:** Use for admin_events. Returns the count of id_card_reprint events per 1,000 distinct members. Use when comparing reprint rates across plans or regions. Avoid using with other event types in the same aggregation.

- **address_change_rate** (admin_events)  
  **Code:** `ROUND(SUM(CASE WHEN admin_events.event_type = 'address_change' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2)`  
  **Synonyms:** address change rate, address change pct, percent address changes, move rate  
  **Instructions:** Use for admin_events. Returns the percentage of rows that are address_change events. Use for member-admin activity or contact-info change rates. Avoid mixing with other event_type filters in the same measure.

**Filters**

- **Active coverage**  
  **Code:** `member_coverage.end_date >= current_date()` or `member_coverage.end_date IS NULL`  
  **Synonyms:** active, current coverage, in force, active members  
  **Instructions:** Use with member_coverage or member_coverage_v to restrict to currently active coverage (end date in future or null). Use for “active member” counts; avoid for historical churn analysis.

- **MA only**  
  **Code:** `plan_options.product_type = 'MA'` or `member_coverage_v.product_type = 'MA'`  
  **Synonyms:** Medicare Advantage, MA only, MA plans  
  **Instructions:** Restricts to Medicare Advantage product type. Use when the question is about MA only; use the view version when querying member_coverage_v.

- **Terminations only**  
  **Code:** `admin_events.event_type = 'termination'`  
  **Synonyms:** terminations, terminated, churn events, disenrollments  
  **Instructions:** Use with admin_events or member_admin_events_v for termination events only. Use for churn or disenrollment analysis.

**Dimensions**

- **Region**  
  **Code:** `member_demographics.region` or `member_coverage_v.region`  
  **Synonyms:** region, geography, market  
  **Instructions:** Use for grouping or filtering by region (e.g. South, Midwest). Prefer member_coverage_v.region when already using that view.

- **Segment**  
  **Code:** `member_demographics.segment`  
  **Synonyms:** segment, member segment, product segment  
  **Instructions:** Use for grouping by member/product segment (e.g. MA, PDP, MAPD).

- **Product type**  
  **Code:** `plan_options.product_type`  
  **Synonyms:** product type, plan type, product  
  **Instructions:** Use for grouping by plan product type (MA, PDP, MAPD, Commercial).

- **Event type**  
  **Code:** `admin_events.event_type`  
  **Synonyms:** event type, admin event type, activity type  
  **Instructions:** Use for grouping admin events by type (address_change, id_card_reprint, plan_change, termination).

- **Channel**  
  **Code:** `admin_events.channel`  
  **Synonyms:** channel, contact channel, source channel  
  **Instructions:** Use for grouping by how the event was initiated (agent, broker, direct, portal).

- **Period month**  
  **Code:** `DATE_TRUNC('month', member_utilization.period_month)`  
  **Synonyms:** month, period month, utilization month  
  **Instructions:** Use for time grouping on member_utilization or member_experience_v. Truncates to first day of month for consistent monthly rollups.

## 3.4 Instructions → SQL Queries (example queries)

Replace YOUR_CATALOG.YOUR_SCHEMA with e.g. humana_payer.genie_memberadmin.

**Active members by plan and region:**
```sql
SELECT product_type, region, COUNT(DISTINCT member_id) AS active_members
FROM YOUR_CATALOG.YOUR_SCHEMA.member_coverage_v
WHERE end_date >= current_date() OR end_date IS NULL
GROUP BY product_type, region ORDER BY active_members DESC
```

**Churn / terminations by region:**
```sql
SELECT region, COUNT(*) AS termination_count
FROM YOUR_CATALOG.YOUR_SCHEMA.member_admin_events_v
WHERE event_type = 'termination'
GROUP BY region ORDER BY termination_count DESC
```

**Portal adoption vs call volume by segment:**
```sql
SELECT segment, SUM(portal_logins) AS portal_total, SUM(call_count) AS call_total
FROM YOUR_CATALOG.YOUR_SCHEMA.member_experience_v
GROUP BY segment
```

**ID card reprint rate per 1,000 members by plan:**  
Use a CTE to avoid a correlated subquery (not allowed with GROUP BY in Spark/Databricks).
```sql
WITH plan_members AS (
  SELECT p.product_type, COUNT(DISTINCT c.member_id) AS total_members
  FROM YOUR_CATALOG.YOUR_SCHEMA.member_coverage c
  JOIN YOUR_CATALOG.YOUR_SCHEMA.plan_options p ON c.plan_id = p.plan_id
  GROUP BY p.product_type
)
SELECT p.product_type, COUNT(DISTINCT e.member_id) AS members_with_reprint,
  ROUND(COUNT(*) * 1000.0 / NULLIF(pm.total_members, 0), 2) AS reprint_rate_per_1k
FROM YOUR_CATALOG.YOUR_SCHEMA.admin_events e
JOIN YOUR_CATALOG.YOUR_SCHEMA.member_coverage c ON e.member_id = c.member_id
JOIN YOUR_CATALOG.YOUR_SCHEMA.plan_options p ON c.plan_id = p.plan_id
JOIN plan_members pm ON pm.product_type = p.product_type
WHERE e.event_type = 'id_card_reprint'
GROUP BY p.product_type, pm.total_members
```

## 3.5 Parameterized queries (Trusted responses)

**Admin events by type** – Parameter: event_type_filter (String). Example: address_change, id_card_reprint, plan_change, termination.
```sql
SELECT member_id, event_type, event_date, channel
FROM YOUR_CATALOG.YOUR_SCHEMA.admin_events
WHERE event_type = :event_type_filter
ORDER BY event_date DESC LIMIT 100
```

**Member experience by region** – Parameter: region_filter (String). Example: South, Midwest, Northeast, West.
```sql
SELECT segment, period_month, SUM(portal_logins) AS portal_logins, SUM(call_count) AS calls, SUM(claims_count) AS claims_count
FROM YOUR_CATALOG.YOUR_SCHEMA.member_experience_v
WHERE region = :region_filter
GROUP BY segment, period_month ORDER BY period_month DESC, segment
```

## 3.6 Benchmarks (Benchmarks → Questions)

Add benchmark **Question** + **Ground truth SQL**. Replace YOUR_CATALOG.YOUR_SCHEMA with e.g. humana_payer.genie_memberadmin.

**Question:** How many active members by plan and region?  
**Ground truth SQL:**
```sql
SELECT product_type, region, COUNT(DISTINCT member_id) AS active_members
FROM YOUR_CATALOG.YOUR_SCHEMA.member_coverage_v
WHERE end_date >= current_date() OR end_date IS NULL
GROUP BY product_type, region ORDER BY active_members DESC
```

**Question:** Where are we seeing the highest churn or terminations?  
**Ground truth SQL:**
```sql
SELECT region, COUNT(*) AS termination_count
FROM YOUR_CATALOG.YOUR_SCHEMA.member_admin_events_v
WHERE event_type = 'termination'
GROUP BY region ORDER BY termination_count DESC
```

**Question:** Which segments have low portal adoption but high call volume?  
**Ground truth SQL:**
```sql
SELECT segment, SUM(portal_logins) AS portal_total, SUM(call_count) AS call_total
FROM YOUR_CATALOG.YOUR_SCHEMA.member_experience_v
GROUP BY segment
```

## 3.7 Settings

- **Description:** Query member administration, enrollments, admin events, and utilization with natural language.
- **Sample questions:** How many active members by plan and region? • Where is churn highest? • ID card reprint rate per 1,000 members by plan? • Portal adoption vs call volume by segment

---

# Part 4: Explore the room (step-by-step)

## 4.1 Before you start

- The setup notebook has been run (schema, tables, views, data, Genie space exist).
- SQL Warehouse ID is set in the notebook and the warehouse is available.
- In Databricks: **SQL → Genie** → open **Genie Room - Payer Member Administration**.

## 4.2 Start the SQL warehouse

1. If you see a banner that the SQL Warehouse is stopped, click **Start Warehouse**.
2. Wait until the warehouse is running.
3. Ask questions in the Genie room.

## 4.3 Chat mode – basic questions

- **"How many active members do we have by plan and region?"** – Expect counts by product_type and region from member_coverage_v.
- **"Where are we seeing the highest churn or terminations?"** – Expect termination counts by region from admin_events.
- **"Which segments have low portal adoption but high call-center volume?"** – Expect member_experience_v or mv_member_experience by segment.
- **"What is the ID card reprint rate per 1,000 members by plan?"** – Expect admin_events event_type = id_card_reprint aggregated by plan.

## 4.4 Agent mode

- **"Identify interesting outlier entities in the dataset"** – Agent may point out regions or segments with unusual termination or reprint rates.
- **"Visualize member experience by region and segment"** – Agent may suggest charts for portal vs calls or claims.

## 4.5 Configure tour

Click **Configure** to see Data (tables/views/metric view), Instructions (Text, Joins, SQL Expressions, SQL Queries), and Settings (description, sample questions).

---

# Part 5: Quick reference

## Questions to try

| Question | What you get |
|----------|--------------|
| How many active members by plan and region? | Counts from member_coverage_v |
| Where is churn or terminations highest? | Termination counts by region |
| Portal adoption vs call volume by segment? | member_experience_v or mv_member_experience |
| ID card reprint rate per 1,000 members by plan? | admin_events id_card_reprint by plan |

## Catalog and schema

- **Catalog:** humana_payer (default)
- **Schema:** genie_memberadmin (default)

## Next steps

- Use **Part 2 (Data at a glance)** when writing or debugging SQL and instructions.
- Add Joins, SQL Expressions, and parameterized queries from **Part 3** for better Genie answers and Trusted responses.
