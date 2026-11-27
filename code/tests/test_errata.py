"""ERRATA.md (2026-11-25): every CORRECTION entry is classified; published changes quote their entry word for word."""
import importlib
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from config import DOCS, PROCESSED  # noqa: E402

pytestmark = pytest.mark.skipif(not (PROCESSED / "dirs_county_day.csv").exists(),
                                reason="step 14 reads the published panel: run the pipeline first")


def step14():
    return importlib.import_module("14_data_repo")


def test_every_correction_is_classified_and_every_value_is_in_its_entry():
    t = step14().errata_rows((DOCS / "decisions.md").read_text(encoding="utf-8"))
    assert set(t.kind) == {"published", "process"}
    pub = t[t.kind == "published"]
    assert set(pub.version) <= {"2.0.0", "3.0.0", "3.1.0", "4.0.0"} and (pub[["what", "before", "after", "why"]] != "").all().all()


def test_a_value_missing_from_its_entry_stops_the_build(tmp_path, monkeypatch):
    m = step14()
    t = pd.read_csv(m.ERRATA, dtype=str, keep_default_na=False)
    t.loc[t.what == "Storms in the panel", "after"] = "23"
    bad = tmp_path / "errata.csv"
    t.to_csv(bad, index=False)
    monkeypatch.setattr(m, "ERRATA", bad)
    with pytest.raises(SystemExit, match="value '23' not in its quote"):
        m.errata_rows((DOCS / "decisions.md").read_text(encoding="utf-8"))


def test_an_unclassified_correction_stops_the_build():
    m = step14()
    log = (DOCS / "decisions.md").read_text(encoding="utf-8")
    log += "\n| 2026-12-01 | CORRECTION (a new one): something changed | why |\n"
    with pytest.raises(SystemExit, match="not classified"):
        m.errata_rows(log)


def test_dependabot_updates_actions_only():
    text = step14().DEPENDABOT
    assert "package-ecosystem: github-actions" in text and "package-ecosystem: pip" not in text
