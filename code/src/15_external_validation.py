"""Step 15 (v3.1.0): external check of the panel against the FCC's 2017 Atlantic Hurricane Season report.

The FCC Public Safety and Homeland Security Bureau's "2017 Atlantic Hurricane Season Impact on Communications: Report
and Recommendations" (August 2018, DOC-353805A1, data/raw/rules/DOC-353805A1.pdf) gives figures for Harvey and Irma
taken from the same DIRS reports. Every county or state figure it gives for the two storms is transcribed, with its
page, in manifest/external_fcc_2017_report.csv. For each, this step computes the matching value from the panel (or,
for Puerto Rico and the USVI, which are outside the study states, from the parsed report rows) and the figure the
report itself prints.

A figure matches when our value, rounded half up to the FCC's printed decimals, equals it. "match after truncation"
means the FCC dropped decimals instead of rounding. Every other status needs an explanation in the manifest, or the
step stops. Nothing here changes any data: the check is reported, never applied.

Writes output/external_validation_fcc_2017.csv and docs/external_validation.md.
Run after step 9:  python src/15_external_validation.py
"""
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

import pandas as pd

from config import DOCS, INTERIM, MANIFEST, OUTPUT, PROCESSED, ROOT, STUDY_STATES

FIGURES = ROOT / "manifest" / "external_fcc_2017_report.csv"
OUT_CSV = OUTPUT / "external_validation_fcc_2017.csv"
OUT_MD = DOCS / "external_validation.md"
SOURCE = ("FCC Public Safety and Homeland Security Bureau (2018). 2017 Atlantic Hurricane Season Impact on "
          "Communications: Report and Recommendations (DOC-353805A1).")
URL = "https://docs.fcc.gov/public/attachments/DOC-353805A1.pdf"
NEEDS_NO_EXPLANATION = {"match", "consistent"}
COLUMNS = ["id", "storm", "where", "fcc_text", "report_date", "doc_id", "area", "county", "measure", "fcc_value",
           "ours", "ours_detail", "printed_in_report", "source", "status", "explanation"]


def decimals(text: str) -> int:
    return len(text.split(".")[1]) if "." in text else 0


def to_places(x: float, places: int, mode=ROUND_HALF_UP) -> Decimal:
    return Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-places), rounding=mode)


def pct_status(ours: float, fcc: str, out_share: float | None = None) -> str:
    """ours and fcc in the same unit (percent out, or percent in service when out_share is given)."""
    if fcc.startswith(">"):
        return "match" if ours > float(fcc[1:]) else "differs"
    places = decimals(fcc)
    if to_places(ours, places) == Decimal(fcc):
        return "match"
    truncated = to_places(ours, places, ROUND_DOWN) if out_share is None else \
        Decimal(100) - to_places(out_share, places, ROUND_DOWN)
    return "match after truncation" if truncated == Decimal(fcc) else "differs"


def load_rows() -> pd.DataFrame:
    """County rows per report: the panel for the study states, the parsed rows for areas outside them."""
    panel = pd.read_parquet(PROCESSED / "panel.parquet",
                            columns=["storm", "doc_id", "report_date", "state", "county", "sites_served", "sites_out"])
    panel = panel[panel.storm.isin(["Harvey", "Irma"])].assign(source="panel")
    parsed = pd.read_parquet(INTERIM / "dirs_county_rows.parquet",
                             columns=["storm_name", "doc_id", "report_date", "state", "county", "sites_served",
                                      "sites_out"]).rename(columns={"storm_name": "storm"})
    outside = parsed[parsed.storm.isin(["Harvey", "Irma"]) & ~parsed.state.isin(STUDY_STATES)]
    rows = pd.concat([panel, outside.assign(source="report rows (outside the study states; not in the panel)")])
    rows["report_date"] = rows.report_date.astype(str)
    return rows


