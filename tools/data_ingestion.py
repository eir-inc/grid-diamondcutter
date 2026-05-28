# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""tools/data_ingestion.py — frozen-snapshot data ingestion contract for §4 historical-event voices.

The §4 historical-events validation (PREREGISTRATION.md) requires real public data to
back each historical-event voice's qualitative-trajectory recovery check. Live-fetch on
test runs would break reproducibility (network failures, source-side data drift). This
file defines the project's frozen-snapshot contract:

  AUTHORING TIME (developer runs once):
    A fetcher pulls fresh data from a public source (NOAA / ERCOT / ENTSO-E / METI).
    The fetcher writes the data into `data_snapshots/<source>__<event>__<version>.json`
    along with a manifest declaring the source URL, the fetch timestamp, the canonical
    SHA-256 of the snapshot contents, and the contributor responsible for the fetch.

  RUNTIME (every CI run, every test, every voice execution):
    Voice files call `load_snapshot(source, event, version)`. The loader reads from
    the committed snapshot file ONLY — no network calls at runtime. The loader verifies
    the snapshot's content SHA-256 against the manifest's declared hash; mismatch =
    hard failure (the snapshot has been tampered with or corrupted).

  COMMIT TIME:
    The snapshot JSON + its manifest entry both live in the repository. Reviewers
    inspecting a §4 voice can verify (a) the snapshot exists, (b) the manifest matches
    the snapshot, (c) the source URL is a real public source, (d) the fetcher source
    is in this file or another tool committed alongside.

This file provides the LOADER (always available, network-free) and a REFERENCE FETCHER
for NOAA weather data (developer-only — requires network at authoring time). Additional
fetchers for ERCOT / ENTSO-E / METI are TODO; contributors are welcome to add them
following the same shape.
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS_DIR = REPO_ROOT / "data_snapshots"
MANIFEST_PATH = SNAPSHOTS_DIR / "MANIFEST.json"


@dataclass
class SnapshotManifestEntry:
    """One row in the project's frozen-snapshot manifest."""
    source: str               # e.g. "noaa_ncei" / "ercot_public" / "entsoe_transparency" / "meti_eccj"
    event: str                # e.g. "texas_uri_feb_2021"
    version: str              # e.g. "v1"
    snapshot_file: str        # relative path under data_snapshots/
    source_url: str           # public URL the data was fetched from
    fetched_at_utc: str       # ISO timestamp of the developer's authoring-time fetch
    fetched_by: str           # contributor handle responsible for the fetch
    canonical_sha256: str     # SHA-256 of the snapshot file's canonical JSON content
    license_note: str         # license / attribution requirement of the upstream source


def canonical_sha256(obj) -> str:
    """SHA-256 over canonical JSON encoding of any object (sorted keys, no whitespace)."""
    encoded = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_manifest() -> list:
    if not MANIFEST_PATH.exists():
        return []
    with open(MANIFEST_PATH) as f:
        return json.load(f).get("entries", [])


