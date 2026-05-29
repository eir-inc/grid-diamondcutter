# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""tools/fetch_noaa_uri.py — REAL NOAA NCEI fetcher for Texas / Uri Feb 2021 (v1 ratchet of PR #10).

Replaces the skeleton fetcher in tools/data_ingestion.py with a real network call to
NOAA NCEI's Daily Summaries v1 API. Pulls TMIN / TMAX / PRCP per day across the Uri
winter-storm window (Feb 11-20 2021) for major Texas weather stations.

Authoring-time tool — developer runs once to freeze the snapshot. The frozen JSON +
manifest entry then live in the repo for runtime use by §4 historical-events voices.

Run:
    python tools/fetch_noaa_uri.py

Stations covered (Texas major metros):
  - USW00012921 — San Antonio Intl AP, TX
  - USW00013904 — Austin Camp Mabry, TX
  - USW00012960 — Houston Hobby AP, TX
  - USW00013960 — Dallas Love Field, TX
  - USW00013959 — Austin Bergstrom AP, TX
  - USW00012917 — Corpus Christi Intl AP, TX
  - USW00023044 — El Paso Intl AP, TX

Data window: 2021-02-11 to 2021-02-20 (covers pre-storm baseline + peak Uri + recovery).

Source: NOAA NCEI Climate Data Online — Daily Summaries v1
        https://www.ncei.noaa.gov/access/services/data/v1
        License: NOAA NCEI Daily Summaries are in the public domain.
"""
from __future__ import annotations
import json
import sys
import os
import urllib.request
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.data_ingestion import freeze_snapshot


NCEI_ENDPOINT = "https://www.ncei.noaa.gov/access/services/data/v1"

STATIONS = [
    ("USW00012921", "San Antonio Intl AP"),
    ("USW00013904", "Austin Camp Mabry"),
    ("USW00012960", "Houston Hobby AP"),
    ("USW00013960", "Dallas Love Field"),
    ("USW00013959", "Austin Bergstrom AP"),
    ("USW00012917", "Corpus Christi Intl AP"),
    ("USW00023044", "El Paso Intl AP"),
]

DATA_TYPES = ["TMIN", "TMAX", "PRCP"]
START_DATE = "2021-02-11"
END_DATE = "2021-02-20"


def fetch_noaa_uri_real() -> dict:
    """Real NOAA NCEI fetch — pulls TMIN/TMAX/PRCP per day per station, Feb 11-20 2021.

    Returns canonical-JSON-shaped dict with stations + observations + provenance.
    """
    station_ids = ",".join(s[0] for s in STATIONS)
    data_types = ",".join(DATA_TYPES)
    params = {
        "dataset": "daily-summaries",
        "stations": station_ids,
        "dataTypes": data_types,
        "startDate": START_DATE,
        "endDate": END_DATE,
        "format": "json",
        "units": "metric",
    }
    url = NCEI_ENDPOINT + "?" + urllib.parse.urlencode(params)
    print(f"fetching: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "grid-diamondcutter-oss/0.1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        raw = response.read().decode("utf-8")
    raw_records = json.loads(raw)
    if not isinstance(raw_records, list):
        raise ValueError(f"unexpected NCEI response shape (expected list of records): {type(raw_records)}")

    # Normalize into per-station / per-date observations
    by_station = {}
    for record in raw_records:
        station = record.get("STATION")
        date = record.get("DATE")
        if station not in by_station:
            station_name = next((name for sid, name in STATIONS if sid == station), "unknown")
            by_station[station] = {
                "station_id": station,
                "station_name": station_name,
                "observations": {},
            }
        if date not in by_station[station]["observations"]:
            by_station[station]["observations"][date] = {}
        for dt in DATA_TYPES:
            if dt in record:
                # V2 UNIT-HANDLING CORRECTION (per PREREGISTRATION §5.1 analyst-error
                # protocol). v1 stored raw_val / 10.0 here, assuming NOAA NCEI returns
                # raw GHCN-Daily tenths (0.1°C / 0.1mm). That is true when units=standard,
                # but the API call uses units=metric — values are ALREADY in degC / mm.
                # v1 stored values at 1/10 their true magnitude. Bug surfaced by two
                # independent voices: groove PR #39 (cold_extremity) and cajal PR #41
                # (temperature_collapse). v2 stores values as-returned.
                try:
                    raw_val = float(record[dt])
                except (ValueError, TypeError):
                    continue
                if dt in ("TMIN", "TMAX"):
                    by_station[station]["observations"][date][f"{dt}_C"] = raw_val
                elif dt == "PRCP":
                    by_station[station]["observations"][date][f"{dt}_mm"] = raw_val

    return {
        "event": "texas_uri_feb_2021",
        "schema_version": "1.0",
        "data_window": {"start_date": START_DATE, "end_date": END_DATE},
        "stations": [
            {"id": sid, "name": name} for sid, name in STATIONS
        ],
        "observations_by_station": by_station,
        "data_types": DATA_TYPES,
        "units_note": "TMIN_C / TMAX_C in degrees Celsius; PRCP_mm in millimeters",
        "source_metadata": {
            "endpoint": NCEI_ENDPOINT,
            "dataset": "daily-summaries",
            "license": "public domain (NOAA NCEI Daily Summaries)",
            "citation": "NOAA National Centers for Environmental Information, Climate Data Online — Daily Summaries",
        },
    }


def main():
    print(f"NOAA NCEI fetch: Texas / Uri Feb 2021 ({len(STATIONS)} stations, {START_DATE} to {END_DATE})")
    try:
        content = fetch_noaa_uri_real()
    except urllib.error.URLError as e:
        print(f"NETWORK ERROR: {e}")
        print("Authoring-time tool requires network. Run from a machine with NCEI reachability.")
        sys.exit(2)
    except Exception as e:
        print(f"FETCH ERROR: {e}")
        sys.exit(3)

    n_stations = len(content["observations_by_station"])
    n_obs = sum(len(s["observations"]) for s in content["observations_by_station"].values())
    print(f"  stations returned: {n_stations}/{len(STATIONS)}")
    print(f"  station-day observations: {n_obs}")
    if n_obs == 0:
        print("WARN: zero observations returned — NCEI may not have data for the requested window/stations.")

    entry = freeze_snapshot(
        source="noaa_ncei",
        event="texas_uri_feb_2021",
        version="v2",
        content=content,
        source_url=NCEI_ENDPOINT,
        fetched_by="tools/fetch_noaa_uri.py (groove, v2 — unit-handling fix per §5.1)",
        license_note="NOAA NCEI Daily Summaries — public domain. Cite NOAA NCEI Climate Data Online.",
    )
    print(f"\nfrozen as: {entry.source}__{entry.event}__{entry.version}")
    print(f"  snapshot file: data_snapshots/{entry.snapshot_file}")
    print(f"  canonical sha256: {entry.canonical_sha256}")
    print(f"  fetched_at_utc: {entry.fetched_at_utc}")


if __name__ == "__main__":
    main()
