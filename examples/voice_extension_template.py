# Copyright 2026 Eir Inc
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""examples/voice_extension_template.py — drop-in starter for adding a new VOICE to the meta-sim.

This file is your starting point. Copy it, rename it, fill in the YOUR_VOICE function below,
and your voice plugs into the meta-sim's chorus alongside the heuristic / pypower / pandapower
voices. The substrate-plugin contract handles everything else — closure_walk + route_adaptive
+ axis_attribution all run unchanged on a meta-sim with your voice in it.

Three patterns covered here (pick the one that matches your situation):

  PATTERN A — wrap an existing grid simulator (PYPOWER / OpenDSS / GridLAB-D / MATPOWER).
  PATTERN B — implement a heuristic from a paper / dataset / your own physics.
  PATTERN C — wrap a fitted model (e.g. a neural-net regressor your team trained).

All three return the same shape — a tuple `(activated_vector, cost)` — so the meta-sim sees
them uniformly.

To run with your voice active:
    1. Save this file as `my_voice.py` somewhere on your PYTHONPATH (or the same dir).
    2. Modify the YOUR_VOICE function below to return your voice's response.
    3. Run `python my_voice.py` — the self-demo at the bottom validates your voice works.
    4. Open a PR in `grid-diamondcutter-oss` adding your voice to the VOICES list in
       `grid_diamondcutter_oss.py`.

