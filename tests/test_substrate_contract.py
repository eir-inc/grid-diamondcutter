# Copyright 2026 Eir Inc
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""tests/test_substrate_contract.py — substrate-plugin contract conformance tests.

The contract is the foundation. If a substrate doesn't conform to this contract, none of the
pipeline primitives (route_adaptive, closure_walk, axis_attribution) work on it. These tests
lock the contract in writing — any voice / adapter contributor can run these against their
substrate before opening a PR.

Run:
    python -m pytest tests/test_substrate_contract.py -v
"""
from __future__ import annotations
import sys
import os

# allow running from repo root or tests/ directory
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import pytest

from grid_diamondcutter_oss import (
    BridgeParams, Substrate, make_evaluator, grid_substrate, GRID_STATES, CONTROLS,
    heuristic_voice, ensemble_voices, route_adaptive, closure_walk,
)


# ---------------------------------------------------------------------------
# 1. Substrate contract — the five functions must exist and have the right shape
# ---------------------------------------------------------------------------

class TestSubstrateContract:
    """The Substrate dataclass + its five callables form the contract."""

    def setup_method(self):
        self.sub = grid_substrate()
        self.p = BridgeParams("steady", "overload", 0.5, 0.5)

    def test_substrate_has_required_fields(self):
        """name, reversal_primitive, percolation_axis, data_source must all be strings."""
        assert isinstance(self.sub.name, str) and self.sub.name
        assert isinstance(self.sub.reversal_primitive, str) and self.sub.reversal_primitive
        assert isinstance(self.sub.percolation_axis, str) and self.sub.percolation_axis
        assert isinstance(self.sub.data_source, str) and self.sub.data_source

    def test_substrate_has_required_callables(self):
        """reach, cost, lifetime, window, forward must all be callable."""
        assert callable(self.sub.reach)
        assert callable(self.sub.cost)
        assert callable(self.sub.lifetime)
        assert callable(self.sub.window)
        assert callable(self.sub.forward)

    def test_reach_returns_tuple(self):
        """reach(p) must return a tuple — used as a dict key in catalogues."""
        fp = self.sub.reach(self.p)
        assert isinstance(fp, tuple)
        # tuples must be hashable (dict-key-able)
        d = {fp: 1}
        assert d[fp] == 1

    def test_cost_returns_float(self):
        """cost(p) must return a number."""
        c = self.sub.cost(self.p)
        assert isinstance(c, (int, float))
        assert c >= 0

    def test_lifetime_returns_float(self):
        """lifetime(p) must return a number."""
        l = self.sub.lifetime(self.p)
        assert isinstance(l, (int, float))
        assert l >= 0

    def test_window_returns_bool(self):
        """window(p) must return a bool."""
        w = self.sub.window(self.p)
        assert isinstance(w, bool)

    def test_forward_returns_set(self):
        """forward() must return a set of fingerprints — used as novelty reference."""
        fwd = self.sub.forward()
        assert isinstance(fwd, set)
        # all elements must be tuples (same shape as reach() output)
        for fp in fwd:
            assert isinstance(fp, tuple)


# ---------------------------------------------------------------------------
# 2. make_evaluator — wraps a Substrate into an Evaluator function
# ---------------------------------------------------------------------------

class TestMakeEvaluator:
    """make_evaluator(sub) should return a callable that produces StateMetrics."""

    def setup_method(self):
        self.sub = grid_substrate()
        self.ev = make_evaluator(self.sub)

    def test_evaluator_is_callable(self):
        assert callable(self.ev)

    def test_evaluator_returns_state_metrics(self):
        """Evaluator should produce a StateMetrics-shaped result with all four fields."""
        m = self.ev(BridgeParams("steady", "overload", 0.5, 0.5))
        assert hasattr(m, "state_id")
        assert hasattr(m, "novel")
        assert hasattr(m, "cost")
        assert hasattr(m, "lifetime")
        assert isinstance(m.state_id, str)
        assert isinstance(m.novel, bool)
        assert isinstance(m.cost, (int, float))
        assert isinstance(m.lifetime, (int, float))


# ---------------------------------------------------------------------------
# 3. Voices pattern — ensemble + graceful-degrade
# ---------------------------------------------------------------------------

class TestVoicesPattern:
    """The meta-sim's voices-pattern: heuristic always-available, optional sims gracefully degrade."""

    def test_heuristic_voice_always_active(self):
        """The heuristic voice ships with the file and must always work."""
        p = BridgeParams("steady", "overload", 0.5, 0.5)
        result = heuristic_voice(p)
        assert result is not None
        activated, cost = result
        assert len(activated) == len(CONTROLS)
        assert cost >= 0

    def test_ensemble_voices_returns_three_tuple(self):
        """ensemble_voices(p) → (activated_vector, mean_cost, voices_heard_list)."""
        p = BridgeParams("steady", "overload", 0.5, 0.5)
        activated, cost, voices = ensemble_voices(p)
        assert len(activated) == len(CONTROLS)
        assert cost >= 0
        assert isinstance(voices, list)
        # heuristic must always be one of the voices heard
        assert "heuristic" in voices

    def test_ensemble_voices_handles_missing_optional_voices(self):
        """If pypower / pandapower aren't installed, ensemble still works (graceful degrade)."""
        p = BridgeParams("fault", "restoration", 0.5, 0.5)
        activated, cost, voices = ensemble_voices(p)
        # heuristic gives us at least 1 voice; optional voices may or may not be present
        assert len(voices) >= 1


