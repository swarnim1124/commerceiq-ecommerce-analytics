-- ===========================================================
-- Funnel and customer analysis. Requires the pipeline to have run.
-- ===========================================================

-- 1. Funnel with step-to-step conversion
-- Question: where do users drop off?
SELECT funnel_step, event_name, users, step_conversion, pct_of_first_step
FROM `{{ dataset_ref }}.funnel_metrics`
ORDER BY funnel_step;

-- 2. One-time vs returning customers
-- Question: do returning customers contribute disproportionate value?
SELECT
    customer_type,
    COUNT(*) AS customers,
    ROUND(SAFE_DIVIDE(COUNT(*), SUM(COUNT(*)) OVER ()), 4) AS customer_share,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(SAFE_DIVIDE(SUM(revenue), SUM(SUM(revenue)) OVER ()), 4) AS revenue_share,
    ROUND(SAFE_DIVIDE(SUM(revenue), COUNT(*)), 2) AS revenue_per_customer,
    ROUND(SAFE_DIVIDE(SUM(revenue), SUM(orders)), 2) AS average_order_value
FROM `{{ dataset_ref }}.customer_metrics`
GROUP BY customer_type
ORDER BY revenue DESC;

-- 3. Purchase frequency distribution
SELECT
    orders,
    COUNT(*) AS customers
FROM `{{ dataset_ref }}.customer_metrics`
GROUP BY orders
ORDER BY orders;

-- 4. Top 10 buyers by revenue (anonymous pseudo IDs, behavioural analysis only)
SELECT
    user_pseudo_id,
    orders,
    revenue,
    average_order_value
FROM `{{ dataset_ref }}.customer_metrics`
ORDER BY revenue DESC
LIMIT 10;
