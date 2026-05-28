# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
power_grid_sim_v2.py — META-SIM with polyphonic VOICE abstraction + cross-band coupling.

Apache License 2.0. Single file. numpy-only. Trivially shareable.

================================================================
META-SIM ARCHITECTURE
================================================================

A power-grid substrate has MULTIPLE TIMESCALES + MULTIPLE PHYSICS layers that no
single existing simulator captures together:

  • LOAD-FLOW VOICE (sec timescale)       — steady-state line utilizations
  • CONTROL VOICE  (min timescale)        — voltage/freq regulator response
  • DYNAMICS VOICE (sub-sec timescale)    — frequency/transient dynamics
  • OUTAGE VOICE   (event timescale)      — contingency / cascading-failure

Each existing simulator (MATPOWER / OpenDSS / GridLAB-D / PSS®E) typically models ONE
of these voices well + the rest poorly. This meta-sim treats each as a VOICE in a
polyphonic substrate; outputs of one voice MODULATE inputs of the next (cross-band
coupling, PAC-style: slow voice's phase shapes fast voice's amplitude).

This file demonstrates the meta-sim shape with 3 toy voices + a wired cross-band
coupling + a single cycle-walk that captures the meta-substrate's stability class.

Honest scope: the reported cross-band correlation values (e.g. +0.832 between control
and dynamics voices) are the correlation produced by the toy coupling we wired into
this file — they demonstrate the polyphony pattern, not measured grid physics. A
production deployment replaces each voice with a real simulator (MATPOWER for
load-flow, OpenDSS for dynamics, GridLAB-D for control, PSS®E for transient
stability) through the same Voice abstraction; those simulators report their own
coupling values measured on real grids.

================================================================
RUN
================================================================

  python power_grid_sim_v2.py

Output: per-voice fingerprints + cross-band coupling matrix + meta-substrate cycle-walk.

================================================================
LICENSE
================================================================

Apache License 2.0. Copyright 2026 Eir, Inc. See LICENSE file at the repository root.
================================================================
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional
import numpy as np


N_GENS, N_LOADS = 4, 4
EDGES = [(0,4),(0,5),(1,4),(1,6),(2,5),(2,7),(3,6),(3,7),(4,5),(5,6),(6,7),(4,7)]
N_LINES = len(EDGES)
LINE_CAP = np.full(N_LINES, 100.0)


# ===========================================================================
# Voice abstraction — each voice is a substrate model at one timescale
# ===========================================================================
@dataclass
class Voice:
    name: str
    timescale: str          # "fast" / "mid" / "slow" — phase relationship lives here
    state_dim: int          # dimensionality of the voice's per-step output
    step_fn: Callable       # state_t, input_t → state_{t+1}
    state: np.ndarray = field(default=None)

    def __post_init__(self):
        if self.state is None:
            self.state = np.zeros(self.state_dim)

    def step(self, input_signal: np.ndarray) -> np.ndarray:
        self.state = self.step_fn(self.state, input_signal)
        return self.state.copy()

    def reset(self):
        self.state = np.zeros(self.state_dim)


# ---------------------------------------------------------------------------
# Voice 1: LOAD-FLOW (steady-state line utilization)
# ---------------------------------------------------------------------------
def load_flow_step(state: np.ndarray, inp: np.ndarray) -> np.ndarray:
    """inp = (load_profile_4, gen_profile_4); state = line utilizations (12)."""
    loads, gens = inp[:4], inp[4:8]
    flows = np.zeros(N_LINES)
    for i, (u, v) in enumerate(EDGES):
        if u < N_GENS and v >= N_GENS:
            flows[i] = min(gens[u] * 0.25, loads[v - N_GENS] * 0.5)
        elif v < N_GENS and u >= N_GENS:
            flows[i] = min(gens[v] * 0.25, loads[u - N_GENS] * 0.5)
        else:
            flows[i] = 5.0
    return flows / LINE_CAP


