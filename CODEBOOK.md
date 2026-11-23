# Codebook

Generated from `datapackage.json` by `code/src/14_data_repo.py`; edit the package, not this file. Missing values are empty cells. Every variable's limitation is in the last column.

## `data/analysis/dirs_county_day.csv`

One row per county per FCC DIRS report in use (167 reports, 21 storms).

Primary key: `storm_key`, `doc_id`, `fips`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `storm_key` | string |  | Storm key: NHC ID and DIRS activation date, joined by an underscore. | Names repeat across years (Isaias 2020 and 2026); always join on this key, not the name. |
| `nhc_id` | string |  | National Hurricane Center storm ID (basin, number, year). |  |
| `storm` | string |  | Storm name. | Not unique across years. |
| `dirs_activation_date` | date |  | Date the FCC activated DIRS for the storm. |  |
| `rule_period` | string |  | FCC rule period by activation date. P0: Voluntary DIRS, voluntary Framework (2016-01-01 to 2024-04-30); P1: MDRI in force, DIRS voluntary (2024-05-01 to 2025-02-19); P2: MDRI + mandatory DIRS (2025-02-20 to 2026-06-29); P3: Streamlined DIRS (FCC 26-34) (2026-06-30 to present). | Descriptive grouping only; periods differ in storms, hazards and filers. |
| `doc_id` | string |  | FCC EDOCS document number of the report. |  |
| `report_date` | date |  | Date of the report. |  |
| `as_of_utc` | datetime | UTC | The report's stated as-of time, in UTC. | Where the report prints none, set to 12:00 Eastern on the report date (as_of_imputed). |
| `as_of_imputed` | boolean |  | True when as_of_utc was set to 12:00 Eastern because the report prints no time. |  |
| `report_status` | string |  | Validation status of the report (step 4): ok, flagged (a check raised a note) or known_fcc_inconsistency (a stated total the FCC's own rows do not sum to, listed in code/manifest/known_fcc_inconsistencies.csv). | Excluded reports are not in the file. |
| `state` | string |  | State, as printed. | Ten study states only. |
| `county` | string |  | County as printed by the FCC (upper case). | Spellings vary between reports; use fips. |
| `fips` | string |  | Five-digit county FIPS code (with leading zero). | Mapped from the printed name with code/manifest/fips_exceptions.csv. |
| `sites_served` | number | sites | Cell sites served in the county, as reported. | The denominator differs by storm and report; compare percentages with care. Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `sites_out` | number | sites | Cell sites out of service in the county, as reported. | Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `pct_out` | number | percent | Percent of sites out, as printed (computed from the two counts where not printed). | Where pct_printed is false the value is computed, not printed. |
| `pct_printed` | boolean |  | True when the report printed the percent column. |  |
| `out_damage` | number | sites | Sites out due to damage, as reported. | Blank where the report has no cause columns. Causes can overlap (see out_overattributed). |
| `out_transport` | number | sites | Sites out due to transport (backhaul), as reported. | Blank where the report has no cause columns. |
| `out_power` | number | sites | Sites out due to power, as reported. | Blank where the report has no cause columns. |
| `on_backup_power` | number | sites | Sites operating on backup power, as reported. | Blank where the report has no such column. Not a measure of sites about to fail. |
| `out_unattributed` | number | sites | Sites out with no cause given: sites_out minus the three causes, never below 0. | Blank where the report has no cause columns. Kept apart from out_overattributed; never net them. |
| `out_overattributed` | number | sites | Causes in excess of sites out (sites counted under more than one cause). | Blank where the report has no cause columns. May print as -0.0, which equals 0. |
| `area_status` | string |  | Whether the county is in the FCC's notice area on the report date: inside, inside_spelling_variant, outside_notice_area or table_not_in_list. | From the FCC's notices (code/manifest/reporting_areas.csv). |
| `fema_declared` | boolean |  | True if OpenFEMA lists a declaration for the storm covering the county. | Context for reuse only; no result uses it. This product uses the Federal Emergency Management Agency's OpenFEMA API, but is not endorsed by FEMA. |
| `time_flag` | string |  | Blank, or pre_onset_likely_marco for Laura's Aug 25, 2020 report (the FCC's combined Marco and Laura report), which is kept but left out of every time-based result. |  |

