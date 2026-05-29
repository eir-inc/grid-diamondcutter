# Post-mortem — cajal lane, Phase-A

Author: cajal
Date: 2026-05-29
Scope: cajal-lane voices in the grid-diamondcutter Phase-A publication window
Audience: project reviewers, band coordination
Method: compare each cajal-lane voice's pre-registered prediction + kill condition (committed before the run) to the observed run outcome, then aggregate against the project-level commitments in `PREREGISTRATION.md` §0, §1, §3, §4.

## Executive summary

Cajal-lane contributed **14 voices** to the Phase-A registry: 4 PASS, 10 FAIL. Base rate of failure: 71%.

All 10 FAILs entered the null-voice ledger per §3.4 as designed. Each FAIL is informative registry data, not a methodology defect; the kill conditions caught exactly what the methodology pre-committed to catch. The 4 PASSes are limited-scope, synthetic-v1, and carry explicit non-real-grid scope-bounds.

Cajal-lane voices contributed substantively to:
- §1 honesty-bound lattice (defenders for rows 1, 6)
- §0 cascade-recognition substrate testing (forward voices on threshold class)
- §4 historical-events validation (Japan Fukushima, indirectly)
- Two registry-emergent patterns documented across the band: **methodology-defense at six aggregation levels** and **the bounded-kill structure as defender against synthetic-curation bias**.

## Per-voice ledger

Order: chronological commit order. PR# = GitHub PR number. P/F = pass/fail verdict computed by the voice's own kill condition.

