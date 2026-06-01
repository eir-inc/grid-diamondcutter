# Phase-A Merge Batches — triage artifact for Eugene's review queue

**Status snapshot (commit 4f312ef, 2026-05-29):** 54 PRs open, 2 merged (#1 prereg, #10 ingestion infra). Voice cadence has outpaced merge cadence by ~20×.

**Purpose:** Eugene's phase-A directive (2026-05-29) is *"max out without eirmath, post results via PR/merge, then open up a separate pre-reg that uses eirmath."* The publication shape = the merged registry. Each unmerged PR is a draft from a public-archive perspective. This document groups open PRs into reviewable batches Eugene can merge by class.

**Subhuti chain-keeper recommendation:** merge Wave 1 first (audit-defense baseline), then Wave 2 (infrastructure), then content waves in dependency order.

---

## Wave 1 — §1 bound-defender lattice (audit baseline)

Merge this wave first. Establishes that every §1 honesty bound is mechanically defended in the registry at every commit hash. With this wave merged, reviewers can answer "how do you know X bound holds?" mechanically.

**11 PRs, recommended order:**

| order | PR | bound | verdict | author | notes |
|---|---|---|---|---|---|
| 1 | #17 | §0.3 low-failure-rate alarm | PARTIAL | subhuti | sets self-audit clock; foundation |
| 2 | #16 | §1.5 no-cross-region-transfer | PASS narrow | miles | first inverted-kill voice |
| 3 | #18 | §1.1 flow-allocator-not-power-flow | PASS | miles | mechanical |
| 4 | #21 | §1.2 adapter-stubs-not-delegation | PASS | miles | supersedes #19 |
| — | ~~#19~~ | §1.2 (same target) | PARTIAL | groove | close as duplicate; #21 covers |
| 5 | #22 | §1.1 second witness | PASS | cajal | strengthens #18 |
| 6 | #49 | §1.3 +0.832-coupling-coefficient | PASS | subhuti | also adds docstring guard the voice surfaced |
| 7 | #54 | §1.8 eirmath-not-required | PASS | subhuti | **phase-A load-bearing** |
| 8 | #50 | §1.4 cascade-not-prediction (doc-scan) | FAIL informative | subhuti | reviewer decision: merge as-FAIL (gap on record) or fix inline first |
| 9 | #53 | §1.4 source-scan (second witness) | PASS | lighthouse | complementary angle to #50 |
| 10 | #55 | lead-time-prior crisis robustness | FAIL substantive | miles | bound counter-observation; prior re-framing required |
| 11 | #56 | §1.6 funding-gap-proxy-not-pipeline | PASS | subhuti | **LATTICE CLOSER — 7/7 named §1 bounds covered** |

**After Wave 1 merges:** registry's audit-defense lattice is structurally complete. Multi-witness coverage on §1.1 (#18 + #22) and §1.4 (#50 + #53).

---

## Wave 2 — infrastructure + CI + data ingestion

Enables the rest of the registry to operate cleanly on real data and to publish status automatically.

**6 PRs:**

| order | PR | what | notes |
|---|---|---|---|
| 12 | #14 | qualitative-comparison harness + §4.2 fixtures | enables §4.3 recovery criterion |
| 13 | #20 | registry-status-sync workflow | auto-regen REGISTRY_STATUS.md |
| 14 | #23 | wire harness into voice_contract.yml CI | depends on #14 |
| 15 | #28 → #47 | NOAA fetcher v1 + v2 unit-fix | merge as v2 (closes v1 via supersede) |
| 16 | #51 | eirmath_bridge.md docs | public boundary description |

---

## Wave 3 — §0 central question voices

The methodology's primary claim. Two PRs, sequential (v1 substantive null → v2 PASS).

**2 PRs:**

| order | PR | verdict | notes |
|---|---|---|---|
| 17 | #5 | FAIL substantive null | v1 names the substrate-inertness issue |
| 18 | #15 | PASS | v2 substrate-modification iteration |

---

## Wave 4 — §4.2 historical-events validation set

Three documented historical events validate methodology recovery. Real-data follow-ons surface upstream analyst-errors honestly.

**5 PRs:**

| order | PR | event | verdict | notes |
|---|---|---|---|---|
| 19 | #3 | Texas Feb 2021 Uri | PASS | §4.2 #1/3 |
| 20 | #8 | EU May 2022 REPowerEU | PASS | §4.2 #2/3 |
| 21 | #11 | Japan March 2011 Fukushima | PASS | §4.2 #3/3 (sequence complete) |
| 22 | #41 | Texas real-data FAIL | FAIL | catches #28's scaling bug |
| 23 | #39 | Uri cold extremity | FAIL | analyst-error surfacing |

---

## Wave 5 — lead-time methodology chain (6-voice closed methodology)

Miles's lead-time prior + LOO CV + forward predictions + expanded global cohort. Closed methodology that delivers concrete forward inflection forecasts. Must merge in chain order — later PRs cite earlier.

**7 PRs:**

| order | PR | what | verdict |
|---|---|---|---|
| 24 | #30 | regulatory_lead_time_v1 (~9y prior) | PASS |
| 25 | #33 | leader_cohort_loo_cv_v1 (1.47y MAE validation) | PASS |
| 26 | #31 | follower_country_prediction_v1 (Poland/Romania/Greece) | PASS |
| 27 | #38 | follower_country_prediction_v2 (calibration-honest ±1.47y) | PASS |
| 28 | #40 | regulatory_lead_time_v2_expanded (12-country global) | PASS |
| 29 | #43 | global_follower_prediction_v1 (Mexico/Vietnam/SA/Indonesia) | PASS |
| 30 | #46 | capability_by_apoha_set_meta_v1 (apoha-mechanized) | PARTIAL |

---

## Wave 6 — substantive substrate-claim voices + cross-region coupling + cross-lane chain-loops

The body of the publication: synthetic substrate exploration, cross-region coupling tests (some PASS, more honest-null FAILs), receiver-shape framing arc (proposed → falsified → re-described), and first cross-lane voices.

**22 PRs (grouped, not strictly ordered):**

### Substrate-claim foundational (6 PRs)
- #2 noise_robustness_v1 (substantive null)
- #4 station_set_dependence_v1 (PASS)
- #6 capacity_scaling_monotonicity_v1 (PASS)
- #7 renewable_mix_threshold_polyphony_v1 (PASS)
- #9 mix_axis_smoothness_v1 (FAIL informative)
- #12 finer_fingerprint_resolves_v1 (FAIL informative — 486× improvement)

### Coupling-axis voices (5 PRs)
- #13 capacity_utilization_load_coupling_v1 (FAIL honest null)
- #24 network_amplification_coupling_v1 (substantive null)
- #25 network_amplification_adoption_cascade_v1 (direction recovered, magnitude below floor)
- #26 germany_neighbor_renewable_coupling_v1 (FAIL DE→FR 1y lag)
- #32 japan_post_fukushima_acceleration_v1 (FAIL window)

### Cross-region positive-cascade exploration (3 PRs)
- #35 denmark_germany_renewable_export_coupling_v1 (FAIL over-correlation)
- #36 spain_morocco_renewable_export_coupling_v1 (PASS — first positive coupling)
- #37 receiver_geometry_substrate_class_v1 (FAIL — meta-falsifies #35/#36 generalization)

### Receiver-shape framing arc (3 PRs — read in order)
- #34 regulatory_shape_apoha_v1 (FAIL caught synthetic bias)
- #42 smooth_receiver_coupling_alarm_v1 (PASS at n=3)
- #44 smooth_s_curve_emergent_bound_fresh_pairs_v1 (FAIL — sibling two-witness)
- #45 receiver_shape_distinguishability_v1 (FAIL — peer-check at n=24 falsifies framing)

### Real-data country suitability (2 PRs)
- #27 country_apoha_suitability_v1 (PASS — 9/10 countries)
- #29 country_blocker_diagnostics_v1 (PASS — Iceland single-blocker)

### Cross-lane chain loops (2 PRs)
- #48 cross_lane_chain_loop_greece_v1 (FAIL -4y early)
- #52 cross_lane_chain_loop_ireland_v1 (FAIL +1y late)

Wave-6 voices may be merged in any order; each is self-contained. Recommend grouping by sub-category for review efficiency. Several FAILs are informative + intended for the §3.4 audit trail.

---

## Reviewer notes per Eugene's phase-A directive

1. **FAIL verdicts are not blockers.** §3.4 is explicit: voices that FAIL their kill conditions enter the null-voice ledger and stay on record. The audit-defense benefits from FAILs being merged honestly.

2. **PARTIAL verdicts are not blockers.** Per §3.1, verdicts are `pass | fail | partial`. PARTIAL appears when sample size is below alarm-arming threshold (e.g., #17 #46) or when the voice depends on registry state that isn't yet merged.

3. **Multi-witness coverage is a feature, not duplication.** §3.4 cross-voice triangulation specifically wants independent ant lanes converging on the same bound (§1.1: subhuti #18 + cajal #22; §1.4: subhuti #50 + lighthouse #53). Both merge.

4. **One PR to close:** #19 (groove's bound-defender-2 PARTIAL) is superseded by #21 (subhuti's PASS version with same target). Close #19 with a note.

5. **Merge-batch cadence suggestion:** Wave 1 (11 PRs) in one sitting establishes the audit baseline; Wave 2 (6 PRs) enables infrastructure; the content waves (3-6) can spread across multiple sittings.

---

## What this artifact is NOT

This is a triage recommendation from the subhuti chain-keeper lane. It is not a directive. Other ants may surface bottlenecks Eugene prioritizes differently. Eugene's review reorders this as needed.

The artifact is regenerable: any open-PR snapshot + the §1 lattice rules + the dependency arrows reproduces it. If the open-PR set changes substantially, regenerate.

Authored by subhuti under §6 publishing shape — public artifact, no eirmath dependency.
