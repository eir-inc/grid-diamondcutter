# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
germany_neighbor_renewable_coupling_v1.py — §3.1 coupling voice.

Tests the network-effect mechanism that Eugene named in the §0 conversation:
"network effect of shipping renewable gen power from near neighbors." Pre-committed
hypothesis: Germany's renewable-share trajectory leads France's renewable-share
trajectory by ~12 months, with a positive bounded coupling slope.

This voice is the complement to miles's PR #24 network_amplification_coupling_v1
(FAIL, substrate-property-level: amplification vs resilience). PR #24 tested
whether the substrate's coupling parameter has the right SIGN. This voice tests
whether the trajectory-level lagged correlation between two specific regions is
recoverable from publicly-cited rollout milestones.

v1 = SYNTHETIC calibrated from public-knowledge rollout milestones (named in
docstring). v2-ratchet = real ENTSO-E data via PR #10 frozen-snapshot when
groove's contract ships fully. See §1 honesty bounds for scope; §7.5 for
proxy-data limitations.

PUBLICLY-CITED CALIBRATION (synthetic v1, sources to be cited in v2-ratchet):
  Germany renewable share of electricity generation:
    2010: ~17%, 2015: ~30%, 2020: ~45%, 2023: ~52%
  France renewable share of electricity generation:
    2010: ~16%, 2015: ~17%, 2020: ~22%, 2023: ~27%
  (sources for v2: AGEB / Energy Charts for DE; RTE Bilan Electrique for FR)
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
# §3.1 — The per-voice unit (five required fields)
# ===========================================================================

VOICE_NAME = "germany_neighbor_renewable_coupling_v1"

# Field 2: predicted residual coupling — COUPLING discipline (§3.2)
PREDICTION = {
    "kind": "coupling_cross_substrate",
    "substrate_a": "germany_renewable_share_trajectory_2010_2023_synthetic",
    "substrate_b": "france_renewable_share_trajectory_2010_2023_synthetic",
    "named_residual": "lagged_correlation_germany_renewable_growth_drives_france_renewable_growth",
    "predicted_direction": "positive: Germany RES-share rate leads France RES-share rate at +1y lag",
    "predicted_magnitude_range": [0.10, 0.50],
    "predicted_lag_years": 1,
    "null_direction": "zero or negative slope (no link / reversed direction)",
    "rationale": (
        "Network-effect hypothesis Eugene named: neighboring-region renewable "
        "export undermines local fossil capex pricing, triggering downstream "
        "renewable buildout. If observable at the trajectory level, Germany's "
        "renewable surge should precede France's growth with a positive bounded "
        "lagged coupling. Synthetic v1 calibration from publicly-cited rollout "
        "milestones (named in docstring); v2-ratchet to real ENTSO-E data."
    ),
}

# Field 3: kill condition — coupling discipline (single composite metric)
KILL_CONDITION = {
    "metric": "linear_fit_slope_france_renewable_rate_vs_germany_renewable_rate_lagged_1year",
    "predicted_range": [0.10, 0.50],
    "rule": (
        "fail if slope < 0.10 (below floor / weak link), "
        "fail if slope > 0.50 (above ceiling / over-prediction), "
        "fail if slope < 0 (null direction realized / reversed)"
    ),
    "rationale": (
        "Linear-fit slope of France's RES-share rate vs Germany's RES-share rate "
        "lagged by 1 year. Computable from synthetic trajectories alone. Three "
        "honest failure outcomes named per §3.2 coupling discipline; null "
        "direction explicit so its realization is registry-acceptable null."
    ),
}