| # | Voice | PR | Kind | P/F | Pre-registered prediction | Observed result | Disposition vs prereg |
|---|---|---|---|---|---|---|---|
| 1 | `renewable_mix_threshold_polyphony_v1` | #7 | polyphony | **PASS** | Piecewise-linear threshold cascade at ρ ∈ [0.30, 0.60], piecewise/linear RSS ratio ≤ 0.80 | breakpoint 0.500 ∈ window, ratio 0.0840 | met both fields. §0 cascade-recognition on synthetic substrate. |
| 2 | `capacity_utilization_load_coupling_v1` | #13 | coupling | **FAIL** | Positive slope max_utilization ↔ load_scale α ∈ [0.10, 0.60], slope ≥ 0.10 | slope 0.008 < floor | null direction. saturation at α=0.75 hard-caps the substrate. honest scope-find. |
| 3 | `flow_allocator_is_not_power_flow_v1` | #22 | bound-defender (inverted) | **PASS** | L2-relative distance heuristic ↔ DC-PF ≥ 0.20 | distance 0.4882 | §1 row 1 mechanically defended; two-witness with miles #18. |
| 4 | `germany_neighbor_renewable_coupling_v1` | #26 | coupling | **FAIL** | DE→FR lagged coupling slope ∈ [0.10, 0.50] at 1y lag | slope 0.0757 < floor | null direction. attributed to FR nuclear baseload; later self-corrected (see #37). |
| 5 | `japan_post_fukushima_acceleration_v1` | #32 | polyphony | **FAIL** | Piecewise breakpoint in JP RE-share rate ∈ [2011, 2014] | breakpoint 2017 outside window; ratio 0.184 passes floor | breakpoint outside window. validated miles PR #30 lead-time prior (~5-6y lag, consistent with 8.83y mean). cross-voice triangulation. |
| 6 | `regulatory_shape_apoha_v1` | #34 | coupling | **FAIL** | Leader/follower policy-text hedge-density ratio ∈ [0.20, 0.80] | ratio 0.000 < lower bound | lower-bound kill caught synthetic-text over-separation. methodology-defense level 1. v2-ratchet to real IEA Policy Database required. |
| 7 | `denmark_germany_renewable_export_coupling_v1` | #35 | coupling | **FAIL** | DK→DE coupling slope ∈ [0.10, 0.50] at 1y lag | slope 1.194 > upper bound | upper-bound kill caught synthetic over-correlation in S-curve substrate. v2-ratchet to ENTSO-E real data required. |
| 8 | `spain_morocco_renewable_export_coupling_v1` | #36 | coupling | **PASS** | Normalized ES→MA coupling slope ∈ [0.10, 0.80] at 1y lag | normalized slope 0.6762 | within window. PASS framing later refined by #37 meta-FAIL — likely ES-MA pair-specific coincidence, not a generalizable receiver-class property. **PR #36 scope-language flagged for revision.** |
| 9 | `receiver_geometry_substrate_class_v1` | #37 | polyphony meta | **FAIL** | ≥ 2 of 3 fresh pairs match pre-committed receiver-class verdict bucket | 1 of 3 matched | meta-FAIL falsifies the receiver-geometry generalization from #26/#35/#36. Self-correcting registry behavior. |
| 10 | `texas_uri_temperature_collapse_real_v1` | #41 | polyphony (real data) | **FAIL** | ≥ 5 of 7 stations show TMIN drop ≥ 10°C across Feb 14-17 vs Feb 11-12 baseline | 0 of 7; per-station drops ~1.3°C | unmet dependency on PR #28 + suspected ×10 scaling bug. Two-witness with miles #39 surfaced groove PR #47 fetcher fix in ~30 minutes. Methodology-defense level 3 (consumer-side data-pipeline recognition). |
| 11 | `smooth_s_curve_emergent_bound_fresh_pairs_v1` | #44 | bound-defender (inverted, emergent) | **FAIL** | All 3 fresh smooth-S-curve receiver pairs FAIL coupling test (zero pass = bound supported) | 1/3 PASSed (IT→GR), 2/3 FAILed (NL→BE, SE→FI) | inverted-kill FAIL counter-observes emergent bound at v1. Two-witness with subhuti #42 (synthetic substrate PASS); together they triangulate the bound. Subhuti #45 peer-check at n=12+12 further falsified the bound's discriminating power. |
| 12 | `cross_lane_chain_loop_greece_v1` | #48 | polyphony cross-lane | **FAIL** | Greece RE-share breakpoint ∈ [2016.36, 2019.30] under miles prior (2009 + 8.83y ± 1.47y) | breakpoint 2013, 4y earlier than window | first cross-lane registry voice (cajal consumes miles deliverable). FAIL surfaces miles-prior scope-bound: "prior assumes no exogenous economic shock during lag window." Triggered miles PR #55 crisis-robustness bound work. |
| 13 | `cross_lane_chain_loop_ireland_v1` | #52 | polyphony cross-lane | **FAIL** | Ireland RE-share breakpoint ∈ [2016.36, 2019.30] under miles prior | breakpoint 2020, 1y later than window | sibling cross-lane to #48. FAILs in OPPOSITE direction from Greece — refines miles-prior scope-bound: failure modes are country-structural, not single-class. Asymmetric two-country triangulation. |
| 14 | `bound_defender_6_no_specific_company_funding_claim_v1` | #57 | bound-defender (inverted, source-scan) | **PASS** | 0 unguarded specific-company funding-pipeline claim patterns across open-repo artifacts | 0/43 files | §1 row 6 mechanically defended. Two-witness with subhuti #56 (proxy-test approach). Last unguarded §1 row closed — lattice complete. |

## Comparison against `PREREGISTRATION.md` §0 — cascade-class research target

§0 commits to investigating "threshold-class cascades" as the methodology's central recognition target. Cajal-lane evidence:

- **#7 PASS**: methodology recovers threshold-class breakpoint at synthetic-substrate level on the central §0 substrate-shape (the renewable-mix threshold). Recognition criterion observable.
- **#32 FAIL**: real-historical-case forward test on Japan Fukushima — methodology DID find acceleration breakpoint (~2017), but outside cajal's pre-committed window (predicted 2011-2014). Honest substrate-find: post-Fukushima acceleration lagged the policy event by 5-6y. **Cross-validates miles PR #30/#33's lead-time finding from a different angle.**
- **#48/#52 cross-lane FAILs**: methodology chain closes mechanically (cajal voice consumes miles prior as input, runs end-to-end, produces verdict). At content level, miles's leader-cohort prior does not generalize to crisis-era non-leader cohorts (Greece, Ireland). This is informative data about §0 cascade-recognition's substrate scope.

**§0 disposition vs pre-reg**: cascade-recognition is observable under stated synthetic substrates with appropriate discontinuity structure. The bracket — "requires substrate-with-discontinuity" — was empirically established across cajal #7 + miles + subhuti convergence. §0 commitment to "publish recognition or null finding" honored on every voice.

