# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
power_grid_sim.core — single-voice DC power flow + cycle-walk measurement.

This module provides the foundational power-grid model and the cycle-walk measurement
that gives a grid a stability class — a one-bit-rich summary of how the grid behaves
under load-profile cycling.

THEORY (brief)
==============

A power grid under operating-cycle stress doesn't return to exactly its starting state
after one rotation through load profiles. The residual is the CYCLE RESIDUAL — the gap
between ideal closure (no accumulated stress per cycle) and actual closure (some residual).

  cycle_residual = home_step − mean_step
        ≈ how much the grid's state-vector drifted off its starting fingerprint
          relative to the typical step-to-step drift during one cycle.

Cycle-residual magnitude classifies the grid:
  • |residual| < 0.5  → stable-cycle           (minimal intervention needed)
  • |residual| < 2.0  → moderate-stress-cycle  (periodic rebalancing helpful)
  • |residual| ≥ 2.0  → high-stress-cycle      (frequent operator action required)

The stability class predicts CYCLE-LIFE = how many operating cycles before the grid
needs structural maintenance / planning adjustment. Stable-cycle grids run for many
cycles; high-stress-cycle grids accumulate debt quickly.

This is the closed-cycle measurement methodology applied to the power-grid domain:
a substrate-shape question — does this grid close under cyclic loading? — answered
by a small, reproducible protocol.

GRID MODEL
==========

An 8-node DC power-flow model: 4 generators + 4 loads + 12 transmission lines.
Topology fixed; load/generation profiles parameterized by REGIME (peak / off_peak /
mixed / spike). Pure numpy; no external simulator required.

For production grids (1000+ nodes), the same cycle-walk math runs on top of any
load-flow solver (MATPOWER, OpenDSS, GridLAB-D, pandapower) — see power_grid_sim.meta
for the meta-sim Voice wrapper that adapts external solvers as plug-in voices.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np


# ---------------------------------------------------------------------------
# Grid topology constants
# ---------------------------------------------------------------------------
N_GENS = 4
N_LOADS = 4
N_NODES = N_GENS + N_LOADS

# 12 transmission lines connecting generators to loads + load-load redistribution paths.
# Format: (node_u, node_v) where 0-3 are generators, 4-7 are loads.
EDGES = [
    (0, 4), (0, 5), (1, 4), (1, 6), (2, 5), (2, 7),
    (3, 6), (3, 7), (4, 5), (5, 6), (6, 7), (4, 7),
]
N_LINES = len(EDGES)

# Per-line transmission capacity (MW). Real grids have varied per-line capacities;
# here uniform for simplicity. Override Grid(line_capacities=…) for asymmetric grids.
DEFAULT_LINE_CAPACITY = 100.0

# Per-line loss factor (proportional to flow²). Simplified DC model.
DEFAULT_LINE_RESISTANCE = 0.05


# ---------------------------------------------------------------------------
# Load and generation profiles — 4 named regimes
# ---------------------------------------------------------------------------
# Each profile is a 4-vector: power at each of the 4 generators or 4 loads (in MW).
# Sum doesn't need to match exactly; the grid handles redistribution through line flows.
LOAD_PROFILES = {
    "peak":     np.array([60.0, 80.0, 70.0, 90.0]),   # high demand across all loads
    "off_peak": np.array([20.0, 30.0, 15.0, 25.0]),   # low demand (e.g., night-time)
    "mixed":    np.array([60.0, 25.0, 80.0, 30.0]),   # uneven (e.g., partial-industrial)
    "spike":    np.array([40.0, 40.0, 95.0, 40.0]),   # transient spike on load 6 (e.g., manufacturing surge)
}

GEN_PROFILES = {
    "peak":     np.array([80.0, 80.0, 80.0, 80.0]),
    "off_peak": np.array([30.0, 30.0, 30.0, 30.0]),
    "mixed":    np.array([50.0, 50.0, 50.0, 60.0]),
    "spike":    np.array([60.0, 60.0, 75.0, 60.0]),
}


