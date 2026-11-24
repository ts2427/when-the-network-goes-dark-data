"""Step 4: check every parsed report before anything downstream uses it.

A report FAILS on:
  * zero county rows; a duplicate county; out > served
  * a missing, repeated or orphaned state total (a state covered by an overall total needs none: the overall
    total must then equal the sum of its states' rows, for sites served and out)
  * sites served, sites out, any cause column or backup power not adding up to the printed state total
  * cause or backup columns only partly filled
  * a row's printed % out more than 0.1 points from out / served
  * a row that is not found, with the same county and values, in a second reading of the PDF. This catches
    values swapped between counties with no sites out, where every sum and percent still agrees.
  * a county in the report's own list with no row in its table, or no list to compare with. Names match when at
    least 90% alike; one unmatched list name and one unmatched row in the same state, at least 70% alike, are paired
  * causes exceeding sites out on a row the second reading does not confirm
  * a headline that disagrees, unless every row is confirmed and the totals reconcile (then flagged headline_mismatch)
  * no printed totals at all, unless every row is confirmed (then flagged no_printed_totals)
  * one state with no printed total, unless all its rows are confirmed and every other state reconciles (then
    flagged state_total_missing; decided 2026-11-22)
A report in manifest/excluded_reports.csv that still fails is EXCLUDED, with its reason (decided 2026-11-22: one
round of parser fixes; the page's methods section lists every excluded report). One that now passes fails until its
entry is removed.
  * area_status missing or not one of inside, inside_spelling_variant, outside_notice_area, table_not_in_list
  * causes exceeding sites out, unless the row matches manifest/cause_exceptions.csv on every printed value
  * a stated % out that is absent, or more than 0.2 points from the computed one, unless the report matches
    manifest/known_fcc_inconsistencies.csv
  * out_unattributed or out_overattributed dropped or altered
  * an exception entry that is incomplete or no longer matches

A report is FLAGGED, not failed, when causes fall short of sites out, when a listed cause or county-list
exception applies, when the FCC lists a county twice, when a row is in the table but not the report's county
list, or when rows are outside the storm's notice area (decided 2026-11-22). Such rows stay in the data, as
printed; the second reading above confirms each was read correctly. Rows with no printed % (Sally 2020) skip
the two percent checks.

Two checks stop the build outright, for every report including excluded ones (correction, 2026-11-24, after Harvey's
Sep 4-5, 2017 two-day table was misread):
  * a count that is not a whole number (sites served or out, a cause, backup power, in a county row or a total)
  * a previous-day column (two-day layout) that differs from the previous day's report for the same county (sites
    out and % out), or a two-day report whose previous day has no report or lacks one of its counties

Status: fail > known_fcc_inconsistency > flagged > ok. Only "fail" stops the build.
The page uses pct_out_used (always computed from county rows) and records stated_pct_out beside it.

Writes output/validation_dirs.csv (status and reasons), output/validation_summary.csv (the table the page cites)
and output/area_status_counts.csv (area status counts per report, for the methods section).
"""
import difflib
import re
import sys
import unicodedata
from collections import Counter

import pandas as pd

from carried import CAUSES, require_carried
AREA_STATUSES = ("inside", "inside_spelling_variant", "outside_notice_area", "table_not_in_list")
from config import INTERIM, OUTPUT, ROOT
from dirs_parser import CODE_TO_STATE
from tables import write_csv

OVER_EXCEPTIONS = ROOT / "manifest" / "cause_exceptions.csv"
LIST_EXCEPTIONS = ROOT / "manifest" / "county_list_exceptions.csv"
EXCLUDED = ROOT / "manifest" / "excluded_reports.csv"
HEADLINE_EXCEPTIONS = ROOT / "manifest" / "known_fcc_inconsistencies.csv"
# A printed state total that its own county rows do not add up to, checked against the PDF (2026-11-24: Harvey Sep 4
# and 5, 2017 print Texas sites served 4,200 over the same rows that Sep 3 totals 4,199). Applies only when every row
# of the state is confirmed by the second reading; gives known_fcc_inconsistency. An entry that no longer matches fails.
TOTAL_EXCEPTIONS = ROOT / "manifest" / "known_total_inconsistencies.csv"

