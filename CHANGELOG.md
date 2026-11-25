# Changelog

This project follows [Semantic Versioning](https://semver.org/): a major version changes a published number or a
variable's meaning, a minor version adds data or variables, a patch fixes documentation or code without changing
any output.

## [3.1.1] - 2026-11-25

Documentation and metadata only. No file under `data/` changes, and no number.

### Added
- `.zenodo.json`: the Zenodo archive's metadata, written by the build from `CITATION.cff` (title, creator with ORCID,
  licence CC-BY-4.0, keywords, version, date) and the README's summary, with upload type dataset and the related
  identifiers in `code/manifest/related_identifiers.csv`, each checked before it was added (the table says how and
  when): the page (isDocumentedBy); Olukola et al. 2026, Brelsford et al. 2024, EAGLE-I on figshare (version 4, the
  files used), FCC 22-50, DA 25-74, FCC 26-34 and the FCC's 2017 season report (references); the FCC's Past Response
  Efforts page (isDerivedFrom). Zenodo uses `.zenodo.json` instead of `CITATION.cff` when it archives a release.
  `code/tests/test_zenodo_json.py` validates it against Zenodo's legacy deposit schema (saved in `code/tests/schemas/`
  with its source and SHA-256) and checks it against `CITATION.cff`; `CONTRIBUTING.md` explains it.
- `DATASHEET.md`, following Gebru et al.'s "Datasheets for Datasets": motivation, composition, collection,
  preprocessing, uses (with uses not supported and known limitations), distribution and maintenance, every number
  generated from `results.json` or the data. Linked from the README and the page's methods, and listed in
  `datapackage.json`.
- The version 3.1.0 DOI (10.5281/zenodo.24534469) in `CITATION.cff` and the README, added after its release.
- The page was restructured (November 25, 2026) and numbers its chapters 1 to 12; a table in the README and
  `CODEBOOK.md` maps each page chapter to its `results.json` key (the keys are unchanged) and to its earlier number.

### Changed
- Keywords (`CITATION.cff`, `.zenodo.json`): FCC DIRS, cell site outages, hurricanes, telecommunications resilience,
  power outages, EAGLE-I, disaster recovery, public records.
- `ERRATA.md` is for readers: one row per change to a published number, by version (what changed, before and after,
  why), from the CORRECTION entries that changed published data (`code/manifest/errata.csv`, checked word for word
  against `docs/decisions.md`). Process corrections stay in `docs/decisions.md` only.
- Dependabot proposes updates to the GitHub Actions only: CI installs from `requirements.lock`, so pip update pull
  requests would pass without testing the new versions (`CONTRIBUTING.md`, Updating packages).
- README: the page's wording on what the FCC's counts measure replaces "A site out is a site out", and a note says
  how much `clean_rows(level="strict")` keeps.

## [3.1.0] - 2026-11-25

Usability and maintenance. No published number changes: `dirs_county_day.csv`, `storms.csv`, the validation tables
and `results.json` are as in 3.0.0 (the reproduction test compares them), and the analysis-ready panel differs only by
its new column.

