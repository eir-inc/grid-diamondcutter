# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""meta_sim — polyphonic meta-simulator for the power-grid substrate.

Public API:
  from meta_sim import MetaSim, Voice, make_default_meta_sim
  from meta_sim import closure_walk_meta, cycle_walk_meta, measure_cross_band_coupling

See meta.py for the implementation + the empirical +0.832 control↔dynamics PAC result.
"""
from meta_sim.meta import (
    Voice,
    MetaSim,
    make_default_meta_sim,
    closure_walk_meta, cycle_walk_meta,
    measure_cross_band_coupling,
)
__all__ = ["Voice", "MetaSim", "make_default_meta_sim", "closure_walk_meta", "measure_cross_band_coupling"]
