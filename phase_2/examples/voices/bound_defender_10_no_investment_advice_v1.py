# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
bound_defender_10_no_investment_advice_v1.py — phase-2 §3.1 polyphony INVERTED-KILL voice.

Mechanically defends phase-2 §1 honesty bound row 10:
  "The project will NOT claim that any phase-2 voice's verdict is investment
   advice in any jurisdiction."

Source-scan inverted-kill, same shape as cajal Phase-A #57 + miles Phase-2
#106 + lighthouse #53 + subhuti #54. Walks open-repo + phase_2/ artifacts
and ALARMs on any reference that could be read as investment-advice or
trading-recommendation language.

If the scan finds matches, the registry has crossed bound row 10 — the
project produced material a reader could read as investment advice. The
voice FAILs to indicate the violation; reviewer attention required to
scrub the leak.

If the scan finds zero unguarded matches, the bound is mechanically
defended.

INVERTED-KILL semantics:
  PASS = 0 unguarded matches → bound supported by absence-of-claim
  FAIL = ≥ 1 unguarded match → bound counter-observed

Per §6 boundary: no eirmath import. Pure regex over committed artifacts.
Per §1.9-12: same shape, hand-asserted bound, mechanically defended.
"""
from __future__ import annotations
import json
import hashlib
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ===========================================================================
# §3.1 — polyphony INVERTED-KILL voice unit
# ===========================================================================

VOICE_NAME = "bound_defender_10_no_investment_advice_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "open_repo_and_phase_2_committed_artifacts_md_py_json",
    "named_residual": "no_investment_advice_or_trading_recommendation_language_leaks_into_phase_2_artifacts",
    "inverted_kill_design": True,
    "predicted_outcome": "zero_unguarded_investment_advice_pattern_matches_at_v1",
    "evasion_class_lineage": "data_availability_evasion",
    "rationale": (
        "Defends phase-2 §1 row 10 by source-scan. Pattern set targets typical "
        "leak vectors: buy/sell/hold language attached to assets or markets, "
        "recommended-allocation language, trading-strategy-specific assertions, "
        "alpha / beta / Sharpe-ratio claims tied to specific positions. Same "
        "shape as cajal Phase-A #57, miles Phase-2 #106, lighthouse #53, "
        "subhuti #54 source-scan defenders. Guard-window exemption permits "
        "intentional §1-row-10 quotation."
    ),
}

KILL_CONDITION = {
    "metric": "unguarded_investment_advice_match_count",
    "rule": (
        "fail if ≥ 1 source-scan match in committed artifacts that asserts or "
        "implies investment advice / trading recommendation language (matches "
        "guarded by §1-row-10 citation within ±400 chars are exempted, matching "
        "Phase-A #57 / Phase-2 #106 guard-window convention)"
    ),
    "rationale": (
        "Inverted-kill: PASS = bound supported by absence-of-claim. Any match "
        "is bound counter-observation. Guard-window exemption permits "
        "intentional §1-row-10 quotation (this voice file, PREREGISTRATION_"
        "PHASE_2.md row text, future bound-invocation contexts)."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python phase_2/examples/voices/bound_defender_10_no_investment_advice_v1.py",
    "source_file": "phase_2/examples/voices/bound_defender_10_no_investment_advice_v1.py",

    # §3.5 — public-signal source: source-scan defender does not consume external public signal
    "public_signal_source": {
        "feed_name": "self_scan_committed_repo_artifacts",
        "country_or_region": "N/A",
        "time_window": "commit_HEAD",
        "citation_anchor": "this_repo_at_run_commit",
    },

    # §3.5 — no cross-phase consumption (defender voice)
    "cross_phase_consumption": [],

    "input_parameters": {
        "scan_root": ".",
        "scan_extensions": [".md", ".py", ".json"],
        "exclude_paths": [
            ".git",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            # Exempt this voice file + sidecar from triggering its own kill:
            "bound_defender_10_no_investment_advice_v1.py",
            "bound_defender_10_no_investment_advice_v1.sidecar.json",
        ],
        # Investment-advice / trading-recommendation leak patterns
        "claim_patterns": [
            # Direct buy/sell/hold recommendation tied to an asset
            r"\b(?:buy|sell|hold|short|long)\s+(?:recommendation|signal|advice)\s+(?:on|for)\b",
            r"\brecommend(?:ed)?\s+(?:position|allocation|exposure)\s+(?:in|to)\b",
            r"\bportfolio\s+allocation\s+(?:should|must|recommended)\b",
            # Trading-strategy-specific assertions
            r"\boptimal\s+trade\s+(?:size|timing|entry|exit)\b",
            r"\btarget\s+price\s+of\s+\$",
            r"\bstop[-\s]loss\s+at\s+\$",
            # Quantitative-finance signal-quality assertions tied to trades
            r"\bsharpe\s+ratio\s+(?:of|≥|>)\s+\d",
            r"\balpha\s+generation\s+(?:of|≥|>)\s+\d",
            r"\binformation\s+ratio\s+(?:of|≥|>)\s+\d",
            # Direct advice-grammar
            r"\binvestors?\s+should\s+(?:buy|sell|hold|short|long|allocate)\b",
            r"\btraders?\s+should\s+(?:enter|exit|increase|decrease)\b",
        ],
        # Guard window — exemptions for intentional §1-row-10 quotation
        "guard_strings": [
            "§1 row 10",
            "honesty bound row 10",
            "bound row 10",
            "row 10 bound",
            "§1.10",
            "§1 bound #10",
            "§1 bound 10",
            "investment advice",  # the bound's own phrasing
            "bound_defender_10",  # voice file itself
            "is NOT a measurement",  # PREREGISTRATION row negation
            "DOES NOT claim",
            "will NOT claim",
            "NOT claim",
            "leak vector",  # discussing leak shapes
        ],
        "guard_window_chars": 400,
        "random_seed": 1010,
    },

    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },

    "computational_budget": {
        "max_runtime_seconds": 30,
        "max_external_api_calls": 0,
    },
}


# ===========================================================================
# Voice implementation
# ===========================================================================

def _iter_scan_files(root: Path, extensions: list[str], exclude: list[str]) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in extensions:
            continue
        path_str = str(path)
        if any(excl in path_str for excl in exclude):
            continue
        files.append(path)
    return sorted(files)


def _match_with_guards(text: str, claim_pat: re.Pattern, guard_strings: list[str], guard_window: int) -> list[dict]:
    matches: list[dict] = []
    for m in claim_pat.finditer(text):
        start, end = m.span()
        window_lo = max(0, start - guard_window)
        window_hi = min(len(text), end + guard_window)
        window_text = text[window_lo:window_hi]
        guarded = any(guard.lower() in window_text.lower() for guard in guard_strings)
        if not guarded:
            matches.append({
                "match_text": m.group(0),
                "char_offset": start,
                "guarded": False,
            })
    return matches


def run_voice() -> dict:
    p = RUN_PROTOCOL["input_parameters"]
    root = REPO_ROOT
    files = _iter_scan_files(root, p["scan_extensions"], p["exclude_paths"])
    claim_patterns = [re.compile(pat, re.IGNORECASE | re.MULTILINE) for pat in p["claim_patterns"]]
    guard_strings = p["guard_strings"]
    guard_window = p["guard_window_chars"]

    per_file_results: list[dict] = []
    total_unguarded_matches = 0

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        file_matches: list[dict] = []
        for pat in claim_patterns:
            file_matches.extend(_match_with_guards(text, pat, guard_strings, guard_window))
        if file_matches:
            per_file_results.append({
                "path": str(path.relative_to(root)),
                "n_unguarded_matches": len(file_matches),
                "matches": file_matches[:10],
            })
            total_unguarded_matches += len(file_matches)

    return {
        "n_files_scanned": len(files),
        "n_files_with_unguarded_matches": len(per_file_results),
        "total_unguarded_matches": int(total_unguarded_matches),
        "per_file": per_file_results,
        "scan_extensions": p["scan_extensions"],
        "claim_patterns": p["claim_patterns"],
        "guard_window_chars": guard_window,
    }


def compute_verdict(run_output: dict) -> dict:
    n_matches = run_output["total_unguarded_matches"]

    if n_matches == 0:
        verdict = "pass"
        rationale = (
            f"INVERTED-KILL PASS: 0 unguarded investment-advice / trading-"
            f"recommendation matches across {run_output['n_files_scanned']} "
            f"scanned files. Phase-2 §1 honesty bound row 10 mechanically "
            f"defended at this commit. Apoha-at-bound-level: bound supported "
            f"by absence-of-claim. Scan is regex-source-only, no eirmath "
            f"dependency per §6 boundary."
        )
    else:
        verdict = "fail"
        rationale = (
            f"INVERTED-KILL FAIL: {n_matches} unguarded investment-advice / "
            f"trading-recommendation match(es) across "
            f"{run_output['n_files_with_unguarded_matches']} file(s). Phase-2 "
            f"§1 bound row 10 counter-observed — registry needs scrub or the "
            f"matches need guard-window §1-row-10 invocation."
        )

    return {
        "verdict": verdict,
        "n_files_scanned": run_output["n_files_scanned"],
        "n_files_with_unguarded_matches": run_output["n_files_with_unguarded_matches"],
        "total_unguarded_matches": n_matches,
        "inverted_kill_design": True,
        "evasion_class_lineage": PREDICTION["evasion_class_lineage"],
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def emit_sidecar(verdict: dict, run_output: dict, output_path: str) -> str:
    unit = {
        "voice_name": VOICE_NAME,
        "prediction": PREDICTION,
        "kill_condition": KILL_CONDITION,
        "run_protocol": RUN_PROTOCOL,
        "run_output": run_output,
        "verdict": verdict,
    }
    canonical = json.dumps(
        {k: v for k, v in unit.items() if k not in ("verdict", "run_output")},
        sort_keys=True, separators=(",", ":"),
    )
    unit["sidecar_sha256_pre_verdict"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with open(output_path, "w") as f:
        json.dump(unit, f, indent=2)
    return output_path


def main():
    print("=" * 72)
    print(f"voice unit: {VOICE_NAME}  (INVERTED-KILL phase-2 §1.10 defender)")
    print("=" * 72)
    print("predicted: 0 unguarded investment-advice matches → PASS")
    print(f"kill rule: {KILL_CONDITION['rule']}")
    print()
    print("scanning committed open-repo + phase_2/ artifacts...")
    out = run_voice()
    print(f"  files scanned:           {out['n_files_scanned']}")
    print(f"  files with matches:      {out['n_files_with_unguarded_matches']}")
    print(f"  total unguarded matches: {out['total_unguarded_matches']}")
    if out["per_file"]:
        print()
        for f in out["per_file"][:5]:
            print(f"  {f['path']}: {f['n_unguarded_matches']} match(es)")
            for m in f["matches"][:3]:
                print(f"    → {m['match_text']!r}  @ char {m['char_offset']}")
    print()
    verdict = compute_verdict(out)
    print(f"  verdict: {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    print()
    sidecar_path = str(THIS_DIR / f"{VOICE_NAME}.sidecar.json")
    emit_sidecar(verdict, out, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
