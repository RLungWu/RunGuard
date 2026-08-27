from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MetricDirection(StrEnum):
    HIGHER_IS_BETTER = "higher-is-better"
    LOWER_IS_BETTER = "lower-is-better"


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
