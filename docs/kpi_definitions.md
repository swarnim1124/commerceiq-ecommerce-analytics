# KPI definitions

Every KPI is computed from `stg_purchases`, which has **one row per `transaction_id`**. That is what keeps revenue, orders and AOV consistent with each other.

| KPI | Definition | Interpretation | Limitations |
|---|---|---|---|
| **Revenue** | `SUM(purchase_revenue)` over unique transactions | Gross merchandise value of orders | GA4 `purchase_revenue` may include tax and shipping. It is not reconciled with product prices (see check `item_line_revenue_within_5pct_of_order_revenue`). Currency is USD. |
| **Transactions** | `COUNT(DISTINCT transaction_id)` | Number of orders | Orders with a missing or `(not set)` ID, or missing revenue, are excluded and counted in an info check. |
| **AOV** (average order value) | `Revenue / Transactions` | Typical basket size | Mean, so large orders pull it up. `median_order_value` is in `analysis/30_business_overview.sql`. |
| **Buyers / customers** | `COUNT(DISTINCT user_pseudo_id)` among valid orders | Purchasing visitors | Cookie based. One person on two devices is two customers. |
| **Revenue per customer** | `Revenue / Customers` for a segment | Value of a buyer | **Not AOV.** The original README labelled this as AOV. |
| **Returning customer** | 2 or more distinct orders in the window | Repeat purchase behaviour | Includes same-day repeats. A 3-month window understates true retention. |
| **Funnel step users** | Distinct users who fired the step's event at least once | Reach of each stage | **Not forced sequential.** A user can purchase without a `view_item` event, and step counts across event types are not a cohort. |
| **Step conversion** | `users(step) / users(previous step)` | Where users leave | Descriptive, not causal. |
| **View-to-purchase rate** | `purchasers / viewers` (users, per product) | Product appeal | Unreliable under about 100 viewers (`is_low_volume`). A user who views product A and buys product B counts as a viewer of A only. |
| **Revenue share** | `revenue / total revenue` | Concentration | Based on first-touch channel and cookie-level identity. |
| **MoM change** | `(month - previous month) / previous month` | Trend | Only meaningful in chronological order, with 3 months and a holiday season. |

## Decisions that change the numbers

1. **Deduplicate on `transaction_id`, keeping the earliest event.** The original project summed revenue per event but counted orders as distinct IDs. Any repeated purchase event therefore inflated revenue but not orders, biasing AOV upward.
2. **Exclude `(not set)` and empty transaction IDs.** Otherwise all such events would collapse into one fake transaction.
3. **Unattributed is its own channel.** `<Other>` and `(data deleted)` are obfuscation artefacts, not a marketing channel.
4. **Rates use `SAFE_DIVIDE`.** Division by zero returns NULL, not an error and not 0.
