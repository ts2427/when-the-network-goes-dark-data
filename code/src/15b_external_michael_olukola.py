"""Step 15b (v3.2.0; addendum 4.x-1, item 4): two more external checks, compared only, never merged.

1. The FCC's report on Hurricane Michael (May 2019, PS Docket 18-339, DOC-357387A1, data/raw/rules/DOC-357387A1.pdf):
   its figures M1 to M8, transcribed with their pages in manifest/external_fcc_michael_report.csv.
2. Olukola, Addeh, Konan & Rahimi (2026), arXiv:2609.10944 v1: four Helene figures (manifest/external_olukola_2026.csv,
   each VERIFIED in docs/literature.md). Their dataset is not used or redistributed.

Each figure has a written test, fixed in the manifest by its measure:
  pct_over      ours > the FCC figure ("over 46 percent")
  pct_nearly    ours < the figure and rounds (half up, no decimals) to it ("nearly 35 percent")
  one_in_n      sites served / sites out rounds to n ("1 of every 5 sites")
  rank          the county's rank by percent out among every county in the report
  pct_up_to     the largest of the named counties is at most the figure ("up to 45%")
  others_below  every other county in the state is below the figure ("less than 15%")
  state_zero    the state has no site out in that report ("fully restored by October 15")
  last_report   our last report for the storm is on that date
  words_*       a statement with no number to test: our series is shown, not scored
A test that fails needs an explanation in the manifest, or the step stops. Nothing here changes any data.

Writes output/external_validation_fcc_michael.csv and output/external_validation_olukola.csv, and rewrites
docs/external_validation.md as step 15's text followed by these two sections.
Run after steps 15 and 17:  python src/15b_external_michael_olukola.py
"""
import importlib
import json
from decimal import Decimal

import pandas as pd

from config import INTERIM, MANIFEST, OUTPUT, PROCESSED, ROOT

s15 = importlib.import_module("15_external_validation")

MICHAEL = ROOT / "manifest" / "external_fcc_michael_report.csv"
OLUKOLA = ROOT / "manifest" / "external_olukola_2026.csv"
OUT_MICHAEL = OUTPUT / "external_validation_fcc_michael.csv"
OUT_OLUKOLA = OUTPUT / "external_validation_olukola.csv"
FCC_21_99 = ROOT / "manifest" / "external_fcc_21_99.csv"
OUT_21_99 = OUTPUT / "external_validation_fcc_21_99.csv"
FCC_21_99_SOURCE = ("Federal Communications Commission (2021). Resilient Networks; Amendments to Part 4 of the "
                    "Commission's Rules Concerning Disruptions to Communications. Notice of Proposed Rulemaking, FCC "
                    "21-99, PS Docket No. 21-346 (adopted September 30, 2021; released October 1, 2021).")
FCC_21_99_URL = "https://docs.fcc.gov/public/attachments/FCC-21-99A1.pdf"
CABLE = PROCESSED / "dirs_cable_wireline.csv"
MICHAEL_SOURCE = ("FCC Public Safety and Homeland Security Bureau (2019). October 2018 Hurricane Michael's Impact on "
                  "Communications: Preparation, Effect, and Recovery. Report and Recommendations, PS Docket No. 18-339 "
                  "(DOC-357387A1).")
MICHAEL_URL = "https://docs.fcc.gov/public/attachments/DOC-357387A1.pdf"
OLUKOLA_SOURCE = ("Olukola, O., Addeh, O. D., Konan, E. A., & Rahimi, N. (2026). The towers were standing: A cause "
                  "decomposition of cellular outages during Hurricane Helene. arXiv:2609.10944 v1.")
SCORED_OK = {"match", "consistent"}
WORDS = "shown, not scored"


