# Changelog

## [Unreleased]

## [0.0.4] - 2026-10-30

### Added

- Paired percentile bootstrap confidence interval for the mean direction-aware
  improvement: 95% and 10,000 resamples by default, an explicit recorded
  random seed, the configured confidence level, and seed-ordered resampling.
- Paired Cohen's `d_z` effect size using the `n - 1` sample standard deviation.
- Structured `PairedEvidence` objects with seed-ordered pairs, positive-pair
  evidence, effect size, bootstrap interval, statistic and method parameters,
  and limitations.
- Explicit insufficient-evidence records for fewer than two pairs and for
  zero-variance effect sizes.
- Leave-one-pair-out sensitivity evidence with per-pair source runs, signed
  and absolute mean changes, and the largest-influence seed.
- Signed mean-minus-median improvement in `PairedEvidence`.
- Explicit value selection for comparisons: summary by default, or metric
  history with a `final` or `best` checkpoint policy. Results record the value
  source and policy, and each pair records the selected steps.
- Missing history evidence is reported by reason with the affected run IDs.
- Evidence limitations describe the value source, including that
  best-checkpoint selection can be optimistic.
- Multi-metric evidence combining a primary metric with secondary metrics on
  the same paired runs, with sign-based direction-conflict flags and
  opposing-pair counts, and no severity or release conclusion.
- Descriptive configuration-difference evidence for compared pairs, with no
  compatibility or causal judgment.
- Ten-seed benchmark fixtures and scenario tests for the M3 evidence
  contract, checked against exact and SciPy reference calculations.
- `runguard compare` options `--value-source`, `--checkpoint`,
  `--random-seed`, `--confidence-level`, `--resamples`, and an experimental
  `--format json`.
- Import-boundary tests for the `domain`, `comparison`, and `statistics`
  modules.

### Changed

- `runguard compare` prints statistical evidence after the existing
  comparison summary lines.
- `ComparisonResult.value_source` is now a `ValueSource` enum, and results
  carry `checkpoint_policy`; `ComparisonPair` carries `baseline_step` and
  `candidate_step`. Summary comparisons keep their previous values.
- Bootstrap resample indices are derived from `random()` only, which Python
  keeps stable across versions for a given seed, instead of `random.choices`.
- The package version in `pyproject.toml` now follows the changelog instead of
  declaring `0.1.0`.
- NumPy and SciPy are development-only dependencies used as test references;
  the runtime still depends only on Pydantic.

### Known Limitations

- Only strict pairing is supported; missing seeds or values fail the
  comparison instead of producing partial evidence.
- Percentile bootstrap intervals can be discrete or unstable with about ten
  pairs; median intervals and BCa are not implemented.
- Influence, metric-conflict, and configuration evidence is descriptive; no
  thresholds, outlier labels, compatibility verdicts, or causal claims are
  produced.
- Multi-metric and configuration-difference evidence are available through
  the Python API only.
- The JSON output layout is experimental and not versioned.
- Remote tracking-system adapters, findings, and release policies remain
  future work.

## [0.0.3] - 2026-09-03

### Added

- Canonical local paired comparison by seed for baseline and candidate runs.
- Structured comparison results with mean, median, positive-pair rate, and
  source run provenance.
- Higher-is-better and lower-is-better metric direction support.
- Human-readable CLI output for valid comparisons and explicit invalid-input
  errors.
- Synthetic multi-seed scenarios covering stable, mixed, single-pair,
  lower-is-better, and invalid-pairing cases.

### Known Limitations

- Summary values are source-reported; best- and final-checkpoint selection are
  not implemented.
- Confidence intervals, outlier analysis, incomplete-pair policies, and
  remote tracking-system ingestion remain future work.

## [0.0.2] - 2026-08-26

### Added

- Pydantic-based canonical experiment models.
- Metric point and series validation with deterministic step ordering.
- Canonical run, experiment group, and artifact reference models.
- Local JSON adapters for M0 flat, nested history, and canonical formats.
- Valid and invalid canonical-model fixtures and round-trip tests.

### Known Limitations

- Timestamps and public schema versioning are deferred.
- Remote tracking-system adapters are not included.
- Statistical comparison and release policies remain outside M1.

## [0.0.1] - 2026-08-11

### Added

- Installable `runguard` Python package and CLI entry point.
- Local JSON experiment fixture support for M0.
- Seed-paired baseline and candidate comparison.
- Deterministic mean paired metric difference output.
- pytest, Ruff, mypy, pre-commit hooks, and GitHub Actions CI.
- Unit and end-to-end CLI tests.

### Known Limitations

- Only local JSON fixtures are supported.
- Only scalar metrics and `--pair-by seed` are supported.
- Input validation is intentionally limited and temporary.
- No confidence intervals, outlier analysis, policies, W&B, or MLflow support.
