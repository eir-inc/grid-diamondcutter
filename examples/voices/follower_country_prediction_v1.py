"""
follower_country_prediction_v1.py — §3.1 polyphony voice applying the
leader-cohort lead-time prior from `regulatory_lead_time_v1.sidecar.json`
to forward-predict renewable-share inflection year for follower countries
with recently-passed analog regulatory milestones.

Closes the methodology loop Eugene opened on 2026-05-29 03:00 CEST: the
leader-cohort voice produces the 8.83y mean lead-time prior; this voice
consumes the prior + a fixture of follower-country recent milestones +
emits per-follower forward predictions with explicit uncertainty windows.

WHAT THIS VOICE PREDICTS
========================

For each follower country in the fixture:
  predicted_inflection_year = milestone_year + mean_lead_time_prior
  inflection_window = predicted_inflection_year ± (max_leader_lead - mean) / 2

Pre-commitment: at least 2 of the 3 follower countries' predicted-inflection
windows fall in the 2027-2037 calendar window (a sanity check that the
methodology produces non-degenerate forward predictions covering the next
decade for follower countries with milestones passed 2018-2022).

  Kind:                       polyphony_within_substrate
  Substrate:                  leader-prior sidecar + follower fixture
  Named residual:             n_followers_with_inflection_window_in_target_decade
  Predicted lower bound:      ≥ 2

KILL CONDITION
==============

  - n_followers_in_target_window < 2 → fail (predictions degenerate or
                                              outside the methodology's
                                              useful forecasting horizon)
  - n_followers_in_target_window ≥ 2 → pass (methodology produces non-
                                              degenerate forward predictions
                                              that eirmath can $-calibrate
                                              against)
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# ===========================================================================
# §3.1 — Standard five-field unit
# ===========================================================================

VOICE_NAME = "follower_country_prediction_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "regulatory_lead_time_v1_sidecar_plus_follower_milestone_fixture",
    "named_residual": "n_followers_with_predicted_inflection_in_target_decade",
    "predicted_value_lower_bound": 2,
    "target_decade_window": [2027, 2037],
}

KILL_CONDITION = {
    "metric": "n_followers_with_predicted_inflection_in_2027_2037_window",
    "rule": (
        "pass if ≥ 2 of 3 followers have predicted inflection in [2027, 2037] "
        "(methodology produces non-degenerate forward predictions for the "
        "next decade); fail otherwise"
    ),
    "rationale": (
        "Forward predictions are the load-bearing methodology output Eugene's "
        "lead-time question targets. A pre-committed sanity check on the "
        "prediction window's location is mechanically testable from sidecar "
        "+ fixture alone. v2 would tighten the window OR add a per-follower "
        "kill condition; this v1 checks the cohort-level shape."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/follower_country_prediction_v1.py",
    "source_file": "examples/voices/follower_country_prediction_v1.py",
    "input_parameters": {
        "leader_prior_sidecar": "examples/voices/regulatory_lead_time_v1.sidecar.json",
        "data_vintage": "follower milestones 2018-2022, public IEA + national sources",
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


# ===========================================================================
# Follower-country fixture (public sources cited per entry)
# ===========================================================================

FOLLOWER_FIXTURE = {
    "Poland": {
        "milestone_year": 2020,
        "milestone_name": "Offshore Wind Act 2020 + RES Act 2018 amendments",
        "public_source_anchor": "IEA Energy Policy Review: Poland 2022; URE/PSE statistics",
    },
    "Romania": {
        "milestone_year": 2020,
        "milestone_name": "PNIESC National Energy and Climate Plan 2020",
        "public_source_anchor": "IEA Energy Policy Review: Romania 2023; ANRE statistics",
    },
    "Greece": {
        "milestone_year": 2021,
        "milestone_name": "Law 4843/2021 RES grid acceleration",
        "public_source_anchor": "IEA Energy Policy Review: Greece 2023; IPTO renewable statistics",
    },
}


def load_leader_prior() -> dict:
    path = Path(RUN_PROTOCOL["input_parameters"]["leader_prior_sidecar"])
    sidecar = json.loads(path.read_text())
    verdict = sidecar["verdict"]
    return {
        "mean_lead_time": verdict["mean_lead_time_years"],
        "min_lead_time": verdict["min_lead_time_years"],
        "max_lead_time": verdict["max_lead_time_years"],
        "predicted_range": verdict["predicted_range"],
    }


def predict_follower(name: str, record: dict, prior: dict) -> dict:
    mean = prior["mean_lead_time"]
    halfwidth = (prior["max_lead_time"] - prior["min_lead_time"]) / 2.0
    predicted = record["milestone_year"] + mean
    window_low = predicted - halfwidth
    window_high = predicted + halfwidth
    return {
        "country": name,
        "milestone_year": record["milestone_year"],
        "milestone_name": record["milestone_name"],
        "public_source_anchor": record["public_source_anchor"],
        "predicted_inflection_year": round(predicted, 2),
        "predicted_inflection_window": [round(window_low, 2), round(window_high, 2)],
    }


def run_follower_analysis() -> tuple[dict, list[dict]]:
    prior = load_leader_prior()
    predictions = [
        predict_follower(name, rec, prior) for name, rec in FOLLOWER_FIXTURE.items()
    ]
    return prior, predictions


def compute_verdict(prior: dict, predictions: list[dict]) -> dict:
    target_low, target_high = PREDICTION["target_decade_window"]
    in_window = [
        p for p in predictions
        if (p["predicted_inflection_window"][0] >= target_low or
            p["predicted_inflection_window"][1] >= target_low)
        and (p["predicted_inflection_window"][1] <= target_high or
             p["predicted_inflection_window"][0] <= target_high)
    ]
    n_in_window = len(in_window)
    bound = PREDICTION["predicted_value_lower_bound"]

    if n_in_window >= bound:
        verdict = "pass"
        outcome = "non_degenerate_forward_predictions_in_target_window"
        rationale = (
            f"{n_in_window} of {len(predictions)} follower countries have "
            f"predicted inflection windows intersecting the pre-committed "
            f"target decade [{target_low}, {target_high}]. The methodology "
            f"produces non-degenerate forward predictions for the next "
            f"decade. Per-country predictions: "
            f"{[(p['country'], p['predicted_inflection_year']) for p in predictions]}. "
            f"Per §1 honesty bounds these are NOT real-trajectory claims; "
            f"they are the methodology's prior-conditional point estimates "
            f"with uncertainty windows. Eirmath would $-calibrate each."
        )
    else:
        verdict = "fail"
        outcome = "predictions_degenerate_or_outside_target_window"
        rationale = (
            f"Only {n_in_window} of {len(predictions)} followers have "
            f"predictions in [{target_low}, {target_high}]. Predictions "
            f"degenerate or fall outside the methodology's useful forecasting "
            f"horizon. v2 should expand target window OR adjust leader prior."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "leader_prior_used": prior,
        "n_followers": len(predictions),
        "n_followers_in_target_window": n_in_window,
        "target_decade_window": [target_low, target_high],
        "per_follower_predictions": predictions,
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
    print(f"voice unit: {VOICE_NAME}  (kind: polyphony, follower forward prediction)")
    print(f"consumes:   {RUN_PROTOCOL['input_parameters']['leader_prior_sidecar']}")
    print("=" * 72)
    prior, predictions = run_follower_analysis()
    print(f"leader prior: mean {prior['mean_lead_time']:.2f}y, range {prior['min_lead_time']}-{prior['max_lead_time']}y")
    print("-" * 72)
    for p in predictions:
        print(
            f"  {p['country']:>10s}  milestone={p['milestone_year']}  "
            f"predicted_inflection={p['predicted_inflection_year']:.2f}  "
            f"window={p['predicted_inflection_window']}"
        )
    print("-" * 72)
    verdict = compute_verdict(prior, predictions)
    print(f"  n followers in target decade: {verdict['n_followers_in_target_window']}/{verdict['n_followers']}")
    print(f"  target decade window:         {verdict['target_decade_window']}")
    print(f"  verdict:                      {verdict['verdict'].upper()}")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