def _save_manifest(entries: list):
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "manifest_version": "1.0",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
    }
    with open(MANIFEST_PATH, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


# ---------------------------------------------------------------------------
# RUNTIME LOADER (always available, network-free, used by voice files)
# ---------------------------------------------------------------------------

def load_snapshot(source: str, event: str, version: str = "v1") -> dict:
    """Load a frozen data snapshot. Verifies the snapshot's SHA-256 against the manifest.

    Used by every §4 historical-events voice file at runtime. No network calls.

    Raises FileNotFoundError if no matching manifest entry. Raises ValueError if the
    snapshot content's SHA-256 does not match the manifest-declared hash.
    """
    entries = _load_manifest()
    match = [e for e in entries
             if e["source"] == source and e["event"] == event and e["version"] == version]
    if not match:
        raise FileNotFoundError(
            f"no snapshot manifest entry for source={source}, event={event}, version={version}. "
            f"available entries: {[(e['source'], e['event'], e['version']) for e in entries]}"
        )
    entry = match[0]
    snapshot_path = SNAPSHOTS_DIR / entry["snapshot_file"]
    if not snapshot_path.exists():
        raise FileNotFoundError(
            f"manifest entry refers to {entry['snapshot_file']} but the file is not present in {SNAPSHOTS_DIR}"
        )
    with open(snapshot_path) as f:
        content = json.load(f)
    observed_sha = canonical_sha256(content)
    if observed_sha != entry["canonical_sha256"]:
        raise ValueError(
            f"snapshot SHA-256 mismatch for source={source} event={event} version={version}.\n"
            f"  manifest declared: {entry['canonical_sha256']}\n"
            f"  observed in file:  {observed_sha}\n"
            f"the snapshot file has been tampered with or corrupted since it was authored. "
            f"do not use this snapshot for measurement; investigate the discrepancy."
        )
    return {
        "data": content,
        "manifest_entry": entry,
    }


# ---------------------------------------------------------------------------
# AUTHORING TIME (developer-only — requires network)
# ---------------------------------------------------------------------------

def freeze_snapshot(source: str, event: str, version: str,
                    content: dict, source_url: str, fetched_by: str,
                    license_note: str) -> SnapshotManifestEntry:
    """Freeze a fetched dataset as a project snapshot. Writes the snapshot JSON + updates the manifest.

    This function is called at authoring time by a fetcher. Tests + voice files do not
    call this — they only call `load_snapshot`.
    """
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_filename = f"{source}__{event}__{version}.json"
    snapshot_path = SNAPSHOTS_DIR / snapshot_filename
    # Always write canonical JSON so SHA-256 is stable
    canonical = json.dumps(content, sort_keys=True, indent=2)
    with open(snapshot_path, "w") as f:
        f.write(canonical)
    # Re-read + hash the on-disk file so the manifest hash matches what the loader sees
    with open(snapshot_path) as f:
        sha = canonical_sha256(json.load(f))
    entry = SnapshotManifestEntry(
        source=source,
        event=event,
        version=version,
        snapshot_file=snapshot_filename,
        source_url=source_url,
        fetched_at_utc=datetime.now(timezone.utc).isoformat(),
        fetched_by=fetched_by,
        canonical_sha256=sha,
        license_note=license_note,
    )
    entries = _load_manifest()
    # remove any existing entry with the same (source, event, version) — overwrite semantics
    entries = [e for e in entries
               if not (e["source"] == source and e["event"] == event and e["version"] == version)]
    entries.append(asdict(entry))
    _save_manifest(entries)
    return entry


# ---------------------------------------------------------------------------
# Reference fetcher: NOAA NCEI Daily Summaries (free, public, no auth)
# ---------------------------------------------------------------------------

def fetch_noaa_texas_feb_2021_skeleton() -> dict:
    """REFERENCE FETCHER — skeleton-only for the OSS demo.

    A production fetcher would query NOAA NCEI's GHCN-Daily endpoint for Texas
    weather stations across Feb 11-20 2021 (the Uri winter storm window) and
    return per-station / per-day temperature + precipitation records.

    This skeleton returns a minimal synthetic shape with TODO markers so contributors
    can implement the real fetch behind it without changing the contract. Replacing
    this body with a real `urllib.request.urlopen(NOAA_URL)` call is a clean upgrade
    path.

    Run from the repo root:
        python tools/data_ingestion.py freeze-skeleton
    """
    return {
        "_TODO": (
            "Replace this synthetic skeleton with a real NOAA NCEI fetch. Endpoint: "
            "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries"
            "&stations=USW00012921,USW00013904,...&dataTypes=TMIN,TMAX,PRCP"
            "&startDate=2021-02-11&endDate=2021-02-20&format=json"
        ),
        "event": "texas_uri_feb_2021",
        "schema_version": "0.0-skeleton",
        "stations": [
            {"id": "TODO", "name": "TODO", "lat": None, "lon": None},
        ],
        "observations": [
            # Each observation: {"station": ..., "date": "YYYY-MM-DD", "TMIN_C": ..., "TMAX_C": ..., "PRCP_mm": ...}
        ],
        "fetch_metadata": {
            "skeleton_only": True,
            "real_fetch_pending": True,
            "implementation_hint": "use urllib.request.urlopen with json output format; cite station IDs from the NOAA station list for Texas",
        },
    }


# ---------------------------------------------------------------------------
# CLI: freeze-skeleton subcommand for the reference fetcher
# ---------------------------------------------------------------------------

def main(argv: list) -> int:
    if len(argv) < 2:
        print("usage: python tools/data_ingestion.py <command>")
        print("commands:")
        print("  list                       — list manifest entries")
        print("  freeze-skeleton            — freeze the NOAA Texas Feb 2021 SKELETON snapshot")
        print("  verify                     — verify all manifest entries match their snapshot SHA-256s")
        return 1
    cmd = argv[1]
    if cmd == "list":
        entries = _load_manifest()
        if not entries:
            print("(manifest is empty — no snapshots frozen yet)")
            return 0
        print(f"{'source':22s}  {'event':24s}  {'version':8s}  sha256[:16]")
        for e in entries:
            print(f"{e['source']:22s}  {e['event']:24s}  {e['version']:8s}  {e['canonical_sha256'][:16]}")
        return 0
    elif cmd == "freeze-skeleton":
        content = fetch_noaa_texas_feb_2021_skeleton()
        entry = freeze_snapshot(
            source="noaa_ncei",
            event="texas_uri_feb_2021",
            version="v0-skeleton",
            content=content,
            source_url="https://www.ncei.noaa.gov/access/services/data/v1",
            fetched_by="reference_fetcher_skeleton",
            license_note="NOAA NCEI Daily Summaries are in the public domain; cite NOAA NCEI as the source.",
        )
        print(f"froze {entry.source}__{entry.event}__{entry.version} (sha256[:16] = {entry.canonical_sha256[:16]})")
        print(f"  see {entry.snapshot_file} + MANIFEST.json under data_snapshots/")
        return 0
    elif cmd == "verify":
        entries = _load_manifest()
        if not entries:
            print("(manifest is empty — nothing to verify)")
            return 0
        all_ok = True
        for e in entries:
            try:
                load_snapshot(e["source"], e["event"], e["version"])
                print(f"  OK   {e['source']}__{e['event']}__{e['version']}")
            except (FileNotFoundError, ValueError) as ex:
                print(f"  FAIL {e['source']}__{e['event']}__{e['version']}: {ex}")
                all_ok = False
        return 0 if all_ok else 1
    else:
        print(f"unknown command: {cmd}")
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
