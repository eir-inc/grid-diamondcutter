# Copyright 2026 Eir Inc
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""tests/test_meta_sim.py — meta_sim package tests (polyphonic voices + cross-band coupling).

Locks the claims the `meta_sim/meta.py` module makes:
  - Voice class behaves correctly (init, step, reset).
  - MetaSim assembles voices + steps without error.
  - closure_walk_meta returns a valid stability class.
  - measure_cross_band_coupling produces the meta-sim's internal +0.832 control↔dynamics
    PAC measurement (with tolerance) — a regression in that number breaks the polyphony
    structural claim of the default 3-voice meta-sim.

Run:
    python -m pytest tests/test_meta_sim.py -v
"""
from __future__ import annotations
import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import pytest
import numpy as np

from meta_sim import (
    Voice, MetaSim, make_default_meta_sim,
    closure_walk_meta, measure_cross_band_coupling,
)
from meta_sim.core import LOAD_PROFILES


# ---------------------------------------------------------------------------
# Voice class — single-voice substrate model
# ---------------------------------------------------------------------------

class TestVoice:
    """Voice = one timescale's substrate model."""

    def _simple_voice(self):
        def step_fn(state, inp):
            return 0.9 * state + 0.1 * inp
        return Voice("test_filter", "fast", 4, step_fn)

    def test_voice_initializes_with_zero_state(self):
        v = self._simple_voice()
        assert v.state.shape == (4,)
        assert np.allclose(v.state, 0.0)

    def test_voice_step_advances_state(self):
        v = self._simple_voice()
        new_state = v.step(np.array([1.0, 1.0, 1.0, 1.0]))
        assert new_state.shape == (4,)
        assert np.allclose(new_state, 0.1)

    def test_voice_step_is_persistent(self):
        """Calling step twice should compound the state, not reset it."""
        v = self._simple_voice()
        v.step(np.array([1.0, 1.0, 1.0, 1.0]))
        s2 = v.step(np.array([1.0, 1.0, 1.0, 1.0]))
        # second step: 0.9 * 0.1 + 0.1 * 1.0 = 0.19
        assert np.allclose(s2, 0.19)

    def test_voice_reset_zeroes_state(self):
        v = self._simple_voice()
        v.step(np.array([1.0, 1.0, 1.0, 1.0]))
        v.reset()
        assert np.allclose(v.state, 0.0)


# ---------------------------------------------------------------------------
# MetaSim — orchestrates voices with cross-band coupling
# ---------------------------------------------------------------------------

class TestMetaSim:
    """MetaSim composes voices + steps cleanly."""

    def setup_method(self):
        self.meta = make_default_meta_sim()

    def test_default_meta_has_three_voices(self):
        assert len(self.meta.voices) == 3
        names = [v.name for v in self.meta.voices]
        assert names == ["load_flow", "control", "dynamics"]

    def test_default_meta_has_documented_timescales(self):
        timescales = [v.timescale for v in self.meta.voices]
        assert timescales == ["slow", "mid", "fast"]

    def test_default_meta_has_cross_couplings(self):
        """The default meta wires load_flow→dynamics and control→dynamics couplings."""
        assert ("load_flow", "dynamics") in self.meta.coupling
        assert ("control", "dynamics") in self.meta.coupling

    def test_meta_step_returns_dict_with_all_voice_outputs(self):
        external = np.concatenate([LOAD_PROFILES["peak"], LOAD_PROFILES["peak"]])
        outputs = self.meta.step(external)
        assert set(outputs.keys()) == {"load_flow", "control", "dynamics"}

    def test_meta_fingerprint_concatenates_voice_states(self):
        """Fingerprint length = sum of voice state dims = 12 + 5 + 4 = 21."""
        external = np.concatenate([LOAD_PROFILES["peak"], LOAD_PROFILES["peak"]])
        self.meta.step(external)
        fp = self.meta.fingerprint()
        assert len(fp) == 12 + 5 + 4

    def test_meta_reset_zeroes_all_voices(self):
        external = np.concatenate([LOAD_PROFILES["peak"], LOAD_PROFILES["peak"]])
        self.meta.step(external)
        self.meta.reset()
        for v in self.meta.voices:
            assert np.allclose(v.state, 0.0)


