# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
"""
texas_uri_temperature_collapse_real_v1.py — §3.1 polyphony voice.

FIRST CAJAL-LANE VOICE ON REAL DATA. Uses the frozen-snapshot SHA-256-verified
NOAA NCEI Texas Uri Feb 11-20 2021 dataset (ingested via groove PR #28 +
PR #10 ingestion infrastructure). Tests §0 cascade-mechanism recognition on
the real Feb 2021 Texas cold-snap event.

Pre-reg knowledge: Texas Uri produced documented record cold across the state
in mid-Feb 2021. Dallas-Fort Worth area hit ~-19°C / -2°F (per NOAA, ERCOT
post-event reports). At minimum, multiple stations should show a TMIN trough
during Feb 14-17 that is at least 10°C colder than the Feb 11-12 (pre-event)
baseline. If the §0 cascade-mechanism recognition holds on this real-data
substrate, a simple pre-committed multi-station TMIN-drop test should detect
the event.

This voice REQUIRES groove PR #28 v1 NOAA data on main. Until #28 merges,
this voice file lives on a feature branch; the data file is fetched from
groove's branch only for local testing of this voice and is NOT committed
in this PR. PR-body declares the dependency.

Per §1 honesty bound: this is real-data v1 from a public source with SHA-256
contract enforcement at load. NOT a power-grid claim — only a weather-signal
recognition test that the cascade event is observable in the temperature
substrate. Power-grid effects (load loss, frequency excursion) are tested by
other voices on other data sources.
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(THIS_DIR))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))


# ===========================================================================
# §3.1 — polyphony voice unit
# ===========================================================================

VOICE_NAME = "texas_uri_temperature_collapse_real_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "noaa_ncei_texas_uri_feb_2021_v1_real_frozen_snapshot",
    "named_residual": "multi_station_tmin_drop_recognizable_during_uri_peak_window_in_real_data",
    "predicted_n_stations_with_drop": 5,  # at least 5 of 7 stations
    "predicted_minimum_tmin_drop_celsius": 10.0,  # at least 10°C cooler than baseline
    "baseline_window_dates": ["2021-02-11", "2021-02-12"],
    "event_window_dates": ["2021-02-14", "2021-02-15", "2021-02-16", "2021-02-17"],
    "rationale": (
        "Texas Uri produced documented record cold across the state in mid-Feb 2021. "
        "Dallas hit -19°C per NOAA / ERCOT post-event reports. A simple multi-station "
        "TMIN-drop test on the real NOAA snapshot should detect: at least 5 of 7 "
        "Texas stations show event-window TMIN ≥ 10°C colder than pre-event baseline. "
        "If §0 cascade-mechanism recognition holds on real-data substrate, this should "
        "PASS. FAIL would indicate either (a) the event was less severe than reported, "
        "(b) data unit / scaling issue in the snapshot, or (c) station selection didn't "
        "capture the event geographically."
    ),
}

KILL_CONDITION = {
    "metric": "n_stations_with_tmin_drop_geq_threshold",
    "rule": (
        "fail if fewer than 5 of 7 stations show event-window TMIN at least 10°C "
        "colder than baseline-window TMIN (signal below pre-committed multi-station "
        "co-recognition floor)"
    ),
    "rationale": (
        "Simple composite metric — count stations meeting the per-station TMIN-drop "
        "threshold. Multi-station floor avoids single-anomaly false-PASS; magnitude "
        "floor encodes the documented event severity."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/texas_uri_temperature_collapse_real_v1.py",
    "source_file": "examples/voices/texas_uri_temperature_collapse_real_v1.py",
    "input_parameters": {
        "data_source": "noaa_ncei",
        "data_event": "texas_uri_feb_2021",
        "data_version": "v1",
        "data_loader": "tools/data_ingestion.py:load_snapshot",
        "depends_on_pr": "#28 groove/real-noaa-uri-fetcher-v1 (provides v1 snapshot)",
        "random_seed": 211,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": [],
    },
}


# ===========================================================================
# Voice implementation
# ===========================================================================

def _load_uri_data() -> dict | None:
    """Load v1 snapshot if available; return None if dependency PR #28 not yet merged."""
    try:
        from data_ingestion import load_snapshot
        snap = load_snapshot(
            RUN_PROTOCOL["input_parameters"]["data_source"],
            RUN_PROTOCOL["input_parameters"]["data_event"],
            RUN_PROTOCOL["input_parameters"]["data_version"],
        )
        return snap["data"]
    except (FileNotFoundError, KeyError, ValueError) as e:
        # v1 snapshot not on main yet — depends on PR #28 merge
        return None


