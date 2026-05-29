# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
japan_post_fukushima_acceleration_v1.py — §3.1 polyphony voice.

Tests whether the March 2011 Fukushima exogenous event triggered a MEASURABLE
acceleration in Japan's renewable-share trajectory — the forward-mechanism
complement to §4.2's existing Japan voice (PR #11, which tested qualitative
recovery of the cascade event itself).

This voice tests Eugene's "lead time on regulation" question on a known case:
Japan's FIT policy (Feed-in Tariff, enacted 2011, effective 2012-13) was the
direct regulatory response to Fukushima. If the §0 mechanism is observable at
the trajectory level, the post-FIT renewable-share rate should show a
recognizable inflection — analogous to threshold_cascade_v2 (PR #15) PASS
condition.

Public IEA / METI calibration (synthetic v1, cited inline; v2-ratchet to
PR #10 frozen-snapshot once IEA bulk extracts ship):
  Japan renewable share of electricity generation (excluding pumped hydro):
    2010: ~10%, 2012: ~11%, 2014: ~13%, 2017: ~17%, 2020: ~22%, 2023: ~26%
  Sources for v2-ratchet: METI Agency for Natural Resources and Energy
  Annual Energy Report; IEA Country Profiles; Renewables 2023.

See §1 honesty bounds — this is a self-test of methodology applied to a
synthetic-calibrated v1 substrate based on publicly-cited milestones.
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

VOICE_NAME = "japan_post_fukushima_acceleration_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "japan_renewable_share_trajectory_2010_2023_synthetic",
    "named_residual": "post_fukushima_acceleration_breakpoint_in_japan_renewable_share_rate",
    "predicted_breakpoint_range": [2011, 2014],
    "predicted_piecewise_improvement_floor": 0.20,
    "rationale": (
        "Fukushima (March 2011) triggered Japan's FIT policy (enacted 2011, "
        "effective 2012). If §0's cascade-mechanism is observable in this case, "
        "the renewable-share rate should show a piecewise-linear inflection "
        "with breakpoint in [2011, 2014]. Forward-mechanism test on a real "
        "historical case complement to §4.2 Japan voice (PR #11) which tested "
        "qualitative-trajectory recovery of the cascade event itself."
    ),
}

KILL_CONDITION = {
    "metric": "post_fukushima_acceleration_validity",
    "rule": (
        "fail if piecewise_rss / linear_rss > 0.80 (no piecewise improvement), "
        "fail if recovered_breakpoint_year < 2011 or > 2014 "
        "(recovery outside predicted window — would suggest acceleration "
        "predates Fukushima or lags FIT effectiveness by too much)"
    ),
    "rationale": (
        "Composite metric decomposable into two underlying numerical checks, "
        "both computable from the publicly-cited synthetic trajectory alone. "
        "Piecewise-improvement ratio tests threshold-class shape. "
        "Breakpoint-window test rejects spurious recoveries outside the "
        "exogenous-event-to-policy-effectiveness window."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/japan_post_fukushima_acceleration_v1.py",
    "source_file": "examples/voices/japan_post_fukushima_acceleration_v1.py",
    "input_parameters": {
        "calibration_source": "synthetic_v1_from_publicly_cited_METI_IEA_milestones",
        "japan_re_share_milestones": {
            "2010": 0.10, "2012": 0.11, "2014": 0.13, "2017": 0.17,
            "2020": 0.22, "2023": 0.26,
        },
        "fukushima_event_year": 2011,
        "fit_policy_effective_year": 2012,
        "predicted_breakpoint_range": [2011, 2014],
        "random_seed": 311,
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
    sorted_years = sorted(int(y) for y in milestones)
    sorted_vals = [milestones[str(y)] for y in sorted_years]
    return np.interp(years, sorted_years, sorted_vals)


def fit_linear(rhos: np.ndarray, residuals: np.ndarray) -> tuple:
    slope, intercept = np.polyfit(rhos, residuals, 1)
    predicted = slope * rhos + intercept
    rss = float(((residuals - predicted) ** 2).sum())
    return float(slope), float(intercept), rss


def fit_piecewise_two_segment(rhos: np.ndarray, residuals: np.ndarray) -> tuple:
    """Brute-force breakpoint search across all interior points."""
    best_bp = None
    best_rss = float("inf")
    for i in range(2, len(rhos) - 2):
        bp = float(rhos[i])
        left_x, left_y = rhos[: i + 1], residuals[: i + 1]
        right_x, right_y = rhos[i:], residuals[i:]
        ls, li = np.polyfit(left_x, left_y, 1)
        rs, ri = np.polyfit(right_x, right_y, 1)
        left_predicted = ls * left_x + li
        right_predicted = rs * right_x + ri
        rss = float(((left_y - left_predicted) ** 2).sum() + ((right_y - right_predicted) ** 2).sum())
        if rss < best_rss:
            best_rss = rss
            best_bp = bp
    return best_bp, best_rss


def run_voice() -> dict:
    np.random.seed(RUN_PROTOCOL["input_parameters"]["random_seed"])
    years = np.arange(2010, 2024)
    milestones = RUN_PROTOCOL["input_parameters"]["japan_re_share_milestones"]
    shares = interpolate_milestones(milestones, years)
    # year-over-year rates (the residual we test for acceleration in)
    rates = np.diff(shares)
    rate_years = years[:-1].astype(float)   # year-N rate is share-of-N+1 minus share-of-N
    _, _, linear_rss = fit_linear(rate_years, rates)
    breakpoint_year, piecewise_rss = fit_piecewise_two_segment(rate_years, rates)
    piecewise_rss_ratio = piecewise_rss / linear_rss if linear_rss > 0 else float("inf")
    return {
        "years": [int(y) for y in years],
        "japan_renewable_share": [float(s) for s in shares],
        "rate_years": [int(y) for y in rate_years],
        "yoy_rates": [float(r) for r in rates],
        "linear_rss": float(linear_rss),
        "piecewise_rss": float(piecewise_rss),
        "piecewise_rss_ratio": float(piecewise_rss_ratio),
        "recovered_breakpoint_year": float(breakpoint_year) if breakpoint_year is not None else None,
    }


# ===========================================================================
# Field 5: verdict
# ===========================================================================

def compute_verdict(run_output: dict) -> dict:
    bp = run_output["recovered_breakpoint_year"]
    ratio = run_output["piecewise_rss_ratio"]
    bp_lo, bp_hi = PREDICTION["predicted_breakpoint_range"]
    ratio_max = 1.0 - PREDICTION["predicted_piecewise_improvement_floor"]

    fails = []
    if ratio > ratio_max:
        fails.append(
            f"piecewise_rss_ratio {ratio:.4f} > {ratio_max:.4f} "
            f"(piecewise fit did not improve on linear by ≥ "
            f"{PREDICTION['predicted_piecewise_improvement_floor']:.0%})"
        )
    if bp is None or bp < bp_lo or bp > bp_hi:
        fails.append(
            f"recovered breakpoint year {bp} outside predicted window "
            f"[{bp_lo}, {bp_hi}] (Fukushima→FIT-effectiveness window)"
        )

    if not fails:
        verdict = "pass"
        rationale = (
            f"Recovered breakpoint year {bp:.0f} ∈ [{bp_lo}, {bp_hi}] AND "
            f"piecewise_rss_ratio {ratio:.4f} ≤ {ratio_max:.4f}. The "
            f"methodology recovers a measurable post-Fukushima acceleration "
            f"in Japan's renewable-share rate at the Fukushima→FIT window. "
            f"§0 forward-mechanism observable on this real historical case "
            f"at synthetic-calibrated v1. v2-ratchet to real METI data required "
            f"for any external real-grid claim."
        )
    else:
        verdict = "fail"
        rationale = (
            "Voice enters the null-voice ledger per §3.4. Failures: "
            + " ; ".join(fails)
        )

    return {
        "verdict": verdict,
        "recovered_breakpoint_year": bp,
        "piecewise_rss_ratio": ratio,
        "linear_rss": run_output["linear_rss"],
        "piecewise_rss": run_output["piecewise_rss"],
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
    print(f"predicted:    piecewise_rss_ratio ≤ 0.80 AND breakpoint_year ∈ {PREDICTION['predicted_breakpoint_range']}")
    print(f"kill rule:    {KILL_CONDITION['rule']}")
    print(f"run:          {RUN_PROTOCOL['entry_point']}")
    print()
    print("running post-Fukushima acceleration test...")
    out = run_voice()
    print(f"  years: {out['years'][0]}–{out['years'][-1]}")
    print(f"  japan RE share: {[round(s, 2) for s in out['japan_renewable_share']]}")
    print(f"  YoY rates:       {[round(r, 3) for r in out['yoy_rates']]}")
    print(f"  linear_rss:    {out['linear_rss']:.6f}")
    print(f"  piecewise_rss: {out['piecewise_rss']:.6f}")
    print(f"  ratio:         {out['piecewise_rss_ratio']:.4f}")
    print(f"  recovered breakpoint year: {out['recovered_breakpoint_year']}")
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
