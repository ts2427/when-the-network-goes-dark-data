"""Step 14 (Phase C): assemble the public data repository, when-the-network-goes-dark-data.

Usage: python src/14_data_repo.py [TARGET]   (default: ../../when-the-network-goes-dark-data next to threshold-site)

Copies only what may be published:
  data/input/     FCC DIRS reports (PDF and text), FCC notices, the two FCC orders cited, Census, ACS, CDC/ATSDR SVI,
                  OpenFEMA pages, NHC files, EAGLE-I's filtered extract plus MCC.csv and coverage_history.csv (never a
                  year file), and the BDC county provider counts (counts only; never a raw BDC file or provider ID).
                  INPUTS.csv gives each file's source, URL, retrieval time and SHA-256.
  data/analysis/  the published panel, the storm table, results.json (what the page shows) and, since 2.2.0, the
                  analysis-ready panel (CSV and Parquet).
  code/           the pipeline (src/), its hand-made tables (manifest/) and tests, with a config.py that reads
                  data/input and writes build/.
  docs/           the analysis plan as committed (with its SHA-256), the addendum, the decision log, sources notes.
Writes README.md, SOURCES.md, CITATION.cff, CHANGELOG.md, DEVIATIONS.md, AI_ASSISTANCE.md, LICENSE, LICENSE-DATA.md,
datapackage.json and CODEBOOK.md (generated from datapackage.json), run_all.py, requirements.txt, requirements.lock
(copied from this project, with hashes; uv pip compile) and the CI workflow (.github/workflows/ci.yml). Then checks
datapackage.json with frictionless (0 errors or it stops).
Never copies .env, .venv, data/interim, data/raw/bdc, the EAGLE-I year files or anything else not listed here.
"""
import hashlib
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

import load
from config import (BDC_COUNTS, BDC_COUNTS_META, DOWNLOADS_LOG, EAGLEI_EXTRACT, EAGLEI_RAW_DIR, OUTPUT, PROCESSED,
                    RAW, REGIMES, ROOT)

VERSION = "3.1.0"
RELEASE_DATE = "2026-11-24"
CREATED = f"{RELEASE_DATE}T12:00:00-06:00"  # datapackage.json created: ISO 8601 date-time (v2.2.0)
# Set to True only after CI has passed on both ubuntu-latest and windows-latest (README then says so).
CI_PASSED_ON_BOTH = False  # 3.1.0: set to True once CI passes on both
GITHUB = "https://github.com/ts2427/when-the-network-goes-dark-data"
BOOTSTRAP_NOTE = importlib.import_module("11_build_page").BOOTSTRAP_METHODS
PUBLIC_REQUIREMENTS = [
    "pandas==2.3.3", "numpy==2.5.5", "scipy==1.18.1", "statsmodels==0.15.0", "scikit-learn==1.9.1",
    "lifelines==0.30.3", "pdfplumber==0.11.11", "pdfminer.six==20260107", "geopandas==1.2.0", "shapely==2.2.0",
    "pyogrio==0.13.0", "pyproj==3.8.0", "pyarrow==26.0.1", "requests==2.34.2", "pytest==9.2.0",
    "frictionless==5.21.0", "matplotlib==3.11.2", "nbmake==1.5.5", "ipykernel==7.4.0", "ruff==0.17.6"]
LOCKFILE = ROOT / "requirements.lock"  # uv pip compile requirements.txt --universal --generate-hashes (see README)
_PANEL = pd.read_csv(PROCESSED / "dirs_county_day.csv", usecols=["storm_key", "doc_id"])
N_STORMS, N_REPORTS = _PANEL.storm_key.nunique(), _PANEL.doc_id.nunique()  # from the panel, never typed
N_STORMS_210 = 21  # storms in the panel as published in 2.1.0 (CHANGELOG history)
REPO_NAME = "when-the-network-goes-dark-data"
TITLE = "When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code)"
AUTHOR = {"family": "Spivey", "given": "Timothy D.", "orcid": "0009-0009-8990-4308"}
PAGE_URL = "https://thresholddatasciences.com/analysis/when-the-network-goes-dark/"
PLAN_COMMIT = "9fc17a4"
PLAN_FILE = "docs/analysis_plan.md"
STUDY_FIPS = {"48", "22", "28", "01", "12", "13", "45", "37", "47", "51"}

# data/input subfolder -> (source label, files): every published input, by name
INPUT_DIRS = {
    "dirs": "FCC DIRS Communications Status Reports",
    "notices": "FCC DIRS activation and area-change notices",
    "census": "U.S. Census Bureau",
    "acs": "U.S. Census Bureau, ACS 5-year 2022 (Census Data API)",
    "svi": "CDC/ATSDR Social Vulnerability Index 2022",
    "fema": "OpenFEMA Disaster Declarations Summaries v2",
}
NHC_FILES = ["hurdat2-1851-2025-092326.txt", "al092026_best_track.zip"]
RULE_FILES = ["FCC-22-50A1_Rcd.pdf", "FCC-26-34A1.txt"]
EXTERNAL_FILES = ["DOC-353805A1.pdf"]  # the FCC's 2017 season report, for the external check (step 15, v3.1.0)
EAGLEI_FILES = ["MCC.csv", "coverage_history.csv"]  # unmodified EAGLE-I files; the year files are never copied
BDC_LISTINGS = ["storm_releases.json", "provider_summary_files.csv"]
STORM_PAGE_FILES = ["fcc_storm_documents.csv", "fcc_storm_documents_supplement.csv", "README_fcc_storm_documents.md"]

NEVER = (".env", ".venv", "__pycache__", "bdc_provider_county", "eaglei_outages_", "bdc_us_provider_summary",
         "listAvailabilityData", ".pytest_cache")
MAX_BYTES = 50 * 1024 * 1024

# --------------------------------------------------------------------------------------------------- codebook --
PERIODS = "; ".join(f"P{i}: {name} ({start} to {end if end < '2099' else 'present'})"
                    for i, (name, start, end) in enumerate(REGIMES))
SITE_LIMIT = ("Cell sites as reported by providers to the FCC; a site out is not a count of people without service "
              "(the FCC's caveat).")
PANEL_FIELDS = [
    # name, type, description, unit, limitation
    ("storm_key", "string", "Storm key: NHC ID and DIRS activation date, joined by an underscore.", "",
     "Names repeat across years (Isaias 2020 and 2026); always join on this key, not the name."),
    ("nhc_id", "string", "National Hurricane Center storm ID (basin, number, year).", "", ""),
    ("storm", "string", "Storm name.", "", "Not unique across years."),
    ("dirs_activation_date", "date", "Date the FCC activated DIRS for the storm.", "", ""),
    ("rule_period", "string", f"FCC rule period by activation date. {PERIODS}.", "",
     "Descriptive grouping only; periods differ in storms, hazards and filers."),
    ("doc_id", "string", "FCC EDOCS document number of the report.", "", ""),
    ("report_date", "date", "Date of the report.", "", ""),
    ("as_of_utc", "datetime", "The report's stated as-of time, in UTC.", "UTC",
     "Where the report prints none, set to 12:00 Eastern on the report date (as_of_imputed)."),
    ("as_of_imputed", "boolean", "True when as_of_utc was set to 12:00 Eastern because the report prints no time.", "",
     ""),
    ("report_status", "string", "Validation status of the report (step 4): ok, flagged (a check raised a note) or "
     "known_fcc_inconsistency (a stated total the FCC's own rows do not sum to, listed in "
     "code/manifest/known_fcc_inconsistencies.csv).", "", "Excluded reports are not in the file."),
    ("state", "string", "State, as printed.", "", "Ten study states only."),
    ("county", "string", "County as printed by the FCC (upper case).", "",
     "Spellings vary between reports; use fips."),
    ("fips", "string", "Five-digit county FIPS code (with leading zero).", "",
     "Mapped from the printed name with code/manifest/fips_exceptions.csv."),
    ("sites_served", "integer", "Cell sites served in the county, as reported.", "sites",
     "The denominator differs by storm and report; compare percentages with care. " + SITE_LIMIT),
    ("sites_out", "integer", "Cell sites out of service in the county, as reported.", "sites", SITE_LIMIT),
    ("pct_out", "number", "Percent of sites out, as printed (computed from the two counts where not printed).",
     "percent", "Where pct_printed is false the value is computed, not printed."),
    ("pct_printed", "boolean", "True when the report printed the percent column.", "", ""),
    ("out_damage", "integer", "Sites out due to damage, as reported.", "sites",
     "Blank where the report has no cause columns. Causes can overlap (see out_overattributed)."),
    ("out_transport", "integer", "Sites out due to transport (backhaul), as reported.", "sites",
     "Blank where the report has no cause columns."),
    ("out_power", "integer", "Sites out due to power, as reported.", "sites",
     "Blank where the report has no cause columns."),
    ("on_backup_power", "integer", "Sites operating on backup power, as reported.", "sites",
     "Blank where the report has no such column. Not a measure of sites about to fail."),
    ("out_unattributed", "integer", "Sites out with no cause given: sites_out minus the three causes, never below 0.",
     "sites", "Blank where the report has no cause columns. Kept apart from out_overattributed; never net them."),
    ("out_overattributed", "integer", "Causes in excess of sites out (sites counted under more than one cause).",
     "sites", "Blank where the report has no cause columns."),
    ("area_status", "string", "Whether the county is in the FCC's notice area on the report date: inside, "
     "inside_spelling_variant, outside_notice_area or table_not_in_list.", "",
     "From the FCC's notices (code/manifest/reporting_areas.csv)."),
    ("fema_declared", "boolean", "True if OpenFEMA lists a declaration for the storm covering the county.", "",
     "Context for reuse only; no result uses it. This product uses the Federal Emergency Management Agency's "
     "OpenFEMA API, but is not endorsed by FEMA."),
    ("time_flag", "string", "Blank, or pre_onset_likely_marco for Laura's Aug 25, 2020 report (the FCC's combined "
     "Marco and Laura report), which is kept but left out of every time-based result.", "", ""),
]
STORM_FIELDS = [
    ("nhc_id", "string", "National Hurricane Center storm ID.", "", ""),
    ("dirs_activation_date", "date", "Date the FCC activated DIRS.", "", ""),
    ("storm_key", "string", "NHC ID and DIRS activation date.", "", ""),
    ("storm", "string", "Storm name.", "", "Not unique across years."),
    ("rule_period", "string", f"FCC rule period by activation date. {PERIODS}.", "", "Blank for storms not in the panel."),
    ("landfall_utc", "datetime", "Day 0: the first time the storm's 34-kt wind radii reach a study-state county "
     "(fallback: first study-state landfall at tropical-storm strength or above).", "UTC",
     "Defined from NHC best-track radii; see docs/decisions.md (2026-11-23)."),
    ("landfall_source", "string", "Which rule set day 0.", "", ""),
    ("previous_landfall_utc", "datetime", "Day 0 under the original rule (kept for chapter 8's comparison).", "UTC",
     "Superseded; not used for the main results."),
    ("interim_landfall_utc", "datetime", "Day 0 under the first 2026-11-23 rule (kept for comparison).", "UTC",
     "Superseded; not used for the main results."),
    ("n_reports", "integer", "Reports in the panel.", "reports", "Blank for storms not in the panel."),
    ("n_counties", "integer", "Counties in the panel.", "counties", "Blank for storms not in the panel."),
    ("first_report", "date", "First report date in the panel.", "", ""),
    ("last_report", "date", "Last report date in the panel.", "", "The FCC's last public report, not the end of outages."),
    ("excluded_reports", "string", "Reports left out, with date and reason.", "", ""),
    ("in_panel", "boolean", "True if the storm has at least one report in the panel.", "", ""),
]
BDC_FIELDS = [
    ("release", "date", "FCC Broadband Data Collection release (as-of date).", "", ""),
    ("fips", "string", "Five-digit county FIPS code.", "", "Study-state counties only."),
    ("mobile_half", "integer", "Mobile broadband providers reporting coverage of at least half of the county.",
     "providers", "Reported coverage, not which networks were out; providers are never named."),
    ("mobile_any", "integer", "Mobile broadband providers reporting any coverage in the county.", "providers",
     "Reported coverage, not which networks were out."),
    ("fixed_any_excl_near_universal", "integer", "Fixed providers with any residential service, near-universal "
     "providers excluded.", "providers", "Near-universal: service in at least 95% of study-state counties."),
    ("fixed_any", "integer", "Fixed providers with any residential service.", "providers",
     "Includes near-universal (likely satellite or national fixed-wireless) providers."),
    ("fixed_half", "integer", "Fixed providers serving at least half of residential locations.", "providers", ""),
    ("fixed_half_excl_near_universal", "integer", "As fixed_half, near-universal providers excluded.", "providers", ""),
]

