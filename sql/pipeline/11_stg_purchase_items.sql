-- ===========================================================
-- Staging: one row per purchased item line
-- Grain: transaction_id x item
-- Built from stg_purchases so product revenue is deduplicated the
-- same way as order revenue.
-- ===========================================================
CREATE OR REPLACE TABLE `{{ dataset_ref }}.stg_purchase_items` AS
SELECT
    p.transaction_id,
    p.user_pseudo_id,
    p.purchase_date,
    item.item_id,
    item.item_name,
    item.item_category,
    item.price,
    item.quantity,
    item.price * item.quantity AS line_revenue
FROM `{{ dataset_ref }}.stg_purchases` AS p,
    UNNEST(p.items) AS item;
