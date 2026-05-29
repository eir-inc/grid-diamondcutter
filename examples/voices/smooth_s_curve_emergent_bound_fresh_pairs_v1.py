# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
smooth_s_curve_emergent_bound_fresh_pairs_v1.py — §3.1 polyphony INVERTED-KILL voice.

Mechanically defends the emergent bound that surfaced from cajal coupling-voice
night-run (PR #26 #35 #37): coupling-detection methodology FAILS to detect
positive coupling when the receiver substrate is a smooth-S-curve renewable
trajectory. The bound is meta-§1-style (emergent from the registry, not a
hand-asserted hypothesis).

INVERTED-KILL pattern (same shape as miles PR #16/#18/#22 bound-defenders for
hand-asserted §1 rows). Mechanical apoha at substrate-class level:

  bound (negation-form):
    coupling-detection methodology does NOT successfully detect
    positive coupling at 1y lag when receiver is smooth-S-curve

  positive content of the bound:
    on N pre-committed smooth-S-curve receiver substrates, the
    normalized-lagged-slope coupling test FAILS (does not PASS in
    range) at the bounded-magnitude-range structure used in
    cajal #35 #36 #37

  PASS condition (inverted):
    methodology FAILS to detect positive coupling on ≥ N of N
    pre-committed smooth-S-curve receivers
    → bound supported by measurement

  FAIL condition (inverted):
    methodology successfully detects coupling on 1+ smooth-S-curve
    receiver → bound counter-observed → emergent registry bound
    not supported

The smooth-S-curve receivers tested here are FRESH, disjoint from the
DK→DE #35 / AT→DE #37-sub / FR→CH #37-sub set used to identify the pattern.
Avoids circularity by testing the bound on previously-unseen pairs.

Per §1 honesty bound: SYNTHETIC v1 only. The bound itself is registry-
emergent and tentative until v2-ratchet to real ENTSO-E + national agency
cross-border data confirms the pattern survives real noise.

Apoha framing: the methodology's substrate-class scope is defined by what
it MECHANICALLY FAILS to detect. Capability via absence-of-success on the
pre-committed class.
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
# §3.1 — polyphony INVERTED-KILL voice unit
# ===========================================================================

VOICE_NAME = "smooth_s_curve_emergent_bound_fresh_pairs_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "smooth_s_curve_receiver_pair_substrate_class_v1_synthetic",
    "named_residual": "coupling_detection_methodology_fails_to_detect_positive_coupling_on_smooth_s_curve_receivers",
    "inverted_kill_design": True,
    "predicted_outcome": "all_3_fresh_smooth_S_curve_pairs_FAIL_the_coupling_test",
    "n_pairs_must_fail": 3,
    "rationale": (
        "Defends emergent registry bound from cajal #26 #35 #37: methodology "
        "consistently fails to detect positive coupling when receiver is smooth-"
        "S-curve renewable trajectory. Tested on 3 FRESH pairs disjoint from the "
        "original 4 (DE→FR, DK→DE, AT→DE-sub, FR→CH-sub). If ≥ 1 fresh pair "
        "PASSes the standard coupling test on a smooth-S-curve receiver, the "
        "bound is counter-observed (REJECT-the-bound). If all 3 FAIL, bound is "
        "mechanically supported (PASS-the-bound, apoha-at-substrate-class)."
    ),
}

