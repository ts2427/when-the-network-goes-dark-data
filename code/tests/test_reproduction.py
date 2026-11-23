"""The code reproduces the published files: run python run_all.py first."""
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BUILD = REPO / "build"
PAIRS = [("processed/dirs_county_day.csv", "dirs_county_day.csv"), ("processed/storms.csv", "storms.csv"),
         ("output/results.json", "results.json")]


@pytest.mark.skipif(not (BUILD / "output" / "results.json").exists(), reason="run python run_all.py first")
@pytest.mark.parametrize("built, published", PAIRS)
def test_build_matches_published(built, published):
    assert (BUILD / built).read_bytes() == (REPO / "data" / "analysis" / published).read_bytes(), built


@pytest.mark.skipif(not (BUILD / "output" / "results.json").exists(), reason="run python run_all.py first")
@pytest.mark.parametrize("name", ["validation_dirs.csv", "validation_summary.csv", "excluded_reports.csv",
                                  "area_status_counts.csv"])
def test_validation_tables_match(name):
    assert (BUILD / "output" / name).read_bytes() == (REPO / "data" / "analysis" / "validation" / name).read_bytes()


def test_inputs_match_their_hashes():
    import csv
    import hashlib
    with open(REPO / "data" / "input" / "INPUTS.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            assert hashlib.sha256((REPO / row["path"]).read_bytes()).hexdigest() == row["sha256"], row["path"]


def test_manifest_tables_unchanged():
    """Step 2b rewrites some of code/manifest; after a run they must equal the published tables."""
    import hashlib
    for line in (REPO / "code" / "manifest.sha256").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        assert hashlib.sha256((REPO / "code" / "manifest" / name).read_bytes()).hexdigest() == digest, name


def test_plan_as_committed_matches_its_hash():
    import hashlib
    line = (REPO / "docs" / "analysis_plan_as_committed.sha256").read_text(encoding="utf-8").split()
    assert hashlib.sha256((REPO / "docs" / line[1]).read_bytes()).hexdigest() == line[0]
