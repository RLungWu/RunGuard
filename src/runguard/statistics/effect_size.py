import math
from collections.abc import Sequence
from statistics import stdev

from runguard.statistics.models import (
    EffectSize,
    InsufficientEvidence,
    InsufficientEvidenceReason,
)


class EffectSizeError(ValueError):
    """Raised when values cannot be used for an effect-size calculation."""


def paired_cohens_dz(values: Sequence[float]) -> EffectSize | InsufficientEvidence:
    """Calculate paired Cohen's d_z for direction-aware paired improvements.

    d_z is the mean improvement divided by the sample standard deviation
    (`n - 1`) of the improvements. When the standard deviation is undefined or
    zero, the result is explicit insufficient evidence instead of a number.
    """
    validated_values = _validate_values(values)
    sample_size = len(validated_values)

    if sample_size < 2:
        return InsufficientEvidence(
            reason=InsufficientEvidenceReason.FEWER_THAN_TWO_PAIRS,
            detail=(
                "Paired Cohen's d_z requires at least two paired observations "
                "because the sample standard deviation is undefined"
            ),
            sample_size=sample_size,
        )

    standard_deviation = stdev(validated_values)
    if standard_deviation == 0:
        return InsufficientEvidence(
            reason=InsufficientEvidenceReason.ZERO_VARIANCE,
            detail=(
                "Paired Cohen's d_z is undefined because every paired "
                "improvement is identical"
            ),
            sample_size=sample_size,
        )

    # Match the arithmetic mean used by the comparison and bootstrap paths.
    mean_improvement = sum(validated_values) / sample_size
    return EffectSize(
        value=mean_improvement / standard_deviation,
        mean=mean_improvement,
        standard_deviation=standard_deviation,
        sample_size=sample_size,
    )


def _validate_values(values: Sequence[float]) -> list[float]:
    validated_values: list[float] = []

    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise EffectSizeError("Effect-size values must be real numbers")

        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            raise EffectSizeError("Effect-size values must be finite")

        validated_values.append(numeric_value)

    return validated_values
