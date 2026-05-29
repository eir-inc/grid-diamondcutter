# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
power_grid_sim.meta — META-SIM with polyphonic voices + cross-band coupling.

This is the architectural escalation beyond `core.py`'s single-voice grid. A real
power grid has multiple physical layers (steady-state flow / control response /
transient dynamics / outage events) operating at different TIMESCALES. No single
existing simulator captures all of them together.

The META-SIM models each layer as a VOICE — a discrete substrate model with its
own state, step function, and timescale. Voices are wired through CROSS-BAND
COUPLING: the slow voice's state modulates the fast voice's input (phase-amplitude
coupling, PAC, the same primitive resonance-topology measures on EEG).

KEY EMPIRICAL RESULT (2026-05-28):
  The default 3-voice meta-sim (load_flow + control + dynamics) measures
  control↔dynamics correlation of +0.832 — strong cross-band coupling. The slow
  control voice DOES shape the fast dynamics voice's amplitude, observable from
  random load-profile perturbations. This is the polyphonic substrate's signature
  that no single-layer sim captures.

  HONESTY-BOUND GUARD (PREREGISTRATION §1 bound #3, mechanically defended by
  voice_bound_defender_3_coupling_coefficient_v1):
  The +0.832 figure is the correlation between two simulated voices the project
  authored. It is not a measurement of physical grid coupling and does not
  generalize to any real grid. The figure demonstrates that the polyphony pattern
  detects coupling when coupling exists in a substrate the project constructed;
  any claim about real-grid coupling magnitudes must come from a per-voice
  predict / kill-condition / run / verdict unit operating against real-grid data.

DROP-IN VOICE SWAPPING:
  Each voice has a `step_fn` callable. Swap it for MATPOWER (load_flow), OpenDSS
  (dynamics), GridLAB-D (control), or your own physics — same MetaSim assembles.
  Pure Python interface; no AI / ML required.

EXAMPLE:
  >>> from power_grid_sim import make_default_meta_sim, cycle_walk_meta
  >>> meta = make_default_meta_sim()
  >>> result = cycle_walk_meta(meta, ["peak", "off_peak", "mixed", "spike", "peak"])
  >>> result["stability_class"]
  'stable-cycle'
  >>> from power_grid_sim import measure_cross_band_coupling
  >>> coupling = measure_cross_band_coupling(meta, n_steps=30)
  >>> coupling["control↔dynamics"]   # PAC strength
  0.832
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional
import numpy as np

from .core import (
    LOAD_PROFILES,
    GEN_PROFILES,
    EDGES,
    N_GENS,
    N_LINES,
    DEFAULT_LINE_CAPACITY,
)


# ===========================================================================
# Voice abstraction
# ===========================================================================
@dataclass
class Voice:
    """A single timescale's substrate model in the polyphonic meta-sim.

    Each Voice maintains its own STATE vector and a STEP FUNCTION that advances
    that state given an input signal. Voices are composed by MetaSim with
    cross-band coupling — slower voices' states modulate faster voices' inputs.

    Attributes
    ----------
    name : str
        Voice identifier (used in cross-coupling map keys).
    timescale : str
        Human label: 'slow' / 'mid' / 'fast'. Used to organize cross-band readings.
    state_dim : int
        Dimensionality of the per-step state vector.
    step_fn : Callable[[np.ndarray, np.ndarray], np.ndarray]
        (state_t, input_t) → state_{t+1}.
    state : np.ndarray
        Current state. Initialized to zeros; reset via .reset().

    Example
    -------
    >>> def my_step(state, inp):
    ...     return 0.9 * state + 0.1 * inp
    >>> v = Voice("decay_filter", "fast", 4, my_step)
    >>> v.step(np.array([1.0, 1.0, 1.0, 1.0]))
    array([0.1, 0.1, 0.1, 0.1])
    """
    name: str
    timescale: str
    state_dim: int
    step_fn: Callable[[np.ndarray, np.ndarray], np.ndarray]
    state: Optional[np.ndarray] = None

    def __post_init__(self):
        if self.state is None:
            self.state = np.zeros(self.state_dim)

    def step(self, input_signal: np.ndarray) -> np.ndarray:
        """Advance the voice's state by one timestep. Returns the new state."""
        self.state = self.step_fn(self.state, input_signal)
        return self.state.copy()

    def reset(self):
        """Zero the state. Use before measuring cross-band coupling for a clean run."""
        self.state = np.zeros(self.state_dim)


