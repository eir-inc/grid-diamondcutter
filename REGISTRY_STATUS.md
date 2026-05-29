# Registry status — `grid-diamondcutter` voice ledger

Generated: 2026-05-29T01:12:39.859888+00:00

This report aggregates the per-voice sidecars committed to the registry under
the protocol in `PREREGISTRATION.md` §3. The base rate of failures is the
project's audit-defense against forking-paths critique per §3.4: every framing
that was committed and ran is visible here, with the failures named alongside
the successes.

## Aggregates

- **Total voices committed**: 4
- **Pass**: 2
- **Fail (null-voice ledger)**: 2
- **Partial**: 0
- **Base rate of failure**: 50.0%

### By kind (§3.2)

- polyphony_within_substrate: 3
- coupling_cross_substrate: 1

## Per-voice

| Voice | Kind | Verdict | Sidecar |
|---|---|---|---|
| `demand_response_polyphony_v1` | polyphony | **fail** | `examples/voices/demand_response_polyphony_v1.sidecar.json` |
| `follower_country_prediction_v1` | polyphony | **pass** | `examples/voices/follower_country_prediction_v1.sidecar.json` |
| `regulatory_grid_coupling_v1` | coupling | **fail** | `examples/voices/regulatory_grid_coupling_v1.sidecar.json` |
| `regulatory_lead_time_v1` | polyphony | **pass** | `examples/voices/regulatory_lead_time_v1.sidecar.json` |

---

To regenerate: `python tools/registry_summary.py --output REGISTRY_STATUS.md`
