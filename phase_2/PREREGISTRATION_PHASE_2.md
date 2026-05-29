# Pre-registration — Phase 2 (monetary-phase substrate)

This is the phase-2 pre-registration for the *grid-diamondcutter*
publication program. Phase 1 is the open methodology in this repository's
root surface (`PREREGISTRATION.md`, `examples/voices/`,
`docs/eirmath_bridge.md`, `REGISTRY_STATUS.md`); phase 2 lives under
`phase_2/` as a parallel surface and inherits phase 1's discipline.

This document is committed as a band-collaborative draft seeded by an
analysis contributed during phase 1's close window: that when an
electricity grid is well-managed enough for excess generation to clear
quickly, the unit-of-account of the supply itself begins to behave as
money. Phase 2 pre-registers the question of whether and where that
transition is observable in public market signals, the same way phase 1
pre-registered the threshold-class cascade question for the physical
grid substrate.

## §0 Phase-2 central question

> When does the electricity-grid substrate transition from "money is
> used to buy power" to "well-managed-grid + excess electricity behaves
> as a unit-of-account," and is that transition recognizable in public
> market signals?

This is the phase-2 analog of phase 1's threshold-class cascade question.
The substrate of interest is no longer physical capacity / dispatch /
control / dynamics; it is the supply-clearing behavior of the
electricity market itself, observed at public price and volume
granularity.

The publication-window goal is **recognition** of the transition,
not prediction of any specific market's $-magnitude or timing. Each
phase-2 voice pre-registers a recognition criterion and a kill condition;
the registry composes those into the phase-2 audit-defense.

### §0.1 — Commits the project to publishing

The phase-2 publication shape mirrors phase 1 (§2, below):
1. **Instrument** — `phase_2/` substrate models + voice registry contract.
2. **Pre-registration** — this document, committed at this commit.
3. **Per-voice units** — each `phase_2/examples/voices/*.py` is a §3.1
   five-field unit.
4. **Interpretation** — at the close of the phase-2 publication window,
   a per-voice predicted-vs-observed ledger comparable to phase 1's
   `POST_MORTEM.md`.

### §0.2 — Phase-2 success criteria

- A recognition-criterion voice (analog of `threshold_cascade_v2`) that
  PASSes on a documented public market regime-shift event.
- At least three phase-2 historical-events voices, each calibrated from
  a separate public source, recovering the documented qualitative
  trajectory.
- At least two bound-defender voices defending phase-2-specific honesty
  bounds (the ones added in §1 below).
- The §6 eirmath-boundary remains mechanically defended (the phase-2
  voices do not import `eirmath` and do not silently embed closed math).

### §0.3 — Phase-2 failure criteria

