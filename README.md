# grid-diamondcutter-oss

**`grid-diamondcutter-oss` is a single-file, Apache 2.0 power grid simulator for utility engineers, grid researchers, security teams, and FOSS contributors who want to measure the avoidable routing inefficiency in a grid's control layer — without sharing raw operating data.**

It runs in under one second on a stock Python + `numpy` install. No model calls. No API keys. No telemetry. `python power_grid_sim.py` from a fresh clone produces a complete demonstration, with reproducibility hashes for every published number.

## Honest scope (read this first)

This repository is an **evaluation artifact**, not a production grid simulator. The flow model inside `power_grid_sim.py` is a **heuristic allocator** (a `min(generator_capacity, load_demand)`-style flow distribution), not a B-bus / phase-angle DC power flow. It is sufficient to demonstrate the cycle-walk measurement and the route-adaptive search; it is not a substitute for MATPOWER, PYPOWER, OpenDSS, GridLAB-D, or PSS®E.

The polyphonic meta-sim (`power_grid_sim_v2.py` + `meta_sim/`) demonstrates a pattern of coupled multi-timescale voices. The cross-band coupling value of +0.832 reported in the published demo is the correlation produced by the **toy voice models with coupling coefficients we wrote into the code**. It is a demonstration of the *polyphony pattern*, not an empirically measured coupling on a real grid. Where real coupling magnitudes matter, the customer's own grid model — wired in behind the substrate-plugin contract — is the source of truth.

The repository is intended for evaluation, replication, methodology evaluation, and extension. Anyone integrating into a production environment should validate against their own grid model and consult their regulatory + safety framework.

## Current state at a glance

Phase A (the methodology pre-registration cycle) and Phase 2 (the monetary-phase substrate extension) have both completed their publication windows + been post-mortem'd on main. Public artifacts:

| Artifact | What it is |
| --- | --- |
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | Phase A pre-registration — central question, honesty bounds, voice-registry protocol, historical-events validation set, deviations + corrections protocol. |
| [`PREREGISTRATION_PHASE_2.md`](phase_2/PREREGISTRATION_PHASE_2.md) | Phase 2 pre-registration — monetary-phase substrate, cross-phase consumption declaration, evasion-class lineage. |
| [`POST_MORTEM.md`](POST_MORTEM.md) | Phase A post-mortem — per-voice predicted-vs-observed, lattice closure read, emergent-pattern documentation. |
| [`POST_MORTEM_PHASE_2.md`](phase_2/POST_MORTEM_PHASE_2.md) | Phase 2 post-mortem — multi-witness bidirectional substrate finding, cross-criterion observations. |
| [`REGISTRY_STATUS.md`](REGISTRY_STATUS.md) | Auto-generated registry aggregate (refreshed by `tools/registry_summary.py`). |
| [`examples/voices/`](examples/voices/) | The pre-registered measurement registry — every voice carries a 5-field predict / kill / run / verdict unit and a signed JSON sidecar. |

Quantitative read at publication close: across both phases, the registry holds dozens of pre-registered voice units with a ~40% kill-fire rate (a healthy null-rate that the §0.3 low-failure-rate alarm in `PREREGISTRATION.md` is calibrated against). The §1 honesty-bound lattice is multi-witness defended on all named bounds. The §4 historical-events validation pass recovered the documented qualitative trajectory on all named events (Texas Feb 2021, EU REPowerEU May 2022, Japan March 2011 Fukushima). The §5 deviations + corrections protocol was exercised live during the publication window — see the post-mortem for the analyst-error → v2 ratchet examples on the record.

## What ships

