# ADR-0004: Define Comparison Value Semantics and Evidence Requirements

## Status

Accepted

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

Best-checkpoint and final-checkpoint selection are separate policies and will
be introduced only when their semantics and configuration are defined.

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
metric values, the raw difference, and the direction-aware improvement. The
aggregate result must retain the group, variants, metric, direction, and value
source.

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
* Future checkpoint policies will need their own configuration and tests.

## Related Documents

* [M2 — Local Paired Comparison](../milestones/M2-local-paired-comparison.md)
* [ADR-0001: Use a Modular Monolith Architecture](ADR-0001-modular-monolith.md)
