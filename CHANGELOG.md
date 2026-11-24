# Changelog

This project follows [Semantic Versioning](https://semver.org/): a major version changes a published number or a
variable's meaning, a minor version adds data or variables, a patch fixes documentation or code without changing
any output.

## [2.2.0] - 2026-11-24

Two parts: a correction to Harvey's last two reports (2017), which changes some published numbers, and engineering
hardening, which changes none.

### Correction: Harvey Sep 4-5, 2017 table layout
- The FCC's Harvey reports for Sep 3, 4 and 5, 2017 print the previous day's sites out and % out before today's. The
  parser had read the previous day as the report's own figures, and put today's count and % into the damage and
  transport columns. It now detects the two-day header and reads today's columns; it also reads these reports'
  totals (printed "Total", which it had missed, so they were never reconciled). Tests from the reports' own text:
  `code/tests/test_two_day_layout.py`.
- Two new checks stop the build, for every report: a count that is not a whole number, and a previous-day column
  that differs from the previous day's report for the same county. A sweep of all 178 reports finds only these three
  reports affected (Sep 3 stays excluded for its original reason); every previous-day column matches.
- With their totals read, Sep 4 and Sep 5 print a Texas total of 4,200 sites served over county rows that add up to
  4,199 (the same rows as Sep 3, which prints 4,199). Recorded as a checked FCC inconsistency
  (`code/manifest/known_total_inconsistencies.csv`); the reports' status is `known_fcc_inconsistency`.
- Numbers that change (2.1.0, then 2.2.0): Harvey's site-days lost 1,474 to 1,430; the median site-days lost across
  storms 2,124 to 2,102; Harvey's share restored by its last report 74.8% to 74.0%; sites still out in the FCC's
  last report 1,883 to 1,886 in total (Harvey 70 to 73); the power vs. cell order (cell first 158 to 159, power
  first 66 to 65, same report 127 to 128, undetermined 148 to 147); chapter 8's hazard ratios move by at most 0.01
  (2,761 to 2,759 intervals); validation counts and the chapter 14 report card for 2017. Every changed value is in
  `docs/decisions.md` (2026-11-24) and on the page's Corrections list. No finding's wording changes.
- Three displayed numbers that are exact halves now round up, as the page's rule states (they had been stored just
  below the half): Nicholas's site-days lost 114 to 115, Irma's peak interval upper end 6,039 to 6,040, and
  Harvey's site-days lost (now 1,430 after the correction).

### Engineering hardening (no change to findings)
- `results.json`: every float is written to 10 significant digits, so last-bit differences between platforms' math
  libraries do not show. Apart from the correction above, every number is within a relative 1e-9 of 2.1.0. The
  reproduction test and the version 1 results test compare numbers with a relative tolerance of 1e-9 and text
  exactly (the version 1 test's SHA-256 fingerprints are replaced by a snapshot of the values,
  `code/tests/snapshots/v1_results.json`). The panel, storm and validation CSVs are still compared byte for byte.
- Counts are written as integers (42, not 42.0) in `dirs_county_day.csv` (sites_served, sites_out, the three cause
  columns, on_backup_power, out_unattributed, out_overattributed), `storms.csv` (n_reports, n_counties) and
  `validation/validation_dirs.csv` (sites_unattributed, sites_overattributed); `datapackage.json` types them as
  integers. `out_overattributed` no longer has -0.0 values (they are 0); the codebook note about -0.0 is removed.
- `datapackage.json` validates with frictionless (0 errors): `created` is a full ISO 8601 date-time and the profile
  is `data-package` (results.json, the Parquet file and the plan file are not tables). Checked as a build step and by
  `code/tests/test_datapackage.py`; `frictionless` added to `requirements.txt`.
