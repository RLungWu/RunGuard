import math

from runguard.comparison.models import (
    CheckpointPolicy,
    MetricDirection,
    MissingValue,
    MissingValueReason,
    SelectedValue,
    ValueSource,
)
from runguard.domain.models import Run


class ValueSelectionError(ValueError):
    """Raised when a value source and checkpoint policy do not fit together."""


def validate_value_selection(
    value_source: ValueSource,
    checkpoint_policy: CheckpointPolicy | None,
) -> None:
    """Require a checkpoint policy for history values and none for summary."""
    if value_source is ValueSource.SUMMARY and checkpoint_policy is not None:
        raise ValueSelectionError(
            f"Summary values do not take a checkpoint policy; got '{checkpoint_policy}'"
        )
    if value_source is ValueSource.HISTORY and checkpoint_policy is None:
        raise ValueSelectionError(
            "History values require a checkpoint policy: "
            f"{[policy.value for policy in CheckpointPolicy]}"
        )


def select_value(
    run: Run,
    metric: str,
    *,
    value_source: ValueSource = ValueSource.SUMMARY,
    checkpoint_policy: CheckpointPolicy | None = None,
    direction: MetricDirection = MetricDirection.HIGHER_IS_BETTER,
) -> SelectedValue | MissingValue:
    """Select one run's comparison value without any fallback.

    Summary values come from `summary_metrics`. History values come from the
    run's single series for the metric, using the final or the direction-aware
    best checkpoint. Missing evidence is returned rather than replaced.
    """
    validate_value_selection(value_source, checkpoint_policy)

    if checkpoint_policy is None:
        return _select_summary(run, metric)
    return _select_checkpoint(run, metric, checkpoint_policy, direction)


def _select_summary(run: Run, metric: str) -> SelectedValue | MissingValue:
    if metric not in run.summary_metrics:
        return MissingValue(
            run_id=run.run_id, reason=MissingValueReason.METRIC_NOT_FOUND
        )

    value = run.summary_metrics[metric]
    if value is None:
        return MissingValue(run_id=run.run_id, reason=MissingValueReason.MISSING_VALUE)

    return SelectedValue(run_id=run.run_id, value=value)


def _select_checkpoint(
    run: Run,
    metric: str,
    policy: CheckpointPolicy,
    direction: MetricDirection,
) -> SelectedValue | MissingValue:
    series = [series for series in run.metrics if series.name == metric]
    if not series:
        return MissingValue(
            run_id=run.run_id, reason=MissingValueReason.METRIC_NOT_FOUND
        )
    if len(series) > 1:
        return MissingValue(
            run_id=run.run_id, reason=MissingValueReason.AMBIGUOUS_SERIES
        )

    points = series[0].points
    if not points:
        return MissingValue(run_id=run.run_id, reason=MissingValueReason.EMPTY_HISTORY)

    if policy is CheckpointPolicy.FINAL:
        # The final point is reported even when its value is missing; earlier
        # points are never used in its place.
        final_point = max(points, key=lambda point: point.step)
        if final_point.value is None:
            return MissingValue(
                run_id=run.run_id, reason=MissingValueReason.MISSING_VALUE
            )
        return SelectedValue(
            run_id=run.run_id, value=final_point.value, step=final_point.step
        )

    observed = [
        (point.step, point.value) for point in points if point.value is not None
    ]
    if not observed:
        return MissingValue(run_id=run.run_id, reason=MissingValueReason.NO_VALID_VALUE)
    if not all(math.isfinite(value) for _, value in observed):
        return MissingValue(
            run_id=run.run_id, reason=MissingValueReason.NON_FINITE_VALUE
        )

    # Rank so that the best value sorts first, then the earliest step on ties.
    sign = 1 if direction is MetricDirection.HIGHER_IS_BETTER else -1
    best_step, best_value = min(observed, key=lambda item: (-sign * item[1], item[0]))
    return SelectedValue(run_id=run.run_id, value=best_value, step=best_step)