## `data/analysis/storms.csv`

One row per storm with a DIRS activation in scope, including storms with no usable report.

Primary key: `storm_key`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `nhc_id` | string |  | National Hurricane Center storm ID. |  |
| `dirs_activation_date` | date |  | Date the FCC activated DIRS. |  |
| `storm_key` | string |  | NHC ID and DIRS activation date. |  |
| `storm` | string |  | Storm name. | Not unique across years. |
| `rule_period` | string |  | FCC rule period by activation date. P0: Voluntary DIRS, voluntary Framework (2016-01-01 to 2024-04-30); P1: MDRI in force, DIRS voluntary (2024-05-01 to 2025-02-19); P2: MDRI + mandatory DIRS (2025-02-20 to 2026-06-29); P3: Streamlined DIRS (FCC 26-34) (2026-06-30 to present). | Blank for storms not in the panel. |
| `landfall_utc` | datetime | UTC | Day 0: the first time the storm's 34-kt wind radii reach a study-state county (fallback: first study-state landfall at tropical-storm strength or above). | Defined from NHC best-track radii; see docs/decisions.md (2026-11-23). |
| `landfall_source` | string |  | Which rule set day 0. |  |
| `previous_landfall_utc` | datetime | UTC | Day 0 under the original rule (kept for chapter 8's comparison). | Superseded; not used for the main results. |
| `interim_landfall_utc` | datetime | UTC | Day 0 under the first 2026-11-23 rule (kept for comparison). | Superseded; not used for the main results. |
| `n_reports` | integer | reports | Reports in the panel. | Blank for storms not in the panel. |
| `n_counties` | integer | counties | Counties in the panel. | Blank for storms not in the panel. |
| `first_report` | date |  | First report date in the panel. |  |
| `last_report` | date |  | Last report date in the panel. | The FCC's last public report, not the end of outages. |
| `excluded_reports` | string |  | Reports left out, with date and reason. |  |
| `in_panel` | boolean |  | True if the storm has at least one report in the panel. |  |

## `data/input/bdc/bdc_county_provider_counts.csv`

Derived from FCC Broadband Data Collection public data; no provider is named or identified.

Primary key: `release`, `fips`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `release` | date |  | FCC Broadband Data Collection release (as-of date). |  |
| `fips` | string |  | Five-digit county FIPS code. | Study-state counties only. |
| `mobile_half` | integer | providers | Mobile broadband providers reporting coverage of at least half of the county. | Reported coverage, not which networks were out; providers are never named. |
| `mobile_any` | integer | providers | Mobile broadband providers reporting any coverage in the county. | Reported coverage, not which networks were out. |
| `fixed_any_excl_near_universal` | integer | providers | Fixed providers with any residential service, near-universal providers excluded. | Near-universal: service in at least 95% of study-state counties. |
| `fixed_any` | integer | providers | Fixed providers with any residential service. | Includes near-universal (likely satellite or national fixed-wireless) providers. |
| `fixed_half` | integer | providers | Fixed providers serving at least half of residential locations. |  |
| `fixed_half_excl_near_universal` | integer | providers | As fixed_half, near-universal providers excluded. |  |

## `data/analysis/results.json`

Nested JSON, one key per chapter (`chapter_1` to `chapter_9`, then `v2_1_public_record_misses`, `v2_2_backup_power`, `v2_3_power_cell_timing`, `v2_5_groups`, `v2_5_network_redundancy`). Each number is stored with its interval (`lo`, `hi`), `n`, `unit` and `method` where it has them. The README maps each page section and figure to its key and script.
