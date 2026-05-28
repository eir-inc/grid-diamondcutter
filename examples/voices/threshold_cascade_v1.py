"""
threshold_cascade_v1.py — §3.1 polyphony voice testing the §0 central-question
recognition criterion: does the substrate exhibit a *threshold-class cascade*?

PREREGISTRATION §0 hunts for a phenomenon whose signature is a sharp transition
in substrate-chain output between a subcritical regime (small perturbations
absorbed) and a supercritical regime (small perturbations amplify across the
chain). That sharp transition is the threshold-class cascade. This voice
pre-registers a recognition criterion: a sharpness ratio measured across a
parameterized coupling-regime sweep.

WHAT THIS VOICE PREDICTS
========================

A substrate-chain whose internal cross-band coupling strength is swept from
subcritical to supercritical exhibits a sharpness ratio ≥ 10× between the
output-amplification in the supercritical regime and the output-amplification
in the subcritical regime. Sharpness ratio is computed from the run output
alone: max amplification divided by mean amplification in the lower half of
the coupling sweep.

  Kind:                       polyphony_within_substrate
  Substrate:                  3_voice_meta_sim_default_topology
  Named residual:             threshold_class_cascade_sharpness_ratio
  Predicted value (lower bound): ≥ 10× sharpness ratio
  Realization that fails:     sharpness ratio < 5× (no recognizable threshold class)

WHAT THIS VOICE DOES NOT CLAIM
==============================

This voice does not claim that a threshold-class cascade has been observed in
any real grid. It tests whether the polyphonic substrate provided by the
existing meta-sim, swept across a coupling-regime axis, exhibits the
sharpness-ratio signature the central question pre-registers as the recognition
criterion. Per §1, the central-question observation in any real grid requires a
separately pre-registered voice using calibrated real-grid data.

A pass on this voice is a finding that the methodology's substrate can
*display* the predicted recognition signature. A fail is the more interesting
finding: even the methodology's own substrate cannot produce the predicted
sharpness, which would prompt a methodological revision per §5.

KILL CONDITION
==============

Sharpness ratio measured from the coupling-regime sweep:
  - sharpness_ratio < 5  → fail (no recognizable threshold-class signature)
  - 5 ≤ sharpness_ratio < 10 → fail (signature present but below pre-committed bound)
  - sharpness_ratio ≥ 10 → pass (signature recognized within pre-committed bound)
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np

from meta_sim import make_default_meta_sim
from meta_sim.core import LOAD_PROFILES, GEN_PROFILES


# ===========================================================================
# §3.1 — Standard five-field unit
# ===========================================================================

VOICE_NAME = "threshold_cascade_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "3_voice_meta_sim_default_topology",
    "named_residual": "threshold_class_cascade_sharpness_ratio",
    "predicted_value_lower_bound": 10.0,
}

KILL_CONDITION = {
    "metric": "sharpness_ratio_over_coupling_regime_sweep",
    "rule": (
        "fail if sharpness_ratio < 5 (no recognizable threshold-class signature), "
        "fail if 5 <= sharpness_ratio < 10 (signature present but below pre-committed bound), "
        "pass if sharpness_ratio >= 10 (signature recognized within pre-committed bound)"
    ),
    "rationale": (
        "The §0 central question asks whether the substrate exhibits a sharp transition "
        "between subcritical and supercritical regimes. A sharpness ratio bounded from "
        "below is the recognition criterion: the supercritical-regime amplification must "
        "be at least 10x the mean subcritical-regime amplification. Both quantities are "
        "computed from the same run output and are testable without external interpretation."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/threshold_cascade_v1.py",
    "source_file": "examples/voices/threshold_cascade_v1.py",
    "input_parameters": {
        "coupling_regime_sweep": [0.05, 0.10, 0.20, 0.40, 0.70, 1.20, 2.00, 3.00],
        "perturbation_profile_sequence": ["peak", "spike", "peak", "spike", "peak"],
        "n_warmup_steps": 12,
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Voice implementation
# ===========================================================================

def _build_perturbation_inputs() -> list[np.ndarray]:
    """Construct the per-step external inputs for the load-flow voice from the
    pre-committed profile sequence. Returns a list of 8-element vectors."""
    seq = RUN_PROTOCOL["input_parameters"]["perturbation_profile_sequence"]
    return [np.concatenate([LOAD_PROFILES[name], GEN_PROFILES[name]]) for name in seq]


def amplification_at_coupling(coupling_strength: float, seed: int) -> float:
    """Run the meta-sim with a load_flow→dynamics cross-coupling at the given
    strength (the PAC pathway, non-cascade); return the substrate-chain output
    amplification (peak transient amplitude over warmed-up baseline)."""
    rng = np.random.default_rng(seed)
    meta = make_default_meta_sim()
    meta.coupling = {("load_flow", "dynamics"): float(coupling_strength)}
    perturbations = _build_perturbation_inputs()

    n_warmup = RUN_PROTOCOL["input_parameters"]["n_warmup_steps"]
    warmup_input = perturbations[0]
    baseline_amplitudes = []
    for _ in range(n_warmup):
        result = meta.step(warmup_input)
        dynamics_state = result.get("dynamics", np.zeros(4))
        baseline_amplitudes.append(float(np.max(np.abs(dynamics_state))))

    baseline = float(np.mean(baseline_amplitudes[-4:])) if baseline_amplitudes else 1.0
    if baseline < 1e-9:
        baseline = 1e-9

    peak_amplitudes = []
    for inp in perturbations:
        noisy_inp = inp + rng.normal(0.0, 0.5, size=inp.shape)
        result = meta.step(noisy_inp)
        dynamics_state = result.get("dynamics", np.zeros(4))
        peak_amplitudes.append(float(np.max(np.abs(dynamics_state))))

    peak = float(np.max(peak_amplitudes))
    return peak / baseline


def run_regime_sweep() -> list[tuple[float, float]]:
    """Sweep the pre-committed coupling-regime axis; return (strength, amplification)."""
    strengths = RUN_PROTOCOL["input_parameters"]["coupling_regime_sweep"]
    seed = RUN_PROTOCOL["input_parameters"]["random_seed"]
    return [(s, amplification_at_coupling(s, seed=seed)) for s in strengths]


def compute_sharpness_ratio(sweep: list[tuple[float, float]]) -> tuple[float, float, float]:
    """From the sweep, compute (max amplification, mean subcritical amplification,
    sharpness_ratio = max / mean_subcritical)."""
    amplifications = np.array([a for _, a in sweep])
    n = len(amplifications)
    subcritical_half = amplifications[: n // 2]
    mean_subcritical = float(np.mean(subcritical_half)) if subcritical_half.size else 1.0
    if mean_subcritical < 1e-9:
        mean_subcritical = 1e-9
    max_amp = float(np.max(amplifications))
    sharpness = max_amp / mean_subcritical
    return max_amp, mean_subcritical, sharpness


def compute_verdict(sweep: list[tuple[float, float]]) -> dict:
    max_amp, mean_subcritical, sharpness = compute_sharpness_ratio(sweep)
    lower_bound = PREDICTION["predicted_value_lower_bound"]

    if sharpness < 5.0:
        verdict = "fail"
        outcome = "no_recognizable_threshold_class_signature"
        inert = sharpness < 1.05 and max_amp > 0.0
        inertness_note = (
            " The observed sharpness ratio of ~1 indicates the coupling-regime sweep "
            "did not transit any regime boundary in this substrate: the amplification "
            "is bounded by the dynamics voice's filter constants and saturates. This "
            "is itself a finding: the meta-sim as currently parameterized cannot "
            "produce the §0 phenomenon under this knob. A v2 voice should sweep a "
            "different recognizability axis (e.g., direct dynamics-amplitude scaling) "
            "or modify the substrate to admit a real regime boundary."
        ) if inert else ""
        rationale = (
            f"Sharpness ratio {sharpness:.3f} is below the recognition floor of 5x. "
            f"The substrate does not display a recognizable threshold-class signature "
            f"under the pre-committed coupling-regime sweep. Voice enters the §3.4 "
            f"null-voice ledger. This is the more interesting failure mode per §5 — "
            f"the methodology's own substrate cannot produce the predicted shape."
            f"{inertness_note}"
        )
    elif sharpness < lower_bound:
        verdict = "fail"
        outcome = "signature_present_but_below_bound"
        rationale = (
            f"Sharpness ratio {sharpness:.3f} is between 5x and the pre-committed "
            f"bound of {lower_bound:.0f}x. Some threshold-class signature is present "
            f"but does not meet the pre-committed recognition criterion. Voice enters "
            f"the §3.4 null-voice ledger."
        )
    else:
        verdict = "pass"
        outcome = "signature_recognized_within_bound"
        rationale = (
            f"Sharpness ratio {sharpness:.3f} meets or exceeds the pre-committed "
            f"recognition bound of {lower_bound:.0f}x. The substrate displays a "
            f"threshold-class signature consistent with the §0 central question's "
            f"pre-registered recognition criterion. Per §1 honesty bounds, this is "
            f"not a real-grid observation; the substrate is the meta-sim, not a grid."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "observed_max_amplification": max_amp,
        "observed_mean_subcritical_amplification": mean_subcritical,
        "observed_sharpness_ratio": sharpness,
        "predicted_lower_bound": lower_bound,
        "regime_sweep": [{"coupling_strength": s, "amplification": a} for s, a in sweep],
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


# ===========================================================================
# Sidecar emission
# ===========================================================================

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
    print(f"voice unit: {VOICE_NAME}  (kind: polyphony, central-question recognition)")
    print("=" * 72)
    sweep = run_regime_sweep()
    for strength, amp in sweep:
        print(f"  coupling={strength:>5.2f}   amplification={amp:.4f}")
    print("-" * 72)
    verdict = compute_verdict(sweep)
    print(f"  max amplification:        {verdict['observed_max_amplification']:.4f}")
    print(f"  mean subcritical amp:     {verdict['observed_mean_subcritical_amplification']:.4f}")
    print(f"  sharpness ratio:          {verdict['observed_sharpness_ratio']:.4f}")
    print(f"  pre-committed bound (≥):  {verdict['predicted_lower_bound']:.0f}")
    print(f"  verdict:                  {verdict['verdict'].upper()}  ({verdict['outcome_category']})")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
