# RunGuard Roadmap

This roadmap defines the planned development of RunGuard from repository foundation to the first stable public release.

The roadmap is organized around verifiable product capabilities rather than calendar months. Each milestone must produce a working, demonstrable increment and satisfy explicit release criteria before the next milestone begins.

## Product Goal

RunGuard should enable an ML engineer to compare a candidate experiment against a trusted baseline and receive a reproducible, evidence-backed release decision.

The first stable workflow is:

```text
Load experiment runs
→ Normalize run data
→ Validate comparability
→ Pair baseline and candidate seeds
→ Calculate statistical evidence
→ Generate structured findings
→ Apply release policies
→ Return Pass / Warn / Fail
```

## Development Principles

### Vertical slices first

Each milestone should produce an end-to-end usable capability. Infrastructure should not be built without a concrete workflow that validates it.

### Correctness before feature count

A small number of well-defined findings with strong tests is more valuable than many heuristic detectors with unclear behavior.

### Explicit scope

Every milestone must define its non-goals. Features outside the current milestone should be recorded without being added to the active implementation scope.

### Traceable development

Each significant change should connect:

```text
Milestone
→ Issue
→ Pull request
→ Commits
→ Tests
→ Release notes
```

### Stable main branch

All changes should be developed through short-lived branches and merged through pull requests. The main branch should remain installable and pass all required checks.

---

# M0 — Project Foundation

## User Value

Developers can install the package, run the command-line interface, execute the test suite, and understand the project structure.

## Scope

* Python package structure using `src/`.
* `pyproject.toml`.
* CLI scaffolding.
* Unit test setup.
* Ruff configuration.
* Static type checking.
* Pre-commit hooks.
* GitHub Actions.
* Issue templates.
* Pull request template.
* Conventional Commit guidelines.
* Initial architecture document.
* Initial contribution guide.
* Initial release workflow.

## Non-Goals

* W&B integration.
* MLflow integration.
* Statistical comparison.
* Policy evaluation.
* Web interface.
* Language model integration.

## Success Criteria

The following commands must pass in a clean environment:

```bash
pip install -e ".[dev]"
runguard --help
pytest
ruff check .
mypy src
```

The repository must include:

* a documented project structure;
* automated CI checks;
* at least one example unit test;
* a pull request template;
* an issue template;
* the first Architecture Decision Record.

## Planned ADRs

* ADR-0001: Use a modular monolith.
* ADR-0002: Use a platform-independent canonical domain model.
* ADR-0003: Keep deterministic analysis separate from natural-language explanation.

## Release

`v0.0.1`

---

# M1 — Canonical Experiment Model

## User Value

Experiment data from different sources can be represented consistently and validated before analysis.

## Scope

Define the core domain model:

* `RunId`
* `RunConfig`
* `MetricPoint`
* `MetricSeries`
* `ArtifactReference`
* `Run`
* `ExperimentGroup`

Implement:

* schema validation;
* serialization and deserialization;
* stable metric ordering;
* missing-value handling;
* duplicate-step validation;
* local JSON adapter;
* representative experiment fixtures.

## Non-Goals

* Statistical interpretation.
* Remote API ingestion.
* Run comparison.
* Release policies.
* Automatic schema migration.

## Success Criteria

* At least three different local experiment formats can be converted into the same canonical representation.
* Invalid metrics fail with explicit errors.
* Serialization round-trip tests pass.
* Domain objects do not import W&B or MLflow SDKs.
* Missing required fields are never silently inferred.
* Fixture data covers both valid and invalid inputs.

## Key Risks

* Different tracking systems may use inconsistent metric step semantics.
* Summary metrics may conflict with the final recorded history value.
* Future adapters may require backend-specific metadata.

## Release

`v0.0.2`

---

# M2 — Local Paired Comparison

## User Value

Users can compare a baseline and candidate across paired seeds using local experiment data.

## Scope

* Baseline and candidate selection.
* Pairing by seed.
* Missing-pair detection.
* Mean paired difference.
* Median paired difference.
* Positive-pair rate.
* Configurable metric direction.
* Structured comparison result.
* CLI output.
* Synthetic comparison scenarios.

## Non-Goals

* Confidence intervals.
* Outlier influence analysis.
* W&B ingestion.
* Release policies.
* Causal interpretation.

## Example

```bash
runguard compare \
  --input tests/fixtures/stable_improvement \
  --baseline baseline \
  --candidate candidate \
  --metric val_f1 \
  --pair-by seed
```

## Success Criteria

* Stable improvement scenarios produce the expected result.
* Single-seed improvement scenarios are not labeled as stable.
* Missing pairs produce explicit warnings or errors.
* Metric direction can be configured as higher-is-better or lower-is-better.
* All comparison results identify their source runs.
* Results are deterministic.

## Release

`v0.0.3`

---

# M3 — Statistical Evidence Engine

## User Value

