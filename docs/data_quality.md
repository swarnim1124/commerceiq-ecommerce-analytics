# Data quality

## What is checked automatically

| Where | What | Needs BigQuery |
|---|---|---|
| `sql/quality/90_pipeline_checks.sql` (`ga4-analytics check`) | Unique `transaction_id`; positive revenue; no NULL channel; dates inside the window; every mart's revenue and order totals reconcile to `stg_purchases`; customer orders equal transactions; funnel purchasers cover customers; line-item revenue within 5% of order revenue (warn); Unattributed share under 30% (warn); counts of excluded and de-duplicated events (info) | Yes |
| `ga4-analytics validate` | The same reconciliations on exported CSVs in `data/processed/` | No (after export) |
| `tests/` | The check logic itself, the SQL files (structure, placeholders, date bounds, no hardcoded project) and internal consistency of the reference snapshot | No |

## Reconciliation items in the original project

These were found by comparing the original SQL, README and dashboard against each other. They are **hypotheses to confirm** with `ga4-analytics run` followed by `ga4-analytics check`, because BigQuery could not be reached when this edition was prepared.

| # | Observation | Likely cause | Status |
|---|---|---|---|
| 1 | Dashboard shows 4,463 transactions; the original SQL reported 4,452 for the same filters | The dashboard adds up per-month distinct counts, so an ID that appears in two months is counted twice. This implies at least 11 repeated purchase events | Fixed in design: the pipeline deduplicates, so monthly counts sum to the total. Confirm with check `monthly_transactions_reconcile` |
| 2 | Revenue was summed per event but orders counted as distinct IDs | Repeated events inflate revenue without changing the order count | Fixed in design. Rough upper bound on the effect from item 1: 11 x $81 = about $900, or 0.25% of revenue. Unverified |
| 3 | Original comment: average purchase revenue about $69, but AOV is $81 | Probably the $69 mean covered purchase events without a transaction ID, which have lower revenue | Open. `purchase_events_excluded_from_staging` reports the count |
| 4 | Funnel shows 4,419 purchasing users; customer table has 4,047 | 372 users (8.4%) fired a purchase event but have no valid order. Probably missing transaction ID or revenue | Open. Check `funnel_purchasers_cover_customers` keeps the direction right; the size of the gap needs the re-run |
| 5 | Original `marketing_channels` table had no null filters, unlike every other table | Inconsistent filtering | Fixed: all marts read from `stg_purchases` |
| 6 | Original dashboard's monthly line chart was sorted by revenue (Dec, Nov, Jan) | Power BI sort on the value field, confirmed in the report layout | Open in the `.pbix` (cannot be edited without Power BI Desktop). Sort the visual by `month` ascending. This edition's `assets/figures/monthly_revenue.png` is chronological |
| 7 | "Top 10 products by purchase conversion" had no minimum traffic rule | `product_conversion` had no volume threshold (SQL exploration used `viewed_users > 100`) | Fixed: `is_low_volume` column. Apply it as a visual filter in Power BI |

## What could not be checked here

- Any query result. No SQL in this repository was executed against BigQuery by the person who prepared this edition.
- Parsing the SQL with a real BigQuery parser (`sqlglot`) could not run locally; the test exists and runs in CI.
- The Power BI file was not opened. It was inspected as a zip: its report layout was read, its data model was not.
