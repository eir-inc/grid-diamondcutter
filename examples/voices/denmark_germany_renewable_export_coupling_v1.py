# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
denmark_germany_renewable_export_coupling_v1.py — §3.2 coupling voice.

Tests the positive-cascade domino-step hypothesis Eugene named:
  region A (Denmark, wind surplus) → cross-border export → undermines region B
  (Germany-North) fossil baseload margins → B's capex shifts toward additional
  renewable + interconnect → measurable positive coupling.

Complement to PR #26 cajal voice 4 (germany_neighbor_renewable_coupling FAIL on
DE→FR, attributable to France nuclear-dominated baseload). This voice tests
the inverse direction (DK→DE) where the import-region has higher fossil-baseload
share + stronger renewable-pull policy. If the cascade-mechanism is observable
at all, DK→DE is the higher-probability pair.

Per §1 honesty bound: SYNTHETIC v1 from publicly-cited Energinet + AGEE-Stat
+ ENTSO-E summary milestones. v2-ratchet to real ENTSO-E cross-border flow
data via PR #10 frozen-snapshot contract required for any external claim.

Eugene's domino-dynamics frame: this is step-1 of the positive cascade chain.
Each PASS pair triangulates the cascade hypothesis. Multiple region-pair voices
needed before chain-loop claim.
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
# §3.2 — coupling voice unit
# ===========================================================================

VOICE_NAME = "denmark_germany_renewable_export_coupling_v1"

PREDICTION = {
    "kind": "coupling_cross_substrate",
    "substrates": [
        "denmark_wind_export_share_yoy_2010_2023_synthetic",
        "germany_north_onshore_wind_capacity_yoy_growth_2010_2023_synthetic",
    ],
    "named_residual": "dk_wind_export_yoy_change_predicts_de_north_wind_capacity_yoy_growth_at_1y_lag",
    "predicted_direction": "positive",  # cascade-step: DK export rise → DE north capex pickup
    "predicted_magnitude_range": [0.10, 0.50],  # slope of lagged regression
    "null_direction": "slope_approximately_zero_or_negative_no_cascade_observable",
    "rationale": (
        "Eugene's domino-step 1 hypothesis: DK wind surplus export undermines "
        "DE-North fossil baseload margin → DE-North capex rationally shifts "
        "toward additional renewable + interconnect strengthening. Tests "
        "specifically the DK→DE pair where DE has higher fossil-baseload share "
        "than nuclear-dominated FR (failed in PR #26 cajal voice 4). Inverse "
        "asymmetry test: same mechanism, different receiving-region structure."
    ),
}

