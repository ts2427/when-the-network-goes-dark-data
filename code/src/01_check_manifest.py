"""Step 1: validate manifest/dirs_reports.csv before downloading anything.

The manifest has one row per FCC DIRS Communications Status Report. status is one of (4.0.0):
  ok            parsed, and passed step 4's validation (status ok, flagged or known_fcc_inconsistency there)
  excluded      parsed, failed step 4, and listed in manifest/excluded_reports.csv with its reason
  out_of_scope  kept and logged, but not parsed or validated
Any other value (the old "verify") fails: every report must be confirmed before a build.
Build it by hand from the FCC storm pages (https://www.fcc.gov/past-response-efforts),
because the FCC site may block automated browsing. Direct docs.fcc.gov file URLs usually download fine.
"""
import sys

import pandas as pd

from config import MANIFEST, ROOT

STATUSES = ("ok", "excluded", "out_of_scope")
EXCLUDED = ROOT / "manifest" / "excluded_reports.csv"

REQUIRED = ["storm_name", "nhc_id", "dirs_activation_date", "report_date", "doc_id", "pdf_url", "txt_url", "status"]


def check(df: pd.DataFrame, excluded: pd.DataFrame | None = None) -> list[str]:
    problems = []
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return [f"missing columns: {missing}"]
    if df.doc_id.duplicated().any():
        problems.append(f"duplicate doc_id: {df.doc_id[df.doc_id.duplicated()].tolist()}")
    bad_doc = df[~df.doc_id.astype(str).str.match(r"^DOC-\d+A\d$")]
    if len(bad_doc):
        problems.append(f"malformed doc_id: {bad_doc.doc_id.tolist()}")
    for col in ["pdf_url", "txt_url"]:
        bad = df[df[col].notna() & ~df[col].astype(str).str.startswith("https://docs.fcc.gov/")]
        if len(bad):
            problems.append(f"{col} not on docs.fcc.gov: {bad.doc_id.tolist()}")
    nhc = df.nhc_id.dropna().astype(str)
    bad_nhc = nhc[~nhc.str.match(r"^AL\d{6}$")]
    if len(bad_nhc):
        problems.append(f"malformed nhc_id (want ALnnYYYY): {bad_nhc.tolist()}")
    todo = df[~df.status.isin(STATUSES) | df.storm_name.eq("TBD") | df.report_date.isna()]
    if len(todo):
        problems.append(f"{len(todo)} reports not confirmed (status not one of {', '.join(STATUSES)}, or no storm or "
                        f"date): {todo.doc_id.tolist()[:10]}")
    if excluded is not None:
        listed, marked = set(excluded.doc_id), set(df[df.status == "excluded"].doc_id)
        if listed != marked:
            problems.append(f"status excluded and manifest/excluded_reports.csv disagree: {sorted(listed ^ marked)}")
    return problems


if __name__ == "__main__":
    df = pd.read_csv(MANIFEST)
    print(f"{len(df)} reports in manifest, {df.storm_name.nunique()} storms")
    print(df.groupby("storm_name").size().to_string())
    probs = check(df, pd.read_csv(EXCLUDED, dtype=str))
    for p in probs:
        print("PROBLEM:", p)
    sys.exit(1 if probs else 0)
