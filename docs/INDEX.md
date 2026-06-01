# Documentation index

This index names where every document in the repository lives + what question each one answers. It's the recommended read order for an external reader landing on a fresh clone.

The repository is a public publication artifact, not only a software package. The reading path matters because the methodology pre-registers its claims (`PREREGISTRATION.md`) before any voice runs, and the close-out documents (`POST_MORTEM.md`, `phase_2/POST_MORTEM_PHASE_2.md`) compare delivered to committed at every publication-window close.

---

## First-time reader path (~30 minutes)

| step | doc | what it answers |
|---|---|---|
| 1 | [`README.md`](../README.md) | What this repo is + who it's for + how to run the single-file demo in under a minute. |
| 2 | [`PREREGISTRATION.md`](../PREREGISTRATION.md) | What the project pre-commits to publishing — central question (§0), honesty bounds (§1), voice-registry protocol (§3), historical-events validation (§4), correction protocol (§5), publishing shape (§6), scope limitations (§7). The committed-in-advance shape every voice + post-mortem is measured against. |
| 3 | [`examples/voices/TUTORIAL.md`](../examples/voices/TUTORIAL.md) | First voice in 5 minutes — copy the template, fill the 5 fields, run end-to-end, see the signed sidecar. Operationalizes §3.1. |
| 4 | [`REGISTRY_STATUS.md`](../REGISTRY_STATUS.md) | The committed-as-of-this-commit aggregate registry — total voices, base rates by verdict + kind, per-voice table. Regenerable via `make registry` at any commit hash. |
| 5 | [`POST_MORTEM.md`](../POST_MORTEM.md) | Phase-A delivered registry vs `PREREGISTRATION.md` commitments. What each pre-reg section actually got. Emergent patterns named honestly as non-pre-registered. Honest gaps named. |
| 6 | [`phase_2/PREREGISTRATION_PHASE_2.md`](../phase_2/PREREGISTRATION_PHASE_2.md) | Phase-2 pre-reg — monetary-phase substrate. Inherits phase-1 §3 protocol + adds bounds #9-12 + §3.5 cross-phase consumption + §3.6 evasion-class lineage + §4 historical events. |
| 7 | [`phase_2/POST_MORTEM_PHASE_2.md`](../phase_2/POST_MORTEM_PHASE_2.md) | Phase-2 delivered vs phase-2 pre-reg. §0.2 4/4 met. Multi-witness §4 bracket discriminates sustained-excess from crisis-spike substrate classes. |

After step 7 you've read the publication arc end-to-end. The remaining docs serve specific extension or contribution paths.

---

## Author a new voice (contributor path)

| doc | what it answers |
|---|---|
| [`examples/voices/TUTORIAL.md`](../examples/voices/TUTORIAL.md) | First voice in 5 minutes — same doc as step 3 above. |
| [`examples/voices/README.md`](../examples/voices/README.md) | File table + authoring steps + reviewer-scope note. |
| [`examples/voices/_voice_template.py`](../examples/voices/_voice_template.py) | Boilerplate (leading underscore excludes it from auto-discovery; copy without the underscore). |
| [`tests/test_voice_registry_contract.py`](../tests/test_voice_registry_contract.py) | Mechanical §3.1 conformance test. Run `make voice-contract` before submitting a PR. |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Voice authoring + simulator adapters + station sets + testing + commit hygiene + the open/closed boundary. |

---

## Understand the substrate (extension / research path)

| doc | what it answers |
|---|---|
| [`docs/methodology.md`](methodology.md) | Longer-form theory — cycle-walk, route-adaptive search, stability classification. |
| [`docs/meta_sim.md`](meta_sim.md) | The polyphonic substrate — `Voice` abstraction, `MetaSim` orchestrator, `measure_cross_band_coupling`, cross-band-coupling demonstration (the +0.832 figure honestly named as between-simulated-voices, not real-grid). |
| [`docs/for_grid_engineers.md`](for_grid_engineers.md) | Translation layer for engineers coming from PYPOWER / PandaPower / OpenDSS / MATPOWER. |
| [`docs/eirmath_bridge.md`](eirmath_bridge.md) | Public-shape description of where `eirmath` (proprietary closed component) plugs in. 3 use cases pre-disclosed. No math disclosed, no eirmath dependency. The §6 boundary anchor. |

---

## Compliance / audit / reproducibility

| doc | what it answers |
|---|---|
| [`LICENSE`](../LICENSE) | Apache License 2.0. |
| [`NOTICE`](../NOTICE) | Apache 2.0 attribution + trademark notices. |
| [`SECURITY.md`](../SECURITY.md) | Vulnerability disclosure path. |
| [`CONTRIBUTORS.md`](../CONTRIBUTORS.md) | Contributor recognition record. |
| [`CHANGELOG.md`](../CHANGELOG.md) | Versioned change log per [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) + [SemVer](https://semver.org/). |
| `reproducibility_hashes.json` | Signed expected outputs from canonical runs (matches `python power_grid_sim.py`). |

---

## Archived

| doc | what it answers | archived because |
|---|---|---|
| `docs/archives/PHASE_A_MERGE_BATCHES.md` (when archived) | Merge-triage artifact from the phase-A publication-window close. Wave-sequenced 99-PR merge plan. | Served its purpose at the 2026-05-29 publication-window close; preserved for audit trail. |

---

## Per-document "what it doesn't answer"

The §3.4 audit-defense pattern wants every claim to name its scope explicitly. Same for the documentation:

- **`README.md` doesn't answer**: how the bound-defender lattice was built, how the publication window was closed, what FAIL voices are on record. (See `POST_MORTEM.md` + `REGISTRY_STATUS.md`.)
- **`PREREGISTRATION.md` doesn't answer**: what actually happened. (See `POST_MORTEM.md`.)
- **`POST_MORTEM.md` doesn't answer**: how to author a new voice in the next publication window. (See `examples/voices/TUTORIAL.md` + `CONTRIBUTING.md`.)
- **`REGISTRY_STATUS.md` doesn't answer**: the framing notes + rationale per voice. (See each voice's sidecar JSON for `verdict.rationale`.)
- **`docs/eirmath_bridge.md` doesn't answer**: any eirmath math. The math is intentionally not in this repository per §6.

---

## How to regenerate this index

This document is hand-maintained. When a new top-level `.md` lands or moves, update this index in the same PR. The `_voice_template.py`-style underscore-prefix convention also applies to work-in-progress docs: underscore-prefixed `.md` files in this repository are draft/internal and not expected to appear in this index.

When in doubt about where a new doc lives: the chain-keeper convention is "the doc lives in `docs/` if it's reference; at repo root if it's audit-trail (READMEs, pre-regs, post-mortems, CHANGELOG); in `phase_N/` if it's phase-window-scoped."
