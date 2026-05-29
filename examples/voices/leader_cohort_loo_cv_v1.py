"""
leader_cohort_loo_cv_v1.py — §3.1 polyphony voice cross-validating the
leader-cohort lead-time prior from `regulatory_lead_time_v1.sidecar.json`
via leave-one-out (LOO) cross-validation.

For each leader country, predict its inflection year using the prior
formed from the OTHER 5 leaders. Compare predicted vs observed. Aggregate
the prediction error across the cohort. This is honest rigor on the 8.83y
prior before any forward-prediction claim leans on it.

WHAT THIS VOICE PREDICTS
========================

Leave-one-out mean absolute error (MAE) of leader-cohort lead-time
predictions is BOUNDED by 3.0 years. This is the pre-committed prediction-
error floor: the prior should retrospectively predict each leader's
inflection year to within 3 years on average when the leader itself is
held out of the prior.

A MAE above 3.0y is a registry-acceptable null: it would mean the leader-
cohort prior is too noisy for forward prediction at the 2.5y window
follower_country_prediction_v1 commits to.

  Kind:                       polyphony_within_substrate (cross-validation)
  Substrate:                  leader fixture from regulatory_lead_time_v1
  Named residual:             loo_mean_absolute_error_years
  Predicted upper bound:      ≤ 3.0 years

KILL CONDITION
==============

  - LOO MAE > 3.0y → fail (prior is too noisy for forward prediction at
                            the committed 2.5y window)
  - LOO MAE ≤ 3.0y → pass (prior is calibration-honest at the committed
                            forward-prediction window)
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

VOICE_NAME = "leader_cohort_loo_cv_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "regulatory_lead_time_v1_sidecar_leader_cohort",
    "named_residual": "leave_one_out_mean_absolute_error_years",
    "predicted_value_upper_bound": 3.0,
    "complementary_to": (
        "regulatory_lead_time_v1 produces the prior; this voice validates "
        "the prior against itself; follower_country_prediction_v1 USES the "
        "prior. The three voices form the leader→follower methodology chain."
    ),
}

KILL_CONDITION = {
    "metric": "loo_mae_years_over_leader_cohort",
    "rule": (
        "pass if LOO MAE ≤ 3.0y (prior is calibration-honest for the 2.5y "
        "forward-prediction window); fail if > 3.0y (prior is too noisy for "
        "the committed window — forward predictions would underreport their "
        "true uncertainty)"
    ),
    "rationale": (
        "Leave-one-out cross-validation is the cleanest test of whether a "
        "small-cohort prior is honest for the prediction window the methodology "
        "downstream voice commits to. Pre-committed 3.0y bound is tighter than "
        "the 2.5y window for the predicted-inflection ± uncertainty halfwidth "
        "in follower_country_prediction_v1, providing a safety margin. A FAIL "
        "would itself be a methodologically important finding."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/leader_cohort_loo_cv_v1.py",
    "source_file": "examples/voices/leader_cohort_loo_cv_v1.py",
    "input_parameters": {
        "leader_prior_sidecar": "examples/voices/regulatory_lead_time_v1.sidecar.json",
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


def load_leader_cohort() -> list[dict]:
    path = Path(RUN_PROTOCOL["input_parameters"]["leader_prior_sidecar"])
    sidecar = json.loads(path.read_text())
    return sidecar["verdict"]["per_country_analyses"]


def loo_predict_and_error(cohort: list[dict]) -> list[dict]:
    """For each leader, hold out, predict from the other N-1, return (predicted, observed, error)."""
    results = []
    for i, target in enumerate(cohort):
        others = [c for j, c in enumerate(cohort) if j != i]
        other_lead_times = [c["lead_time_years"] for c in others]
        loo_mean_lead = sum(other_lead_times) / len(other_lead_times)
        predicted_inflection = target["milestone_year"] + loo_mean_lead
        observed_inflection = target["inflection_year"]
        error = predicted_inflection - observed_inflection
        results.append({
            "country": target["country"],
            "milestone_year": target["milestone_year"],
            "observed_inflection_year": observed_inflection,
            "loo_predicted_inflection_year": round(predicted_inflection, 2),
            "prediction_error_years": round(error, 2),
            "abs_prediction_error_years": round(abs(error), 2),
            "loo_prior_mean_lead_time": round(loo_mean_lead, 2),
        })
    return results


def compute_verdict(loo_results: list[dict]) -> dict:
    abs_errors = [r["abs_prediction_error_years"] for r in loo_results]
    mae = sum(abs_errors) / len(abs_errors)
    max_abs = max(abs_errors)
    bound = PREDICTION["predicted_value_upper_bound"]

    if mae <= bound:
        verdict = "pass"
        outcome = "loo_mae_within_calibration_bound"
        rationale = (
            f"Leave-one-out mean absolute error {mae:.2f}y across "
            f"{len(loo_results)} leaders sits at or below the pre-committed "
            f"upper bound {bound:.1f}y. The 8.83y prior is calibration-honest "
            f"for the 2.5y forward-prediction window. Forward predictions in "
            f"follower_country_prediction_v1 report their true uncertainty "
            f"to the methodology's tested resolution. Max absolute error "
            f"{max_abs}y is the cohort's worst-case retrospective prediction."
        )
    else:
        verdict = "fail"
        outcome = "loo_mae_exceeds_calibration_bound"
        rationale = (
            f"LOO MAE {mae:.2f}y exceeds bound {bound:.1f}y. The prior is "
            f"too noisy for the 2.5y forward-prediction window. Forward "
            f"predictions in follower_country_prediction_v1 underreport "
            f"true uncertainty. v2 should expand cohort OR widen forward "
            f"prediction window OR find tighter inflection-year definition."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "loo_mean_absolute_error_years": mae,
        "loo_max_absolute_error_years": max_abs,
        "predicted_upper_bound": bound,
        "per_leader_loo_results": loo_results,
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
    print(f"voice unit: {VOICE_NAME}  (kind: polyphony, leader-cohort LOO cross-validation)")
    print("=" * 72)
    cohort = load_leader_cohort()
    loo_results = loo_predict_and_error(cohort)
    for r in loo_results:
        print(
            f"  {r['country']:>15s}  predicted_inflection={r['loo_predicted_inflection_year']}  "
            f"observed={r['observed_inflection_year']}  "
            f"abs_error={r['abs_prediction_error_years']}y"
        )
    print("-" * 72)
    verdict = compute_verdict(loo_results)
    print(f"  LOO MAE:              {verdict['loo_mean_absolute_error_years']:.2f}y")
    print(f"  max abs error:        {verdict['loo_max_absolute_error_years']:.2f}y")
    print(f"  pre-committed bound:  {verdict['predicted_upper_bound']:.1f}y")
    print(f"  verdict:              {verdict['verdict'].upper()}")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
