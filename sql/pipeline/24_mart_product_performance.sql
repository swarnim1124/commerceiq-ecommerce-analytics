-- Mart: revenue per product. Grain: item_id x item_name.
-- transactions counts distinct orders containing the product.
CREATE OR REPLACE TABLE `{{ dataset_ref }}.product_performance` AS
SELECT
    item_id,
    item_name,
    COUNT(DISTINCT transaction_id) AS transactions,
    SUM(quantity) AS items_sold,
    ROUND(SUM(line_revenue), 2) AS revenue
FROM `{{ dataset_ref }}.stg_purchase_items`
GROUP BY item_id, item_name;