PRINTED = ["sites_served", "sites_out", "pct_out", *CAUSES, "on_backup_power"]
OVER_FIELDS = ["doc_id", "page", "state", "county", *PRINTED, "checked_on"]
HEADLINE_FIELDS = ["doc_id", "page", "stated_pct", "total_served", "total_out", "checked_on"]
SUMMARY_COLUMNS = ["Report", "Rows", "Exact", "Short by 1", "Short by more", "Causes exceed out",
                   "Sites with no cause"]
PCT_TOLERANCE = 0.2  # points; the FCC rounds and sometimes truncates
ROW_PCT_TOLERANCE = 0.1  # points; row percents are printed to one or two places, rounded or truncated
NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?%?")


def name_key(name) -> str:
    """Case, spacing, punctuation, accents and a trailing "County" or "Parish" don't matter; the letters do."""
    plain = unicodedata.normalize("NFKD", str(name)).strip()
    plain = re.sub(r"\s+(county|parish)$", "", plain, flags=re.IGNORECASE)
    return "".join(c for c in plain.casefold() if c.isalnum())


SPELLING_CUTOFF = 0.9  # an FCC misspelling: "Dillion" for Dillon, "Point Coupee" for Pointe Coupee
PAIR_CUTOFF = 0.7  # one unmatched list name and one unmatched table row in a state: "Unicorn" for Unicoi


def same(a, b) -> bool:
    if pd.isna(a) or pd.isna(b):
        return bool(pd.isna(a) and pd.isna(b))
    return abs(float(a) - float(b)) < 1e-6


def for_report(df: pd.DataFrame, doc: str, columns: list[str]) -> pd.DataFrame:
    if df.empty or "doc_id" not in df.columns:
        return pd.DataFrame(columns=columns)
    return df[df.doc_id == doc]


def incomplete(entry) -> bool:
    return bool(pd.isna(entry["page"]) or pd.isna(entry["checked_on"]))


def check_totals(g: pd.DataFrame, t: pd.DataFrame, overall: pd.DataFrame | None = None) -> list[str]:
    fails = []
    row_states, total_states = g.state.map(name_key), t.state.map(name_key)
    covered = set()
    for o in (overall if overall is not None else pd.DataFrame()).to_dict("records"):
        states = {name_key(s) for s in str(o["states"]).split("; ")}
        covered |= states
        rows = g[row_states.isin(states)]
        for col in ("sites_served", "sites_out"):
            if not same(rows[col].sum(), float(o[col])):
                fails.append(f"overall {col} {rows[col].sum():.0f} vs printed total {float(o[col]):.0f}")
    for state in g.state.unique():
        found = t[total_states == name_key(state)]
        if found.empty:
            if name_key(state) not in covered:
                fails.append(f"missing state total: {state}")
            continue
        if len(found) > 1:
            fails.append(f"more than one state total: {state}")
            continue
        total, counties = found.iloc[0], g[row_states == name_key(state)]
        cols = ["sites_served", "sites_out"]
        values = pd.concat([counties[CAUSES].stack(), total[CAUSES].dropna()])
        if len(values):  # this state's table has cause columns, so every cell must be there
            if counties[CAUSES].isna().to_numpy().any() or total[CAUSES].isna().any():
                fails.append(f"cause columns incomplete: {state}")
            else:
                cols += CAUSES
        backup = "on_backup_power"
        if counties[backup].notna().any() or pd.notna(total[backup]):
            if counties[backup].isna().any() or pd.isna(total[backup]):
                fails.append(f"backup column incomplete: {state}")
            else:
                cols.append(backup)
        for col in cols:
            if not same(counties[col].sum(), total[col]):
                fails.append(f"{state} {col} {counties[col].sum():.0f} vs printed total {total[col]:.0f}")
    for state in t.state.unique():
        if name_key(state) not in set(row_states):
            fails.append(f"state total with no county rows: {state}")
    return fails


COUNT_COLUMNS = ["sites_served", "sites_out", *CAUSES, "on_backup_power"]


def non_integer_counts(*tables: pd.DataFrame) -> list[str]:
    """Every count that is not a whole number, in county rows and totals (build-stopping; 2026-11-24)."""
    bad = []
    for t in tables:
        for col in [c for c in COUNT_COLUMNS if c in t.columns]:
            v = pd.to_numeric(t[col], errors="coerce")
            for r in t[v.notna() & (v % 1 != 0)].itertuples():
                bad.append(f"{r.doc_id} {getattr(r, 'state', '')}/{getattr(r, 'county', 'TOTAL')} {col} = {getattr(r, col)}")
    return bad