_EAGLEI_LIMIT = ("ORNL/DOE EAGLE-I (CC BY 4.0); 'customers' are meters. Blank where no EAGLE-I record lies within 30 "
                 "minutes of the time (never set to zero); see eaglei_match.")
_GROUP_NOTE = ("For storms before 2022 (bdc_role 'sensitivity') the release postdates the storm; chapter 13's main "
               "analysis uses storms from 2022 on.")
ANALYSIS_READY_EXTRA = [  # v2.2.0: columns of panel_analysis_ready after the published panel's (PANEL_FIELDS)
    ("eaglei_time", "datetime", "Time of the EAGLE-I record matched to the report's as-of time.", "UTC",
     "Blank when no record lies within 30 minutes."),
    ("eaglei_match", "string", "EAGLE-I match at the as-of time: matched, no_record_within_30min, "
     "county_not_in_eaglei_window, no_as_of_time or no_eaglei_release (Isaias 2026; EAGLE-I ends in 2025).", "", ""),
    ("eaglei_gap_min", "number", "Minutes between the matched record and the as-of time.", "minutes", ""),
    ("eaglei_customers_out", "integer", "Electricity customers out at the as-of time.", "customers", _EAGLEI_LIMIT),
    ("eaglei_customers_out_6h", "integer", "Customers out 6 hours before the as-of time.", "customers", _EAGLEI_LIMIT),
    ("eaglei_customers_out_12h", "integer", "Customers out 12 hours before.", "customers", _EAGLEI_LIMIT),
    ("eaglei_customers_out_24h", "integer", "Customers out 24 hours before.", "customers", _EAGLEI_LIMIT),
    ("eaglei_customers_out_zero_filled", "integer", "As eaglei_customers_out, with no record counted as 0 where the "
     "county has an EAGLE-I record in the storm's window.", "customers", "Sensitivity display only."),
    ("eaglei_modeled_customers", "integer", "EAGLE-I modeled customers in the county (MCC.csv).", "customers",
     "Below observed outages in some counties; see eaglei_mcc_flag."),
    ("eaglei_pct_out", "number", "eaglei_customers_out as a percent of eaglei_modeled_customers.", "percent",
     "Not used where eaglei_mcc_flag is not ok."),
    ("eaglei_max_out_in_window", "integer", "Highest customers out in the storm's EAGLE-I window (21 days before "
     "activation to 21 days after deactivation).", "customers", ""),
    ("eaglei_release", "boolean", "True if EAGLE-I covers the storm's year (through 2025).", "", ""),
    ("eaglei_mcc_flag", "string", "ok, mcc_below_observed_outages (percent out not used) or no_mcc.", "", ""),
    ("eaglei_coverage_flag", "string", "ok, low_coverage (state's minimum covered share below 0.75 that year; kept), "
     "coverage_unknown (no published coverage for the year) or no_eaglei_release.", "", "Coverage is published by "
     "state and year only (2018-2022)."),
    ("eaglei_state_min_covered", "number", "State's minimum share of customers covered by EAGLE-I in the storm year.",
     "share (0-1)", "Blank when not published."),
    ("eaglei_state_max_covered", "number", "State's maximum share of customers covered in the storm year.",
     "share (0-1)", "Blank when not published."),
    ("min_dist_km", "number", "Distance from the county's Census internal point to the storm's track (15-minute "
     "interpolation).", "km", "NHC HURDAT2; Isaias 2026 from the GIS best track."),
    ("wind_kt_at_closest", "number", "Storm's maximum sustained wind at the track point closest to the county.",
     "knots", ""),
    ("in_34kt", "boolean", "True if the county's internal point fell inside the 34-knot wind radii at some time.", "",
     ""),
    ("in_50kt", "boolean", "True if inside the 50-knot wind radii at some time.", "", ""),
    ("in_64kt", "boolean", "True if inside the 64-knot wind radii at some time.", "", ""),
    ("wind_zone", "string", "Chapter 7's wind zone from the three radii: inside 64 kt, 50-64 kt, 34-50 kt or outside "
     "34 kt.", "", ""),
    ("first_34kt_utc", "datetime", "First time the county was inside the 34-knot wind radii.", "UTC",
     "Blank if never inside."),
    ("nearest_landfall_utc", "datetime", "The storm's HURDAT2 landfall nearest the county.", "UTC",
     "Blank for Isaias 2026 (no landfall marker in the GIS best track)."),
    ("nearest_landfall_km", "number", "Distance from the county to that landfall.", "km", ""),
    ("track_source", "string", "HURDAT2 or GIS best track (Isaias 2026).", "", ""),
    ("landfall_utc", "datetime", "Day 0: the first time the storm's 34-knot wind radii reach a study-state county.",
     "UTC", "Same for every county of a storm; see storms.csv."),
    ("landfall_source", "string", "Which rule set day 0.", "", ""),
    ("days_since_landfall", "number", "Deprecated alias of days_since_day0 (same values), kept until 4.0.0.",
     "days", "Use days_since_day0: day 0 is not always a landfall (see landfall_source)."),
    ("days_since_day0", "number", "Days from day 0 to the report's as-of time (since 3.1.0).", "days", ""),
    ("svi_overall", "number", "CDC/ATSDR SVI 2022 overall national percentile rank (RPL_THEMES).", "percentile (0-1)",
     "Chapter 8's quartiles are of the at-risk storm-counties, not of this column's national cut points."),
    ("svi_socioeconomic", "number", "SVI 2022 theme 1, socioeconomic status (RPL_THEME1).", "percentile (0-1)", ""),
    ("svi_household", "number", "SVI 2022 theme 2, household characteristics (RPL_THEME2).", "percentile (0-1)", ""),
    ("svi_minority_language", "number", "SVI 2022 theme 3, racial and ethnic minority status (RPL_THEME3).",
     "percentile (0-1)", ""),
    ("svi_housing_transport", "number", "SVI 2022 theme 4, housing type and transportation (RPL_THEME4).",
     "percentile (0-1)", ""),
    ("acs_households", "integer", "Households, ACS 2022 5-year (B11001_001E).", "households", ""),
    ("acs_population", "integer", "Population, ACS 2022 5-year (B01001_001E).", "people", ""),
    ("acs_pct_65plus", "number", "Percent of the population aged 65 or over, ACS 2022 5-year (B01001).", "percent", ""),
    ("acs_pct_broadband", "number", "Percent of households with a broadband subscription, ACS 2022 5-year "
     "(B28002_004E / B28002_001E).", "percent", ""),
    ("bdc_release", "date", "FCC Broadband Data Collection release matched to the storm: the latest on or before day "
     "0, or the earliest for storms before 2022.", "", ""),
    ("bdc_role", "string", "main (storms from 2022 on) or sensitivity: network data from after the storm.", "", ""),
    ("bdc_mobile_half", "integer", "Mobile providers covering at least half the county's area (chapter 13's main "
     "measure).", "providers", "Reported coverage, not which networks were out; providers are never named."),
    ("bdc_mobile_any", "integer", "Mobile providers with any coverage in the county.", "providers", ""),
    ("bdc_fixed_any_excl_near_universal", "integer", "Fixed providers with any residential service, near-universal "
     "providers excluded.", "providers", ""),
    ("bdc_fixed_any", "integer", "Fixed providers with any residential service.", "providers", ""),
    ("bdc_fixed_half", "integer", "Fixed providers serving at least half of residential locations.", "providers", ""),
    ("bdc_fixed_half_excl_near_universal", "integer", "As bdc_fixed_half, near-universal providers excluded.",
     "providers", ""),
    ("bdc_mobile_half_group", "string", "Chapter 13's group on bdc_mobile_half: 2 or fewer, 3, or 4 or more "
     "(cut points fixed from counts only; results.json v2_5_groups).", "", _GROUP_NOTE),
    ("first_report_date", "date", "The county's first report in the storm's panel.", "", ""),
    ("last_report_date", "date", "The county's last report in the storm's panel.", "", ""),
    ("n_reports_county", "integer", "Reports in the storm's panel that list the county.", "reports", ""),
    ("censoring", "string", "none, left_reports_while_out (left the reports before the storm's last report while "
     "still out) or out_at_last_report.", "", "Censored counties are not recovered."),
]
ANALYSIS_READY_FIELDS = PANEL_FIELDS + ANALYSIS_READY_EXTRA


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)


# -------------------------------------------------------------------------------------------------- inputs --
def copy_inputs(T: Path) -> pd.DataFrame:
    log = pd.read_csv(DOWNLOADS_LOG, dtype=str, keep_default_na=False)
    log = log[log.status != "exists"].drop_duplicates("path", keep="last").set_index("path")
    rows, inp = [], T / "data" / "input"

    def add(src: Path, rel: str, source: str, logged: str, note: str = ""):
        copy(src, inp / rel)
        hit = log.loc[logged] if logged in log.index else None
        status = "" if hit is None else hit.status
        if status.startswith("not found"):
            note = ("The FCC served a 'not found' page for this .txt URL; the saved page is kept because step 3 reads "
                    "the .txt first and then falls back to the PDF, which holds the report.")
        rows.append({"path": f"data/input/{rel}", "source": source,
                     "doc_id": src.stem if rel.startswith(("dirs/", "notices/", "rules/")) else "",
                     "url": "" if hit is None else hit.url, "retrieved_utc": "" if hit is None else hit["when"],
                     "download_status": status, "sha256": sha256(inp / rel), "bytes": (inp / rel).stat().st_size,
                     "note": note})

    for sub, source in INPUT_DIRS.items():
        for p in sorted((RAW / sub).iterdir()):
            if p.is_file() and not p.name.startswith("."):
                add(p, f"{sub}/{p.name}", source, f"data/raw/{sub}/{p.name}")
    for name in NHC_FILES:
        add(RAW / "nhc" / name, f"nhc/{name}", "NOAA National Hurricane Center", f"data/raw/nhc/{name}")
    for name in RULE_FILES:
        add(RAW / "rules" / name, f"rules/{name}", "FCC orders (cited for rule dates)", f"data/raw/rules/{name}")
    for name in EXTERNAL_FILES:
        add(RAW / "rules" / name, f"rules/{name}", "FCC PSHSB report (external check, step 15)",
            f"data/raw/rules/{name}")
    for name in STORM_PAGE_FILES:
        add(RAW / "storm_pages" / name, f"storm_pages/{name}", "FCC storm pages (document lists)",
            f"data/raw/storm_pages/{name}", "Compiled by reading the FCC storm pages (www.fcc.gov/<storm>) on "
            "2026-11-22; see README_fcc_storm_documents.md. No single URL.")
    for name in EAGLEI_FILES:
        add(EAGLEI_RAW_DIR / name, f"eaglei/{name}", "ORNL/DOE EAGLE-I (unmodified)", f"$EAGLEI_RAW_DIR/{name}")
    add(EAGLEI_EXTRACT, "eaglei/eaglei_extract.parquet", "ORNL/DOE EAGLE-I (modified)", "",
        "Derived by code/src/06_eaglei.py from the 2017-2024 year files: study counties and storm windows only "
        "(21 days before activation to 21 days after deactivation). Modified: aggregated to county at report times.")
    for name in BDC_LISTINGS:
        add(RAW / "bdc" / "listings" / name, f"bdc/listings/{name}", "FCC Broadband Data Collection (file list)",
            f"data/raw/bdc/listings/{name}", "Written by code/src/06c_bdc_list.py from the FCC's file listings: "
            "the files used and each storm's release (the latest on or before its day 0).")
    add(BDC_COUNTS, "bdc/bdc_county_provider_counts.csv", "FCC Broadband Data Collection (derived counts)", "",
        "Derived by code/src/06e_bdc_counties.py and 06f_bdc_counts.py: provider counts by county and release; "
        "no provider ID or name.")
    add(BDC_COUNTS_META, "bdc/bdc_county_provider_counts_meta.json", "FCC Broadband Data Collection (derived)", "",
        "The number of near-universal fixed providers and the measure definitions.")
    idx = pd.DataFrame(rows)
    idx.to_csv(inp / "INPUTS.csv", index=False, lineterminator="\n")
    return idx


