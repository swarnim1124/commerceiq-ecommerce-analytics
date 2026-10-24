"""Build README figures from either the reference snapshot or exported mart CSVs."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from . import metrics  # noqa: E402

ACCENT = "#1f5fbf"
NEUTRAL = "#9aa7b8"
INK = "#1b2430"
MUTED = "#5b6676"
GRID = "#e3e8ef"


def load_snapshot(path: Path) -> dict:
    """Read the reference snapshot JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def frames_from_snapshot(snapshot: dict) -> dict:
    """Convert the snapshot into the frames the figure functions expect."""
    monthly = pd.DataFrame(
        sorted(snapshot["rounded_k"]["monthly_revenue_k"].items()), columns=["month", "revenue"]
    )
    monthly["revenue"] = monthly["revenue"] * 1000.0
    funnel = metrics.funnel_table([(s["step"], s["users"]) for s in snapshot["exact"]["funnel"]])
    segments = metrics.segment_summary(pd.DataFrame(snapshot["exact"]["customer_segments"]))
    return {
        "monthly": monthly,
        "funnel": funnel,
        "segments": segments,
        "source_note": "Source: original BigQuery run (data/reference/dashboard_snapshot.json).",
    }


def frames_from_exports(directory: Path) -> dict:
    """Build the same frames from CSVs written by `ga4-analytics export`."""
    monthly = pd.read_csv(directory / "revenue_monthly.csv").sort_values("month")
    funnel_raw = pd.read_csv(directory / "funnel_metrics.csv").sort_values("funnel_step")
    funnel = metrics.funnel_table(
        list(zip(funnel_raw["event_name"], funnel_raw["users"], strict=True))
    )
    customers = pd.read_csv(directory / "customer_metrics.csv")
    grouped = (
        customers.groupby("customer_type")
        .agg(customers=("user_pseudo_id", "count"), revenue=("revenue", "sum"))
        .reset_index()
        .rename(columns={"customer_type": "segment"})
    )
    return {
        "monthly": monthly[["month", "revenue"]],
        "funnel": funnel,
        "segments": metrics.segment_summary(grouped),
        "source_note": "Source: BigQuery export of the GA4 sample (Nov 2020 to Jan 2021).",
    }


def _t(text: str) -> str:
    """Escape dollar signs so matplotlib does not treat them as math text."""
    return text.replace("$", r"\$")


def _style(ax: plt.Axes) -> None:
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)


def _finish(
    fig: plt.Figure,
    ax: plt.Axes,
    title: str,
    subtitle: str,
    note: str,
    path: Path,
    left: float = 0.1,
) -> None:
    fig.text(0.04, 0.95, _t(title), fontsize=15, fontweight="bold", color=INK, va="top")
    fig.text(0.04, 0.885, _t(subtitle), fontsize=10.5, color=MUTED, va="top")
    fig.text(0.04, 0.02, _t(note), fontsize=8.5, color=MUTED)
    fig.subplots_adjust(top=0.78, bottom=0.12, left=left, right=0.96)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)


def monthly_revenue_figure(frames: dict, path: Path) -> None:
    """Chronological monthly revenue bars (fixes the revenue-sorted trend line)."""
    monthly = frames["monthly"].sort_values("month")
    fig, ax = plt.subplots(figsize=(8, 4.6))
    bars = ax.bar(monthly["month"], monthly["revenue"], color=ACCENT, width=0.5)
    for bar, value in zip(bars, monthly["revenue"], strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + monthly["revenue"].max() * 0.02,
            _t(f"${value / 1000:,.0f}K"),
            ha="center",
            color=INK,
            fontsize=11,
        )
    ax.set_yticks([])
    ax.set_ylim(0, monthly["revenue"].max() * 1.15)
    _style(ax)
    change = metrics.period_change(monthly.set_index("month")["revenue"]).dropna()
    peak = monthly.loc[monthly["revenue"].idxmax(), "month"]
    last = f"{change.iloc[-1]:+.0%}"
    _finish(
        fig,
        ax,
        f"Monthly revenue peaked in {peak}",
        f"Months in chronological order. Latest month vs previous month: {last}.",
        frames["source_note"] + " Monthly values may be rounded.",
        path,
    )


def funnel_figure(frames: dict, path: Path) -> None:
    """Horizontal funnel with step-to-step conversion."""
    funnel = frames["funnel"]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    positions = list(range(len(funnel)))[::-1]
    ax.barh(positions, funnel["users"], color=ACCENT, height=0.55)
    for pos, row in zip(positions, funnel.itertuples(), strict=True):
        ax.text(
            row.users + funnel["users"].max() * 0.015,
            pos,
            f"{row.users:,}",
            va="center",
            color=INK,
            fontsize=10.5,
        )
        if pd.notna(row.step_conversion):
            ax.text(
                funnel["users"].max() * 0.99,
                pos,
                f"{row.step_conversion:.1%} of previous step",
                va="center",
                ha="right",
                color=MUTED,
                fontsize=9,
            )
    ax.set_yticks(positions, funnel["step"], color=INK)
    ax.set_xticks([])
    _style(ax)
    overall = funnel["users"].iloc[-1] / funnel["users"].iloc[0]
    lost = 1 - funnel["step_conversion"].iloc[1]
    _finish(
        fig,
        ax,
        f"{lost:.0%} of product viewers never add to cart",
        f"Users reaching each step (distinct users, steps not forced sequential). "
        f"View to purchase: {overall:.1%}.",
        frames["source_note"],
        path,
        left=0.2,
    )


def segments_figure(frames: dict, path: Path) -> None:
    """Customer share versus revenue share by segment (100% bars)."""
    seg = frames["segments"].set_index("segment")
    names = list(seg.index)
    colors = [NEUTRAL, ACCENT]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    for row, column in enumerate(["revenue_share", "customer_share"]):
        left = 0.0
        for name, color in zip(names, colors, strict=False):
            width = float(seg.loc[name, column])
            ax.barh(row, width, left=left, color=color, height=0.5, edgecolor="white", linewidth=2)
            ax.text(
                left + width / 2,
                row,
                f"{name.split()[0]}\n{width:.1%}",
                ha="center",
                va="center",
                color="white" if color == ACCENT else INK,
                fontsize=9.5,
            )
            left += width
    ax.set_yticks([0, 1], ["Revenue", "Customers"], color=INK)
    ax.set_xticks([])
    ax.set_xlim(0, 1)
    _style(ax)
    ret = seg.loc[names[-1]]
    one = seg.loc[names[0]]
    ratio = ret["revenue_per_customer"] / one["revenue_per_customer"]
    ret_customers, ret_revenue = ret["customer_share"], ret["revenue_share"]
    _finish(
        fig,
        ax,
        f"Returning customers: {ret_customers:.1%} of buyers, {ret_revenue:.1%} of revenue",
        f"Revenue per customer: ${ret['revenue_per_customer']:,.0f} returning vs "
        f"${one['revenue_per_customer']:,.0f} one-time ({ratio:.1f}x).",
        frames["source_note"],
        path,
        left=0.14,
    )


def build_figures(frames: dict, out_dir: Path) -> list[Path]:
    """Write all figures and return their paths."""
    targets = {
        "monthly_revenue.png": monthly_revenue_figure,
        "funnel.png": funnel_figure,
        "customer_segments.png": segments_figure,
    }
    paths = []
    for name, func in targets.items():
        path = out_dir / name
        func(frames, path)
        paths.append(path)
    return paths