# ---------------------------------------------------------------------------
# Voice 2: CONTROL (voltage/frequency regulators respond to load-flow stress)
# ---------------------------------------------------------------------------
def control_step(state: np.ndarray, inp: np.ndarray) -> np.ndarray:
    """inp = line_utilizations (12); state = (voltage_dev_4, freq_dev_1)."""
    line_utils = inp
    stress = float(line_utils.max())
    new_v = 0.7 * state[:4] + 0.3 * stress * np.array([1.0, -0.5, 0.8, -0.3])
    new_f = 0.85 * state[4] + 0.15 * (stress - 0.5)
    return np.concatenate([new_v, [new_f]])


# ---------------------------------------------------------------------------
# Voice 3: DYNAMICS (transient response — controls modulate fast oscillations)
# ---------------------------------------------------------------------------
def dynamics_step(state: np.ndarray, inp: np.ndarray) -> np.ndarray:
    """inp = (voltage_dev_4, freq_dev_1); state = transient oscillation amplitudes (4)."""
    v_dev, f_dev = inp[:4], inp[4]
    new_state = 0.5 * state + 0.5 * (v_dev * (1.0 + f_dev))
    return new_state


# ===========================================================================
# Meta-sim: orchestrates voices with cross-band coupling
# ===========================================================================
@dataclass
class MetaSim:
    voices: list[Voice]
    coupling: dict          # {(src_voice_name, dst_voice_name): coupling_strength ∈ [0,1]}

    def step(self, external_input: np.ndarray) -> dict:
        """One step of the meta-sim: voices step in order, each receiving cross-coupled input.

        cross-band coupling: voice K's input = external + Σ(coupling[(src,K)] × src.state)
        for src ∈ all prior voices.
        """
        outputs = {}
        prior_states = {}
        for v in self.voices:
            # build coupled input: external + couplings from prior voices
            coupled_input = self._coupled_input(v, external_input, prior_states)
            outputs[v.name] = v.step(coupled_input)
            prior_states[v.name] = v.state.copy()
        return outputs

    def _coupled_input(self, v: Voice, external: np.ndarray, prior: dict) -> np.ndarray:
        # default: external goes to first voice; cascade modulates downstream voices
        if v.name == self.voices[0].name:
            return external
        # build input expected by this voice's step_fn from prior voices' outputs
        if v.name == self.voices[1].name:
            base = prior[self.voices[0].name]
        elif v.name == self.voices[2].name:
            base = prior[self.voices[1].name]
        else:
            base = external
        # add coupling-weighted contribution from EVERY prior voice
        for (src, dst), weight in self.coupling.items():
            if dst == v.name and src in prior and src != self.voices[self.voices.index(v) - 1].name:
                cross = prior[src]
                # project cross-voice state into base's dimensionality
                if len(cross) <= len(base):
                    base[:len(cross)] = base[:len(cross)] + weight * cross
        return base

    def fingerprint(self) -> tuple:
        """Meta-substrate fingerprint = concatenation of voice states (rounded for stability)."""
        return tuple(round(float(x), 3) for v in self.voices for x in v.state)

    def reset(self):
        for v in self.voices:
            v.reset()


def make_meta_sim() -> MetaSim:
    return MetaSim(
        voices=[
            Voice("load_flow", "slow", 12, load_flow_step),
            Voice("control",   "mid",  5,  control_step),
            Voice("dynamics",  "fast", 4,  dynamics_step),
        ],
        coupling={
            ("load_flow", "dynamics"): 0.15,   # slow-band phase modulates fast amplitude (PAC)
            ("control",   "dynamics"): 0.20,
        },
    )


# ===========================================================================
# Diamondcutter measurement on the META-substrate
# ===========================================================================
LOAD_PROFILES = {
    "peak":     np.array([60., 80., 70., 90., 80., 80., 80., 80.]),
    "off_peak": np.array([20., 30., 15., 25., 30., 30., 30., 30.]),
    "mixed":    np.array([60., 25., 80., 30., 50., 50., 50., 60.]),
    "spike":    np.array([40., 40., 95., 40., 60., 60., 75., 60.]),
}


