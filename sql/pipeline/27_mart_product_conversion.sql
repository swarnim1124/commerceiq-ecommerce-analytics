-- Mart: product funnel. Grain: item_id x item_name.
-- is_low_volume flags products with < 100 viewers: their rates are noisy
-- and should not be ranked against high-traffic products.
CREATE OR REPLACE TABLE `{{ dataset_ref }}.product_conversion` AS
WITH browsing AS (
    SELECT
        item_id,
        item_name,
        COUNT(DISTINCT IF(event_name = 'view_item', user_pseudo_id, NULL)) AS viewed_users,
        COUNT(DISTINCT IF(event_name = 'add_to_cart', user_pseudo_id, NULL)) AS cart_users
    FROM `{{ dataset_ref }}.stg_item_events`
    GROUP BY item_id, item_name
),
buying AS (
    SELECT
        item_id,
        item_name,
        COUNT(DISTINCT user_pseudo_id) AS purchased_users
    FROM `{{ dataset_ref }}.stg_purchase_items`
    GROUP BY item_id, item_name
)
SELECT
    COALESCE(b.item_id, p.item_id) AS item_id,
    COALESCE(b.item_name, p.item_name) AS item_name,
    IFNULL(b.viewed_users, 0) AS viewed_users,
    IFNULL(b.cart_users, 0) AS cart_users,
    IFNULL(p.purchased_users, 0) AS purchased_users,
    ROUND(SAFE_DIVIDE(b.cart_users, b.viewed_users), 4) AS view_to_cart_rate,
    ROUND(SAFE_DIVIDE(p.purchased_users, b.viewed_users), 4) AS view_to_purchase_rate,
    IFNULL(b.viewed_users, 0) < 100 AS is_low_volume
FROM browsing AS b
FULL OUTER JOIN buying AS p
    ON b.item_id = p.item_id AND b.item_name = p.item_name;
