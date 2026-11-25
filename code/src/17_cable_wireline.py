"""Step 17 (v3.2.0; addendum 4.x-1, item 1): cable and wireline subscribers out of service, per report.

Reads the "Cable Systems and Wireline (Combined)" figures from every in-scope DIRS report (text file first, the PDF
when the text file is missing or gives fewer figures). Four printed forms:
  sentence   "... 471,792 subscribers out of service in the disaster area ... down from 497,793 yesterday"
             (area = the disaster area, or the state the sentence names: Michael's "in the affected areas in Florida")
  code table "State Subscribers Out of Service AL 14,855 FL 185,841 GA 63,473" (Michael, Florence, Barry, Dorian, Zeta)
  name list  "Alabama Louisiana Mississippi 478 338,115 16,106" (Ida)
  colon list "Florida: 441,799 Georgia: None South Carolina: 36,620" (Ian; "None" is kept as printed, with no number)
One row per report and area. Checks (flagged, never corrected): a printed previous-day figure must equal the previous
report's figure for the same area; a report whose section prints no figure gets a row with area "none printed".
No allocation to counties; no total is added up from state rows (the FCC prints none to check it against).

  python src/17_cable_wireline.py   # writes processed/dirs_cable_wireline.csv
"""
import importlib
import re
import sys

import pandas as pd

from config import MANIFEST, PROCESSED, RAW
from tables import write_csv

s3 = importlib.import_module("03_parse_dirs")

OUT = PROCESSED / "dirs_cable_wireline.csv"
STATES = {"Alabama": "AL", "Florida": "FL", "Georgia": "GA", "Louisiana": "LA", "Mississippi": "MS",
          "North Carolina": "NC", "South Carolina": "SC", "Tennessee": "TN", "Texas": "TX", "Virginia": "VA",
          "Kentucky": "KY", "West Virginia": "WV", "Arkansas": "AR", "Maryland": "MD", "Delaware": "DE",
          "New Jersey": "NJ", "Pennsylvania": "PA", "New York": "NY", "Puerto Rico": "PR", "Oklahoma": "OK"}
NAME_RE = "|".join(sorted(STATES, key=len, reverse=True))
NUM = r"\d{1,3}(?:,\d{3})+|\d+"

SECTION_RE = re.compile(r"Cable Systems and Wireline \(Combined\)(.{0,1200})", re.S)
SENTENCE_RE = re.compile(rf"(?P<n>{NUM})\s*(?:\([^)]*\)\s*)?(?:cable\s+system\s+and\s+wireline\s+outage\s+)?subscribers?"
                         rf"(?P<mid>[^.]{{0,80}}?)out\s+of\s+service(?P<where>[^.;]{{0,80}})", re.I)
PREV_RE = re.compile(rf"(?:up|down)\s+from\s+(?P<p>{NUM})\s+yesterday", re.I)
CODE_RE = re.compile(rf"(?:State\s+Subscribers\s+Out\s+of\s+Service|Subscribers\s+Out\s+of\s+State\s+Service)"
                     rf"(?:\s+\d{{1,2}}(?=\s+[A-Z]{{2}}\s))?(?P<rows>(?:\s+[A-Z]{{2}}\s+(?:{NUM})(?![\d,%]))+)")
NAMES_RE = re.compile(rf"by state in the disaster area;[^:]*:\s*(?P<names>(?:(?:{NAME_RE})\s+)+)(?P<nums>(?:(?:{NUM})\s*)+)")
END_RE = re.compile(r"The following chart|Broadcast|As prepared by|Mandatory Disaster|Wireless Services|AM Radio|"
                    r"FM Radio|Television stations")
COLON_RE =re.compile(rf"(?P<name>{NAME_RE}):\s*(?P<v>{NUM}|None)\b")


def to_int(s: str) -> int:
    return int(s.replace(",", ""))


