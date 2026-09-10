import math
import random
from collections.abc import Sequence

from pydantic import ValidationError

from runguard.statistics.models import BootstrapConfig, BootstrapInterval


class BootstrapError(ValueError):
    """Raised when paired values cannot support a bootstrap calculation."""


def bootstrap_mean(
    values: Sequence[float],
    *,
    confidence_level: float = 0.95,
    resamples: int = 10_000,
    random_seed: int,
) -> BootstrapInterval:
    """Calculate a percentile bootstrap interval for a sample mean.

    The input values are expected to be direction-aware paired improvements.
    Baseline and candidate values must already have been paired before calling
    this function.
    """
    validated_values = _validate_values(values)
    config = _build_config(confidence_level, resamples, random_seed)

    # Each resample draws `len(validated_values)` values with replacement using
    # a local RNG seeded by `config.random_seed`.
    bootstrap_means: list[float] = []
    rng = random.Random(config.random_seed)

    for _ in range(config.resamples):
        sample = rng.choices(
            validated_values,
            k=len(validated_values),
        )
        sample_mean = sum(sample) / len(sample)
        bootstrap_means.append(sample_mean)

    # Use the linear interpolation percentile convention from the M3 spec.
    bootstrap_means.sort()
    interval = BootstrapInterval(
        statistic=sum(validated_values) / len(validated_values),
        lower=_percentile(bootstrap_means, 0.025),
        upper=_percentile(bootstrap_means, 0.975),
        sample_size=len(validated_values),
        config=config,
    )
    return interval


def _validate_values(values: Sequence[float]) -> list[float]:
    validated_values: list[float] = []

    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise BootstrapError("Bootstrap values must be real numbers")

        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            raise BootstrapError("Bootstrap values must be finite")

        validated_values.append(numeric_value)

    if len(validated_values) < 2:
        raise BootstrapError("At least two paired values are required")

    # Sorting makes the random stream independent of the caller's input order.
    return sorted(validated_values)


def _build_config(
    confidence_level: float,
    resamples: int,
    random_seed: int,
) -> BootstrapConfig:
    try:
        if not 0 < confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        if resamples <= 0:
            raise ValueError("resamples must be positive")

        return BootstrapConfig(
            confidence_level=confidence_level,
            resamples=resamples,
            random_seed=random_seed,
        )
    except (TypeError, ValueError, ValidationError) as error:
        raise BootstrapError("Invalid bootstrap configuration") from error


def _percentile(sorted_values: Sequence[float], probability: float) -> float:
    """Return one linearly interpolated percentile from sorted values."""
    if not sorted_values:
        raise BootstrapError("Cannot calculate percentile of empty values")
    if not 0 <= probability <= 1:
        raise BootstrapError("Percentile probability must be between 0 and 1")

    position = probability * (len(sorted_values) - 1)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    weight = position - lower_index

    return (1 - weight) * sorted_values[lower_index] + weight * sorted_values[
        upper_index
    ]
