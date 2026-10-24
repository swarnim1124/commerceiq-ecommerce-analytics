-- Mart: user-level ecommerce funnel. Grain: funnel step.
-- A user counts for a step if they fired the event at least once in the
-- window. Steps are NOT forced to be sequential, so a later step can in
-- principle exceed an earlier one (e.g. purchase without a view_item event).
CREATE OR REPLACE TABLE `{{ dataset_ref }}.funnel_metrics` AS
WITH user_steps AS (
    SELECT
        user_pseudo_id,
        LOGICAL_OR(event_name = 'view_item') AS viewed,
        LOGICAL_OR(event_name = 'add_to_cart') AS added,
        LOGICAL_OR(event_name = 'begin_checkout') AS checkout,
        LOGICAL_OR(event_name = 'purchase') AS purchased
    FROM `{{ source_table }}`
    WHERE _TABLE_SUFFIX BETWEEN '{{ start_date }}' AND '{{ end_date }}'
        AND event_name IN ('view_item', 'add_to_cart', 'begin_checkout', 'purchase')
    GROUP BY user_pseudo_id
),
steps AS (
    SELECT 1 AS funnel_step, 'view_item' AS event_name, COUNTIF(viewed) AS users FROM user_steps
    UNION ALL
    SELECT 2, 'add_to_cart', COUNTIF(added) FROM user_steps
    UNION ALL
    SELECT 3, 'begin_checkout', COUNTIF(checkout) FROM user_steps
    UNION ALL
    SELECT 4, 'purchase', COUNTIF(purchased) FROM user_steps
)
SELECT
    funnel_step,
    event_name,
    users,
    ROUND(SAFE_DIVIDE(users, LAG(users) OVER (ORDER BY funnel_step)), 4) AS step_conversion,
    ROUND(SAFE_DIVIDE(users, FIRST_VALUE(users) OVER (ORDER BY funnel_step)), 4) AS pct_of_first_step
FROM steps;