def _per_station_tmin_drop(observations: dict, baseline_dates: list[str], event_dates: list[str]) -> float | None:
    baseline_vals = [observations.get(d, {}).get("TMIN_C") for d in baseline_dates]
    baseline_vals = [v for v in baseline_vals if v is not None]
    event_vals = [observations.get(d, {}).get("TMIN_C") for d in event_dates]
    event_vals = [v for v in event_vals if v is not None]
    if not baseline_vals or not event_vals:
        return None
    baseline_mean = sum(baseline_vals) / len(baseline_vals)
    event_min = min(event_vals)
    # drop is positive if event is colder than baseline
    return float(baseline_mean - event_min)


def run_voice() -> dict:
    data = _load_uri_data()
    baseline_dates = PREDICTION["baseline_window_dates"]
    event_dates = PREDICTION["event_window_dates"]
    threshold = PREDICTION["predicted_minimum_tmin_drop_celsius"]

    if data is None:
        # v1 snapshot dependency not available — graceful FAIL with explicit reason
        return {
            "n_stations_total": 0,
            "n_stations_meeting_threshold": 0,
            "threshold_celsius": threshold,
            "baseline_dates": baseline_dates,
            "event_dates": event_dates,
            "per_station": {},
            "data_source_snapshot_sha256": None,
            "dependency_unmet": "PR #28 groove/real-noaa-uri-fetcher-v1 not yet merged; v1 snapshot unavailable on main",
        }

    per_station = {}
    n_stations_meeting_threshold = 0
    for sid, station_block in data["observations_by_station"].items():
        obs = station_block["observations"]
        drop = _per_station_tmin_drop(obs, baseline_dates, event_dates)
        meets = (drop is not None) and (drop >= threshold)
        per_station[sid] = {
            "station_name": station_block.get("station_name", sid),
            "baseline_dates": baseline_dates,
            "event_dates": event_dates,
            "tmin_drop_celsius": drop,
            "meets_threshold": meets,
        }
        if meets:
            n_stations_meeting_threshold += 1

    return {
        "n_stations_total": len(per_station),
        "n_stations_meeting_threshold": int(n_stations_meeting_threshold),
        "threshold_celsius": threshold,
        "baseline_dates": baseline_dates,
        "event_dates": event_dates,
        "per_station": per_station,
        "data_source_snapshot_sha256": hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }


# ===========================================================================
# Field 5: verdict
# ===========================================================================

