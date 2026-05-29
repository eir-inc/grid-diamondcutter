"""
voice_bound_defender_6_funding_gap_proxy_v1.py — mechanical defender for
PREREGISTRATION.md §1 honesty bound #6.

§1 bound #6 (verbatim):
    "The project will NOT claim that the funding-gap closure for earlier-stage
    alternative-energy approaches, modeled in §0, is a measurement of any
    specific company's funding pipeline. Funding-gap modeling in this repository
    operates against public bibliometric and grant-record proxies. It does not
    have visibility into private financing rounds, term sheets, or commitments
    outside of public record. Results are conditional on the proxies used and
    are not direct funding-flow measurements."

This bound is a *framing+proxy* bound: every mention of funding-gap, funding-
flow, capex, or financing-pipeline in the project's public artifacts must be
paired with the proxy-or-conditional language that distinguishes a proxy-based
estimate from a private-data measurement. The defender scans the documents and
ALARMs if any mention is unguarded.

Inverted-kill bound-defender. Lineage: PR #17 (§0.3), PR #16 (§1.5), PR #18
(§1.1), PR #21 (§1.2), PR #49 (§1.3), PR #50 (§1.4), PR #54 (§1.8). This
voice covers §1.6 — the last uncovered §1 bound.

After this lands, the §1 lattice is structurally complete: every §1 honesty
bound has at least one mechanical inverted-kill defender voice in the registry.

Authored under PREREGISTRATION.md §3.1.
"""
from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


VOICE_NAME = "bound_defender_6_funding_gap_proxy_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "registry_meta",
    "named_residual": (
        "PREREGISTRATION §1 bound #6 defense — every public-artifact mention of "
        "funding-gap, funding-flow, capex, or financing-pipeline must be paired "
        "with the proxy-or-conditional language that distinguishes a proxy-based "
        "estimate from a private-data measurement. Closes the §1 defender lattice."
    ),
    "documents_to_scan": ["PREREGISTRATION.md", "README.md"],
    "funding_anchor_terms": [
        "funding-gap",
        "funding gap",
        "funding-flow",
        "funding flow",
        "funding pipeline",
        "financing pipeline",
        "financing round",
        "term sheets",
        "private financing",
    ],
    "proxy_or_conditional_guard_phrases_any_of": [
        "public bibliometric",
        "bibliometric and grant-record proxies",
        "grant-record proxies",
        "proxies used",
        "public record",
        "outside of public record",
        "no visibility into private",
        "does not have visibility",
        "specific company",
        "not direct funding-flow measurements",
        "not a measurement of any specific company",
        "conditional on the proxies",
        "proxy-based estimate",
    ],
    "guard_search_radius_chars": 400,
    "alarm_semantics": (
        "PASS = §1 bound #6 mechanically defended (every funding-anchor mention "
        "has ≥1 proxy/conditional guard phrase within ±400 chars); FAIL = alarm "
        "(at least one funding-anchor mention is unguarded)."
    ),
}