### Added
- External validation against the FCC's own summary, the 2017 Atlantic Hurricane Season Impact on Communications
  report (DOC-353805A1, August 2018; now in `data/input/rules/`). Every county or state figure it gives for Harvey and
  Irma (80) is transcribed with its page in `code/manifest/external_fcc_2017_report.csv` and compared with the
  matching report by the new step `code/src/15_external_validation.py`: 55 match, 4
  match once the FCC's dropped decimals are allowed for, 1 is consistent with a figure given in words,
  10 differ and 10 cannot be compared (switching centers, PSAPs, broadcast stations,
  providers' filings). Every difference is explained or marked as not explained, and none points to an error in the
  panel. Table: `data/analysis/validation/external_validation_fcc_2017.csv` and `docs/external_validation.md`; summary
  in the README and the page's methods. No data were changed because of it.
- `days_since_day0` in the analysis-ready panel: the documented name for `days_since_landfall` (same values), since
  day 0 is not always a landfall. `days_since_landfall` stays as a deprecated alias until 4.0.0.
- `clean_rows(panel, level="standard" | "strict")` in `code/src/load.py`, documented in `CODEBOOK.md` (Cleaning
  levels): which rows each level drops and why.
- `examples/quickstart.ipynb`: loads the panel and rebuilds two headline figures, the recovery curves with the
  median time to 50% restored (chapter 4) and the pooled cause shares (chapter 5), checking each against
  `results.json`. CI runs it with nbmake.
- `CONTRIBUTING.md`; a "Report a data error" issue form (`.github/ISSUE_TEMPLATE/data_error.yml`: storm, report DOC,
  county, what is wrong, evidence); `ERRATA.md`, generated from the CORRECTION entries of `docs/decisions.md`.
- CI: a monthly scheduled run (the 1st of each month), a ruff lint step (`ruff.toml`: pyflakes and the pycodestyle
  error and warning rules) and the notebook check. Dependabot (`.github/dependabot.yml`) proposes updates to the
  Actions and the Python packages weekly.
- `docs/restructure_plan.md`: the package layout planned for 4.0.0. No file is split or moved in this release.

### Changed
- `load_panel()` parses `report_date` and `dirs_activation_date` as dates (pandas datetime64, no time zone), from
  the CSV and the Parquet alike; they were text. Comparisons with "YYYY-MM-DD" strings still work; string methods on
  those two columns no longer do.
- Every GitHub Action is pinned to a commit SHA, at its current release: checkout v7.0.1, setup-python v7.1.0 and
  upload-artifact v7.0.2 (from v4, v5 and v4; they run on Node.js 24, which GitHub-hosted runners support). None of
  their breaking changes touches this workflow, and CI confirms the build artifacts still upload.
- `requirements.txt` adds matplotlib (already a dependency), nbmake, ipykernel and ruff; `requirements.lock` is
  regenerated, and no version already pinned changes.
- Lint fixes, with no change in behavior: unused imports and variables removed, a constant moved below the imports,
  a lambda given a name, one ambiguous variable renamed, f-strings without placeholders made plain strings.
- The version 3.0.0 DOI (10.5281/zenodo.24514963) in `CITATION.cff` and the README (added after its
  release).

### Note on the 3.0.0 archive
- The 3.0.0 archive on Zenodo (10.5281/zenodo.24514963) holds a decision log (`docs/decisions.md`) that
  predates two wording fixes made on main after the release: the display-rounding correction entry now names only
  Nicholas's site-days lost (114 to 115), and the word "correction" in a notes entry is in lower case, so that entry is
  no longer listed among the page's corrections. Main also adds a log entry for the 3.0.0 release itself. No number
  differs. This release's archive carries the fixed log.

## [3.0.0] - 2026-11-24

A major version, as this file's rule requires, because published numbers change. Two parts: corrections to how
the FCC's reports and notices were read, which change published numbers, and engineering hardening, which changes
no finding.

### Correction: Harvey Sep 4-5, 2017 table layout

The Harvey correction, and the corrections that followed from rechecking every report and notice after it: two
restored reports (Harvey Sep 3 and Nate, 2017), the reporting areas read from the FCC's notices (several storms),
and one county name.

- The FCC's Harvey reports for Sep 3, 4 and 5, 2017 print the previous day's sites out and % out before today's. The
  parser had read the previous day as the report's own figures, and put today's count and % into the damage and
  transport columns. It now detects the two-day header and reads today's columns. Tests from the reports' own text:
  `code/tests/test_two_day_layout.py`.
- Two parser misses had kept four Harvey reports' totals from being read, so they were never reconciled: Sep 3-5
  print "Total" rather than "TOTAL", and in Aug 28 the page-footer pattern took "TOT" from the TOTAL line after it
  (any three capitals counted as a time zone). Both are fixed. A sweep of every report, in its text and its PDF,
  finds no other total line left unread; against the 2.1.0 parser only these four Harvey reports change. No report
  is flagged `no_printed_totals` any more (three reports in use had been, all through these misses).
- Two new checks stop the build, for every report: a count that is not a whole number, and a previous-day column
  that differs from the previous day's report for the same county. Only Harvey Sep 3-5 print a previous-day column,
  and every one matches.
- With their totals read, Sep 4 and Sep 5 print a Texas total of 4,200 sites served over county rows that add up to
  4,199 (the same rows as Sep 3, which prints 4,199). Recorded as checked FCC inconsistencies
  (`code/manifest/known_fcc_inconsistencies.csv`, kind `state_total`; the rows' sum is used, the printed value kept);
  the reports' status is `known_fcc_inconsistency`, which outranks a flag.
- Restored after the parser fix: Harvey Sep 3, 2017, whose Matagorda and San Patricio rows are broken in both its
  text and its PDF, is kept because a new rule counts a row as confirmed (and flags it) when the next report's
  previous-day column reprints it exactly, as Sep 4 does for all 13 of Sep 3's counties. Nate, Oct 9, 2017, which
  prints no headline %, is kept because a missing headline is now a flag (`headline_missing`), not an exclusion,
  where the rows are confirmed and the printed totals reconcile. Nate joins the peak tables; with one report it is
  left out of the recovery summaries, as Nicole is. Its BDC release (the earliest, as for every storm before 2022)
  is added to `storm_releases.json` from the saved release list, with no new download.
- Notice areas: the reader of the FCC's DIRS notices had glued text onto some county names ("Wharton Note that
  ...", "York Washington D.C: ...", "Baton Rouge (East)", footnote digits, a sentence read as a name, two names with
  no comma), so those counties counted as outside the storm's reporting area. Fixed, with tests from the real
  notices (`code/tests/test_notices.py`) and one checked correction (`code/manifest/notice_name_corrections.csv`).
  Every notice county name in the study states now matches a Census county (ignoring spacing and punctuation) or a
  listed FCC misspelling. Reports
  with counties outside the notice area go from 16 to 9; validation from 134 flagged and 36 ok to 126 and 44. No
  headline result changes.
- County names: a name broken across lines in Harvey Sep 3's table ("MATAGORD A") takes the spelling of the
  report's own county list ("MATAGORDA"). A build check requires every county name in the panel to match its
  report's list, a checked spelling variant (`code/manifest/county_spelling_variants.csv`: three misspellings in
  the FCC's lists) or, for a county in the table but not the list, its Census name.
- Counts: storms 21 to 22, reports in use 167 to 169, excluded reports 7 to 5.
- Numbers that change (2.1.0, then 3.0.0): the median peak share 10.3% to 9.8%; Harvey's site-days lost 1,474 to
  1,424 and its share restored by its last report 74.8% to 74.0%; the median site-days lost 2,124 to 2,099; sites
  still out in the FCC's last report 1,883 in 21 storms to 1,887 in 22 (Harvey 70 to 73); the power vs. cell order
  (cell first 158 to 159, undetermined 148 to 147); chapter 7's and chapter 8's model estimates move slightly
  (inside 64 knots 47.9 to 48.4; SVI Q4 interval 0.90 to 1.46 becomes 0.90 to 1.45); validation counts and the
  chapter 14 report card; and figures counted over storm-counties (chapter 9's P0 row, the map's county-reports,
  chapter 7's calibration table). Every per-storm bootstrap interval is also recomputed with the stable seed below.
  The main changes are in
  `docs/decisions.md` (2026-11-24) and on the page's Corrections list; `data/analysis/results.json` holds every
  value. No finding's wording changes.
- A displayed number that is an exact half now rounds up, as the page's rule states (it had been stored just below
  the half): Nicholas's site-days lost 114 to 115. (Harvey's site-days lost is now 1,424 after the correction, and
  Irma's peak interval is recomputed with the stable seed.)

### Engineering hardening (no change to findings)
- Each storm's bootstrap seed is a stable hash of the global seed, the analysis stream and the storm key, not its
  position in date order, so adding or removing a storm never changes another storm's numbers
  (`code/tests/test_storm_seeds.py`). This recomputes every per-storm interval once (chapters 3 to 6); no estimate
  changes.
- `results.json`: every float is written to 10 significant digits, so last-bit differences between platforms' math
  libraries do not show. Apart from the correction above, every number is within a relative 1e-9 of 2.1.0. The
  reproduction test and the version 1 results test compare numbers with a relative tolerance of 1e-8 (with an
  absolute floor of 1e-12 for values that are zero up to floating-point noise) and text exactly (the version 1
  test's SHA-256 fingerprints are replaced by a snapshot of the values, `code/tests/snapshots/v1_results.json`). The panel, storm and validation CSVs are still compared byte for byte.
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
