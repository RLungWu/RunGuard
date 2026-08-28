from collections.abc import Iterable
from statistics import median

from runguard.comparison.models import (
    ComparisonPair,
    ComparisonResult,
    MetricDirection,
)
from runguard.domain.models import ExperimentGroup, Run


class ComparisonError(ValueError):
    """Raised when an experiment group cannot support a paired comparison."""


def compare_group(
    group: ExperimentGroup,
    baseline_variant: str,
    candidate_variant: str,
    metric: str,
    *,
    direction: MetricDirection = MetricDirection.HIGHER_IS_BETTER,
) -> ComparisonResult:
    """Compare source-reported summary metrics for runs paired by seed."""
    try:
        direction = MetricDirection(direction)
    except ValueError as error:
        raise ComparisonError(f"Unsupported metric direction: {direction}") from error

    if baseline_variant == candidate_variant:
        raise ComparisonError("Baseline and candidate variants must differ")

    baseline_runs = _select_runs(group.runs, baseline_variant)
    candidate_runs = _select_runs(group.runs, candidate_variant)

    baseline_by_seed = _index_runs(baseline_runs, baseline_variant, metric)
    candidate_by_seed = _index_runs(candidate_runs, candidate_variant, metric)

    baseline_seeds = set(baseline_by_seed)
    candidate_seeds = set(candidate_by_seed)
    if baseline_seeds != candidate_seeds:
        missing_from_baseline = sorted(candidate_seeds - baseline_seeds)
        missing_from_candidate = sorted(baseline_seeds - candidate_seeds)
        details: list[str] = []
        if missing_from_baseline:
            details.append(f"missing baseline seeds: {missing_from_baseline}")
        if missing_from_candidate:
            details.append(f"missing candidate seeds: {missing_from_candidate}")
        raise ComparisonError("Unpaired seeds; " + "; ".join(details))

    if not baseline_seeds:
        raise ComparisonError("No paired runs found")

    pairs = [
        _make_pair(
            seed,
            baseline_by_seed[seed],
            candidate_by_seed[seed],
            metric,
            direction,
        )
        for seed in sorted(baseline_seeds)
    ]
    raw_differences = [pair.raw_difference for pair in pairs]
    improvements = [pair.improvement_difference for pair in pairs]
    positive_pair_count = sum(improvement > 0 for improvement in improvements)

    return ComparisonResult(
        group_id=group.group_id,
        baseline_variant=baseline_variant,
        candidate_variant=candidate_variant,
        metric=metric,
        direction=direction,
        pairs=pairs,
        mean_difference=sum(raw_differences) / len(raw_differences),
        median_difference=median(raw_differences),
        mean_improvement=sum(improvements) / len(improvements),
        median_improvement=median(improvements),
        positive_pair_count=positive_pair_count,
        positive_pair_rate=positive_pair_count / len(improvements),
    )


def _select_runs(runs: Iterable[Run], variant: str) -> list[Run]:
    return [run for run in runs if run.variant == variant]


def _index_runs(runs: Iterable[Run], variant: str, metric: str) -> dict[int, Run]:
    indexed: dict[int, Run] = {}
    seen_seed_run_ids: dict[int, list[str]] = {}
    missing_seed_run_ids: list[str] = []
    missing_metric_run_ids: list[str] = []
    missing_value_run_ids: list[str] = []
    duplicate_seed_run_ids: dict[int, list[str]] = {}

    for run in runs:
        if run.seed is None:
            missing_seed_run_ids.append(run.run_id)
            continue

        seen_seed_run_ids.setdefault(run.seed, []).append(run.run_id)
        if len(seen_seed_run_ids[run.seed]) > 1:
            duplicate_seed_run_ids[run.seed] = seen_seed_run_ids[run.seed]
            continue

        if metric not in run.summary_metrics:
            missing_metric_run_ids.append(run.run_id)
            continue

        value = run.summary_metrics[metric]
        if value is None:
            missing_value_run_ids.append(run.run_id)
            continue

        indexed[run.seed] = run

    if missing_seed_run_ids:
        raise ComparisonError(
            f"Runs for variant '{variant}' must have a seed: "
            f"{sorted(missing_seed_run_ids)}"
        )
    if duplicate_seed_run_ids:
        raise ComparisonError(
            f"Duplicate seeds for variant '{variant}': {duplicate_seed_run_ids}"
        )
    if missing_metric_run_ids:
        raise ComparisonError(
            f"Metric '{metric}' is missing from summary metrics for variant "
            f"'{variant}': {sorted(missing_metric_run_ids)}"
        )
    if missing_value_run_ids:
        raise ComparisonError(
            f"Metric '{metric}' has a missing summary value for variant "
            f"'{variant}': {sorted(missing_value_run_ids)}"
        )

    return indexed


def _make_pair(
    seed: int,
    baseline: Run,
    candidate: Run,
    metric: str,
    direction: MetricDirection,
) -> ComparisonPair:
    baseline_value = _summary_value(baseline, metric)
    candidate_value = _summary_value(candidate, metric)
    raw_difference = candidate_value - baseline_value
    improvement_difference = (
        raw_difference
        if direction is MetricDirection.HIGHER_IS_BETTER
        else -raw_difference
    )

    return ComparisonPair(
        seed=seed,
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        baseline_value=baseline_value,
        candidate_value=candidate_value,
        raw_difference=raw_difference,
        improvement_difference=improvement_difference,
    )


def _summary_value(run: Run, metric: str) -> float:
    """Return the selected metric after _index_runs validated its presence."""
    value = run.summary_metrics[metric]
    if value is None:
        raise ComparisonError(
            f"Metric '{metric}' has a missing summary value for run '{run.run_id}'"
        )
    return value
