"""Pure KPI functions. No I/O, so they are easy to test and reuse."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def safe_divide(numerator: float, denominator: float) -> float:
    """Return numerator / denominator, or NaN when the denominator is 0 or missing."""
    if denominator is None or pd.isna(denominator) or denominator == 0:
        return float("nan")
    return float(numerator) / float(denominator)


def average_order_value(revenue: float, transactions: float) -> float:
    """AOV = revenue / distinct transactions."""
    return safe_divide(revenue, transactions)


def funnel_table(steps: Sequence[tuple[str, int]]) -> pd.DataFrame:
    """Build funnel metrics from ordered (step_name, users) pairs.

    Columns: users, step_conversion (vs previous step), pct_of_first,
    drop_off (1 - step_conversion). The first step has no step_conversion.
    """
    if not steps:
        raise ValueError("steps must not be empty")
    frame = pd.DataFrame(steps, columns=["step", "users"])
    first = frame["users"].iloc[0]
    frame["step_conversion"] = frame["users"] / frame["users"].shift(1)
    frame["pct_of_first"] = frame["users"] / first if first else float("nan")
    frame["drop_off"] = 1 - frame["step_conversion"]
    return frame


def segment_summary(segments: pd.DataFrame) -> pd.DataFrame:
    """Summarise customer segments.

    Input columns: segment, customers, revenue. Adds customer_share,
    revenue_share and revenue_per_customer.
    """
    out = segments.copy()
    out["customer_share"] = out["customers"] / out["customers"].sum()
    out["revenue_share"] = out["revenue"] / out["revenue"].sum()
    out["revenue_per_customer"] = out["revenue"] / out["customers"]
    return out


def share_of_total(values: pd.Series) -> pd.Series:
    """Each value divided by the series total."""
    return values / values.sum()


def top_n_share(values: pd.Series, n: int) -> float:
    """Share of the total held by the n largest values."""
    if n < 1:
        raise ValueError("n must be >= 1")
    return float(values.nlargest(n).sum() / values.sum())


def period_change(values: pd.Series) -> pd.Series:
    """Relative change versus the previous period, after sorting by index.

    Sorting guards against the out-of-order trend line the original dashboard drew.
    """
    return values.sort_index().pct_change()


def flag_low_volume(frame: pd.DataFrame, column: str, threshold: int) -> pd.DataFrame:
    """Add is_low_volume = frame[column] < threshold."""
    out = frame.copy()
    out["is_low_volume"] = out[column] < threshold
    return out


def implied_duplicate_transactions(monthly_distinct_sum: int, global_distinct: int) -> int:
    """Lower bound on duplicated purchase events.

    Distinct counts per month can only add up to more than the global distinct
    count if some transaction_id appears in more than one month.
    """
    return max(0, int(monthly_distinct_sum) - int(global_distinct))
