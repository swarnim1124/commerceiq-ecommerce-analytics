# Findings and recommendations

**Provenance.** All numbers come from the original author's BigQuery runs, read from SQL comments and Power BI screenshots (`assets/dashboard/`, `data/reference/dashboard_snapshot.json`). They were **not re-computed** in this edition because BigQuery was unreachable. Counts marked "exact" are printed in full at the source. Dollar figures marked "~" are read from chart labels rounded to $1K. After you run the corrected pipeline, totals may move slightly (see [data_quality.md](data_quality.md), items 1 and 2).

Period: 2020-11-01 to 2021-01-31. Store: Google Merchandise Store sample.

## Headline numbers

| Metric | Value | Precision |
|---|---:|---|
| Revenue | $360,837 | exact |
| Transactions (global distinct) | 4,452 | exact |
| AOV | $81.05 | exact (dashboard shows $80.85 because it uses 4,463) |
| Unique users | 270,154 | exact |
| Purchasing customers | 4,047 (1.5% of users) | exact |

## Findings

### 1. The biggest leak is before the cart, but the costliest one is at checkout
Of 61,252 users who viewed a product, 12,545 (20.5%) added to cart, 9,715 (77.4% of those) began checkout, and 4,419 (45.5% of those) purchased. View to purchase is 7.2%.
- Browsing to cart loses the most users in absolute terms (79.5% of viewers).
- Checkout to purchase loses 54.5% of users who had already entered checkout. Those are the highest-intent users, so each one recovered is worth more.
- Caveat: steps are not forced sequential, so this is a reach funnel, not a cohort funnel.

### 2. Returning customers are 11.5% of buyers and 24.5% of revenue
467 returning customers produced $88,473 ($189 each); 3,580 one-time customers produced $272,364 ($76 each). That is **2.5x revenue per customer**.
- This is revenue per customer, not AOV. The original README mislabelled it as AOV.
- "Returning" means 2+ orders within 3 months, including same-day repeats, so it measures repeat buying, not long-term loyalty.

### 3. Revenue is concentrated in the United States
The US contributes ~$160K, about 44% of revenue. The US, India and Canada together contribute ~$228K, about 63%. Beyond the top 3, no country exceeds ~$11K (3% each).

### 4. January revenue fell about 65% from December
~$143K (Nov), ~$161K (Dec), ~$57K (Jan). December was +13% on November. The original dashboard drew this line out of date order (Dec, Nov, Jan), which hid the November to December rise.
- With one holiday season in the data, seasonality cannot be separated from a real decline. This is a question for a longer date range, not a conclusion.

### 5. Paid search is about 2.5% of first-touch revenue, and a quarter of revenue sits in an ambiguous bucket
~$104K Organic, ~$86K Other, ~$84K Referral, ~$80K Direct, ~$9K Paid Search.
- The "Other" bucket in the original dashboard (~24% of revenue) mixes obfuscated `<Other>` / `(data deleted)` values with real channels. This edition separates them as **Unattributed**.
- There is no cost data, so ROI or ROAS cannot be calculated. A small revenue share does not show paid search is inefficient.
- Attribution is first-touch (the user's original source), not last-click.

### 6. Several popular products show thousands of views and no purchases
| Product | Viewers | Purchasers |
|---|---:|---:|
| Google F/C Long Sleeve Tee Charcoal | 9,640 | 0 |
| Google Women's Striped L/S | 9,541 | 0 |
| Google F/C Long Sleeve Tee Ash | 8,184 | 0 |
| Google Eco Tee Black | 7,683 | 0 |

Zero purchases from 7,000+ viewers each is more likely an availability or tracking/naming issue than weak demand. Separately, high-traffic items with low conversion include Google Navy Speckled Tee (13,696 viewers, 0.94%) and Google Campus Bike Eco Tee Navy (11,339 viewers, 0.36%).
- The top product, Google Zip Hoodie F/C, is ~$14K, about 4% of revenue. Revenue is spread across many apparel items rather than one hero product.

## Recommendations

Each is a hypothesis with a first test, not a promised outcome.

| # | Evidence | Action | How to know it worked |
|---|---|---|---|
| 1 | Checkout to purchase loses 54.5% (Finding 1) | Segment checkout abandoners by device and country; review payment and shipping steps for the largest segment. Needs `add_payment_info` / `add_shipping_info` events, which this analysis did not use | Checkout to purchase rate in an A/B test |
| 2 | 4 products with 7,683 to 9,640 viewers each and 0 purchases (Finding 6) | Run `analysis/32_product_analysis.sql` query 4 first: check stock, whether the `item_id` is purchased under another name, and whether `add_to_cart` fires | Either a fixed tracking gap or a stocked, selling product |
| 3 | Returning buyers are worth 2.5x (Finding 2) | Test a post-purchase email or reorder prompt aimed at one-time buyers | Share of buyers placing a second order within 30 days |
| 4 | 44% from one country (Finding 3) | Treat US performance as the baseline. Review India and Canada, which are large relative to their user counts per the original discovery notes | Revenue per user by country in the corrected marts |
| 5 | A quarter of revenue sits in the ambiguous "Other" bucket (Finding 5) | Re-run the corrected channel mart to see how much of "Other" is truly Unattributed, and use session-level source before comparing channel returns | Unattributed share is known and falls under 10% |
