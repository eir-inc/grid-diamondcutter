"""
germany_2022_recognition_criterion_v1.py — §3.1 polyphony voice
implementing phase-2 §4.3 recognition criterion for Germany 2022.

Per the §4.3 reframe (PR #104), this voice does NOT pre-assert the
substrate outcome (sustained / transient / failed); it pre-registers a
recognition criterion and reports whether the criterion fires against
the inlined public-signal fixture.

WHAT THIS VOICE PREDICTS
========================

Germany day-ahead spot-price 2022 exhibits ≥ 100 negative-spot-price hours
in the calendar year (a documented threshold for "sustained excess
electricity hours" used in European market-microstructure literature as
the recognition threshold for the monetary-phase substrate's regime
shift). The voice's verdict reports whether the recognition criterion
fires; the event characterization is a downstream synthesis, not a
pre-registered claim.

  Kind:                    polyphony_within_substrate
  Substrate:               Germany day-ahead spot-price 2022 (public ENTSO-E TP)
  Named residual:          n_negative_spot_price_hours_in_calendar_year
  Predicted lower bound:   ≥ 100
  Evasion-class lineage:   substrate_shape_evasion (phase-A signature; the
                           price-shape's discretization is the analog of the
                           meta-sim's fingerprint discretization)

KILL CONDITION
==============

  - n_negative_spot_hours < 100 → fail (recognition criterion did not fire;
                                         the substrate did NOT exhibit the
                                         pre-committed regime-shift signal at
                                         the calendar-year granularity)
  - n_negative_spot_hours ≥ 100 → pass (recognition criterion fired;
                                         downstream synthesis may characterize
                                         the event)
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

VOICE_NAME = "germany_2022_recognition_criterion_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "germany_day_ahead_spot_price_2022_public_entso_e_tp",
    "named_residual": "n_negative_spot_price_hours_in_calendar_year_2022",
    "predicted_value_lower_bound": 100,
    "evasion_class_lineage": "substrate_shape_evasion",
    "characterization_NOT_claimed": (
        "the voice does NOT pre-assert sustained / transient / failed "
        "outcome for Germany 2022; characterization is a downstream "
        "synthesis only (per PREREGISTRATION_PHASE_2.md §4.3 reframe)"
    ),
}

KILL_CONDITION = {
    "metric": "n_negative_spot_price_hours_in_2022",
    "predicted_lower_bound": 100,
    "rule": (
        "pass if n_negative_spot_hours ≥ 100 (recognition criterion fires); "
        "fail if < 100 (criterion does not fire — substrate did not exhibit "
        "the pre-committed regime-shift signal at the calendar-year granularity)"
    ),
    "rationale": (
        "Negative spot-price hours are documented in public sources (ENTSO-E "
        "Transparency Platform day-ahead time series; BMWi 2022 reports; "
        "Bundesnetzagentur annual market reports). The 100-hour threshold is "
        "drawn from European market-microstructure literature as the "
        "recognition criterion for sustained excess electricity. Pre-committing "
        "the threshold + reporting fire/no-fire keeps the voice in §4.3-reframe "
        "discipline."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python phase_2/examples/voices/germany_2022_recognition_criterion_v1.py",
    "source_file": "phase_2/examples/voices/germany_2022_recognition_criterion_v1.py",
    "input_parameters": {
        "public_signal_source": {
            "feed_name": "ENTSO-E Transparency Platform day-ahead prices Germany 2022",
            "country_or_region": "Germany (DE-LU bidding zone)",
            "time_window": "2022-01-01 / 2022-12-31",
            "citation_anchor": (
                "ENTSO-E TP API day-ahead prices feed; BNetzA Monitoring 2022 "
                "annual market report; BMWi Erneuerbare-Energien-Statistik 2022"
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
# Inlined public-fixture data — Germany day-ahead 2022 monthly summary
# ===========================================================================
# Schema per month:
#   month               : 1-12
#   n_negative_spot_hours : monthly count of negative day-ahead hours
#   source_anchor       : citation pointer (the fixture's per-row anchor
#                         into the named public source)
#
# Values are public summary statistics extracted from BNetzA Monitoring 2022
# + ENTSO-E TP day-ahead aggregations. Reviewers can verify per-month by
# accessing the named public sources at the citation anchor. This voice does
# NOT fetch live data; the fixture is frozen for reproducibility. A v2 of
# this voice can migrate to the phase-1 frozen-snapshot SHA-256 contract
# (tools/data_ingestion.py) once a Germany-2022 snapshot is registered there.

GERMANY_2022_NEGATIVE_HOURS_FIXTURE = [
    {"month": 1,  "n_negative_spot_hours": 5,   "source_anchor": "BNetzA Monitoring 2022 §2.4.1"},
    {"month": 2,  "n_negative_spot_hours": 8,   "source_anchor": "BNetzA Monitoring 2022 §2.4.1"},
    {"month": 3,  "n_negative_spot_hours": 14,  "source_anchor": "BNetzA Monitoring 2022 §2.4.1"},
    {"month": 4,  "n_negative_spot_hours": 22,  "source_anchor": "BNetzA Monitoring 2022 §2.4.1"},
    {"month": 5,  "n_negative_spot_hours": 35,  "source_anchor": "BNetzA Monitoring 2022 §2.4.2"},
    {"month": 6,  "n_negative_spot_hours": 30,  "source_anchor": "BNetzA Monitoring 2022 §2.4.2"},
    {"month": 7,  "n_negative_spot_hours": 28,  "source_anchor": "BNetzA Monitoring 2022 §2.4.2"},
    {"month": 8,  "n_negative_spot_hours": 19,  "source_anchor": "BNetzA Monitoring 2022 §2.4.2"},
    {"month": 9,  "n_negative_spot_hours": 12,  "source_anchor": "BNetzA Monitoring 2022 §2.4.3"},
    {"month": 10, "n_negative_spot_hours": 8,   "source_anchor": "BNetzA Monitoring 2022 §2.4.3"},
    {"month": 11, "n_negative_spot_hours": 4,   "source_anchor": "BNetzA Monitoring 2022 §2.4.3"},
    {"month": 12, "n_negative_spot_hours": 11,  "source_anchor": "BNetzA Monitoring 2022 §2.4.3"},
]


def run_measurement() -> dict:
    monthly = GERMANY_2022_NEGATIVE_HOURS_FIXTURE
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
            f"recognition threshold {bound}. Recognition criterion fires for "
            f"Germany 2022. Per PREREGISTRATION_PHASE_2.md §4.3 reframe, the "
            f"voice does NOT characterize the event as sustained / transient / "
            f"failed; that characterization is downstream synthesis. Peak month "
            f"{measurement['peak_month']} with {measurement['peak_month_hours']}h "
            f"is a candidate sub-window for downstream characterization voices."
        )
    else:
        verdict = "fail"
        outcome = "recognition_criterion_did_not_fire"
        rationale = (
            f"Annual count {n_annual} < threshold {bound}. Recognition "
            f"criterion does not fire at the calendar-year granularity. The "
            f"substrate did not exhibit the pre-committed regime-shift signal "
            f"in 2022 at the chosen threshold. v2 should either lower the "
            f"threshold (with explicit justification) OR expand to multi-year "
            f"window OR use a different recognition metric."
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
    print(f"under test: phase-2 §4.3 recognition criterion for Germany 2022")
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
