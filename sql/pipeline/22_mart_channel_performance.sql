-- Mart: revenue by marketing channel. Grain: marketing_channel.
-- traffic_source in the GA4 export is the user's FIRST-touch source,
-- so this is first-touch attribution, not last-click.
CREATE OR REPLACE TABLE `{{ dataset_ref }}.channel_performance` AS
SELECT
    marketing_channel,
    COUNT(*) AS transactions,
    ROUND(SUM(purchase_revenue), 2) AS revenue,
    ROUND(SAFE_DIVIDE(SUM(purchase_revenue), COUNT(*)), 2) AS average_order_value,
    ROUND(SAFE_DIVIDE(SUM(purchase_revenue), SUM(SUM(purchase_revenue)) OVER ()), 4) AS revenue_share
FROM `{{ dataset_ref }}.stg_purchases`
GROUP BY marketing_channel;

-- Mart: same measures at raw source / medium level. Grain: source x medium.
CREATE OR REPLACE TABLE `{{ dataset_ref }}.source_medium_performance` AS
SELECT
    source,
    medium,
    marketing_channel,
    COUNT(*) AS transactions,
    ROUND(SUM(purchase_revenue), 2) AS revenue,
    ROUND(SAFE_DIVIDE(SUM(purchase_revenue), COUNT(*)), 2) AS average_order_value
FROM `{{ dataset_ref }}.stg_purchases`
GROUP BY source, medium, marketing_channel;