# ---------------------------------------------------------------------------
# Grid model — wraps the topology + flow computation as a Pythonic object
# ---------------------------------------------------------------------------
class Grid:
    """An 8-node DC power-flow grid model.

    Parameters
    ----------
    line_capacities : np.ndarray, optional
        Per-line MW capacity. Default: uniform DEFAULT_LINE_CAPACITY.
    line_resistance : np.ndarray, optional
        Per-line loss factor. Default: uniform DEFAULT_LINE_RESISTANCE.

    Examples
    --------
    >>> g = Grid()
    >>> flows = g.compute_flows("peak", "off_peak", mix=0.5)
    >>> flows.shape
    (12,)
    >>> stations = g.default_stations()
    >>> result = closure_walk(g, stations)
    >>> result["stability_class"]
    'stable-cycle'
    """

    def __init__(self,
                 line_capacities: Optional[np.ndarray] = None,
                 line_resistance: Optional[np.ndarray] = None):
        self.line_capacities = line_capacities if line_capacities is not None \
            else np.full(N_LINES, DEFAULT_LINE_CAPACITY)
        self.line_resistance = line_resistance if line_resistance is not None \
            else np.full(N_LINES, DEFAULT_LINE_RESISTANCE)

    def compute_flows(self, profile_a: str, profile_b: str, mix: float = 0.0) -> np.ndarray:
        """Compute per-line utilization under a (possibly mixed) load profile.

        Parameters
        ----------
        profile_a : str
            Primary load profile name (key in LOAD_PROFILES / GEN_PROFILES).
        profile_b : str
            Secondary profile for interpolation; ignored if mix=0.
        mix : float, default 0.0
            Interpolation weight: 0.0 = pure profile_a, 1.0 = pure profile_b.

        Returns
        -------
        np.ndarray of shape (12,)
            Per-line utilization in [0, 1+]. Values > 1.0 indicate line saturation
            (capacity exceeded — physically infeasible without redispatch).
        """
        loads = (1 - mix) * LOAD_PROFILES.get(profile_a, LOAD_PROFILES["mixed"]) + \
                mix * LOAD_PROFILES.get(profile_b, LOAD_PROFILES["mixed"])
        gens = (1 - mix) * GEN_PROFILES.get(profile_a, GEN_PROFILES["mixed"]) + \
               mix * GEN_PROFILES.get(profile_b, GEN_PROFILES["mixed"])

        # Simplified DC power-flow: each gen-load edge carries min(available_gen, demand)
        # load-load redistribution edges carry a baseline transit load.
        line_flows = np.zeros(N_LINES)
        for i, (u, v) in enumerate(EDGES):
            if u < N_GENS and v >= N_GENS:
                load_idx = v - N_GENS
                line_flows[i] = min(gens[u] * 0.25, loads[load_idx] * 0.5)
            elif v < N_GENS and u >= N_GENS:
                load_idx = u - N_GENS
                line_flows[i] = min(gens[v] * 0.25, loads[load_idx] * 0.5)
            else:
                line_flows[i] = 5.0  # baseline transit on load-load edges

        return line_flows / self.line_capacities

    def fingerprint(self, station: "GridStation") -> tuple:
        """Reduce a station to a 6D substrate-fingerprint for cycle-walk comparison.

        Fingerprint = 5-bin utilization histogram + max-utilization.
        This is the substrate-shape projection used by the closed-cycle measurement.
        """
        flows = self.compute_flows(station.profile_a, station.profile_b, station.mix)
        bins = np.histogram(flows, bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.5])[0]
        return (*[int(b) for b in bins], round(float(flows.max()), 3))

    def cost(self, station: "GridStation") -> float:
        """Operating cost at a station = sum of line losses + congestion penalty.

        Used by the catalogue() function to filter manufacturably-feasible configs.
        """
        flows = self.compute_flows(station.profile_a, station.profile_b, station.mix)
        losses = (flows ** 2 * self.line_resistance).sum()
        congestion = float(((flows - 0.8).clip(0) ** 2).sum() * 100.0)
        return float(losses + congestion)

    def lifetime(self, station: "GridStation") -> float:
        """Time-to-instability estimate (inverse of max line utilization).

        Higher max-utilization → shorter lifetime (line saturation forces redispatch).
        """
        flows = self.compute_flows(station.profile_a, station.profile_b, station.mix)
        return float(10.0 / (0.1 + flows.max()))

    def window(self, station: "GridStation") -> bool:
        """Manufacturable-operating-band check: no saturation, not-all-stressed."""
        flows = self.compute_flows(station.profile_a, station.profile_b, station.mix)
        return bool(flows.max() < 1.0 and flows.min() < 0.7)

    def default_stations(self) -> list["GridStation"]:
        """A 5-station cycle-walk circle through the standard load profiles.

        peak → off_peak → mixed → spike → peak (returning to start to test closure).
        """
        return [
            GridStation("peak",     "off_peak", 0.3),
            GridStation("off_peak", "mixed",    0.3),
            GridStation("mixed",    "spike",    0.3),
            GridStation("spike",    "peak",     0.3),
            GridStation("peak",     "off_peak", 0.3),
        ]


