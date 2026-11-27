"""Version 4.0.0 (corrections from the review of v3.2.1): the parser, second-reading, storm-key and manifest rules, on
fixed text, and the built tables' invariants."""
import importlib
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dirs_parser import TOTAL_ROW_RE, parse_text  # noqa: E402
from storm_keys import assign_storm_keys  # noqa: E402
from config import INTERIM, MANIFEST, OUTPUT, PROCESSED  # noqa: E402

validate = importlib.import_module("04_validate_dirs")
check_manifest = importlib.import_module("01_check_manifest")
HEADER = "State County Cell Sites Served Cell Sites Out Percent Out Damage Transport Power Backup\n"


# ---- parser
def test_state_code_total_line_is_that_states_total():  # Helene 2024-09-28 (DOC-405893A1)
    m = TOTAL_ROW_RE.match("GA - 13083 1293 9.88% 9 273 987 844")
    assert m and m.group("code") == "GA"
    rep = parse_text(HEADER + "GA APPLING 22 0 0.0% 0 0 0 0\nGA BACON 10 1 10.0% 0 0 1 0\n"
                     "GA - 32 1 3.13% 0 0 1 0\nFL BAKER 30 0 0.0% 0 0 0 0\nTOTAL - 30 0 0.0% 0 0 0 0\n")
    totals = {t["state"]: t["sites_served"] for t in rep.state_totals}
    assert totals == {"Georgia": 32, "Florida": 30}


def test_a_county_row_is_never_read_as_a_state_code_total():
    assert TOTAL_ROW_RE.match("GA APPLING 22 0 0.0% 0 0 0 0") is None
    assert TOTAL_ROW_RE.match("GA 13083 1293 9.88% 9 273 987 844") is None  # the dash is required


def test_backquoted_county_names_are_read():  # Laura 2020-08-29 (DOC-366524A1), Maryland
    rep = parse_text(HEADER + "MD PRINCE GEORGE`S 811 0 0.0% 0 0 0 0\nMD QUEEN ANNE`S 64 0 0.0% 0 0 0 0\n"
                     "MD ST. MARY`S 126 0 0.0% 0 0 0 0\nMD ST. MARY’S 126 0 0.0% 0 0 0 0\n")
    assert [r["county"] for r in rep.rows] == ["PRINCE GEORGE`S", "QUEEN ANNE`S", "ST. MARY`S", "ST. MARY’S"]


def test_as_of_date_with_no_space_before_the_day():  # Laura 2020-09-01 (DOC-366601A1)
    rep = parse_text("This report provides information ... as of September1, 2020 at 12:00 p.m. EDT.\n")
    assert (rep.as_of_date, rep.as_of_time, rep.as_of_tz) == ("2020-09-01", "12:00", "EDT")


# ---- second reading
def _row(state, county, *nums):
    cols = ["sites_served", "sites_out", "pct_out", "out_damage", "out_transport", "out_power", "on_backup_power"]
    return {"state": state, "county": county, "pct_printed": True, "prev_sites_out": None, "prev_pct_out": None,
            **dict(zip(cols, [float(n) for n in nums] + [float("nan")] * (len(cols) - len(nums))))}


@pytest.mark.parametrize("lines, row", [
    (["TX SABINE 6 1 16.7% 1 0 0", "SAN 16.7%", "6 1 1 0 0", "TX AUGUSTINE", "TX SAN JACINTO 49 0 0.0% 0 0 0"],
     _row("Texas", "SAN AUGUSTINE", 6, 1, 16.7, 1, 0, 0)),  # Laura 2020-08-28 (DOC-366519A1)
    (["TN Unicoi 17 8 47.1% 0 6 2 0", "Washington", "TN 132 12 9.1% 0 9 3 0"],
     _row("Tennessee", "Washington County", 132, 12, 9.1, 0, 9, 3, 0)),  # Helene 2024-10-04 (DOC-406197A1)
])
def test_rows_split_across_lines_are_confirmed(lines, row):
    split = [line.split() for line in lines]
    assert validate.row_reading(row, split) == "split"


def test_split_lines_need_exactly_the_rows_numbers_and_name():
    split = [line.split() for line in ["SAN 16.7%", "6 1 1 0 0", "TX AUGUSTINE"]]
    assert validate.row_reading(_row("Texas", "SAN AUGUSTINE", 6, 1, 16.7, 1, 0, 1), split) is None  # a value differs
    assert validate.row_reading(_row("Louisiana", "SAN AUGUSTINE", 6, 1, 16.7, 1, 0, 0), split) is None  # state code
    assert validate.row_reading(_row("Texas", "SAN JACINTO", 6, 1, 16.7, 1, 0, 0), split) is None  # name


