"""Step 16 (v3.2.0; addendum 4.x-1, item 2): the FEMA Individual Assistance table, per storm and county.

From OpenFEMA, for each major-disaster (DR) number our storms' declared counties carry:
  RI-IHP v2 (RegistrationIntakeIndividualsHouseholdPrograms): valid registrations, IHP referrals, eligible and amount;
  Housing Assistance Program Data - Renters v2 (HousingAssistanceRenters): valid registrations, inspected, approved.
Rows are by state, county, city and zip code; counties are matched to FIPS through the same disaster's declaration
records (designatedArea and fipsCountyCode in Disaster Declarations Summaries v2, already in data/raw/fema). Rows
from outside the disaster's states, 'Statewide' rows and tribal areas are set aside and counted in
output/fema_ia_set_aside.csv; any other unmatched county stops the build. Summed per storm and county over the storm's disaster numbers.
A storm-county with no IA declared (neither iaProgramDeclared nor ihProgramDeclared) is blank; declared with no record
is 0.

  python src/16_fema_ia.py --download   # one request per dataset and disaster (approved 2026-11-25), logged
  python src/16_fema_ia.py              # build processed/fema_ia_county_storm.csv from the stored responses

This product uses the Federal Emergency Management Agency's OpenFEMA API, but is not endorsed by FEMA. The Federal
Government or FEMA cannot vouch for the data or analyses derived from these data after the data have been retrieved
from the Agency's website(s).
"""
import json
import re
import sys
from urllib.parse import quote

import pandas as pd

import download_util
from config import DOWNLOADS_LOG, OUTPUT, PROCESSED, RAW
from tables import write_csv

BASE = "https://www.fema.gov/api/open/v2/"
DATASETS = {  # endpoint: (fields summed, renamed)
    "RegistrationIntakeIndividualsHouseholdPrograms": {
        "totalValidRegistrations": "ihp_valid_registrations", "ihpReferrals": "ihp_referrals",
        "ihpEligible": "ihp_eligible", "ihpAmount": "ihp_amount_usd"},
    "HousingAssistanceRenters": {
        "validRegistrations": "renters_valid_registrations", "totalInspected": "renters_inspected",
        "approvedForFemaAssistance": "renters_approved"},
}
OUT_DIR = RAW / "fema_ia"
OUT = PROCESSED / "fema_ia_county_storm.csv"
ASIDE = OUTPUT / "fema_ia_set_aside.csv"
TOP = 10000
COUNTS = [c for d in DATASETS.values() for c in d.values() if not c.endswith("_usd")]


def ia_disasters(panel: pd.DataFrame) -> list[int]:
    """The DR numbers (IA is only under major-disaster declarations) of storm-counties with IA or IHP declared."""
    d = panel.drop_duplicates(["storm_key", "fips"])
    d = d[d.fema_ia.eq(True) | d.fema_ih.eq(True)]
    nums = {int(n) for v in d.fema_disasters.dropna() for n in str(v).split("; ") if n}
    return sorted(n for n in nums if n >= 4000)


def job(endpoint: str, number: int) -> dict:
    q = {"$filter": f"disasterNumber eq {number}", "$top": str(TOP), "$inlinecount": "allpages"}
    url = BASE + endpoint + "?" + "&".join(f"{quote(k)}={quote(v)}" for k, v in q.items())
    dest = OUT_DIR / f"{endpoint}_{number}.json"
    return {"url": url, "dest": dest, "logged_path": f"data/raw/fema_ia/{dest.name}", "doc_id": dest.name,
            "kind": "openfema_ia"}


def download(numbers: list[int]) -> None:
    jobs = [job(e, n) for e in DATASETS for n in numbers]
    download_util.run(jobs, DOWNLOADS_LOG, allowed=tuple(BASE + e + "?" for e in DATASETS))


def read(endpoint: str, number: int) -> pd.DataFrame:
    d = json.loads(job(endpoint, number)["dest"].read_text(encoding="utf-8"))
    rows = d[endpoint]
    if int(d["metadata"]["count"]) != len(rows):
        raise SystemExit(f"{endpoint} {number}: {len(rows)} rows read, the API counts {d['metadata']['count']}")
    return pd.DataFrame(rows, columns=["disasterNumber", "state", "county", *DATASETS[endpoint]])


