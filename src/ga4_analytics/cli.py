"""Command line interface: `ga4-analytics <command>`."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import quality, report, sql_runner
from .config import ConfigError, Settings

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"
PROCESSED_DIR = ROOT / "data" / "processed"
SNAPSHOT = ROOT / "data" / "reference" / "dashboard_snapshot.json"
FIGURES_DIR = ROOT / "assets" / "figures"

log = logging.getLogger("ga4_analytics")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ga4-analytics", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="build staging and mart tables in BigQuery")
    run.add_argument("--dry-run", action="store_true", help="estimate bytes scanned only")

    sub.add_parser("check", help="run SQL data-quality checks; exit 1 on any error")
    sub.add_parser("export", help="download mart tables to data/processed/*.csv")
    sub.add_parser("validate", help="cross-check exported CSVs offline")

    rep = sub.add_parser("report", help="build figures into assets/figures")
    rep.add_argument("--source", choices=["snapshot", "exports"], default="snapshot")
    return parser


def _print(results: list[quality.CheckResult]) -> int:
    for r in results:
        mark = "PASS" if r.passed else "FAIL"
        print(f"[{mark}] ({r.severity}) {r.name} {r.detail}")
    bad = quality.failures(results)
    print(f"\n{len(results) - len(bad)}/{len(results)} checks ok, {len(bad)} error(s)")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    try:
        if args.command == "report":
            if args.source == "snapshot":
                frames = report.frames_from_snapshot(report.load_snapshot(SNAPSHOT))
            else:
                frames = report.frames_from_exports(PROCESSED_DIR)
            for path in report.build_figures(frames, FIGURES_DIR):
                print(f"wrote {path}")
            return 0

        if args.command == "validate":
            import pandas as pd

            frames = {p.stem: pd.read_csv(p) for p in PROCESSED_DIR.glob("*.csv")}
            if not frames:
                print("No CSVs in data/processed. Run `ga4-analytics export` first.")
                return 2
            return _print(quality.validate_exports(frames))

        settings = Settings.from_env()
        client = sql_runner.get_client(settings)
        if args.command == "run":
            if not args.dry_run:
                sql_runner.ensure_dataset(client, settings)
            files = sql_runner.sql_files(SQL_DIR, "pipeline")
            sql_runner.run_files(client, settings, files, dry_run=args.dry_run)
            return 0
        if args.command == "check":
            return _print(
                quality.from_sql_check_output(sql_runner.run_checks(client, settings, SQL_DIR))
            )
        if args.command == "export":
            sql_runner.export_tables(client, settings, PROCESSED_DIR)
            return 0
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
