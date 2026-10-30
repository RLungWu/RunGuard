import random
import statistics

import pytest
from pydantic import ValidationError

from runguard.statistics.bootstrap import (
    BootstrapError,
    _percentile,
    _resample_indices,
    bootstrap_mean,
)
from runguard.statistics.models import (
    BootstrapConfig,
    BootstrapMethod,
    BootstrapStatistic,
)


def test_bootstrap_config_records_reproducibility_parameters() -> None:
    config = BootstrapConfig(
        confidence_level=0.95,
        resamples=10_000,
        random_seed=7,
    )

    assert config.method is BootstrapMethod.PERCENTILE
    assert config.statistic is BootstrapStatistic.MEAN
    assert config.confidence_level == 0.95
    assert config.resamples == 10_000
    assert config.random_seed == 7


def test_bootstrap_config_rejects_non_strict_values() -> None:
    with pytest.raises(ValidationError):
        BootstrapConfig(
            confidence_level="0.95",
            resamples=10_000,
            random_seed=7,
        )


def test_bootstrap_config_rejects_invalid_ranges() -> None:
    with pytest.raises(ValidationError):
        BootstrapConfig(confidence_level=1.0, resamples=10_000, random_seed=7)

    with pytest.raises(ValidationError):
        BootstrapConfig(confidence_level=0.95, resamples=0, random_seed=7)


def test_bootstrap_mean_rejects_fewer_than_two_values() -> None:
    with pytest.raises(BootstrapError, match="At least two"):
        bootstrap_mean([0.02], random_seed=7)


def test_bootstrap_mean_rejects_invalid_configuration() -> None:
    with pytest.raises(BootstrapError, match="Invalid bootstrap configuration"):
        bootstrap_mean([0.01, 0.02], confidence_level=1.0, random_seed=7)


def test_percentile() -> None:
    assert _percentile([1.0, 2.0, 3.0, 4.0], 0.25) == pytest.approx(1.75)
    assert _percentile([1.0, 2.0, 3.0, 4.0], 0.0) == 1.0
    assert _percentile([1.0, 2.0, 3.0, 4.0], 1.0) == 4.0


def test_percentile_rejects_empty_values() -> None:
    with pytest.raises(BootstrapError, match="empty"):
        _percentile([], 0.5)


def test_percentile_rejects_invalid_probability() -> None:
    with pytest.raises(BootstrapError, match="between 0 and 1"):
        _percentile([1.0, 2.0], 1.1)


def test_bootstrap_mean_is_reproducible_and_matches_reference() -> None:
    result = bootstrap_mean(
        [0.01, 0.02, 0.03],
        confidence_level=0.95,
        resamples=20,
        random_seed=7,
    )
    repeated = bootstrap_mean(
        [0.01, 0.02, 0.03],
        confidence_level=0.95,
        resamples=20,
        random_seed=7,
    )

    assert result == repeated
    assert result.statistic == pytest.approx(0.02)
    assert result.lower == pytest.approx(0.01)
    assert result.upper == pytest.approx(0.025083333333333332)
    assert result.sample_size == 3
    assert result.config.random_seed == 7
    assert result.config.resamples == 20


def _reference_interval(
    values: list[float],
    *,
    confidence_level: float,
    resamples: int,
    random_seed: int,
) -> tuple[float, float]:
    """Independent reference using the stdlib inclusive quantile method."""
    rng = random.Random(random_seed)
    n = len(values)
    means = [
        sum(values[int(rng.random() * n)] for _ in range(n)) / n
        for _ in range(resamples)
    ]
    tail_cuts = round(2 / (1 - confidence_level))
    cuts = statistics.quantiles(means, n=tail_cuts, method="inclusive")
    return cuts[0], cuts[-1]


@pytest.mark.parametrize("confidence_level", [0.8, 0.9, 0.95])
def test_bootstrap_mean_applies_confidence_level(confidence_level: float) -> None:
    values = [0.012, -0.004, 0.021, 0.008, 0.017, 0.003]

    result = bootstrap_mean(
        values,
        confidence_level=confidence_level,
        resamples=500,
        random_seed=11,
    )
    lower, upper = _reference_interval(
        values,
        confidence_level=confidence_level,
        resamples=500,
        random_seed=11,
    )

    assert result.lower == pytest.approx(lower, abs=1e-12)
    assert result.upper == pytest.approx(upper, abs=1e-12)
    assert result.config.confidence_level == confidence_level


def test_bootstrap_mean_narrower_confidence_gives_narrower_interval() -> None:
    values = [0.012, -0.004, 0.021, 0.008, 0.017, 0.003]

    wide = bootstrap_mean(values, confidence_level=0.95, resamples=500, random_seed=3)
    narrow = bootstrap_mean(values, confidence_level=0.8, resamples=500, random_seed=3)

    assert wide.lower < narrow.lower
    assert narrow.upper < wide.upper


def test_bootstrap_mean_preserves_caller_order() -> None:
    seed_ordered = [0.03, -0.01, 0.02, 0.0]

    result = bootstrap_mean(seed_ordered, resamples=200, random_seed=5)
    lower, upper = _reference_interval(
        seed_ordered,
        confidence_level=0.95,
        resamples=200,
        random_seed=5,
    )

    assert result.lower == pytest.approx(lower, abs=1e-12)
    assert result.upper == pytest.approx(upper, abs=1e-12)


def test_resample_indices_follow_pinned_random_stream() -> None:
    # Pinned golden values: derived only from `random()`, which Python keeps
    # stable across versions for a given seed. A change here means saved
    # evidence can no longer be reproduced.
    rng = random.Random(7)

    assert _resample_indices(rng, 10) == [3, 1, 6, 0, 5, 3, 0, 5, 0, 4]
    assert _resample_indices(rng, 10) == [0, 0, 4, 8, 1, 2, 6, 9, 5, 3]


def test_bootstrap_mean_default_parameters_match_pinned_interval() -> None:
    # Ten seed-ordered improvements with the default 95%, 10,000-resample
    # contract. Pinned from the implementation before the D2 index change.
    improvements = [
        0.020,
        0.015,
        -0.005,
        0.020,
        0.0,
        0.020,
        -0.005,
        0.015,
        0.025,
        0.010,
    ]

    result = bootstrap_mean(improvements, random_seed=7)

    assert result.lower == pytest.approx(0.005, abs=1e-12)
    assert result.upper == pytest.approx(0.0175, abs=1e-12)
