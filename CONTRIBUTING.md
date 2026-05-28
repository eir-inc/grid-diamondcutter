# Contributing to grid-diamondcutter-oss

This document explains how to contribute a new voice, a new simulator adapter, a new cycle-walk station set, or a documentation improvement.

## Table of contents

1. [What this project is](#what-this-project-is)
2. [The kinds of contribution we welcome](#the-kinds-of-contribution-we-welcome)
3. [How to add a voice](#how-to-add-a-voice)
4. [How to add a simulator adapter](#how-to-add-a-simulator-adapter)
5. [How to add a cycle-walk station set](#how-to-add-a-cycle-walk-station-set)
6. [Testing your contribution](#testing-your-contribution)
7. [Code style + commit hygiene](#code-style--commit-hygiene)
8. [Where the boundary is — what stays open, what stays closed](#where-the-boundary-is--what-stays-open-what-stays-closed)
9. [Recognition](#recognition)

---

## What this project is

This is the open-source side of the diamondcutter cycle-walk methodology applied to power-grid dynamics. The repository ships:

- A power-grid surrogate model (or thin wrappers around existing grid simulators) at the abstraction the cycle-walk pipeline needs.
- A five-function `Substrate` contract (`reach`, `cost`, `lifetime`, `window`, `forward`) plus a regime-parameter recipe shape.
- A self-demo that runs `route_adaptive` and `closure_walk` and prints a cycle-residual magnitude + stability class verdict.

If you can write a function that takes a `(regime_a, regime_b, depth, beta)` and returns a tuple fingerprint, you can contribute a voice.

## The kinds of contribution we welcome

| kind | example | review |
|---|---|---|
| **new voice** | a heuristic that captures a different aspect of grid behavior (e.g. thermal-loading, market-clearing, contingency-cascade) | merged if `closure_walk` returns a sensible stability class on the test cases |
| **simulator adapter** | a thin wrapper around PYPOWER, PandaPower, OpenDSS, MATPOWER, GridLAB-D, or another grid simulator that exposes it as a voice | merged if the adapter handles `ImportError` gracefully and the self-demo prints `voice active` when the sim is installed |
| **cycle-walk station set** | a published cycle of `BridgeParams` that probes a particular grid scenario (winter peak, summer cooling, hurricane restoration) | merged if the walk closes within physical-plausibility bounds |
| **documentation** | a tutorial, an annotated example, a translation of the README into another language, a better explanation of a section | merged if it makes the project more legible to a utility engineer who's new to the methodology |

Adapter contributions for sims that are common in the field are especially welcome. The whole point of the voices pattern is that every grid simulator becomes a voice in the chorus.

## How to add a voice

A voice is a function that takes a `BridgeParams` and returns a tuple `(activated_vector, cost)`. The activated vector is the substrate's response across the control / analyzer / mode axis; the cost is what it costs to run that response.

```python
def my_new_voice(p: BridgeParams) -> tuple:
    """One sentence on what this voice captures.

    Voice metadata (in a top-of-file comment):
      voice_id:    my_voice_handle
      author:      your_name_or_handle
      domain:      power_grid
      layer:       e.g. thermal / market / contingency / steady_state
      data_source: e.g. heuristic / pypower / pandapower / NREL_dataset_XYZ
    """
    # ... your implementation, returning (np.ndarray, float)
    pass

VOICES.append(("my_voice_handle", my_new_voice))
```

That's it. The substrate-plugin contract treats voices uniformly; `ensemble_voices()` will pick up your new voice automatically. Run the self-demo and confirm it shows `✓ active`.

## How to add a simulator adapter

A simulator adapter is a voice that wraps an existing grid simulator. The pattern is:

```python
def my_sim_voice(p: BridgeParams) -> Optional[tuple]:
    """Adapter for SimNameHere."""
    try:
        import simnamehere  # noqa: F401
    except ImportError:
        return None    # gracefully degrade if the sim isn't installed
    # ... call into simnamehere to compute (activated, cost)
    return activated, cost
```

The `Optional` return type plus the `try/except ImportError` is essential — it means a user who does NOT have your sim installed can still run the meta-sim, just with one fewer voice in the chorus. This is the "perfectly contained" property.

For a real adapter (not a stub), map `BridgeParams.regime_a` and `BridgeParams.regime_b` to the sim's native scenario inputs (load profiles, switch states, generation dispatch). Run the sim. Extract a fingerprint vector that lives in the same conceptual space as the heuristic voice. Return that.

## How to add a cycle-walk station set

A station set is a list of `BridgeParams` that traces a cycle through the grid's regime space. The default station set walks `steady → overload → fault → restoration → cascade → steady`. Other useful walks include:

- **seasonal:** `winter_peak → summer_peak → spring_low → fall_low → winter_peak`
- **restoration:** `fault → islanding → resynchronization → balanced_dispatch → steady → fault`
- **storm-cascade:** `steady → distribution_outage → transmission_trip → cascading_failure → restoration → steady`

Add your station set as a function returning a `list[BridgeParams]` in `examples/station_sets.py`. Include a docstring naming the physical scenario the walk probes.

## Testing your contribution

The repo ships a `tests/` directory with cycle-walk validation tests. Each test:

1. Runs your voice on a known-shape input.
2. Confirms the voice returns the expected output shape.
3. Confirms `closure_walk` on the meta-sim with your voice in the chorus produces a stability class within physical bounds.

Run with `python -m pytest tests/`. The exact testing scaffold is being assembled; this section will be updated.

## Code style + commit hygiene

- **stdlib + numpy only in the trunk.** Optional dependencies (PYPOWER, PandaPower, etc.) gated behind `try/except ImportError` are fine.
- **One file per voice** where reasonable. Big monolithic voice modules are a smell.
- **Docstrings are the contract.** If your voice's docstring says "models thermal loading per IEEE 738", that's what your voice does — nothing more, nothing less.
- **Commit messages name the contribution type.** Prefix with `voice:`, `adapter:`, `stations:`, `docs:`, or `fix:`. Body explains what the contribution captures.
- **No measurement-output commits.** The `.gitignore` excludes `*_catalogue.json` and `*_invoice.json` — those are per-customer outputs, not source code.

## Where the boundary is — what stays open, what stays closed

This repository is the open-source side of the methodology. The boundary between open and closed runs through the pipeline at the following points:

| layer | what's here | what's elsewhere |
|---|---|---|
| substrate definition | open — the `Substrate` contract + voices + adapters | — |
| `route_adaptive` minimal impl | open — the catalogue-building primitive, inlined | the production customer-side CLI lives in Eir's commercial toolkit |
| `closure_walk` minimal impl | open — the cycle-residual measurement primitive, inlined | the audit-survivable signed CLI lives in Eir's commercial toolkit |
| pricing | — | closed — Eir's commercial pricing layer |
| conducting policy | — | closed — Eir's commercial conducting policy |

If your contribution touches the closed layers, it cannot be merged into this repo — but you can reach out to Eir directly to discuss commercial integration.

## Recognition

Contributors who land merged PRs are listed in `CONTRIBUTORS.md`. Significant contributions are noted in the project changelog. The project follows the standard open-source recognition pattern: your name + handle on every PR you author, public credit in the contributor list, no further obligations on either side.

---

**Questions?** Open an issue, or use the contact channel listed in `README.md`. Maintained by Eir Inc engineering.
