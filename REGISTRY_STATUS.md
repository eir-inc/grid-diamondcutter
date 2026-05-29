# Registry status — `grid-diamondcutter` voice ledger

Generated: 2026-05-29T02:26:00.709754+00:00

This report aggregates the per-voice sidecars committed to the registry under
the protocol in `PREREGISTRATION.md` §3. The base rate of failures is the
project's audit-defense against forking-paths critique per §3.4: every framing
that was committed and ran is visible here, with the failures named alongside
the successes.

## Aggregates

- **Total voices committed**: 3
- **Pass**: 0
- **Fail (null-voice ledger)**: 2
- **Partial**: 1
- **Base rate of failure**: 66.7%

### By kind (§3.2)

- polyphony_within_substrate: 2
- coupling_cross_substrate: 1

## Per-voice

| Voice | Kind | Verdict | Sidecar |
|---|---|---|---|
| `capability_by_apoha_set_meta_v1` | polyphony | **partial** | `examples/voices/capability_by_apoha_set_meta_v1.sidecar.json` |
| `demand_response_polyphony_v1` | polyphony | **fail** | `examples/voices/demand_response_polyphony_v1.sidecar.json` |
| `regulatory_grid_coupling_v1` | coupling | **fail** | `examples/voices/regulatory_grid_coupling_v1.sidecar.json` |

---

To regenerate: `python tools/registry_summary.py --output REGISTRY_STATUS.md`
