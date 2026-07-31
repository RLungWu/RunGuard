import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"


def load_fixture(filename: str) -> dict:
    fixture_path = FIXTURES_DIR / filename

    with fixture_path.open() as file:
        return json.load(file)


def test_minimal_fixture_has_expected_runs() -> None:
    data = load_fixture("minimal-comparison.json")

    assert data["format_version"] == 1
    assert len(data["runs"]) == 6


def test_minimal_fixture_has_paired_seeds() -> None:
    data = load_fixture("minimal-comparison.json")
    runs = data["runs"]

    baseline_seeds = {run["seed"] for run in runs if run["variant"] == "baseline"}

    candidate_seeds = {run["seed"] for run in runs if run["variant"] == "candidate"}

    assert baseline_seeds == {1, 2, 3}
    assert candidate_seeds == {1, 2, 3}
    assert baseline_seeds == candidate_seeds


def test_minimal_fixture_has_unique_run_ids() -> None:
    data = load_fixture("minimal-comparison.json")
    runs = data["runs"]

    run_ids = [run["id"] for run in runs]

    assert len(run_ids) == len(set(run_ids))


def test_minimal_fixture_has_numeric_metrics() -> None:
    data = load_fixture("minimal-comparison.json")

    for run in data["runs"]:
        assert "val_f1" in run["metrics"]
        assert isinstance(run["metrics"]["val_f1"], float)


def test_unpaired_fixture_has_mismatched_seeds() -> None:
    data = load_fixture("unpaired-comparison.json")
    runs = data["runs"]

    baseline_seeds = {run["seed"] for run in runs if run["variant"] == "baseline"}

    candidate_seeds = {run["seed"] for run in runs if run["variant"] == "candidate"}

    assert baseline_seeds == {1, 2}
    assert candidate_seeds == {1}
    assert baseline_seeds != candidate_seeds
