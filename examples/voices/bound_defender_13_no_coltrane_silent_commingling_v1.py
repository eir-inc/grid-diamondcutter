"""
bound_defender_13_no_coltrane_silent_commingling_v1.py — §3.1 polyphony
voice (inverted kill) defending PREREGISTRATION §1 honesty bound #13.

§1 bound #13 (committed in docs/coltrane_substrate_acknowledgement.md):

  "the project will NOT claim grid-diamondcutter is INDEPENDENT of the
   coltrane-oss orchestration substrate it was authored on; the
   acknowledgement above stands; future commits that silently couple
   grid-diamondcutter voice source to coltrane-oss internals (without
   declaring the dependency in the voice's RUN_PROTOCOL) cross this
   bound."

Mechanical enforcement via source-scan: NO voice or library .py file
under examples/voices/, phase_2/examples/voices/, or meta_sim/ may
`import coltrane` (any form) AND no unguarded `coltrane` token may
appear in non-docstring source bodies unless the line is within the
guard-window of a §1 bound text, the §3.5 cross-phase-consumption
declaration, or this voice's own bound description.

Inheritance: source-scan inverted-kill pattern established by
`bound_defender_2_adapter_stubs_source_inspection_v1`,
`bound_defender_8_eirmath_not_required_v1`,
`bound_defender_11_no_eirmath_in_phase_2_v1` (phase-2).

WHAT THIS VOICE PREDICTS
========================

Zero voice + library source files contain `import coltrane` (any form)
AND zero source bodies contain an unguarded `coltrane` token outside
docstrings or the per-voice §3.5 declaration's bounds.

  Kind:                    polyphony_within_substrate (bound defender; inverted)
  Substrate:               examples/voices/ + phase_2/examples/voices/ + meta_sim/ source tree
  Named residual:          n_files_with_unguarded_coltrane_dependency_or_token
  Predicted upper bound:   0
  Bound under test:        PREREGISTRATION §1 bound #13

KILL CONDITION (INVERTED)
=========================

  - n_violations == 0 → pass (bound supported)
  - n_violations > 0  → fail (bound counter-observation — silent
                              coupling to coltrane-oss internals)
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

VOICE_NAME = "bound_defender_13_no_coltrane_silent_commingling_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "examples_voices_plus_phase_2_voices_plus_meta_sim_source_tree",
    "named_residual": "n_files_with_unguarded_coltrane_dependency_or_token",
    "predicted_value_upper_bound": 0,
    "verdict_inversion": True,
    "bound_under_test": (
        "PREREGISTRATION §1 bound #13 (committed in docs/"
        "coltrane_substrate_acknowledgement.md) — grid-diamondcutter is "
        "not silently coupled to coltrane-oss internals; cross-phase "
        "consumption requires explicit §3.5 declaration"
    ),
}

KILL_CONDITION = {
    "metric": "n_voice_or_library_files_with_unguarded_coltrane_token_in_source_body_or_import",
    "rule": (
        "pass if 0 source files contain 'import coltrane' (any form) "
        "AND 0 source bodies contain an unguarded 'coltrane' token outside "
        "docstrings/guarded windows (bound supported); fail if any "
        "violation (bound counter-observation requiring §1 flagging-record)"
    ),
    "rationale": (
        "Cross-phase consumption declarations per phase-2 §3.5 require "
        "explicit upstream sidecar references; silently embedding "
        "coltrane-oss internals would bypass the §3.5 contract. The "
        "defender catches that bypass via source-scan at PR-merge time. "
        "Guard window allows legitimate mentions in §1 bound text, this "
        "voice's own bound description, and explicit §3.5 declarations."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/bound_defender_13_no_coltrane_silent_commingling_v1.py",
    "source_file": "examples/voices/bound_defender_13_no_coltrane_silent_commingling_v1.py",
    "input_parameters": {
        "scan_roots": ["examples/voices", "phase_2/examples/voices", "meta_sim"],
        "scan_extensions": [".py"],
        "exclude_directories": ["__pycache__", ".pytest_cache"],
        "import_patterns": [
            r"^\s*import\s+coltrane\b",
            r"^\s*from\s+coltrane(\.|\s)",
        ],
        "token_pattern": r"\bcoltrane\b",
        "guard_window_chars": 400,
        "guard_phrases": [
            "bound #13",
            "bound_13",
            "row 13",
            "coltrane_substrate_acknowledgement",
            "§1 bound #13",
            "§3.5 cross_phase_consumption",
            "cross_phase_consumption",
            "NOT silently coupled",
            "is NOT a hard dependency",
            "is not a hard dependency",
        ],
        "self_voice_exclusion": "bound_defender_13_no_coltrane_silent_commingling_v1",
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


def _is_self_voice_file(path: Path) -> bool:
    return RUN_PROTOCOL["input_parameters"]["self_voice_exclusion"] in path.stem


def _iter_target_files() -> list[Path]:
    p = RUN_PROTOCOL["input_parameters"]
    excluded = set(p["exclude_directories"])
    files: list[Path] = []
    repo_root_candidates = [Path.cwd(), Path(__file__).resolve().parent.parent.parent]
    repo_root = next((r for r in repo_root_candidates if (r / "PREREGISTRATION.md").exists()), Path.cwd())
    for sub in p["scan_roots"]:
        root = repo_root / sub
        if not root.exists():
            continue
        for ext in p["scan_extensions"]:
            for f in root.rglob(f"*{ext}"):
                if any(part in excluded for part in f.parts):
                    continue
                files.append(f)
    return files


def _strip_python_docstrings(src: str) -> str:
    pattern = re.compile(r'(?P<quote>"""|\'\'\')(?:.*?)(?P=quote)', re.DOTALL)
    return pattern.sub(" ", src)


