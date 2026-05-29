"""
bound_defender_11_no_eirmath_in_phase_2_v1.py — §3.1 polyphony voice
(inverted kill) defending phase-2 honesty bound #11.

Phase-2 bound #11 (from `phase_2/PREREGISTRATION_PHASE_2.md` §1):

  "the project will NOT claim that the phase-2 recognition criterion
   equals or implies the eirmath $-calibration covered by
   `docs/eirmath_bridge.md` use case 1"

Mechanically enforced via source-inspection: NO file under `phase_2/`
may `import eirmath` (or any of its submodules) AND no string token
"eirmath" may appear in non-docstring source under `phase_2/examples/voices/`
unless it is bounded within a citation-anchor.

Inheritance: this voice inherits the bound-defender pattern from
phase-1's `bound_defender_2_adapter_stubs_source_inspection_v1`, applied
to a different boundary.

Evasion-class lineage: declares phase-A signature
`cross_lane_prior_generalization_evasion` because the bound-crossing
this defender catches would be EXACTLY the kind of cross-phase consumption
that the §3.5 cross-phase-consumption declaration is supposed to make
explicit (silently embedding eirmath in phase-2 would be a hidden
cross-phase dependency that the registry must catch).

WHAT THIS VOICE PREDICTS
========================

Zero phase-2 files contain `import eirmath` (any form) AND zero phase-2
voice source bodies contain an unguarded `eirmath` token outside
docstrings.

  Kind:                    polyphony_within_substrate (bound defender; inverted)
  Substrate:               phase_2/ source tree
  Named residual:          n_phase_2_files_with_eirmath_dependency_or_token
  Predicted upper bound:   0
  Bound under test:        phase-2 PREREGISTRATION §1 bound #11
  Evasion-class lineage:   cross_lane_prior_generalization_evasion (phase-A)

KILL CONDITION (INVERTED)
=========================

  - n_violations == 0 → pass (bound supported by direct source inspection)
  - n_violations > 0  → fail (bound counter-observation — phase-2 file
                              silently embeds eirmath dependency)
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ===========================================================================
# §3.1 — Standard five-field unit
# ===========================================================================

VOICE_NAME = "bound_defender_11_no_eirmath_in_phase_2_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "phase_2_source_tree",
    "named_residual": "n_phase_2_files_with_eirmath_dependency_or_token",
    "predicted_value_upper_bound": 0,
    "verdict_inversion": True,
    "evasion_class_lineage": "cross_lane_prior_generalization_evasion",
    "bound_under_test": (
        "phase-2 PREREGISTRATION_PHASE_2.md §1 bound #11 — phase-2 "
        "recognition criterion does not equal or imply the eirmath "
        "$-calibration covered by docs/eirmath_bridge.md use case 1"
    ),
}

KILL_CONDITION = {
    "metric": "n_phase_2_files_with_eirmath_import_or_unguarded_token",
    "rule": (
        "pass if 0 phase-2 .py files contain 'import eirmath' (any form) "
        "AND 0 phase-2 voice source bodies contain an unguarded 'eirmath' "
        "token outside docstrings (bound supported); fail if any "
        "violation (bound counter-observation requiring §1 flagging-record)"
    ),
    "rationale": (
        "The bound is mechanically testable by source-inspection alone. "
        "Cross-phase consumption declarations per §3.5 require explicit "
        "upstream sidecar references; silently embedding eirmath would "
        "bypass the §3.5 contract. The defender catches that bypass at "
        "phase-2-PR-merge time via CI integration on top of this voice."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python phase_2/examples/voices/bound_defender_11_no_eirmath_in_phase_2_v1.py",
    "source_file": "phase_2/examples/voices/bound_defender_11_no_eirmath_in_phase_2_v1.py",
    "input_parameters": {
        "scan_root": "phase_2",
        "scan_extensions": [".py"],
        "exclude_directories": ["__pycache__", ".pytest_cache"],
        "import_patterns": [
            r"^\s*import\s+eirmath\b",
            r"^\s*from\s+eirmath(\.|\s)",
        ],
        "token_pattern": r"\beirmath\b",
        "docstring_pattern": r'("""|\'\'\')',
        "self_voice_exclusion": "bound_defender_11_no_eirmath_in_phase_2_v1",
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


# ===========================================================================
# Source inspection
# ===========================================================================

def _is_self_voice_file(path: Path) -> bool:
    return path.stem == RUN_PROTOCOL["input_parameters"]["self_voice_exclusion"]


def _iter_phase_2_python_files() -> list[Path]:
    p = RUN_PROTOCOL["input_parameters"]
    root_candidates = [
        Path(p["scan_root"]),
        Path.cwd() / p["scan_root"],
        Path(__file__).resolve().parent.parent.parent.parent / p["scan_root"],
    ]
    root = next((r for r in root_candidates if r.exists()), None)
    if root is None:
        return []
    excluded = set(p["exclude_directories"])
    files: list[Path] = []
    for f in root.rglob("*.py"):
        if any(part in excluded for part in f.parts):
            continue
        files.append(f)
    return files


