from runguard.comparison.models import (
    ComparisonResult,
    ConfigComparisonEvidence,
    ConfigDifference,
    PairConfigDifferences,
)
from runguard.domain.models import ExperimentGroup, Run


class ConfigComparisonError(ValueError):
    """Raised when a comparison's runs cannot be found in the group."""


def compare_run_configs(
    group: ExperimentGroup,
    comparison: ComparisonResult,
) -> ConfigComparisonEvidence:
    """Describe top-level configuration differences for each compared pair.

    The pairs come from `comparison`, so the configurations described are
    exactly those of the compared runs. Values are compared type-sensitively:
    `1`, `1.0`, and `True` are different values.
    """
    if group.group_id != comparison.group_id:
        raise ConfigComparisonError(
            f"Comparison is for group '{comparison.group_id}', not '{group.group_id}'"
        )

    runs_by_id = {run.run_id: run for run in group.runs}
    pairs: list[PairConfigDifferences] = []
    for pair in comparison.pairs:
        baseline = _find_run(runs_by_id, pair.baseline_run_id)
        candidate = _find_run(runs_by_id, pair.candidate_run_id)
        pairs.append(
            PairConfigDifferences(
                seed=pair.seed,
                baseline_run_id=pair.baseline_run_id,
                candidate_run_id=pair.candidate_run_id,
                differences=_differences(baseline, candidate),
            )
        )

    differing_keys = sorted(
        {difference.key for pair in pairs for difference in pair.differences}
    )
    return ConfigComparisonEvidence(
        group_id=comparison.group_id,
        baseline_variant=comparison.baseline_variant,
        candidate_variant=comparison.candidate_variant,
        pairs=pairs,
        differing_keys=differing_keys,
    )


def _find_run(runs_by_id: dict[str, Run], run_id: str) -> Run:
    if run_id not in runs_by_id:
        raise ConfigComparisonError(f"Compared run '{run_id}' is not in the group")
    return runs_by_id[run_id]


def _differences(baseline: Run, candidate: Run) -> list[ConfigDifference]:
    baseline_values = baseline.config.values
    candidate_values = candidate.config.values
    differences: list[ConfigDifference] = []

    for key in sorted(baseline_values.keys() | candidate_values.keys()):
        baseline_present = key in baseline_values
        candidate_present = key in candidate_values
        baseline_value = baseline_values.get(key)
        candidate_value = candidate_values.get(key)
        if (
            baseline_present
            and candidate_present
            and _same_value(baseline_value, candidate_value)
        ):
            continue

        differences.append(
            ConfigDifference(
                key=key,
                baseline_present=baseline_present,
                candidate_present=candidate_present,
                baseline_value=baseline_value,
                candidate_value=candidate_value,
            )
        )

    return differences


def _same_value(first: object, second: object) -> bool:
    """Compare JSON-like values without Python's bool/int/float coercion."""
    if type(first) is not type(second):
        return False
    if isinstance(first, dict) and isinstance(second, dict):
        return first.keys() == second.keys() and all(
            _same_value(first[key], second[key]) for key in first
        )
    if isinstance(first, list) and isinstance(second, list):
        return len(first) == len(second) and all(
            _same_value(a, b) for a, b in zip(first, second, strict=True)
        )
    return first == second
