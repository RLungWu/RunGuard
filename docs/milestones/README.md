# Milestone Specifications

This directory contains detailed specifications for active and near-term RunGuard milestones.

The project roadmap provides high-level direction. Milestone specifications define the concrete implementation boundary for work that is active or close enough to begin planning.

Future roadmap items should not receive detailed specifications until their assumptions can be evaluated using completed work.

## Relationship to the Roadmap

The project planning layers are:

```text
ROADMAP.md
High-level product direction and milestone sequence

docs/milestones/
Detailed scope and acceptance criteria for active or proposed milestones

GitHub Milestones and Issues
Execution tracking and individual work items

Pull Requests and ADRs
Implementation history and design decisions
```

The roadmap answers:

> Where is the project going?

A milestone specification answers:

> What does completion mean for this milestone?

GitHub issues answer:

> What work remains to be done?

## Milestone Status

Each specification must declare one of the following statuses:

* **Proposed** — an early draft that may change substantially;
* **Draft** — under active planning, with unresolved questions;
* **Active** — implementation has started and the scope is considered stable enough to execute;
* **Completed** — exit criteria have been satisfied;
* **Superseded** — replaced by another milestone or plan.

Changing milestone status should be performed through a pull request.

## Required Sections

Each milestone specification should contain:

* Status
* Goal
* User value
* Context
* Scope
* Non-goals
* Success criteria
* Risks
* Open questions
* Planned issues
* Release gate
* Decisions made during implementation
* Retrospective

Sections may remain empty when the document is first proposed, but they should not be removed.

## Planning Policy

Only the active milestone must have a complete and committed specification.

The next milestone may have a proposed specification to record assumptions and open questions.

Later milestones should remain in `ROADMAP.md` until planning them would produce concrete implementation value.

This policy is intended to prevent speculative architecture and unnecessary commitment to assumptions that have not yet been tested.

## Change Policy

Milestone specifications are expected to evolve.

Changes should be documented through normal pull requests rather than hidden or rewritten after implementation. A changed plan is not considered a failure when the reasons and consequences are recorded.

Substantial scope changes should include:

* the reason for the change;
* the evidence that motivated it;
* affected issues or releases;
* newly introduced risks;
* features that were removed or deferred.

## Completion Policy

A milestone is complete only when:

1. its success criteria are satisfied;
2. required tests and documentation are merged;
3. known limitations are documented;
4. release notes are prepared;
5. the retrospective is completed;
6. the associated release is created, when applicable.

Completing all planned issues is not sufficient if the milestone's user value has not been demonstrated.
