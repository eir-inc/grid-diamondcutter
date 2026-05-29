# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
germany_2022_cross_lane_lead_time_recognition_v1.py — phase-2 §3.1 polyphony voice.

FIRST CAJAL-LANE PHASE-2 VOICE. Tests whether miles's Phase-A leader-cohort
lead-time prior (PR #30 + PR #40 v2) generalizes from the policy → deployment
substrate (Phase-A scope) to the monetary-phase substrate (Phase-2 scope).

Substrate: Germany 2022 negative-spot-price-hour count trajectory. The
recognition test pre-registers whether the monetary-phase inflection year
falls within the window predicted by applying miles's prior to Germany's
documented renewable-policy anchor year.

Cross-phase consumption (§3.5): consumes miles `regulatory_lead_time_v1`
sidecar as the calibration prior. Voice is a chain-loop closing on the
new substrate-class.

Evasion-class lineage (§3.6): `cross_lane_prior_generalization_evasion` —
the specific spring this voice targets. If a Phase-A prior valid in its
own lane (policy → deployment) does not generalize to a different
substrate-class (monetary-phase), that is the level-6 methodology-defense
evasion documented in cajal post-mortem (PR #62).

Per §1.9-12 phase-2 bounds: this voice does NOT claim Germany 2022 substrate
behavior; it tests whether a Phase-A prior's predicted window CONTAINS the
inflection in a documented public-signal trajectory. Recognition only, not
prediction or characterization. Per §4.3 reframe — substrate outcome is
downstream synthesis, not pre-asserted here.

Per §6 boundary: no `eirmath` import. All math is open repo numpy.
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import numpy as np


# ===========================================================================
# §3.1 — five-field unit (phase-2 inherits this from phase-1 root)
# ===========================================================================

VOICE_NAME = "germany_2022_cross_lane_lead_time_recognition_v1"


# Cross-phase consumed sidecar (§3.5 + §3.6 lineage)
# Pre-declared values from miles PR #30 + #40 (v2 expanded cohort)
MILES_LEAD_TIME_PRIOR = {
    "consumed_voice_name": "regulatory_lead_time_v1",
    "consumed_sidecar_path": "examples/voices/regulatory_lead_time_v1.sidecar.json",
    "consumed_phase": "phase_1",
    "consumption_kind": "prior_anchor",
    "mean_lead_time_years": 8.83,        # PR #30 + #40 EU sub-cohort
    "loo_mae_years": 1.47,                # PR #33 LOO calibration
}

# Germany Energiewende anchor: 2013 EEG amendment locking nuclear phase-out
# trajectory + significant RE buildout commitments. Used per miles's prior
# framing (policy anchor → +mean ± mae years).
GERMANY_POLICY_ANCHOR_YEAR = 2013

_pred_lo = GERMANY_POLICY_ANCHOR_YEAR + MILES_LEAD_TIME_PRIOR["mean_lead_time_years"] - MILES_LEAD_TIME_PRIOR["loo_mae_years"]
_pred_hi = GERMANY_POLICY_ANCHOR_YEAR + MILES_LEAD_TIME_PRIOR["mean_lead_time_years"] + MILES_LEAD_TIME_PRIOR["loo_mae_years"]


PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "germany_2022_negative_spot_price_hour_count_trajectory_synthetic_v1",
    "named_residual": "germany_negative_spot_price_hour_count_inflection_year_falls_within_miles_prior_calibrated_window",
    "policy_anchor_year": GERMANY_POLICY_ANCHOR_YEAR,
    "predicted_inflection_window": [round(_pred_lo, 2), round(_pred_hi, 2)],
    "piecewise_improvement_floor": 0.20,
    "evasion_class_lineage": "cross_lane_prior_generalization_evasion",
    "rationale": (
        "Tests cross-lane generalization of miles's Phase-A lead-time prior "
        "(#30, #40 v2) from the policy → deployment substrate-class to the "
        "monetary-phase substrate-class. Recognition criterion: piecewise-"
        "linear inflection in Germany negative-spot-price-hour count YoY "
        "with breakpoint year ∈ ["
        f"{round(_pred_lo, 2)}, {round(_pred_hi, 2)}] AND piecewise/linear "
        "RSS ratio ≤ 0.80. PASS = prior generalizes across substrate-class. "
        "FAIL = prior is substrate-class-bounded. Either is informative "
        "Phase-2 registry data on the evasion spring's geometry."
    ),
}

KILL_CONDITION = {
    "metric": "germany_2022_inflection_year_validity_under_miles_prior",
    "rule": (
        "fail if recovered_breakpoint_year outside predicted_inflection_window "
        "(miles prior does not generalize to monetary-phase substrate); "
        "fail if piecewise_rss / linear_rss > 0.80 (no inflection detectable "
        "regardless of year window — substrate has no monetary-phase signal)"
    ),
    "rationale": (
        "Composite metric — inflection-year-within-window AND piecewise-fit-"
        "improves-on-linear. First condition tests cross-lane generalization. "
        "Second rejects spurious recoveries on flat / noise substrate. "
        "Same shape as Phase-A cajal #48/#52 chain-loop voices."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python phase_2/examples/voices/germany_2022_cross_lane_lead_time_recognition_v1.py",
    "source_file": "phase_2/examples/voices/germany_2022_cross_lane_lead_time_recognition_v1.py",

    # §3.5 — public-signal source declaration
    "public_signal_source": {
        "feed_name": "ENTSO-E Transparency Platform day-ahead prices + national operator daily reports",
        "country_or_region": "Germany",
        "time_window": "2016-01-01 / 2023-12-31",
        "citation_anchor": "ENTSO-E TP API spec; BMWi 2022 Annual Energy Report; AGEE-Stat 2023 release",
    },

    # §3.5 — cross-phase consumption declaration
    "cross_phase_consumption": [
        {
            "consumed_voice_name": MILES_LEAD_TIME_PRIOR["consumed_voice_name"],
            "consumed_sidecar_path": MILES_LEAD_TIME_PRIOR["consumed_sidecar_path"],
            "consumed_phase": MILES_LEAD_TIME_PRIOR["consumed_phase"],
            "consumption_kind": MILES_LEAD_TIME_PRIOR["consumption_kind"],
        },
    ],

    "input_parameters": {
        "calibration_source": "synthetic_v1_from_publicly_cited_BMWi_AGEE_Stat_ENTSO_E_summaries",
        # Germany annual negative-spot-price-hour count (synthetic-v1 from
        # publicly-cited summaries — DE neg-hour count was ~10 in 2014,
        # grew to ~25 by 2017, ~30 by 2020-2021, surged to ~115 in 2022
        # per BMWi + Fraunhofer ISE summary releases, ~290 in 2023 per
        # provisional data). v2-ratchet to real ENTSO-E hourly query.
        "germany_negative_spot_price_hour_count_milestones": {
            "2016": 18, "2017": 25, "2018": 22, "2019": 28, "2020": 25,
            "2021": 30, "2022": 115, "2023": 290,
        },
        "policy_anchor_year": GERMANY_POLICY_ANCHOR_YEAR,
        "miles_prior_mean": MILES_LEAD_TIME_PRIOR["mean_lead_time_years"],
        "miles_prior_mae": MILES_LEAD_TIME_PRIOR["loo_mae_years"],
        "random_seed": 2022,
    },

    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },

    # §3.7 — computational-budget per Phase-2 §3.7 addition
    "computational_budget": {
        "max_runtime_seconds": 60,
        "max_external_api_calls": 0,
    },
}


# ===========================================================================
# Voice implementation
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
        lx, ly = xs[: i + 1], ys[: i + 1]
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
    years = np.arange(2016, 2024)
    milestones = RUN_PROTOCOL["input_parameters"]["germany_negative_spot_price_hour_count_milestones"]
    counts = interpolate_milestones(milestones, years)
    # YoY changes (test for inflection in growth rate)
    yoy_changes = np.diff(counts)
    rate_years = years[:-1].astype(float)
    _, _, linear_rss = fit_linear(rate_years, yoy_changes)
    breakpoint_year, piecewise_rss = fit_piecewise_two_segment(rate_years, yoy_changes)
    piecewise_rss_ratio = piecewise_rss / linear_rss if linear_rss > 0 else float("inf")
    return {
        "years": [int(y) for y in years],
        "germany_neg_spot_price_hour_count": [float(c) for c in counts],
        "rate_years": [int(y) for y in rate_years],
        "yoy_changes": [float(r) for r in yoy_changes],
        "linear_rss": float(linear_rss),
        "piecewise_rss": float(piecewise_rss),
        "piecewise_rss_ratio": float(piecewise_rss_ratio),
        "recovered_breakpoint_year": float(breakpoint_year) if breakpoint_year is not None else None,
        "policy_anchor_year": GERMANY_POLICY_ANCHOR_YEAR,
        "predicted_inflection_window": PREDICTION["predicted_inflection_window"],
        "miles_prior_consumed": MILES_LEAD_TIME_PRIOR,
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
            f"(no inflection detectable — substrate may be flat / monetary-phase signal absent)"
        )
    if bp is None or bp < bp_lo or bp > bp_hi:
        fails.append(
            f"recovered breakpoint year {bp} outside miles-prior window "
            f"[{bp_lo}, {bp_hi}] (cross-lane prior does NOT generalize to "
            f"monetary-phase substrate; cross_lane_prior_generalization_evasion "
            f"spring observed)"
        )

    if not fails:
        verdict = "pass"
        rationale = (
            f"CROSS-LANE PHASE-2 RECOGNITION PASS. Recovered breakpoint year "
            f"{bp:.1f} ∈ [{bp_lo}, {bp_hi}]. piecewise_rss_ratio {ratio:.4f} ≤ "
            f"{ratio_max:.4f}. Miles's Phase-A leader-cohort lead-time prior "
            f"(#30, #40) generalizes from policy → deployment substrate-class "
            f"to monetary-phase substrate-class on Germany 2022 at synthetic v1. "
            f"Recognition criterion fires within predicted window. NOT a "
            f"substrate-characterization claim per §4.3 — the voice reports "
            f"recognition only; downstream synthesis is left to the Phase-2 "
            f"interpretation document. v2-ratchet to real ENTSO-E hourly data "
            f"required for any external claim."
        )
    else:
        verdict = "fail"
        rationale = (
            f"Voice enters the null-voice ledger per §3.4. Failures: "
            + " ; ".join(fails) + ". This FAIL is informative Phase-2 registry "
            f"data on the cross_lane_prior_generalization_evasion spring's "
            f"geometry per §3.6 lineage declaration."
        )

    return {
        "verdict": verdict,
        "recovered_breakpoint_year": bp,
        "predicted_inflection_window": [bp_lo, bp_hi],
        "piecewise_rss_ratio": ratio,
        "policy_anchor_year": GERMANY_POLICY_ANCHOR_YEAR,
        "miles_prior_consumed": MILES_LEAD_TIME_PRIOR,
        "evasion_class_lineage": PREDICTION["evasion_class_lineage"],
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
    print(f"voice unit: {VOICE_NAME}  (phase-2 cross-lane chain-loop)")
    print("=" * 72)
    print(f"miles prior consumed: #30 + #40 mean {MILES_LEAD_TIME_PRIOR['mean_lead_time_years']:.2f}y ± {MILES_LEAD_TIME_PRIOR['loo_mae_years']:.2f}y MAE")
    print(f"Germany Energiewende anchor: {GERMANY_POLICY_ANCHOR_YEAR}")
    print(f"predicted inflection window: {PREDICTION['predicted_inflection_window']}")
    print(f"evasion class lineage: {PREDICTION['evasion_class_lineage']}")
    print(f"kill rule: {KILL_CONDITION['rule']}")
    print()
    print("running Germany 2022 monetary-phase recognition under miles prior...")
    out = run_voice()
    print(f"  DE neg-spot-price-hour count milestones: {RUN_PROTOCOL['input_parameters']['germany_negative_spot_price_hour_count_milestones']}")
    print(f"  YoY changes:    {[round(r, 1) for r in out['yoy_changes']]}")
    print(f"  linear_rss:    {out['linear_rss']:.4f}")
    print(f"  piecewise_rss: {out['piecewise_rss']:.4f}")
    print(f"  ratio:         {out['piecewise_rss_ratio']:.4f}")
    print(f"  recovered breakpoint year: {out['recovered_breakpoint_year']}")
    print()
    verdict = compute_verdict(out)
    print(f"  verdict: {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    print()
    sidecar_path = str(THIS_DIR / f"{VOICE_NAME}.sidecar.json")
    emit_sidecar(verdict, out, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
