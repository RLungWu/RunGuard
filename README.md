# RunGuard

Evidence-based regression testing for machine learning experiments.

RunGuard is a tool for comparing machine learning experiments across multiple runs, seeds, and configurations. It helps teams determine whether a model change represents a real improvement, an unstable result, or a regression that should block release.

RunGuard is designed to connect to experiment tracking systems such as Weights & Biases and MLflow, normalize their run data into a common representation, perform deterministic statistical analysis, and produce findings that are traceable to the original experiment evidence.

The project is in early development. It currently reads local JSON experiment files and reports paired statistical evidence; tracking-system adapters, findings, and release policies are planned. See [Project Status](#project-status).

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

When the workflow is complete, a RunGuard report should answer:

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
  --input tests/fixtures/benchmarks/stable-small-improvement.json \
  --baseline baseline \
  --candidate candidate \
  --metric val_f1 \
  --pair-by seed \
  --random-seed 7
```

Output (pair list shortened):

```text
Comparison: baseline → candidate
Metric: val_f1
Value source: summary
Direction: higher-is-better
Paired runs: 10
Mean paired difference: +0.010100
Median paired difference: +0.010000
Positive pairs: 10/10 (100.00%)

Evidence (direction-aware improvement):
Mean improvement: +0.010100
Median improvement: +0.010000
Mean minus median: +0.000100
95% percentile bootstrap interval for the mean: [+0.009000, +0.011400] (10000 resamples, random seed 7)
Effect size (d_z): +4.988 (sample SD 0.002025)
Largest leave-one-pair-out change: -0.000433 at seed 6 (mean without it +0.009667)

Pairs:
- seed 1: baseline-seed-1 → candidate-seed-1: improvement +0.012000
- seed 2: baseline-seed-2 → candidate-seed-2: improvement +0.009000
…
- seed 10: baseline-seed-10 → candidate-seed-10: improvement +0.007000

Limitations:
- Seed pairing does not verify dataset, code revision, or configuration comparability between baseline and candidate runs.
- Percentile bootstrap intervals can be discrete or unstable with few paired observations.
- Leave-one-pair-out changes are descriptive influence measurements; they do not label outliers or establish that one seed dominates the result.
- Summary metrics are source-reported values; no checkpoint selection policy was applied.
```

The output reports evidence only. Findings, severity, and Pass / Warn / Fail
release decisions are planned for later milestones and are not produced yet.

Useful options:

* `--direction lower-is-better` for metrics such as loss or latency.
* `--value-source history --checkpoint {final,best}` to compare a checkpoint
  from metric history instead of the source-reported summary value.
* `--random-seed`, `--confidence-level`, and `--resamples` to set the
  bootstrap parameters; they are always printed with the interval.
* `--format json` for machine-readable evidence. **The JSON layout is
  experimental** and may change until finding schema versioning is
  introduced.

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

The first development cycle, up to the first stable release, includes the
items below; [Project Status](#project-status) lists what is delivered.

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

The intended architecture is a modular monolith ([ADR-0001](docs/adr/ADR-0001-modular-monolith.md)). Items marked *(planned)* are not implemented yet:

```text
Sources
├── Local JSON
├── Weights & Biases (planned)
└── MLflow (planned)

        ↓

Canonical Domain Model
├── Run
├── RunConfig
├── MetricSeries
├── ArtifactReference
└── ExperimentGroup

        ↓

Comparison and Statistical Evidence
├── Seed pairing and summary / checkpoint value selection
├── Configuration differences (descriptive)
├── Effect size
├── Confidence intervals
├── Influence analysis
├── Metric conflict detection
└── Comparability policies (planned)

        ↓

Finding Model (planned)
├── Claim
├── Status
├── Severity
├── Evidence
├── Assumptions
├── Alternative hypotheses
├── Missing evidence
└── Provenance

        ↓

Policy Engine (planned)
├── Pass
├── Warn
└── Fail

        ↓

Interfaces
├── Python API
├── CLI
├── HTML or Markdown report (planned)
└── CI integration (planned)
```

## Repository Structure

```text
runguard/
├── src/runguard/
│   ├── domain/          canonical experiment models
│   ├── sources/         local JSON adapters
│   ├── comparison/      seed pairing, value selection, config differences
│   ├── statistics/      bootstrap, effect size, sensitivity, evidence
│   ├── findings/        (planned, empty)
│   ├── policies/        (planned, empty)
│   └── cli/
├── tests/
│   ├── unit/
│   ├── integration/     CLI and M3 benchmark scenarios
│   └── fixtures/        including fixtures/benchmarks/
├── examples/            (placeholder)
├── benchmarks/          (placeholder)
├── docs/
│   ├── architecture/    trade-off and technical choice register
│   ├── adr/
│   └── milestones/
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
* unit, integration, and benchmark tests (golden report tests are planned);
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
git clone https://github.com/RLungWu/RunGuard.git
cd RunGuard
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the checks:

```bash
pytest
ruff check .
mypy src
pre-commit run --all-files
```

## Project Status

Current milestone: **M3 — Statistical Evidence Engine**

Delivered so far:

* `v0.0.2` — canonical experiment model and local JSON adapters;
* `v0.0.3` — seed-paired comparison with direction-aware differences;
* `v0.0.4` (release candidate) — paired bootstrap confidence intervals,
  paired Cohen's `d_z`, positive-pair rate, mean-versus-median and
  leave-one-pair-out sensitivity, final- and best-checkpoint selection,
  multi-metric conflict and configuration-difference evidence (Python API),
  structured evidence objects, and evidence output from `runguard compare`.

Not yet available: W&B and MLflow adapters, findings, Markdown or HTML reports,
release policies, Pass / Warn / Fail decisions, and CI integration.
Design trade-offs are tracked in the
[trade-off register](docs/architecture/tradeoffs-and-tech-choices.md).

See [ROADMAP.md](ROADMAP.md) for the complete development plan.

## Contributing

The project is not yet ready for external contributions. The internal workflow is described in [CONTRIBUTING.md](CONTRIBUTING.md).

Design discussions and implementation decisions should be documented through GitHub issues, pull requests, and Architecture Decision Records.

## License

RunGuard is released under the [MIT License](LICENSE).
