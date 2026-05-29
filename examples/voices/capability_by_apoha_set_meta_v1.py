"""
capability_by_apoha_set_meta_v1.py — §3.1 polyphony meta-voice that
mechanizes Eugene's 2026-05-29 03:00 CEST escalation: "we could actually
rely HEAVILY on reverse kills to define capabilities."

Takes a capability claim + a list of inverted-kill bound-defender sidecars
(NOT-clauses) + a list of positive-direction voices that recover the
residual (POSITIVE-clauses). Returns the apoha-defined capability shape:
the capability is recognized iff all NOT-clauses PASS (each bound holds)
AND at least one POSITIVE-clause PASSes (residual exists).

WHAT THIS VOICE PREDICTS
========================

The §0 central-question capability "methodology recognizes a structurally-
recoverable cascade phenomenon under bounded conditions" can be
mechanically asserted via the apoha-set:

  NOT-clauses (each PASS supports the capability):
    threshold_cascade_v1                 → PASS = methodology cannot
                                          recognize §0 in smooth substrate
                                          (substrate-inertness must be ruled in)
    region_transfer_failure_v1           → PASS = methodology does not
                                          transfer cross-region without
                                          per-region voice (bound #5)
    bound_defender_1_allocator_v1        → PASS = methodology's flow
                                          allocator does not enforce
                                          power-flow conservation (bound #1)
    bound_defender_2_adapter_stubs_source_inspection_v1 → PASS = adapter
                                          stubs do not silently delegate
                                          (bound #2 source inspection)

  POSITIVE-clauses (at least one PASS required):
    threshold_cascade_v2                 → PASS = methodology recovers §0
                                          when substrate admits regime-
                                          shift discontinuity

Apoha-defined capability: "methodology recognizes §0 cascade signature
iff: substrate admits discontinuity AND methodology does NOT pretend to
be a power-flow solver AND does NOT silently delegate AND does NOT
transfer cross-region without per-region voice AND CAN be measured in
smooth substrate to confirm absence of false recognition."

KILL CONDITION
==============

Capability is recognized iff ALL NOT-clauses PASS AND at least 1
POSITIVE-clause PASSes:

  - all NOTs PASS + any POSITIVE PASS → pass (capability recognized
                                              by apoha-set)
  - any NOT FAIL → fail (capability claim falsified by bound counter-
                          observation)
  - no POSITIVE PASS → fail (no residual to define the capability around)
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

VOICE_NAME = "capability_by_apoha_set_meta_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "registry_sidecar_set_consumed_apoha_set_definition",
    "named_residual": "apoha_set_capability_recognized",
    "predicted_value": "all_not_clauses_pass_and_at_least_one_positive_pass",
    "capability_claim": (
        "methodology recognizes a structurally-recoverable cascade phenomenon "
        "under bounded conditions, defined by negation across registry voices"
    ),
}

KILL_CONDITION = {
    "metric": "apoha_set_recognition_predicate",
    "rule": (
        "pass if all NOT-clause sidecars have verdict=='pass' AND at least "
        "one POSITIVE-clause sidecar has verdict=='pass'; fail if any "
        "NOT-clause fails (bound counter-observation) OR no positive "
        "passes (no residual)"
    ),
    "rationale": (
        "Mechanizes Eugene's 2026-05-29 directive: capabilities defined "
        "by negation. Each NOT-clause is a registered inverted-kill voice; "
        "each POSITIVE-clause is a registered standard voice. The meta-"
        "voice computes the apoha-set predicate from sidecar verdicts "
        "alone. No new substrate, no new measurements — just a mechanical "
        "predicate over the registry's existing audit-trailed verdicts."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/capability_by_apoha_set_meta_v1.py",
    "source_file": "examples/voices/capability_by_apoha_set_meta_v1.py",
    "input_parameters": {
        "not_clause_sidecars": [
            "examples/voices/threshold_cascade_v1.sidecar.json",
            "examples/voices/region_transfer_failure_v1.sidecar.json",
            "examples/voices/bound_defender_1_allocator_v1.sidecar.json",
            "examples/voices/bound_defender_2_adapter_stubs_source_inspection_v1.sidecar.json",
        ],
        "positive_clause_sidecars": [
            "examples/voices/threshold_cascade_v2.sidecar.json",
        ],
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


def load_verdict(path_str: str) -> tuple[str, str | None]:
    path = Path(path_str)
    if not path.exists():
        return path.stem.replace(".sidecar", ""), None
    sidecar = json.loads(path.read_text())
    return sidecar.get("voice_name", path.stem), sidecar.get("verdict", {}).get("verdict")


def evaluate_apoha_set() -> dict:
    p = RUN_PROTOCOL["input_parameters"]
    not_results = [load_verdict(s) for s in p["not_clause_sidecars"]]
    positive_results = [load_verdict(s) for s in p["positive_clause_sidecars"]]

    not_clauses = [
        {"voice_name": name, "verdict": v, "available": v is not None}
        for name, v in not_results
    ]
    positive_clauses = [
        {"voice_name": name, "verdict": v, "available": v is not None}
        for name, v in positive_results
    ]
    return {
        "not_clauses": not_clauses,
        "positive_clauses": positive_clauses,
    }


def compute_verdict(apoha_set: dict) -> dict:
    nots = apoha_set["not_clauses"]
    poss = apoha_set["positive_clauses"]

    all_nots_pass = all(c["verdict"] == "pass" for c in nots if c["available"])
    n_nots_available = sum(1 for c in nots if c["available"])
    n_nots_pass = sum(1 for c in nots if c["verdict"] == "pass")
    nots_complete = (n_nots_available == len(nots))

    any_pos_pass = any(c["verdict"] == "pass" for c in poss if c["available"])
    n_pos_available = sum(1 for c in poss if c["available"])
    n_pos_pass = sum(1 for c in poss if c["verdict"] == "pass")

    if not nots_complete or n_pos_available < len(poss):
        verdict = "partial"
        outcome = "sidecars_not_all_present"
        rationale = (
            f"Apoha-set incomplete: {n_nots_available}/{len(nots)} NOT-clause "
            f"sidecars and {n_pos_available}/{len(poss)} POSITIVE-clause "
            f"sidecars available. Voice cannot fully evaluate the capability "
            f"predicate. Will re-evaluate once all referenced sidecars merge "
            f"to main."
        )
    elif all_nots_pass and any_pos_pass:
        verdict = "pass"
        outcome = "capability_recognized_by_apoha_set"
        rationale = (
            f"All {n_nots_pass}/{len(nots)} NOT-clauses PASS (each bound "
            f"defended by registry measurement); {n_pos_pass}/{len(poss)} "
            f"POSITIVE-clauses PASS (residual recovered). Capability "
            f"'{PREDICTION['capability_claim']}' is recognized by the apoha-"
            f"set. Each NOT-clause is an audit-trailed registry voice; each "
            f"POSITIVE-clause likewise. The capability is mechanically "
            f"defined and reviewers verify by running the constituent voices, "
            f"not by trusting the meta-voice's predicate."
        )
    elif not all_nots_pass:
        verdict = "fail"
        outcome = "bound_counter_observation_in_apoha_set"
        failing_nots = [c['voice_name'] for c in nots if c['verdict'] != 'pass']
        rationale = (
            f"NOT-clauses with verdict != pass: {failing_nots}. At least one "
            f"bound counter-observation is on record. Capability claim "
            f"requires a §1 flagging-record entry per bound-crossing protocol "
            f"AND a v2 of the falsified bound."
        )
    else:
        verdict = "fail"
        outcome = "no_positive_residual_in_apoha_set"
        rationale = (
            f"All NOT-clauses PASS (bounds hold) but no POSITIVE-clause PASSes. "
            f"Apoha-set has no residual to define a capability around. The "
            f"capability claim is unsupported even though all the bounds "
            f"are defended."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "n_not_clauses": len(nots),
        "n_not_clauses_available": n_nots_available,
        "n_not_clauses_pass": n_nots_pass,
        "n_positive_clauses": len(poss),
        "n_positive_clauses_available": n_pos_available,
        "n_positive_clauses_pass": n_pos_pass,
        "not_clause_verdicts": nots,
        "positive_clause_verdicts": poss,
        "capability_claim": PREDICTION["capability_claim"],
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
    apoha_set = evaluate_apoha_set()
    print("NOT-clauses:")
    for c in apoha_set["not_clauses"]:
        mark = "✓" if c["verdict"] == "pass" else ("·" if not c["available"] else "✗")
        print(f"  [{mark}] {c['voice_name']:>55s}  verdict={c['verdict']}")
    print("POSITIVE-clauses:")
    for c in apoha_set["positive_clauses"]:
        mark = "✓" if c["verdict"] == "pass" else ("·" if not c["available"] else "✗")
        print(f"  [{mark}] {c['voice_name']:>55s}  verdict={c['verdict']}")
    print("-" * 72)
    verdict = compute_verdict(apoha_set)
    print(f"  capability:                  {verdict['capability_claim']}")
    print(f"  NOT-clauses passed:          {verdict['n_not_clauses_pass']}/{verdict['n_not_clauses']}")
    print(f"  POSITIVE-clauses passed:     {verdict['n_positive_clauses_pass']}/{verdict['n_positive_clauses']}")
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
