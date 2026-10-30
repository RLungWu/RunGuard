from pathlib import Path

import pytest

from runguard.comparison.models import CheckpointPolicy, MetricDirection, ValueSource
from runguard.comparison.paired import ComparisonError, compare_group
from runguard.domain.models import (
    ExperimentGroup,
    MetricPoint,
    MetricSeries,
    Run,
    RunConfig,
)
from runguard.sources.local_json import load_local_json

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"
CANONICAL_FIXTURE = FIXTURES_DIR / "canonical-experiment.json"
SINGLE_SEED_IMPROVEMENT_FIXTURE = FIXTURES_DIR / "single-seed-improvement.json"
STABLE_IMPROVEMENT_FIXTURE = FIXTURES_DIR / "stable-improvement.json"


def test_compare_group_uses_summary_metrics_and_preserves_provenance() -> None:
    group = load_local_json(CANONICAL_FIXTURE, "canonical")

    result = compare_group(group, "baseline", "candidate", "val_f1")

    assert result.value_source == "summary"
    assert result.mean_difference == pytest.approx(0.02)
    assert result.median_difference == pytest.approx(0.02)
    assert result.mean_improvement == pytest.approx(0.02)
    assert result.positive_pair_count == 1
    assert result.positive_pair_rate == pytest.approx(1.0)
    assert result.pairs[0].baseline_run_id == "baseline-seed-1"
    assert result.pairs[0].candidate_run_id == "candidate-seed-1"


def test_compare_group_orders_pairs_by_seed() -> None:
    group = _group(
        _run("candidate-2", "candidate", 2, 0.85),
        _run("baseline-1", "baseline", 1, 0.8),
        _run("candidate-1", "candidate", 1, 0.85),
        _run("baseline-2", "baseline", 2, 0.88),
    )

    result = compare_group(group, "baseline", "candidate", "val_f1")

    assert [pair.seed for pair in result.pairs] == [1, 2]
    assert result.mean_difference == pytest.approx(0.01)
    assert result.positive_pair_count == 1


def test_compare_group_aggregates_stable_multi_seed_improvement() -> None:
    group = load_local_json(STABLE_IMPROVEMENT_FIXTURE, "canonical")

    result = compare_group(group, "baseline", "candidate", "val_f1")

    assert [pair.seed for pair in result.pairs] == [1, 2, 3]
    assert result.mean_difference == pytest.approx(0.02)
    assert result.median_difference == pytest.approx(0.02)
    assert result.positive_pair_count == 3
    assert result.positive_pair_rate == pytest.approx(1.0)


def test_compare_group_does_not_overstate_single_seed_improvement() -> None:
    group = load_local_json(SINGLE_SEED_IMPROVEMENT_FIXTURE, "canonical")

    result = compare_group(group, "baseline", "candidate", "val_f1")

    assert result.mean_difference == pytest.approx(0.0033333333333332993)
    assert result.median_difference == pytest.approx(0.0)
    assert result.positive_pair_count == 1
    assert result.positive_pair_rate == pytest.approx(1 / 3)


def test_compare_group_normalizes_lower_is_better_improvement() -> None:
    group = _group(
        _run(
            "baseline-1",
            "baseline",
            1,
            0.20,
            summary_metrics={"val_loss": 0.20},
        ),
        _run(
            "candidate-1",
            "candidate",
            1,
            0.15,
            summary_metrics={"val_loss": 0.15},
        ),
    )

    result = compare_group(
        group,
        "baseline",
        "candidate",
        "val_loss",
        direction=MetricDirection.LOWER_IS_BETTER,
    )

    assert result.mean_difference == pytest.approx(-0.05)
    assert result.mean_improvement == pytest.approx(0.05)
    assert result.pairs[0].raw_difference == pytest.approx(-0.05)
    assert result.pairs[0].improvement_difference == pytest.approx(0.05)
    assert result.positive_pair_rate == pytest.approx(1.0)


