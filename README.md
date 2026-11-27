# When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24477809.svg)](https://doi.org/10.5281/zenodo.24477809) [![CI](https://github.com/ts2427/when-the-network-goes-dark-data/actions/workflows/ci.yml/badge.svg)](https://github.com/ts2427/when-the-network-goes-dark-data/actions/workflows/ci.yml)

Version 4.0.0 (2026-11-27). Data: CC BY 4.0 (`LICENSE-DATA.md`). Code: MIT (`LICENSE`).

The data and code behind the page *When the Network Goes Dark* (https://thresholddatasciences.com/analysis/when-the-network-goes-dark/): a county-by-report panel of FCC DIRS cell-site outages for 22 storms in ten Gulf and Southeast states, 2017-2026, each report checked against its printed totals, joined to power outages (EAGLE-I), storm tracks (NHC), social vulnerability (CDC/ATSDR SVI) and broadband provider counts (FCC BDC). Every number on the page is in `data/analysis/results.json`, and `run_all.py` rebuilds it and the panel from `data/input/`.

What the data can and cannot be used for, and their known limitations: `DATASHEET.md`.

## Scope

A DIRS activation is included when it is for an Atlantic named storm, hurricane or tropical storm (a storm that never reaches hurricane strength is included too; every storm in this release did, at some point in its track, per HURDAT2), its activation date is in 2017-2026, and its public Communications Status Reports print county rows in at least one of the ten study states (Texas, Louisiana, Mississippi, Alabama, Florida, Georgia, South Carolina, North Carolina, Tennessee, Virginia). Within an included storm, a report whose rows all lie outside those states is kept in the manifest but not used, and rows outside them are dropped. The series starts in 2017 because the committed analysis plan (2026-11-22) fixed the scope at 2017-2026, the years whose report layouts the parser was built and checked on; the only 2016 activation, Matthew, has not been read and is planned as a separate module (docs/roadmap_modules.md). Other hazards (earthquakes, wildfires, winter storms, power shutoffs) and the territories are outside the rule. This dataset is the Gulf and Southeast hurricane subset of a larger public DIRS record: the FCC has also published status reports for activations in the territories and for other hazards (docs/dirs_activations.csv). Later extensions (Matthew 2016, the territories, other hazards) are planned as separate modules with their own versions, so the core numbers do not change when one is added (`docs/roadmap_modules.md`).

### Report counts

| Step | Reports | Which |
|---|---|---|
| In the manifest (`code/manifest/dirs_reports.csv`) | 181 | every FCC report listed from the FCC's storm pages (Nicholas's rows are in two of Ida's reports) |
| Out of scope | 3 | Fiona 2022-09-24 (DOC-387555A1); Fiona 2022-09-26 (DOC-387584A1); Dorian 2019-08-29 (DOC-359363A1): outside the study area (Puerto Rico; Dorian's also the U.S. Virgin Islands); not parsed |
| Validated (step 4) | 178 | parsed and checked |
| Excluded | 0 | none |
| Outside the study states | 4 | Irma 2017-09-07 (DOC-346607A1); Irma 2017-09-08 (DOC-346626A1); Irma 2017-09-09 (DOC-346632A1); Irma 2017-09-10 (DOC-346634A1): county rows only outside the ten study states |
| Used (in `dirs_county_day.csv`) | 174 |  |

In `storms.csv`, `n_reports` sums to 176, not 174: DOC-375778A1 and DOC-375808A1 are shared by Ida and Nicholas and counted for both.

Associations, not causes. Each FCC report carries this caveat: "The number of cell site outages in a specific area does not necessarily correspond to the availability of wireless service to consumers in that area." So the counts here describe the network, not how many people lost service.

## Which licence covers what

| Part | Licence |
|---|---|
| `data/analysis/`, derived files in `data/input/` (marked in `INPUTS.csv`), `datapackage.json`, `CODEBOOK.md` | CC BY 4.0 |
| `code/`, `run_all.py` | MIT |
| Third-party inputs in `data/input/` | their own terms; see `SOURCES.md` |

## Contents

```
data/input/      every input, with INPUTS.csv (source, URL, retrieval time, SHA-256)
data/analysis/   dirs_county_day.csv (the panel), storms.csv, results.json, validation/,
                 panel_analysis_ready.csv and .parquet (the panel with every covariate the analysis uses),
                 context/ (3.2.0: cable and wireline, FEMA Individual Assistance, NCEI hazard)
code/src/        numbered pipeline steps, load.py (load_panel(), clean_rows()); code/manifest/
                 hand-made tables; code/tests/
examples/        quickstart.ipynb: load the panel and rebuild two headline figures
.github/         CI (lint, tests, the notebook and a full rebuild on Linux and Windows, on every push
                 and monthly), Dependabot, the 'Report a data error' issue form
docs/            analysis plan (as committed, with SHA-256), addendum, decision log, sources notes,
                 update_procedure.md (how a new season and a new version are added and released),
                 external_validation.md (the check against the FCC's 2017 season report),
                 restructure_plan.md (the layout planned for 4.0.0), addendum 4.x-1 (as committed,
                 with SHA-256) and scoping_4x.md (the sources considered for 3.2.0 and 4.0.0)
ERRATA.md        every change to a published number; CONTRIBUTING.md: how to report an error
DATASHEET.md     the datasheet: motivation, composition, collection, uses not supported, known
                 limitations, distribution and maintenance
.zenodo.json     the Zenodo archive's metadata (built from CITATION.cff)
run_all.py       one command: rebuild the panel and results.json into build/
```

## Analysis-ready panel

`data/analysis/panel_analysis_ready.parquet` (and `.csv`) is `dirs_county_day.csv`, same rows and order, joined with every covariate the analysis uses: EAGLE-I power outages at each report's as-of time with its match and coverage flags, distance to the track, wind radii and chapter 7's wind zone, day 0 and days since day 0, SVI 2022, ACS 2022, and the storm's BDC release with its provider counts and chapter 13 group. Variables: `CODEBOOK.md`. To load it with its types:

```python
import sys
sys.path.insert(0, "code/src")
from load import load_panel
from load import clean_rows
p = load_panel()   # the Parquet if present, else the CSV, with the same types
q = clean_rows(p, "standard")   # or "strict"
```

`report_date` and `dirs_activation_date` load as dates (since 3.1.0). `days_since_day0` is the days from the storm's day 0 to the report's as-of time; `days_since_landfall` is the same column under its old name, kept as a deprecated alias until 4.0.0. `clean_rows` drops rows at one of two levels and never changes a value:

| Level | Drops | Why |
|---|---|---|
| `standard` | rows with a time_flag: pre_onset_likely_marco, Laura's Aug 25, 2020 report (the FCC's combined Marco and Laura report, before Laura's day 0) | The rows behind every time-based result (steps 10 and 12 filter them the same way, with timed()): a report from before the storm's day 0 cannot be placed on its clock. Flagged reports are kept, as in the main analysis, because most flags are benign (see validation/validation_dirs.csv). Chapters 5 to 7 (causes, power, exposure) use every row. |
| `strict` | everything standard drops, and every report whose report_status is flagged (keeping ok and known_fcc_inconsistency) | The sensitivity display 'without flagged reports': only reports that reconcile with their printed totals, or whose one inconsistency is a checked FCC misprint (manifest/known_fcc_inconsistencies.csv). It drops benign flags too (spelling variants, a footnote, causes over sites out), so it is cautious rather than a list of errors; serious flags alone are in validation/validation_dirs.csv. |

`clean_rows(level="strict")` keeps 10 of 22 storms (47 of 174 reports, 2,518 of 11,296 rows), because most reports carry at least one flag, most of them benign; `standard` keeps 22 of 22 (11,136 rows). Use strict as a sensitivity check rather than as the main sample.

`examples/quickstart.ipynb` loads the panel, rebuilds the recovery curves (with the median time to 50% restored) and the pooled cause shares with plain pandas, and checks both against `results.json`; CI runs it (`python -m pytest --nbmake examples/quickstart.ipynb`).

## External validation

The FCC's own summary of the season, *2017 Atlantic Hurricane Season Impact on Communications* (DOC-353805A1, August 2018), gives 80 county or state figures for Harvey and Irma. Each is transcribed with its page (`code/manifest/external_fcc_2017_report.csv`) and compared with the matching report by `code/src/15_external_validation.py`: 55 match, 4 match once the FCC's dropped decimals are allowed for, 1 is consistent with a figure given in words, 10 differ and 10 cannot be compared (switching centers, PSAPs, broadcast stations, providers' filings). In each difference the season report departs from what the DIRS report prints or from the total its rows reconcile to, so none points to an error in the panel, and no data were changed because of the check. Every figure: `docs/external_validation.md` and `data/analysis/validation/external_validation_fcc_2017.csv`. The differences:

| # | FCC figure | Report | FCC | Ours | Explanation |
|---|---|---|---|---|---|
| H04 | p. 6 para. 13: By September 5, the eleventh and final day of DIRS reporting, only 1.6 percent of cell sites were out of service | 2017-09-05 | 1.6 | 1.74 | 1.6% is the Sep 4 report's printed figure. The Sep 5 report prints 1.73% (73 of 4,200 sites), and the FCC report itself gives 1.7% for Sep 5 on p. 7 (para. 15) and in its chart (H22). |
| H20 | p. 8 chart: Percent of Cell Sites Out Per Day: 9/2 | 2017-09-02 | 3.6 | 2.01 | Not explained. The Sep 2 report prints 2.0% (193 of 9,611 sites), its rows give the same, and no state or combination of states in it gives 3.6%. The chart plots the point at 3.6%, matching its label. |
| H25 | p. 8 para. 16: about 150,000 cable subscribers lacked service at some point during the Hurricane Harvey DIRS reporting period (August 26-September 5, 2017) | all | 150000 | 283593 | The reports print one figure for cable and wireline subscribers out over the whole area. It is 149,909 in the first report (Aug 26) and peaks at 283,593 on Aug 29, so the FCC report's 'about 150,000' matches the first report, not the most at any point. This figure is not used in any result. |
| I01 | p. 5 para. 10: during the initial impact of Hurricane Irma in USVI, 55.2 percent of cell sites were reported out of service (footnote 11: the Sep 7 report) | 2017-09-07 | 55.2 | 48.96 | 55.2% is the Sep 7 report's total for Puerto Rico and the USVI together (397 of 719 sites). The USVI alone is 49.0% (47 of 96). The three island figures in the same sentence (I02-I04) match the report. |
| I05 | p. 8 para. 17: On September 7, 2017, the Commission activated DIRS for all 78 municipios in Puerto Rico and the three counties of the USVI | 2017-09-07 | 81 | 44 | The activation covered 81 areas, but the Sep 7 report lists 41 municipios and the 3 USVI counties. Every later Irma report lists all 78 municipios and 3 USVI counties (81). |
| I20 | p. 14 chart: Puerto Rico 9/9 | 2017-09-09 | 19.3 | 29.32 | Not explained. Puerto Rico's 78 rows in the Sep 9 report give 29.3% (511 of 1,743 sites; the report prints no Puerto Rico total that day), and no state or combination of states in the report gives 19.3%. Our rows agree with the report's printed total for Puerto Rico and the USVI together, 31.1% (576 of 1,850). The chart plots the point at 19.3%, below the 25.0% of Sep 10. |
| I32 | p. 14 chart: USVI 9/14 | 2017-09-14 | 54.7 | 53.77 | Probably the Sep 13 value repeated: the Sep 14 report prints 53.8% (57 of 106 sites), and 54.7% is the Sep 13 figure (58 of 106). The FCC report's own text gives 'fifty-four percent' for Sep 14 (I09), which matches the report. |
| I37 | p. 14 para. 20: in Florida at the height of the storm 27.1 percent of the cell sites were out of service | 2017-09-11 | 27.1 | 27.40 | Not explained. The Sep 11 report prints 27.4% for Florida (3,973 of 14,502 sites), its rows give the same, and no combination of states in the report gives 27.1%. The FCC report's own 'twenty-seven percent' for Sep 11 (I08) is consistent with either. |
| I39 | p. 14 chart: Percent of Cell Sites Out Per Day in Florida: 9/11 | 2017-09-11 | 27.1 | 27.40 | Not explained, as I37. |
| I45 | p. 14 chart: Florida 9/17 | 2017-09-17 | 4.3 | 3.96 | Possibly Florida and the USVI together: the Sep 17 report prints 4.0% for Florida (584 of 14,730 sites), while Florida and the USVI together give 4.29% (637 of 14,836). That reading is not confirmed: the chart's other Florida points are Florida alone. |

Since 3.2.0, three more checks (`code/src/15b_external_michael_olukola.py`, exploratory). The FCC's report on Hurricane Michael (DOC-357387A1, May 2019) gives 12 figures in its text: 8 can be tested, of which 7 match or are consistent and 1 differs (M5a, explained in `docs/external_validation.md`); 4 are statements with no number to test and are shown beside our series. Olukola et al. (2026): the Helene peak (4,562 sites out, 28 September 2024) and sites in the reporting area (37,717, 12.1% out) match an independent extraction exactly; the cause split is the comparison already on the page, and the county-day counts are defined differently. Their Irma peak (4,370 sites out, 11 September 2017) matches our report's rows, counting Puerto Rico and the U.S. Virgin Islands, which are outside the panel. FCC 21-99 cites Ida's report of August 31, 2021 for 699 sites out for power against 354 for damage and transport: those are the report's Louisiana totals, and our county rows sum to the same. Tables: `data/analysis/validation/external_validation_fcc_michael.csv`, `external_validation_olukola.csv` and `external_validation_fcc_21_99.csv`.

## Context tables (3.2.0)

Exploratory, under addendum 4.x-1: descriptive tables added in 3.2.0. No published result reads them, and no association with cell outages has been computed. Variables: `CODEBOOK.md`.

- `data/analysis/context/dirs_cable_wireline.csv`: cable and wireline subscribers out, 233 rows from 178 reports, by area as printed (the whole disaster area, or state rows). Where a report prints the previous day's figure it is checked against the previous report: 45 match, 1 do not (flagged, not corrected).
- `data/analysis/context/fema_ia_county_storm.csv`: FEMA Individual Assistance by storm and county (2,375 storm-counties, 537 with IA declared), from OpenFEMA RI-IHP v2 and Housing Assistance Renters v2; rows that name no single county (tribal areas, statewide, other states) are counted in `fema_ia_set_aside.csv`.
- `data/analysis/context/hazard_ncei_county_storm.csv`: surge, flood and wind flags and damage by storm and county (2,375 storm-counties), from NOAA NCEI Storm Events. Damage from county events is in `damage_property_usd` and `damage_crops_usd`; damage from zone events is in the `zone_..._unallocated` columns, undivided, with `zone_n_counties`, and must never be summed across counties. `hazard_ncei_storm_summary.csv` gives each storm's window and the zone events not mapped. The NCEI files are not redistributed (no licence or use statement was found), so the reproduction test compares this table only when they are supplied (`NCEI_RAW_DIR`). No high-water marks: both USGS sources refused automated requests.

## Related work

To our knowledge, this is the first openly licensed, versioned, DOI-archived county-by-report panel of FCC DIRS cell-site outages spanning multiple hurricanes and states, validated against the reports' printed totals. The other DIRS-derived compilations we found cover a single storm (Helene) or a single state (Florida); for a ten-hurricane county-level study (Du, 2024) we found no public data release.

- Olukola, O., Addeh, O. D., Konan, E. A., & Rahimi, N. (2026). *The towers were standing: A cause decomposition of cellular outages during Hurricane Helene* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2609.10944 Helene only, from the same FCC reports; the preprint gives no link to its dataset, which is not yet deposited. This page uses it as a check (chapter 4 and the methods).
- Du, A. (2024). Data-driven telecommunication outage prediction during hurricane events. *ASCE-ASME Journal of Risk and Uncertainty in Engineering Systems, Part A: Civil Engineering, 10*(3), 04024046. https://doi.org/10.1061/AJRUA6.RUENG-1285 Ten hurricanes in eight states at county level, to predict outages; we found no public data release. This work is a checked record of the outages the FCC reported, not a prediction.
- Anonymous. (n.d.). *grid-to-lifeline-site: Interactive companion site, cross-infrastructure dependency and resilience across nine Florida hurricanes* [Source code]. GitHub. Retrieved November 25, 2026, from https://github.com/ac5907846/grid-to-lifeline-site Florida only, the companion to a manuscript under review, with no licence stated; this work covers ten states under CC BY 4.0.
- Reed, D. A., & Wang, S. (2018). Numerical modeling of power delivery and telecommunications infrastructure for Hurricanes Harvey and Irma. In *Forensic Engineering 2018* (pp. 1008–1016). American Society of Civil Engineers. https://doi.org/10.1061/9780784482018.097 Models power and telecommunications for two 2017 storms; this work records what the reports show for every storm in scope.
- Feeny, N., White, A., & Guikema, S. (2026). A quantitative spatial approach to estimate cellular network coverage during natural hazards using publicly available data. *Journal of Infrastructure Preservation and Resilience, 7*, 14. https://doi.org/10.1186/s43065-026-00176-0 Simulates where cell coverage is likely to be lost (Ann Arbor, Michigan, under high winds); this work uses observed outages.
- Cortes, M., Arora, P., Ceferino, L., Ibrahim, H., Istrati, D., Reed, D., Roueche, D., Safiey, A., Tomiczek, T., Zisis, I., Alam, M., Kijewski-Correa, T., Prevatt, D., & Robertson, I. (2022). *StEER: Hurricane Ian preliminary virtual reconnaissance report (PVRR)* (PRJ-3709) [Data set]. DesignSafe-CI. https://doi.org/10.17603/ds2-kc9k-s242 One storm, from virtual (not field) reconnaissance across power, telecommunications and transportation; this work is cell sites only, across storms.
- claffy, k., & Clark, D. (2022). Challenges in measuring the Internet for the public interest. *Journal of Information Policy, 12*, 195–233. https://doi.org/10.5325/jinfopoli.12.2022.0003 Describes the access limits on NORS/DIRS data that make an open panel useful.
- U.S. Government Accountability Office. (2017). *Telecommunications: FCC should improve monitoring of industry efforts to strengthen wireless network resiliency* (GAO-18-198). https://www.gao.gov/products/gao-18-198 An audit of the FCC's role and of industry efforts; not an outage dataset.
- U.S. Government Accountability Office. (2021). *Telecommunications: FCC assisted in Hurricane Maria network restoration, but a clarified disaster response role and enhanced communication are needed* (GAO-21-297). https://www.gao.gov/products/gao-21-297 An audit of the FCC's role after Hurricane Maria; not an outage dataset.
- Peskin, A. H. (2025). *Cellular network outage reporting and restoration during disasters* (CRS Report R48776). Congressional Research Service. https://www.congress.gov/crs-product/R48776 A report to Congress on outage reporting; not a dataset.
- Gallagher, J. C., & Peskin, A. H. (2024). *Restoration of cell phone services: Hurricane Helene* (CRS In Focus IF12779). Congressional Research Service. https://www.congress.gov/crs-product/IF12779 A brief for Congress on Helene's restoration; not a dataset.
- Federal Communications Commission. (2021). *Resilient networks* (Notice of proposed rulemaking, FCC 21-99). https://docs.fcc.gov/public/attachments/FCC-21-99A1.pdf; Federal Communications Commission. (2024). *Resilient networks* (Second report and order, FCC 24-5), in force February 20, 2025 (Federal Register 2025-00495, 90 FR 6839); Federal Communications Commission. (2026). *Resilient networks* (Third report and order, FCC 26-34). Federal Register 2026-13155, 91 FR 39516. The rules behind the reports; chapter 12 describes the periods they define.

## Analysis plan

The analysis plan was committed on November 22, 2026, in the project's private version-controlled repository (commit 9fc17a4, 2026-11-22T16:16:48-06:00), before any recovery outcome was computed. The plan file as committed is `docs/analysis_plan_as_committed_9fc17a4.md`, SHA-256 `d4aa966e3874d69bc256bbe1c8d1153da9fb35429551d2bae25403e61db1dd8e` (git blob `28c91c70c8be9194848957569fab1e7f5515d345`), so it can be checked against later changes. It is not blind to some figures, which the plan lists. Deviations are in `DEVIATIONS.md`.

The 3.2.0 context tables follow addendum 4.x-1, committed on its own (2026-11-25T11:13:28-06:00, commit d7bdc66) before any of their sources was downloaded or any of their values computed: `docs/analysis_plan_addendum_4x_as_committed_d7bdc66.md`, SHA-256 `fdb273bd2d723354143ff42322cfe2595b6f2c107c7f4d7d503c9c64a9b1123f`.

## Data availability and provenance

| Data | Location | Provider | Terms | Included | Size |
|---|---|---|---|---|---|
| FCC DIRS reports (PDF and text) | `data/input/dirs/` | FCC | Public domain (U.S. government) | yes | 103.7 MB |
| FCC DIRS notices | `data/input/notices/` | FCC | Public domain | yes | 0.4 MB |
| FCC orders cited for dates | `data/input/rules/` | FCC | Public domain | yes | 3.6 MB |
| FCC storm-page document lists | `data/input/storm_pages/` | FCC (compiled list) | Public domain | yes | 0.1 MB |
| EAGLE-I extract, MCC, coverage | `data/input/eaglei/` | ORNL/DOE | CC BY 4.0 | yes (extract modified) | 12.9 MB |
| EAGLE-I year files 2017-2024 | not included (8.9 GB) | ORNL/DOE via figshare | CC BY 4.0 | no: download with code/src/06a_download_eaglei.py | 8.9 GB |
| BDC provider counts | `data/input/bdc/` | FCC BDC (derived) | CC BY 4.0 (counts) | yes (counts only) | 0.1 MB |
| BDC provider-by-geography files | not included | FCC BDC | FCC API terms | no: provider-level files are not redistributed |  |
| ACS 5-year 2022 | `data/input/acs/` | Census Data API | Public domain; API notice in SOURCES.md | yes | 0.5 MB |
| County lists, gazetteer, boundaries | `data/input/census/` | Census | Public domain | yes | 11.9 MB |
| SVI 2022 | `data/input/svi/` | CDC/ATSDR | Public domain; credit line in SOURCES.md | yes | 2.3 MB |
| OpenFEMA declarations | `data/input/fema/` | FEMA | Public domain; disclaimer in SOURCES.md | yes | 6.1 MB |
| NHC HURDAT2 and Isaias best track | `data/input/nhc/` | NOAA/NHC | Public domain | yes | 7.2 MB |
| OpenFEMA Individual Assistance (3.2.0) | `data/input/fema_ia/` | FEMA | OpenFEMA terms; disclaimer in SOURCES.md | yes | 30.7 MB |
| NWS zone-county file (3.2.0) | `data/input/nws/` | NOAA/NWS | Public domain | yes | 0.4 MB |
| NCEI Storm Events details 2017-2026 (3.2.0) | not included (135 MB) | NOAA/NCEI | no licence or use statement found | no: download the c20261119 files and set NCEI_RAW_DIR | 135 MB |

Exact attribution for each source: `SOURCES.md`. Variables: `CODEBOOK.md` and `datapackage.json`.

## Computational requirements

- Python 3.13 (tested with 3.13.2) on Windows 11; the code uses no platform-specific calls. CI runs the tests and a full rebuild on windows-latest and ubuntu-latest (badge above).
- Packages: `requirements.txt` (exact versions of the packages used) and `requirements.lock` (every package, including dependencies, pinned with SHA-256 hashes for Windows, Linux and macOS; generated with `uv pip compile requirements.txt --universal --generate-hashes --python-version 3.13 -o requirements.lock`). For an exact environment: `python -m pip install --require-hashes -r requirements.lock`.
- Memory: about 4 GB. Disk: about 200 MB for the repository and `build/`.
- Run time: 18.8 minutes for `run_all.py`, measured on the author's Windows 11 laptop on 2026-11-25 (most of it is parsing the reports in steps 3 and 17 and the bootstrap in step 10).
- No network access is needed: every step reads `data/input/`. Steps 02, 06a, 06c, 06d and 06e (downloads and raw BDC reading) are included for transparency but are not run; they need the original sources and, for BDC, an FCC account.
- Random numbers: fixed seed 20261122 (bootstrap, 2,000 draws).
- Intervals: The county bootstrap (chapters 3 to 6 within each storm; chapters 8 and 13 across storm-counties) resamples counties as if they were independent. Counties hit by the same storm share its wind, flooding, power grid and networks, so their outcomes are correlated, and these intervals may be somewhat narrow. The storm bootstrap (medians and pooled shares across storms, chapter 7's zone shares, chapter 12) resamples whole storms, and the models in chapters 7, 8 and 13 use storm- or county-clustered intervals. This is a note on the method, not a change to any result.
- Floating point: `results.json` stores floats to 10 significant digits, and the reproduction test compares its numbers with a relative tolerance of 1e-8 and an absolute floor of 1e-12 (text exactly), because platforms' math libraries can differ in the last bits (up to about 1e-9 relative, in model fits). The panel, storm and validation CSVs must match byte for byte; the analysis-ready panel is compared value by value at the same tolerance.

## Run order

```
python -m pip install -r requirements.txt   # or: --require-hashes -r requirements.lock
python -m pytest code/tests        # unit tests; the build checks skip until run_all.py has run
python run_all.py                   # rebuild into build/
python -m pytest code/tests        # now including the reproduction test (build/ vs data/analysis/)
python -m pytest --nbmake examples/quickstart.ipynb   # the quickstart notebook
python -m ruff check code examples run_all.py        # lint (ruff.toml)
```

`run_all.py` runs these steps in this order (all in `code/src/`):

| # | Script | Arguments | Does |
|---|---|---|---|
| 1 | `01_check_manifest.py` |  | 4.0.0: the report manifest; fails on any report whose status is not ok, excluded or out_of_scope |
| 2 | `02b_reporting_areas.py` |  | each storm's reporting area from the FCC notices (rewrites code/manifest tables; the test checks they are unchanged) |
| 3 | `03_parse_dirs.py` |  | parse every DIRS report (text first, PDF fallback) into county rows and totals |
| 4 | `04_validate_dirs.py` |  | reconcile county rows with each report's printed totals; validation tables |
| 5 | `05_fips.py` |  | county names to FIPS |
| 6 | `06_eaglei.py` |  | match EAGLE-I (from the published extract) to each report's as-of time |
| 7 | `07_nhc.py` |  | tracks, wind radii, distance to track, day 0 |
| 8 | `08_fema_svi_bdc.py` |  | ACS, SVI and OpenFEMA declarations (from the stored files; no request is made) |
| 9 | `09_build_panel.py` |  | the panel, the storm table and dirs_county_day.csv |
| 10 | `10_analysis.py` | 3 4 5 6 7 8 9 | chapters 3-9 to results.json |
| 11 | `10_analysis.py` | 1 2 | chapters 1 and 2 (run second so results.json keeps the published key order) |
| 12 | `12_v2_analysis.py` | v2_1 v2_2 v2_3 v2_5_groups v2_5 report_card | chapters 10-14 to results.json |
| 13 | `12b_analysis_ready.py` |  | the analysis-ready panel (CSV and Parquet): the panel with every covariate |
| 14 | `15_external_validation.py` |  | external check against the FCC's 2017 season report (Harvey and Irma figures) |
| 15 | `16_fema_ia.py` |  | v3.2.0: FEMA Individual Assistance by storm and county (from the stored OpenFEMA responses) |
| 16 | `17_cable_wireline.py` |  | v3.2.0: cable and wireline subscribers out, per report and area |
| 17 | `18_hazard_ncei.py` |  | v3.2.0: NCEI hazard flags and damage by storm and county (skipped unless the NCEI files are supplied: they are not redistributed) |
| 18 | `15b_external_michael_olukola.py` |  | v3.2.0: external checks against the FCC's Michael report and Olukola et al. (2026) |

`code/tests/test_reproduction.py` then compares `build/` with `data/analysis/`: `dirs_county_day.csv`, `storms.csv` and the validation tables byte for byte, `results.json` with numbers within a relative 1e-8 (absolute 1e-12 near zero) and everything else exactly, and the analysis-ready panel value by value. `code/tests/test_datapackage.py` checks `datapackage.json` with frictionless (`frictionless validate datapackage.json`: 0 errors).

## Page sections and figures

Each section of the page, its figures (the figure CSVs are published with the page), the key in `results.json` and the script that produces it. The page itself is built by `code/src/11_build_page.py`, which needs the website and is not run here.

| Page section | Figures | results.json key | Script |
|---|---|---|---|
| Opening: Why this page exists, How to read it |  | chapter_1, chapter_4, v2_1_public_record_misses, v2_2_backup_power, v2_3_power_cell_timing, v2_5_network_redundancy | 10_analysis.py, 12_v2_analysis.py |
| Map: where cell sites were out | storm map (hurricane-map.json) | panel (dirs_county_day.csv) | 09_build_panel.py; map data written by 11_build_page.py |
| The data |  | chapter_1 | 10_analysis.py |
| 1. Anatomy of a storm: Isaias | fig-isaias-map: hurricane-isaias-map.csv; fig-isaias: hurricane-isaias-counties.csv | chapter_2 | 10_analysis.py (track: 07_nhc.py) |
| 2. How much goes dark | fig-peaks: hurricane-peaks.csv | chapter_3 | 10_analysis.py |
| 3. How fast it comes back | fig-curves: hurricane-recovery-curves.csv; fig-restored: hurricane-restored.csv | chapter_4 | 10_analysis.py |
| 4. Why sites go dark | fig-causes: hurricane-causes.csv | chapter_5 | 10_analysis.py |
| 5. The power coupling (with Which comes back first: power or cell service?) | fig-power-overlay: hurricane-power-overlay.csv; fig-power: hurricane-power-lags.csv | chapter_6, v2_3_power_cell_timing | 10_analysis.py (EAGLE-I match: 06_eaglei.py); 12_v2_analysis.py v2_3 |
| 6. Running on backup power |  | v2_2_backup_power | 12_v2_analysis.py v2_2 |
| 7. Exposure | fig-zone: hurricane-wind-zone.csv; fig-distance: hurricane-distance.csv; fig-calibration (methods): hurricane-calibration.csv | chapter_7 | 10_analysis.py (exposure: 07_nhc.py) |
| 8. Social vulnerability | fig-svi: hurricane-svi-wait.csv | chapter_8 | 10_analysis.py (SVI: 08_fema_svi_bdc.py) |
| 9. Mobile providers |  | v2_5_groups, v2_5_network_redundancy | 12_v2_analysis.py v2_5_groups v2_5 (counts: 06e, 06f) |
| 10. Where the reports stop | fig-coverage: hurricane-coverage-heatmap.csv | chapter_1 (heatmap), v2_1_public_record_misses | 10_analysis.py; 12_v2_analysis.py v2_1 |
| 11. How complete the reports are |  | v2_1_1_report_card; validation/external_validation_fcc_2017.csv | 12_v2_analysis.py report_card (from the validation outputs); 15_external_validation.py |
| 12. Did the rules help? |  | chapter_9 | 10_analysis.py |
| What it adds up to |  | chapter_4 to chapter_9, v2_1_public_record_misses, v2_2_backup_power, v2_3_power_cell_timing, v2_5_network_redundancy, v2_1_1_report_card; validation/external_validation_fcc_2017.csv | 11_build_page.py (each number taken from its chapter; tested) |
| Look up a county | county lookup (hurricane-county-lookup.json) | panel | 11_build_page.py |
| Methods (with the Audit trail) | validation tables | chapter_1, validation/*.csv | 04_validate_dirs.py, 10_analysis.py, 15_external_validation.py |

### Page chapters and results.json keys

The page numbers its chapters 1 to 12 (since November 25, 2026). The keys of `results.json` keep their original numbering and did not change; dated entries in `docs/decisions.md` use the chapter numbers the page had when they were written (the last column).

| Page chapter | results.json key (unchanged) | Chapter number on the page before |
|---|---|---|
| The data (unnumbered) | `chapter_1` | 1. The question and the data (its heatmap is now in 10) |
| 1. Anatomy of a storm: Isaias, October 2026 | `chapter_2` | 2 |
| 2. How much goes dark | `chapter_3` | 3 |
| 3. How fast it comes back | `chapter_4` | 4 |
| 4. Why sites go dark | `chapter_5` | 5 |
| 5. The power coupling | `chapter_6`, `v2_3_power_cell_timing` | 6 (and 12, now a subsection) |
| 6. Running on backup power (Exploratory) | `v2_2_backup_power` | 11 |
| 7. Exposure | `chapter_7` | 7 |
| 8. Social vulnerability | `chapter_8` | 8 |
| 9. Mobile providers (Exploratory) | `v2_5_network_redundancy`, `v2_5_groups` | 13 |
| 10. Where the reports stop (Exploratory) | `v2_1_public_record_misses`, `chapter_1` | 10 (its heatmap was in 1) |
| 11. How complete the reports are (Exploratory) | `v2_1_1_report_card` | 14 |
| 12. Did the rules help? | `chapter_9` | 9 |

## How to cite

The repository is archived on Zenodo. For specific numbers, cite the version DOI shown on the Zenodo record of the version you used; for the work in general, cite the concept DOI:

- In general (all versions; resolves to the latest): Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24477809
- Version 2.0.0: Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) (Version 2.0.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24477811
- Version 2.1.0: Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) (Version 2.1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24480432
- Version 3.0.0: Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) (Version 3.0.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24514963
- Version 3.1.0: Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) (Version 3.1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24534469
- Version 3.1.1: Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) (Version 3.1.1) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24537335
- Version 3.2.0: Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) (Version 3.2.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24542647
- Version 3.2.1: Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) (Version 3.2.1) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24595378
- Version 4.0.0 (this one) gets its own DOI when it is released; until then, cite the concept DOI.

`CITATION.cff` lists every DOI, and GitHub's "Cite this repository" button reads it.

## Corrections and contributing

Every correction made so far is in `ERRATA.md` (generated from the decision log). To report a data error, use the issue form described in `CONTRIBUTING.md`.

## Versions

major: an existing published value, or the meaning of a variable, changes; minor: rows, storms, files or variables are added and every existing published value is unchanged; patch: no value changes (bytes may change, for example a format or documentation fix, and the changelog says so) (`CHANGELOG.md`).

## Disclosure

Competing interests: The author works for a cable operator. This is independent work on public data only; no employer data, time or resources were used, and the employer has no role in it. Funding: none. The views are the author's alone, and the author has no financial interest in any FCC proceeding. Contact: timothy@thresholddatasciences.com. AI assistance: `AI_ASSISTANCE.md`.
