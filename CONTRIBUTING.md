# Contributing to RunGuard

RunGuard is not yet accepting external contributions. This document defines the
workflow the project follows internally, so that development history stays
consistent and reviewable as the project grows. It will be revisited once the
project is ready for outside contributors.

## Before Writing Code

Every non-trivial change should trace back to a milestone and an issue:

```text
docs/milestones/<milestone>.md
    → GitHub issue
        → feature branch
            → pull request
                → commits
```

If the change does not fit an existing milestone's scope, either it belongs in
a future milestone (record it, don't build it early) or the milestone
specification needs to be updated first.

Only the active milestone (see [docs/milestones/](docs/milestones/)) should be
under implementation at a given time.

## Development Setup

```bash
git clone https://github.com/<username>/runguard.git
cd runguard
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Before committing, all of the following must pass locally:

```bash
pytest
ruff check .
mypy src
```

## Branching

Use short-lived feature branches named after the change, not the milestone:

```text
feat/canonical-run-schema
fix/wandb-pagination
test/missing-metric-fixtures
docs/adr-source-abstraction
```

A branch should be mergeable within one to three days. If it grows larger,
split the issue instead of extending the branch.

## Commit Messages

RunGuard uses [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat(domain): add canonical run schema
fix(wandb): preserve step ordering during ingestion
test(domain): cover missing metric validation
docs(adr): explain source adapter boundary
refactor(comparison): separate pairing from aggregation
perf(ingestion): avoid repeated history downloads
```

Each commit should have a single purpose, be understandable on its own, and
keep the test suite passing. Prefer one commit per explainable change over one
commit per day or one commit per line changed.

Avoid non-descriptive messages such as `update`, `fix bug`, or `wip`.

## Pull Requests

All non-trivial changes go through a pull request, even without external
reviewers — the PR is the permanent record of what changed and why. Fill in
the [pull request template](.github/PULL_REQUEST_TEMPLATE.md) in full,
including design decisions and risks, not just a summary of the diff.

A pull request should reference the issue it closes and, where relevant, the
milestone and ADR it implements.

## Issues

Use the [issue template](.github/ISSUE_TEMPLATE) when opening new work. An
issue should state the problem, its acceptance criteria, its non-goals, and
how it will be tested — not just a title.

## Architecture Decision Records

Record a new ADR under [docs/adr/](docs/adr/) when a decision would be
expensive to reverse or would surprise a future contributor reading the code
without context: choice of persistence format, cross-cutting abstractions,
dependency boundaries, or anything that trades off one desirable property for
another. Day-to-day implementation choices do not need an ADR.

Do not record an ADR for decisions that are easily reversible or purely local
to one module.

## Scope Discipline

Every milestone in [docs/milestones/](docs/milestones/) lists explicit
non-goals. If a change falls under a milestone's non-goals, it does not belong
in that milestone's branches or pull requests, regardless of how small it
seems. Record the idea instead of building it early.

## Main Branch

`main` must remain installable and pass `pytest`, `ruff check .`, and
`mypy src` at all times. Do not merge a pull request that breaks this.
