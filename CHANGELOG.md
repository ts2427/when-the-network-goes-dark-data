# Changelog

This project follows [Semantic Versioning](https://semver.org/): a major version changes a published number or a
variable's meaning, a minor version adds data or variables, a patch fixes documentation or code without changing
any output.

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