- New: `data/analysis/panel_analysis_ready.csv` and `.parquet`, the county-report panel (same rows and order as
  `dirs_county_day.csv`) joined with every covariate the analysis uses (EAGLE-I values and coverage flags, exposure,
  wind zone, day 0, SVI, ACS, and the BDC release, provider counts and chapter 13 group). Written by the new step
  `code/src/12b_analysis_ready.py`; documented in `datapackage.json` and `CODEBOOK.md`; loaded with `load_panel()` in
  the new `code/src/load.py`.
- New: continuous integration (`.github/workflows/ci.yml`): on every push, on ubuntu-latest and windows-latest with
  Python 3.13, install the locked environment, run the tests, validate `datapackage.json`, run `run_all.py`, then run
  the reproduction tests. CI badge in the README.
- New: `requirements.lock`, every package including dependencies pinned with SHA-256 hashes (uv pip compile,
  universal), alongside `requirements.txt`.
- Every test that needs `build/` skips with a reason ("run python run_all.py first") on a fresh clone; two tests that
  looked for build outputs in the wrong folder (and so always skipped here) now find them.
- Warnings: NumPy's 'generic' timedelta deprecation (steps 6 and 8) is fixed, and the expected 'invalid value
  encountered in subtract' from bootstrap draws that never reach a threshold (inf - inf inside NumPy's percentile
  interpolation; the bound is reported as none, as before) is no longer printed.
- A methods note wherever intervals appear (README, `CODEBOOK.md`, and the page's captions, How to read it and
  methods): the county bootstrap treats counties within a storm as independent, so those intervals may be somewhat
  narrow. A note on the method, not a change to any result.
- `storms.csv` is written by step 9; `run_all.py` no longer writes it separately.
- Documentation: `CODEBOOK.md` names the interval fields `ci_low` and `ci_high` (it said `lo` and `hi`); the 2.1.0
  entry below gives version 2.0.0's DOI (it had given 2.1.0's); the version 2.1.0 DOI
  (10.5281/zenodo.24480432) is in `CITATION.cff` and the README.

## [2.1.0] - 2026-11-23

### Added
- Chapter 14, "How complete are the FCC's public reports?" (exploratory: a descriptive summary of the existing
  validation results; addendum entry V2.1-1, committed before it was computed). For each storm and each year:
  reports with cause columns, causes short of or above sites out, headline mismatches, missing state totals, counties
  in the table but not the county list, counties outside the notice area, the backup-power column, and excluded
  reports, each with its denominator, plus a one-line summary per year. New key `v2_1_1_report_card` in
  `results.json`, written by `code/src/12_v2_analysis.py report_card` from the validation outputs; no new data.
- The Zenodo DOIs (concept 10.5281/zenodo.24477809; version 2.0.0: 10.5281/zenodo.24477811) in `CITATION.cff` and the README, with a DOI
  badge and a How to cite section.
- `docs/update_procedure.md`: how a new season and a new version are added and released.

### Changed
- `code/src/11_build_page.py` (the page builder, not run by `run_all.py`): chapter 14; the page's How to cite box,
  Dataset metadata and Reproduce it links; the site's old code folder is replaced by a pointer to this repository.

### Unchanged
- Every input, the panel, the storm table, the validation tables, and every other key of `results.json`.

## [2.0.0] - 2026-11-23

First release of this repository. The analysis is version 2 of the page.

### Added
- Version 2 analyses (chapters 10-13): sites still out in the FCC's last report, sites on backup power, power vs. cell
  timing, network redundancy from FCC Broadband Data Collection provider counts; the county lookup and the map.
- Inputs with provenance (`data/input/INPUTS.csv`), `datapackage.json`, `CODEBOOK.md`, `SOURCES.md`,
  `DEVIATIONS.md`, `CITATION.cff`, and `run_all.py`, which rebuilds the panel and `results.json` from `data/input`.
- The analysis plan as committed, with its SHA-256.

### Unchanged
- Every version 1 result (chapters 1-9); a test fails if one changes.

## [1.0.0] - 2026-11-22

Version 1 of the page (chapters 1-9) and the panel, published with the page's code snapshot.