def _is_guarded(text: str, match_start: int, guard_phrases: list[str], window: int) -> bool:
    lo = max(0, match_start - window)
    hi = min(len(text), match_start + window)
    window_text = text[lo:hi].lower()
    return any(phrase.lower() in window_text for phrase in guard_phrases)


def _scan_file(path: Path) -> dict:
    p = RUN_PROTOCOL["input_parameters"]
    try:
        src = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"path": str(path), "read_error": str(e), "violations": []}

    violations: list[dict] = []

    # Import-pattern scan (always — even on self voice; self has no real imports)
    for line_no, line in enumerate(src.splitlines(), start=1):
        if _is_self_voice_file(path):
            break
        for pat in p["import_patterns"]:
            if re.search(pat, line):
                violations.append({
                    "kind": "import_statement",
                    "line": line_no,
                    "text": line.strip(),
                    "pattern": pat,
                })
                break

    # Token-pattern scan with guard window (skip self voice)
    if not _is_self_voice_file(path):
        body = _strip_python_docstrings(src)
        for m in re.finditer(p["token_pattern"], body, flags=re.IGNORECASE):
            already_import = any(re.search(ip, body, flags=re.MULTILINE) for ip in p["import_patterns"])
            if _is_guarded(body, m.start(), p["guard_phrases"], p["guard_window_chars"]):
                continue
            violations.append({
                "kind": "unguarded_token_in_non_docstring_body",
                "match_start": m.start(),
                "match_text": m.group(0),
                "already_caught_as_import": already_import,
            })

    return {
        "path": str(path),
        "read_error": None,
        "violations": violations,
        "n_violations": len(violations),
    }


def run_scan() -> dict:
    files = _iter_target_files()
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
        outcome = "bound_supported_no_silent_coltrane_coupling"
        rationale = (
            f"Inspected {scan['n_files_scanned']} voice + library .py "
            f"file(s). Total unguarded coltrane-import-or-token "
            f"violations: {n_total}. Pre-committed upper bound: {bound}. "
            f"§1 bound #13 supported by direct source inspection. Voice "
            f"PASSes its inverted kill condition."
        )
    else:
        verdict = "fail"
        outcome = "bound_counter_observation_silent_coltrane_coupling"
        offending = [
            {"path": r["path"], "n_violations": r["n_violations"]}
            for r in scan["per_file_results"]
            if r["n_violations"] > 0
        ]
        rationale = (
            f"Inspected {scan['n_files_scanned']} files. Found {n_total} "
            f"unguarded coltrane-import-or-token violations across "
            f"{scan['n_offending_files']} files: {offending}. Crosses the "
            f"pre-committed upper bound of {bound}. Per §1 bound-crossing "
            f"protocol requires flagging-record entry. Either the coltrane "
            f"reference should be removed, declared explicitly via "
            f"phase-2 §3.5 cross-phase consumption, or guarded by §1 "
            f"bound #13 text."
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
    print(f"under test: PREREGISTRATION §1 bound #13 (no silent coltrane coupling)")
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
                    print(f"      {v['kind']}: {v.get('match_text', v.get('text', ''))[:80]}")
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
