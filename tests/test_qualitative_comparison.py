# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""Unit tests for tools.qualitative_comparison — §4.3 harness.

Self-contained: tests build their own sidecars + fixtures in tmp_path and
invoke the harness API directly. No dependency on any particular voice's
sidecar being on disk.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.qualitative_comparison import compare


def _write_sidecar(path: Path, voice_name: str, verdict: dict) -> Path:
    path.write_text(json.dumps({"voice_name": voice_name, "verdict": verdict}, indent=2))
    return path


def _write_fixture(path: Path, voice_name: str, rules: list) -> Path:
    path.write_text(json.dumps({
        "voice_name": voice_name,
        "citation": "test fixture",
        "expected_recovery_rules": rules,
    }, indent=2))
    return path


def test_verdict_equals_rule_passes_when_verdict_matches(tmp_path):
    sidecar = _write_sidecar(
        tmp_path / "v.sidecar.json",
        "voice_a",
        {"verdict": "pass"},
    )
    fixture = _write_fixture(
        tmp_path / "v.fixture.json",
        "voice_a",
        [{
            "rule_id": "r1",
            "rule_kind": "verdict_equals",
            "spec": {"value": "pass"},
            "citation_anchor": "anchor",
        }],
    )
    report = compare(sidecar, fixture)
    assert report["harness_verdict"] == "recover"
    assert report["n_passed"] == 1


def test_verdict_equals_rule_fails_when_verdict_differs(tmp_path):
    sidecar = _write_sidecar(
        tmp_path / "v.sidecar.json", "voice_a", {"verdict": "fail"},
    )
    fixture = _write_fixture(
        tmp_path / "v.fixture.json", "voice_a",
        [{
            "rule_id": "r1",
            "rule_kind": "verdict_equals",
            "spec": {"value": "pass"},
            "citation_anchor": "anchor",
        }],
    )
    report = compare(sidecar, fixture)
    assert report["harness_verdict"] == "no_recover"
    assert report["n_passed"] == 0


def test_slope_within_range_passes(tmp_path):
    sidecar = _write_sidecar(
        tmp_path / "v.sidecar.json", "voice_a",
        {"verdict": "pass", "observed_slope": 0.55},
    )
    fixture = _write_fixture(
        tmp_path / "v.fixture.json", "voice_a",
        [{
            "rule_id": "r2",
            "rule_kind": "slope_within_range",
            "spec": {"low": 0.40, "high": 0.95},
            "citation_anchor": "anchor",
        }],
    )
    report = compare(sidecar, fixture)
    assert report["harness_verdict"] == "recover"


def test_slope_within_range_fails_when_outside_window(tmp_path):
    sidecar = _write_sidecar(
        tmp_path / "v.sidecar.json", "voice_a",
        {"verdict": "pass", "observed_slope": 0.10},
    )
    fixture = _write_fixture(
        tmp_path / "v.fixture.json", "voice_a",
        [{
            "rule_id": "r2",
            "rule_kind": "slope_within_range",
            "spec": {"low": 0.40, "high": 0.95},
            "citation_anchor": "anchor",
        }],
    )
    report = compare(sidecar, fixture)
    assert report["harness_verdict"] == "no_recover"


def test_scenario_field_within_range_passes(tmp_path):
    sidecar = _write_sidecar(
        tmp_path / "v.sidecar.json", "voice_a",
        {
            "verdict": "pass",
            "scenario_summaries": [
                {"name": "s0", "metric_a": 0.10},
                {"name": "s1", "metric_a": 0.50},
            ],
        },
    )
    fixture = _write_fixture(
        tmp_path / "v.fixture.json", "voice_a",
        [{
            "rule_id": "r3",
            "rule_kind": "scenario_field_within_range",
            "spec": {"scenario_index": 1, "field": "metric_a", "low": 0.40, "high": 0.60},
            "citation_anchor": "anchor",
        }],
    )
    report = compare(sidecar, fixture)
    assert report["harness_verdict"] == "recover"


def test_voice_name_mismatch_refuses_to_compare(tmp_path):
    sidecar = _write_sidecar(
        tmp_path / "v.sidecar.json", "voice_a", {"verdict": "pass"},
    )
    fixture = _write_fixture(
        tmp_path / "v.fixture.json", "voice_DIFFERENT",
        [{
            "rule_id": "r1",
            "rule_kind": "verdict_equals",
            "spec": {"value": "pass"},
            "citation_anchor": "anchor",
        }],
    )
    report = compare(sidecar, fixture)
    assert report["harness_verdict"] == "fail"
    assert "voice_name" in report["rationale"]


def test_all_rules_must_pass_for_recover(tmp_path):
    sidecar = _write_sidecar(
        tmp_path / "v.sidecar.json", "voice_a",
        {"verdict": "pass", "observed_slope": 0.10},
    )
    fixture = _write_fixture(
        tmp_path / "v.fixture.json", "voice_a",
        [
            {
                "rule_id": "r1",
                "rule_kind": "verdict_equals",
                "spec": {"value": "pass"},
                "citation_anchor": "a1",
            },
            {
                "rule_id": "r2",
                "rule_kind": "slope_within_range",
                "spec": {"low": 0.40, "high": 0.95},
                "citation_anchor": "a2",
            },
        ],
    )
    report = compare(sidecar, fixture)
    assert report["harness_verdict"] == "no_recover"
    assert report["n_passed"] == 1
    assert report["n_rules"] == 2


def test_unknown_rule_kind_fails_cleanly(tmp_path):
    sidecar = _write_sidecar(
        tmp_path / "v.sidecar.json", "voice_a", {"verdict": "pass"},
    )
    fixture = _write_fixture(
        tmp_path / "v.fixture.json", "voice_a",
        [{
            "rule_id": "r1",
            "rule_kind": "not_a_real_kind",
            "spec": {},
            "citation_anchor": "anchor",
        }],
    )
    report = compare(sidecar, fixture)
    assert report["harness_verdict"] == "no_recover"
    assert "unknown rule_kind" in report["rule_outcomes"][0]["audit"]
