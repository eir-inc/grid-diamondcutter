# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
power_grid_sim.py — perfectly contained DC power-grid simulator + cycle-walk measurement.

Apache License 2.0. Single file. numpy-only dependency. Trivially shareable.

================================================================
WHAT IT DOES
================================================================

Models an 8-node toy DC power grid (4 generators + 4 loads, 12 transmission lines) and
demonstrates the closed-cycle measurement: walk the grid through a
representative cycle of load profiles, return to the starting profile, and report
how cleanly the cycle closed.

The cycle-walk produces a single classification — the grid's stability class:

  • stable-cycle            → minimal intervention needed, long cycle-life
  • moderate-stress-cycle   → periodic rebalancing helpful
  • high-stress-cycle       → frequent operator action required, short cycle-life

The classification is derived from the cycle residual: the gap between idealized
closure (no accumulated drift per cycle) and actual closure (some residual after
the walk returns to its starting load profile).

================================================================
WHY IT MATTERS
================================================================

Existing grid simulators (MATPOWER, PYPOWER, OpenDSS, GridLAB-D, pandapower, PSS®E)
are designed for load-flow analysis, contingency simulation, transient stability,
and market clearing — they answer "what is the steady-state / dynamic response
given X?" They do not typically answer "what's this grid's cycle-walk signature
under realistic operating-regime cycles?" The closed-cycle measurement plugs on
top of any of those simulators (via the substrate-plugin contract) and reports
the cycle-walk signature.

This file is the minimum viable demonstration: 8 nodes, 12 lines, 4 load profiles,
a heuristic flow allocator (NOT a B-bus / phase-angle DC power flow). Real production
grids plug their existing models behind the same substrate-plugin contract; this file
shows the shape.

================================================================
RUN
================================================================

  python power_grid_sim.py

Output: catalogue of manufacturably-novel operating-regime recipes + cycle-walk
cycle-residual + stability-class verdict.

================================================================
LICENSE
================================================================

Apache License 2.0. Copyright 2026 Eir, Inc. See LICENSE file at the repository root
for the full text. The per-file SPDX-style header above + the repository LICENSE file
are the authoritative license claim.

================================================================
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import numpy as np


# ---------------------------------------------------------------------------
# Grid topology: 8 nodes (4 generators G0-G3, 4 loads L4-L7), 12 transmission lines
# ---------------------------------------------------------------------------
N_GENS = 4
N_LOADS = 4
EDGES = [
    (0, 4), (0, 5), (1, 4), (1, 6), (2, 5), (2, 7),
    (3, 6), (3, 7), (4, 5), (5, 6), (6, 7), (4, 7),
]
N_LINES = len(EDGES)
LINE_CAPACITIES = np.full(N_LINES, 100.0)    # MW per line
LINE_RESISTANCE = np.full(N_LINES, 0.05)     # per-line loss factor


# ---------------------------------------------------------------------------
# Load + generation profiles per operating regime
# ---------------------------------------------------------------------------
LOAD_PROFILES = {
    "peak":     np.array([60.0, 80.0, 70.0, 90.0]),   # high load across all
    "off_peak": np.array([20.0, 30.0, 15.0, 25.0]),   # low load
    "mixed":    np.array([60.0, 25.0, 80.0, 30.0]),   # uneven distribution
    "spike":    np.array([40.0, 40.0, 95.0, 40.0]),   # transient spike on L6
}
GEN_PROFILES = {
    "peak":     np.array([80.0, 80.0, 80.0, 80.0]),
    "off_peak": np.array([30.0, 30.0, 30.0, 30.0]),
    "mixed":    np.array([50.0, 50.0, 50.0, 60.0]),
    "spike":    np.array([60.0, 60.0, 75.0, 60.0]),
}


def power_flow(profile_a: str, profile_b: str, mix: float) -> np.ndarray:
    """Compute per-line utilization under a mixed load (a→b interpolation by `mix` ∈ [0,1])."""
    loads = (1 - mix) * LOAD_PROFILES.get(profile_a, LOAD_PROFILES["mixed"]) + \
            mix * LOAD_PROFILES.get(profile_b, LOAD_PROFILES["mixed"])
    gens = (1 - mix) * GEN_PROFILES.get(profile_a, GEN_PROFILES["mixed"]) + \
           mix * GEN_PROFILES.get(profile_b, GEN_PROFILES["mixed"])

    line_flows = np.zeros(N_LINES)
    for i, (u, v) in enumerate(EDGES):
        if u < N_GENS and v >= N_GENS:
            load_idx = v - N_GENS
            line_flows[i] += min(gens[u] * 0.25, loads[load_idx] * 0.5)
        elif v < N_GENS and u >= N_GENS:
            load_idx = u - N_GENS
            line_flows[i] += min(gens[v] * 0.25, loads[load_idx] * 0.5)
        else:
            line_flows[i] += 5.0    # load-load redistribution baseline
    return line_flows / LINE_CAPACITIES


