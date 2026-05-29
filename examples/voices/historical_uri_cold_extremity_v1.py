# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""historical_uri_cold_extremity_v1.py — §4 historical-event voice consuming real NOAA snapshot.

First registry voice that uses the frozen-snapshot data infrastructure (tools/data_ingestion.py +
data_snapshots/noaa_ncei__texas_uri_feb_2021__v1.json, merged in PR #10 + PR #28). Demonstrates
the §4 historical-events pipeline end-to-end with real public-domain weather data.

WHAT THIS VOICE PREDICTS
========================

Per documented historical record (NOAA, ERCOT post-mortem, FERC-NERC inquiry), the Texas
Uri winter storm produced extreme cold across the state during Feb 14-17 2021, with
multiple major cities recording all-time-low temperatures.

Specifically pre-registered prediction: across the 7 Texas weather stations in the
noaa_ncei snapshot, AT LEAST ONE station MUST record a TMIN ≤ -10°C on AT LEAST ONE day
in the documented Uri peak window (Feb 14-17 2021).

This is a sanity-check voice: it tests that the project's first real-data snapshot
actually recovers a known documented climatological event. It is not a methodology claim
about the grid response — that's downstream voice work that this snapshot enables.

KILL CONDITION
==============

If no station records TMIN ≤ -10°C on any day in the Feb 14-17 window, the snapshot
either (a) does not contain the documented cold extremity, or (b) was authored from a
different source than the documented NOAA NCEI station readings. Either case is a
data-integrity counter-observation that would require investigating the snapshot's
provenance before any downstream §4 voice consumes it.

If the kill fires, the v1 NOAA snapshot is NOT amended to make the voice pass (per
§5.2 — correctly-specified failing measurements are not retroactively revised). Instead,
the snapshot's provenance is audited and either re-fetched (yielding a v2 snapshot with
explicit correction note) OR the voice's understanding of the documented event is amended.

HONEST SCOPE
============

This voice does NOT claim to recover the grid response, the dispatch sequence, or any
downstream operational consequence. It tests ONE narrow climatological fact against ONE
frozen data snapshot. Its value is end-to-end demonstration of the load_snapshot →
predict → run → verdict pipeline using real data; downstream §4 voices can layer
atop this minimum-viable-demonstration.
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.data_ingestion import load_snapshot


# ===========================================================================
# §3.1 — The per-voice unit (five required fields)
# ===========================================================================

VOICE_NAME = "historical_uri_cold_extremity_v1"

PREDICTION = {
    "kind": "historical_event_data_recovery",
    "substrate": "noaa_ncei_daily_summaries_texas",
    "named_event": "Texas / February 2021 / Uri winter storm — peak cold window",
    "snapshot_source": "noaa_ncei",
    "snapshot_event": "texas_uri_feb_2021",
    "snapshot_version": "v1",
    "predicted_observation": (
        "at least one of the 7 Texas stations records TMIN ≤ -10°C on at least one day "
        "in the Feb 14-17 2021 window (documented peak of Uri)"
    ),
    "peak_window": ["2021-02-14", "2021-02-15", "2021-02-16", "2021-02-17"],
    "tmin_threshold_C": -10.0,
}