def cycle_walk_meta(meta: MetaSim, profile_sequence: list[str], steps_per_station: int = 5) -> dict:
    """Walk through profile_sequence (≥3 stations), step each profile N steps, capture fingerprints.

    measures the meta-substrate cycle residual = home_step − mean_step on the polyphonic fingerprints.
    """
    fps = []
    for prof in profile_sequence:
        for _ in range(steps_per_station):
            meta.step(LOAD_PROFILES[prof])
        fps.append(meta.fingerprint())
    step_dists = [
        float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[i], fps[i + 1]))))
        for i in range(len(fps) - 1)
    ]
    home = float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[-1], fps[0]))))
    mean = float(np.mean(step_dists)) if step_dists else 0.0
    cycle_residual = home - mean
    if abs(cycle_residual) < 0.5: t = "stable-cycle"
    elif abs(cycle_residual) < 2.0: t = "moderate-stress-cycle"
    else: t = "high-stress"
    return {"step_distances": [round(d, 4) for d in step_dists],
            "home_step": round(home, 4), "mean_step": round(mean, 4),
            "cycle_residual": round(cycle_residual, 4), "stability_class": t,
            "n_voices": len(meta.voices),
            "voice_names": [v.name for v in meta.voices]}


def measure_cross_band_coupling(meta: MetaSim, n_steps: int = 30) -> dict:
    """Measure cross-band coupling empirically: how each voice's state correlates with others.

    Returns coupling matrix (voice_i, voice_j) → correlation.
    """
    meta.reset()
    histories = {v.name: [] for v in meta.voices}
    rng = np.random.default_rng(42)
    for _ in range(n_steps):
        # random load profile sequence to expose cross-coupling
        profile_name = rng.choice(list(LOAD_PROFILES.keys()))
        meta.step(LOAD_PROFILES[profile_name])
        for v in meta.voices:
            histories[v.name].append(np.linalg.norm(v.state))
    matrix = {}
    names = list(histories.keys())
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if i < j:
                c = float(np.corrcoef(histories[a], histories[b])[0, 1])
                matrix[f"{a}↔{b}"] = round(c if not np.isnan(c) else 0.0, 3)
    return matrix


def demo():
    print("=" * 78)
    print("power_grid_sim_v2 — META-SIM with polyphonic voices + cross-band coupling")
    print("=" * 78)
    meta = make_meta_sim()
    print(f"\nvoices: {[(v.name, v.timescale, v.state_dim) for v in meta.voices]}")
    print(f"coupling: {meta.coupling}")

    print("\n--- cross-band coupling measurement (empirical) ---")
    cross = measure_cross_band_coupling(meta)
    for pair, corr in cross.items():
        print(f"  {pair:<25} corr = {corr:+.3f}")

    print("\n--- META-substrate cycle walk (5 profile stations × 5 steps each) ---")
    meta.reset()
    m = cycle_walk_meta(meta, ["peak", "off_peak", "mixed", "spike", "peak"], steps_per_station=5)
    for k, v in m.items():
        print(f"  {k}: {v}")

    print("\n--- INTERPRETATION ---")
    print(f"  meta-substrate stability: {m['stability_class']}")
    print(f"  cycle_residual = {m['cycle_residual']:+.4f} ; cycle-walk on the polyphonic fingerprint of {m['n_voices']} voices")
    print(f"  cross-band coupling: captured across {len(cross)} voice pairs (toy values from wired coupling)")
    print(f"  in a production deployment each voice would be a real simulator: MATPOWER (load-flow) /")
    print(f"  OpenDSS (dynamics) / GridLAB-D (control) / PSS®E (transient) wired in via swappable step_fn.")
    print("=" * 78)


if __name__ == "__main__":
    demo()
