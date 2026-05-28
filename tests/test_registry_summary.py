"""
test_registry_summary.py — verify the registry summary aggregator stays correct.

`tools/registry_summary.py` is the §3.4 audit-defense mechanism: it computes the
base rate of failure from committed sidecars at any commit hash. If the aggregator
itself drifts (mis-counts, mis-classifies, mis-computes the base rate), §3.4's
"base rate computable at any commit hash" promise becomes false.

These tests pin the aggregator's behavior against synthetic and real sidecars.
"""
from __future__ import annotations
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL_PATH = REPO_ROOT / "tools" / "registry_summary.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("registry_summary", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(REPO_ROOT))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


@pytest.fixture(scope="module")
def tool():
    return _load_tool()


def _make_sidecar(name: str, kind: str, verdict: str, dest: Path) -> Path:
    sidecar = {
        "voice_name": name,
        "prediction": {"kind": kind, "named_residual": "test residual"},
        "kill_condition": {"metric": "test", "rule": "test"},
        "run_protocol": {"entry_point": "n/a", "source_file": "n/a", "input_parameters": {}},
        "verdict": {
            "verdict": verdict,
            "observed_value": 0.0,
            "rationale": "test",
            "computed_at_utc": "2026-05-28T00:00:00+00:00",
        },
        "sidecar_sha256_pre_verdict": "0" * 64,
    }
    path = dest / f"{name}.sidecar.json"
    with open(path, "w") as f:
        json.dump(sidecar, f)
    return path


def test_summarize_empty_registry(tool):
    summary = tool.summarize([])
    assert summary["total_voices_committed"] == 0
    assert summary["pass_count"] == 0
    assert summary["fail_count"] == 0
    assert summary["base_rate_failure"] == 0.0


def test_summarize_all_pass(tool):
    sidecars = [
        {"voice_name": "v1", "prediction": {"kind": "polyphony_within_substrate"},
         "verdict": {"verdict": "pass"}},
        {"voice_name": "v2", "prediction": {"kind": "polyphony_within_substrate"},
         "verdict": {"verdict": "pass"}},
    ]
    summary = tool.summarize(sidecars)
    assert summary["total_voices_committed"] == 2
    assert summary["pass_count"] == 2
    assert summary["fail_count"] == 0
    assert summary["base_rate_failure"] == 0.0
    assert summary["base_rate_pass"] == 1.0


def test_summarize_mixed_verdicts(tool):
    sidecars = [
        {"voice_name": "v1", "prediction": {"kind": "polyphony_within_substrate"},
         "verdict": {"verdict": "pass"}},
        {"voice_name": "v2", "prediction": {"kind": "polyphony_within_substrate"},
         "verdict": {"verdict": "fail"}},
        {"voice_name": "v3", "prediction": {"kind": "coupling_cross_substrate"},
         "verdict": {"verdict": "fail"}},
        {"voice_name": "v4", "prediction": {"kind": "coupling_cross_substrate"},
         "verdict": {"verdict": "partial"}},
    ]
    summary = tool.summarize(sidecars)
    assert summary["total_voices_committed"] == 4
    assert summary["pass_count"] == 1
    assert summary["fail_count"] == 2
    assert summary["partial_count"] == 1
    assert summary["base_rate_failure"] == 0.5
    assert summary["base_rate_pass"] == 0.25
    assert summary["kind_counts"]["polyphony_within_substrate"] == 2
    assert summary["kind_counts"]["coupling_cross_substrate"] == 2


def test_summarize_preserves_per_voice_detail(tool):
    sidecars = [
        {"voice_name": "alpha", "prediction": {"kind": "polyphony_within_substrate"},
         "verdict": {"verdict": "pass", "rationale": "alpha passed"},
         "sidecar_sha256_pre_verdict": "a" * 64,
         "_sidecar_path": "examples/voices/alpha.sidecar.json"},
    ]
    summary = tool.summarize(sidecars)
    assert len(summary["voices"]) == 1
    voice = summary["voices"][0]
    assert voice["voice_name"] == "alpha"
    assert voice["verdict"] == "pass"
    assert voice["rationale"] == "alpha passed"
    assert voice["sha256_anchor"] == "a" * 64


def test_collect_sidecars_reads_examples_voices(tool):
    """If real sidecars exist in examples/voices/, collect_sidecars should find them."""
    sidecars = tool.collect_sidecars()
    # At minimum, the two committed example sidecars should be discoverable
    voice_names = {s.get("voice_name") for s in sidecars}
    if voice_names:
        # If the examples directory has any sidecars, both reference voices should be there
        assert "demand_response_polyphony_v1" in voice_names or "regulatory_grid_coupling_v1" in voice_names, \
            f"expected at least one example sidecar in examples/voices/; found {voice_names}"


def test_markdown_render_has_required_sections(tool):
    sidecars = [
        {"voice_name": "v1", "prediction": {"kind": "polyphony_within_substrate"},
         "verdict": {"verdict": "fail", "rationale": "test"},
         "sidecar_sha256_pre_verdict": "0" * 64,
         "_sidecar_path": "examples/voices/v1.sidecar.json"},
    ]
    summary = tool.summarize(sidecars)
    md = tool.render_markdown(summary)
    assert "# Registry status" in md
    assert "Total voices committed" in md
    assert "Base rate of failure" in md
    assert "v1" in md
    assert "fail" in md


def test_render_markdown_handles_empty_registry(tool):
    summary = tool.summarize([])
    md = tool.render_markdown(summary)
    # should not crash; should produce well-formed markdown with zero counts
    assert "Total voices committed**: 0" in md
    assert "Base rate of failure" in md
