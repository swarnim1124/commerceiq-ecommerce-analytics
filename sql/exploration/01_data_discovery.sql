-- ===========================================================
-- Project: GA4 Ecommerce Analytics
-- Run directly in the BigQuery console; no setup needed (public dataset).
-- Cost note: no date filter, so each query scans the full 3-month sample.
-- File: 01_data_discovery.sql
-- Purpose: Explore the structure of the GA4 dataset
-- ===========================================================

-- ===========================================================
-- 1. Explore available event types
-- ===========================================================

-- Business question:
-- What user events are recorded in the dataset?

SELECT
    event_name,
    COUNT(*) AS events
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
GROUP BY event_name
ORDER BY events DESC;

-- Findings:
-- • The dataset contains 17 event types.
-- • The most frequent events are page_view and user_engagement.
-- • Purchase events are relatively rare compared to browsing events.


-- ===========================================================
-- 2. Explore user identifiers
-- ===========================================================

SELECT
    COUNT(*) AS total_events,
    COUNT(user_id) AS user_id_count,
    COUNT(user_pseudo_id) AS pseudo_user_count
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`;

-- Findings:
-- • user_id is not populated in the sample dataset.
-- • user_pseudo_id is available for every event.
-- • All user-level analysis in this project will be based on user_pseudo_id.


-- ===========================================================
-- 3. Count unique users
-- ===========================================================

-- Business question:
-- How many unique users are represented in the dataset?

SELECT
    COUNT(DISTINCT user_pseudo_id) AS unique_users
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`;

-- Findings:
-- • The dataset contains 270,154 unique users.
-- • Each user can generate multiple events during one or more sessions.
-- • Therefore, the number of events is much higher than the number of unique users.


-- ===========================================================
-- 4. Explore date range
-- ===========================================================

-- Business question:
-- What time period does the dataset cover?

SELECT
    MIN(event_date) AS first_date,
    MAX(event_date) AS last_date
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`;

-- Findings:
-- • The dataset covers the period from 2020-11-01 to 2021-01-31.
-- • The available data spans approximately three months.
-- • All further analysis in this project is limited to this time period.


-- ===========================================================
-- 5. Explore users by country
-- ===========================================================

-- Business question:
-- Which countries generate the largest number of users?

SELECT
    geo.country,
    COUNT(DISTINCT user_pseudo_id) AS unique_users
FROM 
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

GROUP BY
    geo.country

ORDER BY
    unique_users DESC

LIMIT 10;


-- Findings:
-- • The United States is the dominant market, representing the largest share of users.
-- • India and Canada are the next largest user segments, but with significantly smaller audiences.
-- • European countries show a more distributed user base without one dominant market.
-- • Country-level analysis will be extended later by comparing revenue and conversion performance,
--   because a large number of users does not necessarily mean high business value.


-- ===========================================================
-- 6. Explore users by device
-- ===========================================================

-- Business question:
-- Which devices are used by customers?

SELECT
    device.category,
    COUNT(DISTINCT user_pseudo_id) AS unique_users
FROM 
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

GROUP BY
    device.category

ORDER BY
    unique_users DESC;


-- Findings:
-- • Desktop is the most common device category among users.
-- • Mobile users represent a significant share of the audience,
--   therefore mobile experience should not be ignored.
-- • Tablet usage is relatively low compared to desktop and mobile.
-- • Device-level analysis will be used later to compare conversion rates
--   and purchasing behavior across platforms.


-- ===========================================================
-- 7. Explore sessions
-- ===========================================================

-- Business question:
-- How many sessions were generated during the analyzed period?

SELECT
    COUNT(*) AS total_sessions,
    COUNT(DISTINCT user_pseudo_id) AS users_with_sessions,
    ROUND(
        COUNT(*) / COUNT(DISTINCT user_pseudo_id),
        2
    ) AS avg_sessions_per_user

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

WHERE
    event_name = 'session_start';

-- Findings:
-- • The dataset contains 354,970 sessions generated by 267,116 users.
-- • On average, each user generated approximately 1.33 sessions during the analyzed period.
-- • The difference between users and sessions indicates that some users returned
--   to the website more than once.
-- • Further analysis will examine whether returning users demonstrate higher
--   engagement and purchase activity.


-- ===========================================================
-- 8. Explore traffic sources
-- ===========================================================

-- Business question:
-- Which traffic sources bring users to the website?

SELECT
    traffic_source.source,
    traffic_source.medium,
    COUNT(DISTINCT user_pseudo_id) AS unique_users

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

GROUP BY
    traffic_source.source,
    traffic_source.medium

ORDER BY
    unique_users DESC

LIMIT 10;

-- Findings:
-- • Organic search from Google is the largest acquisition channel,
--   bringing the highest number of users.
-- • Direct traffic is the second largest source, indicating users who
--   accessed the website without a tracked external source.
-- • Paid Google traffic (cpc) represents a smaller but measurable share
--   of acquisition.
-- • A significant amount of traffic is grouped into <Other> and
--   (data deleted) categories, which should be considered during further analysis.
-- • Traffic source performance should later be evaluated by revenue and
--   conversion rate, because user volume alone does not indicate business value.


-- Business question:
-- Which traffic sources generate the most sessions?

SELECT
    traffic_source.source,
    traffic_source.medium,
    COUNT(*) AS sessions

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

WHERE
    event_name = 'session_start'

GROUP BY
    traffic_source.source,
    traffic_source.medium

ORDER BY
    sessions DESC

LIMIT 10;

-- Findings:
-- • Session distribution follows a similar pattern to user acquisition.
-- • Google organic generates the highest number of sessions and represents
--   the main traffic acquisition channel.
-- • Direct traffic is the second largest source of sessions.
-- • The number of sessions is close to the number of users for most channels,
--   suggesting limited repeat visits during the analyzed period.
-- • Further analysis will compare traffic sources by purchase behavior and revenue.
