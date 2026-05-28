"""
texas_feb_2021_uri_v1.py — §3.2 coupling voice + §4.2 historical-events validation entry.

This voice is a coupling voice in the §3.2 sense: it pre-registers a directional
cross-substrate link with a magnitude range and a named null direction. It is also
the first entry in the §4.2 historical-events validation pass: the predicted
coupling shape is calibrated from public findings in the FERC / NERC / NRC Inquiry
into the February 2021 Cold Weather Outages in Texas and the South Central United
States (final report, November 2021).

WHAT THIS VOICE PREDICTS
========================

A cross-substrate link from a gas_throughput substrate to a generation_dispatch
substrate, evaluated under a cold-snap temperature perturbation across N scenarios:

  Direction (predicted):  gas_throughput_drop → generation_dispatch_loss (positive)
  Magnitude (predicted):  slope in [0.40, 0.95] dispatch-loss per unit gas-drop
  Null direction:         no correlation OR negative correlation

The predicted magnitude range is calibrated from the report's quantification of
gas-supply curtailment as a contributing cause of generation forced outages
during the event window. The lower bound (0.40) corresponds to a finding that
gas curtailment was a substantial but non-dominant contributor; the upper bound
(0.95) corresponds to a finding that gas curtailment fully transmitted to
generation loss. Either of these is within scope; neither is the claim of this
voice. The voice predicts that the link sits somewhere inside this window.

WHAT THIS VOICE DOES NOT CLAIM
==============================

This voice does not claim to be a measurement of the real ERCOT system, or a
back-test against the documented February 2021 timeline. The voice runs a
substrate model whose parameters are seeded from the FERC/NERC report; the
substrate is not the grid. Per §1, the project does not represent this run
as a real-grid measurement or a forecast of any future event.

What the voice does establish: whether the methodology's coupling protocol
recovers a coupling shape consistent with the documented qualitative finding
(gas supply drop drove generation loss in a specific direction with a specific
sign of the coupling) when the substrate is calibrated to the report.

KILL CONDITION
==============

A linear fit of dispatch-loss against gas-throughput-drop across the cold-snap
scenarios has slope outside the predicted range [0.40, 0.95]:
  - slope < 0.40 → fail (link too weak to recover the documented shape)
  - slope > 0.95 → fail (over-prediction; coupling magnitude exceeded the
                          window even at the report's upper bound)
  - slope < 0    → fail (null direction realized — the documented direction
                          was not recovered; the report's primary causal
                          finding would not be supported by the methodology)

REFERENCES (PUBLIC)
===================

  - FERC, NERC, and the NRC Regional Entity, "The February 2021 Cold Weather
    Outages in Texas and the South Central United States", Final Report
    (November 2021). Public.
  - ERCOT EEA3 declarations + grid-event timeline, February 15-19, 2021. Public.
  - NOAA / NCEI February 2021 temperature anomaly data for Texas. Public.

This is a §3.2 coupling voice and §4.2 historical-events validation entry. See
PREREGISTRATION.md §1 honesty bounds for the bounds this voice inherits.
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

VOICE_NAME = "texas_feb_2021_uri_v1"

PREDICTION = {
    "kind": "coupling_cross_substrate",
    "substrate_source": "gas_throughput",
    "substrate_target": "generation_dispatch",
    "named_residual": "cross_substrate_link_strength_gas_throughput_to_generation_dispatch",
    "predicted_direction": "gas_throughput_drop → generation_dispatch_loss (positive)",
    "predicted_magnitude_range": [0.40, 0.95],
    "null_direction": "no correlation OR negative correlation",
    "calibration_source": (
        "FERC/NERC/NRC RE Final Report on the February 2021 Cold Weather Outages "
        "in Texas and the South Central United States (November 2021); public."
    ),
}

KILL_CONDITION = {
    "metric": "linear_fit_slope_of_dispatch_loss_vs_gas_throughput_drop",
    "predicted_range": [0.40, 0.95],
    "rule": (
        "fail if slope < 0.40 (link too weak to recover the documented coupling shape), "
        "fail if slope > 0.95 (over-prediction even above the report's upper bound), "
        "fail if slope < 0 (null direction realized — documented direction not recovered)"
    ),
    "rationale": (
        "The voice claims a positive, bounded coupling whose window is taken from the "
        "FERC/NERC report's range of findings on gas-curtailment-to-generation-loss. "
        "Any of three falsification outcomes is testable from run output alone: slope "
        "below the floor, above the ceiling, or wrong sign. The null direction is "
        "named explicitly so its realization is a registry-acceptable null per §3.4, "
        "not a hidden disconfirmation. This voice's pass does not constitute a "
        "real-grid claim; see PREREGISTRATION §1 honesty bound on coupling magnitudes."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/texas_feb_2021_uri_v1.py",
    "source_file": "examples/voices/texas_feb_2021_uri_v1.py",
    "input_parameters": {
        "temperature_anomaly_scenarios_degC": [
            -5.0, -10.0, -15.0, -20.0, -25.0, -30.0,
        ],
        "scenario_descriptor": (
            "Six cold-snap scenarios at progressively colder temperature anomalies "
            "from the regional norm, spanning from mild cold front to the documented "
            "February 15-16, 2021 peak anomaly window."
        ),
        "n_substrate_steps_per_scenario": 96,
        "scenario_horizon_hours": 96,
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Substrate models — gas_throughput + generation_dispatch
# ===========================================================================

def gas_throughput_response(temperature_anomaly_degC: float, n_steps: int, seed: int) -> np.ndarray:
    """Substrate model: gas-pipeline-system throughput as a function of cold-snap
    intensity over a multi-hour window.

    Gas processing capacity decreases with cold anomaly through three mechanisms
    documented in the FERC/NERC report: well-head freezing, gas-processing-plant
    instrumentation failure, and gathering-line ice formation. Throughput is
    normalized to [0, 1] where 1 = pre-event baseline.
    """
    rng = np.random.default_rng(seed)
    # Three loss channels with progressively colder onset:
    wellhead_loss = max(0.0, min(0.5, (-temperature_anomaly_degC - 5.0) / 30.0))
    processing_loss = max(0.0, min(0.3, (-temperature_anomaly_degC - 10.0) / 30.0))
    gathering_loss = max(0.0, min(0.2, (-temperature_anomaly_degC - 15.0) / 30.0))
    target_throughput = max(0.05, 1.0 - wellhead_loss - processing_loss - gathering_loss)

    throughput = np.ones(n_steps)
    for t in range(1, n_steps):
        decay = 0.85 if t < 24 else 0.95
        noise = rng.normal(0.0, 0.01)
        throughput[t] = decay * throughput[t - 1] + (1.0 - decay) * target_throughput + noise
    return np.clip(throughput, 0.0, 1.0)


def generation_dispatch_response(
    gas_throughput: np.ndarray, temperature_anomaly_degC: float, seed: int,
) -> np.ndarray:
    """Substrate model: generation dispatch capacity over a multi-hour window.

    Driven by two channels: (a) gas-fueled generation responds proportionally to
    gas throughput (the cross-substrate link this voice tests); (b) non-gas
    generation has its own direct cold-weather derating (wind, nuclear, coal
    pile freezing) independent of gas. Normalized to [0, 1].
    """
    rng = np.random.default_rng(seed + 1)
    n_steps = len(gas_throughput)

    # Direct cold derating, independent of gas substrate.
    direct_cold_loss = max(0.0, min(0.30, (-temperature_anomaly_degC - 5.0) / 50.0))

    # Gas-fueled share of generation (representative ERCOT-region fixture: ~0.50).
    gas_share = 0.50

    dispatch = np.ones(n_steps)
    for t in range(1, n_steps):
        gas_driven_capacity = gas_share * gas_throughput[t]
        non_gas_capacity = (1.0 - gas_share) * (1.0 - direct_cold_loss)
        target = gas_driven_capacity + non_gas_capacity
        decay = 0.80 if t < 24 else 0.92
        noise = rng.normal(0.0, 0.01)
        dispatch[t] = decay * dispatch[t - 1] + (1.0 - decay) * target + noise
    return np.clip(dispatch, 0.0, 1.0)


def run_scenario(temperature_anomaly_degC: float, n_steps: int, seed: int) -> dict:
    """Run one cold-snap scenario; return scenario-level summary."""
    gas = gas_throughput_response(temperature_anomaly_degC, n_steps, seed)
    dispatch = generation_dispatch_response(gas, temperature_anomaly_degC, seed)
    return {
        "temperature_anomaly_degC": temperature_anomaly_degC,
        "gas_throughput_drop": float(1.0 - gas.min()),
        "dispatch_loss": float(1.0 - dispatch.min()),
        "gas_min_step": int(gas.argmin()),
        "dispatch_min_step": int(dispatch.argmin()),
    }


def run_scenario_sweep() -> list[dict]:
    """Sweep the pre-committed cold-snap scenarios; return per-scenario summaries."""
    scenarios = RUN_PROTOCOL["input_parameters"]["temperature_anomaly_scenarios_degC"]
    n_steps = RUN_PROTOCOL["input_parameters"]["n_substrate_steps_per_scenario"]
    seed = RUN_PROTOCOL["input_parameters"]["random_seed"]
    return [run_scenario(t, n_steps, seed) for t in scenarios]


# ===========================================================================
# Verdict computation — slope check against predicted range
# ===========================================================================

def compute_verdict(scenario_summaries: list[dict]) -> dict:
    """Linear fit slope of dispatch_loss vs gas_throughput_drop; check against
    pre-committed range. Pass / fail per §3.2 with null direction named.
    """
    x = np.array([s["gas_throughput_drop"] for s in scenario_summaries])
    y = np.array([s["dispatch_loss"] for s in scenario_summaries])
    slope = float(np.cov(x, y, bias=True)[0, 1] / np.var(x))
    intercept = float(y.mean() - slope * x.mean())

    low, high = KILL_CONDITION["predicted_range"]

    if slope < 0:
        verdict = "fail"
        outcome = "null_direction_realized"
        rationale = (
            f"Observed slope {slope:.4f} is negative. The null direction "
            f"(reversed coupling) was realized. The methodology did not recover the "
            f"FERC/NERC report's documented gas → generation direction. Voice enters "
            f"the §3.4 null-voice ledger with null-direction-realized flag set."
        )
    elif slope < low:
        verdict = "fail"
        outcome = "below_predicted_range"
        rationale = (
            f"Observed slope {slope:.4f} is below the predicted floor {low:.4f}. "
            f"The recovered coupling is weaker than the report's lower-bound finding. "
            f"Voice enters the §3.4 null-voice ledger."
        )
    elif slope > high:
        verdict = "fail"
        outcome = "above_predicted_range"
        rationale = (
            f"Observed slope {slope:.4f} is above the predicted ceiling {high:.4f}. "
            f"The recovered coupling exceeds even the report's upper-bound finding "
            f"(full gas → generation transmission). Voice enters the §3.4 null-voice ledger."
        )
    else:
        verdict = "pass"
        outcome = "within_predicted_range"
        rationale = (
            f"Observed slope {slope:.4f} is within the pre-committed range "
            f"[{low:.4f}, {high:.4f}], calibrated from the FERC/NERC final-report "
            f"window. The methodology's coupling protocol recovers a shape consistent "
            f"with the documented direction and magnitude. Per §1 honesty bounds, "
            f"this is not a real-grid measurement; the substrate is parameterized "
            f"from the public report, not the operating grid."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "observed_slope": slope,
        "observed_intercept": intercept,
        "predicted_range": [low, high],
        "scenario_summaries": scenario_summaries,
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
    print(f"voice unit: {VOICE_NAME}  (kind: coupling, cross-substrate)")
    print(f"calibration: FERC/NERC/NRC RE Final Report (Nov 2021), public.")
    print("=" * 72)
    print(f"sweeping {len(RUN_PROTOCOL['input_parameters']['temperature_anomaly_scenarios_degC'])} cold-snap scenarios...")
    summaries = run_scenario_sweep()
    for s in summaries:
        print(
            f"  temp_anom={s['temperature_anomaly_degC']:>+6.1f}degC  "
            f"gas_drop={s['gas_throughput_drop']:.4f}  "
            f"dispatch_loss={s['dispatch_loss']:.4f}  "
            f"gas_min_t={s['gas_min_step']:>3d}  disp_min_t={s['dispatch_min_step']:>3d}"
        )
    print("-" * 72)
    verdict = compute_verdict(summaries)
    print(f"  slope:     {verdict['observed_slope']:.4f}")
    print(f"  intercept: {verdict['observed_intercept']:.4f}")
    print(f"  range:     {verdict['predicted_range']}")
    print(f"  verdict:   {verdict['verdict'].upper()}  ({verdict['outcome_category']})")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
