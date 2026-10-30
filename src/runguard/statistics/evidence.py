from statistics import median

from runguard.comparison.models import (
    CheckpointPolicy,
    ComparisonPair,
    ComparisonResult,
    ValueSource,
)
from runguard.statistics.bootstrap import bootstrap_mean, build_bootstrap_config
from runguard.statistics.effect_size import paired_cohens_dz
from runguard.statistics.models import (
    BootstrapInterval,
    InsufficientEvidence,
    InsufficientEvidenceReason,
    PairedEvidence,
    PositivePairEvidence,
)
from runguard.statistics.sensitivity import leave_one_pair_out

BASE_LIMITATIONS = (
    "Seed pairing does not verify dataset, code revision, or configuration "
    "comparability between baseline and candidate runs.",
    "Percentile bootstrap intervals can be discrete or unstable with few "
    "paired observations.",
    "Leave-one-pair-out changes are descriptive influence measurements; they "
    "do not label outliers or establish that one seed dominates the result.",
)


SUMMARY_LIMITATION = (
    "Summary metrics are source-reported values; no checkpoint selection policy "
    "was applied."
)
HISTORY_LIMITATION = (
    "Values were selected from metric history with the '{policy}' checkpoint "
    "policy; selected steps are recorded per pair and may differ between "
    "baseline and candidate runs."
)
BEST_CHECKPOINT_LIMITATION = (
    "Best-checkpoint selection takes the most favourable observed step of each "
    "run and can be optimistic compared with a checkpoint fixed in advance."
)


class EvidenceError(ValueError):
    """Raised when a comparison result cannot support statistical evidence."""


def build_paired_evidence(
    comparison: ComparisonResult,
    *,
    random_seed: int,
    confidence_level: float = 0.95,
    resamples: int = 10_000,
) -> PairedEvidence:
    """Build statistical evidence from a seed-paired comparison result.

    Every statistic is recalculated from the comparison pairs, ordered by seed,
    so the evidence can be reproduced from its stored pairs and parameters.
    """
    # Validate parameters even when the bootstrap will not run, so an invalid
    # configuration is never hidden behind insufficient evidence.
    config = build_bootstrap_config(confidence_level, resamples, random_seed)
    pairs = _ordered_pairs(comparison.pairs)
    improvements = [pair.improvement_difference for pair in pairs]
    sample_size = len(improvements)
    positive_count = sum(improvement > 0 for improvement in improvements)
    mean_improvement = sum(improvements) / sample_size
    median_improvement = median(improvements)

    bootstrap: BootstrapInterval | InsufficientEvidence
    if sample_size < 2:
        bootstrap = InsufficientEvidence(
            reason=InsufficientEvidenceReason.FEWER_THAN_TWO_PAIRS,
            detail=(
                "A bootstrap confidence interval requires at least two paired "
                "observations"
            ),
            sample_size=sample_size,
        )
    else:
        bootstrap = bootstrap_mean(
            improvements,
            confidence_level=config.confidence_level,
            resamples=config.resamples,
            random_seed=config.random_seed,
        )

    return PairedEvidence(
        group_id=comparison.group_id,
        baseline_variant=comparison.baseline_variant,
        candidate_variant=comparison.candidate_variant,
        metric=comparison.metric,
        direction=comparison.direction,
        value_source=comparison.value_source,
        checkpoint_policy=comparison.checkpoint_policy,
        pairs=pairs,
        sample_size=sample_size,
        mean_improvement=mean_improvement,
        median_improvement=median_improvement,
        mean_minus_median_improvement=mean_improvement - median_improvement,
        positive_pairs=PositivePairEvidence(
            count=positive_count,
            sample_size=sample_size,
            rate=positive_count / sample_size,
        ),
        effect_size=paired_cohens_dz(improvements),
        bootstrap=bootstrap,
        leave_one_pair_out=leave_one_pair_out(pairs),
        limitations=[*BASE_LIMITATIONS, *_value_limitations(comparison)],
    )


def _ordered_pairs(pairs: list[ComparisonPair]) -> list[ComparisonPair]:
    if not pairs:
        raise EvidenceError("No paired observations to analyse")

    seeds = [pair.seed for pair in pairs]
    duplicate_seeds = sorted({seed for seed in seeds if seeds.count(seed) > 1})
    if duplicate_seeds:
        raise EvidenceError(f"Duplicate paired seeds: {duplicate_seeds}")

    return sorted(pairs, key=lambda pair: pair.seed)


def _value_limitations(comparison: ComparisonResult) -> list[str]:
    policy = comparison.checkpoint_policy
    if comparison.value_source is ValueSource.SUMMARY or policy is None:
        return [SUMMARY_LIMITATION]

    limitations = [HISTORY_LIMITATION.format(policy=policy.value)]
    if policy is CheckpointPolicy.BEST:
        limitations.append(BEST_CHECKPOINT_LIMITATION)
    return limitations