# ------------------------------------------------------------------------------------------------ analysis --
def copy_analysis(T: Path) -> None:
    a = T / "data" / "analysis"
    copy(PROCESSED / "dirs_county_day.csv", a / "dirs_county_day.csv")
    copy(PROCESSED / "storms.csv", a / "storms.csv")  # written by step 9 (counts as integers) since v2.2.0
    for ext in ("csv", "parquet"):
        copy(PROCESSED / f"panel_analysis_ready.{ext}", a / f"panel_analysis_ready.{ext}")
    copy(OUTPUT / "results.json", a / "results.json")
    for f in ("validation_dirs.csv", "validation_summary.csv", "excluded_reports.csv", "area_status_counts.csv",
              "external_validation_fcc_2017.csv"):
        copy(OUTPUT / f, a / "validation" / f)


# -------------------------------------------------------------------------------------------------- code --
PUBLIC_CONFIG_PATHS = '''"""Paths and constants shared by all scripts (public data repository).

The constants below the path block are the private project's, unchanged. Only the paths differ: inputs are read from
data/input and every output goes to build/ (set WTNGD_BUILD to use another folder). tests/test_reproduction.py
compares build/ with the published files in data/analysis.
"""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "code"
RAW = REPO / "data" / "input"
BUILD = Path(os.environ.get("WTNGD_BUILD", str(REPO / "build")))
INTERIM = BUILD / "interim"
PROCESSED = BUILD / "processed"
OUTPUT = BUILD / "output"
DOCS = REPO / "docs"
MANIFEST = ROOT / "manifest" / "dirs_reports.csv"
DOWNLOADS_LOG = ROOT / "manifest" / "downloads.csv"  # every download; a rerun adds nothing (files exist)
# MCC.csv and coverage_history.csv only (the year files are not redistributed); EAGLEI_RAW_DIR overrides it
EAGLEI_RAW_DIR = Path(os.environ.get("EAGLEI_RAW_DIR", str(RAW / "eaglei")))
EAGLEI_EXTRACT = RAW / "eaglei" / "eaglei_extract.parquet"
BDC_COUNTS = RAW / "bdc" / "bdc_county_provider_counts.csv"
BDC_COUNTS_META = RAW / "bdc" / "bdc_county_provider_counts_meta.json"
for _d in (INTERIM, PROCESSED, OUTPUT):
    _d.mkdir(parents=True, exist_ok=True)
'''


def public_config() -> str:
    s = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
    start = s.index("\n\ndef census_api_key")
    return PUBLIC_CONFIG_PATHS + s[start:]