def panel(storm: str) -> pd.DataFrame:
    p = pd.read_parquet(PROCESSED / "panel.parquet",
                        columns=["storm", "doc_id", "report_date", "state", "county", "sites_served", "sites_out"])
    p = p[p.storm == storm].copy()
    p["report_date"] = p.report_date.astype(str)
    p["pct"] = 100 * p.sites_out / p.sites_served
    return p


def state_series(p: pd.DataFrame, states: list) -> str:
    g = p[p.state.isin(states)].groupby(["state", "report_date"])[["sites_out", "sites_served"]].sum()
    parts = []
    for st in states:
        if st not in g.index.get_level_values(0):
            continue
        s = g.loc[st]
        cells = [f"{d[5:]} {int(r.sites_out)} ({100 * r.sites_out / r.sites_served:.2f}%)" for d, r in s.iterrows()]
        parts.append(f"{st}: " + ", ".join(cells) + f"; last in the reports {s.index.max()}")
    return " | ".join(parts)


def cable_series() -> str:
    c = pd.read_csv(CABLE, dtype={"subscribers_out": "Int64"})
    c = c[c.storm == "Michael"]
    out = []
    for d, g in c.groupby("report_date"):
        out.append(f"{d[5:]} " + ", ".join(f"{a} {'' if pd.isna(v) else f'{int(v):,}'}"
                                           for a, v in zip(g.area, g.subscribers_out)))
    return "; ".join(out)


def check_michael(f: pd.DataFrame) -> pd.DataFrame:
    p = panel("Michael")
    listed = pd.read_csv(MANIFEST, dtype=str)
    listed = listed[listed.storm_name == "Michael"]
    out = []
    for r in f.fillna("").itertuples(index=False):
        rec = {**r._asdict(), "doc_id": "", "ours": "", "ours_detail": "", "status": ""}
        if r.report_date and r.measure != "last_report":
            rec["doc_id"] = listed[listed.report_date == r.report_date].doc_id.iloc[0]
        rep = p[p.report_date == r.report_date]
        states = [a for a in r.area.split(";") if a]
        counties = [c for c in r.county.split(";") if c]
        sel = rep[rep.state.isin(states) & rep.county.isin(counties)] if counties else rep[rep.state.isin(states)]
        m = r.measure
        if m in ("pct_over", "pct_nearly", "one_in_n"):
            x = sel.iloc[0]
            rec["ours"] = f"{x.pct:.2f}"
            rec["ours_detail"] = f"{x.sites_out:,.0f} of {x.sites_served:,.0f} sites out"
            v = float(r.fcc_value)
            if m == "pct_over":
                ok = x.pct > v
            elif m == "pct_nearly":
                ok = x.pct < v and s15.to_places(x.pct, 0) == Decimal(r.fcc_value)
            else:
                n = x.sites_served / x.sites_out
                rec["ours_detail"] += f" (1 in {n:.2f})"
                ok = s15.to_places(n, 0) == Decimal(r.fcc_value)
            rec["status"] = ("match" if m == "pct_over" else "consistent") if ok else "differs"
        elif m == "rank":
            ranked = rep.sort_values("pct", ascending=False).reset_index(drop=True)
            pos = int(ranked.index[ranked.county == counties[0]][0]) + 1
            rec["ours"] = str(pos)
            rec["ours_detail"] = "; ".join(f"{c.title()} {v:.2f}%" for c, v in zip(ranked.county[:4], ranked.pct[:4]))
            rec["status"] = "match" if pos == int(r.fcc_value) else "differs"
        elif m == "pct_up_to":
            rec["ours"] = f"{sel.pct.max():.2f}"
            rec["ours_detail"] = "; ".join(f"{c.title()} {v:.2f}% ({o:.0f} of {s:.0f})" for c, v, o, s in
                                           zip(sel.county, sel.pct, sel.sites_out, sel.sites_served))
            rec["status"] = "consistent" if sel.pct.max() <= float(r.fcc_value) else "differs"
        elif m == "others_below":
            named = set(f[f.id == "M4a"].county.iloc[0].split(";"))
            rest = sel[~sel.county.isin(named)].sort_values("pct", ascending=False)
            rec["ours"] = f"{rest.pct.max():.2f}"
            rec["ours_detail"] = (f"highest other Florida county: {rest.county.iloc[0].title()} "
                                  f"({rest.sites_out.iloc[0]:.0f} of {rest.sites_served.iloc[0]:.0f}); {len(rest)} counties")
            rec["status"] = "consistent" if (rest.pct < float(r.fcc_value)).all() else "differs"
        elif m == "state_zero":
            out_n, served = sel.sites_out.sum(), sel.sites_served.sum()
            rec["ours"] = f"{out_n:.0f}"
            rec["ours_detail"] = f"{out_n:.0f} of {served:,.0f} sites out ({100 * out_n / served:.2f}%)"
            rec["status"] = "match" if out_n == 0 else "differs"
        elif m == "last_report":
            last = listed.report_date.max()
            rec["ours"] = last
            rec["ours_detail"] = f"{len(listed)} reports, {listed.report_date.min()} to {last}"
            rec["status"] = "match" if last == r.fcc_value else "differs"
        elif m == "words_state_series":
            rec["ours_detail"] = state_series(p, states)
            rec["status"] = WORDS
        elif m == "words_cable_series":
            rec["ours_detail"] = cable_series()
            rec["status"] = WORDS
        else:
            raise SystemExit(f"{r.id}: unknown measure {m}")
        if rec["status"] not in SCORED_OK | {WORDS} and not r.explanation:
            raise SystemExit(f"{r.id}: {rec['status']} with no explanation (ours {rec['ours']}, FCC {r.fcc_value})")
        out.append(rec)
    cols = ["id", "where", "fcc_text", "report_date", "doc_id", "area", "county", "measure", "fcc_value", "ours",
            "ours_detail", "status", "explanation"]
    return pd.DataFrame(out)[cols]


