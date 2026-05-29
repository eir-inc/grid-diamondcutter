"""
bound_defender_10_no_investment_advice_v1.py — §3.1 polyphony voice
(inverted kill) defending phase-2 honesty bound #10.

Phase-2 bound #10 (from `phase_2/PREREGISTRATION_PHASE_2.md` §1):

  "the project will NOT claim that any phase-2 voice's verdict is
   investment advice in any jurisdiction"

Mechanically enforced via source-scan: NO phase-2 voice's source or
sidecar body may contain unguarded investment-advice tokens (buy /
sell / hold / forecast / recommend / position / allocate / target price /
expected return / etc.) outside docstrings or §1-style guard windows.

Inheritance: this voice inherits the bound-defender pattern from phase-1
`bound_defender_4_no_forecast_language_v1` (groove PR #53), applied to a
different token set centered on investment-advice claim language.

Evasion-class lineage: declares phase-A signature
`substrate_shape_evasion` (investment-advice token usage IS a
substrate-shape signal — the substrate of language patterns the voice
emits to its audience).

WHAT THIS VOICE PREDICTS
========================

Zero phase-2 .py source bodies (excluding docstrings) AND zero phase-2
sidecar verdict-rationale-or-outcome-category strings contain an
unguarded investment-advice token.

  Kind:                    polyphony_within_substrate (bound defender; inverted)
  Substrate:               phase_2/ source + sidecar JSON tree
  Named residual:          n_phase_2_files_with_unguarded_investment_advice_token
  Predicted upper bound:   0
  Bound under test:        phase-2 PREREGISTRATION_PHASE_2.md §1 bound #10
  Evasion-class lineage:   substrate_shape_evasion (phase-A)

KILL CONDITION (INVERTED)
=========================

  - n_violations == 0 → pass (bound supported by source-scan)
  - n_violations > 0  → fail (bound counter-observation — phase-2 file
                              contains unguarded investment-advice language)
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

VOICE_NAME = "bound_defender_10_no_investment_advice_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "phase_2_source_and_sidecar_tree",
    "named_residual": "n_phase_2_files_with_unguarded_investment_advice_token",
    "predicted_value_upper_bound": 0,
    "verdict_inversion": True,
    "evasion_class_lineage": "substrate_shape_evasion",
    "bound_under_test": (
        "phase-2 PREREGISTRATION_PHASE_2.md §1 bound #10 — phase-2 voice "
        "verdicts are not investment advice in any jurisdiction"
    ),
}

KILL_CONDITION = {
    "metric": "n_phase_2_files_with_unguarded_investment_advice_token_in_body_or_sidecar_text",
    "rule": (
        "pass if 0 phase-2 .py source bodies (non-docstring) AND 0 phase-2 "
        "sidecar verdict-text strings contain an unguarded investment-advice "
        "token (bound supported); fail if any violation (bound counter-"
        "observation requiring §1 flagging-record)"
    ),
    "rationale": (
        "Investment-advice tokens are detectable from source + sidecar text. "
        "A guard window (±400 chars of the §1 bound text or 'NOT advice' "
        "language) allows legitimate mentions in the bound text + this "
        "defender's own bound description without firing. The defender "
        "catches bound-crossing at phase-2-PR-merge time via CI integration "
        "on top of this voice."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python phase_2/examples/voices/bound_defender_10_no_investment_advice_v1.py",
    "source_file": "phase_2/examples/voices/bound_defender_10_no_investment_advice_v1.py",
    "input_parameters": {
        "scan_root": "phase_2",
        "scan_extensions": [".py", ".sidecar.json"],
        "exclude_directories": ["__pycache__", ".pytest_cache"],
        "investment_advice_tokens": [
            r"\bbuy\s+(?:signal|recommendation|rating|action|now)\b",
            r"\bsell\s+(?:signal|recommendation|rating|action|now)\b",
            r"\bhold\s+(?:signal|recommendation|rating)\b",
            r"\binvest(?:ment)?\s+(?:advice|recommendation|rating|guidance)\b",
            r"\btarget\s+price\b",
            r"\bexpected\s+return\b",
            r"\bportfolio\s+allocation\b",
            r"\b(?:buy|sell|long|short)\s+the\s+(?:market|asset|stock|future|trade)\b",
        ],
        "guard_window_chars": 400,
        "guard_phrases": [
            "is NOT investment advice",
            "not investment advice",
            "are NOT investment advice",
            "verdicts are not investment advice",
            "bound #10",
            "PREREGISTRATION_PHASE_2.md §1 bound #10",
            "NOT a substitute for",
            "out of phase-2 scope",
        ],
        "self_voice_exclusion": "bound_defender_10_no_investment_advice_v1",
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


def _is_self_voice_file(path: Path) -> bool:
    return RUN_PROTOCOL["input_parameters"]["self_voice_exclusion"] in path.stem


def _iter_phase_2_files() -> list[Path]:
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
    for ext in p["scan_extensions"]:
        for f in root.rglob(f"*{ext}"):
            if any(part in excluded for part in f.parts):
                continue
            files.append(f)
    return files


def _strip_python_docstrings(src: str) -> str:
    pattern = re.compile(r'(?P<quote>"""|\'\'\')(?:.*?)(?P=quote)', re.DOTALL)
    return pattern.sub(" ", src)


