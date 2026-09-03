# Changelog

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
