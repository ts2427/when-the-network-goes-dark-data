"""Version 2 must not change version 1's results: every chapter_* key of results.json equals the snapshot, numbers
within a relative tolerance of 1e-9 (absolute 1e-12 near zero) and everything else exactly (v2.2.0; before, a
SHA-256 of each key).

The snapshot holds the v1 keys as written by v2.2.0 (floats to 10 significant digits), after the correction to
Harvey's Sep 4-5, 2017 reports, whose changes are listed in docs/decisions.md (2026-11-24). Every other v1 number is
within a relative 1e-9 of version 2.1.0."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from compare import RTOL, differences  # noqa: E402
from config import OUTPUT  # noqa: E402
RESULTS = OUTPUT / "results.json"
SNAP = ROOT / "tests" / "snapshots" / "v1_results.json"


@pytest.mark.skipif(not RESULTS.exists(), reason=f"needs {RESULTS.name} from a build: run python run_all.py first")
def test_v1_chapter_keys_are_unchanged():
    r = json.loads(RESULTS.read_text(encoding="utf-8"))
    want = json.loads(SNAP.read_text(encoding="utf-8"))
    diffs = [d for k in want for d in differences(r[k], want[k], RTOL, k)]
    assert not diffs, diffs[:20]