def copy_code(T: Path) -> None:
    c = T / "code"
    for p in sorted((ROOT / "src").glob("*.py")):
        if p.name == "config.py":
            write(c / "src" / "config.py", public_config())
        else:
            copy(p, c / "src" / p.name)
    hashes = []
    for p in sorted((ROOT / "manifest").iterdir()):
        if p.is_file():
            copy(p, c / "manifest" / p.name)
            hashes.append(f"{sha256(p)}  {p.name}")
    # step 2b rewrites some of these tables; the reproduction test checks they come out unchanged
    write(c / "manifest.sha256", "\n".join(hashes) + "\n")
    for p in sorted((ROOT / "tests").rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            copy(p, c / "tests" / p.relative_to(ROOT / "tests"))


# -------------------------------------------------------------------------------------------------- docs --
def plan_as_committed(T: Path) -> dict:
    blob = subprocess.run(["git", "-C", str(ROOT), "show", f"{PLAN_COMMIT}:{PLAN_FILE}"], capture_output=True,
                          check=True).stdout
    when = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%ad", "--date=iso-strict", PLAN_COMMIT],
                          capture_output=True, text=True, check=True).stdout.strip()
    blob_id = subprocess.run(["git", "-C", str(ROOT), "rev-parse", f"{PLAN_COMMIT}:{PLAN_FILE}"], capture_output=True,
                             text=True, check=True).stdout.strip()
    dest = T / "docs" / f"analysis_plan_as_committed_{PLAN_COMMIT}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(blob)
    info = {"file": dest.name, "commit": PLAN_COMMIT, "committed": when, "git_blob": blob_id,
            "sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)}
    write(T / "docs" / "analysis_plan_as_committed.sha256",
          f"{info['sha256']}  {dest.name}\n")
    return info


def copy_docs(T: Path) -> None:
    for name in ("analysis_plan.md", "analysis_plan_addendum_v2.md", "decisions.md", "data_sources.md",
                 "literature.md", "update_procedure.md", "external_validation.md", "restructure_plan.md"):
        copy(ROOT / "docs" / name, T / "docs" / name)
    copy(ROOT / "examples" / "quickstart.ipynb", T / "examples" / "quickstart.ipynb")
    copy(ROOT / "ruff.toml", T / "ruff.toml")


def deviations_md(T: Path) -> None:
    step11 = importlib.import_module("11_build_page")
    text = (ROOT / "docs" / "decisions.md").read_text(encoding="utf-8")
    lines = ["# Deviations from the analysis plan", "",
             "Generated by `code/src/14_data_repo.py` from `docs/decisions.md`: every entry marked DEVIATION, then every "
             "entry marked CORRECTION, in the log's order and wording. The full log is `docs/decisions.md`.", "",
             "## Deviations", "", "| Date | Deviation | Reason |", "|---|---|---|"]
    lines += [f"| {d} | {w} | {y} |" for d, w, y in step11.deviations(text)]
    lines += ["", "## Corrections", "", "| Date | Correction | Reason |", "|---|---|---|"]
    lines += [f"| {d} | {w} | {y} |" for d, w, y in step11.corrections(text)]
    write(T / "DEVIATIONS.md", "\n".join(lines) + "\n")


# --------------------------------------------------------------------------------------------- data package --
def schema(fields, primary_key, missing=("",)) -> dict:
    out = []
    for name, typ, desc, unit, limit in fields:
        f = {"name": name, "type": typ, "description": desc}
        if unit:
            f["unit"] = unit
        if limit:
            f["limitations"] = limit
        if typ == "string" and name == "fips":
            f["constraints"] = {"pattern": "^[0-9]{5}$", "required": True}
        if typ == "boolean":
            f["trueValues"], f["falseValues"] = ["True"], ["False"]
        if typ == "datetime":
            f["format"] = "any"
        out.append(f)
    return {"fields": out, "primaryKey": primary_key, "missingValues": list(missing)}


def datapackage(T: Path, plan: dict) -> dict:
    a = T / "data" / "analysis"
    panel_cols = list(pd.read_csv(a / "dirs_county_day.csv", nrows=0).columns)
    storm_cols = list(pd.read_csv(a / "storms.csv", nrows=0).columns)
    bdc_cols = list(pd.read_csv(T / "data" / "input" / "bdc" / "bdc_county_provider_counts.csv", nrows=0).columns)
    ready_cols = list(pd.read_csv(a / "panel_analysis_ready.csv", nrows=0).columns)
    dates = pd.read_csv(a / "dirs_county_day.csv", usecols=["report_date"]).report_date
    for cols, fields, name in ((panel_cols, PANEL_FIELDS, "panel"), (storm_cols, STORM_FIELDS, "storms"),
                               (bdc_cols, BDC_FIELDS, "bdc"), (ready_cols, ANALYSIS_READY_FIELDS, "analysis-ready")):
        if cols != [f[0] for f in fields]:
            raise SystemExit(f"{name}: documented fields {[f[0] for f in fields]} differ from the file's {cols}")
    pkg = {
        # "data-package", not "tabular-data-package": results.json, the parquet and the plan file are not tables
        "profile": "data-package", "name": REPO_NAME, "title": TITLE, "version": VERSION,
        "created": CREATED, "homepage": PAGE_URL,
        "description": ("County-by-report panel of FCC Disaster Information Reporting System (DIRS) cell-site outages "
                        f"for {N_STORMS} Atlantic hurricanes and tropical storms in ten Gulf and Southeast states, 2017-2026, "
                        "checked against each report's printed totals, with the inputs and code that rebuild it."),
        "keywords": ["hurricanes", "cell sites", "telecommunications outages", "FCC DIRS", "disaster resilience",
                     "power outages", "EAGLE-I", "Gulf Coast"],
        "contributors": [{"title": "Timothy D. Spivey", "role": "author",
                          "path": f"https://orcid.org/{AUTHOR['orcid']}"}],
        "licenses": [{"name": "CC-BY-4.0", "title": "Creative Commons Attribution 4.0 International (data)",
                      "path": "https://creativecommons.org/licenses/by/4.0/"},
                     {"name": "MIT", "title": "MIT License (code)", "path": "https://opensource.org/license/mit"}],
        "temporalCoverage": f"{dates.min()}/{dates.max()}", "spatialCoverage": "Texas, Louisiana, Mississippi, Alabama, "
        "Florida, Georgia, South Carolina, North Carolina, Tennessee, Virginia (United States), county level",
        "resources": [
            {"name": "dirs_county_day", "path": "data/analysis/dirs_county_day.csv", "profile": "tabular-data-resource",
             "format": "csv", "mediatype": "text/csv", "encoding": "utf-8",
             "title": "FCC DIRS cell-site outages by county and report",
             "description": f"One row per county per FCC DIRS report in use ({N_REPORTS} reports, {N_STORMS} storms).",
             "schema": schema(PANEL_FIELDS, ["storm_key", "doc_id", "fips"])},
            {"name": "storms", "path": "data/analysis/storms.csv", "profile": "tabular-data-resource",
             "format": "csv", "mediatype": "text/csv", "encoding": "utf-8", "title": "Storm table",
             "description": "One row per storm with a DIRS activation in scope, including storms with no usable report.",
             "schema": schema(STORM_FIELDS, ["storm_key"])},
            {"name": "panel_analysis_ready", "path": "data/analysis/panel_analysis_ready.csv",
             "profile": "tabular-data-resource", "format": "csv", "mediatype": "text/csv", "encoding": "utf-8",
             "title": "Analysis-ready panel: the county-report panel with every covariate the analysis uses",
             "description": "The rows of dirs_county_day.csv, in the same order, joined with EAGLE-I power outages "
                            "and coverage flags, exposure and wind zone, day 0, SVI 2022, ACS 2022 and the BDC "
                            "provider counts and chapter 13 group. Built by code/src/12b_analysis_ready.py; load it "
                            "with load_panel() in code/src/load.py. Counts are integers; other numbers are written "
                            "to 10 significant digits.",
             "schema": schema(ANALYSIS_READY_FIELDS, ["storm_key", "doc_id", "fips"])},
            {"name": "panel_analysis_ready_parquet", "path": "data/analysis/panel_analysis_ready.parquet",
             "profile": "tabular-data-resource", "format": "parquet", "mediatype": "application/vnd.apache.parquet",
             "title": "Analysis-ready panel (Parquet)",
             "description": "The same table as panel_analysis_ready.csv, with its types (UTC datetimes, nullable "
                            "integers) and full float precision.",
             "schema": schema(ANALYSIS_READY_FIELDS, ["storm_key", "doc_id", "fips"])},
            {"name": "bdc_county_provider_counts", "path": "data/input/bdc/bdc_county_provider_counts.csv",
             "profile": "tabular-data-resource", "format": "csv", "mediatype": "text/csv", "encoding": "utf-8",
             "title": "Broadband provider counts by county and BDC release (counts only)",
             "description": "Derived from FCC Broadband Data Collection public data; no provider is named or identified.",
             "schema": schema(BDC_FIELDS, ["release", "fips"])},
            {"name": "results", "path": "data/analysis/results.json", "format": "json", "mediatype": "application/json",
             "title": "Every number on the page",
             "description": "Chapter results with intervals, n and method, written by code/src/10_analysis.py "
                            "(chapters 1-9) and 12_v2_analysis.py (chapters 10-14); floats to 10 significant "
                            "digits."},
            {"name": "analysis_plan_as_committed", "path": f"docs/{plan['file']}", "format": "md",
             "mediatype": "text/markdown", "title": "Analysis plan as committed",
             "description": f"Committed {plan['committed']} (commit {plan['commit']}); SHA-256 {plan['sha256']}.",
             "hash": f"sha256:{plan['sha256']}"},
        ],
    }
    for r in pkg["resources"]:
        if r["format"] == "parquet":  # frictionless reads Parquet through pyarrow and cannot check bytes or hash
            r["description"] += f" SHA-256 {sha256(T / r['path'])}; {(T / r['path']).stat().st_size} bytes."
            continue
        if "hash" not in r:
            r["hash"] = "sha256:" + sha256(T / r["path"])
        r["bytes"] = (T / r["path"]).stat().st_size
    write(T / "datapackage.json", json.dumps(pkg, indent=2, ensure_ascii=False) + "\n")
    return pkg


def codebook_md(T: Path, pkg: dict) -> None:
    L = ["# Codebook", "", "Generated from `datapackage.json` by `code/src/14_data_repo.py`; edit the package, not this "
         "file. Missing values are empty cells. Every variable's limitation is in the last column.", ""]
    for r in pkg["resources"]:
        if "schema" not in r:
            continue
        s = r["schema"]
        L += [f"## `{r['path']}`", "", r["description"], "",
              f"Primary key: {', '.join('`' + k + '`' for k in s['primaryKey'])}. Missing value code: empty cell.", "",
              "| Variable | Type | Unit | Description | Limitations |", "|---|---|---|---|---|"]
        for f in s["fields"]:
            L.append(f"| `{f['name']}` | {f['type']} | {f.get('unit', '')} | {f['description']} | "
                     f"{f.get('limitations', '')} |")
        L.append("")
    L += ["## Cleaning levels (`clean_rows`)", "",
          "`clean_rows(panel, level)` in `code/src/load.py` (since 3.1.0) drops rows of the analysis-ready panel at one "
          "of two levels; it never changes a value. The main analysis uses every row except as noted; the flags behind "
          "each report's status are in `data/analysis/validation/validation_dirs.csv`.", "",
          "| Level | Drops | Why |", "|---|---|---|"]
    L += [f"| `{k}` | {v['drops']} | {v['why']} |" for k, v in load.CLEAN_LEVELS.items()]
    L += [""]
    L += ["## `data/analysis/results.json`", "",
          "Nested JSON, one key per chapter (`chapter_1` to `chapter_9`, then `v2_1_public_record_misses`, "
          "`v2_2_backup_power`, `v2_3_power_cell_timing`, `v2_5_groups`, `v2_5_network_redundancy`, `v2_1_1_report_card`). Each number is "
          "stored with its interval (`ci_low`, `ci_high`), `n`, `unit` and `method` where it has them. Floats are "
          "written to 10 significant digits (since 2.2.0). The README maps each page section and figure to its key "
          "and script.", "",
          f"Intervals: {BOOTSTRAP_NOTE}", ""]
    write(T / "CODEBOOK.md", "\n".join(L))


# ------------------------------------------------------------------------------------------- text files --
def dois() -> tuple:
    """(concept DOI, the latest archived version's DOI), from step 11, where each was checked on its Zenodo record."""
    s11 = importlib.import_module("11_build_page")
    return s11.CONCEPT_DOI, s11.VERSION_DOI


def version_dois() -> dict:
    """{version: DOI} for every archived version (step 11's record; a new version has none until it is released)."""
    return dict(importlib.import_module("11_build_page").VERSION_DOIS)


def citation_cff(T: Path) -> None:
    concept, _ = dois()
    ids = "".join(f'''  - type: doi
    value: "{doi}"
    description: "Version {ver}"
''' for ver, doi in version_dois().items())
    write(T / "CITATION.cff", f"""cff-version: 1.2.0
message: "If you use these data or code, please cite them as below. Use the concept DOI for the work in general and the version DOI for specific numbers."
type: dataset
title: "{TITLE}"
version: {VERSION}
date-released: {RELEASE_DATE}
doi: "{concept}"
identifiers:
  - type: doi
    value: "{concept}"
    description: "Concept DOI: all versions (resolves to the latest)"
{ids}license: CC-BY-4.0
authors:
  - family-names: "{AUTHOR['family']}"
    given-names: "{AUTHOR['given']}"
    orcid: "https://orcid.org/{AUTHOR['orcid']}"
url: "{PAGE_URL}"
repository-code: "https://github.com/ts2427/{REPO_NAME}"
keywords:
  - hurricanes
  - cell sites
  - telecommunications outages
  - FCC DIRS
  - disaster resilience
abstract: >-
  A county-by-report panel of FCC Disaster Information Reporting System (DIRS) cell-site outages for {N_STORMS} Atlantic
  storms in ten Gulf and Southeast states, 2017-2026, checked against each report's printed totals, with the public
  inputs and the code that rebuild the panel and every number on the page "When the Network Goes Dark".
  Data are CC BY 4.0; code is MIT.
""")


def changelog(T: Path) -> None:
    ext = importlib.import_module("15_external_validation")
    ev = ext.summary(pd.read_csv(ext.OUT_CSV, dtype=str, keep_default_na=False))
    unreleased = (f"""## [Unreleased]

### Added
- The version {VERSION} DOI ({version_dois()[VERSION]}) in `CITATION.cff` and the README, added after the release.
  Documentation only.

""" if VERSION in version_dois() else "")
    write(T / "CHANGELOG.md", f"""# Changelog

This project follows [Semantic Versioning](https://semver.org/): a major version changes a published number or a
variable's meaning, a minor version adds data or variables, a patch fixes documentation or code without changing
any output.

{unreleased}## [{VERSION}] - {RELEASE_DATE}

Usability and maintenance. No published number changes: `dirs_county_day.csv`, `storms.csv`, the validation tables
and `results.json` are as in 3.0.0 (the reproduction test compares them), and the analysis-ready panel differs only by
its new column.

### Added
- External validation against the FCC's own summary, the 2017 Atlantic Hurricane Season Impact on Communications
  report (DOC-353805A1, August 2018; now in `data/input/rules/`). Every county or state figure it gives for Harvey and
  Irma ({ev["n"]}) is transcribed with its page in `code/manifest/external_fcc_2017_report.csv` and compared with the
  matching report by the new step `code/src/15_external_validation.py`: {ev["match"]} match, {ev["match after truncation"]}
  match once the FCC's dropped decimals are allowed for, {ev["consistent"]} is consistent with a figure given in words,
  {ev["differs"]} differ and {ev["no panel field"]} cannot be compared (switching centers, PSAPs, broadcast stations,
  providers' filings). Every difference is explained or marked as not explained, and none points to an error in the
  panel. Table: `data/analysis/validation/external_validation_fcc_2017.csv` and `docs/external_validation.md`; summary
  in the README and the page's methods. No data were changed because of it.
- `days_since_day0` in the analysis-ready panel: the documented name for `days_since_landfall` (same values), since
  day 0 is not always a landfall. `days_since_landfall` stays as a deprecated alias until 4.0.0.
- `clean_rows(panel, level="standard" | "strict")` in `code/src/load.py`, documented in `CODEBOOK.md` (Cleaning
  levels): which rows each level drops and why.
- `examples/quickstart.ipynb`: loads the panel and rebuilds two headline figures, the recovery curves with the
  median time to 50% restored (chapter 4) and the pooled cause shares (chapter 5), checking each against
  `results.json`. CI runs it with nbmake.
- `CONTRIBUTING.md`; a "Report a data error" issue form (`.github/ISSUE_TEMPLATE/data_error.yml`: storm, report DOC,
  county, what is wrong, evidence); `ERRATA.md`, generated from the CORRECTION entries of `docs/decisions.md`.
- CI: a monthly scheduled run (the 1st of each month), a ruff lint step (`ruff.toml`: pyflakes and the pycodestyle
  error and warning rules) and the notebook check. Dependabot (`.github/dependabot.yml`) proposes updates to the
  Actions and the Python packages weekly.
- `docs/restructure_plan.md`: the package layout planned for 4.0.0. No file is split or moved in this release.

### Changed
- `load_panel()` parses `report_date` and `dirs_activation_date` as dates (pandas datetime64, no time zone), from
  the CSV and the Parquet alike; they were text. Comparisons with "YYYY-MM-DD" strings still work; string methods on
  those two columns no longer do.
- Every GitHub Action is pinned to a commit SHA (checkout v4.4.0, setup-python v5.6.0, upload-artifact v4.6.2).
- `requirements.txt` adds matplotlib (already a dependency), nbmake, ipykernel and ruff; `requirements.lock` is
  regenerated, and no version already pinned changes.
- Lint fixes, with no change in behavior: unused imports and variables removed, a constant moved below the imports,
  a lambda given a name, one ambiguous variable renamed, f-strings without placeholders made plain strings.
- The version 3.0.0 DOI ({version_dois().get("3.0.0", "")}) in `CITATION.cff` and the README (added after its
  release).

### Note on the 3.0.0 archive
- The 3.0.0 archive on Zenodo ({version_dois().get("3.0.0", "")}) holds a decision log (`docs/decisions.md`) that
  predates two wording fixes made on main after the release: the display-rounding correction entry now names only
  Nicholas's site-days lost (114 to 115), and the word "correction" in a notes entry is in lower case, so that entry is
  no longer listed among the page's corrections. Main also adds a log entry for the 3.0.0 release itself. No number
  differs. This release's archive carries the fixed log.

## [3.0.0] - 2026-11-24

A major version, as this file's rule requires, because published numbers change. Two parts: corrections to how
the FCC's reports and notices were read, which change published numbers, and engineering hardening, which changes
no finding.

### Correction: Harvey Sep 4-5, 2017 table layout

The Harvey correction, and the corrections that followed from rechecking every report and notice after it: two
restored reports (Harvey Sep 3 and Nate, 2017), the reporting areas read from the FCC's notices (several storms),
and one county name.

- The FCC's Harvey reports for Sep 3, 4 and 5, 2017 print the previous day's sites out and % out before today's. The
  parser had read the previous day as the report's own figures, and put today's count and % into the damage and
  transport columns. It now detects the two-day header and reads today's columns. Tests from the reports' own text:
  `code/tests/test_two_day_layout.py`.
- Two parser misses had kept four Harvey reports' totals from being read, so they were never reconciled: Sep 3-5
  print "Total" rather than "TOTAL", and in Aug 28 the page-footer pattern took "TOT" from the TOTAL line after it
  (any three capitals counted as a time zone). Both are fixed. A sweep of every report, in its text and its PDF,
  finds no other total line left unread; against the 2.1.0 parser only these four Harvey reports change. No report
  is flagged `no_printed_totals` any more (three reports in use had been, all through these misses).
- Two new checks stop the build, for every report: a count that is not a whole number, and a previous-day column
  that differs from the previous day's report for the same county. Only Harvey Sep 3-5 print a previous-day column,
  and every one matches.
- With their totals read, Sep 4 and Sep 5 print a Texas total of 4,200 sites served over county rows that add up to
  4,199 (the same rows as Sep 3, which prints 4,199). Recorded as checked FCC inconsistencies
  (`code/manifest/known_fcc_inconsistencies.csv`, kind `state_total`; the rows' sum is used, the printed value kept);
  the reports' status is `known_fcc_inconsistency`, which outranks a flag.
- Restored after the parser fix: Harvey Sep 3, 2017, whose Matagorda and San Patricio rows are broken in both its
  text and its PDF, is kept because a new rule counts a row as confirmed (and flags it) when the next report's
  previous-day column reprints it exactly, as Sep 4 does for all 13 of Sep 3's counties. Nate, Oct 9, 2017, which
  prints no headline %, is kept because a missing headline is now a flag (`headline_missing`), not an exclusion,
  where the rows are confirmed and the printed totals reconcile. Nate joins the peak tables; with one report it is
  left out of the recovery summaries, as Nicole is. Its BDC release (the earliest, as for every storm before 2022)
  is added to `storm_releases.json` from the saved release list, with no new download.
- Notice areas: the reader of the FCC's DIRS notices had glued text onto some county names ("Wharton Note that
  ...", "York Washington D.C: ...", "Baton Rouge (East)", footnote digits, a sentence read as a name, two names with
  no comma), so those counties counted as outside the storm's reporting area. Fixed, with tests from the real
  notices (`code/tests/test_notices.py`) and one checked correction (`code/manifest/notice_name_corrections.csv`).
  Every notice county name in the study states now matches a Census county (ignoring spacing and punctuation) or a
  listed FCC misspelling. Reports
  with counties outside the notice area go from 16 to 9; validation from 134 flagged and 36 ok to 126 and 44. No
  headline result changes.
- County names: a name broken across lines in Harvey Sep 3's table ("MATAGORD A") takes the spelling of the
  report's own county list ("MATAGORDA"). A build check requires every county name in the panel to match its
  report's list, a checked spelling variant (`code/manifest/county_spelling_variants.csv`: three misspellings in
  the FCC's lists) or, for a county in the table but not the list, its Census name.
- Counts: storms {N_STORMS_210} to 22, reports in use 167 to 169, excluded reports 7 to 5.
- Numbers that change (2.1.0, then 3.0.0): the median peak share 10.3% to 9.8%; Harvey's site-days lost 1,474 to
  1,424 and its share restored by its last report 74.8% to 74.0%; the median site-days lost 2,124 to 2,099; sites
  still out in the FCC's last report 1,883 in 21 storms to 1,887 in 22 (Harvey 70 to 73); the power vs. cell order
  (cell first 158 to 159, undetermined 148 to 147); chapter 7's and chapter 8's model estimates move slightly
  (inside 64 knots 47.9 to 48.4; SVI Q4 interval 0.90 to 1.46 becomes 0.90 to 1.45); validation counts and the
  chapter 14 report card; and figures counted over storm-counties (chapter 9's P0 row, the map's county-reports,
  chapter 7's calibration table). Every per-storm bootstrap interval is also recomputed with the stable seed below.
  The main changes are in
  `docs/decisions.md` (2026-11-24) and on the page's Corrections list; `data/analysis/results.json` holds every
  value. No finding's wording changes.
- A displayed number that is an exact half now rounds up, as the page's rule states (it had been stored just below
  the half): Nicholas's site-days lost 114 to 115. (Harvey's site-days lost is now 1,424 after the correction, and
  Irma's peak interval is recomputed with the stable seed.)

### Engineering hardening (no change to findings)
- Each storm's bootstrap seed is a stable hash of the global seed, the analysis stream and the storm key, not its
  position in date order, so adding or removing a storm never changes another storm's numbers
  (`code/tests/test_storm_seeds.py`). This recomputes every per-storm interval once (chapters 3 to 6); no estimate
  changes.
- `results.json`: every float is written to 10 significant digits, so last-bit differences between platforms' math
  libraries do not show. Apart from the correction above, every number is within a relative 1e-9 of 2.1.0. The
  reproduction test and the version 1 results test compare numbers with a relative tolerance of 1e-8 (with an
  absolute floor of 1e-12 for values that are zero up to floating-point noise) and text exactly (the version 1
  test's SHA-256 fingerprints are replaced by a snapshot of the values, `code/tests/snapshots/v1_results.json`). The panel, storm and validation CSVs are still compared byte for byte.
- Counts are written as integers (42, not 42.0) in `dirs_county_day.csv` (sites_served, sites_out, the three cause
  columns, on_backup_power, out_unattributed, out_overattributed), `storms.csv` (n_reports, n_counties) and
  `validation/validation_dirs.csv` (sites_unattributed, sites_overattributed); `datapackage.json` types them as
  integers. `out_overattributed` no longer has -0.0 values (they are 0); the codebook note about -0.0 is removed.
- `datapackage.json` validates with frictionless (0 errors): `created` is a full ISO 8601 date-time and the profile
  is `data-package` (results.json, the Parquet file and the plan file are not tables). Checked as a build step and by
  `code/tests/test_datapackage.py`; `frictionless` added to `requirements.txt`.
- New: `data/analysis/panel_analysis_ready.csv` and `.parquet`, the county-report panel (same rows and order as
  `dirs_county_day.csv`) joined with every covariate the analysis uses (EAGLE-I values and coverage flags, exposure,
  wind zone, day 0, SVI, ACS, and the BDC release, provider counts and chapter 13 group). Written by the new step
  `code/src/12b_analysis_ready.py`; documented in `datapackage.json` and `CODEBOOK.md`; loaded with `load_panel()` in
  the new `code/src/load.py`.
- New: continuous integration (`.github/workflows/ci.yml`): on every push, on ubuntu-latest and windows-latest with
  Python 3.13, install the locked environment, run the tests, validate `datapackage.json`, run `run_all.py`, then run
  the reproduction tests. CI badge in the README.
- New: `requirements.lock`, every package including dependencies pinned with SHA-256 hashes (uv pip compile,
  universal), alongside `requirements.txt`.
- Every test that needs `build/` skips with a reason ("run python run_all.py first") on a fresh clone; two tests that
  looked for build outputs in the wrong folder (and so always skipped here) now find them.
- Warnings: NumPy's 'generic' timedelta deprecation (steps 6 and 8) is fixed, and the expected 'invalid value
  encountered in subtract' from bootstrap draws that never reach a threshold (inf - inf inside NumPy's percentile
  interpolation; the bound is reported as none, as before) is no longer printed.
- A methods note wherever intervals appear (README, `CODEBOOK.md`, and the page's captions, How to read it and
  methods): the county bootstrap treats counties within a storm as independent, so those intervals may be somewhat
  narrow. A note on the method, not a change to any result.
- `storms.csv` is written by step 9; `run_all.py` no longer writes it separately.
- Documentation: `CODEBOOK.md` names the interval fields `ci_low` and `ci_high` (it said `lo` and `hi`); the 2.1.0
  entry below gives version 2.0.0's DOI (it had given 2.1.0's); the version 2.1.0 DOI
  ({version_dois().get("2.1.0", "")}) is in `CITATION.cff` and the README.

## [2.1.0] - 2026-11-23

### Added
- Chapter 14, "How complete are the FCC's public reports?" (exploratory: a descriptive summary of the existing
  validation results; addendum entry V2.1-1, committed before it was computed). For each storm and each year:
  reports with cause columns, causes short of or above sites out, headline mismatches, missing state totals, counties
  in the table but not the county list, counties outside the notice area, the backup-power column, and excluded
  reports, each with its denominator, plus a one-line summary per year. New key `v2_1_1_report_card` in
  `results.json`, written by `code/src/12_v2_analysis.py report_card` from the validation outputs; no new data.
- The Zenodo DOIs (concept {dois()[0]}; version 2.0.0: {version_dois()["2.0.0"]}) in `CITATION.cff` and the README, with a DOI
  badge and a How to cite section.
- `docs/update_procedure.md`: how a new season and a new version are added and released.

### Changed
- `code/src/11_build_page.py` (the page builder, not run by `run_all.py`): chapter 14; the page's How to cite box,
  Dataset metadata and Reproduce it links; the site's old code folder is replaced by a pointer to this repository.

### Unchanged
- Every input, the panel, the storm table, the validation tables, and every other key of `results.json`.

## [2.0.0] - 2026-11-23

First release of this repository. The analysis is version 2 of the page.

### Added
- Version 2 analyses (chapters 10-13): sites still out in the FCC's last report, sites on backup power, power vs. cell
  timing, network redundancy from FCC Broadband Data Collection provider counts; the county lookup and the map.
- Inputs with provenance (`data/input/INPUTS.csv`), `datapackage.json`, `CODEBOOK.md`, `SOURCES.md`,
  `DEVIATIONS.md`, `CITATION.cff`, and `run_all.py`, which rebuilds the panel and `results.json` from `data/input`.
- The analysis plan as committed, with its SHA-256.

### Unchanged
- Every version 1 result (chapters 1-9); a test fails if one changes.

## [1.0.0] - 2026-11-22

Version 1 of the page (chapters 1-9) and the panel, published with the page's code snapshot.
""")


def licenses(T: Path) -> None:
    write(T / "LICENSE", """MIT License

Copyright (c) 2026 Timothy D. Spivey

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
""")
    write(T / "LICENSE-DATA.md", """# Data license

The author's data in this repository (everything in `data/analysis/`, the derived files in `data/input/` marked
"derived" or "modified" in `data/input/INPUTS.csv`, `datapackage.json` and `CODEBOOK.md`) are licensed under the
Creative Commons Attribution 4.0 International license (CC BY 4.0):
https://creativecommons.org/licenses/by/4.0/ (legal code: https://creativecommons.org/licenses/by/4.0/legalcode).

Attribute: Timothy D. Spivey, "When the Network Goes Dark" data, version """ + VERSION + """ (2026). See `CITATION.cff`.

The third-party inputs in `data/input/` keep their own terms, listed with the exact attribution for each in
`SOURCES.md`. U.S. federal government works (FCC, Census, NOAA/NHC, CDC/ATSDR, FEMA) are in the public domain in the
United States; EAGLE-I files are CC BY 4.0 from ORNL/DOE.

The code (`code/`, `run_all.py`) is under the MIT License in `LICENSE`.

---

The full legal code follows, unmodified, as published by Creative Commons at
https://creativecommons.org/licenses/by/4.0/legalcode.txt (retrieved 2026-11-23; SHA-256 in
`code/manifest/downloads.csv`).

```text
""" + (RAW / "licenses" / "cc-by-4.0-legalcode.txt").read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n")
          + "\n```\n")


def ai_statement(T: Path) -> None:
    write(T / "AI_ASSISTANCE.md", """# AI assistance

The code and documentation in this repository were written with the help of an AI coding assistant (Claude Code,
by Anthropic) working under the author's direction. The author set the questions, the ground rules and the analysis
plan, and made every analytical decision; who proposed and who chose each one is recorded in `docs/decisions.md`.
Every number in `data/analysis/` is generated by the code here from the public inputs in `data/input/`, and
`tests/test_reproduction.py` checks that the code reproduces the published files. The assistant had no access to
any non-public data.
""")


def sources_md(T: Path, idx: pd.DataFrame) -> None:
    def when(prefix):
        w = idx[idx.path.str.startswith(prefix) & (idx.retrieved_utc != "")].retrieved_utc
        if not len(w):
            return ""
        return (f"{w.min()[:10]}" + ("" if w.min()[:10] == w.max()[:10] else f" to {w.max()[:10]}")
                + f" (UTC; first file {w.min()[11:16]} UTC)")

    def span(prefix):
        w = idx[idx.path.str.startswith(prefix) & (idx.retrieved_utc != "")].retrieved_utc.sort_values()
        return f"{w.iloc[0]} to {w.iloc[-1]}" if len(w) else ""

    dirs = idx[idx.path.str.startswith("data/input/dirs/")]
    n_docs = dirs.doc_id.nunique()
    nhc = idx.set_index("path").loc["data/input/nhc/hurdat2-1851-2025-092326.txt"]
    eag = ", ".join(EAGLEI_FILES)
    text = f"""# Sources and attribution

Every input file, with its URL, retrieval time (UTC) and SHA-256, is listed in `data/input/INPUTS.csv`. Downloads
followed one rule: approved sources only, one request at a time at least 3 seconds apart, a generic User-Agent, and
no retry after a refusal.

## FCC Disaster Information Reporting System (DIRS)

Federal Communications Commission, Public Safety and Homeland Security Bureau. *Communications Status Report for
Areas Impacted by* [storm], {n_docs} reports, 2017-2026, each cited by its EDOCS DOC number and date in
`data/input/INPUTS.csv` and `code/manifest/dirs_reports.csv` (https://docs.fcc.gov/public/attachments/DOC-<number>.pdf
and .txt). Retrieved {when('data/input/dirs/')}. U.S. government work; public domain in the United States.
The FCC's DIRS notices (activation, area changes, deactivation) are in `data/input/notices/`.

Each report carries this caveat: "The number of cell site outages in a specific area does not necessarily correspond
to the availability of wireless service to consumers in that area."

Rules cited for dates: FCC 22-50 (Mandatory Disaster Response Initiative, adopted June 27, 2022;
`data/input/rules/FCC-22-50A1_Rcd.pdf`), compliance from May 1, 2024 per the FCC's MDRI page
(https://www.fcc.gov/node/254876, accessed November 23, 2026; the formal compliance notice was not retrieved);
FCC 24-5 and DA 25-74 (mandatory DIRS from February 20, 2025; Federal Register 2025-00495); FCC 26-34 (adopted
May 20, 2026; Federal Register 2026-13155, 91 FR 39516, June 30, 2026; `data/input/rules/FCC-26-34A1.txt`).

## FCC Broadband Data Collection (counts only)

FCC Broadband Data Collection public data (National Broadband Map, https://broadbandmap.fcc.gov/data-download) were
obtained through the FCC's Public Data API under the FCC API terms of service accepted for the account, and are used
for provider counts only; no provider is named and the files are not redistributed. What is published here is
`data/input/bdc/bdc_county_provider_counts.csv` (counts by county and release, derived by `code/src/06e_bdc_counties.py`
and `06f_bdc_counts.py`) and the list of files used (`provider_summary_files.csv`, `storm_releases.json`).

## ORNL/DOE EAGLE-I

Brelsford, C., et al. (2024). A dataset of recorded electricity outages by United States county 2014-2022.
*Scientific Data*, 11, 271. https://doi.org/10.1038/s41597-024-03095-5.
Data: figshare, https://doi.org/10.6084/m9.figshare.24237376 (version 4, published 2026-02-25), files
eaglei_outages_2017.csv to eaglei_outages_2024.csv, {eag}; licence CC BY 4.0, read from the figshare record of
version 4 on 2026-11-22 (the record that holds these file IDs; `code/manifest/eaglei_files.csv`). The 2025 release
(https://doi.org/10.13139/ORNLNCCS/3012826) was not used.
Modified: aggregated to county at report times. `data/input/eaglei/eaglei_extract.parquet` keeps only the study
counties and storm windows; `MCC.csv` and `coverage_history.csv` are unmodified. The year files are not
redistributed. Retrieved {when('data/input/eaglei/')}.

## CDC/ATSDR Social Vulnerability Index

Centers for Disease Control and Prevention/ Agency for Toxic Substances and Disease Registry/ Geospatial Research,
Analysis, and Services Program. CDC/ATSDR Social Vulnerability Index 2022 Database United States.
https://www.atsdr.cdc.gov/placeandhealth/svi/data_documentation_download.html Accessed on {when('data/input/svi/')}.

## OpenFEMA

This product uses the Federal Emergency Management Agency's OpenFEMA API, but is not endorsed by FEMA. The Federal
Government or FEMA cannot vouch for the data or analyses derived from these data after the data have been retrieved
from the Agency's website(s).
Dataset: Disaster Declarations Summaries v2, https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries, accessed
{span('data/input/fema/')} (UTC). Used as context only (`fema_declared`); no result uses it.

## NOAA National Hurricane Center

Landsea, C. W., & Franklin, J. L. (2013). Atlantic hurricane database uncertainty and presentation of a new database
format. *Monthly Weather Review*, 141(10), 3576-3592. https://doi.org/10.1175/MWR-D-12-00254.1.
File: HURDAT2 Atlantic, `hurdat2-1851-2025-092326.txt` (1851-2025, NHC file version dated 2026-09-23 in its name),
{nhc.url}, retrieved {nhc.retrieved_utc[:10]}. Isaias 2026 (AL092026) best track from the NHC GIS archive,
`al092026_best_track.zip`. U.S. government work; public domain.

## U.S. Census Bureau

This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau.
American Community Survey 5-year estimates, 2018-2022 (households, population 65 and over, broadband subscription),
county level, from api.census.gov (the key is not stored; the logged URL has it redacted). 2020 county list
(`national_county2020.txt`), 2020 Gazetteer counties and the 2022 cartographic boundary file (1:500,000) from
www2.census.gov. Retrieved {when('data/input/census/')}.

## Software on the page

D3 7.9.0 and topojson-client 3.1.0 (ISC License), used by the page's map; not part of this repository.

## Related work cited on the page

Olukola et al. (2026), arXiv:2609.10944, is used on the page only as a check on Helene; its dataset is not
redistributed here.
"""
    write(T / "SOURCES.md", text)


# ---------------------------------------------------------------------------------------------- README --
PAGE_MAP = [  # page section, figures (figure id: published CSV), results.json key, script
    ("Opening, How to read it", "", "chapter_3, chapter_4, v2_1_public_record_misses", "10_analysis.py, 12_v2_analysis.py"),
    ("Map: where cell sites were out", "storm map (hurricane-map.json)", "panel (dirs_county_day.csv)",
     "09_build_panel.py; map data written by 11_build_page.py"),
    ("1. The question and the data", "fig-coverage: hurricane-coverage-heatmap.csv", "chapter_1", "10_analysis.py"),
    ("2. Anatomy of a storm: Isaias", "fig-isaias-map: hurricane-isaias-map.csv; fig-isaias: hurricane-isaias-counties.csv",
     "chapter_2", "10_analysis.py (track: 07_nhc.py)"),
    ("3. How much goes dark", "fig-peaks: hurricane-peaks.csv", "chapter_3", "10_analysis.py"),
    ("4. How fast it comes back", "fig-curves: hurricane-recovery-curves.csv; fig-restored: hurricane-restored.csv",
     "chapter_4", "10_analysis.py"),
    ("5. Why sites go dark", "fig-causes: hurricane-causes.csv", "chapter_5", "10_analysis.py"),
    ("6. The power coupling", "fig-power-overlay: hurricane-power-overlay.csv; fig-power: hurricane-power-lags.csv",
     "chapter_6", "10_analysis.py (EAGLE-I match: 06_eaglei.py)"),
    ("7. Exposure", "fig-zone: hurricane-wind-zone.csv; fig-distance: hurricane-distance.csv; "
     "fig-calibration (methods): hurricane-calibration.csv", "chapter_7", "10_analysis.py (exposure: 07_nhc.py)"),
    ("8. Who waits longest", "fig-svi: hurricane-svi-wait.csv", "chapter_8", "10_analysis.py (SVI: 08_fema_svi_bdc.py)"),
    ("9. Did the rules help?", "", "chapter_9", "10_analysis.py"),
    ("10. What the public record misses", "", "v2_1_public_record_misses", "12_v2_analysis.py v2_1"),
    ("11. Sites on backup power", "", "v2_2_backup_power", "12_v2_analysis.py v2_2"),
    ("12. Which comes back first: power or cell service?", "", "v2_3_power_cell_timing", "12_v2_analysis.py v2_3"),
    ("13. Do counties with more mobile providers recover differently?", "",
     "v2_5_groups, v2_5_network_redundancy", "12_v2_analysis.py v2_5_groups v2_5 (counts: 06e, 06f)"),
    ("14. How complete are the FCC's public reports?", "", "v2_1_1_report_card",
     "12_v2_analysis.py report_card (from the validation outputs)"),
    ("Look up a county", "county lookup (hurricane-county-lookup.json)", "panel", "11_build_page.py"),
    ("Methods, data and licenses", "validation tables", "chapter_1, validation/*.csv", "04_validate_dirs.py, 10_analysis.py"),
]
RUN_ORDER = [
    ("02b_reporting_areas.py", "", "each storm's reporting area from the FCC notices (rewrites code/manifest tables; "
                                   "the test checks they are unchanged)"),
    ("03_parse_dirs.py", "", "parse every DIRS report (text first, PDF fallback) into county rows and totals"),
    ("04_validate_dirs.py", "", "reconcile county rows with each report's printed totals; validation tables"),
    ("05_fips.py", "", "county names to FIPS"),
    ("06_eaglei.py", "", "match EAGLE-I (from the published extract) to each report's as-of time"),
    ("07_nhc.py", "", "tracks, wind radii, distance to track, day 0"),
    ("08_fema_svi_bdc.py", "", "ACS, SVI and OpenFEMA declarations (from the stored files; no request is made)"),
    ("09_build_panel.py", "", "the panel, the storm table and dirs_county_day.csv"),
    ("10_analysis.py", "3 4 5 6 7 8 9", "chapters 3-9 to results.json"),
    ("10_analysis.py", "1 2", "chapters 1 and 2 (run second so results.json keeps the published key order)"),
    ("12_v2_analysis.py", "v2_1 v2_2 v2_3 v2_5_groups v2_5 report_card", "chapters 10-14 to results.json"),
    ("12b_analysis_ready.py", "", "the analysis-ready panel (CSV and Parquet): the panel with every covariate"),
    ("15_external_validation.py", "", "external check against the FCC's 2017 season report (Harvey and Irma figures)"),
]


def external_validation_section() -> list:
    ext = importlib.import_module("15_external_validation")
    t = pd.read_csv(ext.OUT_CSV, dtype=str, keep_default_na=False)
    ev = ext.summary(t)
    L = ["## External validation", "",
         f"The FCC's own summary of the season, *2017 Atlantic Hurricane Season Impact on Communications* "
         f"(DOC-353805A1, August 2018), gives {ev['n']} county or state figures for Harvey and Irma. Each is "
         f"transcribed with its page (`code/manifest/external_fcc_2017_report.csv`) and compared with the matching "
         f"report by `code/src/15_external_validation.py`: {ev['match']} match, {ev['match after truncation']} match "
         f"once the FCC's dropped decimals are allowed for, {ev['consistent']} is consistent with a figure given in "
         f"words, {ev['differs']} differ and {ev['no panel field']} cannot be compared (switching centers, PSAPs, "
         "broadcast stations, providers' filings). In each difference the season report departs from what the DIRS "
         "report prints or from the total its rows reconcile to, so none points to an error in the panel, and no data "
         "were changed because of the check. Every figure: `docs/external_validation.md` and "
         "`data/analysis/validation/external_validation_fcc_2017.csv`. The differences:", "",
         "| # | FCC figure | Report | FCC | Ours | Explanation |", "|---|---|---|---|---|---|"]
    for r in t[t.status == "differs"].itertuples():
        L.append(f"| {r.id} | {r.where}: {r.fcc_text} | {r.report_date or 'all'} | {r.fcc_value} | {r.ours} | "
                 f"{r.explanation} |")
    return L + [""]


def readme(T: Path, idx: pd.DataFrame, plan: dict) -> None:
    def size(prefix):
        b = idx[idx.path.str.startswith(prefix)].bytes.sum()
        return f"{b / 1e6:,.1f} MB"

    avail = [
        ("FCC DIRS reports (PDF and text)", "data/input/dirs/", "FCC", "Public domain (U.S. government)", "yes",
         size("data/input/dirs/")),
        ("FCC DIRS notices", "data/input/notices/", "FCC", "Public domain", "yes", size("data/input/notices/")),
        ("FCC orders cited for dates", "data/input/rules/", "FCC", "Public domain", "yes", size("data/input/rules/")),
        ("FCC storm-page document lists", "data/input/storm_pages/", "FCC (compiled list)", "Public domain", "yes",
         size("data/input/storm_pages/")),
        ("EAGLE-I extract, MCC, coverage", "data/input/eaglei/", "ORNL/DOE", "CC BY 4.0", "yes (extract modified)",
         size("data/input/eaglei/")),
        ("EAGLE-I year files 2017-2024", "not included (8.9 GB)", "ORNL/DOE via figshare", "CC BY 4.0",
         "no: download with code/src/06a_download_eaglei.py", "8.9 GB"),
        ("BDC provider counts", "data/input/bdc/", "FCC BDC (derived)", "CC BY 4.0 (counts)", "yes (counts only)",
         size("data/input/bdc/")),
        ("BDC provider-by-geography files", "not included", "FCC BDC", "FCC API terms", "no: provider-level files are "
         "not redistributed", ""),
        ("ACS 5-year 2022", "data/input/acs/", "Census Data API", "Public domain; API notice in SOURCES.md", "yes",
         size("data/input/acs/")),
        ("County lists, gazetteer, boundaries", "data/input/census/", "Census", "Public domain", "yes",
         size("data/input/census/")),
        ("SVI 2022", "data/input/svi/", "CDC/ATSDR", "Public domain; credit line in SOURCES.md", "yes",
         size("data/input/svi/")),
        ("OpenFEMA declarations", "data/input/fema/", "FEMA", "Public domain; disclaimer in SOURCES.md", "yes",
         size("data/input/fema/")),
        ("NHC HURDAT2 and Isaias best track", "data/input/nhc/", "NOAA/NHC", "Public domain", "yes",
         size("data/input/nhc/")),
    ]
    concept, version = dois()
    L = [f"# {TITLE}", "",
         f"[![DOI](https://zenodo.org/badge/DOI/{concept}.svg)](https://doi.org/{concept}) "
         f"[![CI]({GITHUB}/actions/workflows/ci.yml/badge.svg)]({GITHUB}/actions/workflows/ci.yml)", "",
         f"Version {VERSION} ({RELEASE_DATE}). Data: CC BY 4.0 (`LICENSE-DATA.md`). Code: MIT (`LICENSE`).", "",
         f"The data and code behind the page *When the Network Goes Dark* ({PAGE_URL}): a county-by-report panel of "
         f"FCC DIRS cell-site outages for {N_STORMS} storms in ten Gulf and Southeast states, 2017-2026, each report checked "
         "against its printed totals, joined to power outages (EAGLE-I), storm tracks (NHC), social vulnerability "
         "(CDC/ATSDR SVI) and broadband provider counts (FCC BDC). Every number on the page is in "
         "`data/analysis/results.json`, and `run_all.py` rebuilds it and the panel from `data/input/`.", "",
         "Associations, not causes. A site out is a site out: the FCC's counts describe the network, not how many "
         "people lost service.", "",
         "## Which licence covers what", "",
         "| Part | Licence |", "|---|---|",
         "| `data/analysis/`, derived files in `data/input/` (marked in `INPUTS.csv`), `datapackage.json`, "
         "`CODEBOOK.md` | CC BY 4.0 |",
         "| `code/`, `run_all.py` | MIT |",
         "| Third-party inputs in `data/input/` | their own terms; see `SOURCES.md` |", "",
         "## Contents", "", "```",
         "data/input/      every input, with INPUTS.csv (source, URL, retrieval time, SHA-256)",
         "data/analysis/   dirs_county_day.csv (the panel), storms.csv, results.json, validation/,",
         "                 panel_analysis_ready.csv and .parquet (the panel with every covariate the analysis uses)",
         "code/src/        numbered pipeline steps, load.py (load_panel(), clean_rows()); code/manifest/",
         "                 hand-made tables; code/tests/",
         "examples/        quickstart.ipynb: load the panel and rebuild two headline figures",
         ".github/         CI (lint, tests, the notebook and a full rebuild on Linux and Windows, on every push",
         "                 and monthly), Dependabot, the 'Report a data error' issue form",
         "docs/            analysis plan (as committed, with SHA-256), addendum, decision log, sources notes,",
         "                 update_procedure.md (how a new season and a new version are added and released),",
         "                 external_validation.md (the check against the FCC's 2017 season report),",
         "                 restructure_plan.md (the layout planned for 4.0.0)",
         "ERRATA.md        every correction, from the decision log; CONTRIBUTING.md: how to report an error",
         "run_all.py       one command: rebuild the panel and results.json into build/",
         "```", "",
         "## Analysis-ready panel", "",
         "`data/analysis/panel_analysis_ready.parquet` (and `.csv`) is `dirs_county_day.csv`, same rows and order, "
         "joined with every covariate the analysis uses: EAGLE-I power outages at each report's as-of time with its "
         "match and coverage flags, distance to the track, wind radii and chapter 7's wind zone, day 0 and days since "
         "day 0, SVI 2022, ACS 2022, and the storm's BDC release with its provider counts and chapter 13 group. "
         "Variables: `CODEBOOK.md`. To load it with its types:", "",
         "```python", "import sys", "sys.path.insert(0, \"code/src\")", "from load import load_panel",
         "from load import clean_rows",
         "p = load_panel()   # the Parquet if present, else the CSV, with the same types",
         "q = clean_rows(p, \"standard\")   # or \"strict\"", "```", "",
         "`report_date` and `dirs_activation_date` load as dates (since 3.1.0). `days_since_day0` is the days from the "
         "storm's day 0 to the report's as-of time; `days_since_landfall` is the same column under its old name, kept "
         "as a deprecated alias until 4.0.0. `clean_rows` drops rows at one of two levels and never changes a value:", "",
         "| Level | Drops | Why |", "|---|---|---|",
         *[f"| `{k}` | {v['drops']} | {v['why']} |" for k, v in load.CLEAN_LEVELS.items()], "",
         "`examples/quickstart.ipynb` loads the panel, rebuilds the recovery curves (with the median time to 50% "
         "restored) and the pooled cause shares with plain pandas, and checks both against `results.json`; CI runs it "
         "(`python -m pytest --nbmake examples/quickstart.ipynb`).", "",
         *external_validation_section(),
         "## Analysis plan", "",
         f"The analysis plan was committed on November 22, 2026, in the project's private version-controlled "
         f"repository (commit {plan['commit']}, {plan['committed']}), before any recovery outcome was computed. The "
         f"plan file as committed is `docs/{plan['file']}`, SHA-256 `{plan['sha256']}` (git blob "
         f"`{plan['git_blob']}`), so it can be checked against later changes. It is not blind to some figures, which "
         "the plan lists. Deviations are in `DEVIATIONS.md`.", "",
         "## Data availability and provenance", "",
         "| Data | Location | Provider | Terms | Included | Size |", "|---|---|---|---|---|---|"]
    L += [f"| {a} | `{b}` | {c} | {d} | {e} | {f} |" if b.startswith("data/") else f"| {a} | {b} | {c} | {d} | {e} | {f} |"
          for a, b, c, d, e, f in avail]
    L += ["", "Exact attribution for each source: `SOURCES.md`. Variables: `CODEBOOK.md` and `datapackage.json`.", "",
          "## Computational requirements", "",
          ("- Python 3.13 (tested with 3.13.2 on Windows 11). Reproduced on Windows and Linux: CI rebuilds everything "
           "and runs the reproduction tests on windows-latest and ubuntu-latest with Python 3.13 on every push "
           "(badge above)." if CI_PASSED_ON_BOTH else
           "- Python 3.13 (tested with 3.13.2) on Windows 11; the code uses no platform-specific calls. CI runs the "
           "tests and a full rebuild on windows-latest and ubuntu-latest (badge above)."),
          "- Packages: `requirements.txt` (exact versions of the packages used) and `requirements.lock` (every "
          "package, including dependencies, pinned with SHA-256 hashes for Windows, Linux and macOS; generated with "
          "`uv pip compile requirements.txt --universal --generate-hashes --python-version 3.13 -o requirements.lock`). "
          "For an exact environment: `python -m pip install --require-hashes -r requirements.lock`.",
          "- Memory: about 4 GB. Disk: about 200 MB for the repository and `build/`.",
          "- Run time: 12.4 minutes for `run_all.py`, measured on the author's Windows 11 laptop on 2026-11-23 "
          "(most of it is parsing the reports in step 3 and the bootstrap in step 10).",
          "- No network access is needed: every step reads `data/input/`. Steps 02, 06a, 06c, 06d and 06e (downloads "
          "and raw BDC reading) are included for transparency but are not run; they need the original sources and, "
          "for BDC, an FCC account.",
          "- Random numbers: fixed seed 20261122 (bootstrap, 2,000 draws).",
          f"- Intervals: {BOOTSTRAP_NOTE}",
          "- Floating point: `results.json` stores floats to 10 significant digits, and the reproduction test "
          "compares its numbers with a relative tolerance of 1e-8 and an absolute floor of 1e-12 (text exactly), because "
          "platforms' math libraries "
          "can differ in the last bits (up to about 1e-9 relative, in model fits). The panel, storm and validation CSVs must match byte "
          "for byte; the analysis-ready panel is compared value by value at the same tolerance.", "",
          "## Run order", "",
          "```", "python -m pip install -r requirements.txt   # or: --require-hashes -r requirements.lock",
          "python -m pytest code/tests        # unit tests; the build checks skip until run_all.py has run",
          "python run_all.py                   # rebuild into build/",
          "python -m pytest code/tests        # now including the reproduction test (build/ vs data/analysis/)",
          "python -m pytest --nbmake examples/quickstart.ipynb   # the quickstart notebook",
          "python -m ruff check code examples run_all.py        # lint (ruff.toml)",
          "```", "",
          "`run_all.py` runs these steps in this order (all in `code/src/`):", "",
          "| # | Script | Arguments | Does |", "|---|---|---|---|"]
    L += [f"| {i} | `{s}` | {a} | {d} |" for i, (s, a, d) in enumerate(RUN_ORDER, 1)]
    L += ["", "`code/tests/test_reproduction.py` then compares `build/` with `data/analysis/`: "
          "`dirs_county_day.csv`, `storms.csv` and the validation tables byte for byte, `results.json` with numbers "
          "within a relative 1e-8 (absolute 1e-12 near zero) and everything else exactly, and the analysis-ready panel "
          "value by value. "
          "`code/tests/test_datapackage.py` checks `datapackage.json` with frictionless (`frictionless validate "
          "datapackage.json`: 0 errors).", "",
          "## Page sections and figures", "",
          "Each section of the page, its figures (the figure CSVs are published with the page), the key in "
          "`results.json` and the script that produces it. The page itself is built by `code/src/11_build_page.py`, "
          "which needs the website and is not run here.", "",
          "| Page section | Figures | results.json key | Script |", "|---|---|---|---|"]
    L += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in PAGE_MAP]
    L += ["", "## How to cite", "",
          "The repository is archived on Zenodo. Cite the concept DOI for the data and code in general, and the "
          "version DOI when you use specific numbers:", "",
          f"- In general (all versions; resolves to the latest): Spivey, T. D. (2026). {TITLE} [Data set]. Zenodo. "
          f"https://doi.org/{concept}",
          *[f"- Version {ver}: Spivey, T. D. (2026). {TITLE} (Version {ver}) [Data set]. Zenodo. "
            f"https://doi.org/{doi}" for ver, doi in version_dois().items()],
          *([] if VERSION in version_dois() else
            [f"- Version {VERSION} (this one) gets its own DOI when it is released; until then, cite the concept DOI."]),
          "",
          "`CITATION.cff` lists every DOI, and GitHub's \"Cite this repository\" button reads it.", "",
          "## Corrections and contributing", "",
          "Every correction made so far is in `ERRATA.md` (generated from the decision log). To report a data error, "
          "use the issue form described in `CONTRIBUTING.md`; a change to a published number is a new major version.", "",
          "## Disclosure", "",
          "The author works in the telecommunications industry. This analysis was done independently, on personal "
          "time, using only publicly available government data. It uses no employer data or confidential "
          "information, and the views are the author's alone. The author has no financial interest in any FCC "
          "proceeding. AI assistance: `AI_ASSISTANCE.md`.", ""]
    write(T / "README.md", "\n".join(L))


