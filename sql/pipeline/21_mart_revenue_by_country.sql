-- Mart: revenue and orders per buyer country. Grain: country.
CREATE OR REPLACE TABLE `{{ dataset_ref }}.revenue_by_country` AS
SELECT
    IFNULL(country, '(not set)') AS country,
    COUNT(*) AS transactions,
    ROUND(SUM(purchase_revenue), 2) AS revenue,
    ROUND(SAFE_DIVIDE(SUM(purchase_revenue), COUNT(*)), 2) AS average_order_value,
    ROUND(SAFE_DIVIDE(SUM(purchase_revenue), SUM(SUM(purchase_revenue)) OVER ()), 4) AS revenue_share
FROM `{{ dataset_ref }}.stg_purchases`
GROUP BY country;