def check_olukola(f: pd.DataFrame) -> pd.DataFrame:
    res = json.loads((OUTPUT / "results.json").read_text(encoding="utf-8"))["chapter_5"]["external_check"]
    out = []
    for r in f.fillna("").itertuples(index=False):
        rec = {**r._asdict(), "ours": "", "status": ""}
        p = panel(r.storm)
        rep = p[p.report_date == r.report_date]
        if r.measure == "sites_out_all_rows":
            rows = pd.read_parquet(INTERIM / "dirs_county_rows.parquet", columns=["doc_id", "state", "sites_out"])
            doc = pd.read_csv(MANIFEST, dtype=str).query("storm_name == @r.storm and report_date == @r.report_date")
            x = rows[rows.doc_id == doc.doc_id.iloc[0]]
            by = x.groupby("state").sites_out.sum()
            rec["ours"] = (f"{x.sites_out.sum():,.0f} in the report's rows ({doc.doc_id.iloc[0]}): "
                           + ", ".join(f"{k} {v:,.0f}" for k, v in by.items())
                           + "; the panel holds only the study states")
            rec["status"] = "match" if x.sites_out.sum() == int(r.theirs) else "differs"
        elif r.measure == "sites_out":
            rec["ours"] = f"{rep.sites_out.sum():,.0f} ({rep.state.nunique()} states, report of {r.report_date})"
            rec["status"] = "match" if rep.sites_out.sum() == int(r.theirs) else "differs"
        elif r.measure == "sites_served":
            served, n = rep.sites_served.sum(), rep.sites_out.sum()
            rec["ours"] = f"{served:,.0f} ({100 * n / served:.1f}%)"
            rec["status"] = "match" if f"{served:.0f} ({100 * n / served:.1f}%)" == r.theirs else "differs"
        elif r.measure == "attributed_shares":
            o = res["ours_converted"]
            rec["ours"] = "; ".join(f"{k} {o[k]:.1f}" for k in ("damage", "power", "transport"))
            same = [f"{o[k]:.1f}" == f"{res['paper'][k]:.1f}" for k in ("damage", "power", "transport")]
            rec["status"] = "match" if all(same) else f"{sum(same)} of 3 match"
        elif r.measure == "county_days":
            nc = int((p.state == "North Carolina").sum())
            tn = int((p.state == "Tennessee").sum())
            rec["ours"] = f"NC {nc:,}; TN {tn:,}; all six states {len(p):,} ({p.doc_id.nunique()} reports)"
            rec["status"] = WORDS
        else:
            raise SystemExit(f"{r.id}: unknown measure {r.measure}")
        if rec["status"] not in SCORED_OK | {WORDS} and not r.explanation:
            raise SystemExit(f"{r.id}: {rec['status']} with no explanation")
        out.append(rec)
    return pd.DataFrame(out)[["id", "storm", "figure", "where", "theirs", "ours", "status", "explanation"]]


