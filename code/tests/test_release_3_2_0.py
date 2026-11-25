"""Version 3.2.0 (addendum 4.x-1 and the Michael correction): the new parsers and rules, on fixed text, and the
tables' invariants."""
import importlib
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
cable = importlib.import_module("17_cable_wireline")
hazard = importlib.import_module("18_hazard_ncei")
fema = importlib.import_module("16_fema_ia")
from config import INTERIM, MANIFEST, OUTPUT, PROCESSED  # noqa: E402

HEAD = "Cable Systems and Wireline (Combined) "


# ---- step 17: the four printed forms (wording from the reports, as read 2026-11-25)
def test_sentence_with_next_sentence_previous_day():  # Beryl 2024-07-13 (DOC-403935A1)
    rows = cable.parse(HEAD + "Cable and wireline companies reported in the DIRS that there are 471,792 subscribers out "
                       "of service in the disaster area for Hurricane Beryl. This is down from 497,793 yesterday. "
                       "Broadcast: ...")
    assert rows == [{"area": "disaster area", "subscribers_out": 471792, "printed": "471,792", "form": "sentence",
                     "previous_day_printed": 497793}]


def test_sentence_naming_one_state_is_that_state():  # Michael 2018-10-21 (DOC-354668A1)
    text = ("In Florida, for example, the number of cable system and wireline subscribers out of service in the affected "
            "areas fell from 103,811 to 56,334 over the last three days. " + HEAD + "There are 56,334 cable system and "
            "wireline outage subscribers out of service in the affected areas in Florida. This is down from 60,300 "
            "yesterday. This number reflects outages.")
    [r] = cable.parse(text)
    assert (r["area"], r["subscribers_out"], r["previous_day_printed"]) == ("FL", 56334, 60300)  # not the 103,811


def test_sentence_naming_several_states_is_the_area_and_mid_sentence_previous_day():  # Irma 2017-09-12
    [r] = cable.parse(HEAD + "There are at least 7,184,909 (down from 7,597,945 yesterday) subscribers out of service in "
                      "the affected areas in Alabama, Florida, and Georgia. There are a total of 819 (up from 390 "
                      "yesterday) non-mobile switching centers out in Florida.")
    assert (r["area"], r["subscribers_out"], r["previous_day_printed"]) == ("disaster area", 7184909, 7597945)


def test_switching_centre_previous_day_is_not_taken():  # Harvey-style: the next "up from N yesterday" is not ours
    [r] = cable.parse(HEAD + "There are 189,487 subscribers out of service in the affected areas. There are 5 "
                      "switching centers out (up from 11 yesterday).")
    assert r["previous_day_printed"] is None


def test_code_table():  # Michael 2018-10-11 (DOC-354510A1)
    rows = cable.parse(HEAD + "The cable system and wireline outage table reflects outages. ... TOTAL 3,910 554 14.2% "
                       "State Subscribers Out of Service AL 14,855 FL 185,841 GA 63,473 P a ge | 7 Broadcast")
    assert [(r["area"], r["subscribers_out"]) for r in rows] == [("AL", 14855), ("FL", 185841), ("GA", 63473)]


def test_code_table_with_page_number():  # Zeta 2020-10-30 (DOC-367882A1)
    rows = cable.parse(HEAD + "The cable system and wireline outage table reflects outages. Subscribers Out of State "
                       "Service 10 AL 110,054 Broadcast:")
    assert [(r["area"], r["subscribers_out"]) for r in rows] == [("AL", 110054)]


def test_name_list():  # Ida 2021-08-30 (DOC-375318A1)
    rows = cable.parse(HEAD + "Cable and wireline companies reported the following number of subscribers out of service "
                       "by state in the disaster area; this may include the loss of telephone, television, and/or "
                       "Internet services: Alabama Louisiana Mississippi 478 338,115 16,106 Broadcast:")
    assert [(r["area"], r["subscribers_out"]) for r in rows] == [("AL", 478), ("LA", 338115), ("MS", 16106)]


def test_colon_list_keeps_none_and_ignores_page_numbers():  # Ian 2022-10-01 (DOC-387810A1, PDF order)
    rows = cable.parse(HEAD + "Florida: 441,799 Georgia: None South Carolina: 36,620 The following chart illustrates "
                       "... 9 Cable and wireline companies reported the following number of subscribers out of "
                       "service by state in the disaster area")
    assert [(r["area"], r["subscribers_out"], r["printed"]) for r in rows] == [
        ("FL", 441799, "441,799"), ("GA", None, "None"), ("SC", 36620, "36,620")]


def test_no_figure_printed():  # Irma 2017-09-07
    assert cable.parse(HEAD + "Since there are widespread power outages over Puerto Rico, large percentages of "
                       "consumers are without either cable services or wireline service. Broadcast") == []


# ---- step 18
@pytest.mark.parametrize("text, usd", [("10.00K", 10_000), ("0.15K", 150), ("1.5M", 1_500_000), ("2.00B", 2e9),
                                       ("", 0), (None, 0), ("0", 0)])
