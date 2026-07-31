import json
from pathlib import Path
from typing import TypedDict, cast


class Run(TypedDict):
    id: str
    variant: str
    seed: int
    metrics: dict[str, float]


class ExperimentFixture(TypedDict):
    format_version: int
    runs: list[Run]


def load_runs(filename: Path) -> ExperimentFixture:
    with filename.open(encoding="utf-8") as file:
        data = json.load(file)

    return cast(ExperimentFixture, data)


def paired_differences(filename: Path) -> list[float]:
    data = load_runs(filename)
    runs = data["runs"]

    baseline_by_seed = {
        run["seed"]: run["metrics"]["val_f1"]
        for run in runs
        if run["variant"] == "baseline"
    }
    candidate_by_seed = {
        run["seed"]: run["metrics"]["val_f1"]
        for run in runs
        if run["variant"] == "candidate"
    }

    if baseline_by_seed.keys() != candidate_by_seed.keys():
        raise ValueError("Baseline and candidate seeds do not match")

    return [
        candidate_by_seed[seed] - baseline_by_seed[seed]
        for seed in sorted(baseline_by_seed)
    ]


def mean_difference(filename: Path) -> float:
    differences = paired_differences(filename)

    if not differences:
        raise ValueError("No paired runs found")

    return sum(differences) / len(differences)
