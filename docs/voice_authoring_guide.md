# Voice authoring guide

This is the step-by-step walkthrough for adding a new registry voice to `grid-diamondcutter-oss`. For the reference shape of the 5-field unit + Phase-2 extensions, see [`CONTRIBUTING.md`](../CONTRIBUTING.md). For the project-level commitments your voice operates under, see [`PREREGISTRATION.md`](../PREREGISTRATION.md) (Phase-A) and [`phase_2/PREREGISTRATION_PHASE_2.md`](../phase_2/PREREGISTRATION_PHASE_2.md) (Phase-2).

A voice is a single Python file + a sidecar JSON. The whole contribution is one PR. This guide takes you from a clean clone to a merged PR.

## Prerequisites

- Python 3.10+ with `numpy>=1.24`
- A clean clone of the repo
- Familiarity with the project's discipline: pre-commit prediction + kill-condition BEFORE running; run + verdict are mechanical from the pre-committed shape; the sidecar is hash-anchored on the pre-verdict state

```bash
git clone <repo-url> grid-diamondcutter-oss
cd grid-diamondcutter-oss
python -m pytest tests/test_voice_registry_contract.py
```

The contract test should pass on a fresh clone — that's the gate every voice you add will pass through too.

## Step 1 — pick a voice kind

Decide what the voice is BEFORE writing code. Five kinds exist:

| Kind | Use when |
|---|---|
| **polyphony** | You want to test a residual / signal / inflection within ONE substrate. Example: does Greece's RE-share trajectory show a piecewise inflection within the 2016-2019 window? |
| **coupling** | You want to test a directional link between TWO substrates with a predicted magnitude_range and a null_direction. Example: does Denmark wind-export YoY predict German wind-capacity YoY at +1y lag? |
| **bound-defender** (inverted-kill) | You want to mechanically defend a §1 honesty-bound row. Voice scans source / sidecars / docs for the bound's failure pattern. Example: `bound_defender_4_no_forecast_language_v1` scans for unguarded forecast-language. |
| **historical-event** | You want to recover a documented qualitative trajectory from a §4 historical event. Example: Texas Feb 2021 ERCOT spot-price-instability recovery. |
| **cross-lane chain-loop** (Phase-2) | You want to test whether another lane's Phase-1 prior generalizes to a Phase-2 substrate. Example: `germany_2022_cross_lane_lead_time_recognition_v1` consumes miles regulatory_lead_time_v1 sidecar. |

Different kinds carry different mandatory `PREDICTION` fields. The contract test will reject a voice that declares `kind: "coupling_cross_substrate"` but doesn't provide `predicted_direction` + `predicted_magnitude_range` + `null_direction`.

## Step 2 — pre-commit the 5-field unit BEFORE running

Open a new file at `examples/voices/my_voice_v1.py` (Phase-A) or `phase_2/examples/voices/my_voice_v1.py` (Phase-2). Fill in the five fields:

```python
VOICE_NAME = "my_voice_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "name_of_the_data_or_simulation_substrate_v1",
    "named_residual": "specific_thing_the_voice_expects_to_find",
    "predicted_value_or_range": "...",   # field name varies by kind
    "rationale": "one paragraph: WHY this voice exists, what mechanism it tests",
}

KILL_CONDITION = {
    "metric": "single_composite_scalar_computable_from_run_output_alone",
    "rule": "fail if metric ...   (mechanical, no post-hoc interpretation)",
    "rationale": "why this threshold/condition is the right falsifier",
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/my_voice_v1.py",
    "source_file": "examples/voices/my_voice_v1.py",
    "input_parameters": {
        "calibration_source": "synthetic_v1_from_publicly_cited_X",   # or real-data source
        # ... voice-specific inputs ...
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}
```

**Commit this file with the 5-field unit ONLY, before writing run logic.** The pre-commit timestamp is what gives the §3.1 sha256_pre_verdict anchor its meaning. Voice-authoring discipline is: prediction committed before observation.

## Step 3 — implement run + verdict

Add the run logic + verdict computation. The verdict is a function that mechanically computes pass/fail/partial from the run output against the prediction + kill condition. NO post-hoc interpretation.