def test_ncei_damage_strings(text, usd):
    assert hazard.damage_usd(text) == usd


@pytest.mark.parametrize("ncei, county, agree", [
    ("DE SOTO", "DeSoto", True), ("INLAND PASCO", "Pasco", True), ("LOWER JEFFERSON COUNTY", "Jefferson", True),
    ("MONROE/LOWER KEYS", "Monroe", True), ("HARRIS", "Harris", True),
    ("WEST BATON ROUGE", "East Baton Rouge", False), ("OCRACOKE ISLAND", "Hyde", False),
    ("COASTAL SAN PATRICO COUNTY", "San Patricio", False), ("BOLIVAR PENINSULA", "Galveston", False)])
def test_zone_names_agree(ncei, county, agree):
    assert hazard.zone_names_agree(ncei, county) is agree


# ---- step 16
@pytest.mark.parametrize("disaster, state, county, fips, reason", [
    (4827, "NC", "Buncombe (County)", "37021", ""),
    (4827, "NC", "Eastern Band of Cherokee Indians", None, "tribal area"),
    (4337, "FL", "Statewide", None, "statewide"),
    (4332, "MO", "Dade (County)", None, "outside the disaster's states"),
    (4827, "NC", "Nowhere (County)", None, "")])  # an unknown county: no reason, so the build stops on it
def test_fema_set_aside(disaster, state, county, fips, reason):
    assert fema.set_aside_reason(disaster, state, county, fips, {4827: {"NC"}, 4337: {"FL"}, 4332: {"TX"}}) == reason


# ---- the built tables
built = pytest.mark.skipif(not (PROCESSED / "dirs_cable_wireline.csv").exists(), reason="run steps 16-18 first")


@built
def test_cable_table_keys_unique_and_every_report_present():
    c = pd.read_csv(PROCESSED / "dirs_cable_wireline.csv", dtype=str, keep_default_na=False)
    assert not c.duplicated(["storm_key", "doc_id", "area", "form"]).any()
    m = pd.read_csv(MANIFEST, dtype=str)
    assert set(c.doc_id) == set(m[m.status != "out_of_scope"].doc_id)


@built
def test_cable_table_recovers_every_area_figure_step3_parsed():
    """Every report where step 3 found the area figure has a figure here, and the sentence figures agree with step 3
    (before the 3.2.0 correction, four Michael reports differed: step 3 took the summary paragraph's 103,811)."""
    c = pd.read_csv(PROCESSED / "dirs_cable_wireline.csv", dtype={"subscribers_out": "Int64"})
    r = pd.read_parquet(INTERIM / "dirs_reports.parquet")[["doc_id", "cable_wireline_subs_out"]]
    r = r.dropna()
    have = c.dropna(subset=["subscribers_out"])
    assert set(r.doc_id) <= set(have.doc_id)
    s = have[have.form.str.contains("sentence")].drop_duplicates("doc_id").merge(r, on="doc_id")
    differ = set(s[s.subscribers_out != s.cable_wireline_subs_out].doc_id)
    assert differ == set()


@built
def test_fema_blank_when_not_declared_and_counts_when_declared():
    f = pd.read_csv(PROCESSED / "fema_ia_county_storm.csv", dtype=str, keep_default_na=False)
    nd, d = f[f.ia_declared == "False"], f[f.ia_declared == "True"]
    assert (nd.ihp_valid_registrations == "").all() and (d.ihp_valid_registrations != "").all()


@built
def test_external_checks_have_explanations():
    m = pd.read_csv(OUTPUT / "external_validation_fcc_michael.csv", dtype=str, keep_default_na=False)
    assert not m[~m.status.isin(["match", "consistent", "shown, not scored"]) & (m.explanation == "")].shape[0]
    o = pd.read_csv(OUTPUT / "external_validation_olukola.csv", dtype=str, keep_default_na=False).set_index("id")
    assert o.loc["O1", "status"] == "match" and o.loc["O2", "status"] == "match"


# ---- step 3 (v3.2.0 correction): the cable and wireline figure is read from its section, not a summary paragraph
def test_step3_reads_the_cable_section_not_the_summary():  # Michael 2018-10-21 (DOC-354668A1), wording as printed
    from dirs_parser import parse_text
    text = ("In Florida, for example, the number of cable system and wireline subscribers out of service in the affected "
            "areas fell from 103,811 to 56,334 over the last three days.\n"
            "Cable Systems and Wireline (Combined)\nThere are 56,334 cable system and wireline outage subscribers out "
            "of service in the affected areas in Florida. This is down from 60,300 yesterday.\n")
    assert parse_text(text).cable_wireline_subs_out == 56334


def test_step3_without_a_section_keeps_the_first_figure():  # reports with no section heading are read as before
    from dirs_parser import parse_text
    assert parse_text("Cable and wireline companies reported 471,792 subscribers out of service in the disaster "
                      "area.\n").cable_wireline_subs_out == 471792