KILL_CONDITION = {
    "metric": "min_TMIN_across_stations_and_peak_window_days",
    "rule": f"fail if min_TMIN > {PREDICTION['tmin_threshold_C']}°C across all 7 stations × 4 peak-window days",
    "rationale": (
        "Documented historical record (NOAA, ERCOT, FERC-NERC) reports TMIN below -10°C "
        "at major Texas cities during the Uri peak window. A snapshot that does not "
        "recover this is either a different dataset or a corrupted fetch — kill condition "
        "surfaces the data-integrity failure before any downstream voice consumes it."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/historical_uri_cold_extremity_v1.py",
    "source_file": "examples/voices/historical_uri_cold_extremity_v1.py",
    "consumes_snapshot": "noaa_ncei__texas_uri_feb_2021__v1",
    "python_min_version": "3.9",
    "deps": [],  # stdlib only — load_snapshot doesn't need numpy
    "deterministic": True,
}


# ===========================================================================
# Run + verdict computation
# ===========================================================================

def _run_voice() -> dict:
    """Load the snapshot, scan TMIN across peak window, report observed minimum."""
    snapshot = load_snapshot(
        source=PREDICTION["snapshot_source"],
        event=PREDICTION["snapshot_event"],
        version=PREDICTION["snapshot_version"],
    )
    data = snapshot["data"]
    observations_by_station = data.get("observations_by_station", {})
    peak_window = set(PREDICTION["peak_window"])

    per_station_window_tmin = {}
    overall_min_tmin = None
    overall_min_at = None  # (station_id, date)

    for station_id, station_block in observations_by_station.items():
        station_name = station_block.get("station_name", "unknown")
        obs = station_block.get("observations", {})
        station_window_tmin = None
        for date_str, day_obs in obs.items():
            if date_str not in peak_window:
                continue
            if "TMIN_C" not in day_obs:
                continue
            tmin = day_obs["TMIN_C"]
            if station_window_tmin is None or tmin < station_window_tmin:
                station_window_tmin = tmin
            if overall_min_tmin is None or tmin < overall_min_tmin:
                overall_min_tmin = tmin
                overall_min_at = (station_id, station_name, date_str)
        per_station_window_tmin[station_id] = {
            "station_name": station_name,
            "window_min_TMIN_C": station_window_tmin,
        }

    return {
        "per_station_window_tmin": per_station_window_tmin,
        "overall_min_TMIN_C": overall_min_tmin,
        "overall_min_observed_at": overall_min_at,
        "snapshot_sha256": snapshot["manifest_entry"]["canonical_sha256"],
        "snapshot_fetched_at_utc": snapshot["manifest_entry"]["fetched_at_utc"],
    }


def _compute_verdict(observed: dict) -> str:
    overall_min = observed["overall_min_TMIN_C"]
    if overall_min is None:
        return "fail"  # no TMIN data at all in the window = snapshot integrity issue
    if overall_min <= PREDICTION["tmin_threshold_C"]:
        return "pass"
    return "fail"


def _emit_sidecar(observed: dict, verdict: str) -> str:
    sidecar = {
        "voice_name": VOICE_NAME,
        "verdict": verdict,
        "named_event": PREDICTION["named_event"],
        "predicted_observation": PREDICTION["predicted_observation"],
        "kill_condition_rule": KILL_CONDITION["rule"],
        "observed": observed,
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    canonical = json.dumps(sidecar, sort_keys=True).encode("utf-8")
    sidecar["run_sha256"] = hashlib.sha256(canonical).hexdigest()
    here = os.path.dirname(os.path.abspath(__file__))
    sidecar_path = os.path.join(here, f"{VOICE_NAME}.sidecar.json")
    with open(sidecar_path, "w") as f:
        json.dump(sidecar, f, indent=2, sort_keys=True)
    return sidecar_path


def main():
    print("=" * 76)
    print(f"§4 historical-event voice — {VOICE_NAME}")
    print(f"first registry voice consuming real NOAA snapshot")
    print("=" * 76)

    print(f"\nnamed event: {PREDICTION['named_event']}")
    print(f"snapshot:    {PREDICTION['snapshot_source']}__{PREDICTION['snapshot_event']}__{PREDICTION['snapshot_version']}")
    print(f"predicted:   at least one station ≤ {PREDICTION['tmin_threshold_C']}°C on at least one day in {PREDICTION['peak_window']}")
    print(f"kill:        {KILL_CONDITION['rule']}")

    observed = _run_voice()
    verdict = _compute_verdict(observed)
    sidecar_path = _emit_sidecar(observed, verdict)

    print(f"\nobserved across peak window ({len(PREDICTION['peak_window'])} days):")
    for station_id, block in observed["per_station_window_tmin"].items():
        wmin = block["window_min_TMIN_C"]
        wmin_str = f"{wmin:+.1f}°C" if wmin is not None else "(no data)"
        print(f"  {station_id} {block['station_name']:30s}  min TMIN in window: {wmin_str}")

    print(f"\noverall min TMIN in peak window: {observed['overall_min_TMIN_C']:+.1f}°C")
    print(f"observed at: {observed['overall_min_observed_at']}")
    print(f"\nVERDICT: {verdict.upper()}")
    print(f"snapshot sha256 (verified at load): {observed['snapshot_sha256']}")
    print(f"snapshot fetched at: {observed['snapshot_fetched_at_utc']}")
    print(f"sidecar: {sidecar_path}")


if __name__ == "__main__":
    main()
