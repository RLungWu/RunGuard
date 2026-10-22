from enum import StrEnum
from typing import Literal

from pydantic import Field

from runguard.comparison.models import ComparisonPair, MetricDirection
from runguard.domain.models import CanonicalModel


class BootstrapMethod(StrEnum):
    PERCENTILE = "percentile"


class BootstrapConfig(CanonicalModel):
    """Parameters that fully describe one bootstrap calculation."""

    confidence_level: float = Field(gt=0, lt=1)
    resamples: int = Field(gt=0)
    random_seed: int
    method: BootstrapMethod = BootstrapMethod.PERCENTILE


class BootstrapInterval(CanonicalModel):
    """Bootstrap output plus the parameters needed to reproduce it."""

    statistic: float
    lower: float
    upper: float
    sample_size: int = Field(gt=0)
    config: BootstrapConfig


class EffectSizeMethod(StrEnum):
    PAIRED_COHENS_DZ = "paired-cohens-dz"


class EffectSize(CanonicalModel):
    """Paired Cohen's d_z with the components needed to recompute it."""

    method: EffectSizeMethod = EffectSizeMethod.PAIRED_COHENS_DZ
    value: float
    mean: float
    standard_deviation: float = Field(gt=0)
    sample_size: int = Field(ge=2)


class InsufficientEvidenceReason(StrEnum):
    FEWER_THAN_TWO_PAIRS = "fewer-than-two-pairs"
    ZERO_VARIANCE = "zero-variance"


class InsufficientEvidence(CanonicalModel):
    """Explicit record that a statistic was not calculated, and why."""

    reason: InsufficientEvidenceReason
    detail: str = Field(min_length=1)
    sample_size: int = Field(ge=0)


class PositivePairEvidence(CanonicalModel):
    """Pairs with strictly positive direction-aware improvement."""

    count: int = Field(ge=0)
    sample_size: int = Field(gt=0)
    rate: float = Field(ge=0, le=1)


class PairedEvidence(CanonicalModel):
    """Statistical evidence for one paired metric comparison.

    The evidence describes observations and calculation parameters only. It
    does not contain severity, interpretation, or release conclusions.
    """

    group_id: str = Field(min_length=1)
    baseline_variant: str = Field(min_length=1)
    candidate_variant: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    direction: MetricDirection
    value_source: Literal["summary"]
    pairs: list[ComparisonPair] = Field(min_length=1)
    sample_size: int = Field(gt=0)
    mean_improvement: float
    median_improvement: float
    positive_pairs: PositivePairEvidence
    effect_size: EffectSize | InsufficientEvidence
    bootstrap: BootstrapInterval | InsufficientEvidence
    limitations: list[str]
