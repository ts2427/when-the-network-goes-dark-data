"""Harvey Sep 3-5, 2017 print a two-day table (previous day's out and %, then today's). Correction, 2026-11-24:
the parser had read the previous day as sites_out and today's count and % as out_damage and out_transport.

The excerpts below are verbatim from the FCC's text files (DOC-346482A1.txt and DOC-346499A1.txt), including the
FCC's own "X REFUGIO" (the state code is cut short in the text file; step 3 reads this report from the PDF)."""
import importlib
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from config import RAW  # noqa: E402
from dirs_parser import parse_text  # noqa: E402

step4 = importlib.import_module("04_validate_dirs")

SEP4 = """State
Affected
Counties
Cell Sites
Served
Cell Sites
Out on
09/03
Percent Out
on 09/03
Cell Sites
Out Today
(09/04)
Percent Out
Today
(09/04)
TX ARANSAS 19 2 10.50% 4 21.10%
TX CALHOUN 28 3 10.70% 3 10.70%
TX CHAMBERS 54 3 5.60% 2 3.70%
TX HARRIS 3,131 44 1.40% 27 0.90%
TX JEFFERSON 247 14 5.70% 7 2.80%
TX MATAGORDA 58 1 1.70% 0 0.00%
TX NUECES 267 5 1.90% 4 1.50%
TX ORANGE 85 20 23.50% 16 18.80%
X REFUGIO 26 0 0.00% 0 0.00%
TX SAN PATRICIO 58 1 1.70% 0 0.00%
TX VICTORIA 92 2 2.20% 2 2.20%
TX WHARTON 63 2 3.20% 1 1.60%
TX HARDIN 71 5 7.00% 4 5.60%
Total 4,200 102 2.40% 70 1.60%
"""

SEP5_HEAD = """Cell Sites
Out on
09/04
Percent Out
on 09/04
Cell Sites
Out Today
(09/05)
Percent Out
Today
(09/05)
TX ARANSAS 19 4 21.10% 4 21.10%
TX CALHOUN 28 3 10.70% 2 7.10%
TX CHAMBERS 54 2 3.70% 1 1.90%
"""


def test_two_day_header_is_detected_and_today_is_read():
    rep = parse_text(SEP4)
    assert (rep.previous_day, rep.today) == ("09/03", "09/04")
    aransas = next(r for r in rep.rows if r["county"] == "ARANSAS")
    assert (aransas["sites_served"], aransas["sites_out"], aransas["pct_out"]) == (19, 4, 21.1)
    assert (aransas["prev_sites_out"], aransas["prev_pct_out"]) == (2, 10.5)
    assert all(aransas[c] is None for c in ("out_damage", "out_transport", "out_power", "on_backup_power"))


def test_two_day_total_is_read_in_mixed_case():
    rep = parse_text(SEP4)
    [total] = rep.state_totals
    assert (total["sites_served"], total["sites_out"], total["pct_out"], total["prev_sites_out"]) == (4200, 70, 1.6, 102)
    assert sum(r["sites_out"] for r in rep.rows) == 70  # today's column sums to today's total (12 rows here)


def test_sep5_reads_sep5_not_sep4():
    rep = parse_text(SEP5_HEAD)
    assert (rep.previous_day, rep.today) == ("09/04", "09/05")
    calhoun = next(r for r in rep.rows if r["county"] == "CALHOUN")
    assert (calhoun["sites_out"], calhoun["pct_out"], calhoun["prev_sites_out"]) == (2, 7.1, 3)


def test_one_day_tables_are_unchanged():
    rep = parse_text("Texas Harris 3,131 44 1.4% 1 2 3 4\n")
    assert rep.today is None and "prev_sites_out" not in rep.rows[0]
    assert (rep.rows[0]["sites_out"], rep.rows[0]["out_transport"]) == (44, 2)


@pytest.mark.parametrize("doc, prev, today, aransas", [("DOC-346482A1", "09/03", "09/04", 4),
                                                       ("DOC-346499A1", "09/04", "09/05", 4)])