KILL_CONDITION = {
    "metric": "dk_to_de_north_wind_coupling_lagged_slope",
    "rule": (
        "fail if slope < 0.10 (below predicted magnitude floor — cascade "
        "below detectable threshold); "
        "fail if slope > 0.50 (over-prediction — implausible synthetic-curation); "
        "fail if slope < 0 (null direction realized — coupling reversed)"
    ),
    "rationale": (
        "Single composite metric — lagged linear-regression slope of "
        "DE-North-wind YoY growth on DK-wind-export YoY change at 1y lag. "
        "Magnitude window rejects both null and over-curation."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/denmark_germany_renewable_export_coupling_v1.py",
    "source_file": "examples/voices/denmark_germany_renewable_export_coupling_v1.py",
    "input_parameters": {
        "calibration_source": "synthetic_v1_publicly_cited_Energinet_AGEE_Stat_ENTSO_E_milestones",
        "years": list(range(2010, 2024)),
        # Denmark wind-export share of generation (% of total generation, synthetic-calibrated
        # from publicly-cited Energinet annual reports — Danish wind reached ~50% generation
        # share by 2020, with ~12-15% net-export to neighbors in peak years)
        "dk_wind_export_share_pct": [
            6.0, 7.5, 9.0, 10.2, 11.5, 13.0, 14.2, 15.5, 16.3, 17.0,
            17.8, 18.0, 18.2, 18.5,
        ],
        # Germany-North onshore wind installed capacity year-end (GW, synthetic-calibrated
        # from publicly-cited AGEE-Stat / Bundesnetzagentur — DE total onshore wind grew
        # from ~27 GW in 2010 to ~58 GW in 2023; DE-North = Niedersachsen + S-H + M-V + Bremen
        # share is roughly 55-60% of national)
        "de_north_wind_capacity_gw": [
            16.2, 18.0, 19.5, 21.0, 23.0, 25.5, 28.0, 30.5, 32.0, 33.2,
            34.0, 34.5, 35.0, 35.8,
        ],
        "lag_years": 1,
        "random_seed": 1015,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Voice implementation
# ===========================================================================

def yoy_change(series: list[float]) -> list[float]:
    """Year-over-year absolute change."""
    return [series[i + 1] - series[i] for i in range(len(series) - 1)]


def lagged_regression_slope(x: list[float], y: list[float], lag: int) -> tuple[float, float, int]:
    """Slope of y[lag:] on x[:-lag] if lag > 0, else y on x."""
    if lag <= 0:
        x_arr = np.array(x)
        y_arr = np.array(y)
    else:
        x_arr = np.array(x[:-lag])
        y_arr = np.array(y[lag:])
    if len(x_arr) < 3 or len(y_arr) < 3:
        return float("nan"), float("nan"), len(x_arr)
    slope, intercept = np.polyfit(x_arr, y_arr, 1)
    return float(slope), float(intercept), len(x_arr)


def run_voice() -> dict:
    np.random.seed(RUN_PROTOCOL["input_parameters"]["random_seed"])
    dk_export = RUN_PROTOCOL["input_parameters"]["dk_wind_export_share_pct"]
    de_north_capacity = RUN_PROTOCOL["input_parameters"]["de_north_wind_capacity_gw"]
    lag = RUN_PROTOCOL["input_parameters"]["lag_years"]

    dk_yoy = yoy_change(dk_export)
    de_yoy = yoy_change(de_north_capacity)
    slope, intercept, n_pairs = lagged_regression_slope(dk_yoy, de_yoy, lag)

    return {
        "years": RUN_PROTOCOL["input_parameters"]["years"],
        "dk_wind_export_share_pct": dk_export,
        "de_north_wind_capacity_gw": de_north_capacity,
        "dk_yoy_export_change": dk_yoy,
        "de_yoy_capacity_change": de_yoy,
        "lag_years": lag,
        "n_lagged_pairs": int(n_pairs),
        "lagged_slope": slope,
        "lagged_intercept": intercept,
    }


# ===========================================================================
# Field 5: verdict
# ===========================================================================

def compute_verdict(run_output: dict) -> dict:
    slope = run_output["lagged_slope"]
    slope_lo, slope_hi = PREDICTION["predicted_magnitude_range"]
    fails = []

    if np.isnan(slope):
        fails.append("lagged_slope is NaN (insufficient data)")
    elif slope < 0:
        fails.append(
            f"slope {slope:.4f} < 0 (null direction realized — coupling reversed)"
        )
    elif slope < slope_lo:
        fails.append(
            f"slope {slope:.4f} < {slope_lo:.2f} floor "
            f"(cascade-step below detectable threshold)"
        )
    elif slope > slope_hi:
        fails.append(
            f"slope {slope:.4f} > {slope_hi:.2f} ceiling "
            f"(over-prediction — implausible synthetic-curation)"
        )

    if not fails:
        verdict = "pass"
        rationale = (
            f"lagged regression slope {slope:.4f} ∈ [{slope_lo:.2f}, {slope_hi:.2f}]. "
            f"DK→DE-North wind-cascade observable at 1y lag in synthetic v1. "
            f"Domino-step 1 supported as a candidate mechanism. NOT a real-grid "
            f"claim — v2-ratchet to real ENTSO-E cross-border flow data via "
            f"PR #10 frozen-snapshot required."
        )
    else:
        verdict = "fail"
        rationale = "Voice enters the null-voice ledger per §3.4. Failures: " + " ; ".join(fails)

    return {
        "verdict": verdict,
        "lagged_slope": slope,
        "lagged_intercept": run_output["lagged_intercept"],
        "n_lagged_pairs": run_output["n_lagged_pairs"],
        "lag_years": run_output["lag_years"],
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def emit_sidecar(verdict: dict, run_output: dict, output_path: str) -> str:
    unit = {
        "voice_name": VOICE_NAME,
        "prediction": PREDICTION,
        "kill_condition": KILL_CONDITION,
        "run_protocol": RUN_PROTOCOL,
        "run_output": run_output,
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


def main():
    print("=" * 72)
    print(f"voice unit: {VOICE_NAME}")
    print("=" * 72)
    print(f"predicted:    slope ∈ {PREDICTION['predicted_magnitude_range']} at 1y lag, positive direction")
    print(f"kill rule:    {KILL_CONDITION['rule']}")
    print(f"run:          {RUN_PROTOCOL['entry_point']}")
    print()
    print("running DK→DE-North wind-cascade coupling measurement...")
    out = run_voice()
    print(f"  years:                       {out['years'][0]}–{out['years'][-1]}")
    print(f"  dk wind-export share (%):    {[round(v, 1) for v in out['dk_wind_export_share_pct']]}")
    print(f"  de-north wind capacity (GW): {[round(v, 1) for v in out['de_north_wind_capacity_gw']]}")
    print(f"  dk yoy export change:        {[round(v, 2) for v in out['dk_yoy_export_change']]}")
    print(f"  de yoy capacity change:      {[round(v, 2) for v in out['de_yoy_capacity_change']]}")
    print(f"  lag (years):                 {out['lag_years']}")
    print(f"  n lagged pairs:              {out['n_lagged_pairs']}")
    print(f"  lagged slope:                {out['lagged_slope']:.4f}")
    print(f"  lagged intercept:            {out['lagged_intercept']:.4f}")
    print()
    verdict = compute_verdict(out)
    print(f"  verdict: {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    print()

    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, out, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
