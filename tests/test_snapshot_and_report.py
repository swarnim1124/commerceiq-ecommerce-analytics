import json
import tempfile
import unittest
from pathlib import Path

from ga4_analytics import report

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "reference" / "dashboard_snapshot.json"


class SnapshotConsistencyTests(unittest.TestCase):
    """The transcribed numbers must agree with each other, which catches typos."""

    @classmethod
    def setUpClass(cls):
        cls.s = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    def test_segments_sum_to_total_revenue_and_customers(self):
        seg = self.s["exact"]["customer_segments"]
        self.assertEqual(sum(x["revenue"] for x in seg), self.s["exact"]["total_revenue"])
        self.assertEqual(sum(x["customers"] for x in seg), self.s["exact"]["total_customers"])

    def test_monthly_rounded_values_sum_to_total_within_rounding(self):
        monthly = self.s["rounded_k"]["monthly_revenue_k"]
        self.assertLessEqual(
            abs(sum(monthly.values()) * 1000 - self.s["exact"]["total_revenue"]), 1500
        )

    def test_channels_sum_to_total_within_rounding(self):
        channels = self.s["rounded_k"]["channel_revenue_k"]
        self.assertLessEqual(
            abs(sum(channels.values()) * 1000 - self.s["exact"]["total_revenue"]), 2500
        )

    def test_top_countries_do_not_exceed_total(self):
        countries = self.s["rounded_k"]["top_countries_revenue_k"]
        self.assertLessEqual(
            sum(countries.values()) * 1000, self.s["exact"]["total_revenue"] + 5000
        )

    def test_aov_matches_revenue_over_distinct_transactions(self):
        e = self.s["exact"]
        self.assertAlmostEqual(
            e["total_revenue"] / e["transactions_global_distinct"],
            e["average_order_value_global"],
            2,
        )

    def test_dashboard_transaction_count_is_larger_than_global_distinct(self):
        e = self.s["exact"]
        self.assertGreater(
            e["transactions_sum_of_monthly_distinct"], e["transactions_global_distinct"]
        )

    def test_funnel_purchasers_exceed_customers(self):
        e = self.s["exact"]
        self.assertGreater(e["funnel"][-1]["users"], e["total_customers"])

    def test_zero_purchase_products_really_have_zero(self):
        for row in self.s["product_observations"]["zero_purchase_high_view"]:
            self.assertEqual(row["purchased_users"], 0)
            self.assertGreaterEqual(row["viewed_users"], 500)


class ReportTests(unittest.TestCase):
    def test_figures_are_written(self):
        frames = report.frames_from_snapshot(report.load_snapshot(SNAPSHOT))
        with tempfile.TemporaryDirectory() as tmp:
            paths = report.build_figures(frames, Path(tmp))
            self.assertEqual(len(paths), 3)
            for p in paths:
                self.assertGreater(p.stat().st_size, 5000)

    def test_monthly_frame_is_chronological(self):
        frames = report.frames_from_snapshot(report.load_snapshot(SNAPSHOT))
        self.assertEqual(frames["monthly"]["month"].tolist(), sorted(frames["monthly"]["month"]))


if __name__ == "__main__":
    unittest.main()


class ReadmeLinkTests(unittest.TestCase):
    """Every relative link and image in the README and docs must resolve."""

    def test_relative_links_exist(self):
        import re

        pattern = re.compile(r"(?:\]\(|src=\")(?!https?:|#|mailto:)([^)\"#]+)")
        for md in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]:
            for target in pattern.findall(md.read_text(encoding="utf-8")):
                resolved = (md.parent / target).resolve()
                self.assertTrue(resolved.exists(), f"{md.name} links to missing {target}")
