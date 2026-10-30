import pytest

from runguard.comparison.models import MetricDirection
from runguard.comparison.paired import compare_group
from runguard.domain.models import ExperimentGroup, Run, RunConfig
from runguard.statistics.evidence import build_paired_evidence
from runguard.statistics.models import PairedEvidence
from runguard.statistics.multi_metric import (
    MultiMetricError,
    build_multi_metric_evidence,
)

# Per seed: (baseline, candidate) summary values for each metric.
#   val_f1 (higher is better) improvements: +0.02, +0.01, +0.01, -0.01
#   latency_ms (lower is better) improvements: -2, -1, +1, 0
#   val_acc (higher is better) improvements: +0.01 on every seed
#   throughput (higher is better) improvements: 0 on every seed
METRICS = {
    "val_f1": {1: (0.80, 0.82), 2: (0.81, 0.82), 3: (0.79, 0.80), 4: (0.80, 0.79)},
    "latency_ms": {1: (10.0, 12.0), 2: (10.0, 11.0), 3: (10.0, 9.0), 4: (10.0, 10.0)},
    "val_acc": {1: (0.90, 0.91), 2: (0.89, 0.90), 3: (0.91, 0.92), 4: (0.90, 0.91)},
    "throughput": {
        1: (100.0, 100.0),
        2: (100.0, 100.0),
        3: (100.0, 100.0),
        4: (100.0, 100.0),
    },
}
DIRECTIONS = {
    "val_f1": MetricDirection.HIGHER_IS_BETTER,
    "latency_ms": MetricDirection.LOWER_IS_BETTER,
    "val_acc": MetricDirection.HIGHER_IS_BETTER,
    "throughput": MetricDirection.HIGHER_IS_BETTER,
}


def _group() -> ExperimentGroup:
    runs = [
        Run(
            run_id=f"{variant}-{seed}",
            variant=variant,
            seed=seed,
            config=RunConfig(values={}),
            metrics=[],
            summary_metrics={
                metric: values[seed][index] for metric, values in METRICS.items()
            },
        )
        for index, variant in enumerate(("baseline", "candidate"))
        for seed in (1, 2, 3, 4)
    ]
    return ExperimentGroup(group_id="multi-study", runs=runs)


def _evidence(
    metric: str, *, baseline: str = "baseline", candidate: str = "candidate"
) -> PairedEvidence:
    comparison = compare_group(
        _group(), baseline, candidate, metric, direction=DIRECTIONS[metric]
    )
    return build_paired_evidence(comparison, random_seed=7, resamples=100)


def test_reports_direction_conflict_for_secondary_regression() -> None:
    result = build_multi_metric_evidence(_evidence("val_f1"), [_evidence("latency_ms")])

    conflict = result.conflicts[0]
    assert conflict.primary_metric == "val_f1"
    assert conflict.secondary_metric == "latency_ms"
    # Means: val_f1 +0.0075; latency_ms (-2 - 1 + 1 + 0) / 4 = -0.5.
    assert conflict.primary_mean_improvement == pytest.approx(0.0075)
    assert conflict.secondary_mean_improvement == pytest.approx(-0.5)
    assert conflict.direction_conflict is True
    # Seeds 1 and 2 oppose; seed 3 agrees; seed 4 has a zero secondary.
    assert conflict.opposing_pair_count == 2
    assert conflict.sample_size == 4


def test_counts_opposing_pairs_without_mean_conflict() -> None:
    result = build_multi_metric_evidence(_evidence("val_f1"), [_evidence("val_acc")])

    conflict = result.conflicts[0]
    assert conflict.direction_conflict is False
    # Only seed 4 opposes: val_f1 regresses while val_acc improves.
    assert conflict.opposing_pair_count == 1


def test_zero_mean_is_not_a_direction_conflict() -> None:
    result = build_multi_metric_evidence(_evidence("val_f1"), [_evidence("throughput")])

    conflict = result.conflicts[0]
    assert conflict.secondary_mean_improvement == 0.0
    assert conflict.direction_conflict is False
    assert conflict.opposing_pair_count == 0


def test_preserves_each_metric_evidence_in_order() -> None:
    primary = _evidence("val_f1")
    secondaries = [_evidence("latency_ms"), _evidence("val_acc")]

    result = build_multi_metric_evidence(primary, secondaries)

    assert result.group_id == "multi-study"
    assert result.baseline_variant == "baseline"
    assert result.candidate_variant == "candidate"
    assert result.primary == primary
    assert result.secondaries == secondaries
    assert [c.secondary_metric for c in result.conflicts] == ["latency_ms", "val_acc"]
    assert result.secondaries[0].direction is MetricDirection.LOWER_IS_BETTER
    assert result.limitations


def test_rejects_missing_secondaries() -> None:
    with pytest.raises(MultiMetricError, match="At least one secondary"):
        build_multi_metric_evidence(_evidence("val_f1"), [])


def test_rejects_duplicate_metrics() -> None:
    with pytest.raises(MultiMetricError, match=r"Duplicate metrics: \['val_f1'\]"):
        build_multi_metric_evidence(_evidence("val_f1"), [_evidence("val_f1")])


def test_rejects_different_variants() -> None:
    reversed_secondary = _evidence(
        "latency_ms", baseline="candidate", candidate="baseline"
    )

    with pytest.raises(MultiMetricError, match="but the primary metric compares"):
        build_multi_metric_evidence(_evidence("val_f1"), [reversed_secondary])


def test_rejects_different_paired_runs() -> None:
    secondary = _evidence("latency_ms")
    renamed = [
        pair.model_copy(update={"candidate_run_id": f"other-{pair.seed}"})
        for pair in secondary.pairs
    ]
    mismatched = secondary.model_copy(update={"pairs": renamed})

    with pytest.raises(MultiMetricError, match="same paired runs"):
        build_multi_metric_evidence(_evidence("val_f1"), [mismatched])


def test_contains_no_release_conclusion() -> None:
    result = build_multi_metric_evidence(_evidence("val_f1"), [_evidence("latency_ms")])
    fields = set(result.model_dump()) | set(result.conflicts[0].model_dump())

    assert not fields & {"decision", "severity", "verdict", "status", "finding"}