Users can determine whether an observed improvement is stable, uncertain, or dominated by a small number of runs.

## Scope

* Paired bootstrap confidence intervals.
* Effect size.
* Positive-seed rate.
* Outlier influence analysis.
* Leave-one-pair-out sensitivity.
* Mean and median comparison.
* Metric conflict detection.
* Best-checkpoint and final-checkpoint policies.
* Structured evidence objects.
* Reference statistical implementation.

## Non-Goals

* Automatic causal diagnosis.
* Hyperparameter recommendation.
* Data quality diagnosis.
* Language model explanations.
* Experiment scheduling.

## Benchmark Scenarios

* Stable small improvement.
* Stable regression.
* Improvement dominated by one seed.
* Increased variance with unchanged mean.
* Missing paired runs.
* Final checkpoint regression.
* Best checkpoint improvement.
* Primary metric improvement with secondary metric regression.
* Incompatible baseline and candidate configurations.
* Confounded code and configuration changes.

## Success Criteria

* Statistical outputs match a reference implementation within a defined tolerance.
* Every benchmark scenario produces the expected finding.
* Missing runs are included in the report.
* Sensitivity results identify findings dominated by a single pair.
* Findings distinguish evidence from interpretation.
* All calculations are reproducible from stored inputs.

## Release

`v0.0.4`

---

# M4 — Evidence and Finding Model

## User Value

Users receive conclusions that are explicit, reviewable, and traceable to raw experiment evidence.

## Scope

Introduce a structured `Finding` model containing:

* finding type;
* claim;
* status;
* severity;
* evidence strength;
* observations;
* assumptions;
* alternative hypotheses;
* missing evidence;
* supported interpretation;
* unsupported interpretation;
* provenance;
* recommended next experiment.

Implement:

* machine-readable JSON output;
* human-readable Markdown report;
* evidence links to runs and metric ranges;
* golden report tests;
* finding schema versioning.

## Non-Goals

* Free-form language model diagnosis.
* Interactive chat.
* Automatic root-cause attribution.
* Web dashboard.

## Success Criteria

* Every finding contains provenance.
* No finding may be generated without evidence.
* Assumptions and missing evidence are represented explicitly.
* Report output is deterministic.
* Golden reports detect unintended wording or schema changes.
* Finding schema changes require release notes.

## Planned ADRs

* ADR-0004: Findings are deterministic structured objects.
* ADR-0005: Raw metrics are preserved without implicit smoothing.
* ADR-0006: Unsupported claims are represented explicitly.

## Release

`v0.0.5`

---

# M5 — Policy Engine and CI Gate

## User Value

Teams can enforce experiment quality and performance requirements automatically in continuous integration.

## Scope

* YAML policy format.
* Pass, Warn, and Fail decisions.
* Threshold-based policies.
* Seed-stability policies.
* Confidence interval policies.
* Metric regression policies.
* CLI exit codes.
* Markdown CI summary.
* GitHub Actions example.
* Report artifact generation.

## Example Policy

```yaml
primary_metric:
  name: val_f1
  direction: maximize
  minimum_effect: 0.01
  require_positive_pairs: 0.8
  require_ci_above: 0.0

regressions:
  - metric: latency_p95
    direction: minimize
    maximum_relative_regression: 0.10

missing_data:
  action: fail
```

## Non-Goals

* Automatic training execution.
* Deployment orchestration.
* Model registry replacement.
* Organization-wide access control.

## Success Criteria

* Policies produce deterministic exit codes.
* Invalid policies fail before analysis.
* A demonstration pull request can be blocked by seed instability.
* A demonstration pull request can be blocked by a secondary metric regression.
* CI summaries reference the underlying evidence.
* Policy decisions cannot be overridden by report-generation logic.

## Release

`v0.0.6`

---

# M6 — W&B Adapter

## User Value

Users can analyze real W&B projects without manually exporting run data.

## Scope

* W&B source adapter.
* Project and run selection.
* Pagination.
* Metric history ingestion.
* Config ingestion.
* Summary ingestion.
* Missing metric handling.
* API retry behavior.
* Rate-limit handling.
* Local normalized snapshots.
* Mocked integration tests.
* Real project case study.

## Non-Goals

* W&B dashboard replacement.
* W&B artifact storage.
* Sweep execution.
* W&B report generation.

## Success Criteria

* The adapter converts W&B runs into the canonical domain model.
* Analysis results are identical for equivalent local and W&B inputs.
* Network failures produce actionable errors.
* Repeated ingestion avoids unnecessary history downloads where possible.
* A public or reproducible case study demonstrates the complete workflow.

## Planned ADRs

* ADR-0007: Source adapters must satisfy a common conformance contract.
* ADR-0008: Normalized snapshots are used for reproducible analysis.

## Release

`v0.0.7`

---

# M7 — System Metrics and Multi-Objective Regression

## User Value

Users can evaluate model quality together with latency, memory, throughput, and reliability constraints.

