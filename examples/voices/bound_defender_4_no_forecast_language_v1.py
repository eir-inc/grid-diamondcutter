# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""bound_defender_4_no_forecast_language_v1.py — §3.1 polyphony voice defending §1 bound #4.

§1 honesty bound #4: cascade results produced by the methodology — the threshold-class
cascade investigated in §0, the qualitative trajectory recovered in §4's validation pass,
or any aggregate across voices — are NOT predictions of what the real economy or the real
grid will do. Cascade results are conditional findings under stated modeling assumptions.

This voice defends bound #4 by source-inspection across the registry: it scans every
voice file + sidecar in examples/voices/ for forecast-language that would cross the bound.
Inverted-kill (per miles PR #16/#18 + groove PR #19): PASS = bound defended (no creep
language found), FAIL = bound counter-observation (creep detected; voices need amendment
OR the bound needs to be revisited per §5.1).

WHAT THIS VOICE PREDICTS
========================

For every .py file in examples/voices/ and every .sidecar.json in the same directory,
the file does NOT contain language that would assert any of the following:

  - "this voice predicts the real grid will [...]"
  - "forecasts that [country/region/grid] [will/shall/by year X] [...]"
  - "the methodology predicts a real-world outcome of [...]"
  - "expected [actual / real / production] grid [response / behavior / state] [...]"

The pattern set is enumerated in FORECAST_LANGUAGE_PATTERNS below. Each pattern is a
regex; a match anywhere in the scanned files counts as a bound counter-observation.

The bound DOES permit (and many voices use) language that is explicitly hedged:

  - "the methodology recovers the qualitative trajectory [...]"
  - "under stated assumptions, the substrate produces [...]"
  - "in the synthetic substrate, the cycle [...]"
  - "demonstration substrate [...]"
  - "this voice does NOT claim real-grid forecast"

KILL CONDITION
==============

Voice FAILS if any forecast-language regex matches anywhere in the scanned files.
The matching files + line numbers are reported in the verdict sidecar so the bound's
counter-observation is auditable + remediable.

HONEST SCOPE
============

Source-inspection is one defense path. It catches the most common creep mode: language
that asserts forward-causal real-world claims. It does NOT catch:
  - subtle implicit forecasting (e.g. precise numerical predictions without explicit
    "forecast" word)
  - sidecar metadata that implies forecast through field naming
  - external presentation material (slides, blog posts, white papers) that re-frame
    OSS voices as forecasts after publication

Subtler defenses (e.g. semantic-level inspection, presentation-content audits) are
complementary follow-up voices. This v1 covers the surface-language path.
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ===========================================================================
# §3.1 — The per-voice unit (five required fields)
# ===========================================================================

VOICE_NAME = "bound_defender_4_no_forecast_language_v1"

FORECAST_LANGUAGE_PATTERNS = [
    # Direct forward-causal real-world claim language
    r"\bpredicts? the real\s+(grid|economy|world|market)\b",
    r"\bforecast(s|ed)?\s+that\s+(the\s+)?(grid|economy|real|country)\b",
    r"\bthe (real )?grid will\b",
    r"\bby\s+(20\d{2})\s+the\s+(real|actual|production)\s+(grid|economy)\b",
    r"\bthis\s+voice\s+predicts\s+the\s+real\b",
    r"\bmethodology\s+predicts\s+a\s+real(\s|-)world\b",
    r"\bproduction\s+grid\s+(response|behavior|forecast)\b",
    r"\breal(\s|-)?grid\s+forecast\b",
]

# Compile case-insensitive, multiline
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in FORECAST_LANGUAGE_PATTERNS]

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "examples_voices_directory_source_scan",
    "named_residual": "no_forecast_language_in_voice_or_sidecar_files",
    "honesty_bound_defended": (
        "§1 bound #4: cascade results from the methodology are NOT predictions of "
        "what the real economy or real grid will do. They are conditional findings "
        "under stated modeling assumptions."
    ),
    "patterns_scanned": FORECAST_LANGUAGE_PATTERNS,
    "scan_target_globs": ["examples/voices/*.py", "examples/voices/*.sidecar.json"],
    "exclusions": ["bound_defender_4_no_forecast_language_v1.py", "bound_defender_4_no_forecast_language_v1.sidecar.json"],
}

