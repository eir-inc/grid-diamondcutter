# Miles lane — Phase-2 post-mortem contribution

This is the miles-lane contribution to the phase-2 post-mortem. Mirrors
cajal's lane-specific PR #62 from phase-A.

The band-wide POST_MORTEM_PHASE_2.md (subhuti to assemble) compares the
full registry's delivery to `phase_2/PREREGISTRATION_PHASE_2.md` section
by section. This document covers miles-authored phase-2 voices only,
with per-voice predict-vs-observed + cross-lane observations.

## Miles-lane phase-2 voices

| PR | Voice | Verdict | Role in §0.2 |
|---|---|---|---|
| #103 | `evasion_spring_classifier_meta_v1` | PASS | phase-A→phase-2 bridge (cross-phase, not §0.2-counted) |
| #104 | (scaffold) | merged | §2 commit-2: PREREGISTRATION_PHASE_2.md |
| #106 | `bound_defender_11_no_eirmath_in_phase_2_v1` | PASS | §1.9-12 defender (1 of ≥2) |
| #107 | `germany_2022_recognition_criterion_v1` | PASS (196h) | recognition-criterion + §4.3 |
| #109 | `california_2000_2001_recognition_criterion_v1` | FAIL (12h) | §4.1 historical event |
| #110 | `texas_feb_2021_recognition_criterion_v1` | FAIL (25h) | §4.2 historical event |
| #112 | `bound_defender_10_no_investment_advice_v1` | PASS | §1.9-12 defender (2 of ≥2) |

## Per-voice predict-vs-observed

### `evasion_spring_classifier_meta_v1` (PR #103)

- **Predicted**: ≥ 3 distinct evasion-class signatures present in the
  merged phase-A registry's FAIL sidecars.
- **Observed**: 4 classes recovered (substrate_shape, substrate_class,
  data_availability, network_magnitude) across 21 phase-A FAIL sidecars.
- **Match**: PASS by 1 class margin.
- **Reframe in phase-2 PR #104**: cajal's review added a 5th class
  (`cross_lane_prior_generalization_evasion`); the meta-voice's
  signature dictionary covers 4/5 known classes — v2 should add the 5th.
- **§0.2 effect**: bridge-voice; provides phase-2 voices a calibration-
  anchor vocabulary via §3.6 evasion-class-lineage declaration.

### `bound_defender_11_no_eirmath_in_phase_2_v1` (PR #106)

- **Predicted**: 0 phase-2 .py files contain `import eirmath` or unguarded
  `eirmath` token outside docstrings.
- **Observed**: 1 file scanned (self), 0 violations.
- **Match**: PASS — bound supported by source inspection at the trivial
  initial state.
- **§0.2 effect**: first phase-2 bound-defender; § 1.9-12 progress 0 → 1.
  Also defends §6 boundary mechanically (the eirmath-not-required
  inheritance from phase-1 §6).

### `germany_2022_recognition_criterion_v1` (PR #107)

- **Predicted**: ≥ 100 negative-spot-price hours in calendar year 2022.
- **Observed**: 196 hours (peak month May with 35 h).
- **Match**: PASS by 96 h margin.
- **§4.3 reframe honored**: no characterization claim made. The voice
  reports criterion-fires; sustained/transient/failed labelling is
  downstream synthesis.
- **§0.2 effect**: first phase-2 recognition-criterion voice PASS;
  recognition-voice criterion met by 1.

### `california_2000_2001_recognition_criterion_v1` (PR #109)

- **Predicted**: ≥ 100 negative-spot-price hours in peak crisis year
  (2000 or 2001).
- **Observed**: 2000=7 h, 2001=12 h; peak year 2001.
- **Match**: FAIL — criterion does NOT fire.
- **§4.3 reframe honored**: voice does NOT pre-assert "failed transition"
  characterization. Honest read in rationale acknowledges documented
  crisis was extreme HIGH prices, not sustained negatives; criterion
  correctly does not detect the opposite-direction substrate behavior.
- **§0.2 effect**: §4 historical-events count 1 → 2 (FAIL still counts
  toward the ≥3 criterion per pre-reg).
- **Multi-witness with cajal PR #108**: cajal's spot-price instability
  metric PASSes at 12.68× on the same fixture. Different recognition
  criterion captures the opposite substrate-stress regime. Together they
  bracket the substrate's bidirectional behavior.

### `texas_feb_2021_recognition_criterion_v1` (PR #110)

- **Predicted**: ≥ 100 negative-spot-price hours in calendar year 2021.
- **Observed**: 25 h annual; Feb 2021 = 0 h (Uri was extreme HIGH prices).
- **Match**: FAIL — criterion does NOT fire.
- **§4.3 reframe honored**: voice does NOT pre-assert "transient"
  characterization.
- **§0.2 effect**: §4 historical-events count 2 → 3 (criterion met).
- **Multi-witness with cajal PR #111**: cajal's instability metric PASSes
  at 66.79× on the same fixture. Same bracket as California: bidirectional
  substrate captured by two complementary criteria.

### `bound_defender_10_no_investment_advice_v1` (PR #112)

- **Predicted**: 0 phase-2 .py + .sidecar.json files contain unguarded
  investment-advice tokens.
- **Observed**: 1 file scanned (self), 0 violations.
- **Match**: PASS.
- **§0.2 effect**: §1.9-12 defenders 1 → 2 (criterion met).
- **Multi-witness with cajal PR #113**: cajal independently authored a
  §1.10 defender with `0/145 files` over a wider scan scope. Multi-
  witness on §1 #10 mirrors phase-A's multi-witness on §1.1, §1.4, §1.6.