- `power_grid_sim.py` — single-voice baseline. 8-node toy grid, 4 generators + 4 loads + 12 lines. The file you DM to a grid engineer who has never heard of this project.
- `power_grid_sim_v2.py` + `meta_sim/` — polyphonic meta-sim. Three timescale-separated voices (load-flow, control, dynamics) with the cross-coupling pattern wired explicitly so a real grid model can replace each voice through the same contract.
- `grid_diamondcutter_oss.py` — voices-pattern demonstrator with graceful-degrade soft-import of optional backends (`pypower`, `pandapower`).
- `examples/voices/` — the pre-registered voice registry. Each file is one published measurement unit with a sidecar verdict.
- `tools/` — `data_ingestion.py` (frozen-snapshot SHA-256 contract for real-data voices), `fetch_noaa_uri.py` (reference fetcher for the §4 Texas Uri snapshot), `registry_summary.py` (aggregator), `qualitative_comparison.py` (§4 recovery harness).
- `data_snapshots/` — frozen public-data snapshots used by §4 voices; loader verifies SHA-256 at runtime, no network calls during test runs.

## Who this is for

- **Utility engineers + grid operators** evaluating whether a cycle-walk measurement applies to their topology. Run the demo locally; wire in real grid models behind the contract.
- **Grid researchers** comparing how a single-model run compares to a coupled-voice meta-sim run on the same toy. The framework is small enough to read in one sitting.
- **Security auditors + regulators** verifying the measurement claims. Read every line; signatures are pure-Python `hmac` over canonical JSON. Reproducibility hashes published in `reproducibility_hashes.json`.
- **FOSS contributors** adding new grid voices (AC power flow, transient stability, market dispatch, distribution feeders). See [`CONTRIBUTING.md`](CONTRIBUTING.md) + [`examples/voices/TUTORIAL.md`](examples/voices/TUTORIAL.md) + [`examples/voices/_voice_template.py`](examples/voices/_voice_template.py).

## How this relates to existing grid sims

This repository does not replace MATPOWER, PYPOWER, OpenDSS, GridLAB-D, pandapower, or PSS®E. It plugs **on top of** them through the substrate-plugin contract, and answers one question they don't typically answer directly: *what's this grid's cycle-walk signature — cycle residual magnitude, stability class, cycle-life estimate — under realistic operating-regime cycles?*

| Existing tool | Typical use | This repo |
| --- | --- | --- |
| MATPOWER, PYPOWER | Steady-state load flow given inputs | Cycle-walk measurement on top of the steady-state results |
| OpenDSS, GridLAB-D | Distribution-feeder behavior under scenarios | Cycle-by-cycle cycle residual of the control layer |
| pandapower | Network behavior under N-1 contingencies | Cheapest-durable routing recipes for each operating regime |
| PSS®E | Full-system transient + dynamic stability | Multi-voice meta-sim that demonstrates how to couple PSS®E with other models |

To wire a real grid model into this framework, implement the substrate-plugin contract (a `reach()` / `cost()` / `lifetime()` triple over `BridgeParams`) around your existing simulator. See [`examples/voice_extension_template.py`](examples/voice_extension_template.py) + [`CONTRIBUTING.md`](CONTRIBUTING.md).

## What's in the box

