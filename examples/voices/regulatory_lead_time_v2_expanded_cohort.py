"""
regulatory_lead_time_v2_expanded_cohort.py — v2 of regulatory_lead_time_v1
with the leader cohort expanded from 6 to 12 countries (6 EU + 6 non-EU).

v1 had n=6 (all EU); the LOO-CV (PR #33) showed MAE 1.47y, max 3.8y (UK).
v2 doubles the cohort and tests whether the 8.83y prior holds under
expansion or whether the EU-only fixture was over-fit to a regional
regulatory archetype.

WHAT THIS VOICE PREDICTS
========================

With 12 leader countries (6 EU + 6 non-EU: Japan, China, USA, Australia,
Brazil, India), the mean lead-time stays within ±2.0y of the v1 EU-only
prior (8.83y), and the spread (max - min) stays within 1.5x the v1 spread
(5y).

  Kind:                       polyphony_within_substrate
  Substrate:                  12-country leader fixture (6 EU + 6 non-EU)
  Named residual:             v2_mean_lead_time_drift_from_v1_prior
  Predicted bound:            abs(v2_mean - 8.83) ≤ 2.0
                              AND (v2_max - v2_min) ≤ 7.5

KILL CONDITION
==============

  - drift > 2.0y OR spread > 7.5y → fail (v1 EU-only fixture was over-fit;
                                           the prior does not generalize
                                           globally without per-region
                                           voice addition)
  - drift ≤ 2.0y AND spread ≤ 7.5y → pass (prior generalizes globally at
                                           the methodology's current
                                           characterization)
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

VOICE_NAME = "regulatory_lead_time_v2_expanded_cohort"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "12_leader_countries_6_EU_plus_6_non_EU",
    "named_residual": "v2_mean_lead_time_drift_from_v1_prior_plus_spread_check",
    "v1_prior_mean": 8.83,
    "v1_prior_spread": 5,
    "predicted_drift_bound": 2.0,
    "predicted_spread_bound_x_v1": 1.5,
    "lineage": "v2 of regulatory_lead_time_v1 (PR #30); tests whether EU-only fixture was over-fit to regional archetype",
}

KILL_CONDITION = {
    "metric": "drift_from_v1_prior_and_spread_vs_v1",
    "rule": (
        "pass if abs(v2_mean - 8.83) ≤ 2.0 AND (v2_max - v2_min) ≤ 7.5; "
        "fail if either bound crossed"
    ),
    "rationale": (
        "Two simultaneous bounds: stability of the central tendency (mean "
        "shouldn't drift far) AND stability of the spread (cohort shouldn't "
        "spread much wider). Either failure mode flags region-specific "
        "behavior that the methodology should recognize as a v3 per-region "
        "voice rather than a single-prior generalization."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/regulatory_lead_time_v2_expanded_cohort.py",
    "source_file": "examples/voices/regulatory_lead_time_v2_expanded_cohort.py",
    "input_parameters": {
        "leader_countries": [
            "Denmark", "Germany", "Spain", "Portugal", "United_Kingdom", "Italy",
            "Japan", "China", "United_States", "Australia", "Brazil", "India",
        ],
        "data_vintage": "milestones 1992-2014, inflections 2000-2022; public IEA/IRENA/national sources",
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


# ===========================================================================
# Expanded leader fixture (12 countries; public sources cited inline)
# ===========================================================================

LEADER_FIXTURE_V2 = {
    # EU 6 (same as v1)
    "Denmark":        {"milestone_year": 1992, "milestone_name": "Wind feed-in tariff law (Energy Act amendment 1992)", "inflection_year": 2001, "public_source_anchor": "IEA EPR: Denmark 2017 + 2023"},
    "Germany":        {"milestone_year": 2000, "milestone_name": "EEG 2000 feed-in tariff", "inflection_year": 2009, "public_source_anchor": "IEA EPR: Germany 2020"},
    "Spain":          {"milestone_year": 2007, "milestone_name": "Royal Decree 661/2007 feed-in", "inflection_year": 2014, "public_source_anchor": "IEA EPR: Spain 2021"},
    "Portugal":       {"milestone_year": 2001, "milestone_name": "Decree-Law 339-C/2001 renewable feed-in", "inflection_year": 2010, "public_source_anchor": "IEA EPR: Portugal 2021"},
    "United_Kingdom": {"milestone_year": 2002, "milestone_name": "Renewables Obligation 2002", "inflection_year": 2014, "public_source_anchor": "IEA EPR: UK 2019"},
    "Italy":          {"milestone_year": 2005, "milestone_name": "Conto Energia 2005 PV feed-in", "inflection_year": 2012, "public_source_anchor": "IEA EPR: Italy 2023"},
    # Non-EU 6 (added in v2)
    "Japan":          {"milestone_year": 2012, "milestone_name": "Renewable Energy Special Measures Act (FIT) 2012", "inflection_year": 2017, "public_source_anchor": "IEA EPR: Japan 2021; METI statistics"},
    "China":          {"milestone_year": 2005, "milestone_name": "Renewable Energy Law 2005 + 2009 amendment", "inflection_year": 2013, "public_source_anchor": "IEA EPR: China 2017 + Clean Energy Investment 2023"},
    "United_States":  {"milestone_year": 2005, "milestone_name": "EPAct 2005 PTC extension + 2009 ARRA renewable provisions", "inflection_year": 2014, "public_source_anchor": "IEA EPR: USA 2019; EIA AEO 2020"},
    "Australia":      {"milestone_year": 2001, "milestone_name": "Renewable Energy (Electricity) Act 2000 MRET 2001", "inflection_year": 2011, "public_source_anchor": "IEA EPR: Australia 2018; CER statistics"},
    "Brazil":         {"milestone_year": 2002, "milestone_name": "PROINFA 2002 + Decree 5.025/2004", "inflection_year": 2013, "public_source_anchor": "IEA EPR: Brazil 2013; ANEEL statistics"},
    "India":          {"milestone_year": 2003, "milestone_name": "Electricity Act 2003 RE provisions + JNNSM 2010", "inflection_year": 2014, "public_source_anchor": "IEA EPR: India 2020; CEA statistics"},
}


def compute_lead_time(country_record: dict) -> int:
    return int(country_record["inflection_year"] - country_record["milestone_year"])


def run_leader_analysis() -> list[dict]:
    return [
        {
            "country": name,
            "milestone_year": rec["milestone_year"],
            "milestone_name": rec["milestone_name"],
            "inflection_year": rec["inflection_year"],
            "lead_time_years": compute_lead_time(rec),
            "public_source_anchor": rec["public_source_anchor"],
            "region_bucket": "EU" if name in ["Denmark","Germany","Spain","Portugal","United_Kingdom","Italy"] else "non_EU",
        }
        for name, rec in LEADER_FIXTURE_V2.items()
    ]


def compute_verdict(analyses: list[dict]) -> dict:
    lead_times = [a["lead_time_years"] for a in analyses]
    mean_lead = sum(lead_times) / len(lead_times)
    min_lead = min(lead_times)
    max_lead = max(lead_times)
    spread = max_lead - min_lead
    v1_mean = PREDICTION["v1_prior_mean"]
    v1_spread = PREDICTION["v1_prior_spread"]
    drift = abs(mean_lead - v1_mean)
    spread_bound = v1_spread * PREDICTION["predicted_spread_bound_x_v1"]
    drift_bound = PREDICTION["predicted_drift_bound"]

    eu_means = [a["lead_time_years"] for a in analyses if a["region_bucket"] == "EU"]
    non_eu_means = [a["lead_time_years"] for a in analyses if a["region_bucket"] == "non_EU"]
    eu_mean = sum(eu_means) / len(eu_means)
    non_eu_mean = sum(non_eu_means) / len(non_eu_means)

    if drift <= drift_bound and spread <= spread_bound:
        verdict = "pass"
        outcome = "prior_generalizes_globally"
        rationale = (
            f"v2 mean lead time {mean_lead:.2f}y (drift {drift:.2f}y ≤ "
            f"{drift_bound}y) and spread {spread}y (≤ {spread_bound}y). "
            f"Prior generalizes globally at the methodology's current "
            f"characterization. EU sub-cohort mean {eu_mean:.2f}y; non-EU "
            f"sub-cohort mean {non_eu_mean:.2f}y. Per §1 honesty bounds the "
            f"v1 bound on per-region voice addition remains in force; this "
            f"pass means the COHORT-AGGREGATE prior is stable, NOT that any "
            f"single country's trajectory can be predicted without its own voice."
        )
    elif drift > drift_bound and spread > spread_bound:
        verdict = "fail"
        outcome = "prior_drifts_AND_spreads_beyond_bounds"
        rationale = (
            f"v2 mean {mean_lead:.2f}y, drift {drift:.2f}y exceeds bound "
            f"{drift_bound}y AND spread {spread}y exceeds bound {spread_bound}y. "
            f"EU-only v1 fixture was over-fit; methodology requires per-region "
            f"voice addition per §1 bound #5."
        )
    elif drift > drift_bound:
        verdict = "fail"
        outcome = "prior_drifts_central_tendency_unstable"
        rationale = (
            f"v2 mean {mean_lead:.2f}y, drift {drift:.2f}y exceeds bound "
            f"{drift_bound}y. Spread {spread}y within bound. Central tendency "
            f"shifts with expansion — v1 EU prior was systematically biased."
        )
    else:
        verdict = "fail"
        outcome = "prior_spreads_cohort_heterogeneous"
        rationale = (
            f"v2 mean {mean_lead:.2f}y within drift bound, but spread {spread}y "
            f"exceeds bound {spread_bound}y. The cohort is too heterogeneous "
            f"for a single prior; per-region voices needed."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "v2_mean_lead_time": mean_lead,
        "v2_min_lead_time": min_lead,
        "v2_max_lead_time": max_lead,
        "v2_spread": spread,
        "drift_from_v1": drift,
        "drift_bound": drift_bound,
        "spread_bound": spread_bound,
        "eu_sub_cohort_mean": eu_mean,
        "non_eu_sub_cohort_mean": non_eu_mean,
        "per_country_analyses": analyses,
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
    analyses = run_leader_analysis()
    for a in analyses:
        print(
            f"  {a['country']:>15s}  [{a['region_bucket']:>6s}]  "
            f"milestone={a['milestone_year']}  inflection={a['inflection_year']}  "
            f"lead_time={a['lead_time_years']}y"
        )
    print("-" * 72)
    verdict = compute_verdict(analyses)
    print(f"  v2 mean:              {verdict['v2_mean_lead_time']:.2f}y")
    print(f"  v2 spread:            {verdict['v2_spread']}y")
    print(f"  drift from v1 (8.83): {verdict['drift_from_v1']:.2f}y (bound {verdict['drift_bound']}y)")
    print(f"  spread bound:         {verdict['spread_bound']}y")
    print(f"  EU sub-cohort mean:   {verdict['eu_sub_cohort_mean']:.2f}y")
    print(f"  non-EU sub-cohort:    {verdict['non_eu_sub_cohort_mean']:.2f}y")
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