def previous_day_mismatches(rows: pd.DataFrame, reports: pd.DataFrame) -> tuple[list[str], dict]:
    """Two-day reports (prev_sites_out printed): each county's previous-day figures must equal the previous day's
    report of the same storm (sites out exactly, % out within 0.05). Returns (problems, rows checked per report)."""
    if "prev_sites_out" not in rows.columns:
        return [], {}
    problems, checked = [], {}
    for doc, g in rows[rows.prev_sites_out.notna()].groupby("doc_id"):
        day = (pd.Timestamp(g.report_date.iloc[0]) - pd.Timedelta(1, unit="D")).date().isoformat()
        prev_docs = reports[(reports.storm_name == g.storm_name.iloc[0]) & (reports.report_date == day)].doc_id
        if len(prev_docs) != 1:
            problems.append(f"{doc}: {len(prev_docs)} reports on the previous day ({day}); expected 1")
            continue
        p = rows[rows.doc_id == prev_docs.iloc[0]].assign(_k=lambda d: d.state.map(name_key) + "|" + d.county.map(name_key))
        p = p.drop_duplicates("_k").set_index("_k")
        for r in g.itertuples():
            k = f"{name_key(r.state)}|{name_key(r.county)}"
            if k not in p.index:
                problems.append(f"{doc} {r.state}/{r.county}: not in the previous day's report {prev_docs.iloc[0]}")
            elif r.prev_sites_out != p.at[k, "sites_out"] or abs(r.prev_pct_out - p.at[k, "pct_out"]) > 0.05:
                problems.append(f"{doc} {r.state}/{r.county}: previous day {r.prev_sites_out:g} ({r.prev_pct_out:g}%), "
                                f"{prev_docs.iloc[0]} says {p.at[k, 'sites_out']:g} ({p.at[k, 'pct_out']:g}%)")
        checked[doc] = (prev_docs.iloc[0], len(g))
    return problems, checked


def check_row_percent(g: pd.DataFrame) -> list[str]:
    bad = []
    for r in g.itertuples():
        if getattr(r, "pct_printed", True) is False:
            continue
        implied = 100 * r.sites_out / r.sites_served if r.sites_served else 0.0
        if pd.isna(r.pct_out) or abs(r.pct_out - implied) > ROW_PCT_TOLERANCE + 1e-6:
            bad.append(f"{r.state}/{r.county} printed {r.pct_out:g}, implied {implied:.2f}")
    return [f"row % out differs from out / served ({'; '.join(bad)})"] if bad else []


def last_word(name: str) -> str:
    """A name wrapped inside its cell leaves only its last word on the line that holds the numbers."""
    return name_key(name.split()[-1].split("-")[-1])


def check_second_reading(g: pd.DataFrame, lines: pd.DataFrame) -> list[str]:
    """Each row must appear, with the same county and values, on a plain-text line of the PDF."""
    missing = unconfirmed_rows(g, lines)
    return [f"not confirmed by second reading of the PDF: {', '.join(missing)}"] if missing else []


def unconfirmed_rows(g: pd.DataFrame, lines: pd.DataFrame) -> list[str]:
    split = [line.split() for line in lines["line"]]
    missing = []
    for row in g.to_dict("records"):
        skip = {"pct_out"} if row.get("pct_printed", True) is False else set()
        want = [float(row[col]) for col in PRINTED if col not in skip and pd.notna(row[col])]
        if pd.notna(row.get("prev_sites_out")):  # two-day layout: served, previous out and %, today's out and %
            want = [float(row["sites_served"]), float(row["prev_sites_out"]), float(row["prev_pct_out"]),
                    *want[1:]]
        for tokens in split:
            head, tail = tokens[:-len(want)], tokens[-len(want):]
            if not head or not all(NUMBER_RE.fullmatch(tok) for tok in tail):
                continue
            if [float(tok.replace(",", "").replace("%", "")) for tok in tail] != want:
                continue
            if head[0] in CODE_TO_STATE and name_key(CODE_TO_STATE[head[0]]) != name_key(row["state"]):
                continue
            words = {name_key(w) for w in re.split(r"[\s-]+", row["county"]) if w}
            # pdfplumber can split a wrapped name: "PEARL 72 0 0% ..." then "MS RIVER" (Isaias 2026)
            if last_word(head[-1]) == last_word(row["county"]) or name_key(head[-1]) in words:
                break
        else:
            missing.append(f"{row['state']}/{row['county']}")
    return missing


