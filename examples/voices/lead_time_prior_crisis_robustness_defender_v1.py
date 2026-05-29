"""
lead_time_prior_crisis_robustness_defender_v1.py — §3.1 polyphony voice
(inverted kill) defending a NEW empirical honesty bound surfaced by
cajal's cross-lane chain-loop test (PR #48):

  "The leader-cohort lead-time prior assumes NO exogenous economic crisis
   during the policy → deployment window. Crisis-affected countries break
   the assumption."

cajal applied the v2 expanded-cohort prior to Greece and observed
inflection 2013 vs predicted 2016-2019 (~4y early). The exogenous shock
(Eurozone crisis 2010-2015) compressed the policy → deployment window.

This voice DEFENDS the empirical bound by mechanically checking that the
lead-time prior excludes crisis-affected countries from its training
cohort, AND that documented crisis-window countries are flagged as
out-of-scope for direct prior application.

WHAT THIS VOICE PREDICTS
========================

The leader-cohort fixture in regulatory_lead_time_v1 contains zero
countries whose policy → deployment window (milestone_year to
inflection_year) overlaps a documented major economic crisis period.

  Kind:                    polyphony_within_substrate (bound defender, inverted)
  Substrate:               regulatory_lead_time_v1 leader fixture
  Named residual:          n_leaders_with_crisis_overlap_in_pd_window
  Predicted upper bound:   0 (no crisis-overlap leader in training cohort)
  Bound under test:        empirical bound surfaced by cajal PR #48

CRISIS PERIODS (documented, public)
=====================================

  2008-2010 — Global Financial Crisis (worldwide impact)
  2010-2015 — Eurozone Sovereign Debt Crisis (Eurozone members)
  2014-2016 — Oil Price Collapse (oil-exporting + petrostate impact)
  2020-2022 — COVID-19 Pandemic + 2022 Energy Crisis

A leader country whose [milestone_year, inflection_year] window OVERLAPS
any of these is a candidate for being a special-case substrate that the
direct prior cannot recover.

KILL CONDITION (INVERTED)
=========================

  - n_crisis_overlap_leaders == 0 → pass (bound supported; training
                                           cohort excludes crisis-window
                                           countries by construction)
  - n_crisis_overlap_leaders > 0  → fail (bound counter-observation;
                                           prior was trained on crisis-
                                           affected countries; honest
                                           prior needs to drop those or
                                           the bound text needs revision)

A PASS supports the bound surfaced by cajal #48 by direct fixture
inspection. A FAIL produces evidence that the v1 prior is itself
contaminated by crisis windows and a v2 should refit.
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

VOICE_NAME = "lead_time_prior_crisis_robustness_defender_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "regulatory_lead_time_v1_leader_fixture",
    "named_residual": "n_leaders_with_crisis_overlap_in_policy_to_deployment_window",
    "predicted_value_upper_bound": 0,
    "verdict_inversion": True,
    "bound_under_test": (
        "Empirical bound surfaced by cajal PR #48: leader-cohort lead-time "
        "prior assumes NO exogenous economic crisis during the policy → "
        "deployment window."
    ),
    "documented_crisis_periods": [
        {"name": "Global Financial Crisis", "start": 2008, "end": 2010, "scope": "worldwide"},
        {"name": "Eurozone Sovereign Debt Crisis", "start": 2010, "end": 2015, "scope": "Eurozone members"},
        {"name": "Oil Price Collapse", "start": 2014, "end": 2016, "scope": "oil-exporting + petrostates"},
        {"name": "COVID-19 + Energy Crisis", "start": 2020, "end": 2022, "scope": "worldwide"},
    ],
}

KILL_CONDITION = {
    "metric": "n_leader_pd_windows_overlapping_documented_crisis_period",
    "rule": (
        "pass if 0 leader policy → deployment windows overlap any documented "
        "crisis period (bound supported by fixture inspection); fail if any "
        "leader overlaps (bound counter-observation; prior may be crisis-"
        "contaminated)"
    ),
    "rationale": (
        "Crisis-window overlap is detectable from the public fixture data "
        "alone — milestone_year and inflection_year are already in the v1 "
        "sidecar; crisis periods are documented in public sources. The "
        "inverted kill protects the bound surfaced by cajal #48. A FAIL "
        "would require either a v2 prior with crisis-affected leaders "
        "removed or an explicit broadening of the bound text."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/lead_time_prior_crisis_robustness_defender_v1.py",
    "source_file": "examples/voices/lead_time_prior_crisis_robustness_defender_v1.py",
    "input_parameters": {
        "leader_prior_sidecar": "examples/voices/regulatory_lead_time_v1.sidecar.json",
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


def _windows_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return not (a_end < b_start or b_end < a_start)


def detect_crisis_overlaps() -> list[dict]:
    p = RUN_PROTOCOL["input_parameters"]
    sidecar = json.loads(Path(p["leader_prior_sidecar"]).read_text())
    leaders = sidecar["verdict"]["per_country_analyses"]
    crises = PREDICTION["documented_crisis_periods"]
    results = []
    for ld in leaders:
        ld_start = ld["milestone_year"]
        ld_end = ld["inflection_year"]
        overlapping_crises = [
            c["name"] for c in crises
            if _windows_overlap(ld_start, ld_end, c["start"], c["end"])
        ]
        results.append({
            "country": ld["country"],
            "policy_to_deployment_window": [ld_start, ld_end],
            "overlapping_documented_crises": overlapping_crises,
            "n_overlapping_crises": len(overlapping_crises),
            "has_crisis_overlap": len(overlapping_crises) > 0,
        })
    return results


def compute_verdict(overlap_results: list[dict]) -> dict:
    n_overlap = sum(1 for r in overlap_results if r["has_crisis_overlap"])
    upper_bound = PREDICTION["predicted_value_upper_bound"]
    offenders = [r for r in overlap_results if r["has_crisis_overlap"]]

    if n_overlap <= upper_bound:
        verdict = "pass"
        outcome = "bound_supported_no_crisis_overlap_in_training_cohort"
        rationale = (
            f"Inspected {len(overlap_results)} leader policy → deployment "
            f"windows against {len(PREDICTION['documented_crisis_periods'])} "
            f"documented crisis periods. Overlap count: {n_overlap}. "
            f"Pre-committed upper bound: {upper_bound}. Empirical bound "
            f"surfaced by cajal PR #48 supported by direct fixture inspection."
        )
    else:
        verdict = "fail"
        outcome = "bound_counter_observation_crisis_contamination"
        rationale = (
            f"{n_overlap} leader(s) have policy → deployment windows "
            f"overlapping documented crisis periods: "
            f"{[(o['country'], o['overlapping_documented_crises']) for o in offenders]}. "
            f"Crosses the pre-committed upper bound of {upper_bound}. The "
            f"v1 prior may be crisis-contaminated; a v2 refit excluding "
            f"these countries would produce a different mean lead-time + "
            f"different forward predictions. cajal's chain-loop test would "
            f"validate the v2."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "n_leaders_inspected": len(overlap_results),
        "n_leaders_with_crisis_overlap": n_overlap,
        "predicted_upper_bound": upper_bound,
        "per_leader_crisis_check": overlap_results,
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
    overlaps = detect_crisis_overlaps()
    for r in overlaps:
        mark = "✗" if r["has_crisis_overlap"] else "✓"
        print(
            f"  [{mark}] {r['country']:>15s}  window={r['policy_to_deployment_window']}  "
            f"overlapping_crises={r['overlapping_documented_crises']}"
        )
    print("-" * 72)
    verdict = compute_verdict(overlaps)
    print(f"  n leaders inspected:            {verdict['n_leaders_inspected']}")
    print(f"  n leaders with crisis overlap:  {verdict['n_leaders_with_crisis_overlap']}")
    print(f"  pre-committed upper bound:      {verdict['predicted_upper_bound']}")
    print(f"  verdict:                        {verdict['verdict'].upper()}")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
