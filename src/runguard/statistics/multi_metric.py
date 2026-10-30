from collections.abc import Sequence

from runguard.statistics.models import (
    MetricConflictEvidence,
    MultiMetricEvidence,
    PairedEvidence,
)

MULTI_METRIC_LIMITATIONS = (
    "Direction conflict compares only the signs of mean improvements; it does "
    "not account for uncertainty or practical-significance thresholds.",
    "Metrics are evaluated on the same paired runs, but correlation between "
    "metrics is not modelled.",
)


class MultiMetricError(ValueError):
    """Raised when per-metric evidence cannot be combined."""


def build_multi_metric_evidence(
    primary: PairedEvidence,
    secondaries: Sequence[PairedEvidence],
) -> MultiMetricEvidence:
    """Combine per-metric evidence and describe direction conflicts.

    Every metric must come from the same group and variants and use exactly
    the same paired runs, so that conflicts compare like with like. Each
    metric's own value source, checkpoint policy, and statistics are kept.
    """
    if not secondaries:
        raise MultiMetricError("At least one secondary metric is required")

    _validate_same_pairs(primary, secondaries)

    return MultiMetricEvidence(
        group_id=primary.group_id,
        baseline_variant=primary.baseline_variant,
        candidate_variant=primary.candidate_variant,
        primary=primary,
        secondaries=list(secondaries),
        conflicts=[_conflict(primary, secondary) for secondary in secondaries],
        limitations=list(MULTI_METRIC_LIMITATIONS),
    )


def _validate_same_pairs(
    primary: PairedEvidence, secondaries: Sequence[PairedEvidence]
) -> None:
    metrics = [primary.metric, *(secondary.metric for secondary in secondaries)]
    duplicate_metrics = sorted({m for m in metrics if metrics.count(m) > 1})
    if duplicate_metrics:
        raise MultiMetricError(f"Duplicate metrics: {duplicate_metrics}")

    expected_scope = _scope(primary)
    expected_runs = _paired_runs(primary)
    for secondary in secondaries:
        if _scope(secondary) != expected_scope:
            raise MultiMetricError(
                f"Metric '{secondary.metric}' compares {_scope(secondary)}, "
                f"but the primary metric compares {expected_scope}"
            )
        if _paired_runs(secondary) != expected_runs:
            raise MultiMetricError(
                f"Metric '{secondary.metric}' does not use the same paired runs "
                f"as primary metric '{primary.metric}'"
            )


def _scope(evidence: PairedEvidence) -> tuple[str, str, str]:
    return (evidence.group_id, evidence.baseline_variant, evidence.candidate_variant)


def _paired_runs(evidence: PairedEvidence) -> list[tuple[int, str, str]]:
    return [
        (pair.seed, pair.baseline_run_id, pair.candidate_run_id)
        for pair in evidence.pairs
    ]


def _conflict(
    primary: PairedEvidence, secondary: PairedEvidence
) -> MetricConflictEvidence:
    # Pairs are seed-ordered in both objects and validated to match, so they
    # line up by position.
    opposing_pair_count = sum(
        _opposite_signs(p.improvement_difference, s.improvement_difference)
        for p, s in zip(primary.pairs, secondary.pairs, strict=True)
    )
    return MetricConflictEvidence(
        primary_metric=primary.metric,
        secondary_metric=secondary.metric,
        primary_mean_improvement=primary.mean_improvement,
        secondary_mean_improvement=secondary.mean_improvement,
        direction_conflict=_opposite_signs(
            primary.mean_improvement, secondary.mean_improvement
        ),
        opposing_pair_count=opposing_pair_count,
        sample_size=primary.sample_size,
    )


def _opposite_signs(first: float, second: float) -> bool:
    return (first > 0 and second < 0) or (first < 0 and second > 0)
