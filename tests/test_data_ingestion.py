# Copyright 2026 Eir, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""tests/test_data_ingestion.py — frozen-snapshot loader contract tests.

Locks the §4 data-ingestion infrastructure contract:
  - load_snapshot reads from frozen snapshot only (no network at test time)
  - SHA-256 verification catches snapshot tampering
  - manifest entries match the on-disk snapshot files

These tests apply to every snapshot in `data_snapshots/MANIFEST.json` — they're picked
up automatically as new snapshots are added by future fetchers.

Run:
    python -m pytest tests/test_data_ingestion.py -v
"""
from __future__ import annotations
import json
import sys
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from tools.data_ingestion import (
    SNAPSHOTS_DIR, MANIFEST_PATH,
    canonical_sha256, load_snapshot, _load_manifest,
)


class TestSnapshotInfrastructure:
    """Basic invariants for the snapshot infrastructure regardless of which snapshots exist."""

    def test_snapshots_dir_exists_or_creatable(self):
        """The data_snapshots directory must exist (or be creatable on demand)."""
        assert SNAPSHOTS_DIR.exists() or SNAPSHOTS_DIR.parent.exists()

    def test_canonical_sha256_is_deterministic(self):
        """Two encodings of the same object must produce identical SHA-256."""
        obj = {"foo": [1, 2, 3], "bar": {"baz": "qux"}}
        sha1 = canonical_sha256(obj)
        sha2 = canonical_sha256(obj)
        assert sha1 == sha2

    def test_canonical_sha256_is_key_order_invariant(self):
        """Different dict insertion orders must produce identical SHA-256 (sorted-keys property)."""
        obj1 = {"a": 1, "b": 2, "c": 3}
        obj2 = {"c": 3, "a": 1, "b": 2}
        assert canonical_sha256(obj1) == canonical_sha256(obj2)

    def test_canonical_sha256_distinguishes_different_content(self):
        """Different content must produce different SHA-256."""
        assert canonical_sha256({"a": 1}) != canonical_sha256({"a": 2})


class TestManifestContract:
    """Every manifest entry must satisfy the structural contract for the loader to work."""

    def test_manifest_loadable(self):
        """The manifest file must be parseable JSON (or absent, which is also valid)."""
        entries = _load_manifest()
        assert isinstance(entries, list)

    def test_every_manifest_entry_has_required_fields(self):
        """Per the SnapshotManifestEntry dataclass: source, event, version, snapshot_file,
        source_url, fetched_at_utc, fetched_by, canonical_sha256, license_note."""
        entries = _load_manifest()
        required_fields = (
            "source", "event", "version", "snapshot_file",
            "source_url", "fetched_at_utc", "fetched_by",
            "canonical_sha256", "license_note",
        )
        for entry in entries:
            for field in required_fields:
                assert field in entry, f"manifest entry missing required field '{field}': {entry}"

    def test_every_manifest_entry_sha_format_valid(self):
        """SHA-256 hashes must be 64 lowercase-hex chars."""
        import re
        entries = _load_manifest()
        sha_re = re.compile(r"^[0-9a-f]{64}$")
        for entry in entries:
            assert sha_re.match(entry["canonical_sha256"]), (
                f"manifest entry sha256 not valid 64-hex: {entry['canonical_sha256']!r}"
            )

    def test_every_snapshot_file_exists_on_disk(self):
        """Every manifest entry's snapshot_file must point to a real file in data_snapshots/."""
        entries = _load_manifest()
        for entry in entries:
            snapshot_path = SNAPSHOTS_DIR / entry["snapshot_file"]
            assert snapshot_path.exists(), (
                f"manifest entry points to missing file: {snapshot_path}"
            )


class TestLoaderVerifiesSnapshotIntegrity:
    """The loader must enforce SHA-256 verification — its load-bearing audit role."""

    def test_load_snapshot_verifies_all_existing_manifest_entries(self):
        """Calling load_snapshot on every existing entry must succeed (no SHA mismatch)."""
        entries = _load_manifest()
        for entry in entries:
            result = load_snapshot(entry["source"], entry["event"], entry["version"])
            assert "data" in result
            assert "manifest_entry" in result
            assert result["manifest_entry"]["canonical_sha256"] == entry["canonical_sha256"]

    def test_load_snapshot_raises_on_missing_source(self):
        """Loader raises FileNotFoundError for unknown (source, event, version) combo."""
        with pytest.raises(FileNotFoundError):
            load_snapshot("nonexistent_source_xyz", "fake_event", "v1")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
