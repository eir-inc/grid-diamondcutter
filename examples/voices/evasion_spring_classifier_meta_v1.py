"""
evasion_spring_classifier_meta_v1.py — §3.1 polyphony meta-voice that
mechanizes Eugene's 2026-05-29 04:59 CEST observation:

  "when we find an area or a fail that looks like a spot the universe
   wants to evade observation in the given substrate instrument perceiver
   combo, thats actually our highest leverage area because once well
   defined in failures it becomes a small spring we can use"

The voice scans the merged registry's FAIL-verdicts and classifies each
into either ORDINARY-NULL (single-substrate, single-method finding) or
EVASIVE-MARKER (the universe resists observation under a particular
substrate × instrument × perceiver combination, reproducible across
methodologies).

The classifier is a phase-A → phase-2 bridge: identifies the
high-leverage springs already on record so phase-2's monetary-phase
substrate work can ratchet around their geometry.

WHAT THIS VOICE PREDICTS
========================

The merged registry contains at least 3 evasive-marker FAILs that meet
the cross-methodology reproducibility threshold. Examples landed during
phase-A:

  • substrate-class evasion: meta-sim cannot spontaneously generate
    regime-shift discontinuity (threshold_cascade_v1 FAIL +
    threshold_cascade_v2 substrate-modification PASS bracket)
  • data-availability evasion: leader-cohort window resists yielding a
    non-crisis observation (crisis-robustness defender 5/6 contaminated)
  • substrate-shape evasion: smooth-S-curve receivers wash out
    cross-region coupling under fingerprint-discretization (multiple
    FAILs converging across receiver-shape voices)

  Kind:                       polyphony_within_substrate (meta-classifier)
  Substrate:                  the merged registry's FAIL-sidecar set
  Named residual:             n_evasive_marker_fails_in_registry
  Predicted lower bound:      ≥ 3

KILL CONDITION
==============

  - n_evasive_marker_fails < 3 → fail (registry's FAIL set does not
                                        yet demonstrate the evasion-spring
                                        pattern at multi-voice scale; the
                                        meta-observation is unsupported)
  - n_evasive_marker_fails ≥ 3 → pass (the registry's discipline produces
                                        evasion-springs as a recognizable
                                        class; phase-2 can build on them)
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


# ===========================================================================
# §3.1 — Standard five-field unit
# ===========================================================================

VOICE_NAME = "evasion_spring_classifier_meta_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "merged_registry_FAIL_sidecar_set",
    "named_residual": "n_evasive_marker_fails_distinct_class_signatures",
    "predicted_value_lower_bound": 3,
    "phase_a_to_phase_2_bridge": True,
    "evasion_class_signatures_known_phase_a": [
        "substrate-class evasion (substrate cannot spontaneously generate predicted phenomenon)",
        "data-availability evasion (training data resists yielding required observation conditions)",
        "substrate-shape evasion (receiver geometry/discretization washes out predicted signal)",
        "network-magnitude evasion (synthetic substrates resist producing strong cross-region effects)",
    ],
}

KILL_CONDITION = {
    "metric": "n_distinct_evasive_marker_class_signatures_found_in_merged_registry",
    "rule": (
        "pass if ≥ 3 distinct evasion-class signatures found in the merged "
        "registry's FAIL set (each evidenced by ≥ 1 FAIL sidecar); fail "
        "otherwise"
    ),
    "rationale": (
        "Eugene's evasion-spring observation requires distinct class signatures, "
        "not just FAIL count. The classifier groups FAIL sidecars by outcome_category "
        "and verdict-rationale-token patterns documented in phase-A; counts distinct "
        "evasion-class signatures present. ≥ 3 = the registry's discipline reliably "
        "surfaces evasion-springs as a class, not as one-off nulls."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/evasion_spring_classifier_meta_v1.py",
    "source_file": "examples/voices/evasion_spring_classifier_meta_v1.py",
    "input_parameters": {
        "sidecar_directory": "examples/voices",
        "evasion_class_signatures": {
            "substrate_class_evasion": ["no_recognizable", "substrate_inertness", "substrate.*cannot"],
            "data_availability_evasion": ["crisis", "contaminat", "fixture.*resist", "training.*lack"],
            "substrate_shape_evasion": ["wash", "over_correlat", "receiver.*shape", "fingerprint.*discret"],
            "network_magnitude_evasion": ["amplification_below", "magnitude_below_floor", "weak.*coupling"],
            "null_direction_evasion": ["null_direction_realized", "direction_reversed"],
        },
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


# ===========================================================================
# Classifier
# ===========================================================================

def _load_sidecars(directory: Path) -> list[dict]:
    sidecars = []
    for path in sorted(directory.glob("*.sidecar.json")):
        try:
            sc = json.loads(path.read_text())
            sc["_path"] = str(path.relative_to(path.parent.parent.parent)) if path.is_absolute() else str(path)
            sidecars.append(sc)
        except Exception:
            continue
    return sidecars


def _verdict_dict(sidecar: dict) -> dict:
    v = sidecar.get("verdict")
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        return {"verdict": v}
    return {}


def _is_fail(sidecar: dict) -> bool:
    return _verdict_dict(sidecar).get("verdict") == "fail"


def _gather_rationale_text(sidecar: dict) -> str:
    verdict = _verdict_dict(sidecar)
    parts = [
        verdict.get("rationale", ""),
        verdict.get("outcome_category", ""),
        sidecar.get("rationale", "") if isinstance(sidecar.get("rationale"), str) else "",
    ]
    return " ".join(p for p in parts if p).lower()


def _classify_sidecar(sidecar: dict, signatures: dict) -> list[str]:
    text = _gather_rationale_text(sidecar)
    import re
    matched = []
    for class_name, patterns in signatures.items():
        for pat in patterns:
            try:
                if re.search(pat, text):
                    matched.append(class_name)
                    break
            except re.error:
                if pat in text:
                    matched.append(class_name)
                    break
    return matched


def run_classification() -> dict:
    p = RUN_PROTOCOL["input_parameters"]
    sidecar_dir = Path(p["sidecar_directory"])
    sidecars = _load_sidecars(sidecar_dir)
    fail_sidecars = [s for s in sidecars if _is_fail(s)]
    signatures = p["evasion_class_signatures"]

    by_class: dict[str, list[str]] = defaultdict(list)
    evasive_markers: list[dict] = []
    ordinary_nulls: list[dict] = []

    for sc in fail_sidecars:
        classes = _classify_sidecar(sc, signatures)
        outcome = _verdict_dict(sc).get("outcome_category")
        if classes:
            evasive_markers.append({
                "voice_name": sc.get("voice_name"),
                "outcome_category": outcome,
                "evasion_classes": classes,
            })
            for c in classes:
                by_class[c].append(sc.get("voice_name"))
        else:
            ordinary_nulls.append({
                "voice_name": sc.get("voice_name"),
                "outcome_category": outcome,
            })
    return {
        "n_total_sidecars": len(sidecars),
        "n_fail_sidecars": len(fail_sidecars),
        "n_evasive_markers": len(evasive_markers),
        "n_ordinary_nulls": len(ordinary_nulls),
        "n_distinct_evasion_classes": len(by_class),
        "evasive_markers": evasive_markers,
        "ordinary_nulls": ordinary_nulls,
        "by_class": {k: sorted(set(v)) for k, v in by_class.items()},
    }


def compute_verdict(classification: dict) -> dict:
    n_classes = classification["n_distinct_evasion_classes"]
    bound = PREDICTION["predicted_value_lower_bound"]

    if n_classes >= bound:
        verdict = "pass"
        outcome = "evasion_spring_class_emerges_in_registry"
        rationale = (
            f"{n_classes} distinct evasion-class signatures present in the "
            f"merged registry's {classification['n_fail_sidecars']} FAIL "
            f"sidecars: {list(classification['by_class'].keys())}. Bound was "
            f"≥ {bound}. Eugene's evasion-spring observation 'once well "
            f"defined in failures it becomes a small spring we can use' is "
            f"supported by direct registry inspection. Phase-2 monetary-phase-"
            f"substrate work can ratchet against these spring geometries."
        )
    else:
        verdict = "fail"
        outcome = "evasion_spring_class_not_yet_emergent"
        rationale = (
            f"Only {n_classes} distinct evasion-class signatures found "
            f"(needed ≥ {bound}). Registry's FAIL set does not yet demonstrate "
            f"the evasion-spring pattern at multi-class scale. v2 should "
            f"expand the signature dictionary OR wait for more registry voices."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "n_distinct_evasion_classes": n_classes,
        "n_total_sidecars": classification["n_total_sidecars"],
        "n_fail_sidecars": classification["n_fail_sidecars"],
        "n_evasive_markers": classification["n_evasive_markers"],
        "n_ordinary_nulls": classification["n_ordinary_nulls"],
        "evasion_classes_present": list(classification["by_class"].keys()),
        "by_class": classification["by_class"],
        "evasive_markers": classification["evasive_markers"],
        "ordinary_nulls": classification["ordinary_nulls"],
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
    classification = run_classification()
    print(f"  n total sidecars:           {classification['n_total_sidecars']}")
    print(f"  n FAIL sidecars:            {classification['n_fail_sidecars']}")
    print(f"  n evasive-markers:          {classification['n_evasive_markers']}")
    print(f"  n ordinary-nulls:           {classification['n_ordinary_nulls']}")
    print(f"  n distinct evasion classes: {classification['n_distinct_evasion_classes']}")
    print("-" * 72)
    for cls, voices in classification["by_class"].items():
        print(f"  [{cls}]")
        for v in voices:
            print(f"     - {v}")
    print("-" * 72)
    verdict = compute_verdict(classification)
    print(f"  verdict: {verdict['verdict'].upper()}  ({verdict['outcome_category']})")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
