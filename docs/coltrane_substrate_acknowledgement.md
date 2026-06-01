# coltrane-oss as the substrate this band ran on

This is honest documentation, not aspiration: the per-voice 5-field
contract documented in `PREREGISTRATION.md §3.1`, the bound-defender
inverted-kill pattern documented across the §1 lattice, and the
multi-witness convergence pattern documented in the post-mortems were
all authored on top of the `coltrane-oss` agent-orchestration substrate.
`coltrane-oss` is in progress separately; this document acknowledges its
role in producing this repository.

The document does not introduce a hard dependency. It records the
substrate the band ran on so that future readers can see the
provenance, and so that the §6 boundary (between this repository's
methodology layer and the `eirmath` commercial layer) generalizes
analogously to a §13 boundary between this repository's methodology
layer and the `coltrane-oss` orchestration layer that runs it.

## Reading order

1. `PREREGISTRATION.md` — the pre-registration this repository
   was authored against.
2. `examples/voices/` — the §3.1 per-voice 5-field units that were
   pre-registered.
3. `REGISTRY_STATUS.md` — the §3.4 audit aggregate at the latest commit.
4. `docs/eirmath_bridge.md` — the §6 boundary between methodology and
   `eirmath`'s commercial layer.
5. This document — the §13 boundary between methodology and
   `coltrane-oss`'s orchestration layer.

## Substrate mapping

The `coltrane-oss` agent-orchestration substrate's primitive types map
to this repository's per-voice 5-field contract as follows. The mapping
is documented from this repository's side; `coltrane-oss` will document
its own end of the mapping when it has a public API surface.

| coltrane-oss primitive | grid-diamondcutter analog |
|---|---|
| `signal` | `RUN_PROTOCOL.input_parameters.public_signal_source` (per voice) |
| `interpretation` | `PREDICTION` (per voice) |
| `judgment` | `KILL_CONDITION` (per voice) |
| `plan` | `RUN_PROTOCOL.entry_point` + steps |
| `artifact` | `*.sidecar.json` (per voice) |
| `verdict` | `VERDICT` field of the sidecar (per voice) |

The mapping is type-shape-isomorphic, not implementation-coupled. A
`coltrane-oss` orchestrator could run the voices in this repository as
agent primitives without modifying the voice contract; equally, a band
could author voices in this repository without `coltrane-oss` at all,
as long as the 5-field shape is honored.

## What this repository inherited from the substrate

This repository's discipline-in-action shape was authored on top of
`coltrane-oss`. Specifically:

- The bound-defender inverted-kill pattern (`§1` lattice 7/7 + phase-2
  additions) was the band's response to a need for mechanical
  honesty-bound enforcement at agent-orchestration scope. The pattern
  proved load-bearing for `coltrane-oss`'s test discipline (T1-T8 type
  layer + P1-P6 pipeline layer) and was carried into this repository's
  `§1` defenses.

- The multi-witness convergence pattern (cross-ant independent voices
  catching each other's blind spots) was the band's operational
  discovery during the overnight authoring window for this repository,
  and pre-figures the kind of orchestration `coltrane-oss` is designed
  to coordinate at agent-team scope.

- The §5 correction protocol (the analyst-error / fetcher unit-bug
  recovery worked through `coltrane-oss`-mediated agent coordination)
  was exercised live during this repository's authoring window.

## What this repository does NOT claim

- This repository does NOT claim that `coltrane-oss` is required to use
  the voice registry contract. The 5-field unit is a standalone
  specification.

- This repository does NOT claim that `coltrane-oss` is the only
  substrate the voices could have been authored on. Any orchestration
  layer that respects the `§3.1` voice contract can run them.

- This repository does NOT claim that the §1 bound lattice is required
  to be defended on `coltrane-oss` specifically. The bound-defenders
  scan source + sidecars; they do not depend on the orchestration layer
  that authored them.

- This repository does NOT claim a `coltrane-oss` release date,
  versioning compatibility, or feature roadmap. `coltrane-oss` will
  document its own state when it has a public API surface.

## §13 — Bound

This repository commits, as `§1` bound row 13, that:

> the project will NOT claim grid-diamondcutter is INDEPENDENT of the
> `coltrane-oss` orchestration substrate it was authored on; the
> acknowledgement above stands; future commits that silently couple
> grid-diamondcutter voice source to `coltrane-oss` internals (without
> declaring the dependency in the voice's `RUN_PROTOCOL`) cross this
> bound.

The bound is defended mechanically by the §1 row 13 defender voice
`bound_defender_13_no_coltrane_silent_commingling_v1` (shipped in the
same PR as this document) using the source-scan inverted-kill pattern
established by `bound_defender_2_adapter_stubs_source_inspection_v1`,
`bound_defender_8_eirmath_not_required_v1`,
`bound_defender_11_no_eirmath_in_phase_2_v1`, and others.

The defender's pass condition: zero voice source files contain
`import coltrane` (any form) AND zero voice source bodies contain an
unguarded `coltrane` token outside docstrings unless guarded by §13
bound text or this document's reference.

## When this document gets revised

This document is amended when one of three things happens:

1. `coltrane-oss` reaches a public API surface and the substrate
   mapping section above can be updated with a runtime-coupling shape
   (declared as a `RUN_PROTOCOL.cross_phase_consumption` entry per phase-2 §3.5).

2. A new bound about the `coltrane-oss` substrate is identified and
   added as a new §1 row + defender voice.

3. The §13 boundary moves (e.g., a previously-coupled component is
   decoupled, or `coltrane-oss` is forked and the upstream becomes a
   different project). The boundary line is updated.

This document does not get revised when:

- A voice's verdict changes (verdicts are voice-level events).
- A new voice lands in `examples/voices/` (the substrate mapping is
  invariant to which voice runs on it).
- `coltrane-oss` makes internal changes that do not affect its public
  API surface or this document's stated mapping.
