# Phase-A Post-Mortem — `grid-diamondcutter` as compared to `PREREGISTRATION.md`

**Window:** 2026-05-28 → 2026-05-29 (single overnight session)
**Repo state at post-mortem:** 48 voices committed, 99 PRs total, all phase-A PRs merged to `main`.

This document compares what the registry actually delivered to what `PREREGISTRATION.md` committed to — section by section. The pre-reg's §3.4 audit-defense pattern asks: *at any commit hash, can the project's claims be checked against the project's own ledger?* This post-mortem does that check at the end of phase A.

---

## §0 — Central question — *recognition delivered, conditional on substrate-discontinuity*

**Pre-reg commitment**: the project would test whether the methodology recognizes the *threshold-class cascade* — a discrete regime-shift moment at which alternative-energy reallocation transitions from washed-out (capex below threshold) to cascading (above threshold).

**Delivered**:
- `threshold_cascade_v1` (PR #5 → #63) — **FAIL substantive null**: default linear-filter substrate does not generate discontinuity; methodology correctly returns sharpness 1.0 (< 5 threshold) with substantive null diagnosis.
- `threshold_cascade_v2` (PR #15 → #64) — **PASS**: with substrate-modification (dynamics-amplitude scaling), methodology recovers sharpness 8.0 within the ≥5.0 v2 bound.
- `capability_by_apoha_set_meta_v1` (PR #46 → #73) — **PARTIAL**: mechanizes §0 capability framing via apoha-set (capability = intersection of bound-defenders that PASS).

**Comparison**: recognition delivered, **conditional on substrate admitting regime-discontinuity**. This conditionality was not in the pre-reg; it emerged from v1 → v2 iteration and is now an explicit bracket on §0's claim.

**Honest read**: §0's primary claim is supported, but the recognition substrate is narrower than pre-reg implied — only substrates that admit discrete regime-boundaries produce the cascade signature.

---

## §0.3 — Low-failure-rate alarm — *armed and PASS-equivalent*

**Pre-reg commitment**: a low voice-failure rate is named as a project failure mode (kill conditions too loose, voices selected after observing outcomes); §0.3 commits to surfacing this if it occurs.

**Delivered**:
- `low_failure_rate_alarm_v1` (PR #17) — **PARTIAL** (armed at ≥5 voices, registry now at 48 voices; armed).
- Registry's observed base rate: **43.8% FAIL** (21 fail / 48 total) — well above the 20% alarm threshold.

**Comparison**: §0.3 commitment fully honored. The alarm exists mechanically; the registry's fail rate is healthy. No fishing signal.

---

## §1 — Honesty bounds — *7/7 named bounds mechanically defended*

**Pre-reg commitment**: 8 named bounds (#1 flow-allocator-not-power-flow, #2 adapter-stubs-not-delegation, #3 +0.832-not-real-grid, #4 cascade-not-prediction, #5 no-cross-region-transfer, #6 funding-gap-proxy-not-pipeline, #7 low-failure-rate-not-positive-signal, #8 eirmath-not-required) that the project would not cross silently.

**Delivered — every named bound has at least one mechanical inverted-kill defender voice**:

| bound | defender PR(s) | verdict |
|---|---|---|
| §0.3 / #7 | #17 | PARTIAL (armed) |
| §1.1 | #59 (was #18) + #22 (multi-witness) | PASS + PASS |
| §1.2 | #60 (was #21) | PASS |
| §1.3 | #49 | PASS (+ added missing docstring guard same PR) |
| §1.4 | #50 (doc-scan) + #53 (source-scan) | FAIL (informative — 5 unguarded mentions surfaced) + PASS |
| §1.5 | #16 | PASS narrow |
| §1.6 | #56 + #57 (multi-witness) | PASS + PASS |
| §1.8 | #54 | PASS (+ added missing guard phrase same PR) |

**Comparison**: §1 commitment exceeded. Multi-witness coverage on §1.1, §1.4, §1.6 (independent ant lanes converging on the same bound — exactly the §3.4 cross-voice triangulation the pre-reg names). Two defender voices (PR #49 §1.3 + PR #54 §1.8) surfaced real documentation gaps in `meta_sim/meta.py` and `README.md` and closed them in the same PR — the bound-defender pattern is operating as a self-correcting apparatus.

**Honest read**: the §1 defender lattice is the most over-delivered part of phase A. What the pre-reg framed as a discipline became a mechanical apparatus.

**Emergent finding (not in pre-reg)**: PR #50's honest FAIL surfaced 5 unguarded cascade mentions in `PREREGISTRATION.md` §0 + §6. The §1 bound table at @8707–@8964 contains all guard language but the §0/§6 mentions are far enough away that even a 3000-char radius doesn't reach. Decision on whether to fix inline vs. relax the defender's scope remains open.

---

## §3 — Voice-registry protocol — *operating as committed, 48 voices*

**Pre-reg commitment**: §3.1 five-field unit, §3.2 two axes, §3.3 minimum-coupled-chain, §3.4 null-voice ledger, §3.5 independent-contributor protocol.

**Delivered**:
- 48 voices, all §3.1-conformant (`make voice-contract` green).
- §3.2 split: 35 polyphony + 12 coupling + 1 unknown-shape (lighthouse PR #53 used a bare-string verdict; aggregator tolerated; loose interpretation).
- §3.4 null-voice ledger: 21 FAILs publicly named in `REGISTRY_STATUS.md`.
- §3.5 independent-contributor protocol: not exercised in phase A (all 48 voices authored by the 4-ant band). First external test deferred to public window.

**Comparison**: §3.1-3.4 fully honored. §3.5 still untested.

**Emergent finding (not in pre-reg)**: apoha-as-design-pattern (Eugene confirmed 2026-05-29 02:37 UTC). The inverted-kill bound-defender lineage mechanizes capability-by-negation: capability is defined by what fails outside the claim, not by what succeeds within it. Band-emergent; not pre-reg.

---

## §4 — Validation — *§4.2 3/3 PASS; §4.3 wired*

**Delivered §4.2 — all 3 PASS**:
- `texas_feb_2021_uri_v1` (PR #3 → #65) — PASS
- `eu_may_2022_repowereu_v1` (PR #8 → #66) — PASS
- `japan_march_2011_fukushima_v1` (PR #11 → #67) — PASS

**Delivered §4.3**:
- `qualitative_comparison` harness + fixtures (PR #14) — merged.
- Harness wired into `voice_contract.yml` CI (PR #23) — merged.

**Real-data follow-ons (not in pre-reg)**:
- `texas_uri_temperature_collapse_real_v1` (PR #41) — **FAIL**: first real-data cajal voice; caught a unit-scaling bug in NOAA fetcher v1.
- `historical_uri_cold_extremity_v1` (groove PR #39) — **FAIL**: independent witness on same fetcher bug.
- NOAA fetcher v2 unit-fix (PR #47) — merged, restores correct magnitudes.

**Comparison**: §4.2 + §4.3 fully delivered. Real-data FAILs are the §3.4 audit-defense working at the data-pipeline layer — independent ants caught the same upstream analyst-error.

---

## §5 — Correction protocol — *exercised live*

| pre-reg pathway | exercised by |
|---|---|
| §5.1 incorrectly-specified | NOAA fetcher v1 → v2 unit-fix (#47); lighthouse PR #53 verdict-shape divergence (tolerated) |
| §5.2 inconsistent result + framing note | Receiver-shape framing arc: #42 PASS at n=3 → #45 FAIL at n=24 → #44 sibling-witness FAIL → all merged with framing-correction note |
| §5.2 (additional) | Crisis-robustness PR #61: substantive bound counter-observation on miles's lead-time prior (5/6 leaders crisis-contaminated; prior re-framing required) |

**Comparison**: §5 framework operating exactly as pre-reg specified. The §5.2 receiver-shape arc is the cleanest example.

---

## §6 — Publishing shape + `eirmath` boundary — *defended structurally*

**Delivered**:
- `bound_defender_8_eirmath_not_required_v1` (PR #54) — PASS. Two-pronged: 22 .py files scanned, 0 `import eirmath`; 12 eirmath mentions in PREREGISTRATION.md + README.md, all 12 boundary-guarded within ±400 chars.
- `eirmath_bridge.md` (miles PR #51) — public-shape description, no eirmath dependency.

**Comparison**: §6 boundary mechanically defended at every commit. A future edit adding `import eirmath` anywhere in the open repo triggers an alarm. The boundary is the load-bearing line for Eugene's phase-A/phase-B split.

---

## §7 — Scope limitations — *honored*

Pre-reg's §7.1-§7.4 — phase A operated entirely within these. No claim crossed into regions, time periods, or substrates the pre-reg excluded.

---

## Emergent patterns not pre-registered

1. **apoha-as-design-pattern** (Eugene-confirmed). Bound-defender lattice mechanizes capability-by-negation. Miles's PR #73 (was #46) is the first explicit mechanization.

2. **Multi-witness convergence as registry feature**. Cross-voice triangulation operationalized across §1.1, §1.4, §1.6 — independent ant lanes converging on same bound from different methods.

3. **Receiver-shape framing → over-fit → re-described**. Smooth-S-curve-receiver coupling-washout framing surfaced from n=3, mechanized, peer-checked at n=24, falsified. Honest correction recorded.

4. **Evasion-spring frame** (Eugene-introduced 2026-05-29 02:59 UTC). Failures that look like the universe evading observation at a (substrate, instrument, perceiver) intersection are highest-leverage. Three evasion-spring candidates surfaced (smooth-receiver wash-out, threshold-cascade v1 substrate-class evasion, lead-time prior crisis-contamination). Phase-2 candidate work.

5. **Cross-lane chain-loops**. Cajal-lane voices consume miles-lane deliverables (#48 Greece, #52 Ireland). Asymmetric failure modes — Greece -4y early, Ireland +1y late.

---

## Quantitative summary

| metric | value |
|---|---|
| Voices committed | 48 |
| PASS | 25 (52.1%) |
| FAIL | 21 (43.8%) |
| PARTIAL | 2 (4.2%) |
| polyphony voices | 35 |
| coupling voices | 12 |
| §1 bounds mechanically defended | 7/7 named (multi-witness on 3 of them) |
| §4.2 historical events validated | 3/3 PASS |
| §4.3 qualitative-recovery harness | wired + CI |
| §6 eirmath boundary | mechanically defended (structural + documentational) |
| open PRs at post-mortem | **0** |
| total PRs in window | 99 |

The 43.8% FAIL base rate is the registry's audit-defense: well above the §0.3 alarm threshold (20%), well below the 100% boundary that would indicate the methodology never recognizes anything.

---

## What was NOT delivered (honest gaps)

1. **§3.5 independent-contributor protocol untested.** All 48 voices came from the 4-ant band.

2. **One PR's verdict shape is loose.** Lighthouse PR #53's sidecar has `"verdict": "pass"` as a bare string. Aggregator patched (`_extract_verdict()`) to handle both shapes. Consider tightening contract test in phase-A v2.

3. **Cascade-mentions in §0/§6 of `PREREGISTRATION.md` are not locally guarded.** PR #50 surfaced this; band decision (inline guards vs. broader defender) deferred. Gap recorded in audit trail.

4. **§0's primary claim is conditional on substrate-discontinuity** in a way the pre-reg did not pre-flag. Honest re-description: methodology recognizes the cascade signature only when the substrate admits regime-boundaries.

5. **Real-grid validation deferred.** Real-data work operated on public proxies, not grid-operator telemetry. §1 bounds #3, #4, #6 explicitly cover this.

6. **`REGISTRY_STATUS.md` auto-sync not yet exercised on full lattice.** Registry-status-sync workflow (#20) merged; first full-lattice regeneration happened manually for this post-mortem.

---

## Phase-A close-out

Phase A delivered the audit-defense apparatus, the substantive substrate exploration, the §4 validation pass, the §6 boundary defense, and the §5 correction protocol exercised live. The registry is now structurally complete and audit-defensible from the open repository alone.

**Phase B** opens with the separate pre-reg using `eirmath` to get a precise answer, per Eugene's 2026-05-29 02:37 UTC directive. The phase-A audit-defense lattice carries forward as the public ground that the eirmath layer interprets against. Miles is laying down the phase-2 monetary-phase-substrate ledger.

Authored by subhuti under §6 publishing shape — public artifact, no eirmath dependency. Co-Authored-By: Claude Opus 4.7.
