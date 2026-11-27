"""Step 19 (4.0.0): the DIRS activation inventory, docs/dirs_activations.csv.

One row per DIRS activation with public Communications Status Reports that is known here, 2016-2026: the 22 storms in
the panel, from manifest/dirs_reports.csv and the parsed tables (dates, states, reports, the table's columns), and the
others from manifest/dirs_activations_other.csv, a checked hand table (its source column says where each row comes
from; the FCC's Past Response Efforts listing refused automated reading, HTTP 403, 2026-11-27).

The inclusion rule (INCLUSION_RULE) is shared with the README and the DATASHEET (step 14).
"""
import pandas as pd

from config import DOCS, INTERIM, MANIFEST, PROCESSED, ROOT, STUDY_STATES

OTHER = ROOT / "manifest" / "dirs_activations_other.csv"
OUT = DOCS / "dirs_activations.csv"
COLUMNS = ["event", "year", "event_type", "nhc_id", "dirs_activation_date", "first_report", "last_report", "geography",
           "n_reports", "table_columns", "decision", "reason", "source"]
INCLUSION_RULE = (
    "A DIRS activation is included when it is for an Atlantic named storm, hurricane or tropical storm (a storm that "
    "never reaches hurricane strength is included too; every storm in this release did, at some point in its track, "
    "per HURDAT2), its activation date is in 2017-2026, and its public Communications Status Reports print county rows "
    f"in at least one of the ten study states ({', '.join(STUDY_STATES)}). Within an included storm, a report whose "
    "rows all lie outside those states is kept in the manifest but not used, and rows outside them are dropped. The "
    "series starts in 2017 because the committed analysis plan (2026-11-22) fixed the scope at 2017-2026, the years "
    "whose report layouts the parser was built and checked on; the only 2016 activation, Matthew, has not been read "
    "and is planned as a separate module (docs/roadmap_modules.md). Other hazards (earthquakes, wildfires, winter "
    "storms, power shutoffs) and the territories are outside the rule.")
SUBSET_SENTENCE = ("This dataset is the Gulf and Southeast hurricane subset of a larger public DIRS record: the FCC has "
                   "also published status reports for activations in the territories and for other hazards "
                   "(docs/dirs_activations.csv).")


def table_columns(rows: pd.DataFrame) -> str:
    has = lambda c: rows[c].notna().any()  # noqa: E731
    cols = ["sites served", "sites out", "% out" if rows.pct_printed.astype(bool).any() else "no % out"]
    if has("out_damage"):
        cols.append("out due to damage, transport, power")
    else:
        cols.append("no cause columns")
    cols.append("sites on backup power" if has("on_backup_power") else "no backup-power column")
    if has("prev_sites_out"):
        cols.append("previous day's sites out (two-day layout, some reports)")
    return "; ".join(cols)


def panel_rows() -> pd.DataFrame:
    m = pd.read_csv(MANIFEST, dtype=str, keep_default_na=False)
    rows = pd.read_parquet(INTERIM / "dirs_county_rows.parquet")
    storms = pd.read_csv(PROCESSED / "storms.csv", dtype=str, keep_default_na=False)
    out = []
    for s in storms.itertuples():
        mm = m[(m.nhc_id == s.nhc_id) & (m.dirs_activation_date == s.dirs_activation_date)]
        r = rows[(rows.row_nhc_id == s.nhc_id) & (rows.row_dirs_activation_date.astype(str) == s.dirs_activation_date)]
        states = sorted(set(r.state))
        inside = [x for x in states if x in STUDY_STATES]
        outside = [x for x in states if x not in STUDY_STATES]
        geo = ", ".join(inside) + (f" (also outside the study states: {', '.join(outside)})" if outside else "")
        n_scope = int((mm.status != "out_of_scope").sum())
        if mm.empty:  # Nicholas: its rows are in reports listed under Ida (shared reports, Sep 15-16, 2021)
            docs = sorted(set(r.doc_id))
            mm = m[m.doc_id.isin(docs)]
            host = ", ".join(sorted(set(mm.storm_name)))
            n_text = f"{len(docs)} reports shared with {host} ({', '.join(docs)}), all in the panel"
        else:
            n_text = f"{len(mm)} in the manifest ({n_scope} in scope, {s.n_reports} in the panel)"
        out.append({
            "event": s.storm, "year": s.dirs_activation_date[:4], "event_type": "Atlantic hurricane or tropical storm",
            "nhc_id": s.nhc_id, "dirs_activation_date": s.dirs_activation_date, "first_report": mm.report_date.min(),
            "last_report": mm.report_date.max(), "geography": geo,
            "n_reports": n_text,
            "table_columns": table_columns(r), "decision": "include",
            "reason": "Atlantic storm, 2017-2026, county rows in the study states",
            "source": "manifest/dirs_reports.csv and the parsed reports (steps 3-4)"})
    return pd.DataFrame(out)


def main():
    other = pd.read_csv(OTHER, dtype=str, keep_default_na=False).assign(nhc_id="")
    inv = pd.concat([panel_rows(), other], ignore_index=True)[COLUMNS]
    inv = inv.sort_values(["year", "dirs_activation_date", "event"], kind="stable")
    DOCS.mkdir(exist_ok=True)
    inv.to_csv(OUT, index=False, lineterminator="\n")
    print(f"{OUT.name}: {len(inv)} activations, {int((inv.decision == 'include').sum())} included")


if __name__ == "__main__":
    main()
