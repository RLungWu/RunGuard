import pytest
from pydantic import ValidationError

from runguard.statistics.bootstrap import BootstrapError, _percentile, bootstrap_mean
from runguard.statistics.models import BootstrapConfig, BootstrapMethod


def test_bootstrap_config_records_reproducibility_parameters() -> None:
    config = BootstrapConfig(
        confidence_level=0.95,
        resamples=10_000,
        random_seed=7,
    )

    assert config.method is BootstrapMethod.PERCENTILE
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
