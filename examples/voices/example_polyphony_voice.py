"""
example_polyphony_voice.py — reference implementation of a §3.1 voice unit.

This file is a working example of the per-voice unit template defined in §3.1 of
the project's PREREGISTRATION.md. It demonstrates a polyphony voice (a voice added
within a single substrate; see §3.2) with all five required fields and a runnable
verdict computation.

External contributors authoring their own voice for the registry should structure
their voice the same way: a Python module that defines the five fields at module
scope and computes the verdict in a single function that depends only on the run
output and the kill condition.

WHAT THIS VOICE PREDICTS
========================

The base power_grid_sim.py cycle_walk on the rotating-load-profile station set
produces a cycle_residual of approximately −0.0465. This voice predicts that adding
a "demand-response" polyphony voice — modeling load shedding under high stress —
will reduce the unsigned cycle_residual on the same station set by at least 30%.

KILL CONDITION
==============

If the demand-response voice's run, on the canonical station set, produces a
cycle_residual whose unsigned magnitude is greater than 70% of the baseline
(i.e., greater than 0.0326), the voice has failed to capture the predicted
residual. The voice enters the null-voice ledger per §3.4 and stays on record.

This is a worked example. The numbers are simulated to demonstrate the protocol;
they do not constitute a claim about real-world demand-response effects on real
grids. See §1 honesty bounds for the project's scope.
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

# Field 1: voice name (fixed at predict-step commit; not revised by subsequent commits)
VOICE_NAME = "demand_response_polyphony_v1"

# Field 2: predicted residual coupling (numerical bound on what the voice will report)
PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "8node_dc_grid",
    "named_residual": "unsigned_cycle_residual_on_rotating_load_profile_station_set",
    "baseline_value": 0.0465,
    "predicted_value_upper_bound": 0.0326,  # 70% of baseline; voice passes if observed value is at or below this
    "predicted_reduction_floor": 0.30,       # voice predicts at least a 30% reduction
}

# Field 3: kill condition (testable from run output alone)
KILL_CONDITION = {
    "metric": "unsigned_cycle_residual",
    "threshold": 0.0326,
    "rule": "fail if observed metric > threshold",
    "rationale": (
        "The voice claims to reduce the named residual by at least 30%. "
        "Failure to meet that threshold falsifies the prediction. The threshold "
        "is computable from the voice's run output alone, with no external "
        "reinterpretation required."
    ),
}

# Field 4: run protocol (literal invocation that produces the verdict)
RUN_PROTOCOL = {
    "entry_point": "python examples/voices/example_polyphony_voice.py",
    "source_file": "examples/voices/example_polyphony_voice.py",
    "input_parameters": {
        "station_set": "default rotating-load-profile (5 stations: peak, off_peak, mixed, spike, peak)",
        "demand_response_factor": 0.45,
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Voice implementation (the substrate modification this voice contributes)
# ===========================================================================

def apply_demand_response(line_flows: np.ndarray, demand_response_factor: float) -> np.ndarray:
    """Apply a simple demand-response model: when any line exceeds 0.7 utilization,
    shed demand uniformly across the grid by `demand_response_factor` of the excess.

    This is the within-substrate addition the voice contributes. A real demand-response
    voice would be richer; this version is the minimal model that exercises the
    protocol end-to-end.
    """
    excess = np.clip(line_flows - 0.7, 0.0, None)
    if excess.max() <= 0:
        return line_flows
    shedding = demand_response_factor * excess.mean()
    return np.clip(line_flows - shedding, 0.0, None)


def cycle_walk_with_voice(seed: int = 42) -> float:
    """Run the canonical rotating-load-profile cycle walk with the demand-response
    voice applied at each station. Returns the unsigned cycle_residual on the
    voice-modified station fingerprints.
    """
    from power_grid_sim import power_flow, GridStation

    stations = [
        GridStation("peak", "off_peak", 0.3),
        GridStation("off_peak", "mixed", 0.3),
        GridStation("mixed", "spike", 0.3),
        GridStation("spike", "peak", 0.3),
        GridStation("peak", "off_peak", 0.3),
    ]

    fingerprints = []
    for station in stations:
        flows = power_flow(station.profile_a, station.profile_b, station.mix)
        flows_after_dr = apply_demand_response(flows, RUN_PROTOCOL["input_parameters"]["demand_response_factor"])
        bins = np.histogram(flows_after_dr, bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.5])[0]
        fingerprints.append((*[int(b) for b in bins], round(float(flows_after_dr.max()), 3)))

    step_distances = [
        float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fingerprints[i], fingerprints[i + 1]))))
        for i in range(len(fingerprints) - 1)
    ]
    home_step = float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fingerprints[-1], fingerprints[0]))))
    mean_step = float(np.mean(step_distances)) if step_distances else 0.0
    return abs(home_step - mean_step)


# ===========================================================================
# Field 5: verdict (computed mechanically from run output against kill condition)
# ===========================================================================

def compute_verdict(observed_unsigned_residual: float) -> dict:
    """Mechanically compute pass / fail / partial from the run output against the
    pre-committed kill condition. No post-hoc interpretation.
    """
    threshold = KILL_CONDITION["threshold"]
    if observed_unsigned_residual <= threshold:
        verdict = "pass"
        reduction = (PREDICTION["baseline_value"] - observed_unsigned_residual) / PREDICTION["baseline_value"]
        rationale = (
            f"Observed unsigned cycle_residual {observed_unsigned_residual:.4f} "
            f"is at or below the pre-committed threshold {threshold:.4f}. "
            f"Reduction from baseline: {reduction:.1%}."
        )
    else:
        verdict = "fail"
        rationale = (
            f"Observed unsigned cycle_residual {observed_unsigned_residual:.4f} "
            f"exceeds the pre-committed threshold {threshold:.4f}. "
            f"Voice enters the null-voice ledger per §3.4 and stays on record."
        )

    return {
        "verdict": verdict,
        "observed_value": observed_unsigned_residual,
        "threshold": threshold,
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


# ===========================================================================
# Sidecar JSON — the five-field unit serialized for the registry per §4.1
# ===========================================================================

def emit_sidecar(verdict: dict, output_path: str) -> str:
    """Emit the signed JSON sidecar carrying the full five-field unit + run output.

    The sidecar's SHA-256 hash is computed over the canonical serialization of the
    voice's five fields (excluding the verdict-timestamp field) and recorded
    alongside the sidecar. This establishes that the predict, kill-condition, and
    run-protocol fields preceded the verdict.
    """
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


# ===========================================================================
# Main: run the voice end-to-end and emit the sidecar
# ===========================================================================

def main():
    print("=" * 72)
    print(f"voice unit: {VOICE_NAME}")
    print("=" * 72)
    print(f"prediction:     reduce unsigned cycle_residual by ≥ 30% (baseline {PREDICTION['baseline_value']:.4f})")
    print(f"kill condition: fail if observed > {KILL_CONDITION['threshold']:.4f}")
    print(f"run:            {RUN_PROTOCOL['entry_point']}")
    print()
    print("running...")
    observed = cycle_walk_with_voice(seed=RUN_PROTOCOL["input_parameters"]["random_seed"])
    print(f"  observed unsigned cycle_residual: {observed:.4f}")
    verdict = compute_verdict(observed)
    print(f"  verdict: {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    print()

    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
