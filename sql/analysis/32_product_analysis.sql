-- ===========================================================
-- Product analysis. Requires the pipeline to have run.
-- ===========================================================

-- 1. Top 10 products by revenue, with share of total
SELECT
    item_name,
    transactions,
    items_sold,
    revenue,
    ROUND(SAFE_DIVIDE(revenue, SUM(revenue) OVER ()), 4) AS revenue_share
FROM `{{ dataset_ref }}.product_performance`
ORDER BY revenue DESC
LIMIT 10;

-- 2. Best converting products among products with enough traffic
-- Question: which items turn viewers into buyers? (>= 100 viewers to avoid noisy rates)
SELECT item_name, viewed_users, cart_users, purchased_users,
    view_to_cart_rate, view_to_purchase_rate
FROM `{{ dataset_ref }}.product_conversion`
WHERE viewed_users >= 100
ORDER BY view_to_purchase_rate DESC
LIMIT 20;

-- 3. High interest, low conversion
-- Question: which popular products fail to sell? (>= 500 viewers)
SELECT item_name, viewed_users, cart_users, purchased_users, view_to_purchase_rate
FROM `{{ dataset_ref }}.product_conversion`
WHERE viewed_users >= 500
ORDER BY view_to_purchase_rate ASC, viewed_users DESC
LIMIT 20;

-- 4. Zero-purchase products: real problem or a tracking/naming artefact?
-- Products with thousands of views and no purchases were reported by the original
-- dashboard. Before acting on them, check whether the item_id appears in purchases
-- under another name, and whether it was added to carts at all.
SELECT
    c.item_id,
    c.item_name,
    c.viewed_users,
    c.cart_users,
    c.purchased_users,
    n.names_seen_in_purchases
FROM `{{ dataset_ref }}.product_conversion` AS c
LEFT JOIN (
    SELECT item_id, COUNT(DISTINCT item_name) AS names_seen_in_purchases
    FROM `{{ dataset_ref }}.stg_purchase_items`
    GROUP BY item_id
) AS n
    ON c.item_id = n.item_id
WHERE c.viewed_users >= 500 AND c.purchased_users = 0
ORDER BY c.viewed_users DESC;
