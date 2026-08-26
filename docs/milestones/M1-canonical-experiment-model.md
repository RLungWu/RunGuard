# M1 — Canonical Experiment Model

## Status

Active

## Goal

Define a platform-independent representation for experiment runs, configurations, metrics, and related metadata.

## User Value

Experiment data can be validated and analyzed consistently without coupling the comparison engine to W&B, MLflow, or another tracking SDK.

## Context

M0 uses a minimal local representation to validate the first end-to-end workflow.

That representation is not expected to support real tracking systems or become a stable public interface. M1 will use lessons from the M0 vertical slice to define the first deliberate canonical model.

The milestone should begin only after the M0 retrospective identifies which data structures were required by the comparison workflow.

## Scope

The milestone is expected to explore:

* run identity;
* experiment grouping;
* configuration values;
* metric points and metric series;
* metric step semantics;
* seed representation;
* artifact and source references;
* serialization;
* schema validation;
* local JSON ingestion;
* valid and invalid experiment fixtures.

The M1 model decisions are recorded below; timestamp semantics and public schema versioning are explicitly deferred.

## Non-Goals

M1 is not expected to include:

* statistical comparison;
* confidence intervals;
* release policies;
* remote source APIs;
* W&B-specific behavior;
* MLflow-specific behavior;
* automatic schema migration;
* artifact storage;
* generalized data lineage;
* stable public compatibility guarantees.

## Success Criteria

The milestone will likely require:

* three local input formats converting into the same canonical representation;
* explicit validation errors for malformed input and duplicate run identities;
* deterministic model serialization with normalized metric point ordering;
* preserved metric step ordering;
* no import of tracking-platform SDKs in the domain layer;
* tests for missing values, duplicated steps, and conflicting summary/history values.

## Proposed Model Decisions

| Topic | Decision | Reason | Trade-off |
|---|---|---|---|
| Run identity | `run_id` is required on `Run` and unique within an `ExperimentGroup` | Each run must be traceable, and runs must not be duplicated within one experiment group | Uniqueness requires group-level validation and duplicate records are rejected |
| Experiment grouping | `ExperimentGroup` contains a required `group_id` and a list of `Run` objects | Group-level validation needs a boundary where relationships between runs can be checked | A run can only be checked for duplicate identity within a group, not in isolation |
| Run variant | Preserve an optional `variant` on `Run` | M0 and comparison workflows use labels such as `baseline` and `candidate` | Runs from sources without a variant remain representable but need an explicit analysis eligibility decision |
| Artifact references | Preserve an optional list of `ArtifactReference` objects on `Run` | Analysis results may need to identify the checkpoint or artifact used by a run without storing the artifact itself | References can become stale, and RunGuard does not verify or download the referenced artifact |
| Seed | A run may have no seed, but it cannot participate in paired comparison without one | Some source systems may not record seed information | The model can preserve the run, but comparison must handle it explicitly |
| Metric storage | Store metrics as an ordered list of `MetricPoint` objects, normalized by ascending step | This preserves step information and provides deterministic ordering | Lookup is more verbose than a simple dictionary, and normalization may change input order |
| Missing values | Preserve missing values explicitly | Missingness is part of the original experiment evidence | Downstream analysis must decide whether to reject, warn, or exclude the value |
| Summary vs history | Store summary metrics and metric history separately | Their meanings may differ, so ingestion should not guess which one is authoritative | The model is more complex and requires a later selection policy |
| Duplicate steps | Reject duplicate steps during validation | Silently overwriting a value could lose experiment evidence | Some imperfect source data will be rejected instead of automatically repaired |
| Validation approach | Use Pydantic v2 models for validation and serialization | Reduce manual validation and serialization code, and provide structured validation errors | Adds a runtime dependency and may coerce input values unless strict validation is configured |
| Extra fields | Reject unknown fields in canonical models; preserve source-specific data inside an explicit `source_metadata` field | Prevent typos and unsupported fields from being silently ignored | Backend-specific data must be intentionally placed under `source_metadata` |

## Risks

### Designing from imagined backend requirements

The schema may attempt to support every possible tracking platform before real adapters exist.

### Losing source-specific information

A shared model may discard useful backend metadata.

### Creating an overly permissive schema

Excessive optional fields may move validation problems into later analysis stages.

### Creating an overly strict schema

Requirements based on one project may reject valid experiments from other workflows.

## Resolved and Deferred Questions

Resolved in M1:

* Metric history is stored as ordered `MetricPoint` objects.
* Duplicate metric steps are rejected.
* Summary metrics and metric history are stored separately.
* `RunId` is represented as a validated non-empty string; a dedicated wrapper type is not needed yet.
* Seed is optional; comparison eligibility is decided by a later analysis layer.
* Canonical validation uses Pydantic v2 with strict fields and forbidden unknown fields.
* Backend-specific values are kept in explicit `source_metadata` or `ArtifactReference` fields.

Deferred beyond M1:

* Timestamp semantics and normalization across tracking systems.
* A versioned public snapshot format and automatic schema migration.

## Completed Issues

* Define the canonical model and validation strategy.
* Implement metric, run, experiment group, and artifact reference models.
* Implement the local JSON adapter for three input formats.
* Add valid and invalid fixtures and serialization tests.

## Release Gate

M1 is ready to complete when:

* all success criteria are satisfied;
* `pytest`, `ruff check .`, `mypy src`, and pre-commit checks pass;
* the domain layer imports no tracking-platform SDK;
* known limitations and deferred decisions are documented;
* `CHANGELOG.md` contains the `v0.0.2` entry;
* the retrospective is complete;
* the `v0.0.2` release is tagged after the changes are merged to `main`.

## Decisions Made During Implementation

- Use Pydantic v2 models for validation and serialization.
- Use strict validation for important numeric fields.
- Forbid unknown fields in canonical models.
- Preserve backend-specific data inside an explicit `source_metadata` field.
- Validate `run_id` uniqueness at the `ExperimentGroup` level.
- Preserve comparison-relevant `variant` information on `Run` when a source provides it.
- Store artifact locations and optional digests as references, without managing artifact storage.

## Retrospective

* Pydantic reduced manual validation and serialization code while keeping errors explicit at the source boundary.
* Separating source models from canonical models allowed M0, nested, and canonical JSON formats to converge without coupling the domain layer to a backend.
* Preserving summary metrics separately from history avoids making an ingestion-time decision when the two values disagree.
* Timestamps and public schema versioning were deferred because M1 did not yet have stable cross-backend semantics or a compatibility requirement.
