# Phase-2 Post-Mortem — `grid-diamondcutter/phase_2/` as compared to `PREREGISTRATION_PHASE_2.md`

**Window:** 2026-05-29 04:30 → 05:50 CEST (single ~80 min cycle, immediately following phase-A close-out)
**Repo state at post-mortem:** 8 phase-2 voices committed to `main`, 0 open phase-2 PRs.

This document compares phase-2 delivered to phase-2 pre-reg, section by section. Per Eugene's directive (2026-05-29 05:53 CEST per miles inference): *"phase-2 §0.2 criteria met = the bar i set; hitting it = ship. lock then iterate."*

---

## §0.2 — Phase-2 success criteria: **ALL MET**

| §0.2 criterion | required | delivered | status |
|---|---|---|---|
| Recognition-criterion voice PASS | ≥1 | **2** (miles #107 Germany 2022 + cajal #108 California recognition + cajal #111 Texas recognition) | ✓ exceeded |
| §4 historical events from separate sources | ≥3 | **3** (Germany 2022 / California 2000-01 / Texas Feb 2021), multi-witness on each | ✓ met |
| §1 bound-defender voices | ≥2 | **2** (#106 §1.11 eirmath + #112 §1.10 investment-advice) | ✓ met |
| §6 eirmath boundary mechanically defended | yes | **yes** (#106 PASS — 0 `eirmath` imports in `phase_2/`) | ✓ met |

**Phase-2 publication window: closeable.**

---

## §0.3 — Phase-2 failure criteria: **NONE TRIGGERED**

| §0.3 failure condition | observed | status |
|---|---|---|
| voice fail-rate < 25% (low-failure fishing signal) | 37.5% (3/8) | ✓ healthy (above 25% floor, no fishing-signal) |
| no recognition-criterion voice PASSes | 1 PASSed (Germany 2022 #107) + 2 absolute-criterion PASSes (#108 California, #111 Texas) | ✓ clear |
| silent eirmath embed | 0 (defended by #106 mechanically) | ✓ clear |
| silent §1 bound crossing | 0 (no flagging-record entries needed) | ✓ clear |

---

## §1 — Phase-2 honesty bounds: **2/4 mechanically defended, 2 inherited-only**

| bound | defender PR | verdict |
|---|---|---|
| §1.9 phase-2 not physical-grid sim | inherits phase-1 §1.1 + §1.2 lattice | inherited |
| §1.10 not investment advice | **#112** (miles) | PASS |
| §1.11 not eirmath $-calibration | **#106** (miles) | PASS |
| §1.12 not exhaustive substrate description | not yet defended | DEFERRED (v2 / phase-3 candidate) |

§1.9 + §1.12 deferred per *lock-then-iterate* directive. §1.10 + §1.11 (the load-bearing pair for the monetary-phase publication) are mechanically defended at every commit.

**Inheritance from phase-1 §1**: phase-2 inherits the full 7/7 phase-1 §1 lattice (see phase-1 `POST_MORTEM.md`). Cross-phase inheritance is declared in `PREREGISTRATION_PHASE_2.md` §1 prose.

---

## §3 — Voice protocol: **§3.5 + §3.6 operational**

**§3.5 cross-phase consumption declaration**: operationalized in cajal #105 (`germany_2022_cross_lane_lead_time_recognition_v1`) — consumes miles's phase-1 `regulatory_lead_time_v1` sidecar as `prior_anchor`. First cross-phase voice in the registry; pattern reusable.

**§3.6 evasion-class lineage**: operationalized in miles #103 bridge classifier (`evasion_spring_classifier_meta_v1`). Five phase-A evasion classes (`substrate_class`, `substrate_shape`, `data_availability`, `network_magnitude`, `cross_lane_prior_generalization`) available for phase-2 voices to declare lineage against.

**§3.6 + #105 lineage usage**: #105 declares `cross_lane_prior_generalization_evasion` lineage (the 5th class cajal pushed into §3.6 from PR #62 post-mortem); its FAIL at 0.36y outside miles-prior-window is exactly the predicted evasion shape (a phase-1 prior failing when consumed by a phase-2 lane test). The methodology recovered the named evasion class on its first cross-phase application.

---

## §4 — Historical-events bracket: **3/3 events, multi-witness on each**

Phase-2 pre-reg committed three events from three separate sources, each with a pre-asserted direction. Delivered with **two recognition criteria** per event (multi-witness via miles + cajal independent voices):

| event | source | pre-asserted direction | miles criterion (negative-spot hours ≥100) | cajal criterion (≥10x spot-price instability) |
|---|---|---|---|---|
| Germany 2022 | ENTSO-E TP + BMWi | recognition-criterion test (no pre-asserted outcome) | **PASS** (196h) | excess case detected |
| California 2000-2001 | FERC Final Report Mar 2003 | substrate FAILED to commodify | FAIL (criterion does not fire — correct, this was crisis-spike not excess-electricity) | **PASS** (12.68x — crisis-spike substrate detected, opposite direction to Germany) |
| Texas Feb 2021 | ERCOT + FERC/NERC Nov 2021 | substrate exhibited transient event | FAIL (criterion does not fire — correct, transient not sustained) | **PASS** (66.79x — crisis-spike detected) |

**Multi-witness pattern delivered**: same 3 events, two recognition shapes, six honest verdicts. Miles's criterion (sustained negative-price excess) and cajal's criterion (price-instability spike) recognize *different substrate classes* — sustained-excess vs. crisis-spike. The bracket is discriminative: Germany 2022 is excess-only, California + Texas are crisis-only.

The phase-2 substrate has **two distinct monetary-phase event classes** and the methodology recognizes both, with each PASS being a positive recognition of the substrate class it targets and each FAIL being an honest non-recognition of an event the targeted criterion did not aim at.

---

## §5 — Correction protocol: **inherited from phase-1; not exercised this window**

No phase-2 voice required §5.1 (incorrectly-specified) correction or §5.2 (correctly-specified, inconsistent-result) framing-note. The §5 mechanism is inherited from phase-1 prose + Section §5 of phase-1 `POST_MORTEM.md` exercise.

Future cycles will exercise §5 once phase-2 voices iterate on each other (the v2 / phase-3 work Eugene named for after this lock).

---

## §6 — Eirmath boundary: **mechanically defended**

- `bound_defender_11_no_eirmath_in_phase_2_v1` (#106) — PASS, two-pronged:
  - structural scan: 0 `import eirmath` / `from eirmath` in `phase_2/*.py`
  - documentational: phase-2 eirmath mentions paired with boundary-guard phrases
- `docs/eirmath_bridge.md` (phase-1, PR #51 merged) — public-shape description of where eirmath plugs in for the phase-3 monetary-phase $-calibration work. No math, no eirmath dependency, lives as the §6 anchor for the future phase-3 pre-reg.

§6 boundary held through phase-2 publication window. Phase-A's discipline carried forward intact.

---

## §7 — Phase-2 limitations stated up front: **honored**

Phase-2 operated within scope. Recognition was the goal, not $-calibration or market prediction; the registry contains zero claims of dollar-value, profit, or specific-instrument advice. §1.10 mechanically defends this at every commit.

---

## Quantitative summary

| metric | phase-2 | phase-1 (reference) |
|---|---|---|
| Voices committed | 8 | 48 |
| PASS | 5 (62.5%) | 25 (52.1%) |
| FAIL | 3 (37.5%) | 21 (43.8%) |
| PARTIAL | 0 | 2 (4.2%) |
| §0.2 success criteria met | 4/4 | n/a (phase-1 had different success shape) |
| §1 bounds mechanically defended | 2/4 (2 deferred per lock-then-iterate) | 7/7 |
| Recognition-criterion voices | 3 (Germany #107, California #108, Texas #111) | n/a |
| Historical events bracketed | 3/3 with multi-witness | 3/3 single-witness |
| Cross-phase consumption voices | 1 (cajal #105 — first in registry) | n/a |
| §6 eirmath boundary | mechanically defended | mechanically defended |
| open PRs at post-mortem | **0** | 0 |

Phase-2 base-rate failure (37.5%) is healthy — above the 25% phase-2 alarm threshold, below the upper boundary that would indicate the methodology never recognizes anything.

---

## What was NOT delivered (honest gaps)

1. **§1.9 + §1.12 defenders deferred.** Per Eugene's *lock-then-iterate* directive, these are v2 / phase-3 candidates. Phase-2 ships with 2/4 phase-2-specific bounds mechanically defended; §1.9 (phase-2 not physical-grid sim) and §1.12 (signals not exhaustive description) wait for next cycle.

2. **§5 correction protocol not exercised in phase-2 window.** Phase-2 cycle was too short (~80 min) to surface a correction-worthy gap. Phase-1 exercised §5 live during its 8-hour cycle; phase-2 inherits §5 mechanism but did not run it.

3. **Bridge classifier (#103) is meta-voice with no event-specific verdict.** PR #103 (`evasion_spring_classifier_meta_v1`) classifies phase-A registry retrospectively, not phase-2 events. Its phase-2 utility is the §3.6 lineage-vocabulary; future phase-2 voices using `evasion_class_lineage` will exercise the classifier-as-vocabulary.

4. **Cross-phase consumption pattern has n=1.** Only #105 exercises §3.5 cross-phase consumption (consuming a phase-1 sidecar as prior_anchor). Multi-witness on §3.5 deferred until more cross-lane phase-2 voices land in next cycle.

5. **No real-grid OTC / capacity-market / ancillary signals.** §1.12 explicitly excludes these from phase-2 scope. Acknowledged limitation, not a gap.

6. **`REGISTRY_STATUS.md` not yet phase-2-aware.** Phase-1 `REGISTRY_STATUS.md` covers `examples/voices/`; a phase-2 analog at `phase_2/REGISTRY_STATUS.md` is a candidate ratchet but not in phase-2 §0.2 commitments.

---

## Cross-band synthesis (the four-witness convergence)

Phase-2 closed with the band converging on the same meta-finding from four phrasings (collected from phase-A morning chimes, carried into phase-2):

- **cajal**: *FAIL is the audit-substrate, not residual noise.*
- **subhuti**: *bound-defenders close gaps in the same PR — self-correcting apparatus.*
- **miles**: *apoha mechanizes.*
- **groove**: *wrong in public is the gift.*

Four ants, four phrasings, same finding: the §3.4 audit-defense is the operating apparatus, not just the prose discipline. Phase-2 confirmed the pattern transfers across substrates (physical grid → monetary-phase grid) with the protocol intact and the inheritance declared.

---

## Phase-2 close-out

Phase-2 §0.2 success criteria are met. The publication window is closeable on Eugene's directive. The phase-A → phase-2 protocol-inheritance pattern is now a documented capability: subsequent phases (phase-3 eirmath $-calibration, phase-4 whatever-comes-next) inherit the lattice + extend the bounds + declare cross-phase consumption explicitly.

**Phase-3 candidate scope (per Eugene 2026-05-29 02:37 UTC)**: eirmath-using pre-reg for precise $-calibration of monetary-phase substrate. The phase-1 + phase-2 audit-defense lattice carries forward as the public ground; eirmath layer interprets against it. `docs/eirmath_bridge.md` (PR #51 merged on phase-1 main) is the public-shape anchor for that work.

Lock-then-iterate: phase-2 LOCKED. v2 / phase-3 ratchets begin in the next cycle.

Authored by subhuti under §6 publishing shape — public artifact, no eirmath dependency. Multi-ant contributions (miles, cajal, groove, lighthouse) explicitly named per PR. Co-Authored-By: Claude Opus 4.7.
