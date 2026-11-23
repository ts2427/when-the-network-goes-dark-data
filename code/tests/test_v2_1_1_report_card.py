"""V2.1-1 report card: generated from the validation outputs; counts and denominators consistent."""
import importlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from config import OUTPUT  # noqa: E402

v2 = importlib.import_module("12_v2_analysis")
step11 = importlib.import_module("11_build_page")
RESULTS = OUTPUT / "results.json"
needs = pytest.mark.skipif(not (OUTPUT / "validation_dirs.csv").exists(), reason="needs the validation outputs")


@needs
def test_every_validated_report_is_counted_once_per_storm():
    r = json.loads(RESULTS.read_text(encoding="utf-8"))
    rec = v2.report_records(r)
    v = pd.read_csv(OUTPUT / "validation_dirs.csv")
    assert set(rec.doc_id) == set(v.doc_id)
    assert not rec.duplicated(["doc_id", "storm_key"]).any()
    assert set(rec[rec.excluded].doc_id) == set(v[v.status == "excluded"].doc_id)


@needs
def test_counts_never_exceed_their_denominators_and_years_add_up():
    r = json.loads(RESULTS.read_text(encoding="utf-8"))
    rc = v2.report_card(r)
    for block in [rc["all_reports"], *rc["by_year"], *rc["by_storm"]]:
        for k, _, _ in v2.RC_MEASURES:
            assert 0 <= block[k]["count"] <= block[k]["of"] <= block["n_reports"]
    assert sum(y["n_reports"] for y in rc["by_year"]) == rc["all_reports"]["n_reports"]


@needs
def test_backup_column_agrees_with_the_panel():
    r = json.loads(RESULTS.read_text(encoding="utf-8"))
    rec = v2.report_records(r).dropna(subset=["backup_printed"])
    p = pd.read_parquet(OUTPUT.parent / "data" / "processed" / "panel.parquet", columns=["doc_id", "on_backup_power"]) \
        if (OUTPUT.parent / "data" / "processed" / "panel.parquet").exists() else None
    if p is None:
        pytest.skip("needs the panel")
    printed = p.groupby("doc_id").on_backup_power.apply(lambda s: s.notna().any())
    assert all(bool(printed[d]) == bool(b) for d, b in zip(rec.doc_id, rec.backup_printed))


def test_page_wording_is_descriptive():
    if not RESULTS.exists() or "v2_1_1_report_card" not in json.loads(RESULTS.read_text(encoding="utf-8")):
        pytest.skip("report card not computed")
    text = step11.report_card_section(json.loads(RESULTS.read_text(encoding="utf-8"))).lower()
    for bad in ("improved", "worsened", "better", "worse", "deteriorat", "quality"):
        assert bad not in text, bad



@needs
def test_shares_match_counts():
    rc = v2.report_card(json.loads(RESULTS.read_text(encoding="utf-8")))
    for block in [rc["all_reports"], *rc["by_year"], *rc["by_storm"]]:
        for k, _, _ in v2.RC_MEASURES:
            c = block[k]
            assert c["share_pct"] == (round(100 * c["count"] / c["of"], 1) if c["of"] else None)


@needs
def test_reports_with_excess_causes_do_not_carry_the_fccs_note():
    """The page says none of the reports with causes above sites out carries the FCC's multiple-causes note."""
    v = pd.read_csv(OUTPUT / "validation_dirs.csv", keep_default_na=False)
    over = v[(v.sites_overattributed != "") & (v.sites_overattributed.replace("", "0").astype(float) > 0)]
    assert len(over) and not over.fcc_multiple_causes_note.astype(str).eq("True").any()



def test_whole_percents_on_the_page_come_from_the_counts():
    import re
    from decimal import Decimal, ROUND_HALF_UP
    if not RESULTS.exists() or "v2_1_1_report_card" not in json.loads(RESULTS.read_text(encoding="utf-8")):
        pytest.skip("report card not computed")
    text = step11.report_card_section(json.loads(RESULTS.read_text(encoding="utf-8")))
    cells = re.findall(r"(\d+) of (\d+) \((\d+)%\)", text)
    assert cells
    for k, n, pct in cells:
        want = (Decimal(100) * int(k) / int(n)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        assert int(pct) == want, (k, n, pct)
