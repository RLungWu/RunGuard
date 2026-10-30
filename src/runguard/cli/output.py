import json

from runguard.comparison.models import ComparisonResult
from runguard.statistics.models import (
    EffectSize,
    InsufficientEvidence,
    PairedEvidence,
)

# The JSON layout follows PairedEvidence and may change until M4 introduces
# schema versioning (trade-off D7).
JSON_FORMAT = "runguard.paired-evidence"
JSON_STABILITY = "experimental"


def render_text(comparison: ComparisonResult, evidence: PairedEvidence) -> str:
    """Render the comparison summary followed by evidence-only statistics."""
    lines = [
        f"Comparison: {comparison.baseline_variant} → {comparison.candidate_variant}",
        f"Metric: {comparison.metric}",
        f"Value source: {comparison.value_source}",
    ]
    if comparison.checkpoint_policy is not None:
        lines.append(f"Checkpoint policy: {comparison.checkpoint_policy}")
    lines += [
        f"Direction: {comparison.direction.value}",
        f"Paired runs: {len(comparison.pairs)}",
        f"Mean paired difference: {comparison.mean_difference:+.6f}",
        f"Median paired difference: {comparison.median_difference:+.6f}",
        "Positive pairs: "
        f"{comparison.positive_pair_count}/{len(comparison.pairs)} "
        f"({comparison.positive_pair_rate:.2%})",
        "",
        "Evidence (direction-aware improvement):",
        f"Mean improvement: {evidence.mean_improvement:+.6f}",
        f"Median improvement: {evidence.median_improvement:+.6f}",
        f"Mean minus median: {evidence.mean_minus_median_improvement:+.6f}",
        _bootstrap_line(evidence),
        _effect_size_line(evidence.effect_size),
        _influence_line(evidence),
        "",
        "Pairs:",
        *_pair_lines(evidence),
        "",
        "Limitations:",
        *(f"- {limitation}" for limitation in evidence.limitations),
    ]
    return "\n".join(lines) + "\n"


def render_json(evidence: PairedEvidence) -> str:
    """Render evidence as experimental JSON with an explicit stability marker."""
    document = {
        "format": JSON_FORMAT,
        "stability": JSON_STABILITY,
        "evidence": evidence.model_dump(mode="json"),
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def _bootstrap_line(evidence: PairedEvidence) -> str:
    bootstrap = evidence.bootstrap
    if isinstance(bootstrap, InsufficientEvidence):
        return f"Bootstrap interval: {_insufficient(bootstrap)}"

    config = bootstrap.config
    return (
        f"{config.confidence_level:.0%} {config.method} bootstrap interval "
        f"for the {config.statistic}: "
        f"[{bootstrap.lower:+.6f}, {bootstrap.upper:+.6f}] "
        f"({config.resamples} resamples, random seed {config.random_seed})"
    )


def _effect_size_line(effect_size: EffectSize | InsufficientEvidence) -> str:
    if isinstance(effect_size, InsufficientEvidence):
        return f"Effect size (d_z): {_insufficient(effect_size)}"
    return (
        f"Effect size (d_z): {effect_size.value:+.3f} "
        f"(sample SD {effect_size.standard_deviation:.6f})"
    )


def _influence_line(evidence: PairedEvidence) -> str:
    loo = evidence.leave_one_pair_out
    if isinstance(loo, InsufficientEvidence):
        return f"Largest leave-one-pair-out change: {_insufficient(loo)}"

    largest = next(
        change for change in loo.changes if change.seed == loo.largest_influence_seed
    )
    return (
        f"Largest leave-one-pair-out change: {largest.signed_change:+.6f} "
        f"at seed {largest.seed} (mean without it {largest.leave_one_out_mean:+.6f})"
    )


def _pair_lines(evidence: PairedEvidence) -> list[str]:
    lines = []
    for pair in evidence.pairs:
        baseline = pair.baseline_run_id
        candidate = pair.candidate_run_id
        if pair.baseline_step is not None and pair.candidate_step is not None:
            baseline += f" @ step {pair.baseline_step}"
            candidate += f" @ step {pair.candidate_step}"
        lines.append(
            f"- seed {pair.seed}: {baseline} → {candidate}: "
            f"improvement {pair.improvement_difference:+.6f}"
        )
    return lines


def _insufficient(evidence: InsufficientEvidence) -> str:
    return f"insufficient evidence ({evidence.reason})"
