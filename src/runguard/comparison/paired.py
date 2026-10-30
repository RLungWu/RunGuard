from collections.abc import Iterable
from dataclasses import dataclass
from statistics import median

from runguard.comparison.models import (
    CheckpointPolicy,
    ComparisonPair,
    ComparisonResult,
    MetricDirection,
    MissingValue,
    MissingValueReason,
    SelectedValue,
    ValueSource,
)
from runguard.comparison.selection import (
    select_value,
    validate_value_selection,
)
from runguard.domain.models import ExperimentGroup, Run


class ComparisonError(ValueError):
    """Raised when an experiment group cannot support a paired comparison."""


@dataclass(frozen=True)
class _Selection:
    metric: str
    value_source: ValueSource
    checkpoint_policy: CheckpointPolicy | None
    direction: MetricDirection

    def missing_message(self, reason: MissingValueReason) -> str:
        if self.value_source is ValueSource.SUMMARY:
            summary_messages = {
                MissingValueReason.METRIC_NOT_FOUND: "is missing from summary metrics",
                MissingValueReason.MISSING_VALUE: "has a missing summary value",
            }
            return summary_messages[reason]

        policy = self.checkpoint_policy
        history_messages = {
            MissingValueReason.METRIC_NOT_FOUND: "has no history series",
            MissingValueReason.AMBIGUOUS_SERIES: "has more than one history series",
            MissingValueReason.EMPTY_HISTORY: "has an empty history series",
            MissingValueReason.MISSING_VALUE: (
                f"has a missing value at the {policy} checkpoint"
            ),
            MissingValueReason.NO_VALID_VALUE: (
                f"has no non-missing history value for the {policy} checkpoint"
            ),
            MissingValueReason.NON_FINITE_VALUE: (
                f"has non-finite history values that cannot be ranked for the "
                f"{policy} checkpoint"
            ),
        }
        return history_messages[reason]


def compare_group(
    group: ExperimentGroup,
    baseline_variant: str,
    candidate_variant: str,
    metric: str,
    *,
    direction: MetricDirection = MetricDirection.HIGHER_IS_BETTER,
    value_source: ValueSource = ValueSource.SUMMARY,
    checkpoint_policy: CheckpointPolicy | None = None,
) -> ComparisonResult:
    """Compare one selected metric value per run, for runs paired by seed.

    Values default to source-reported summary metrics. History values require
    an explicit checkpoint policy; there is no fallback between sources.
    """
    try:
        direction = MetricDirection(direction)
    except ValueError as error:
        raise ComparisonError(f"Unsupported metric direction: {direction}") from error

    try:
        value_source = ValueSource(value_source)
        if checkpoint_policy is not None:
            checkpoint_policy = CheckpointPolicy(checkpoint_policy)
        validate_value_selection(value_source, checkpoint_policy)
    except ValueError as error:
        raise ComparisonError(str(error)) from error

    if baseline_variant == candidate_variant:
        raise ComparisonError("Baseline and candidate variants must differ")

    baseline_runs = _select_runs(group.runs, baseline_variant)
    candidate_runs = _select_runs(group.runs, candidate_variant)

    selection = _Selection(metric, value_source, checkpoint_policy, direction)
    baseline_by_seed = _index_runs(baseline_runs, baseline_variant, selection)
    candidate_by_seed = _index_runs(candidate_runs, candidate_variant, selection)

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
        _make_pair(seed, baseline_by_seed[seed], candidate_by_seed[seed], direction)
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
        value_source=value_source,
        checkpoint_policy=checkpoint_policy,
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


def _index_runs(
    runs: Iterable[Run], variant: str, selection: _Selection
) -> dict[int, SelectedValue]:
    indexed: dict[int, SelectedValue] = {}
    seen_seed_run_ids: dict[int, list[str]] = {}
    missing_seed_run_ids: list[str] = []
    missing_by_reason: dict[MissingValueReason, list[str]] = {}
    duplicate_seed_run_ids: dict[int, list[str]] = {}

    for run in runs:
        if run.seed is None:
            missing_seed_run_ids.append(run.run_id)
            continue

        seen_seed_run_ids.setdefault(run.seed, []).append(run.run_id)
        if len(seen_seed_run_ids[run.seed]) > 1:
            duplicate_seed_run_ids[run.seed] = seen_seed_run_ids[run.seed]
            continue

        selected = select_value(
            run,
            selection.metric,
            value_source=selection.value_source,
            checkpoint_policy=selection.checkpoint_policy,
            direction=selection.direction,
        )
        if isinstance(selected, MissingValue):
            missing_by_reason.setdefault(selected.reason, []).append(run.run_id)
            continue

        indexed[run.seed] = selected

    if missing_seed_run_ids:
        raise ComparisonError(
            f"Runs for variant '{variant}' must have a seed: "
            f"{sorted(missing_seed_run_ids)}"
        )
    if duplicate_seed_run_ids:
        raise ComparisonError(
            f"Duplicate seeds for variant '{variant}': {duplicate_seed_run_ids}"
        )
    if missing_by_reason:
        # Report every kind of missing evidence, in a stable reason order.
        details = [
            f"Metric '{selection.metric}' {selection.missing_message(reason)} "
            f"for variant '{variant}': {sorted(missing_by_reason[reason])}"
            for reason in MissingValueReason
            if reason in missing_by_reason
        ]
        raise ComparisonError("; ".join(details))

    return indexed


def _make_pair(
    seed: int,
    baseline: SelectedValue,
    candidate: SelectedValue,
    direction: MetricDirection,
) -> ComparisonPair:
    raw_difference = candidate.value - baseline.value
    improvement_difference = (
        raw_difference
        if direction is MetricDirection.HIGHER_IS_BETTER
        else -raw_difference
    )

    return ComparisonPair(
        seed=seed,
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        baseline_value=baseline.value,
        candidate_value=candidate.value,
        raw_difference=raw_difference,
        improvement_difference=improvement_difference,
        baseline_step=baseline.step,
        candidate_step=candidate.step,
    )
