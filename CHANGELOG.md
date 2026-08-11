# Changelog

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