def test_a_plain_text_parse_needs_an_independent_reading():
    row = _row("Mississippi", "ADAMS", 35, 0, 0.0, 0, 0, 0)
    g = pd.DataFrame([row])
    plain_only = pd.DataFrame({"reading": ["pdf_plain"], "line": ["MS ADAMS 35 0 0.0% 0 0 0"]})
    assert validate.second_reading(g, plain_only, plain_is_parse=False)[:2] == ([], "pdf_plain_text")
    assert validate.second_reading(g, plain_only, plain_is_parse=True)[0] == ["Mississippi/ADAMS"]
    cells_short = pd.concat([plain_only, pd.DataFrame({"reading": ["pdf_cells"], "line": ["MS ADAMS 35 0 0.0% 0"]})])
    assert validate.second_reading(g, cells_short, plain_is_parse=True)[0] == ["Mississippi/ADAMS"]
    with_pdfium = pd.concat([cells_short, pd.DataFrame({"reading": ["pdfium"], "line": ["MS ADAMS 35 0 0.0% 0 0 0"]})])
    assert validate.second_reading(g, with_pdfium, plain_is_parse=True)[:2] == ([], "pdfium")


# ---- storm keys
def test_a_state_only_the_second_storms_notice_covers_takes_its_key():  # Harrison County, Texas, Ida/Nicholas
    rows = pd.DataFrame({"storm_name": ["Ida", "Ida", "Ida"], "nhc_id": ["AL092021"] * 3,
                         "report_date": ["2021-09-15"] * 3, "state": ["Texas", "Louisiana", "Louisiana"],
                         "county": ["HARRISON", "ORLEANS", "ACADIA"]})
    shared = pd.DataFrame({"notice": ["DA-21-1152A1"] * 2, "storm_page": ["ida"] * 2, "applies_from": ["2021-09-15"] * 2,
                           "state": ["Texas", "Louisiana"], "county": ["Brazoria", "Acadia"],
                           "assigned_storm": ["Nicholas", "Ida"], "assigned_nhc_id": ["AL142021", "AL092021"],
                           "flag": ["", "also named by the second storm's notice; kept with the first storm"]})
    storms = pd.DataFrame({"storm_name": ["Ida", "Nicholas"], "storm_page": ["ida", "ida"],
                           "dirs_activation_date": ["2021-08-29", "2021-09-14"]})
    states = pd.DataFrame({"storm_page": ["ida"] * 3, "state": ["Louisiana", "Mississippi", "Texas"],
                           "began_notice": ["DA-21-1070A1", "DA-21-1070A1", "DA-21-1152A1"]})
    out = assign_storm_keys(rows, shared, storms, states).set_index("county")
    assert out.at["HARRISON", "row_storm"] == "Nicholas"
    assert out.at["HARRISON", "storm_key_flag"] == "state covered only by the second storm's notice"
    assert out.at["ORLEANS", "row_storm"] == "Ida" and out.at["ACADIA", "row_storm"] == "Ida"


# ---- manifest
def test_manifest_status_must_be_confirmed():
    df = pd.read_csv(MANIFEST)
    assert check_manifest.check(df.assign(status=df.status.replace({"ok": "verify"}))), "verify must fail"
    assert check_manifest.check(df, pd.read_csv(ROOT / "manifest" / "excluded_reports.csv", dtype=str)) == []


# ---- built tables (after the pipeline has run)
built = pytest.mark.skipif(not (PROCESSED / "dirs_county_day.csv").exists(), reason="needs the built panel")


@built
def test_restored_reports_are_in_the_panel_and_none_is_excluded():
    p = pd.read_csv(PROCESSED / "dirs_county_day.csv", dtype=str)
    assert {"DOC-366519A1", "DOC-366524A1", "DOC-366526A1", "DOC-406144A1", "DOC-406197A1"} <= set(p.doc_id)
    v = pd.read_csv(OUTPUT / "validation_dirs.csv", dtype=str, keep_default_na=False)
    assert not (v.status.isin(["fail", "excluded"])).any()
    assert set(v.second_reading) <= {"pdf_plain_text", "txt", "pdfium", "pdf_cells", "pdfium and txt",
                                     "pdf_cells and txt", "pdf_cells and pdfium", "pdf_cells and pdfium and txt"}


@built
def test_harrison_texas_is_nicholas_and_laura_sep_1_time_is_printed():
    p = pd.read_csv(PROCESSED / "dirs_county_day.csv", dtype=str)
    h = p[(p.state == "Texas") & p.county.str.upper().str.startswith("HARRISON")
          & p.doc_id.isin(["DOC-375778A1", "DOC-375808A1"])]
    assert (h.storm == "Nicholas").all() and len(h) == 2
    assert set(p[p.doc_id == "DOC-366601A1"].as_of_imputed) == {"False"}


@built
def test_county_name_census_is_one_name_per_fips():
    p = pd.read_csv(PROCESSED / "dirs_county_day.csv", dtype=str)
    assert p.county_name_census.notna().all()
    assert (p.groupby("fips").county_name_census.nunique() == 1).all()


@built
def test_eaglei_pct_out_only_where_the_mcc_flag_is_ok():
    a = pd.read_parquet(PROCESSED / "panel_analysis_ready.parquet")
    assert a.loc[a.eaglei_mcc_flag != "ok", "eaglei_pct_out"].isna().all()
    assert a.eaglei_pct_out.dropna().between(0, 100).all()


def test_interim_lines_keep_their_reading():
    lines = INTERIM / "dirs_pdf_lines.parquet"
    if not lines.exists():
        pytest.skip("needs step 3")
    assert set(pd.read_parquet(lines, columns=["reading"]).reading) <= {"pdf_plain", "txt", "pdf_cells", "pdfium"}