def matching_entry(entries: list[dict], row) -> int | None:
    """Index of the exception entry with this state, county and every printed value."""
    return next((n for n, e in enumerate(entries)
                 if name_key(e["state"]) == name_key(row.state) and name_key(e["county"]) == name_key(row.county)
                 and all(same(e[col], getattr(row, col)) for col in PRINTED)), None)


def match_spellings(parsed: dict, stated: dict, flags: list[str]) -> dict:
    """Re-key list names that are FCC spellings of a table row, and say so."""
    stated = dict(stated)
    for state in {s for s, _ in stated}:
        loose_list = [k for k in stated if k[0] == state and k not in parsed]
        loose_rows = [k for k in parsed if k[0] == state and k not in stated]
        for k in loose_list:
            near = difflib.get_close_matches(k[1], [r[1] for r in loose_rows], 1, SPELLING_CUTOFF)
            if near:
                flags.append(f"FCC spelling: {parsed[(state, near[0])]} listed as {stated[k].split('/', 1)[1]}")
                stated[(state, near[0])] = stated.pop(k)
                loose_rows.remove((state, near[0]))
        loose_list = [k for k in stated if k[0] == state and k not in parsed]
        if len(loose_list) == 1 and len(loose_rows) == 1:
            ratio = difflib.SequenceMatcher(None, loose_list[0][1], loose_rows[0][1]).ratio()
            if ratio >= PAIR_CUTOFF:
                flags.append(f"FCC spelling: {parsed[loose_rows[0]]} listed as {stated[loose_list[0]].split('/', 1)[1]}")
                stated[loose_rows[0]] = stated.pop(loose_list[0])
    return stated


def check_names(g: pd.DataFrame, listed: pd.DataFrame, allowed: pd.DataFrame) -> tuple[list[str], list[str]]:
    if listed.empty:
        return ["no county list found in the report"], []
    parsed = {(name_key(r.state), name_key(r.county)): f"{r.state}/{r.county}" for r in g.itertuples()}
    stated = {(name_key(r.state), name_key(r.county)): f"{r.state}/{r.county}" for r in listed.itertuples()}
    fails, flags = [], []
    stated = match_spellings(parsed, stated, flags)
    entries, used, excused = allowed.to_dict("records"), set(), set()
    for row in g.itertuples():
        key = (name_key(row.state), name_key(row.county))
        match = None if key in stated else matching_entry(entries, row)
        if match is not None:
            used.add(match)
            excused.add(key)
            flags.append(f"in table, not in the report's list, listed exception: {row.state}/{row.county} "
                         f"({row.sites_served:.0f} kept in sites served)")
    for n, entry in enumerate(entries):
        if incomplete(entry):
            fails.append(f"county-list exception for {entry['county']} lacks page or checked_on")
        if n not in used:
            fails.append(f"county-list exception matches no unlisted row: {entry['county']}")
    extra = [parsed[k] for k in sorted(parsed.keys() - stated.keys() - excused)]
    absent = [stated[k] for k in sorted(stated.keys() - parsed.keys())]
    if extra:
        flags.append(f"in table, not in the report's county list: {', '.join(extra)}")
    if absent:
        fails.append(f"county names differ from the report's list (in list, not in table: {', '.join(absent)})")
    counts = Counter((name_key(r.state), name_key(r.county)) for r in listed.itertuples())
    twice = [stated[k] for k, n in counts.items() if n > 1]
    if twice:
        flags.append(f"listed more than once by the FCC: {', '.join(twice)}")
    return fails, flags