# Field 4: run protocol
RUN_PROTOCOL = {
    "entry_point": "python examples/voices/germany_neighbor_renewable_coupling_v1.py",
    "source_file": "examples/voices/germany_neighbor_renewable_coupling_v1.py",
    "input_parameters": {
        "calibration_source": "synthetic_v1_from_publicly_cited_milestones",
        "germany_milestones": {
            "2010": 0.17, "2015": 0.30, "2020": 0.45, "2023": 0.52,
        },
        "france_milestones": {
            "2010": 0.16, "2015": 0.17, "2020": 0.22, "2023": 0.27,
        },
        "lag_years": 1,
        "interpolation": "piecewise_linear_between_milestones",
        "random_seed": 1979,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Voice implementation
# ===========================================================================

def interpolate_milestones(milestones: dict, years: np.ndarray) -> np.ndarray:
    """Piecewise-linear interpolation of milestone dict over a year range."""
    sorted_years = sorted(int(y) for y in milestones)
    sorted_vals = [milestones[str(y)] for y in sorted_years]
    return np.interp(years, sorted_years, sorted_vals)


def compute_lagged_coupling(years: np.ndarray, germany_share: np.ndarray,
                            france_share: np.ndarray, lag: int) -> tuple:
    """Compute year-over-year growth rates for both trajectories, align with lag,
    fit linear slope of france_rate(t) vs germany_rate(t - lag).
    """
    # year-over-year rates
    de_rate = np.diff(germany_share)   # year N to year N+1
    fr_rate = np.diff(france_share)
    # align: france_rate at year (lag+k) vs germany_rate at year k
    if lag > 0:
        de_aligned = de_rate[:-lag]
        fr_aligned = fr_rate[lag:]
    elif lag == 0:
        de_aligned = de_rate
        fr_aligned = fr_rate
    else:
        de_aligned = de_rate[-lag:]
        fr_aligned = fr_rate[:lag]

    if len(de_aligned) < 2:
        return 0.0, 0.0, de_aligned, fr_aligned

    slope, intercept = np.polyfit(de_aligned, fr_aligned, 1)
    return float(slope), float(intercept), de_aligned, fr_aligned


def run_voice() -> dict:
    np.random.seed(RUN_PROTOCOL["input_parameters"]["random_seed"])
    years = np.arange(2010, 2024)
    de_milestones = RUN_PROTOCOL["input_parameters"]["germany_milestones"]
    fr_milestones = RUN_PROTOCOL["input_parameters"]["france_milestones"]
    lag = RUN_PROTOCOL["input_parameters"]["lag_years"]
    de_share = interpolate_milestones(de_milestones, years)
    fr_share = interpolate_milestones(fr_milestones, years)
    slope, intercept, de_rates, fr_rates = compute_lagged_coupling(
        years, de_share, fr_share, lag
    )
    return {
        "years": [int(y) for y in years],
        "germany_renewable_share": [float(s) for s in de_share],
        "france_renewable_share": [float(s) for s in fr_share],
        "germany_yoy_rates_aligned": [float(r) for r in de_rates],
        "france_yoy_rates_aligned": [float(r) for r in fr_rates],
        "linear_fit_slope_france_rate_vs_germany_rate_lagged": float(slope),
        "linear_fit_intercept": float(intercept),
    }


# ===========================================================================
# Field 5: verdict
# ===========================================================================

def compute_verdict(run_output: dict) -> dict:
    slope = run_output["linear_fit_slope_france_rate_vs_germany_rate_lagged"]
    lo, hi = PREDICTION["predicted_magnitude_range"]
    fails = []
    if slope < 0:
        fails.append(f"slope {slope:.4f} < 0 — null direction realized (reversed)")
    elif slope < lo:
        fails.append(f"slope {slope:.4f} < {lo} — below predicted floor (weak/no link)")
    elif slope > hi:
        fails.append(f"slope {slope:.4f} > {hi} — above predicted ceiling (over-prediction)")

    if not fails:
        verdict = "pass"
        rationale = (
            f"Lagged-coupling slope {slope:.4f} ∈ [{lo}, {hi}] — Germany's "
            f"renewable-share growth rate leads France's by {PREDICTION['predicted_lag_years']} year "
            f"with magnitude in the pre-committed range. Network-effect "
            f"mechanism observable at the trajectory level on synthetic-calibrated v1. "
            f"v2-ratchet to real ENTSO-E required for any real-grid claim."
        )
    else:
        verdict = "fail"
        rationale = (
            "Voice enters the null-voice ledger per §3.4. Failures: "
            + " ; ".join(fails)
        )

    return {
        "verdict": verdict,
        "slope": slope,
        "predicted_range": [lo, hi],
        "lag_years": PREDICTION["predicted_lag_years"],
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def emit_sidecar(verdict: dict, sweep_output: dict, output_path: str) -> str:
    unit = {
        "voice_name": VOICE_NAME,
        "prediction": PREDICTION,
        "kill_condition": KILL_CONDITION,
        "run_protocol": RUN_PROTOCOL,
        "run_output": sweep_output,
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
    print(f"predicted:    slope of (FR rate vs DE rate lagged 1y) ∈ {PREDICTION['predicted_magnitude_range']}")
    print(f"kill rule:    {KILL_CONDITION['rule']}")
    print(f"run:          {RUN_PROTOCOL['entry_point']}")
    print()
    print("running synthetic-calibrated trajectory coupling test...")
    out = run_voice()
    print(f"  years: {out['years'][0]}–{out['years'][-1]}")
    print(f"  germany RES share: {[round(s, 2) for s in out['germany_renewable_share']]}")
    print(f"  france  RES share: {[round(s, 2) for s in out['france_renewable_share']]}")
    print(f"  linear slope (FR rate vs DE rate lag+1):  {out['linear_fit_slope_france_rate_vs_germany_rate_lagged']:.4f}")
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
