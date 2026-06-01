# Reading order

This document is a hallway map. Pick the path that matches your need;
each path lists the artifacts in the order they make sense to read.

`README.md` is the front door — it tells you what the repository is.
This document tells you which door to open next.

## Path 1 — Five-minute evaluation

You have five minutes. You want to know whether this repository is worth
a second look.

1. `README.md` — what ships, who it's for, honest scope.
2. `REGISTRY_STATUS.md` — auto-generated aggregate of every voice's
   verdict at the latest commit. Tells you what the registry actually
   says right now.
3. `python power_grid_sim.py` — run the single-file baseline; takes
   under a second. The output you see is the output published in
   `reproducibility_hashes.json`, byte-for-byte.

If those three pass your bar, continue with one of the other paths.

## Path 2 — Thirty-minute review

You want to evaluate the methodology, not just the engineering. You're
the reviewer the project's audit-defense is designed for.

1. `PREREGISTRATION.md` — phase-1 pre-registration. The bounds the
   project pre-committed to before any voice ran.
2. `POST_MORTEM.md` — phase-1 post-mortem. Compares what shipped to
   what `PREREGISTRATION.md` committed to, section by section. Honest
   about deviations.
3. `PREREGISTRATION_PHASE_2.md` — phase-2 pre-registration. Same shape,
   different substrate (monetary-phase substrate).
4. `POST_MORTEM_PHASE_2.md` — phase-2 post-mortem.
5. `examples/voices/` + `phase_2/examples/voices/` — the per-voice
   `predict / kill / run / verdict` units. Each voice has a sidecar
   JSON carrying its actual verdict. Read three or four; the shape
   repeats.
6. `docs/methodology.md` — longer-form theory.

If you want to inspect specifically how the project defends its own
honesty bounds (the `§1` lattice), read the voices whose names start
with `bound_defender_` (phase-1) or `bound_defender_*_in_phase_2`
(phase-2). Each is an inverted-kill voice: pass = bound supported by
direct measurement, fail = bound counter-observation requiring `§1`
flagging.

## Path 3 — Contributor

You want to add a voice. You are not Eir staff. The protocol you need
is documented in two places.

1. `CONTRIBUTING.md` — the contributor protocol and contract.
2. `examples/voices/_voice_template.py` — boilerplate for a new voice
   that satisfies the `§3.1` five-field unit shape.
3. `examples/voices/example_polyphony_voice.py` and
   `examples/voices/example_coupling_voice.py` — worked examples for
   the two `§3.2` axes (polyphony / coupling).
4. `examples/voices/TUTORIAL.md` — first-voice-in-five-minutes
   walkthrough.
5. `tests/test_voice_registry_contract.py` — the mechanical
   conformance test your voice will be checked against in CI.

Run `make check` from the repository root before opening a PR. The
voice-contract test + the full suite must both stay green.

## Path 4 — Cross-project integration

You are building something on top of this repository, or wiring it
into a separate stack.

1. `README.md`'s "Open-core split" section — the line between this
   open repository and the proprietary `eirmath` package.
2. `docs/eirmath_bridge.md` — the public-shape description of where
   `eirmath` plugs into the methodology, and what it does not do. No
   math; interface only.
3. `docs/coltrane_substrate_acknowledgement.md` — honest documentation
   of the agent-orchestration substrate the repository was authored on,
   and the `§13` boundary that keeps the two repositories decoupled
   even when both ship publicly.
4. `phase_2/PREREGISTRATION_PHASE_2.md §3.5` — the cross-phase
   consumption declaration field; a voice that consumes another voice's
   sidecar (cross-lane, cross-phase, or cross-project) declares the
   dependency mechanically.

If you want to integrate at the orchestration layer rather than the
voice layer, `coltrane_substrate_acknowledgement.md` is the document
that tells you where the boundary sits and how it is mechanically
defended.

## Path 5 — Auditor (security + reviewer surface)

You want to verify the project's honesty-bound claims independently.

1. `SECURITY.md` — vulnerability disclosure path.
2. `PREREGISTRATION.md §1` — every named bound the project pre-committed
   not to cross.
3. `examples/voices/bound_defender_*` — the mechanical defenders of
   those bounds. Each carries its own `predict / kill / run / verdict`
   sidecar so the bound's status is computable from disk at any commit
   hash.
4. `REGISTRY_STATUS.md` — the aggregate at the latest commit. The base
   rate of failure (currently around 40 percent across phase-1 and
   phase-2 combined) is the project's audit-defense against
   forking-paths critique per `§3.4`.
5. `POST_MORTEM.md` + `POST_MORTEM_PHASE_2.md` — the project's own
   comparison of what shipped to what was pre-committed.

If a sidecar's verdict in `REGISTRY_STATUS.md` does not match the
verdict you compute from running the voice yourself, please file a
security issue per `SECURITY.md`. The reproducibility hashes in
`reproducibility_hashes.json` plus the per-voice sidecar
`sidecar_sha256_pre_verdict` field together cover end-to-end
tamper-resistance.

## What this document is NOT

- Not a substitute for `README.md`. Read the front door first.
- Not a comprehensive table of contents (see `docs/INDEX.md` if it
  exists, or `ls docs/` directly).
- Not a tutorial. The paths point at artifacts; each artifact carries
  its own walkthrough where needed.

This document is amended when the publication-window structure
materially changes (a new phase opens, an existing artifact is renamed,
or a new reader-archetype is identified).
