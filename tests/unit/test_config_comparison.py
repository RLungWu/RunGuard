import pytest

from runguard.comparison.config import ConfigComparisonError, compare_run_configs
from runguard.comparison.models import ConfigComparisonEvidence, ConfigDifference
from runguard.comparison.paired import compare_group
from runguard.domain.models import ExperimentGroup, Run, RunConfig


def _run(run_id: str, variant: str, seed: int, config: dict[str, object]) -> Run:
    return Run(
        run_id=run_id,
        variant=variant,
        seed=seed,
        config=RunConfig(values=config),
        metrics=[],
        summary_metrics={"val_f1": 0.8},
    )


def _evidence(*runs: Run) -> ConfigComparisonEvidence:
    group = ExperimentGroup(group_id="config-study", runs=list(runs))
    return compare_run_configs(
        group, compare_group(group, "baseline", "candidate", "val_f1")
    )


def test_reports_only_differing_keys_per_pair() -> None:
    evidence = _evidence(
        _run("b-1", "baseline", 1, {"lr": 0.001, "optimizer": "adam", "epochs": 10}),
        _run("c-1", "candidate", 1, {"lr": 0.001, "optimizer": "adamw", "epochs": 10}),
    )

    assert evidence.differing_keys == ["optimizer"]
    pair = evidence.pairs[0]
    assert (pair.seed, pair.baseline_run_id, pair.candidate_run_id) == (1, "b-1", "c-1")
    assert pair.differences == [
        ConfigDifference(
            key="optimizer",
            baseline_present=True,
            candidate_present=True,
            baseline_value="adam",
            candidate_value="adamw",
        )
    ]


def test_distinguishes_missing_key_from_none() -> None:
    evidence = _evidence(
        _run("b-1", "baseline", 1, {"scheduler": None}),
        _run("c-1", "candidate", 1, {}),
    )

    difference = evidence.pairs[0].differences[0]
    assert difference.key == "scheduler"
    assert difference.baseline_present is True
    assert difference.candidate_present is False
    assert difference.baseline_value is None


def test_compares_values_type_sensitively() -> None:
    evidence = _evidence(
        _run("b-1", "baseline", 1, {"flag": 1, "ratio": 1, "nested": {"a": [1, 2]}}),
        _run(
            "c-1", "candidate", 1, {"flag": True, "ratio": 1.0, "nested": {"a": [1, 2]}}
        ),
    )

    assert evidence.differing_keys == ["flag", "ratio"]


def test_collects_keys_that_differ_on_some_pairs_only() -> None:
    evidence = _evidence(
        _run("b-1", "baseline", 1, {"batch_size": 32}),
        _run("c-1", "candidate", 1, {"batch_size": 32}),
        _run("b-2", "baseline", 2, {"batch_size": 32}),
        _run("c-2", "candidate", 2, {"batch_size": 64}),
    )

    assert evidence.differing_keys == ["batch_size"]
    assert [len(pair.differences) for pair in evidence.pairs] == [0, 1]


def test_rejects_comparison_from_another_group() -> None:
    runs = [_run("b-1", "baseline", 1, {}), _run("c-1", "candidate", 1, {})]
    group = ExperimentGroup(group_id="config-study", runs=runs)
    other = ExperimentGroup(group_id="other", runs=runs)

    with pytest.raises(ConfigComparisonError, match="not 'other'"):
        compare_run_configs(
            other, compare_group(group, "baseline", "candidate", "val_f1")
        )


def test_contains_no_compatibility_or_causal_conclusion() -> None:
    evidence = _evidence(
        _run("b-1", "baseline", 1, {"dataset": "v1"}),
        _run("c-1", "candidate", 1, {"dataset": "v2"}),
    )
    fields = set(evidence.model_dump())

    assert not fields & {"compatible", "decision", "cause", "verdict", "severity"}
