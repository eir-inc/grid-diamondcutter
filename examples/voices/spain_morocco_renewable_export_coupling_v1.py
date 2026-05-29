# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
spain_morocco_renewable_export_coupling_v1.py — §3.2 coupling voice.

Tests Eugene's positive-cascade domino-step 2 hypothesis: Spain solar surplus
+ ES-MA 700 MW interconnect (extended to 1400 MW capacity) → Morocco solar
buildout response. Inverse of the typical EU→neighbor cascade — here both
regions are growing renewables but Spain leads on solar PV; Morocco's response
is policy-driven (Noor program 2016+).

Distinguishes from PR #35 (DK→DE FAIL on over-correlation) because Morocco
solar growth is step-function (Noor 1 2016 / Noor 2-3 2018) rather than smooth
S-curve. The geometry should be lumpier, testing whether the bounded kills
operate differently on step-function substrates vs S-curve substrates.

Per §1 honesty bound: SYNTHETIC v1 from publicly-cited Red Eléctrica de España
+ ONEE Morocco + IEA milestones. v2-ratchet to ENTSO-E ES-MA cross-border
flow + ONEE annual report real data via PR #10 frozen-snapshot required.

Eugene's domino-dynamics frame: this is step-2 of the chain. Asymmetric pair
(developed grid → developing grid) tests cascade hypothesis under different
receiving-region maturity than the DK→DE EU-internal case.
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

VOICE_NAME = "spain_morocco_renewable_export_coupling_v1"

PREDICTION = {
    "kind": "coupling_cross_substrate",
    "substrates": [
        "spain_solar_pv_capacity_yoy_growth_2010_2023_synthetic",
        "morocco_solar_capacity_yoy_growth_2010_2023_synthetic",
    ],
    "named_residual": "spain_solar_yoy_change_predicts_morocco_solar_yoy_growth_at_1y_lag_via_es_ma_interconnect_mechanism",
    "predicted_direction": "positive",
    "predicted_magnitude_range": [0.10, 0.80],  # wider than DK→DE because step-function geometry
    "null_direction": "slope_approximately_zero_or_negative_no_cascade_observable",
    "rationale": (
        "Eugene's domino-step 2 hypothesis. Tests asymmetric developed→developing "
        "pair with step-function receiving-region capacity (Noor solar 2016/2018 "
        "events) rather than smooth S-curve. Wider magnitude range [0.10, 0.80] "
        "because step-function geometry naturally produces higher peak slopes "
        "during ramp-years and lower elsewhere. v1 tests whether the cascade-"
        "mechanism is detectable specifically when receiver-region has policy-"
        "triggered step-function capacity rather than continuous build-out."
    ),
}

