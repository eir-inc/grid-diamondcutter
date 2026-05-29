"""
voice_bound_defender_3_coupling_coefficient_v1.py — mechanical defender for
PREREGISTRATION.md §1 honesty bound #3.

§1 bound #3 (verbatim):
    "The project will NOT claim that the cross-band coupling coefficient measured
    in the demonstration meta-simulation (currently +0.832 control↔dynamics
    correlation) is a measurement of physical grid coupling, or that its
    magnitude generalizes to any real grid."

This bound is a two-pronged commitment:
  (a) The +0.832 figure must reproduce from the committed code — if the meta-sim
      drifts and 0.832 no longer reproduces, the documentation is silently
      stale and reviewers can no longer audit the underlying claim.
  (b) The figure must remain documented as a between-simulated-voices
      measurement — if the bound's guard-language (e.g., "simulated", "not
      generalize to real grid", "demonstration") disappears from the package's
      own documentation, the bound is no longer mechanically defended at the
      surface of the artifact a reader will see.

This voice exercises both (a) and (b) at every commit. PASS iff both hold;
FAIL (alarm) iff either one drifts. This is an inverted-kill bound-defender per
the lineage in PR #16 (bound #5), PR #17 (§0.3), PR #18 (bound #1), and PR #21
(bound #2). Bound #3 was previously uncovered.

Authored under PREREGISTRATION.md §3.1.
"""
from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
META_SIM_DOC = REPO_ROOT / "meta_sim" / "meta.py"


VOICE_NAME = "bound_defender_3_coupling_coefficient_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "registry_meta",
    "named_residual": (
        "PREREGISTRATION §1 bound #3 defense — the +0.832 control↔dynamics coupling "
        "coefficient must (a) reproduce from the committed code with documented seed, "
        "AND (b) remain documented as a between-simulated-voices measurement (not a "
        "real-grid claim). If either drifts silently, the bound is no longer mechanically "
        "defended at every commit."
    ),
    "expected_control_dynamics_coupling": 0.832,
    "reproducibility_tolerance": 0.05,
    "documentation_guard_phrases_any_of": [
        "simulated",
        "demonstration",
        "not a measurement of physical grid coupling",
        "does not measure coupling in any real grid",
        "between two simulated voices",
        "generalizes to no real grid",
        "DOES NOT generalize",
    ],
    "documentation_anchor_phrase": "0.832",
    "alarm_semantics": (
        "PASS = §1 bound #3 mechanically defended (figure reproduces AND guard-language "
        "still names the figure as between simulated voices); FAIL = alarm (figure drifted "
        "OR guard-language vanished from documentation)."
    ),
}

