# For Grid Engineers — a translation layer

This document is for engineers who've used PYPOWER, PandaPower, OpenDSS, MATPOWER, or GridLAB-D and want to understand `diamondcutter-grid` in vocabulary they already know. It's a translation layer, not a replacement for the methodology doc; once the mapping is clear, the rest reads more easily.

If you've never touched a load-flow simulator, skip this and read [`docs/methodology.md`](methodology.md) directly.

## Table of contents

1. [The 60-second version](#the-60-second-version)
2. [Vocabulary mapping](#vocabulary-mapping)
3. [Workflow side-by-side](#workflow-side-by-side)
4. [Hello-world example](#hello-world-example)
5. [Working with IEEE test cases](#working-with-ieee-test-cases)
6. [Plugging in your own load-flow solver](#plugging-in-your-own-load-flow-solver)
7. [What this sim does NOT do](#what-this-sim-does-not-do)
8. [FAQ from grid engineers](#faq-from-grid-engineers)

---

## The 60-second version

If you've used PYPOWER:

```python
# PYPOWER style: solve a single steady-state
from pypower.api import runpf, case14
result = runpf(case14())
# → you get voltages, line flows, mismatches for ONE operating point
```

`diamondcutter-grid` adds one more measurement on top of that workflow: it answers **"what's the cyclic stability class of this grid under realistic operating profiles?"**

```python
# diamondcutter style: characterize the substrate's CYCLE behavior
from grid_diamondcutter_oss import (
    BridgeParams, grid_substrate, make_evaluator, closure_walk,
)
sub = grid_substrate()                  # heuristic 8-node surrogate (swap your network in via voice pattern)
ev = make_evaluator(sub)
stations = [
    BridgeParams("steady",      "overload",    0.5, 0.5),
    BridgeParams("overload",    "fault",       0.5, 0.5),
    BridgeParams("fault",       "restoration", 0.5, 0.5),
    BridgeParams("restoration", "cascade",     0.5, 0.5),
    BridgeParams("cascade",     "steady",      0.5, 0.5),
]
result = closure_walk(ev, stations)
# → result["cycle_residual"] + result["stability class"] summarize the substrate's cyclic behavior
```

Note: the 5-state regime vocabulary (`steady / overload / fault / restoration / cascade`) is
the `grid_diamondcutter_oss.py` voices-pattern surrogate. The single-voice `power_grid_sim.py`
file uses a parallel 4-profile vocabulary (`peak / off_peak / mixed / spike`) for its DC-allocation
heuristic. The two sims are complementary; pick whichever maps better to your existing operating
scenarios + plug your real load-flow solver in as a voice.

The stability class is a single scalar verdict on the grid's cyclic efficiency that survives across all the per-bus, per-line load-flow detail. It does NOT replace load-flow analysis — it sits on top of whatever load-flow solver you trust.

## Vocabulary mapping

| diamondcutter term | what it means in grid-engineering vocabulary |
|---|---|
| **substrate** | the grid network — buses, lines, generators, loads. Equivalent to a PYPOWER `case` dict or a PandaPower `net`. |
| **regime** (`regime_a`, `regime_b`) | a named operating scenario — "peak", "off_peak", "mixed", "spike". You provide load + generation profiles per regime. |
| **bridge** / `BridgeParams` | a recipe describing a transition between two regimes, plus two scalar modulation parameters (`depth`, `beta`). Think of it as a load-following sequence. |
| **reach()** | the network's fingerprint under a given bridge. Output is a hashable tuple — the discrete state-id the substrate occupies. Roughly analogous to "result of runpf with this bridge as input" reduced to a fingerprint. |
| **cost()** | the operational cost of running that bridge. Use whatever cost-function you trust — economic dispatch, line-loss, control-action count, MW-hours. |
| **lifetime()** | how long the resulting operating point stays stable before requiring re-dispatch. In a real grid, this could be ramp-limit-derived. |
| **window()** | a boolean: is this bridge in your operating envelope? Use this to encode N-1 contingency feasibility or stability constraints. |
| **forward()** | the set of "baseline" fingerprints — the fingerprints that result from same-regime transitions (no scenario change). The novelty reference. |
| **cycle walk** | run a cyclic sequence of bridges through the substrate, measure how far the final state drifts from the starting state. The drift is the **cycle residual**. |
| **cycle residual** | residual cyclic inefficiency. Equivalent in spirit to: "after one daily load cycle, how far has accumulated stress moved the grid away from where it started?" |
| **stability class** | the verdict — `stable` (stable, minimal intervention), `moderate-stress` (moderate cyclic stress), or `high-stress` (high cyclic stress, frequent operator action required). |
| **route_adaptive** | a search that enumerates the cheapest-durable bridges. Outputs a CATALOGUE — your minimal-action playbook for the substrate. |
| **catalogue** | the output of route_adaptive: a dict of `{state_fingerprint: recipe}` mapping each reachable durable state to the cheapest bridge that reaches it. Think of it as the substrate's minimal operating playbook. |
| **voice** | one substrate model. In the meta-sim, multiple voices (load-flow / control / dynamics) run at different timescales and cross-couple, similar to slow/fast EMS layers. |

## Workflow side-by-side

### PYPOWER workflow (what you do today)

```python
from pypower.api import runpf, case14
import pypower.api as pp

case = case14()
case["bus"][9, pp.PD] = 2.5    # set load at bus 9
result = runpf(case)
# inspect: result['gen'], result['branch']
```

You solve a single operating point and inspect post-solve quantities.

### diamondcutter-grid workflow

```python
from power_grid_sim import GridSubstrate, BridgeParams, route_adaptive, closure_walk

sub = GridSubstrate()    # uses the 8-node DC model; substitute your network in

# Step 1: build the catalogue
space = [BridgeParams(a, b, d, beta)
         for a in ["peak", "off_peak", "mixed", "spike"]
         for b in ["peak", "off_peak", "mixed", "spike"] if a != b
         for d in (0.3, 0.6)
         for beta in (0.1, 0.5)]
catalogue, dropped = route_adaptive(sub, space, lifetime_threshold=3.0)

# Step 2: measure the substrate's cycle residual
stations = [
    BridgeParams("peak",     "off_peak", 0.5, 0.5),
    BridgeParams("off_peak", "mixed",    0.5, 0.5),
    BridgeParams("mixed",    "spike",    0.5, 0.5),
    BridgeParams("spike",    "peak",     0.5, 0.5),
]
walk = closure_walk(sub, stations)
print(f"stability class: {walk['stability_class']}, cycle residual: {walk['cycle_residual']:.4f}")
```

You build a catalogue of efficient bridges + measure the cyclic stability class. Both are summary artifacts — orders of magnitude smaller than raw operating logs.

## Hello-world example

The shortest possible end-to-end run:

```bash
git clone <repo-url> diamondcutter-grid
cd diamondcutter-grid
pip install numpy
python power_grid_sim.py
```

Expected output (full numbers in `reproducibility_hashes.json`):

```
CATALOGUE: 36 manufacturably-novel operating regimes
CYCLE WALK (5 stations rotating load profiles):
  cycle residual: -0.0465  →  stability class: stable
```

That's it. No config files, no command-line flags, no install dance. If you have `numpy`, you have a running diamondcutter measurement.

## Working with IEEE test cases

The shipped 8-node DC model is a teaching example. For real work you'll want to plug in IEEE test cases (`case14`, `case30`, `case118`, etc.). The pattern:

```python
from pypower.api import case14, runpf
from power_grid_sim import Substrate

def reach_via_pypower(p):
    """A reach() that delegates to PYPOWER's load-flow solver."""
    case = case14()
    # ...map p.regime_a + p.regime_b to perturbations of the case
    result = runpf(case)
    return tuple(round(v, 2) for v in result["bus"][:, 7])    # bus voltage magnitudes

def cost_via_pypower(p):
    case = case14()
    # ...same mapping
    result = runpf(case)
    return float(result["gen"][:, 1].sum())                    # total generation MW

# build your Substrate with these callbacks + run the diamondcutter pipeline as above.
```

The meta-sim (`meta_sim_v2.py`) extends this to multiple voices simultaneously — one voice per solver if you want PYPOWER + PandaPower + OpenDSS running in parallel as a chorus.

## Plugging in your own load-flow solver

This is the **voice pattern** in `examples/voices_pattern.py`. Three real-world plug-in shapes:

1. **PYPOWER adapter** — uses `pypower.api.runpf` for load-flow; reads bus voltages + line flows; returns the diamondcutter fingerprint.
2. **PandaPower adapter** — uses `pp.runpp(net)`; reads `net.res_bus.vm_pu`; returns the fingerprint.
3. **OpenDSS adapter** — invokes OpenDSS via `dss-python`; reads circuit object voltages.

Each adapter implements the same shape: `(BridgeParams) → (activated_vector, cost)`. The meta-sim's `ensemble_voices()` function averages across whichever voices report results, gracefully degrading to numpy-only heuristics if no real solver is installed. See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for the contribution path.

## What this sim does NOT do

To set expectations clearly:

- **It does not run a full transient-stability solver.** For sub-cycle dynamics use PSS/E, DSATools, or your existing tool. The dynamics voice in our meta-sim is a simplified surrogate.
- **It does not solve unit commitment.** For UC use FERC tools, MATPOWER's MOST, or commercial tools. We're measuring substrate-shape, not dispatching.
- **It does not perform fault analysis.** No short-circuit currents, no protection coordination. Use your existing fault tools.
- **It is not a replacement for SCADA / EMS.** It's a methodology layer that sits ABOVE your existing tools, measuring cyclic efficiency. Don't unplug your EMS.

What it DOES do: tell you, in one scalar verdict per substrate, **how much cyclic efficiency your control layer is leaving on the table**, and produce an audit-survivable artifact you can hand to your CFO + your regulator.

## FAQ from grid engineers

**Q: What's the relationship between cycle residual and standard grid stability metrics?**

A: Cycle residual measures *cyclic closure failure* under repeated load-profile rotation, not steady-state stability. A grid can be perfectly stable (no instabilities, no contingency violations) and still have a large cycle residual — meaning it's burning fuel on cyclic inefficiency that it could be operating cheaper. Cycle residual is a complementary measurement, not a replacement.

**Q: How does stability class map to a grid I'd actually plan?**

A: Roughly:
- *stable*: your grid is well-matched to its load profile. Minimal cyclic intervention needed. (Most idealized planning studies.)
- *moderate-stress*: moderate cyclic stress. Periodic rebalancing in the EMS catches most issues. (Most real grids.)
- *high-stress*: high cyclic stress. Operators are intervening frequently to keep the substrate within bounds. (Stressed grids — coastal under heavy renewable integration, or aging infrastructure under modern load patterns.)

**Q: Can I use this for renewables integration planning?**

A: Yes — that's the main commercial use case. The cycle walk measures how a given grid responds to *cyclic* load + generation patterns, which is precisely what renewables introduce (diurnal solar, multi-day wind cycles, EV charging waves). A grid that's stable under fossil-baseline load can become high-stress under a renewable mix — and the diamondcutter measures that without requiring a year of operational logs.

**Q: Is the closed-source eirmath package required to use this OSS sim?**

A: No. The OSS sim measures + catalogues standalone. `eirmath` adds the conducting policy + signed invoice generation + lineage tracking — useful when you want audit-survivable measurements for regulatory or commercial purposes. For methodology learning + internal characterization, the OSS sim is sufficient.

**Q: How do I cite this in a paper?**

A: We'll provide a CITATION.cff and a DOI when the v1.0 release lands. For pre-release citation, reference: *Eir Inc, diamondcutter-grid, 2026, [https://github.com/eir-inc/grid-diamondcutter-oss](https://github.com/eir-inc/grid-diamondcutter-oss)*.

**Q: Who's behind this?**

A: Eir Inc — see [`CONTRIBUTING.md`](../CONTRIBUTING.md) for the contributor list + lineage / attribution model. The methodology generalizes earlier work in chemistry/materials/biological-substrate measurement (the cycle-walk + stability class-class framework was originally developed for non-grid substrates and ported here unchanged).

---

**Found something unclear?** Open an issue. Better yet — open a PR with a clearer paragraph. This file is meant to be the friendliest entry point for engineers coming from existing grid tools; if it isn't doing that job, fix it.
