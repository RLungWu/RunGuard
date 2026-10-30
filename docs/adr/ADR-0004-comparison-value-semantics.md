# ADR-0004: Define Comparison Value Semantics and Evidence Requirements

## Status

Accepted. Amended 2026-10-30 to define history checkpoint selection for
M3 (see [Value selection](#value-selection)).

## Context

RunGuard compares a baseline experiment with a candidate experiment using
canonical `Run` objects. A run can contain both metric history and a scalar
`summary_metrics` value. These values do not necessarily have the same
meaning: a source system may report a summary as the latest value, the best
value, or another source-defined aggregate.

The comparison engine also needs to define what happens when runs cannot be
paired cleanly. Silent value selection, dictionary overwrites, or silently
discarded runs could make an experiment appear more stable than its evidence
supports.

## Decision

RunGuard will separate the storage of metric observations from the policy used
to select a comparison value.

### Comparison value

`summary_metrics` is treated as a source-reported scalar observation. It is not
assumed to represent a best checkpoint or a final checkpoint.

M2 will compare the requested metric from `summary_metrics` only. If the
metric is absent or its value is missing, the comparison fails explicitly.
There is no automatic fallback from summary metrics to metric history.

Best-checkpoint and final-checkpoint selection are separate, explicitly
requested policies defined below. Summary remains the default value source.

### Value selection

Choosing which observation of a run is compared is a separate step that runs
before pairing arithmetic, implemented in the `comparison` module. The caller
selects exactly one value source per comparison:

* `summary` — the source-reported `summary_metrics` value, with no checkpoint
  policy;
* `history` — a value from the run's `MetricSeries` for the metric, with a
  required checkpoint policy of `final` or `best`.

History checkpoint policies are:

* `final` selects the point with the greatest step. If that point's value is
  missing, the run has missing evidence; earlier points are not used instead.
* `best` selects the maximum value for higher-is-better metrics and the minimum
  for lower-is-better metrics, ignoring missing values. Ties select the
  earliest step. A series with no non-missing value is missing evidence.
  Non-finite values cannot be ranked and are rejected.

A run without exactly one series for the metric, or with an empty series, has
missing evidence. Under the strict default, missing evidence for any selected
run fails the comparison and lists the affected run IDs. Missing values are
never replaced by zero, by another checkpoint, or by the summary value.

One comparison applies one value source and policy to every run, so the
source and policy are recorded once on the comparison result. Each pair records
the selected baseline and candidate steps; both steps are absent for summary
comparisons and present for history comparisons.

### Difference and metric direction

The comparison result will preserve the raw difference:

```text
raw_difference = candidate - baseline
```

It will also calculate a direction-aware improvement difference. A positive
improvement means that the candidate is better:

```text
higher-is-better: improvement = candidate - baseline
lower-is-better:  improvement = baseline - candidate
```

Both values are retained so that interpretation does not overwrite the
observed data.

### Pairing and validation

Runs are paired by seed. A comparison fails explicitly when:

* a selected run has no seed;
* the baseline and candidate seed sets do not match;
* a selected run lacks the requested summary metric or has a missing value;
* more than one run has the same variant and seed.

The comparison engine must not silently discard runs or overwrite duplicate
pairing keys. Pair results are ordered by seed for deterministic output.

### Evidence and provenance

Every pair result must retain its seed, baseline and candidate run IDs, both
metric values, the raw difference, and the direction-aware improvement, plus
the selected baseline and candidate steps for history comparisons. The
aggregate result must retain the group, variants, metric, direction, value
source, and checkpoint policy.

## Alternatives Considered

**Always use the final history value.** Rejected for M2 because different
sources may have different step semantics, and some local formats do not
contain history. Defining final-checkpoint behavior is deferred to an explicit
policy.

**Always use the best history value.** Rejected for M2 because it requires a
metric direction and introduces checkpoint-selection behavior that can make
results optimistic. It also belongs to a later policy layer.

**Try summary, then final, then best as fallbacks.** Rejected because the
selection rule would be hidden in the comparison engine and could produce
different meanings for apparently identical inputs.

**Add optional step fields to the summary path without a selection step.**
Rejected for M3 because the selection rule would remain implicit and summary
comparisons would gain fields with no defined meaning. The pair still carries
optional steps, but only a dedicated selection step sets them, and the result
validates that steps match the value source.

**Store a full selected-value object on each side of every pair.** Rejected
because the value source and policy are identical for every pair in one
comparison, and repeating the run ID and value would create two copies that
could disagree.

**Select checkpoints inside the statistics module.** Rejected because the
statistics module consumes paired comparisons and must not re-implement value
selection or pairing.

**Allow incomplete pairs and compare the available runs.** Rejected as the
default because changing the pair denominator silently can turn missing data
into apparent evidence. An explicit incomplete-pair policy may be added later.

**Store only one signed difference.** Rejected because lower-is-better metrics
would make it difficult to distinguish the observed candidate-minus-baseline
value from the interpreted improvement.

## Consequences

Positive:

* Comparison values have an explicit and inspectable source.
* Best and final checkpoint semantics are not inferred from ambiguous source
  data.
* Positive-pair rate has one consistent interpretation for both metric
  directions.
* Invalid or ambiguous pairing is visible instead of being hidden by input
  order or dictionary behavior.
* Results can be traced back to the exact source runs.

Negative:

* M2 may reject data that could be useful for exploratory analysis.
* Users must understand that a source-reported summary is not necessarily a
  best or final checkpoint.
* Structured results contain more fields than a list of numeric differences.
* Each new checkpoint policy needs its own selection rule, provenance, and
  tests.
* The M2 pair and result schemas gained step and policy fields in M3.

## Related Documents

* [M2 — Local Paired Comparison](../milestones/M2-local-paired-comparison.md)
* [M3 — Statistical Evidence Engine](../milestones/M3-statistical-evidence-engine.md)
* [Trade-off register, D1](../architecture/tradeoffs-and-tech-choices.md)
* [ADR-0001: Use a Modular Monolith Architecture](ADR-0001-modular-monolith.md)
