"""Step 18 (v3.2.0; addendum 4.x-1, item 3): the NCEI hazard columns, per storm and county in the panel.

From the NOAA NCEI Storm Events details files (NCEI_RAW_DIR, default data/raw/ncei; 2017-2026, c20261119): for each storm, the events whose
begin date falls in its window (DIRS activation date minus 2 days to its last report plus 2 days), by type:
  surge_flag  Storm Surge/Tide
  flood_flag  Flood or Flash Flood
  wind_flag   Hurricane (Typhoon), Tropical Storm or High Wind
with the episode ids used. Damage (deviation of 2026-11-25, made after seeing a value): damage_property_usd and
damage_crops_usd sum the county (C) events only; zone (Z) events' damage goes in zone_damage_property_usd_unallocated
and zone_damage_crops_usd_unallocated, each event's whole figure, with zone_n_counties, the counties those zones cover.
The zone columns must never be summed across counties: the same dollars appear in every county of the zone. County events (CZ_TYPE
C) carry the county FIPS; zone events (Z) are mapped to counties with the NWS zone-to-county file bp16ap26.dbx for every
storm (deviation of 2026-11-25: earlier versions are not published). A zone event whose state and zone are not in the file is
left unmapped and counted per storm, and so is a mapped zone event whose NCEI zone name (without position words such
as Inland or Coastal) names none of the counties the file gives that zone (a renumbered zone) (output/hazard_ncei_storm_summary.csv). No high-water marks (both USGS sources
refused). A descriptive table only: no result reads it.

  python src/18_hazard_ncei.py   # writes processed/hazard_ncei_county_storm.csv and output/hazard_ncei_storm_summary.csv
"""
import re
from decimal import Decimal

import pandas as pd

from config import NCEI_RAW_DIR, OUTPUT, PROCESSED, RAW
from tables import write_csv

NCEI = sorted(NCEI_RAW_DIR.glob("StormEvents_details-ftp_v1.0_d20*_c20261119.csv.gz"))
ZONES = RAW / "nws" / "bp16ap26.dbx"
WINDOW_DAYS = 2
TYPES = {"surge_flag": ["Storm Surge/Tide"], "flood_flag": ["Flood", "Flash Flood"],
         "wind_flag": ["Hurricane (Typhoon)", "Tropical Storm", "High Wind"]}
USE = ["EPISODE_ID", "EVENT_ID", "STATE", "STATE_FIPS", "EVENT_TYPE", "CZ_TYPE", "CZ_FIPS", "CZ_NAME", "BEGIN_YEARMONTH",
       "BEGIN_DAY", "DAMAGE_PROPERTY", "DAMAGE_CROPS"]
OUT = PROCESSED / "hazard_ncei_county_storm.csv"
SUMMARY = OUTPUT / "hazard_ncei_storm_summary.csv"


def damage_usd(text) -> float:
    """NCEI's damage strings: '10.00K' = $10,000, '1.5M' = $1,500,000, '2B' = $2 billion; blank = 0."""
    if pd.isna(text) or str(text).strip() == "":
        return 0.0
    s = str(text).strip().upper()
    mult = {"K": 1000, "M": 10 ** 6, "B": 10 ** 9}.get(s[-1], 1)
    exact = Decimal(s[:-1] if s[-1] in "KMB" else s) * mult  # exact: '0.15K' is 150, not 150.00000000000003
    if exact != exact.to_integral_value():
        raise SystemExit(f"NCEI damage {text!r} is not a whole number of dollars")
    return float(exact)


def read_events() -> pd.DataFrame:
    keep = [t for v in TYPES.values() for t in v]
    parts = [pd.read_csv(p, usecols=USE, compression="gzip", dtype={"CZ_FIPS": int, "STATE_FIPS": int}) for p in NCEI]
    e = pd.concat(parts, ignore_index=True)
    e = e[e.EVENT_TYPE.isin(keep) & e.CZ_TYPE.isin(["C", "Z"])].copy()
    e["begin_date"] = pd.to_datetime(e.BEGIN_YEARMONTH.astype(str) + e.BEGIN_DAY.astype(str).str.zfill(2), format="%Y%m%d")
    e["damage_property_usd"] = e.DAMAGE_PROPERTY.map(damage_usd)
    e["damage_crops_usd"] = e.DAMAGE_CROPS.map(damage_usd)
    return e


