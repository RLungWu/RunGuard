# M3 — Statistical Evidence Engine

## Status

Draft

The statistical direction is agreed and the implementation boundary is being
prepared. The status will become **Active** when the first implementation slice
starts.

## Goal

Extend the deterministic paired comparison from M2 into a reproducible
statistical evidence engine. The engine should quantify uncertainty, effect
magnitude, seed-level consistency, and sensitivity to individual paired runs
without turning those measurements into release conclusions.

## User Value

An ML engineer can inspect whether an observed baseline-versus-candidate
improvement is precise, practically meaningful, consistent across seeds, or
strongly dependent on one paired run. Every reported statistic can be
recomputed from the stored input pairs and the recorded analysis parameters.

## Context

M2 provides a canonical, seed-paired `ComparisonResult` containing raw and
direction-aware differences, mean and median differences, positive-pair rate,
and source run provenance. M3 builds on that result rather than reimplementing
source loading or seed pairing.

M2 deliberately does not interpret one positive pair as stable improvement. M3
adds statistical measurements that make uncertainty and sensitivity explicit,
while leaving claims, severity, and release decisions to later milestones.

The initial benchmark scenarios should use approximately ten paired seeds per
scenario. This gives the reference calculations more realistic sample sizes;
the number of paired seeds is distinct from the number of bootstrap resamples.

## Scope

M3 includes:

* a paired bootstrap confidence interval for mean direction-aware improvement;
* a reference implementation whose results can be checked against hand- or
  independently-calculated expected values;
* paired Cohen's `d_z` effect size;
* positive-seed count and rate, preserving M2's strict positive definition;
* mean-versus-median comparison evidence;
* leave-one-pair-out sensitivity analysis;
* outlier-influence measurements without an automatic causal or policy claim;
* deterministic best-checkpoint and final-checkpoint selection policies for
  metric history;
* multi-metric evidence sufficient to identify direction conflicts between a
  primary and secondary metric;
* structured evidence objects containing calculation parameters,
  observations, provenance, and limitations;
* explicit incomplete-data handling with strict behavior as the default;
* benchmark fixtures covering stable, regressed, noisy, single-seed-driven,
  checkpoint-dependent, conflicting-metric, and incomplete-data scenarios.

The comparison and evidence APIs must continue to accept canonical domain
objects. Statistical modules must not import W&B, MLflow, or other source
adapters.

## Non-goals

M3 does not include:

* Pass, Warn, or Fail release policies;
* natural-language findings or explanations;
* automatic causal diagnosis;
* hyperparameter or next-experiment recommendations;
* experiment scheduling or training execution;
* W&B, MLflow, or other remote ingestion;
* automatic imputation or silent exclusion of missing pairs;
* arbitrary outlier deletion;
* statistical significance claims based only on a p-value;
* deployment orchestration or a web interface.

## Statistical Contract

### Bootstrap confidence interval

The bootstrap unit is one paired `improvement_difference` from M2. Baseline
and candidate values are never resampled independently because that would
destroy the seed pairing.

The initial default contract is:

* statistic: arithmetic mean improvement;
* confidence level: 95%;
* method: percentile bootstrap;
* resamples: 10,000;
* random seed: explicit and stored in the evidence object;
* paired observations: sorted deterministically by seed before analysis.

For fewer than two valid paired observations, the engine reports insufficient
evidence instead of fabricating a confidence interval. It must not silently
replace a missing value or change the denominator.

### Effect size

Effect size is paired Cohen's `d_z`:

```text
mean(improvement_difference)
--------------------------------
sample standard deviation(improvement_difference)
```

The sample standard deviation uses `n - 1`. Effect-size labels such as small,
medium, or large are outside M3. Fewer than two valid pairs produce explicit
insufficient evidence because the sample standard deviation is undefined.

### Positive-seed rate

An observation is positive only when:

```text
improvement_difference > 0
```

