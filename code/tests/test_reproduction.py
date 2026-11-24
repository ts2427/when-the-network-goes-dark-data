"""The code reproduces the published files: run python run_all.py first (each check skips until then).

CSVs must match byte for byte. results.json: numbers within a relative 1e-9 (or 1e-12 absolute, for values that are
zero up to floating-point noise), everything else exactly (platforms' math libraries differ in the last bits). The
analysis-ready panel: value by value at the same tolerance."""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BUILD = REPO / "build"
PUBLISHED = REPO / "data" / "analysis"
sys.path.insert(0, str(REPO / "code" / "src"))
from compare import ATOL, RTOL, differences  # noqa: E402

NOT_BUILT = "needs build/ (not committed): run python run_all.py first"
built = pytest.mark.skipif(not (BUILD / "output" / "results.json").exists(), reason=NOT_BUILT)
CSV_PAIRS = [("processed/dirs_county_day.csv", "dirs_county_day.csv"), ("processed/storms.csv", "storms.csv")] + [
    (f"output/{n}", f"validation/{n}") for n in ("validation_dirs.csv", "validation_summary.csv",
                                                 "excluded_reports.csv", "area_status_counts.csv")]


@built
@pytest.mark.parametrize("built_path, published", CSV_PAIRS)
def test_csv_matches_published_byte_for_byte(built_path, published):
    got, want = (BUILD / built_path).read_bytes(), (PUBLISHED / published).read_bytes()
    if got != want:
        g, w = got.decode("utf-8").splitlines(), want.decode("utf-8").splitlines()
        diff = [(i + 1, a, b) for i, (a, b) in enumerate(zip(g, w)) if a != b]
        pytest.fail(f"{built_path}: {len(g)} vs {len(w)} lines, {len(diff)} differ; first: "
                    + " | ".join(f"line {n}: built {a!r} published {b!r}" for n, a, b in diff[:3]))


@built
def test_results_json_matches_published():
    got = json.loads((BUILD / "output" / "results.json").read_text(encoding="utf-8"))
    want = json.loads((PUBLISHED / "results.json").read_text(encoding="utf-8"))
    diffs = differences(got, want, RTOL)
    assert not diffs, f"{len(diffs)} differences, first: {diffs[:10]}"


@built
@pytest.mark.parametrize("ext", ["csv", "parquet"])
def test_analysis_ready_panel_matches_published(ext):
    import pandas as pd
    from load import load_panel
    got = load_panel(BUILD / "processed" / f"panel_analysis_ready.{ext}")
    want = load_panel(PUBLISHED / f"panel_analysis_ready.{ext}")
    pd.testing.assert_frame_equal(got, want, check_exact=False, rtol=RTOL, atol=ATOL)


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
