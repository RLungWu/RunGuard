# RunGuard

Evidence-based regression testing for machine learning experiments.

RunGuard is a tool for comparing machine learning experiments across multiple runs, seeds, and configurations. It helps teams determine whether a model change represents a real improvement, an unstable result, or a regression that should block release.

RunGuard connects to experiment tracking systems such as Weights & Biases and MLflow, normalizes their run data into a common representation, performs deterministic statistical analysis, and produces findings that are traceable to the original experiment evidence.

The project is currently in early development.

## Problem

Machine learning teams often compare experiments using dashboards, manually inspected curves, and summary metrics. This process creates several recurring problems:

* Improvements may be driven by a single seed.
* Baseline and candidate runs may not be directly comparable.
* Missing runs or incomplete metrics may be silently ignored.
* Model quality may improve while latency, memory usage, or another important metric regresses.
* Experiment conclusions are often difficult to reproduce or audit.
* Natural-language summaries may sound convincing without being supported by sufficient evidence.

Experiment tracking platforms already provide reliable storage, visualization, and run management. RunGuard does not replace those systems. It operates above them by turning experiment data into explicit, testable, and reproducible release decisions.

## Product Definition

RunGuard follows this workflow:

```text
Experiment sources
    ↓
Canonical run normalization
    ↓
Comparability validation
    ↓
Paired multi-run analysis
    ↓
Evidence-backed findings
    ↓
Policy evaluation
    ↓
Pass / Warn / Fail
```

A typical RunGuard report should answer:

1. Are the selected runs comparable?
2. Are baseline and candidate seeds correctly paired?
3. What is the estimated effect size?
4. Is the result stable across seeds?
5. Is the average result dominated by an outlier?
6. Did another quality or system metric regress?
7. What conclusion is supported by the available evidence?
8. What conclusion is not supported?
9. Should the candidate pass the configured release policy?

## Example

```bash
runguard compare \
  --input experiments.json \
  --baseline baseline-v1 \
  --candidate candidate-v2 \
  --metric val_f1 \
  --pair-by seed
```

Example output:

```text
Comparison: baseline-v1 → candidate-v2
Metric: val_f1
Paired runs: 5

Mean paired difference: +0.018
Median paired difference: +0.006
Positive pairs: 3/5
95% bootstrap confidence interval: [-0.004, 0.037]

Finding: Improvement is not seed-stable
Severity: Warning
Evidence strength: Moderate

Supported conclusion:
The candidate may improve val_f1, but the current evidence is insufficient
to claim a consistent improvement.

Unsupported conclusion:
The candidate consistently outperforms the baseline.

Recommended next step:
Run additional paired seeds using the same dataset, code revision, and
evaluation configuration.
```

## Design Principles

### Deterministic findings

Core findings must be produced by deterministic analysis. A language model may later be used to explain structured findings, but it must not create findings, change their severity, or override policy decisions.

### Evidence before interpretation

Every finding must reference the runs, metrics, comparison window, assumptions, and statistical method used to produce it.

### Explicit uncertainty

RunGuard must distinguish between:

* observed evidence;
* supported interpretation;
* alternative explanations;
* missing evidence;
* unsupported claims.

### Fail loudly

Missing seeds, incompatible configurations, malformed metrics, and incomplete data must not be silently ignored.

### Backend independence

The analysis engine must not depend directly on W&B, MLflow, or another tracking SDK. Each source must convert its data into a shared canonical domain model.

### Narrow scope before broad features

The first stable version focuses on paired multi-seed experiment comparison and regression policies. General root-cause diagnosis, hyperparameter optimization, and conversational agents are outside the initial scope.

## Initial Scope

The first development cycle includes:

* a canonical experiment schema;
* local JSON experiment ingestion;
* paired baseline and candidate comparison;
* seed-aware aggregation;
* effect size and uncertainty estimation;
* outlier influence checks;
* metric regression detection;
* structured findings;
* evidence provenance;
* YAML-based release policies;
* CLI support;
* GitHub Actions integration;
* W&B and MLflow adapters.

## Non-Goals

RunGuard is not intended to:

* replace W&B, MLflow, or another experiment tracker;
* store model checkpoints or artifacts;
* provide a full experiment dashboard;
* automatically optimize hyperparameters;
* claim causal root causes from observational experiment data;
* diagnose every possible training failure;
* execute training jobs;
* replace expert review;
* allow a language model to make unverified release decisions.

## Architecture

The intended architecture is a modular monolith:

```text
Sources
├── Local JSON
├── Weights & Biases
└── MLflow

        ↓

Canonical Domain Model
├── Run
├── RunConfig
├── MetricSeries
├── ArtifactReference
└── ExperimentGroup

        ↓

Comparison Engine
├── Comparability checks
├── Seed pairing
├── Effect size
├── Confidence intervals
├── Influence analysis
└── Metric conflict detection

        ↓

Finding Model
├── Claim
├── Status
├── Severity
├── Evidence
├── Assumptions
├── Alternative hypotheses
├── Missing evidence
└── Provenance

        ↓

Policy Engine
├── Pass
├── Warn
└── Fail

        ↓

Interfaces
├── Python API
├── CLI
├── HTML or Markdown report
└── CI integration
```

## Repository Structure

```text
runguard/
├── src/runguard/
│   ├── domain/
│   ├── sources/
│   ├── comparison/
│   ├── findings/
│   ├── policies/
│   └── cli/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── golden/
├── examples/
├── benchmarks/
├── docs/
│   ├── architecture/
│   ├── adr/
│   └── development/
├── pyproject.toml
├── README.md
├── ROADMAP.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE
```

## Development Standards

The project will use:

* Python type annotations;
* automated formatting and linting;
* static type checking;
* unit, integration, and golden tests;
* continuous integration;
* Conventional Commits;
* issue-based development;
* pull requests for all non-trivial changes;
* Architecture Decision Records for important design choices;
* semantic versioning;
* documented release gates.

The `main` branch should remain installable and testable at all times.

## Installation

RunGuard is not yet published. During development:

```bash
git clone https://github.com/<username>/runguard.git
cd runguard
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the checks:

```bash
pytest
ruff check .
mypy src
```

## Project Status

Current milestone: **M3 — Statistical Evidence Engine**

The immediate target is `v0.0.4`, which will include:

* paired bootstrap confidence intervals;
* effect size and positive-seed rate;
* outlier influence and leave-one-pair-out sensitivity analysis;
* best-checkpoint and final-checkpoint policies;
* structured evidence objects.

See [ROADMAP.md](ROADMAP.md) for the complete development plan.

## Contributing

The project is not yet ready for external contributions. Contribution guidelines, development setup, and issue templates will be added during M0.

Design discussions and implementation decisions should be documented through GitHub issues, pull requests, and Architecture Decision Records.

## License

License to be selected before the first public release.
