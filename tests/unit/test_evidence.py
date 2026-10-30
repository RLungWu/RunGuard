import pytest

from runguard.comparison.models import ComparisonResult, MetricDirection
from runguard.comparison.paired import compare_group
from runguard.domain.models import ExperimentGroup, Run, RunConfig
from runguard.statistics.bootstrap import BootstrapError, bootstrap_mean
from runguard.statistics.evidence import EvidenceError, build_paired_evidence
from runguard.statistics.models import (
    BootstrapInterval,
    EffectSize,
    InsufficientEvidence,
    InsufficientEvidenceReason,
    LeaveOnePairOutEvidence,
)

# Ten paired seeds; candidate improves loss on seven seeds, ties on one.
TEN_SEED_LOSSES = {
    1: (0.500, 0.480),
    2: (0.510, 0.495),
    3: (0.495, 0.500),
    4: (0.520, 0.500),
    5: (0.505, 0.505),
    6: (0.490, 0.470),
    7: (0.515, 0.520),
    8: (0.500, 0.485),
    9: (0.530, 0.505),
    10: (0.485, 0.475),
}


def _run(run_id: str, variant: str, seed: int, value: float) -> Run:
    return Run(
        run_id=run_id,
        variant=variant,
        seed=seed,
        config=RunConfig(values={}),
        metrics=[],
        summary_metrics={"val_loss": value},
    )


def _ten_seed_comparison() -> ComparisonResult:
    runs: list[Run] = []
    for seed, (baseline, candidate) in TEN_SEED_LOSSES.items():
        runs.append(_run(f"baseline-{seed}", "baseline", seed, baseline))
        runs.append(_run(f"candidate-{seed}", "candidate", seed, candidate))
    group = ExperimentGroup(group_id="loss-study", runs=runs)
    return compare_group(
        group,
        "baseline",
        "candidate",
        "val_loss",
        direction=MetricDirection.LOWER_IS_BETTER,
    )


def test_evidence_preserves_comparison_provenance() -> None:
    evidence = build_paired_evidence(_ten_seed_comparison(), random_seed=7)

    assert evidence.group_id == "loss-study"
    assert evidence.baseline_variant == "baseline"
    assert evidence.candidate_variant == "candidate"
    assert evidence.metric == "val_loss"
    assert evidence.direction is MetricDirection.LOWER_IS_BETTER
    assert evidence.value_source == "summary"
    assert evidence.sample_size == 10
    assert [pair.seed for pair in evidence.pairs] == list(range(1, 11))
    assert evidence.pairs[2].baseline_run_id == "baseline-3"
    assert evidence.pairs[2].candidate_run_id == "candidate-3"
    assert evidence.limitations


def test_evidence_uses_direction_aware_improvements() -> None:
    evidence = build_paired_evidence(_ten_seed_comparison(), random_seed=7)

    # Lower-is-better improvement is baseline - candidate.
    improvements = [b - c for b, c in TEN_SEED_LOSSES.values()]
    expected_mean = sum(improvements) / 10

    assert evidence.mean_improvement == pytest.approx(expected_mean)
    assert evidence.mean_improvement == pytest.approx(0.0115)
    assert evidence.median_improvement == pytest.approx(0.015)


def test_evidence_reports_mean_minus_median() -> None:
    evidence = build_paired_evidence(_ten_seed_comparison(), random_seed=7)

    # Mean 11.5e-3 sits below median 15e-3 because of the two regressing seeds.
    assert evidence.mean_minus_median_improvement == pytest.approx(-0.0035)


def test_evidence_reports_leave_one_pair_out_reference_values() -> None:
    evidence = build_paired_evidence(_ten_seed_comparison(), random_seed=7)

    # Removing pair i moves the mean by (mean - x_i) / (n - 1). In 1e-3 units
    # seeds 3 and 7 (x = -5) both move it by 16.5 / 9, the largest change;
    # the tie selects the smaller seed.
    loo = evidence.leave_one_pair_out
    assert isinstance(loo, LeaveOnePairOutEvidence)
    assert loo.full_mean == pytest.approx(evidence.mean_improvement)
    assert [change.seed for change in loo.changes] == list(range(1, 11))
    assert loo.largest_influence_seed == 3

    seed_3 = loo.changes[2]
    assert seed_3.baseline_run_id == "baseline-3"
    assert seed_3.candidate_run_id == "candidate-3"
    assert seed_3.leave_one_out_mean == pytest.approx(0.001 * 120 / 9)
    assert seed_3.signed_change == pytest.approx(0.001 * 16.5 / 9)
    assert loo.changes[8].signed_change == pytest.approx(-0.001 * 13.5 / 9)


