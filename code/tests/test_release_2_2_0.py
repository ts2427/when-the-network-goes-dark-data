"""v2.2.0 engineering changes: results.json rounding, the tolerant comparison, count columns, the analysis-ready
panel and its loader. No result changes."""
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from compare import differences  # noqa: E402
from config import PROCESSED  # noqa: E402
from tables import as_counts  # noqa: E402
import load  # noqa: E402

step10 = importlib.import_module("10_analysis")
carried = importlib.import_module("carried")


def test_floats_are_rounded_to_ten_significant_digits_and_nothing_else_changes():
    got = step10.round_floats({"a": 0.1 + 0.2, "b": [1 / 3, 7, True, None, "x"], "c": np.float64(2) / 3,
                               "d": float("inf"), "e": 123456789012.5})
    assert got == {"a": 0.3, "b": [0.3333333333, 7, True, None, "x"], "c": 0.6666666667, "d": float("inf"),
                   "e": 123456789000.0}
    assert type(got["b"][1]) is int and type(got["b"][2]) is bool


def test_write_chapter_rounds(tmp_path):
    path = tmp_path / "r.json"
    step10.write_chapter(path, "k", {"v": 2 / 3})
    assert json.loads(path.read_text(encoding="utf-8")) == {"k": {"v": 0.6666666667}}


def test_comparison_allows_last_digit_noise_but_not_changes():
    want = {"x": 1.234567891, "n": 5, "s": "a", "l": [0.5, None]}
    assert differences({"x": 1.234567891 * (1 + 5e-10), "n": 5.0, "s": "a", "l": [0.5, None]}, want) == []
    assert differences({"x": 1.234567891 * (1 + 5e-9), "n": 5, "s": "a", "l": [0.5, None]}, want)
    assert differences({"x": 1.234567891, "n": 5, "s": "b", "l": [0.5, None]}, want)  # strings exact
    assert differences({"x": 1.234567891, "n": 5, "s": "a", "l": [0.5]}, want)  # lengths exact
    assert differences({"x": 1.234567891, "n": True, "s": "a", "l": [0.5, None]}, want)  # bool is not a number
    assert differences({"s": "a", "x": 1.234567891, "n": 5, "l": [0.5, None]}, want)  # key order exact


def test_counts_are_integers_and_negative_zero_is_zero():
    df = pd.DataFrame({"n": [42.0, np.nan, -0.0], "x": [1.5, 2.0, 3.0]})
    out = as_counts(df, ["n"])
    assert str(out.n.dtype) == "Int64" and out.to_csv(index=False, lineterminator="\n") == "n,x\n42,1.5\n,2.0\n0,3.0\n"
    with pytest.raises(SystemExit):
        as_counts(df, ["x"])


def test_overattributed_is_never_negative_zero():
    df = pd.DataFrame({"sites_out": [3.0, 3.0], "out_damage": [1, 2], "out_transport": [1, 1], "out_power": [1, 1]})
    over = carried.add_unattributed(df).out_overattributed
    assert list(over) == [0.0, 1.0] and not np.signbit(over).any()


@pytest.mark.skipif(not (PROCESSED / f"{load.NAME}.parquet").exists(),
                    reason="needs the analysis-ready panel from a build: run python run_all.py first")
def test_analysis_ready_panel_loads_the_same_from_csv_and_parquet_and_matches_the_published_panel():
    a = load.load_panel(PROCESSED / f"{load.NAME}.parquet")
    b = load.load_panel(PROCESSED / f"{load.NAME}.csv")
    pd.testing.assert_frame_equal(a, b, check_exact=False, rtol=1e-9)
    pub = pd.read_csv(PROCESSED / "dirs_county_day.csv", dtype=str, keep_default_na=False)
    assert list(a.columns[:len(pub.columns)]) == list(pub.columns)
    assert (a.doc_id.to_numpy() == pub.doc_id.to_numpy()).all() and (a.fips.to_numpy() == pub.fips.to_numpy()).all()
    assert a.fips.str.fullmatch(r"\d{5}").all()
    assert set(a.wind_zone) <= set(step10.ZONES)


def test_values_that_are_zero_up_to_noise_match():
    # chapter 7's in-sample calibration-in-the-large: -2.35e-15 here, -2.67e-15 and -3.05e-15 on the CI machines
    assert differences({"v": -2.669789202e-15}, {"v": -2.35065873e-15}) == []
    assert differences({"v": 1e-11}, {"v": 0.0})  # above the floor it is a real difference
