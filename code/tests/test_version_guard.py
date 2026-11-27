"""Version guard (4.0.0): no published file changes within a major version.

code/snapshots/published_sha256.json holds the SHA-256 of every file under data/analysis when the current major
version was first released, and code/snapshots/results_frozen.json a copy of its results.json. A minor version may add
files; a patch may change no published file. If any listed file changes or disappears, this fails unless the major
number in CITATION.cff differs from the snapshot's (a new major version, whose release writes a new snapshot)."""
import hashlib
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SNAP = REPO / "code" / "snapshots"


def cff_major() -> int:
    text = (REPO / "CITATION.cff").read_text(encoding="utf-8")
    return int(re.search(r'^version: "?(\d+)\.', text, re.M).group(1))


def test_published_files_unchanged_within_the_major_version():
    snap = json.loads((SNAP / "published_sha256.json").read_text(encoding="utf-8"))
    if cff_major() != snap["major"]:
        pytest.skip(f"CITATION.cff is a new major version ({cff_major()}); its release writes a new snapshot")
    changed = [p for p, h in snap["files"].items()
               if not (REPO / p).exists() or hashlib.sha256((REPO / p).read_bytes()).hexdigest() != h]
    assert not changed, f"published files changed within major version {snap['major']}: {changed[:10]}"


def test_results_json_matches_the_frozen_copy():
    snap = json.loads((SNAP / "published_sha256.json").read_text(encoding="utf-8"))
    if cff_major() != snap["major"]:
        pytest.skip("a new major version")
    got = json.loads((REPO / "data" / "analysis" / "results.json").read_text(encoding="utf-8"))
    assert got == json.loads((SNAP / "results_frozen.json").read_text(encoding="utf-8"))