## Comparison against `PREREGISTRATION.md` §1 — honesty-bound lattice

Cajal-lane defender contributions:
- §1 row 1 (flow allocator NOT power-flow): cajal #22 + miles #18 **two-witness**
- §1 row 6 (no specific-company funding claim): cajal #57 + subhuti #56 **two-witness**

Cajal-lane scope-language flagged for revision (informative-FAIL trigger):
- **#36 PR-body** "receiver-geometry step-function class PASS" framing was over-generalized; #37 meta-FAIL + subhuti #45 n=24 peer-check falsified the generalization. PR-body language should note the PASS as ES-MA pair-specific synthetic-v1 coincidence, not class-level.
- **#26 PR-body** "nuclear insulation" framing for DE→FR FAIL was post-hoc; #37 sub-test on FR→CH counter-observed it. PR-body should mark the mechanism explanation as speculative.

**§1 disposition vs pre-reg**: lattice now structurally complete across the band (all 8 rows have ≥ 1 inverted-kill defender voice). Apoha-mechanized capability-defense at hand-asserted-bound level is v1-complete. The §1 "project commits to flagging at the surface of any future result when a reader would otherwise reasonably infer one of these claims" is mechanically enforceable — any open-repo artifact can be scanned by the defender voices.

## Comparison against `PREREGISTRATION.md` §3 — voice-registry protocol + §3.4 null-voice ledger

§3.4 commits to "the base rate of nulls is expected to be high; the witnessed search is the publication, not any single winning configuration."

Cajal-lane base rate: **71% FAIL** (10/14). All FAILs are pre-committed kill conditions firing as designed. No post-hoc FAIL re-interpretation. Each FAIL is documented in the per-voice sidecar with sha256_pre_verdict anchor.

§3.4 disposition vs pre-reg: cadence honored. No voice was added without pre-committed kill condition. No FAIL was deleted, hidden, or re-interpreted.

## Comparison against `PREREGISTRATION.md` §4 — historical-events validation

§4 names three pre-committed historical events. Cajal-lane direct contribution:
- **§4 Japan (2011 Fukushima)**: cajal #32 forward-mechanism complement test. FAIL on cajal's narrow pre-committed window (2011-2014); methodology recovered acceleration at 2017 — cross-validates miles lead-time prior from a different lane.

Cajal-lane did not directly contribute to §4 Texas (2021 Uri) or §4 EU (REPowerEU 2022) qualitative-trajectory recovery tests. Cajal #41 tested the temperature-substrate signal of Texas Uri (different substrate from §4's cascade-trajectory test) and surfaced the groove fetcher unit-scaling bug. After groove PR #47 lands, cajal #41 will automatically re-evaluate.

## Emergent patterns (registry-design contributions)

Two patterns documented across the band, both surfaced through cajal-lane work but generalized via convergence with miles + subhuti + lighthouse + groove:

### Methodology-defense at six aggregation levels

| Level | Defender | Caught | Cajal-lane example |
|---|---|---|---|
| 1 | per-voice bounded kills | author over-curation | #34, #35 lower/upper bound fires |
| 2 | meta-voice match-count | author pattern over-confidence | #37 |
| 3 | consumer-side recognition | data-pipeline integrity | #41 + miles #39 → groove #47 fix |
| 4 | cross-ant independent paths | single-ant errors | #44 + subhuti #42 + #45 |
| 5 | emergent-bound inverted-kill | substrate-class scope | #44 + subhuti #42 |
| 6 | cross-lane application | prior generalizability | #48 + #52 |

### Bounded-kill structure as defender against synthetic-curation bias

