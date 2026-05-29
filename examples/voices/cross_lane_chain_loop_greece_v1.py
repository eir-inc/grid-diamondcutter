# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
cross_lane_chain_loop_greece_v1.py — §3.1 polyphony voice.

FIRST CROSS-LANE REGISTRY VOICE — cajal lane consumes miles lane deliverables.
Closes the methodology chain by using miles's lead-time prior (PR #30, #33, #40)
as INPUT to predict an inflection-year window for Greece RE-share trajectory,
then tests the prediction against publicly-cited synthetic-v1 GR data.

The miles lead-time chain:
  PR #30 regulatory_lead_time_v1: mean lead time 8.83y across DK/DE/ES/PT/UK/IT
  PR #33 leader_cohort_loo_cv_v1: LOO MAE 1.47y validates the prior
  PR #40 regulatory_lead_time_v2: 12-country expanded cohort, 8.92y, EU 8.83y

Greece is a NON-LEADER cohort country with a documented FIT policy year:
  - 2006 Law 3468/2006 first comprehensive RES support framework
  - 2009 Law 3851/2010 (passed 2010, retroactive effective 2009) expanded
    FIT for renewables — this is the principal Greece RES policy anchor

Using miles's calibrated prior (8.83y ± 1.47y MAE), predicted inflection-year
window for Greece:
  policy_year: 2009 (Greece principal FIT)
  prior_mean: 8.83y
  prior_mae_halfwidth: 1.47y
  predicted_inflection_window: [2009 + 8.83 - 1.47, 2009 + 8.83 + 1.47]
                              = [2016.36, 2019.30]

Per §1 honesty bound: SYNTHETIC v1 from publicly-cited IEA + Eurostat
milestones for Greece RE-share. v2-ratchet to real Eurostat / ENTSO-E
data via PR #10 frozen-snapshot required for any external claim.

Cross-lane two-witness implication: if the voice PASSes, the methodology
chain {prior → CV → application} closes at the cajal-lane consumer level.
If it FAILs, the chain is broken at the new-country generalization step,
informative data on miles's prior's true generalizability.
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
# §3.1 — polyphony voice (cross-lane chain-loop closer)
# ===========================================================================

VOICE_NAME = "cross_lane_chain_loop_greece_v1"

# Imported from miles PR #30/#33/#40 lead-time chain
MILES_LEAD_TIME_PRIOR = {
    "source_chain": ["PR #30 regulatory_lead_time_v1", "PR #33 leader_cohort_loo_cv_v1", "PR #40 regulatory_lead_time_v2"],
    "mean_lead_time_years": 8.83,    # PR #30 EU cohort, also PR #40 EU sub-cohort
    "loo_mae_years": 1.47,            # PR #33 calibration-honest uncertainty
    "expanded_cohort_mean_years": 8.92,  # PR #40 12-country (EU 8.83, non-EU 9.00)
}

GREECE_POLICY_ANCHOR_YEAR = 2009  # Greece FIT principal policy (Law 3851/2010 retroactive eff 2009)

_pred_lo = GREECE_POLICY_ANCHOR_YEAR + MILES_LEAD_TIME_PRIOR["mean_lead_time_years"] - MILES_LEAD_TIME_PRIOR["loo_mae_years"]
_pred_hi = GREECE_POLICY_ANCHOR_YEAR + MILES_LEAD_TIME_PRIOR["mean_lead_time_years"] + MILES_LEAD_TIME_PRIOR["loo_mae_years"]

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "greece_renewable_share_trajectory_2010_2023_synthetic_v1_for_cross_lane_chain_test",
    "named_residual": "greece_re_share_inflection_year_falls_within_miles_prior_calibrated_window",
    "policy_anchor_year": GREECE_POLICY_ANCHOR_YEAR,
    "miles_prior_chain": MILES_LEAD_TIME_PRIOR,
    "predicted_inflection_window": [round(_pred_lo, 2), round(_pred_hi, 2)],
    "piecewise_improvement_floor": 0.20,
    "rationale": (
        "Closes miles lead-time chain (#30 → #33 → #40) by applying the "
        "calibrated prior to Greece (non-leader cohort, documented FIT policy "
        "anchor 2009). Predicts inflection year ∈ "
        f"[{round(_pred_lo, 2)}, {round(_pred_hi, 2)}] AND piecewise-linear "
        "fit improves on linear by ≥ 20% (same methodology as cajal #7 + #32 "
        "polyphony voice geometry). PASS = chain closes at cross-lane consumer "
        "level; FAIL = chain breaks at new-country generalization."
    ),
}