KILL_CONDITION = {
    "metric": "n_forecast_language_matches",
    "rule": "fail if n_matches > 0 across the scan-target file set (after excluding this voice's own files)",
    "rationale": (
        "Each match is a place in the registry where a voice or sidecar has crossed the "
        "bound: claiming or implying a real-world forecast outcome. Per §0.3 + §5.1, "
        "the counter-observation should surface so voices can be amended OR the bound "
        "can be revisited."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/bound_defender_4_no_forecast_language_v1.py",
    "source_file": "examples/voices/bound_defender_4_no_forecast_language_v1.py",
    "scan_method": "regex over file contents, case-insensitive multiline",
    "python_min_version": "3.9",
    "deps": [],  # stdlib only
}


# ===========================================================================
# Run + verdict computation
# ===========================================================================

def _scan_files() -> dict:
    """Scan examples/voices/*.py + *.sidecar.json for forecast-language matches."""
    REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    voices_dir = REPO_ROOT / "examples" / "voices"
    excluded = set(PREDICTION["exclusions"])
    files_scanned = []
    matches = []
    for path in sorted(voices_dir.glob("*.py")):
        if path.name in excluded:
            continue
        files_scanned.append(str(path.relative_to(REPO_ROOT)))
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IOError):
            continue
        for pattern_idx, pattern in enumerate(COMPILED_PATTERNS):
            for m in pattern.finditer(content):
                line_no = content[: m.start()].count("\n") + 1
                matches.append({
                    "file": str(path.relative_to(REPO_ROOT)),
                    "line": line_no,
                    "matched_text": m.group(0)[:120],
                    "pattern": FORECAST_LANGUAGE_PATTERNS[pattern_idx],
                })
    for path in sorted(voices_dir.glob("*.sidecar.json")):
        if path.name in excluded:
            continue
        files_scanned.append(str(path.relative_to(REPO_ROOT)))
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IOError):
            continue
        for pattern_idx, pattern in enumerate(COMPILED_PATTERNS):
            for m in pattern.finditer(content):
                line_no = content[: m.start()].count("\n") + 1
                matches.append({
                    "file": str(path.relative_to(REPO_ROOT)),
                    "line": line_no,
                    "matched_text": m.group(0)[:120],
                    "pattern": FORECAST_LANGUAGE_PATTERNS[pattern_idx],
                })
    return {
        "n_files_scanned": len(files_scanned),
        "files_scanned": files_scanned,
        "n_matches": len(matches),
        "matches": matches,
    }


def _compute_verdict(observed: dict) -> str:
    return "pass" if observed["n_matches"] == 0 else "fail"


def _emit_sidecar(observed: dict, verdict: str) -> str:
    sidecar = {
        "voice_name": VOICE_NAME,
        "verdict": verdict,
        "honesty_bound_defended": PREDICTION["honesty_bound_defended"],
        "observed": observed,
        "kill_condition_rule": KILL_CONDITION["rule"],
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    canonical = json.dumps(sidecar, sort_keys=True).encode("utf-8")
    sidecar["run_sha256"] = hashlib.sha256(canonical).hexdigest()
    here = os.path.dirname(os.path.abspath(__file__))
    sidecar_path = os.path.join(here, f"{VOICE_NAME}.sidecar.json")
    with open(sidecar_path, "w") as f:
        json.dump(sidecar, f, indent=2, sort_keys=True)
    return sidecar_path


def main():
    print("=" * 76)
    print(f"§3.1 polyphony voice — {VOICE_NAME}")
    print(f"defends §1 honesty bound #4 (cascade results NOT real-grid forecasts)")
    print("=" * 76)

    observed = _scan_files()
    verdict = _compute_verdict(observed)
    sidecar_path = _emit_sidecar(observed, verdict)

    print(f"\nscanned {observed['n_files_scanned']} files in examples/voices/")
    print(f"forecast-language matches found: {observed['n_matches']}")
    if observed["n_matches"] > 0:
        print(f"\nbound counter-observations:")
        for m in observed["matches"][:20]:
            print(f"  {m['file']}:{m['line']}  match: {m['matched_text']!r}  (pattern: {m['pattern']})")
        if len(observed["matches"]) > 20:
            print(f"  ... and {len(observed['matches']) - 20} more")
    print(f"\nVERDICT: {verdict.upper()}")
    print(f"  (inverted-kill: PASS = §1 bound #4 defended; FAIL = forecast-language creep detected)")
    print(f"sidecar: {sidecar_path}")


if __name__ == "__main__":
    main()
