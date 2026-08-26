# M2 — Local Paired Comparison

## Status

Active

## Goal

Compare a baseline and candidate experiment using canonical local data and
paired seeds, while preserving enough detail to explain how every aggregate
value was produced.

## User Value

An ML engineer can compare two local experiment variants without relying on
input ordering or silently dropping runs. The result reports both aggregate
statistics and the source runs that produced each pair.

## Context

M1 introduced `ExperimentGroup` and the canonical `Run` model. The existing
M0 comparison code still reads the temporary flat JSON shape directly and
returns only a list of numeric differences. M2 moves comparison to the
canonical model and adds an explicit result model.

The canonical model stores summary metrics separately from metric history. A
summary metric is treated as a scalar value reported by the source system. It
is not assumed to represent the best checkpoint or the final checkpoint.
Selecting a best or final checkpoint from history is deferred to a later
checkpoint-selection policy.

## Scope

M2 includes:

* baseline and candidate selection by `variant`;
* pairing by `seed`;
* missing-pair detection;
* comparison of source-reported `summary_metrics`;
* mean paired difference;
* median paired difference;
* positive-pair rate;
* explicit higher-is-better and lower-is-better direction;
* structured comparison and pair results;
* source run IDs in every pair result;
* deterministic ordering;
* human-readable CLI output;
* synthetic scenarios for stable improvement, mixed outcomes, single-seed
  improvement, and invalid pairing.

## Non-Goals

M2 does not include:

* best-checkpoint selection;
* final-checkpoint selection;
* automatic fallback from summary metrics to history;
* confidence intervals;
* outlier influence analysis;
* W&B or other remote ingestion;
* release policies;
* causal interpretation;
* incomplete-pair analysis that silently excludes runs.

## Comparison Decisions

| Topic | M2 decision | Reason |
|---|---|---|
| Input boundary | Comparison accepts an `ExperimentGroup`, not raw JSON | Keeps source ingestion separate from analysis and allows all local formats to converge first |
| Value source | Use `Run.summary_metrics[metric]` only | The source-provided scalar is available for M0 and M1 local formats without inventing checkpoint semantics |
| Summary semantics | Preserve the value as `source-reported summary`; do not call it best or final | A source may define its summary as latest, best, or another aggregate |
| Missing metric/value | Reject the comparison with an explicit error | Avoid changing the denominator or silently producing partial evidence |
| Missing seed | A run without a seed cannot participate in pairing and is reported explicitly | Pairing requires an unambiguous key |
| Missing pair | Reject the comparison and report the unmatched seeds | A paired comparison is invalid when the baseline and candidate seed sets differ |
| Duplicate variant and seed | Reject the comparison and report the conflicting run IDs | Dictionary-style overwriting would make results input-order dependent |
| Raw difference | Preserve `candidate - baseline` | Keeps the observed data unchanged |
| Improvement difference | Derive a direction-aware value where positive means candidate is better | Makes positive-pair rate interpretable for both metric directions |
| Positive pair | Count pairs with `improvement_difference > 0`; ties are not positive | Defines a deterministic and conservative interpretation of improvement |
| Ordering | Sort pair results by seed | Makes serialized results and CLI output deterministic |
| Provenance | Store group ID, variants, seed, both run IDs, both values, and both differences | Every aggregate should be traceable to source runs |

## Result Shape

The implementation should expose a structured result containing:

* metric name and direction;
* value source (`summary`);
* baseline and candidate variant names;
* group ID;
* ordered pair records;
* mean difference;
* median difference;
* positive-pair count and rate;
* any comparison validation details needed by the CLI.

Each pair record should contain:

* seed;
* baseline run ID;
* candidate run ID;
* baseline metric value;
* candidate metric value;
* raw difference;
* direction-aware improvement difference.

## Error Handling

Comparison errors must identify the violated assumption and, when possible,
the affected seeds or run IDs. The implementation must not silently discard
runs, overwrite duplicate keys, or fall back from summary metrics to history.

## Synthetic Scenarios

The fixtures and tests should cover at least:

* stable improvement across all paired seeds;
* mixed positive and negative pairs;
* a single-seed improvement with otherwise no evidence of stable improvement;
* lower-is-better metrics;
* missing candidate seeds;
* missing summary metrics or `None` values;
* duplicate variant and seed records;
* deterministic pair ordering independent of input order.

## Success Criteria

* Canonical local input can be compared without importing a source adapter in
  the comparison module.
* Stable improvement scenarios produce the expected mean, median, and
  positive-pair rate.
* A single positive seed is visible in the pair results and is not described
  as stable improvement by the M2 output.
* Higher-is-better and lower-is-better metrics use the same positive-means-
  improvement interpretation.
* Missing pairs, missing seeds, missing values, and duplicate pairing keys
  produce explicit errors.
* Every pair result identifies both source runs.
* Pair and aggregate results are deterministic.
* `pytest`, `ruff check .`, `mypy src`, and pre-commit checks pass.

## Risks

### Ambiguous source summary semantics

A source-reported summary may mean best, final, or another aggregation. M2
documents this limitation and preserves `value_source=summary`; explicit best
and final policies remain future work.

### Overly strict incomplete-data handling

Rejecting incomplete comparisons may be inconvenient for exploratory work. M2
chooses strict behavior to protect reproducibility. A later explicit policy
may allow incomplete pairs without changing the default behavior.

### Confusing raw and direction-aware differences

Reporting only one signed difference can make lower-is-better metrics hard to
interpret. M2 stores both the raw difference and the direction-aware
improvement difference.

## Open Questions

The following are intentionally deferred:

* How should best-checkpoint selection be configured?
* How should final-checkpoint selection handle missing or non-monotonic steps?
* Should incomplete pairing become an opt-in analysis policy?
* Should a machine-readable JSON CLI format be added alongside human output?

## Planned Issues

* Define comparison result and pair models.
* Implement canonical-model pairing and validation.
* Implement mean, median, and positive-pair aggregation.
* Add synthetic comparison fixtures and tests.
* Update the CLI to load canonical local input and display the structured
  result.

## Release Gate

M2 is ready to complete when:

* all success criteria are satisfied;
* the canonical comparison path is covered by unit and integration tests;
* known limitations and deferred checkpoint decisions are documented;
* `CHANGELOG.md` contains the `v0.0.3` entry;
* the retrospective is complete;
* the `v0.0.3` release is tagged after the changes are merged to `main`.

## Decisions Made During Implementation

To be updated as implementation details are finalized.

## Retrospective

Not started.
