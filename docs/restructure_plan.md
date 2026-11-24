# Restructure plan for 4.0.0

Written for 3.1.0 (2026-11-24). Nothing here is done in 3.x: no file is split or moved until 4.0.0, so every 3.x path
in the README, CODEBOOK and decision log stays valid. 4.0.0 is a major version because paths and the deprecated
column change, not because any number does; the reproduction tests must pass unchanged through every step below.

## Why

Three files carry most of the code and mix concerns:

| File | Lines (3.1.0) | What it mixes |
|---|---|---|
| `src/10_analysis.py` | about 1,850 | chapters 1 to 9, shared helpers (peaks, recovery curves, bootstrap, flags), results.json writing |
| `src/11_build_page.py` | about 1,870 | the page text for every chapter, figures, the map, metadata, citation boxes; needs the website |
| `src/14_data_repo.py` | about 1,700 | copying inputs, datapackage and codebook, README, CHANGELOG, CITATION, CI, tests as strings |

The numbered scripts import one another with `importlib` (`step10 = importlib.import_module("10_analysis")`), because
module names cannot start with a digit. The page and repository builders are publishing tools, yet they ship in the
analysis code.

## Target layout

```
code/
  wtngd/                      the package (import wtngd)
    config.py                 paths and constants (one file; the public repo's paths by environment variable)
    load.py                   load_panel(), clean_rows() (unchanged API)
    ingest/                   download.py, notices.py, reporting_areas.py           (steps 2, 2b)
    parse/                    dirs_parser.py, parse_reports.py                       (step 3)
    validate/                 reconcile.py, flags.py, known_inconsistencies.py       (step 4)
    panel/                    fips.py, eaglei.py, nhc.py, covariates.py, bdc.py, build.py, analysis_ready.py
    analysis/
      common.py               report_totals, peak_report, recovery_curve, bootstrap, storm_seed, flag classes
      ch01_data.py ... ch09_rules.py, ch10_last_report.py ... ch14_report_card.py
      results.py              rounding, key order, writing results.json
    checks/external.py        step 15
  pipeline.py                 the run order as data; `python -m wtngd.pipeline [--from STEP]` replaces run_all.py
  tests/                      mirrors wtngd/ (tests/analysis/test_ch04.py, ...)
tools/                        not part of the published package
  page/                       the page builder (today 11 and 13), moved to the website repository
  release/                    the data-repository builder (today 14), split: inputs.py, datapackage.py, docs.py,
                              templates/ (README, CHANGELOG, CI, tests and CONTRIBUTING as files, not strings)
```

## Steps (each its own commit, each passing the reproduction tests)

1. Package skeleton: add `wtngd/` with `config.py` and `load.py`; the numbered scripts import from it. Nothing moves.
2. Shared analysis helpers move to `wtngd/analysis/common.py`; `10_analysis.py` and `12_v2_analysis.py` import them.
   Replaces every `importlib.import_module("10_analysis")`.
3. One module per chapter, moved function by function; the chapter functions keep their names and signatures, and
   `results.py` keeps results.json's key order (the reproduction test checks it).
4. Steps 2 to 9 and 15 move into `ingest/`, `parse/`, `validate/`, `panel/`, `checks/`, each with a `main()`; the
   numbered files become one-line wrappers for one minor version, then go.
5. `pipeline.py` replaces `run_all.py` (same steps, same order, `--from` to restart); CI calls it.
6. The page builder moves to the website repository, reading `results.json` and the figure CSVs from a tagged release
   of this repository; it stops being shipped here.
7. The repository builder moves to `tools/release/`, its long strings become template files, and the generated tests
   become ordinary files in `tests/`.
8. Remove the deprecated `days_since_landfall` column (alias of `days_since_day0` since 3.1.0) and log it.

## What does not change

Every published number, column (except the deprecated alias), file in `data/`, `results.json` key, test assertion and
the seeds. `load_panel()` and `clean_rows()` keep their signatures. The decision log, ERRATA and the analysis plan as
committed keep their paths in `docs/`.

## Risks and checks

- Imports that change module state (constants read at import) are moved with the code that reads them; the
  reproduction tests and the version 1 snapshot test catch any number that moves.
- Ruff stays on throughout; a split that leaves an unused import fails CI.
- The CHANGELOG for 4.0.0 lists every moved path, old and new.