KILL_CONDITION = {
    "metric": "greece_inflection_year_validity_under_miles_prior",
    "rule": (
        "fail if recovered_breakpoint_year outside predicted_inflection_window "
        "(prior does not generalize to Greece); "
        "fail if piecewise_rss / linear_rss > 0.80 (no inflection detectable "
        "regardless of year window)"
    ),
    "rationale": (
        "Composite metric — inflection-year-within-window AND piecewise-fit-"
        "improves-on-linear. First condition tests chain closure; second "
        "rejects spurious recoveries on flat substrate."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/cross_lane_chain_loop_greece_v1.py",
    "source_file": "examples/voices/cross_lane_chain_loop_greece_v1.py",
    "input_parameters": {
        "calibration_source": "synthetic_v1_from_publicly_cited_IEA_Eurostat_milestones",
        # Greece RE share of electricity generation (% of total, synthetic-v1 from
        # publicly-cited Eurostat + IEA — GR was ~17% RE in 2010, reached ~31%
        # by 2020 post-2014 plateau exit, ~46% by 2023)
        "greece_re_share_milestones": {
            "2010": 0.17, "2012": 0.21, "2014": 0.21, "2016": 0.22, "2018": 0.26,
            "2020": 0.31, "2022": 0.41, "2023": 0.46,
        },
        "policy_anchor_year": GREECE_POLICY_ANCHOR_YEAR,
        "miles_prior_mean": MILES_LEAD_TIME_PRIOR["mean_lead_time_years"],
        "miles_prior_mae": MILES_LEAD_TIME_PRIOR["loo_mae_years"],
        "random_seed": 1821,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Voice implementation (matches cajal #7 + #32 methodology)
# ===========================================================================

def interpolate_milestones(milestones: dict, years: np.ndarray) -> np.ndarray:
    sorted_years = sorted(int(y) for y in milestones)
    sorted_vals = [milestones[str(y)] for y in sorted_years]
    return np.interp(years, sorted_years, sorted_vals)


def fit_linear(xs: np.ndarray, ys: np.ndarray) -> tuple:
    slope, intercept = np.polyfit(xs, ys, 1)
    predicted = slope * xs + intercept
    rss = float(((ys - predicted) ** 2).sum())
    return float(slope), float(intercept), rss


def fit_piecewise_two_segment(xs: np.ndarray, ys: np.ndarray) -> tuple:
    best_bp = None
    best_rss = float("inf")
    for i in range(2, len(xs) - 2):
        bp = float(xs[i])
        lx, ly = xs[:i + 1], ys[:i + 1]
        rx, ry = xs[i:], ys[i:]
        ls, li = np.polyfit(lx, ly, 1)
        rs, ri = np.polyfit(rx, ry, 1)
        lp = ls * lx + li
        rp = rs * rx + ri
        rss = float(((ly - lp) ** 2).sum() + ((ry - rp) ** 2).sum())
        if rss < best_rss:
            best_rss = rss
            best_bp = bp
    return best_bp, best_rss


def run_voice() -> dict:
    np.random.seed(RUN_PROTOCOL["input_parameters"]["random_seed"])
    years = np.arange(2010, 2024)
    milestones = RUN_PROTOCOL["input_parameters"]["greece_re_share_milestones"]
    shares = interpolate_milestones(milestones, years)
    # year-over-year rates (test for inflection)
    rates = np.diff(shares)
    rate_years = years[:-1].astype(float)
    _, _, linear_rss = fit_linear(rate_years, rates)
    breakpoint_year, piecewise_rss = fit_piecewise_two_segment(rate_years, rates)
    piecewise_rss_ratio = piecewise_rss / linear_rss if linear_rss > 0 else float("inf")
    return {
        "years": [int(y) for y in years],
        "greece_re_share": [float(s) for s in shares],
        "rate_years": [int(y) for y in rate_years],
        "yoy_rates": [float(r) for r in rates],
        "linear_rss": float(linear_rss),
        "piecewise_rss": float(piecewise_rss),
        "piecewise_rss_ratio": float(piecewise_rss_ratio),
        "recovered_breakpoint_year": float(breakpoint_year) if breakpoint_year is not None else None,
        "policy_anchor_year": GREECE_POLICY_ANCHOR_YEAR,
        "predicted_inflection_window": PREDICTION["predicted_inflection_window"],
        "miles_prior_chain": PREDICTION["miles_prior_chain"],
    }


def compute_verdict(run_output: dict) -> dict:
    bp = run_output["recovered_breakpoint_year"]
    ratio = run_output["piecewise_rss_ratio"]
    bp_lo, bp_hi = PREDICTION["predicted_inflection_window"]
    ratio_max = 1.0 - PREDICTION["piecewise_improvement_floor"]
    fails = []

    if ratio > ratio_max:
        fails.append(
            f"piecewise_rss_ratio {ratio:.4f} > {ratio_max:.4f} "
            f"(piecewise fit did not improve on linear by ≥ "
            f"{PREDICTION['piecewise_improvement_floor']:.0%})"
        )
    if bp is None or bp < bp_lo or bp > bp_hi:
        fails.append(
            f"recovered breakpoint year {bp} outside miles-prior-calibrated "
            f"window [{bp_lo}, {bp_hi}] (chain does not close at Greece)"
        )

    if not fails:
        verdict = "pass"
        rationale = (
            f"CROSS-LANE CHAIN CLOSES at v1. Recovered breakpoint year "
            f"{bp:.1f} ∈ [{bp_lo}, {bp_hi}] (miles-prior-calibrated window from "
            f"policy_anchor 2009 + 8.83y mean ± 1.47y MAE). piecewise_rss_ratio "
            f"{ratio:.4f} ≤ {ratio_max:.4f}. The miles lead-time chain "
            f"(#30 → #33 → #40) generalizes to Greece at cross-lane consumer "
            f"level. NOT a real-grid claim — v2-ratchet to real Eurostat data "
            f"required."
        )
    else:
        verdict = "fail"
        rationale = (
            "Voice enters the null-voice ledger per §3.4. Failures: " + " ; ".join(fails)
            + ". This is informative cross-lane data on where the methodology "
            "chain breaks at new-country generalization."
        )

    return {
        "verdict": verdict,
        "recovered_breakpoint_year": bp,
        "predicted_inflection_window": [bp_lo, bp_hi],
        "piecewise_rss_ratio": ratio,
        "miles_prior_used": PREDICTION["miles_prior_chain"],
        "policy_anchor_year": GREECE_POLICY_ANCHOR_YEAR,
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
        sort_keys=True, separators=(",", ":"),
    )
    unit["sidecar_sha256_pre_verdict"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with open(output_path, "w") as f:
        json.dump(unit, f, indent=2)
    return output_path


def main():
    print("=" * 72)
    print(f"voice unit: {VOICE_NAME}  (CROSS-LANE chain-loop)")
    print("=" * 72)
    print(f"miles prior chain: {MILES_LEAD_TIME_PRIOR['source_chain']}")
    print(f"miles prior: {MILES_LEAD_TIME_PRIOR['mean_lead_time_years']:.2f}y ± {MILES_LEAD_TIME_PRIOR['loo_mae_years']:.2f}y MAE")
    print(f"Greece policy anchor: {GREECE_POLICY_ANCHOR_YEAR}")
    print(f"predicted inflection window: {PREDICTION['predicted_inflection_window']}")
    print(f"kill rule: {KILL_CONDITION['rule']}")
    print()
    print("running Greece inflection-year recovery under miles prior...")
    out = run_voice()
    print(f"  greece RE share milestones: {RUN_PROTOCOL['input_parameters']['greece_re_share_milestones']}")
    print(f"  interpolated yoy rates: {[round(r, 3) for r in out['yoy_rates']]}")
    print(f"  linear_rss:    {out['linear_rss']:.6f}")
    print(f"  piecewise_rss: {out['piecewise_rss']:.6f}")
    print(f"  ratio:         {out['piecewise_rss_ratio']:.4f}")
    print(f"  recovered breakpoint year: {out['recovered_breakpoint_year']}")
    print()
    verdict = compute_verdict(out)
    print(f"  verdict: {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    print()
    sidecar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{VOICE_NAME}.sidecar.json")
    emit_sidecar(verdict, out, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
