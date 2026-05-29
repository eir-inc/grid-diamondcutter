# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
regulatory_shape_apoha_v1.py — §3.2 coupling voice (cross-substrate).

Complements miles PR #30 (regulatory_lead_time_v1, mean lead time 8.83y across
DK/DE/ES/PT/UK/IT leaders). Where #30 measured the *temporal* shape of policy →
deployment, this voice measures the *linguistic* shape of leader-policy text
itself — apoha-framed: leader-class defined by ABSENCE of hedge-markers, not
by positive content (carbon target / RES percentage).

apoha read: a regulatory text is "leader-class" iff it LACKS the following
hedge-markers (NOT-conditions). The negation defines the class.

Hedge-markers (publicly-citeable English-translation policy-text features):
  - conditional-deferral: "where feasible", "subject to", "if conditions"
  - tech-emergence-conditional: "as technology matures", "pending feasibility"
  - deadline-soft: "by approximately", "target date" (vs hard "by 2030")
  - exemption-clause: "exempting", "grandfathered", "phased exception"
  - reviewability: "subject to review", "may be amended"

Per §1 honesty bound: this is a SYNTHETIC v1 from publicly-cited policy
title/abstract excerpts. Real-policy claim requires v2-ratchet to IEA Policy
Database via PR #10 frozen-snapshot contract.

