"""Step 12b: the analysis-ready panel (v2.2.0). No new data and no new result.

The published county-report panel (dirs_county_day.csv, same rows and order) joined with every covariate the analysis
uses, as built by steps 6 to 9 and 12:
  EAGLE-I       customers out matched to the report's as-of time (and 6, 12 and 24 hours earlier), match quality,
                modeled customers, percent out, coverage and MCC flags (step 6)
  exposure      distance to track, wind at closest approach, 34/50/64-kt radii, the chapter 7 wind zone (step 7)
  day 0         day 0 (UTC), the rule that set it, days since day 0 (step 9; days_since_day0, with
                days_since_landfall kept as a deprecated alias until 4.0.0)
  SVI, ACS      CDC/ATSDR SVI 2022 percentile ranks; ACS 2022 5-year households, population, 65+, broadband (step 8)
  BDC           the storm's Broadband Data Collection release and role, the six provider counts, and the chapter 13
                group on the main measure, using the cut points in results.json v2_5_groups (steps 6f and 12)
  county spans  first and last report in the panel and the censoring status (step 9)

Writes processed/panel_analysis_ready.parquet and .csv (counts as integers, other numbers to 10 significant digits).
Run after step 12:  python src/12b_analysis_ready.py
"""
import importlib
import json

import pandas as pd

from config import OUTPUT, PROCESSED, RAW
from tables import as_counts
import load

step9 = importlib.import_module("09_build_panel")
step10 = importlib.import_module("10_analysis")
step12 = importlib.import_module("12_v2_analysis")

EAGLEI = ["eaglei_time", "eaglei_match", "eaglei_gap_min", "eaglei_customers_out", "eaglei_customers_out_6h",
          "eaglei_customers_out_12h", "eaglei_customers_out_24h", "eaglei_customers_out_zero_filled",
          "eaglei_modeled_customers", "eaglei_pct_out", "eaglei_max_out_in_window", "eaglei_release",
          "eaglei_mcc_flag", "eaglei_coverage_flag", "eaglei_state_min_covered", "eaglei_state_max_covered"]
EXPOSURE = ["min_dist_km", "wind_kt_at_closest", "in_34kt", "in_50kt", "in_64kt", "wind_zone", "first_34kt_utc",
            "nearest_landfall_utc", "nearest_landfall_km", "track_source"]
DAY0 = ["landfall_utc", "landfall_source", "days_since_landfall", "days_since_day0"]  # days_since_day0: 3.1.0
SVI_ACS = ["svi_overall", "svi_socioeconomic", "svi_household", "svi_minority_language", "svi_housing_transport",
           "acs_households", "acs_population", "acs_pct_65plus", "acs_pct_broadband"]
BDC = ["bdc_release", "bdc_role", *[f"bdc_{m}" for m in step12.MEASURES], "bdc_mobile_half_group"]
SPANS = ["first_report_date", "last_report_date", "n_reports_county", "censoring"]
COLUMNS = step9.PUBLIC_COLUMNS + EAGLEI + EXPOSURE + DAY0 + SVI_ACS + BDC + SPANS
if set(load.COUNTS) - set(COLUMNS) or not set(step9.PANEL_COUNTS) <= set(load.COUNTS):
    raise SystemExit("load.COUNTS does not match the columns")


def bdc_columns(panel: pd.DataFrame, results: dict) -> pd.DataFrame:
    """Per storm-county: the storm's BDC release and role, the six provider counts and the main-measure group."""
    releases = json.loads((RAW / "bdc" / "listings" / "storm_releases.json").read_text(encoding="utf-8"))
    counts, n_universal = step12.load_counts()
    sc = step12.storm_county_counts(panel, counts, releases, n_universal)
    cuts = results["v2_5_groups"]["groups"][step12.MAIN_MEASURE]
    sc["bdc_mobile_half_group"] = [step12.assign_group(x, cuts) for x in sc[step12.MAIN_MEASURE]]
    full_role = sc.storm.map(lambda x: releases[x]["role"])
    sc = sc.assign(role=full_role).rename(columns={"release": "bdc_release", "role": "bdc_role",
                                                   **{m: f"bdc_{m}" for m in step12.MEASURES}})
    return sc[["storm_key", "fips", *BDC]]


def analysis_ready(panel: pd.DataFrame, results: dict) -> pd.DataFrame:
    p = panel.assign(wind_zone=[step10.wind_zone(a, b, c) for a, b, c in zip(panel.in_34kt, panel.in_50kt,
                                                                             panel.in_64kt)],
                     time_flag=panel.time_flag.fillna(""),
                     days_since_day0=panel.days_since_landfall)  # documented name since 3.1.0; the old one is an alias
    p = p.rename(columns={"n_reports": "n_reports_county"})
    p = p.merge(bdc_columns(panel, results), on=["storm_key", "fips"], how="left", validate="many_to_one")
    p = p[COLUMNS].sort_values(["storm_key", "report_date", "state", "county"])
    return as_counts(p, load.COUNTS).reset_index(drop=True)


def main():
    panel = pd.read_parquet(PROCESSED / "panel.parquet")
    results = json.loads((OUTPUT / "results.json").read_text(encoding="utf-8"))
    out = analysis_ready(panel, results)
    published = pd.read_csv(PROCESSED / "dirs_county_day.csv", dtype=str, keep_default_na=False)
    if len(out) != len(published) or not (out.doc_id.to_numpy() == published.doc_id.to_numpy()).all() or \
            not (out.fips.to_numpy() == published.fips.to_numpy()).all():
        raise SystemExit("analysis-ready rows differ from dirs_county_day.csv")
    out.to_parquet(PROCESSED / "panel_analysis_ready.parquet", index=False)
    out.to_csv(PROCESSED / "panel_analysis_ready.csv", index=False, lineterminator="\n", float_format="%.10g")
    print(f"panel_analysis_ready: {len(out):,} rows, {out.shape[1]} columns")


if __name__ == "__main__":
    main()
