# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
receiver_geometry_substrate_class_v1.py — §3.1 polyphony meta-voice.

Tests a substrate-class hypothesis emerging from three cajal pair-coupling
voices on the same night (PR #26 DE→FR, #35 DK→DE, #36 ES→MA). All three
substrates differ in receiver-region geometry; all three produced different
verdicts under the SAME coupling test structure.

Substrate-class hypothesis: cascade-coupling slope is monotonic in receiver-
region renewable-policy responsiveness. Specifically:

  receiver_type        | example pair  | predicted slope behavior
  ---------------------|---------------|------------------------------
  nuclear_insulated    | DE→FR         | slope ≈ 0 (no signal)
  smooth_S_curve       | DK→DE         | raw slope > magnitude_range
                       |               | (over-correlation kill)
  step_function_policy | ES→MA         | normalized slope in range

If this substrate-class pattern is real, it should be reproducible at a
different pair-set. This voice tests three NEW synthetic pairs constructed
to match the three receiver-geometry classes, with PRE-COMMITTED prediction
that each pair lands in its predicted bucket. The "polyphony within
substrate" claim is: receiver-geometry class predicts coupling-test outcome.

Per §1 honesty bound: SYNTHETIC v1 ONLY. Tests substrate-class hypothesis
on freshly-constructed pairs (not the original DE→FR / DK→DE / ES→MA) to
avoid circularity. v2-ratchet to real cross-border data via PR #10 frozen-
snapshot required for any external claim. This voice itself can FAIL — it
will FAIL if the three new pairs don't reproduce the receiver-geometry
pattern, indicating the night's emergent observation was substrate-pair-
specific rather than class-level.

Independent-pair design (deliberately disjoint from #26 #35 #36):
  - nuclear_insulated:    FR→CH (France→Switzerland, CH heavily-hydro+nuclear)
  - smooth_S_curve:       AT→DE (Austria→Germany, both smooth EU build-out)
  - step_function_policy: PT→CV (Portugal→Cape Verde, CV step-function island)
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
# §3.1 — polyphony voice unit (meta-substrate-class test)
# ===========================================================================

VOICE_NAME = "receiver_geometry_substrate_class_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "cross_border_solar_coupling_receiver_geometry_class_v1_synthetic",
    "named_residual": "receiver_geometry_class_predicts_coupling_outcome_at_class_level_not_pair_level",
    "predicted_pair_outcomes": {
        "nuclear_insulated_FR_CH": "verdict_fail_null_direction",
        "smooth_S_curve_AT_DE": "verdict_fail_upper_bound_or_pass_high_in_range",
        "step_function_policy_PT_CV": "verdict_pass_normalized_slope_in_range",
    },
    "minimum_class_consistency": 2,  # at least 2 of 3 must match prediction
    "rationale": (
        "Substrate-class hypothesis: receiver-region renewable-policy-response "
        "geometry predicts coupling-test outcome at the CLASS level, not pair-"
        "specific. Tested on three FRESH pairs disjoint from PR #26/#35/#36 to "
        "avoid circularity. If at least 2 of 3 new pairs land in their predicted "
        "verdict bucket, substrate-class hypothesis is supported at v1. If 0 or "
        "1 of 3 match, the night's emergent observation was pair-specific not "
        "class-level (which is itself useful registry data per §3.4)."
    ),
}

KILL_CONDITION = {
    "metric": "class_predicted_outcome_match_count",
    "rule": (
        "fail if fewer than 2 of 3 fresh pairs land in their pre-committed "
        "predicted-verdict bucket (substrate-class hypothesis not supported at v1)"
    ),
    "rationale": (
        "Composite mechanical match-count metric. Each fresh pair runs the "
        "standard normalized-coupling test, gets a verdict, and is checked "
        "against the pre-committed predicted-verdict for that pair's receiver-"
        "geometry class. Threshold of 2/3 is a soft-majority requirement — "
        "0 or 1 match indicates the pattern was pair-specific."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/receiver_geometry_substrate_class_v1.py",
    "source_file": "examples/voices/receiver_geometry_substrate_class_v1.py",
    "input_parameters": {
        "calibration_source": "synthetic_v1_publicly_cited_country_milestones",
        "years": list(range(2010, 2024)),
        # FR → CH (nuclear+hydro insulated receiver, predict null direction)
        # France solar GW year-end, Switzerland solar GW year-end
        "fr_solar_capacity_gw": [
            1.0, 2.7, 4.0, 4.7, 5.6, 6.6, 7.1, 8.0, 8.8, 9.4,
            10.4, 13.1, 15.7, 18.9,
        ],
        "ch_solar_capacity_gw": [
            0.1, 0.2, 0.4, 0.7, 1.0, 1.4, 1.7, 1.9, 2.1, 2.5,
            2.9, 3.5, 4.1, 5.1,
        ],
        # AT → DE (both smooth S-curve, predict over-correlation upper-bound FAIL)
        # Austria PV GW, Germany PV GW
        "at_solar_capacity_gw": [
            0.1, 0.2, 0.4, 0.6, 0.8, 0.9, 1.1, 1.3, 1.4, 1.7,
            2.1, 2.5, 3.5, 4.9,
        ],
        "de_solar_capacity_gw": [
            17.6, 25.4, 33.0, 36.7, 38.2, 39.7, 41.2, 42.4, 45.9, 49.2,
            54.0, 58.5, 66.5, 81.7,
        ],
        # PT → CV (step-function island receiver, predict PASS)
        # Portugal solar GW, Cape Verde solar MW (heavily step-function island)
        "pt_solar_capacity_gw": [
            0.13, 0.18, 0.24, 0.30, 0.42, 0.45, 0.48, 0.57, 0.66, 0.91,
            1.05, 1.51, 2.65, 3.95,
        ],
        "cv_solar_capacity_mw": [
            0, 0, 0, 5, 7, 7, 7, 7, 30, 30,
            30, 47, 47, 47,
        ],
        "lag_years": 1,
        "random_seed": 7777,
        "magnitude_range_normalized": [0.10, 0.80],
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
    s_min, s_max = min(series), max(series)
    rng = s_max - s_min
    if rng == 0:
        return [0.0 for _ in series]
    return [(v - s_min) / rng for v in series]


def lagged_regression_slope(x: list[float], y: list[float], lag: int) -> tuple[float, int]:
    if lag <= 0:
        x_arr = np.array(x)
        y_arr = np.array(y)
    else:
        x_arr = np.array(x[:-lag])
        y_arr = np.array(y[lag:])
    if len(x_arr) < 3:
        return float("nan"), len(x_arr)
    slope, _ = np.polyfit(x_arr, y_arr, 1)
    return float(slope), len(x_arr)


def run_pair_test(x_capacity: list[float], y_capacity: list[float], lag: int, mag_range: list) -> dict:
    """Run normalized-slope coupling test on a single pair, classify verdict."""
    x_yoy = yoy_change(x_capacity)
    y_yoy = yoy_change(y_capacity)
    # Raw slope first (for over-correlation check, can blow up if unit-mismatched)
    raw_slope, n = lagged_regression_slope(x_yoy, y_yoy, lag)
    # Normalized slope (the actual test metric)
    x_yoy_norm = normalize(x_yoy)
    y_yoy_norm = normalize(y_yoy)
    norm_slope, _ = lagged_regression_slope(x_yoy_norm, y_yoy_norm, lag)

    mag_lo, mag_hi = mag_range
    if np.isnan(norm_slope):
        verdict_bucket = "verdict_fail_nan"
    elif norm_slope < 0:
        verdict_bucket = "verdict_fail_null_direction"
    elif norm_slope < mag_lo:
        verdict_bucket = "verdict_fail_below_threshold"
    elif norm_slope > mag_hi:
        verdict_bucket = "verdict_fail_upper_bound_or_pass_high_in_range"
    else:
        verdict_bucket = "verdict_pass_normalized_slope_in_range"

    return {
        "raw_slope": raw_slope,
        "normalized_slope": norm_slope,
        "n_lagged_pairs": int(n),
        "verdict_bucket": verdict_bucket,
    }


def run_voice() -> dict:
    p = RUN_PROTOCOL["input_parameters"]
    lag = p["lag_years"]
    mag_range = p["magnitude_range_normalized"]

    fr_ch_result = run_pair_test(p["fr_solar_capacity_gw"], p["ch_solar_capacity_gw"], lag, mag_range)
    at_de_result = run_pair_test(p["at_solar_capacity_gw"], p["de_solar_capacity_gw"], lag, mag_range)
    pt_cv_result = run_pair_test(p["pt_solar_capacity_gw"], p["cv_solar_capacity_mw"], lag, mag_range)

    predicted = PREDICTION["predicted_pair_outcomes"]
    matches = {
        "nuclear_insulated_FR_CH": fr_ch_result["verdict_bucket"] == predicted["nuclear_insulated_FR_CH"],
        "smooth_S_curve_AT_DE": at_de_result["verdict_bucket"] == predicted["smooth_S_curve_AT_DE"],
        "step_function_policy_PT_CV": pt_cv_result["verdict_bucket"] == predicted["step_function_policy_PT_CV"],
    }
    match_count = sum(1 for v in matches.values() if v)

    return {
        "lag_years": lag,
        "magnitude_range_normalized": mag_range,
        "pair_results": {
            "nuclear_insulated_FR_CH": fr_ch_result,
            "smooth_S_curve_AT_DE": at_de_result,
            "step_function_policy_PT_CV": pt_cv_result,
        },
        "predicted_outcomes": predicted,
        "pair_match_with_prediction": matches,
        "class_consistency_match_count": int(match_count),
    }


def compute_verdict(run_output: dict) -> dict:
    match_count = run_output["class_consistency_match_count"]
    min_required = PREDICTION["minimum_class_consistency"]

    if match_count < min_required:
        verdict = "fail"
        rationale = (
            f"Voice enters the null-voice ledger per §3.4. "
            f"Only {match_count}/3 fresh pairs landed in their pre-committed "
            f"predicted-verdict bucket (minimum required: {min_required}/3). "
            f"Substrate-class hypothesis is NOT supported at v1 — the night's "
            f"emergent receiver-geometry pattern was pair-specific rather than "
            f"class-level. This is informative registry data: the pattern from "
            f"PR #26 #35 #36 may have been coincidence in those specific pairs."
        )
    else:
        verdict = "pass"
        rationale = (
            f"{match_count}/3 fresh pairs landed in their pre-committed "
            f"predicted-verdict bucket. Substrate-class hypothesis SUPPORTED "
            f"at v1: receiver-geometry class is a candidate predictor of "
            f"cascade-coupling outcome. NOT a real-grid claim — v2-ratchet to "
            f"real ENTSO-E + national-agency cross-border data required for "
            f"any external citation."
        )

    return {
        "verdict": verdict,
        "class_consistency_match_count": match_count,
        "minimum_required": min_required,
        "per_pair_match": run_output["pair_match_with_prediction"],
        "per_pair_observed_bucket": {
            k: v["verdict_bucket"] for k, v in run_output["pair_results"].items()
        },
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
    print(f"predicted:    ≥ {PREDICTION['minimum_class_consistency']}/3 fresh pairs land in pre-committed bucket")
    print(f"kill rule:    {KILL_CONDITION['rule']}")
    print(f"run:          {RUN_PROTOCOL['entry_point']}")
    print()
    print("running receiver-geometry substrate-class meta-test...")
    out = run_voice()
    print(f"  lag: {out['lag_years']} years, magnitude_range: {out['magnitude_range_normalized']}")
    print()
    for pair_name, pair_result in out["pair_results"].items():
        match = "✓ MATCH" if out["pair_match_with_prediction"][pair_name] else "✗ MISS"
        print(f"  {pair_name}:")
        print(f"    raw_slope: {pair_result['raw_slope']:.4f}")
        print(f"    normalized_slope: {pair_result['normalized_slope']:.4f}")
        print(f"    observed bucket: {pair_result['verdict_bucket']}")
        print(f"    predicted bucket: {out['predicted_outcomes'][pair_name]}")
        print(f"    {match}")
    print()
    print(f"  class consistency match count: {out['class_consistency_match_count']}/3")
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
