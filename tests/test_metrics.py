import math
import unittest

import pandas as pd

from ga4_analytics import metrics


class SafeDivideTests(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(metrics.safe_divide(10, 4), 2.5)

    def test_zero_denominator_is_nan(self):
        self.assertTrue(math.isnan(metrics.safe_divide(1, 0)))

    def test_missing_denominator_is_nan(self):
        self.assertTrue(math.isnan(metrics.safe_divide(1, None)))
        self.assertTrue(math.isnan(metrics.safe_divide(1, float("nan"))))

    def test_aov(self):
        self.assertAlmostEqual(metrics.average_order_value(360837, 4452), 81.05, places=2)


class FunnelTests(unittest.TestCase):
    def setUp(self):
        self.funnel = metrics.funnel_table(
            [
                ("view_item", 61252),
                ("add_to_cart", 12545),
                ("begin_checkout", 9715),
                ("purchase", 4419),
            ]
        )

    def test_first_step_has_no_step_conversion(self):
        self.assertTrue(pd.isna(self.funnel["step_conversion"].iloc[0]))

    def test_step_conversion(self):
        self.assertAlmostEqual(self.funnel["step_conversion"].iloc[3], 4419 / 9715)

    def test_overall_conversion_matches_dashboard(self):
        self.assertAlmostEqual(self.funnel["pct_of_first"].iloc[3], 0.0721, places=4)

    def test_drop_off_is_complement(self):
        self.assertAlmostEqual(self.funnel["drop_off"].iloc[1], 1 - 12545 / 61252)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            metrics.funnel_table([])


class SegmentTests(unittest.TestCase):
    def test_shares_sum_to_one_and_value_ratio(self):
        seg = metrics.segment_summary(
            pd.DataFrame(
                {
                    "segment": ["one", "ret"],
                    "customers": [3580, 467],
                    "revenue": [272364.0, 88473.0],
                }
            )
        )
        self.assertAlmostEqual(seg["customer_share"].sum(), 1.0)
        self.assertAlmostEqual(seg["revenue_share"].sum(), 1.0)
        ratio = seg["revenue_per_customer"].iloc[1] / seg["revenue_per_customer"].iloc[0]
        self.assertAlmostEqual(ratio, 2.49, places=2)


class MiscTests(unittest.TestCase):
    def test_top_n_share(self):
        s = pd.Series([50, 30, 10, 10])
        self.assertAlmostEqual(metrics.top_n_share(s, 2), 0.8)
        with self.assertRaises(ValueError):
            metrics.top_n_share(s, 0)

    def test_period_change_sorts_chronologically(self):
        # Deliberately unsorted, like the original dashboard's revenue-sorted line.
        s = pd.Series({"2020-12": 161.0, "2020-11": 143.0, "2021-01": 57.0})
        change = metrics.period_change(s)
        self.assertAlmostEqual(change["2020-12"], 161 / 143 - 1)
        self.assertAlmostEqual(change["2021-01"], 57 / 161 - 1)
        self.assertTrue(pd.isna(change["2020-11"]))

    def test_flag_low_volume(self):
        out = metrics.flag_low_volume(pd.DataFrame({"v": [10, 100, 500]}), "v", 100)
        self.assertEqual(out["is_low_volume"].tolist(), [True, False, False])

    def test_implied_duplicates(self):
        self.assertEqual(metrics.implied_duplicate_transactions(4463, 4452), 11)
        self.assertEqual(metrics.implied_duplicate_transactions(10, 12), 0)


if __name__ == "__main__":
    unittest.main()