def _strip_docstrings_simple(src: str) -> str:
    pattern = re.compile(r'(?P<quote>"""|\'\'\')(?:.*?)(?P=quote)', re.DOTALL)
    return pattern.sub(" ", src)


def _scan_file(path: Path) -> dict:
    p = RUN_PROTOCOL["input_parameters"]
    try:
        src = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"path": str(path), "read_error": str(e), "violations": []}

    violations: list[dict] = []

    for line_no, line in enumerate(src.splitlines(), start=1):
        for pat in p["import_patterns"]:
            if re.search(pat, line):
                violations.append({
                    "kind": "import_statement",
                    "line": line_no,
                    "text": line.strip(),
                    "pattern": pat,
                })
                break

    if not _is_self_voice_file(path):
        body = _strip_docstrings_simple(src)
        for line_no, line in enumerate(body.splitlines(), start=1):
            if re.search(p["token_pattern"], line):
                already_import = any(
                    re.search(ip, line) for ip in p["import_patterns"]
                )
                if not already_import:
                    violations.append({
                        "kind": "unguarded_token_in_non_docstring_body",
                        "line": line_no,
                        "text": line.strip()[:200],
                    })

    return {
        "path": str(path),
        "read_error": None,
        "violations": violations,
        "n_violations": len(violations),
    }


def run_scan() -> dict:
    files = _iter_phase_2_python_files()
    per_file = [_scan_file(f) for f in files]
    total_violations = sum(r["n_violations"] for r in per_file)
    n_offending_files = sum(1 for r in per_file if r["n_violations"] > 0)
    return {
        "n_files_scanned": len(per_file),
        "per_file_results": per_file,
        "n_total_violations": total_violations,
        "n_offending_files": n_offending_files,
    }


def compute_verdict(scan: dict) -> dict:
    n_total = scan["n_total_violations"]
    bound = PREDICTION["predicted_value_upper_bound"]

    if n_total <= bound:
        verdict = "pass"
        outcome = "bound_supported_no_eirmath_dependency_or_token"
        rationale = (
            f"Inspected {scan['n_files_scanned']} phase-2 .py file(s). "
            f"Total eirmath-import-or-token violations: {n_total}. "
            f"Pre-committed upper bound: {bound}. Phase-2 bound #11 "
            f"supported by direct source inspection. Voice PASSes its "
            f"inverted kill condition."
        )
    else:
        verdict = "fail"
        outcome = "bound_counter_observation_eirmath_in_phase_2"
        offending = [r for r in scan["per_file_results"] if r["n_violations"] > 0]
        offending_summary = [
            {"path": r["path"], "n_violations": r["n_violations"]}
            for r in offending
        ]
        rationale = (
            f"Inspected {scan['n_files_scanned']} phase-2 .py file(s). "
            f"Found {n_total} eirmath-import-or-token violations across "
            f"{scan['n_offending_files']} file(s): {offending_summary}. "
            f"Crosses the pre-committed upper bound of {bound}. Per §1 "
            f"bound-crossing protocol, this run requires a flagging-record "
            f"entry. Either the eirmath reference should be removed OR the "
            f"voice should be reframed as a phase-1 voice (which can "
            f"reference eirmath via the §6 boundary documentation, not in "
            f"voice source)."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "n_files_scanned": scan["n_files_scanned"],
        "n_total_violations": n_total,
        "n_offending_files": scan["n_offending_files"],
        "predicted_upper_bound": bound,
        "per_file_results": scan["per_file_results"],
        "bound_under_test": PREDICTION["bound_under_test"],
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


# ===========================================================================
# Sidecar emission
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
    print(f"under test: phase-2 PREREGISTRATION_PHASE_2.md §1 bound #11 (no eirmath in phase_2)")
    print("=" * 72)
    scan = run_scan()
    print(f"  n files scanned:       {scan['n_files_scanned']}")
    print(f"  n total violations:    {scan['n_total_violations']}")
    print(f"  n offending files:     {scan['n_offending_files']}")
    if scan["n_offending_files"] > 0:
        for r in scan["per_file_results"]:
            if r["n_violations"] > 0:
                print(f"    [{r['n_violations']}] {r['path']}")
                for v in r["violations"]:
                    print(f"      L{v['line']:>4d} ({v['kind']}): {v.get('text', '')}")
    print("-" * 72)
    verdict = compute_verdict(scan)
    print(f"  pre-committed bound:   {verdict['predicted_upper_bound']}")
    print(f"  verdict:               {verdict['verdict'].upper()}")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
