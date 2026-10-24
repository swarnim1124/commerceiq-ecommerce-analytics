"""Project settings read from environment variables (see .env.example)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime

DEFAULT_SOURCE_TABLE = "bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*"
DEFAULT_START_DATE = "20201101"
DEFAULT_END_DATE = "20210131"

_PROJECT_ID = re.compile(r"^[a-z][a-z0-9\-]{4,28}[a-z0-9]$")
_DATASET = re.compile(r"^[A-Za-z0-9_]{1,1024}$")


class ConfigError(ValueError):
    """Raised when a setting is missing or malformed."""


def _check_date(value: str, name: str) -> str:
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError as exc:
        raise ConfigError(f"{name} must be YYYYMMDD, got {value!r}") from exc
    return value


@dataclass(frozen=True)
class Settings:
    """Everything the SQL templates need."""

    project: str
    dataset: str = "ga4_ecommerce_analysis"
    location: str = "US"
    source_table: str = DEFAULT_SOURCE_TABLE
    start_date: str = DEFAULT_START_DATE
    end_date: str = DEFAULT_END_DATE

    def __post_init__(self) -> None:
        if not _PROJECT_ID.match(self.project):
            raise ConfigError(f"GA4_GCP_PROJECT_ID looks invalid: {self.project!r}")
        if not _DATASET.match(self.dataset):
            raise ConfigError(f"GA4_BQ_DATASET looks invalid: {self.dataset!r}")
        _check_date(self.start_date, "start_date")
        _check_date(self.end_date, "end_date")
        if self.start_date > self.end_date:
            raise ConfigError("start_date must not be after end_date")

    @property
    def dataset_ref(self) -> str:
        """Fully qualified `project.dataset` the pipeline writes to."""
        return f"{self.project}.{self.dataset}"

    def template_values(self) -> dict[str, str]:
        """Placeholder values for `{{ name }}` tokens in SQL files."""
        return {
            "dataset_ref": self.dataset_ref,
            "project": self.project,
            "dataset": self.dataset,
            "source_table": self.source_table,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Settings:
        """Build settings from environment variables (GA4_* prefix)."""
        env = dict(os.environ) if env is None else env
        project = env.get("GA4_GCP_PROJECT_ID", "").strip()
        if not project:
            raise ConfigError(
                "GA4_GCP_PROJECT_ID is not set. Copy .env.example to .env and export it."
            )
        return cls(
            project=project,
            dataset=env.get("GA4_BQ_DATASET", "ga4_ecommerce_analysis"),
            location=env.get("GA4_BQ_LOCATION", "US"),
            source_table=env.get("GA4_SOURCE_TABLE", DEFAULT_SOURCE_TABLE),
            start_date=env.get("GA4_START_DATE", DEFAULT_START_DATE),
            end_date=env.get("GA4_END_DATE", DEFAULT_END_DATE),
        )
