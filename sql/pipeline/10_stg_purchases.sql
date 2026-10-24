-- ===========================================================
-- Staging: one row per purchase transaction
-- Grain: transaction_id (unique)
-- Why: GA4 can emit the same purchase more than once (the original
-- project saw 4,463 vs 4,452 transactions depending on how it was
-- counted). Summing purchase_revenue over raw events would double
-- count revenue for those repeats, so we keep the first event only.
-- ===========================================================
CREATE OR REPLACE TABLE `{{ dataset_ref }}.stg_purchases` AS
SELECT
    transaction_id,
    user_pseudo_id,
    event_timestamp,
    PARSE_DATE('%Y%m%d', event_date) AS purchase_date,
    purchase_revenue,
    country,
    device_category,
    source,
    medium,
    CASE
        WHEN source = '(direct)' THEN 'Direct'
        WHEN medium = 'organic' THEN 'Organic Search'
        WHEN medium IN ('cpc', 'ppc', 'paidsearch') THEN 'Paid Search'
        WHEN medium = 'referral' THEN 'Referral'
        WHEN source IS NULL
            OR source IN ('<Other>', '(data deleted)')
            OR medium IN ('<Other>', '(data deleted)') THEN 'Unattributed'
        ELSE 'Other'
    END AS marketing_channel,
    items
FROM (
    SELECT
        ecommerce.transaction_id AS transaction_id,
        user_pseudo_id,
        event_timestamp,
        event_date,
        ecommerce.purchase_revenue AS purchase_revenue,
        geo.country AS country,
        device.category AS device_category,
        traffic_source.source AS source,
        traffic_source.medium AS medium,
        items
    FROM `{{ source_table }}`
    WHERE _TABLE_SUFFIX BETWEEN '{{ start_date }}' AND '{{ end_date }}'
        AND event_name = 'purchase'
        AND ecommerce.transaction_id IS NOT NULL
        AND ecommerce.transaction_id NOT IN ('', '(not set)')
        AND ecommerce.purchase_revenue IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY ecommerce.transaction_id
        ORDER BY event_timestamp
    ) = 1
);
