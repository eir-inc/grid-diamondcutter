# Changelog

All notable changes to `grid-diamondcutter-oss` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (entries land here as PRs ship into `main` after the v0.2.0 tag.)

---

## [0.2.0] — 2026-05-29 (phase-A + phase-2 publication-window close)

The first full publication-window cycle. 99 PRs merged in a single overnight + morning session. The §3.4 audit-substrate operated end-to-end: voices were pre-registered, ran, produced verdicts, multi-witness cross-voice triangulation surfaced + corrected the registry's own framing errors, and the close-out documents (POST_MORTEM.md + POST_MORTEM_PHASE_2.md) compared delivered registry to the pre-reg commitments.

### Added — phase-A (registry + audit-defense lattice)

- **`PREREGISTRATION.md`** — public pre-reg (§0 central question, §1 honesty bounds, §3 voice protocol, §4 historical-events validation, §5 correction protocol, §6 publishing shape, §7 scope limitations).
- **§3 voice-registry protocol infrastructure**:
  - `examples/voices/_voice_template.py` — boilerplate (underscore-prefixed → excluded from auto-discovery).
  - `examples/voices/README.md` — file table + authoring steps + reviewer-scope note.
  - `examples/voices/TUTORIAL.md` — 8-step first-voice-in-5-minutes walkthrough.
  - `tests/test_voice_registry_contract.py` — mechanical §3.1 conformance test (auto-discovers `examples/voices/*.py`).
  - `tools/registry_summary.py` — `REGISTRY_STATUS.md` + JSON generator; shape-tolerant verdict aggregator.
  - `tests/test_registry_summary.py` — pins §3.4 aggregator behavior.
  - `.github/workflows/voice_contract.yml` — §3.1 conformance CI.
  - `.github/workflows/registry_status_sync.yml` — auto-regen REGISTRY_STATUS.md.
- **§1 honesty-bounds defender lattice — 7/7 named bounds mechanically defended**:
  - `low_failure_rate_alarm_v1` (§0.3 fishing-signal defender).
  - `bound_defender_1_allocator_v1` + `flow_allocator_is_not_power_flow_v1` (§1.1 — multi-witness).
  - `bound_defender_2_adapter_stubs_source_inspection_v1` (§1.2).
  - `bound_defender_3_coupling_coefficient_v1` (§1.3 — surfaced + closed a documentation gap in `meta_sim/meta.py` in the same PR).
  - `bound_defender_4_cascade_not_prediction_v1` + `bound_defender_4_no_forecast_language_v1` (§1.4 — multi-witness; first FAIL surfaced 5 unguarded cascade mentions in §0/§6 as honest-gap on record).
  - `region_transfer_failure_v1` (§1.5).
  - `bound_defender_6_funding_gap_proxy_v1` + `bound_defender_6_no_specific_company_funding_claim_v1` (§1.6 — multi-witness; lattice closer).
  - `bound_defender_8_eirmath_not_required_v1` (§1.8 — phase-A load-bearing; structural .py scan + documentation guard).
  - `lead_time_prior_crisis_robustness_defender_v1` (substantive bound counter-observation; 5/6 leaders crisis-contaminated).
- **§4.2 historical-events validation — 3/3 PASS**:
  - `texas_feb_2021_uri_v1`, `eu_may_2022_repowereu_v1`, `japan_march_2011_fukushima_v1`.
- **§4.3 qualitative-trajectory recovery**:
  - `tools/qualitative_comparison` harness + fixtures.
  - Harness wired into `voice_contract.yml` CI.
- **Real-data ingestion**:
  - `tools/data_ingestion.py` — frozen-snapshot SHA-256 contract.
  - `tools/fetch_noaa_uri.py` v2 (unit-handling fix per §5.1; v1 surfaced bug + retired).
  - `data_snapshots/noaa_ncei__texas_uri_feb_2021__v1.json` — 70 station-day observations across 7 Texas stations.
