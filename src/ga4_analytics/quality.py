"""Data-quality checks for exported mart tables and for the SQL check output."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    severity: str = "error"


def check_columns(name: str, frame: pd.DataFrame, required: Iterable[str]) -> CheckResult:
    missing = [c for c in required if c not in frame.columns]
    return CheckResult(f"{name}: required columns", not missing, f"missing={missing}")


def check_unique(name: str, frame: pd.DataFrame, column: str) -> CheckResult:
    dupes = int(frame[column].duplicated().sum())
    return CheckResult(f"{name}: {column} is unique", dupes == 0, f"duplicates={dupes}")


def check_no_nulls(name: str, frame: pd.DataFrame, columns: Iterable[str]) -> CheckResult:
    nulls = {c: int(frame[c].isna().sum()) for c in columns}
    bad = {c: n for c, n in nulls.items() if n}
    return CheckResult(f"{name}: no nulls in {list(nulls)}", not bad, f"nulls={bad}")


def check_positive(name: str, frame: pd.DataFrame, column: str) -> CheckResult:
    bad = int((frame[column] <= 0).sum())
    return CheckResult(f"{name}: {column} > 0", bad == 0, f"non_positive={bad}")


def check_reconciles(
    name: str, left: float, right: float, tolerance: float = 0.05, severity: str = "error"
) -> CheckResult:
    diff = float(left) - float(right)
    return CheckResult(name, abs(diff) <= tolerance, f"diff={diff:.2f}", severity)


def check_sorted(name: str, values: pd.Series) -> CheckResult:
    ok = bool(values.is_monotonic_increasing)
    return CheckResult(name, ok, "chronological" if ok else "out of order")


def validate_exports(frames: dict[str, pd.DataFrame]) -> list[CheckResult]:
    """Validate exported mart tables against each other.

    Expects keys: revenue_monthly, revenue_by_country, channel_performance,
    device_performance, customer_metrics, funnel_metrics (any subset is fine;
    only checks whose inputs are present are run).
    """
    results: list[CheckResult] = []
    monthly = frames.get("revenue_monthly")
    total_revenue = None
    total_txn = None
    if monthly is not None:
        results += [
            check_columns("revenue_monthly", monthly, ["month", "transactions", "revenue"]),
            check_unique("revenue_monthly", monthly, "month"),
            check_positive("revenue_monthly", monthly, "revenue"),
        ]
        total_revenue = float(monthly["revenue"].sum())
        total_txn = int(monthly["transactions"].sum())

    customers = frames.get("customer_metrics")
    if customers is not None:
        results += [
            check_columns("customer_metrics", customers, ["user_pseudo_id", "orders", "revenue"]),
            check_unique("customer_metrics", customers, "user_pseudo_id"),
        ]
        if total_revenue is not None:
            results.append(
                check_reconciles(
                    "customer revenue = monthly revenue", customers["revenue"].sum(), total_revenue
                )
            )
        if total_txn is not None:
            results.append(
                check_reconciles(
                    "customer orders = monthly transactions",
                    customers["orders"].sum(),
                    total_txn,
                    tolerance=0,
                )
            )

    for table in ("revenue_by_country", "channel_performance", "device_performance"):
        frame = frames.get(table)
        if frame is not None and total_revenue is not None:
            results.append(
                check_reconciles(
                    f"{table} revenue = monthly revenue", frame["revenue"].sum(), total_revenue
                )
            )

    funnel = frames.get("funnel_metrics")
    if funnel is not None and customers is not None:
        purchasers = int(funnel.loc[funnel["event_name"] == "purchase", "users"].iloc[0])
        results.append(
            CheckResult(
                "funnel purchasers cover customers",
                purchasers >= len(customers),
                f"funnel={purchasers}, customers={len(customers)}",
            )
        )
    return results


def failures(results: Iterable[CheckResult]) -> list[CheckResult]:
    """Failed checks with severity 'error'."""
    return [r for r in results if not r.passed and r.severity == "error"]


def from_sql_check_output(frame: pd.DataFrame) -> list[CheckResult]:
    """Convert the output of sql/quality/90_pipeline_checks.sql into CheckResults."""
    return [
        CheckResult(str(r.check_name), bool(r.passed), str(r.observed), str(r.severity))
        for r in frame.itertuples()
    ]