# ---------------------------------------------------------------------------
# closure_walk_meta — cycle-residual measurement on the polyphonic substrate
# ---------------------------------------------------------------------------

class TestClosureWalkMeta:
    """closure_walk_meta returns a valid stability class + closure measurements."""

    def setup_method(self):
        self.meta = make_default_meta_sim()
        self.profiles = ["peak", "off_peak", "mixed", "spike", "peak"]

    def test_closure_walk_returns_required_fields(self):
        result = closure_walk_meta(self.meta, self.profiles)
        for key in ("n_stations", "n_voices", "voice_names",
                     "step_distances", "home_step", "mean_step", "cycle_residual", "stability_class"):
            assert key in result

    def test_stability_class_is_valid(self):
        result = closure_walk_meta(self.meta, self.profiles)
        assert result["stability_class"] in ("stable-cycle", "moderate-stress-cycle", "high-stress-cycle")

    def test_n_voices_matches_default_three(self):
        result = closure_walk_meta(self.meta, self.profiles)
        assert result["n_voices"] == 3
        assert result["voice_names"] == ["load_flow", "control", "dynamics"]

    def test_step_distances_non_negative(self):
        result = closure_walk_meta(self.meta, self.profiles)
        for d in result["step_distances"]:
            assert d >= 0


# ---------------------------------------------------------------------------
# measure_cross_band_coupling — the +0.832 empirical result
# ---------------------------------------------------------------------------

class TestCrossBandCoupling:
    """Locks the meta-sim's INTERNAL PAC measurement at ~+0.832.

    HONEST SCOPE (per pre-release review feedback): this number characterizes the meta-sim's
    own polyphony structure under random selection from the 4 hard-coded load profiles —
    it is determined by the coupling coefficients in `make_default_meta_sim()` plus the
    surrogate dynamics, NOT a comparison against real grid PAC measurements. The test
    catches regressions in the meta-sim's own structure. Validating against real-grid
    PAC requires an external dataset and a separate test suite — not in scope here.
    """

    def setup_method(self):
        self.meta = make_default_meta_sim()
        self.coupling = measure_cross_band_coupling(self.meta, n_steps=30, seed=42)

    def test_coupling_dict_has_all_pairs(self):
        """Three voices → three unique pairwise couplings."""
        assert "load_flow↔control" in self.coupling
        assert "load_flow↔dynamics" in self.coupling
        assert "control↔dynamics" in self.coupling

    def test_control_dynamics_pac_is_strong(self):
        """The headline empirical result: control↔dynamics correlation ~ +0.832.

        Tolerance ±0.05 to allow numerical drift across numpy versions / random ordering.
        Tighter than that and a real regression slips through; looser and we're not
        actually locking the claim.
        """
        pac = self.coupling["control↔dynamics"]
        assert 0.78 <= pac <= 0.88, \
            f"control↔dynamics PAC was {pac}, expected ~+0.832 (locked empirical claim)"

    def test_control_dynamics_pac_is_strongest(self):
        """Among the three pairs, control↔dynamics should be the strongest correlation
        — that's the cross-band-coupling signature of the meta-sim's polyphony."""
        c_d = abs(self.coupling["control↔dynamics"])
        l_c = abs(self.coupling["load_flow↔control"])
        l_d = abs(self.coupling["load_flow↔dynamics"])
        assert c_d > l_c, f"control↔dynamics ({c_d}) should exceed load_flow↔control ({l_c})"
        assert c_d > l_d, f"control↔dynamics ({c_d}) should exceed load_flow↔dynamics ({l_d})"

    def test_coupling_values_in_correlation_range(self):
        for pair, val in self.coupling.items():
            assert -1.0 <= val <= 1.0, f"{pair} = {val} outside [-1, 1]"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
