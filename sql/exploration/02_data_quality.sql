-- ===========================================================
-- Project: GA4 Ecommerce Analytics
-- Run directly in the BigQuery console; no setup needed (public dataset).
-- Cost note: no date filter, so each query scans the full 3-month sample.
-- File: 02_data_quality.sql
-- Purpose: Validate data quality before analytical modeling
-- ===========================================================

-- ===========================================================
-- 1. Check missing user identifiers
-- ===========================================================

-- Business question:
-- Are user identifiers available for all events?

SELECT
    COUNT(*) AS total_events,
    COUNT(user_pseudo_id) AS available_user_ids,
    COUNTIF(user_pseudo_id IS NULL) AS missing_user_ids
FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`;

-- Findings:
-- • All events contain user_pseudo_id values.
-- • No missing user identifiers were found.
-- • user_pseudo_id can be used as the primary identifier for user-level analysis.


-- ===========================================================
-- 2. Check event timestamps
-- ===========================================================

-- Business question:
-- Are event timestamps available for all events?

SELECT
    COUNT(*) AS total_events,
    COUNT(event_timestamp) AS available_timestamps,
    COUNTIF(event_timestamp IS NULL) AS missing_timestamps
FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`;

-- Findings:
-- • All events contain event_timestamp values.
-- • No missing timestamps were found.
-- • Event-level analysis and time-based metrics can be performed reliably.


-- ===========================================================
-- 3. Check purchase data completeness
-- ===========================================================

-- Business question:
-- Are purchase events complete enough for revenue analysis?

SELECT
    COUNT(*) AS purchase_events,
    COUNT(ecommerce.transaction_id) AS transactions_with_id,
    COUNT(ecommerce.purchase_revenue) AS purchases_with_revenue,
    COUNTIF(ecommerce.transaction_id IS NULL) AS missing_transaction_id,
    COUNTIF(ecommerce.purchase_revenue IS NULL) AS missing_revenue

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

WHERE
    event_name = 'purchase';

-- Findings:
-- • Most purchase events contain transaction IDs, with only a small number of missing values.
-- • A noticeable share of purchase events is missing purchase_revenue values.
-- • Revenue calculations should include only purchase events with available revenue data.
-- • Missing revenue values should be documented as a data limitation.


-- ===========================================================
-- 4. Check revenue values
-- ===========================================================

-- Business question:
-- Are purchase revenue values valid?

SELECT
    MIN(ecommerce.purchase_revenue) AS min_revenue,
    MAX(ecommerce.purchase_revenue) AS max_revenue,
    AVG(ecommerce.purchase_revenue) AS avg_revenue,
    COUNTIF(ecommerce.purchase_revenue <= 0) AS non_positive_revenue

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

WHERE
    event_name = 'purchase'
    AND ecommerce.purchase_revenue IS NOT NULL;

-- Findings:
-- • Purchase revenue values are positive for all valid purchase events.
-- • No negative or zero revenue values were found.
-- • Revenue values range from 1 to 1530, with an average purchase revenue of approximately 69.
-- • Purchase revenue can be used for further ecommerce analysis after excluding missing values.


-- ===========================================================
-- 5. Check product data completeness
-- ===========================================================

-- Business question:
-- Are product attributes available for ecommerce analysis?


SELECT
    COUNT(*) AS total_items,
    COUNT(item.item_id) AS items_with_id,
    COUNT(item.item_name) AS items_with_name,
    COUNT(item.price) AS items_with_price,
    COUNT(item.quantity) AS items_with_quantity,

    COUNTIF(item.item_id IS NULL) AS missing_item_id,
    COUNTIF(item.item_name IS NULL) AS missing_item_name,
    COUNTIF(item.price IS NULL) AS missing_price,
    COUNTIF(item.quantity IS NULL) AS missing_quantity

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
    UNNEST(items) AS item;

-- Findings:
-- • All items have item_id and item_name values available.
-- • A small percentage of items are missing price values.
-- • Quantity is missing for most item records, which is expected because
--   quantity is not required for all ecommerce events.
-- • Product-level revenue analysis should focus on purchase events
--   with available price and quantity information.


-- ===========================================================
-- 6. Check purchased item data completeness
-- ===========================================================

-- Business question:
-- Are product attributes available for completed purchases?


SELECT
    COUNT(*) AS purchased_items,

    COUNT(item.item_id) AS items_with_id,
    COUNT(item.item_name) AS items_with_name,
    COUNT(item.price) AS items_with_price,
    COUNT(item.quantity) AS items_with_quantity,

    COUNTIF(item.price IS NULL) AS missing_price,
    COUNTIF(item.quantity IS NULL) AS missing_quantity

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
    UNNEST(items) AS item

WHERE
    event_name = 'purchase';

-- Findings:
-- • All purchased items have item IDs and names available.
-- • A small percentage of purchased items is missing price and quantity values.
-- • Product-level analysis can be performed using purchase items with available price and quantity.
-- • Missing product attributes should be excluded or handled separately during revenue calculations.