RUN_ALL = '''"""Rebuild the panel and results.json from data/input, into build/ (one command: python run_all.py).

Runs the steps listed in README.md, in order, each in its own process, and stops at the first failure. Nothing is
downloaded. Compare with: python -m pytest code/tests/test_reproduction.py
"""
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
SRC = REPO / "code" / "src"
STEPS = STEPS_LITERAL


def main():
    t0 = time.time()
    for script, args in STEPS:
        print(f"== {script} {' '.join(args)}", flush=True)
        r = subprocess.run([sys.executable, script, *args], cwd=SRC)
        if r.returncode:
            raise SystemExit(f"{script} failed (exit {r.returncode})")
    print(f"done in {(time.time() - t0) / 60:.1f} min; outputs in build/")


if __name__ == "__main__":
    main()
'''

TEST_REPRO = '''"""The code reproduces the published files: run python run_all.py first (each check skips until then).

CSVs must match byte for byte. results.json: numbers within a relative 1e-8 (or 1e-12 absolute, for values that are
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
                                                 "excluded_reports.csv", "area_status_counts.csv",
                                                 "external_validation_fcc_2017.csv")]


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
'''

TEST_DATAPACKAGE = '''"""datapackage.json is a valid Data Package: frictionless validate datapackage.json gives 0 errors (v2.2.0).

Checks the descriptor and every tabular resource's rows against its schema (types, required values, primary keys)."""
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def test_datapackage_validates_with_no_errors():
    frictionless = pytest.importorskip("frictionless", reason="pip install frictionless (in requirements.txt)")
    report = frictionless.validate(str(REPO / "datapackage.json"))
    errors = [e.message for e in report.errors]
    for task in report.tasks:
        errors += [f"{task.name}: {e.message}" for e in task.errors]
    assert report.valid and not errors, errors[:20]
'''