- **Lead-time methodology chain (closed 6+1 voice methodology)**:
  - `regulatory_lead_time_v1` (~9y policy → deployment prior across 6 leader countries).
  - `leader_cohort_loo_cv_v1` (LOO MAE 1.47y validates prior).
  - `follower_country_prediction_v1` + `follower_country_prediction_v2` (Poland/Romania/Greece; v2 uses calibration-honest ±1.47y uncertainty).
  - `regulatory_lead_time_v2_expanded_cohort` (12-country global; drift 0.09y vs v1).
  - `global_follower_prediction_v1` (Mexico/Vietnam/SA/Indonesia inflection ~2028-2030).
  - `capability_by_apoha_set_meta_v1` (mechanizes apoha-set-as-capability).
- **Country-suitability voices**:
  - `country_apoha_suitability_v1` — 9/10 countries identified for positive grid-resiliency cascade.
  - `country_blocker_diagnostics_v1` — single-intervention candidate detection (Iceland surfaced).
- **§5 correction-protocol exercised live**:
  - Receiver-shape framing arc: `smooth_receiver_coupling_alarm_v1` PASS at n=3 → `receiver_shape_distinguishability_v1` FAIL at n=24 (self-audit) → `smooth_s_curve_emergent_bound_fresh_pairs_v1` sibling-witness FAIL. Framing correction recorded.
  - NOAA fetcher v1 → v2 unit-fix (two-witness analyst-error surfacing).
- **Cross-region positive-cascade exploration**:
  - `denmark_germany_renewable_export_coupling_v1` (FAIL — over-correlation kill caught synthetic curation).
  - `spain_morocco_renewable_export_coupling_v1` (PASS — first positive coupling).
  - `receiver_geometry_substrate_class_v1` (FAIL — meta-voice falsifies receiver-shape generalization).
- **`POST_MORTEM.md`** — phase-A delivered registry vs `PREREGISTRATION.md` commitments. Multi-ant contributions named per PR.
- **`PHASE_A_MERGE_BATCHES.md`** — wave-sequenced merge triage (archived after window close).

### Added — phase-2 (monetary-phase substrate)

- **`phase_2/PREREGISTRATION_PHASE_2.md`** — phase-2 pre-reg inheriting phase-1's §3 protocol + adding §1.9-12, §3.5 cross-phase consumption declaration, §3.6 evasion-class lineage declaration, §4.1-4.3 historical-events bracket.
- **§0.2 phase-2 success criteria 4/4 MET**:
  - Recognition-criterion voice PASS: 3 delivered (`germany_2022_recognition_criterion_v1` 196h; `california_2000_2001_recognition_v1` 12.68x; `texas_feb_2021_recognition_v1` 66.79x).
  - §4 historical events from separate sources, multi-witness on each: 3/3.
  - §1 phase-2 bound-defenders: 2 (`bound_defender_11_no_eirmath_in_phase_2_v1`, `bound_defender_10_no_investment_advice_v1`).
  - §6 eirmath boundary mechanically defended in `phase_2/`.
- **§0.3 phase-2 failure criteria**: 0/4 triggered. 37.5% base-rate fail healthy.
- **§4 multi-witness bracket discriminates two substrate classes**:
  - Sustained-excess (negative-spot-hours): Germany 2022 PASS.
  - Crisis-spike (price-instability): California 2000-01 + Texas Feb 2021 PASS.
- **§3.5 cross-phase consumption** operationalized in `germany_2022_cross_lane_lead_time_recognition_v1` (first cross-phase voice in registry; consumes phase-1 `regulatory_lead_time_v1` as `prior_anchor`).
- **§3.6 evasion-class lineage** operationalized in `evasion_spring_classifier_meta_v1` (phase-A→phase-2 bridge classifier; 5 phase-A evasion-class signatures available for inheritance).
- **`phase_2/POST_MORTEM_PHASE_2.md`** — phase-2 delivered registry vs phase-2 pre-reg.
- **`phase_2/MILES_LANE_PHASE_2_POST_MORTEM.md`** — miles lane-specific post-mortem with per-voice predict-vs-observed.

### Added — bridge documentation

- **`docs/eirmath_bridge.md`** — public-shape description of where `eirmath` plugs in (3 use cases pre-disclosed: temporal → $, voice aggregation → portfolio risk, bound-defender ledger → audit report). No math, no eirmath dependency. The §6 boundary anchor for phase-1 reviewers + phase-3 baseline.

### Changed

