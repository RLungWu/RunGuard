import pytest
from pydantic import ValidationError

from runguard.domain.models import MetricPoint, MetricSeries


def test_metric_point_can_be_created() -> None:
    point = MetricPoint(step=1, value=0.75)

    assert point.step == 1
    assert point.value == 0.75


def test_metric_point_preserves_missing_value() -> None:
    point = MetricPoint(step=1, value=None)

    assert point.value is None


def test_metric_series_sorts_points_by_step() -> None:
    series = MetricSeries(
        name="val_f1",
        points=[
            MetricPoint(step=3, value=0.8),
            MetricPoint(step=1, value=0.7),
            MetricPoint(step=2, value=0.75),
        ],
    )

    assert [point.step for point in series.points] == [1, 2, 3]


def test_metric_series_rejects_duplicate_steps() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        MetricSeries(
            name="val_f1",
            points=[
                MetricPoint(step=1, value=0.7),
                MetricPoint(step=1, value=0.8),
            ],
        )


def test_metric_point_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        MetricPoint(step=1, value=0.7, unexpected="not allowed")


def test_metric_series_round_trip() -> None:
    original = MetricSeries(
        name="val_f1",
        points=[MetricPoint(step=1, value=0.7)],
    )

    payload = original.model_dump()
    restored = MetricSeries.model_validate(payload)

    assert restored.model_dump() == original.model_dump()