# GitHub Actions pinned to commit SHAs (v3.1.0); Dependabot proposes updates weekly
ACTIONS = {"checkout": ("actions/checkout", "11d5960a326750d5838078e36cf38b85af677262", "v4.4.0"),
           "setup-python": ("actions/setup-python", "a26af69be951a213d495a4c3e4e4022e16d87065", "v5.6.0"),
           "upload-artifact": ("actions/upload-artifact", "ea165f8d65b6e75b540449e92b4886f43607fa02", "v4.6.2")}


def uses(name: str) -> str:
    repo, sha, tag = ACTIONS[name]
    return f"{repo}@{sha}  # {tag}"


CI_WORKFLOW = f"""name: CI

# On every push, and on the 1st of each month: lint, the tests, the quickstart notebook, a full rebuild from
# data/input, then the reproduction tests (build/ vs data/analysis/), on Linux and Windows. Nothing is downloaded
# except the Python packages. Every action is pinned to a commit SHA (Dependabot proposes updates).
on:
  push:
  pull_request:
  workflow_dispatch:
  schedule:
    - cron: "17 6 1 * *"

permissions:
  contents: read

jobs:
  reproduce:
    name: ${{{{ matrix.os }}}}
    runs-on: ${{{{ matrix.os }}}}
    timeout-minutes: 90
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
    env:
      PYTHONHASHSEED: "0"
      PYTHONIOENCODING: utf-8
      MPLBACKEND: Agg
    steps:
      - uses: {uses("checkout")}
      - uses: {uses("setup-python")}
        with:
          python-version: "3.13"
          cache: pip
          cache-dependency-path: requirements.lock
      - name: Install the locked environment
        run: python -m pip install --require-hashes -r requirements.lock
      - name: Lint (ruff.toml)
        run: python -m ruff check code examples run_all.py
      - name: Tests (build checks skip before the rebuild)
        run: python -m pytest code/tests -q -rs
      - name: Quickstart notebook (examples/quickstart.ipynb)
        run: python -m pytest --nbmake examples/quickstart.ipynb -q
      - name: Validate datapackage.json
        run: frictionless validate datapackage.json
      - name: Rebuild everything from data/input
        run: python run_all.py
      - name: Reproduction tests (build/ vs data/analysis/)
        run: python -m pytest code/tests -q -rs --junitxml=build/pytest.xml
      - name: Report failures as annotations
        if: failure()
        shell: python
        run: |
          import xml.etree.ElementTree as ET
          from pathlib import Path
          p = Path("build/pytest.xml")
          for case in (ET.parse(p).getroot().iter("testcase") if p.exists() else []):
              for bad in list(case.findall("failure")) + list(case.findall("error")):
                  msg = (bad.get("message") or bad.text or "")[:1800].replace("%", "%25").replace("\\r", "").replace("\\n", "%0A")
                  print(f"::error title={{case.get('name')}}::{{msg}}")
      - name: Keep the rebuilt results for comparison
        if: always()
        uses: {uses("upload-artifact")}
        with:
          name: build-${{{{ matrix.os }}}}
          path: |
            build/output/results.json
            build/processed/dirs_county_day.csv
            build/processed/storms.csv
            build/processed/panel_analysis_ready.csv
          if-no-files-found: warn
"""