def check_21_99(f: pd.DataFrame) -> pd.DataFrame:
    """FCC 21-99's Ida figures against the report it cites: the state's printed totals, and our county rows."""
    totals = pd.read_parquet(INTERIM / "dirs_state_totals.parquet")
    rows = pd.read_parquet(INTERIM / "dirs_county_rows.parquet")
    listed = set(pd.read_csv(MANIFEST, dtype=str).doc_id)
    out = []
    for r in f.fillna("").itertuples(index=False):
        if r.doc_id not in listed:
            raise SystemExit(f"{r.id}: {r.doc_id} is not among our reports")
        t = totals[(totals.doc_id == r.doc_id) & (totals.state == r.state)].iloc[0]
        x = rows[(rows.doc_id == r.doc_id) & (rows.state == r.state)]
        cols = ["out_power"] if r.measure == "out_power" else ["out_damage", "out_transport"]
        printed, summed = int(sum(t[c] for c in cols)), int(x[cols].sum().sum())
        status = "match" if printed == summed == int(r.fcc_value) else "differs"
        if status != "match" and not r.explanation:
            raise SystemExit(f"{r.id}: {status} with no explanation")
        out.append({**r._asdict(), "ours": f"{summed:,}",
                    "ours_detail": (f"{r.state} total printed in the report: {printed:,}"
                                    + ("" if len(cols) == 1 else f" (damage {int(t.out_damage)}, transport "
                                                                 f"{int(t.out_transport)})")
                                    + f"; sum of its {len(x)} county rows: {summed:,}"),
                    "status": status})
    return pd.DataFrame(out)[["id", "where", "fcc_text", "doc_id", "report_date", "state", "measure", "fcc_value",
                              "ours", "ours_detail", "status", "explanation"]]


