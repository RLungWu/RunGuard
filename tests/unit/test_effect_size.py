import math

import pytest

from runguard.statistics.effect_size import EffectSizeError, paired_cohens_dz
from runguard.statistics.models import (
    EffectSize,
    EffectSizeMethod,
    InsufficientEvidence,
    InsufficientEvidenceReason,
)


def test_paired_cohens_dz_matches_hand_calculation() -> None:
    # mean = 2.5, sample variance = 5 / 3, d_z = 2.5 / sqrt(5 / 3)
    result = paired_cohens_dz([1.0, 2.0, 3.0, 4.0])

    assert isinstance(result, EffectSize)
    assert result.method is EffectSizeMethod.PAIRED_COHENS_DZ
    assert result.mean == pytest.approx(2.5)
    assert result.standard_deviation == pytest.approx(math.sqrt(5 / 3))
    assert result.value == pytest.approx(1.9364916731037085)
    assert result.sample_size == 4


def test_paired_cohens_dz_uses_sample_standard_deviation() -> None:
    # Population SD would be 0.01; the n - 1 sample SD is 0.01 * sqrt(2).
    result = paired_cohens_dz([0.01, 0.03])

    assert isinstance(result, EffectSize)
    assert result.standard_deviation == pytest.approx(0.01 * math.sqrt(2))
    assert result.value == pytest.approx(0.02 / (0.01 * math.sqrt(2)))


def test_paired_cohens_dz_is_negative_for_regression() -> None:
    result = paired_cohens_dz([-0.02, -0.01, -0.03])

    assert isinstance(result, EffectSize)
    assert result.value == pytest.approx(-2.0)


def test_paired_cohens_dz_reports_fewer_than_two_pairs() -> None:
    result = paired_cohens_dz([0.02])

    assert isinstance(result, InsufficientEvidence)
    assert result.reason is InsufficientEvidenceReason.FEWER_THAN_TWO_PAIRS
    assert result.sample_size == 1


def test_paired_cohens_dz_reports_empty_input_as_insufficient() -> None:
    result = paired_cohens_dz([])

    assert isinstance(result, InsufficientEvidence)
    assert result.sample_size == 0


def test_paired_cohens_dz_reports_zero_variance() -> None:
    result = paired_cohens_dz([0.01, 0.01, 0.01])

    assert isinstance(result, InsufficientEvidence)
    assert result.reason is InsufficientEvidenceReason.ZERO_VARIANCE
    assert result.sample_size == 3


@pytest.mark.parametrize("value", [math.nan, math.inf, True])
def test_paired_cohens_dz_rejects_invalid_values(value: float) -> None:
    with pytest.raises(EffectSizeError):
        paired_cohens_dz([0.01, value])