def read_zones() -> pd.DataFrame:
    z = pd.read_csv(ZONES, sep="|", header=None, dtype=str,
                    names=["STATE", "ZONE", "CWA", "NAME", "STATE_ZONE", "COUNTY", "FIPS", "TIME_ZONE", "FE_AREA",
                           "LAT", "LON"])
    return z[["STATE_ZONE", "COUNTY", "FIPS"]].drop_duplicates()


def norm_name(text) -> str:
    """Zone names compared without case, punctuation or a trailing 'County'/'Parish' (NCEI: 'LOWER JEFFERSON
    COUNTY'; zone file: 'Lower Jefferson')."""
    s = re.sub(r"[^A-Z ]", " ", str(text).upper())
    # bare compass words are kept: they are part of names such as East Baton Rouge
    s = re.sub(r"\b(COUNTY|PARISH|COUNTIES|PARISHES|CITY|OF|INCLUDING|THE|INLAND|COASTAL|MAINLAND|NORTHERN|SOUTHERN|"
               r"EASTERN|WESTERN|CENTRAL|UPPER|LOWER|NORTHEASTERN|NORTHWESTERN|SOUTHEASTERN|SOUTHWESTERN|INTERIOR|"
               r"BARRIER|ISLANDS?|BEACHES|MOUNTAINS)\b",
               " ", s)
    return " ".join(s.split())


def zone_names_agree(ncei: str, county: str) -> bool:
    """An NCEI zone name names this county: compared after norm_name and without spaces ('DE SOTO' = 'DeSoto',
    'INLAND PASCO' = 'Pasco', 'MONROE/LOWER KEYS' = 'Monroe'). Zones named for places ('OCRACOKE ISLAND') and misspelt
    names ('SAN PATRICO') do not agree: such events are set aside and counted, never guessed."""
    a, b = norm_name(ncei).replace(" ", ""), norm_name(county).replace(" ", "")
    return a != "" and b != "" and (b in a or a in b)


def state_abbr(zones_raw: pd.DataFrame) -> dict:
    """State FIPS -> postal abbreviation, from the zone file itself (its FIPS and STATE columns)."""
    z = pd.read_csv(ZONES, sep="|", header=None, dtype=str, usecols=[0, 6], names=["STATE", "FIPS"])
    z = z[z.FIPS.str.fullmatch(r"\d{5}")]
    return dict(zip(z.FIPS.str[:2].astype(int), z.STATE))


