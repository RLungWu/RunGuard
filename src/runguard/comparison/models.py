from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self


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
    baseline_step: int | None = None
    candidate_step: int | None = None


class ComparisonResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    group_id: str = Field(min_length=1)
    baseline_variant: str = Field(min_length=1)
    candidate_variant: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    value_source: ValueSource = ValueSource.SUMMARY
    checkpoint_policy: CheckpointPolicy | None = None
    direction: MetricDirection
    pairs: list[ComparisonPair]
    mean_difference: float
    median_difference: float
    mean_improvement: float
    median_improvement: float
    positive_pair_count: int
    positive_pair_rate: float

    @model_validator(mode="after")
    def validate_value_provenance(self) -> Self:
        # Summary values carry no policy or steps; history values carry both.
        is_history = self.value_source is ValueSource.HISTORY
        if is_history != (self.checkpoint_policy is not None):
            raise ValueError(
                "checkpoint_policy is required for history values and not "
                "allowed for summary values"
            )

        for pair in self.pairs:
            steps = (pair.baseline_step, pair.candidate_step)
            if is_history and None in steps:
                raise ValueError(
                    f"History pair for seed {pair.seed} must record both steps"
                )
            if not is_history and steps != (None, None):
                raise ValueError(
                    f"Summary pair for seed {pair.seed} must not record steps"
                )

        return self
