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
| `sites_served` | integer | sites | Cell sites served in the county, as reported. | The denominator differs by storm and report; compare percentages with care. Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `sites_out` | integer | sites | Cell sites out of service in the county, as reported. | Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `pct_out` | number | percent | Percent of sites out, as printed (computed from the two counts where not printed). | Where pct_printed is false the value is computed, not printed. |
| `pct_printed` | boolean |  | True when the report printed the percent column. |  |
| `out_damage` | integer | sites | Sites out due to damage, as reported. | Blank where the report has no cause columns. Causes can overlap (see out_overattributed). |
| `out_transport` | number | sites | Sites out due to transport (backhaul), as reported. | Blank where the report has no cause columns. |
| `out_power` | integer | sites | Sites out due to power, as reported. | Blank where the report has no cause columns. |
| `on_backup_power` | integer | sites | Sites operating on backup power, as reported. | Blank where the report has no such column. Not a measure of sites about to fail. |
| `out_unattributed` | integer | sites | Sites out with no cause given: sites_out minus the three causes, never below 0. | Blank where the report has no cause columns. Kept apart from out_overattributed; never net them. |
| `out_overattributed` | integer | sites | Causes in excess of sites out (sites counted under more than one cause). | Blank where the report has no cause columns. |
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

## `data/analysis/panel_analysis_ready.csv`

