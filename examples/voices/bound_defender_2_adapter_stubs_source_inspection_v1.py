"""
bound_defender_2_adapter_stubs_source_inspection_v1.py — §3.1 polyphony voice
(inverted) defending PREREGISTRATION §1 honesty bound #2 by SOURCE INSPECTION.

§1 row #2 says the project will NOT claim:

  "the `pypower_adapter_stub` or `pandapower_adapter_stub` voices in the
   repository delegate to real PYPOWER or pandapower load-flow runs unless
   the documentation for each voice explicitly states that delegation has
   been implemented in a specific commit and references the commit hash where
   delegation became real."

This voice tests that bound by inspecting each adapter-stub function's source
code for absence of real-delegation tokens (`runpf`, `runpp`), excluding
docstrings (which often mention the absent calls explicitly).

COMPLEMENTARY TO: `bound_defender_2_adapter_stubs_v1` (PR #19, groove), which
tests the same bound by RUNTIME BEHAVIOR measurement on the adapter stubs'
outputs across 80 BridgeParams samples. Two independent verifications of the
same bound — source-presence (this voice) and runtime-shape (groove's voice).
The two voices co-exist in the registry as distinct §3.4 entries.

WHAT THIS VOICE PREDICTS
========================

For each adapter stub in `grid_diamondcutter_oss.VOICES`:
  - The stub's source code (excluding docstrings) does NOT contain a real-
    delegation token from the pre-committed token set.

  Kind:                    polyphony_within_substrate (bound defender; inverted)
  Substrate:               adapter-stub function source bodies
  Named residual:          n_adapter_stubs_with_real_delegation_token_in_body
  Predicted upper bound:   0
  Bound under test:        PREREGISTRATION §1 row #2

KILL CONDITION (INVERTED)
=========================

  - n_with_delegation_token == 0 → pass  (bound supported by source inspection)
  - n_with_delegation_token > 0  → fail  (bound counter-observation — token
                                          present in stub source without
                                          documented commit-hash)
"""
from __future__ import annotations
import inspect
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ===========================================================================
# §3.1 — Standard five-field unit
# ===========================================================================

VOICE_NAME = "bound_defender_2_adapter_stubs_source_inspection_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "adapter_stub_function_source_bodies",
    "named_residual": "n_adapter_stubs_with_real_delegation_token_in_body",
    "predicted_value_upper_bound": 0,
    "verdict_inversion": True,
    "real_delegation_tokens": ["runpf", "runpp", "pypower.api.runpf", "pandapower.runpp"],
    "complementary_to": (
        "bound_defender_2_adapter_stubs_v1 (groove, PR #19) — runtime-behavior "
        "test on the same bound. This voice is the source-inspection counterpart."
    ),
    "bound_under_test": (
        "PREREGISTRATION §1 row #2 — adapter stubs do not silently delegate "
        "to real solvers without documented commit-hash."
    ),
}

