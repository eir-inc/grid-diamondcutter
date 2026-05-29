# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
renewable_mix_threshold_polyphony_v1.py — §3.1 voice unit.

This voice addresses PREREGISTRATION.md §0's central question directly: whether
the simulation can identify a *threshold-class cascade* in a substrate where one
exists. The voice perturbs the 8-node DC grid substrate with a synthetic
renewable-mix parameter that injects a non-linear inflection in dispatch
behavior, then asks whether the methodology's cycle-walk recovers the threshold.

This is a SELF-TEST of the methodology, not a claim about real grids. The
renewable-mix model is synthetic by construction; the substrate inflection is
deliberately placed at ρ ≈ 0.40 for the methodology to find or fail to find.
See PREREGISTRATION.md §1 (honesty bounds) for the project's scope.

WHAT THIS VOICE PREDICTS
========================

When the substrate is perturbed by a renewable-fraction parameter ρ ∈ [0, 1],
the cycle_residual measured by the same canonical station set exhibits a
piecewise-linear trajectory with an inflection in [0.30, 0.60]. Specifically:

- A piecewise-linear fit (two segments with one breakpoint) explains the
  sweep at least 20% better than a single-segment linear fit, measured by
  residual sum of squares.
- The recovered breakpoint lies in [0.30, 0.60].

Either result failing falsifies the prediction.

KILL CONDITION
==============

The voice fails if ANY of:

1. piecewise_rss / linear_rss > 0.80 (the piecewise fit does not improve on
   the linear fit by at least 20%); OR
2. the recovered breakpoint is outside [0.30, 0.60].

Both conditions are computable from the run output alone.

This is a worked voice testing the methodology's threshold-recovery capability
on a synthetic substrate with a known inflection. See §1 honesty bounds.
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

# Allow running this module from the repo root or from examples/voices/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np


# ===========================================================================
# §3.1 — The per-voice unit (five required fields)
# ===========================================================================

# Field 1: voice name
VOICE_NAME = "renewable_mix_threshold_polyphony_v1"

# Field 2: predicted residual coupling
PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "8node_dc_grid",
    "named_residual": "threshold_class_cascade_in_renewable_mix_sweep",
    "predicted_breakpoint_range": [0.30, 0.60],
    "predicted_piecewise_improvement_floor": 0.20,
    "rationale": (
        "PREREGISTRATION §0 names a 'threshold-class cascade' as the phenomenon "
        "the simulation is built to test for. This voice injects a known "
        "non-linear inflection in the substrate at ρ ≈ 0.40 and asks whether "
        "the methodology recovers it. If the methodology cannot recover a "
        "deliberately-placed threshold in its own substrate, it cannot be "
        "trusted to find a threshold elsewhere."
    ),
}

# Field 3: kill condition
KILL_CONDITION = {
    "metric": "threshold_recovery_validity",
    "rule": (
        "fail if piecewise_rss / linear_rss > 0.80 (no piecewise improvement), "
        "fail if recovered_breakpoint < 0.30 or recovered_breakpoint > 0.60 "
        "(recovery outside predicted range)"
    ),
    "rationale": (
        "The composite metric `threshold_recovery_validity` is decomposable into "
        "two underlying numerical checks, both computable from the run output "
        "alone with no post-hoc reinterpretation. The piecewise-improvement "
        "ratio tests whether a threshold-class shape fits the sweep better than "
        "linear. The breakpoint-range test rejects spurious recoveries outside "
        "the predicted window. A voice that passes both has recovered a known "
        "threshold; a voice that fails either has not."
    ),
}

