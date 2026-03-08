# Genie room creation prompt – Payer Member Administration

Use this prompt to configure a Genie room for the **Payer Member Admin** domain, assuming the right UC data is available.

---

We want to create a Genie space for the **Payer Member Administration** domain at a US health plan (e.g., Humana).

**Scope:**

- The **payer** is the health plan that pays providers for members' care (e.g., Medicare Advantage plans).
- **Member administration** includes:
  - Enrollments and eligibility (who is covered, for which plan, and when).
  - Benefits and coverage (copays, deductibles, networks).
  - ID cards, address changes, terminations, and plan changes.
  - Premium billing at the member/household level.
  - Member and provider self‑service portals, including claims history views.

**Data to include in this Genie space (all in Unity Catalog):**

- Core member tables: demographics, contact info, member‑plan relationships, enrollment periods, PCP assignments.
- Eligibility and benefits tables: coverage spans, plan options, network indicators.
- Admin events: address change events, ID card mailings, plan change transactions, termination reasons.
- Utilization/experience summaries: counts of portal logins, call‑center contacts, claims counts and high‑level dollars (no PHI at claim line level).

**Modeling guidance:**

- Use **SQL views** to create clean "wide" serving views at the right grain:
  - `member_coverage_v` (one row per member‑plan‑coverage period).
  - `member_admin_events_v` (one row per admin event such as address change, ID card, plan change).
  - `member_experience_v` (one row per member per month with portal usage, calls, claims counts).
- On top of those views, define **Metric Views** that expose:
  - Measures: active member count, enrollment churn rate, average tenure, ID‑card reprint rate, address change rate, call volume per 1k members, portal adoption rate.
  - Dimensions: member segment, product/plan, geography/region, channel (agent, broker, direct), time (month, quarter, year).
  - Reusable filters: "active members only", "Medicare Advantage only", "production traffic only".

**Genie goals:**

- Enable operations, member‑services, and product teams to ask questions like:
  - "How many active members do we have by plan and region?"
  - "Where are we seeing the highest churn or terminations?"
  - "Which segments have low portal adoption but high call‑center volume?"
  - "What is the ID‑card reprint rate per 1,000 members by plan?"
- Answers should be based only on the governed views and Metric Views above, not raw tables.
