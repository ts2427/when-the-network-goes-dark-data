# Scoping: the next data additions (4.x)

Written 2026-11-25 on branch `scope-4x`. Scoping only: nothing here is built, computed or released, and no published
number changes. Every source below was checked on 2026-11-25 by reading it (agents' reads are quoted with their URLs
in the session log). Sites that refused automated requests were not retried or worked around; they are listed under
"Not verified". No outcome was computed: the checks below are of what the sources contain and how they are laid out.

## Summary

| # | Source | What it adds | Limitation it addresses | Licence (as stated) | Redistribution | Identifier and version | Effort | Recommend |
|---|---|---|---|---|---|---|---|---|
| A1 | DIRS reports already in `data/input`: cable and wireline subscribers out | Subscribers out of service, per report, mostly for the whole disaster area (Michael 2018: by state) | The panel is cell sites only | FCC, U.S. government work (the reports are already redistributed) | Redistribute (derived table; inputs already published) | FCC DOC numbers per report (`manifest/dirs_reports.csv`) | Small (area totals: 143 of 178 already parsed); medium with the Michael state tables | Yes, 3.2.0 |
| A2 | DIRS reports: 911 / PSAP status | Named PSAPs by state, with re-route and ALI status, in most storms; counts only in some | Cell sites are not 911 | As A1 | Redistribute (derived) | As A1 | Large (free text; PSAP names, not counties; wording changes by year) | Later, after A1 |
| A3 | DIRS reports: broadcast status | TV, FM and AM stations out, for the whole area (some reports by state, with call signs) | Not covered now | As A1 | Redistribute (derived) | As A1 | Medium | No (low value for this study) |
| B1 | EAGLE-I yearly releases on OSTI/ORNL: 2023, 2024, 2025 | The same county outage series by year; the 2023 release says it includes each state's coverage for each year; the 2024 release describes total customers per county | Coverage gaps (2017, 2023, 2024 county-reports) | **No licence stated** on any of the three landing pages | Derived only, and only after the licence is clarified (our current EAGLE-I source, figshare v4, is CC BY 4.0) | 10.13139/OLCF/2297398 (2023, released 2024-02-12); 10.13139/OLCF/2500278 (2024, released 2025-04-03); 10.13139/ORNLNCCS/3012826 (2025, released 2026-02-19); no version numbers shown | Medium | Only the coverage table, and only as 4.0.0 |
| B2 | EAGLE-I County Customer Dataset Fall 2025 | County electric customer counts marked modeled, collected or mixed | Our denominator (MCC.csv) is below observed outages in some counties | **No licence stated** | Derived only, after the licence is clarified | 10.13139/ORNLNCCS/3022751 (OSTI 3022751; published 2026-05-06); no version shown | Small to medium | 4.0.0 at most, as a sensitivity first |
| C1 | NOAA NCEI Storm Events (bulk CSVs) | Event records with type, damage (property, crops), episode narrative; hurricane and surge events by NWS zone, floods by county | No measure of flooding, surge or damage | No licence or use statement found (not assumed public domain) | Derived only (county-storm flags and sums) until the terms are confirmed | `StormEvents_details-ftp_v1.0_d{YEAR}_c20261119.csv.gz`, 2017 to 2026 present (2026 may be incomplete); zones to counties: NWS `bp16ap26.dbx` | Medium | Yes, 3.2.0 (context table) |
| C2 | USGS high-water marks: STN (unverified, refused) or, if found, USGS data releases on ScienceBase (proposed) | Surveyed flood heights by site, per storm | No measured flood height | **Not verified**: STN refused (HTTP 403, automated and in Tim's browser); the ScienceBase catalog search refused too (HTTP 403) | To decide after a release and its terms are read | None found (no DOI known) | Medium | Proposed source: a ScienceBase data release with a DOI, if one can be reached |
| D | OpenFEMA Individual Assistance: RI-IHP v2 and Housing Assistance Program Data, Renters v2 | Valid registrations, referrals and amounts by county (and city, zip) per disaster | No measure of household impact | OpenFEMA Terms and Conditions (citation required; dataset licence field is empty) | Redistribute derived county counts with the required statement | API `v2/RegistrationIntakeIndividualsHouseholdPrograms` and `v2/HousingAssistanceRenters`, both version 2, last refresh 2026-11-25T06:51:46Z (daily) | Small to medium | Yes, 3.2.0 (context table) |
| E1 | Olukola et al. (2026), arXiv:2609.10944 | An independent Helene decomposition | External check | Paper: CC BY-NC-ND 4.0; dataset: not yet released ("will be deposited ... under a CC-BY-4.0 licence, with a citable DOI, on acceptance", as summarised from the paper) | Link only; compare, never merge | arXiv:2609.10944 v1 (10 Sep 2026) | Small | Yes, as a check (already partly done in chapter 4) |
| E2 | FCC PSHSB, "October 2018 Hurricane Michael's Impact on Communications: Preparation, Effect, and Recovery" (May 2019, PS Docket 18-339) | The FCC's own Michael figures | External check (like the 2017 report) | U.S. government work (FCC); no licence statement in it | Stored in `data/raw/rules/` with its hash, as DOC-353805A1; would be redistributed in `data/input/rules/` | DOC-357387A1 (DOC number from Tim, 2026-11-25); SHA-256 fbebdd7b93f1fd6ebfb795d380192c6d3a023542c86a195995a782d4413a17d3 | Small (a handful of text figures; the charts are images) | Yes, as a check (3.2.0) |

## A. The unused sections of the DIRS reports

Read from every in-scope report (text file where valid, and the PDF) with a structure-only sweep. Fiona's two reports
are out of scope (Puerto Rico) and left out; Nicholas shares Ida's reports.

| Storm (FCC report name) | Year | Reports | 911 section | 911 level | ALI / location categories | Cable+wireline section | Cable+wireline level | Area total parsed by step 3 | Previous-day figure printed | Switching centers | Broadcast section |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Harvey | 2017 | 11 | 11/11 | PSAPs named, by state | yes | 11/11 | disaster area | 11/11 | 9/11 | yes | 11/11 |
| Irma | 2017 | 12 | 12/12 | PSAPs named, by state | yes | 12/12 | disaster area | 8/12 | 7/12 | yes | 12/12 |
| Nate | 2017 | 1 | 1/1 | count only | no | 1/1 | disaster area | 1/1 | 0/1 | no | 1/1 |
| Florence | 2018 | 11 | 11/11 | PSAPs named, by state | yes | 11/11 | disaster area | 5/11 | 0/11 | no | 11/11 |
| Michael | 2018 | 16 | 16/16 | PSAPs named, by state | yes | 16/16 | state table (AL, FL, GA) | 8/16 | 8/16 | no | 16/16 |
| Barry | 2019 | 2 | 2/2 | count only | no | 2/2 | disaster area | 0/2 | 0/2 | no | 2/2 |
| Dorian | 2019 | 6 | 5/6 | count only | yes | 5/6 | disaster area | 2/6 | 1/6 | no | 5/6 |
| Laura | 2020 | 15 | 15/15 | PSAPs named, by state | yes | 15/15 | disaster area | 15/15 | 2/15 | no | 15/15 |
| Sally | 2020 | 7 | 7/7 | section only | yes | 7/7 | disaster area | 7/7 | 0/7 | no | 7/7 |
| Delta | 2020 | 5 | 5/5 | count only | yes | 5/5 | disaster area | 4/5 | 0/5 | no | 5/5 |
| Zeta | 2020 | 4 | 4/4 | count only | yes | 4/4 | disaster area | 3/4 | 0/4 | no | 4/4 |
| Ida | 2021 | 22 | 22/22 | PSAPs named, by state | yes | 22/22 | disaster area; state figures in 7 reports (Mississippi, Texas) | 15/22 | 2/22 | no | 22/22 |
| Ian | 2022 | 13 | 13/13 | PSAPs named, by state | yes | 13/13 | disaster area; state figures in 2 reports (Florida, South Carolina) | 11/13 | 0/13 | no | 13/13 |
| Nicole | 2022 | 2 | 2/2 | PSAPs named, by state | no | 2/2 | disaster area | 2/2 | 1/2 | no | 2/2 |
| Idalia | 2023 | 6 | 6/6 | PSAPs named, by state | yes | 6/6 | disaster area | 6/6 | 0/6 | no | 6/6 |
| Beryl | 2024 | 6 | 6/6 | PSAPs named, by state | yes | 6/6 | disaster area | 6/6 | 4/6 | no | 6/6 |
| Debby | 2024 | 5 | 5/5 | PSAPs named, by state | no | 5/5 | disaster area | 5/5 | 1/5 | no | 5/5 |
| Francine | 2024 | 3 | 3/3 | PSAPs named, by state | no | 3/3 | disaster area | 3/3 | 1/3 | no | 3/3 |
| Helene | 2024 | 24 | 24/24 | PSAPs named, by state | yes | 24/24 | disaster area | 24/24 | 17/24 | no | 24/24 |
| Milton | 2024 | 5 | 5/5 | PSAPs named, by state | yes | 5/5 | disaster area | 5/5 | 4/5 | no | 5/5 |
| Isaias | 2026 | 3 | 3/3 | count only | no | 3/3 | disaster area | 2/3 | 2/3 | no | 3/3 |

How the sweep classified them, and its limits: "PSAPs named" means the 911 section names PSAPs under a state; "count
only" means it states a number (often "no PSAPs"); "section only" means the heading is there with neither (Sally). The
cable and wireline level comes from whether the section prints figures next to state or county names. The columns are
pattern matches over free text, so a parser would confirm each one; the counts of area totals come from step 3's own
parsed field (`cable_wireline_subs_out`).

**Levels.** No section is at county level in any report. Cable and wireline is a single figure for the whole disaster
area in every storm except Michael (a table by state: AL, FL, GA, which step 3 does not read; it parses 8 of Michael's
16 totals) and a few Ida and Ian reports that add state figures. 911 is at the level of individual PSAPs (named, by
state), not counties: a PSAP name ("Matagorda County Sheriff's Office") can usually be placed in a county, but not by a
rule we can check against the FCC's own county list. Broadcast is by station (call signs) for the area, sometimes by
state (Helene). Harvey and Irma (2017) also print switching centers out and on backup power.

**Can they be parsed with our checks?**
- Printed totals: the cable and wireline figure is a single printed number (no rows to add up), so there is nothing to
  reconcile. Michael prints state rows; in the report read (DOC-354533A1, 2018-10-13) no total line follows them, so
  there is nothing to check them against (the other 15 Michael reports are not yet read for this). 911 and broadcast print counts that could be checked against the listed names (for example, "16 PSAPs
  affected" against the names that follow).
- Previous-day match: yes for cable and wireline where the report prints "up/down from N yesterday" (from 0 to 17 of a
  storm's reports, table above); the check is the same as the cell-site one, against the previous report's printed
  figure. Beryl, below, passes it.
- County names: does not apply (no county-level figures). PSAP names would need a hand-made PSAP-to-county table.

**Spot checks against the PDFs (by hand, 2026-11-25).**
- Helene, 2024-10-04 (DOC-406197A1; this report is excluded from the cell panel for its table, not for this section):
  the PDF reads "Cable and wireline companies reported 342,375 subscribers out of service in the disaster area." Step 3
  parsed 342,375. No previous-day figure is printed.
- Beryl, 2024-07-13 (DOC-403935A1): the PDF reads "471,792 subscribers out of service in the disaster area for
  Hurricane Beryl. This is down from 497,793 yesterday." Step 3 parsed 471,792, and the 2024-07-12 report
  (DOC-403926A1) parsed 497,793: the previous-day check passes.

## B. EAGLE-I updates

All four landing pages were read through their DOIs (osti.gov redirects to ORNL's catalogue pages):

| Release | DOI | Released | Covers | Files | Licence | Coverage information |
|---|---|---|---|---|---|---|
| EAGLE-I Power Outage Data 2023 | 10.13139/OLCF/2297398 | 2024-02-12 | 2023, county, 15-minute | 3 files, ~1.2 GB | **No licence stated** | "Also included is the EAGLE-I coverage of each state for each year" (which years is not stated) |
| EAGLE-I Power Outage Data 2024 | 10.13139/OLCF/2500278 | 2025-04-03 | 2024 | 2 files, ~91 MB | **No licence stated** | No coverage statement; describes "total customers per county" |
| EAGLE-I Power Outage Data 2025 | 10.13139/ORNLNCCS/3012826 | 2026-02-19 | 2025 | 2 files, ~1.4 GB | **No licence stated** | No coverage statement |
| EAGLE-I County Customer Dataset Fall 2025 | 10.13139/ORNLNCCS/3022751 | 2026-05-06 | Customer counts per county (all states, PR, DC) | Not shown | **No licence stated** | Customer type: modeled, collected or mixed |

Our EAGLE-I source is the figshare collection, version 4 (10.6084/m9.figshare.24237376.v4, CC BY 4.0), which already
holds the 2017-2024 year files we used. So the yearly releases matter for coverage and customer counts, not for the
outage counts themselves (whether ORNL's yearly files are identical to figshare's year files is **not verified**).

**Which coverage gaps each would fill.** Our county-reports without published coverage are 4,337 (`coverage_unknown`)
plus Isaias's 131 (`no_eaglei_release`). By the storm's year:

| Year | County-reports | Storms | 2023 release | 2024 release | 2025 release | County Customer Dataset |
|---|---|---|---|---|---|---|
| 2017 | 1,108 | Harvey 497, Irma 603, Nate 8 | Only if its coverage table includes 2017 (not verified) | No | No | No (customer counts, not coverage) |
| 2023 | 160 | Idalia | Probably (it says it includes each state's coverage for each year; not verified until the file is read) | No | No | No |
| 2024 | 3,069 | Beryl 33, Debby 339, Francine 105, Helene 2,332, Milton 260 | No (it predates 2024) | No coverage statement (customer counts only) | No | No |
| 2026 | 131 | Isaias | No | No | No | No |

No release fills Isaias: EAGLE-I has no 2026 release yet. Confirming the 2023 coverage table's years needs that file,
which means a download (about 1.2 GB for the release, or one file of it if they can be fetched separately); I have not
downloaded it.

**Would using them change a published number? Yes.**
- Using any new coverage figures changes the `coverage_unknown` and `low_coverage` flags, so these change (not
  computed): `chapter_6.headlines.matched_by_coverage`; the coverage counts in `chapter_6.by_lag.*.by_storm.*.coverage_counts`
  and the per-storm flags in `chapter_6`; `chapter_6.sensitivity.without_low_coverage`,
  `chapter_6.sensitivity.coverage_unknown_only` and `chapter_6.sensitivity.coverage_ok_only`;
  `v2_3_power_cell_timing.sensitivity.without_low_or_unknown_coverage`; and the published analysis-ready columns
  `eaglei_coverage_flag`, `eaglei_state_min_covered`, `eaglei_state_max_covered`.
- Using the County Customer Dataset (or the 2024 release's customer totals) as the denominator in place of MCC.csv
  changes the share of customers out and the MCC flag, so these change as well: `chapter_6.headlines.comovement_at_as_of_time`,
  `chapter_6.headlines.median_by_lag`, `chapter_6.headlines.comovement_power_cause_at_as_of_time`,
  `chapter_6.headlines.storm_counties_mcc_below_observed_outages`, `chapter_6.headlines.county_reports_used`,
  `chapter_6.by_lag`, every `chapter_6.sensitivity` display except `households_denominator`, `chapter_6.page_text`
  (the denominator note and its example), the whole of `v2_3_power_cell_timing` (its power threshold is 5% of customers), and the
  analysis-ready `eaglei_modeled_customers`, `eaglei_pct_out` and `eaglei_mcc_flag`.
- So any use beyond adding new, unused columns is 4.0.0. Adding the coverage or customer figures as new columns that no
  result reads would be 3.2.0, but only once the licence allows it.

## C. Hazard intensity

**NOAA NCEI Storm Events.** The bulk listing
(https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/) has a details file for every year 2017-2026, all
recreated 2026-11-19 (`c20261119`). 2026 is present, but the season may not be complete in it (not verifiable from the
listing). From the format document (`Storm-Data-Bulk-csv-Format.pdf`, read 2026-11-25): `cz_type` is C (county or
parish), Z (NWS public forecast zone) or M (marine); `cz_fips` is the county FIPS for C records and the zone number for
Z records; `state_fips` the state; damage is `damage_property` and `damage_crops` in the form "10.00K" or "10.00M";
`episode_id` groups events into an episode with an `episode_narrative`. **Hurricane (Typhoon), Tropical Storm, Storm
Surge/Tide and High Wind are zone events (Z); Flood and Flash Flood are county events (C).** So the hurricane and surge
records need the NWS zone-to-county file: `bp16ap26.dbx` (valid 16 April 2026; pipe-delimited; fields STATE, ZONE, CWA,
NAME, STATE_ZONE, COUNTY, FIPS, TIME_ZONE, FE_AREA, LAT, LON), one record per zone polygon, so a county split across
zones appears once per zone. Zones change over time, so 2017-2023 events need the zone file in force at the time (NWS
keeps earlier versions; which ones are needed is not yet checked). Coverage for our 22 storms and ten states is
**not counted** (that needs the files, about 12-16 MB each). No licence or use statement was found on the NCEI pages
read.

**USGS high-water marks.** **Not verified.**
- *STN (Short-Term Network):* refused on 2026-11-25: `stn.wim.usgs.gov/STNServices/Events.json` returned HTTP 403 to
  an automated request, and the STN Data Portal (https://stn.wim.usgs.gov/STNDataPortal) gave "Access forbidden, error
  403" in Tim's own browser. No STN endpoint is tried again (decision log, 2026-11-25).
- *ScienceBase (proposed source):* USGS publishes some HWM collections as data releases with DOIs on ScienceBase. A
  catalog search for each of Helene, Ian, Michael, Harvey, Florence, Ida and Idalia
  (`https://www.sciencebase.gov/catalog/items?q=high-water+marks+Hurricane+<storm>&format=json...`, sent together on
  2026-11-25) returned HTTP 403 for all seven; following the rule, the search stopped there, with no retry and no other
  route (decision log, 2026-11-25). So no release, DOI, licence, HWM count, coverage or file format is known for any
  storm.
- Which storms have HWM data, and how many marks each has, is unknown. The hazard table's HWM columns (below) stay
  proposed only; the NCEI columns do not depend on them.

**Proposed county-storm hazard table** (one row per storm and county in the panel; context only):

| Column | Source | Definition |
|---|---|---|
| `storm_key`, `fips` | panel | The keys |
| `hwm_max_ft`, `hwm_max_above_ground_ft` | USGS HWM data release (if one is found; not STN) | Highest surveyed high-water elevation and height above ground among the county's HWMs for the storm's event (quality "excellent" to "fair" only; the rule fixed in the plan) |
| `hwm_n` | USGS HWM data release (if found) | Number of HWMs in the county (0 where the release has none there; blank where the storm has no release) |
| `surge_flag`, `flood_flag`, `wind_flag` | NCEI | Any Storm Surge/Tide; Flood or Flash Flood; Hurricane, Tropical Storm or High Wind event in the county (zones mapped to counties) within the storm's window |
| `damage_property_usd`, `damage_crops_usd` | NCEI | Sum over those events; for zone events, the zone's damage is not divided among its counties (flagged `damage_from_zone`) |
| `ncei_episode_ids` | NCEI | The episodes used, so each value can be traced |

## D. OpenFEMA Individual Assistance

| Dataset | API | Version | Last refresh | Records | Level | Starts with |
|---|---|---|---|---|---|---|
| Registration Intake and Individuals Household Program (RI-IHP) - v2 | https://www.fema.gov/api/open/v2/RegistrationIntakeIndividualsHouseholdPrograms | 2 | 2026-11-25T06:51:46Z (daily) | 226,124 | State, county (name), city, zip | Disaster 4116 (covers all our storms, 2017 on) |
| Housing Assistance Program Data - Renters - v2 | https://www.fema.gov/api/open/v2/HousingAssistanceRenters | 2 | 2026-11-25T06:51:46Z (daily) | 148,487 | State, county (name), city, zip | DR1439 (2002) |

Neither carries a county FIPS code, so counties are matched by name with our existing crosswalk and its exception
table. No suppression or minimum-count rule is stated on either page. County coverage for our storms is **not counted**
(that needs the records; the API is free and small per disaster).

**"No IA declared" vs "zero registrations".** We already pull Disaster Declarations Summaries v2, whose
`iaProgramDeclared` and `ihProgramDeclared` ("To determine which FEMA events have been authorized to receive Individual
Assistance, use both ihProgramDeclared and iaProgramDeclared") are per declared county. The rule: a storm-county with
neither flag true is "no IA declared" (blank, not zero); with a flag true and no RI-IHP record for that disaster and
county, it is "zero valid registrations" (0); with a record, its sums. The panel's `fema_ia` and `fema_ih` columns hold
the flags already.

**Required citation, exactly as the OpenFEMA Terms and Conditions state it** (https://www.fema.gov/about/openfema/terms-conditions,
"Last updated January 22, 2025"; our existing wording matches it word for word): "This product uses the Federal Emergency
Management Agency's OpenFEMA API, but is not endorsed by FEMA. The Federal Government or FEMA cannot vouch for the data
or analyses derived from these data after the data have been retrieved from the Agency's website(s)." The terms also
ask users to cite the specific API endpoint with its version, by name or by URL, and the date and time the data were
retrieved.

## E. Validation sources (compare only)

**Olukola et al. (2026), arXiv:2609.10944.** The abstract says "We release the dataset"; the data availability section
says the dataset accompanies the submission as supplementary material and will be deposited in a public repository
under CC BY 4.0, with a DOI, on acceptance (this part was read from a summary of the HTML, not verbatim). No URL, DOI or
repository is given, so the dataset is **not released** as of 2026-11-25. The paper itself is CC BY-NC-ND 4.0. Which of
our Helene figures can be compared:

| Figure | Theirs | Ours (published) | Comparable? |
|---|---|---|---|
| Peak cell sites out | 4,562, 28 Sep 2024 | 4,562, report of 2024-09-28 | Yes: identical |
| Sites served in the reporting area | 37,717 (12.1% out) | 37,717 at the peak (12.1%) | Yes: identical |
| Cause split | Six states pooled, attributed base: transport 35.7%, power 63.2%, damage 1.1% (20,413 site-days) | 34.5%, 64.4%, 1.1% converted to their base (22 reports) | Yes, and already shown in chapter 4's external check |
| County-days | 580 (North Carolina 420, Tennessee 160; 24 reports) | 2,332 county-reports in six states (22 reports in use) | Only for NC and TN, report by report; their count is county-days with county detail, not all counties |

**FCC report on Hurricane Michael (PS Docket 18-339).** DOC number DOC-357387 given by Tim (2026-11-25; fcc.gov had
refused an automated request, so it was not looked up there). Downloaded from
https://docs.fcc.gov/public/attachments/DOC-357387A1.pdf on 2026-11-25 (one request, the existing download step), saved
as `data/raw/rules/DOC-357387A1.pdf` (461,134 bytes, 26 pages) and logged in `manifest/downloads.csv` with SHA-256
fbebdd7b93f1fd6ebfb795d380192c6d3a023542c86a195995a782d4413a17d3. First page (read): "October 2018 Hurricane Michael's
Impact on Communications: Preparation, Effect, and Recovery / Public Safety Docket No. 18-339 / Report and
Recommendations / A Report of the Public Safety and Homeland Security Bureau / Federal Communications Commission / May
2019". Its figures that can be set against ours (none compared yet):

| # | Where | The report's figure | Ours to compare (from the panel, for the same report) | Comparable? |
|---|---|---|---|---|
| M1 | Footnote 10 (citing the Oct 17, 2018 status report, p. 4) | "over 46 percent of cell sites in Bay County were still down" a week after impact | Bay County, Florida, report of 2018-10-17 | Yes (county) |
| M2 | Footnote 10 | "nearly 35 percent of such sites were down in Gulf County" | Gulf County, 2018-10-17 | Yes (county) |
| M3 | Footnote 10 | Washington County next highest, "only" 1 of every 5 sites down | Washington County, 2018-10-17, and its rank among the report's counties | Yes (county and rank) |
| M4 | Para. 29 (Figure 3, Oct 20) | Bay and Gulf "up to 45% cell sites down", surrounding counties "less than 15%" | Florida counties, report of 2018-10-20 | Yes (counties, as bounds) |
| M5 | Para. 28 (Figure 2) | Alabama "fully restored by October 15", Georgia "shortly after", Florida "little change from October 19 through October 25" | State totals by report, Oct 15 to 25 | Yes (state, in words) |
| M6 | Para. 2 | Georgia, Alabama and most of Florida rebounded "within 48 hours" of landfall | State totals, Oct 11 to 12 | Only in words |
| M7 | Background (footnote) | DIRS deactivated for Michael on October 26, 2018 | Our last Michael report: 2018-10-26 (16 reports, Oct 11 to 26) | Yes (matches) |
| M8 | Para. 36 (Figure 6) | Wireline and cable customers out "dropped steadily from October 10 to October 19", then steady until deactivation | The cable and wireline table (A1: Michael's state rows) | Only in words; the chart's values are not in the PDF's text layer |
| M9 | Figures 1 and 3 (maps, Oct 11 and Oct 20), 7 (broadcast), 8 (PSAPs in Florida) | Images | — | Only by eye; not used |
| M10 | Figures 4 and 5 (Bay and Gulf, cell sites out by cause) | Images, "derived from anonymized DIRS data" | Our Michael reports print no cause columns | No |

## Version plan

- **3.2.0 (adds tables and columns; no published number changes):**
  - A1: a report-level cable and wireline table (`dirs_cable_wireline.csv`: storm, report, area or state, subscribers
    out, the printed previous-day figure and the check), from the reports already in `data/input`.
  - D: a county-storm Individual Assistance table (valid registrations, IHP referrals and amounts, renters inspected
    and approved), with the declaration rule above and the OpenFEMA statement.
  - C1 (and the HWM columns only if a USGS data release is found and its terms read): the county-storm hazard table above.
  - E: comparison notes (Olukola: the four rows above; Michael: M1 to M8, by the same method as the 2017 check, with
    the report added to `data/input/rules/`), as `docs/external_validation.md` sections. No data change follows from
    them without asking.
  - None of these feeds an existing result, so `results.json` and every published file stay byte for byte; the new
    tables are new files, and any new page text describes them, without new findings, until a plan addendum is
    committed and run.
- **4.0.0 (published numbers change):**
  - B: any use of the ORNL yearly coverage tables or the County Customer Dataset in the analysis (the keys listed in B).
  - Any new analysis that uses the 3.2.0 tables as outcomes or controls (for example, cell outages against flood
    height), once its addendum is committed.
  - Already listed for 4.0.0: the package restructure, removing `days_since_landfall`, and the pandas 3 upgrade.

## Draft analysis-plan addendum (for the recommended parts; to be committed before any of it is computed)

> **Addendum 4.x-1 (draft, not committed).** Written 2026-11-25, before any of the quantities below is computed. Only
> the structure of the sources has been seen (section layouts, field definitions, refresh dates), not their values for
> our storms. Results from it are exploratory, and the page labels them so.
>
> 1. *Cable and wireline subscribers out (3.2.0).* For each report, the printed figure for the whole disaster area
>    (or each state, where printed), read with the existing text-then-PDF rule. Checks: the figure is a whole number;
>    where the report prints a previous-day figure, it must equal the previous report's printed figure, or the report is
>    flagged (not corrected). Reported per storm: the figure at each report, its largest value and the report it
>    occurred in, and the figure at the storm's last report. No allocation to counties, and no comparison with cell
>    sites beyond showing both per report. Excluded reports keep their cable figure, flagged as from an excluded report.
> 2. *Individual Assistance (3.2.0).* Per storm and county: IA declared (from `iaProgramDeclared` or
>    `ihProgramDeclared`), valid registrations, IHP referrals, IHP eligible and amount (RI-IHP v2), and renters'
>    valid registrations, inspected and approved counts (Housing Assistance Renters v2), summed over the storm's
>    disaster numbers in the county. "No IA declared" is blank; declared with no record is 0. Retrieval date and
>    endpoint versions are recorded. Reported as a descriptive table only.
> 3. *Hazard (3.2.0).* The county-storm hazard table defined in the scoping document, with the storm's window fixed
>    as its DIRS activation date minus 2 days to its last report plus 2 days, the NWS zone file in force on the event
>    date, and HWM quality limited to excellent, good and fair. Reported as a descriptive table only.
> 4. *Not in this addendum:* any association between these tables and cell outages, and any change to EAGLE-I coverage
>    or denominators. Each needs its own addendum, committed before it is run, and is a 4.0.0 change.

## Not verified (and what each needs)

- **USGS high-water marks**: STN refused (HTTP 403, automated and in Tim's browser), and the ScienceBase catalog
  search refused (HTTP 403, all seven storms). Needs: a ScienceBase data release URL or DOI you can open yourself (for
  example from a USGS storm page), which I would then read, or a decision to drop HWMs from the hazard table.
- **FCC Michael report**: stored and its first page checked; its charts are images, so only the text figures (M1 to M8)
  can be compared, and none has been compared yet.
- **EAGLE-I licences**: none of the four ORNL/OSTI landing pages states a licence; whether ORNL applies one elsewhere is
  unknown. Needs a statement from ORNL (or a licence file inside the releases) before any redistribution.
- **EAGLE-I 2023 coverage years**, and whether ORNL's yearly outage files equal figshare's: needs the files (a download
  you would approve first).
- **NCEI Storm Events terms**: no licence or use statement found on the pages read; the counts of events for our storms
  and states need the yearly files (about 12-16 MB each; a download you would approve first). Whether the 2026 file is
  complete is not knowable from the listing.
- **OpenFEMA county coverage** for our storms: needs API queries per disaster (small, but not yet made).
- **Olukola et al.'s dataset**: not released; its data-availability wording was read from a summary, not verbatim.
- **The section sweep** in A is a pattern match over free text; a parser with tests would confirm each cell before
  anything is built.