```
grid-diamondcutter-oss/
├── README.md                          ← this file
├── LICENSE                            ← Apache 2.0
├── NOTICE                             ← Apache 2.0 attribution + trademark notices
├── SECURITY.md                        ← vulnerability disclosure path
├── CONTRIBUTING.md                    ← how to add a voice + attribution model
├── CONTRIBUTORS.md                    ← contributor record
├── CHANGELOG.md                       ← Keep-a-Changelog format
├── CITATION.cff                       ← citation file for academic + institutional use
├── PREREGISTRATION.md                 ← Phase A pre-registration (the methodology's called-shot)
├── POST_MORTEM.md                     ← Phase A post-mortem (delivered-vs-pre-registered)
├── REGISTRY_STATUS.md                 ← auto-generated voice-registry aggregate
├── pyproject.toml                     ← pip-installable metadata + dev extras
├── Makefile                           ← convenience targets (test / demo / install-dev / lint / voices / registry)
├── reproducibility_hashes.json        ← canonical expected outputs + SHA-256
├── registry_summary.json              ← machine-readable registry aggregate
│
├── power_grid_sim.py                  ← single-voice baseline (numpy-only)
├── power_grid_sim_v2.py               ← 3-voice meta-sim entry point
├── grid_diamondcutter_oss.py          ← voices-pattern demonstrator (graceful-degrade fallbacks)
│
├── meta_sim/                          ← 3-voice polyphonic package
├── tests/                             ← test suite (substrate contract, meta-sim, pipeline integration, voice registry contract, data ingestion, IEEE case demo)
├── tools/                             ← data ingestion + fetchers + registry summary + qualitative comparison harness
├── data_snapshots/                    ← frozen public-data snapshots + MANIFEST.json (SHA-256-verified)
│
├── examples/
│   ├── basic_grid.py                  ← shortest possible single-voice run
│   ├── ieee_case_demo.py              ← real PYPOWER runpf on case14 / case30 / case118
│   ├── voice_extension_template.py    ← drop-in starter for contributors (3 patterns)
│   └── voices/                        ← the pre-registered voice registry + tutorial + template
│
├── phase_2/                           ← Phase 2 (monetary-phase substrate) extension
│   ├── PREREGISTRATION_PHASE_2.md
│   ├── POST_MORTEM_PHASE_2.md
│   └── examples/                      ← Phase-2-specific voices
│
├── docs/
│   ├── methodology.md                 ← longer-form theory
│   ├── for_grid_engineers.md          ← translation layer for engineers coming from PYPOWER / PandaPower / OpenDSS
│   ├── meta_sim.md                    ← polyphonic substrate package documentation
│   └── eirmath_bridge.md              ← public description of the closed-half integration boundary
│
└── .github/workflows/                 ← CI: test matrix + voice-registry contract + license-header check
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

To explore the full registry: `make voices` runs every voice in `examples/voices/` end-to-end; `make registry` regenerates `REGISTRY_STATUS.md`.

## Two-tier shape

The repository ships in two complementary tiers so an engineer with five minutes can run something useful, and an engineer with a real grid modeling team can plug into deeper voices.

**Tier 0 — `power_grid_sim.py`.** Single file, numpy-only, attachable to email. Implements an 8-node toy grid model with four generators, four loads, and twelve transmission lines, plus a heuristic flow allocator and the cycle-walk measurement. Sufficient to demonstrate every step of the workflow. This is the file you send to an engineer who has never heard of this project.

**Tier 1 — `power_grid_sim_v2.py` + `meta_sim/` + `grid_diamondcutter_oss.py`.** Polyphonic meta-sim that demonstrates the multi-voice coupling pattern: a slow load-flow voice (12-dim toy state), a mid-tempo control voice (5-dim), and a fast dynamics voice (4-dim). Cross-voice coupling is wired explicitly into the meta-sim so the pattern is visible in code; the +0.832 correlation between control and dynamics voices in the published demo is the correlation produced by the wired toy coupling, not a measurement of real grid physics. The graceful-degrade pattern in `grid_diamondcutter_oss.py` activates richer backends (`pypower`, `pandapower`) if they are installed and falls back cleanly to the numpy-only heuristic when they are not. A utility engineering team can wire their real PSS®E / MATPOWER / OpenDSS models in behind the same voice contract.

## The pre-registration discipline

The repository follows a pre-registration discipline: predictions are committed in code (with kill conditions) BEFORE measurements are run, then verdicts are sealed in signed JSON sidecars next to the voice file that produced them. The `PREREGISTRATION.md` and `PREREGISTRATION_PHASE_2.md` documents declare what the project does and does not claim; the §1 honesty-bound lattice is mechanically defended by inverted-kill bound-defender voices that surface counter-observations before they slip past review. See the post-mortems for the lived results, including documented analyst-errors and the v1 → v2 corrections the §5 deviations protocol covers.

External contributors add voices through the same contract — see [`examples/voices/TUTORIAL.md`](examples/voices/TUTORIAL.md) for a five-minute walkthrough.

## Run without any AI

Every script in this repository is deterministic Python. There is no model call, no API key, no telemetry. You can audit every line by reading it. The cryptographic signatures used for measurement artifacts are pure-Python `hmac` over canonical JSON. The repository is designed to be reviewable in one sitting.

## Open-core split

This repository is the open part of a two-part architecture. Both parts are intentional, neither is incomplete.

**Open (Apache 2.0, this repository):**
- The grid topology + measurement protocol (cycle walk + cycle-residual reporting + stability classification).
- The route-adaptive search (catalogue of cheapest-durable routes).
- The substrate-plugin contract (how new voices are added).
- The pre-registration discipline + voice-registry + post-mortems.
- All tests, documentation, and reproducibility artifacts.

**Closed (`eirmath`, separate Eir, Inc. package):**
- The conducting policy that selects which catalogued recipe to run when.
- The signing service for measurement artifacts.
- The 59-dimensional grid-state math that powers the search heuristics and the classifier.

This is the same shape as PostgreSQL/Citus, Spark/Databricks, Kafka/Confluent, LLVM/proprietary backends, HuggingFace/closed fine-tunes. The open layer is sufficient to evaluate the measurement protocol, classify a grid, and use the search results for whatever purpose Apache 2.0 permits. The closed layer is Eir, Inc.'s commercial product; selling it is how the project funds continued open development.

A utility engineering team can use everything in this repository indefinitely without engaging Eir. Engagement happens by choice, when a team has measured their grid and decided the closed conducting + signing layer is worth the commercial terms. The integration boundary is documented in [`docs/eirmath_bridge.md`](docs/eirmath_bridge.md).

## Optional `eirmath` extension

The OSS sim defines a small set of abstract methods that the proprietary `eirmath` package can plug into:

- `optimize(catalogue)` — conducting policy that selects which catalogued recipe to run when, given the grid's current state.
- `sign(artifact, key)` — HMAC signing service for measurement artifacts.

Without `eirmath` installed, these methods return clear "install eirmath to enable" stubs. The OSS sim continues to run the measurement, catalogue, and cycle-walk standalone.

With `eirmath` installed (`pip install eirmath`, separate commercial license terms apply), the methods route to closed-source implementations. `eirmath` is not required for any of the OSS sim's measurement or reporting capabilities — bound mechanically defended by the §1.8 (Phase A) + §1.11 (Phase 2) bound-defender voices in the registry.

## How to add a voice

Adding a grid voice (AC power flow, transient stability, market dispatch, distribution feeder, etc.) means writing a Python module that exposes:

- A list of regime names (e.g. `["steady", "overload", "fault", "restoration", "cascade"]`).
- A `reach(BridgeParams) -> tuple` function that returns the grid-state fingerprint for a given regime transition.
- A `cost(BridgeParams) -> float` function returning the per-call cost.
- A `lifetime(BridgeParams) -> float` function returning the expected durability of that recipe.

Voices that go into the published registry additionally carry the §3.1 5-field unit (voice_id / prediction / kill_condition / run_protocol / verdict). See [`examples/voices/TUTORIAL.md`](examples/voices/TUTORIAL.md) for the contributor walkthrough and [`examples/voices/_voice_template.py`](examples/voices/_voice_template.py) for the drop-in template.

## License + attribution

Apache License, Version 2.0 for everything in this repository. See `LICENSE` and `NOTICE`. `docs/methodology.md` covers the longer-form theory.

Contributors are recognized in [`CONTRIBUTORS.md`](CONTRIBUTORS.md) and the project's [`CHANGELOG.md`](CHANGELOG.md). The commercial wrapper (Eir, Inc.'s `eirmath` package, separate from this repository) describes the commercial terms; nothing in this repository requires it.

"Diamondcutter" is a trademark of Eir, Inc. The Apache 2.0 license grants you permission to use, modify, and distribute the software in this repository; trademark use is governed separately and described in `NOTICE`.

## Status

This is an evaluation artifact at v0.1, with the Phase A + Phase 2 publication windows closed and post-mortem'd. Numbers reproduce exactly on the listed dependencies. The repository is intended for evaluation, replication, and extension — not for production grid control. Anyone integrating into a production environment should validate against their own grid model and consult their regulatory + safety framework.
