"""M3 benchmark scenarios: each states and checks its expected evidence.

Reference values are calculated exactly with `Fraction` from the designed
improvements in `tests/fixtures/benchmarks/README.md`, independently of the
evidence implementation.
"""

import math
from fractions import Fraction
from pathlib import Path
from statistics import median

import pytest

from runguard.comparison.config import compare_run_configs
from runguard.comparison.models import (
    CheckpointPolicy,
    ComparisonResult,
    MetricDirection,
    ValueSource,
)
from runguard.comparison.paired import ComparisonError, compare_group
from runguard.domain.models import ExperimentGroup
from runguard.sources.local_json import load_local_json
from runguard.statistics.evidence import build_paired_evidence
from runguard.statistics.models import (
    BootstrapInterval,
    EffectSize,
    LeaveOnePairOutEvidence,
    PairedEvidence,
)
from runguard.statistics.multi_metric import build_multi_metric_evidence

BENCHMARKS_DIR = Path(__file__).parents[1] / "fixtures" / "benchmarks"
RANDOM_SEED = 20261030
SEEDS = list(range(1, 11))
STABLE = [12, 9, 11, 10, 8, 14, 10, 9, 11, 7]
CONCLUSION_FIELDS = {
    "decision",
    "severity",
    "verdict",
    "status",
    "finding",
    "compatible",
    "cause",
}


def _load(name: str) -> ExperimentGroup:
    return load_local_json(BENCHMARKS_DIR / f"{name}.json", "canonical")


def _compare(
    group: ExperimentGroup,
    metric: str = "val_f1",
    direction: MetricDirection = MetricDirection.HIGHER_IS_BETTER,
    policy: CheckpointPolicy | None = None,
) -> ComparisonResult:
    return compare_group(
        group,
        "baseline",
        "candidate",
        metric,
        direction=direction,
        value_source=ValueSource.SUMMARY if policy is None else ValueSource.HISTORY,
        checkpoint_policy=policy,
    )


def _evidence(comparison: ComparisonResult) -> PairedEvidence:
    # Default contract: 95% percentile interval with 10,000 resamples.
    return build_paired_evidence(comparison, random_seed=RANDOM_SEED)


def _assert_matches_reference(
    evidence: PairedEvidence, improvements: list[int], scale: int = 1000
) -> None:
    """Check every point statistic against an exact Fraction reference."""
    values = [Fraction(value, scale) for value in improvements]
    n = len(values)
    mean = sum(values, Fraction(0)) / n
    variance = sum(((value - mean) ** 2 for value in values), Fraction(0)) / (n - 1)
    sd = math.sqrt(variance)
    # Removing pair i moves the mean by (mean - x_i) / (n - 1).
    changes = [(mean - value) / (n - 1) for value in values]
    largest = max(range(n), key=lambda i: (abs(changes[i]), -SEEDS[i]))

    assert evidence.sample_size == n
    assert [pair.seed for pair in evidence.pairs] == SEEDS
    assert evidence.mean_improvement == pytest.approx(float(mean), abs=1e-12)
    assert evidence.median_improvement == pytest.approx(
        float(median(values)), abs=1e-12
    )
    assert evidence.positive_pairs.count == sum(value > 0 for value in values)

    assert isinstance(evidence.effect_size, EffectSize)
    assert evidence.effect_size.standard_deviation == pytest.approx(sd)
    assert evidence.effect_size.value == pytest.approx(float(mean) / sd)

    loo = evidence.leave_one_pair_out
    assert isinstance(loo, LeaveOnePairOutEvidence)
    assert [change.signed_change for change in loo.changes] == pytest.approx(
        [float(change) for change in changes], abs=1e-12
    )
    assert loo.largest_influence_seed == SEEDS[largest]

    assert isinstance(evidence.bootstrap, BootstrapInterval)
    assert evidence.bootstrap.config.resamples == 10_000
    assert evidence.bootstrap.config.random_seed == RANDOM_SEED
    assert min(values) <= evidence.bootstrap.lower <= evidence.bootstrap.upper
    assert evidence.bootstrap.upper <= max(values)

    assert not set(evidence.model_dump()) & CONCLUSION_FIELDS


def _shift(seed: int) -> int:
    return 3 if seed == 10 else 0


def _interval(evidence: PairedEvidence) -> BootstrapInterval:
    assert isinstance(evidence.bootstrap, BootstrapInterval)
    return evidence.bootstrap


def test_stable_small_improvement() -> None:
    evidence = _evidence(_compare(_load("stable-small-improvement")))

    _assert_matches_reference(evidence, STABLE)
    assert evidence.positive_pairs.count == 10
    assert _interval(evidence).lower > 0


def test_stable_regression() -> None:
    evidence = _evidence(_compare(_load("stable-regression")))

    _assert_matches_reference(evidence, [-9, -11, -10, -12, -8, -10, -9, -13, -11, -10])
    assert evidence.positive_pairs.count == 0
    assert _interval(evidence).upper < 0
    assert isinstance(evidence.effect_size, EffectSize)
    assert evidence.effect_size.value < 0


