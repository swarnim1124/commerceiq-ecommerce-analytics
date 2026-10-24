-- Mart: revenue and orders per calendar month. Grain: month.
CREATE OR REPLACE TABLE `{{ dataset_ref }}.revenue_monthly` AS
SELECT
    FORMAT_DATE('%Y-%m', purchase_date) AS month,
    COUNT(*) AS transactions,
    ROUND(SUM(purchase_revenue), 2) AS revenue,
    ROUND(SAFE_DIVIDE(SUM(purchase_revenue), COUNT(*)), 2) AS average_order_value
FROM `{{ dataset_ref }}.stg_purchases`
GROUP BY month;