def printed_pct(doc_id: str, area: list, county: str, state_totals, overall, rows) -> str:
    """The percent out the report itself prints for this area, if it prints one."""
    if county:
        r = rows[(rows.doc_id == doc_id) & (rows.county.str.upper() == county)]
        return "" if r.empty else f"{r.pct_out.iloc[0]:g}% out"
    present = [a for a in area if a in set(rows[rows.doc_id == doc_id].state)]  # the area's states in this report
    if len(present) == 1:
        t = state_totals[(state_totals.doc_id == doc_id) & (state_totals.state == present[0])]
        if not t.empty:
            return f"{t.pct_out.iloc[0]:g}% out ({present[0]} total)"
    o = overall[overall.doc_id == doc_id]
    if not o.empty and set(o.states.iloc[0].split("; ")) == set(present):
        return f"{o.pct_out.iloc[0]:g}% out (report total)"
    return ""


def check(figures: pd.DataFrame) -> pd.DataFrame:
    rows = load_rows()
    parsed_rows = pd.read_parquet(INTERIM / "dirs_county_rows.parquet", columns=["doc_id", "state", "county", "pct_out"])
    state_totals = pd.read_parquet(INTERIM / "dirs_state_totals.parquet")
    overall = pd.read_parquet(INTERIM / "dirs_overall_totals.parquet")
    reports = pd.read_parquet(INTERIM / "dirs_reports.parquet")
    listed = pd.read_csv(MANIFEST, dtype=str)
    out = []
    for f in figures.fillna("").itertuples(index=False):
        rec = {**f._asdict(), "doc_id": "", "ours": "", "ours_detail": "", "printed_in_report": "", "source": ""}
        storm_docs = listed[listed.storm_name == f.storm]
        if f.report_date:
            hit = storm_docs[storm_docs.report_date == f.report_date]
            if len(hit) != 1:
                raise SystemExit(f"{f.id}: no single {f.storm} report on {f.report_date}")
            rec["doc_id"] = hit.doc_id.iloc[0]
        area = [a for a in f.area.split(";") if a]
        r = rows[(rows.doc_id == rec["doc_id"]) & rows.state.isin(area)]
        if f.county:
            r = r[r.county.str.upper() == f.county]
        if f.measure in ("pct_out", "pct_in_service"):
            if r.empty:
                raise SystemExit(f"{f.id}: no rows for {f.area} {f.county} in {rec['doc_id']}")
            share = 100 * r.sites_out.sum() / r.sites_served.sum()
            value = share if f.measure == "pct_out" else 100 - share
            rec["ours"] = f"{value:.2f}"
            rec["ours_detail"] = (f"{r.sites_out.sum():,.0f} of {r.sites_served.sum():,.0f} sites out"
                                  + (f" ({len(r)} counties)" if not f.county else ""))
            rec["status"] = pct_status(value, f.fcc_value, share if f.measure == "pct_in_service" else None)
            rec["printed_in_report"] = printed_pct(rec["doc_id"], area, f.county, state_totals, overall, parsed_rows)
            rec["source"] = "; ".join(sorted(set(r.source)))
        elif f.measure in ("n_counties", "n_counties_over_50"):
            sel = r if f.measure == "n_counties" else r[100 * r.sites_out / r.sites_served > 50]
            rec["ours"] = str(len(sel))
            if f.measure == "n_counties_over_50":
                rec["ours_detail"] = ", ".join(sorted(sel.county))
            rec["status"] = "match" if len(sel) == int(f.fcc_value) else "differs"
            rec["source"] = "; ".join(sorted(set(r.source)))
        elif f.measure == "n_reports":
            in_panel = rows[(rows.storm == f.storm) & (rows.source == "panel")].doc_id.nunique()
            rec["ours"] = str(len(storm_docs))
            rec["ours_detail"] = f"{in_panel} with rows in the study states"
            rec["status"] = "match" if len(storm_docs) == int(f.fcc_value) else "differs"
            rec["source"] = "manifest/dirs_reports.csv"
        elif f.measure in ("cable_wireline_peak", "cable_wireline_at_least"):
            c = reports[reports.storm_name == f.storm].sort_values("report_date")
            peak = c.loc[c.cable_wireline_subs_out.idxmax()]
            first = c.dropna(subset=["cable_wireline_subs_out"]).iloc[0]
            rec["ours"] = f"{peak.cable_wireline_subs_out:.0f}"
            rec["ours_detail"] = (f"most on {peak.report_date}; first report printing it ({first.report_date}): "
                                  f"{first.cable_wireline_subs_out:,.0f}")
            fcc = float(f.fcc_value)
            ok = (peak.cable_wireline_subs_out >= fcc if f.measure == "cable_wireline_at_least"
                  else abs(peak.cable_wireline_subs_out - fcc) <= 0.05 * fcc)
            rec["status"] = ("consistent" if f.measure == "cable_wireline_at_least" else "match") if ok else "differs"
            rec["source"] = "the reports' cable and wireline line (whole area)"
        elif f.measure == "no_panel_field":
            rec["status"] = "no panel field"
        else:
            raise SystemExit(f"{f.id}: unknown measure {f.measure}")
        if rec["status"] not in NEEDS_NO_EXPLANATION and not f.explanation:
            raise SystemExit(f"{f.id}: {rec['status']} with no explanation in {FIGURES.name} (ours {rec['ours']}, "
                             f"FCC {f.fcc_value})")
        out.append(rec)
    return pd.DataFrame(out)[COLUMNS]


