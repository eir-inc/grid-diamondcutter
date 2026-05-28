# Diamondcutter methodology — grid context

This document explains the diamondcutter measurement methodology in the context of power-grid simulation. The aim is to give a grid engineer with no prior exposure enough background to read the code, reproduce the published numbers, and judge whether the methodology applies to their own grid.

## Honest scope

This methodology is a **measurement protocol** layered on top of an existing grid model. It does not provide a new grid model, a new power-flow solver, a new optimal-power-flow algorithm, or a new control law. It provides:

1. A way to walk a grid through a representative cycle of operating regimes and measure how cleanly the cycle closes.
2. A way to search the parameter space of regime-transition recipes and record the cheapest ones that survive a configurable confirmation threshold.

The reference implementation in this repository uses a **heuristic flow allocator** for the underlying grid model — a `min(generator_capacity, load_demand)`-style allocator with line-utilization heuristics. It is not a B-bus / phase-angle DC power flow. The methodology itself is independent of the grid model; substituting a real solver (MATPOWER, PYPOWER, OpenDSS, pandapower, PSS®E) behind the substrate-plugin contract is the production path.

## The substrate-plugin contract

The methodology operates entirely through a four-function contract:

- A list of **regimes** — discrete operating modes (e.g. `peak / off_peak / mixed / spike` in `power_grid_sim.py`, or `steady / overload / fault / restoration / cascade` in extension examples).
- A `reach(BridgeParams) -> tuple` function — returns the grid-state fingerprint after a regime transition is executed with given control parameters. The fingerprint must be hashable + comparable for equality.
- A `cost(BridgeParams) -> float` function — returns the scalar per-call cost of executing a recipe.
- A `lifetime(BridgeParams) -> float` function — returns how many cycles the recipe is expected to remain durable before recalibration is needed.

That's the whole contract. A grid engineer can wire their own simulator behind it without modifying any other code in this repository. See `examples/voice_extension_template.py`.

## Cycle walk — the measurement

The methodology measures a *cycle residual*: when a representative sequence of operating-regime transitions returns to its starting regime, how far has the grid-state fingerprint drifted from where the walk started?

In code, the cycle walk:

1. Picks a representative sequence of regime transitions that returns to the starting regime.
2. Runs `reach()` through each transition, recording the grid-state fingerprints.
3. Computes the per-step distances between consecutive fingerprints.
4. Computes the **home step**: the distance between the final fingerprint and the starting fingerprint.
5. Reports the **cycle residual** = `home_step − mean(step_distances)`.

A grid that closes cleanly has cycle residual ≈ 0. A grid whose closing fingerprint overshoots has positive cycle residual; a grid that undershoots has negative residual.

## Stability classification

The cycle residual classifies the grid into a stability class:

| Cycle residual magnitude | Stability class | Expected cycle-life |
| --- | --- | --- |
| `\|c\| < 0.5` | **stable-cycle** | long; minimal intervention needed |
| `0.5 ≤ \|c\| < 2.0` | **moderate-stress** | medium; periodic rebalancing helpful |
| `\|c\| ≥ 2.0` | **high-stress** | short; frequent intervention needed |

The classification is operational, not predictive. It tells you the substrate's reachable-space shape under the regimes you walked it through, not what will happen under a different regime cycle. The thresholds in `power_grid_sim.py` are tuned for the 8-node toy grid; production deployment should re-tune them against the customer's real grid model.

## Route-adaptive search

Given the substrate-plugin contract, the route-adaptive search explores the parameter space of regime-transition recipes and emits a *catalogue* of cheapest-durable routes. The search is bounded by two thresholds:

- `lifetime_threshold` — recipes whose `lifetime()` falls below this are rejected.
- `confirm_frac` — recipes whose fingerprint matches a previously-confirmed fingerprint at least this fraction of the time are accepted into the catalogue.

The output catalogue is a list of `(regime_a, regime_b, depth, beta, cost, lifetime, score, confirm_frac)` tuples — the grid's manufacturably-novel routes ranked by cost-per-cycle. A grid operator can use the catalogue directly as a routing table: for each transition the grid needs to make, look up the cheapest catalogued recipe.

The methodology does not prescribe a control law. It describes the grid's reachable space and the cheapest paths through that space; what the operator does with that catalogue is operational policy.

## Polyphonic meta-sim

A real grid has multiple timescales + multiple physics layers that no single existing simulator captures together: load-flow (seconds), control (minutes), dynamics (sub-second), outage/contingency (events). The polyphonic meta-sim in `power_grid_sim_v2.py` + `meta_sim/` demonstrates how to compose multiple voices, each one a grid model at a different timescale, into a single cycle-walk measurement.

The reference implementation uses three toy voices with cross-voice coupling wired explicitly into the code. The reported cross-voice correlation of +0.832 between the control voice and the dynamics voice is the correlation produced by the wired toy coupling — it demonstrates the polyphony pattern, it does not measure a coupling in real grid physics. Production deployment replaces each voice with a real simulator (MATPOWER for load-flow, OpenDSS for distribution dynamics, PSS®E for full transient stability) through the same `Voice` abstraction.

## What the methodology does not claim

- A new power-flow solver. The reference implementation uses a heuristic allocator; production deployment should plug in a real solver.
- A predictive theory of grid behavior. The measurement is descriptive of the grid's reachable space under the regimes you walked; it does not predict behavior under regimes you didn't walk.
- Substitution for domain expertise. The substrate-plugin contract is intentionally minimal; real AC power flow, transient stability, market clearing, and distribution-feeder modeling live behind the contract and are the contributor's responsibility.
- Production safety. The reference implementation is an evaluation artifact. Production deployment requires the regulatory + safety review your jurisdiction requires.
- Empirically validated coupling magnitudes from the meta-sim. The cross-voice correlation reported is a property of the wired toy coupling, not of real grid physics. Production deployment will report different numbers measured on real models.

## Reading list

- The diamondcutter name + the cycle-residual framing borrow a small amount of vocabulary from the music-theory literature on tuning closure. A grid engineer does not need that background to use this repository; it is acknowledged here for transparency.
- IEEE Standard Test Cases (IEEE 14-bus, 30-bus, 39-bus, 57-bus, 118-bus, 300-bus). Canonical grid topologies for cross-implementation comparison; future work in this repository will validate the cycle-walk measurement against these cases.
- MATPOWER User's Manual; OpenDSS Manual; pandapower documentation. The existing-simulator landscape this repository is designed to plug into.

These are pointers. The code is independently auditable; everything above is context for why the code is shaped the way it is.
