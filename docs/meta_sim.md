# meta_sim — the polyphonic substrate

The `meta_sim` package models a power grid as a *polyphonic substrate*: multiple
substrate models, operating at different timescales, wired together with cross-band
coupling. The package is independent of the single-file `power_grid_sim.py` —
both demonstrate the project's `Substrate` contract from different angles.

## Why polyphony

Real power grids have multiple physical layers that operate at different timescales:

| Layer | Timescale | Existing simulators that cover it well |
|---|---|---|
| Load flow | seconds–minutes | MATPOWER, pandapower, PYPOWER |
| Voltage / frequency control | minutes | OpenDSS, GridLAB-D |
| Transient dynamics | milliseconds–seconds | PSCAD, Simulink |
| Outage / contingency | event timescale | PowerWorld, DIgSILENT |

No single existing simulator captures all four together. The cross-layer coupling
— where the slow control voice modulates the fast dynamics voice's amplitude,
for instance — is precisely what gets lost when each layer is studied in isolation.

`meta_sim` models the polyphony directly: each substrate layer is a `Voice` with
its own state and step function; voices are wired through `MetaSim` with explicit
cross-band coupling.

## The `Voice` abstraction

A `Voice` is a substrate model at one timescale. The minimal interface:

```python
from meta_sim import Voice
import numpy as np

def my_step_fn(state, input_signal):
    return 0.9 * state + 0.1 * input_signal

voice = Voice(
    name="my_voice",
    timescale="fast",        # 'slow' | 'mid' | 'fast'
    state_dim=4,
    step_fn=my_step_fn,
)
```

The `Voice` maintains its state across `.step()` calls. Reset via `.reset()`.

## Swapping in an existing simulator

The `step_fn` is the only required behavior; everything else is housekeeping.
That means an existing simulator can wrap as a Voice:

```python
def matpower_load_flow_step(state, inp):
    """state = previous line utilizations; inp = (loads, generations)."""
    # convert inp to MATPOWER's case format
    # run pypower.runpf or similar
    # extract line utilizations from result
    # return as numpy array, same shape as state
    ...

load_flow_voice = Voice("matpower_loadflow", "slow", N_LINES, matpower_load_flow_step)
```

The grid simulator stays where it is; the project wraps it as a Voice for the
specific purpose of measuring cross-band coupling. No re-implementation required.

## The `MetaSim` orchestrator

`MetaSim` advances voices in order, threading the previous voice's output into
the next voice's input. Cross-band coupling adds extra connections beyond the
default cascade:

```python
from meta_sim import MetaSim, Voice

meta = MetaSim(
    voices=[load_flow_voice, control_voice, dynamics_voice],
    coupling={
        ("load_flow", "dynamics"): 0.15,  # slow phase → fast amplitude
        ("control",   "dynamics"): 0.20,
    },
)
```

Each step: the first voice receives the external input; subsequent voices receive
the previous voice's output, plus any extra contributions specified in the
`coupling` map.

## Measuring cross-band coupling

The `measure_cross_band_coupling()` function runs the meta-sim under random
perturbation and computes pairwise correlations between voice state norms:

```python
from meta_sim import make_default_meta_sim, measure_cross_band_coupling

meta = make_default_meta_sim()
coupling = measure_cross_band_coupling(meta, n_steps=30, seed=42)
# {'load_flow↔control': -0.073, 'load_flow↔dynamics': 0.058, 'control↔dynamics': 0.832}
```

The strong `control↔dynamics` correlation (+0.832) in the default 3-voice
configuration is the project's reference measurement of cross-band coupling.
It is reproducible from the committed code with seed=42; the value is pinned by
`tests/test_meta_sim.py`.

This measurement *demonstrates* that the cross-band-coupling shape exists in the
meta-substrate the project constructed. It does not measure coupling in any real
grid the project has not built. Honest-bounds scoping for this measurement is in
`PREREGISTRATION.md` §1.

## Measuring closure on the meta-substrate

The `cycle_walk_meta()` (and its backward-compatible alias `closure_walk_meta`)
runs the standard cycle-walk on the meta-substrate's polyphonic fingerprint:

```python
from meta_sim import make_default_meta_sim, cycle_walk_meta

meta = make_default_meta_sim()
result = cycle_walk_meta(meta, ["peak", "off_peak", "mixed", "spike", "peak"])
# {'cycle_residual': -0.0597, 'stability_class': 'stable-cycle', ...}
```

The meta-substrate's cycle_residual is computed on the concatenated state of all
voices — a fingerprint no single voice captures alone.

## Authoring a new voice

Adding a Voice to the meta-sim is one PR. The Voice can wrap an existing
simulator backend, implement custom physics, or be a thin heuristic. The
constraint is the `step_fn` signature: `(state_t, input_t) -> state_{t+1}`.

For a Voice that enters the project's voice registry (per `PREREGISTRATION.md` §3
and the protocol in `examples/voices/`), the Voice's measurement is wrapped as a
5-field unit with a predict / kill-condition / run / verdict shape. See
`examples/voices/README.md` for the authoring protocol.

## What this package does not do

Per `PREREGISTRATION.md` §1, the meta_sim package does not:

- Solve DC or AC power flow numerically. Voices in the default configuration are
  heuristic; production-grade voices wrap real solvers.
- Predict real-grid coupling magnitudes. The +0.832 reference measurement is
  between two simulated voices the project authored; it demonstrates the
  measurement shape, not a claim about any real grid.
- Replace existing grid simulators. The package wraps existing simulators as
  voices; it does not reimplement them.
