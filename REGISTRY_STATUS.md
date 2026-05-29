# Registry status — `grid-diamondcutter` voice ledger

Generated: 2026-05-29T03:21:48.205131+00:00

This report aggregates the per-voice sidecars committed to the registry under
the protocol in `PREREGISTRATION.md` §3. The base rate of failures is the
project's audit-defense against forking-paths critique per §3.4: every framing
that was committed and ran is visible here, with the failures named alongside
the successes.

## Aggregates

- **Total voices committed**: 48
- **Pass**: 25
- **Fail (null-voice ledger)**: 21
- **Partial**: 2
- **Base rate of failure**: 43.8%

### By kind (§3.2)

- polyphony_within_substrate: 35
- unknown: 1
- coupling_cross_substrate: 12

## Per-voice

| Voice | Kind | Verdict | Sidecar |
|---|---|---|---|
| `bound_defender_1_allocator_v1` | polyphony | **pass** | `examples/voices/bound_defender_1_allocator_v1.sidecar.json` |
| `bound_defender_2_adapter_stubs_source_inspection_v1` | polyphony | **pass** | `examples/voices/bound_defender_2_adapter_stubs_source_inspection_v1.sidecar.json` |
| `bound_defender_3_coupling_coefficient_v1` | polyphony | **pass** | `examples/voices/bound_defender_3_coupling_coefficient_v1.sidecar.json` |
| `bound_defender_4_cascade_not_prediction_v1` | polyphony | **fail** | `examples/voices/bound_defender_4_cascade_not_prediction_v1.sidecar.json` |
| `bound_defender_4_no_forecast_language_v1` | unknown | **pass** | `examples/voices/bound_defender_4_no_forecast_language_v1.sidecar.json` |
| `bound_defender_6_funding_gap_proxy_v1` | polyphony | **pass** | `examples/voices/bound_defender_6_funding_gap_proxy_v1.sidecar.json` |
| `bound_defender_8_eirmath_not_required_v1` | polyphony | **pass** | `examples/voices/bound_defender_8_eirmath_not_required_v1.sidecar.json` |
| `capability_by_apoha_set_meta_v1` | polyphony | **partial** | `examples/voices/capability_by_apoha_set_meta_v1.sidecar.json` |
| `capacity_scaling_monotonicity_v1` | polyphony | **pass** | `examples/voices/capacity_scaling_monotonicity_v1.sidecar.json` |
| `capacity_utilization_load_coupling_v1` | coupling | **fail** | `examples/voices/capacity_utilization_load_coupling_v1.sidecar.json` |
| `country_apoha_suitability_v1` | polyphony | **pass** | `examples/voices/country_apoha_suitability_v1.sidecar.json` |
| `country_blocker_diagnostics_v1` | polyphony | **pass** | `examples/voices/country_blocker_diagnostics_v1.sidecar.json` |
| `cross_lane_chain_loop_greece_v1` | polyphony | **fail** | `examples/voices/cross_lane_chain_loop_greece_v1.sidecar.json` |
| `cross_lane_chain_loop_ireland_v1` | polyphony | **fail** | `examples/voices/cross_lane_chain_loop_ireland_v1.sidecar.json` |
| `demand_response_polyphony_v1` | polyphony | **fail** | `examples/voices/demand_response_polyphony_v1.sidecar.json` |
| `denmark_germany_renewable_export_coupling_v1` | coupling | **fail** | `examples/voices/denmark_germany_renewable_export_coupling_v1.sidecar.json` |
| `eu_may_2022_repowereu_v1` | coupling | **pass** | `examples/voices/eu_may_2022_repowereu_v1.sidecar.json` |
| `finer_fingerprint_resolves_v1` | polyphony | **fail** | `examples/voices/finer_fingerprint_resolves_v1.sidecar.json` |
| `flow_allocator_is_not_power_flow_v1` | polyphony | **pass** | `examples/voices/flow_allocator_is_not_power_flow_v1.sidecar.json` |
| `follower_country_prediction_v1` | polyphony | **pass** | `examples/voices/follower_country_prediction_v1.sidecar.json` |
| `follower_country_prediction_v2` | polyphony | **pass** | `examples/voices/follower_country_prediction_v2.sidecar.json` |
| `germany_neighbor_renewable_coupling_v1` | coupling | **fail** | `examples/voices/germany_neighbor_renewable_coupling_v1.sidecar.json` |
| `global_follower_prediction_v1` | polyphony | **pass** | `examples/voices/global_follower_prediction_v1.sidecar.json` |
| `japan_march_2011_fukushima_v1` | coupling | **pass** | `examples/voices/japan_march_2011_fukushima_v1.sidecar.json` |
| `japan_post_fukushima_acceleration_v1` | polyphony | **fail** | `examples/voices/japan_post_fukushima_acceleration_v1.sidecar.json` |
| `lead_time_prior_crisis_robustness_defender_v1` | polyphony | **fail** | `examples/voices/lead_time_prior_crisis_robustness_defender_v1.sidecar.json` |
| `leader_cohort_loo_cv_v1` | polyphony | **pass** | `examples/voices/leader_cohort_loo_cv_v1.sidecar.json` |
| `low_failure_rate_alarm_v1` | polyphony | **partial** | `examples/voices/low_failure_rate_alarm_v1.sidecar.json` |
| `mix_axis_smoothness_v1` | polyphony | **fail** | `examples/voices/mix_axis_smoothness_v1.sidecar.json` |
| `network_amplification_adoption_cascade_v1` | coupling | **fail** | `examples/voices/network_amplification_adoption_cascade_v1.sidecar.json` |
| `network_amplification_coupling_v1` | coupling | **fail** | `examples/voices/network_amplification_coupling_v1.sidecar.json` |
| `noise_robustness_v1` | polyphony | **fail** | `examples/voices/noise_robustness_v1.sidecar.json` |
| `receiver_geometry_substrate_class_v1` | polyphony | **fail** | `examples/voices/receiver_geometry_substrate_class_v1.sidecar.json` |
| `receiver_shape_distinguishability_v1` | polyphony | **fail** | `examples/voices/receiver_shape_distinguishability_v1.sidecar.json` |
| `region_transfer_failure_v1` | coupling | **pass** | `examples/voices/region_transfer_failure_v1.sidecar.json` |
| `regulatory_grid_coupling_v1` | coupling | **fail** | `examples/voices/regulatory_grid_coupling_v1.sidecar.json` |
| `regulatory_lead_time_v1` | polyphony | **pass** | `examples/voices/regulatory_lead_time_v1.sidecar.json` |
| `regulatory_lead_time_v2_expanded_cohort` | polyphony | **pass** | `examples/voices/regulatory_lead_time_v2_expanded_cohort.sidecar.json` |
| `regulatory_shape_apoha_v1` | coupling | **fail** | `examples/voices/regulatory_shape_apoha_v1.sidecar.json` |
| `renewable_mix_threshold_polyphony_v1` | polyphony | **pass** | `examples/voices/renewable_mix_threshold_polyphony_v1.sidecar.json` |
| `smooth_receiver_coupling_alarm_v1` | polyphony | **pass** | `examples/voices/smooth_receiver_coupling_alarm_v1.sidecar.json` |
| `smooth_s_curve_emergent_bound_fresh_pairs_v1` | polyphony | **fail** | `examples/voices/smooth_s_curve_emergent_bound_fresh_pairs_v1.sidecar.json` |
| `spain_morocco_renewable_export_coupling_v1` | coupling | **pass** | `examples/voices/spain_morocco_renewable_export_coupling_v1.sidecar.json` |
| `station_set_dependence_v1` | polyphony | **pass** | `examples/voices/station_set_dependence_v1.sidecar.json` |
| `texas_feb_2021_uri_v1` | coupling | **pass** | `examples/voices/texas_feb_2021_uri_v1.sidecar.json` |
| `texas_uri_temperature_collapse_real_v1` | polyphony | **fail** | `examples/voices/texas_uri_temperature_collapse_real_v1.sidecar.json` |
| `threshold_cascade_v1` | polyphony | **fail** | `examples/voices/threshold_cascade_v1.sidecar.json` |
| `threshold_cascade_v2` | polyphony | **pass** | `examples/voices/threshold_cascade_v2.sidecar.json` |

---

To regenerate: `python tools/registry_summary.py --output REGISTRY_STATUS.md`
