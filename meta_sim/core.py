# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""meta_sim.core — topology constants + load/generation profiles for the meta-sim.

These are self-contained (no imports from the root single-file) so the meta_sim
package works as a drop-in module. The values mirror the root power_grid_sim.py
canonical grid; keep in sync if either changes.
"""
import numpy as np

N_GENS = 4
N_LOADS = 4
EDGES = [
    (0, 4), (0, 5), (1, 4), (1, 6), (2, 5), (2, 7),
    (3, 6), (3, 7), (4, 5), (5, 6), (6, 7), (4, 7),
]
N_LINES = len(EDGES)
DEFAULT_LINE_CAPACITY = 100.0

LOAD_PROFILES = {
    "peak":     np.array([60.0, 80.0, 70.0, 90.0]),
    "off_peak": np.array([20.0, 30.0, 15.0, 25.0]),
    "mixed":    np.array([60.0, 25.0, 80.0, 30.0]),
    "spike":    np.array([40.0, 40.0, 95.0, 40.0]),
}
GEN_PROFILES = {
    "peak":     np.array([80.0, 80.0, 80.0, 80.0]),
    "off_peak": np.array([30.0, 30.0, 30.0, 30.0]),
    "mixed":    np.array([50.0, 50.0, 50.0, 60.0]),
    "spike":    np.array([60.0, 60.0, 75.0, 60.0]),
}

__all__ = ["LOAD_PROFILES", "GEN_PROFILES", "EDGES", "N_GENS", "N_LINES", "DEFAULT_LINE_CAPACITY"]
