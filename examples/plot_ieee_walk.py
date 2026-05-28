# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""examples/plot_ieee_walk.py — IEEE cycle-walk visualization (matplotlib).

Addresses utility-engineer audience feedback: existing grid-simulator workflows
include plotting; this project shouldn't be an exception. This file runs the
same pre-registered cycle walk as `ieee_case_demo.py` and renders three views:

  1. Bus-voltage profiles per load scenario (case14, case30, case118).
  2. Step distances across the cycle walk for each case.
  3. Cycle-residual + path-excursion summary bar chart.

The plot is saved to disk (not shown interactively) so the example runs in
headless environments (CI, remote shells). Optional dependency: matplotlib —
without it, the file degrades gracefully to a text-only report.

Run:
    pip install matplotlib pypower
    python examples/plot_ieee_walk.py    # writes ieee_walk_plot.png

If matplotlib is missing, prints the same data tabular-style + suggests the
install. Same pre-registration discipline as `ieee_case_demo.py`.
"""
from __future__ import annotations
import sys
import os
from typing import Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

try:
    import numpy as np
except ImportError:
    raise SystemExit("numpy required. install with: pip install numpy")

try:
    import pypower.api as pp
except ImportError:
    raise SystemExit(
        "pypower required for this demo. install with: pip install pypower"
    )

try:
    import matplotlib
    matplotlib.use("Agg")    # headless backend; no display required
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# Reuse the pre-registration + walk shape from ieee_case_demo.py
SCENARIO_MULTIPLIERS = {"peak": 1.20, "off_peak": 0.55, "mixed": 1.00, "spike": 1.40}
WALK_ORDER = ["peak", "off_peak", "mixed", "spike", "peak"]


def collect_walk_data(case_fn, case_name: str) -> dict:
    """Run pre-registered walk + collect per-station bus voltages for plotting."""
    import copy
    PD, QD, VM = 2, 3, 7
    voltages_per_scenario = {}
    step_distances = []
    fingerprints = []
    total_gen = {}

    for scenario in WALK_ORDER:
        case = copy.deepcopy(case_fn())
        case["bus"][:, PD] *= SCENARIO_MULTIPLIERS[scenario]
        case["bus"][:, QD] *= SCENARIO_MULTIPLIERS[scenario]
        ppopt = pp.ppoption(PF_ALG=1, VERBOSE=0, OUT_ALL=0)
        result, success = pp.runpf(case, ppopt)
        if not success:
            continue
        voltages = result["bus"][:, VM].copy()
        voltages_per_scenario[scenario] = voltages
        # fingerprint discretization matches ieee_case_demo.py
        fp = np.array([int(round(v / 0.02)) for v in voltages])
        fingerprints.append(fp)
        total_gen[scenario] = float(result["gen"][:, 1].sum())

    for i in range(len(fingerprints) - 1):
        step_distances.append(float(np.linalg.norm(fingerprints[i + 1] - fingerprints[i])))
    closure_residual = float(np.linalg.norm(fingerprints[-1] - fingerprints[0])) if fingerprints else 0.0
    path_excursion = float(sum(step_distances))

    return {
        "case_name":        case_name,
        "voltages":         voltages_per_scenario,
        "step_distances":   step_distances,
        "closure_residual": closure_residual,
        "path_excursion":   path_excursion,
        "total_gen_MW":     total_gen,
    }


def plot_walk_data(walk_data_list: list, output_path: str):
    """Render the three-panel summary to `output_path`."""
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    # Panel 1: per-scenario voltage profile for each case (mean + spread)
    ax = axes[0]
    scenarios = WALK_ORDER[:-1]  # drop the repeated "peak"
    x = np.arange(len(scenarios))
    width = 0.25
    for i, wd in enumerate(walk_data_list):
        means = [float(np.mean(wd["voltages"][s])) for s in scenarios]
        stds = [float(np.std(wd["voltages"][s])) for s in scenarios]
        ax.bar(x + i * width, means, width, yerr=stds, label=wd["case_name"], alpha=0.8, capsize=3)
    ax.set_xticks(x + width)
    ax.set_xticklabels(scenarios)
    ax.set_ylabel("bus voltage magnitude (p.u.)")
    ax.set_title("Bus-voltage profile per load scenario (mean ± std across buses)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 2: step distances across the cycle walk
    ax = axes[1]
    step_labels = [f"{a}→{b}" for a, b in zip(WALK_ORDER[:-1], WALK_ORDER[1:])]
    x = np.arange(len(step_labels))
    for i, wd in enumerate(walk_data_list):
        ax.plot(x, wd["step_distances"], marker="o", label=wd["case_name"], linewidth=2)
    ax.set_xticks(x)
    ax.set_xticklabels(step_labels, rotation=10)
    ax.set_ylabel("step distance (fingerprint units)")
    ax.set_title("Cycle-walk step distances")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 3: summary bar chart — closure_residual + path_excursion per case
    ax = axes[2]
    names = [wd["case_name"] for wd in walk_data_list]
    x = np.arange(len(names))
    closure = [wd["closure_residual"] for wd in walk_data_list]
    excursion = [wd["path_excursion"] for wd in walk_data_list]
    ax.bar(x - 0.2, closure, 0.4, label="closure_residual", color="steelblue")
    ax.bar(x + 0.2, excursion, 0.4, label="path_excursion", color="coral")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("magnitude (fingerprint units)")
    ax.set_title("Cycle-walk dual scalars: closure_residual + path_excursion")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close()


def text_only_report(walk_data_list: list):
    """Tabular text fallback when matplotlib isn't installed."""
    print(f"\n{'case':10s}  {'closure_residual':>18s}  {'path_excursion':>16s}")
    for wd in walk_data_list:
        print(f"{wd['case_name']:10s}  {wd['closure_residual']:>18.4f}  {wd['path_excursion']:>16.4f}")
    print(f"\n(install matplotlib for graphical summary: pip install matplotlib)")


def main():
    print("=" * 72)
    print("IEEE cycle-walk visualization — case14 + case30 + case118")
    print("=" * 72)

    walk_data = []
    for case_fn, case_name in [(pp.case14, "case14"), (pp.case30, "case30"), (pp.case118, "case118")]:
        print(f"  collecting {case_name}...")
        walk_data.append(collect_walk_data(case_fn, case_name))

    if MATPLOTLIB_AVAILABLE:
        out_path = os.path.join(REPO_ROOT, "ieee_walk_plot.png")
        plot_walk_data(walk_data, out_path)
        print(f"\nplot saved to: {out_path}")
        print(f"  panels: (1) bus-voltage profile per scenario, (2) cycle-walk step distances,")
        print(f"          (3) closure_residual + path_excursion dual-scalar summary")
    else:
        text_only_report(walk_data)


if __name__ == "__main__":
    main()
