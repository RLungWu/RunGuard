from enum import StrEnum

from pydantic import Field

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