Ties are not positive. The rate is the positive-pair count divided by the
number of valid paired observations. M3 reports the point estimate; a separate
confidence interval for the rate is not required for the first slice.

### Sensitivity and influence

For every paired seed, the engine computes the mean improvement after removing
that pair. The evidence must identify:

* the removed seed and both source run IDs;
* the full-sample mean;
* the leave-one-out mean;
* the absolute and signed change;
* the pair with the largest absolute influence.

M3 reports influence measurements but does not label a pair as an outlier or
declare that a result is dominated by one seed. Such interpretation belongs to
a later finding or policy layer.

### Checkpoint policies

For history-backed analysis:

* `final` selects the point with the greatest step;
* `best` selects the maximum for higher-is-better metrics and the minimum for
  lower-is-better metrics;
* ties select the earliest step;
* missing values are never treated as zero;
* a final point with a missing value is reported as missing evidence;
* a best policy with no valid value is reported as missing evidence.

The selected value, policy, and step must be preserved in the evidence
provenance. Summary metrics remain source-reported values and are not silently
replaced by checkpoint-derived values.

### Incomplete pairing

The default pairing policy is strict. A missing baseline or candidate seed
rejects the statistical comparison and reports the exact missing seeds.

An explicit future analysis mode may preserve available pairs while recording
the incomplete denominator and missing runs. No mode may silently discard
unpaired runs.

### Evidence versus interpretation

The M3 result describes observations and calculation metadata, for example:

```text
mean improvement: 0.018
95% bootstrap CI: [-0.004, 0.037]
positive seeds: 7/10
effect size: 0.42
largest leave-one-out change: -0.016 at seed 3
```

It must not convert those values into claims such as stable improvement,
regression, or release approval.

## Evidence Object Requirements

Every structured evidence object must retain enough information to reproduce
its calculations, including:

* experiment group ID;
* baseline and candidate variants;
* metric name and direction;
* value source and checkpoint policy, when applicable;
* ordered paired observations and source run IDs;
* sample size and missing-data details;
* statistic and effect-size definitions;
* bootstrap method, confidence level, resample count, and random seed;
* confidence interval bounds, when available;
* positive-pair count and rate;
* leave-one-out sensitivity results;
* assumptions, limitations, and insufficient-evidence reasons.

## Benchmark Scenarios

Fixtures and tests should cover at least:

* stable small improvement across approximately ten paired seeds;
* stable regression;
* improvement dominated by one seed;
* increased variance with approximately unchanged mean;
* missing paired runs under strict mode;
* final-checkpoint regression;
* best-checkpoint improvement;
* primary metric improvement with secondary metric regression;
* incompatible baseline and candidate configurations as explicit comparison
  evidence or validation errors;
* confounded code and configuration changes without an automatic causal claim.

Each scenario must state the expected evidence, not only an expected final
label.

## Success Criteria

* Bootstrap outputs match a reference implementation within a documented
  floating-point tolerance.
* The same input, method parameters, and random seed produce identical
  statistical output.
* Every benchmark scenario produces the expected evidence fields.
* Approximately ten paired seeds are used in the primary benchmark scenarios.
* Fewer than two valid pairs produce explicit insufficient evidence for CI and
  effect size rather than misleading numeric output.
* Leave-one-pair-out results identify the pair with the largest measured
  influence.
* Mean, median, effect size, and positive-seed rate preserve metric direction
  semantics.
* Missing runs, missing values, and incompatible pairing assumptions are
  visible and are never silently discarded.
* Checkpoint-derived values identify their selected policy and step.
* Evidence objects identify source runs and all parameters needed for
  reproduction.
* Evidence output does not contain release conclusions or unsupported causal
  interpretations.
* The canonical comparison path remains independent of source adapters.
* `pytest`, `ruff check .`, `mypy src`, and pre-commit checks pass.

## Risks

### Small paired sample sizes

