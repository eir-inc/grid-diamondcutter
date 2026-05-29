"""
voice_bound_defender_8_eirmath_not_required_v1.py — mechanical defender for
PREREGISTRATION.md §1 honesty bound #8.

§1 bound #8 (verbatim):
    "The project will NOT claim that the closed components of the project's
    analytical pipeline (`eirmath`, per §6) are required to evaluate any claim
    made in this pre-registration. The central question of §0, the substrate-
    voice methodology of §3, the historical-events validation pass of §4, and
    the safety-boundary commitments of §5 are evaluable from the open
    repository alone."

This bound is dual-pronged and *operational*: the open repository must not
depend on `eirmath` for any operational evaluation step, AND every public
mention of `eirmath` must be paired with the boundary-guard language ("not
required", "proprietary", "closed components", "not part of this pre-
registration's claims", etc.).

The defender exercises both:
  (a) STRUCTURAL: walks every .py file in the open repo and looks for
      `import eirmath` or `from eirmath` references. If any open-repo .py
      file imports eirmath, the operational boundary is violated.
  (b) DOCUMENTATIONAL: scans PREREGISTRATION.md + README.md for every
      "eirmath" mention; verifies each is paired with ≥1 boundary-guard phrase
      within ±400 chars.

PASS iff BOTH (a) zero open-repo eirmath imports AND (b) every eirmath mention
is boundary-guarded. FAIL (alarm) if either prong drifts. The bound is uniquely
load-bearing given Eugene's phase-A/phase-B split: phase-A is precisely the
open-repo-only path the §1 bound #8 protects.

Inverted-kill bound-defender. Lineage: PR #17 (§0.3), PR #16 (§1.5), PR #18
(§1.1), PR #21 (§1.2), PR #49 (§1.3), PR #50 (§1.4 attempt). This voice
covers §1.8.

Authored under PREREGISTRATION.md §3.1.
"""
from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


VOICE_NAME = "bound_defender_8_eirmath_not_required_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "registry_meta",
    "named_residual": (
        "PREREGISTRATION §1 bound #8 defense — the open repository must NOT depend "
        "on the proprietary `eirmath` package operationally (no `import eirmath` "
        "anywhere in *.py), AND every public mention of `eirmath` must be paired "
        "with boundary-guard language within a local window. The bound is uniquely "
        "load-bearing for Eugene's phase-A directive (max-out without eirmath, post "
        "results via PR/merge); phase-A is precisely the open-repo-only path #8 "
        "protects."
    ),
    "documents_to_scan": ["PREREGISTRATION.md", "README.md"],
    "eirmath_anchor_terms": ["eirmath"],
    "boundary_guard_phrases_any_of": [
        "not required",
        "proprietary",
        "closed components",
        "closed component",
        "not part of this pre-registration's claims",
        "not part of this pre-registration",
        "kept private",
        "evaluable from the open repository alone",
        "open repository is sufficient",
        "separate proprietary package",
        "separate from this repository",
        "commercial wrapper",
    ],
    "guard_search_radius_chars": 400,
    "structural_check_python_extensions": [".py"],
    "structural_check_excluded_paths": [
        ".venv",
        "venv",
        "__pycache__",
        ".git",
        "build",
        "dist",
    ],
    "alarm_semantics": (
        "PASS = §1 bound #8 mechanically defended on both prongs (no open-repo "
        "eirmath imports AND every eirmath doc mention is boundary-guarded); "
        "FAIL = alarm (either prong drifts — operational dependency leaked OR "
        "documentation guard removed)."
    ),
}

