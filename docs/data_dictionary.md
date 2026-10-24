# Data dictionary

## Source columns used (GA4 export schema)

| Column | Type | Used for |
|---|---|---|
| `event_date` | STRING `YYYYMMDD` | Month and date grouping (parsed with `PARSE_DATE`) |
| `event_timestamp` | INT64 (microseconds) | Keeping the first of duplicated purchase events |
| `event_name` | STRING | `view_item`, `add_to_cart`, `begin_checkout`, `purchase`, `session_start` |
| `user_pseudo_id` | STRING | User and customer identity |
| `ecommerce.transaction_id` | STRING | Order identity |
| `ecommerce.purchase_revenue` | FLOAT | Order revenue (USD) |
| `items` | ARRAY<STRUCT> | `item_id`, `item_name`, `item_category`, `price`, `quantity` |
| `geo.country` | STRING | Country |
| `device.category` | STRING | desktop, mobile, tablet |
| `traffic_source.source`, `.medium` | STRING | First-touch acquisition |

## Tables created by `sql/pipeline`

Staging tables are intermediate; marts are what dashboards read.

| Table | Layer | Grain | Key columns |
|---|---|---|---|
| `stg_purchases` | staging | `transaction_id` | `purchase_revenue`, `country`, `device_category`, `marketing_channel`, `items` |
| `stg_purchase_items` | staging | `transaction_id` x item | `item_id`, `item_name`, `price`, `quantity`, `line_revenue` |
| `stg_item_events` | staging | user x item x event | `view_item` and `add_to_cart` only |
| `revenue_monthly` | mart | month | `transactions`, `revenue`, `average_order_value` |
| `revenue_by_country` | mart | country | `transactions`, `revenue`, `average_order_value`, `revenue_share` |
| `channel_performance` | mart | marketing channel | same plus `revenue_share` |
| `source_medium_performance` | mart | source x medium | raw attribution detail |
| `device_performance` | mart | device category | `transactions`, `revenue`, `average_order_value` |
| `product_performance` | mart | item | `transactions`, `items_sold`, `revenue` |
| `customer_metrics` | mart | `user_pseudo_id` | `orders`, `revenue`, `average_order_value`, `customer_type` |
| `funnel_metrics` | mart | funnel step | `users`, `step_conversion`, `pct_of_first_step` |
| `product_conversion` | mart | item | `viewed_users`, `cart_users`, `purchased_users`, rates, `is_low_volume` |

## Marketing channel mapping

Defined once, in `sql/pipeline/10_stg_purchases.sql`. Rules are evaluated top to bottom.

| Channel | Rule |
|---|---|
| Direct | `source = '(direct)'` |
| Organic Search | `medium = 'organic'` |
| Paid Search | `medium IN ('cpc', 'ppc', 'paidsearch')` |
| Referral | `medium = 'referral'` |
| Unattributed | `source` is NULL, or `source` / `medium` is `<Other>` or `(data deleted)` |
| Other | everything else |

## Table names changed from the original project

| Original (Power BI) | This edition |
|---|---|
| `marketing_channels` (`channel`) | `channel_performance` (`marketing_channel`) |
| `channel_performance` (source / medium) | `source_medium_performance` |
| `customer_metrics.revenue` | unchanged, plus `average_order_value` |

Re-point the Power BI model at the new tables before refreshing the dashboard.
