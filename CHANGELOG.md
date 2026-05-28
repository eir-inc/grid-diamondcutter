# Changelog

All notable changes to `grid-diamondcutter-oss` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial public release scaffolding.

## [0.1.0] — 2026-05-28 (pre-release)

### Added
- `power_grid_sim.py` — single-file, numpy-only 8-node grid surrogate + cycle-walk measurement.
- `power_grid_sim_v2.py` — meta-sim with 3 polyphonic voices (load-flow / control / dynamics) and cross-band coupling demonstration.
- `meta_sim/` package — `Voice` / `MetaSim` abstractions, `closure_walk_meta`, `measure_cross_band_coupling`.
- `grid_diamondcutter_oss.py` — voices-pattern reference with optional sim-backend stubs (PYPOWER / PandaPower).
- `examples/basic_grid.py` — single-voice quickstart.
- `examples/ieee_case_demo.py` — REAL PYPOWER `runpf` ingest for case14 / case30 / case118 with pre-registered analysis + dual-scalar reporting (closure_residual + path_excursion).
- `examples/voice_extension_template.py` — drop-in starter for contributors adding new voices.
- `docs/methodology.md` — longer-form theory.
- `docs/for_grid_engineers.md` — translation layer for engineers coming from PYPOWER / PandaPower / OpenDSS.
- `tests/test_substrate_contract.py` — 19 substrate-plugin contract conformance tests.
- `tests/test_meta_sim.py` — 18 meta-sim + cross-band-coupling regression tests.
- `tests/test_pipeline_integration.py` — 11 end-to-end pipeline tests.
- `LICENSE` (Apache 2.0), `NOTICE`, `SECURITY.md`, `CONTRIBUTING.md`.
- `pyproject.toml` (pip-installable), `Makefile` (contributor convenience commands).
- `reproducibility_hashes.json` — signed expected outputs from canonical runs.

### Notes
- This is a pre-release scaffolding version. The internal git history is the scaffolding record; public-shipping versions will be cut as clean snapshots from this working tree.
- 48 tests passing in 0.4s.
- Public vocabulary set: `cycle_residual`, `stability_class` (`stable-cycle` / `moderate-stress-cycle` / `high-stress-cycle`), `cycle walk`, `prevention-based pricing`. Earlier internal-development vocabulary has been replaced across the public-facing surface.
