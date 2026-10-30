import pytest

from runguard.comparison.models import ComparisonPair
from runguard.statistics.models import (
    InsufficientEvidence,
    InsufficientEvidenceReason,
    LeaveOnePairOutEvidence,
)
from runguard.statistics.sensitivity import SensitivityError, leave_one_pair_out


def _pair(seed: int, improvement: float) -> ComparisonPair:
    # Higher-is-better pair whose improvement equals candidate - baseline.
    return ComparisonPair(
        seed=seed,
        baseline_run_id=f"baseline-{seed}",
        candidate_run_id=f"candidate-{seed}",
        baseline_value=0.0,
        candidate_value=improvement,
        raw_difference=improvement,
        improvement_difference=improvement,
    )


def test_leave_one_pair_out_matches_hand_calculation() -> None:
    # Improvements [1, 2, 3, 10]: full mean 4; removing each pair leaves
    # 15/3, 14/3, 13/3 and 6/3.
    result = leave_one_pair_out(
        [_pair(1, 1.0), _pair(2, 2.0), _pair(3, 3.0), _pair(4, 10.0)]
    )

    assert isinstance(result, LeaveOnePairOutEvidence)
    assert result.full_mean == pytest.approx(4.0)
    assert result.sample_size == 4
    assert [change.leave_one_out_mean for change in result.changes] == pytest.approx(
        [5.0, 14 / 3, 13 / 3, 2.0]
    )
    assert [change.signed_change for change in result.changes] == pytest.approx(
        [1.0, 2 / 3, 1 / 3, -2.0]
    )
    assert [change.absolute_change for change in result.changes] == pytest.approx(
        [1.0, 2 / 3, 1 / 3, 2.0]
    )
    assert result.largest_influence_seed == 4


def test_leave_one_pair_out_preserves_source_runs() -> None:
    result = leave_one_pair_out([_pair(1, 1.0), _pair(2, 3.0)])

    assert isinstance(result, LeaveOnePairOutEvidence)
    removed = result.changes[1]
    assert removed.seed == 2
    assert removed.baseline_run_id == "baseline-2"
    assert removed.candidate_run_id == "candidate-2"
    assert removed.removed_improvement == 3.0
    assert removed.leave_one_out_mean == 1.0


def test_leave_one_pair_out_breaks_ties_by_smallest_seed() -> None:
    # Both pairs move the mean by exactly 1; the input order must not matter.
    result = leave_one_pair_out([_pair(5, -1.0), _pair(2, 1.0)])

    assert isinstance(result, LeaveOnePairOutEvidence)
    assert [change.seed for change in result.changes] == [5, 2]
    assert [change.signed_change for change in result.changes] == [1.0, -1.0]
    assert result.largest_influence_seed == 2


def test_leave_one_pair_out_reports_insufficient_evidence_for_single_pair() -> None:
    result = leave_one_pair_out([_pair(1, 0.5)])

    assert isinstance(result, InsufficientEvidence)
    assert result.reason is InsufficientEvidenceReason.FEWER_THAN_TWO_PAIRS
    assert result.sample_size == 1


def test_leave_one_pair_out_rejects_empty_pairs() -> None:
    with pytest.raises(SensitivityError, match="No paired observations"):
        leave_one_pair_out([])


def test_leave_one_pair_out_rejects_non_finite_improvements() -> None:
    with pytest.raises(SensitivityError, match="finite"):
        leave_one_pair_out([_pair(1, 1.0), _pair(2, float("nan"))])
