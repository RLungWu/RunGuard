import pytest
from pydantic import ValidationError

from runguard.domain.models import (
    ArtifactReference,
    ExperimentGroup,
    MetricPoint,
    MetricSeries,
    Run,
    RunConfig,
)


def test_metric_point_can_be_created() -> None:
    point = MetricPoint(step=1, value=0.75)

    assert point.step == 1
    assert point.value == 0.75


def test_metric_point_preserves_missing_value() -> None:
    point = MetricPoint(step=1, value=None)

    assert point.value is None


def test_metric_point_rejects_type_coercion() -> None:
    with pytest.raises(ValidationError):
        MetricPoint(step="1", value=0.75)


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


def test_metric_series_serialization_is_stable_after_order_normalization() -> None:
    unordered = MetricSeries(
        name="val_f1",
        points=[
            MetricPoint(step=2, value=0.8),
            MetricPoint(step=1, value=0.7),
        ],
    )
    ordered = MetricSeries(
        name="val_f1",
        points=[
            MetricPoint(step=1, value=0.7),
            MetricPoint(step=2, value=0.8),
        ],
    )

    assert unordered.model_dump_json() == ordered.model_dump_json()


def test_artifact_reference_can_be_created() -> None:
    artifact = ArtifactReference(
        uri="s3://bucket/model.pt",
        artifact_type="model_checkpoint",
        digest="sha256:abc123",
    )

    assert artifact.uri == "s3://bucket/model.pt"
    assert artifact.artifact_type == "model_checkpoint"
    assert artifact.digest == "sha256:abc123"


def test_artifact_reference_rejects_empty_uri() -> None:
    with pytest.raises(ValidationError):
        ArtifactReference(uri="")


def test_artifact_reference_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ArtifactReference(uri="file:///tmp/model.pt", unexpected="not allowed")


def test_run_can_be_created_with_nested_models() -> None:
    run = Run(
        run_id="candidate-seed-1",
        variant="candidate",
        seed=1,
        config=RunConfig(values={"learning_rate": 0.001}),
        metrics=[
            MetricSeries(
                name="val_f1",
                points=[MetricPoint(step=1, value=0.75)],
            )
        ],
        artifacts=[
            ArtifactReference(
                uri="s3://bucket/model.pt",
                artifact_type="model_checkpoint",
            )
        ],
        summary_metrics={"val_f1": 0.75},
        source_metadata={"backend": "local-json"},
    )

    assert run.run_id == "candidate-seed-1"
    assert run.config.values["learning_rate"] == 0.001
    assert run.metrics[0].name == "val_f1"
    assert run.artifacts[0].uri == "s3://bucket/model.pt"


def test_run_allows_missing_seed_and_optional_metadata() -> None:
    run = Run(
        run_id="run-without-seed",
        config=RunConfig(values={}),
        metrics=[],
    )

    assert run.seed is None
    assert run.summary_metrics == {}
    assert run.source_metadata == {}
    assert run.artifacts == []


def test_run_rejects_empty_run_id() -> None:
    with pytest.raises(ValidationError):
        Run(run_id="", config=RunConfig(values={}), metrics=[])


def test_run_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Run(
            run_id="run-1",
            config=RunConfig(values={}),
            metrics=[],
            unexpected="not allowed",
        )


def test_run_round_trip() -> None:
    original = Run(
        run_id="candidate-seed-1",
        variant="candidate",
        seed=1,
        config=RunConfig(values={"learning_rate": 0.001}),
        metrics=[
            MetricSeries(
                name="val_f1",
                points=[
                    MetricPoint(step=2, value=0.8),
                    MetricPoint(step=1, value=0.75),
                ],
            )
        ],
        artifacts=[ArtifactReference(uri="s3://bucket/model.pt")],
        summary_metrics={"val_f1": 0.8},
        source_metadata={"backend": "local-json"},
    )

    payload = original.model_dump()
    restored = Run.model_validate(payload)

    assert restored.model_dump() == original.model_dump()


def test_run_preserves_conflicting_summary_and_history_values() -> None:
    run = Run(
        run_id="run-1",
        config=RunConfig(values={}),
        metrics=[
            MetricSeries(
                name="val_f1",
                points=[MetricPoint(step=1, value=0.8)],
            )
        ],
        summary_metrics={"val_f1": 0.9},
    )

    assert run.metrics[0].points[-1].value == 0.8
    assert run.summary_metrics["val_f1"] == 0.9


def make_run(run_id: str) -> Run:
    return Run(
        run_id=run_id,
        variant="candidate",
        seed=1,
        config=RunConfig(values={"learning_rate": 0.001}),
        metrics=[
            MetricSeries(
                name="val_f1",
                points=[MetricPoint(step=1, value=0.75)],
            )
        ],
    )


def test_experiment_group_can_be_created_with_nested_runs() -> None:
    group = ExperimentGroup(
        group_id="experiment-1",
        runs=[make_run("baseline-1"), make_run("candidate-1")],
    )

    assert group.group_id == "experiment-1"
    assert [run.run_id for run in group.runs] == ["baseline-1", "candidate-1"]


def test_experiment_group_rejects_duplicate_run_ids() -> None:
    with pytest.raises(ValidationError, match="unique"):
        ExperimentGroup(
            group_id="experiment-1",
            runs=[make_run("run-1"), make_run("run-1")],
        )


def test_experiment_group_rejects_empty_group_id() -> None:
    with pytest.raises(ValidationError):
        ExperimentGroup(group_id="", runs=[])


def test_experiment_group_round_trip() -> None:
    original = ExperimentGroup(
        group_id="experiment-1",
        runs=[make_run("baseline-1"), make_run("candidate-1")],
    )

    payload = original.model_dump()
    restored = ExperimentGroup.model_validate(payload)

    assert restored.model_dump() == original.model_dump()