def test_improvement_dominated_by_one_seed() -> None:
    evidence = _evidence(_compare(_load("single-seed-dominated")))

    _assert_matches_reference(evidence, [1, -1, 0, 2, -2, 1, -1, 0, 1, 40])
    assert evidence.mean_minus_median_improvement == pytest.approx(0.0036)
    assert evidence.positive_pairs.count == 5
    loo = evidence.leave_one_pair_out
    assert isinstance(loo, LeaveOnePairOutEvidence)
    assert loo.largest_influence_seed == 10
    assert loo.changes[9].leave_one_out_mean == pytest.approx(0.001 / 9)


def test_increased_variance_with_unchanged_mean() -> None:
    evidence = _evidence(_compare(_load("increased-variance")))

    _assert_matches_reference(evidence, [30, -30, 25, -25, 20, -20, 36, -35, 10, -10])
    assert evidence.mean_improvement == pytest.approx(0.0001)
    interval = _interval(evidence)
    assert interval.lower < 0 < interval.upper


def test_missing_paired_runs_fail_under_strict_mode() -> None:
    with pytest.raises(ComparisonError, match=r"missing candidate seeds: \[4, 9\]"):
        _compare(_load("missing-paired-runs"))


def test_final_checkpoint_regression() -> None:
    comparison = _compare(
        _load("checkpoint-dependent"),
        "val_loss",
        MetricDirection.LOWER_IS_BETTER,
        CheckpointPolicy.FINAL,
    )
    evidence = _evidence(comparison)

    # Final improvement per seed s: (0.40 + 0.001s) - (0.43 + 0.002s), with
    # seed 10's baseline shifted by +0.003.
    _assert_matches_reference(evidence, [-30 - seed + _shift(seed) for seed in SEEDS])
    assert evidence.checkpoint_policy is CheckpointPolicy.FINAL
    assert {(p.baseline_step, p.candidate_step) for p in evidence.pairs} == {(30, 30)}
    assert evidence.positive_pairs.count == 0
    assert _interval(evidence).upper < 0


def test_best_checkpoint_improvement() -> None:
    comparison = _compare(
        _load("checkpoint-dependent"),
        "val_loss",
        MetricDirection.LOWER_IS_BETTER,
        CheckpointPolicy.BEST,
    )
    evidence = _evidence(comparison)

    # Best improvement per seed s: (0.40 + 0.001s) - (0.33 + 0.002s), with
    # seed 10's baseline shifted by +0.003.
    _assert_matches_reference(evidence, [70 - seed + _shift(seed) for seed in SEEDS])
    assert evidence.checkpoint_policy is CheckpointPolicy.BEST
    assert {(p.baseline_step, p.candidate_step) for p in evidence.pairs} == {(30, 20)}
    assert evidence.positive_pairs.count == 10
    assert any("optimistic" in item for item in evidence.limitations)


def test_checkpoint_scenario_has_no_summary_fallback() -> None:
    with pytest.raises(ComparisonError, match="missing from summary metrics"):
        _compare(_load("checkpoint-dependent"), "val_loss")


def test_primary_improvement_with_secondary_regression() -> None:
    group = _load("conflicting-metrics")
    primary = _evidence(_compare(group))
    latency = _evidence(_compare(group, "latency_ms", MetricDirection.LOWER_IS_BETTER))

    result = build_multi_metric_evidence(primary, [latency])

    latency_design = [
        -2000,
        -1500,
        -2500,
        500,
        -2000,
        -3000,
        -1500,
        -2000,
        -2500,
        -1000,
    ]
    _assert_matches_reference(primary, STABLE)
    _assert_matches_reference(latency, latency_design)
    conflict = result.conflicts[0]
    assert conflict.direction_conflict is True
    assert conflict.secondary_mean_improvement == pytest.approx(-1.75)
    assert conflict.opposing_pair_count == 9
    assert not set(result.model_dump()) & CONCLUSION_FIELDS


def test_incompatible_configuration_is_reported_as_evidence() -> None:
    group = _load("incompatible-config")
    comparison = _compare(group)

    evidence = _evidence(comparison)
    configs = compare_run_configs(group, comparison)

    _assert_matches_reference(evidence, STABLE)
    assert configs.differing_keys == ["augmentation", "dataset"]
    assert all(
        [d.key for d in pair.differences] == ["augmentation", "dataset"]
        for pair in configs.pairs
    )
    dataset = configs.pairs[0].differences[1]
    assert (dataset.baseline_value, dataset.candidate_value) == (
        "imagenet-v1",
        "imagenet-v2",
    )
    assert not set(configs.model_dump()) & CONCLUSION_FIELDS


def test_confounded_code_and_config_change_has_no_causal_claim() -> None:
    group = _load("confounded-change")
    comparison = _compare(group)

    evidence = _evidence(comparison)
    configs = compare_run_configs(group, comparison)

    _assert_matches_reference(evidence, STABLE)
    assert configs.differing_keys == ["code_revision", "optimizer"]
    assert all(len(pair.differences) == 2 for pair in configs.pairs)
    assert any("configuration comparability" in item for item in evidence.limitations)
    assert not set(configs.model_dump()) & CONCLUSION_FIELDS


def test_benchmark_evidence_is_reproducible() -> None:
    comparison = _compare(_load("single-seed-dominated"))

    assert _evidence(comparison) == _evidence(comparison)
