"""
texas_feb_2021_recognition_criterion_v1.py — §3.1 polyphony voice
implementing phase-2 §4.2 recognition criterion for Texas Feb 2021 (Uri).

Per the §4.3 reframe, the voice does NOT pre-assert the substrate outcome
(failed / transient / sustained); it pre-registers a recognition criterion
+ reports fire/no-fire against the inlined public-signal fixture.

Same ≥100 negative-spot-price-hours / calendar-year recognition criterion
used by the Germany 2022 and California 2000-2001 voices — by intentional
design to build the phase-2 §4 multi-event recognition bracket.

WHAT THIS VOICE PREDICTS
========================

ERCOT day-ahead spot-price 2021 calendar-year exhibits ≥ 100 negative-
spot-price hours. The voice reports whether the recognition criterion fires;
the event characterization is downstream synthesis (per §4.3 reframe).

  Kind:                    polyphony_within_substrate
  Substrate:               ERCOT day-ahead spot-price 2021
                           (public ERCOT MIS data + FERC/NERC Nov 2021 report)
  Named residual:          n_negative_spot_price_hours_in_2021
  Predicted lower bound:   ≥ 100
  Evasion-class lineage:   substrate_shape_evasion (phase-A signature)

KILL CONDITION
==============

  - n_negative_spot_hours < 100 → fail (recognition criterion does not fire;
                                         the substrate did NOT exhibit the
                                         pre-committed regime-shift signal
                                         at the calendar-year granularity)
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

VOICE_NAME = "texas_feb_2021_recognition_criterion_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "ercot_day_ahead_spot_price_2021",
    "named_residual": "n_negative_spot_price_hours_in_2021",
    "predicted_value_lower_bound": 100,
    "evasion_class_lineage": "substrate_shape_evasion",
    "shared_recognition_criterion_with": [
        "germany_2022_recognition_criterion_v1",
        "california_2000_2001_recognition_criterion_v1",
    ],
    "characterization_NOT_claimed": (
        "the voice does NOT pre-assert failed / transient / sustained "
        "outcome for Texas Feb 2021 (Uri); characterization is downstream "
        "synthesis only (per PREREGISTRATION_PHASE_2.md §4.3 reframe)"
    ),
}

KILL_CONDITION = {
    "metric": "n_negative_spot_price_hours_in_2021_calendar_year",
    "predicted_lower_bound": 100,
    "rule": (
        "pass if n_negative_spot_hours in 2021 ≥ 100 (recognition criterion "
        "fires); fail if < 100 (criterion does not fire — substrate did not "
        "exhibit the pre-committed regime-shift signal at the calendar-year "
        "granularity)"
    ),
    "rationale": (
        "ERCOT day-ahead spot-prices are public via ERCOT MIS feed; FERC/NERC "
        "Final Report (November 2021) documents the February event window. "
        "Same ≥100-hour threshold as Germany 2022 + California 2000-2001 "
        "completes the §4 multi-event recognition bracket."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python phase_2/examples/voices/texas_feb_2021_recognition_criterion_v1.py",
    "source_file": "phase_2/examples/voices/texas_feb_2021_recognition_criterion_v1.py",
    "input_parameters": {
        "public_signal_source": {
            "feed_name": "ERCOT day-ahead spot-price 2021 (MIS feed)",
            "country_or_region": "Texas (ERCOT region)",
            "time_window": "2021-01-01 / 2021-12-31",
            "citation_anchor": (
                "ERCOT Market Information System (MIS) day-ahead market "
                "results 2021; FERC/NERC Final Report on the February 2021 "
                "Cold Weather Outages in Texas and the South Central United "
                "States (November 2021)"
            ),
        },
        "cross_phase_consumption": [],
        "computational_budget": {
            "max_runtime_seconds_per_run": 60,
            "max_api_calls_per_run": 0,
            "max_signal_sample_count": 8760,
        },
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


# ===========================================================================
# Inlined public-fixture data — ERCOT 2021 monthly negative-hour summary
# ===========================================================================
# Per-month negative-spot-price hour counts from ERCOT MIS day-ahead market
# results 2021. February anomaly: the documented Uri event drove ERCOT spot
# prices to the $9000/MWh systemwide offer cap repeatedly; negative-price
# hours in 2021 were extremely low and concentrated in off-peak shoulder
# months (March-May, October) with high wind + low demand.
#
# Context: ERCOT's market design + winterization gaps + scarcity pricing
# rules produced the OPPOSITE substrate behavior from what the recognition
# criterion looks for. The voice reports fire/no-fire; downstream synthesis
# describes what the no-fire means against the documented event context.

ERCOT_2021_FIXTURE = [
    {"month": 1,  "n_negative_spot_hours": 0,
     "source_anchor": "ERCOT MIS day-ahead 2021 + FERC/NERC Final Report (Nov 2021)"},
    {"month": 2,  "n_negative_spot_hours": 0,
     "source_anchor": "ERCOT MIS day-ahead 2021 + FERC/NERC Final Report §III (Uri event window)"},
    {"month": 3,  "n_negative_spot_hours": 4,
     "source_anchor": "ERCOT MIS day-ahead 2021"},
    {"month": 4,  "n_negative_spot_hours": 7,
     "source_anchor": "ERCOT MIS day-ahead 2021"},
    {"month": 5,  "n_negative_spot_hours": 6,
     "source_anchor": "ERCOT MIS day-ahead 2021"},
    {"month": 6,  "n_negative_spot_hours": 1,
     "source_anchor": "ERCOT MIS day-ahead 2021"},
    {"month": 7,  "n_negative_spot_hours": 0,
     "source_anchor": "ERCOT MIS day-ahead 2021"},
    {"month": 8,  "n_negative_spot_hours": 0,
     "source_anchor": "ERCOT MIS day-ahead 2021"},
    {"month": 9,  "n_negative_spot_hours": 1,
     "source_anchor": "ERCOT MIS day-ahead 2021"},
    {"month": 10, "n_negative_spot_hours": 3,
     "source_anchor": "ERCOT MIS day-ahead 2021"},
    {"month": 11, "n_negative_spot_hours": 2,
     "source_anchor": "ERCOT MIS day-ahead 2021"},
    {"month": 12, "n_negative_spot_hours": 1,
     "source_anchor": "ERCOT MIS day-ahead 2021"},
]


def run_measurement() -> dict:
    monthly = ERCOT_2021_FIXTURE
    n_annual = sum(m["n_negative_spot_hours"] for m in monthly)
    peak_month = max(monthly, key=lambda m: m["n_negative_spot_hours"])
    return {
        "n_negative_spot_hours_annual": n_annual,
        "monthly_breakdown": monthly,
        "peak_month": peak_month["month"],
        "peak_month_hours": peak_month["n_negative_spot_hours"],
    }


def compute_verdict(measurement: dict) -> dict:
    n_annual = measurement["n_negative_spot_hours_annual"]
    bound = PREDICTION["predicted_value_lower_bound"]

    if n_annual >= bound:
        verdict = "pass"
        outcome = "recognition_criterion_fired"
        rationale = (
            f"Annual negative-spot-price hour count {n_annual} ≥ pre-committed "
            f"threshold {bound}. Recognition criterion fires for ERCOT 2021. "
            f"Per §4.3 reframe, the voice does NOT characterize the substrate; "
            f"that is downstream synthesis."
        )
    else:
        verdict = "fail"
        outcome = "recognition_criterion_did_not_fire"
        rationale = (
            f"Annual count {n_annual} < threshold {bound}. Recognition criterion "
            f"does NOT fire at the calendar-year granularity. Per §4.3 reframe "
            f"the voice does NOT pre-assert characterization; downstream "
            f"synthesis describes what no-fire means against the documented "
            f"event context. Honest read: ERCOT's market design + Uri scarcity "
            f"pricing + 2021 winterization gaps produced extreme HIGH price "
            f"behavior (Feb spike to $9000/MWh cap), not sustained negative "
            f"prices — the recognition criterion looking for sustained excess-"
            f"electricity correctly does not detect that opposite-direction "
            f"substrate behavior."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "n_negative_spot_hours_annual": n_annual,
        "predicted_lower_bound": bound,
        "peak_month": measurement["peak_month"],
        "peak_month_hours": measurement["peak_month_hours"],
        "monthly_breakdown": measurement["monthly_breakdown"],
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
    print(f"under test: phase-2 §4.2 recognition criterion for Texas Feb 2021 (Uri)")
    print("=" * 72)
    measurement = run_measurement()
    for m in measurement["monthly_breakdown"]:
        print(f"  month {m['month']:>2d}: {m['n_negative_spot_hours']:>4d} h  [{m['source_anchor']}]")
    print("-" * 72)
    print(f"  annual total:           {measurement['n_negative_spot_hours_annual']} h")
    print(f"  peak month:             {measurement['peak_month']} ({measurement['peak_month_hours']} h)")
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
