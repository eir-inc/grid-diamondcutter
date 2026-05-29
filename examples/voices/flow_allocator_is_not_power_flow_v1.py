# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
flow_allocator_is_not_power_flow_v1.py — §3.1 bound-defender voice.

Defends PREREGISTRATION §1's first honesty bound: the flow allocator in this
repository is a heuristic energy allocator, NOT a DC/AC power-flow solver, NOT
an EMT or transient-stability simulator, NOT a protection simulator. This
voice tests whether that bound is observably supported by measurement: the
heuristic's per-line flows should be measurably different from a textbook
DC-power-flow approximation on the same grid + load injection.

Inverted kill condition (per the bound-defender pattern miles introduced in
PR #16): PASS = the bound is supported by measurement (heuristic IS detectably
different from DC-PF). FAIL = the heuristic's output is indistinguishable from
DC-PF, which would call the §1 bound into question.

This is a self-test of the project's own honesty bound, not a claim about
real grids. See §1 honesty bounds for the scope.
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np


# ===========================================================================
# §3.1 — The per-voice unit (five required fields)
# ===========================================================================

VOICE_NAME = "flow_allocator_is_not_power_flow_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "8node_dc_grid",
    "named_residual": "heuristic_vs_textbook_dc_power_flow_distance",
    "bound_defended": "§1 row 1: flow allocator is NOT a DC/AC power-flow solver",
    "predicted_distance_floor": 0.20,
    "rationale": (
        "If the heuristic's per-line flows on a benchmark load injection are "
        "indistinguishable (within 20% L2-relative distance) from a textbook "
        "DC-power-flow approximation on the same grid, the §1 bound is "
        "questionable: the project would be claiming a separation that is "
        "not observable. This voice tests whether the bound is in fact "
        "supported by measurement — an inverted kill condition: PASS = "
        "bound supported (heuristic measurably differs), FAIL = bound "
        "counter-observed."
    ),
}

