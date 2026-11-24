"""Each storm's bootstrap seed comes from a stable hash of its storm key (3.0.0), so adding a storm never changes
another storm's numbers. Until 3.0.0 the seed was the storm's position in date order, and adding Nate (2017) shifted
every later storm's intervals."""
import importlib
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from config import PROCESSED  # noqa: E402

step10 = importlib.import_module("10_analysis")
KEEP = ["Barry", "Nicholas", "Nicole", "Idalia"]  # small storms, so the test is quick; two have cause columns


def test_storm_seed_depends_only_on_the_key_and_the_stream():
    a = step10.storm_seed("AL092017_2017-08-25", 100)
    assert a == step10.storm_seed("AL092017_2017-08-25", 100)
    assert a != step10.storm_seed("AL092017_2017-08-25", 0) and a != step10.storm_seed("AL112017_2017-09-06", 100)
    assert 0 <= a < 2 ** 64


@pytest.fixture(scope="module")
def with_and_without_dummy():
    if not (PROCESSED / "panel.parquet").exists():
        pytest.skip("needs panel.parquet from a build: run python run_all.py first")
    panel = step10.timed(pd.read_parquet(PROCESSED / "panel.parquet"))
    storms = pd.read_parquet(PROCESSED / "storms.parquet")
    panel, storms = panel[panel.storm.isin(KEEP)], storms[storms.storm.isin(KEEP)]
    # a dummy storm, a copy of Nicole keyed and dated before every other storm, so it comes first in date order
    src = storms[storms.storm == "Nicole"].iloc[0]
    key = "AL991990_1990-01-01"
    d_storm = src.to_frame().T.assign(storm_key=key, storm="Dummy", nhc_id="AL991990",
                                      landfall_utc=pd.Timestamp("1990-01-02", tz="UTC"))
    d_panel = panel[panel.storm == "Nicole"].assign(storm_key=key, storm="Dummy", nhc_id="AL991990")
    more_storms = pd.concat([d_storm, storms], ignore_index=True).astype(storms.dtypes.to_dict())
    return panel, storms, pd.concat([d_panel, panel], ignore_index=True), more_storms


def _by_storm(records, name):
    return {r["storm_key"]: r for r in records[name] if r["storm_key"] != "AL991990_1990-01-01"}


def test_adding_a_storm_leaves_every_other_storms_recovery_and_cause_intervals_unchanged(with_and_without_dummy):
    panel, storms, panel2, storms2 = with_and_without_dummy
    assert _by_storm(step10.chapter_4(panel2, storms2), "storms") == _by_storm(step10.chapter_4(panel, storms), "storms")
    assert _by_storm(step10.chapter_5(panel2, storms2), "storms") == _by_storm(step10.chapter_5(panel, storms), "storms")


def test_adding_a_storm_leaves_every_other_storms_peak_interval_unchanged(with_and_without_dummy):
    panel, storms, panel2, storms2 = with_and_without_dummy
    before = {r["storm_key"]: step10.storm_peak(panel[panel.storm_key == r["storm_key"]],
                                                step10.storm_seed(r["storm_key"], 0)) for r in storms.to_dict("records")}
    keys = [k for k in storms2.storm_key if k in before]
    after = {k: step10.storm_peak(panel2[panel2.storm_key == k], step10.storm_seed(k, 0)) for k in keys}
    assert after == before


def test_adding_a_storm_leaves_every_other_storms_power_correlation_unchanged(with_and_without_dummy):
    panel, storms, panel2, storms2 = with_and_without_dummy
    keys, keys2 = list(storms.storm_key), list(storms2.storm_key)
    a = step10.comovement_block(panel, keys, step10.SEED + 300, lags=(0,))
    b = step10.comovement_block(panel2, keys2, step10.SEED + 300, lags=(0,))
    for y in a["lag_0h"]:
        assert {k: v for k, v in b["lag_0h"][y]["by_storm"].items() if k != "Dummy"} == a["lag_0h"][y]["by_storm"]