def compute_verdict(run_output: dict) -> dict:
    n_meeting = run_output["n_stations_meeting_threshold"]
    n_total = run_output["n_stations_total"]
    n_required = PREDICTION["predicted_n_stations_with_drop"]
    threshold = PREDICTION["predicted_minimum_tmin_drop_celsius"]

    if run_output.get("dependency_unmet"):
        verdict = "fail"
        rationale = (
            f"Voice enters the null-voice ledger per §3.4. Dependency unmet: "
            f"{run_output['dependency_unmet']}. Voice file is registry-resident "
            f"and will re-run automatically once dependency lands on main. "
            f"Last local-test verdict (against groove branch v1 data): FAIL — "
            f"0/7 stations met 10°C-drop threshold (per-station drops ~1.3°C). "
            f"Failure-mode hypothesis at local test: NOAA tenths-of-°C scaling "
            f"may not be handled in fetcher (raw NOAA daily-summaries TMIN is "
            f"reported as integer tenths-of-°C; -189 raw = -18.9°C actual)."
        )
        return {
            "verdict": verdict,
            "n_stations_total": n_total,
            "n_stations_meeting_threshold": n_meeting,
            "n_stations_required": n_required,
            "threshold_celsius": threshold,
            "dependency_unmet": run_output["dependency_unmet"],
            "rationale": rationale,
            "computed_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    if n_meeting < n_required:
        verdict = "fail"
        rationale = (
            f"Voice enters the null-voice ledger per §3.4. Only "
            f"{n_meeting}/{n_total} stations show event-window TMIN ≥ {threshold:.1f}°C "
            f"cooler than baseline-window TMIN (predicted: ≥ {n_required}/{n_total}). "
            f"Three failure-mode hypotheses to investigate: "
            f"(a) the snapshot's data-magnitude scale may be off (per-station drops "
            f"look unexpectedly small for an event documented to produce ~-19°C in "
            f"Dallas — flag for groove PR #28 fetcher review); "
            f"(b) station selection may not have captured Dallas-Fort Worth where "
            f"severity was highest; "
            f"(c) the snapshot's data-window may not bracket the freeze-trough "
            f"correctly. Each is a §3.4 informative-null signal."
        )
    else:
        verdict = "pass"
        rationale = (
            f"{n_meeting}/{n_total} stations show event-window TMIN ≥ {threshold:.1f}°C "
            f"cooler than baseline-window TMIN. §0 cascade-mechanism recognition "
            f"observable on real NOAA Texas Uri Feb 2021 data substrate. NOT a "
            f"power-grid claim — only a weather-signal cascade-recognition test."
        )

    return {
        "verdict": verdict,
        "n_stations_total": n_total,
        "n_stations_meeting_threshold": n_meeting,
        "n_stations_required": n_required,
        "threshold_celsius": threshold,
        "per_station_drops": {
            sid: s["tmin_drop_celsius"] for sid, s in run_output["per_station"].items()
        },
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


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
        sort_keys=True,
        separators=(",", ":"),
    )
    unit["sidecar_sha256_pre_verdict"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with open(output_path, "w") as f:
        json.dump(unit, f, indent=2)
    return output_path


def main():
    print("=" * 72)
    print(f"voice unit: {VOICE_NAME}")
    print("=" * 72)
    print(f"predicted: ≥ {PREDICTION['predicted_n_stations_with_drop']} of 7 stations show TMIN drop ≥ {PREDICTION['predicted_minimum_tmin_drop_celsius']:.1f}°C")
    print(f"kill rule: {KILL_CONDITION['rule']}")
    print(f"run:       {RUN_PROTOCOL['entry_point']}")
    print()
    print("running Texas Uri Feb 2021 temperature-collapse recognition on real data...")
    out = run_voice()
    if out.get("dependency_unmet"):
        print(f"  dependency_unmet: {out['dependency_unmet']}")
    else:
        print(f"  data snapshot sha256: {out['data_source_snapshot_sha256'][:16]}...")
    print(f"  baseline window: {out['baseline_dates']}")
    print(f"  event window:    {out['event_dates']}")
    print(f"  threshold:       {out['threshold_celsius']:.1f}°C")
    print()
    for sid, s in out["per_station"].items():
        drop_str = f"{s['tmin_drop_celsius']:6.2f}°C" if s["tmin_drop_celsius"] is not None else "  None"
        mark = "✓" if s["meets_threshold"] else "✗"
        print(f"  {mark} {sid} {s['station_name']:25s}  drop: {drop_str}")
    print()
    print(f"  stations meeting threshold: {out['n_stations_meeting_threshold']}/{out['n_stations_total']}")
    print()
    verdict = compute_verdict(out)
    print(f"  verdict: {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    print()

    sidecar_path = os.path.join(THIS_DIR, f"{VOICE_NAME}.sidecar.json")
    emit_sidecar(verdict, out, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
