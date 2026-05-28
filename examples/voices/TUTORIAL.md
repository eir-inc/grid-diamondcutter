# Your first voice in 5 minutes

This tutorial walks through authoring your first voice for the
`grid-diamondcutter` registry from a fresh clone. By the end, you will have:

- Copied the voice template to a new file
- Filled in the five required fields per `PREREGISTRATION.md` §3.1
- Run the conformance test to confirm your voice is well-formed
- Run your voice end-to-end and produced a signed JSON sidecar
- A pull-request-ready commit

Total time: ~5 minutes. Total dependencies: Python 3.10+, numpy, pytest.

## Step 0 — Fresh clone + setup

```bash
git clone https://github.com/eir-inc/grid-diamondcutter
cd grid-diamondcutter
pip install -e ".[dev]"
make test
# Expected: 72+ tests pass
```

## Step 1 — Copy the template

```bash
cp examples/voices/_voice_template.py examples/voices/my_first_voice.py
```

The leading underscore on `_voice_template.py` excludes it from auto-discovery
by the conformance test. Your copy without the underscore IS discovered and
tested.

## Step 2 — Decide which axis (§3.2)

Choose one:

- **Polyphony voice** (within a substrate): you are adding a new model inside
  one substrate to capture a residual the existing model misses. Example:
  a demand-response model inside the grid substrate.
- **Coupling voice** (across substrates): you are claiming a causal link between
  two substrates — one substrate's output drives the other's input. Example:
  regulatory_stringency → grid behavior.

If you are unsure, start with a polyphony voice. Coupling voices have stricter
pre-commitments (direction + magnitude range + null direction).

## Step 3 — Fill the five fields

Open `examples/voices/my_first_voice.py`. The template marks every REPLACE point
in comments. The five required module-level constants are:

```python
VOICE_NAME = "my_first_voice_v1"  # unique, versioned

PREDICTION = {
    "kind": "polyphony_within_substrate",     # or "coupling_cross_substrate"
    "substrate": "8node_dc_grid",
    "named_residual": "specific residual this voice claims to capture",
    "predicted_value_upper_bound": 0.05,       # the numerical bound
    # for coupling voices, ALSO required:
    # "predicted_direction": "A → B (positive)",
    # "predicted_magnitude_range": [low, high],
    # "null_direction": "no correlation OR reversed direction",
}

KILL_CONDITION = {
    "metric": "name of measurement the kill check uses",
    "rule": "fail if observed > 0.05",
    "rationale": "why this rule constitutes falsification",
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/my_first_voice.py",
    "source_file": "examples/voices/my_first_voice.py",
    "input_parameters": {"random_seed": 42, ...},
    "environment": {"python": "3.10+", "dependencies": ["numpy>=1.24"]},
}
```

The fifth field — `compute_verdict()` — is a function that mechanically returns
pass/fail/partial from the run output against your kill condition. The template
provides a working example you adapt.

## Step 4 — Implement the voice

Replace `run_voice_measurement()` with your voice's actual logic. The function
must return a single value (or structure) that `compute_verdict()` can check
against the kill condition. Keep it deterministic given the random seed in your
`RUN_PROTOCOL`.

Worked examples:

- `examples/voices/example_polyphony_voice.py` — a within-substrate
  demand-response voice that fails its kill condition (enters the null-voice
  ledger per §3.4).
- `examples/voices/example_coupling_voice.py` — a cross-substrate
  regulatory-stringency voice that also fails its kill condition (null
  direction realized).

Both worked examples are deliberate honest nulls. Voices that pass and voices
that fail are equally valid registry entries; only voices missing fields or
with untestable kill conditions are rejected.

## Step 5 — Verify shape before committing

```bash
make voice-contract
# Expected: 15+ tests pass (your voice picked up by auto-discovery)
```

If any test fails, the test message names the missing field or the malformed
field. Fix it. Run again. The conformance test is the same one CI will run on
your pull request, so a green local run means a green CI run.

## Step 6 — Run end-to-end + emit the sidecar

```bash
python examples/voices/my_first_voice.py
```

The voice's `main()` runs the measurement, computes the verdict, and emits a
signed JSON sidecar at `examples/voices/my_first_voice_v1.sidecar.json`. The
sidecar carries a SHA-256 hash over the pre-verdict canonical serialization
(the predict + kill-condition + run-protocol fields), which establishes that
those fields preceded the verdict at commit time.

## Step 7 — Regenerate the registry summary

```bash
make registry
```

This updates `REGISTRY_STATUS.md` to include your voice in the aggregate
counts and per-voice table. Commit the updated `REGISTRY_STATUS.md` alongside
your voice file.

## Step 8 — Commit + open the pull request

```bash
git checkout -b my-first-voice
git add examples/voices/my_first_voice.py examples/voices/my_first_voice_v1.sidecar.json REGISTRY_STATUS.md
git commit -m "voice: my_first_voice_v1 — <one-line description>"
git push origin my-first-voice
gh pr create --title "voice: my_first_voice_v1" --body "Per §3.1 five-field unit. <one-paragraph description of the predicted residual coupling and why it matters.>"
```

## What reviewers will check

Per `PREREGISTRATION.md` §6 and `examples/voices/README.md`:

1. The voice conforms to §3.1's five-field shape (CI verifies this
   mechanically).
2. The kill condition is testable from the run output alone, without external
   reinterpretation (CI verifies this too, by re-running the voice).
3. The sidecar's SHA-256 hash matches the regenerated hash (CI verifies; catches
   post-verdict tampering).

Reviewers do **not** check whether your prediction will turn out to be correct.
A voice the reviewer believes will fail is still merged if its shape is correct;
its failure enters the null-voice ledger per §3.4 and stays on record. The
registry's base rate of failures is part of the project's audit-defense — see
§3.4 in `PREREGISTRATION.md`.

## What happens after merge

Your voice's verdict — pass, fail, or partial — joins the registry. The base
rate updates in `REGISTRY_STATUS.md` on the next regeneration. If your voice
passes, the residual it captured is now accounted for; if it fails, the null
ledger records it dated to the commit timestamp, alongside the framing that
did not work.

Either outcome is a contribution to the witnessed search. There is no
penalty for failed voices; there is a penalty for voices added without a
pre-committed kill condition (those are not registry entries at all).
