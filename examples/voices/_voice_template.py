"""
_voice_template.py — boilerplate for authoring a new voice that conforms to §3.1.

Copy this file to `examples/voices/your_voice_name.py`, fill in each field below,
implement the voice's substrate modification and verdict computation, then run:

  python -m pytest tests/test_voice_registry_contract.py -v

The test suite mechanically verifies that the file conforms to §3.1's five-field
shape and that the kill condition is testable from the run output alone. Reviewers
then adjudicate whether the prediction is interesting; they do not have to check
whether the file is well-formed (the test enforces that for them).

The leading underscore in this filename is the convention for files that should
NOT be discovered as voice modules. Remove the underscore when you rename your copy.

See:
  - PREREGISTRATION.md §3.1 — the five required fields
  - PREREGISTRATION.md §3.2 — the two axes (polyphony vs coupling) and which
    additional fields coupling voices must pre-register
  - examples/voices/example_polyphony_voice.py — worked polyphony example
  - examples/voices/example_coupling_voice.py — worked coupling example
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone


# ===========================================================================
# §3.1 — Field 1: voice name
# ===========================================================================
# A unique identifier for the voice. Fixed at the moment of the predict-step
# commit; not revised by subsequent commits. Use lowercase_with_underscores +
# a version suffix (v1, v2, ...).

VOICE_NAME = "your_voice_name_v1"  # REPLACE


# ===========================================================================
# §3.1 — Field 2: predicted residual coupling
# ===========================================================================
# State the specific coupling the voice is hypothesized to capture as a numerical
# or categorical bound.
#
# For a polyphony voice (within-substrate addition; §3.2 first axis):
#   - 'kind' must be 'polyphony_within_substrate'
#   - 'named_residual' names the pre-existing residual the voice claims to capture
#
# For a coupling voice (cross-substrate link; §3.2 second axis):
#   - 'kind' must be 'coupling_cross_substrate'
#   - 'named_residual' names the cross-substrate link being tested
#   - 'predicted_direction' states which substrate's output drives the other's input
#   - 'predicted_magnitude_range' states the expected magnitude range [low, high]
#   - 'null_direction' states the realization that would falsify the directional claim

PREDICTION = {
    "kind": "polyphony_within_substrate",  # or "coupling_cross_substrate"
    "substrate": "your_substrate_name",     # REPLACE
    "named_residual": "describe the specific residual this voice claims to capture",  # REPLACE
    "predicted_value_upper_bound": 0.0,    # REPLACE: numerical bound the voice predicts
    # --- coupling-only fields (DELETE for polyphony, KEEP + FILL for coupling) ---
    # "predicted_direction": "substrate_A_output → substrate_B_input (positive)",
    # "predicted_magnitude_range": [low, high],
    # "null_direction": "no correlation OR reversed direction",
}


# ===========================================================================
# §3.1 — Field 3: kill condition
# ===========================================================================
# The specific run outcome that would falsify the prediction. Must be testable
# from the voice's run output alone, without external reinterpretation.

KILL_CONDITION = {
    "metric": "name_of_the_measurement_this_kill_condition_checks",  # REPLACE
    "rule": "describe the falsification rule in plain English",       # REPLACE
    "rationale": (
        "Explain why this rule constitutes falsification of the prediction "
        "and how the rule is evaluable from the voice's run output alone."
    ),  # REPLACE
}


# ===========================================================================
# §3.1 — Field 4: run protocol
# ===========================================================================
# The literal invocation that produces the verdict. Must include the source-file
# path, entry point, all input parameters, the random seed if stochastic, and
# any environment specification required for independent reproduction.

RUN_PROTOCOL = {
    "entry_point": f"python examples/voices/{VOICE_NAME}.py",
    "source_file": f"examples/voices/{VOICE_NAME}.py",
    "input_parameters": {
        # REPLACE with the actual parameters your voice consumes
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],  # ADD any others your voice requires
    },
}


# ===========================================================================
# Voice implementation (the substrate modification or measurement this voice
# contributes). Replace this section with your voice's actual logic.
# ===========================================================================

def run_voice_measurement() -> float:
    """Compute the observed value that the verdict will check against the kill
    condition. Returns a single scalar (or a structure that compute_verdict can
    interpret) — keep it deterministic given the run protocol's seed.
    """
    # REPLACE: compute the voice's actual measurement here
    return 0.0


# ===========================================================================
# §3.1 — Field 5: verdict
# ===========================================================================
# Mechanically compute pass / fail / partial from the run output against the
# kill condition. No post-hoc interpretation. The verdict function should be
# pure given its input.

def compute_verdict(observed_value: float) -> dict:
    """Compute pass/fail mechanically from observed_value against KILL_CONDITION.
    REPLACE the rule below with the actual check from your KILL_CONDITION.
    """
    # Example shape — REPLACE with your actual rule:
    threshold = PREDICTION.get("predicted_value_upper_bound", 0.0)
    if observed_value <= threshold:
        verdict = "pass"
        rationale = (
            f"Observed {observed_value:.4f} ≤ threshold {threshold:.4f}; "
            f"prediction consistent with run output."
        )
    else:
        verdict = "fail"
        rationale = (
            f"Observed {observed_value:.4f} > threshold {threshold:.4f}; "
            f"voice enters null-voice ledger per §3.4."
        )

    return {
        "verdict": verdict,
        "observed_value": observed_value,
        "threshold": threshold,
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


# ===========================================================================
# Sidecar emission — boilerplate, do not modify
# ===========================================================================

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
    print("running...")
    observed = run_voice_measurement()
    verdict = compute_verdict(observed)
    print(f"  observed:  {observed}")
    print(f"  verdict:   {verdict['verdict'].upper()}")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