def test_compare_group_rejects_unpaired_seeds() -> None:
    group = _group(
        _run("baseline-1", "baseline", 1, 0.8),
        _run("candidate-2", "candidate", 2, 0.82),
    )

    with pytest.raises(ComparisonError, match="missing baseline seeds"):
        compare_group(group, "baseline", "candidate", "val_f1")


def test_compare_group_rejects_run_without_seed() -> None:
    group = _group(
        _run("baseline-without-seed", "baseline", None, 0.8),
        _run("candidate-1", "candidate", 1, 0.82),
    )

    with pytest.raises(ComparisonError, match="must have a seed"):
        compare_group(group, "baseline", "candidate", "val_f1")


def test_compare_group_rejects_missing_summary_metric() -> None:
    group = _group(
        _run("baseline-1", "baseline", 1, 0.8),
        _run("candidate-1", "candidate", 1, 0.82, summary_metrics={}),
    )

    with pytest.raises(ComparisonError, match="missing from summary metrics"):
        compare_group(group, "baseline", "candidate", "val_f1")


def test_compare_group_rejects_missing_summary_value() -> None:
    group = _group(
        _run("baseline-1", "baseline", 1, 0.8),
        _run("candidate-1", "candidate", 1, None),
    )

    with pytest.raises(ComparisonError, match="missing summary value"):
        compare_group(group, "baseline", "candidate", "val_f1")


def test_compare_group_rejects_duplicate_variant_seed() -> None:
    group = _group(
        _run("baseline-1a", "baseline", 1, 0.8),
        _run("baseline-1b", "baseline", 1, 0.81),
        _run("candidate-1", "candidate", 1, 0.82),
    )

    with pytest.raises(ComparisonError, match="Duplicate seeds"):
        compare_group(group, "baseline", "candidate", "val_f1")


def _group(*runs: Run) -> ExperimentGroup:
    return ExperimentGroup(group_id="test-group", runs=list(runs))


def _run(
    run_id: str,
    variant: str,
    seed: int | None,
    value: float | None,
    *,
    summary_metrics: dict[str, float | None] | None = None,
) -> Run:
    return Run(
        run_id=run_id,
        variant=variant,
        seed=seed,
        config=RunConfig(values={}),
        metrics=[],
        summary_metrics=(
            {"val_f1": value} if summary_metrics is None else summary_metrics
        ),
    )


def test_compare_group_selects_final_checkpoint_with_steps() -> None:
    group = _checkpoint_group()

    result = compare_group(
        group,
        "baseline",
        "candidate",
        "val_loss",
        direction=MetricDirection.LOWER_IS_BETTER,
        value_source=ValueSource.HISTORY,
        checkpoint_policy=CheckpointPolicy.FINAL,
    )

    # Final values: baseline 0.40 / 0.42, candidate 0.45 / 0.44 (regression).
    assert result.value_source is ValueSource.HISTORY
    assert result.checkpoint_policy is CheckpointPolicy.FINAL
    assert [pair.baseline_step for pair in result.pairs] == [30, 30]
    assert [pair.candidate_step for pair in result.pairs] == [30, 30]
    assert [pair.improvement_difference for pair in result.pairs] == pytest.approx(
        [-0.05, -0.02]
    )
    assert result.positive_pair_count == 0


def test_compare_group_selects_best_checkpoint_with_steps() -> None:
    group = _checkpoint_group()

    result = compare_group(
        group,
        "baseline",
        "candidate",
        "val_loss",
        direction=MetricDirection.LOWER_IS_BETTER,
        value_source=ValueSource.HISTORY,
        checkpoint_policy=CheckpointPolicy.BEST,
    )

    # Best values: baseline 0.40@30 / 0.42@30, candidate 0.30@10 / 0.33@20.
    assert result.checkpoint_policy is CheckpointPolicy.BEST
    assert [pair.baseline_step for pair in result.pairs] == [30, 30]
    assert [pair.candidate_step for pair in result.pairs] == [10, 20]
    assert [pair.improvement_difference for pair in result.pairs] == pytest.approx(
        [0.10, 0.09]
    )
    assert result.positive_pair_count == 2


