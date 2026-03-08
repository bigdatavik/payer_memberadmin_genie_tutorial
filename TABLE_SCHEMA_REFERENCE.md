# Table and view schema reference – Payer Member Administration

**Catalog:** humana_payer (default)  
**Schema:** genie_memberadmin (default)

Replace `YOUR_CATALOG.YOUR_SCHEMA` in SQL with e.g. `humana_payer.genie_memberadmin` when copying.

---

## Base tables

| Table | Columns | Grain |
|-------|---------|-------|
| **member_demographics** | member_id, first_name, last_name, region, segment, created_date | One row per member |
| **plan_options** | plan_id, plan_name, product_type | One row per plan |
| **member_coverage** | member_id, plan_id, start_date, end_date, network_ind | One row per member-plan-coverage period |
| **admin_events** | event_id, member_id, event_type, event_date, channel | One row per admin event (address_change, id_card_reprint, plan_change, termination) |
| **member_utilization** | member_id, period_month, portal_logins, call_count, claims_count, claims_dollars | One row per member per month |
| **config_genie** | config_key, config_value, created_at | Key/value (e.g. genie_space_id) |

---

## Views

| View | Columns | Grain |
|------|---------|-------|
| **member_coverage_v** | member_id, plan_id, plan_name, product_type, start_date, end_date, network_ind, region, segment | One row per member-plan-coverage period (join of member_coverage, plan_options, member_demographics) |
| **member_admin_events_v** | event_id, member_id, event_type, event_date, channel, region, segment | One row per admin event with member region/segment |
| **member_experience_v** | member_id, period_month, portal_logins, call_count, claims_count, claims_dollars, region, segment | One row per member per month with region/segment |

---

## Metric view

| Metric view | Dimensions | Measures |
|-------------|------------|----------|
| **mv_member_experience** | member_id, period_month, region, segment | portal_logins_total, call_count_total, claims_count_total, claims_dollars_total, active_member_months |

Source: member_experience_v.