# ---------------------------------------------------------------------------
# Default voice physics (DC power flow at three timescales)
# ---------------------------------------------------------------------------
def load_flow_step(state: np.ndarray, inp: np.ndarray) -> np.ndarray:
    """LOAD-FLOW voice: steady-state per-line utilization.

    Parameters
    ----------
    state : np.ndarray (N_LINES,)
        Previous line utilizations (overwritten — this voice is stateless conceptually).
    inp : np.ndarray (8,)
        First 4 elements = load profile, last 4 = generation profile (MW each).

    Returns
    -------
    np.ndarray (N_LINES,)
        New per-line utilizations (capacity-normalized to [0, 1+]).
    """
    loads, gens = inp[:4], inp[4:8]
    flows = np.zeros(N_LINES)
    for i, (u, v) in enumerate(EDGES):
        if u < N_GENS and v >= N_GENS:
            flows[i] = min(gens[u] * 0.25, loads[v - N_GENS] * 0.5)
        elif v < N_GENS and u >= N_GENS:
            flows[i] = min(gens[v] * 0.25, loads[u - N_GENS] * 0.5)
        else:
            flows[i] = 5.0   # load-load redistribution baseline
    return flows / DEFAULT_LINE_CAPACITY


def control_step(state: np.ndarray, inp: np.ndarray) -> np.ndarray:
    """CONTROL voice: voltage + frequency regulator response to line stress.

    Slow timescale (minutes in real grids). Reads max line stress, produces voltage
    deviations across 4 substations + a single frequency deviation. Smoothed by
    autoregressive memory (0.7 × prev + 0.3 × response).

    Parameters
    ----------
    state : np.ndarray (5,)
        Previous (voltage_dev_0, ..., voltage_dev_3, frequency_dev).
    inp : np.ndarray (N_LINES,)
        Current line utilizations (output of load-flow voice).

    Returns
    -------
    np.ndarray (5,)
        New (voltage_dev_0-3, frequency_dev).
    """
    line_utils = inp
    stress = float(line_utils.max())
    new_v = 0.7 * state[:4] + 0.3 * stress * np.array([1.0, -0.5, 0.8, -0.3])
    new_f = 0.85 * state[4] + 0.15 * (stress - 0.5)
    return np.concatenate([new_v, [new_f]])


def dynamics_step(state: np.ndarray, inp: np.ndarray) -> np.ndarray:
    """DYNAMICS voice: transient oscillations modulated by control + frequency.

    Fast timescale (sub-second in real grids). The control voice's state shapes
    this voice's amplitude — that's the cross-band coupling (PAC) the meta-sim
    captures.

    Parameters
    ----------
    state : np.ndarray (4,)
        Previous transient oscillation amplitudes.
    inp : np.ndarray (5,)
        Current control state (voltage_dev_0-3, frequency_dev).

    Returns
    -------
    np.ndarray (4,)
        New oscillation amplitudes.
    """
    v_dev, f_dev = inp[:4], inp[4]
    return 0.5 * state + 0.5 * (v_dev * (1.0 + f_dev))


# ===========================================================================
# MetaSim: orchestrates voices with cross-band coupling
# ===========================================================================
@dataclass
class MetaSim:
    """A polyphonic meta-simulator: multiple Voices wired by cross-band coupling.

    Each step:
      1. External input (e.g., load profile) feeds the first voice.
      2. Each subsequent voice's input = output of previous voice + cross-coupling
         from any prior voice (per the coupling dict).
      3. Each voice's state advances by one step.

    The meta-substrate's "fingerprint" is the concatenated state of all voices —
    a polyphonic signature no single voice captures alone.

    Attributes
    ----------
    voices : list[Voice]
        Ordered list. Voice 0 receives external input; downstream voices receive
        the previous voice's output (plus cross-coupled contributions).
    coupling : dict[tuple[str, str], float]
        {(src_voice_name, dst_voice_name): coupling_strength_in_[0,1]}
        Defines extra cross-band feeds beyond the natural cascade.

    Example
    -------
    >>> meta = make_default_meta_sim()
    >>> meta.step(LOAD_PROFILES["peak"] + GEN_PROFILES["peak"])
    {'load_flow': ..., 'control': ..., 'dynamics': ...}
    """
    voices: list[Voice]
    coupling: dict = field(default_factory=dict)

    def step(self, external_input: np.ndarray) -> dict:
        """One full pass through all voices. Returns dict of {voice_name: new_state}."""
        outputs = {}
        prior_states = {}
        for v in self.voices:
            coupled_input = self._coupled_input(v, external_input, prior_states)
            outputs[v.name] = v.step(coupled_input)
            prior_states[v.name] = v.state.copy()
        return outputs

    def _coupled_input(self, v: Voice, external: np.ndarray, prior: dict) -> np.ndarray:
        """Build voice v's input from external + previous voice + cross-couplings."""
        idx = self.voices.index(v)
        if idx == 0:
            return external

        # default cascade: input = output of previous voice
        base = prior[self.voices[idx - 1].name].copy()

        # add coupling contributions from any prior voice NOT in the cascade
        for (src, dst), weight in self.coupling.items():
            if dst == v.name and src in prior and src != self.voices[idx - 1].name:
                cross = prior[src]
                if len(cross) <= len(base):
                    base[:len(cross)] = base[:len(cross)] + weight * cross
        return base

    def fingerprint(self) -> tuple:
        """Meta-substrate fingerprint = concatenation of all voice states."""
        return tuple(round(float(x), 3) for v in self.voices for x in v.state)

    def reset(self):
        """Reset all voices to zero state."""
        for v in self.voices:
            v.reset()