def test_compare_group_summary_pairs_have_no_steps() -> None:
    group = _checkpoint_group()

    result = compare_group(group, "baseline", "candidate", "val_loss")

    assert result.checkpoint_policy is None
    assert all(
        pair.baseline_step is None and pair.candidate_step is None
        for pair in result.pairs
    )


def test_compare_group_reports_missing_final_value_run_ids() -> None:
    group = _group(
        _history_run("baseline-1", "baseline", 1, [(10, 0.5), (20, 0.4)]),
        _history_run("candidate-1", "candidate", 1, [(10, 0.4), (20, None)]),
    )

    with pytest.raises(
        ComparisonError,
        match=(
            r"Metric 'val_loss' has a missing value at the final checkpoint for "
            r"variant 'candidate': \['candidate-1'\]"
        ),
    ):
        compare_group(
            group,
            "baseline",
            "candidate",
            "val_loss",
            value_source=ValueSource.HISTORY,
            checkpoint_policy=CheckpointPolicy.FINAL,
        )


def test_compare_group_reports_every_missing_history_reason() -> None:
    group = _group(
        _history_run("baseline-1", "baseline", 1, [(10, None)]),
        _history_run("baseline-2", "baseline", 2, None),
        _history_run("candidate-1", "candidate", 1, [(10, 0.4)]),
        _history_run("candidate-2", "candidate", 2, [(10, 0.4)]),
    )

    with pytest.raises(ComparisonError) as error:
        compare_group(
            group,
            "baseline",
            "candidate",
            "val_loss",
            value_source=ValueSource.HISTORY,
            checkpoint_policy=CheckpointPolicy.BEST,
        )

    message = str(error.value)
    assert "has no history series for variant 'baseline': ['baseline-2']" in message
    assert "no non-missing history value for the best checkpoint" in message
    assert "['baseline-1']" in message


@pytest.mark.parametrize(
    ("value_source", "checkpoint_policy", "match"),
    [
        (ValueSource.SUMMARY, CheckpointPolicy.BEST, "do not take a checkpoint"),
        (ValueSource.HISTORY, None, "require a checkpoint policy"),
    ],
)
def test_compare_group_rejects_mismatched_value_selection(
    value_source: ValueSource,
    checkpoint_policy: CheckpointPolicy | None,
    match: str,
) -> None:
    with pytest.raises(ComparisonError, match=match):
        compare_group(
            _checkpoint_group(),
            "baseline",
            "candidate",
            "val_loss",
            value_source=value_source,
            checkpoint_policy=checkpoint_policy,
        )


def _history_run(
    run_id: str,
    variant: str,
    seed: int,
    points: list[tuple[int, float | None]] | None,
) -> Run:
    metrics = []
    if points is not None:
        metrics = [
            MetricSeries(
                name="val_loss",
                points=[MetricPoint(step=step, value=value) for step, value in points],
            )
        ]
    return Run(
        run_id=run_id,
        variant=variant,
        seed=seed,
        config=RunConfig(values={}),
        metrics=metrics,
        summary_metrics={"val_loss": 0.5},
    )


def _checkpoint_group() -> ExperimentGroup:
    # Candidate reaches a better best checkpoint but ends worse at the final step.
    return _group(
        _history_run("baseline-1", "baseline", 1, [(10, 0.50), (20, 0.45), (30, 0.40)]),
        _history_run("baseline-2", "baseline", 2, [(10, 0.52), (20, 0.47), (30, 0.42)]),
        _history_run(
            "candidate-1", "candidate", 1, [(10, 0.30), (20, 0.35), (30, 0.45)]
        ),
        _history_run(
            "candidate-2", "candidate", 2, [(10, 0.36), (20, 0.33), (30, 0.44)]
        ),
    )
