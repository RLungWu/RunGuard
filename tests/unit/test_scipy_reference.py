"""Cross-check statistics against SciPy/NumPy as an independent reference.

SciPy is a development-only dependency (trade-off D3). Its bootstrap uses a
different random generator, so intervals agree only within Monte Carlo error;
the tolerance is a quarter of the standard error of the mean, which covers the
observed sampling and small-sample discreteness differences.
"""

import pytest

from runguard.statistics.bootstrap import bootstrap_mean
from runguard.statistics.effect_size import paired_cohens_dz
from runguard.statistics.models import EffectSize

np = pytest.importorskip("numpy")
stats = pytest.importorskip("scipy.stats")

# Benchmark designs in units of 1e-3 (see tests/fixtures/benchmarks/README.md).
DESIGNS = {
    "stable-small-improvement": [12, 9, 11, 10, 8, 14, 10, 9, 11, 7],
    "stable-regression": [-9, -11, -10, -12, -8, -10, -9, -13, -11, -10],
    "single-seed-dominated": [1, -1, 0, 2, -2, 1, -1, 0, 1, 40],
    "increased-variance": [30, -30, 25, -25, 20, -20, 36, -35, 10, -10],
}
TOLERANCE_IN_STANDARD_ERRORS = 0.25


@pytest.mark.parametrize("design", DESIGNS.values(), ids=DESIGNS.keys())
def test_effect_size_matches_numpy(design: list[int]) -> None:
    values = np.array(design) / 1000

    result = paired_cohens_dz(values.tolist())

    assert isinstance(result, EffectSize)
    assert result.standard_deviation == pytest.approx(values.std(ddof=1))
    assert result.value == pytest.approx(values.mean() / values.std(ddof=1))


@pytest.mark.parametrize("confidence_level", [0.9, 0.95])
@pytest.mark.parametrize("design", DESIGNS.values(), ids=DESIGNS.keys())
def test_bootstrap_interval_matches_scipy(
    design: list[int], confidence_level: float
) -> None:
    values = np.array(design) / 1000
    standard_error = values.std(ddof=1) / np.sqrt(len(values))
    tolerance = TOLERANCE_IN_STANDARD_ERRORS * standard_error

    ours = bootstrap_mean(
        values.tolist(), confidence_level=confidence_level, random_seed=20261030
    )
    reference = stats.bootstrap(
        (values,),
        np.mean,
        confidence_level=confidence_level,
        n_resamples=10_000,
        method="percentile",
        rng=np.random.default_rng(0),
    ).confidence_interval

    assert ours.lower == pytest.approx(reference.low, abs=tolerance)
    assert ours.upper == pytest.approx(reference.high, abs=tolerance)
