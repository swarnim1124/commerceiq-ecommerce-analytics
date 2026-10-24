# Data source

| | |
|---|---|
| Dataset | `bigquery-public-data.ga4_obfuscated_sample_ecommerce` |
| Tables | Daily sharded event tables `events_YYYYMMDD`, queried with the wildcard `events_*` |
| Store | Google Merchandise Store (an obfuscated sample of real GA4 data) |
| Period | 2020-11-01 to 2021-01-31 (92 days) |
| Grain | One row per GA4 event |
| Access | Free to query with any Google Cloud project; queries are billed to your project (the first 1 TB per month is free) |

Browse it in the BigQuery console: <https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=ga4_obfuscated_sample_ecommerce&page=dataset>

## Properties that shape the analysis

- **Obfuscated.** Google removes or masks some values. `traffic_source` often shows `<Other>` or `(data deleted)`. Those rows cannot be attributed, so this project reports them as **Unattributed** instead of mixing them with real "Other" channels.
- **`traffic_source` is first touch.** In the GA4 export it is the source that first acquired the user, not the source of the session that bought. Channel revenue here is first-touch attribution.
- **No `user_id`.** Users are identified by `user_pseudo_id`, a browser/device identifier. One person on two devices counts twice, so "customers" means "purchasing visitors".
- **Three months, one holiday season.** Seasonality cannot be separated from trend, and "returning customer" only means "bought twice in this window".
- **Sample only.** Counts are not representative of the live store.

## Cost control

Every pipeline query filters `_TABLE_SUFFIX` to the configured date range so BigQuery only reads the shards it needs. Use `ga4-analytics run --dry-run` to see bytes scanned before running anything.
