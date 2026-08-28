from pathlib import Path

import pytest

from runguard.comparison.models import MetricDirection
from runguard.comparison.paired import ComparisonError, compare_group
from runguard.domain.models import ExperimentGroup, Run, RunConfig
from runguard.sources.local_json import load_local_json

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"
CANONICAL_FIXTURE = FIXTURES_DIR / "canonical-experiment.json"


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
