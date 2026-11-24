"""Load the analysis-ready panel with its types (v2.2.0).

    import sys; sys.path.insert(0, "code/src")
    from load import load_panel
    p = load_panel()          # data/analysis/panel_analysis_ready.parquet, or the .csv if there is no parquet

One row per county per FCC DIRS report, joined with every covariate the analysis uses. Variables: CODEBOOK.md.
"""
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve()
# public repository: <repo>/code/src/load.py -> <repo>/data/analysis; private project: <root>/src -> data/processed
_FOLDERS = [_HERE.parents[2] / "data" / "analysis", _HERE.parents[1] / "data" / "processed"]
NAME = "panel_analysis_ready"
DATETIMES = ["as_of_utc", "eaglei_time", "first_34kt_utc", "nearest_landfall_utc", "landfall_utc"]
BOOLEANS = ["as_of_imputed", "pct_printed", "fema_declared", "eaglei_release", "in_34kt", "in_50kt", "in_64kt"]
STRINGS = ["storm_key", "nhc_id", "storm", "dirs_activation_date", "rule_period", "doc_id", "report_date",
           "report_status", "state", "county", "fips", "area_status", "time_flag", "eaglei_match", "eaglei_mcc_flag",
           "eaglei_coverage_flag", "wind_zone", "track_source", "landfall_source", "bdc_release", "bdc_role",
           "bdc_mobile_half_group", "first_report_date", "last_report_date", "censoring"]
COUNTS = ["sites_served", "sites_out", "out_damage", "out_transport", "out_power", "on_backup_power",
          "out_unattributed", "out_overattributed", "eaglei_customers_out", "eaglei_customers_out_6h", "eaglei_customers_out_12h",
          "eaglei_customers_out_24h", "eaglei_customers_out_zero_filled", "eaglei_modeled_customers",
          "eaglei_max_out_in_window", "acs_households", "acs_population", "bdc_mobile_half", "bdc_mobile_any",
          "bdc_fixed_any_excl_near_universal", "bdc_fixed_any", "bdc_fixed_half", "bdc_fixed_half_excl_near_universal",
          "n_reports_county"]


def find_panel(folder=None) -> Path:
    for d in ([Path(folder)] if folder else _FOLDERS):
        for ext in (".parquet", ".csv"):
            if (d / f"{NAME}{ext}").exists():
                return d / f"{NAME}{ext}"
    raise FileNotFoundError(f"{NAME}.parquet or .csv not found in {folder or _FOLDERS}")


def load_panel(path=None, folder=None) -> pd.DataFrame:
    """The analysis-ready panel. The CSV is given the parquet's types: text columns as strings (fips keeps its leading
    zero; missing text is None, time_flag is '' when blank), UTC datetimes, booleans, counts as nullable Int64 and
    every other number as float."""
    path = Path(path) if path else find_panel(folder)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    p = pd.read_csv(path, dtype={c: str for c in STRINGS + BOOLEANS}, keep_default_na=False, na_values={
        c: [""] for c in pd.read_csv(path, nrows=0).columns if c != "time_flag"})
    for c in STRINGS:
        p[c] = p[c].astype(object).where(p[c].notna(), None)
    for c in DATETIMES:
        p[c] = pd.to_datetime(p[c], utc=True)
    for c in BOOLEANS:
        p[c] = p[c].map({"True": True, "False": False}).astype(bool)
    for c in COUNTS:
        p[c] = p[c].astype("Int64")
    for c in p.columns:
        if c not in STRINGS + BOOLEANS + DATETIMES + COUNTS:
            p[c] = p[c].astype(float)
    return p
