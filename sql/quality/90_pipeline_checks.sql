-- ===========================================================
-- Pipeline data-quality checks. Run AFTER the pipeline.
-- Output: one row per check (check_name, severity, passed, observed).
--   severity 'error'  -> a failure means a metric is wrong; fix before use.
--   severity 'warn'   -> unusual; investigate and document.
--   severity 'info'   -> context only; always passes.
-- ===========================================================
WITH
p AS (
    SELECT
        COUNT(*) AS n,
        COUNT(DISTINCT transaction_id) AS n_distinct,
        SUM(purchase_revenue) AS revenue,
        COUNTIF(purchase_revenue <= 0) AS non_positive,
        COUNTIF(marketing_channel IS NULL) AS null_channel,
        COUNT(DISTINCT user_pseudo_id) AS buyers,
        MIN(purchase_date) AS min_date,
        MAX(purchase_date) AS max_date,
        SUM(IF(marketing_channel = 'Unattributed', purchase_revenue, 0)) AS unattributed_revenue
    FROM `{{ dataset_ref }}.stg_purchases`
),
m AS (SELECT SUM(transactions) AS n, SUM(revenue) AS revenue FROM `{{ dataset_ref }}.revenue_monthly`),
c AS (SELECT SUM(transactions) AS n, SUM(revenue) AS revenue FROM `{{ dataset_ref }}.revenue_by_country`),
ch AS (SELECT SUM(transactions) AS n, SUM(revenue) AS revenue FROM `{{ dataset_ref }}.channel_performance`),
d AS (SELECT SUM(transactions) AS n, SUM(revenue) AS revenue FROM `{{ dataset_ref }}.device_performance`),
cu AS (SELECT COUNT(*) AS customers, SUM(orders) AS orders, SUM(revenue) AS revenue FROM `{{ dataset_ref }}.customer_metrics`),
li AS (SELECT SUM(line_revenue) AS line_revenue FROM `{{ dataset_ref }}.stg_purchase_items`),
f AS (SELECT MAX(IF(event_name = 'purchase', users, NULL)) AS purchasers FROM `{{ dataset_ref }}.funnel_metrics`),
raw_purchases AS (
    SELECT
        COUNT(*) AS purchase_events,
        COUNTIF(
            ecommerce.transaction_id IS NULL
            OR ecommerce.transaction_id IN ('', '(not set)')
            OR ecommerce.purchase_revenue IS NULL
        ) AS excluded_events
    FROM `{{ source_table }}`
    WHERE _TABLE_SUFFIX BETWEEN '{{ start_date }}' AND '{{ end_date }}'
        AND event_name = 'purchase'
)
SELECT 'transaction_id_is_unique' AS check_name, 'error' AS severity,
    p.n = p.n_distinct AS passed, CAST(p.n - p.n_distinct AS STRING) AS observed
FROM p
UNION ALL
SELECT 'revenue_is_positive', 'error', p.non_positive = 0, CAST(p.non_positive AS STRING) FROM p
UNION ALL
SELECT 'channel_is_never_null', 'error', p.null_channel = 0, CAST(p.null_channel AS STRING) FROM p
UNION ALL
SELECT 'dates_inside_requested_window', 'error',
    p.min_date >= PARSE_DATE('%Y%m%d', '{{ start_date }}')
        AND p.max_date <= PARSE_DATE('%Y%m%d', '{{ end_date }}'),
    CONCAT(CAST(p.min_date AS STRING), ' to ', CAST(p.max_date AS STRING))
FROM p
UNION ALL
SELECT 'monthly_revenue_reconciles', 'error', ABS(m.revenue - p.revenue) < 0.05,
    CAST(ROUND(m.revenue - p.revenue, 2) AS STRING)
FROM m, p
UNION ALL
SELECT 'monthly_transactions_reconcile', 'error', m.n = p.n, CAST(m.n - p.n AS STRING) FROM m, p
UNION ALL
SELECT 'country_revenue_reconciles', 'error', ABS(c.revenue - p.revenue) < 0.05,
    CAST(ROUND(c.revenue - p.revenue, 2) AS STRING)
FROM c, p
UNION ALL
SELECT 'channel_revenue_reconciles', 'error', ABS(ch.revenue - p.revenue) < 0.05,
    CAST(ROUND(ch.revenue - p.revenue, 2) AS STRING)
FROM ch, p
UNION ALL
SELECT 'device_revenue_reconciles', 'error', ABS(d.revenue - p.revenue) < 0.05,
    CAST(ROUND(d.revenue - p.revenue, 2) AS STRING)
FROM d, p
UNION ALL
SELECT 'customer_revenue_reconciles', 'error', ABS(cu.revenue - p.revenue) < 0.05,
    CAST(ROUND(cu.revenue - p.revenue, 2) AS STRING)
FROM cu, p
UNION ALL
SELECT 'customer_orders_equal_transactions', 'error', cu.orders = p.n, CAST(cu.orders - p.n AS STRING)
FROM cu, p
UNION ALL
SELECT 'funnel_purchasers_cover_customers', 'error', f.purchasers >= cu.customers,
    CAST(f.purchasers - cu.customers AS STRING)
FROM f, cu
UNION ALL
SELECT 'item_line_revenue_within_5pct_of_order_revenue', 'warn',
    ABS(SAFE_DIVIDE(li.line_revenue, p.revenue) - 1) <= 0.05,
    CAST(ROUND(SAFE_DIVIDE(li.line_revenue, p.revenue), 4) AS STRING)
FROM li, p
UNION ALL
SELECT 'unattributed_revenue_share_below_30pct', 'warn',
    SAFE_DIVIDE(p.unattributed_revenue, p.revenue) < 0.30,
    CAST(ROUND(SAFE_DIVIDE(p.unattributed_revenue, p.revenue), 4) AS STRING)
FROM p
UNION ALL
SELECT 'purchase_events_excluded_from_staging', 'info', TRUE,
    CONCAT(CAST(r.excluded_events AS STRING), ' of ', CAST(r.purchase_events AS STRING))
FROM raw_purchases AS r
UNION ALL
SELECT 'purchase_events_deduplicated_away', 'info', TRUE,
    CAST(r.purchase_events - r.excluded_events - p.n AS STRING)
FROM raw_purchases AS r, p;