The rows of dirs_county_day.csv, in the same order, joined with EAGLE-I power outages and coverage flags, exposure and wind zone, day 0, SVI 2022, ACS 2022 and the BDC provider counts and chapter 13 group. Built by code/src/12b_analysis_ready.py; load it with load_panel() in code/src/load.py. Counts are integers; other numbers are written to 10 significant digits.

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
| `sites_served` | integer | sites | Cell sites served in the county, as reported. | The denominator differs by storm and report; compare percentages with care. Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `sites_out` | integer | sites | Cell sites out of service in the county, as reported. | Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `pct_out` | number | percent | Percent of sites out, as printed (computed from the two counts where not printed). | Where pct_printed is false the value is computed, not printed. |
| `pct_printed` | boolean |  | True when the report printed the percent column. |  |
| `out_damage` | integer | sites | Sites out due to damage, as reported. | Blank where the report has no cause columns. Causes can overlap (see out_overattributed). |
| `out_transport` | number | sites | Sites out due to transport (backhaul), as reported. | Blank where the report has no cause columns. |
| `out_power` | integer | sites | Sites out due to power, as reported. | Blank where the report has no cause columns. |
| `on_backup_power` | integer | sites | Sites operating on backup power, as reported. | Blank where the report has no such column. Not a measure of sites about to fail. |
| `out_unattributed` | integer | sites | Sites out with no cause given: sites_out minus the three causes, never below 0. | Blank where the report has no cause columns. Kept apart from out_overattributed; never net them. |
| `out_overattributed` | integer | sites | Causes in excess of sites out (sites counted under more than one cause). | Blank where the report has no cause columns. |
| `area_status` | string |  | Whether the county is in the FCC's notice area on the report date: inside, inside_spelling_variant, outside_notice_area or table_not_in_list. | From the FCC's notices (code/manifest/reporting_areas.csv). |
| `fema_declared` | boolean |  | True if OpenFEMA lists a declaration for the storm covering the county. | Context for reuse only; no result uses it. This product uses the Federal Emergency Management Agency's OpenFEMA API, but is not endorsed by FEMA. |
| `time_flag` | string |  | Blank, or pre_onset_likely_marco for Laura's Aug 25, 2020 report (the FCC's combined Marco and Laura report), which is kept but left out of every time-based result. |  |
| `eaglei_time` | datetime | UTC | Time of the EAGLE-I record matched to the report's as-of time. | Blank when no record lies within 30 minutes. |
| `eaglei_match` | string |  | EAGLE-I match at the as-of time: matched, no_record_within_30min, county_not_in_eaglei_window, no_as_of_time or no_eaglei_release (Isaias 2026; EAGLE-I ends in 2025). |  |
| `eaglei_gap_min` | number | minutes | Minutes between the matched record and the as-of time. |  |
| `eaglei_customers_out` | integer | customers | Electricity customers out at the as-of time. | ORNL/DOE EAGLE-I (CC BY 4.0); 'customers' are meters. Blank where no EAGLE-I record lies within 30 minutes of the time (never set to zero); see eaglei_match. |
| `eaglei_customers_out_6h` | integer | customers | Customers out 6 hours before the as-of time. | ORNL/DOE EAGLE-I (CC BY 4.0); 'customers' are meters. Blank where no EAGLE-I record lies within 30 minutes of the time (never set to zero); see eaglei_match. |
| `eaglei_customers_out_12h` | integer | customers | Customers out 12 hours before. | ORNL/DOE EAGLE-I (CC BY 4.0); 'customers' are meters. Blank where no EAGLE-I record lies within 30 minutes of the time (never set to zero); see eaglei_match. |
| `eaglei_customers_out_24h` | integer | customers | Customers out 24 hours before. | ORNL/DOE EAGLE-I (CC BY 4.0); 'customers' are meters. Blank where no EAGLE-I record lies within 30 minutes of the time (never set to zero); see eaglei_match. |
| `eaglei_customers_out_zero_filled` | integer | customers | As eaglei_customers_out, with no record counted as 0 where the county has an EAGLE-I record in the storm's window. | Sensitivity display only. |
| `eaglei_modeled_customers` | integer | customers | EAGLE-I modeled customers in the county (MCC.csv). | Below observed outages in some counties; see eaglei_mcc_flag. |
| `eaglei_pct_out` | number | percent | eaglei_customers_out as a percent of eaglei_modeled_customers. | Not used where eaglei_mcc_flag is not ok. |
| `eaglei_max_out_in_window` | integer | customers | Highest customers out in the storm's EAGLE-I window (21 days before activation to 21 days after deactivation). |  |
| `eaglei_release` | boolean |  | True if EAGLE-I covers the storm's year (through 2025). |  |
| `eaglei_mcc_flag` | string |  | ok, mcc_below_observed_outages (percent out not used) or no_mcc. |  |
| `eaglei_coverage_flag` | string |  | ok, low_coverage (state's minimum covered share below 0.75 that year; kept), coverage_unknown (no published coverage for the year) or no_eaglei_release. | Coverage is published by state and year only (2018-2022). |
| `eaglei_state_min_covered` | number | share (0-1) | State's minimum share of customers covered by EAGLE-I in the storm year. | Blank when not published. |
| `eaglei_state_max_covered` | number | share (0-1) | State's maximum share of customers covered in the storm year. | Blank when not published. |
| `min_dist_km` | number | km | Distance from the county's Census internal point to the storm's track (15-minute interpolation). | NHC HURDAT2; Isaias 2026 from the GIS best track. |
| `wind_kt_at_closest` | number | knots | Storm's maximum sustained wind at the track point closest to the county. |  |
| `in_34kt` | boolean |  | True if the county's internal point fell inside the 34-knot wind radii at some time. |  |
| `in_50kt` | boolean |  | True if inside the 50-knot wind radii at some time. |  |
| `in_64kt` | boolean |  | True if inside the 64-knot wind radii at some time. |  |
| `wind_zone` | string |  | Chapter 7's wind zone from the three radii: inside 64 kt, 50-64 kt, 34-50 kt or outside 34 kt. |  |
| `first_34kt_utc` | datetime | UTC | First time the county was inside the 34-knot wind radii. | Blank if never inside. |
| `nearest_landfall_utc` | datetime | UTC | The storm's HURDAT2 landfall nearest the county. | Blank for Isaias 2026 (no landfall marker in the GIS best track). |
| `nearest_landfall_km` | number | km | Distance from the county to that landfall. |  |
| `track_source` | string |  | HURDAT2 or GIS best track (Isaias 2026). |  |
| `landfall_utc` | datetime | UTC | Day 0: the first time the storm's 34-knot wind radii reach a study-state county. | Same for every county of a storm; see storms.csv. |
| `landfall_source` | string |  | Which rule set day 0. |  |
| `days_since_landfall` | number | days | Days from day 0 to the report's as-of time. |  |
| `svi_overall` | number | percentile (0-1) | CDC/ATSDR SVI 2022 overall national percentile rank (RPL_THEMES). | Chapter 8's quartiles are of the at-risk storm-counties, not of this column's national cut points. |
| `svi_socioeconomic` | number | percentile (0-1) | SVI 2022 theme 1, socioeconomic status (RPL_THEME1). |  |
| `svi_household` | number | percentile (0-1) | SVI 2022 theme 2, household characteristics (RPL_THEME2). |  |
| `svi_minority_language` | number | percentile (0-1) | SVI 2022 theme 3, racial and ethnic minority status (RPL_THEME3). |  |
| `svi_housing_transport` | number | percentile (0-1) | SVI 2022 theme 4, housing type and transportation (RPL_THEME4). |  |
| `acs_households` | integer | households | Households, ACS 2022 5-year (B11001_001E). |  |
| `acs_population` | integer | people | Population, ACS 2022 5-year (B01001_001E). |  |
| `acs_pct_65plus` | number | percent | Percent of the population aged 65 or over, ACS 2022 5-year (B01001). |  |
| `acs_pct_broadband` | number | percent | Percent of households with a broadband subscription, ACS 2022 5-year (B28002_004E / B28002_001E). |  |
| `bdc_release` | date |  | FCC Broadband Data Collection release matched to the storm: the latest on or before day 0, or the earliest for storms before 2022. |  |
| `bdc_role` | string |  | main (storms from 2022 on) or sensitivity: network data from after the storm. |  |
| `bdc_mobile_half` | integer | providers | Mobile providers covering at least half the county's area (chapter 13's main measure). | Reported coverage, not which networks were out; providers are never named. |
| `bdc_mobile_any` | integer | providers | Mobile providers with any coverage in the county. |  |
| `bdc_fixed_any_excl_near_universal` | integer | providers | Fixed providers with any residential service, near-universal providers excluded. |  |
| `bdc_fixed_any` | integer | providers | Fixed providers with any residential service. |  |
| `bdc_fixed_half` | integer | providers | Fixed providers serving at least half of residential locations. |  |
| `bdc_fixed_half_excl_near_universal` | integer | providers | As bdc_fixed_half, near-universal providers excluded. |  |
| `bdc_mobile_half_group` | string |  | Chapter 13's group on bdc_mobile_half: 2 or fewer, 3, or 4 or more (cut points fixed from counts only; results.json v2_5_groups). | For storms before 2022 (bdc_role 'sensitivity') the release postdates the storm; chapter 13's main analysis uses storms from 2022 on. |
| `first_report_date` | date |  | The county's first report in the storm's panel. |  |
| `last_report_date` | date |  | The county's last report in the storm's panel. |  |
| `n_reports_county` | integer | reports | Reports in the storm's panel that list the county. |  |
| `censoring` | string |  | none, left_reports_while_out (left the reports before the storm's last report while still out) or out_at_last_report. | Censored counties are not recovered. |

## `data/analysis/panel_analysis_ready.parquet`

The same table as panel_analysis_ready.csv, with its types (UTC datetimes, nullable integers) and full float precision. SHA-256 cf493ac3b57c25acfdfd1d301be13cd493818879836932cd050929c27450441d; 665735 bytes.

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
| `sites_served` | integer | sites | Cell sites served in the county, as reported. | The denominator differs by storm and report; compare percentages with care. Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `sites_out` | integer | sites | Cell sites out of service in the county, as reported. | Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `pct_out` | number | percent | Percent of sites out, as printed (computed from the two counts where not printed). | Where pct_printed is false the value is computed, not printed. |
| `pct_printed` | boolean |  | True when the report printed the percent column. |  |
| `out_damage` | integer | sites | Sites out due to damage, as reported. | Blank where the report has no cause columns. Causes can overlap (see out_overattributed). |
| `out_transport` | number | sites | Sites out due to transport (backhaul), as reported. | Blank where the report has no cause columns. |
| `out_power` | integer | sites | Sites out due to power, as reported. | Blank where the report has no cause columns. |
| `on_backup_power` | integer | sites | Sites operating on backup power, as reported. | Blank where the report has no such column. Not a measure of sites about to fail. |
| `out_unattributed` | integer | sites | Sites out with no cause given: sites_out minus the three causes, never below 0. | Blank where the report has no cause columns. Kept apart from out_overattributed; never net them. |
| `out_overattributed` | integer | sites | Causes in excess of sites out (sites counted under more than one cause). | Blank where the report has no cause columns. |
| `area_status` | string |  | Whether the county is in the FCC's notice area on the report date: inside, inside_spelling_variant, outside_notice_area or table_not_in_list. | From the FCC's notices (code/manifest/reporting_areas.csv). |
| `fema_declared` | boolean |  | True if OpenFEMA lists a declaration for the storm covering the county. | Context for reuse only; no result uses it. This product uses the Federal Emergency Management Agency's OpenFEMA API, but is not endorsed by FEMA. |
| `time_flag` | string |  | Blank, or pre_onset_likely_marco for Laura's Aug 25, 2020 report (the FCC's combined Marco and Laura report), which is kept but left out of every time-based result. |  |
| `eaglei_time` | datetime | UTC | Time of the EAGLE-I record matched to the report's as-of time. | Blank when no record lies within 30 minutes. |
| `eaglei_match` | string |  | EAGLE-I match at the as-of time: matched, no_record_within_30min, county_not_in_eaglei_window, no_as_of_time or no_eaglei_release (Isaias 2026; EAGLE-I ends in 2025). |  |
| `eaglei_gap_min` | number | minutes | Minutes between the matched record and the as-of time. |  |
| `eaglei_customers_out` | integer | customers | Electricity customers out at the as-of time. | ORNL/DOE EAGLE-I (CC BY 4.0); 'customers' are meters. Blank where no EAGLE-I record lies within 30 minutes of the time (never set to zero); see eaglei_match. |
| `eaglei_customers_out_6h` | integer | customers | Customers out 6 hours before the as-of time. | ORNL/DOE EAGLE-I (CC BY 4.0); 'customers' are meters. Blank where no EAGLE-I record lies within 30 minutes of the time (never set to zero); see eaglei_match. |
| `eaglei_customers_out_12h` | integer | customers | Customers out 12 hours before. | ORNL/DOE EAGLE-I (CC BY 4.0); 'customers' are meters. Blank where no EAGLE-I record lies within 30 minutes of the time (never set to zero); see eaglei_match. |
| `eaglei_customers_out_24h` | integer | customers | Customers out 24 hours before. | ORNL/DOE EAGLE-I (CC BY 4.0); 'customers' are meters. Blank where no EAGLE-I record lies within 30 minutes of the time (never set to zero); see eaglei_match. |
| `eaglei_customers_out_zero_filled` | integer | customers | As eaglei_customers_out, with no record counted as 0 where the county has an EAGLE-I record in the storm's window. | Sensitivity display only. |
| `eaglei_modeled_customers` | integer | customers | EAGLE-I modeled customers in the county (MCC.csv). | Below observed outages in some counties; see eaglei_mcc_flag. |
| `eaglei_pct_out` | number | percent | eaglei_customers_out as a percent of eaglei_modeled_customers. | Not used where eaglei_mcc_flag is not ok. |
| `eaglei_max_out_in_window` | integer | customers | Highest customers out in the storm's EAGLE-I window (21 days before activation to 21 days after deactivation). |  |
| `eaglei_release` | boolean |  | True if EAGLE-I covers the storm's year (through 2025). |  |
| `eaglei_mcc_flag` | string |  | ok, mcc_below_observed_outages (percent out not used) or no_mcc. |  |
| `eaglei_coverage_flag` | string |  | ok, low_coverage (state's minimum covered share below 0.75 that year; kept), coverage_unknown (no published coverage for the year) or no_eaglei_release. | Coverage is published by state and year only (2018-2022). |
| `eaglei_state_min_covered` | number | share (0-1) | State's minimum share of customers covered by EAGLE-I in the storm year. | Blank when not published. |
| `eaglei_state_max_covered` | number | share (0-1) | State's maximum share of customers covered in the storm year. | Blank when not published. |
| `min_dist_km` | number | km | Distance from the county's Census internal point to the storm's track (15-minute interpolation). | NHC HURDAT2; Isaias 2026 from the GIS best track. |
| `wind_kt_at_closest` | number | knots | Storm's maximum sustained wind at the track point closest to the county. |  |
| `in_34kt` | boolean |  | True if the county's internal point fell inside the 34-knot wind radii at some time. |  |
| `in_50kt` | boolean |  | True if inside the 50-knot wind radii at some time. |  |
| `in_64kt` | boolean |  | True if inside the 64-knot wind radii at some time. |  |
| `wind_zone` | string |  | Chapter 7's wind zone from the three radii: inside 64 kt, 50-64 kt, 34-50 kt or outside 34 kt. |  |
| `first_34kt_utc` | datetime | UTC | First time the county was inside the 34-knot wind radii. | Blank if never inside. |
| `nearest_landfall_utc` | datetime | UTC | The storm's HURDAT2 landfall nearest the county. | Blank for Isaias 2026 (no landfall marker in the GIS best track). |
| `nearest_landfall_km` | number | km | Distance from the county to that landfall. |  |
| `track_source` | string |  | HURDAT2 or GIS best track (Isaias 2026). |  |
| `landfall_utc` | datetime | UTC | Day 0: the first time the storm's 34-knot wind radii reach a study-state county. | Same for every county of a storm; see storms.csv. |
| `landfall_source` | string |  | Which rule set day 0. |  |
| `days_since_landfall` | number | days | Days from day 0 to the report's as-of time. |  |
| `svi_overall` | number | percentile (0-1) | CDC/ATSDR SVI 2022 overall national percentile rank (RPL_THEMES). | Chapter 8's quartiles are of the at-risk storm-counties, not of this column's national cut points. |
| `svi_socioeconomic` | number | percentile (0-1) | SVI 2022 theme 1, socioeconomic status (RPL_THEME1). |  |
| `svi_household` | number | percentile (0-1) | SVI 2022 theme 2, household characteristics (RPL_THEME2). |  |
| `svi_minority_language` | number | percentile (0-1) | SVI 2022 theme 3, racial and ethnic minority status (RPL_THEME3). |  |
| `svi_housing_transport` | number | percentile (0-1) | SVI 2022 theme 4, housing type and transportation (RPL_THEME4). |  |
| `acs_households` | integer | households | Households, ACS 2022 5-year (B11001_001E). |  |
| `acs_population` | integer | people | Population, ACS 2022 5-year (B01001_001E). |  |
| `acs_pct_65plus` | number | percent | Percent of the population aged 65 or over, ACS 2022 5-year (B01001). |  |
| `acs_pct_broadband` | number | percent | Percent of households with a broadband subscription, ACS 2022 5-year (B28002_004E / B28002_001E). |  |
| `bdc_release` | date |  | FCC Broadband Data Collection release matched to the storm: the latest on or before day 0, or the earliest for storms before 2022. |  |
| `bdc_role` | string |  | main (storms from 2022 on) or sensitivity: network data from after the storm. |  |
| `bdc_mobile_half` | integer | providers | Mobile providers covering at least half the county's area (chapter 13's main measure). | Reported coverage, not which networks were out; providers are never named. |
| `bdc_mobile_any` | integer | providers | Mobile providers with any coverage in the county. |  |
| `bdc_fixed_any_excl_near_universal` | integer | providers | Fixed providers with any residential service, near-universal providers excluded. |  |
| `bdc_fixed_any` | integer | providers | Fixed providers with any residential service. |  |
| `bdc_fixed_half` | integer | providers | Fixed providers serving at least half of residential locations. |  |
| `bdc_fixed_half_excl_near_universal` | integer | providers | As bdc_fixed_half, near-universal providers excluded. |  |
| `bdc_mobile_half_group` | string |  | Chapter 13's group on bdc_mobile_half: 2 or fewer, 3, or 4 or more (cut points fixed from counts only; results.json v2_5_groups). | For storms before 2022 (bdc_role 'sensitivity') the release postdates the storm; chapter 13's main analysis uses storms from 2022 on. |
| `first_report_date` | date |  | The county's first report in the storm's panel. |  |
| `last_report_date` | date |  | The county's last report in the storm's panel. |  |
| `n_reports_county` | integer | reports | Reports in the storm's panel that list the county. |  |
| `censoring` | string |  | none, left_reports_while_out (left the reports before the storm's last report while still out) or out_at_last_report. | Censored counties are not recovered. |

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

Nested JSON, one key per chapter (`chapter_1` to `chapter_9`, then `v2_1_public_record_misses`, `v2_2_backup_power`, `v2_3_power_cell_timing`, `v2_5_groups`, `v2_5_network_redundancy`, `v2_1_1_report_card`). Each number is stored with its interval (`ci_low`, `ci_high`), `n`, `unit` and `method` where it has them. Floats are written to 10 significant digits (since 2.2.0). The README maps each page section and figure to its key and script.

Intervals: The county bootstrap (chapters 3 to 6 within each storm; chapters 8 and 13 across storm-counties) resamples counties as if they were independent. Counties hit by the same storm share its wind, flooding, power grid and networks, so their outcomes are correlated, and these intervals may be somewhat narrow. The storm bootstrap (medians and pooled shares across storms, chapter 7's zone shares, chapter 12) resamples whole storms, and the models in chapters 7, 8 and 13 use storm- or county-clustered intervals. This is a note on the method, not a change to any result.
