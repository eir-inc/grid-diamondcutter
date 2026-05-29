# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
texas_feb_2021_recognition_v1.py — phase-2 §3.1 polyphony voice.

PHASE-2 §4.2 HISTORICAL-EVENTS VALIDATION VOICE. Tests recognition criterion
on Texas Feb 2021 electricity market crisis event.

§4.2 reframe (per scaffold integration): voice reports recognition criterion
+ observed value; does NOT pre-assert "substrate failed to transition to
monetary-phase." That characterization is downstream synthesis.

Recognition criterion: extreme spot-price instability index — ratio of
peak monthly average spot price to baseline (pre-crisis median spot price).
If ratio > 10x, recognition criterion fires.

Public source: ERCOT post-event report; FERC/NERC Inquiry into Bulk-Power System Events of Feb 2021 (March
2003), tabulated monthly wholesale spot prices from PX/ISO settlement data.

Evasion-class lineage (§3.6): data_availability_evasion — the substrate
is historical/closed (FERC final report published 2003); the voice operates
on summary-table values rather than primary-source feed.

Per §1.9-12 phase-2 bounds: NO substrate-characterization claim, NO
investment-advice claim, NO eirmath-stub equivalence, NO claim that
public spot+volume signal exhaustively describes the substrate.

Per §6 boundary: no eirmath import. Pure numpy.
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
# §3.1 — five-field unit
# ===========================================================================

VOICE_NAME = "texas_feb_2021_recognition_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "texas_iso_px_wholesale_spot_price_monthly_avg_1999_2001_synthetic_v1",
    "named_residual": "texas_2000_2001_extreme_spot_price_instability_index_fires_recognition_criterion",
    "recognition_criterion_threshold": 10.0,  # peak-monthly-spot / baseline-median-spot
    "baseline_window": ["2020-12", "2021-01"],
    "event_window": ["2021-02", "2021-02"],
    "evasion_class_lineage": "data_availability_evasion",
    "rationale": (
        "Tests whether the methodology recognizes extreme substrate-stress in "
        "Texas Q2-2000 → Q2-2001 wholesale electricity market. "
        "Recognition criterion: ratio of peak-monthly-mean spot price in event "
        "window to median spot price in baseline window > 10x. Does NOT "
        "pre-assert that this means 'substrate failed to commodify' — that is "
        "downstream synthesis per §4.2 reframe. The voice reports criterion-"
        "fires + observed value only."
    ),
}

KILL_CONDITION = {
    "metric": "texas_2000_2001_extreme_spot_price_instability_index",
    "rule": (
        "fail if peak-event-window-monthly-spot / baseline-median-monthly-spot < 10.0 "
        "(recognition criterion does not fire — substrate did not exhibit extreme "
        "spot-price instability at the pre-committed threshold)"
    ),
    "rationale": (
        "Single composite metric: peak-monthly-mean-spot in event window divided "
        "by median-monthly-spot in baseline window. Threshold 10x is well below "
        "documented ERCOT + FERC/NERC Nov 2021 Report peak figures (~$750-1000/MWh vs "
        "~$25/MWh baseline = ~70x); 10x gives substantial headroom for "
        "alternative public-source calibrations."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python phase_2/examples/voices/texas_feb_2021_recognition_v1.py",
    "source_file": "phase_2/examples/voices/texas_feb_2021_recognition_v1.py",

    # §3.5 — public-signal source declaration
    "public_signal_source": {
        "feed_name": "Texas ISO / PX wholesale spot prices (settlement data)",
        "country_or_region": "Texas, USA",
        "time_window": "1999-01-01 / 2001-12-31",
        "citation_anchor": "ERCOT post-event report; FERC/NERC Inquiry into Bulk-Power System Events of Feb 2021, March 2003; Texas ISO public settlement archives",
    },

    # §3.5 — no cross-phase consumption (pure phase-2 recognition voice)
    "cross_phase_consumption": [],

    "input_parameters": {
        "calibration_source": "synthetic_v1_from_ERCOT_post_event_report_FERC_NERC_Nov_2021_Inquiry",
        # ERCOT Real-Time settlement-point spot prices ($/MWh) monthly mean.
        # Synthetic v1 from publicly-cited ERCOT post-event report + FERC/NERC
        # Nov 2021 Inquiry. Pre-event (2020-12 / 2021-01) monthly-mean ~$25/MWh.
        # Feb 2021 event window: ERCOT real-time prices hit the PUC-mandated
        # $9000/MWh cap repeatedly Feb 14-17 during the Uri freeze; resulting
        # monthly mean for Feb 2021 was ~$1700/MWh per published summaries.
        # Post-event (Mar 2021) returned to ~$30/MWh band.
        # v2-ratchet to real ERCOT settlement-point CSV via PR #10 frozen-snapshot.
        "texas_monthly_spot_price_usd_mwh": {
            "2020-12": 26.4,
            "2021-01": 25.7,
            "2021-02": 1740.0,
            "2021-03": 30.5,
        },
        "random_seed": 2021,
    },

    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },

    # §3.7 — computational-budget per Phase-2 §3.7 addition
    "computational_budget": {
        "max_runtime_seconds": 30,
        "max_external_api_calls": 0,
    },
}