DEPENDABOT = """# Weekly update proposals for the pinned GitHub Actions and the Python packages (v3.1.0).
# A package update changes requirements.txt; regenerate requirements.lock (see README) before merging.
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
"""


ISSUE_TEMPLATE = """name: Report a data error
description: A number in the panel, the storm table or results.json that does not match the FCC report it comes from.
title: "Data error: <storm>, <report date>, <county>"
labels: ["data error"]
body:
  - type: markdown
    attributes:
      value: >-
        Thank you. Each row of the panel comes from one FCC DIRS Communications Status Report; the reports are in
        data/input/dirs/ and listed in code/manifest/dirs_reports.csv. Known FCC misprints are in
        code/manifest/known_fcc_inconsistencies.csv, and corrections made so far are in ERRATA.md.
  - type: input
    id: storm
    attributes:
      label: Storm
      description: Name and year, or the storm_key (NHC ID and DIRS activation date).
      placeholder: Harvey 2017 (AL092017_2017-08-25)
    validations:
      required: true
  - type: input
    id: report
    attributes:
      label: Report (DOC id)
      description: The doc_id column, or the report's date.
      placeholder: DOC-346499A1
    validations:
      required: true
  - type: input
    id: county
    attributes:
      label: County
      description: County and state, or the 5-digit FIPS code. Leave blank if the error is not about one county.
      placeholder: Matagorda, Texas (48321)
  - type: textarea
    id: wrong
    attributes:
      label: What is wrong
      description: The file and column, the value it has, and the value you expected.
    validations:
      required: true
  - type: textarea
    id: evidence
    attributes:
      label: Evidence
      description: >-
        Where the right value is printed: the report's page and table row, a quote, or a screenshot. A public source
        only, please.
    validations:
      required: true
"""


