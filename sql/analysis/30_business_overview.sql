-- ===========================================================
-- Business overview. Requires the pipeline (sql/pipeline) to have run.
-- Replace {{ dataset_ref }} with project.dataset when pasting into the console,
-- or run via the CLI which renders it for you.
-- ===========================================================

-- 1. Headline KPIs
-- Question: how much did the store sell, and at what average order value?
SELECT
    COUNT(*) AS transactions,
    COUNT(DISTINCT user_pseudo_id) AS buyers,
    ROUND(SUM(purchase_revenue), 2) AS total_revenue,
    ROUND(SAFE_DIVIDE(SUM(purchase_revenue), COUNT(*)), 2) AS average_order_value,
    ROUND(APPROX_QUANTILES(purchase_revenue, 100)[OFFSET(50)], 2) AS median_order_value
FROM `{{ dataset_ref }}.stg_purchases`;

-- 2. Monthly trend with month-over-month change
-- Question: is revenue growing, and is the change driven by orders or order size?
SELECT
    month,
    transactions,
    revenue,
    average_order_value,
    ROUND(SAFE_DIVIDE(revenue - LAG(revenue) OVER (ORDER BY month),
        LAG(revenue) OVER (ORDER BY month)), 4) AS revenue_mom_change,
    ROUND(SAFE_DIVIDE(transactions - LAG(transactions) OVER (ORDER BY month),
        LAG(transactions) OVER (ORDER BY month)), 4) AS transactions_mom_change
FROM `{{ dataset_ref }}.revenue_monthly`
ORDER BY month;

-- 3. Country concentration
-- Question: how dependent is revenue on a few markets?
SELECT
    country,
    transactions,
    revenue,
    average_order_value,
    revenue_share,
    ROUND(SUM(revenue_share) OVER (ORDER BY revenue DESC), 4) AS cumulative_share
FROM `{{ dataset_ref }}.revenue_by_country`
ORDER BY revenue DESC
LIMIT 10;

-- 4. Channel mix (first-touch attribution)
-- Question: which acquisition channels bring buyers, and how big is the unattributed bucket?
SELECT
    marketing_channel,
    transactions,
    revenue,
    average_order_value,
    revenue_share
FROM `{{ dataset_ref }}.channel_performance`
ORDER BY revenue DESC;

-- 5. Device mix
SELECT
    device_category,
    transactions,
    revenue,
    average_order_value,
    ROUND(SAFE_DIVIDE(revenue, SUM(revenue) OVER ()), 4) AS revenue_share
FROM `{{ dataset_ref }}.device_performance`
ORDER BY revenue DESC;
