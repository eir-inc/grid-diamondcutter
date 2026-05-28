# grid-diamondcutter-oss

**`grid-diamondcutter-oss` is a single-file, Apache 2.0 power grid simulator for utility engineers, grid researchers, security teams, and FOSS contributors who want to measure the avoidable routing inefficiency in a grid's control layer — without sharing raw operating data.**

It runs in under one second on a stock Python + `numpy` install. No model calls. No API keys. No telemetry. `python power_grid_sim.py` from a fresh clone produces a complete demonstration, with reproducibility hashes for every published number.

## Honest scope (read this first)

This repository is an **evaluation artifact**, not a production grid simulator. The flow model inside `power_grid_sim.py` is a **heuristic allocator** (a `min(generator_capacity, load_demand)`-style flow distribution), not a B-bus / phase-angle DC power flow. It is sufficient to demonstrate the cycle-walk measurement and the route-adaptive search; it is not a substitute for MATPOWER, PYPOWER, OpenDSS, GridLAB-D, or PSS®E.

The polyphonic meta-sim (`power_grid_sim_v2.py` + `meta_sim/`) demonstrates a pattern of coupled multi-timescale voices. The cross-band coupling value of +0.832 reported in the published demo is the correlation produced by the **toy voice models with coupling coefficients we wrote into the code**. It is a demonstration of the *polyphony pattern*, not an empirically measured coupling on a real grid. Where real coupling magnitudes matter, the customer's own grid model — wired in behind the substrate-plugin contract — is the source of truth.

The repository is intended for evaluation, replication, methodology evaluation, and extension. Anyone integrating into a production environment should validate against their own grid model and consult their regulatory + safety framework.

## What ships

- `power_grid_sim.py` — single-voice baseline. 8-node toy grid, 4 generators + 4 loads + 12 lines. The file you DM to a grid engineer who has never heard of this project.
- `power_grid_sim_v2.py` + `meta_sim/` — polyphonic meta-sim. Three timescale-separated voices (load-flow, control, dynamics) with the cross-coupling pattern wired explicitly so a real grid model can replace each voice through the same contract.

## Who this is for

- **Utility engineers + grid operators** evaluating whether a cycle-walk measurement applies to their topology. Run the demo locally; wire in real grid models behind the contract.
- **Grid researchers** comparing how a single-model run compares to a coupled-voice meta-sim run on the same toy. The framework is small enough to read in one sitting.
- **Security auditors + regulators** verifying the measurement claims. Read every line; signatures are pure-Python `hmac` over canonical JSON. Reproducibility hashes published in `reproducibility_hashes.json`.
- **FOSS contributors** adding new grid voices (AC power flow, transient stability, market dispatch, distribution feeders). See `CONTRIBUTING.md`.

## How this relates to existing grid sims

This repository does not replace MATPOWER, PYPOWER, OpenDSS, GridLAB-D, pandapower, or PSS®E. It plugs **on top of** them through the substrate-plugin contract, and answers one question they don't typically answer directly: *what's this grid's cycle-walk signature — cycle residual magnitude, stability class, cycle-life estimate — under realistic operating-regime cycles?*

| Existing tool | Typical use | This repo |
| --- | --- | --- |
| MATPOWER, PYPOWER | Steady-state load flow given inputs | Cycle-walk measurement on top of the steady-state results |
| OpenDSS, GridLAB-D | Distribution-feeder behavior under scenarios | Cycle-by-cycle cycle residual of the control layer |
| pandapower | Network behavior under N-1 contingencies | Cheapest-durable routing recipes for each operating regime |
| PSS®E | Full-system transient + dynamic stability | Multi-voice meta-sim that demonstrates how to couple PSS®E with other models |

To wire a real grid model into this framework, implement the substrate-plugin contract (a `reach()` / `cost()` / `lifetime()` triple over `BridgeParams`) around your existing simulator. See `examples/voice_extension_template.py` and `CONTRIBUTING.md`.

## What's in the box

```
grid-diamondcutter-oss/
├── README.md                          ← this file
├── LICENSE                            ← Apache 2.0
├── NOTICE                             ← Apache 2.0 attribution + trademark notices
├── SECURITY.md                        ← vulnerability disclosure path
├── CONTRIBUTING.md                    ← how to add a voice + attribution model
├── pyproject.toml                     ← pip-installable metadata + dev extras
├── Makefile                           ← convenience targets (test / demo / install-dev / lint)
├── power_grid_sim.py                  ← single-voice baseline (numpy-only)
├── power_grid_sim_v2.py               ← 3-voice meta-sim entry point
├── grid_diamondcutter_oss.py          ← voices-pattern demonstrator (graceful-degrade fallbacks)
├── reproducibility_hashes.json        ← expected outputs from `python power_grid_sim.py`
├── meta_sim/                          ← 3-voice polyphonic package
│   ├── __init__.py
│   ├── core.py                        ← topology + load/generation profiles
│   └── meta.py                        ← MetaSim + cross-voice coupling demo
├── examples/
│   ├── basic_grid.py                  ← shortest possible single-voice run
│   └── voice_extension_template.py    ← drop-in starter for contributors (3 patterns)
├── tests/
│   ├── test_substrate_contract.py     ← 19 tests locking the substrate-plugin contract
│   └── test_meta_sim.py               ← 18 tests on the 3-voice meta-sim + coupling
└── docs/
    └── methodology.md                 ← longer-form theory
```

## Quickstart

```bash
git clone <repo-url> grid-diamondcutter-oss
cd grid-diamondcutter-oss
python -m venv venv && source venv/bin/activate
pip install -e .         # or just: pip install numpy
python power_grid_sim.py
```