def markdown(m: pd.DataFrame, o: pd.DataFrame, f: pd.DataFrame) -> str:
    scored = m[m.status != WORDS]
    ok = scored.status.isin(SCORED_OK).sum()
    lines = [
        "", "# External validation: the FCC's report on Hurricane Michael (v3.2.0)", "",
        "Generated by `src/15b_external_michael_olukola.py` from `manifest/external_fcc_michael_report.csv`. "
        "Exploratory (addendum 4.x-1, item 4). No data were changed because of this check.", "",
        f"**Source.** {MICHAEL_SOURCE} {MICHAEL_URL}. Each figure the report gives in its text is transcribed with its "
        "page and compared with the matching DIRS report in the panel. Its maps and charts are images and are not "
        "read. Each figure's test is fixed by its measure (see the step's docstring); statements with no number to "
        "test are shown beside our series, not scored.", "",
        f"**Result.** {len(m)} figures: {len(scored)} scored, of which {ok} match or are consistent and "
        f"{len(scored) - ok} differ{'s' if len(scored) - ok == 1 else ''} (explained below); {len(m) - len(scored)} "
        "shown, not scored.", "",
        "| # | Where | FCC figure | Report | Area | FCC | Ours | Detail | Status | Explanation |",
        "|---|---|---|---|---|---|---|---|---|---|"]
    for r in m.itertuples():
        area = f"{r.county.title().replace(';', ', ')}, {r.area}" if r.county else r.area.replace(";", ", ")
        lines.append(f"| {r.id} | {r.where} | {r.fcc_text} | {r.report_date} {r.doc_id} | {area} | {r.fcc_value} | "
                     f"{r.ours} | {r.ours_detail} | {r.status} | {r.explanation} |")
    lines += [
        "", "# External check: Olukola et al. (2026), Helene (v3.2.0)", "",
        f"**Source.** {OLUKOLA_SOURCE} Each figure is VERIFIED in `docs/literature.md`. Compared only: their dataset is "
        "not released, and would not be merged or redistributed if it were.", "",
        "**Result.** The Helene peak (4,562 sites out, 28 September 2024) and the sites in the reporting area (37,717, "
        "12.1% out) match an independent extraction exactly, and so does Irma's peak (4,370 sites out on 11 September "
        "2017, counting Puerto Rico and the U.S. Virgin Islands, which are in the report but outside the panel). The "
        "cause split is already published in chapter 4; the county-day counts are defined differently and are shown, "
        "not scored.", "",
        "| # | Storm | Figure | Where | Theirs | Ours | Status | Explanation |", "|---|---|---|---|---|---|---|---|"]
    for r in o.itertuples():
        lines.append(f"| {r.id} | {r.storm} | {r.figure} | {r.where} | {r.theirs} | {r.ours} | {r.status} | "
                     f"{r.explanation} |")
    ok = (f.status == "match").sum()
    lines += [
        "", "# External check: FCC 21-99 on Hurricane Ida (v3.2.0)", "",
        f"**Source.** {FCC_21_99_SOURCE} {FCC_21_99_URL} (`data/input/rules/FCC-21-99A1.pdf`). Its footnote 60 gives "
        "Ida's cell sites out by cause from the FCC's status report of August 31, 2021 (DOC-375367A1), which is among "
        "our reports. Exploratory; no data were changed because of this check.", "",
        f"**Result.** {ok} of {len(f)} figures match: they are Louisiana's printed totals in that report, and our "
        "county rows sum to the same.", "",
        "| # | Where | FCC 21-99 | Report | State | FCC | Ours | Detail | Status |", "|---|---|---|---|---|---|---|---|---|"]
    for r in f.itertuples():
        lines.append(f"| {r.id} | {r.where} | {r.fcc_text} | {r.report_date} {r.doc_id} | {r.state} | {r.fcc_value} | "
                     f"{r.ours} | {r.ours_detail} | {r.status} |")
    return "\n".join(lines) + "\n"


def main():
    m = check_michael(pd.read_csv(MICHAEL, dtype=str, keep_default_na=False))
    o = check_olukola(pd.read_csv(OLUKOLA, dtype=str, keep_default_na=False))
    f = check_21_99(pd.read_csv(FCC_21_99, dtype=str, keep_default_na=False))
    m.to_csv(OUT_MICHAEL, index=False, lineterminator="\n")
    o.to_csv(OUT_OLUKOLA, index=False, lineterminator="\n")
    f.to_csv(OUT_21_99, index=False, lineterminator="\n")
    figures = pd.read_csv(s15.FIGURES, dtype=str, keep_default_na=False)
    text = s15.markdown(s15.check(figures)) + markdown(m, o, f)
    s15.OUT_MD.write_text(text, encoding="utf-8", newline="\n")
    print(m[["id", "fcc_value", "ours", "status"]].to_string(index=False))
    print(o[["id", "theirs", "ours", "status"]].to_string(index=False))
    print(f[["id", "fcc_value", "ours", "status", "ours_detail"]].to_string(index=False))


if __name__ == "__main__":
    main()