KILL_CONDITION = {
    "metric": "n_unguarded_funding_mentions",
    "rule": (
        "FAIL (alarm) if any funding-anchor mention (funding-gap/funding gap/"
        "funding-flow/funding flow/funding pipeline/financing pipeline/financing "
        "round/term sheets/private financing) in PREREGISTRATION.md or README.md "
        "lacks ≥1 proxy/conditional guard phrase within ±400 chars."
    ),
    "rationale": (
        "Bound #6 is the easiest of all §1 bounds to cross by accident, because "
        "any future paragraph adding 'funding-gap closure' or 'capex pipeline' "
        "without the proxy guard-language silently turns a proxy-based estimate "
        "into an apparent measurement claim. Mechanizing the scan defends the "
        "boundary at every commit."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/voice_bound_defender_6_funding_gap_proxy_v1.py",
    "source_file": "examples/voices/voice_bound_defender_6_funding_gap_proxy_v1.py",
    "input_parameters": {
        "documents_to_scan": ["PREREGISTRATION.md", "README.md"],
        "guard_search_radius_chars": 400,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


def _scan_document(doc_path: Path, anchor_terms: list[str], guard_phrases: list[str], radius: int) -> dict:
    if not doc_path.exists():
        return {"doc": doc_path.name, "doc_exists": False, "anchor_mentions": []}
    text = doc_path.read_text()
    text_lower = text.lower()
    positions = set()
    for term in anchor_terms:
        for m in re.finditer(re.escape(term.lower()), text_lower):
            positions.add((m.start(), term))
    sorted_positions = sorted(positions, key=lambda x: x[0])
    anchor_mentions = []
    for pos, term in sorted_positions:
        ws = max(0, pos - radius)
        we = min(len(text), pos + radius)
        window = text[ws:we].lower()
        matched = [p for p in guard_phrases if p.lower() in window]
        cs = max(0, pos - 60)
        ce = min(len(text), pos + 60)
        snippet = text[cs:ce].replace("\n", " ").strip()
        anchor_mentions.append({
            "char_offset": pos,
            "matched_term": term,
            "context": f"...{snippet}...",
            "guard_phrases_found": matched,
            "guarded": len(matched) >= 1,
        })
    return {"doc": doc_path.name, "doc_exists": True, "anchor_mentions": anchor_mentions}


def run_voice_measurement() -> dict:
    docs = []
    for doc_name in PREDICTION["documents_to_scan"]:
        result = _scan_document(
            REPO_ROOT / doc_name,
            PREDICTION["funding_anchor_terms"],
            PREDICTION["proxy_or_conditional_guard_phrases_any_of"],
            PREDICTION["guard_search_radius_chars"],
        )
        docs.append(result)
    total = sum(len(d["anchor_mentions"]) for d in docs)
    guarded = sum(sum(1 for m in d["anchor_mentions"] if m["guarded"]) for d in docs)
    return {
        "documents": docs,
        "total_funding_mentions": total,
        "guarded_mentions": guarded,
        "unguarded_mentions": total - guarded,
    }


def compute_verdict(observed: dict) -> dict:
    n_unguarded = observed["unguarded_mentions"]
    if n_unguarded == 0:
        verdict = "pass"
        rationale = (
            f"§1 bound #6 defended at this commit: all "
            f"{observed['total_funding_mentions']} funding-anchor mention(s) across "
            f"the scanned documents have ≥1 proxy/conditional guard phrase within "
            f"±{PREDICTION['guard_search_radius_chars']} chars."
        )
    else:
        unguarded_examples = []
        for doc in observed["documents"]:
            for m in doc["anchor_mentions"]:
                if not m["guarded"]:
                    unguarded_examples.append(
                        f"{doc['doc']}@{m['char_offset']} ({m['matched_term']}): {m['context']}"
                    )
        verdict = "fail"
        rationale = (
            f"§1 bound #6 alarm: {n_unguarded} of {observed['total_funding_mentions']} "
            f"funding-anchor mentions are unguarded within "
            f"±{PREDICTION['guard_search_radius_chars']} chars. Examples: "
            f"{unguarded_examples[:3]}"
        )
    return {
        "verdict": verdict,
        "total_funding_mentions": observed["total_funding_mentions"],
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
    print(f"defending: PREREGISTRATION §1 bound #6 (funding-gap is proxy-based, not specific-company measurement)")
    print(f"  closes §1 defender lattice (after #17, #16, #18, #21, #49, #50, #54).")
    print()
    observed = run_voice_measurement()
    for doc in observed["documents"]:
        if not doc["doc_exists"]:
            print(f"  {doc['doc']}: NOT FOUND")
            continue
        n = len(doc["anchor_mentions"])
        ng = sum(1 for m in doc["anchor_mentions"] if m["guarded"])
        print(f"  {doc['doc']}: {n} funding-anchor mentions, {ng} guarded, {n-ng} unguarded")
    print(f"\ntotal: {observed['total_funding_mentions']}, guarded: {observed['guarded_mentions']}, unguarded: {observed['unguarded_mentions']}")
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
