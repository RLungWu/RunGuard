# M0 — Project Foundation

## Status

Active

## Goal

Establish a professional project foundation that is installable, testable, documented, and capable of running one narrow end-to-end workflow.

## User Value

A developer can clone the repository, install RunGuard, run its automated checks, and execute a minimal experiment comparison without understanding the internal implementation.

## Context

RunGuard is intended to become a long-lived ML engineering project rather than a single demonstration script.

Before adding tracking backends or statistical analysis, the project needs development conventions, module boundaries, automated validation, and one complete vertical slice.

M0 is not intended to establish the final architecture. It should create the minimum structure required to develop future milestones safely.

## Scope

### Repository foundation

* `src/` package layout;
* `pyproject.toml`;
* development dependency groups;
* project license;
* initial README and roadmap;
* contribution guidelines;
* changelog.

### Development tooling

* pytest;
* Ruff formatting and linting;
* static type checking;
* pre-commit hooks;
* GitHub Actions;
* coverage reporting if it requires minimal additional configuration.

### Project workflow

* issue templates;
* pull request template;
* Conventional Commit guidelines;
* short-lived feature branches;
* documented local development commands.

### Architecture foundation

* modular monolith as the initial architecture;
* initial package boundaries;
* first Architecture Decision Record;
* no direct dependency on W&B or MLflow.

### Minimal vertical slice

The initial workflow should:

1. load a small local experiment fixture;
2. identify baseline and candidate runs;
3. pair runs by seed;
4. calculate a simple paired metric difference;
5. print a deterministic CLI result.

The implementation may use a deliberately minimal temporary data model. The full canonical model belongs to M1.

## Non-Goals

M0 does not include:

* W&B ingestion;
* MLflow ingestion;
* remote APIs;
* confidence intervals;
* effect-size estimation;
* outlier analysis;
* structured evidence findings;
* YAML policies;
* CI release gates;
* HTML reports;
* web interfaces;
* language model integration;
* production performance optimization;
* final domain-model design.

## Success Criteria

### Installation

The project can be installed in a clean supported Python environment:

```bash
pip install -e ".[dev]"
```

### Automated checks

The following commands pass:

```bash
pytest
ruff check .
mypy src
```

Formatting checks may be executed through Ruff or an equivalent configured command.

### CLI

The following command succeeds:

```bash
runguard --help
```

A minimal comparison command can run against a repository fixture.

Example:

```bash
runguard compare \
  --input tests/fixtures/minimal-comparison.json \
  --baseline baseline \
  --candidate candidate \
  --metric val_f1 \
  --pair-by seed
```

The exact CLI interface may change during M0.

### Continuous integration

GitHub Actions runs installation, linting, type checking, and tests on pull requests and changes to the main branch.

### Documentation

The repository contains:

* README;
* roadmap;
* milestone documentation;
* contribution guide;
* pull request template;
* issue templates;
* at least one ADR.

### Traceability

Every non-trivial M0 change is connected to a GitHub issue and pull request.

## Risks

### Overdesigning the architecture

The project may spend too much time defining abstractions before encountering real experiment data.

Mitigation:

* build one narrow vertical slice;
* defer the complete canonical model to M1;
* record unresolved decisions rather than solving them prematurely.

### Treating tooling as product progress

CI, linting, and templates can create activity without validating user value.

Mitigation:

* require the milestone to include a working comparison flow.

### Creating unstable public APIs too early

The first CLI and internal interfaces may change substantially.

Mitigation:

* mark all APIs as experimental;
* avoid compatibility guarantees before the first stable release.

### Expanding into tracking integration

Connecting W&B may appear more useful than completing the local workflow.

Mitigation:

* explicitly defer remote source adapters to a later milestone.

## Open Questions

* Which Python versions should the first release support?
* Should the CLI use Typer, Click, or the standard library?
* Should domain validation initially use dataclasses, Pydantic, or plain typed classes?
* Should coverage enforcement begin in M0 or after core behavior exists?
* Should the first release be published to PyPI or only tagged on GitHub?
* What is the minimum acceptable local fixture format before M1?

Open questions should be resolved only when they block implementation.

## Planned Issues

Suggested issues:

1. Initialize the Python package structure.
2. Configure development dependencies.
3. Add the CLI entry point.
4. Configure pytest.
5. Configure Ruff.
6. Configure static type checking.
7. Configure pre-commit hooks.
8. Add GitHub Actions.
9. Add issue templates.
10. Add the pull request template.
11. Write ADR-0001 for the modular monolith.
12. Create the minimal local experiment fixture.
13. Implement the minimal paired comparison flow.
14. Add an end-to-end CLI test.
15. Prepare the `v0.0.1` release checklist.

The issue list may be split or consolidated during implementation.

## Release Gate

M0 can be completed when:

* all success criteria pass in CI;
* the minimal workflow works from a clean installation;
* setup instructions have been followed successfully from scratch;
* the milestone's known limitations are documented;
* the changelog contains the `v0.0.1` entry;
* the retrospective has been completed.

## Decisions Made During Implementation

Record implementation decisions here as they occur.

Major architectural decisions should also receive an ADR.

## Retrospective

Complete after the release.

Suggested questions:

* Which assumptions were incorrect?
* Which tooling provided real value?
* Which setup work was unnecessary?
* Did the vertical slice expose missing architecture boundaries?
* What should change before M1 begins?
* Was the milestone small enough to complete without prolonged branches?