def map_counties(e: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(events with a county FIPS per row, zone events not found in the zone file)."""
    zones = read_zones()
    abbr = state_abbr(zones)
    c = e[e.CZ_TYPE == "C"].assign(fips=lambda d: d.STATE_FIPS.astype(str).str.zfill(2)
                                   + d.CZ_FIPS.astype(str).str.zfill(3), from_zone=False)
    z = e[e.CZ_TYPE == "Z"].assign(STATE_ZONE=lambda d: d.STATE_FIPS.map(abbr).fillna("??")
                                   + d.CZ_FIPS.astype(str).str.zfill(3))
    zm = z.merge(zones, on="STATE_ZONE", how="left")
    unmapped = zm[zm.FIPS.isna()].drop_duplicates("EVENT_ID")
    zm = zm[zm.FIPS.notna()].rename(columns={"FIPS": "fips"}).assign(from_zone=True)
    # a zone renumbered since the event would map to the wrong counties: the event is kept only when its NCEI zone
    # name (without position words such as Inland or Coastal) names one of the counties the file gives that zone
    zm["row_ok"] = [zone_names_agree(n, c) for n, c in zip(zm.CZ_NAME, zm.COUNTY)]
    zm["name_ok"] = zm.groupby("EVENT_ID").row_ok.transform("any")
    mismatched = zm[~zm.name_ok].drop_duplicates("EVENT_ID")
    zm = zm[zm.name_ok]
    unmapped = pd.concat([unmapped.assign(reason="zone not in file"), mismatched.assign(reason="zone name differs")])
    return pd.concat([c, zm.drop(columns=["STATE_ZONE", "COUNTY", "row_ok", "name_ok"])], ignore_index=True), unmapped


def table(panel: pd.DataFrame, storms: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    events, unmapped = map_counties(read_events())
    zone_counties = events[events.from_zone.astype(bool)][["EVENT_ID", "fips"]].drop_duplicates()
    sc = panel.drop_duplicates(["storm_key", "fips"])[["storm_key", "storm", "fips"]]
    rows, summary = [], []
    for s in storms[storms.in_panel.eq("True")].itertuples():
        start = pd.Timestamp(s.dirs_activation_date) - pd.Timedelta(f"{WINDOW_DAYS}D")
        end = pd.Timestamp(s.last_report) + pd.Timedelta(f"{WINDOW_DAYS}D")
        counties = sc[sc.storm_key == s.storm_key]
        ev = events[events.begin_date.between(start, end) & events.fips.isin(counties.fips)]
        states = set(counties.fips.str[:2].astype(int))  # only the storm's own states count as misses
        un = unmapped[unmapped.begin_date.between(start, end) & unmapped.STATE_FIPS.isin(states)]
        summary.append({"storm_key": s.storm_key, "storm": s.storm, "window_start": start.date().isoformat(),
                        "window_end": end.date().isoformat(), "events_used": int(ev.EVENT_ID.nunique()),
                        "zone_events_unmapped": int(un[un.reason == "zone not in file"].EVENT_ID.nunique()),
                        "zone_events_name_differs": int(un[un.reason == "zone name differs"].EVENT_ID.nunique())})
        for f in counties.fips:
            g = ev[ev.fips == f]
            rec = {"storm_key": s.storm_key, "storm": s.storm, "fips": f}
            for flag, types in TYPES.items():
                rec[flag] = bool(g.EVENT_TYPE.isin(types).any())
            g1 = g.drop_duplicates("EVENT_ID")
            county_ev, zone_ev = g1[~g1.from_zone.astype(bool)], g1[g1.from_zone.astype(bool)]
            # damage: county (C) events only (deviation of 2026-11-25, made after seeing Ian's Charlotte County)
            rec["damage_property_usd"] = float(county_ev.damage_property_usd.sum())
            rec["damage_crops_usd"] = float(county_ev.damage_crops_usd.sum())
            # zone events' damage, each event's whole figure, not divided among its counties: never sum it across
            # counties (the same dollars appear in every county of the zone)
            rec["zone_damage_property_usd_unallocated"] = float(zone_ev.damage_property_usd.sum())
            rec["zone_damage_crops_usd_unallocated"] = float(zone_ev.damage_crops_usd.sum())
            rec["zone_n_counties"] = int(zone_counties[zone_counties.EVENT_ID.isin(zone_ev.EVENT_ID)].fips.nunique())
            rec["n_events"] = int(g1.EVENT_ID.nunique())
            rec["ncei_episode_ids"] = "; ".join(str(x) for x in sorted(g1.EPISODE_ID.unique()))
            rows.append(rec)
    return pd.DataFrame(rows), pd.DataFrame(summary)


def main():
    if len(NCEI) != 10:  # 2017-2026; in the public repository they are not included (terms not yet confirmed)
        print(f"step 18 skipped: {len(NCEI)} of the 10 NCEI details files in {NCEI_RAW_DIR.name}/ (not redistributed; "
              "download them from https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/ and set NCEI_RAW_DIR)")
        return
    panel = pd.read_parquet(PROCESSED / "panel.parquet")
    storms = pd.read_csv(PROCESSED / "storms.csv", dtype=str)
    out, summary = table(panel, storms)
    write_csv(out, OUT, counts=["n_events", "damage_property_usd", "damage_crops_usd", "zone_n_counties",
                              "zone_damage_property_usd_unallocated", "zone_damage_crops_usd_unallocated"])  # NCEI damage is whole dollars
    write_csv(summary, SUMMARY, counts=["events_used", "zone_events_unmapped", "zone_events_name_differs"])
    print(f"hazard_ncei_county_storm: {len(out):,} storm-counties; zone events unmapped: "
          f"{int(summary.zone_events_unmapped.sum())}; zone name differs: {int(summary.zone_events_name_differs.sum())}")


if __name__ == "__main__":
    main()
