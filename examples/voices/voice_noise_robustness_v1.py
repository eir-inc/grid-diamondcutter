"""
voice_noise_robustness_v1.py — first non-example voice in the registry.

Tests whether the cycle_residual measurement is robust to small perturbations on
the underlying grid model. If the measurement collapses under modest noise, it
is not a useful signal; if it survives, the measurement carries real structure.

Authored under the protocol in PREREGISTRATION.md §3.1.
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
# §3.1 five-field unit
# ===========================================================================

VOICE_NAME = "noise_robustness_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "8node_dc_grid",
    "named_residual": (
        "stability of cycle_residual under small Gaussian perturbation of line "
        "capacities. If the measurement is meaningful, modest noise should not "
        "change the unsigned cycle_residual by more than 50% across N=20 trials "
        "of 5% multiplicative Gaussian noise on line capacities."
    ),
    "baseline_unsigned_cycle_residual": 0.0465,
    "predicted_max_relative_drift": 0.50,    # 50% relative change
    "noise_sigma_relative": 0.05,            # 5% multiplicative Gaussian on capacities
    "n_trials": 20,
}

KILL_CONDITION = {
    "metric": "max_absolute_relative_drift_across_trials",
    "rule": (
        "fail if any of the 20 trials produces an unsigned cycle_residual "
        "more than 50% different from the baseline unsigned cycle_residual "
        "(i.e., |observed - baseline| / baseline > 0.50)"
    ),
    "rationale": (
        "A measurement that swings >50% under modest 5% noise on a single "
        "parameter is not robust enough to support cross-region claims. Failure "
        "indicates the cycle_residual is sensitive in a way that limits the "
        "measurement's usefulness, which is itself a registry-worthy finding."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/voice_noise_robustness_v1.py",
    "source_file": "examples/voices/voice_noise_robustness_v1.py",
    "input_parameters": {
        "random_seed": 42,
        "n_trials": 20,
        "noise_sigma_relative": 0.05,
        "station_set": "default rotating-load-profile (5 stations)",
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Voice implementation
# ===========================================================================

def cycle_residual_with_perturbed_capacities(capacity_multipliers: np.ndarray) -> float:
    """Compute unsigned cycle_residual with line capacities perturbed by the
    multiplicative factors provided. Returns the unsigned cycle_residual on the
    default station set.
    """
    from power_grid_sim import GridStation, LOAD_PROFILES, GEN_PROFILES, EDGES, N_GENS, N_LINES

    perturbed_capacities = np.full(N_LINES, 100.0) * capacity_multipliers

    def power_flow_perturbed(profile_a, profile_b, mix):
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
        return flows / perturbed_capacities

    stations = [
        GridStation("peak", "off_peak", 0.3),
        GridStation("off_peak", "mixed", 0.3),
        GridStation("mixed", "spike", 0.3),
        GridStation("spike", "peak", 0.3),
        GridStation("peak", "off_peak", 0.3),
    ]
    fingerprints = []
    for s in stations:
        flows = power_flow_perturbed(s.profile_a, s.profile_b, s.mix)
        bins = np.histogram(flows, bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.5])[0]
        fingerprints.append((*[int(b) for b in bins], round(float(flows.max()), 3)))
    step_distances = [
        float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fingerprints[i], fingerprints[i + 1]))))
        for i in range(len(fingerprints) - 1)
    ]
    home_step = float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fingerprints[-1], fingerprints[0]))))
    mean_step = float(np.mean(step_distances)) if step_distances else 0.0
    return abs(home_step - mean_step)


def run_noise_trials() -> dict:
    """Run N_TRIALS independent perturbation trials; return per-trial residuals + max drift."""
    rng = np.random.default_rng(RUN_PROTOCOL["input_parameters"]["random_seed"])
    n = RUN_PROTOCOL["input_parameters"]["n_trials"]
    sigma = RUN_PROTOCOL["input_parameters"]["noise_sigma_relative"]
    n_lines = 12
    baseline = PREDICTION["baseline_unsigned_cycle_residual"]

    residuals = []
    for _ in range(n):
        multipliers = 1.0 + sigma * rng.standard_normal(n_lines)
        # clip to avoid negative or zero capacities
        multipliers = np.clip(multipliers, 0.5, 2.0)
        r = cycle_residual_with_perturbed_capacities(multipliers)
        residuals.append(r)
    residuals = np.array(residuals)
    relative_drifts = np.abs(residuals - baseline) / max(baseline, 1e-9)
    return {
        "trial_residuals": residuals.tolist(),
        "relative_drifts": relative_drifts.tolist(),
        "max_relative_drift": float(relative_drifts.max()),
        "mean_relative_drift": float(relative_drifts.mean()),
        "std_relative_drift": float(relative_drifts.std()),
    }


def compute_verdict(trial_result: dict) -> dict:
    max_drift = trial_result["max_relative_drift"]
    threshold = PREDICTION["predicted_max_relative_drift"]
    if max_drift <= threshold:
        verdict = "pass"
        rationale = (
            f"Max relative drift across {RUN_PROTOCOL['input_parameters']['n_trials']} "
            f"trials = {max_drift:.1%}, at or below the predicted threshold {threshold:.0%}. "
            f"Mean drift {trial_result['mean_relative_drift']:.1%}, std "
            f"{trial_result['std_relative_drift']:.1%}. The cycle_residual is stable to "
            f"5% multiplicative noise on line capacities at the scope tested."
        )
    else:
        verdict = "fail"
        rationale = (
            f"Max relative drift across trials = {max_drift:.1%}, exceeds predicted "
            f"threshold {threshold:.0%}. The cycle_residual is not robust to 5% noise "
            f"at the scope tested. Voice enters the null-voice ledger per §3.4."
        )
    return {
        "verdict": verdict,
        "max_relative_drift_observed": max_drift,
        "threshold": threshold,
        "trial_residuals": trial_result["trial_residuals"],
        "mean_relative_drift": trial_result["mean_relative_drift"],
        "std_relative_drift": trial_result["std_relative_drift"],
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
    print(f"prediction: max drift ≤ {PREDICTION['predicted_max_relative_drift']:.0%} "
          f"across {PREDICTION['n_trials']} trials at {PREDICTION['noise_sigma_relative']:.0%} noise")
    print()
    print("running trials...")
    trial_result = run_noise_trials()
    verdict = compute_verdict(trial_result)
    print(f"  baseline unsigned cycle_residual: {PREDICTION['baseline_unsigned_cycle_residual']:.4f}")
    print(f"  max relative drift:               {verdict['max_relative_drift_observed']:.1%}")
    print(f"  mean relative drift:              {verdict['mean_relative_drift']:.1%}")
    print(f"  threshold:                        {verdict['threshold']:.0%}")
    print(f"  verdict:                          {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"\nsidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
