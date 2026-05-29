# Where eirmath plugs into this repository's methodology

This document describes the interface between the open methodology in this
repository and the `eirmath` package referenced in `PREREGISTRATION.md` §6.

It is intentionally a description of the **shape** of the interface, not of
the math behind it. The math is kept proprietary; how it is used is public.

The document is amendable as the methodology evolves. Reviewers
encountering an `eirmath` reference in a future commit message or PR body
should consult this document to understand what is being referred to and
where the open / closed line falls.

## Reading order

If you are looking at this repository for the first time:

1. `PREREGISTRATION.md` is the publication-window's pre-registration.
2. `examples/voices/` contains the per-voice predict / kill / run / verdict
   units that test parts of the methodology.
3. `REGISTRY_STATUS.md` (auto-regenerated on CI) aggregates verdicts.
4. This document tells you where `eirmath` would sit if you wanted to
   build a $-calibrated commercial product on top of the methodology.

## The interface

`eirmath` consumes voice sidecars from this repository as input. It does
not import from this repository's substrate models. It does not depend on
this repository's verdict computations. It does not run any of the voice
modules. Its input is the **sidecar JSON shape** that every voice in
`examples/voices/` emits.

The sidecar shape is documented in `PREREGISTRATION.md` §3.1 and is fixed
across the publication window. Each sidecar carries:

- `voice_name`
- `prediction` (kind, named residual, predicted range or bound)
- `kill_condition` (metric, rule, rationale)
- `run_protocol` (entry point, parameters, environment)
- `verdict` (verdict, observed values, rationale, computed_at_utc)
- `sidecar_sha256_pre_verdict` (canonical hash for tamper-resistance)

`eirmath` is a function whose input is one or more such sidecar JSON
objects and whose output is a **$-calibrated commercial output**. The
shape of that output is the subject of the second pre-registration
referenced in the project's publication plan; this document does not
fix the output shape.

## What eirmath uses sidecars for

Three use cases are pre-disclosed:

1. **Temporal anchor → $-calibrated trajectory.** The methodology's
   leader-cohort lead-time prior is a temporal anchor (a year-window).
   `eirmath` converts a temporal anchor for a given country / region into
   a $ deployment trajectory whose magnitude depends on the country's
   capex pipeline, regulatory regime, and capital cost of grid build-out.
   The math behind the conversion is proprietary; the existence of the
   conversion is public.

2. **Voice verdict aggregation → portfolio risk metric.** A bundle of
   voice sidecars covering a candidate country, region, or program is
   converted into a portfolio risk metric for an institutional investor.
   The math behind the aggregation is proprietary; the bundle composition
   rule is public.

3. **Bound-defender ledger → audit-defense report.** The registry's
   bound-defender voices (the `inverted-kill` pattern: pass = bound
   defended by measurement, fail = bound counter-observation requiring
   `§1` flagging) compose into an audit-defense report deliverable to
   institutional reviewers. The math is light; the composition rule is
   public.

## What eirmath does NOT do

`eirmath` does **not** modify any voice's prediction, kill condition,
run protocol, or verdict. It is a consumer of sidecars, not an editor.
Any `eirmath` output that contradicts a voice's verdict is itself a
verdict on `eirmath`'s use of that sidecar, not on the voice.

`eirmath` does **not** introduce new substrate models. It composes
existing-substrate sidecars. New substrates land via new voices in
this repository, under `§3.1` voice-registry contract.

`eirmath` does **not** require any private grid data. It operates on
the public-data fixtures and public-report calibrations the voices
already cite.

## Why the math is kept proprietary

`eirmath` is the commercial layer. Customers pay for the $-calibrated
output. Keeping the math proprietary is the project's funding
mechanism for ongoing methodology work in this repository.

The interface above is intentionally fixed and public so that:

- Reviewers can audit how `eirmath` would use methodology outputs
  without seeing the math.
- Customers can verify the methodology layer independently of the
  commercial layer.
- Future contributors can extend the methodology without coordinating
  with the commercial team.

## When this document gets revised

This document is amended when one of three things happens:

1. The methodology's sidecar shape changes (a `§3.1` revision in
   PREREGISTRATION.md).
2. A new `eirmath` use case is announced. The use case shape is
   added here; the math stays closed.
3. The `eirmath` interface boundary moves (e.g., a previously-proprietary
   component is released open-source). The boundary line is updated.

The document does not get revised when:

- A voice's verdict changes (verdicts are voice-level events).
- A new voice lands (the sidecar shape is invariant to which voice
  emits it).
- A bound is counter-observed (the bound-crossing protocol in
  `PREREGISTRATION.md §1` handles bound revisions).
