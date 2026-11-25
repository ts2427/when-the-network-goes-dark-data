# When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24477809.svg)](https://doi.org/10.5281/zenodo.24477809) [![CI](https://github.com/ts2427/when-the-network-goes-dark-data/actions/workflows/ci.yml/badge.svg)](https://github.com/ts2427/when-the-network-goes-dark-data/actions/workflows/ci.yml)

Version 3.1.0 (2026-11-24). Data: CC BY 4.0 (`LICENSE-DATA.md`). Code: MIT (`LICENSE`).

The data and code behind the page *When the Network Goes Dark* (https://thresholddatasciences.com/analysis/when-the-network-goes-dark/): a county-by-report panel of FCC DIRS cell-site outages for 22 storms in ten Gulf and Southeast states, 2017-2026, each report checked against its printed totals, joined to power outages (EAGLE-I), storm tracks (NHC), social vulnerability (CDC/ATSDR SVI) and broadband provider counts (FCC BDC). Every number on the page is in `data/analysis/results.json`, and `run_all.py` rebuilds it and the panel from `data/input/`.

Associations, not causes. A site out is a site out: the FCC's counts describe the network, not how many people lost service.

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
                 panel_analysis_ready.csv and .parquet (the panel with every covariate the analysis uses)
code/src/        numbered pipeline steps, load.py (load_panel(), clean_rows()); code/manifest/
                 hand-made tables; code/tests/
examples/        quickstart.ipynb: load the panel and rebuild two headline figures
.github/         CI (lint, tests, the notebook and a full rebuild on Linux and Windows, on every push
                 and monthly), Dependabot, the 'Report a data error' issue form
docs/            analysis plan (as committed, with SHA-256), addendum, decision log, sources notes,
                 update_procedure.md (how a new season and a new version are added and released),
                 external_validation.md (the check against the FCC's 2017 season report),
                 restructure_plan.md (the layout planned for 4.0.0)
ERRATA.md        every correction, from the decision log; CONTRIBUTING.md: how to report an error
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

## Analysis plan

The analysis plan was committed on November 22, 2026, in the project's private version-controlled repository (commit 9fc17a4, 2026-11-22T16:16:48-06:00), before any recovery outcome was computed. The plan file as committed is `docs/analysis_plan_as_committed_9fc17a4.md`, SHA-256 `d4aa966e3874d69bc256bbe1c8d1153da9fb35429551d2bae25403e61db1dd8e` (git blob `28c91c70c8be9194848957569fab1e7f5515d345`), so it can be checked against later changes. It is not blind to some figures, which the plan lists. Deviations are in `DEVIATIONS.md`.

## Data availability and provenance

| Data | Location | Provider | Terms | Included | Size |
|---|---|---|---|---|---|
| FCC DIRS reports (PDF and text) | `data/input/dirs/` | FCC | Public domain (U.S. government) | yes | 103.7 MB |
| FCC DIRS notices | `data/input/notices/` | FCC | Public domain | yes | 0.4 MB |
| FCC orders cited for dates | `data/input/rules/` | FCC | Public domain | yes | 2.8 MB |
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

Exact attribution for each source: `SOURCES.md`. Variables: `CODEBOOK.md` and `datapackage.json`.

## Computational requirements

- Python 3.13 (tested with 3.13.2 on Windows 11). Reproduced on Windows and Linux: CI rebuilds everything and runs the reproduction tests on windows-latest and ubuntu-latest with Python 3.13 on every push (badge above).
- Packages: `requirements.txt` (exact versions of the packages used) and `requirements.lock` (every package, including dependencies, pinned with SHA-256 hashes for Windows, Linux and macOS; generated with `uv pip compile requirements.txt --universal --generate-hashes --python-version 3.13 -o requirements.lock`). For an exact environment: `python -m pip install --require-hashes -r requirements.lock`.
- Memory: about 4 GB. Disk: about 200 MB for the repository and `build/`.
- Run time: 12.4 minutes for `run_all.py`, measured on the author's Windows 11 laptop on 2026-11-23 (most of it is parsing the reports in step 3 and the bootstrap in step 10).
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
| 1 | `02b_reporting_areas.py` |  | each storm's reporting area from the FCC notices (rewrites code/manifest tables; the test checks they are unchanged) |
| 2 | `03_parse_dirs.py` |  | parse every DIRS report (text first, PDF fallback) into county rows and totals |
| 3 | `04_validate_dirs.py` |  | reconcile county rows with each report's printed totals; validation tables |
| 4 | `05_fips.py` |  | county names to FIPS |
| 5 | `06_eaglei.py` |  | match EAGLE-I (from the published extract) to each report's as-of time |
| 6 | `07_nhc.py` |  | tracks, wind radii, distance to track, day 0 |
| 7 | `08_fema_svi_bdc.py` |  | ACS, SVI and OpenFEMA declarations (from the stored files; no request is made) |
| 8 | `09_build_panel.py` |  | the panel, the storm table and dirs_county_day.csv |
| 9 | `10_analysis.py` | 3 4 5 6 7 8 9 | chapters 3-9 to results.json |
| 10 | `10_analysis.py` | 1 2 | chapters 1 and 2 (run second so results.json keeps the published key order) |
| 11 | `12_v2_analysis.py` | v2_1 v2_2 v2_3 v2_5_groups v2_5 report_card | chapters 10-14 to results.json |
| 12 | `12b_analysis_ready.py` |  | the analysis-ready panel (CSV and Parquet): the panel with every covariate |
| 13 | `15_external_validation.py` |  | external check against the FCC's 2017 season report (Harvey and Irma figures) |

`code/tests/test_reproduction.py` then compares `build/` with `data/analysis/`: `dirs_county_day.csv`, `storms.csv` and the validation tables byte for byte, `results.json` with numbers within a relative 1e-8 (absolute 1e-12 near zero) and everything else exactly, and the analysis-ready panel value by value. `code/tests/test_datapackage.py` checks `datapackage.json` with frictionless (`frictionless validate datapackage.json`: 0 errors).

## Page sections and figures

Each section of the page, its figures (the figure CSVs are published with the page), the key in `results.json` and the script that produces it. The page itself is built by `code/src/11_build_page.py`, which needs the website and is not run here.

| Page section | Figures | results.json key | Script |
|---|---|---|---|
| Opening, How to read it |  | chapter_3, chapter_4, v2_1_public_record_misses | 10_analysis.py, 12_v2_analysis.py |
| Map: where cell sites were out | storm map (hurricane-map.json) | panel (dirs_county_day.csv) | 09_build_panel.py; map data written by 11_build_page.py |
| 1. The question and the data | fig-coverage: hurricane-coverage-heatmap.csv | chapter_1 | 10_analysis.py |
| 2. Anatomy of a storm: Isaias | fig-isaias-map: hurricane-isaias-map.csv; fig-isaias: hurricane-isaias-counties.csv | chapter_2 | 10_analysis.py (track: 07_nhc.py) |
| 3. How much goes dark | fig-peaks: hurricane-peaks.csv | chapter_3 | 10_analysis.py |
| 4. How fast it comes back | fig-curves: hurricane-recovery-curves.csv; fig-restored: hurricane-restored.csv | chapter_4 | 10_analysis.py |
| 5. Why sites go dark | fig-causes: hurricane-causes.csv | chapter_5 | 10_analysis.py |
| 6. The power coupling | fig-power-overlay: hurricane-power-overlay.csv; fig-power: hurricane-power-lags.csv | chapter_6 | 10_analysis.py (EAGLE-I match: 06_eaglei.py) |
| 7. Exposure | fig-zone: hurricane-wind-zone.csv; fig-distance: hurricane-distance.csv; fig-calibration (methods): hurricane-calibration.csv | chapter_7 | 10_analysis.py (exposure: 07_nhc.py) |
| 8. Who waits longest | fig-svi: hurricane-svi-wait.csv | chapter_8 | 10_analysis.py (SVI: 08_fema_svi_bdc.py) |
| 9. Did the rules help? |  | chapter_9 | 10_analysis.py |
| 10. What the public record misses |  | v2_1_public_record_misses | 12_v2_analysis.py v2_1 |
| 11. Sites on backup power |  | v2_2_backup_power | 12_v2_analysis.py v2_2 |
| 12. Which comes back first: power or cell service? |  | v2_3_power_cell_timing | 12_v2_analysis.py v2_3 |
| 13. Do counties with more mobile providers recover differently? |  | v2_5_groups, v2_5_network_redundancy | 12_v2_analysis.py v2_5_groups v2_5 (counts: 06e, 06f) |
| 14. How complete are the FCC's public reports? |  | v2_1_1_report_card | 12_v2_analysis.py report_card (from the validation outputs) |
| Look up a county | county lookup (hurricane-county-lookup.json) | panel | 11_build_page.py |
| Methods, data and licenses | validation tables | chapter_1, validation/*.csv | 04_validate_dirs.py, 10_analysis.py |

## How to cite

The repository is archived on Zenodo. Cite the concept DOI for the data and code in general, and the version DOI when you use specific numbers:

- In general (all versions; resolves to the latest): Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24477809
- Version 2.0.0: Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) (Version 2.0.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24477811
- Version 2.1.0: Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) (Version 2.1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24480432
- Version 3.0.0: Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) (Version 3.0.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24514963
- Version 3.1.0: Spivey, T. D. (2026). When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code) (Version 3.1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24534469

`CITATION.cff` lists every DOI, and GitHub's "Cite this repository" button reads it.

## Corrections and contributing

Every correction made so far is in `ERRATA.md` (generated from the decision log). To report a data error, use the issue form described in `CONTRIBUTING.md`; a change to a published number is a new major version.

## Disclosure

The author works in the telecommunications industry. This analysis was done independently, on personal time, using only publicly available government data. It uses no employer data or confidential information, and the views are the author's alone. The author has no financial interest in any FCC proceeding. AI assistance: `AI_ASSISTANCE.md`.