## Scope

Support metrics such as:

* inference latency;
* training throughput;
* peak GPU memory;
* samples per second;
* training duration;
* failed-run rate;
* NaN occurrence;
* out-of-memory occurrence.

Implement:

* absolute regression thresholds;
* relative regression thresholds;
* multi-objective policies;
* quality-performance trade-off reporting;
* system metric fixtures;
* one deployment-oriented case study.

## Non-Goals

* Hardware profiling agent.
* TensorRT optimization.
* CUDA kernel analysis.
* Full observability platform.

## Success Criteria

* Candidate models can be rejected despite quality improvement when system regressions exceed policy limits.
* Reports separate model quality from system performance.
* Missing system metrics are handled according to explicit policy.
* At least one case study includes both quality and latency or memory measurements.

## Release

`v0.0.8`

---

# M8 — MLflow Adapter and Backend Conformance

## User Value

Users can run the same analysis workflow across W&B and MLflow.

## Scope

* MLflow source adapter.
* Backend conformance test suite.
* Equivalent-run comparison.
* Backend-specific extension fields.
* Adapter documentation.
* Cross-backend example.

## Non-Goals

* Model registry management.
* Deployment management.
* MLflow server administration.
* Tracking database migration.

## Success Criteria

* Equivalent W&B, MLflow, and local inputs produce equivalent canonical runs.
* Comparison and policy behavior are backend-independent.
* Backend-specific fields do not leak into the comparison engine.
* Adding an adapter does not require changes to the core statistical modules.

## Release

`v0.0.9`

---

# M9 — Production Hardening

## User Value

RunGuard remains reliable when processing larger projects and imperfect real-world experiment data.

## Scope

* Incremental ingestion.
* Caching.
* Idempotent execution.
* Retry strategy.
* Structured logging.
* Performance benchmarks.
* Memory benchmarks.
* Large-run fixtures.
* Failure recovery.
* Documentation improvements.
* Migration policy.
* Security review of configuration and file handling.

## Target Scenarios

* 10,000 runs.
* Large metric histories.
* Partial API failures.
* Duplicate run ingestion.
* Interrupted analysis.
* Schema version mismatch.
* Missing configuration fields.

## Success Criteria

* Repeated analysis avoids unnecessary recomputation.
* Duplicate ingestion does not create duplicate findings.
* Performance and memory benchmarks are published.
* Failure modes are documented.
* Backward-incompatible changes include migration guidance.
* Installation and first-use documentation are validated by an external user.

## Release

`v0.0.10`

---

# M10 — First Stable Release

## User Value

External users can install RunGuard, connect a supported experiment source, configure a policy, and integrate the result into CI.

## Scope

* Stable Python API.
* Stable CLI commands.
* W&B, MLflow, and local adapters.
* Paired multi-seed comparison.
* Statistical evidence.
* Structured findings.
* Model quality and system regression policies.
* GitHub Actions integration.
* Documentation site.
* Example repositories.
* Changelog.
* Migration and deprecation policy.
* External user feedback.
* Public benchmarks.

## Release Criteria

The stable release requires:

* all supported workflows documented;
* test coverage targets satisfied;
* no unresolved critical defects;
* at least two real project case studies;
* at least one external user completing the full workflow;
* published performance benchmarks;
* stable finding and policy schemas;
* installation from a package registry;
* reproducible release automation;
* complete release notes.

## Release

`v0.1.0`

---

# Future Directions

These ideas are intentionally excluded from the first stable release and should only be considered after the core workflow is validated.

* Additional experiment tracking backends.
* Automated regression localization across commits.
* Training phase segmentation.
* Generalization-gap analysis.
* Dataset shift indicators.
* PyTorch Profiler integration.
* ONNX Runtime or TensorRT benchmark ingestion.
* Pull request comments through a GitHub App.
* HTML evidence explorer.
* Language-model-generated explanations of deterministic findings.
* Recommended next experiments based on structured evidence.
* Team-level policy templates.
* Centralized evidence storage.

None of these features should bypass the core requirements of deterministic analysis, explicit uncertainty, and evidence provenance.

---

# Immediate Day 1 Deliverables

The first development day should produce:

* project name and one-sentence definition;
* README;
* roadmap;
* repository structure;
* scope and non-goals;
* initial GitHub milestones;
* initial issue labels;
* first Architecture Decision Record;
* first M0 issues.

Recommended initial issues:

1. Set up Python package structure.
2. Configure Ruff, pytest, and mypy.
3. Add GitHub Actions CI.
4. Add CLI entry point.
5. Add issue and pull request templates.
6. Write ADR-0001 for the modular monolith architecture.
7. Define the initial canonical run schema.
8. Create the first local experiment fixture.
9. Implement one minimal paired comparison flow.
10. Prepare the `v0.0.1` release checklist.

The first milestone is complete only when the repository is installable, testable, and able to execute one narrow end-to-end workflow.
