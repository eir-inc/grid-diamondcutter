"""
voice_bound_defender_4_cascade_not_prediction_v1.py — mechanical defender for
PREREGISTRATION.md §1 honesty bound #4.

§1 bound #4 (paraphrased):
    The project will NOT claim that a cascade result produced by the methodology
    — the threshold-class cascade investigated in §0, the qualitative trajectory
    recovered in §4's validation pass, or any aggregate across voices — is a
    prediction of what the real economy or the real grid will do. Cascade results
    are conditional findings: under stated voices, under stated assumptions,
    under stated substrate parameters, the methodology returns X.

This bound is a *framing* bound — easy to cross by accident in any artifact that
mentions "cascade" without the conditional guard-language. The defender scans
the project's public artifacts (PREREGISTRATION.md, README.md) for "cascade"
mentions and verifies that each mention is paired with at least one conditional-
guard phrase within a local window. ALARM fires if any cascade mention is
unguarded — reviewer attention required.

Inverted-kill pattern. Lineage: PR #17 (§0.3), PR #16 (§1.5), PR #18 (§1.1),
PR #21 (§1.2), PR #49 (§1.3). This voice covers §1.4.

Authored under PREREGISTRATION.md §3.1.
"""
from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


VOICE_NAME = "bound_defender_4_cascade_not_prediction_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "registry_meta",
    "named_residual": (
        "PREREGISTRATION §1 bound #4 defense — every 'cascade' mention in the "
        "project's public-facing artifacts (PREREGISTRATION.md, README.md) must "
        "appear within a local window of at least one conditional-guard phrase "
        "('conditional', 'under stated', 'under modeling assumptions', 'not a "
        "prediction', 'not a forecast', 'not a measurement of the real grid'). "
        "Otherwise the bound is silently crossable."
    ),
    "documents_to_scan": ["PREREGISTRATION.md", "README.md"],
    "cascade_anchor_terms": ["cascade", "Cascade"],
    "guard_phrases_any_of": [
        "conditional",
        "under stated",
        "under modeling assumptions",
        "modeling assumptions",
        "not a prediction",
        "not a forecast",
        "not a measurement of the real grid",
        "what the real economy or the real grid will do",
        "without a registered voice that explicitly tests the forecasting claim",
        "stated voices",
        "stated assumptions",
        "stated substrate parameters",
    ],
    "guard_search_radius_chars": 600,
    "alarm_semantics": (
        "PASS = §1 bound #4 mechanically defended (every cascade mention has ≥1 "
        "guard phrase within ±600 chars); FAIL = alarm (≥1 cascade mention is "
        "unguarded in the scanned artifacts)."
    ),
}