- Voice-level failure rate drops below 25% of total phase-2 voices
  (per phase 1's `low_failure_rate_alarm` discipline).
- No recognition-criterion voice PASSes — the methodology cannot
  recover the §0 transition at the publicly observable granularity.
- A phase-2 voice silently embeds eirmath math (the §6 boundary is
  crossed without documentation).
- A phase-2 voice claims a real-market measurement that crosses any
  inherited or new §1 bound without the §1 bound-crossing protocol's
  flagging-record entry.

### §0.4 — Audience

The phase-2 publication's audience is the same institutional-reviewer
set the phase 1 publication addresses, plus market-microstructure
researchers, energy-economics policy analysts, and the regulatory
audience the IEA Energy Policy Reviews target.

## §1 — Honesty bounds (phase-2 additions; phase 1 inherited)

Phase 2 inherits every §1 bound the phase 1 pre-registration committed
to. Each is mechanically defended on phase 1's `main` (`§1` lattice 7/7,
see phase 1's `REGISTRY_STATUS.md`).

Phase 2 adds the following bounds, each defended by its own
inverted-kill voice (`bound_defender_<n>_*.py`) in `phase_2/examples/voices/`:

| Bound | The project will NOT claim |
|---|---|
| 9 | that the phase-2 substrate is identical to or modeled by physical-grid simulators in the phase 1 surface |
| 10 | that any phase-2 voice's verdict is investment advice in any jurisdiction |
| 11 | that the phase-2 recognition criterion equals or implies the eirmath $-calibration covered by `docs/eirmath_bridge.md` use case 1 |
| 12 | that public spot-price + volume signals exhaustively describe the phase-2 substrate; private OTC, capacity-market, and ancillary-services signals are out of phase-2 scope |

Each new bound's defender is its own voice with inverted kill: PASS =
bound supported by measurement, FAIL = bound counter-observation
requiring a §1 flagging-record entry.

## §2 — Phase-2 publication shape

Mirror of phase 1 §2, scoped to `phase_2/`:

| Commit | Content |
|---|---|
| Commit 1 | `phase_2/instrument/` substrate models + `phase_2/examples/voices/` voice contract |
| Commit 2 | This pre-registration (`phase_2/PREREGISTRATION_PHASE_2.md`) |
| Commit 3+ | Per-voice predict / kill-condition / run / verdict units in `phase_2/examples/voices/` |
| Final commit | Phase-2 interpretation document |

## §3 — Voice-registry protocol (phase-2 additions)

Phase 2 inherits phase 1's §3.1 five-field unit shape and §3.2 two-axis
discipline (polyphony / coupling).

Phase 2 adds §3.5:

### §3.5 — Public-signal source + cross-phase consumption declaration

A phase-2 voice must pre-declare which public price/volume signal it
consumes AND, if the voice also consumes one or more phase-1 voice
sidecars (the `#48/#52` chain-loop pattern formalized for phase 2), it
must pre-declare those upstream sidecars. The declaration is two fields
in the voice's `RUN_PROTOCOL`:

```python
"public_signal_source": {
    "feed_name": "ENTSO-E Transparency Platform day-ahead prices",
    "country_or_region": "Germany",
    "time_window": "2022-01-01 / 2022-12-31",
    "citation_anchor": "ENTSO-E TP API spec + national operator daily reports",
},
"cross_phase_consumption": [
    {
        "consumed_voice_name": "regulatory_lead_time_v1",
        "consumed_sidecar_path": "examples/voices/regulatory_lead_time_v1.sidecar.json",
        "consumed_phase": "phase_1",
        "consumption_kind": "prior_anchor",
    },
],
```

The reproducibility contract from phase 1's `tools/data_ingestion.py`
(frozen-snapshot SHA-256) applies to phase-2 public-signal sources
unchanged. The cross-phase-consumption declaration is required so the
phase-2 registry can audit upstream-dependency chains end-to-end.

### §3.6 — Evasion-class lineage declaration

Per the phase-A → phase-2 bridge voice (`evasion_spring_classifier_meta_v1`),
each phase-2 voice MAY declare which phase-A evasion-class signature its
prediction inherits from, in a `PREDICTION["evasion_class_lineage"]` field.

The five phase-A signatures available for inheritance:

- `substrate_class_evasion` (substrate cannot spontaneously generate predicted phenomenon)
- `substrate_shape_evasion` (receiver geometry/discretization washes out predicted signal)
- `data_availability_evasion` (training data resists yielding required observation conditions)
- `network_magnitude_evasion` (synthetic substrates resist producing strong cross-region effects)
- `cross_lane_prior_generalization_evasion` (a prior valid in one ant's lane fails when consumed by another ant's lane test — the chain-loop pattern documented in `cajal-lane Phase-A post-mortem` (PR #62) as level 6 of the methodology-defense ladder)

Declaring an inheritance is not required, but it lets the phase-2 registry
ratchet against known spring geometries rather than rediscover them.

## §4 — Phase-2 historical-events validation

Three pre-committed phase-2 historical events, each calibrated from a
separate public source corpus. Each voice's verdict is qualitative
recovery (per phase 1 §4.3); $-magnitude is not claimed.

### §4.1 — California 2000-2001 (failed signal)

- Public source: FERC Final Report on California Electricity Crisis (March 2003).
- Pre-committed direction: substrate FAILED to commodify electricity-as-currency.
- Recovery criterion: voice's verdict assigns "transition rejected" to the event window.

### §4.2 — Texas Feb 2021 (transient signal)

- Public source: ERCOT public spot prices Feb 2021 + FERC/NERC report (Nov 2021).
- Pre-committed direction: substrate exhibited transient monetary-phase event;
  no sustained transition.
- Recovery criterion: voice's verdict assigns "transient — substrate did not
  stabilize" to the event window.

### §4.3 — Germany 2022 (recognition-criterion test event)

- Public source: ENTSO-E Transparency Platform day-ahead prices 2022; BMWi 2022 reports.
- Event characterization: the project does NOT pre-assert the substrate
  outcome for Germany 2022. The voice that targets this event pre-registers
  a recognition criterion (e.g., negative-spot-price-hour count threshold,
  step-function spot-price regime-shift detection) and reports whether the
  criterion fires. Pre-asserting the outcome would be a §1-style bound
  crossing per the phase-1 §1.4 cascade-results-not-predictions lineage.
- Recovery criterion: voice's verdict reports recognition criterion +
  fixture-vs-observed comparison; the event characterization in any phase-2
  publication is a downstream synthesis, not a pre-registered claim.

## §4.3 — Qualitative-trajectory recovery criterion

Inherits phase 1 §4.3: binary recover / no-recover per fixture, citation
anchors required, no point-estimate claims. The phase-2 fixtures live in
`phase_2/tools/qualitative_fixtures/`.

## §5 — Deviations and corrections protocol

Inherits phase 1 §5 unchanged.

## §6 — Phase-2 contribution and governance

Inherits phase 1 §6 + `docs/eirmath_bridge.md`. The phase-2 voices are
**not** allowed to import or depend on `eirmath`. The §6 boundary line
remains: the methodology layer in `phase_2/` produces sidecars; eirmath
consumes them per the bridge document's interface.

Phase-2 commits the contribution rule: every phase-2 voice's kill
condition must be pre-committed in the voice file or in this document
before the voice is run.

## §7 — Phase-2 limitations stated up front

Phase 2 inherits phase 1's §7 limitations. Phase-2-specific additions:

- **§7.9 — Public-signal granularity limitation.** Phase 2 operates on
  publicly available price and volume signals. Day-ahead, intraday,
  and balancing-market signals are in scope; OTC bilateral trades,
  capacity auctions, and ancillary services are not.
- **§7.10 — Market-microstructure-not-claim limitation.** Phase 2 does
  not claim to model the microstructure of any specific exchange. The
  substrate is the regime-shift recognition criterion, not the
  market-maker behavior.
- **§7.11 — Currency-status disclaimer.** Phase 2 does NOT claim
  electricity is, or will become, legal tender in any jurisdiction.
  "Electricity-as-money" is a substrate-behavior claim, not a
  legal-status claim.

## Decisions on the open questions (cajal-reviewed band convergence)

The three open questions in the initial scaffold were resolved as
follows after cajal's first-round review (PR #104 comment thread):

### Q1 — Harness inheritance: REUSE phase-1's `tools/qualitative_comparison.py`

The phase-1 harness's fixture-driven recover/no-recover predicate
generalizes to phase-2 historical-events validation. Phase-2 fixtures
live in `phase_2/tools/qualitative_fixtures/` under the same shape.
A phase-2-specific harness extension may be added later if a price-signal
regime-shift detection step is needed that the phase-1 harness cannot
express; not required for the publication window.

### Q2 — §3.7 computational-budget per-voice limit: ADDED (deferred to live-signal voices)

Phase-2 voices that consume live signals (per §4.4 below) must
pre-declare a computational-budget limit in their `RUN_PROTOCOL` to
avoid recomputed-public-data drift between voice runs. Frozen-snapshot
voices inherit the phase-1 SHA-256 contract and do NOT require a budget
field. The §3.7 field shape:

```python
"computational_budget": {
    "max_runtime_seconds_per_run": 60,
    "max_api_calls_per_run": 100,
    "max_signal_sample_count": 10000,
}
```

### Q3 — §4.4 live-observation voice class: ADDED with reproducibility-window field

Phase-2 supports a live-observation voice class for voices consuming
not-yet-frozen recent signals. Each such voice must pre-declare a
reproducibility window in its `RUN_PROTOCOL`:

```python
"live_observation": {
    "reproducibility_window_start_utc": "2026-06-01T00:00:00Z",
    "reproducibility_window_end_utc": "2026-06-30T23:59:59Z",
    "expected_signal_drift_within_window": "low / medium / high",
    "post_window_freeze_path": "phase_2/data_snapshots/<feed>__<window>__v1.json",
}
```

Outside the declared window the voice's verdict is partial (per
phase-1's `capability_by_apoha_set_meta_v1.sidecar.json` partial-shape).
The voice MUST emit a frozen-snapshot of the signals it consumed,
preserving the phase-1 SHA-256 reproducibility contract end-to-end.

## Open questions for next iteration of this document

The Q1-Q3 above are now in scope; the next iteration of this document
should address:

4. Should phase 2 add a §3.8 declaring a per-voice "evasion-spring use"
   field that names which calibration anchor (out of the five phase-A
   evasion classes in §3.6) the voice is ratcheting against, separately
   from the lineage declaration?
5. Should phase-2's §4 historical events list be expanded with a fourth
   event before the publication window opens, to satisfy cajal's
   chain-loop pattern requirement that any phase-A → phase-2 prior
   consumption have at least two independent phase-2 substrates testing
   the same prior?

## Bridge from phase 1

This document does not stand alone. It is the phase 1 pre-registration's
declared next phase, made operational. Readers should consult phase 1's
`PREREGISTRATION.md` for the §3.1 voice-registry contract that phase 2
extends, `docs/eirmath_bridge.md` for the §6 boundary phase 2 preserves,
and `REGISTRY_STATUS.md` for the phase 1 voices whose evasion-class
signatures phase 2 inherits via §3.6.