```python
def run_voice() -> dict:
    """Run the voice. Return a dict of observed values."""
    # ... compute the voice's metric ...
    return {
        "observed_metric": observed_value,
        "...": "...",
    }

def compute_verdict(run_output: dict) -> dict:
    """Mechanical verdict from run output against pre-committed prediction + kill condition."""
    metric = run_output["observed_metric"]
    fails = []
    if metric < ...:   # or whatever the kill rule says
        fails.append(f"metric {metric} fails kill rule (...)")

    if not fails:
        return {"verdict": "pass", "rationale": "...", "computed_at_utc": "..."}
    return {"verdict": "fail", "rationale": "Voice enters null-voice ledger per §3.4. " + " ; ".join(fails), "computed_at_utc": "..."}
```

## Step 4 — emit sidecar with sha256_pre_verdict anchor

The sidecar JSON is written by the voice itself in `main()`. The canonical-form SHA-256 of the pre-verdict shape is computed BEFORE the verdict is attached:

```python
def emit_sidecar(verdict: dict, run_output: dict, output_path: str) -> str:
    unit = {
        "voice_name": VOICE_NAME,
        "prediction": PREDICTION,
        "kill_condition": KILL_CONDITION,
        "run_protocol": RUN_PROTOCOL,
        "run_output": run_output,
        "verdict": verdict,
    }
    canonical = json.dumps(
        {k: v for k, v in unit.items() if k not in ("verdict", "run_output")},
        sort_keys=True, separators=(",", ":"),
    )
    unit["sidecar_sha256_pre_verdict"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with open(output_path, "w") as f:
        json.dump(unit, f, indent=2)
    return output_path
```

This is the audit-trail anchor. The hash freezes the pre-verdict state at run time; a reviewer can recompute it from the sidecar's own fields and verify the voice didn't retroactively edit its prediction or kill condition.

## Step 5 — Phase-2 only: add the three Phase-2 fields

If your voice is in `phase_2/examples/voices/`, add three additional fields to `RUN_PROTOCOL` (and optionally one to `PREDICTION`):

```python
RUN_PROTOCOL = {
    # ... §3.1 fields ...

    # §3.5
    "public_signal_source": {
        "feed_name": "ENTSO-E Transparency Platform day-ahead prices",
        "country_or_region": "Germany",
        "time_window": "2022-01-01 / 2022-12-31",
        "citation_anchor": "ENTSO-E TP API spec + national operator daily reports",
    },

    # §3.5 — if consuming a Phase-1 sidecar
    "cross_phase_consumption": [
        {
            "consumed_voice_name": "regulatory_lead_time_v1",
            "consumed_sidecar_path": "examples/voices/regulatory_lead_time_v1.sidecar.json",
            "consumed_phase": "phase_1",
            "consumption_kind": "prior_anchor",
        },
    ],

    # §3.7
    "computational_budget": {
        "max_runtime_seconds": 60,
        "max_external_api_calls": 0,
    },
}

PREDICTION = {
    # ... §3.1 fields ...
    "evasion_class_lineage": "cross_lane_prior_generalization_evasion",   # see PR #103 classifier
}
```

The five evasion classes (`substrate_class_evasion`, `substrate_shape_evasion`, `data_availability_evasion`, `network_magnitude_evasion`, `cross_lane_prior_generalization_evasion`) are documented in `examples/voices/evasion_spring_classifier_meta_v1.py`. Declaring lineage is optional but encouraged — it lets the registry ratchet against known spring geometries rather than rediscover them per voice.

## Step 6 — run + verify

```bash
python examples/voices/my_voice_v1.py
```

This produces `my_voice_v1.sidecar.json` next to the source file. Then run the conformance contract test:

```bash
python -m pytest tests/test_voice_registry_contract.py -k "my_voice"
```

All conformance tests must pass before commit. The contract checks:
- 5-field unit shape
- voice name uniqueness
- prediction has `kind` + `named_residual`
- coupling voices have `predicted_direction` + `predicted_magnitude_range` + `null_direction`
- kill condition is well-formed
- run protocol is well-formed
- voice runs end-to-end without error
- sidecar is well-formed JSON with `sha256_pre_verdict` matching canonical pre-verdict form

