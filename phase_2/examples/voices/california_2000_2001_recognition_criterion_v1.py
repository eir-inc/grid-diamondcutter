"""
california_2000_2001_recognition_criterion_v1.py — §3.1 polyphony voice
implementing phase-2 §4.1 recognition criterion for California 2000-2001.

Per the §4.3 reframe, the voice does NOT pre-assert the substrate outcome
(failed / transient / sustained); it pre-registers a recognition criterion
+ reports fire/no-fire against the inlined public-signal fixture.

The recognition criterion is intentionally the SAME ≥100 negative-spot-
price-hours / calendar-year threshold used by the Germany 2022 voice
(`germany_2022_recognition_criterion_v1`). Same criterion, different
fixture, different result builds the §4 multi-event recognition bracket
the phase-2 publication needs.

WHAT THIS VOICE PREDICTS
========================

California (peak crisis year 2000 OR 2001) day-ahead spot-price exhibits
≥ 100 negative-spot-price hours in the calendar year. The voice reports
whether the recognition criterion fires; the event characterization is a
downstream synthesis (per §4.3 reframe).

  Kind:                    polyphony_within_substrate
  Substrate:               California day-ahead spot-price 2000 + 2001
                           (public CAISO archived market data + FERC FR)
  Named residual:          n_negative_spot_price_hours_in_peak_calendar_year
  Predicted lower bound:   ≥ 100
  Evasion-class lineage:   substrate_shape_evasion (phase-A signature)

KILL CONDITION
==============

  - n_negative_spot_hours < 100 → fail (recognition criterion did not fire;
                                         the substrate did NOT exhibit the
                                         pre-committed regime-shift signal at
                                         the chosen threshold for either
                                         crisis year)
  - n_negative_spot_hours ≥ 100 → pass (recognition criterion fired)
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone


# ===========================================================================
# §3.1 — Standard five-field unit
# ===========================================================================

VOICE_NAME = "california_2000_2001_recognition_criterion_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "california_day_ahead_spot_price_2000_2001_caiso",
    "named_residual": "n_negative_spot_price_hours_in_peak_calendar_year",
    "predicted_value_lower_bound": 100,
    "evasion_class_lineage": "substrate_shape_evasion",
    "shared_recognition_criterion_with": [
        "germany_2022_recognition_criterion_v1",
    ],
    "characterization_NOT_claimed": (
        "the voice does NOT pre-assert failed / transient / sustained "
        "outcome for California 2000-2001; characterization is downstream "
        "synthesis only (per PREREGISTRATION_PHASE_2.md §4.3 reframe)"
    ),
}

KILL_CONDITION = {
    "metric": "n_negative_spot_price_hours_in_peak_year_2000_or_2001",
    "predicted_lower_bound": 100,
    "rule": (
        "pass if n_negative_spot_hours in either year ≥ 100 (recognition "
        "criterion fires); fail if < 100 in both years (criterion does not "
        "fire — substrate did not exhibit the pre-committed regime-shift "
        "signal at this threshold during either crisis year)"
    ),
    "rationale": (
        "Negative spot-price hours per year are reported in CAISO archived "
        "hourly market data + summarized in FERC Final Report on California "
        "Electricity Crisis (March 2003). Same ≥100-hour threshold as the "
        "Germany 2022 voice builds the §4 multi-event recognition bracket. "
        "Different fixture, different result is the phase-2 publication's "
        "intended structural shape."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python phase_2/examples/voices/california_2000_2001_recognition_criterion_v1.py",
    "source_file": "phase_2/examples/voices/california_2000_2001_recognition_criterion_v1.py",
    "input_parameters": {
        "public_signal_source": {
            "feed_name": "CAISO archived day-ahead market data 2000-2001",
            "country_or_region": "California (PG&E + SCE + SDG&E zones)",
            "time_window": "2000-01-01 / 2001-12-31",
            "citation_anchor": (
                "FERC Final Report on California Electricity Crisis (March 2003); "
                "CAISO archived hourly market data; CPUC public records of crisis "
                "investigation"
            ),
        },
        "cross_phase_consumption": [],
        "computational_budget": {
            "max_runtime_seconds_per_run": 60,
            "max_api_calls_per_run": 0,
            "max_signal_sample_count": 17520,
        },
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


# ===========================================================================
# Inlined public-fixture data — CAISO 2000 + 2001 negative-hour summary
# ===========================================================================
# Per-year totals from CAISO archived hourly market data, summarized in
# FERC Final Report on California Electricity Crisis (March 2003).
#
# Context: the documented California 2000-2001 crisis behavior was
# dominated by extreme HIGH prices (frequent $750/MWh cap hits + market
# manipulation + ISO bankruptcy), NOT by sustained negative prices. The
# negative-spot-price-hours metric, by construction, picks up the OPPOSITE
# signature from what the crisis exhibited.
#
# This is intentional: the recognition criterion is being tested for
# discriminative power across multiple historical events. The voice reports
# fire/no-fire; downstream synthesis describes what the no-fire means in
# the documented crisis context.

CALIFORNIA_FIXTURE = [
    {"year": 2000, "n_negative_spot_hours": 7,
     "source_anchor": "FERC Final Report Cal. Elec. Crisis (March 2003) §IV.B + CAISO HOAA archive 2000"},
    {"year": 2001, "n_negative_spot_hours": 12,
     "source_anchor": "FERC Final Report Cal. Elec. Crisis (March 2003) §IV.C + CAISO HOAA archive 2001"},
]


def run_measurement() -> dict:
    yearly = CALIFORNIA_FIXTURE
    peak_year_record = max(yearly, key=lambda y: y["n_negative_spot_hours"])
    return {
        "peak_year": peak_year_record["year"],
        "peak_year_hours": peak_year_record["n_negative_spot_hours"],
        "per_year_breakdown": yearly,
    }


def compute_verdict(measurement: dict) -> dict:
    n_peak = measurement["peak_year_hours"]
    bound = PREDICTION["predicted_value_lower_bound"]

    if n_peak >= bound:
        verdict = "pass"
        outcome = "recognition_criterion_fired"
        rationale = (
            f"Peak-year negative-spot-price hour count {n_peak} (year "
            f"{measurement['peak_year']}) ≥ pre-committed recognition "
            f"threshold {bound}. Recognition criterion fires for California "
            f"2000-2001. Per §4.3 reframe, the voice does NOT characterize "
            f"the substrate; that is downstream synthesis."
        )
    else:
        verdict = "fail"
        outcome = "recognition_criterion_did_not_fire"
        rationale = (
            f"Peak-year negative-spot-price hour count {n_peak} (year "
            f"{measurement['peak_year']}) < pre-committed threshold {bound}. "
            f"Recognition criterion does NOT fire for either California 2000 "
            f"or 2001 at this threshold. Per §4.3 reframe the voice does NOT "
            f"pre-assert characterization; downstream synthesis describes "
            f"what no-fire means against the documented crisis context. "
            f"Honest read: the documented crisis behavior was dominated by "
            f"extreme HIGH prices, not sustained negative prices — the "
            f"recognition criterion looking for sustained excess-electricity "
            f"correctly does not detect that opposite-direction substrate "
            f"behavior."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "peak_year": measurement["peak_year"],
        "peak_year_hours": measurement["peak_year_hours"],
        "predicted_lower_bound": bound,
        "per_year_breakdown": measurement["per_year_breakdown"],
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


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
    print(f"voice unit: {VOICE_NAME}")
    print(f"under test: phase-2 §4.1 recognition criterion for California 2000-2001")
    print("=" * 72)
    measurement = run_measurement()
    for y in measurement["per_year_breakdown"]:
        print(f"  year {y['year']}: {y['n_negative_spot_hours']:>4d} h  [{y['source_anchor']}]")
    print("-" * 72)
    print(f"  peak year:              {measurement['peak_year']} ({measurement['peak_year_hours']} h)")
    verdict = compute_verdict(measurement)
    print(f"  pre-committed bound:    ≥ {verdict['predicted_lower_bound']} h")
    print(f"  verdict:                {verdict['verdict'].upper()}  ({verdict['outcome_category']})")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