KILL_CONDITION = {
    "metric": "es_to_ma_solar_coupling_lagged_slope",
    "rule": (
        "fail if slope < 0.10 (cascade-step below detectable threshold); "
        "fail if slope > 0.80 (over-prediction / implausible curation); "
        "fail if slope < 0 (null direction realized — coupling reversed)"
    ),
    "rationale": (
        "Composite metric — lagged linear-regression slope of MA solar YoY "
        "growth on ES solar YoY change at 1y lag. Magnitude window widened "
        "for step-function receiver-substrate geometry."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/spain_morocco_renewable_export_coupling_v1.py",
    "source_file": "examples/voices/spain_morocco_renewable_export_coupling_v1.py",
    "input_parameters": {
        "calibration_source": "synthetic_v1_publicly_cited_REE_ONEE_IEA_milestones",
        "years": list(range(2010, 2024)),
        # Spain installed solar PV capacity year-end (GW, synthetic-calibrated from
        # publicly-cited Red Eléctrica de España data — Spain solar was ~3.8 GW
        # in 2010, stagnated 2013-2018 due to sun-tax, exploded post-2019
        # repeal to ~25 GW by 2023)
        "es_solar_capacity_gw": [
            3.8, 4.2, 4.5, 4.6, 4.7, 4.8, 4.9, 5.0, 5.1, 8.7,
            13.7, 17.4, 22.5, 27.8,
        ],
        # Morocco installed solar capacity year-end (MW, synthetic-calibrated
        # from publicly-cited ONEE/MASEN — Noor 1 (160 MW) 2016, Noor 2+3
        # (350 MW) 2018, additional ~700 MW added 2020-2023; total ~1700 MW
        # by end-2023; step-function geometry)
        "ma_solar_capacity_mw": [
            20, 20, 20, 20, 30, 40, 200, 220, 580, 600,
            760, 1100, 1450, 1700,
        ],
        "lag_years": 1,
        "random_seed": 1492,
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
    return [series[i + 1] - series[i] for i in range(len(series) - 1)]


def normalize(series: list[float]) -> list[float]:
    """Per-series min-max normalization so units don't dominate the slope."""
    s_min, s_max = min(series), max(series)
    rng = s_max - s_min
    if rng == 0:
        return [0.0 for _ in series]
    return [(v - s_min) / rng for v in series]


def lagged_regression_slope(x: list[float], y: list[float], lag: int) -> tuple[float, float, int]:
    if lag <= 0:
        x_arr = np.array(x)
        y_arr = np.array(y)
    else:
        x_arr = np.array(x[:-lag])
        y_arr = np.array(y[lag:])
    if len(x_arr) < 3:
        return float("nan"), float("nan"), len(x_arr)
    slope, intercept = np.polyfit(x_arr, y_arr, 1)
    return float(slope), float(intercept), len(x_arr)


def run_voice() -> dict:
    np.random.seed(RUN_PROTOCOL["input_parameters"]["random_seed"])
    es = RUN_PROTOCOL["input_parameters"]["es_solar_capacity_gw"]
    ma = RUN_PROTOCOL["input_parameters"]["ma_solar_capacity_mw"]
    lag = RUN_PROTOCOL["input_parameters"]["lag_years"]

    es_yoy = yoy_change(es)
    ma_yoy = yoy_change(ma)
    # Normalize YoY changes to unit-free [0, 1] before slope estimation
    # so GW vs MW scale doesn't artificially blow up the slope.
    es_yoy_norm = normalize(es_yoy)
    ma_yoy_norm = normalize(ma_yoy)
    slope, intercept, n_pairs = lagged_regression_slope(es_yoy_norm, ma_yoy_norm, lag)

    return {
        "years": RUN_PROTOCOL["input_parameters"]["years"],
        "es_solar_capacity_gw": es,
        "ma_solar_capacity_mw": ma,
        "es_yoy_change_gw": es_yoy,
        "ma_yoy_change_mw": ma_yoy,
        "es_yoy_normalized": es_yoy_norm,
        "ma_yoy_normalized": ma_yoy_norm,
        "lag_years": lag,
        "n_lagged_pairs": int(n_pairs),
        "lagged_slope_normalized": slope,
        "lagged_intercept_normalized": intercept,
    }


def compute_verdict(run_output: dict) -> dict:
    slope = run_output["lagged_slope_normalized"]
    slope_lo, slope_hi = PREDICTION["predicted_magnitude_range"]
    fails = []

    if np.isnan(slope):
        fails.append("lagged_slope is NaN (insufficient data)")
    elif slope < 0:
        fails.append(f"slope {slope:.4f} < 0 (null direction realized)")
    elif slope < slope_lo:
        fails.append(f"slope {slope:.4f} < {slope_lo:.2f} floor (below detectable threshold)")
    elif slope > slope_hi:
        fails.append(f"slope {slope:.4f} > {slope_hi:.2f} ceiling (over-prediction)")

    if not fails:
        verdict = "pass"
        rationale = (
            f"normalized lagged regression slope {slope:.4f} ∈ "
            f"[{slope_lo:.2f}, {slope_hi:.2f}]. ES→MA solar-cascade observable at "
            f"1y lag in synthetic v1 with step-function receiver geometry. "
            f"Domino-step 2 supported as a candidate mechanism for asymmetric "
            f"developed→developing pair. NOT a real-grid claim — v2-ratchet to "
            f"real ENTSO-E ES-MA flow + ONEE capacity data required."
        )
    else:
        verdict = "fail"
        rationale = "Voice enters the null-voice ledger per §3.4. Failures: " + " ; ".join(fails)

    return {
        "verdict": verdict,
        "lagged_slope_normalized": slope,
        "lagged_intercept_normalized": run_output["lagged_intercept_normalized"],
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
    print(f"predicted:    normalized slope ∈ {PREDICTION['predicted_magnitude_range']} at 1y lag, positive")
    print(f"kill rule:    {KILL_CONDITION['rule']}")
    print(f"run:          {RUN_PROTOCOL['entry_point']}")
    print()
    print("running ES→MA solar-cascade coupling measurement...")
    out = run_voice()
    print(f"  years:                       {out['years'][0]}–{out['years'][-1]}")
    print(f"  es solar capacity (GW):      {[round(v, 1) for v in out['es_solar_capacity_gw']]}")
    print(f"  ma solar capacity (MW):      {out['ma_solar_capacity_mw']}")
    print(f"  es yoy change (GW):          {[round(v, 2) for v in out['es_yoy_change_gw']]}")
    print(f"  ma yoy change (MW):          {[round(v, 1) for v in out['ma_yoy_change_mw']]}")
    print(f"  lag (years):                 {out['lag_years']}")
    print(f"  n lagged pairs:              {out['n_lagged_pairs']}")
    print(f"  normalized lagged slope:     {out['lagged_slope_normalized']:.4f}")
    print(f"  normalized lagged intercept: {out['lagged_intercept_normalized']:.4f}")
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
