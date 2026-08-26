from pydantic import BaseModel, ConfigDict, model_validator
from typing_extensions import Self


class CanonicalModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class MetricPoint(CanonicalModel):
    step: int
    value: float | None


class MetricSeries(CanonicalModel):
    name: str
    points: list[MetricPoint]

    @model_validator(mode="after")
    def validate_points(self) -> Self:
        steps = [point.step for point in self.points]

        if len(steps) != len(set(steps)):
            raise ValueError("Metric point must not contain duplicate steps")

        self.points.sort(key=lambda point: point.step)

        return self
