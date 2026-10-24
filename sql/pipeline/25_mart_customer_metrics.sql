-- Mart: one row per purchasing visitor. Grain: user_pseudo_id.
-- "Customer" = a user_pseudo_id (browser/device cookie) with >= 1 valid order.
-- "Returning" = 2+ distinct orders inside the 3-month window (same-day repeats count).
CREATE OR REPLACE TABLE `{{ dataset_ref }}.customer_metrics` AS
SELECT
    user_pseudo_id,
    COUNT(*) AS orders,
    ROUND(SUM(purchase_revenue), 2) AS revenue,
    ROUND(SAFE_DIVIDE(SUM(purchase_revenue), COUNT(*)), 2) AS average_order_value,
    MIN(purchase_date) AS first_purchase_date,
    MAX(purchase_date) AS last_purchase_date,
    IF(COUNT(*) = 1, 'One-time customer', 'Returning customer') AS customer_type
FROM `{{ dataset_ref }}.stg_purchases`
GROUP BY user_pseudo_id;
