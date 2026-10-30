import pytest

from runguard.comparison.models import (
    CheckpointPolicy,
    MetricDirection,
    MissingValue,
    MissingValueReason,
    SelectedValue,
    ValueSource,
)
from runguard.comparison.selection import ValueSelectionError, select_value
from runguard.domain.models import MetricPoint, MetricSeries, Run, RunConfig

HISTORY = ValueSource.HISTORY
FINAL = CheckpointPolicy.FINAL
BEST = CheckpointPolicy.BEST
LOWER = MetricDirection.LOWER_IS_BETTER


def _run(
    points: list[tuple[int, float | None]] | None = None,
    *,
    summary: dict[str, float | None] | None = None,
    series_count: int = 1,
) -> Run:
    metrics = []
    if points is not None:
        metrics = [
            MetricSeries(
                name="val_loss",
                points=[MetricPoint(step=step, value=value) for step, value in points],
            )
            for _ in range(series_count)
        ]
    return Run(
        run_id="run-1",
        config=RunConfig(values={}),
        metrics=metrics,
        summary_metrics=summary or {},
    )


def test_summary_selection_has_no_step() -> None:
    result = select_value(_run(summary={"val_loss": 0.4}), "val_loss")

    assert result == SelectedValue(run_id="run-1", value=0.4, step=None)


@pytest.mark.parametrize(
    ("summary", "reason"),
    [
        ({}, MissingValueReason.METRIC_NOT_FOUND),
        ({"val_loss": None}, MissingValueReason.MISSING_VALUE),
    ],
)
def test_summary_selection_reports_missing_evidence(
    summary: dict[str, float | None], reason: MissingValueReason
) -> None:
    result = select_value(_run(summary=summary), "val_loss")

    assert result == MissingValue(run_id="run-1", reason=reason)


def test_final_selects_greatest_step_regardless_of_input_order() -> None:
    run = _run([(30, 0.35), (10, 0.50), (20, 0.30)])

    result = select_value(
        run, "val_loss", value_source=HISTORY, checkpoint_policy=FINAL
    )

    assert result == SelectedValue(run_id="run-1", value=0.35, step=30)


def test_final_reports_missing_last_value_without_falling_back() -> None:
    run = _run([(10, 0.50), (20, 0.30), (30, None)])

    result = select_value(
        run, "val_loss", value_source=HISTORY, checkpoint_policy=FINAL
    )

    assert result == MissingValue(
        run_id="run-1", reason=MissingValueReason.MISSING_VALUE
    )


def test_best_uses_direction() -> None:
    run = _run([(10, 0.50), (20, 0.30), (30, 0.35)])

    lower = select_value(
        run,
        "val_loss",
        value_source=HISTORY,
        checkpoint_policy=BEST,
        direction=LOWER,
    )
    higher = select_value(run, "val_loss", value_source=HISTORY, checkpoint_policy=BEST)

    assert lower == SelectedValue(run_id="run-1", value=0.30, step=20)
    assert higher == SelectedValue(run_id="run-1", value=0.50, step=10)


def test_best_breaks_ties_by_earliest_step() -> None:
    run = _run([(30, 0.30), (10, 0.50), (20, 0.30)])

    result = select_value(
        run,
        "val_loss",
        value_source=HISTORY,
        checkpoint_policy=BEST,
        direction=LOWER,
    )

    assert result == SelectedValue(run_id="run-1", value=0.30, step=20)


def test_best_ignores_missing_values() -> None:
    run = _run([(10, None), (20, 0.40), (30, None)])

    result = select_value(
        run,
        "val_loss",
        value_source=HISTORY,
        checkpoint_policy=BEST,
        direction=LOWER,
    )

    assert result == SelectedValue(run_id="run-1", value=0.40, step=20)


@pytest.mark.parametrize(
    ("points", "reason"),
    [
        ([(10, None), (20, None)], MissingValueReason.NO_VALID_VALUE),
        ([(10, 0.4), (20, float("nan"))], MissingValueReason.NON_FINITE_VALUE),
        ([], MissingValueReason.EMPTY_HISTORY),
    ],
)
def test_best_reports_missing_evidence(
    points: list[tuple[int, float | None]], reason: MissingValueReason
) -> None:
    result = select_value(
        _run(points), "val_loss", value_source=HISTORY, checkpoint_policy=BEST
    )

    assert result == MissingValue(run_id="run-1", reason=reason)


@pytest.mark.parametrize("policy", [FINAL, BEST])
def test_history_does_not_fall_back_to_summary(policy: CheckpointPolicy) -> None:
    run = _run(summary={"val_loss": 0.4})

    result = select_value(
        run, "val_loss", value_source=HISTORY, checkpoint_policy=policy
    )

    assert result == MissingValue(
        run_id="run-1", reason=MissingValueReason.METRIC_NOT_FOUND
    )


def test_history_rejects_ambiguous_series() -> None:
    run = _run([(10, 0.5)], series_count=2)

    result = select_value(
        run, "val_loss", value_source=HISTORY, checkpoint_policy=FINAL
    )

    assert result == MissingValue(
        run_id="run-1", reason=MissingValueReason.AMBIGUOUS_SERIES
    )


def test_summary_rejects_checkpoint_policy() -> None:
    with pytest.raises(ValueSelectionError, match="do not take a checkpoint policy"):
        select_value(
            _run(summary={"val_loss": 0.4}), "val_loss", checkpoint_policy=BEST
        )


def test_history_requires_checkpoint_policy() -> None:
    with pytest.raises(ValueSelectionError, match="require a checkpoint policy"):
        select_value(_run([(10, 0.5)]), "val_loss", value_source=HISTORY)
