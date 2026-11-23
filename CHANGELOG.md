# Changelog

This project follows [Semantic Versioning](https://semver.org/): a major version changes a published number or a
variable's meaning, a minor version adds data or variables, a patch fixes documentation or code without changing
any output.

## [Unreleased]

### Added
- The Zenodo DOIs (concept 10.5281/zenodo.24477809; version 2.0.0: 10.5281/zenodo.24477811) in `CITATION.cff` and the README, with a DOI
  badge and a How to cite section.

### Changed
- `code/src/11_build_page.py` (the page builder, not run by `run_all.py`): the page's How to cite box, Dataset
  metadata and Reproduce it links; the site's old code folder is replaced by a pointer to this repository.
  `code/src/14_data_repo.py` writes the DOIs. No input, pipeline step or output changed.

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