def _is_guarded(src: str, match_start: int, guard_phrases: list[str], window: int) -> bool:
    lo = max(0, match_start - window)
    hi = min(len(src), match_start + window)
    window_text = src[lo:hi].lower()
    return any(phrase.lower() in window_text for phrase in guard_phrases)


def _scan_python_file(path: Path) -> dict:
    p = RUN_PROTOCOL["input_parameters"]
    try:
        src = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"path": str(path), "read_error": str(e), "violations": []}

    body = _strip_python_docstrings(src) if not _is_self_voice_file(path) else src

    violations: list[dict] = []
    for pat in p["investment_advice_tokens"]:
        for m in re.finditer(pat, body, flags=re.IGNORECASE):
            if _is_self_voice_file(path):
                continue
            if _is_guarded(body, m.start(), p["guard_phrases"], p["guard_window_chars"]):
                continue
            violations.append({
                "pattern": pat,
                "match_text": m.group(0)[:80],
                "match_start": m.start(),
            })
    return {
        "path": str(path),
        "read_error": None,
        "violations": violations,
        "n_violations": len(violations),
    }


def _scan_sidecar_file(path: Path) -> dict:
    p = RUN_PROTOCOL["input_parameters"]
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"path": str(path), "read_error": str(e), "violations": []}

    if _is_self_voice_file(path):
        return {"path": str(path), "read_error": None, "violations": [], "n_violations": 0}

    violations: list[dict] = []
    for pat in p["investment_advice_tokens"]:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            if _is_guarded(text, m.start(), p["guard_phrases"], p["guard_window_chars"]):
                continue
            violations.append({
                "pattern": pat,
                "match_text": m.group(0)[:80],
                "match_start": m.start(),
            })
    return {
        "path": str(path),
        "read_error": None,
        "violations": violations,
        "n_violations": len(violations),
    }


def run_scan() -> dict:
    files = _iter_phase_2_files()
    per_file = []
    for f in files:
        if f.name.endswith(".sidecar.json"):
            per_file.append(_scan_sidecar_file(f))
        else:
            per_file.append(_scan_python_file(f))
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
        outcome = "bound_supported_no_unguarded_investment_advice_token"
        rationale = (
            f"Inspected {scan['n_files_scanned']} phase-2 .py + .sidecar.json "
            f"file(s). Total unguarded investment-advice token matches: {n_total}. "
            f"Pre-committed upper bound: {bound}. Phase-2 §1 bound #10 supported "
            f"by direct source + sidecar scan. Voice PASSes its inverted kill "
            f"condition."
        )
    else:
        verdict = "fail"
        outcome = "bound_counter_observation_investment_advice_token_present"
        offending = [r for r in scan["per_file_results"] if r["n_violations"] > 0]
        rationale = (
            f"Inspected {scan['n_files_scanned']} phase-2 file(s). Found "
            f"{n_total} unguarded investment-advice token matches across "
            f"{scan['n_offending_files']} file(s). Crosses the pre-committed "
            f"upper bound of {bound}. Per §1 bound-crossing protocol requires "
            f"flagging-record entry. Each offending match should either be "
            f"guarded with explicit 'NOT investment advice' or bound-#10 "
            f"reference, or the token should be removed."
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
    print(f"under test: phase-2 §1 bound #10 (no investment advice)")
    print("=" * 72)
    scan = run_scan()
    print(f"  n files scanned:    {scan['n_files_scanned']}")
    print(f"  n total violations: {scan['n_total_violations']}")
    print(f"  n offending files:  {scan['n_offending_files']}")
    if scan["n_offending_files"] > 0:
        for r in scan["per_file_results"]:
            if r["n_violations"] > 0:
                print(f"    [{r['n_violations']}] {r['path']}")
                for v in r["violations"]:
                    print(f"      pattern: {v['pattern']}  match: {v['match_text']}")
    print("-" * 72)
    verdict = compute_verdict(scan)
    print(f"  pre-committed bound: {verdict['predicted_upper_bound']}")
    print(f"  verdict:             {verdict['verdict'].upper()}")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
