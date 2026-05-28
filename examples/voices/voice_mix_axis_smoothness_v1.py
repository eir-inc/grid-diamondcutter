"""
voice_mix_axis_smoothness_v1.py — registry voice.

Tests whether the unsigned cycle_residual varies smoothly along the mix axis
when station profile-transitions are held fixed and only the interpolation
parameter `mix ∈ [0, 1]` is swept. Smoothness here means: across a fine sweep
of mix values, no consecutive step produces a jump larger than 5× the median
step. A measurement that jumps discontinuously along a continuous parameter
is fingerprint-quantization-dominated rather than substrate-driven.

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


VOICE_NAME = "mix_axis_smoothness_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "8node_dc_grid",
    "named_residual": (
        "smoothness of unsigned cycle_residual under continuous variation of "
        "the mix interpolation parameter. Predict: across 21 mix values "
        "uniformly spaced in [0, 1], no consecutive-step difference exceeds "
        "5× the median consecutive-step difference."
    ),
    "n_mix_samples": 21,
    "predicted_max_jump_ratio": 5.0,
}

KILL_CONDITION = {
    "metric": "max_step_to_median_step_ratio",
    "rule": (
        "fail if max(|diff|) / median(|diff|) > 5.0 across the 20 consecutive "
        "diffs in the 21-sample mix sweep, where diff[i] = "
        "cycle_residual(mix[i+1]) - cycle_residual(mix[i])"
    ),
    "rationale": (
        "A continuous parameter sweep on a continuous substrate should produce "
        "diffs of roughly comparable magnitude. A single diff that is 5× "
        "larger than the typical diff indicates the measurement is dominated "
        "by fingerprint-discretization boundaries rather than substrate "
        "dynamics. Such jumps mean interpretation across mix-parameter ranges "
        "must account for the discretization, not just the substrate."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/voice_mix_axis_smoothness_v1.py",
    "source_file": "examples/voices/voice_mix_axis_smoothness_v1.py",
    "input_parameters": {
        "mix_samples": "linspace(0, 1, 21)",
        "profile_transitions": [
            ["peak", "off_peak"],
            ["off_peak", "mixed"],
            ["mixed", "spike"],
            ["spike", "peak"],
        ],
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


def cycle_residual_at_mix(mix: float) -> float:
    from power_grid_sim import power_flow

    transitions = [("peak", "off_peak"), ("off_peak", "mixed"),
                   ("mixed", "spike"), ("spike", "peak"), ("peak", "off_peak")]
    fps = []
    for profile_a, profile_b in transitions:
        flows = power_flow(profile_a, profile_b, mix)
        bins = np.histogram(flows, bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.5])[0]
        fps.append((*[int(b) for b in bins], round(float(flows.max()), 3)))
    step_distances = [
        float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[i], fps[i + 1]))))
        for i in range(len(fps) - 1)
    ]
    home_step = float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[-1], fps[0]))))
    mean_step = float(np.mean(step_distances)) if step_distances else 0.0
    return abs(home_step - mean_step)


def run_mix_sweep() -> dict:
    mixes = np.linspace(0.0, 1.0, 21)
    residuals = [cycle_residual_at_mix(float(m)) for m in mixes]
    diffs = np.abs(np.diff(residuals))
    median_diff = float(np.median(diffs))
    max_diff = float(diffs.max())
    ratio = max_diff / max(median_diff, 1e-9)
    return {
        "mixes": mixes.tolist(),
        "residuals": residuals,
        "abs_diffs": diffs.tolist(),
        "median_abs_diff": median_diff,
        "max_abs_diff": max_diff,
        "max_to_median_ratio": ratio,
    }


def compute_verdict(trial: dict) -> dict:
    threshold = PREDICTION["predicted_max_jump_ratio"]
    ratio = trial["max_to_median_ratio"]
    if ratio <= threshold:
        verdict = "pass"
        rationale = (
            f"max/median jump ratio = {ratio:.2f}, at or below threshold {threshold:.1f}. "
            f"cycle_residual varies smoothly along the mix axis at this discretization; "
            f"interpretation across mix ranges is not dominated by fingerprint-quantization "
            f"boundaries."
        )
    else:
        verdict = "fail"
        rationale = (
            f"max/median jump ratio = {ratio:.2f}, exceeds threshold {threshold:.1f}. "
            f"cycle_residual jumps discontinuously at fingerprint-quantization boundaries; "
            f"interpretation across mix ranges must account for the discretization. "
            f"Voice enters the null-voice ledger per §3.4."
        )
    return {
        "verdict": verdict,
        "max_to_median_ratio_observed": ratio,
        "median_abs_diff": trial["median_abs_diff"],
        "max_abs_diff": trial["max_abs_diff"],
        "threshold": threshold,
        "mixes": trial["mixes"],
        "residuals": trial["residuals"],
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
    print("running mix sweep (21 samples)...")
    trial = run_mix_sweep()
    verdict = compute_verdict(trial)
    print(f"  median abs diff:    {verdict['median_abs_diff']:.4f}")
    print(f"  max abs diff:       {verdict['max_abs_diff']:.4f}")
    print(f"  max/median ratio:   {verdict['max_to_median_ratio_observed']:.2f}")
    print(f"  threshold:          {verdict['threshold']:.1f}")
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
