"""
bound_defender_1_allocator_v1.py — §3.1 polyphony voice (inverted) defending
PREREGISTRATION §1 honesty bound #1.

§1 row #1 says the project will NOT claim:

  "the flow allocator implemented in the open repository is a DC power-flow
   solver, an AC power-flow solver, an EMT simulator, a transient-stability
   simulator, or a protection simulator."

This voice tests that bound mechanically by checking whether the heuristic
flow allocator obeys the energy-conservation invariant that any real
power-flow solver enforces: total injected power at a bus equals the sum of
flows on its incident lines (Kirchhoff's current-law analogue).

Real DC / AC power-flow solvers enforce this invariant numerically. If the
heuristic allocator does NOT, then the §1 bound is supported by direct
mechanical observation: the heuristic produces flows but does not balance
generation against load at the bus level.

WHAT THIS VOICE PREDICTS
========================

The heuristic flow allocator's per-bus energy balance residual is bounded
below by a non-trivial threshold (>= 0.05 normalized). A real power-flow
solver would produce a residual at numerical-noise level (< 1e-6).

  Kind:                    polyphony_within_substrate (bound defender; inverted)
  Substrate:               default 8-node grid + heuristic flow allocator
  Named residual:          per_bus_energy_balance_residual
  Predicted lower bound:   >= 0.05 (heuristic violates conservation)
  Bound under test:        PREREGISTRATION §1 row #1

KILL CONDITION (INVERTED)
=========================

  - residual < 0.05 → fail (heuristic accidentally satisfies conservation;
                            this would be a §1 bound counter-observation
                            requiring flagging-record entry — the heuristic
                            allocator may be closer to a real power-flow
                            solver than the bound text claims)
  - residual >= 0.05 → pass (heuristic visibly does not enforce conservation;
                              §1 bound #1 supported by direct measurement)

A PASS here is the project's own protection against a §1 bound violation.
A FAIL here would be informative evidence that the bound is too strict.
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np

from meta_sim.core import EDGES, N_GENS, N_LINES, LOAD_PROFILES, GEN_PROFILES
from meta_sim.meta import load_flow_step


# ===========================================================================
# §3.1 — Standard five-field unit
# ===========================================================================

VOICE_NAME = "bound_defender_1_allocator_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "default_8_node_grid_with_heuristic_flow_allocator",
    "named_residual": "per_bus_energy_balance_residual",
    "predicted_value_lower_bound": 0.05,
    "verdict_inversion": True,
    "bound_under_test": (
        "PREREGISTRATION §1 row #1 — the project will NOT claim the heuristic "
        "flow allocator is a DC/AC/EMT/transient-stability/protection solver."
    ),
}

KILL_CONDITION = {
    "metric": "max_per_bus_energy_balance_residual_normalized",
    "rule": (
        "pass if residual >= 0.05 (heuristic visibly does not enforce conservation; "
        "bound #1 supported by direct measurement), fail if residual < 0.05 "
        "(heuristic accidentally satisfies conservation; bound counter-observation "
        "requiring flagging-record entry per §1 bound-crossing protocol)"
    ),
    "rationale": (
        "Energy conservation is the defining numerical property of any real "
        "power-flow solver. If the heuristic allocator does not enforce it, "
        "the §1 bound #1 is supported by direct mechanical observation, not by "
        "rhetorical assertion. The verdict logic is inverted relative to "
        "standard polyphony voices: pass protects the bound, fail produces "
        "evidence that the bound text may be too strict and a v2 bound "
        "revision would be in scope under §1 expansion-permitted discipline."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/bound_defender_1_allocator_v1.py",
    "source_file": "examples/voices/bound_defender_1_allocator_v1.py",
    "input_parameters": {
        "test_profile_names": ["peak", "off_peak", "mixed", "spike"],
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Per-bus energy balance computation
# ===========================================================================

def per_bus_balance_residual(load_name: str, gen_name: str) -> float:
    """Compute the maximum per-bus energy-balance residual under the heuristic
    flow allocator for a given (load, gen) profile pair.

    For each bus, residual = | injected_power - sum_of_incident_line_flows |,
    normalized by the bus's injected power. The maximum across all buses is
    returned. A real power-flow solver would produce residuals at numerical-
    noise level (< 1e-6); the heuristic does not enforce conservation."""
    loads = LOAD_PROFILES[load_name]
    gens = GEN_PROFILES[gen_name]
    external_input = np.concatenate([loads, gens])

    line_flows = load_flow_step(np.zeros(N_LINES), external_input)
    # Un-normalize back to MW for balance computation (load_flow_step normalizes
    # by DEFAULT_LINE_CAPACITY = 100).
    line_flows_mw = line_flows * 100.0

    n_nodes = N_GENS + len(loads)
    incident_flow_sums = np.zeros(n_nodes)
    for line_idx, (u, v) in enumerate(EDGES):
        incident_flow_sums[u] += line_flows_mw[line_idx]
        incident_flow_sums[v] += line_flows_mw[line_idx]

    injected = np.zeros(n_nodes)
    for i in range(N_GENS):
        injected[i] = gens[i]
    for i in range(len(loads)):
        injected[N_GENS + i] = -loads[i]

    residuals = []
    for i in range(n_nodes):
        denom = max(abs(injected[i]), 1e-6)
        residuals.append(abs(injected[i] - incident_flow_sums[i]) / denom)
    return float(max(residuals))


def run_balance_check() -> list[dict]:
    profile_names = RUN_PROTOCOL["input_parameters"]["test_profile_names"]
    return [
        {
            "profile_pair": f"{name}/{name}",
            "max_residual": per_bus_balance_residual(name, name),
        }
        for name in profile_names
    ]


def compute_verdict(scenario_summaries: list[dict]) -> dict:
    max_residuals = [s["max_residual"] for s in scenario_summaries]
    worst = max(max_residuals)
    best = min(max_residuals)
    lower_bound = PREDICTION["predicted_value_lower_bound"]

    if best >= lower_bound:
        verdict = "pass"
        outcome = "bound_supported_residual_above_floor_across_all_scenarios"
        rationale = (
            f"Best-case per-bus energy-balance residual {best:.4f} (worst {worst:.4f}) "
            f"is at or above the predicted floor {lower_bound:.4f} across all tested "
            f"profile pairs. The heuristic flow allocator visibly does not enforce "
            f"the conservation invariant a real DC/AC power-flow solver would. "
            f"§1 bound #1 supported by direct measurement; voice PASSes its inverted "
            f"kill condition."
        )
    elif worst < lower_bound:
        verdict = "fail"
        outcome = "bound_counter_observation_residual_below_floor"
        rationale = (
            f"Worst-case residual {worst:.4f} is below the predicted floor "
            f"{lower_bound:.4f} for all scenarios. The heuristic allocator may be "
            f"closer to enforcing conservation than the §1 bound text claims. This "
            f"is a §1 bound counter-observation requiring flagging-record entry. "
            f"v2 of this voice or the bound text itself should be revisited."
        )
    else:
        verdict = "partial"
        outcome = "mixed_residual_at_floor"
        rationale = (
            f"Some scenarios (best {best:.4f}) sit below the predicted floor "
            f"{lower_bound:.4f} while others (worst {worst:.4f}) sit above. The "
            f"heuristic's conservation behavior is profile-dependent. This is "
            f"partial bound support and warrants a v2 voice with tighter "
            f"per-profile rules."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "worst_residual": worst,
        "best_residual": best,
        "predicted_lower_bound": lower_bound,
        "scenario_summaries": scenario_summaries,
        "bound_under_test": PREDICTION["bound_under_test"],
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def emit_sidecar(verdict: dict, output_path: str) -> str:
    unit = {
        "voice_name": VOICE_NAME,
        "prediction": PREDICTION,
        "kill_condition": KILL_CONDITION,
        "run_protocol": RUN_PROTOCOL,
        "verdict": verdict,
    }
    canonical = json.dumps(
        {k: v for k, v in unit.items() if k != "verdict"},
        sort_keys=True,
        separators=(",", ":"),
    )
    unit["sidecar_sha256_pre_verdict"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with open(output_path, "w") as f:
        json.dump(unit, f, indent=2)
    return output_path


def main():
    print("=" * 72)
    print(f"voice unit: {VOICE_NAME}  (kind: polyphony, bound defender, inverted)")
    print(f"under test: PREREGISTRATION §1 bound #1 (heuristic allocator is not a power-flow solver)")
    print("=" * 72)
    summaries = run_balance_check()
    for s in summaries:
        print(f"  profile_pair={s['profile_pair']:>20s}  max_per_bus_residual={s['max_residual']:.4f}")
    print("-" * 72)
    verdict = compute_verdict(summaries)
    print(f"  worst residual:        {verdict['worst_residual']:.4f}")
    print(f"  best residual:         {verdict['best_residual']:.4f}")
    print(f"  predicted floor:       {verdict['predicted_lower_bound']:.4f}")
    print(f"  verdict:               {verdict['verdict'].upper()}  ({verdict['outcome_category']})")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