NO AI ASSISTANCE REQUIRED — this file is meant to be readable by any Python engineer.
WITH AI (Claude / GPT / Copilot), it's also designed to be the kind of well-shaped scaffold
an LLM can fill in correctly given a description of your simulator's API.
"""
from __future__ import annotations
from typing import Optional
import sys, os

# allow running this file from anywhere — adjust path to find grid_diamondcutter_oss
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

try:
    import numpy as np
except ImportError:
    raise SystemExit("numpy required. install with: pip install numpy")

from grid_diamondcutter_oss import (
    BridgeParams, GRID_STATES, CONTROLS, heuristic_voice,
)


# ===========================================================================
# YOUR VOICE — fill this in.
# ===========================================================================

def YOUR_VOICE(p: BridgeParams) -> Optional[tuple]:
    """Replace the body of this function with your voice's response.

    Required: return a tuple (activated, cost), where:
      - activated:  np.ndarray of shape (len(CONTROLS),) — your voice's response strength
                    across the 5 control strategies. Doesn't need to sum to 1; the meta-sim
                    will normalize. Negative values are clamped during ensemble averaging.
      - cost:       float — the computational / economic cost of running this response.
                    Use any unit you like; the meta-sim averages costs across voices.

    Optional graceful-degrade pattern: if your voice depends on an external library
    (PYPOWER, OpenDSS, a trained model), return None when the dependency isn't available.
    The meta-sim drops the voice silently and continues with whatever voices ARE available.

    The BridgeParams object you receive has four fields:
      p.regime_a:           str (one of GRID_STATES) — the "from" grid state
      p.regime_b:           str (one of GRID_STATES) — the "to" grid state
      p.redevelop_depth:    float in [0, 1] — how deep the regime transition probes
      p.beta:               float in [0, 1] — blend coefficient between a and b
    """
    # ------------------------------------------------------------------------
    # PATTERN A — wrap an existing simulator (commented; uncomment to use)
    # ------------------------------------------------------------------------
    # try:
    #     import your_simulator  # noqa: F401
    # except ImportError:
    #     return None
    # # Map BridgeParams to your simulator's inputs:
    # scenario = your_simulator.build_scenario(
    #     from_state=p.regime_a, to_state=p.regime_b,
    #     depth=p.redevelop_depth, blend=p.beta,
    # )
    # result = your_simulator.run(scenario)
    # activated = np.array([result.voltage_response, result.frequency_response,
    #                       result.breaker_response, result.load_shed_response,
    #                       result.dispatch_response])
    # cost = result.computation_seconds + result.simulated_economic_cost
    # return activated, cost

    # ------------------------------------------------------------------------
    # PATTERN B — heuristic from your own physics / paper / dataset
    # ------------------------------------------------------------------------
    # Example: a voice that captures "thermal-loading-dominated" grid response.
    # For the purposes of this template, we just shape the heuristic voice's
    # output slightly differently — REPLACE with your real heuristic.
    activated, cost = heuristic_voice(p)
    thermal_bias = np.array([0.0, 0.0, 0.0, 0.2, 0.0])   # emphasize load_shed
    activated = activated + thermal_bias
    if activated.sum() > 0:
        activated = activated / activated.sum()
    return activated, cost * 1.1   # thermal voice slightly more expensive than heuristic

    # ------------------------------------------------------------------------
    # PATTERN C — wrapped fitted model (commented; uncomment to use)
    # ------------------------------------------------------------------------
    # try:
    #     import joblib
    #     model = joblib.load("/path/to/your/grid_response_model.pkl")
    # except (ImportError, FileNotFoundError):
    #     return None
    # feature_vector = encode_bridge_params(p)   # implement this for your model
    # activated = model.predict(feature_vector.reshape(1, -1))[0]
    # cost = float(model.predict_cost(feature_vector.reshape(1, -1))[0])
    # return activated, cost


# ===========================================================================
# Voice metadata — used by the contributor attribution ledger.
# ===========================================================================

VOICE_METADATA = {
    "voice_id":    "your_voice_handle",         # short, unique, kebab-case
    "author":      "your_name_or_github_handle",
    "email":       "your_email@somewhere.example",
    "domain":      "power_grid",                # or "audio_topology", "chip_sim", etc.
    "layer":       "thermal",                   # e.g. thermal / market / contingency / steady_state
    "timescale":   "mid",                       # slow / mid / fast (for cross-band coupling map)
    "data_source": "heuristic + IEEE 738 thermal loading model",
    "license":     "Apache-2.0",
    "version":     "0.1.0",
    "description": "ONE SENTENCE on what physics/aspect this voice captures.",
}


# ===========================================================================
# Self-demo — validates your voice works before you open a PR.
# ===========================================================================

def self_demo():
    print("=" * 72)
    print(f"Voice self-demo: {VOICE_METADATA['voice_id']}")
    print("=" * 72)

    test_recipes = [
        BridgeParams("steady",      "overload",    0.3, 0.5),
        BridgeParams("overload",    "fault",       0.6, 0.5),
        BridgeParams("fault",       "restoration", 0.5, 0.3),
        BridgeParams("restoration", "cascade",     0.7, 0.5),
        BridgeParams("cascade",     "steady",      0.5, 0.7),
    ]

    print(f"\nVoice metadata:")
    for k, v in VOICE_METADATA.items():
        print(f"  {k:14s}  {v}")

    print(f"\nTesting voice on {len(test_recipes)} grid-state transitions:")
    print(f"  {'transition':32s}  {'response shape':16s}  {'cost':>8s}")
    print(f"  {'-'*32}  {'-'*16}  {'-'*8}")
    for p in test_recipes:
        result = YOUR_VOICE(p)
        if result is None:
            print(f"  {p.regime_a:14s} → {p.regime_b:14s}  voice unavailable (dep missing)")
            continue
        activated, cost = result
        transition = f"{p.regime_a} → {p.regime_b}"
        shape_str = f"({len(activated)},) sum={activated.sum():.2f}"
        print(f"  {transition:32s}  {shape_str:16s}  {cost:>8.2f}")

    print(f"\nValidation checklist (everything must say PASS):")

    def check(name, ok):
        print(f"  [{('PASS' if ok else 'FAIL')}] {name}")
        return ok

    p = test_recipes[0]
    result = YOUR_VOICE(p)
    all_ok = True
    all_ok &= check("voice returns a non-None result on a valid input",
                    result is not None)
    if result is not None:
        activated, cost = result
        all_ok &= check(f"activated vector has length {len(CONTROLS)}",
                        len(activated) == len(CONTROLS))
        all_ok &= check("activated vector is np.ndarray",
                        isinstance(activated, np.ndarray))
        all_ok &= check("cost is a float / int",
                        isinstance(cost, (int, float)))
        all_ok &= check("cost is non-negative", cost >= 0)
        all_ok &= check("voice_id is set in metadata (not the default placeholder)",
                        VOICE_METADATA["voice_id"] != "your_voice_handle")

    print()
    if all_ok:
        print("All checks PASS. Your voice is ready to PR.")
        print("Next: add it to the VOICES list in grid_diamondcutter_oss.py:")
        print(f'      VOICES.append(("{VOICE_METADATA["voice_id"]}", YOUR_VOICE))')
    else:
        print("Some checks failed. Fix the voice + re-run before opening a PR.")


if __name__ == "__main__":
    self_demo()