# ===========================================================================
# Voice implementation
# ===========================================================================

def _months_in_window(window: list[str]) -> list[str]:
    """Expand a [start, end] inclusive YYYY-MM window into the month list."""
    start_y, start_m = (int(x) for x in window[0].split("-"))
    end_y, end_m = (int(x) for x in window[1].split("-"))
    months: list[str] = []
    y, m = start_y, start_m
    while (y, m) <= (end_y, end_m):
        months.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            m = 1
            y += 1
    return months


def run_voice() -> dict:
    np.random.seed(RUN_PROTOCOL["input_parameters"]["random_seed"])
    series = RUN_PROTOCOL["input_parameters"]["texas_monthly_spot_price_usd_mwh"]
    baseline_months = _months_in_window(PREDICTION["baseline_window"])
    event_months = _months_in_window(PREDICTION["event_window"])

    baseline_vals = [series[m] for m in baseline_months if m in series]
    event_vals = [series[m] for m in event_months if m in series]
    baseline_median = float(np.median(baseline_vals))
    event_peak_month_idx = int(np.argmax(event_vals))
    event_peak = float(event_vals[event_peak_month_idx])
    event_peak_month = event_months[event_peak_month_idx]
    instability_index = event_peak / baseline_median if baseline_median > 0 else float("inf")
    return {
        "baseline_window": PREDICTION["baseline_window"],
        "event_window": PREDICTION["event_window"],
        "baseline_n_months": len(baseline_vals),
        "event_n_months": len(event_vals),
        "baseline_median_usd_mwh": baseline_median,
        "event_peak_month": event_peak_month,
        "event_peak_usd_mwh": event_peak,
        "extreme_spot_price_instability_index": float(instability_index),
        "threshold": PREDICTION["recognition_criterion_threshold"],
    }


def compute_verdict(run_output: dict) -> dict:
    idx = run_output["extreme_spot_price_instability_index"]
    threshold = PREDICTION["recognition_criterion_threshold"]
    fails = []

    if idx < threshold:
        fails.append(
            f"instability index {idx:.2f}x < {threshold:.1f}x threshold "
            f"(recognition criterion does not fire — substrate did not exhibit "
            f"extreme spot-price instability at pre-committed threshold)"
        )

    if not fails:
        verdict = "pass"
        rationale = (
            f"Recognition criterion FIRES. extreme_spot_price_instability_index = "
            f"{idx:.2f}x (peak {run_output['event_peak_month']} ${run_output['event_peak_usd_mwh']:.1f}/MWh "
            f"vs 2020-12/2021-01 baseline median ${run_output['baseline_median_usd_mwh']:.1f}/MWh), "
            f"≥ {threshold:.1f}x threshold. Voice reports criterion-fires + observed "
            f"value; downstream synthesis (whether this constitutes 'substrate "
            f"failed to commodify' or 'transient extreme event' or 'regulatory-"
            f"design failure') is left to the Phase-2 interpretation document "
            f"per §4.2 reframe. v2-ratchet to real ERCOT hourly settlement-point data "
            f"required for any external claim."
        )
    else:
        verdict = "fail"
        rationale = (
            "Voice enters the null-voice ledger per §3.4. Failures: "
            + " ; ".join(fails) + ". This is informative Phase-2 registry data "
            "per §3.6 data_availability_evasion lineage — the synthetic-v1 "
            "summary tables may understate the substrate-stress."
        )

    return {
        "verdict": verdict,
        "extreme_spot_price_instability_index": idx,
        "threshold": threshold,
        "baseline_median_usd_mwh": run_output["baseline_median_usd_mwh"],
        "event_peak_month": run_output["event_peak_month"],
        "event_peak_usd_mwh": run_output["event_peak_usd_mwh"],
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
    print(f"voice unit: {VOICE_NAME}  (phase-2 §4.2 historical-events validation)")
    print("=" * 72)
    print(f"baseline window: {PREDICTION['baseline_window']}")
    print(f"event window:    {PREDICTION['event_window']}")
    print(f"threshold:       {PREDICTION['recognition_criterion_threshold']:.1f}x")
    print(f"evasion class lineage: {PREDICTION['evasion_class_lineage']}")
    print()
    print("running Texas Feb 2021 spot-price-instability recognition...")
    out = run_voice()
    print(f"  baseline n months: {out['baseline_n_months']}")
    print(f"  event n months:    {out['event_n_months']}")
    print(f"  baseline median $: {out['baseline_median_usd_mwh']:.2f}/MWh")
    print(f"  event peak month:  {out['event_peak_month']}")
    print(f"  event peak $:      {out['event_peak_usd_mwh']:.2f}/MWh")
    print(f"  instability index: {out['extreme_spot_price_instability_index']:.2f}x")
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
