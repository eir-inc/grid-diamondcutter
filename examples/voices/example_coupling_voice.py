"""
example_coupling_voice.py — reference implementation of a §3.2 coupling voice.

This file is a working example of a *coupling* voice — the second axis in §3.2 of
the project's PREREGISTRATION.md. A coupling voice links two substrates: the output
of one is hypothesized to drive the input of another. Coupling voices are held to a
stricter pre-commitment than polyphony voices because they assert a *causal*
direction across substrates.

Per §3.2, a coupling voice must pre-register three things in addition to the
standard five-field unit:

  1. The predicted direction (which substrate's output drives the other's input)
  2. The predicted magnitude range
  3. The null direction (the link does not exist OR the direction is reversed)

The verdict reports whether the run output is consistent with the predicted direction,
consistent with the null, or neither (which is itself a failure to recover any
direction and is recorded as fail).

WHAT THIS VOICE PREDICTS
========================

A coupling between the regulatory-substrate (regulatory stringency on grid operators)
and the grid-operational substrate (cycle_residual on the rotating-load-profile
station set). The hypothesis: higher regulatory stringency increases unsigned
cycle_residual (because operators have less flexibility to optimize routing under
tighter constraints).

  Direction (predicted):  regulatory_stringency → cycle_residual_magnitude
  Magnitude (predicted):  positive correlation, slope in [0.005, 0.030] per unit stringency
  Null direction:         no correlation OR negative correlation

KILL CONDITION
==============

A linear fit of cycle_residual against regulatory_stringency across N sample
stringency levels has slope outside the predicted range. Specifically:
  - slope < 0.005 → fail (no link or too-weak link)
  - slope > 0.030 → fail (over-prediction by ≥ 2x)
  - slope < 0     → fail (reversed direction — the null direction)

This is a worked example. The numbers are simulated to demonstrate the cross-substrate
coupling protocol; they do not constitute a claim about real regulatory effects on
real grids. See §1 honesty bounds.
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
# §3.1 — Standard five-field unit (also required for coupling voices)
# ===========================================================================

VOICE_NAME = "regulatory_grid_coupling_v1"

PREDICTION = {
    "kind": "coupling_cross_substrate",  # the second axis — §3.2
    "substrate_source": "regulatory_stringency",
    "substrate_target": "8node_dc_grid",
    "named_residual": "cross_substrate_link_strength_regulatory_to_grid",
    # coupling-specific extra fields per §3.2
    "predicted_direction": "regulatory_stringency → unsigned_cycle_residual (positive)",
    "predicted_magnitude_range": [0.005, 0.030],  # slope per unit stringency, in [low, high]
    "null_direction": "no correlation OR negative correlation",
}

KILL_CONDITION = {
    "metric": "linear_fit_slope_of_cycle_residual_vs_stringency",
    "predicted_range": [0.005, 0.030],
    "rule": (
        "fail if slope < 0.005 (no link / weak link), "
        "fail if slope > 0.030 (over-prediction), "
        "fail if slope < 0 (reversed direction = null direction realized)"
    ),
    "rationale": (
        "The voice claims a positive, bounded coupling. Any of three falsification "
        "outcomes are testable from the run output alone: slope below the floor, "
        "slope above the ceiling, or slope of the wrong sign. The null direction "
        "is named explicitly so its realization is a registry-acceptable null, "
        "not a hidden disconfirmation."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/example_coupling_voice.py",
    "source_file": "examples/voices/example_coupling_voice.py",
    "input_parameters": {
        "stringency_levels": [0.0, 0.25, 0.50, 0.75, 1.00],
        "stations_per_level": "default rotating-load-profile (5 stations)",
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Cross-substrate model: regulatory_stringency modifies grid behavior
# ===========================================================================

def apply_regulatory_stringency(line_flows: np.ndarray, stringency: float) -> np.ndarray:
    """Model: higher regulatory stringency reduces the operator's ability to route
    around stress, expressed as a multiplier on line utilizations above a threshold.

    stringency=0 → no effect; stringency=1 → maximum penalty on stressed lines.
    This is a deliberately simple toy coupling; a richer model would be richer.
    """
    above_threshold = np.clip(line_flows - 0.5, 0.0, None)
    penalty = stringency * 0.20 * above_threshold
    return np.clip(line_flows + penalty, 0.0, None)


def cycle_residual_at_stringency(stringency: float, seed: int = 42) -> float:
    """Compute the unsigned cycle_residual on the canonical station set at a given
    stringency level. Returns one scalar per stringency level for the linear fit.
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
        flows_after = apply_regulatory_stringency(flows, stringency)
        bins = np.histogram(flows_after, bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.5])[0]
        fingerprints.append((*[int(b) for b in bins], round(float(flows_after.max()), 3)))

    step_distances = [
        float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fingerprints[i], fingerprints[i + 1]))))
        for i in range(len(fingerprints) - 1)
    ]
    home_step = float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fingerprints[-1], fingerprints[0]))))
    mean_step = float(np.mean(step_distances)) if step_distances else 0.0
    return abs(home_step - mean_step)


