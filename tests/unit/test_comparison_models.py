import pytest

from runguard.comparison.models import (
    ComparisonPair,
    ComparisonResult,
    MetricDirection,
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
