"""Render and execute the SQL files in `sql/` against BigQuery."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .config import Settings

log = logging.getLogger(__name__)

PLACEHOLDER = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")

#: Tables written by the pipeline that are exported for BI tools.
MART_TABLES = (
    "revenue_monthly",
    "revenue_by_country",
    "channel_performance",
    "source_medium_performance",
    "device_performance",
    "product_performance",
    "customer_metrics",
    "funnel_metrics",
    "product_conversion",
)


def render_sql(text: str, settings: Settings) -> str:
    """Replace `{{ name }}` placeholders; unknown names raise KeyError."""
    values = settings.template_values()

    def substitute(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in values:
            raise KeyError(f"Unknown SQL placeholder: {name}")
        return values[name]

    return PLACEHOLDER.sub(substitute, text)


def split_statements(sql: str) -> list[str]:
    """Split a script on semicolons that end a line; drop comment-only chunks."""
    statements = []
    for chunk in re.split(r";[ \t]*(?:\n|$)", sql):
        body = "\n".join(
            line
            for line in chunk.splitlines()
            if line.strip() and not line.strip().startswith("--")
        )
        if body.strip():
            statements.append(chunk.strip())
    return statements


def sql_files(sql_dir: Path, subdir: str) -> list[Path]:
    """SQL files in `sql_dir/subdir`, in execution (filename) order."""
    return sorted((sql_dir / subdir).glob("*.sql"))


def get_client(settings: Settings) -> Any:
    """Create a BigQuery client; the dependency is optional for offline use."""
    try:
        from google.cloud import bigquery
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "google-cloud-bigquery is not installed. Run: pip install -r requirements.txt"
        ) from exc
    return bigquery.Client(project=settings.project, location=settings.location)


def ensure_dataset(client: Any, settings: Settings) -> None:
    """Create the destination dataset if it does not exist."""
    from google.cloud import bigquery  # pragma: no cover

    dataset = bigquery.Dataset(f"{settings.project}.{settings.dataset}")  # pragma: no cover
    dataset.location = settings.location  # pragma: no cover
    client.create_dataset(dataset, exists_ok=True)  # pragma: no cover


def run_files(client: Any, settings: Settings, files: list[Path], dry_run: bool = False) -> None:
    """Execute each file's statements in order. With dry_run, only estimate scan size.

    Dry runs of statements that read tables created by earlier steps fail with
    NotFound until those tables exist; those are reported and skipped.
    """
    from google.cloud import bigquery  # pragma: no cover

    for path in files:  # pragma: no cover - needs BigQuery
        for statement in split_statements(render_sql(path.read_text(encoding="utf-8"), settings)):
            config = bigquery.QueryJobConfig(dry_run=dry_run, use_query_cache=False)
            try:
                job = client.query(statement, job_config=config)
                if dry_run:
                    log.info(
                        "%s: would process %.1f MB", path.name, job.total_bytes_processed / 1e6
                    )
                else:
                    job.result()
                    log.info("%s: done", path.name)
            except Exception as exc:
                if dry_run and exc.__class__.__name__ == "NotFound":
                    log.info("%s: skipped dry run (depends on tables not built yet)", path.name)
                    continue
                raise


def run_checks(client: Any, settings: Settings, sql_dir: Path) -> pd.DataFrame:
    """Run the quality-check query and return one row per check."""
    path = sql_files(sql_dir, "quality")[0]
    sql = render_sql(path.read_text(encoding="utf-8"), settings)
    return client.query(sql).to_dataframe()


def export_tables(client: Any, settings: Settings, out_dir: Path) -> list[Path]:
    """Download each mart table to `out_dir/<table>.csv`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for table in MART_TABLES:
        frame = client.query(f"SELECT * FROM `{settings.dataset_ref}.{table}`").to_dataframe()
        target = out_dir / f"{table}.csv"
        frame.to_csv(target, index=False)
        log.info("exported %s (%d rows)", target, len(frame))
        written.append(target)
    return written
