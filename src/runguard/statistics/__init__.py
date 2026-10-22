"""Statistical evidence calculations for paired experiment comparisons."""

from runguard.statistics.bootstrap import (
    BootstrapError,
    bootstrap_mean,
    build_bootstrap_config,
)
from runguard.statistics.effect_size import EffectSizeError, paired_cohens_dz
from runguard.statistics.evidence import EvidenceError, build_paired_evidence
from runguard.statistics.models import (
    BootstrapConfig,
    BootstrapInterval,
    BootstrapMethod,
    EffectSize,
    EffectSizeMethod,
    InsufficientEvidence,
    InsufficientEvidenceReason,
    PairedEvidence,
    PositivePairEvidence,
)

__all__ = [
    "BootstrapConfig",
    "BootstrapError",
    "BootstrapInterval",
    "BootstrapMethod",
    "EffectSize",
    "EffectSizeError",
    "EffectSizeMethod",
    "EvidenceError",
    "InsufficientEvidence",
    "InsufficientEvidenceReason",
    "PairedEvidence",
    "PositivePairEvidence",
    "bootstrap_mean",
    "build_bootstrap_config",
    "build_paired_evidence",
    "paired_cohens_dz",
]