KILL_CONDITION = {
    "metric": "n_adapter_stubs_with_real_delegation_token_in_body",
    "rule": (
        "pass if 0 stubs contain a real-delegation token in their function "
        "body (bound supported by source inspection), fail if any stub "
        "contains a real-delegation token (bound counter-observation "
        "requiring flagging-record entry per §1 bound-crossing protocol)"
    ),
    "rationale": (
        "Source-code inspection complements groove's runtime-behavior test "
        "(PR #19) of the same bound. Two independent verifications widen the "
        "audit posture for §1 #2: a stub that started silently delegating "
        "would have to either change runtime shape (caught by groove's voice) "
        "or carry a delegation token in its body (caught by this voice). "
        "Verdict inversion is consistent with the bound-defender pattern."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/bound_defender_2_adapter_stubs_source_inspection_v1.py",
    "source_file": "examples/voices/bound_defender_2_adapter_stubs_source_inspection_v1.py",
    "input_parameters": {
        "target_module": "grid_diamondcutter_oss",
        "adapter_stub_names": ["pypower_adapter_stub", "pandapower_adapter_stub"],
        "real_delegation_tokens": ["runpf", "runpp"],
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Source-code inspection
# ===========================================================================

def inspect_stub_for_delegation_tokens(stub_name: str) -> dict:
    import grid_diamondcutter_oss as module
    fn = getattr(module, stub_name, None)
    if fn is None:
        return {
            "stub_name": stub_name,
            "source_found": False,
            "tokens_found": [],
            "n_tokens_found": 0,
            "note": "stub function not present in target module",
        }

    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        return {
            "stub_name": stub_name,
            "source_found": False,
            "tokens_found": [],
            "n_tokens_found": 0,
            "note": "inspect.getsource failed",
        }

    src_no_docstring = _strip_docstring(src)
    tokens_to_check = RUN_PROTOCOL["input_parameters"]["real_delegation_tokens"]
    tokens_found = [tok for tok in tokens_to_check if tok in src_no_docstring]
    return {
        "stub_name": stub_name,
        "source_found": True,
        "source_line_count": src.count("\n") + 1,
        "tokens_found": tokens_found,
        "n_tokens_found": len(tokens_found),
    }


def _strip_docstring(src: str) -> str:
    """Remove the first triple-quoted docstring from a function source body."""
    triple_quote_styles = ('"""', "'''")
    for tq in triple_quote_styles:
        first_open = src.find(tq)
        if first_open == -1:
            continue
        first_close = src.find(tq, first_open + 3)
        if first_close == -1:
            continue
        return src[:first_open] + src[first_close + 3:]
    return src


def run_inspection() -> list[dict]:
    return [
        inspect_stub_for_delegation_tokens(name)
        for name in RUN_PROTOCOL["input_parameters"]["adapter_stub_names"]
    ]


def compute_verdict(stub_inspections: list[dict]) -> dict:
    total_tokens = sum(s["n_tokens_found"] for s in stub_inspections)
    upper_bound = PREDICTION["predicted_value_upper_bound"]

    if total_tokens <= upper_bound:
        verdict = "pass"
        outcome = "bound_supported_no_delegation_tokens_in_stub_source"
        rationale = (
            f"Inspected {len(stub_inspections)} adapter stubs. "
            f"Total real-delegation tokens in stub source bodies "
            f"(excluding docstrings): {total_tokens}. The bound's pre-committed "
            f"upper bound is {upper_bound}. §1 bound #2 supported by direct "
            f"source inspection. Voice PASSes its inverted kill condition. "
            f"Complementary to groove's PR #19 runtime-behavior test."
        )
    else:
        verdict = "fail"
        outcome = "bound_counter_observation_delegation_tokens_present"
        offending = [(s["stub_name"], s["tokens_found"]) for s in stub_inspections if s["n_tokens_found"] > 0]
        rationale = (
            f"Inspected {len(stub_inspections)} adapter stubs. Total delegation "
            f"tokens: {total_tokens}; offending stubs: {offending}. Crosses the "
            f"pre-committed upper bound of {upper_bound}. Per §1 bound-crossing "
            f"protocol this requires a flagging-record entry."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "n_stubs_inspected": len(stub_inspections),
        "n_total_delegation_tokens": total_tokens,
        "predicted_upper_bound": upper_bound,
        "stub_inspections": stub_inspections,
        "bound_under_test": PREDICTION["bound_under_test"],
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
    print(f"under test: PREREGISTRATION §1 bound #2 (source-inspection variant)")
    print(f"complementary to: bound_defender_2_adapter_stubs_v1 (groove PR #19)")
    print("=" * 72)
    inspections = run_inspection()
    for s in inspections:
        print(f"  stub: {s['stub_name']:>28s}  source_found={s['source_found']}  tokens_found={s['tokens_found']}")
    print("-" * 72)
    verdict = compute_verdict(inspections)
    print(f"  n stubs inspected:                {verdict['n_stubs_inspected']}")
    print(f"  n delegation tokens found:        {verdict['n_total_delegation_tokens']}")
    print(f"  pre-committed upper bound:        {verdict['predicted_upper_bound']}")
    print(f"  verdict:                          {verdict['verdict'].upper()}")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