def check_causes(g: pd.DataFrame, gap: pd.Series, allowed: pd.DataFrame,
                 unconfirmed: set | None = None) -> tuple[list[str], list[str]]:
    fails, flags = [], []
    short = gap[gap > 0]
    if len(short):
        flags.append(f"{len(short)} rows short of sites out ({short.sum():.0f} sites unattributed)")
    entries, used = allowed.to_dict("records"), set()
    for i in gap[gap < 0].index:
        row = g.loc[i]
        match = matching_entry(entries, row)
        where = f"{row.state}/{row.county} by {-gap[i]:.0f}"
        if match is None and f"{row.state}/{row.county}" not in (unconfirmed or set()):
            flags.append(f"causes exceed sites out, confirmed by second reading: {where}")
        elif match is None:
            fails.append(f"causes exceed sites out: {where}")
        else:
            used.add(match)
            flags.append(f"causes exceed sites out, listed exception: {where}")
    for n, entry in enumerate(entries):
        if incomplete(entry):
            fails.append(f"exception for {entry['county']} lacks page or checked_on")
        if n not in used:
            fails.append(f"exception matches no over-attributed row: {entry['county']}")
    return fails, flags


TOTAL_FAIL_RE = re.compile(r"(?P<state>.+) (?P<col>[a-z_]+) (?P<sum>-?\d+) vs printed total (?P<printed>-?\d+)")


def apply_total_exceptions(fails: list[str], entries: pd.DataFrame, unconfirmed: set) -> tuple[list[str], list[str]]:
    """Total failures matched by a checked entry (state, column, printed total, rows' sum), with every row of that
    state confirmed by the second reading, become known inconsistencies. Returns (failures, known). An entry that
    matches nothing, or lacks its page or check date, fails."""
    kept, known, used = [], [], set()
    rows = entries.to_dict("records")
    for f in fails:
        m = TOTAL_FAIL_RE.fullmatch(f)
        hit = next((i for i, e in enumerate(rows) if m and name_key(e["state"]) == name_key(m["state"])
                    and e["column"] == m["col"] and same(e["rows_sum"], float(m["sum"]))
                    and same(e["printed_total"], float(m["printed"]))), None)
        if hit is None or any(name_key(u.split("/")[0]) == name_key(m["state"]) for u in unconfirmed):
            kept.append(f)
        elif incomplete(rows[hit]):
            kept.append(f"total exception lacks page or checked_on: {f}")
        else:
            used.add(hit)
            known.append(f"{m['state']} {m['col']}: printed total {int(float(m['printed'])):,} vs "
                         f"{int(float(m['sum'])):,} from its rows (checked, every row confirmed)")
    kept += [f"total exception no longer matches: {e['state']} {e['column']} {e['printed_total']}"
             for i, e in enumerate(rows) if i not in used]
    return kept, known


