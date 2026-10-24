import unittest

import pandas as pd

from ga4_analytics import quality


def good_frames():
    monthly = pd.DataFrame(
        {"month": ["2020-11", "2020-12"], "transactions": [2, 1], "revenue": [150.0, 50.0]}
    )
    customers = pd.DataFrame(
        {"user_pseudo_id": ["a", "b"], "orders": [2, 1], "revenue": [150.0, 50.0]}
    )
    country = pd.DataFrame({"country": ["US", "IN"], "revenue": [120.0, 80.0]})
    funnel = pd.DataFrame({"event_name": ["view_item", "purchase"], "users": [10, 3]})
    return {
        "revenue_monthly": monthly,
        "customer_metrics": customers,
        "revenue_by_country": country,
        "funnel_metrics": funnel,
    }


class CheckTests(unittest.TestCase):
    def test_unique_detects_duplicates(self):
        frame = pd.DataFrame({"k": [1, 1, 2]})
        self.assertFalse(quality.check_unique("t", frame, "k").passed)
        self.assertTrue(quality.check_unique("t", frame.iloc[[0, 2]], "k").passed)

    def test_positive(self):
        self.assertFalse(quality.check_positive("t", pd.DataFrame({"x": [1, 0]}), "x").passed)

    def test_no_nulls(self):
        self.assertFalse(quality.check_no_nulls("t", pd.DataFrame({"x": [1, None]}), ["x"]).passed)

    def test_reconciles_tolerance(self):
        self.assertTrue(quality.check_reconciles("r", 100.0, 100.04).passed)
        self.assertFalse(quality.check_reconciles("r", 100.0, 101.0).passed)

    def test_sorted(self):
        self.assertTrue(quality.check_sorted("s", pd.Series(["2020-11", "2020-12"])).passed)
        self.assertFalse(quality.check_sorted("s", pd.Series(["2020-12", "2020-11"])).passed)

    def test_columns(self):
        self.assertFalse(quality.check_columns("t", pd.DataFrame({"a": [1]}), ["a", "b"]).passed)


class ValidateExportsTests(unittest.TestCase):
    def test_clean_data_passes(self):
        results = quality.validate_exports(good_frames())
        self.assertEqual(quality.failures(results), [])
        self.assertGreaterEqual(len(results), 8)

    def test_revenue_mismatch_is_caught(self):
        frames = good_frames()
        frames["revenue_by_country"].loc[0, "revenue"] = 500.0
        names = [r.name for r in quality.failures(quality.validate_exports(frames))]
        self.assertIn("revenue_by_country revenue = monthly revenue", names)

    def test_double_counted_orders_are_caught(self):
        frames = good_frames()
        frames["customer_metrics"].loc[0, "orders"] = 3
        names = [r.name for r in quality.failures(quality.validate_exports(frames))]
        self.assertIn("customer orders = monthly transactions", names)

    def test_funnel_with_fewer_purchasers_than_customers_fails(self):
        frames = good_frames()
        frames["funnel_metrics"].loc[1, "users"] = 1
        names = [r.name for r in quality.failures(quality.validate_exports(frames))]
        self.assertIn("funnel purchasers cover customers", names)

    def test_partial_inputs_do_not_crash(self):
        self.assertEqual(quality.validate_exports({}), [])


class SqlOutputTests(unittest.TestCase):
    def test_warn_failures_are_not_errors(self):
        frame = pd.DataFrame(
            {
                "check_name": ["a", "b"],
                "severity": ["warn", "error"],
                "passed": [False, True],
                "observed": ["1", "0"],
            }
        )
        results = quality.from_sql_check_output(frame)
        self.assertEqual(len(results), 2)
        self.assertEqual(quality.failures(results), [])


if __name__ == "__main__":
    unittest.main()