KILL_CONDITION = {
    "metric": "n_unguarded_cascade_mentions",
    "rule": (
        "FAIL (alarm) if any cascade mention in PREREGISTRATION.md or README.md "
        "lacks at least one guard phrase within ±600 chars. PASS iff every cascade "
        "mention is guarded."
    ),
    "rationale": (
        "Bound #4 is a framing bound — it is the easiest to cross by accident, "
        "because any future edit can add the word 'cascade' without the conditional-"
        "finding language. Reviewers cannot mentally scan every public artifact at "
        "every commit. Mechanizing the scan as a voice means the bound is defended "
        "at every commit by inspection of the same artifacts an external reader sees."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/voice_bound_defender_4_cascade_not_prediction_v1.py",
    "source_file": "examples/voices/voice_bound_defender_4_cascade_not_prediction_v1.py",
    "input_parameters": {
        "documents_to_scan": ["PREREGISTRATION.md", "README.md"],
        "cascade_anchor_terms_case_sensitive": False,
        "guard_search_radius_chars": 600,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
        "filesystem_dependency": "PREREGISTRATION.md + README.md at repo root",
    },
}


def _scan_document(
    doc_path: Path,
    anchor_terms: list[str],
    guard_phrases: list[str],
    radius: int,
) -> dict:
    if not doc_path.exists():
        return {
            "doc": str(doc_path.name),
            "doc_exists": False,
            "anchor_mentions": [],
        }
    text = doc_path.read_text()
    text_lower = text.lower()

    # Find every anchor occurrence (case-insensitive)
    anchor_positions: list[int] = []
    for term in anchor_terms:
        for m in re.finditer(re.escape(term.lower()), text_lower):
            anchor_positions.append(m.start())
    anchor_positions = sorted(set(anchor_positions))

    anchor_mentions = []
    for pos in anchor_positions:
        window_start = max(0, pos - radius)
        window_end = min(len(text), pos + radius)
        window = text[window_start:window_end].lower()
        matched_phrases = [p for p in guard_phrases if p.lower() in window]
        # extract a short context snippet for reporting
        context_start = max(0, pos - 60)
        context_end = min(len(text), pos + 60)
        snippet = text[context_start:context_end].replace("\n", " ").strip()
        anchor_mentions.append(
            {
                "char_offset": pos,
                "context": f"...{snippet}...",
                "guard_phrases_found_in_window": matched_phrases,
                "guarded": len(matched_phrases) >= 1,
            }
        )
    return {
        "doc": str(doc_path.name),
        "doc_exists": True,
        "anchor_mentions": anchor_mentions,
    }


def run_voice_measurement() -> dict:
    docs = []
    for doc_name in PREDICTION["documents_to_scan"]:
        doc_path = REPO_ROOT / doc_name
        result = _scan_document(
            doc_path,
            PREDICTION["cascade_anchor_terms"],
            PREDICTION["guard_phrases_any_of"],
            PREDICTION["guard_search_radius_chars"],
        )
        docs.append(result)

    total_mentions = sum(len(d["anchor_mentions"]) for d in docs)
    guarded_mentions = sum(
        sum(1 for m in d["anchor_mentions"] if m["guarded"]) for d in docs
    )
    unguarded = total_mentions - guarded_mentions

    return {
        "documents": docs,
        "total_cascade_mentions": total_mentions,
        "guarded_mentions": guarded_mentions,
        "unguarded_mentions": unguarded,
    }


def compute_verdict(observed: dict) -> dict:
    n_unguarded = observed["unguarded_mentions"]
    if n_unguarded == 0:
        verdict = "pass"
        rationale = (
            f"§1 bound #4 defended at this commit: all "
            f"{observed['total_cascade_mentions']} cascade mentions across "
            f"{len([d for d in observed['documents'] if d['doc_exists']])} scanned "
            f"documents have ≥1 guard phrase within ±{PREDICTION['guard_search_radius_chars']} "
            f"chars."
        )
    else:
        # list the unguarded ones explicitly
        unguarded_examples = []
        for doc in observed["documents"]:
            for m in doc["anchor_mentions"]:
                if not m["guarded"]:
                    unguarded_examples.append(f"{doc['doc']}@{m['char_offset']}: {m['context']}")
        verdict = "fail"
        rationale = (
            f"§1 bound #4 alarm: {n_unguarded} of {observed['total_cascade_mentions']} "
            f"cascade mentions are unguarded (no conditional-finding language within "
            f"±{PREDICTION['guard_search_radius_chars']} chars). Reviewer attention required. "
            f"Examples: {unguarded_examples[:3]}"
        )
    return {
        "verdict": verdict,
        "total_cascade_mentions": observed["total_cascade_mentions"],
        "guarded_mentions": observed["guarded_mentions"],
        "unguarded_mentions": observed["unguarded_mentions"],
        "documents": observed["documents"],
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
    print(f"defending: PREREGISTRATION §1 bound #4")
    print(f"  every 'cascade' mention in public artifacts must have a conditional-")
    print(f"  finding guard phrase within ±{PREDICTION['guard_search_radius_chars']} chars.")
    print()
    observed = run_voice_measurement()
    for doc in observed["documents"]:
        if not doc["doc_exists"]:
            print(f"  {doc['doc']}: NOT FOUND (skip)")
            continue
        n = len(doc["anchor_mentions"])
        n_guarded = sum(1 for m in doc["anchor_mentions"] if m["guarded"])
        print(f"  {doc['doc']}: {n} cascade mentions, {n_guarded} guarded, {n - n_guarded} unguarded")
    print()
    print(
        f"total cascade mentions: {observed['total_cascade_mentions']}, "
        f"guarded: {observed['guarded_mentions']}, "
        f"unguarded: {observed['unguarded_mentions']}"
    )
    verdict = compute_verdict(observed)
    print(f"verdict: {verdict['verdict']}")
    print(f"rationale: {verdict['rationale'][:400]}")

    sidecar_path = Path(__file__).parent / f"{VOICE_NAME}.sidecar.json"
    sha = emit_sidecar(verdict, sidecar_path)
    print(f"\nsidecar emitted: {sidecar_path.name}")
    print(f"sha256_pre_verdict: {sha}")
    return verdict


if __name__ == "__main__":
    main()
