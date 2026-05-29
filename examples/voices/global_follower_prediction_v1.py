"""
global_follower_prediction_v1.py — §3.1 polyphony voice applying the
v2 expanded-cohort prior (8.92y, drift 0.09y from v1) to non-EU follower
countries with recent renewable acceleration milestones.

Builds on regulatory_lead_time_v2_expanded_cohort.sidecar.json (PR #40)
which established the prior generalizes globally. Forward-predicts
inflection year for Mexico, Vietnam, South Africa, Indonesia.

WHAT THIS VOICE PREDICTS
========================

At least 3 of 4 non-EU follower countries' predicted inflection windows
intersect the target decade [2027, 2037] at the v2 calibration-honest
halfwidth (LOO MAE 1.47y from PR #33).

  Kind:                       polyphony_within_substrate (global forward prediction)
  Substrate:                  v2 expanded prior + leader LOO MAE + non-EU follower fixture
  Named residual:             n_non_eu_followers_in_target_decade
  Predicted lower bound:      ≥ 3

KILL CONDITION
==============

  - n_in_target_window < 3 → fail (global prior application to non-EU
                                    followers is degenerate or out of horizon)
  - n_in_target_window ≥ 3 → pass (global prior applies cross-culturally;
                                    forward predictions cover the next decade
                                    for non-EU followers)
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

VOICE_NAME = "global_follower_prediction_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "regulatory_lead_time_v2_expanded_cohort_sidecar_plus_leader_loo_cv_v1_plus_non_eu_follower_fixture",
    "named_residual": "n_non_eu_followers_with_inflection_in_target_decade",
    "predicted_value_lower_bound": 3,
    "target_decade_window": [2027, 2037],
}

KILL_CONDITION = {
    "metric": "n_non_eu_followers_with_calibration_honest_inflection_in_2027_2037",
    "rule": (
        "pass if ≥ 3 of 4 non-EU followers have predicted inflection in "
        "[2027, 2037] at LOO MAE halfwidth; fail otherwise"
    ),
    "rationale": (
        "Tests whether the global prior (v2 PR #40 PASSed prior generalizes "
        "across EU + non-EU leaders) carries forward when applied to non-EU "
        "follower predictions. v2 calibrated PR #38 used EU followers; this "
        "voice closes the global-application loop."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/global_follower_prediction_v1.py",
    "source_file": "examples/voices/global_follower_prediction_v1.py",
    "input_parameters": {
        "expanded_prior_sidecar": "examples/voices/regulatory_lead_time_v2_expanded_cohort.sidecar.json",
        "loo_mae_halfwidth_years": 1.47,
        "loo_max_halfwidth_years": 3.80,
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


# ===========================================================================
# Non-EU follower fixture (public sources cited per entry)
# ===========================================================================

GLOBAL_FOLLOWER_FIXTURE = {
    "Mexico": {
        "milestone_year": 2020,
        "milestone_name": "Energy Reform 2013 RE provisions + 2020 acceleration plan",
        "public_source_anchor": "IEA EPR: Mexico 2017 + 2023; CFE statistics; SENER renewables outlook",
    },
    "Vietnam": {
        "milestone_year": 2020,
        "milestone_name": "PDP8 draft 2020 + Decision 2068/2015 RE strategy",
        "public_source_anchor": "IEA EPR: Vietnam 2022; MOIT statistics; EVN annual report",
    },
    "South_Africa": {
        "milestone_year": 2020,
        "milestone_name": "IRP 2019 implementation + REIPPPP rounds 5-6 2020",
        "public_source_anchor": "IEA EPR: South Africa 2017 + 2023; DMRE IRP 2019",
    },
    "Indonesia": {
        "milestone_year": 2021,
        "milestone_name": "RUPTL 2021-2030 + Energy Resilience Roadmap 2021",
        "public_source_anchor": "IEA EPR: Indonesia 2022; ESDM statistics; PLN annual report",
    },
}


def load_prior() -> dict:
    path = Path(RUN_PROTOCOL["input_parameters"]["expanded_prior_sidecar"])
    sidecar = json.loads(path.read_text())["verdict"]
    return {
        "mean_lead_time": sidecar["v2_mean_lead_time"],
        "spread": sidecar["v2_spread"],
        "eu_sub_cohort_mean": sidecar["eu_sub_cohort_mean"],
        "non_eu_sub_cohort_mean": sidecar["non_eu_sub_cohort_mean"],
    }


def predict_follower(name: str, record: dict, prior: dict) -> dict:
    mean = prior["mean_lead_time"]
    mae = RUN_PROTOCOL["input_parameters"]["loo_mae_halfwidth_years"]
    max_h = RUN_PROTOCOL["input_parameters"]["loo_max_halfwidth_years"]
    predicted = record["milestone_year"] + mean
    return {
        "country": name,
        "milestone_year": record["milestone_year"],
        "milestone_name": record["milestone_name"],
        "public_source_anchor": record["public_source_anchor"],
        "predicted_inflection_year": round(predicted, 2),
        "calibration_honest_window": [round(predicted - mae, 2), round(predicted + mae, 2)],
        "worst_case_window": [round(predicted - max_h, 2), round(predicted + max_h, 2)],
    }


def run_follower_analysis() -> tuple[dict, list[dict]]:
    prior = load_prior()
    predictions = [predict_follower(name, rec, prior) for name, rec in GLOBAL_FOLLOWER_FIXTURE.items()]
    return prior, predictions


def compute_verdict(prior: dict, predictions: list[dict]) -> dict:
    target_low, target_high = PREDICTION["target_decade_window"]
    in_window = [
        p for p in predictions
        if (p["calibration_honest_window"][0] >= target_low or p["calibration_honest_window"][1] >= target_low)
        and (p["calibration_honest_window"][1] <= target_high or p["calibration_honest_window"][0] <= target_high)
    ]
    n = len(in_window)
    bound = PREDICTION["predicted_value_lower_bound"]

    if n >= bound:
        verdict = "pass"
        outcome = "global_prior_carries_to_non_eu_followers"
        rationale = (
            f"{n}/{len(predictions)} non-EU followers' calibration-honest "
            f"windows intersect [{target_low}, {target_high}]. The global "
            f"prior (v2 expanded cohort, mean {prior['mean_lead_time']:.2f}y, "
            f"EU-vs-non-EU sub-cohorts {prior['eu_sub_cohort_mean']:.2f}y vs "
            f"{prior['non_eu_sub_cohort_mean']:.2f}y) carries forward when "
            f"applied to non-EU followers. Per §1, these are NOT real-trajectory "
            f"claims for any named country — they are methodology prior-"
            f"conditional point estimates with uncertainty windows."
        )
    else:
        verdict = "fail"
        outcome = "global_prior_does_not_carry_to_non_eu_followers"
        rationale = (
            f"Only {n}/{len(predictions)} non-EU followers have predictions "
            f"in [{target_low}, {target_high}]. Global prior application "
            f"shows degeneracy. v2 should refine the prior with sub-region "
            f"per-region voices."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "prior_used": prior,
        "n_followers": len(predictions),
        "n_followers_in_target_window": n,
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
    print(f"voice unit: {VOICE_NAME}")
    print("=" * 72)
    prior, predictions = run_follower_analysis()
    print(f"prior: mean {prior['mean_lead_time']:.2f}y (EU {prior['eu_sub_cohort_mean']:.2f}y / non-EU {prior['non_eu_sub_cohort_mean']:.2f}y)")
    print("-" * 72)
    for p in predictions:
        print(
            f"  {p['country']:>15s}  milestone={p['milestone_year']}  "
            f"predicted={p['predicted_inflection_year']}  "
            f"calibration_window={p['calibration_honest_window']}  "
            f"worst={p['worst_case_window']}"
        )
    print("-" * 72)
    verdict = compute_verdict(prior, predictions)
    print(f"  n followers in target decade: {verdict['n_followers_in_target_window']}/{verdict['n_followers']}")
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