# ---------------------------------------------------------------------------
# 4. route_adaptive — the catalogue-building primitive
# ---------------------------------------------------------------------------

class TestRouteAdaptive:
    """route_adaptive returns (confirmed_dict, dropped_list); shape + invariants."""

    def setup_method(self):
        self.sub = grid_substrate()
        self.ev = make_evaluator(self.sub)
        self.space = [BridgeParams(a, b, d, beta)
                      for a in GRID_STATES for b in GRID_STATES if a != b
                      for d in (0.3, 0.6)
                      for beta in (0.1, 0.5)]

    def test_route_adaptive_returns_two_collections(self):
        confirmed, dropped = route_adaptive(self.ev, self.space, lifetime_threshold=3.0)
        assert isinstance(confirmed, dict)
        assert isinstance(dropped, list)

    def test_confirmed_recipes_all_have_required_keys(self):
        confirmed, _ = route_adaptive(self.ev, self.space, lifetime_threshold=3.0)
        for state_id, rec in confirmed.items():
            assert "recipe" in rec
            assert "cost" in rec
            assert "lifetime" in rec
            assert "score" in rec
            assert isinstance(rec["recipe"], BridgeParams)

    def test_confirmed_recipes_all_clear_lifetime_threshold(self):
        threshold = 3.0
        confirmed, _ = route_adaptive(self.ev, self.space, lifetime_threshold=threshold)
        for state_id, rec in confirmed.items():
            assert rec["lifetime"] >= threshold, \
                f"confirmed recipe {state_id} has lifetime {rec['lifetime']} below threshold {threshold}"


# ---------------------------------------------------------------------------
# 5. closure_walk — the cycle-residual measurement primitive
# ---------------------------------------------------------------------------

class TestClosureWalk:
    """closure_walk must return a dict with cycle-residual magnitude + stability class."""

    def setup_method(self):
        self.sub = grid_substrate()
        self.ev = make_evaluator(self.sub)
        self.stations = [
            BridgeParams("steady", "overload", 0.5, 0.5),
            BridgeParams("overload", "fault", 0.5, 0.5),
            BridgeParams("fault", "restoration", 0.5, 0.5),
            BridgeParams("restoration", "cascade", 0.5, 0.5),
            BridgeParams("cascade", "steady", 0.5, 0.5),
        ]

    def test_closure_walk_returns_required_fields(self):
        cw = closure_walk(self.ev, self.stations)
        assert "n_stations" in cw
        assert "step_distances" in cw
        assert "return_distance" in cw
        assert "cycle_residual" in cw
        assert "stability_class" in cw

    def test_stability_class_is_one_of_three_classes(self):
        cw = closure_walk(self.ev, self.stations)
        assert cw["stability_class"] in ("stable-cycle", "high-stress (opens)", "high-stress (closes)")

    def test_step_distances_match_station_count(self):
        cw = closure_walk(self.ev, self.stations)
        # step_distances has one entry per transition between consecutive stations
        assert len(cw["step_distances"]) == len(self.stations) - 1

    def test_step_distances_non_negative(self):
        cw = closure_walk(self.ev, self.stations)
        for d in cw["step_distances"]:
            assert d >= 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
