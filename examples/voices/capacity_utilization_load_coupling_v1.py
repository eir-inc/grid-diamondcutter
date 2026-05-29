# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
capacity_utilization_load_coupling_v1.py — §3.1 voice unit.

Coupling voice (§3.2 second axis). Tests the substrate's physical-direction
sanity: under uniform load scale-up, the maximum line utilization observed in
the cycle walk should rise. This is a basic sanity check on the substrate's
dispatch path; if it fails, more sophisticated voices that depend on
substrate-physics are not on stable ground.

The voice complements subhuti's `capacity_scaling_monotonicity_v1`
(uniform-capacity-up should reduce residual) by testing the dual direction:
uniform-load-up should raise observed utilization. Both should hold if the
substrate's dispatch logic is reasonable.
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

VOICE_NAME = "capacity_utilization_load_coupling_v1"

# Field 2: predicted residual coupling — COUPLING discipline (§3.2):
# direction + magnitude range + null direction all pre-committed.
PREDICTION = {
    "kind": "coupling_cross_substrate",
    "substrate_a": "load_profile_scale (system-wide load multiplier α ∈ [0.5, 2.0])",
    "substrate_b": "max_line_utilization observed across cycle-walk stations",
    "named_residual": "load_alpha_drives_observed_max_utilization",
    "predicted_direction": "positive: higher α → higher max_line_utilization",
    "predicted_magnitude_range": [0.10, 0.60],   # slope range in unit-of-utilization per unit-of-α
    "null_direction": "zero or negative slope (no link / reversed direction)",
    "rationale": (
        "Physical-direction sanity check on the substrate's dispatch path. "
        "If uniform load scale-up does not raise observed maximum line "
        "utilization, the substrate's dispatch is not behaving as a grid "
        "should. Complement to capacity_scaling_monotonicity_v1 (PR #6), "
        "which tests the dual: uniform-capacity-up should reduce cycle_residual. "
        "Both should hold under reasonable dispatch."
    ),
}

# Field 3: kill condition (single composite metric per the contract)
KILL_CONDITION = {
    "metric": "linear_fit_slope_of_max_utilization_vs_load_scale",
    "predicted_range": [0.10, 0.60],
    "rule": (
        "fail if slope < 0.10 (no link / weak link below predicted floor), "
        "fail if slope > 0.60 (over-prediction or numerical instability), "
        "fail if slope < 0 (reversed direction = null direction realized)"
    ),
    "rationale": (
        "All three failure outcomes are testable from the run output alone. "
        "Below-floor / above-ceiling / wrong-sign cover the three honest "
        "ways the prediction can be wrong; the null direction is named "
        "explicitly so its realization is a registry-acceptable null per §3.4."
    ),
}

# Field 4: run protocol
RUN_PROTOCOL = {
    "entry_point": "python examples/voices/capacity_utilization_load_coupling_v1.py",
    "source_file": "examples/voices/capacity_utilization_load_coupling_v1.py",
    "input_parameters": {
        "load_scale_sweep": [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0],
        "station_set": "default rotating-load-profile (5 stations: peak, off_peak, mixed, spike, peak)",
        "random_seed": 271,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Voice implementation
# ===========================================================================

from power_grid_sim import LOAD_PROFILES, cycle_walk, GridStation, power_flow


def scale_load_profiles(alpha: float) -> dict:
    """Return a copy of LOAD_PROFILES with every profile scaled by α."""
    return {name: profile * alpha for name, profile in LOAD_PROFILES.items()}


def max_utilization_at_load_scale(alpha: float, seed: int = 271) -> float:
    """Run the cycle walk at a fixed load scale α; return the maximum
    line-utilization observed across all stations."""
    np.random.seed(seed)
    saved = {k: v.copy() for k, v in LOAD_PROFILES.items()}
    try:
        scaled = scale_load_profiles(alpha)
        for name in LOAD_PROFILES:
            LOAD_PROFILES[name] = scaled[name]
        stations = [
            GridStation("peak", "off_peak", 0.5),
            GridStation("off_peak", "mixed", 0.5),
            GridStation("mixed", "spike", 0.5),
            GridStation("spike", "peak", 0.5),
            GridStation("peak", "off_peak", 0.5),
        ]
        # observe max line utilization across all station evaluations
        max_util = 0.0
        for s in stations:
            flows = power_flow(s.profile_a, s.profile_b, s.mix)
            m = float(flows.max())
            if m > max_util:
                max_util = m
        return max_util
    finally:
        for k, v in saved.items():
            LOAD_PROFILES[k] = v


def fit_linear_slope(alphas: np.ndarray, max_utils: np.ndarray) -> tuple:
    """Linear fit; return (slope, intercept)."""
    slope, intercept = np.polyfit(alphas, max_utils, 1)
    return float(slope), float(intercept)


def run_voice() -> dict:
    alphas = np.array(RUN_PROTOCOL["input_parameters"]["load_scale_sweep"])
    max_utils = np.array([
        max_utilization_at_load_scale(float(a), seed=RUN_PROTOCOL["input_parameters"]["random_seed"])
        for a in alphas
    ])
    slope, intercept = fit_linear_slope(alphas, max_utils)
    return {
        "load_scales": [float(a) for a in alphas],
        "max_utilizations": [float(u) for u in max_utils],
        "linear_fit_slope": float(slope),
        "linear_fit_intercept": float(intercept),
    }


# ===========================================================================
# Field 5: verdict
# ===========================================================================

def compute_verdict(run_output: dict) -> dict:
    slope = run_output["linear_fit_slope"]
    lo, hi = PREDICTION["predicted_magnitude_range"]
    fails = []
    if slope < 0:
        fails.append(f"slope {slope:.4f} < 0 — null direction realized (reversed)")
    elif slope < lo:
        fails.append(f"slope {slope:.4f} < {lo} — below predicted floor (weak/no link)")
    elif slope > hi:
        fails.append(f"slope {slope:.4f} > {hi} — above predicted ceiling (over-prediction)")

    if not fails:
        verdict = "pass"
        rationale = (
            f"Linear fit slope {slope:.4f} ∈ [{lo}, {hi}] — load scale-up "
            f"raises observed max_utilization in the predicted direction "
            f"with magnitude in the pre-committed range."
        )
    else:
        verdict = "fail"
        rationale = (
            "Voice enters the null-voice ledger per §3.4. Failures: "
            + " ; ".join(fails)
        )

    return {
        "verdict": verdict,
        "slope": slope,
        "predicted_range": [lo, hi],
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
    print(f"prediction:     slope of max_utilization vs load_scale ∈ {PREDICTION['predicted_magnitude_range']}")
    print(f"kill rule:      {KILL_CONDITION['rule']}")
    print(f"run:            {RUN_PROTOCOL['entry_point']}")
    print()
    print("running load-scale sweep...")
    sweep_output = run_voice()
    for alpha, util in zip(sweep_output["load_scales"], sweep_output["max_utilizations"]):
        print(f"  α={alpha:.2f}  max_utilization={util:.4f}")
    print(f"  linear slope: {sweep_output['linear_fit_slope']:.4f}")
    print(f"  intercept:    {sweep_output['linear_fit_intercept']:.4f}")
    print()
    verdict = compute_verdict(sweep_output)
    print(f"  verdict: {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    print()

    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sweep_output, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
