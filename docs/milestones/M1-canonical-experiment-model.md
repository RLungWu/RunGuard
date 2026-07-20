# M1 — Canonical Experiment Model

## Status

Proposed

## Goal

Define a platform-independent representation for experiment runs, configurations, metrics, and related metadata.

## User Value

Experiment data can be validated and analyzed consistently without coupling the comparison engine to W&B, MLflow, or another tracking SDK.

## Context

M0 uses a minimal local representation to validate the first end-to-end workflow.

That representation is not expected to support real tracking systems or become a stable public interface. M1 will use lessons from the M0 vertical slice to define the first deliberate canonical model.

The milestone should begin only after the M0 retrospective identifies which data structures were required by the comparison workflow.

## Preliminary Scope

The milestone is expected to explore:

* run identity;
* experiment grouping;
* configuration values;
* metric points and metric series;
* metric step semantics;
* timestamps;
* seed representation;
* source references;
* serialization;
* schema validation;
* local JSON ingestion;
* valid and invalid experiment fixtures.

The exact types and field requirements remain undecided.

## Preliminary Non-Goals

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

## Preliminary Success Criteria

The milestone will likely require:

* multiple local input formats converting into the same canonical representation;
* explicit validation errors for malformed input;
* deterministic serialization;
* preserved metric step ordering;
* no import of tracking-platform SDKs in the domain layer;
* tests for missing values, duplicated steps, and conflicting metadata.

These criteria should be reviewed after the M0 retrospective.

## Risks

### Designing from imagined backend requirements

The schema may attempt to support every possible tracking platform before real adapters exist.

### Losing source-specific information

A shared model may discard useful backend metadata.

### Creating an overly permissive schema

Excessive optional fields may move validation problems into later analysis stages.

### Creating an overly strict schema

Requirements based on one project may reject valid experiments from other workflows.

## Open Questions

* What information is required for a run to participate in comparison?
* Should metrics be stored as raw points, tabular histories, or both?
* How should duplicated metric steps be handled?
* Should summary metrics be stored separately from metric history?
* How should seed identity be represented?
* Which metadata belongs in the canonical model versus source extensions?
* Should validation use Pydantic, dataclasses, or another approach?
* How should schema versions be represented?
* Should normalized snapshots preserve unknown source fields?

## Planned Issues

Issues should be created after M0 is complete.

Expected planning areas include:

* domain requirements from the M0 workflow;
* canonical model proposal;
* validation strategy;
* serialization format;
* fixture design;
* local adapter contract;
* domain-layer tests.

## Release Gate

To be defined when the milestone becomes Draft or Active.

## Decisions Made During Implementation

Not started.

## Retrospective

Not started.