# Field 4: run protocol
RUN_PROTOCOL = {
    "entry_point": "python examples/voices/renewable_mix_threshold_polyphony_v1.py",
    "source_file": "examples/voices/renewable_mix_threshold_polyphony_v1.py",
    "input_parameters": {
        "station_set": "default rotating-load-profile (5 stations: peak, off_peak, mixed, spike, peak)",
        "renewable_fraction_sweep": [round(x, 2) for x in np.linspace(0.0, 1.0, 11).tolist()],
        "synthetic_threshold_position": 0.40,
        "synthetic_threshold_strength": 1.5,
        "random_seed": 137,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Voice implementation (the substrate modification)
# ===========================================================================

# Imports from the package's grid substrate; the voice operates over the
# existing reach/cost/lifetime/cycle_walk contract by perturbing generator
# profiles before each cycle walk.
from power_grid_sim import GEN_PROFILES, cycle_walk, GridStation


def perturb_gen_profile_for_renewable_mix(
    profile_name: str, rho: float, threshold: float = 0.40, strength: float = 1.5
) -> np.ndarray:
    """Return a perturbed generator-profile vector for a given renewable
    fraction ρ. Synthetic model:

      - Generators 0 and 1 are "renewable" — their dispatched output scales
        with a capacity-factor C(ρ) that depends on ρ.
      - Generators 2 and 3 are "conventional" — they ramp to cover the gap.
      - Below the threshold, C(ρ) = ρ (linear participation).
      - Above the threshold, C(ρ) = threshold + strength * (ρ - threshold),
        injecting a piecewise-linear inflection at ρ = threshold.

    The substrate's own dispatch then renders this perturbation into
    line utilizations through the unmodified power_flow path.
    """
    base = GEN_PROFILES[profile_name].copy()
    if rho < threshold:
        c_rho = rho
    else:
        c_rho = threshold + strength * (rho - threshold)
    # renewable generators 0,1: scaled by C(ρ); conventional 2,3: scaled by (1 - ρ)
    renewable_scale = max(0.0, min(1.0, c_rho))
    conventional_scale = max(0.0, 1.0 - rho)
    base[0] *= renewable_scale
    base[1] *= renewable_scale
    base[2] *= conventional_scale
    base[3] *= conventional_scale
    return base


def cycle_walk_at_renewable_fraction(rho: float, seed: int = 137) -> float:
    """Run a cycle walk at a fixed renewable fraction ρ; return signed cycle_residual."""
    np.random.seed(seed)
    saved = {k: v.copy() for k, v in GEN_PROFILES.items()}
    try:
        for name in GEN_PROFILES:
            GEN_PROFILES[name] = perturb_gen_profile_for_renewable_mix(
                name, rho,
                threshold=RUN_PROTOCOL["input_parameters"]["synthetic_threshold_position"],
                strength=RUN_PROTOCOL["input_parameters"]["synthetic_threshold_strength"],
            )
        stations = [
            GridStation("peak", "off_peak", 0.5),
            GridStation("off_peak", "mixed", 0.5),
            GridStation("mixed", "spike", 0.5),
            GridStation("spike", "peak", 0.5),
            GridStation("peak", "off_peak", 0.5),
        ]
        result = cycle_walk(stations)
        return float(result["cycle_residual"])
    finally:
        for k, v in saved.items():
            GEN_PROFILES[k] = v


def fit_linear(rhos: np.ndarray, residuals: np.ndarray) -> tuple:
    """Linear fit; return (slope, intercept, rss)."""
    n = len(rhos)
    slope, intercept = np.polyfit(rhos, residuals, 1)
    predicted = slope * rhos + intercept
    rss = float(((residuals - predicted) ** 2).sum())
    return float(slope), float(intercept), rss


def fit_piecewise_two_segment(rhos: np.ndarray, residuals: np.ndarray) -> tuple:
    """Brute-force breakpoint search across all interior points;
    return (best_breakpoint, rss_at_best_breakpoint)."""
    best_bp = None
    best_rss = float("inf")
    for i in range(2, len(rhos) - 2):
        bp = float(rhos[i])
        # fit left segment + right segment
        left_x, left_y = rhos[: i + 1], residuals[: i + 1]
        right_x, right_y = rhos[i:], residuals[i:]
        ls, li = np.polyfit(left_x, left_y, 1)
        rs, ri = np.polyfit(right_x, right_y, 1)
        left_predicted = ls * left_x + li
        right_predicted = rs * right_x + ri
        rss = float(((left_y - left_predicted) ** 2).sum() + ((right_y - right_predicted) ** 2).sum())
        if rss < best_rss:
            best_rss = rss
            best_bp = bp
    return best_bp, best_rss


def run_voice() -> dict:
    """Sweep ρ across the pre-committed range, compute cycle_residual at each,
    fit linear vs piecewise, return the comparison metrics."""
    rhos = np.array(RUN_PROTOCOL["input_parameters"]["renewable_fraction_sweep"])
    residuals = np.array([
        cycle_walk_at_renewable_fraction(float(r), seed=RUN_PROTOCOL["input_parameters"]["random_seed"])
        for r in rhos
    ])

    _, _, linear_rss = fit_linear(rhos, residuals)
    breakpoint, piecewise_rss = fit_piecewise_two_segment(rhos, residuals)
    piecewise_rss_ratio = piecewise_rss / linear_rss if linear_rss > 0 else float("inf")

    return {
        "sweep_rhos": [float(r) for r in rhos],
        "sweep_cycle_residuals": [float(r) for r in residuals],
        "linear_rss": float(linear_rss),
        "piecewise_rss": float(piecewise_rss),
        "piecewise_rss_ratio": float(piecewise_rss_ratio),
        "recovered_breakpoint": float(breakpoint) if breakpoint is not None else None,
    }


# ===========================================================================
# Field 5: verdict (computed mechanically from run output against kill condition)
# ===========================================================================

def compute_verdict(run_output: dict) -> dict:
    """Mechanically compute pass / fail from the run output against the
    pre-committed kill condition. No post-hoc interpretation."""
    bp = run_output["recovered_breakpoint"]
    ratio = run_output["piecewise_rss_ratio"]
    bp_lo, bp_hi = PREDICTION["predicted_breakpoint_range"]
    ratio_max = 1.0 - PREDICTION["predicted_piecewise_improvement_floor"]   # 0.80 for floor 0.20

    fails = []
    if ratio > ratio_max:
        fails.append(
            f"piecewise_rss_ratio {ratio:.4f} > {ratio_max:.4f} "
            f"(piecewise fit did not improve on linear by ≥ {PREDICTION['predicted_piecewise_improvement_floor']:.0%})"
        )
    if bp is None or bp < bp_lo or bp > bp_hi:
        fails.append(
            f"recovered breakpoint {bp} outside predicted range [{bp_lo}, {bp_hi}]"
        )

    if not fails:
        verdict = "pass"
        rationale = (
            f"Recovered breakpoint {bp:.3f} ∈ [{bp_lo}, {bp_hi}] AND "
            f"piecewise_rss_ratio {ratio:.4f} ≤ {ratio_max:.4f}. "
            f"The methodology recovered the synthetic threshold."
        )
    else:
        verdict = "fail"
        rationale = (
            "Voice enters the null-voice ledger per §3.4. Failures: "
            + " ; ".join(fails)
        )

    return {
        "verdict": verdict,
        "recovered_breakpoint": bp,
        "piecewise_rss_ratio": ratio,
        "linear_rss": run_output["linear_rss"],
        "piecewise_rss": run_output["piecewise_rss"],
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


# ===========================================================================
# Sidecar JSON — the five-field unit serialized for the registry per §4.1
# ===========================================================================

def emit_sidecar(verdict: dict, sweep_output: dict, output_path: str) -> str:
    """Emit the signed JSON sidecar carrying the full five-field unit + run output."""
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


# ===========================================================================
# Main: run the voice end-to-end and emit the sidecar
# ===========================================================================

def main():
    print("=" * 72)
    print(f"voice unit: {VOICE_NAME}")
    print("=" * 72)
    print(f"prediction:     piecewise_rss_ratio ≤ 0.80 AND breakpoint ∈ {PREDICTION['predicted_breakpoint_range']}")
    print(f"kill conditions:")
    for rule in KILL_CONDITION["rules"]:
        print(f"  - {rule}")
    print(f"run:            {RUN_PROTOCOL['entry_point']}")
    print()
    print("running renewable-mix sweep...")
    sweep_output = run_voice()
    for rho, resid in zip(sweep_output["sweep_rhos"], sweep_output["sweep_cycle_residuals"]):
        print(f"  ρ={rho:.2f}  cycle_residual={resid:+.4f}")
    print(f"  linear_rss:    {sweep_output['linear_rss']:.4f}")
    print(f"  piecewise_rss: {sweep_output['piecewise_rss']:.4f}")
    print(f"  ratio:         {sweep_output['piecewise_rss_ratio']:.4f}")
    print(f"  recovered breakpoint: {sweep_output['recovered_breakpoint']}")
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
