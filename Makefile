# Copyright 2026 Eir Inc
# Licensed under the Apache License, Version 2.0
#
# Convenience commands for grid-diamondcutter-oss contributors.
# Run `make` with no args to see this help.

.PHONY: help test demo demo-meta demo-template install install-dev clean lint check

PYTHON ?= python3

help:
	@echo "Diamondcutter Grid OSS — contributor commands"
	@echo ""
	@echo "  make install       — install the package (numpy only)"
	@echo "  make install-dev   — install with dev deps (pytest + coverage)"
	@echo "  make test          — run all tests (37 tests, expect green in <1s)"
	@echo "  make demo          — run the single-file meta-sim self-demo (voices pattern)"
	@echo "  make demo-meta     — run the 3-voice meta-sim self-demo + measure cross-band PAC"
	@echo "  make demo-template — run the voice-extension template's self-demo (5/6 PASS expected)"
	@echo "  make check         — install-dev + test + demos (full verification)"
	@echo "  make lint          — basic syntax check on all .py files"
	@echo "  make clean         — remove __pycache__ + .pytest_cache + build artifacts"

install:
	$(PYTHON) -m pip install .

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest tests/

demo:
	$(PYTHON) grid_diamondcutter_oss.py

demo-meta:
	$(PYTHON) -c "from meta_sim import make_default_meta_sim, closure_walk_meta, measure_cross_band_coupling; \
m=make_default_meta_sim(); \
print('cycle walk:', closure_walk_meta(m, ['peak', 'off_peak', 'mixed', 'spike', 'peak'])); \
print('cross-band coupling:', measure_cross_band_coupling(m))"

demo-template:
	$(PYTHON) examples/voice_extension_template.py

check: install-dev test demo demo-meta
	@echo ""
	@echo "All checks passed."

lint:
	@echo "Compiling all .py files to check for syntax errors..."
	@$(PYTHON) -m compileall -q grid_diamondcutter_oss.py power_grid_sim.py power_grid_sim_v2.py meta_sim examples tests
	@echo "lint OK"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build dist
	@echo "cleaned."
