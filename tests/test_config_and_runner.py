import unittest

from ga4_analytics import sql_runner
from ga4_analytics.config import ConfigError, Settings


def settings(**kw):
    return Settings(project=kw.pop("project", "demo-project-123"), **kw)


class SettingsTests(unittest.TestCase):
    def test_from_env_requires_project(self):
        with self.assertRaises(ConfigError):
            Settings.from_env({})

    def test_from_env_defaults(self):
        s = Settings.from_env({"GA4_GCP_PROJECT_ID": "demo-project-123"})
        self.assertEqual(s.dataset_ref, "demo-project-123.ga4_ecommerce_analysis")
        self.assertEqual((s.start_date, s.end_date), ("20201101", "20210131"))

    def test_invalid_project_rejected(self):
        with self.assertRaises(ConfigError):
            Settings(project="Bad Project!")

    def test_bad_dates_rejected(self):
        with self.assertRaises(ConfigError):
            settings(start_date="2020-11-01")
        with self.assertRaises(ConfigError):
            settings(start_date="20210201", end_date="20210131")


class RenderTests(unittest.TestCase):
    def test_render_replaces_placeholders(self):
        out = sql_runner.render_sql(
            "SELECT 1 FROM `{{ dataset_ref }}.t` -- {{start_date}}", settings()
        )
        self.assertEqual(
            out, "SELECT 1 FROM `demo-project-123.ga4_ecommerce_analysis.t` -- 20201101"
        )

    def test_unknown_placeholder_raises(self):
        with self.assertRaises(KeyError):
            sql_runner.render_sql("{{ nope }}", settings())

    def test_split_statements_ignores_comment_only_chunks(self):
        sql = "-- header\nSELECT 1;\n\n-- note only\n;\nSELECT 2;\n"
        self.assertEqual(sql_runner.split_statements(sql), ["-- header\nSELECT 1", "SELECT 2"])


if __name__ == "__main__":
    unittest.main()