def county_fips(decl: pd.DataFrame) -> pd.DataFrame:
    """(disaster, state, county name as OpenFEMA prints it) -> FIPS, from the declaration records."""
    d = decl[decl.fipsCountyCode != "000"]
    return (d.assign(fips=d.fipsStateCode.str.zfill(2) + d.fipsCountyCode.str.zfill(3))
            [["disasterNumber", "state", "designatedArea", "fips"]].drop_duplicates()
            .rename(columns={"designatedArea": "county"}))


TRIBAL = r"\b(Tribe|Tribal|Nation|Band|Reservation|Indians?|Pueblo|Rancheria)\b"


def set_aside_reason(disaster: int, state: str, county: str, fips, dstates: dict) -> str:
    """Rows kept out of the county table (deviation of 2026-11-25), counted in the set-aside summary instead:
    an address outside the disaster's declared states; 'Statewide'; a tribal area (it spans counties, and no single
    county is assigned). Any other unmatched name stops the build."""
    if isinstance(fips, str):
        return ""
    if state not in dstates.get(disaster, set()):
        return "outside the disaster's states"
    if county == "Statewide":
        return "statewide"
    if re.search(TRIBAL, county):
        return "tribal area"
    return ""


def build(panel: pd.DataFrame, decl: pd.DataFrame, numbers: list[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = county_fips(decl)
    dstates = decl.groupby("disasterNumber").state.agg(set).to_dict()
    parts, aside = [], []
    for endpoint, fields in DATASETS.items():
        raw = pd.concat([read(endpoint, n) for n in numbers], ignore_index=True)
        m = raw.merge(keys, on=["disasterNumber", "state", "county"], how="left")
        m["set_aside"] = [set_aside_reason(d, st, c, f, dstates) for d, st, c, f in
                          zip(m.disasterNumber, m.state, m.county, m.fips)]
        bad = m[m.fips.isna() & m.set_aside.eq("")][["disasterNumber", "state", "county"]].drop_duplicates()
        if len(bad):
            raise SystemExit(f"{endpoint}: {len(bad)} county names not in the declarations, e.g. {bad.head(5).values.tolist()}")
        first = list(fields)[0]
        aside.append(m[m.set_aside != ""].groupby(["disasterNumber", "state", "county", "set_aside"])[first].sum()
                     .rename("valid_registrations").reset_index().assign(dataset=endpoint))
        m = m[m.set_aside == ""]
        parts.append(m.groupby(["disasterNumber", "fips"])[list(fields)].sum().rename(columns=fields))
    by_disaster = pd.concat(parts, axis=1).fillna(0).reset_index()
    sc = panel.drop_duplicates(["storm_key", "fips"])[["storm_key", "storm", "fips", "fema_ia", "fema_ih", "fema_disasters"]]
    rows = []
    for s in sc.itertuples():
        declared = bool(s.fema_ia) or bool(s.fema_ih)
        nums = [int(n) for n in str(s.fema_disasters).split("; ") if n.isdigit() and int(n) >= 4000]
        vals = by_disaster[by_disaster.fips.eq(s.fips) & by_disaster.disasterNumber.isin(nums)]
        rec = {"storm_key": s.storm_key, "storm": s.storm, "fips": s.fips, "ia_declared": declared,
               "fema_disasters_ia": "; ".join(str(n) for n in nums) if declared else ""}
        for c in [*COUNTS, "ihp_amount_usd"]:
            rec[c] = float(vals[c].sum()) if declared else None
        rows.append(rec)
    out = pd.DataFrame(rows).sort_values(["storm_key", "fips"], ignore_index=True)
    aside = pd.concat(aside, ignore_index=True)
    return out, aside[["dataset", "disasterNumber", "state", "county", "set_aside", "valid_registrations"]]


def main():
    panel = pd.read_parquet(PROCESSED / "panel.parquet")
    numbers = ia_disasters(panel)
    if "--download" in sys.argv:
        download(numbers)
        return
    decl = pd.concat([pd.DataFrame(json.loads(p.read_text(encoding="utf-8"))["DisasterDeclarationsSummaries"])
                      for p in sorted((RAW / "fema").glob("declarations_*.json"))], ignore_index=True)
    out, aside = build(panel, decl, numbers)
    write_csv(out, OUT, counts=COUNTS)
    write_csv(aside, ASIDE, counts=["valid_registrations"])
    print(f"fema_ia_county_storm: {len(out):,} storm-counties, {int(out.ia_declared.sum())} with IA declared, "
          f"{len(numbers)} disasters")


if __name__ == "__main__":
    main()