def parse(text: str) -> list[dict]:
    """Figures from one report's text, as rows {area, subscribers_out, printed, form, previous_day_printed}."""
    t = re.sub(r"\s+", " ", text)
    rows = []
    m = CODE_RE.search(t)
    if m:
        for code, n in re.findall(rf"([A-Z]{{2}})\s+({NUM})", m.group("rows")):
            rows.append({"area": code, "subscribers_out": to_int(n), "printed": n, "form": "code table"})
    m = NAMES_RE.search(t)
    if m:
        names = re.findall(NAME_RE, m.group("names"))
        nums = re.findall(NUM, m.group("nums"))[:len(names)]
        if len(nums) == len(names):
            rows += [{"area": STATES[a], "subscribers_out": to_int(n), "printed": n, "form": "name list"}
                     for a, n in zip(names, nums)]
    sec = SECTION_RE.search(t)
    body = END_RE.split(sec.group(1), maxsplit=1)[0] if sec else ""  # the section only, up to its chart or the next
    if not rows:
        for name, v in COLON_RE.findall(body):
            rows.append({"area": STATES[name], "subscribers_out": None if v == "None" else to_int(v), "printed": v,
                         "form": "colon list"})
    # the whole report is searched for the sentence only when it has no section heading (never for a page number)
    where, m = (body, SENTENCE_RE.search(body)) if sec else (t, SENTENCE_RE.search(t))
    if m and not re.search(r"\b(sites?|PSAPs?|stations?|reported)\b", m.group("mid"), re.I):
        named = re.findall(rf"\b({NAME_RE})\b", m.group("where"))
        # the previous-day figure is in the same sentence (Irma: "(down from N yesterday)") or in a next sentence that
        # starts "This is" (Beryl, Michael); never further on, where switching centers print "(up from N yesterday)"
        stop = where.find(". ", m.end())
        stop = len(where) if stop < 0 else stop
        nxt = re.match(r"\.\s+This (?:is|number is)[^.]*", where[stop:])
        p = PREV_RE.search(where[m.start():stop] + (nxt.group(0) if nxt else ""))
        row = {"area": STATES[named[0]] if len(named) == 1 else "disaster area",
               "subscribers_out": to_int(m.group("n")), "printed": m.group("n"), "form": "sentence",
               "previous_day_printed": to_int(p.group("p")) if p else None}
        same = [r for r in rows if r["area"] == row["area"]]
        if same and same[0]["subscribers_out"] == row["subscribers_out"]:
            same[0]["previous_day_printed"] = row["previous_day_printed"]  # one figure printed twice: one row
            same[0]["form"] += " and sentence"
        else:
            rows.append(row)  # a differing second figure for the same area stays as its own row
    return rows


def report_rows(doc_id: str) -> tuple[list[dict], str]:
    txt = RAW / "dirs" / f"{doc_id}.txt"
    t_txt = txt.read_text(encoding="utf-8", errors="replace") if txt.exists() else ""
    if t_txt.lstrip().lower().startswith(("<!doctype", "<html")):
        t_txt = ""
    a = parse(t_txt) if t_txt else []
    b = parse(s3.pdf_text(RAW / "dirs" / f"{doc_id}.pdf"))
    return (a, "txt") if len(a) >= len(b) and a else (b, "pdf")


def build() -> pd.DataFrame:
    man = pd.read_csv(MANIFEST, dtype=str)
    man = man[man.status != "out_of_scope"].sort_values(["nhc_id", "dirs_activation_date", "report_date"])
    storms = pd.read_csv(PROCESSED / "storms.csv", dtype=str)
    excluded = " ".join(storms.excluded_reports.dropna())
    rows = []
    for r in man.itertuples():
        found, src = report_rows(r.doc_id)
        base = {"storm_key": f"{r.nhc_id}_{r.dirs_activation_date}", "nhc_id": r.nhc_id, "storm": r.storm_name,
                "doc_id": r.doc_id, "report_date": r.report_date, "source": src,
                "from_excluded_report": r.doc_id in excluded}
        if not found:
            rows.append({**base, "area": "none printed", "subscribers_out": None, "printed": "", "form": "none",
                         "previous_day_printed": None})
        for f in found:
            rows.append({**base, "previous_day_printed": None, **f})
    d = pd.DataFrame(rows)
    # previous-day check: the printed figure against the previous report's figure for the same storm and area
    d["previous_report_value"] = None
    d["previous_day_check"] = ""
    for (key, area), g in d.groupby(["storm_key", "area"], sort=False):
        prev_val = g.subscribers_out.shift(1)
        prev_date = g.report_date.shift(1)
        for i, pv, pd_ in zip(g.index, prev_val, prev_date):
            printed = d.at[i, "previous_day_printed"]
            if pd.isna(printed):
                continue
            if pd.isna(pd_):
                d.at[i, "previous_day_check"] = "no previous figure for this area"
                continue
            d.at[i, "previous_report_value"] = pv
            d.at[i, "previous_day_check"] = "match" if not pd.isna(pv) and int(pv) == int(printed) else "mismatch"
    cols = ["storm_key", "nhc_id", "storm", "doc_id", "report_date", "area", "subscribers_out", "printed", "form",
            "source", "previous_day_printed", "previous_report_value", "previous_day_check", "from_excluded_report"]
    return d[cols].sort_values(["storm_key", "report_date", "area"], ignore_index=True)


def main():

    d = build()
    write_csv(d, OUT, counts=["subscribers_out", "previous_day_printed", "previous_report_value"])
    print(f"dirs_cable_wireline: {len(d)} rows, {d.doc_id.nunique()} reports, "
          f"{(d.area == 'none printed').sum()} reports with no figure; previous-day checks: "
          f"{d.previous_day_check.value_counts().to_dict()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