- `meta_sim/meta.py` — added HONESTY-BOUND GUARD block adjacent to the +0.832 mention (per `bound_defender_3_coupling_coefficient_v1` finding).
- `tools/registry_summary.py` — added `_extract_verdict()` / `_extract_rationale()` helpers tolerating both `{verdict: {verdict: 'x'}}` (template shape) and `{verdict: 'x'}` (bare-string shape one early voice used).
- `Makefile` — added targets: `voices`, `voice-contract`, `registry`, `registry-md`.
- `docs/meta_sim.md` — package documentation for the polyphonic substrate.

### Notes

- **48 voices on `main`** at phase-A close + **8 voices on `main`** at phase-2 close = **56 voice sidecars** in the registry.
- **Pass/fail/partial distribution**: 25 PASS / 21 FAIL / 2 PARTIAL across phase-A (43.8% fail rate); 5 PASS / 3 FAIL across phase-2 (37.5% fail rate). Both above the §0.3 low-failure-rate alarm floor.
- **99 PRs in the publication window**, including 30+ rebased replacements (REGISTRY_STATUS.md auto-regen conflict pattern; resolved by cherry-pick-onto-fresh-branch).
- **Four-witness band convergence** documented in POST_MORTEM_PHASE_2.md: four phrasings of the same meta-finding from four ant lanes (cajal: *FAIL is the audit-substrate*; subhuti: *bound-defenders close gaps in the same PR*; miles: *apoha mechanizes*; groove: *wrong in public is the gift*).
- **Emergent patterns** named in POST_MORTEM.md as honest additions (not pre-registered): apoha-as-design-pattern, multi-witness cross-voice triangulation, receiver-shape framing → over-fit → re-described arc, evasion-spring frame (Eugene-introduced), cross-lane chain-loops.
- **Honest gaps** named in POST_MORTEM.md: §3.5 independent-contributor protocol untested in phase-A; PR #50 surfaced unguarded cascade mentions in PREREGISTRATION.md §0 + §6; §0 conditionality on substrate-discontinuity surfaced post-pre-reg; real-grid validation deferred; phase-A `REGISTRY_STATUS.md` auto-sync first full-lattice regeneration was manual.

---

## [0.1.0] — 2026-05-28 (pre-release)

### Added
- `power_grid_sim.py` — single-file, numpy-only 8-node grid surrogate + cycle-walk measurement.
- `power_grid_sim_v2.py` — meta-sim with 3 polyphonic voices (load-flow / control / dynamics) and cross-band coupling demonstration.
- `meta_sim/` package — `Voice` / `MetaSim` abstractions, `closure_walk_meta`, `measure_cross_band_coupling`.
- `grid_diamondcutter_oss.py` — voices-pattern reference with optional sim-backend stubs (PYPOWER / PandaPower).
- `examples/basic_grid.py` — single-voice quickstart.
- `examples/ieee_case_demo.py` — REAL PYPOWER `runpf` ingest for case14 / case30 / case118 with pre-registered analysis + dual-scalar reporting (closure_residual + path_excursion).
- `examples/voice_extension_template.py` — drop-in starter for contributors adding new voices.
- `docs/methodology.md` — longer-form theory.
- `docs/for_grid_engineers.md` — translation layer for engineers coming from PYPOWER / PandaPower / OpenDSS.
- `tests/test_substrate_contract.py` — 19 substrate-plugin contract conformance tests.
- `tests/test_meta_sim.py` — 18 meta-sim + cross-band-coupling regression tests.
- `tests/test_pipeline_integration.py` — 11 end-to-end pipeline tests.
- `LICENSE` (Apache 2.0), `NOTICE`, `SECURITY.md`, `CONTRIBUTING.md`.
- `pyproject.toml` (pip-installable), `Makefile` (contributor convenience commands).
- `reproducibility_hashes.json` — signed expected outputs from canonical runs.

### Notes
- This is a pre-release scaffolding version. The internal git history is the scaffolding record; public-shipping versions will be cut as clean snapshots from this working tree.
- 48 tests passing in 0.4s.
- Public vocabulary set: `cycle_residual`, `stability_class` (`stable-cycle` / `moderate-stress-cycle` / `high-stress-cycle`), `cycle walk`, `prevention-based pricing`. Earlier internal-development vocabulary has been replaced across the public-facing surface.