def check_headline(stated, computed, t: pd.DataFrame, known: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Returns (failures, known inconsistencies)."""
    if pd.isna(stated):
        return ["stated % out not found"], []
    if computed is None:
        return [], []  # already failed for having no rows
    if abs(stated - computed) <= PCT_TOLERANCE:
        return (["headline entry not needed: stated and computed % agree"] if len(known) else []), []
    for entry in known.to_dict("records"):
        if (same(entry["stated_pct"], stated) and same(entry["total_served"], t.sites_served.sum())
                and same(entry["total_out"], t.sites_out.sum())):
            if incomplete(entry):
                return ["headline entry lacks page or checked_on"], []
            return [], [f"headline {stated:.1f}% vs {computed:.2f}% from the report's own totals"]
    return [f"overall % out {computed:.2f} vs stated {stated:.2f}"], []


MULTIPLE_CAUSES_RE = re.compile(r"differ from the sum of numbers of cell sites out by cause|multiple causes", re.IGNORECASE)


def has_multiple_causes_note(lines: pd.DataFrame) -> bool:
    """The FCC's note that sites out may differ from the sum of causes, because a site can be out for several
    causes or its cause is still being assessed (Idalia 2023, Beryl 2024)."""
    return bool(MULTIPLE_CAUSES_RE.search(" ".join(" ".join(lines.line).split())))


def report_label(report) -> str:
    try:
        day = pd.to_datetime(report["report_date"])
        return f"{report['storm_name']}, {day:%b} {day.day}, {day.year} ({report['doc_id']})"
    except (ValueError, TypeError):
        return str(report["doc_id"])


def validate(rows, totals, reports, lists, over_allowed, headline_allowed, unlisted_allowed,
             pdf_lines, overall_totals=None, excluded=None, total_allowed=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    excluded = excluded if excluded is not None else pd.DataFrame(columns=["doc_id"])
    results, summary = [], []
    for _, report in reports.iterrows():
        doc = report["doc_id"]
        g = for_report(rows, doc, ["doc_id", "state", "county", *PRINTED]).copy()
        t = for_report(totals, doc, ["doc_id", "state", *PRINTED]).copy()
        listed = for_report(lists, doc, ["doc_id", "state", "county"])
        for col in PRINTED:
            g[col] = pd.to_numeric(g[col]).astype(float)
            t[col] = pd.to_numeric(t[col]).astype(float)

        fails, flags, unconfirmed, known_totals = [], [], set(), []
        total_entries = for_report(total_allowed if total_allowed is not None else pd.DataFrame(), doc, ["doc_id"])
        if g.empty:
            fails.append("zero county rows")
        else:
            if pd.DataFrame({"s": g.state.map(name_key), "c": g.county.map(name_key)}).duplicated().any():
                fails.append("duplicate county rows")
            if (g.sites_out > g.sites_served).any():
                fails.append("out > served")
            try:
                require_carried(g, doc)
            except ValueError as err:
                fails.append(str(err))
            ov = for_report(overall_totals if overall_totals is not None else pd.DataFrame(), doc,
                            ["doc_id", "states", "sites_served", "sites_out"])
            unconfirmed = set(unconfirmed_rows(g, for_report(pdf_lines, doc, ["doc_id", "line"])))
            if t.empty and ov.empty and not unconfirmed:
                flags.append("no_printed_totals: the report prints no totals; every row confirmed by second reading")
                more_fails, known_totals = apply_total_exceptions(
                    [f for f in check_totals(g, t, ov) if not f.startswith("missing state total")], total_entries,
                    unconfirmed)
                fails += more_fails
            else:
                total_fails, known_totals = apply_total_exceptions(check_totals(g, t, ov), total_entries, unconfirmed)
                missing = [f for f in total_fails if f.startswith("missing state total: ")]
                state = missing[0].split(": ", 1)[1] if len(missing) == 1 else None
                confirmed = state and not any(u.startswith(f"{state}/") for u in unconfirmed)
                if confirmed and len(total_fails) == 1:  # every other state reconciles
                    flags.append(f"state_total_missing: {state} (its rows all confirmed; other states reconcile)")
                else:
                    fails += total_fails
            if "area_status" not in g.columns or not g.area_status.isin(AREA_STATUSES).all():
                fails.append("area_status missing or not a known value")
            else:
                counts = g.area_status.value_counts()
                flags += [f"{counts[s]} rows {s}" for s in AREA_STATUSES[1:] if counts.get(s, 0)]
            fails += check_row_percent(g)
            fails += check_second_reading(g, for_report(pdf_lines, doc, ["doc_id", "line"]))
            more_fails, more_flags = check_names(g, listed, for_report(unlisted_allowed, doc, OVER_FIELDS))
            fails += more_fails
            flags += more_flags

        # sites out minus causes, for rows that have all three causes
        gap = (g.sites_out - g[CAUSES].sum(axis=1, skipna=False)).dropna()
        more_fails, more_flags = check_causes(g, gap, for_report(over_allowed, doc, OVER_FIELDS), unconfirmed)
        fails += more_fails
        flags += more_flags

        served = g.sites_served.sum()
        computed = 100 * g.sites_out.sum() / served if served else None
        stated = report["pct_sites_out_stated"]
        more_fails, known = check_headline(stated, computed, t, for_report(headline_allowed, doc, HEADLINE_FIELDS))
        known = known_totals + known
        mismatch = [f for f in more_fails if f.startswith("overall % out")]
        if mismatch and not fails and not unconfirmed:
            flags.append(f"headline_mismatch: stated {stated:.2f}, computed {computed:.2f} (computed used)")
        else:
            fails += more_fails

        status = "fail" if fails else "known_fcc_inconsistency" if known else "flagged" if flags else "ok"
        if doc in set(excluded.doc_id):
            if fails:
                status = "excluded"
            else:
                fails.append("listed as excluded but now passes: remove it from manifest/excluded_reports.csv")
                status = "fail"
        has_causes = len(gap) > 0
        results.append({
            "doc_id": doc, "status": status, "n_rows": len(g),
            "fcc_multiple_causes_note": has_multiple_causes_note(for_report(pdf_lines, doc, ["doc_id", "line"])),
            "computed_pct_out": computed, "stated_pct_out": stated, "pct_out_used": computed,
            "sites_unattributed": gap.clip(lower=0).sum() if has_causes else None,
            "sites_overattributed": (-gap).clip(lower=0).sum() if has_causes else None,
            "failures": "; ".join(fails), "flag_reasons": "; ".join(known + flags),
        })
        counts = ([int((gap == 0).sum()), int((gap == 1).sum()), int((gap > 1).sum()), int((gap < 0).sum()),
                   f"{gap.clip(lower=0).sum():.0f} of {g.sites_out.sum():.0f}"] if has_causes else ["n/a"] * 5)
        summary.append(dict(zip(SUMMARY_COLUMNS, [report_label(report), len(g), *counts])))
    return pd.DataFrame(results), pd.DataFrame(summary, columns=SUMMARY_COLUMNS)


def area_counts(rows: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    """Area status counts per report, and whether the second reading of the PDF confirmed every row."""
    if rows.empty or "area_status" not in rows.columns:
        return pd.DataFrame(columns=["doc_id", *AREA_STATUSES, "confirmed_by_second_reading"])
    counts = rows.groupby("doc_id").area_status.value_counts().unstack(fill_value=0)
    counts = counts.reindex(columns=list(AREA_STATUSES), fill_value=0).reset_index()
    failures = results.set_index("doc_id").failures
    counts["confirmed_by_second_reading"] = ~counts.doc_id.map(failures).fillna("").str.contains("second reading")
    return counts


def main():
    read = {name: pd.read_parquet(INTERIM / f"dirs_{name}.parquet")
            for name in ("county_rows", "state_totals", "reports", "county_lists", "pdf_lines", "overall_totals")}
    if read["reports"].empty:
        print("FAIL: no reports to validate")
        sys.exit(1)
    stop = non_integer_counts(read["county_rows"], read["state_totals"], read["overall_totals"])
    prev_problems, prev_checked = previous_day_mismatches(read["county_rows"], read["reports"])
    stop += prev_problems
    if stop:
        print("FAIL (build stops): non-integer counts or previous-day columns that disagree:\n  " + "\n  ".join(stop))
        sys.exit(1)
    for doc, (prev, n) in prev_checked.items():
        print(f"{doc}: previous-day column matches {prev} for all {n} counties")
    results, summary = validate(read["county_rows"], read["state_totals"], read["reports"], read["county_lists"],
                                pd.read_csv(OVER_EXCEPTIONS), pd.read_csv(HEADLINE_EXCEPTIONS),
                                pd.read_csv(LIST_EXCEPTIONS), read["pdf_lines"], read["overall_totals"],
                                pd.read_csv(EXCLUDED, dtype=str, keep_default_na=False),
                                total_allowed=pd.read_csv(TOTAL_EXCEPTIONS))
    OUTPUT.mkdir(exist_ok=True)
    write_csv(results, OUTPUT / "validation_dirs.csv", ["sites_unattributed", "sites_overattributed"])
    summary.to_csv(OUTPUT / "validation_summary.csv", index=False, lineterminator="\n")  # already whole; "n/a" text
    gone = pd.read_csv(EXCLUDED, dtype=str, keep_default_na=False)  # for the page's methods section
    gone.merge(results[["doc_id", "status", "failures"]], on="doc_id", how="left").to_csv(
        OUTPUT / "excluded_reports.csv", index=False, lineterminator="\n")
    area_counts(read["county_rows"], results).to_csv(OUTPUT / "area_status_counts.csv", index=False,
                                                     lineterminator="\n")
    print(results[["doc_id", "status", "n_rows", "computed_pct_out", "stated_pct_out"]].to_string(index=False))
    for r in results.itertuples():
        for label, text in (("FAIL", r.failures), ("flag", r.flag_reasons)):
            if text:
                print(f"  {label} {r.doc_id}: {text}")
    sys.exit(1 if (results.status == "fail").any() else 0)


if __name__ == "__main__":
    main()