def test_real_reports(doc, prev, today, aransas):
    path = RAW / "dirs" / f"{doc}.txt"
    if not path.exists():
        pytest.skip(f"needs {path.name} (data/raw or data/input)")
    rep = parse_text(path.read_text(encoding="utf-8", errors="replace"))
    assert (rep.previous_day, rep.today) == (prev, today)
    assert next(r for r in rep.rows if r["county"] == "ARANSAS")["sites_out"] == aransas
    assert all(float(r[c]).is_integer() for r in rep.rows for c in ("sites_served", "sites_out", "prev_sites_out"))


def _rows(doc, date, data, prev=None):
    out = []
    for county, out_n, pct, *p in data:
        r = {"doc_id": doc, "storm_name": "Harvey", "report_date": date, "state": "Texas", "county": county,
             "sites_served": 19.0, "sites_out": out_n, "pct_out": pct}
        if prev:
            r["prev_sites_out"], r["prev_pct_out"] = p
        out.append(r)
    return out


REPORTS = pd.DataFrame({"doc_id": ["D3", "D4"], "storm_name": "Harvey", "report_date": ["2017-09-03", "2017-09-04"]})


def test_previous_day_column_must_match_the_previous_report():
    ok = pd.DataFrame(_rows("D3", "2017-09-03", [("ARANSAS", 2.0, 10.5)])
                      + _rows("D4", "2017-09-04", [("ARANSAS", 4.0, 21.1, 2.0, 10.5)], prev=True))
    problems, checked = step4.previous_day_mismatches(ok, REPORTS)
    assert problems == [] and checked == {"D4": ("D3", 1)}
    bad = ok.copy()
    bad.loc[bad.doc_id == "D4", "prev_sites_out"] = 3.0
    assert step4.previous_day_mismatches(bad, REPORTS)[0]
    missing = ok[~((ok.doc_id == "D3") & (ok.county == "ARANSAS"))]
    assert "not in the previous day's report" in step4.previous_day_mismatches(missing, REPORTS)[0][0]
    no_prev = ok[ok.doc_id == "D4"]
    assert "0 reports on the previous day" in step4.previous_day_mismatches(no_prev, REPORTS[REPORTS.doc_id == "D4"])[0][0]


def test_non_integer_counts_are_found():
    rows = pd.DataFrame(_rows("D4", "2017-09-04", [("ARANSAS", 4.0, 21.1)])).assign(out_transport=21.1)
    assert step4.non_integer_counts(rows) == ["D4 Texas/ARANSAS out_transport = 21.1"]
    assert step4.non_integer_counts(rows.assign(out_transport=2.0)) == []


def test_total_exception_applies_only_to_the_checked_total():
    entries = pd.DataFrame([{"doc_id": "D4", "page": 3, "state": "Texas", "column": "sites_served",
                             "printed_total": 4200, "rows_sum": 4199, "checked_on": "2026-11-24"}])
    fails, known = step4.apply_total_exceptions(["Texas sites_served 4199 vs printed total 4200"], entries, set())
    assert fails == [] and known and "4,200 vs 4,199" in known[0]
    fails, _ = step4.apply_total_exceptions(["Texas sites_served 4199 vs printed total 4200"], entries,
                                            {"Texas/HARRIS"})  # a row not confirmed: no exception
    assert fails[0] == "Texas sites_served 4199 vs printed total 4200"
    fails, _ = step4.apply_total_exceptions(["Texas sites_out 70 vs printed total 71"], entries, set())
    assert "Texas sites_out 70 vs printed total 71" in fails and any("no longer matches" in f for f in fails)


def test_a_total_right_after_a_page_footer_is_read():
    """Harvey Aug 28, 2017 (DOC-346381A1, PDF text): the footer's time-zone pattern took 'TOT' from the next line."""
    text = ("LA ASSUMPTION 23 0 0.0%\nTX ARANSAS 7,780 364 4.7%\n"
            "As prepared by the Federal Communications Commission: August 28, 2017 11:30 a.m.\n"
            "TOTAL  7,803 364 4.7%\n")
    rep = parse_text(text)
    assert [(t["sites_served"], t["sites_out"]) for t in rep.overall_totals] == [(7803, 364)]
    footer_tz = parse_text("TX ARANSAS 19 4 21.1%\nAs prepared by the Federal Communications Commission: "
                           "August 28, 2017 11:30 a.m. EDT\nTOTAL 19 4 21.1%\n")
    assert [(t["sites_served"], t["sites_out"]) for t in footer_tz.state_totals] == [(19, 4)]
