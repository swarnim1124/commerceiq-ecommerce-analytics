-- ===========================================================
-- Staging: distinct users per item and pre-purchase event
-- Grain: user_pseudo_id x item_id x item_name x event_name
-- ===========================================================
CREATE OR REPLACE TABLE `{{ dataset_ref }}.stg_item_events` AS
SELECT DISTINCT
    user_pseudo_id,
    item.item_id,
    item.item_name,
    event_name
FROM `{{ source_table }}`,
    UNNEST(items) AS item
WHERE _TABLE_SUFFIX BETWEEN '{{ start_date }}' AND '{{ end_date }}'
    AND event_name IN ('view_item', 'add_to_cart');