# ---------------------------------------------------------------------------
# Station: one position on the cycle-walk circle
# ---------------------------------------------------------------------------
@dataclass
class GridStation:
    """One station on a cycle-walk circle — a particular operating regime.

    profile_a / profile_b allow mixed regimes (e.g., transitioning from peak to off_peak).
    mix ∈ [0, 1] interpolates between them; mix=0 = pure profile_a.
    """
    profile_a: str
    profile_b: str
    mix: float = 0.5


# ---------------------------------------------------------------------------
# closure_walk — the closed-cycle measurement primitive
# ---------------------------------------------------------------------------
def closure_walk(grid: Grid, stations: list[GridStation]) -> dict:
    """Walk an N-station circle through load profiles; measure the cycle residual at home-closure.

    The cycle walk asks: after traversing this sequence of operating regimes and
    returning to the start, how much did the grid's state-fingerprint drift?

    Parameters
    ----------
    grid : Grid
        The power grid being characterized.
    stations : list[GridStation]
        Ordered circle of operating regimes. Last station should equal first
        (or be close) for the closure check to be meaningful.

    Returns
    -------
    dict with keys:
        n_stations         : int
        step_distances     : list[float]  — distance between consecutive station fingerprints
        home_step          : float        — distance between last and first fingerprint
        mean_step          : float        — average step distance
        cycle_residual     : float        — home_step − mean_step (the closure gap)
        closes             : bool         — residual ≤ 0 (grid returns within typical step)
        stability_class    : str          — 'stable-cycle' / 'moderate-stress-cycle' / 'high-stress-cycle'
    """
    fps = [grid.fingerprint(s) for s in stations]

    step_distances = [
        float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[i], fps[i + 1]))))
        for i in range(len(fps) - 1)
    ]
    home_step = float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[-1], fps[0]))))
    mean_step = float(np.mean(step_distances)) if step_distances else 0.0
    cycle_residual = home_step - mean_step

    abs_residual = abs(cycle_residual)
    if abs_residual < 0.5:
        stability_class = "stable-cycle"
    elif abs_residual < 2.0:
        stability_class = "moderate-stress-cycle"
    else:
        stability_class = "high-stress-cycle"

    return {
        "n_stations": len(stations),
        "step_distances": [round(d, 4) for d in step_distances],
        "home_step": round(home_step, 4),
        "mean_step": round(mean_step, 4),
        "cycle_residual": round(cycle_residual, 4),
        "closes": home_step <= mean_step,
        "stability_class": stability_class,
    }


# ---------------------------------------------------------------------------
# catalogue — enumerate manufacturably-feasible operating regimes
# ---------------------------------------------------------------------------
def catalogue(grid: Grid, lifetime_threshold: float = 3.0,
              cost_threshold: float = 50.0) -> list[dict]:
    """Enumerate all (profile_a, profile_b, mix) regimes that pass manufacturable thresholds.

    A regime is "manufacturable" if:
      - lifetime > lifetime_threshold (won't fail too fast)
      - cost < cost_threshold (operating within budget)

    Returns a list of records sorted by cost (cheapest first).
    """
    out = []
    profiles = list(LOAD_PROFILES.keys())
    for a in profiles:
        for b in profiles:
            if a == b:
                continue
            for mix in (0.2, 0.5, 0.8):
                s = GridStation(a, b, mix)
                c, lt = grid.cost(s), grid.lifetime(s)
                if lt > lifetime_threshold and c < cost_threshold:
                    out.append({
                        "profile_a": a,
                        "profile_b": b,
                        "mix": mix,
                        "cost": round(c, 3),
                        "lifetime": round(lt, 3),
                        "fingerprint": grid.fingerprint(s),
                    })
    return sorted(out, key=lambda r: r["cost"])
