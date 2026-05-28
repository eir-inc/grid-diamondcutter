"""
test_voice_registry_contract.py — mechanical conformance tests for the §3.1 voice contract.

Any voice file in `examples/voices/` is validated against the §3.1 five-field shape.
Reviewers do not have to eyeball each PR's structure; this test catches missing or
malformed fields mechanically.

What is validated:

  1. Module exposes the five required module-level constants:
     VOICE_NAME, PREDICTION, KILL_CONDITION, RUN_PROTOCOL, and a main() function.
  2. PREDICTION contains a 'kind' field (polyphony_within_substrate | coupling_cross_substrate)
     and a 'named_residual' field.
  3. Coupling voices additionally contain: predicted_direction, predicted_magnitude_range,
     null_direction (the stricter discipline per §3.2).
  4. KILL_CONDITION contains 'metric' and 'rule' fields.
  5. RUN_PROTOCOL contains 'entry_point', 'source_file', 'input_parameters'.
  6. The voice runs end-to-end (main() executes without exception).
  7. The verdict is one of {pass, fail, partial}.
  8. The sidecar JSON file is emitted next to the voice source and conforms to
     the shape (voice_name, prediction, kill_condition, run_protocol, verdict,
     sidecar_sha256_pre_verdict).

External contributors authoring a new voice should run this test locally before
submitting a PR:

  python -m pytest tests/test_voice_registry_contract.py -v
"""
from __future__ import annotations
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
VOICES_DIR = REPO_ROOT / "examples" / "voices"


def _discover_voice_modules() -> list[Path]:
    """Return all *.py files in examples/voices/ that look like voice modules."""
    if not VOICES_DIR.exists():
        return []
    return sorted(
        p for p in VOICES_DIR.glob("*.py")
        if not p.name.startswith("_") and p.name != "__init__.py"
    )


VOICE_FILES = _discover_voice_modules()


def _load_voice(voice_path: Path):
    spec = importlib.util.spec_from_file_location(voice_path.stem, voice_path)
    module = importlib.util.module_from_spec(spec)
    # Run module in its own namespace; package context not required
    sys.path.insert(0, str(REPO_ROOT))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


@pytest.fixture(scope="module")
def voice_modules():
    return {p.stem: _load_voice(p) for p in VOICE_FILES}


# ---------------------------------------------------------------------------
# Field-presence tests — §3.1 five-field unit
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("voice_path", VOICE_FILES, ids=[p.stem for p in VOICE_FILES])
def test_voice_has_five_required_fields(voice_path):
    """Per §3.1: a voice missing any one of the five required fields is not in the registry."""
    module = _load_voice(voice_path)
    required = ["VOICE_NAME", "PREDICTION", "KILL_CONDITION", "RUN_PROTOCOL"]
    for field in required:
        assert hasattr(module, field), \
            f"{voice_path.name} missing required field: {field}"
    assert callable(getattr(module, "main", None)), \
        f"{voice_path.name} missing main() function (entry point that produces verdict)"


@pytest.mark.parametrize("voice_path", VOICE_FILES, ids=[p.stem for p in VOICE_FILES])
def test_voice_name_is_unique_identifier(voice_path):
    module = _load_voice(voice_path)
    assert isinstance(module.VOICE_NAME, str) and module.VOICE_NAME, \
        f"{voice_path.name}: VOICE_NAME must be a non-empty string"


@pytest.mark.parametrize("voice_path", VOICE_FILES, ids=[p.stem for p in VOICE_FILES])
def test_prediction_has_kind_and_named_residual(voice_path):
    module = _load_voice(voice_path)
    pred = module.PREDICTION
    assert isinstance(pred, dict), f"{voice_path.name}: PREDICTION must be a dict"
    assert "kind" in pred, f"{voice_path.name}: PREDICTION missing 'kind'"
    assert pred["kind"] in (
        "polyphony_within_substrate",
        "coupling_cross_substrate",
    ), f"{voice_path.name}: PREDICTION['kind'] must be polyphony_within_substrate or coupling_cross_substrate"
    assert "named_residual" in pred, f"{voice_path.name}: PREDICTION missing 'named_residual'"


@pytest.mark.parametrize("voice_path", VOICE_FILES, ids=[p.stem for p in VOICE_FILES])
def test_coupling_voices_have_directional_fields(voice_path):
    """Per §3.2: coupling voices must pre-register direction, magnitude range, null direction."""
    module = _load_voice(voice_path)
    if module.PREDICTION.get("kind") != "coupling_cross_substrate":
        pytest.skip("not a coupling voice; only coupling voices require directional fields")
    pred = module.PREDICTION
    for field in ("predicted_direction", "predicted_magnitude_range", "null_direction"):
        assert field in pred, \
            f"{voice_path.name}: coupling voice missing required §3.2 field: {field}"


@pytest.mark.parametrize("voice_path", VOICE_FILES, ids=[p.stem for p in VOICE_FILES])
def test_kill_condition_is_well_formed(voice_path):
    module = _load_voice(voice_path)
    kc = module.KILL_CONDITION
    assert isinstance(kc, dict), f"{voice_path.name}: KILL_CONDITION must be a dict"
    assert "metric" in kc, f"{voice_path.name}: KILL_CONDITION missing 'metric'"
    assert "rule" in kc, f"{voice_path.name}: KILL_CONDITION missing 'rule'"


@pytest.mark.parametrize("voice_path", VOICE_FILES, ids=[p.stem for p in VOICE_FILES])
def test_run_protocol_is_well_formed(voice_path):
    module = _load_voice(voice_path)
    rp = module.RUN_PROTOCOL
    assert isinstance(rp, dict), f"{voice_path.name}: RUN_PROTOCOL must be a dict"
    for field in ("entry_point", "source_file", "input_parameters"):
        assert field in rp, f"{voice_path.name}: RUN_PROTOCOL missing '{field}'"


# ---------------------------------------------------------------------------
# Runnability test — voice must actually execute end-to-end
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("voice_path", VOICE_FILES, ids=[p.stem for p in VOICE_FILES])
def test_voice_runs_end_to_end(voice_path):
    """The voice's main() must execute without exception and emit a sidecar."""
    result = subprocess.run(
        [sys.executable, str(voice_path)],
        capture_output=True,
        timeout=60,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, \
        f"{voice_path.name} failed to run end-to-end: {result.stderr.decode()[:500]}"


# ---------------------------------------------------------------------------
# Sidecar conformance test — emitted JSON must conform to §3.1 shape
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("voice_path", VOICE_FILES, ids=[p.stem for p in VOICE_FILES])
def test_sidecar_is_well_formed(voice_path):
    module = _load_voice(voice_path)
    sidecar_path = VOICES_DIR / f"{module.VOICE_NAME}.sidecar.json"
    assert sidecar_path.exists(), \
        f"{voice_path.name}: expected sidecar at {sidecar_path} after run; missing"
    with open(sidecar_path) as f:
        sidecar = json.load(f)
    for field in ("voice_name", "prediction", "kill_condition", "run_protocol", "verdict"):
        assert field in sidecar, f"{sidecar_path.name}: missing field '{field}'"
    assert "sidecar_sha256_pre_verdict" in sidecar, \
        f"{sidecar_path.name}: missing sidecar_sha256_pre_verdict (audit-trail anchor)"
    assert sidecar["verdict"]["verdict"] in ("pass", "fail", "partial"), \
        f"{sidecar_path.name}: verdict must be pass / fail / partial; got {sidecar['verdict']['verdict']!r}"