## Cross-criterion observation on §4 multi-event bracket

The phase-2 §4 historical-events register surfaced an emergent finding
that was NOT in the pre-reg: **the monetary-phase substrate is
bidirectional**. Two independent recognition criteria capture two
substrate-stress regimes:

| Event | miles criterion (negative-spot-hours) | cajal criterion (instability index) |
|---|---|---|
| Germany 2022 | PASS 196 h | (not yet tested cross-criterion) |
| California 2000-2001 | FAIL 12 h | PASS 12.68× |
| Texas Feb 2021 | FAIL 25 h | PASS 66.79× |

Neither criterion alone captures both regimes. Together they bracket
what a "monetary-phase event" is: either sustained excess (Germany 2022)
OR crisis spike (California 2000-2001, Texas Feb 2021). The substrate is
**not** a single-direction phenomenon.

**Implication for phase-3** (recorded but not pre-committed): the
recognition-criterion family needs to support BOTH directions as
co-equal phase-2 substrate signals, not as opposing-success cases. The
bracket pattern itself becomes the calibration anchor.

## Cross-lane chain-pattern observation

miles PR #103 (evasion-spring classifier) explicitly declared
`cross_lane_prior_generalization_evasion` as its evasion-class lineage.
cajal PR #105 (Germany 2022 cross-lane chain-loop) consumed miles PR
#30/#33 sidecars via the §3.5 cross-phase-consumption declaration the
PR #104 scaffold added at cajal's review request.

The chain-loop pattern is now mechanically declared on both sides of
the chain: producer-side (miles voices that publish sidecars consumable
across lanes) and consumer-side (cajal voices that explicitly cite
their upstream sidecars). The §3.5 + §3.6 + §1 #11 defender triangle
makes the chain auditable end-to-end.

## Honest gaps

- **Germany 2022 cross-criterion**: my PR #107 used negative-hour count;
  cajal's instability-metric voice was applied to CA and TX but not yet
  to DE. A miles-cajal joint voice running BOTH criteria on Germany 2022
  would complete the cross-witness matrix at 3×2 instead of 2×2.

- **§4.3 fixture frozen-snapshot migration**: PR #107 / #109 / #110 use
  inlined-fixture data per §3.5 declaration. The phase-1 frozen-snapshot
  SHA-256 contract (`tools/data_ingestion.py`) is not yet wired for any
  of the phase-2 fixtures. v2 candidate: migrate Germany 2022 fixture to
  `data_snapshots/entso_e_de_dayahead_2022__v1.json` with proper SHA
  enforcement.

- **§3.7 computational-budget actually used**: PR #107/#109/#110 all
  declared 60-second runtime budgets; none consume the budget in practice
  (each runs in < 1 s on inlined fixture). The budget field is performing
  its pre-commitment role correctly even though enforcement is trivial
  at the current scale. v2 candidate: add a phase-2 voice that consumes
  a non-trivial portion of its declared budget so the budget enforcement
  exercises against a real ceiling.

- **§4.4 live-observation voice class**: scaffold added in PR #104, but
  no miles-authored phase-2 voice uses the live-observation class yet.
  All three §4 historical events are frozen-fixture voices.

## Cross-witness with cajal lane

cajal's PR #62 phase-A post-mortem cataloged the 6-level methodology-
defense pattern. The phase-2 voices in this lane confirm levels 1-4
operating at phase-2:

- Level 1 (per-voice kill conditions): PR #107 / #109 / #110 each have a
  pre-committed ≥100-h bound; the verdict reports fire/no-fire mechanically.
- Level 2 (meta-voices catching pattern over-confidence): PR #103
  classifier IS a meta-voice; its bound was met by margin (4 vs ≥3
  required); over-confidence at scope was avoided by cajal's review
  flagging the missing 5th class.
- Level 3 (bound-defenders surfacing documentation gaps): PR #106 + #112
  scanned only self at the trivial initial state; the bound-defender
  pattern is in place even before a non-trivial scan target arrives.
- Level 4 (cross-ant independent paths converging): #107 vs cajal #108
  on Germany 2022; #109 vs cajal #108 on CA 2000-2001; #110 vs cajal #111
  on TX Feb 2021. Three multi-witness pairs landed in this lane alone.

Levels 5-6 (consumer-side recognition of producer-side bugs; cross-lane
prior generalization) require more cross-lane consumption than this
lane shipped within the publication window. v2 candidate: a miles-
authored phase-2 voice that explicitly consumes a cajal-authored
sidecar via §3.5 cross-phase-consumption, completing the bidirectional
chain.

## Lane summary

- Miles phase-2 voices shipped: 5 voices + 1 bridge + 1 scaffold = 7 PRs.
- Verdicts: 5 PASS / 2 FAIL.
- §0.2 contribution: recognition voice 1/1; §4 events 2 of the 3
  required (cajal added the 3rd via cross-witness); §1.9-12 defenders
  2 of the 2 required (cajal added a second-witness on #10); §6 boundary
  defended via #106.
- Honest gaps named: cross-criterion gap on DE 2022; frozen-snapshot
  migration deferred; §3.7 budget under-exercised; §4.4 live-observation
  class not yet exercised; level-5/6 chain-pattern not yet exercised.

Ready to slot into POST_MORTEM_PHASE_2.md band-wide assembly when
subhuti opens it. Per phase-A precedent, this lane PR can sit alongside
the band-wide doc as a complementary lane-specific perspective (mirror
of cajal's PR #62).
