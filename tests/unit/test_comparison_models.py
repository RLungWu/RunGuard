import pytest
from pydantic import ValidationError

from runguard.comparison.models import (
    CheckpointPolicy,
    ComparisonPair,
    ComparisonResult,
    MetricDirection,
    ValueSource,
)


def test_comparison_pair_preserves_source_run_ids_and_differences() -> None:
    pair = ComparisonPair(
        seed=1,
        baseline_run_id="baseline-seed-1",
        candidate_run_id="candidate-seed-1",
        baseline_value=0.8,
        candidate_value=0.82,
        raw_difference=0.02,
        improvement_difference=0.02,
    )

    assert pair.seed == 1
    assert pair.baseline_run_id == "baseline-seed-1"
    assert pair.candidate_run_id == "candidate-seed-1"
    assert pair.raw_difference == pytest.approx(0.02)
    assert pair.improvement_difference == pytest.approx(0.02)


def test_comparison_result_defaults_to_source_reported_summary() -> None:
    pair = ComparisonPair(
        seed=1,
        baseline_run_id="baseline-seed-1",
        candidate_run_id="candidate-seed-1",
        baseline_value=0.8,
        candidate_value=0.82,
        raw_difference=0.02,
        improvement_difference=0.02,
    )
    result = ComparisonResult(
        group_id="experiment-1",
        baseline_variant="baseline",
        candidate_variant="candidate",
        metric="val_f1",
        direction=MetricDirection.HIGHER_IS_BETTER,
        pairs=[pair],
        mean_difference=0.02,
        median_difference=0.02,
        mean_improvement=0.02,
        median_improvement=0.02,
        positive_pair_count=1,
        positive_pair_rate=1.0,
    )

    assert result.value_source == "summary"
    assert result.direction is MetricDirection.HIGHER_IS_BETTER


def _result(pair: ComparisonPair, **overrides: object) -> ComparisonResult:
    fields: dict[str, object] = {
        "group_id": "experiment-1",
        "baseline_variant": "baseline",
        "candidate_variant": "candidate",
        "metric": "val_f1",
        "direction": MetricDirection.HIGHER_IS_BETTER,
        "pairs": [pair],
        "mean_difference": 0.02,
        "median_difference": 0.02,
        "mean_improvement": 0.02,
        "median_improvement": 0.02,
        "positive_pair_count": 1,
        "positive_pair_rate": 1.0,
    }
    fields.update(overrides)
    return ComparisonResult.model_validate(fields)


def _pair(baseline_step: int | None, candidate_step: int | None) -> ComparisonPair:
    return ComparisonPair(
        seed=1,
        baseline_run_id="baseline-seed-1",
        candidate_run_id="candidate-seed-1",
        baseline_value=0.8,
        candidate_value=0.82,
        raw_difference=0.02,
        improvement_difference=0.02,
        baseline_step=baseline_step,
        candidate_step=candidate_step,
    )


def test_comparison_result_accepts_history_with_policy_and_steps() -> None:
    result = _result(
        _pair(30, 20),
        value_source=ValueSource.HISTORY,
        checkpoint_policy=CheckpointPolicy.BEST,
    )

    assert result.pairs[0].candidate_step == 20


def test_comparison_result_rejects_history_without_policy() -> None:
    with pytest.raises(ValidationError, match="checkpoint_policy is required"):
        _result(_pair(30, 30), value_source=ValueSource.HISTORY)


def test_comparison_result_rejects_history_pair_without_steps() -> None:
    with pytest.raises(ValidationError, match="must record both steps"):
        _result(
            _pair(30, None),
            value_source=ValueSource.HISTORY,
            checkpoint_policy=CheckpointPolicy.FINAL,
        )


def test_comparison_result_rejects_summary_pair_with_steps() -> None:
    with pytest.raises(ValidationError, match="must not record steps"):
        _result(_pair(30, 30))