def run_coupling_sweep() -> tuple[list[float], list[float]]:
    """Sweep stringency levels; return (stringency_values, observed_residuals)."""
    levels = RUN_PROTOCOL["input_parameters"]["stringency_levels"]
    seed = RUN_PROTOCOL["input_parameters"]["random_seed"]
    residuals = [cycle_residual_at_stringency(s, seed=seed) for s in levels]
    return levels, residuals


# ===========================================================================
# Verdict computation — slope check against predicted range
# ===========================================================================

def compute_verdict(stringency_levels: list[float], observed_residuals: list[float]) -> dict:
    """Linear fit slope of observed_residuals vs stringency_levels; check against
    pre-committed range. Pass / fail / null-direction outcomes per §3.2.
    """
    x = np.array(stringency_levels)
    y = np.array(observed_residuals)
    # simple least-squares slope
    slope = float(np.cov(x, y, bias=True)[0, 1] / np.var(x))
    intercept = float(y.mean() - slope * x.mean())

    low, high = KILL_CONDITION["predicted_range"]

    if slope < 0:
        verdict = "fail"
        rationale = (
            f"Observed slope {slope:.4f} is negative. The null direction (reversed coupling) "
            f"is the realized outcome. Voice enters the null-voice ledger per §3.4 with the "
            f"null-direction-realized flag set."
        )
        outcome = "null_direction_realized"
    elif slope < low:
        verdict = "fail"
        rationale = (
            f"Observed slope {slope:.4f} is below the predicted floor {low:.4f}. "
            f"The link is too weak to support the prediction. Voice enters the null-voice "
            f"ledger per §3.4."
        )
        outcome = "below_predicted_range"
    elif slope > high:
        verdict = "fail"
        rationale = (
            f"Observed slope {slope:.4f} is above the predicted ceiling {high:.4f}. "
            f"The link is stronger than predicted (over-prediction by the voice). "
            f"Voice enters the null-voice ledger per §3.4."
        )
        outcome = "above_predicted_range"
    else:
        verdict = "pass"
        rationale = (
            f"Observed slope {slope:.4f} is within the pre-committed range "
            f"[{low:.4f}, {high:.4f}]. The predicted coupling direction and magnitude "
            f"are consistent with the run output."
        )
        outcome = "within_predicted_range"

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "observed_slope": slope,
        "observed_intercept": intercept,
        "predicted_range": [low, high],
        "stringency_levels": stringency_levels,
        "observed_residuals": observed_residuals,
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


# ===========================================================================
# Sidecar emission (same shape as polyphony voice; coupling-specific fields preserved)
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
    print(f"voice unit: {VOICE_NAME}  (kind: coupling, cross-substrate)")
    print("=" * 72)
    print(f"prediction:     {PREDICTION['predicted_direction']}")
    print(f"                slope in {PREDICTION['predicted_magnitude_range']}")
    print(f"null direction: {PREDICTION['null_direction']}")
    print(f"run:            {RUN_PROTOCOL['entry_point']}")
    print()
    print("running stringency sweep...")
    levels, residuals = run_coupling_sweep()
    for s, r in zip(levels, residuals):
        print(f"  stringency {s:.2f} → unsigned cycle_residual {r:.4f}")
    verdict = compute_verdict(levels, residuals)
    print()
    print(f"  observed slope:        {verdict['observed_slope']:+.4f}")
    print(f"  predicted range:       {verdict['predicted_range']}")
    print(f"  outcome:               {verdict['outcome_category']}")
    print(f"  verdict:               {verdict['verdict'].upper()}")
    print(f"  rationale: {verdict['rationale']}")
    print()
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
