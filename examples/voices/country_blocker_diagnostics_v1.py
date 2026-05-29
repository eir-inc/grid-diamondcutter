"""
country_blocker_diagnostics_v1.py — §3.1 polyphony voice diagnosing which
single NOT-blocker check fails for each country that does NOT have a full
apoha-set membership per country_apoha_suitability_v1.

Companion / consumer of country_apoha_suitability_v1's sidecar. Where the
suitability voice identifies WHICH countries make the apoha-set, this voice
asks WHAT BLOCKS the others — and is the methodology layer's equivalent
of "what's the cheapest single intervention that would flip a country into
the apoha-set."

The actual $-cost of any intervention lives in eirmath per §6 and is NOT
claimed by this voice. This voice names the structural blocker per
country; eirmath would price the intervention.

WHAT THIS VOICE PREDICTS
========================

For each candidate country with apoha-set < 4/4, exactly one structural
blocker class accounts for the gap.

  Kind:                    polyphony_within_substrate (blocker-diagnostic)
  Substrate:               country_apoha_suitability_v1's sidecar
  Named residual:          n_countries_with_single_blocker_pattern
  Predicted lower bound:   ≥ 1 (at least one country in the candidate list
                                  is blocked by exactly one criterion)

KILL CONDITION
==============

  - n_single_blocker < 1 → fail (every non-apoha country has multiple
                                  blockers; the "single-intervention flips
                                  country" pattern is not observed)
  - n_single_blocker ≥ 1 → pass (at least one country is one-blocker away
                                  from apoha-set membership; the methodology
                                  surfaces single-intervention candidates
                                  for eirmath $-calibration)
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

VOICE_NAME = "country_blocker_diagnostics_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "country_apoha_suitability_v1_sidecar_ranked_candidates",
    "named_residual": "n_countries_with_single_blocker_pattern",
    "predicted_value_lower_bound": 1,
}

KILL_CONDITION = {
    "metric": "n_countries_with_single_apoha_blocker",
    "rule": (
        "pass if at least 1 country with apoha-set < 4/4 has exactly 1 failing "
        "NOT-blocker check (single-intervention candidate for eirmath); fail "
        "if no country has the single-blocker pattern (every non-apoha country "
        "has multiple blockers)"
    ),
    "rationale": (
        "The single-blocker pattern is the methodology's diagnostic for "
        "'cheapest intervention to flip country into apoha-set membership'. "
        "Eirmath would price the named intervention per country. This voice "
        "does not price; it identifies. The mechanical check is computable "
        "from country_apoha_suitability_v1's sidecar alone — no real-grid "
        "measurement, no private data."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/country_blocker_diagnostics_v1.py",
    "source_file": "examples/voices/country_blocker_diagnostics_v1.py",
    "input_parameters": {
        "upstream_sidecar": "examples/voices/country_apoha_suitability_v1.sidecar.json",
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


# ===========================================================================
# Diagnostic
# ===========================================================================

def diagnose_country(candidate: dict) -> dict:
    not_blockers = candidate["not_blockers"]
    failing = [name for name, passed in not_blockers.items() if not passed]
    return {
        "country": candidate["country"],
        "n_failing": len(failing),
        "failing_apoha_checks": failing,
        "single_blocker": failing[0] if len(failing) == 1 else None,
    }


def run_diagnostic() -> list[dict]:
    sidecar_path = Path(RUN_PROTOCOL["input_parameters"]["upstream_sidecar"])
    sidecar = json.loads(sidecar_path.read_text())
    ranked = sidecar["verdict"]["ranked_candidates"]
    diagnostics = [diagnose_country(c) for c in ranked if c["n_not_blockers_satisfied"] < 4]
    return diagnostics


def compute_verdict(diagnostics: list[dict]) -> dict:
    single_blocker = [d for d in diagnostics if d["single_blocker"] is not None]
    multi_blocker = [d for d in diagnostics if d["n_failing"] > 1]
    n_single = len(single_blocker)
    bound = PREDICTION["predicted_value_lower_bound"]

    if n_single >= bound:
        verdict = "pass"
        outcome = "single_intervention_candidates_identified"
        rationale = (
            f"Apoha-blocker diagnostic identifies {n_single} country/ies with "
            f"exactly one failing NOT-blocker check: "
            f"{[d['country'] + '/' + d['single_blocker'] for d in single_blocker]}. "
            f"At the methodology layer, each is a single-intervention candidate "
            f"whose cost eirmath would price separately. Multi-blocker countries "
            f"({len(multi_blocker)}): {[d['country'] for d in multi_blocker]} — "
            f"these need composite interventions or are out-of-scope for the "
            f"single-flip heuristic. Per §1 honesty bounds this voice does NOT "
            f"price any intervention and does NOT claim the named intervention "
            f"would in fact flip the country; it claims the methodology "
            f"identifies single-blocker structural patterns mechanically."
        )
    else:
        verdict = "fail"
        outcome = "no_single_intervention_candidates"
        rationale = (
            f"No countries with single-blocker pattern. All {len(diagnostics)} "
            f"non-apoha candidates have multi-blocker gaps. v2 would expand "
            f"the candidate list OR refine the apoha-criteria thresholds."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "n_countries_with_single_blocker": n_single,
        "n_countries_with_multi_blocker": len(multi_blocker),
        "single_blocker_candidates": single_blocker,
        "multi_blocker_candidates": multi_blocker,
        "predicted_lower_bound": bound,
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
    print(f"voice unit: {VOICE_NAME}  (kind: polyphony, blocker diagnostic)")
    print(f"consumes:   {RUN_PROTOCOL['input_parameters']['upstream_sidecar']}")
    print("=" * 72)
    diagnostics = run_diagnostic()
    for d in diagnostics:
        marker = "[SINGLE]" if d["single_blocker"] else "[MULTI ]"
        print(f"  {marker} {d['country']:>20s}  n_failing={d['n_failing']}  blockers={d['failing_apoha_checks']}")
    print("-" * 72)
    verdict = compute_verdict(diagnostics)
    print(f"  n single-blocker candidates: {verdict['n_countries_with_single_blocker']}")
    print(f"  n multi-blocker candidates:  {verdict['n_countries_with_multi_blocker']}")
    print(f"  pre-committed bound (>=):    {verdict['predicted_lower_bound']}")
    print(f"  verdict:                     {verdict['verdict'].upper()}")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