KILL_CONDITION = {
    "metric": "fresh_smooth_s_curve_pair_pass_count",
    "rule": (
        "fail if ANY fresh smooth-S-curve receiver pair PASSes the standard "
        "normalized-lagged-slope coupling test (≥ 1 PASS → bound counter-observed)"
    ),
    "rationale": (
        "INVERTED-KILL: PASS-the-bound condition is that all fresh pairs FAIL "
        "the coupling test (zero pass count). Any PASS is bound counter-observation."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/smooth_s_curve_emergent_bound_fresh_pairs_v1.py",
    "source_file": "examples/voices/smooth_s_curve_emergent_bound_fresh_pairs_v1.py",
    "input_parameters": {
        "calibration_source": "synthetic_v1_smooth_s_curve_pair_substrates",
        "years": list(range(2010, 2024)),
        # 3 FRESH smooth-S-curve receiver pairs disjoint from #26 #35 #37 set
        # NL → BE (both smooth EU build-out, Netherlands solar + Belgium solar)
        "nl_solar_capacity_gw": [
            0.09, 0.15, 0.36, 0.74, 1.05, 1.53, 2.05, 2.86, 4.61, 6.92,
            10.21, 14.85, 18.85, 22.45,
        ],
        "be_solar_capacity_gw": [
            0.79, 1.85, 2.65, 2.98, 3.10, 3.25, 3.42, 3.62, 4.00, 4.65,
            5.65, 6.70, 7.85, 9.20,
        ],
        # IT → GR (both smooth EU build-out, Italy solar + Greece solar)
        "it_solar_capacity_gw": [
            3.5, 13.0, 16.4, 18.2, 18.6, 18.9, 19.3, 19.7, 20.1, 20.9,
            21.7, 22.6, 25.0, 30.3,
        ],
        "gr_solar_capacity_gw": [
            0.2, 0.6, 1.5, 2.6, 2.6, 2.6, 2.6, 2.6, 2.7, 2.8,
            3.3, 4.4, 5.4, 7.0,
        ],
        # SE → FI (both smooth Nordic build-out, Sweden solar + Finland solar)
        "se_solar_capacity_gw": [
            0.01, 0.02, 0.02, 0.04, 0.08, 0.14, 0.21, 0.31, 0.43, 0.71,
            1.11, 1.59, 2.43, 3.79,
        ],
        "fi_solar_capacity_gw": [
            0.00, 0.01, 0.01, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.20,
            0.34, 0.58, 0.74, 1.05,
        ],
        "lag_years": 1,
        "magnitude_range_normalized": [0.10, 0.80],
        "random_seed": 90210,
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


def lagged_slope(x: list[float], y: list[float], lag: int) -> tuple[float, int]:
    if lag <= 0:
        x_arr = np.array(x); y_arr = np.array(y)
    else:
        x_arr = np.array(x[:-lag]); y_arr = np.array(y[lag:])
    if len(x_arr) < 3:
        return float("nan"), len(x_arr)
    slope, _ = np.polyfit(x_arr, y_arr, 1)
    return float(slope), len(x_arr)


def run_pair_coupling_test(sender: list, receiver: list, lag: int, mag_range: list) -> dict:
    s_yoy = yoy_change(sender)
    r_yoy = yoy_change(receiver)
    s_norm = normalize(s_yoy); r_norm = normalize(r_yoy)
    slope, n = lagged_slope(s_norm, r_norm, lag)
    mag_lo, mag_hi = mag_range
    if np.isnan(slope):
        pair_verdict = "fail_nan"
    elif slope < 0:
        pair_verdict = "fail_null_direction"
    elif slope < mag_lo:
        pair_verdict = "fail_below_threshold"
    elif slope > mag_hi:
        pair_verdict = "fail_upper_bound"
    else:
        pair_verdict = "pass_in_range"
    return {
        "normalized_slope": slope,
        "n_pairs": int(n),
        "pair_verdict": pair_verdict,
        "passed_coupling_test": (pair_verdict == "pass_in_range"),
    }


def run_voice() -> dict:
    p = RUN_PROTOCOL["input_parameters"]
    lag = p["lag_years"]
    mag = p["magnitude_range_normalized"]

    pairs = {
        "NL_to_BE": run_pair_coupling_test(p["nl_solar_capacity_gw"], p["be_solar_capacity_gw"], lag, mag),
        "IT_to_GR": run_pair_coupling_test(p["it_solar_capacity_gw"], p["gr_solar_capacity_gw"], lag, mag),
        "SE_to_FI": run_pair_coupling_test(p["se_solar_capacity_gw"], p["fi_solar_capacity_gw"], lag, mag),
    }
    n_passed = sum(1 for r in pairs.values() if r["passed_coupling_test"])

    return {
        "lag_years": lag,
        "magnitude_range_normalized": mag,
        "fresh_pairs": pairs,
        "n_pairs_total": len(pairs),
        "n_pairs_passing_coupling_test": int(n_passed),
        "n_pairs_failing_coupling_test": int(len(pairs) - n_passed),
    }


def compute_verdict(run_output: dict) -> dict:
    n_passed = run_output["n_pairs_passing_coupling_test"]
    n_failed = run_output["n_pairs_failing_coupling_test"]
    n_total = run_output["n_pairs_total"]

    if n_passed == 0:
        # INVERTED-KILL: all pairs FAIL coupling test → bound supported
        verdict = "pass"
        rationale = (
            f"Inverted-kill PASS: 0/{n_total} fresh smooth-S-curve receiver pairs "
            f"detected positive coupling under the standard normalized-lagged-slope "
            f"test. The emergent registry bound 'methodology fails to detect "
            f"positive coupling on smooth-S-curve receivers' is mechanically "
            f"SUPPORTED by measurement on 3 fresh disjoint pairs (NL→BE, IT→GR, "
            f"SE→FI). Apoha-at-substrate-class: methodology scope defined by "
            f"absence-of-success on this substrate-class. NOT a real-grid claim — "
            f"v2-ratchet to real ENTSO-E data required."
        )
    else:
        # Bound counter-observed by at least one fresh pair
        verdict = "fail"
        rationale = (
            f"Inverted-kill FAIL: {n_passed}/{n_total} fresh smooth-S-curve "
            f"receiver pairs PASSed the coupling test, counter-observing the "
            f"emergent registry bound. Bound 'methodology fails to detect "
            f"coupling on smooth-S-curve receivers' is NOT supported at v1 — "
            f"the bound needs revision, or the substrate-class definition "
            f"needs tightening (e.g., 'smooth-S-curve receivers WITHOUT shared "
            f"S-curve sender' vs unrestricted)."
        )

    return {
        "verdict": verdict,
        "n_pairs_total": n_total,
        "n_pairs_passing_coupling_test": n_passed,
        "n_pairs_failing_coupling_test": n_failed,
        "inverted_kill_design": True,
        "per_pair_outcomes": {
            k: {"normalized_slope": v["normalized_slope"], "pair_verdict": v["pair_verdict"]}
            for k, v in run_output["fresh_pairs"].items()
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
        sort_keys=True, separators=(",", ":"),
    )
    unit["sidecar_sha256_pre_verdict"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with open(output_path, "w") as f:
        json.dump(unit, f, indent=2)
    return output_path


def main():
    print("=" * 72)
    print(f"voice unit: {VOICE_NAME}  (INVERTED-KILL bound-defender)")
    print("=" * 72)
    print(f"predicted: all 3 fresh smooth-S-curve pairs FAIL coupling test (PASS-the-bound)")
    print(f"kill rule: {KILL_CONDITION['rule']}")
    print(f"run:       {RUN_PROTOCOL['entry_point']}")
    print()
    print("running fresh smooth-S-curve receiver pair coupling tests...")
    out = run_voice()
    for pair_name, pair in out["fresh_pairs"].items():
        mark = "PASS-coupling (counter-bound)" if pair["passed_coupling_test"] else "FAIL-coupling (supports-bound)"
        print(f"  {pair_name:12s}  norm_slope: {pair['normalized_slope']:7.4f}  → {pair['pair_verdict']:25s}  → {mark}")
    print()
    print(f"  pairs PASS coupling: {out['n_pairs_passing_coupling_test']}/{out['n_pairs_total']}")
    print(f"  pairs FAIL coupling: {out['n_pairs_failing_coupling_test']}/{out['n_pairs_total']}")
    print()
    verdict = compute_verdict(out)
    print(f"  voice verdict: {verdict['verdict'].upper()}  (inverted-kill: PASS = bound supported)")
    print(f"  {verdict['rationale']}")
    print()
    sidecar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{VOICE_NAME}.sidecar.json")
    emit_sidecar(verdict, out, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