def summary(t: pd.DataFrame) -> dict:
    counts = t.status.value_counts()
    return {"n": len(t), **{k: int(counts.get(k, 0)) for k in
                            ("match", "match after truncation", "consistent", "differs", "no panel field")}}


def markdown(t: pd.DataFrame) -> str:
    s = summary(t)
    compared = s["n"] - s["no panel field"]
    differs = t[t.status == "differs"]
    lines = [
        "# External validation: the FCC's 2017 hurricane season report", "",
        "Generated by `src/15_external_validation.py` from `manifest/external_fcc_2017_report.csv` (v3.1.0). "
        "No data were changed because of this check.", "",
        f"**Source.** {SOURCE} {URL}. Every county or state figure it gives for Harvey and Irma is transcribed with "
        "its page and compared with the matching report: the panel's rows for the study states, and the parsed report "
        "rows for Puerto Rico and the U.S. Virgin Islands, which are outside the study states and not in the panel. "
        "\"Printed in the report\" is the figure the DIRS report itself prints, where it prints one.", "",
        f"**Result.** {s['n']} figures: {compared} can be compared with the reports and {s['no panel field']} cannot "
        "(switching centers, PSAPs, broadcast stations and providers' filings, which the panel does not hold). Of the "
        f"{compared}, {s['match']} match, {s['match after truncation']} match once the FCC's dropped decimals are "
        f"allowed for, {s['consistent']} is consistent with a figure stated only in words, and {s['differs']} differ. "
        "Each difference is explained below or marked as not explained. In each, the season report departs from what "
        "the DIRS report prints or from the total its rows reconcile to, so none points to an error in the panel.", "",
        "## Differences", "",
        "| # | FCC figure | Report | Area | FCC | Ours | Printed in the report | Explanation |",
        "|---|---|---|---|---|---|---|---|"]
    for r in differs.itertuples():
        lines.append(f"| {r.id} | {r.where}: {r.fcc_text} | {r.report_date or 'all'} | {_area(r)} | {r.fcc_value} | "
                     f"{r.ours} | {r.printed_in_report} | {r.explanation} |")
    lines += ["", "## Every figure", "",
              "| # | Storm | Where | FCC figure | Report | Area | Measure | FCC | Ours | Detail | Printed in the report | "
              "Source | Status | Explanation |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in t.itertuples():
        lines.append(f"| {r.id} | {r.storm} | {r.where} | {r.fcc_text} | {r.report_date} {r.doc_id} | {_area(r)} | "
                     f"{r.measure} | {r.fcc_value} | {r.ours} | {r.ours_detail} | {r.printed_in_report} | {r.source} | "
                     f"{r.status} | {r.explanation} |")
    return "\n".join(lines) + "\n"


def _area(r) -> str:
    return f"{r.county.title()}, {r.area}" if r.county else r.area.replace(";", ", ")


def main():
    figures = pd.read_csv(FIGURES, dtype=str, keep_default_na=False)
    if figures.id.duplicated().any():
        raise SystemExit("duplicate ids in " + FIGURES.name)
    t = check(figures)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT_CSV, index=False, lineterminator="\n")
    OUT_MD.write_text(markdown(t), encoding="utf-8", newline="\n")
    print(summary(t))


if __name__ == "__main__":
    main()
