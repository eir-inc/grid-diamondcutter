# Copyright 2026 Eir Inc
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""tests/test_pipeline_integration.py — end-to-end pipeline tests.

Locks the FULL CHAIN at the contract boundary: substrate → route_adaptive → closure_walk →
prevention-based invoice math. Unit tests (test_substrate_contract.py, test_meta_sim.py) cover
each primitive in isolation; this file catches integration regressions — when individual
units pass but their composition breaks.

The invoice math itself lives in the closed `eirmath` package (per the open-core
split: open substrate + measurement primitives; closed conducting policy + signed invoice).
What this test verifies in the OSS layer is that the MEASUREMENTS the closed toolkit consumes
have the right shape + ordering + invariants.

Run:
    python -m pytest tests/test_pipeline_integration.py -v
"""
from __future__ import annotations
import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import pytest
import numpy as np

from grid_diamondcutter_oss import (
    BridgeParams, grid_substrate, make_evaluator, GRID_STATES, CONTROLS,
    route_adaptive, closure_walk,
)


# ---------------------------------------------------------------------------
# End-to-end: substrate → catalogue → walk → measurement chain
# ---------------------------------------------------------------------------

class TestEndToEndPipeline:
    """Locks the full chain: substrate produces a catalogue, then a walk, then measurements
    in the right shape for a downstream pricing layer to consume."""

    def setup_method(self):
        self.sub = grid_substrate()
        self.ev = make_evaluator(self.sub)
        self.space = [
            BridgeParams(a, b, d, beta)
            for a in GRID_STATES for b in GRID_STATES if a != b
            for d in (0.3, 0.6, 0.9)
            for beta in (0.1, 0.5, 0.9)
        ]
        self.stations = [
            BridgeParams("steady",      "overload",    0.5, 0.5),
            BridgeParams("overload",    "fault",       0.5, 0.5),
            BridgeParams("fault",       "restoration", 0.5, 0.5),
            BridgeParams("restoration", "cascade",     0.5, 0.5),
            BridgeParams("cascade",     "steady",      0.5, 0.5),
        ]

    def test_catalogue_then_walk_both_succeed(self):
        """The two pipeline primitives compose without crashing."""
        cat, dropped = route_adaptive(self.ev, self.space, lifetime_threshold=3.0)
        cw = closure_walk(self.ev, self.stations)
        assert len(cat) > 0
        assert "cycle_residual" in cw

    def test_catalogue_size_in_expected_range(self):
        """For the heuristic grid surrogate, route_adaptive should produce a non-trivial catalogue."""
        cat, _ = route_adaptive(self.ev, self.space, lifetime_threshold=3.0)
        # not empty, not catalogues-all-the-things (i.e. distinctness gate is working)
        assert 1 < len(cat) < len(self.space), \
            f"catalogue size {len(cat)} suspicious (space={len(self.space)})"

    def test_invoice_math_shape(self):
        """The closed pricing toolkit consumes (|cycle_residual|, cycle_life, cut_fraction) → invoice unit.
        OSS layer must produce |cycle_residual| in a shape that supports this multiplication."""
        cw = closure_walk(self.ev, self.stations)
        residual_magnitude = abs(cw["cycle_residual"])
        cycle_life = 5.0   # placeholder; closed toolkit computes this from substrate properties
        cut_fraction = 0.12   # placeholder; commercial-policy term

        invoice_unit = residual_magnitude * cycle_life * cut_fraction
        assert invoice_unit >= 0
        assert isinstance(invoice_unit, float)

    def test_stability_class_determines_pricing_tier(self):
        """The stability class is the substrate-shape summary that determines downstream
        commercial tier. OSS layer guarantees the class enum is one of three values."""
        cw = closure_walk(self.ev, self.stations)
        assert cw["stability_class"] in (
            "stable-cycle",
            "high-stress (opens)",
            "high-stress (closes)",
        )

    def test_catalogue_ordering_invariant(self):
        """Catalogue entries should all share the same score formula (cost / lifetime).
        A downstream conducting policy relies on this ordering."""
        cat, _ = route_adaptive(self.ev, self.space, lifetime_threshold=3.0)
        for state_id, rec in cat.items():
            expected_score = rec["cost"] / max(rec["lifetime"], 0.01)
            assert abs(rec["score"] - expected_score) < 0.01, \
                f"catalogue score for {state_id} = {rec['score']}, expected ~{expected_score}"


# ---------------------------------------------------------------------------
# Invariants — properties that must hold regardless of substrate specifics
# ---------------------------------------------------------------------------

class TestPipelineInvariants:
    """Invariants the contract guarantees no matter which substrate is plugged in."""

    def setup_method(self):
        self.sub = grid_substrate()
        self.ev = make_evaluator(self.sub)

    def test_higher_lifetime_threshold_yields_smaller_catalogue(self):
        """A tighter lifetime gate must produce a CATALOGUE NO LARGER than a looser gate.
        Monotonicity of the distinctness filter."""
        space = [
            BridgeParams(a, b, 0.5, 0.5)
            for a in GRID_STATES for b in GRID_STATES if a != b
        ]
        loose, _ = route_adaptive(self.ev, space, lifetime_threshold=0.0)
        tight, _ = route_adaptive(self.ev, space, lifetime_threshold=5.0)
        assert len(tight) <= len(loose), \
            f"tight gate ({len(tight)}) somehow produced larger catalogue than loose gate ({len(loose)})"

    def test_trivial_walk_has_small_cycle_residual(self):
        """A walk of one station (no transition) should have ~zero cycle residual — there's no
        cycle to accumulate stress over."""
        stations = [BridgeParams("steady", "overload", 0.5, 0.5)]
        cw = closure_walk(self.ev, stations)
        assert abs(cw["cycle_residual"]) < 0.1, \
            f"trivial 1-station walk had cycle_residual {cw['cycle_residual']}, expected ~0"
        assert len(cw["step_distances"]) == 0   # no transitions

    def test_voices_in_state_id_when_grid_substrate_used(self):
        """The grid substrate's reach() includes a voice-count field (n_voices) which makes
        meta-sim fingerprints distinguishable from single-voice substrates."""
        from grid_diamondcutter_oss import reach as grid_reach
        fp = grid_reach(BridgeParams("steady", "overload", 0.5, 0.5))
        # last element is n_voices (per the reach() implementation)
        n_voices = fp[-1]
        assert isinstance(n_voices, int)
        assert n_voices >= 1   # at least heuristic voice is always present


# ---------------------------------------------------------------------------
# Reproducibility — same input → same output across runs
# ---------------------------------------------------------------------------

class TestReproducibility:
    """Reproducibility is a customer-facing audit guarantee. Same substrate + same recipe
    must always produce the same fingerprint."""

    def setup_method(self):
        self.sub = grid_substrate()
        self.ev = make_evaluator(self.sub)
        self.p = BridgeParams("steady", "overload", 0.5, 0.5)

    def test_reach_is_deterministic(self):
        """Calling reach(p) twice must return identical fingerprints."""
        fp1 = self.sub.reach(self.p)
        fp2 = self.sub.reach(self.p)
        assert fp1 == fp2

    def test_cost_is_deterministic(self):
        c1 = self.sub.cost(self.p)
        c2 = self.sub.cost(self.p)
        assert c1 == c2

    def test_full_evaluator_is_deterministic(self):
        m1 = self.ev(self.p)
        m2 = self.ev(self.p)
        assert m1.state_id == m2.state_id
        assert m1.cost == m2.cost
        assert m1.lifetime == m2.lifetime
        assert m1.novel == m2.novel


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
