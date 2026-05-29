"""
region_transfer_failure_v1.py — §3.2 coupling voice that PRE-REGISTERS a fail.

PREREGISTRATION §1 honesty bound #5 says:

  "The methodology generalizes across regulatory regions without per-region
   voice addition."  — the project will NOT claim this.

This voice tests that bound mechanically. The prediction is that running a
region-A substrate's parameters through a region-B calibration window will
not recover the region-B documented coupling magnitude. The voice's PASS
verdict is a kill condition on the §1 bound — a pass here would itself be
a §1 bound-crossing event requiring a flagging-record entry per the
PREREGISTRATION's §1 bound-crossing protocol.

WHAT THIS VOICE PREDICTS
========================

Running the texas_feb_2021 substrate parameters (gas → electricity coupling)
through the eu_may_2022 calibration window (regulatory → capital) produces
a slope OUTSIDE the EU-calibrated window [0.30, 0.85] — i.e., the texas
substrate does NOT spuriously recover the EU finding.

  Direction (predicted):    no end-to-end coupling under cross-region transfer
  Magnitude (predicted):    slope outside [0.30, 0.85] under transfer
  Null direction (here):    slope sits inside [0.30, 0.85] = false-positive transfer

KILL CONDITION (NOTE THE INVERSION)
====================================

This voice's verdict logic INVERTS the standard kill condition because the
voice predicts failure-to-transfer:

  - transfer-slope OUTSIDE [0.30, 0.85] → pass  (methodology correctly
                                                  fails to transfer; §1 bound #5
                                                  is supported by this run)
  - transfer-slope INSIDE  [0.30, 0.85] → fail  (false-positive transfer;
                                                  §1 bound #5 has a counter-
                                                  observation requiring
                                                  bound-crossing flagging)

A PASS here is the project's own protection against a §1 bound violation.
A FAIL here is itself the registry-acceptable finding that the methodology
admits cross-region transfer in this particular pairing — which would be
new methodological evidence that the §1 bound is too strict and a v2 honesty
bound revision would be in scope.
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
# §3.1 — Standard five-field unit
# ===========================================================================

VOICE_NAME = "region_transfer_failure_v1"

PREDICTION = {
    "kind": "coupling_cross_substrate",
    "substrate_source": "texas_substrate_parameters_applied_to_eu_calibration_window",
    "substrate_target": "eu_capital_reallocation",
    "named_residual": "false_positive_cross_region_transfer_link_strength",
    "predicted_direction": "no end-to-end coupling under cross-region transfer (the §1 bound #5)",
    "predicted_magnitude_range": [-1.0, 0.299],
    "predicted_magnitude_range_alternate_high": [0.851, 5.0],
    "null_direction": "slope sits INSIDE [0.30, 0.85] = false-positive transfer = §1 bound counter-observation",
    "bound_under_test": (
        "PREREGISTRATION §1 row #5 — 'the methodology generalizes across "
        "regulatory regions without per-region voice addition'; the project "
        "will NOT claim this. This voice's PASS supports the bound."
    ),
}

KILL_CONDITION = {
    "metric": "transfer_slope_outside_eu_calibrated_window",
    "predicted_pass_condition": "transfer-slope < 0.30 OR transfer-slope > 0.85",
    "rule": (
        "pass if transfer-slope is OUTSIDE [0.30, 0.85] (bound supported), "
        "fail if transfer-slope is INSIDE [0.30, 0.85] (false-positive transfer; "
        "§1 bound counter-observation)"
    ),
    "rationale": (
        "The voice's verdict logic is intentionally inverted relative to the "
        "standard coupling voice: a transfer that lands inside the EU-calibrated "
        "window would be a §1 bound violation, not a methodological success. "
        "The voice's PASS protects the bound. Its FAIL produces evidence that "
        "the bound is too strict and may need v2 revision under §1's expansion-"
        "permitted-relaxation-not discipline."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/region_transfer_failure_v1.py",
    "source_file": "examples/voices/region_transfer_failure_v1.py",
    "input_parameters": {
        "texas_temperature_anomaly_scenarios_degC": [
            -5.0, -10.0, -15.0, -20.0, -25.0, -30.0,
        ],
        "eu_calibrated_predicted_range": [0.30, 0.85],
        "n_steps_per_scenario": 24,
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Cross-region substrate: texas substrate driven into eu measurement axes
# ===========================================================================

def texas_substrate_under_eu_axes(temperature_anomaly_degC: float, n_steps: int, seed: int) -> dict:
    """Run the texas-substrate dynamics (cold-snap → gas-throughput-drop) but
    measure the output along the EU axes (regulatory-signal → capital-
    reallocation share). The mismatch is intentional: this voice tests the
    failure-to-transfer."""
    rng = np.random.default_rng(seed)
    # Texas substrate: cold-snap drives gas-supply curtailment
    wellhead_loss = max(0.0, min(0.5, (-temperature_anomaly_degC - 5.0) / 30.0))
    processing_loss = max(0.0, min(0.3, (-temperature_anomaly_degC - 10.0) / 30.0))
    target_gas_throughput = max(0.05, 1.0 - wellhead_loss - processing_loss)

    gas_throughput = np.ones(n_steps)
    for t in range(1, n_steps):
        decay = 0.85
        noise = rng.normal(0.0, 0.01)
        gas_throughput[t] = decay * gas_throughput[t - 1] + (1.0 - decay) * target_gas_throughput + noise

    # Force the texas output through the EU measurement axes — gas-supply-drop
    # is interpreted AS IF it were a regulatory-signal trajectory, and the
    # "downstream" output is measured as capital-reallocation share. The texas
    # substrate has no calibration toward the EU regulatory/capital coupling
    # gains; if the methodology spuriously recovers an EU-shaped slope, that
    # would be the §1 bound counter-observation.
    gas_drop_as_signal = 1.0 - gas_throughput
    measurement_target = 0.62 * np.tanh(2.0 * gas_drop_as_signal)
    measurement = np.zeros(n_steps)
    rng_b = np.random.default_rng(seed + 1)
    for t in range(1, n_steps):
        target = measurement_target[t]
        decay = 0.7
        noise = rng_b.normal(0.0, 0.005)
        measurement[t] = decay * measurement[t - 1] + (1.0 - decay) * target + noise

    return {
        "temperature_anomaly_degC": temperature_anomaly_degC,
        "gas_drop_as_signal_mean": float(gas_drop_as_signal.mean()),
        "transferred_measurement_mean": float(measurement[8:].mean()),
    }


def run_transfer_sweep() -> list[dict]:
    scenarios = RUN_PROTOCOL["input_parameters"]["texas_temperature_anomaly_scenarios_degC"]
    n_steps = RUN_PROTOCOL["input_parameters"]["n_steps_per_scenario"]
    seed = RUN_PROTOCOL["input_parameters"]["random_seed"]
    return [texas_substrate_under_eu_axes(t, n_steps, seed) for t in scenarios]


def compute_verdict(scenario_summaries: list[dict]) -> dict:
    x = np.array([s["gas_drop_as_signal_mean"] for s in scenario_summaries])
    y = np.array([s["transferred_measurement_mean"] for s in scenario_summaries])
    slope = float(np.cov(x, y, bias=True)[0, 1] / np.var(x))
    intercept = float(y.mean() - slope * x.mean())

    eu_low, eu_high = RUN_PROTOCOL["input_parameters"]["eu_calibrated_predicted_range"]

    if slope < eu_low or slope > eu_high:
        verdict = "pass"
        # narrow-margin flag — true if slope is within 0.05 of either window edge
        narrow_margin = (
            abs(slope - eu_low) < 0.05 or abs(slope - eu_high) < 0.05
        )
        if narrow_margin:
            outcome = "transfer_outside_eu_window_but_narrow_margin"
            rationale = (
                f"Transfer slope {slope:.4f} is OUTSIDE the EU-calibrated window "
                f"[{eu_low:.2f}, {eu_high:.2f}] but with a narrow margin (< 0.05 "
                f"from a window edge). The bound is supported by this run but the "
                f"narrow margin is itself a diagnostic: the methodology's substrate "
                f"family produces similar-shaped responses even across distinct "
                f"calibration sources, and a small perturbation to the texas "
                f"substrate parameterization could move the test inside the window. "
                f"A v2 of this voice should either tighten the substrate "
                f"isolation or widen the bound's claimed strength."
            )
        else:
            outcome = "transfer_correctly_outside_eu_window"
            rationale = (
                f"Transfer slope {slope:.4f} is OUTSIDE the EU-calibrated window "
                f"[{eu_low:.2f}, {eu_high:.2f}]. The texas substrate does not "
                f"spuriously recover the EU finding when measured along EU axes. "
                f"This run supports PREREGISTRATION §1 bound #5: the methodology "
                f"does not transfer across regions without per-region voice "
                f"addition. Voice PASSes its inverted kill condition."
            )
    else:
        verdict = "fail"
        outcome = "false_positive_transfer_inside_eu_window"
        rationale = (
            f"Transfer slope {slope:.4f} is INSIDE the EU-calibrated window "
            f"[{eu_low:.2f}, {eu_high:.2f}]. This is a §1 bound counter-"
            f"observation: the texas substrate, measured along EU axes, "
            f"reproduces an EU-shaped slope. Per §1's bound-crossing protocol "
            f"this run requires a flagging-record entry alongside the failure "
            f"ledger. v2 of this voice would either tighten the bound test or "
            f"the bound text itself would need expansion under §1's expansion-"
            f"permitted-relaxation-not discipline."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "observed_slope": slope,
        "observed_intercept": intercept,
        "eu_calibrated_window": [eu_low, eu_high],
        "scenario_summaries": scenario_summaries,
        "bound_under_test": PREDICTION["bound_under_test"],
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
    print(f"voice unit: {VOICE_NAME}  (kind: coupling, inverted kill condition)")
    print(f"under test: PREREGISTRATION §1 bound #5 (no cross-region transfer)")
    print("=" * 72)
    summaries = run_transfer_sweep()
    for s in summaries:
        print(
            f"  temp_anom={s['temperature_anomaly_degC']:>+6.1f}degC  "
            f"gas_drop_as_signal_mean={s['gas_drop_as_signal_mean']:.4f}  "
            f"transferred_measurement_mean={s['transferred_measurement_mean']:.4f}"
        )
    print("-" * 72)
    verdict = compute_verdict(summaries)
    print(f"  transfer slope:     {verdict['observed_slope']:.4f}")
    print(f"  intercept:          {verdict['observed_intercept']:.4f}")
    print(f"  EU-calibrated window: {verdict['eu_calibrated_window']}")
    print(f"  verdict:            {verdict['verdict'].upper()}  ({verdict['outcome_category']})")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
