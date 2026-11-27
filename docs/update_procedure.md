# Update procedure

How to add a hurricane season to *When the Network Goes Dark* and publish a new version of the data repository
(ts2427/when-the-network-goes-dark-data) and its Zenodo archive. Written for the 2027 season; the same steps apply
to later ones. This is a procedure, not a record: log every decision taken while following it in
`docs/decisions.md`, with who proposed and who chose.

The ground rules in `CLAUDE.md` still hold: public data only, company-neutral, every number from code, `data/raw/`
append-only with SHA-256, associations not causes.

## 1. Before the season: commit the 2027 analysis plan (by June 1, 2027)

1. Write `docs/analysis_plan_2027.md` before any 2027 report is read for outcomes. State what will be added (the
   2027 storms that meet the scope rules in `docs/analysis_plan.md`), what stays fixed (definitions, day 0,
   thresholds, the rebound rule, seeds, model specifications), and every result the update will report.
2. List, honestly, what has been seen already (for example, the FCC's public storm pages), as the 2026 plan did.
3. Commit it alone, before June 1, 2027, with a message saying it is committed before any 2027 recovery outcome is
   computed. Record the commit hash and date in `docs/decisions.md`; the page and the data repository will cite
   them, and the plan file as committed is published with its SHA-256.
4. The version 1 and version 2 results must not change. `tests/test_v1_results_unchanged.py` guards them; add the
   same fingerprint for every v2 key before the update starts.

## 2. During the season: archive each report when it is published

The FCC can now change DIRS reporting and its forms without notice (FCC 26-34 streamlined DIRS from June 30,
2026), so each report is archived as soon as it appears, not at the end of the season.

1. When the FCC activates DIRS for a storm in scope, add the storm to `manifest/storms.csv` (NHC ID and DIRS
   activation date; never key by name) and its notices to `manifest/fcc_storm_documents.csv`.
2. For each Communications Status Report: add one row to `manifest/dirs_reports.csv` (storm, NHC ID, activation date,
   report date and local time, EDOCS DOC number, PDF and text URLs from the FCC's own storm page; never a guessed
   DOC number), then run `src/02_download.py`.
3. Step 2 saves the PDF and the text file to `data/raw/dirs/` and logs each in `manifest/downloads.csv` with the URL,
   retrieval time (UTC) and SHA-256. Conduct is unchanged: approved URLs only, one request at a time at least 3
   seconds apart, the generic User-Agent, and a 403 or 429 (or any error) stops the run with no retry. A text URL that
   returns a "not found" page is logged as such and the PDF is used.
4. Never overwrite a raw file. If the FCC reissues a report, it gets a new DOC number and a new row.

## 3. Parser tests that fail loudly on any format change

The parser (`src/dirs_parser.py`) is tolerant of the layouts seen in 2017-2026. A new layout must stop the build,
never pass quietly.

1. Before parsing any 2027 report, add a format check to `tests/test_dirs_parser.py` that reads each 2027 report's
   text and asserts the table header (its column names, in order) is one of the headers already seen. An unknown
   header fails with the DOC number and the header printed.
2. Step 3 then parses, and step 4 (`src/04_validate_dirs.py`) reconciles every report: county rows must sum to the
   report's printed state and overall totals, every county must be in the report's own county list, and the
   headline percentage must match. A failure stops the build (status `fail`); nothing is published with a failed
   report.
3. For every layout change: add a real-text fixture from the new report and a test for it (as the 2017-2026 cases
   in `tests/test_dirs_parser.py` do), compare the parsed rows with the PDF by eye, and log the change.
4. If a report cannot be read reliably, exclude it in `manifest/excluded_reports.csv` with the reason. Exclusions are
   listed on the page and in the report card chapter.

## 4. After the season: wait for EAGLE-I's 2026 release

Power outages come from ORNL/DOE EAGLE-I, released yearly. The 2026 file is expected between February and April
2027.

1. Do not run the yearly update until the EAGLE-I release covering 2026 is published. Until then, 2026 storms keep
   "no EAGLE-I release" for power, as Isaias 2026 does now.
2. When it is published: read its figshare (or ORNL) record, confirm the licence (CC BY 4.0) on those specific files,
   add the files with their MD5s to `manifest/eaglei_files.csv`, and download with `src/06a_download_eaglei.py`
   (to `EAGLEI_RAW_DIR`; ask before any download over 1 GB). Cite the new DOI.
3. Rerun from step 6. The public repository publishes only the filtered extract, never the year files.

## 5. Build, check and publish

1. Run the pipeline (steps 02b to 12), then `pytest -q`: the v1 and v2 fingerprints must be unchanged.
2. Rebuild the page (step 11), the site (`python build.py`) and run `tools/a11y_audit.py` (0 violations) and the
   "Claude" guard (step 11 refuses a page that names the coding assistant).
3. Run an independent check of every new number (a separate, read-only check that recomputes from the panel).
4. Rebuild the public repository with `src/14_data_repo.py`, run `python run_all.py` there and
   `pytest code/tests` (the rebuilt files must match the published ones byte for byte), and review the scan
   (no secrets, no provider IDs, no file over 50 MB).

## 6. Release steps

1. **Version.** Semantic versioning (see `CHANGELOG.md`; stated exactly since 4.0.0, Tim's policy of 2026-11-27):
   major = an existing published value or the meaning of a variable changes; minor = rows, storms, files or
   variables are added and every existing published value is unchanged; patch = no value changes (bytes may change,
   and the changelog says so). A new season changes pooled results (medians, pooled shares), so it is a major version
   unless it is published as a separate module (`docs/roadmap_modules.md`). `code/tests/test_version_guard.py` in
   the data repository fails if a published file changes while the major number in `CITATION.cff` does not. Set `VERSION` and `RELEASE_DATE` in
   `src/14_data_repo.py` (it writes `CITATION.cff`, the README and `datapackage.json`) and `DATA_VERSION` in
   `src/11_build_page.py`.
2. **CHANGELOG.** Move the "Unreleased" notes in `src/14_data_repo.py`'s changelog under the new version and date,
   saying what was added, what changed and what did not.
3. **Commit and push** the data repository (`main`), then create the GitHub release: tag `v<version>` on that commit,
   title `v<version>`, notes from the CHANGELOG. Do not create a release from anything else.
4. **Zenodo.** The release is archived automatically and appears under the concept DOI (10.5281/zenodo.24477809)
   within a few minutes. Read the new record and confirm which DOI is the version DOI. Then edit the record: Zenodo's
   GitHub integration files every version as **Software**; set **Resource type** to **Dataset** and publish the
   edit (the DOIs do not change). Log it.
5. **Version DOI on the page.** Set `VERSION_DOI` and `ZENODO_FILE` (from the new record's file entry) in
   `src/11_build_page.py`, add the new DOI to `CITATION.cff`'s identifiers through `src/14_data_repo.py`, rebuild
   the page and the site, check the How to cite box and the Dataset JSON-LD (validator.schema.org), and push.
   Links that point to the files behind the page use the new tag.

First done for version 2.0.0 (record 24477811; resource type set to Dataset by the author on 2026-11-23).