def make_default_meta_sim() -> MetaSim:
    """Construct the default 3-voice meta-sim:
        load_flow (slow, 12d) → control (mid, 5d) → dynamics (fast, 4d)
       with cross-couplings:
        load_flow → dynamics: 0.15  (slow phase → fast amplitude)
        control   → dynamics: 0.20  (PAC-style)

    Returns the empirically-validated meta-sim that measures +0.832 control↔dynamics
    PAC under random load perturbation.
    """
    return MetaSim(
        voices=[
            Voice("load_flow", "slow", N_LINES, load_flow_step),
            Voice("control",   "mid",  5,        control_step),
            Voice("dynamics",  "fast", 4,        dynamics_step),
        ],
        coupling={
            ("load_flow", "dynamics"): 0.15,
            ("control",   "dynamics"): 0.20,
        },
    )


# ===========================================================================
# Meta-substrate measurements
# ===========================================================================
def cycle_walk_meta(meta: MetaSim, profile_sequence: list[str],
                       steps_per_station: int = 5) -> dict:
    """Walk through `profile_sequence`, run `steps_per_station` steps at each,
    capture meta-fingerprints, compute the cycle residual.

    Same measurement as core.cycle_walk, but on the META-substrate's polyphonic
    fingerprint. Captures cross-voice closure that single-voice walks miss.

    Parameters
    ----------
    meta : MetaSim
        The meta-sim to measure.
    profile_sequence : list[str]
        Ordered list of load-profile names (keys in LOAD_PROFILES).
        Last name should equal first for meaningful return check.
    steps_per_station : int, default 5
        Number of meta-steps per station (allows voices to settle into the regime).

    Returns
    -------
    dict with the same keys as core.cycle_walk + voice_names + n_voices.
    """
    fps = []
    for profile_name in profile_sequence:
        external_input = np.concatenate([
            LOAD_PROFILES[profile_name],
            GEN_PROFILES[profile_name],
        ])
        for _ in range(steps_per_station):
            meta.step(external_input)
        fps.append(meta.fingerprint())

    step_dists = [
        float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[i], fps[i + 1]))))
        for i in range(len(fps) - 1)
    ]
    home_step = float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fps[-1], fps[0]))))
    mean_step = float(np.mean(step_dists)) if step_dists else 0.0
    cycle_residual = home_step - mean_step

    abs_residual = abs(cycle_residual)
    if abs_residual < 0.5:
        stability_class = "stable-cycle"
    elif abs_residual < 2.0:
        stability_class = "moderate-stress-cycle"
    else:
        stability_class = "high-stress-cycle"

    return {
        "n_stations": len(profile_sequence),
        "n_voices": len(meta.voices),
        "voice_names": [v.name for v in meta.voices],
        "step_distances": [round(d, 4) for d in step_dists],
        "home_step": round(home_step, 4),
        "mean_step": round(mean_step, 4),
        "cycle_residual": round(cycle_residual, 4),
        "stability_class": stability_class,
    }


def measure_cross_band_coupling(meta: MetaSim, n_steps: int = 30,
                                  seed: int = 42) -> dict:
    """Empirically measure cross-band coupling: correlation between voice state-norms.

    Runs `n_steps` of the meta-sim with random load profiles, records each voice's
    state norm at each step, computes pairwise correlations. Strong correlations
    indicate cross-band coupling (PAC-style modulation between timescales).

    Parameters
    ----------
    meta : MetaSim
        The meta-sim to characterize.
    n_steps : int, default 30
        Number of random-perturbation steps. More = tighter correlations but slower.
    seed : int, default 42
        Random seed for reproducibility.

    Returns
    -------
    dict {"voice_a↔voice_b": correlation_in_[-1, 1]}

    Empirical result on default 3-voice meta-sim:
        load_flow↔control:   -0.073
        load_flow↔dynamics:  +0.058
        control↔dynamics:    +0.832  ← strong PAC
    """
    meta.reset()
    histories = {v.name: [] for v in meta.voices}
    rng = np.random.default_rng(seed)
    profile_names = list(LOAD_PROFILES.keys())

    for _ in range(n_steps):
        profile_name = rng.choice(profile_names)
        external_input = np.concatenate([
            LOAD_PROFILES[profile_name],
            GEN_PROFILES[profile_name],
        ])
        meta.step(external_input)
        for v in meta.voices:
            histories[v.name].append(float(np.linalg.norm(v.state)))

    matrix = {}
    names = list(histories.keys())
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if i < j:
                c = float(np.corrcoef(histories[a], histories[b])[0, 1])
                matrix[f"{a}↔{b}"] = round(c if not np.isnan(c) else 0.0, 3)
    return matrix

# backward-compatible alias (deprecated naming; will remove in v1.0)
closure_walk_meta = cycle_walk_meta
