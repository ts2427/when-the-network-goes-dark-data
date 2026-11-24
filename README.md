# When the Network Goes Dark: Gulf Coast cell-site outages in hurricanes, 2017-2026 (data and code)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24477809.svg)](https://doi.org/10.5281/zenodo.24477809) [![CI](https://github.com/ts2427/when-the-network-goes-dark-data/actions/workflows/ci.yml/badge.svg)](https://github.com/ts2427/when-the-network-goes-dark-data/actions/workflows/ci.yml)

Version 2.2.0 (2026-11-24). Data: CC BY 4.0 (`LICENSE-DATA.md`). Code: MIT (`LICENSE`).

The data and code behind the page *When the Network Goes Dark* (https://thresholddatasciences.com/analysis/when-the-network-goes-dark/): a county-by-report panel of FCC DIRS cell-site outages for 21 storms in ten Gulf and Southeast states, 2017-2026, each report checked against its printed totals, joined to power outages (EAGLE-I), storm tracks (NHC), social vulnerability (CDC/ATSDR SVI) and broadband provider counts (FCC BDC). Every number on the page is in `data/analysis/results.json`, and `run_all.py` rebuilds it and the panel from `data/input/`.

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
code/src/        numbered pipeline steps, load.py (load_panel()); code/manifest/ hand-made tables;
                 code/tests/
.github/         CI: the tests and a full rebuild on Linux and Windows on every push
docs/            analysis plan (as committed, with SHA-256), addendum, decision log, sources notes,
                 update_procedure.md (how a new season and a new version are added and released)
run_all.py       one command: rebuild the panel and results.json into build/
```

## Analysis-ready panel

`data/analysis/panel_analysis_ready.parquet` (and `.csv`) is `dirs_county_day.csv`, same rows and order, joined with every covariate the analysis uses: EAGLE-I power outages at each report's as-of time with its match and coverage flags, distance to the track, wind radii and chapter 7's wind zone, day 0 and days since day 0, SVI 2022, ACS 2022, and the storm's BDC release with its provider counts and chapter 13 group. Variables: `CODEBOOK.md`. To load it with its types:

```python
import sys
sys.path.insert(0, "code/src")
from load import load_panel
p = load_panel()   # the Parquet if present, else the CSV, with the same types
```

## Analysis plan

The analysis plan was committed on November 22, 2026, in the project's private version-controlled repository (commit 9fc17a4, 2026-11-22T16:16:48-06:00), before any recovery outcome was computed. The plan file as committed is `docs/analysis_plan_as_committed_9fc17a4.md`, SHA-256 `d4aa966e3874d69bc256bbe1c8d1153da9fb35429551d2bae25403e61db1dd8e` (git blob `28c91c70c8be9194848957569fab1e7f5515d345`), so it can be checked against later changes. It is not blind to some figures, which the plan lists. Deviations are in `DEVIATIONS.md`.

## Data availability and provenance

| Data | Location | Provider | Terms | Included | Size |
|---|---|---|---|---|---|
| FCC DIRS reports (PDF and text) | `data/input/dirs/` | FCC | Public domain (U.S. government) | yes | 103.7 MB |
| FCC DIRS notices | `data/input/notices/` | FCC | Public domain | yes | 0.4 MB |
| FCC orders cited for dates | `data/input/rules/` | FCC | Public domain | yes | 0.4 MB |
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

- Python 3.13 (tested with 3.13.2) on Windows 11; the code uses no platform-specific calls. CI runs the tests and a full rebuild on windows-latest and ubuntu-latest (badge above).
- Packages: `requirements.txt` (exact versions of the packages used) and `requirements.lock` (every package, including dependencies, pinned with SHA-256 hashes for Windows, Linux and macOS; generated with `uv pip compile requirements.txt --universal --generate-hashes --python-version 3.13 -o requirements.lock`). For an exact environment: `python -m pip install --require-hashes -r requirements.lock`.
- Memory: about 4 GB. Disk: about 200 MB for the repository and `build/`.
- Run time: 12.4 minutes for `run_all.py`, measured on the author's Windows 11 laptop on 2026-11-23 (most of it is parsing the reports in step 3 and the bootstrap in step 10).
- No network access is needed: every step reads `data/input/`. Steps 02, 06a, 06c, 06d and 06e (downloads and raw BDC reading) are included for transparency but are not run; they need the original sources and, for BDC, an FCC account.
- Random numbers: fixed seed 20261122 (bootstrap, 2,000 draws).
- Intervals: The county bootstrap (chapters 3 to 6 within each storm; chapters 8 and 13 across storm-counties) resamples counties as if they were independent. Counties hit by the same storm share its wind, flooding, power grid and networks, so their outcomes are correlated, and these intervals may be somewhat narrow. The storm bootstrap (medians and pooled shares across storms, chapter 7's zone shares, chapter 12) resamples whole storms, and the models in chapters 7, 8 and 13 use storm- or county-clustered intervals. This is a note on the method, not a change to any result.
- Floating point: `results.json` stores floats to 10 significant digits, and the reproduction test compares its numbers with a relative tolerance of 1e-9 (text exactly), because platforms' math libraries can differ in the last bits (about 1e-10 relative). The panel, storm and validation CSVs must match byte for byte; the analysis-ready panel is compared value by value at the same tolerance.

## Run order

```
python -m pip install -r requirements.txt   # or: --require-hashes -r requirements.lock
python -m pytest code/tests        # unit tests; the build checks skip until run_all.py has run
python run_all.py                   # rebuild into build/
python -m pytest code/tests        # now including the reproduction test (build/ vs data/analysis/)
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

`code/tests/test_reproduction.py` then compares `build/` with `data/analysis/`: `dirs_county_day.csv`, `storms.csv` and the validation tables byte for byte, `results.json` with numbers within a relative 1e-9 and everything else exactly, and the analysis-ready panel value by value. `code/tests/test_datapackage.py` checks `datapackage.json` with frictionless (`frictionless validate datapackage.json`: 0 errors).

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
- Version 2.2.0 (this one) gets its own DOI when it is released; until then, cite the concept DOI.

`CITATION.cff` lists every DOI, and GitHub's "Cite this repository" button reads it.

## Disclosure

The author works in the telecommunications industry. This analysis was done independently, on personal time, using only publicly available government data. It uses no employer data or confidential information, and the views are the author's alone. The author has no financial interest in any FCC proceeding. AI assistance: `AI_ASSISTANCE.md`.
