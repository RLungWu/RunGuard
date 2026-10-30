import math
from collections.abc import Sequence

from runguard.comparison.models import ComparisonPair
from runguard.statistics.models import (
    InsufficientEvidence,
    InsufficientEvidenceReason,
    LeaveOnePairOutChange,
    LeaveOnePairOutEvidence,
)


class SensitivityError(ValueError):
    """Raised when pairs cannot be used for a sensitivity calculation."""


def leave_one_pair_out(
    pairs: Sequence[ComparisonPair],
) -> LeaveOnePairOutEvidence | InsufficientEvidence:
    """Measure how the mean improvement changes when each pair is removed.

    Changes are reported in the order the caller supplies the pairs. The pair
    with the largest absolute change is identified; exact ties select the
    smallest seed so the result does not depend on input order.
    """
    if not pairs:
        raise SensitivityError("No paired observations to analyse")

    improvements = [pair.improvement_difference for pair in pairs]
    if not all(math.isfinite(value) for value in improvements):
        raise SensitivityError("Paired improvements must be finite")

    sample_size = len(improvements)
    if sample_size < 2:
        return InsufficientEvidence(
            reason=InsufficientEvidenceReason.FEWER_THAN_TWO_PAIRS,
            detail=(
                "Leave-one-pair-out sensitivity requires at least two paired "
                "observations so that a pair remains after removal"
            ),
            sample_size=sample_size,
        )

    total = sum(improvements)
    full_mean = total / sample_size
    changes: list[LeaveOnePairOutChange] = []

    for pair in pairs:
        leave_one_out_mean = (total - pair.improvement_difference) / (sample_size - 1)
        signed_change = leave_one_out_mean - full_mean
        changes.append(
            LeaveOnePairOutChange(
                seed=pair.seed,
                baseline_run_id=pair.baseline_run_id,
                candidate_run_id=pair.candidate_run_id,
                removed_improvement=pair.improvement_difference,
                leave_one_out_mean=leave_one_out_mean,
                signed_change=signed_change,
                absolute_change=abs(signed_change),
            )
        )

    largest = min(changes, key=lambda change: (-change.absolute_change, change.seed))
    return LeaveOnePairOutEvidence(
        full_mean=full_mean,
        sample_size=sample_size,
        changes=changes,
        largest_influence_seed=largest.seed,
    )
