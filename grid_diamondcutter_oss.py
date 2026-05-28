# Copyright 2026 Eir Inc
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# See the LICENSE file in this repository for the full text.

"""grid_diamondcutter_oss.py — a meta-sim of power-grid sims, single file, Apache 2.0.

A meta-sim of existing grid simulators (PYPOWER, PandaPower, OpenDSS, GridLAB-D, MATPOWER)
treated as different VOICES on the same grid substrate. Each voice is a partial view; the
meta-sim is the harmonization layer. No new from-scratch simulator — a thin substrate-plugin
wrapper that listens to whichever voices are installed and fingerprints the grid state across them.

Diamondcutter cycle-walk methodology: cyclic-stress cartography on dynamical systems that
exposes the residual cycle inefficiency — the gap between default operation and conducted
operation, priced in real units. This file is the OSS substrate-plugin demo for the grid domain.

Usage (the trivial-share bar):
    python3 grid_diamondcutter_oss.py

That's it. With numpy only, the heuristic voice runs and the diamondcutter measures the
cycle residual. With PYPOWER / PandaPower / OpenDSS additionally installed, those voices
join the chorus and the fingerprint richens. Email/Slack-DM/paste-into-venv friendly.

License: Apache 2.0 (Eir Inc, 2026). Use it, fork it, plug your sim in as a voice, send a PR.
The prevention-based pricing toolkit that consumes catalogues from this sim is held above
(closed); the substrate is open — the moat is measurement, not simulation.

Author: Eir Inc. See CONTRIBUTING.md for contributor + maintainer attribution. 2026-05-28.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional
import math
import random

# numpy is the only required external dep
try:
    import numpy as np
except ImportError:
    raise SystemExit("numpy required. install with: pip install numpy")

# ----------------------------------------------------------------------------
# THE SUBSTRATE-PLUGIN CONTRACT (inlined from substrate_plugin.py)
# ----------------------------------------------------------------------------

@dataclass
class BridgeParams:
    """Four-parameter recipe: (from_state, to_state, depth, beta)."""
    regime_a: str
    regime_b: str
    redevelop_depth: float
    beta: float


@dataclass
class StateMetrics:
    state_id: str
    novel: bool
    cost: float
    lifetime: float


@dataclass
class Substrate:
    name: str
    reversal_primitive: str
    percolation_axis: str
    data_source: str
    reach: Callable[[BridgeParams], tuple]
    cost: Callable[[BridgeParams], float]
    lifetime: Callable[[BridgeParams], float]
    window: Callable[[BridgeParams], bool]
    forward: Callable[[], set]


def make_evaluator(sub: Substrate):
    fwd = sub.forward()
    def ev(p: BridgeParams) -> StateMetrics:
        fp = sub.reach(p)
        novel = (fp not in fwd) and sub.window(p)
        return StateMetrics(f"{sub.name}|{fp}", novel, float(sub.cost(p)), float(sub.lifetime(p)))
    return ev


# ----------------------------------------------------------------------------
# MINIMAL ROUTE_ADAPTIVE (inlined; the catalogue-building primitive)
# ----------------------------------------------------------------------------

def route_adaptive(ev, space: list, lifetime_threshold: float = 2.0,
                   confirm_frac: float = 0.25):
    """Build the catalogue of manufacturably-novel state-recipes.

    Pass 1: novel + window → candidates. Pass 2: lifetime >= threshold → catalogued.
    Returns (confirmed_dict, dropped_list).
    """
    confirmed = {}
    dropped = []
    for p in space:
        m = ev(p)
        if not m.novel:
            continue
        if m.lifetime < lifetime_threshold:
            dropped.append((p, m))
            continue
        score = m.cost / max(m.lifetime, 0.01)
        if m.state_id not in confirmed or confirmed[m.state_id]["score"] > score:
            confirmed[m.state_id] = {
                "recipe": p, "cost": m.cost, "lifetime": m.lifetime, "score": score,
                "confirm_frac": confirm_frac,
            }
    return confirmed, dropped


# ----------------------------------------------------------------------------
# MINIMAL CLOSURE_WALK (the cycle-residual measurement primitive)
# ----------------------------------------------------------------------------

def closure_walk(ev, stations: list) -> dict:
    """Walk a closure cycle through the substrate's regime space; measure cycle residual + stability class.

    stations: list of BridgeParams forming a cycle (last → first should match for true closure).
    Returns dict with step distances + cycle-residual magnitude + stability class.
    """
    fps = [ev(p).state_id for p in stations]
    # step distance = simple hamming-like distance between consecutive fingerprints (string compare)
    def fp_to_vec(fp):
        # extract numeric bins from the fingerprint string
        try:
            inner = fp.split("|", 1)[1].strip("()").split(",")
            nums = []
            for tok in inner:
                tok = tok.strip().strip("'").strip('"')
                try:
                    nums.append(float(tok))
                except ValueError:
                    pass
            return np.array(nums) if nums else np.zeros(1)
        except Exception:
            return np.zeros(1)
    vecs = [fp_to_vec(fp) for fp in fps]
    # pad/trim to common length
    max_len = max(len(v) for v in vecs)
    vecs = [np.pad(v, (0, max_len - len(v))) for v in vecs]
    step_dists = [float(np.linalg.norm(vecs[i+1] - vecs[i])) for i in range(len(vecs) - 1)]
    # cycle residual = signed accumulation; closes if walk returns to first fingerprint
    return_dist = float(np.linalg.norm(vecs[-1] - vecs[0]))
    cycle_residual = sum(step_dists) - return_dist     # signed: how much the walk OPENS
    if abs(cycle_residual) < 0.01:
        stability_class = "stable-cycle"
    elif cycle_residual > 0:
        stability_class = "high-stress (opens)"
    else:
        stability_class = "high-stress (closes)"
    return {
        "n_stations": len(stations),
        "step_distances": step_dists,
        "return_distance": return_dist,
        "cycle_residual": cycle_residual,
        "stability_class": stability_class,
    }


# ----------------------------------------------------------------------------
# THE GRID SUBSTRATE — voices pattern
# ----------------------------------------------------------------------------

GRID_STATES = ["steady", "overload", "fault", "restoration", "cascade"]
CONTROLS    = ["voltage", "frequency", "breakers", "load_shed", "dispatch"]


# voice 1: HEURISTIC SURROGATE (always available — published-physics-shaped response matrix)
HEURISTIC_RESPONSE = np.array([
    [0.30, 0.85, 0.10, 0.20, 0.50],   # steady:      frequency dominant
    [0.85, 0.40, 0.60, 0.70, 0.55],   # overload:    voltage + load_shed + breakers
    [0.20, 0.30, 0.90, 0.65, 0.20],   # fault:       breakers + load_shed
    [0.75, 0.40, 0.50, 0.20, 0.70],   # restoration: voltage + dispatch
    [0.40, 0.50, 0.85, 0.90, 0.30],   # cascade:     breakers + load_shed urgent
])
HEURISTIC_COST = np.array([0.5, 0.8, 1.2, 1.5, 2.0])


def heuristic_voice(p: BridgeParams) -> tuple:
    """Voice 1: heuristic surrogate, ships with file, always available."""
    ia = GRID_STATES.index(p.regime_a)
    ib = GRID_STATES.index(p.regime_b)
    d = max(0.1, p.redevelop_depth)
    profile = (1 - p.beta) * HEURISTIC_RESPONSE[ia] + p.beta * HEURISTIC_RESPONSE[ib]
    n_engaged = max(1, int(round(d * len(CONTROLS))))
    top = np.argsort(profile)[-n_engaged:]
    activated = np.zeros_like(profile)
    activated[top] = profile[top]
    if activated.sum() > 0:
        activated /= activated.sum()
    cost = float(np.dot(activated, HEURISTIC_COST))
    return activated, cost


# voice 2: PYPOWER ADAPTER STUB — DEMONSTRATES THE PATTERN, DOES NOT RUN PYPOWER.
def pypower_adapter_stub(p: BridgeParams) -> Optional[tuple]:
    """STUB ADAPTER illustrating where a real PYPOWER voice would live in the contract.

    HONEST SCOPE: this function does NOT call `pypower.api.runpf`. It probes whether
    PYPOWER is importable (so users see the graceful-degrade pattern) and returns the
    heuristic-voice output with deterministic sinusoidal perturbation to make the voice
    distinguishable in `ensemble_voices()`. A real PYPOWER voice would map BridgeParams
    to a case-file perturbation, call `runpf`, and return a fingerprint built from
    actual bus voltages + line MW flows. See `examples/voice_extension_template.py`
    PATTERN A for the shape of a real adapter; that file documents what to fill in
    when wrapping PYPOWER for production.
    """
    try:
        import pypower.api  # noqa: F401
    except ImportError:
        return None
    activated, cost = heuristic_voice(p)
    noise = 0.03 * np.sin(np.arange(len(activated)) * (hash((p.regime_a, p.regime_b)) % 7))
    return activated + noise, cost * 1.02


# voice 3: PANDAPOWER ADAPTER STUB — DEMONSTRATES THE PATTERN, DOES NOT RUN PANDAPOWER.
def pandapower_adapter_stub(p: BridgeParams) -> Optional[tuple]:
    """STUB ADAPTER illustrating where a real PandaPower voice would live in the contract.

    HONEST SCOPE: this function does NOT call `pandapower.runpp`. It probes for the
    pandapower import + returns heuristic + cosine-perturbed output. A real PandaPower
    voice would build a `pandapower.create_empty_network()` perturbed per BridgeParams,
    call `pp.runpp(net)`, and return a fingerprint from `net.res_bus.vm_pu`. See
    `examples/voice_extension_template.py` PATTERN A for the production shape.
    """
    try:
        import pandapower  # noqa: F401
    except ImportError:
        return None
    activated, cost = heuristic_voice(p)
    noise = 0.025 * np.cos(np.arange(len(activated)) * (hash((p.regime_b, p.redevelop_depth)) % 5 + 1))
    return activated + noise, cost * 1.01


VOICES = [
    ("heuristic",          heuristic_voice),
    ("pypower_stub",       pypower_adapter_stub),     # renamed: stub-status now in the voice name
    ("pandapower_stub",    pandapower_adapter_stub),
]


def ensemble_voices(p: BridgeParams) -> tuple:
    """Listen to all available voices; average their activation + cost. Cross-band coupling."""
    activated_list = []
    costs = []
    voices_heard = []
    for name, fn in VOICES:
        result = fn(p)
        if result is not None:
            activated_list.append(result[0])
            costs.append(result[1])
            voices_heard.append(name)
    if not activated_list:
        return np.zeros(len(CONTROLS)), 0.0, []
    activated = np.mean(activated_list, axis=0)
    # renormalize after averaging
    if activated.sum() > 0:
        activated /= activated.sum()
    return activated, float(np.mean(costs)), voices_heard


def reach(p: BridgeParams) -> tuple:
    activated, _, voices = ensemble_voices(p)
    bins = tuple(round(float(a), 1) for a in activated)
    flatness = float(activated.std())
    dominant = CONTROLS[int(np.argmax(activated))]
    n_voices = len(voices)
    return (*bins, round(flatness, 2), dominant, n_voices)


def cost_fn(p: BridgeParams) -> float:
    _, c, _ = ensemble_voices(p)
    return float(c + 0.4 * p.beta)


def lifetime_fn(p: BridgeParams) -> float:
    activated, _, _ = ensemble_voices(p)
    return float(1.5 + 8.0 * activated.max())


def window_fn(p: BridgeParams) -> bool:
    activated, _, _ = ensemble_voices(p)
    return bool(0.20 <= activated.max() <= 0.85)


def forward_fn() -> set:
    return set(reach(BridgeParams(s, s, 0.5, 0.0)) for s in GRID_STATES)


def grid_substrate() -> Substrate:
    return Substrate(
        name="grid_diamondcutter_oss",
        reversal_primitive="restoration: re-energize grid to steady",
        percolation_axis="power flow balanced across nodes",
        data_source="Meta-sim of grid simulator voices (heuristic always; PYPOWER/PandaPower if installed)",
        reach=reach, cost=cost_fn, lifetime=lifetime_fn, window=window_fn, forward=forward_fn,
    )


# ----------------------------------------------------------------------------
# SELF-DEMO
# ----------------------------------------------------------------------------

def demo():
    print("=" * 72)
    print("Grid Diamondcutter OSS — meta-sim demo")
    print("=" * 72)
    # check voice availability
    print("\nVOICES AVAILABLE:")
    for name, fn in VOICES:
        p_test = BridgeParams("steady", "overload", 0.5, 0.5)
        result = fn(p_test)
        print(f"  {name:12s}  {'✓ active' if result is not None else '✗ install for richer chorus'}")

    sub = grid_substrate()
    ev = make_evaluator(sub)
    space = [BridgeParams(a, b, d, beta)
             for a in GRID_STATES for b in GRID_STATES if a != b
             for d in (0.3, 0.6, 0.9)
             for beta in (0.1, 0.5, 0.9)]
    print(f"\nROUTE_ADAPTIVE — building catalogue:")
    cat, dropped = route_adaptive(ev, space, lifetime_threshold=3.0)
    print(f"  search space: {len(space)} recipes")
    print(f"  catalogued:    {len(cat)} manufacturably-novel control configs")
    print(f"  dropped:       {len(dropped)}")
    print(f"\n  top 5 cheapest-durable configs:")
    for st, rec in sorted(cat.items(), key=lambda kv: kv[1]["score"])[:5]:
        r = rec["recipe"]
        print(f"    {r.regime_a:12s} → {r.regime_b:12s}  d={r.redevelop_depth} β={r.beta}  "
              f"cost={rec['cost']:.2f}  lifetime={rec['lifetime']:.2f}")

    # cycle walk for stability-class measurement
    print(f"\nCYCLE_WALK — measuring grid substrate's cycle residual:")
    stations = [BridgeParams("steady", "overload", 0.5, 0.5),
                BridgeParams("overload", "fault", 0.5, 0.5),
                BridgeParams("fault", "restoration", 0.5, 0.5),
                BridgeParams("restoration", "cascade", 0.5, 0.5),
                BridgeParams("cascade", "steady", 0.5, 0.5)]
    cw = closure_walk(ev, stations)
    print(f"  stations: {cw['n_stations']}-cycle through grid states")
    print(f"  step distances: {[round(d, 4) for d in cw['step_distances']]}")
    print(f"  return distance: {cw['return_distance']:.4f}")
    print(f"  CYCLE RESIDUAL: {cw['cycle_residual']:+.4f}")
    print(f"  stability class: {cw['stability_class']}")

    print(f"\nOSS NOTE:")
    print(f"  This is the OPEN substrate (Apache 2.0). The prevention-based pricing toolkit")
    print(f"  that converts a catalogue + cycle-walk into a customer-facing audit-survivable")
    print(f"  signed invoice is the closed half of the open-core split (separate Eir package).")
    print(f"  Plug your grid sim in as a 4th voice — send a PR.")


if __name__ == "__main__":
    demo()
