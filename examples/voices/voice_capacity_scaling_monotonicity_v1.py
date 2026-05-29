"""
voice_capacity_scaling_monotonicity_v1.py — registry voice.

Tests whether the unsigned cycle_residual decreases monotonically when line
capacities are uniformly scaled up. The physical interpretation: more capacity
per line → less stress per fixed load → fewer high-utilization bins → smaller
fingerprint distance step → smaller closure residual. If the measurement is
physically interpretable in that direction, scaling capacity up should never
increase cycle_residual.

Authored under PREREGISTRATION.md §3.1.
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np


VOICE_NAME = "capacity_scaling_monotonicity_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "8node_dc_grid",
    "named_residual": (
        "monotonic non-increase of unsigned cycle_residual under uniform line "
        "capacity scaling. Predict: as capacity multiplier sweeps over "
        "[0.5, 0.75, 1.0, 1.5, 2.0, 4.0], the unsigned cycle_residual is "
        "monotonically non-increasing (no scale-up step increases the residual)."
    ),
    "capacity_multipliers_swept": [0.5, 0.75, 1.0, 1.5, 2.0, 4.0],
    "predicted_monotonicity_direction": "non-increasing",
    "predicted_max_step_increase_tolerance": 0.001,
}

KILL_CONDITION = {
    "metric": "max_step_increase_in_cycle_residual_across_capacity_sweep",
    "rule": (
        "fail if any consecutive scale-up step in the capacity sweep increases "
        "the unsigned cycle_residual by more than 0.001 (absolute). "
        "Strict non-decrease tolerance is 0 with a numerical-stability margin "
        "of 0.001 to absorb floating-point and binning rounding."
    ),
    "rationale": (
        "If scaling capacity up ever increases the cycle_residual, the "
        "measurement is not monotonically interpretable in the natural "
        "physical direction. Such a finding would mean the histogram-binning "
        "fingerprint introduces non-monotonic regions in the measurement's "
        "response to a one-axis parameter sweep, which constrains "
        "interpretation."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/voice_capacity_scaling_monotonicity_v1.py",
    "source_file": "examples/voices/voice_capacity_scaling_monotonicity_v1.py",
    "input_parameters": {
        "capacity_multipliers": [0.5, 0.75, 1.0, 1.5, 2.0, 4.0],
        "station_set": "default rotating-load-profile",
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


def cycle_residual_at_capacity_multiplier(capacity_mult: float) -> float:
    from power_grid_sim import GridStation, LOAD_PROFILES, GEN_PROFILES, EDGES, N_GENS, N_LINES

    perturbed_caps = np.full(N_LINES, 100.0) * capacity_mult

    def power_flow_pert(profile_a, profile_b, mix):
        loads = (1 - mix) * LOAD_PROFILES.get(profile_a, LOAD_PROFILES["mixed"]) + \
                mix * LOAD_PROFILES.get(profile_b, LOAD_PROFILES["mixed"])
        gens = (1 - mix) * GEN_PROFILES.get(profile_a, GEN_PROFILES["mixed"]) + \
               mix * GEN_PROFILES.get(profile_b, GEN_PROFILES["mixed"])
        flows = np.zeros(N_LINES)
        for i, (u, v) in enumerate(EDGES):
            if u < N_GENS and v >= N_GENS:
                flows[i] = min(gens[u] * 0.25, loads[v - N_GENS] * 0.5)
            elif v < N_GENS and u >= N_GENS:
                flows[i] = min(gens[v] * 0.25, loads[u - N_GENS] * 0.5)
            else:
                flows[i] = 5.0
        return flows / perturbed_caps

    stations = [
        GridStation("peak", "off_peak", 0.3),
        GridStation("off_peak", "mixed", 0.3),
        GridStation("mixed", "spike", 0.3),
        GridStation("spike", "peak", 0.3),
        GridStation("peak", "off_peak", 0.3),
    ]
    fps = []
    for s in stations:
        flows = power_flow_pert(s.profile_a, s.profile_b, s.mix)
        bins = np.histogram(flows, bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.5])[0]
        fps.append((*[int(b) for b in bins], round(float(flows.max()), 3)))
    step_distances = [
        float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[i], fps[i + 1]))))
        for i in range(len(fps) - 1)
    ]
    home_step = float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[-1], fps[0]))))
    mean_step = float(np.mean(step_distances)) if step_distances else 0.0
    return abs(home_step - mean_step)


def run_capacity_sweep() -> dict:
    multipliers = RUN_PROTOCOL["input_parameters"]["capacity_multipliers"]
    residuals = [cycle_residual_at_capacity_multiplier(m) for m in multipliers]
    step_diffs = [residuals[i + 1] - residuals[i] for i in range(len(residuals) - 1)]
    return {
        "multipliers": multipliers,
        "residuals": residuals,
        "step_diffs": step_diffs,
        "max_step_increase": max(step_diffs) if step_diffs else 0.0,
    }


def compute_verdict(trial: dict) -> dict:
    threshold = PREDICTION["predicted_max_step_increase_tolerance"]
    max_inc = trial["max_step_increase"]
    if max_inc <= threshold:
        verdict = "pass"
        rationale = (
            f"Max step-increase across capacity sweep = {max_inc:+.6f}, at or below "
            f"tolerance {threshold:.4f}. cycle_residual is monotonically non-increasing "
            f"under uniform capacity scale-up across the swept range. The measurement "
            f"is physically interpretable in the natural direction at this scope."
        )
    else:
        verdict = "fail"
        rationale = (
            f"Max step-increase across capacity sweep = {max_inc:+.6f}, exceeds "
            f"tolerance {threshold:.4f}. cycle_residual is not monotonically "
            f"non-increasing under capacity scale-up; the histogram-binning "
            f"fingerprint introduces non-monotonic regions. Voice enters the "
            f"null-voice ledger per §3.4."
        )
    return {
        "verdict": verdict,
        "multipliers": trial["multipliers"],
        "residuals_per_multiplier": trial["residuals"],
        "step_diffs": trial["step_diffs"],
        "max_step_increase_observed": max_inc,
        "tolerance": threshold,
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
    print(f"voice unit: {VOICE_NAME}")
    print("=" * 72)
    print(f"prediction: cycle_residual non-increasing under capacity scale-up")
    print()
    print("running capacity sweep...")
    trial = run_capacity_sweep()
    verdict = compute_verdict(trial)
    print(f"  multipliers:        {trial['multipliers']}")
    print(f"  residuals:          {[round(r, 4) for r in trial['residuals']]}")
    print(f"  step diffs:         {[round(d, 4) for d in trial['step_diffs']]}")
    print(f"  max step-increase:  {verdict['max_step_increase_observed']:+.6f}")
    print(f"  tolerance:          {verdict['tolerance']:.4f}")
    print(f"  verdict:            {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"\nsidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
