"""Version 3.1.0: the external check (step 15), days_since_day0, dates in load_panel(), clean_rows(), pinned Actions."""
import importlib
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import load  # noqa: E402
from config import INTERIM, PROCESSED  # noqa: E402

step15 = importlib.import_module("15_external_validation")
BUILT = pytest.mark.skipif(not (PROCESSED / "panel.parquet").exists() or not (INTERIM / "dirs_county_rows.parquet").exists(),
                           reason="needs the panel and the parsed rows from a build: run python run_all.py first")
READY = pytest.mark.skipif(not (PROCESSED / f"{load.NAME}.parquet").exists(),
                           reason="needs the analysis-ready panel from a build: run python run_all.py first")


@pytest.mark.parametrize("ours, fcc, status", [
    (4.04, "4", "match"), (4.04, "4.0", "match"), (60.7476, "60.7", "match"),  # rounded from the counts, not 60.75
    (6.25, "6.3", "match"),  # half up
    (1.667, "1.6", "match after truncation"),  # the FCC dropped the second decimal
    (2.01, "3.6", "differs"), (94.7, ">50", "match"), (49.9, ">50", "differs"),
])
def test_percent_status(ours, fcc, status):
    assert step15.pct_status(ours, fcc) == status


def test_percent_in_service_allows_the_out_share_with_its_decimals_dropped():
    # USVI, Sep 18, 2017: 54.72% out; the FCC prints 46% in service (100 - 54), rounding would give 45
    assert step15.pct_status(100 - 54.72, "46", out_share=54.72) == "match after truncation"
    assert step15.pct_status(100 - 2.97, "97", out_share=2.97) == "match"


def test_every_figure_that_cannot_match_by_rule_has_an_explanation():
    f = pd.read_csv(step15.FIGURES, dtype=str, keep_default_na=False)
    assert f.id.is_unique and set(f.storm) == {"Harvey", "Irma"}
    assert (f[f.measure == "no_panel_field"].explanation != "").all()


@BUILT
def test_external_check_counts_and_every_difference_is_explained():
    t = step15.check(pd.read_csv(step15.FIGURES, dtype=str, keep_default_na=False))
    assert step15.summary(t) == {"n": 80, "match": 55, "match after truncation": 4, "consistent": 1, "differs": 10,
                                 "no panel field": 10}
    assert (t[~t.status.isin(step15.NEEDS_NO_EXPLANATION)].explanation != "").all()


@BUILT
def test_external_check_stops_on_an_unexplained_difference():
    f = pd.read_csv(step15.FIGURES, dtype=str, keep_default_na=False)
    f.loc[f.id == "H20", "explanation"] = ""
    with pytest.raises(SystemExit, match="H20: differs with no explanation"):
        step15.check(f)


def test_clean_rows_levels():
    p = pd.DataFrame({"time_flag": ["", "pre_onset_likely_marco", "", None],
                      "report_status": ["ok", "ok", "flagged", "known_fcc_inconsistency"]})
    assert load.clean_rows(p).index.tolist() == [0, 2, 3]
    assert load.clean_rows(p, "standard").index.tolist() == [0, 2, 3]
    assert load.clean_rows(p, "strict").index.tolist() == [0, 3]
    with pytest.raises(ValueError, match="level must be one of"):
        load.clean_rows(p, "loose")
    assert set(load.CLEAN_LEVELS) == {"standard", "strict"}


def test_clean_rows_matches_the_analysis_filters():
    step10 = importlib.import_module("10_analysis")
    assert load.UNFLAGGED_STATUSES == step10.UNFLAGGED_STATUSES
    p = pd.DataFrame({"time_flag": ["", "x", None], "report_status": ["ok", "flagged", "flagged"]})
    pd.testing.assert_frame_equal(load.clean_rows(p), step10.timed(p))
    pd.testing.assert_frame_equal(load.clean_rows(p, "strict"), step10.without_flagged(step10.timed(p)))


@READY
@pytest.mark.parametrize("ext", ["parquet", "csv"])
def test_dates_and_days_since_day0(ext):
    p = load.load_panel(PROCESSED / f"{load.NAME}.{ext}")
    assert str(p.report_date.dtype) == "datetime64[ns]" and str(p.dirs_activation_date.dtype) == "datetime64[ns]"
    assert (p.report_date >= p.dirs_activation_date).all()
    assert p.days_since_day0.equals(p.days_since_landfall)
    cols = list(p.columns)
    assert cols.index("days_since_day0") == cols.index("days_since_landfall") + 1  # old columns keep their places


def _ci_workflow() -> str:
    public = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
    if public.exists():
        return public.read_text(encoding="utf-8")
    if not (PROCESSED / "dirs_county_day.csv").exists():
        pytest.skip("needs the published panel (step 14 reads it): run the pipeline first")
    return importlib.import_module("14_data_repo").CI_WORKFLOW


def test_every_action_is_pinned_to_a_commit_sha():
    lines = [ln.strip() for ln in _ci_workflow().splitlines() if ln.strip().startswith(("- uses:", "uses:"))]
    assert len(lines) == 3
    for ln in lines:
        assert re.fullmatch(r"(- )?uses: [\w.-]+/[\w.-]+@[0-9a-f]{40}  # v\d+\.\d+\.\d+", ln), ln


def test_ci_runs_monthly_lints_and_checks_the_notebook():
    w = _ci_workflow()
    assert re.search(r"schedule:\n\s+- cron: \"\d+ \d+ 1 \* \*\"", w)
    assert "ruff check" in w and "--nbmake examples/quickstart.ipynb" in w