def test_evidence_counts_strictly_positive_pairs() -> None:
    evidence = build_paired_evidence(_ten_seed_comparison(), random_seed=7)

    # Seeds 3 and 7 regress and seed 5 ties; ties are not positive.
    assert evidence.positive_pairs.count == 7
    assert evidence.positive_pairs.sample_size == 10
    assert evidence.positive_pairs.rate == pytest.approx(0.7)


def test_evidence_reports_effect_size_reference_value() -> None:
    evidence = build_paired_evidence(_ten_seed_comparison(), random_seed=7)

    # Independent hand calculation from the ten improvements (in 1e-3 units):
    # [20, 15, -5, 20, 0, 20, -5, 15, 25, 10]; mean 11.5,
    # sum of squared deviations 1102.5, sample SD sqrt(1102.5 / 9) = sqrt(122.5).
    assert isinstance(evidence.effect_size, EffectSize)
    assert evidence.effect_size.standard_deviation == pytest.approx(0.001 * 122.5**0.5)
    assert evidence.effect_size.value == pytest.approx(11.5 / 122.5**0.5)


def test_evidence_bootstrap_uses_seed_ordered_improvements() -> None:
    comparison = _ten_seed_comparison()
    shuffled = comparison.model_copy(update={"pairs": list(reversed(comparison.pairs))})

    evidence = build_paired_evidence(shuffled, random_seed=7, resamples=500)
    reference = bootstrap_mean(
        [pair.improvement_difference for pair in comparison.pairs],
        resamples=500,
        random_seed=7,
    )

    assert [pair.seed for pair in evidence.pairs] == list(range(1, 11))
    assert evidence.bootstrap == reference


def test_evidence_is_reproducible() -> None:
    comparison = _ten_seed_comparison()

    first = build_paired_evidence(comparison, random_seed=13, resamples=500)
    second = build_paired_evidence(comparison, random_seed=13, resamples=500)

    assert first == second
    assert isinstance(first.bootstrap, BootstrapInterval)
    assert first.bootstrap.config.random_seed == 13
    assert first.bootstrap.config.resamples == 500
    assert first.bootstrap.config.confidence_level == 0.95


def test_evidence_reports_insufficient_evidence_for_single_pair() -> None:
    group = ExperimentGroup(
        group_id="single",
        runs=[
            _run("baseline-1", "baseline", 1, 0.5),
            _run("candidate-1", "candidate", 1, 0.4),
        ],
    )
    comparison = compare_group(
        group,
        "baseline",
        "candidate",
        "val_loss",
        direction=MetricDirection.LOWER_IS_BETTER,
    )

    evidence = build_paired_evidence(comparison, random_seed=7)

    assert evidence.sample_size == 1
    assert evidence.positive_pairs.count == 1
    assert isinstance(evidence.bootstrap, InsufficientEvidence)
    assert evidence.bootstrap.reason is InsufficientEvidenceReason.FEWER_THAN_TWO_PAIRS
    assert isinstance(evidence.effect_size, InsufficientEvidence)
    assert (
        evidence.effect_size.reason is InsufficientEvidenceReason.FEWER_THAN_TWO_PAIRS
    )
    assert isinstance(evidence.leave_one_pair_out, InsufficientEvidence)
    assert evidence.mean_minus_median_improvement == 0.0


def test_evidence_validates_bootstrap_parameters_for_single_pair() -> None:
    group = ExperimentGroup(
        group_id="single",
        runs=[
            _run("baseline-1", "baseline", 1, 0.5),
            _run("candidate-1", "candidate", 1, 0.4),
        ],
    )
    comparison = compare_group(group, "baseline", "candidate", "val_loss")

    with pytest.raises(BootstrapError):
        build_paired_evidence(comparison, random_seed=7, resamples=0)


def test_evidence_rejects_empty_pairs() -> None:
    comparison = _ten_seed_comparison().model_copy(update={"pairs": []})

    with pytest.raises(EvidenceError, match="No paired observations"):
        build_paired_evidence(comparison, random_seed=7)


def test_evidence_rejects_duplicate_seeds() -> None:
    comparison = _ten_seed_comparison()
    duplicated = comparison.model_copy(
        update={"pairs": [*comparison.pairs, comparison.pairs[0]]}
    )

    with pytest.raises(EvidenceError, match=r"Duplicate paired seeds: \[1\]"):
        build_paired_evidence(duplicated, random_seed=7)


def test_evidence_contains_no_release_conclusion() -> None:
    evidence = build_paired_evidence(_ten_seed_comparison(), random_seed=7)
    fields = set(evidence.model_dump())

    assert not fields & {"decision", "severity", "verdict", "status", "finding"}
