import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from runguard.domain.models import (
    ExperimentGroup,
    MetricPoint,
    MetricSeries,
    Run,
    RunConfig,
)

LocalJsonFormat = Literal["m0", "nested", "canonical"]


class _SourceModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class _M0Run(_SourceModel):
    id: str = Field(min_length=1)
    variant: str = Field(min_length=1)
    seed: int
    metrics: dict[str, float]


class _M0Document(_SourceModel):
    format_version: Literal[1]
    runs: list[_M0Run]


class _NestedExperiment(_SourceModel):
    id: str = Field(min_length=1)


class _NestedRun(_SourceModel):
    run_id: str = Field(min_length=1)
    variant: str | None = None
    seed: int | None = None
    config: dict[str, object] = Field(default_factory=dict)
    history: dict[str, list[MetricPoint]]
    summary: dict[str, float | None] = Field(default_factory=dict)
    metadata: dict[str, object] = Field(default_factory=dict)


class _NestedDocument(_SourceModel):
    experiment: _NestedExperiment
    runs: list[_NestedRun]


def load_local_json(
    path: Path,
    source_format: LocalJsonFormat,
    *,
    group_id: str | None = None,
) -> ExperimentGroup:
    """Load one supported local JSON format into an ExperimentGroup."""
    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    if source_format == "m0":
        return _convert_m0(_M0Document.model_validate(data), group_id)

    if source_format == "nested":
        return _convert_nested(_NestedDocument.model_validate(data))

    if source_format == "canonical":
        return ExperimentGroup.model_validate(data)

    raise ValueError(f"Unsupported local JSON format: {source_format}")


def _convert_m0(document: _M0Document, group_id: str | None) -> ExperimentGroup:
    if group_id is None:
        raise ValueError("group_id is required for the m0 JSON format")

    runs = [
        Run(
            run_id=run.id,
            variant=run.variant,
            seed=run.seed,
            config=RunConfig(values={}),
            metrics=[],
            summary_metrics={name: value for name, value in run.metrics.items()},
            source_metadata={"format": "m0", "format_version": document.format_version},
        )
        for run in document.runs
    ]
    return ExperimentGroup(group_id=group_id, runs=runs)


def _convert_nested(document: _NestedDocument) -> ExperimentGroup:
    runs = [
        Run(
            run_id=run.run_id,
            variant=run.variant,
            seed=run.seed,
            config=RunConfig(values=run.config),
            metrics=[
                MetricSeries(name=name, points=points)
                for name, points in run.history.items()
            ],
            summary_metrics=run.summary,
            source_metadata=run.metadata,
        )
        for run in document.runs
    ]
    return ExperimentGroup(group_id=document.experiment.id, runs=runs)