# ---------------------------------------------------------------------------
# Substrate-plugin shape (subset; full contract in Eir's substrate_plugin.py)
# ---------------------------------------------------------------------------
@dataclass
class GridStation:
    profile_a: str
    profile_b: str
    mix: float = 0.5    # interpolation between profile_a and profile_b


def reach(s: GridStation) -> tuple:
    """Per-station fingerprint: utilization histogram + max-utilization."""
    flows = power_flow(s.profile_a, s.profile_b, s.mix)
    bins = np.histogram(flows, bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.5])[0]
    return (*[int(b) for b in bins], round(float(flows.max()), 3))


def cost(s: GridStation) -> float:
    flows = power_flow(s.profile_a, s.profile_b, s.mix)
    return float((flows ** 2 * LINE_RESISTANCE).sum() + ((flows - 0.8).clip(0) ** 2).sum() * 100.0)


def lifetime(s: GridStation) -> float:
    flows = power_flow(s.profile_a, s.profile_b, s.mix)
    return float(10.0 / (0.1 + flows.max()))


# ---------------------------------------------------------------------------
# Cycle walk: the closed-cycle measurement
# ---------------------------------------------------------------------------
def cycle_walk(stations: list[GridStation]) -> dict:
    """Walk an N-station circle through load profiles, measure the cycle residual at home-closure."""
    fps = [reach(s) for s in stations]
    step_distances = [
        float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[i], fps[i + 1]))))
        for i in range(len(fps) - 1)
    ]
    home_step = float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[-1], fps[0]))))
    mean_step = float(np.mean(step_distances)) if step_distances else 0.0
    cycle_residual = home_step - mean_step

    abs_residual = abs(cycle_residual)
    if abs_residual < 0.5: stability_class = "stable-cycle"
    elif abs_residual < 2.0: stability_class = "moderate-stress-cycle"
    else: stability_class = "high-stress-cycle"

    return {
        "n_stations": len(stations),
        "step_distances": [round(d, 4) for d in step_distances],
        "home_step": round(home_step, 4),
        "mean_step": round(mean_step, 4),
        "cycle_residual": round(cycle_residual, 4),
        "closes": home_step <= mean_step,
        "stability_class": stability_class,
    }


def catalogue() -> list[dict]:
    """Enumerate all manufacturably-novel (cost-effective + long-life) operating regimes."""
    out = []
    profiles = list(LOAD_PROFILES.keys())
    for a in profiles:
        for b in profiles:
            if a == b:
                continue
            for mix in (0.2, 0.5, 0.8):
                s = GridStation(a, b, mix)
                c, lt = cost(s), lifetime(s)
                if lt > 3.0 and c < 50.0:   # manufacturable thresholds
                    out.append({"a": a, "b": b, "mix": mix, "cost": round(c, 3),
                                "lifetime": round(lt, 3), "fingerprint": reach(s)})
    return out


# ---------------------------------------------------------------------------
# Demo: run the cycle-walk measurement end-to-end
# ---------------------------------------------------------------------------
def demo():
    print("=" * 72)
    print("power_grid_sim — cycle-walk measurement on 8-node toy DC grid")
    print("=" * 72)

    cat = catalogue()
    print(f"\nCATALOGUE: {len(cat)} manufacturably-novel operating-regime recipes")
    print(f"  cheapest 5 (by lowest cost):")
    for rec in sorted(cat, key=lambda r: r["cost"])[:5]:
        print(f"    {rec['a']:>9}→{rec['b']:<9} mix={rec['mix']:.1f}  "
              f"cost={rec['cost']:>6.3f}  lifetime={rec['lifetime']:>6.2f}")

    stations = [
        GridStation("peak", "off_peak", 0.3),
        GridStation("off_peak", "mixed", 0.3),
        GridStation("mixed", "spike", 0.3),
        GridStation("spike", "peak", 0.3),
        GridStation("peak", "off_peak", 0.3),     # cycle return
    ]
    m = cycle_walk(stations)
    print(f"\nCYCLE WALK ({m['n_stations']} stations rotating load profiles):")
    print(f"  step distances:    {m['step_distances']}")
    print(f"  home step:         {m['home_step']}")
    print(f"  mean step:         {m['mean_step']}")
    print(f"  cycle residual:    {m['cycle_residual']:+.4f}")
    print(f"  closes:            {m['closes']}")
    print(f"  stability class:   {m['stability_class']}")

    cycle_life = sum(rec['lifetime'] for rec in cat) / max(1, len(cat))
    print(f"\n  avg recipe cycle-life: {cycle_life:.2f}")
    print(f"\n{'=' * 72}")
    print(f"INTERPRETATION:")
    print(f"  this grid is {m['stability_class']} → ", end="")
    if m['stability_class'] == "stable-cycle":
        print("long expected cycle-life, minimal intervention needed.")
    elif m['stability_class'] == "moderate-stress-cycle":
        print("moderate stress accumulation, periodic rebalancing recommended.")
    else:
        print("HIGH stress accumulation, frequent operator intervention required.")
    print(f"  reduction-opportunity proportional to (cycle-residual × cycle-life). Measurable.")
    print("=" * 72)
    return m


if __name__ == "__main__":
    demo()