KILL_CONDITION = {
    "metric": "reproducibility_and_doc_guard_both_hold",
    "rule": (
        "FAIL if |measured_value − 0.832| > 0.05 (substrate-drift alarm) "
        "OR if zero documentation-guard phrases appear within 200 chars of the "
        "0.832 mention in meta_sim/meta.py (documentation-drift alarm). "
        "PASS iff BOTH the measurement reproduces AND ≥1 guard phrase is present "
        "near the anchor."
    ),
    "rationale": (
        "§1 bound #3 is a two-pronged commitment: the figure must be reproducible, AND "
        "the figure must continue to be documented honestly. A failure in either prong "
        "means the bound is no longer mechanically defended at the surface of the artifact. "
        "Reviewers checking the registry at any commit get an immediate alarm if a future "
        "edit drifts the meta-sim measurement or strips the guard-language. Defends the "
        "registry against silent erosion of an existing honesty bound."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/voice_bound_defender_3_coupling_coefficient_v1.py",
    "source_file": "examples/voices/voice_bound_defender_3_coupling_coefficient_v1.py",
    "input_parameters": {
        "random_seed": 42,
        "n_steps": 30,
        "documentation_anchor_path": "meta_sim/meta.py",
        "guard_phrase_search_radius_chars": 200,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
        "module_dependency": "meta_sim (vendored in this repository)",
    },
}


def _check_reproducibility() -> dict:
    """Re-run the meta-sim coupling measurement; return measured value + drift."""
    import sys
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from meta_sim import make_default_meta_sim, measure_cross_band_coupling

    meta = make_default_meta_sim()
    coupling = measure_cross_band_coupling(
        meta,
        n_steps=RUN_PROTOCOL["input_parameters"]["n_steps"],
        seed=RUN_PROTOCOL["input_parameters"]["random_seed"],
    )
    measured = float(coupling.get("control↔dynamics", float("nan")))
    expected = PREDICTION["expected_control_dynamics_coupling"]
    drift = abs(measured - expected)
    return {
        "measured_value": measured,
        "expected_value": expected,
        "drift": drift,
        "tolerance": PREDICTION["reproducibility_tolerance"],
        "within_tolerance": drift <= PREDICTION["reproducibility_tolerance"],
    }


def _check_documentation_guard() -> dict:
    """Scan meta_sim/meta.py for at least one guard-phrase near the 0.832 anchor."""
    anchor = PREDICTION["documentation_anchor_phrase"]
    radius = RUN_PROTOCOL["input_parameters"]["guard_phrase_search_radius_chars"]
    phrases = PREDICTION["documentation_guard_phrases_any_of"]

    if not META_SIM_DOC.exists():
        return {
            "doc_path": str(META_SIM_DOC),
            "doc_exists": False,
            "anchor_present": False,
            "guard_phrases_found_near_anchor": [],
            "guard_present": False,
        }
    text = META_SIM_DOC.read_text()
    # find all anchor positions
    anchor_positions = [m.start() for m in re.finditer(re.escape(anchor), text)]
    if not anchor_positions:
        return {
            "doc_path": str(META_SIM_DOC),
            "doc_exists": True,
            "anchor_present": False,
            "guard_phrases_found_near_anchor": [],
            "guard_present": False,
        }
    found_phrases = set()
    for pos in anchor_positions:
        window_start = max(0, pos - radius)
        window_end = min(len(text), pos + len(anchor) + radius)
        window = text[window_start:window_end].lower()
        for phrase in phrases:
            if phrase.lower() in window:
                found_phrases.add(phrase)
    return {
        "doc_path": str(META_SIM_DOC),
        "doc_exists": True,
        "anchor_present": True,
        "anchor_occurrence_count": len(anchor_positions),
        "guard_phrases_found_near_anchor": sorted(found_phrases),
        "guard_present": len(found_phrases) >= 1,
    }


def run_voice_measurement() -> dict:
    return {
        "reproducibility": _check_reproducibility(),
        "documentation_guard": _check_documentation_guard(),
    }


def compute_verdict(observed: dict) -> dict:
    repro_ok = observed["reproducibility"]["within_tolerance"]
    doc_ok = observed["documentation_guard"]["guard_present"]
    if repro_ok and doc_ok:
        verdict = "pass"
        rationale = (
            f"§1 bound #3 defended at this commit: "
            f"measured {observed['reproducibility']['measured_value']:.4f} "
            f"(within ±{PREDICTION['reproducibility_tolerance']} of 0.832); "
            f"guard phrases found near anchor: "
            f"{observed['documentation_guard']['guard_phrases_found_near_anchor']}."
        )
    else:
        failed = []
        if not repro_ok:
            failed.append(
                f"reproducibility-alarm: measured "
                f"{observed['reproducibility']['measured_value']:.4f}, "
                f"drift {observed['reproducibility']['drift']:.4f} > "
                f"tolerance {observed['reproducibility']['tolerance']}"
            )
        if not doc_ok:
            failed.append(
                f"documentation-alarm: zero guard phrases found near 0.832 anchor in "
                f"{observed['documentation_guard']['doc_path']} "
                f"(anchor present: {observed['documentation_guard']['anchor_present']})"
            )
        verdict = "fail"
        rationale = (
            f"§1 bound #3 alarm fired — reviewer attention required. "
            f"Failed: {'; '.join(failed)}. The bound is no longer mechanically "
            f"defended at this commit; either restore the documentation guard-language "
            f"or fix the meta-sim drift."
        )
    return {
        "verdict": verdict,
        "reproducibility": observed["reproducibility"],
        "documentation_guard": observed["documentation_guard"],
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def emit_sidecar(verdict: dict, output_path: Path) -> str:
    unit_pre_verdict = {
        "voice_name": VOICE_NAME,
        "prediction": PREDICTION,
        "kill_condition": KILL_CONDITION,
        "run_protocol": RUN_PROTOCOL,
    }
    canonical = json.dumps(unit_pre_verdict, sort_keys=True, separators=(",", ":"))
    sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    unit = {**unit_pre_verdict, "verdict": verdict, "sidecar_sha256_pre_verdict": sha}
    output_path.write_text(json.dumps(unit, indent=2))
    return sha


def main() -> dict:
    print(f"=== {VOICE_NAME} ===")
    print(f"defending: PREREGISTRATION §1 bound #3")
    print(f"  (a) +0.832 control↔dynamics coefficient reproduces from committed code")
    print(f"  (b) figure remains documented as between-simulated-voices, not real-grid")
    print()
    observed = run_voice_measurement()
    repro = observed["reproducibility"]
    doc = observed["documentation_guard"]
    print(
        f"  reproducibility: measured={repro['measured_value']:.4f}, "
        f"drift={repro['drift']:.4f}, within tolerance={repro['within_tolerance']}"
    )
    print(
        f"  documentation guard: anchor_present={doc['anchor_present']}, "
        f"guard_phrases_found={doc['guard_phrases_found_near_anchor']}, "
        f"guard_present={doc['guard_present']}"
    )
    print()
    verdict = compute_verdict(observed)
    print(f"verdict: {verdict['verdict']}")
    print(f"rationale: {verdict['rationale']}")

    sidecar_path = Path(__file__).parent / f"{VOICE_NAME}.sidecar.json"
    sha = emit_sidecar(verdict, sidecar_path)
    print(f"\nsidecar emitted: {sidecar_path.name}")
    print(f"sha256_pre_verdict: {sha}")
    return verdict


if __name__ == "__main__":
    main()