KILL_CONDITION = {
    "metric": "structural_and_documentation_eirmath_guard_both_hold",
    "rule": (
        "FAIL (alarm) if (a) any open-repo .py file contains `import eirmath` or "
        "`from eirmath`, OR (b) any 'eirmath' mention in scanned docs lacks ≥1 "
        "boundary-guard phrase within ±400 chars. PASS iff both hold."
    ),
    "rationale": (
        "Bound #8 is the single most load-bearing bound for phase-A (Eugene's "
        "directive to max-out without eirmath and post via PR/merge). A future "
        "edit that adds an `import eirmath` to any open-repo .py would silently "
        "break the bound. Mechanizing both the structural and documentation prongs "
        "means a CI run at any commit can audit the boundary by inspection of the "
        "same artifacts external readers and reviewers see."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/voice_bound_defender_8_eirmath_not_required_v1.py",
    "source_file": "examples/voices/voice_bound_defender_8_eirmath_not_required_v1.py",
    "input_parameters": {
        "documents_to_scan": ["PREREGISTRATION.md", "README.md"],
        "guard_search_radius_chars": 400,
        "structural_scan_root": str(REPO_ROOT),
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


_IMPORT_PATTERNS = [
    re.compile(r"^\s*import\s+eirmath(?:\s|$|\.|;)", re.MULTILINE),
    re.compile(r"^\s*from\s+eirmath(?:\s+import|\.)", re.MULTILINE),
]


def _structural_scan() -> dict:
    """Walk .py files; collect any eirmath imports."""
    findings = []
    n_files = 0
    excluded = set(PREDICTION["structural_check_excluded_paths"])
    for path in REPO_ROOT.rglob("*.py"):
        # skip excluded path components
        if any(part in excluded for part in path.parts):
            continue
        n_files += 1
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        for pat in _IMPORT_PATTERNS:
            for m in pat.finditer(text):
                # capture line context
                line_start = text.rfind("\n", 0, m.start()) + 1
                line_end = text.find("\n", m.start())
                if line_end == -1:
                    line_end = len(text)
                line = text[line_start:line_end].strip()
                findings.append(
                    {
                        "file": str(path.relative_to(REPO_ROOT)),
                        "match": line,
                    }
                )
    return {
        "n_python_files_scanned": n_files,
        "n_eirmath_imports_found": len(findings),
        "findings": findings,
        "structural_clean": len(findings) == 0,
    }


def _documentation_scan() -> dict:
    """Scan PREREGISTRATION.md + README.md for eirmath mentions + guard presence."""
    radius = PREDICTION["guard_search_radius_chars"]
    phrases = PREDICTION["boundary_guard_phrases_any_of"]
    docs = []
    for doc_name in PREDICTION["documents_to_scan"]:
        doc_path = REPO_ROOT / doc_name
        if not doc_path.exists():
            docs.append({
                "doc": doc_name,
                "doc_exists": False,
                "anchor_mentions": [],
            })
            continue
        text = doc_path.read_text()
        text_lower = text.lower()
        positions = sorted({m.start() for m in re.finditer(r"eirmath", text_lower)})
        anchor_mentions = []
        for pos in positions:
            ws = max(0, pos - radius)
            we = min(len(text), pos + radius)
            window = text[ws:we].lower()
            matched = [p for p in phrases if p.lower() in window]
            cs = max(0, pos - 60)
            ce = min(len(text), pos + 60)
            snippet = text[cs:ce].replace("\n", " ").strip()
            anchor_mentions.append({
                "char_offset": pos,
                "context": f"...{snippet}...",
                "guard_phrases_found": matched,
                "guarded": len(matched) >= 1,
            })
        docs.append({
            "doc": doc_name,
            "doc_exists": True,
            "anchor_mentions": anchor_mentions,
        })
    total = sum(len(d["anchor_mentions"]) for d in docs)
    guarded = sum(sum(1 for m in d["anchor_mentions"] if m["guarded"]) for d in docs)
    return {
        "documents": docs,
        "total_eirmath_mentions": total,
        "guarded_mentions": guarded,
        "unguarded_mentions": total - guarded,
        "documentation_clean": (total - guarded) == 0,
    }


def run_voice_measurement() -> dict:
    return {
        "structural": _structural_scan(),
        "documentation": _documentation_scan(),
    }


def compute_verdict(observed: dict) -> dict:
    structural_ok = observed["structural"]["structural_clean"]
    documentation_ok = observed["documentation"]["documentation_clean"]
    if structural_ok and documentation_ok:
        verdict = "pass"
        rationale = (
            f"§1 bound #8 defended at this commit. Structural: "
            f"{observed['structural']['n_python_files_scanned']} .py files scanned, "
            f"zero eirmath imports. Documentation: "
            f"{observed['documentation']['total_eirmath_mentions']} eirmath mentions, "
            f"all boundary-guarded within ±{PREDICTION['guard_search_radius_chars']} chars."
        )
    else:
        failed = []
        if not structural_ok:
            failed.append(
                f"structural-alarm: {observed['structural']['n_eirmath_imports_found']} "
                f"eirmath import(s) found in open-repo .py files: "
                f"{observed['structural']['findings'][:3]}"
            )
        if not documentation_ok:
            failed.append(
                f"documentation-alarm: "
                f"{observed['documentation']['unguarded_mentions']} of "
                f"{observed['documentation']['total_eirmath_mentions']} eirmath "
                f"mentions are unguarded within ±{PREDICTION['guard_search_radius_chars']} chars"
            )
        verdict = "fail"
        rationale = (
            f"§1 bound #8 alarm fired — reviewer attention required. "
            f"Failed: {'; '.join(failed)}. Bound #8 is uniquely load-bearing "
            f"for phase-A (open-repo-only path)."
        )
    return {
        "verdict": verdict,
        "structural": observed["structural"],
        "documentation": observed["documentation"],
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
    print(f"defending: PREREGISTRATION §1 bound #8")
    print(f"  (a) STRUCTURAL: no `import eirmath` or `from eirmath` in any open-repo .py")
    print(f"  (b) DOCUMENTATIONAL: every eirmath doc mention has boundary-guard within ±400 chars")
    print(f"  load-bearing for Eugene's phase-A directive (open-repo-only).")
    print()
    observed = run_voice_measurement()
    s = observed["structural"]
    d = observed["documentation"]
    print(f"structural: {s['n_python_files_scanned']} .py files scanned, "
          f"{s['n_eirmath_imports_found']} eirmath import(s)")
    if s["findings"]:
        for f in s["findings"][:5]:
            print(f"  ! {f['file']}: {f['match']}")
    for doc in d["documents"]:
        if not doc["doc_exists"]:
            print(f"  {doc['doc']}: NOT FOUND")
            continue
        n = len(doc["anchor_mentions"])
        ng = sum(1 for m in doc["anchor_mentions"] if m["guarded"])
        print(f"  {doc['doc']}: {n} eirmath mentions, {ng} guarded, {n-ng} unguarded")
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
