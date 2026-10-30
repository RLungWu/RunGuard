from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MetricDirection(StrEnum):
    HIGHER_IS_BETTER = "higher-is-better"
    LOWER_IS_BETTER = "lower-is-better"


class ValueSource(StrEnum):
    SUMMARY = "summary"
    HISTORY = "history"


class CheckpointPolicy(StrEnum):
    FINAL = "final"
    BEST = "best"


class MissingValueReason(StrEnum):
    METRIC_NOT_FOUND = "metric-not-found"
    AMBIGUOUS_SERIES = "ambiguous-series"
    EMPTY_HISTORY = "empty-history"
    MISSING_VALUE = "missing-value"
    NO_VALID_VALUE = "no-valid-value"
    NON_FINITE_VALUE = "non-finite-value"


class SelectedValue(BaseModel):
    """One run's comparison value; `step` is set only for history values."""

    model_config = ConfigDict(strict=True, extra="forbid")

    run_id: str = Field(min_length=1)
    value: float
    step: int | None = None


class MissingValue(BaseModel):
    """Explicit record that no comparison value could be selected for a run."""

    model_config = ConfigDict(strict=True, extra="forbid")

    run_id: str = Field(min_length=1)
    reason: MissingValueReason


class ComparisonPair(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    seed: int
    baseline_run_id: str = Field(min_length=1)
    candidate_run_id: str = Field(min_length=1)
    baseline_value: float
    candidate_value: float
    raw_difference: float
    improvement_difference: float


class ComparisonResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    group_id: str = Field(min_length=1)
    baseline_variant: str = Field(min_length=1)
    candidate_variant: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    value_source: Literal["summary"] = "summary"
    direction: MetricDirection
    pairs: list[ComparisonPair]
    mean_difference: float
    median_difference: float
    mean_improvement: float
    median_improvement: float
    positive_pair_count: int
    positive_pair_rate: float