def contributing_md(T: Path) -> None:
    write(T / "CONTRIBUTING.md", f"""# Contributing

Thank you for checking this work. Corrections are welcome, and every one is credited in the decision log.

## Report a data error

Open an issue with the **Report a data error** form ({GITHUB}/issues/new?template=data_error.yml): the storm, the
report's DOC id, the county, what is wrong and the evidence (the report's page and row). Each panel row comes from
one FCC DIRS report in `data/input/dirs/`; checked FCC misprints are in `code/manifest/known_fcc_inconsistencies.csv`
and the corrections made so far in `ERRATA.md`.

## How a correction is made

1. The error is checked against the report's text and PDF.
2. The fix goes into the code or a hand-made table in `code/manifest/` (never into a published file by hand), with
   a test from the report's own text.
3. It is logged in `docs/decisions.md` as a CORRECTION (date, what, why). `ERRATA.md`, `DEVIATIONS.md` and the
   page's Corrections list are generated from that log.
4. The whole pipeline is rerun and the reproduction tests compared. A change to any published number is a new major
   version (`CHANGELOG.md` states the rule), archived on Zenodo with its own DOI.

## Code changes

This repository is generated by `code/src/14_data_repo.py` from the author's working project, so pull requests are
applied there and the repository regenerated; they are still the best way to propose a change. Before opening one:

```
python -m pip install --require-hashes -r requirements.lock
python -m ruff check code examples run_all.py
python -m pytest code/tests -q
python run_all.py && python -m pytest code/tests -q   # the reproduction tests must still pass
python -m pytest --nbmake examples/quickstart.ipynb
```

Ground rules: public data only; never name, infer or estimate an individual provider; associations, not causes.
""")


def errata_md(T: Path) -> None:
    step11 = importlib.import_module("11_build_page")
    text = (ROOT / "docs" / "decisions.md").read_text(encoding="utf-8")
    rows = step11.corrections(text)
    L = ["# Errata", "",
         "Generated by `code/src/14_data_repo.py` from the CORRECTION entries of `docs/decisions.md`, in the log's "
         "order and wording. Each correction was made after results or an independent check were seen; the version "
         "that carries it is in `CHANGELOG.md`. To report an error: `CONTRIBUTING.md`.", "",
         f"{len(rows)} corrections.", "", "| Date | Correction | Reason |", "|---|---|---|"]
    L += [f"| {d} | {w} | {y} |" for d, w, y in rows]
    write(T / "ERRATA.md", "\n".join(L) + "\n")


def scripts(T: Path) -> None:
    write(T / "run_all.py", RUN_ALL.replace("STEPS_LITERAL", "[\n" + "".join(
        f"    ({s!r}, {a.split()!r}),\n" for s, a, _ in RUN_ORDER) + "]"))
    write(T / "code" / "tests" / "test_reproduction.py", TEST_REPRO)
    write(T / "code" / "tests" / "test_datapackage.py", TEST_DATAPACKAGE)
    write(T / ".github" / "workflows" / "ci.yml", CI_WORKFLOW)
    write(T / ".github" / "dependabot.yml", DEPENDABOT)
    write(T / ".github" / "ISSUE_TEMPLATE" / "data_error.yml", ISSUE_TEMPLATE)
    write(T / "requirements.txt", "\n".join(PUBLIC_REQUIREMENTS) + "\n")
    lock = LOCKFILE.read_text(encoding="utf-8")
    norm = lambda x: x.lower().replace("_", "-").replace(".", "-")  # noqa: E731
    pinned = {norm(line.split(" ")[0].split(";")[0]) for line in lock.splitlines()
              if "==" in line and not line.startswith((" ", "#"))}
    stale = [r for r in PUBLIC_REQUIREMENTS if norm(r) not in pinned]
    if stale:  # the lockfile must pin exactly what requirements.txt asks for
        raise SystemExit(f"requirements.lock is stale ({stale}); regenerate it (see README)")
    write(T / "requirements.lock", lock)
    write(T / ".gitignore", "build/\n__pycache__/\n.pytest_cache/\n.env\n.venv/\n")
    write(T / ".gitattributes", "# Store every file byte for byte: INPUTS.csv and the reproduction test check SHA-256 "
                                "hashes.\n* -text\n")


def validate_datapackage(T: Path) -> None:
    """Build step (v2.2.0): frictionless must find 0 errors in datapackage.json, or the build stops."""
    import frictionless
    report = frictionless.validate(str(T / "datapackage.json"))
    errors = [e.message for e in report.errors] + [f"{t.name}: {e.message}" for t in report.tasks for e in t.errors]
    if not report.valid or errors:
        raise SystemExit("datapackage.json does not validate:\n" + "\n".join(errors[:30]))
    print(f"datapackage.json: valid (frictionless {frictionless.__version__}, {len(report.tasks)} resources checked)")


# ------------------------------------------------------------------------------------------------ checks --
def scan(T: Path) -> dict:
    """Secrets (.env values, never printed), provider names and IDs, forbidden files, files over 50 MB."""
    files = [p for p in T.rglob("*") if p.is_file() and ".git" not in p.relative_to(T).parts
             and "build" not in p.relative_to(T).parts[:1]]
    env = ROOT / ".env"
    secrets = []
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition("=")
            value = value.strip().strip('"')
            if name.strip() and len(value) >= 8:
                secrets.append((name.strip(), value.encode()))
    names, ids = set(), set()
    for z in sorted((RAW / "bdc").glob("bdc_us_provider_summary_by_geography_*.zip")):
        import zipfile
        zf = zipfile.ZipFile(z)
        for ch in pd.read_csv(zf.open(zf.namelist()[0]), dtype=str, chunksize=500_000,
                              usecols=lambda c: c in ("provider_id", "holding_company", "provider_name", "brand_name")):
            for col in ch.columns:
                vals = set(ch[col].dropna())
                (ids if col == "provider_id" else names).update(vals)
    names = {n for n in names if len(n) >= 6}
    out = {"files": len(files), "bytes": sum(p.stat().st_size for p in files),
           "over_50MB": [str(p.relative_to(T)) for p in files if p.stat().st_size > MAX_BYTES],
           "forbidden_names": [str(p.relative_to(T)) for p in files if any(n in str(p) for n in NEVER)],
           "secret_hits": {}, "provider_name_hits": {}, "provider_id_column_hits": [],
           "provider_names_checked": len(names), "provider_ids_known": len(ids)}
    name_pat = None
    if names:
        import re
        name_pat = re.compile("|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)), re.I)
    for p in files:
        b = p.read_bytes()
        for label, v in secrets:
            if v in b:
                out["secret_hits"].setdefault(label, []).append(str(p.relative_to(T)))
        if p.suffix.lower() in (".csv", ".json", ".md", ".txt", ".cff", ".py", ".yaml", ".html"):
            t = b.decode("utf-8", errors="replace")
            if name_pat:
                hits = sorted({m.group(0) for m in name_pat.finditer(t)})
                if hits:
                    out["provider_name_hits"][str(p.relative_to(T))] = hits[:12]
            if p.suffix.lower() in (".csv", ".json") and "provider_id" in t:
                out["provider_id_column_hits"].append(str(p.relative_to(T)))
        if p.suffix == ".parquet":
            cols = list(pd.read_parquet(p).columns)
            if any("provider" in c for c in cols):
                out["provider_id_column_hits"].append(str(p.relative_to(T)))
        # any table column whose values are mostly BDC provider IDs, whatever it is called
        if ids and p.suffix in (".csv", ".parquet"):
            try:
                df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p, dtype=str, keep_default_na=False)
            except Exception as err:  # reported, not hidden
                out.setdefault("unreadable_tables", []).append(f"{p.relative_to(T)}: {type(err).__name__}")
                continue
            for col in df.columns:
                vals = {str(v) for v in df[col].dropna().unique() if str(v) != ""}
                if len(vals) >= 5 and len(vals & ids) >= 0.5 * len(vals):
                    out.setdefault("provider_id_value_hits", []).append(f"{p.relative_to(T)}:{col}")
    out.setdefault("provider_id_value_hits", [])
    out["provider_names_note"] = ("The BDC summary files and listings used carry no provider names (0 found), so names "
                                  "are checked by column: no file has a provider_name, brand_name or holding_company "
                                  "column, and the FCC DIRS reports are county aggregates that name no provider.")
    return out


def main():
    T = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parents[1] / REPO_NAME
    keep_git = (T / ".git").exists()
    if T.exists():
        for p in T.iterdir():
            if p.name not in (".git", "build"):  # build/ is git-ignored; kept so a finished run can be retested
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    T.mkdir(parents=True, exist_ok=True)
    idx = copy_inputs(T)
    copy_analysis(T)
    copy_code(T)
    copy_docs(T)
    plan = plan_as_committed(T)
    deviations_md(T)
    errata_md(T)
    contributing_md(T)
    pkg = datapackage(T, plan)
    codebook_md(T, pkg)
    citation_cff(T)
    changelog(T)
    licenses(T)
    ai_statement(T)
    sources_md(T, idx)
    readme(T, idx, plan)
    scripts(T)
    validate_datapackage(T)
    report = scan(T)
    write(ROOT / "output" / "data_repo_scan.json", json.dumps(report, indent=1) + "\n")
    print(json.dumps({k: v for k, v in report.items()}, indent=1)[:4000])
    print("target:", T, "| kept .git:", keep_git, "| inputs:", len(idx), "| missing URL:",
          int((idx.url == "").sum()), "(derived files have none)")


if __name__ == "__main__":
    main()
