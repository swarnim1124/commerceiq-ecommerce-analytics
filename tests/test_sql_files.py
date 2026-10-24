"""Structural checks on every SQL file, plus a real BigQuery-dialect parse when sqlglot exists."""

import re
import unittest
from pathlib import Path

from ga4_analytics import sql_runner
from ga4_analytics.config import Settings

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
FILES = sorted(SQL_DIR.rglob("*.sql"))
SETTINGS = Settings(project="demo-project-123")
TEMPLATED = [f for f in FILES if f.parent.name != "exploration"]

try:
    import sqlglot
except ImportError:  # sqlglot is a dev dependency; CI installs it
    sqlglot = None


class SqlFileTests(unittest.TestCase):
    def test_files_found(self):
        self.assertGreaterEqual(len(FILES), 15)

    def test_no_hardcoded_personal_project_or_select_star(self):
        for f in FILES:
            text = f.read_text(encoding="utf-8")
            self.assertNotIn("504613", text, f.name)
            code = "\n".join(
                line for line in text.splitlines() if not line.strip().startswith("--")
            )
            self.assertIsNone(re.search(r"select\s+\*", code, re.I), f"SELECT * in {f.name}")

    def test_balanced_brackets_and_backticks(self):
        for f in FILES:
            code = "\n".join(
                line
                for line in f.read_text(encoding="utf-8").splitlines()
                if not line.strip().startswith("--")
            )
            self.assertEqual(code.count("("), code.count(")"), f.name)
            self.assertEqual(code.count("`") % 2, 0, f.name)

    def test_templated_files_render_completely(self):
        for f in TEMPLATED:
            rendered = sql_runner.render_sql(f.read_text(encoding="utf-8"), SETTINGS)
            self.assertNotIn("{{", rendered, f.name)

    def test_pipeline_scans_are_date_bounded(self):
        for f in sql_runner.sql_files(SQL_DIR, "pipeline"):
            text = f.read_text(encoding="utf-8")
            if "{{ source_table }}" in text:
                self.assertIn("_TABLE_SUFFIX BETWEEN", text, f.name)

    def test_pipeline_files_are_ordered_and_unique(self):
        names = [f.name for f in sql_runner.sql_files(SQL_DIR, "pipeline")]
        self.assertEqual(names, sorted(names))
        self.assertEqual(len({n[:2] for n in names}), len(names))

    def test_every_exported_table_is_created_by_the_pipeline(self):
        created = " ".join(
            f.read_text(encoding="utf-8") for f in sql_runner.sql_files(SQL_DIR, "pipeline")
        )
        for table in sql_runner.MART_TABLES:
            self.assertRegex(created, rf"\.{table}`\s+AS")

    @unittest.skipIf(sqlglot is None, "sqlglot not installed; runs in CI")
    def test_parses_as_bigquery(self):
        for f in FILES:
            rendered = sql_runner.render_sql(f.read_text(encoding="utf-8"), SETTINGS)
            for statement in sql_runner.split_statements(rendered):
                sqlglot.parse_one(statement, read="bigquery")


if __name__ == "__main__":
    unittest.main()
