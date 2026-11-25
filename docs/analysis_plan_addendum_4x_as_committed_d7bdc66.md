# Analysis plan addendum 4.x-1

**Exploratory: added after the earlier results were published.** Written and committed 2026-11-25, before any of the
quantities below is computed and before any NCEI or OpenFEMA file is downloaded. It covers version 3.2.0 of the data
repository: new tables that no existing result reads. Results from it are exploratory, and the page labels them so.
Any change after this commit is logged in `docs/decisions.md` as a deviation, with its reason, before it is run.

## What has been seen before this addendum

- Step 3 already parses the cable and wireline figure for the whole disaster area: 143 of the 178 in-scope reports
  (`dirs_reports.parquet`, column `cable_wireline_subs_out`, published as the "Cable and wireline subscribers out
  (report area)" column of the peak table). Michael's state rows (AL, FL, GA) are not parsed by it.
- Two values were read by hand in spot checks of the scoping (2026-11-25): Helene, 2024-10-04 (DOC-406197A1): 342,375
  subscribers out; Beryl, 2024-07-13 (DOC-403935A1): 471,792, with the previous-day figure 497,793 (and step 3's
  2024-07-12 value is 497,793).
- The Helene cause comparison with Olukola et al. (2026) is already published (chapter 4's external check), and their
  Helene peak (4,562 sites out, 28 Sep 2024) and sites served (37,717) were set beside ours in the scoping and match
  exactly.
- The FCC's Michael report (DOC-357387A1) was read for its figures (M1 to M8 in `docs/scoping_4x.md`); none was
  compared with our panel.
- No per-storm summary, maximum or county table of cable and wireline subscribers, Individual Assistance or hazard has
  been computed.
- Nothing from NCEI Storm Events or OpenFEMA Individual Assistance has been read for our storms (only their format
  documents, field definitions, file listings and refresh dates).

## 1. Cable and wireline subscribers out

For each in-scope report, the printed figure for the whole disaster area, or each state where the report prints state
rows (Michael, and the Ida and Ian reports that add state figures), read with the existing rule (text file first, the
PDF when it recovers more). Checks: every figure is a whole number; where the report prints a previous-day figure
("up/down from N yesterday"), it must equal the previous report's printed figure for the same area, or the report is
flagged (never corrected). Reported per storm: the figure at each report, its largest value and the report it occurred
in, and the figure at the storm's last report. No allocation to counties, and no comparison with cell sites beyond
showing both per report. Excluded reports keep their figure, flagged as from an excluded report.

## 2. Individual Assistance

Per storm and county in the panel: IA declared (`iaProgramDeclared` or `ihProgramDeclared` in Disaster Declarations
Summaries v2), and from RI-IHP v2 the valid registrations, IHP referrals, IHP eligible and IHP amount, and from Housing
Assistance Renters v2 the valid registrations, inspected and approved counts, summed over the storm's disaster numbers
in the county. A storm-county with no IA declared is blank; declared with no record is 0. Counties are matched by name
with the existing crosswalk and exception table; an unmatched name stops the build. Retrieval times and endpoint
versions are recorded, with the OpenFEMA statement. A descriptive table only.

## 3. Hazard (NCEI Storm Events)

Per storm and county in the panel, from the NCEI Storm Events details files: `surge_flag` (any Storm Surge/Tide event),
`flood_flag` (Flood or Flash Flood), `wind_flag` (Hurricane (Typhoon), Tropical Storm or High Wind), the sums of
`damage_property` and `damage_crops` over those events (zone events' damage is not divided among counties and is
flagged `damage_from_zone`), and the episode ids used. Window: the storm's DIRS activation date minus 2 days to its last
report plus 2 days. Zone events are mapped to counties with the NWS zone-to-county file in force on the event date. No
high-water marks (both USGS sources refused; to be revisited in 4.x). A descriptive table only.

## 4. External checks

The FCC Michael report's figures M1 to M8 are compared with the matching report, by the rule used for the 2017 season
report (`src/15_external_validation.py`: a figure matches when ours, rounded half up to the FCC's printed decimals,
equals it; every other status needs a written explanation). The Olukola et al. rows are the four in the scoping
document. Neither changes any data without asking.

## Not in this addendum

Any association between these tables and cell outages, and any change to EAGLE-I coverage or denominators. Each needs
its own addendum, committed before it is run, and is a 4.0.0 change.
