"""
voice_low_failure_rate_alarm_v1.py — registry-defender voice.

Defends PREREGISTRATION.md §0.3's commitment: "if every voice the project adds
passes its kill condition, that is a signal of fishing — kill conditions were
not tight enough, or voices were selected after observing outcomes."

This voice reads the registry's current state via tools/registry_summary.py
and checks whether the failure rate is suspiciously low. The intent is to make
the §0.3 commitment mechanical and visible at any commit hash: if reviewers
suspect fishing, the registry's own measurement says so.

This is an inverted-kill voice (like region_transfer_failure_v1 PR #16):
PASS = the §0.3 bound is supported (failure rate is healthy).
FAIL = the bound is counter-observed (failure rate is suspiciously low, alarm).

Authored under PREREGISTRATION.md §3.1.
"""
from __future__ import annotations
import json
import hashlib
import importlib.util
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


VOICE_NAME = "low_failure_rate_alarm_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "registry_meta",
    "named_residual": (
        "low-failure-rate fishing signal per §0.3. Once the registry has ≥5 voices "
        "committed (sufficient sample for a base-rate read), the failure rate "
        "should remain above 20% to indicate kill conditions are tight enough "
        "and that voices are not being selected after observing outcomes."
    ),
    "minimum_voices_for_alarm_armed": 5,
    "predicted_minimum_failure_rate": 0.20,
    "alarm_semantics": "PASS = §0.3 bound supported (failure rate ≥ 20%); FAIL = alarm fired (failure rate < 20%, fishing signal)",
}

KILL_CONDITION = {
    "metric": "registry_failure_rate",
    "rule": (
        "with ≥5 voices committed: fail (alarm) if failure rate < 0.20. "
        "With <5 voices: skip with `partial` verdict (alarm not yet armed, sample too small). "
        "The kill condition's PASS direction defends the §0.3 commitment; FAIL "
        "is the alarm firing and surfaces a potential fishing signal for reviewer attention."
    ),
    "rationale": (
        "§0.3 names a low failure rate as a project-level failure mode (kill conditions "
        "too loose, or voices selected after observing). Making the §0.3 check mechanical "
        "and committed-as-a-voice means the alarm appears in the registry's own audit trail "
        "at every commit. Reviewers do not have to remember to check §0.3 manually; this "
        "voice's verdict on each run is the §0.3 status."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/voice_low_failure_rate_alarm_v1.py",
    "source_file": "examples/voices/voice_low_failure_rate_alarm_v1.py",
    "input_parameters": {
        "registry_summary_tool": "tools/registry_summary.py",
        "minimum_voices_for_alarm_armed": 5,
        "alarm_threshold_failure_rate": 0.20,
        "random_seed": "n/a (registry read is deterministic)",
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_registry_summary_tool():
    """Import tools/registry_summary.py as a module."""
    tool_path = REPO_ROOT / "tools" / "registry_summary.py"
    spec = importlib.util.spec_from_file_location("registry_summary", tool_path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(REPO_ROOT))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def read_registry_state() -> dict:
    """Read the current registry state EXCLUDING this voice itself.

    This voice must not include its own sidecar in the calculation, otherwise
    the alarm reads circularly. If this voice's sidecar exists when this voice
    runs, exclude it from the count.
    """
    tool = _load_registry_summary_tool()
    sidecars = tool.collect_sidecars()
    # exclude this voice's own sidecar if it has been emitted previously
    sidecars = [s for s in sidecars if s.get("voice_name") != VOICE_NAME]
    summary = tool.summarize(sidecars)
    return summary


def compute_verdict(summary: dict) -> dict:
    total = summary["total_voices_committed"]
    failure_rate = summary["base_rate_failure"]
    min_voices = RUN_PROTOCOL["input_parameters"]["minimum_voices_for_alarm_armed"]
    threshold = RUN_PROTOCOL["input_parameters"]["alarm_threshold_failure_rate"]

    if total < min_voices:
        verdict = "partial"
        rationale = (
            f"Alarm not yet armed: {total} voices committed (excluding this voice), "
            f"minimum sample size for alarm is {min_voices}. The registry has not yet "
            f"accumulated enough voices for a meaningful base-rate read. Voice's "
            f"verdict is `partial` to indicate the §0.3 check is deferred until the "
            f"registry reaches {min_voices} voices."
        )
    elif failure_rate >= threshold:
        verdict = "pass"
        rationale = (
            f"§0.3 bound supported: failure rate {failure_rate:.1%} (across {total} voices) "
            f"is at or above the {threshold:.0%} alarm threshold. Kill conditions appear "
            f"tight enough; no fishing signal at this commit."
        )
    else:
        verdict = "fail"
        rationale = (
            f"§0.3 ALARM FIRED: failure rate {failure_rate:.1%} (across {total} voices) "
            f"is below the {threshold:.0%} threshold. Per §0.3 this is a project-level "
            f"failure signal — kill conditions may be too loose OR voices may be being "
            f"selected after observing outcomes. Voice enters null-voice ledger per §3.4 "
            f"with the alarm signature on the record. Reviewers: see §0.3 in PREREGISTRATION.md."
        )

    return {
        "verdict": verdict,
        "registry_failure_rate_observed": failure_rate,
        "registry_pass_rate_observed": summary["base_rate_pass"],
        "total_voices_excluding_this_voice": total,
        "alarm_threshold_failure_rate": threshold,
        "minimum_voices_for_alarm_armed": min_voices,
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
    print(f"defends PREREGISTRATION §0.3 (low-failure-rate = fishing signal)")
    print()
    print("reading registry state (excluding this voice itself)...")
    summary = read_registry_state()
    verdict = compute_verdict(summary)
    print(f"  total voices (excl. this voice): {verdict['total_voices_excluding_this_voice']}")
    print(f"  failure rate observed:           {verdict['registry_failure_rate_observed']:.1%}")
    print(f"  alarm threshold:                 {verdict['alarm_threshold_failure_rate']:.0%}")
    print(f"  verdict:                         {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"\nsidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