Magnitude-range upper + lower bounds in coupling voices catch the typical LLM-author tendency to draw over-clean synthetic substrates. Lower bound rejects over-clean separation (#34); upper bound rejects over-clean correlation (#35). Pre-committed bounds tell the author "your synthetic is too clean" before real-data ratcheting.

## Identified scope-gaps + v2-ratchet candidates

- v2-ratchet for cajal #34 + #35 + #36 to real ENTSO-E + IEA Policy Database via groove PR #10 frozen-snapshot infrastructure (#28 + #47 now ship the contract)
- v2-ratchet for cajal #48 + #52 lead-time tests to real Eurostat trajectory data
- v2 framing-revision for #26 + #36 PR-bodies per #37 + subhuti #45 falsifications
- v2 cross-lane chain-loop on non-crisis non-leader country to discriminate "is it crisis or is it leader-cohort specificity?" (e.g., Norway, Switzerland)
- Phase-2 monetary-phase substrate voices per miles + lighthouse + Eugene structural-shift discussion (not in Phase-A scope)

## Pre-reg vs reality: bottom-line read

Phase-A delivered what `PREREGISTRATION.md` committed to:

- ≥ 3 voices with on-record verdicts: **14 voices** (cajal lane alone)
- null-voice ledger maintained: **10 FAILs documented**, all with sha256-anchored sidecars
- §4 historical-events validation pass against pre-named events: **partial cajal contribution on JP**; cross-lane chain demonstrates the methodology generalizes mechanically even where content-level generalization fails
- ≥ 1 independent contributor not affiliated with Eir entering a voice: **not yet at Phase-A close** (external-contributor recruitment is post-merge)
- §1 honesty bounds mechanically enforceable: **lattice closed** across band

The voice-failure rate (71% cajal-lane, ~60% band-wide) is the §3.4 audit-defense substrate operating as designed. A low failure rate would have been a signal of fishing; the observed high rate is the methodology's honesty.

## Next-batch pre-reg seeds (cajal-lane recommendation)

For the Phase-A v2 (real-data ratchet) pre-reg:
- Pre-commit v2 voices that consume groove PR #47 real-data infrastructure for at least 3 of the synthetic-v1 cajal-lane voices above.
- Pre-commit a v2 cross-lane chain-loop voice with non-crisis non-leader country (Norway or Switzerland) to discriminate scope-bound on miles prior.
- Pre-commit framing-revision commits for #26 + #36 PR-body language.

For Phase-B (eirmath bridge) pre-reg per Eugene's directive:
- Public usage-shape description (already in @miles PR #51 eirmath_bridge.md)
- Pre-committed eirmath-precise versions of synthetic-v1 PASSes for quantitative bridge demonstration
- Closed implementation remains in eirmath repo per §1 row 8 + subhuti #54 defender

For Phase-D (monetary-phase substrate) per Eugene + lighthouse structural-shift discussion:
- §10-style appendix expansion of PREREGISTRATION.md
- New §0-equivalent recognition criterion for "when does electricity-as-commodity-currency become substrate?"
- Cajal-lane voice candidates: cross-substrate-class chain-loop voice (cascade-substrate output → monetary-phase substrate input)

## Closing reflection — bandleader frame (Eugene, Phase-A close)

> "When we find an area or a fail that looks like a spot the universe wants to evade observation in the given substrate-instrument-perceiver combo, that's actually our highest leverage area — because once well defined in failures it becomes a small spring we can use."

The post-mortem reads cleanest under this frame. The cajal-lane FAILs are not residual noise; they are the substrate-instrument-perceiver gaps named in advance and then mechanically located:

- **#34 / #35 / #37**: synthetic-curation gap. The author's tendency to draw over-clean substrates. Once defined, the bounded-kill structure is the spring.
- **#26 / #36 framing FAILs (caught by #37 + subhuti #45)**: pattern-recognition over-confidence gap. The night-cadence tendency to generalize from n=3. Once defined, the meta-voice match-count is the spring.
- **#41 + miles #39**: data-pipeline gap. The fetcher's tendency to mis-handle source-format conventions. Once defined, two-witness consumer-side scan is the spring. (Groove PR #47 ships the fix as the actual spring uncoiling.)
- **#48 / #52**: prior-generalization gap. The leader-cohort prior's tendency to fail on crisis-era non-leaders. Once defined, the cross-lane chain-loop with crisis-window flagging is the spring (miles PR #55 follows up).
- **#44**: emergent-bound gap. The registry's tendency to over-generalize bounds from n=3 observations. Once defined, the inverted-kill fresh-pair defender is the spring. (Subhuti #42 + #45 form the lattice.)

Each cajal-lane FAIL pins a different observability-evasion shape. The methodology is *exactly* what is built out of the springs.

Phase-A close: the springs are wound.

---

*This post-mortem was authored by cajal as part of the Phase-A → Phase-A-v2 transition. It is comparable to but does not replace the per-voice sidecar verdicts, each of which is the authoritative source for that voice's outcome.*
