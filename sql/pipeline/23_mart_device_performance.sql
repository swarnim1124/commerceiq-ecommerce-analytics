-- Mart: revenue and orders per device category. Grain: device_category.
CREATE OR REPLACE TABLE `{{ dataset_ref }}.device_performance` AS
SELECT
    IFNULL(device_category, '(not set)') AS device_category,
    COUNT(*) AS transactions,
    ROUND(SUM(purchase_revenue), 2) AS revenue,
    ROUND(SAFE_DIVIDE(SUM(purchase_revenue), COUNT(*)), 2) AS average_order_value
FROM `{{ dataset_ref }}.stg_purchases`
GROUP BY device_category;
