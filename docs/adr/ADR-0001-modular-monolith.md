# ADR-0001: Use a Modular Monolith Architecture

## Status

Accepted

## Context

RunGuard needs to support multiple experiment sources (local JSON, W&B,
MLflow), a comparison engine, a finding model, and a policy engine. These
components must evolve independently — a new source adapter should not
require changes to the statistical engine, and a new policy type should not
require changes to ingestion.

At the same time, RunGuard is a single-purpose tool used by one process (a CLI
invocation, or later a CI job). There is no requirement yet for independent
deployment, independent scaling, or separate teams owning separate services.

Two architectural styles were considered for enforcing these boundaries:
splitting the system into separate deployable services now, or keeping a
single deployable unit with enforced internal module boundaries.

## Decision

RunGuard will be built as a modular monolith: one installable Python package
(`src/runguard/`) with strict internal boundaries between modules —
`domain`, `sources`, `comparison`, `findings`, `policies`, and `cli` — but no
network boundary between them.

Module boundaries are enforced through code organization and review, not
through separate processes:

* `domain` defines the canonical model and depends on nothing else in the
  package.
* `sources` converts external data into `domain` objects. `comparison`,
  `findings`, and `policies` never import a source module directly.
* `comparison` and `findings` do not import platform SDKs (W&B, MLflow).
* `cli` is the only module allowed to compose all the others together.

## Alternatives Considered

**Separate services per component (e.g. an ingestion service and an analysis
service).** Rejected for the current stage: there are no independent scaling,
deployment, or ownership requirements that would justify the operational
overhead of network boundaries, serialization, and service discovery. This
would also make local development and testing significantly slower.

**A single undifferentiated script or module.** Rejected because it was tried
implicitly during early exploration and made it unclear which code was
allowed to depend on W&B- or MLflow-specific objects, which is the exact
coupling RunGuard needs to avoid (see the source-independence goal in
[README.md](../../README.md)).

## Consequences

Positive:

* Source adapters can be added or changed without touching the comparison or
  policy engines.
* The comparison and policy engines can be tested and reasoned about without
  any network dependency.
* Local development stays simple: one package, one test suite, one CI
  pipeline.

Negative:

* Nothing prevents an accidental import across a module boundary except code
  review and, later, lint rules; the boundary is a convention, not a hard
  runtime barrier.
* If RunGuard later needs independent scaling or deployment of ingestion
  versus analysis, this decision will need to be revisited.
