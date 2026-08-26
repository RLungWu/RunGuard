from pathlib import Path

import pytest
from pydantic import ValidationError

from runguard.domain.models import ExperimentGroup, MetricSeries, Run
from runguard.sources.local_json import load_local_json

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"
M0_FIXTURE = FIXTURES_DIR / "minimal-comparison.json"
NESTED_FIXTURE = FIXTURES_DIR / "nested-experiment.json"
CANONICAL_FIXTURE = FIXTURES_DIR / "canonical-experiment.json"
INVALID_NESTED_FIXTURE = FIXTURES_DIR / "invalid-nested-duplicate-step.json"


def test_m0_json_is_converted_to_canonical_group() -> None:
    group = load_local_json(M0_FIXTURE, "m0", group_id="m0-experiment")

    assert isinstance(group, ExperimentGroup)
    assert group.group_id == "m0-experiment"
    assert len(group.runs) == 6
    assert group.runs[0].variant == "baseline"
    assert group.runs[0].summary_metrics == {"val_f1": 0.8}
    assert group.runs[0].metrics == []


def test_m0_json_requires_explicit_group_id() -> None:
    with pytest.raises(ValueError, match="group_id is required"):
        load_local_json(M0_FIXTURE, "m0")


def test_nested_json_is_converted_to_canonical_group() -> None:
    group = load_local_json(NESTED_FIXTURE, "nested")

    assert isinstance(group, ExperimentGroup)
    assert group.group_id == "local-experiment"
    assert isinstance(group.runs[0], Run)
    assert isinstance(group.runs[0].metrics[0], MetricSeries)
    assert [point.step for point in group.runs[0].metrics[0].points] == [1, 2]


def test_canonical_json_is_validated_as_canonical_group() -> None:
    group = load_local_json(CANONICAL_FIXTURE, "canonical")

    assert isinstance(group, ExperimentGroup)
    assert group.group_id == "local-experiment"
    assert group.runs[1].variant == "candidate"


def test_local_json_formats_produce_canonical_models() -> None:
    inputs = [
        (M0_FIXTURE, "m0", {"group_id": "m0-experiment"}),
        (NESTED_FIXTURE, "nested", {}),
        (CANONICAL_FIXTURE, "canonical", {}),
    ]

    for path, source_format, kwargs in inputs:
        group = load_local_json(path, source_format, **kwargs)

        assert isinstance(group, ExperimentGroup)
        assert all(isinstance(run, Run) for run in group.runs)


def test_nested_json_rejects_duplicate_metric_steps() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        load_local_json(INVALID_NESTED_FIXTURE, "nested")


def test_canonical_json_round_trips() -> None:
    group = load_local_json(CANONICAL_FIXTURE, "canonical")

    restored = ExperimentGroup.model_validate(group.model_dump())

    assert restored.model_dump() == group.model_dump()