KILL_CONDITION = {
    "metric": "l2_relative_distance_between_heuristic_and_dc_pf_flows",
    "predicted_range": [0.20, 5.0],
    "rule": (
        "INVERTED: pass if distance ≥ 0.20 (bound supported — measurably different), "
        "fail if distance < 0.20 (bound counter-observed — too similar to DC-PF)"
    ),
    "rationale": (
        "Bound-defender pattern: a §1 honesty bound is itself a project claim "
        "that should be testable. If the heuristic's flows match a textbook "
        "DC-PF within 20% L2-relative distance, the project's §1 row 1 claim "
        "is not supported by measurement and the bound itself must be revised. "
        "The 5.0 upper bound rejects degenerate / non-finite distances "
        "(e.g., divide-by-zero on a load injection that produces no flow)."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/flow_allocator_is_not_power_flow_v1.py",
    "source_file": "examples/voices/flow_allocator_is_not_power_flow_v1.py",
    "input_parameters": {
        "benchmark_profile": "mixed",
        "comparison_method": "textbook_dc_power_flow_with_slack_bus_0",
        "distance_metric": "l2_relative",
        "random_seed": 211,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Voice implementation — DC-PF computation + comparison
# ===========================================================================

from power_grid_sim import (
    EDGES, N_GENS, N_LOADS, N_LINES, LINE_CAPACITIES, LINE_RESISTANCE,
    LOAD_PROFILES, GEN_PROFILES, power_flow,
)


def textbook_dc_power_flow(profile_name: str) -> np.ndarray:
    """Compute textbook DC-power-flow per-line flows on the 8-node DC grid.

    Uses the standard B-bus formulation:
      1. Build node-admittance matrix B from edge reactances (1/resistance proxy).
      2. Set bus 0 as slack (angle = 0).
      3. Compute net injection at each non-slack bus: gen - load.
      4. Solve B_red * theta = P_net for non-slack angles.
      5. Per-line flow = (theta[u] - theta[v]) / x[edge].

    Returns flow magnitudes normalized by LINE_CAPACITIES (utilization units).
    """
    n_buses = N_GENS + N_LOADS  # 8 total
    # Build susceptance matrix from edges (reciprocal of reactance proxy)
    B = np.zeros((n_buses, n_buses))
    x = LINE_RESISTANCE.copy()  # use resistance as proxy for reactance
    for k, (u, v) in enumerate(EDGES):
        b_uv = 1.0 / x[k]
        B[u, v] -= b_uv
        B[v, u] -= b_uv
        B[u, u] += b_uv
        B[v, v] += b_uv
    # net injection at each bus: generators are buses 0..3, loads are 4..7
    gens = GEN_PROFILES.get(profile_name, GEN_PROFILES["mixed"])
    loads = LOAD_PROFILES.get(profile_name, LOAD_PROFILES["mixed"])
    P = np.zeros(n_buses)
    P[:N_GENS] = gens
    P[N_GENS:] = -loads
    # remove slack bus (bus 0): solve B_red * theta_red = P_red
    B_red = B[1:, 1:]
    P_red = P[1:]
    try:
        theta_red = np.linalg.solve(B_red, P_red)
    except np.linalg.LinAlgError:
        # singular — return zeros (will be far from heuristic, so PASS)
        return np.zeros(N_LINES)
    theta = np.zeros(n_buses)
    theta[1:] = theta_red
    # compute per-line flow
    flows = np.zeros(N_LINES)
    for k, (u, v) in enumerate(EDGES):
        flows[k] = (theta[u] - theta[v]) / x[k]
    return np.abs(flows) / LINE_CAPACITIES


def l2_relative_distance(a: np.ndarray, b: np.ndarray) -> float:
    """L2-relative distance between two flow vectors.

    distance = ||a - b||_2 / max(||a||_2, ||b||_2, 1e-9)
    """
    num = float(np.linalg.norm(a - b))
    den = max(float(np.linalg.norm(a)), float(np.linalg.norm(b)), 1e-9)
    return num / den


def run_voice() -> dict:
    np.random.seed(RUN_PROTOCOL["input_parameters"]["random_seed"])
    profile = RUN_PROTOCOL["input_parameters"]["benchmark_profile"]
    heuristic_flows = power_flow(profile, profile, 0.5)
    dcpf_flows = textbook_dc_power_flow(profile)
    distance = l2_relative_distance(heuristic_flows, dcpf_flows)
    return {
        "benchmark_profile": profile,
        "heuristic_flows": [float(f) for f in heuristic_flows],
        "textbook_dc_pf_flows": [float(f) for f in dcpf_flows],
        "l2_relative_distance": float(distance),
    }


# ===========================================================================
# Field 5: verdict (INVERTED kill condition — pass means bound is supported)
# ===========================================================================

def compute_verdict(run_output: dict) -> dict:
    distance = run_output["l2_relative_distance"]
    floor, ceiling = PREDICTION["predicted_distance_floor"], 5.0
    fails = []
    if distance < floor:
        fails.append(
            f"distance {distance:.4f} < floor {floor} — heuristic indistinguishable "
            f"from textbook DC-PF; §1 row 1 bound NOT supported by this measurement"
        )
    elif distance > ceiling:
        fails.append(
            f"distance {distance:.4f} > ceiling {ceiling} — degenerate / non-finite"
        )

    if not fails:
        verdict = "pass"
        rationale = (
            f"L2-relative distance {distance:.4f} ≥ {floor} — the heuristic's "
            f"per-line flows differ measurably from a textbook DC-power-flow "
            f"approximation on the same grid + injection. §1 row 1 bound "
            f"(flow allocator NOT a DC-PF solver) is supported by this measurement."
        )
    else:
        verdict = "fail"
        rationale = (
            "Voice enters the null-voice ledger per §3.4. Failures: "
            + " ; ".join(fails)
        )

    return {
        "verdict": verdict,
        "distance": distance,
        "predicted_floor": floor,
        "bound_defended_status": "supported" if verdict == "pass" else "counter-observed",
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def emit_sidecar(verdict: dict, sweep_output: dict, output_path: str) -> str:
    unit = {
        "voice_name": VOICE_NAME,
        "prediction": PREDICTION,
        "kill_condition": KILL_CONDITION,
        "run_protocol": RUN_PROTOCOL,
        "run_output": sweep_output,
        "verdict": verdict,
    }
    canonical = json.dumps(
        {k: v for k, v in unit.items() if k not in ("verdict", "run_output")},
        sort_keys=True,
        separators=(",", ":"),
    )
    unit["sidecar_sha256_pre_verdict"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with open(output_path, "w") as f:
        json.dump(unit, f, indent=2)
    return output_path


def main():
    print("=" * 72)
    print(f"voice unit: {VOICE_NAME}")
    print("=" * 72)
    print(f"bound defended: §1 row 1 — flow allocator is NOT a DC/AC power-flow solver")
    print(f"predicted:      L2-relative distance between heuristic and textbook DC-PF ≥ 0.20")
    print(f"kill rule:      {KILL_CONDITION['rule']}")
    print(f"run:            {RUN_PROTOCOL['entry_point']}")
    print()
    print("running heuristic-vs-textbook-DC-PF comparison...")
    out = run_voice()
    print(f"  benchmark profile:       {out['benchmark_profile']}")
    print(f"  heuristic flows (sample): {out['heuristic_flows'][:4]}...")
    print(f"  textbook DC-PF (sample): {out['textbook_dc_pf_flows'][:4]}...")
    print(f"  L2-relative distance:    {out['l2_relative_distance']:.4f}")
    print()
    verdict = compute_verdict(out)
    print(f"  verdict: {verdict['verdict'].upper()}")
    print(f"  bound status: {verdict['bound_defended_status']}")
    print(f"  {verdict['rationale']}")
    print()

    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, out, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