Expected output (matches exactly on a recent CPython + `numpy`; see `reproducibility_hashes.json` for canonical values + SHA-256):

```
CATALOGUE: 36 manufacturably-novel operating regimes
CYCLE WALK (5 stations rotating load profiles):
  step distances:    [0.065, 0.052, 0.041, 0.028]
  mean step:         0.0465
  cycle residual:  -0.0465
  closes:            True
  stability class:   stable-cycle
```

That single command exercises the grid topology definition, the route-adaptive search, and the cycle-walk measurement. No AI tooling is used. No external service is contacted.

## Two-tier shape

The repository ships in two complementary tiers so an engineer with five minutes can run something useful, and an engineer with a real grid modeling team can plug into deeper voices.

**Tier 0 — `power_grid_sim.py`.** Single file, numpy-only, attachable to email. Implements an 8-node toy grid model with four generators, four loads, and twelve transmission lines, plus a heuristic flow allocator and the cycle-walk measurement. Sufficient to demonstrate every step of the workflow. This is the file you send to an engineer who has never heard of this project.

**Tier 1 — `power_grid_sim_v2.py` + `meta_sim/` + `grid_diamondcutter_oss.py`.** Polyphonic meta-sim that demonstrates the multi-voice coupling pattern: a slow load-flow voice (12-dim toy state), a mid-tempo control voice (5-dim), and a fast dynamics voice (4-dim). Cross-voice coupling is wired explicitly into the meta-sim so the pattern is visible in code; the +0.832 correlation between control and dynamics voices in the published demo is the correlation produced by the wired toy coupling, not a measurement of real grid physics. The graceful-degrade pattern in `grid_diamondcutter_oss.py` activates richer backends (`pypower`, `pandapower`) if they are installed and falls back cleanly to the numpy-only heuristic when they are not. A utility engineering team can wire their real PSS®E / MATPOWER / OpenDSS models in behind the same voice contract.

## Run without any AI

Every script in this repository is deterministic Python. There is no model call, no API key, no telemetry. You can audit every line by reading it. The cryptographic signatures used for measurement artifacts are pure-Python `hmac` over canonical JSON. The repository is designed to be reviewable in one sitting.

## Open-core split

This repository is the open part of a two-part architecture. Both parts are intentional, neither is incomplete.

**Open (Apache 2.0, this repository):**
- The grid topology + measurement protocol (cycle walk + cycle-residual reporting + stability classification).
- The route-adaptive search (catalogue of cheapest-durable routes).
- The substrate-plugin contract (how new voices are added).
- All tests, documentation, and reproducibility artifacts.

**Closed (`eirmath`, separate Eir, Inc. package):**
- The conducting policy that selects which catalogued recipe to run when.
- The signing service for measurement artifacts.
- The 59-dimensional grid-state math that powers the search heuristics and the classifier.

This is the same shape as PostgreSQL/Citus, Spark/Databricks, Kafka/Confluent, LLVM/proprietary backends, HuggingFace/closed fine-tunes. The open layer is sufficient to evaluate the measurement protocol, classify a grid, and use the search results for whatever purpose Apache 2.0 permits. The closed layer is Eir, Inc.'s commercial product; selling it is how the project funds continued open development.

A utility engineering team can use everything in this repository indefinitely without engaging Eir. Engagement happens by choice, when a team has measured their grid and decided the closed conducting + signing layer is worth the commercial terms.

## Optional `eirmath` extension

The OSS sim defines a small set of abstract methods that the proprietary `eirmath` package can plug into:

- `optimize(catalogue)` — conducting policy that selects which catalogued recipe to run when, given the grid's current state.
- `sign(artifact, key)` — HMAC signing service for measurement artifacts.

Without `eirmath` installed, these methods return clear "install eirmath to enable" stubs. The OSS sim continues to run the measurement, catalogue, and cycle-walk standalone.

With `eirmath` installed (`pip install eirmath`, separate commercial license terms apply), the methods route to closed-source implementations. `eirmath` is not required for any of the OSS sim's measurement or reporting capabilities.

## How to add a voice

Adding a grid voice (AC power flow, transient stability, market dispatch, distribution feeder, etc.) means writing a Python module that exposes:

- A list of regime names (e.g. `["steady", "overload", "fault", "restoration", "cascade"]`).
- A `reach(BridgeParams) -> tuple` function that returns the grid-state fingerprint for a given regime transition.
- A `cost(BridgeParams) -> float` function returning the per-call cost.
- A `lifetime(BridgeParams) -> float` function returning the expected durability of that recipe.

That's the entire contract. See `power_grid_sim.py` for the canonical small example, and `CONTRIBUTING.md` for the contributor protocol.

## License + attribution

Apache License, Version 2.0 for everything in this repository. See `LICENSE` and `NOTICE`. `docs/methodology.md` covers the longer-form theory.

Contributors are recognized in the project's contributor record described in `CONTRIBUTING.md`. The commercial wrapper (Eir, Inc.'s `eirmath` package, separate from this repository) describes the commercial terms; nothing in this repository requires it.

"Diamondcutter" is a trademark of Eir, Inc. The Apache 2.0 license grants you permission to use, modify, and distribute the software in this repository; trademark use is governed separately and described in `NOTICE`.

## Status

This is an evaluation artifact at v0.1. Numbers reproduce exactly on the listed dependencies. The repository is intended for evaluation, replication, and extension — not for production grid control. Anyone integrating into a production environment should validate against their own grid model and consult their regulatory + safety framework.