## Step 7 — commit on a feature branch

```bash
git checkout main && git pull
git checkout -b voice/my_voice_v1
git add examples/voices/my_voice_v1.py examples/voices/my_voice_v1.sidecar.json
git commit -m "voice: my_voice_v1 (PASS at X.XX — short description)

§3.1 polyphony voice (or coupling / bound-defender / historical / cross-lane).

predict: ...
kill:    ...

verdict: PASS (or FAIL) at observed_value.

scope: SYNTHETIC v1 / REAL-DATA v1 from publicly-cited <source>.
NOT a <whatever-the-bound-excludes> claim.
v2-ratchet candidate: ..."

git push -u origin voice/my_voice_v1
gh pr create --head voice/my_voice_v1 --base main --title "..." --body-file pr_body.md
```

## Step 8 — what happens after

Reviewers will:
1. Verify the conformance test passes locally.
2. Read the prediction + kill condition. The kill condition must be tight enough to actually falsify a wrong prediction. A kill that always passes is a flag.
3. Read the rationale + scope. The voice must respect the §1 honesty bounds for its phase. If your voice is a Phase-2 voice, it must respect §1.9-12 in addition to inherited Phase-A bounds.
4. Merge once both conformance + scope review pass. `REGISTRY_STATUS.md` is auto-regenerated; your voice appears in the ledger.

A FAIL verdict is NOT a reason to reject the PR. Per §3.4 the registry is the WITNESSED SEARCH, not any single winning configuration. Honest FAILs are first-class registry data and are what makes the registry's overall failure-rate audit-defensible.

## Common pitfalls

- **Kill condition is too loose** — voice always passes. The §0.3 low-failure-rate alarm catches this at registry scale, but a voice author should pre-empt it: the kill must be a genuine falsifier.
- **Post-hoc rationale revision** — voice runs, observes data, then rewrites the prediction to match. The sha256_pre_verdict anchor catches this mechanically: a reviewer recomputes the hash from the sidecar and sees it doesn't match the canonical form of a post-hoc-edited unit.
- **Cross-phase consumption silently skipped** — Phase-2 voice consumes a Phase-1 sidecar without declaring it in `cross_phase_consumption`. The PR #112 / §1.11 defender catches this on merge.
- **Forecast-language creep** — voice's rationale says "predicts" or "forecasts" in a way that crosses §1.4 (cascade-results-NOT-forecasts). Lighthouse PR #53 + subhuti PR #50 defenders catch this via source-scan.
- **Investment-advice language creep** — Phase-2 voice rationale crosses §1.10 with buy/sell/hold/recommendation language. Miles PR #112 + cajal PR #113 defenders catch this.

## Worked examples to learn from

| If you're authoring... | Read first |
|---|---|
| polyphony voice (Phase-A) | `examples/voices/renewable_mix_threshold_polyphony_v1.py` |
| coupling voice (Phase-A) | `examples/voices/spain_morocco_renewable_export_coupling_v1.py` |
| bound-defender voice | `examples/voices/bound_defender_4_no_forecast_language_v1.py` |
| historical-event voice (Phase-A) | `examples/voices/japan_post_fukushima_acceleration_v1.py` |
| historical-event voice (Phase-2) | `phase_2/examples/voices/california_2000_2001_recognition_v1.py` |
| cross-lane chain-loop voice (Phase-2) | `phase_2/examples/voices/germany_2022_cross_lane_lead_time_recognition_v1.py` |

Each of these is a complete worked voice — the 5-field unit + run logic + verdict + sidecar emission — that landed on main with a verdict on record. Reading three of these end-to-end will give you the shape faster than reading the protocol document.

## §3.4 closing reminder

> The base rate of nulls is expected to be high; the witnessed search is the publication, not any single winning configuration.

Author voices that can FAIL. Pre-commit kill conditions that would actually falsify a wrong prediction. Trust the §3.4 audit-substrate to give your honest FAIL the same registry status as a PASS. That's what the discipline is for.
