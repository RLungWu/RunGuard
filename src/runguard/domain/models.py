from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self


class CanonicalModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class MetricPoint(CanonicalModel):
    step: int
    value: float | None


class MetricSeries(CanonicalModel):
    name: str = Field(min_length=1)
    points: list[MetricPoint]

    @model_validator(mode="after")
    def validate_points(self) -> Self:
        steps = [point.step for point in self.points]

        if len(steps) != len(set(steps)):
            raise ValueError("Metric point must not contain duplicate steps")

        self.points.sort(key=lambda point: point.step)

        return self


class RunConfig(CanonicalModel):
    values: dict[str, object]


class Run(CanonicalModel):
    run_id: str = Field(min_length=1)
    seed: int | None = None
    config: RunConfig
    metrics: list[MetricSeries]
    summary_metrics: dict[str, float | None] = Field(default_factory=dict)
    source_metadata: dict[str, object] = Field(default_factory=dict)


class ExperimentGroup(CanonicalModel):
    group_id: str = Field(min_length=1)
    runs: list[Run]

    @model_validator(mode="after")
    def validate_unique_run_ids(self) -> Self:
        run_ids = [run.run_id for run in self.runs]

        if len(run_ids) != len(set(run_ids)):
            raise ValueError("Run IDs must be unique within an experiment group")

        return self
