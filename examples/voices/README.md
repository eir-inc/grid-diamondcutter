# Voices — registry-conforming examples + template

This directory contains reference voices for the `grid-diamondcutter` registry
protocol described in `PREREGISTRATION.md` §3.

## What's here

| File | Kind | Status | Purpose |
|------|------|--------|---------|
| `example_polyphony_voice.py` | polyphony (within-substrate, §3.2) | fail → null ledger | reference for §3.1 5-field unit |
| `example_coupling_voice.py` | coupling (cross-substrate, §3.2) | fail → null ledger | reference for §3.2 stricter directional discipline |
| `_voice_template.py` | (template) | n/a | copy this when authoring a new voice |
| `*.sidecar.json` | (generated) | n/a | signed verdicts emitted by `main()` runs |

The two example voices both end in the null-voice ledger per §3.4 — they are
deliberately *honest nulls* that demonstrate the registry's failure-recording
discipline, not voices that pass.

## Authoring a new voice

1. Copy `_voice_template.py` to `your_voice_name.py` (drop the leading underscore).
2. Fill in the five required fields: `VOICE_NAME`, `PREDICTION`, `KILL_CONDITION`,
   `RUN_PROTOCOL`, and the `compute_verdict()` function.
3. Implement the voice's substrate modification or measurement in
   `run_voice_measurement()`.
4. Verify the file conforms to §3.1 before submitting a PR:

   ```bash
   python -m pytest tests/test_voice_registry_contract.py -v
   ```

5. Run your voice end-to-end:

   ```bash
   python examples/voices/your_voice_name.py
   ```

   The run emits a signed JSON sidecar (`your_voice_name.sidecar.json`) containing
   the five-field unit plus the verdict, with a SHA-256 anchor over the pre-verdict
   canonical serialization.

## Coupling voices have stricter pre-commitments

Per §3.2, a coupling voice (cross-substrate link) must additionally pre-register:

- `predicted_direction` — which substrate's output drives the other's input
- `predicted_magnitude_range` — the expected magnitude range [low, high]
- `null_direction` — the realization that would falsify the directional claim

The conformance test enforces this; if `PREDICTION["kind"] == "coupling_cross_substrate"`,
the three additional fields are required.

## Reviewer scope

Reviewers adjudicate two things only:

1. The voice's file conforms to §3.1's shape (verified mechanically by
   `tests/test_voice_registry_contract.py`).
2. The voice's `KILL_CONDITION` is testable from its `RUN_PROTOCOL`'s output
   alone, without external reinterpretation.

Reviewers do **not** adjudicate whether the prediction will turn out to be correct.
A voice that the reviewer believes will fail is still merged if its shape is correct;
its failure enters the null-voice ledger per §3.4 and stays on record.