This is independent recognition lane from miles PR #30: lead-time tells WHEN,
text-shape tells WHY. Independent recognition paths against the same
publication-window goal.
"""
from __future__ import annotations
import json
import hashlib
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ===========================================================================
# §3.2 — coupling voice unit (five required fields)
# ===========================================================================

VOICE_NAME = "regulatory_shape_apoha_v1"

PREDICTION = {
    "kind": "coupling_cross_substrate",
    "substrates": [
        "leader_country_policy_text_excerpts_synthetic_v1",
        "follower_country_policy_text_excerpts_synthetic_v1",
    ],
    "named_residual": "leader_policy_text_shows_lower_hedge_density_than_follower_policy_text",
    "predicted_direction": "negative",  # leader hedge-density / follower hedge-density < 1
    "predicted_magnitude_range": [0.20, 0.80],  # ratio bounds
    "null_direction": "ratio_approximately_1_indistinguishable_or_above_1_followers_less_hedged",
    "rationale": (
        "apoha framing: a leader-policy is defined by ABSENCE of hedge-markers, "
        "not by positive carbon-target content. Leaders commit-hard; followers "
        "commit-soft with deferrals + exemptions + reviewability. If observable, "
        "the ratio leader_hedge_density / follower_hedge_density should be "
        "measurably less than 1 (between 0.20 and 0.80). Independent recognition "
        "lane to miles PR #30 lead-time temporal-shape measurement."
    ),
}

KILL_CONDITION = {
    "metric": "leader_to_follower_hedge_density_ratio",
    "rule": (
        "fail if ratio > 0.80 (apoha-distinction absent or weak); "
        "fail if ratio < 0.20 (implausible separation suggests text-selection bias); "
        "PASS only if ratio ∈ [0.20, 0.80] AND both substrates have ≥ 50 tokens to measure"
    ),
    "rationale": (
        "Single composite metric — the ratio of hedge-marker frequency between "
        "the two substrates. Upper bound rejects null. Lower bound rejects "
        "over-curation. Token-count floor prevents trivially-small-corpus reads."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/regulatory_shape_apoha_v1.py",
    "source_file": "examples/voices/regulatory_shape_apoha_v1.py",
    "input_parameters": {
        "calibration_source": "synthetic_v1_publicly_cited_policy_title_abstract_excerpts",
        "leader_countries": ["Denmark", "Germany", "Spain", "Portugal", "UK", "Italy"],
        "follower_countries": ["Poland", "Romania", "Bulgaria", "Hungary", "Czechia"],
        "hedge_marker_patterns": [
            r"\bwhere feasible\b",
            r"\bsubject to\b",
            r"\bif conditions\b",
            r"\bas technology matures\b",
            r"\bpending feasibility\b",
            r"\bby approximately\b",
            r"\btarget date\b",
            r"\bexempting\b",
            r"\bgrandfathered\b",
            r"\bphased exception\b",
            r"\bsubject to review\b",
            r"\bmay be amended\b",
            r"\bwhere possible\b",
            r"\bto the extent practicable\b",
            r"\bbest efforts\b",
        ],
        "random_seed": 530,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


# ===========================================================================
# Synthetic v1 policy-text excerpts
# ---------------------------------------------------------------------------
# These are paraphrased composites styled after publicly-cited English-translation
# excerpts from IEA Country Policy Database, EU directive summaries, and national
# energy agency communications. They are SYNTHETIC v1 for methodology smoke,
# NOT direct quotation. v2-ratchet ingests real policy text via PR #10.
# ===========================================================================

LEADER_TEXTS = {
    "Denmark": (
        "Denmark shall achieve 100 percent renewable electricity by 2030. "
        "All new onshore wind capacity must connect by 2028. The Danish Energy "
        "Agency commits to 4 gigawatts offshore wind by 2030. Fossil heating "
        "in new buildings is banned from 2025. Coal-fired generation ends 2028. "
        "The state commits 23 billion DKK to grid reinforcement by 2030."
    ),
    "Germany": (
        "Germany shall reach 80 percent renewable share by 2030. The Energiewende "
        "mandates phase-out of nuclear by 2022 and coal by 2030 latest. Onshore "
        "wind expansion shall reach 115 gigawatts by 2030. Solar PV shall reach "
        "215 gigawatts by 2030. Each federal state must designate 2 percent of "
        "land for wind. REPowerEU contribution: 40 gigawatts offshore by 2030."
    ),
    "Spain": (
        "Spain shall achieve 81 percent renewable electricity by 2030. The PNIEC "
        "binds the state to 62 gigawatts solar PV and 50 gigawatts wind by 2030. "
        "Coal generation ends 2025. The state shall invest 241 billion euros "
        "across the 2021-2030 decade. Self-consumption is removed from sun-tax. "
        "Hydrogen capacity shall reach 4 gigawatts by 2030."
    ),
    "Portugal": (
        "Portugal shall reach 80 percent renewable share by 2026. Coal generation "
        "ended in 2021. The state binds to 9.9 gigawatts solar by 2030. Offshore "
        "wind auction launches in 2024. The carbon-neutrality target is 2050 "
        "with a binding interim of minus 55 percent versus 2005 by 2030."
    ),
    "UK": (
        "The United Kingdom shall reduce emissions by 78 percent by 2035 versus "
        "1990 baseline. Offshore wind shall reach 50 gigawatts by 2030. The "
        "Contracts for Difference scheme guarantees strike-price stability over "
        "fifteen years. The Climate Change Act binds net-zero by 2050 in statute. "
        "Coal generation ends 2024."
    ),
    "Italy": (
        "Italy shall reach 65 percent renewable electricity share by 2030. The "
        "PNIEC commits 70 gigawatts new renewable capacity by 2030. Coal "
        "generation ends 2025. The state commits 222 billion euros under PNRR "
        "to the green transition. Auctions are launched annually with binding "
        "delivery dates."
    ),
}

FOLLOWER_TEXTS = {
    "Poland": (
        "Poland shall reach 23 percent renewable share by 2030 where feasible. "
        "Coal capacity may be amended subject to security-of-supply review. "
        "Offshore wind target of 5.9 gigawatts by 2030 is conditional on "
        "interconnection readiness. The state shall support coal mining "
        "communities through phased exception. New onshore wind subject to "
        "10H distance rule as technology matures. Best efforts toward decarbonization."
    ),
    "Romania": (
        "Romania shall pursue 30.7 percent renewable share by 2030 where possible. "
        "Existing coal generation is grandfathered through 2032 subject to review. "
        "Offshore wind framework is pending feasibility studies. New solar PV "
        "above 1 megawatt subject to grid-connection capacity assessment. The "
        "state may support fossil-fuel transition through phased exception. "
        "Target date for full renewable integration is by approximately 2030."
    ),
    "Bulgaria": (
        "Bulgaria shall aim for 27 percent renewable share by 2030 where feasible. "
        "Coal generation may continue subject to review of energy security. "
        "Offshore wind is pending feasibility. Lignite-fired generation is "
        "grandfathered through 2038. New renewable connections subject to grid "
        "capacity assessment. Best efforts to phase out coal as technology matures."
    ),
    "Hungary": (
        "Hungary shall pursue 21 percent renewable share by 2030 where conditions "
        "permit. Nuclear expansion at Paks II is the primary decarbonization vector. "
        "Coal-fired Matra plant phase-out by approximately 2025 subject to review. "
        "Solar PV target of 6 gigawatts by 2030 subject to grid-connection "
        "feasibility. Best efforts toward EU climate targets."
    ),
    "Czechia": (
        "Czechia shall pursue 22 percent renewable share by 2030 to the extent "
        "practicable. Coal phase-out by 2033 subject to security review. "
        "New nuclear at Dukovany is the primary decarbonization path. Onshore "
        "wind subject to distance regulations as technology matures. Best efforts "
        "to reach EU 2030 target where feasible."
    ),
}


# ===========================================================================
# Voice implementation
# ===========================================================================

def measure_hedge_density(text: str, patterns: list[str]) -> tuple[int, int]:
    """Return (hedge_count, total_words) for a text."""
    text_lower = text.lower()
    hedge_count = 0
    for pat in patterns:
        hedge_count += len(re.findall(pat, text_lower))
    total_words = len(text_lower.split())
    return hedge_count, total_words


def hedge_density(corpus: dict, patterns: list[str]) -> dict:
    """Aggregate hedge density across a corpus dict."""
    total_hedges = 0
    total_words = 0
    per_country = {}
    for country, text in corpus.items():
        h, w = measure_hedge_density(text, patterns)
        per_country[country] = {
            "hedge_count": h,
            "total_words": w,
            "hedge_per_1000_words": (1000.0 * h / w) if w > 0 else 0.0,
        }
        total_hedges += h
        total_words += w
    aggregate_density = (1000.0 * total_hedges / total_words) if total_words > 0 else 0.0
    return {
        "per_country": per_country,
        "total_hedges": total_hedges,
        "total_words": total_words,
        "hedge_per_1000_words": aggregate_density,
    }


def run_voice() -> dict:
    patterns = RUN_PROTOCOL["input_parameters"]["hedge_marker_patterns"]
    leader_result = hedge_density(LEADER_TEXTS, patterns)
    follower_result = hedge_density(FOLLOWER_TEXTS, patterns)
    leader_density = leader_result["hedge_per_1000_words"]
    follower_density = follower_result["hedge_per_1000_words"]
    ratio = (leader_density / follower_density) if follower_density > 0 else float("inf")
    return {
        "leader": leader_result,
        "follower": follower_result,
        "leader_hedge_density_per_1000_words": float(leader_density),
        "follower_hedge_density_per_1000_words": float(follower_density),
        "leader_to_follower_hedge_density_ratio": float(ratio),
    }


# ===========================================================================
# Field 5: verdict
# ===========================================================================

def compute_verdict(run_output: dict) -> dict:
    ratio = run_output["leader_to_follower_hedge_density_ratio"]
    leader_words = run_output["leader"]["total_words"]
    follower_words = run_output["follower"]["total_words"]
    ratio_lo, ratio_hi = PREDICTION["predicted_magnitude_range"]
    fails = []

    if leader_words < 50 or follower_words < 50:
        fails.append(
            f"corpus floor not met: leader={leader_words} words, follower={follower_words} words "
            f"(both must be ≥ 50)"
        )
    if ratio > ratio_hi:
        fails.append(
            f"ratio {ratio:.3f} > {ratio_hi:.2f} (apoha distinction absent or weak — "
            f"leaders not measurably less hedged than followers)"
        )
    if ratio < ratio_lo:
        fails.append(
            f"ratio {ratio:.3f} < {ratio_lo:.2f} (implausible separation suggests "
            f"text-selection bias in synthetic excerpts)"
        )

    if not fails:
        verdict = "pass"
        rationale = (
            f"leader/follower hedge-density ratio {ratio:.3f} ∈ [{ratio_lo:.2f}, {ratio_hi:.2f}]. "
            f"leader corpus {leader_words} words, follower corpus {follower_words} words "
            f"(both ≥ 50 floor). apoha-distinction observable: leader-class policy text "
            f"is measurably LESS hedged than follower-class. Independent recognition lane "
            f"to miles PR #30 lead-time finding. SYNTHETIC v1 only; v2-ratchet to IEA "
            f"Policy Database required for any external real-policy claim."
        )
    else:
        verdict = "fail"
        rationale = "Voice enters the null-voice ledger per §3.4. Failures: " + " ; ".join(fails)

    return {
        "verdict": verdict,
        "leader_to_follower_hedge_density_ratio": ratio,
        "leader_hedge_density_per_1000_words": run_output["leader_hedge_density_per_1000_words"],
        "follower_hedge_density_per_1000_words": run_output["follower_hedge_density_per_1000_words"],
        "leader_words": leader_words,
        "follower_words": follower_words,
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
    print(f"predicted:    ratio ∈ {PREDICTION['predicted_magnitude_range']} (leaders LESS hedged)")
    print(f"kill rule:    {KILL_CONDITION['rule']}")
    print(f"run:          {RUN_PROTOCOL['entry_point']}")
    print()
    print("running regulatory_shape_apoha hedge-density measurement...")
    out = run_voice()
    print(f"  leader corpus: {out['leader']['total_words']} words, {out['leader']['total_hedges']} hedges")
    print(f"  follower corpus: {out['follower']['total_words']} words, {out['follower']['total_hedges']} hedges")
    print(f"  leader hedge density:    {out['leader_hedge_density_per_1000_words']:.3f} per 1000 words")
    print(f"  follower hedge density:  {out['follower_hedge_density_per_1000_words']:.3f} per 1000 words")
    print(f"  ratio (leader/follower): {out['leader_to_follower_hedge_density_ratio']:.4f}")
    print()
    print("  per-country leader breakdown:")
    for c, r in out["leader"]["per_country"].items():
        print(f"    {c:12s}  {r['hedge_per_1000_words']:6.2f} per 1k  ({r['hedge_count']} hedges in {r['total_words']} words)")
    print("  per-country follower breakdown:")
    for c, r in out["follower"]["per_country"].items():
        print(f"    {c:12s}  {r['hedge_per_1000_words']:6.2f} per 1k  ({r['hedge_count']} hedges in {r['total_words']} words)")
    print()
    verdict = compute_verdict(out)
    print(f"  verdict: {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    print()

    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, out, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
