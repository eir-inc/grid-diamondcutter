"""
voice_finer_fingerprint_resolves_v1.py — registry voice.

Tests whether a finer-binned histogram fingerprint resolves the discretization
sensitivity that two earlier registry voices (`noise_robustness_v1` PR #2 FAIL
and `mix_axis_smoothness_v1` PR #9 FAIL) exposed in the default 6-bin
fingerprint. This is a methodology-improvement voice: it uses prior registry
findings as its baseline and asks whether a specific alternative fixes them.

If a finer fingerprint resolves both failures, the methodology has a clean
upgrade path. If it does not, the issue is deeper than binning resolution.

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


VOICE_NAME = "finer_fingerprint_resolves_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "8node_dc_grid",
    "named_residual": (
        "discretization-induced jump sensitivity in cycle_residual measurement, "
        "previously documented in noise_robustness_v1 (PR #2) and "
        "mix_axis_smoothness_v1 (PR #9). Predict that a finer-binned fingerprint "
        "(20 bins instead of 6) reduces the mix-axis max/median jump ratio "
        "below 5.0, which would resolve the discretization weakness on that axis."
    ),
    "default_fingerprint_bins": 6,
    "fine_fingerprint_bins": 20,
    "baseline_jump_ratio_default": 2813.89,
    "predicted_fine_jump_ratio_upper_bound": 5.0,
}

KILL_CONDITION = {
    "metric": "fine_fingerprint_max_to_median_jump_ratio",
    "rule": (
        "fail if max(|diff|)/median(|diff|) > 5.0 across 21-sample mix sweep "
        "when using the 20-bin fingerprint. Equivalent to the kill condition "
        "of mix_axis_smoothness_v1 (PR #9) applied to the alternative "
        "fingerprint. A PASS demonstrates that binning resolution alone "
        "resolves the discretization weakness; a FAIL indicates the issue "
        "is deeper than binning."
    ),
    "rationale": (
        "The kill condition is identical in form to mix_axis_smoothness_v1's, "
        "so a direct PASS/FAIL comparison answers whether finer binning is a "
        "real fix. The threshold (5.0) is the same as the prior voice; only "
        "the fingerprint resolution differs."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/voice_finer_fingerprint_resolves_v1.py",
    "source_file": "examples/voices/voice_finer_fingerprint_resolves_v1.py",
    "input_parameters": {
        "mix_samples": "linspace(0, 1, 21)",
        "profile_transitions": [
            ["peak", "off_peak"],
            ["off_peak", "mixed"],
            ["mixed", "spike"],
            ["spike", "peak"],
        ],
        "fingerprint_bins": 20,
        "fingerprint_bin_edges": "linspace(0.0, 1.5, 21)",
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


def cycle_residual_at_mix_fine(mix: float, n_bins: int = 20) -> float:
    from power_grid_sim import power_flow

    bin_edges = np.linspace(0.0, 1.5, n_bins + 1)
    transitions = [("peak", "off_peak"), ("off_peak", "mixed"),
                   ("mixed", "spike"), ("spike", "peak"), ("peak", "off_peak")]
    fps = []
    for profile_a, profile_b in transitions:
        flows = power_flow(profile_a, profile_b, mix)
        bins = np.histogram(flows, bins=bin_edges)[0]
        fps.append((*[int(b) for b in bins], round(float(flows.max()), 3)))
    step_distances = [
        float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[i], fps[i + 1]))))
        for i in range(len(fps) - 1)
    ]
    home_step = float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[-1], fps[0]))))
    mean_step = float(np.mean(step_distances)) if step_distances else 0.0
    return abs(home_step - mean_step)


def run_fine_mix_sweep() -> dict:
    mixes = np.linspace(0.0, 1.0, 21)
    residuals = [cycle_residual_at_mix_fine(float(m), n_bins=20) for m in mixes]
    diffs = np.abs(np.diff(residuals))
    median_diff = float(np.median(diffs))
    max_diff = float(diffs.max())
    ratio = max_diff / max(median_diff, 1e-9)
    return {
        "mixes": mixes.tolist(),
        "residuals_fine_fingerprint": residuals,
        "abs_diffs": diffs.tolist(),
        "median_abs_diff": median_diff,
        "max_abs_diff": max_diff,
        "max_to_median_ratio_fine": ratio,
    }


def compute_verdict(trial: dict) -> dict:
    threshold = PREDICTION["predicted_fine_jump_ratio_upper_bound"]
    ratio = trial["max_to_median_ratio_fine"]
    baseline = PREDICTION["baseline_jump_ratio_default"]
    improvement = baseline / max(ratio, 1e-9)
    if ratio <= threshold:
        verdict = "pass"
        rationale = (
            f"Fine-fingerprint (20-bin) max/median jump ratio = {ratio:.2f}, at or "
            f"below threshold {threshold:.1f}. Baseline 6-bin ratio was {baseline:.1f} "
            f"(prior voice mix_axis_smoothness_v1 PR #9). Improvement factor: {improvement:.0f}×. "
            f"Finer binning resolves the discretization weakness on the mix axis; the "
            f"methodology has a clean upgrade path on this dimension."
        )
    else:
        verdict = "fail"
        rationale = (
            f"Fine-fingerprint (20-bin) max/median jump ratio = {ratio:.2f}, exceeds "
            f"threshold {threshold:.1f}. Baseline was {baseline:.1f}; improvement factor "
            f"{improvement:.1f}× is insufficient. The discretization issue is deeper "
            f"than binning resolution — likely the categorical max-utilization element "
            f"or the histogram-projection itself. Voice enters null-voice ledger per §3.4."
        )
    return {
        "verdict": verdict,
        "max_to_median_ratio_fine_observed": ratio,
        "baseline_max_to_median_ratio": baseline,
        "improvement_factor": improvement,
        "threshold": threshold,
        "residuals_fine_fingerprint": trial["residuals_fine_fingerprint"],
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
    print("baseline (6-bin fingerprint, mix_axis_smoothness_v1 PR #9):")
    print(f"  max/median jump ratio = {PREDICTION['baseline_jump_ratio_default']:.1f} (FAIL)")
    print()
    print("running 21-sample mix sweep with 20-bin fingerprint...")
    trial = run_fine_mix_sweep()
    verdict = compute_verdict(trial)
    print(f"  fine-fingerprint max/median ratio: {verdict['max_to_median_ratio_fine_observed']:.2f}")
    print(f"  improvement factor:                 {verdict['improvement_factor']:.1f}x")
    print(f"  threshold:                          {verdict['threshold']:.1f}")
    print(f"  verdict:                            {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"\nsidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