Ten paired seeds are a useful benchmark target but do not make an estimate
automatically reliable. The evidence object must retain the sample size and
limitations so later interpretation can account for it.

### Bootstrap instability

With few pairs, bootstrap intervals can be discrete or unstable. M3 uses a
simple percentile reference implementation first and records its parameters;
more advanced intervals remain a later decision if evidence demonstrates a
need.

### Arbitrary outlier thresholds

An automatic outlier label could turn a descriptive sensitivity measurement
into an unsupported conclusion. M3 therefore reports influence magnitudes and
leaves thresholds to a later policy layer.

### Checkpoint semantic drift

Best and final values can differ from source-reported summaries. The selected
step and policy must be recorded, and summary values must remain distinct from
history-derived values.

### Configuration comparability

Determining whether a configuration difference is intended treatment or an
incompatible comparison requires an explicit policy. M3 should expose the
observed differences and avoid claiming causality.

## Open Questions

The following questions do not block the first statistical slice but must be
resolved before the related features are considered complete:

* Should the incomplete-pair reporting mode be implemented in M3, or remain a
  later explicit analysis policy while strict mode is the only supported mode?
* What exact configuration fields are allowed to differ between baseline and
  candidate before a comparison is considered incompatible?
* Should multi-metric conflict detection be exposed in the CLI during M3, or
  remain an analysis API capability until M4's finding and report model?
* Should median confidence intervals be added after the mean-based reference
  implementation is validated?
* Is percentile bootstrap sufficient for the first release, or is BCa required
  by a concrete benchmark or user scenario?

## Planned Issues

* Define statistical evidence and bootstrap parameter models.
* Implement and test the deterministic percentile bootstrap reference path.
* Implement paired effect size and positive-seed evidence.
* Implement mean-versus-median and leave-one-pair-out sensitivity evidence.
* Implement best/final checkpoint selectors with provenance.
* Add multi-metric conflict evidence without producing conclusions.
* Add approximately ten-seed benchmark fixtures and reference expectations.
* Extend the CLI with evidence-only output after the domain API is stable.
* Update README, changelog, and release notes for `v0.0.4`.

## Release Gate

M3 is ready to complete when:

* all success criteria are satisfied;
* statistical outputs are checked against a reference implementation;
* benchmark scenarios demonstrate uncertainty and sensitivity behavior;
* evidence objects preserve source provenance and calculation parameters;
* known limitations and unresolved policy decisions are documented;
* the CLI exposes evidence without converting it into release conclusions;
* `CHANGELOG.md` contains the `v0.0.4` entry;
* the retrospective is complete;
* the `v0.0.4` release is tagged after the changes are merged to `main`.

## Decisions Made During Implementation

The following decisions were agreed during M3 planning:

* M3 outputs evidence only. It does not output release conclusions, severity,
  or Pass/Warn/Fail decisions.
* The primary bootstrap contract is a 95% percentile interval for mean
  direction-aware paired improvement, using 10,000 resamples and an explicit
  recorded random seed.
* Bootstrap resamples paired improvement observations rather than independently
  resampling baseline and candidate values.
* Primary benchmark scenarios target approximately ten paired seeds.
* Paired Cohen's `d_z` is the effect-size definition, using sample standard
  deviation.
* Positive pairs require a strictly positive direction-aware improvement;
  ties are not positive.
* Leave-one-pair-out analysis reports influence measurements without an
  automatic outlier or dominance conclusion.
* Final and best checkpoint policies are explicit, deterministic, and preserve
  the selected step in provenance.
* Strict incomplete-pair handling is the default. Missing runs must never be
  silently dropped.
* Evidence objects must contain source provenance, statistical parameters,
  assumptions, and limitations sufficient for reproduction.

## Retrospective

To be completed after implementation. It should record which statistical
assumptions survived reference testing, which benchmark scenarios exposed
limitations, and which policy or interpretation questions were deferred to M4
or M5.
