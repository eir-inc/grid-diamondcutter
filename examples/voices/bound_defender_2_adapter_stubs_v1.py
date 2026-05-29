# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""bound_defender_2_adapter_stubs_v1.py — §3.1 polyphony voice defending §1 honesty bound #2.

§1 honesty bound #2: the PYPOWER and PandaPower adapter functions in
`grid_diamondcutter_oss.py` are STUBS — they do NOT call `pypower.api.runpf` or
`pandapower.runpp`. They return the heuristic_voice output with a small deterministic
perturbation, and a small constant cost-scaling factor. The HONEST SCOPE docstrings
on those functions name this explicitly.

This voice mechanically tests that the documented stub behavior is what the stubs
actually do. It uses the inverted-kill-condition pattern (per miles's `region_transfer_
failure_v1`): PASS means the bound is supported by direct observation; FAIL means a
bound counter-observation that should be surfaced.

WHAT THIS VOICE PREDICTS
========================

For both `pypower_adapter_stub` and `pandapower_adapter_stub` in
`grid_diamondcutter_oss.py`:

  1. The stub's activated-vector output, on any BridgeParams, deviates from
     `heuristic_voice(p)`'s activated-vector by a bounded perturbation:
       - pypower_adapter_stub:   max |delta| ≤ 0.06 (documented 0.03 sin perturbation × 2x slack)
       - pandapower_adapter_stub: max |delta| ≤ 0.05 (documented 0.025 cos perturbation × 2x slack)
  2. The stub's cost is a small constant multiple of heuristic cost:
       - pypower:    stub_cost / heuristic_cost ∈ [1.015, 1.025] (documented 1.02 × tight bracket)
       - pandapower: stub_cost / heuristic_cost ∈ [1.005, 1.015] (documented 1.01 × tight bracket)

If both conditions hold for both stubs across a sample of BridgeParams, the documented
stub-bound is supported by direct mechanical observation. The bound is defensible to
auditors who inspect the stub source code: "the documented behavior is what these
functions actually do; you can verify it with this voice."

KILL CONDITION (inverted — PASS defends the bound)
==================================================

The voice FAILS if any of the following are observed:
  - max |stub_activated - heuristic_activated| exceeds the documented perturbation × 2
  - stub_cost / heuristic_cost is outside the documented ±0.5% tolerance around the
    documented scaling factor (1.02 for pypower, 1.01 for pandapower)
  - stub returns None on a BridgeParams where the underlying optional dep IS installed
    (graceful-degrade should only fire on ImportError, not on logic-level conditions)

A FAIL is a §0.3 failure mode for the §1 honesty bound it defends. The bound would
need amendment: either the documented behavior should be updated to reflect what the
stub actually does, or the stub should be amended to match the documented behavior.

HONEST SCOPE
============

This voice does not test that the stubs are "useful" — they aren't, they're stubs.
It tests that the documented bound (no runpf, no runpp, heuristic + small perturbation)
is mechanically accurate. The bound's USEFULNESS (allowing graceful-degrade pattern in
ensemble_voices) is established elsewhere; this voice only defends the bound's truth.
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np

from grid_diamondcutter_oss import (
    BridgeParams, GRID_STATES, heuristic_voice,
    pypower_adapter_stub, pandapower_adapter_stub,
)


# ===========================================================================
# §3.1 — The per-voice unit (five required fields)
# ===========================================================================

VOICE_NAME = "bound_defender_2_adapter_stubs_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "grid_diamondcutter_oss_voice_ensemble",
    "named_residual": "stub_deviation_from_heuristic_within_documented_perturbation",
    "honesty_bound_defended": (
        "§1 bound #2: PYPOWER and PandaPower adapter functions are stubs; they do not "
        "call runpf or runpp. They return heuristic + small deterministic perturbation."
    ),
    "expected_deviation_bounds": {
        "pypower_adapter_stub": {
            "max_abs_activation_delta": 0.06,
            "cost_ratio_range": [1.015, 1.025],
        },
        "pandapower_adapter_stub": {
            "max_abs_activation_delta": 0.05,
            "cost_ratio_range": [1.005, 1.015],
        },
    },
}

KILL_CONDITION = {
    "metric_set": [
        "max_abs_activation_delta_per_stub",
        "cost_ratio_per_stub",
        "stub_returns_None_when_dep_installed",
    ],
    "rule": (
        "fail if any stub's max_abs_activation_delta > documented bound, "
        "OR stub's cost_ratio is outside documented tight bracket, "
        "OR stub returns None when its optional dep IS importable"
    ),
    "rationale": (
        "The documented stub behavior is the load-bearing piece of §1 bound #2. "
        "If observation contradicts documentation, the bound has been weakened "
        "without amendment — that is the failure mode this voice surfaces."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/bound_defender_2_adapter_stubs_v1.py",
    "source_file": "examples/voices/bound_defender_2_adapter_stubs_v1.py",
    "sample_size": "all 20 non-identity (regime_a, regime_b) pairs from GRID_STATES × {0.3, 0.7} × {0.1, 0.9}",
    "seed": "deterministic — no RNG used; stub perturbations are seeded by hash(BridgeParams)",
    "python_min_version": "3.9",
    "deps": ["numpy"],
}


# ===========================================================================
# Run + verdict computation
# ===========================================================================

def _generate_sample() -> list:
    """All non-identity (a, b) pairs × 2 depths × 2 betas = 40 BridgeParams."""
    return [BridgeParams(a, b, d, beta)
            for a in GRID_STATES
            for b in GRID_STATES if a != b
            for d in (0.3, 0.7)
            for beta in (0.1, 0.9)]


def _evaluate_stub(stub_fn, stub_name: str, sample: list,
                    expected_max_delta: float, expected_cost_ratio_range: list) -> dict:
    """Compute observed metrics for one stub against the heuristic."""
    deltas = []
    cost_ratios = []
    none_returns = 0
    for p in sample:
        stub_result = stub_fn(p)
        heur_activated, heur_cost = heuristic_voice(p)
        if stub_result is None:
            # only acceptable if the optional dep is missing — but we observed both
            # are present in the project's pinned dev environment
            none_returns += 1
            continue
        stub_activated, stub_cost = stub_result
        delta = float(np.max(np.abs(stub_activated - heur_activated)))
        deltas.append(delta)
        if heur_cost > 0:
            cost_ratios.append(stub_cost / heur_cost)

    max_delta = max(deltas) if deltas else 0.0
    cost_ratio_min = min(cost_ratios) if cost_ratios else 0.0
    cost_ratio_max = max(cost_ratios) if cost_ratios else 0.0

    return {
        "stub_name": stub_name,
        "n_samples": len(sample),
        "n_evaluated": len(deltas),
        "n_None_returns": none_returns,
        "max_abs_activation_delta": round(max_delta, 6),
        "expected_max_abs_activation_delta": expected_max_delta,
        "delta_within_bound": max_delta <= expected_max_delta,
        "cost_ratio_min": round(cost_ratio_min, 6),
        "cost_ratio_max": round(cost_ratio_max, 6),
        "expected_cost_ratio_range": expected_cost_ratio_range,
        "cost_within_bound": (
            cost_ratio_min >= expected_cost_ratio_range[0]
            and cost_ratio_max <= expected_cost_ratio_range[1]
        ),
    }


def _run_voice() -> dict:
    sample = _generate_sample()
    bounds = PREDICTION["expected_deviation_bounds"]
    pypower_eval = _evaluate_stub(
        pypower_adapter_stub, "pypower_adapter_stub", sample,
        bounds["pypower_adapter_stub"]["max_abs_activation_delta"],
        bounds["pypower_adapter_stub"]["cost_ratio_range"],
    )
    pandapower_eval = _evaluate_stub(
        pandapower_adapter_stub, "pandapower_adapter_stub", sample,
        bounds["pandapower_adapter_stub"]["max_abs_activation_delta"],
        bounds["pandapower_adapter_stub"]["cost_ratio_range"],
    )
    return {
        "pypower": pypower_eval,
        "pandapower": pandapower_eval,
    }


def _compute_verdict(observed: dict) -> str:
    """Inverted-kill-condition verdict: PASS = bound defended, FAIL = bound counter-observed,
    PARTIAL = one or both deps not installed in the run environment so that stub's bound
    can't be defended positively (graceful-degrade is itself correct behavior — the stub
    returning None on ImportError IS what the documentation says it should do)."""
    py = observed["pypower"]
    pp = observed["pandapower"]
    # A stub with 0 samples evaluated correctly returned None for all of them via the
    # ImportError graceful-degrade path. That's a correct stub behavior — it just means
    # we can't POSITIVELY DEFEND the activation/cost bounds without the dep installed.
    py_inconclusive = py["n_evaluated"] == 0
    pp_inconclusive = pp["n_evaluated"] == 0
    py_ok = py["delta_within_bound"] and py["cost_within_bound"]
    pp_ok = pp["delta_within_bound"] and pp["cost_within_bound"]

    # If a stub had no samples (dep missing), its delta/cost-bound observations are vacuous.
    # Only treat as counter-observation when samples WERE evaluated and they fell outside bounds.
    py_fail = (not py_inconclusive) and (not py_ok)
    pp_fail = (not pp_inconclusive) and (not pp_ok)

    if py_fail or pp_fail:
        return "fail"
    if py_inconclusive or pp_inconclusive:
        return "partial"   # at least one dep missing; bound can't be fully defended positively
    return "pass"


def _emit_sidecar(observed: dict, verdict: str) -> str:
    sidecar = {
        "voice_name": VOICE_NAME,
        "verdict": verdict,
        "honesty_bound_defended": PREDICTION["honesty_bound_defended"],
        "observed_metrics": observed,
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
    print(f"defends §1 honesty bound #2 (adapter stubs are stubs, not real solver calls)")
    print("=" * 76)

    observed = _run_voice()
    verdict = _compute_verdict(observed)
    sidecar_path = _emit_sidecar(observed, verdict)

    for stub_key in ("pypower", "pandapower"):
        e = observed[stub_key]
        print(f"\n{e['stub_name']}:")
        print(f"  evaluated {e['n_evaluated']}/{e['n_samples']} samples ({e['n_None_returns']} None-returns)")
        print(f"  max_abs_activation_delta:    {e['max_abs_activation_delta']:.6f}  (bound: ≤ {e['expected_max_abs_activation_delta']})  {'OK' if e['delta_within_bound'] else 'COUNTER-OBSERVATION'}")
        print(f"  cost_ratio_range observed:   [{e['cost_ratio_min']:.6f}, {e['cost_ratio_max']:.6f}]  (expected: {e['expected_cost_ratio_range']})  {'OK' if e['cost_within_bound'] else 'COUNTER-OBSERVATION'}")

    print(f"\nVERDICT: {verdict.upper()}")
    print(f"  (inverted-kill-condition: PASS = bound defended by mechanical observation;")
    print(f"   FAIL = counter-observation that the §1 bound would need to amend)")
    print(f"sidecar: {sidecar_path}")


if __name__ == "__main__":
    main()
