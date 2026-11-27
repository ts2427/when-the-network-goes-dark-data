# Codebook

Generated from `datapackage.json` by `code/src/14_data_repo.py`; edit the package, not this file. Missing values are empty cells. Every variable's limitation is in the last column.

## `data/analysis/dirs_county_day.csv`

One row per county per FCC DIRS report in use (174 reports, 22 storms).

Primary key: `storm_key`, `doc_id`, `fips`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `storm_key` | string |  | Storm key: NHC ID and DIRS activation date, joined by an underscore. | Names repeat across years (Isaias 2020 and 2026); always join on this key, not the name. |
| `nhc_id` | string |  | National Hurricane Center storm ID (basin, number, year). |  |
| `storm` | string |  | Storm name. | Not unique across years. |
| `dirs_activation_date` | date |  | Date the FCC activated DIRS for the storm. |  |
| `rule_period` | string |  | FCC rule period by activation date. P0: Voluntary DIRS, voluntary Framework (2016-01-01 to 2024-04-30); P1: MDRI in force, DIRS voluntary (2024-05-01 to 2025-02-19); P2: MDRI + mandatory DIRS (2025-02-20 to 2026-06-29); P3: Mandatory DIRS, with FCC 26-34 in effect from 2026-06-30 (its revised reporting list, 47 CFR 4.18, not yet in effect) (2026-06-30 to present). | Descriptive grouping only; periods differ in storms, hazards and filers. |
| `doc_id` | string |  | FCC EDOCS document number of the report. |  |
| `report_date` | date |  | Date of the report. |  |
| `as_of_utc` | datetime | UTC | The report's stated as-of time, in UTC. | Where the report prints none, set to 12:00 Eastern on the report date (as_of_imputed). |
| `as_of_imputed` | boolean |  | True when as_of_utc was set to 12:00 Eastern because the report prints no time. |  |
| `report_status` | string |  | Validation status of the report (step 4): ok, flagged (a check raised a note) or known_fcc_inconsistency (a stated total the FCC's own rows do not sum to, listed in code/manifest/known_fcc_inconsistencies.csv). | Excluded reports are not in the file. |
| `state` | string |  | State, as printed. | Ten study states only. |
| `county` | string |  | County as printed by the FCC; case and suffix vary by report format. | Use fips or county_name_census. |
| `county_name_census` | string |  | The county's 2020 Census name for its FIPS code (NAMELSAD form, e.g. "Baldwin County", "Orleans Parish"), from data/input/census/national_county2020.txt. | Added in 4.0.0. One name per FIPS across every report. |
| `fips` | string |  | Five-digit county FIPS code (with leading zero). | Mapped from the printed name with code/manifest/fips_exceptions.csv. |
| `sites_served` | integer | sites | Cell sites served in the county, as reported. | The denominator differs by storm and report; compare percentages with care. Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `sites_out` | integer | sites | Cell sites out of service in the county, as reported. | Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `pct_out` | number | percent | Percent of sites out, as printed (computed from the two counts where not printed). | Where pct_printed is false the value is computed, not printed. |
| `pct_printed` | boolean |  | True when the report printed the percent column. |  |
| `out_damage` | integer | sites | Sites out due to damage, as reported. | Blank where the report has no cause columns. Causes can overlap (see out_overattributed). |
| `out_transport` | integer | sites | Sites out due to transport (backhaul), as reported. | Blank where the report has no cause columns. |
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
| `rule_period` | string |  | FCC rule period by activation date. P0: Voluntary DIRS, voluntary Framework (2016-01-01 to 2024-04-30); P1: MDRI in force, DIRS voluntary (2024-05-01 to 2025-02-19); P2: MDRI + mandatory DIRS (2025-02-20 to 2026-06-29); P3: Mandatory DIRS, with FCC 26-34 in effect from 2026-06-30 (its revised reporting list, 47 CFR 4.18, not yet in effect) (2026-06-30 to present). | Blank for storms not in the panel. |
| `landfall_utc` | datetime | UTC | Day 0: the first time the storm's 34-kt wind radii reach a study-state county (fallback: first study-state landfall at tropical-storm strength or above). | Defined from NHC best-track radii; see docs/decisions.md (2026-11-23). |
| `landfall_source` | string |  | Which rule set day 0. |  |
| `previous_landfall_utc` | datetime | UTC | Day 0 under the original rule (kept for chapter 8's comparison). | Superseded; not used for the main results. |
| `interim_landfall_utc` | datetime | UTC | Day 0 under the first 2026-11-23 rule (kept for comparison). | Superseded; not used for the main results. |
| `n_reports` | integer | reports | Reports in the panel. | Blank for storms not in the panel. DOC-375778A1 and DOC-375808A1 are shared by Ida and Nicholas and counted for both, so the column sums to more than the reports used (README, Report counts). |
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
| `rule_period` | string |  | FCC rule period by activation date. P0: Voluntary DIRS, voluntary Framework (2016-01-01 to 2024-04-30); P1: MDRI in force, DIRS voluntary (2024-05-01 to 2025-02-19); P2: MDRI + mandatory DIRS (2025-02-20 to 2026-06-29); P3: Mandatory DIRS, with FCC 26-34 in effect from 2026-06-30 (its revised reporting list, 47 CFR 4.18, not yet in effect) (2026-06-30 to present). | Descriptive grouping only; periods differ in storms, hazards and filers. |
| `doc_id` | string |  | FCC EDOCS document number of the report. |  |
| `report_date` | date |  | Date of the report. |  |
| `as_of_utc` | datetime | UTC | The report's stated as-of time, in UTC. | Where the report prints none, set to 12:00 Eastern on the report date (as_of_imputed). |
| `as_of_imputed` | boolean |  | True when as_of_utc was set to 12:00 Eastern because the report prints no time. |  |
| `report_status` | string |  | Validation status of the report (step 4): ok, flagged (a check raised a note) or known_fcc_inconsistency (a stated total the FCC's own rows do not sum to, listed in code/manifest/known_fcc_inconsistencies.csv). | Excluded reports are not in the file. |
| `state` | string |  | State, as printed. | Ten study states only. |
| `county` | string |  | County as printed by the FCC; case and suffix vary by report format. | Use fips or county_name_census. |
| `county_name_census` | string |  | The county's 2020 Census name for its FIPS code (NAMELSAD form, e.g. "Baldwin County", "Orleans Parish"), from data/input/census/national_county2020.txt. | Added in 4.0.0. One name per FIPS across every report. |
| `fips` | string |  | Five-digit county FIPS code (with leading zero). | Mapped from the printed name with code/manifest/fips_exceptions.csv. |
| `sites_served` | integer | sites | Cell sites served in the county, as reported. | The denominator differs by storm and report; compare percentages with care. Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `sites_out` | integer | sites | Cell sites out of service in the county, as reported. | Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `pct_out` | number | percent | Percent of sites out, as printed (computed from the two counts where not printed). | Where pct_printed is false the value is computed, not printed. |
| `pct_printed` | boolean |  | True when the report printed the percent column. |  |
| `out_damage` | integer | sites | Sites out due to damage, as reported. | Blank where the report has no cause columns. Causes can overlap (see out_overattributed). |
| `out_transport` | integer | sites | Sites out due to transport (backhaul), as reported. | Blank where the report has no cause columns. |
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
| `days_since_landfall` | number | days | Deprecated alias of days_since_day0 (same values), kept until 4.0.0. | Use days_since_day0: day 0 is not always a landfall (see landfall_source). |
| `days_since_day0` | number | days | Days from day 0 to the report's as-of time (since 3.1.0). |  |
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

The same table as panel_analysis_ready.csv, with its types (UTC datetimes, nullable integers) and full float precision. A missing float is NaN, which frictionless reads as the text nan, so nan is a missing value here (4.0.0). SHA-256 722d9b6700e690dd4c17b7d824d48431acab833e39fb8d62e835c1a212b66ac4; 742466 bytes.

Primary key: `storm_key`, `doc_id`, `fips`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `storm_key` | string |  | Storm key: NHC ID and DIRS activation date, joined by an underscore. | Names repeat across years (Isaias 2020 and 2026); always join on this key, not the name. |
| `nhc_id` | string |  | National Hurricane Center storm ID (basin, number, year). |  |
| `storm` | string |  | Storm name. | Not unique across years. |
| `dirs_activation_date` | date |  | Date the FCC activated DIRS for the storm. |  |
| `rule_period` | string |  | FCC rule period by activation date. P0: Voluntary DIRS, voluntary Framework (2016-01-01 to 2024-04-30); P1: MDRI in force, DIRS voluntary (2024-05-01 to 2025-02-19); P2: MDRI + mandatory DIRS (2025-02-20 to 2026-06-29); P3: Mandatory DIRS, with FCC 26-34 in effect from 2026-06-30 (its revised reporting list, 47 CFR 4.18, not yet in effect) (2026-06-30 to present). | Descriptive grouping only; periods differ in storms, hazards and filers. |
| `doc_id` | string |  | FCC EDOCS document number of the report. |  |
| `report_date` | date |  | Date of the report. |  |
| `as_of_utc` | datetime | UTC | The report's stated as-of time, in UTC. | Where the report prints none, set to 12:00 Eastern on the report date (as_of_imputed). |
| `as_of_imputed` | boolean |  | True when as_of_utc was set to 12:00 Eastern because the report prints no time. |  |
| `report_status` | string |  | Validation status of the report (step 4): ok, flagged (a check raised a note) or known_fcc_inconsistency (a stated total the FCC's own rows do not sum to, listed in code/manifest/known_fcc_inconsistencies.csv). | Excluded reports are not in the file. |
| `state` | string |  | State, as printed. | Ten study states only. |
| `county` | string |  | County as printed by the FCC; case and suffix vary by report format. | Use fips or county_name_census. |
| `county_name_census` | string |  | The county's 2020 Census name for its FIPS code (NAMELSAD form, e.g. "Baldwin County", "Orleans Parish"), from data/input/census/national_county2020.txt. | Added in 4.0.0. One name per FIPS across every report. |
| `fips` | string |  | Five-digit county FIPS code (with leading zero). | Mapped from the printed name with code/manifest/fips_exceptions.csv. |
| `sites_served` | integer | sites | Cell sites served in the county, as reported. | The denominator differs by storm and report; compare percentages with care. Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `sites_out` | integer | sites | Cell sites out of service in the county, as reported. | Cell sites as reported by providers to the FCC; a site out is not a count of people without service (the FCC's caveat). |
| `pct_out` | number | percent | Percent of sites out, as printed (computed from the two counts where not printed). | Where pct_printed is false the value is computed, not printed. |
| `pct_printed` | boolean |  | True when the report printed the percent column. |  |
| `out_damage` | integer | sites | Sites out due to damage, as reported. | Blank where the report has no cause columns. Causes can overlap (see out_overattributed). |
| `out_transport` | integer | sites | Sites out due to transport (backhaul), as reported. | Blank where the report has no cause columns. |
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
| `days_since_landfall` | number | days | Deprecated alias of days_since_day0 (same values), kept until 4.0.0. | Use days_since_day0: day 0 is not always a landfall (see landfall_source). |
| `days_since_day0` | number | days | Days from day 0 to the report's as-of time (since 3.1.0). |  |
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

## `data/analysis/context/dirs_cable_wireline.csv`

One row per report and area, from the reports' Cable Systems and Wireline section, with the previous-day check. Built by code/src/17_cable_wireline.py. Exploratory (addendum 4.x-1, v3.2.0): a descriptive context table; no published result reads it, and no association with cell outages has been computed.

Primary key: `storm_key`, `doc_id`, `area`, `form`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `storm_key` | string |  | NHC ID and DIRS activation date (the manifest row's storm). |  |
| `nhc_id` | string |  | National Hurricane Center storm ID. |  |
| `storm` | string |  | Storm name. |  |
| `doc_id` | string |  | FCC EDOCS document ID of the report. |  |
| `report_date` | date |  | Report date. |  |
| `area` | string |  | What the figure covers: 'disaster area' (the whole reporting area, or a sentence naming several states), a state's postal code (a state row, or a sentence naming one state), or 'none printed'. | The FCC's area changes during a storm; compare figures only within one area. |
| `subscribers_out` | integer | subscribers | Cable and wireline subscribers out of service, as printed. | Blank where the report prints 'None' or no figure. Subscribers, not people or premises; not allocated to counties. No total is added up from state rows. |
| `printed` | string |  | The figure as printed in the report. |  |
| `form` | string |  | How it is printed: sentence, code table, name list or colon list ('and sentence' when the same figure is printed twice). |  |
| `source` | string |  | Which file the figure was read from: txt or pdf. |  |
| `previous_day_printed` | integer | subscribers | The previous-day figure the report prints ('up/down from N yesterday'). | Only where printed. |
| `previous_report_value` | integer | subscribers | The previous report's figure for the same storm and area. |  |
| `previous_day_check` | string |  | match, mismatch or 'no previous figure for this area' (blank where no previous-day figure is printed). | A mismatch is flagged, never corrected. |
| `from_excluded_report` | boolean |  | The report is excluded from the cell-site panel (its cable figure is kept). |  |

## `data/analysis/context/fema_ia_county_storm.csv`

One row per storm and panel county, from OpenFEMA RI-IHP v2 and Housing Assistance Renters v2. This product uses the Federal Emergency Management Agency's OpenFEMA API, but is not endorsed by FEMA. Built by code/src/16_fema_ia.py. Exploratory (addendum 4.x-1, v3.2.0): a descriptive context table; no published result reads it, and no association with cell outages has been computed.

Primary key: `storm_key`, `fips`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `storm_key` | string |  | NHC ID and DIRS activation date. |  |
| `storm` | string |  | Storm name. |  |
| `fips` | string |  | County FIPS code. |  |
| `ia_declared` | boolean |  | Individual Assistance or IHP declared for the county under the storm's declarations (iaProgramDeclared or ihProgramDeclared). |  |
| `fema_disasters_ia` | string |  | The major-disaster numbers summed over ('; '-separated). |  |
| `ihp_valid_registrations` | integer | registrations | RI-IHP v2 totalValidRegistrations. | Blank where no IA was declared; 0 where declared with no record. Applicants' damaged-dwelling counties as OpenFEMA gives them; tribal-area and statewide rows are not in any county (context/fema_ia_set_aside.csv). |
| `ihp_referrals` | integer | registrations | RI-IHP v2 ihpReferrals. | As above. |
| `ihp_eligible` | integer | registrations | RI-IHP v2 ihpEligible. | As above. |
| `renters_valid_registrations` | integer | registrations | Housing Assistance Renters v2 validRegistrations. | As above. |
| `renters_inspected` | integer | registrations | Housing Assistance Renters v2 totalInspected. | As above. |
| `renters_approved` | integer | registrations | Housing Assistance Renters v2 approvedForFemaAssistance. | As above. |
| `ihp_amount_usd` | number | US dollars (nominal) | RI-IHP v2 ihpAmount. | As above. Not adjusted for inflation. |

## `data/analysis/context/fema_ia_set_aside.csv`

Counted here instead of the county table. Built by code/src/16_fema_ia.py. Exploratory (addendum 4.x-1, v3.2.0): a descriptive context table; no published result reads it, and no association with cell outages has been computed.

Primary key: `dataset`, `disasterNumber`, `state`, `county`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `dataset` | string |  | OpenFEMA dataset. |  |
| `disasterNumber` | integer |  | FEMA disaster number. |  |
| `state` | string |  | State as OpenFEMA gives it. |  |
| `county` | string |  | County or area name as OpenFEMA gives it. |  |
| `set_aside` | string |  | Why the rows are not in the county table: outside the disaster's states, statewide, or tribal area (spans counties; no single county is assigned). |  |
| `valid_registrations` | integer | registrations | Valid registrations in those rows. |  |

## `data/analysis/context/hazard_ncei_county_storm.csv`

One row per storm and panel county: surge, flood and wind flags and damage from NOAA NCEI Storm Events (details files c20261119; zones mapped with NWS bp16ap26.dbx). The NCEI files are not redistributed. Built by code/src/18_hazard_ncei.py. Exploratory (addendum 4.x-1, v3.2.0): a descriptive context table; no published result reads it, and no association with cell outages has been computed.

Primary key: `storm_key`, `fips`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `storm_key` | string |  | NHC ID and DIRS activation date. |  |
| `storm` | string |  | Storm name. |  |
| `fips` | string |  | County FIPS code. |  |
| `surge_flag` | boolean |  | Any NCEI Storm Surge/Tide event in the county in the storm's window. |  |
| `flood_flag` | boolean |  | Any Flood or Flash Flood event. |  |
| `wind_flag` | boolean |  | Any Hurricane (Typhoon), Tropical Storm or High Wind event. |  |
| `damage_property_usd` | integer | US dollars (nominal) | Property damage of the county (C) events. | County events only; zone events' damage is in the zone columns. |
| `damage_crops_usd` | integer | US dollars (nominal) | Crop damage of the county (C) events. | County events only. |
| `zone_damage_property_usd_unallocated` | integer | US dollars (nominal) | Property damage of the zone (Z) events that cover the county: each event's whole figure, not divided among the zone's counties. | NEVER sum across counties: the same dollars appear in every county of the zone (see zone_n_counties). |
| `zone_damage_crops_usd_unallocated` | integer | US dollars (nominal) | Crop damage of the zone events that cover the county, undivided. | NEVER sum across counties. |
| `zone_n_counties` | integer | counties | Counties covered by those zone events (from bp16ap26.dbx). | 1 means the zone figures belong to this county alone; more means they are shared. |
| `n_events` | integer | events | NCEI events used. |  |
| `ncei_episode_ids` | string |  | NCEI episode IDs used ('; '-separated). |  |

## `data/analysis/context/hazard_ncei_storm_summary.csv`

Window, events used and zone events not mapped. Built by code/src/18_hazard_ncei.py. Exploratory (addendum 4.x-1, v3.2.0): a descriptive context table; no published result reads it, and no association with cell outages has been computed.

Primary key: `storm_key`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `storm_key` | string |  | NHC ID and DIRS activation date. |  |
| `storm` | string |  | Storm name. |  |
| `window_start` | date |  | DIRS activation date minus 2 days. |  |
| `window_end` | date |  | Last report plus 2 days. |  |
| `events_used` | integer | events | NCEI events matched to the storm's panel counties. |  |
| `zone_events_unmapped` | integer | events | Zone events in the storm's states whose zone is not in bp16ap26.dbx. |  |
| `zone_events_name_differs` | integer | events | Zone events set aside because their NCEI zone name names none of the counties bp16ap26.dbx gives the zone (renumbered zones, place-named zones, misspellings). |  |

## `data/analysis/validation/validation_dirs.csv`

One row per report: its status, what confirmed its rows and every failure and flag. Written by code/src/04_validate_dirs.py.

Primary key: `doc_id`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `doc_id` | string |  | FCC EDOCS document ID of the report. |  |
| `storm` | string |  | Storm of the report, as in the manifest (Ida for the reports Ida and Nicholas share). | Added in 4.0.0. |
| `status` | string |  | ok, flagged, known_fcc_inconsistency, excluded or fail (fail stops the build). |  |
| `n_rows` | integer | rows | County rows parsed. |  |
| `second_reading` | string |  | What confirmed every row: pdf_plain_text (the PDF's plain text, independent of the parse, which used the .txt or the PDF's table cells), or, where the parse itself used plain PDF text, txt, pdfium (PDFium's text) or pdf_cells (both pdfplumber readings), joined by "and". | Added in 4.0.0. |
| `fcc_multiple_causes_note` | boolean |  | The report prints the FCC's note that a site can be out for more than one cause. |  |
| `computed_pct_out` | number | percent | Sites out over sites served, from the county rows. |  |
| `stated_pct_out` | number | percent | The report's printed headline share of sites out. | Blank where none is printed. |
| `pct_out_used` | number | percent | The share used: always computed from the rows. |  |
| `sites_unattributed` | integer | cell sites | Sum over rows of sites out with no cause given. | Blank where the report prints no causes. |
| `sites_overattributed` | integer | cell sites | Sum over rows of causes in excess of sites out. | Blank where the report prints no causes. |
| `failures` | string |  | Why the report fails, if it does; ';'-separated. |  |
| `flag_reasons` | string |  | Known FCC inconsistencies and flags; ';'-separated. |  |

## `data/analysis/validation/validation_summary.csv`

One row per report: county rows and how their causes compare with sites out. n/a where the report prints no causes. Column names without spaces since 4.0.0.

Primary key: `report`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `report` | string |  | Storm, date and DOC ID. |  |
| `rows` | integer | rows | County rows. |  |
| `rows_causes_exact` | integer | rows | Rows whose causes sum to sites out. | n/a: no causes printed. |
| `rows_causes_short_by_1` | integer | rows | Rows whose causes fall short of sites out by 1. |  |
| `rows_causes_short_by_more` | integer | rows | Rows whose causes fall short by more than 1. |  |
| `rows_causes_exceed_out` | integer | rows | Rows whose causes exceed sites out. |  |
| `sites_with_no_cause` | string |  | Sites out with no cause, "N of M" sites out. |  |

## `data/analysis/validation/excluded_reports.csv`

manifest/excluded_reports.csv with each report's status and failures (empty in 4.0.0: every report in scope passes).

Primary key: `doc_id`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `doc_id` | string |  | FCC EDOCS document ID. |  |
| `storm_name` | string |  | Storm. |  |
| `report_date` | date |  | Report date. |  |
| `reason` | string |  | Why it is excluded. |  |
| `decided_on` | date |  | When the exclusion was decided. |  |
| `status` | string |  | Its validation status. |  |
| `failures` | string |  | Its failures. |  |

## `data/analysis/validation/area_status_counts.csv`

Counts of each report's rows inside the storm's notice area, inside under a spelling variant, outside it, or in the table but not the report's list.

Primary key: `doc_id`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `doc_id` | string |  | FCC EDOCS document ID. |  |
| `inside` | integer | rows | Rows inside the notice area. |  |
| `inside_spelling_variant` | integer | rows | Rows inside under a checked spelling variant. |  |
| `outside_notice_area` | integer | rows | Rows outside the notice area (kept, flagged). |  |
| `table_not_in_list` | integer | rows | Rows in the table but not the report's county list. |  |
| `confirmed_by_second_reading` | boolean |  | Every row confirmed by the second reading. |  |

## `data/analysis/validation/external_validation_fcc_2017.csv`

One row per figure the source gives in its text; see docs/external_validation.md. Values are text, since some figures are ranges or words.

Primary key: `id`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `id` | string |  | Figure ID. |  |
| `storm` | string |  | Storm. |  |
| `where` | string |  | Page and paragraph in the source. |  |
| `fcc_text` | string |  | The source's figure, as printed. |  |
| `report_date` | date |  | Matching DIRS report date. |  |
| `doc_id` | string |  | Matching DIRS report. |  |
| `area` | string |  | State or area (';'-separated). |  |
| `county` | string |  | County, where the figure is for one. |  |
| `measure` | string |  | How the figure is tested. |  |
| `fcc_value` | string |  | The source's value (text: some are ranges or words). |  |
| `ours` | string |  | Our value. |  |
| `ours_detail` | string |  | Our counts behind the value. |  |
| `printed_in_report` | string |  | What the daily report prints. |  |
| `source` | string |  | Where our value comes from. |  |
| `status` | string |  | match, consistent, differs, or shown, not scored. |  |
| `explanation` | string |  | Why a figure differs, where it does. |  |

## `data/analysis/validation/external_validation_fcc_michael.csv`

One row per figure the source gives in its text; see docs/external_validation.md. Values are text, since some figures are ranges or words.

Primary key: `id`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `id` | string |  | Figure ID. |  |
| `where` | string |  | Page and paragraph in the source. |  |
| `fcc_text` | string |  | The source's figure, as printed. |  |
| `report_date` | date |  | Matching DIRS report date. |  |
| `doc_id` | string |  | Matching DIRS report. |  |
| `area` | string |  | State or area (';'-separated). |  |
| `county` | string |  | County, where the figure is for one. |  |
| `measure` | string |  | How the figure is tested. |  |
| `fcc_value` | string |  | The source's value (text: some are ranges or words). |  |
| `ours` | string |  | Our value. |  |
| `ours_detail` | string |  | Our counts behind the value. |  |
| `status` | string |  | match, consistent, differs, or shown, not scored. |  |
| `explanation` | string |  | Why a figure differs, where it does. |  |

## `data/analysis/validation/external_validation_olukola.csv`

One row per figure the source gives in its text; see docs/external_validation.md. Values are text, since some figures are ranges or words.

Primary key: `id`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `id` | string |  | Figure ID. |  |
| `storm` | string |  | Storm. |  |
| `figure` | string |  | What is compared. |  |
| `where` | string |  | Page and paragraph in the source. |  |
| `theirs` | string |  | Their value. |  |
| `ours` | string |  | Our value. |  |
| `status` | string |  | match, consistent, differs, or shown, not scored. |  |
| `explanation` | string |  | Why a figure differs, where it does. |  |

## `data/analysis/validation/external_validation_fcc_21_99.csv`

One row per figure the source gives in its text; see docs/external_validation.md. Values are text, since some figures are ranges or words.

Primary key: `id`. Missing value code: empty cell.

| Variable | Type | Unit | Description | Limitations |
|---|---|---|---|---|
| `id` | string |  | Figure ID. |  |
| `where` | string |  | Page and paragraph in the source. |  |
| `fcc_text` | string |  | The source's figure, as printed. |  |
| `doc_id` | string |  | Matching DIRS report. |  |
| `report_date` | date |  | Matching DIRS report date. |  |
| `state` | string |  | State. |  |
| `measure` | string |  | How the figure is tested. |  |
| `fcc_value` | string |  | The source's value (text: some are ranges or words). |  |
| `ours` | string |  | Our value. |  |
| `ours_detail` | string |  | Our counts behind the value. |  |
| `status` | string |  | match, consistent, differs, or shown, not scored. |  |
| `explanation` | string |  | Why a figure differs, where it does. |  |

## Cleaning levels (`clean_rows`)

`clean_rows(panel, level)` in `code/src/load.py` (since 3.1.0) drops rows of the analysis-ready panel at one of two levels; it never changes a value. The main analysis uses every row except as noted; the flags behind each report's status are in `data/analysis/validation/validation_dirs.csv`.

| Level | Drops | Why |
|---|---|---|
| `standard` | rows with a time_flag: pre_onset_likely_marco, Laura's Aug 25, 2020 report (the FCC's combined Marco and Laura report, before Laura's day 0) | The rows behind every time-based result (steps 10 and 12 filter them the same way, with timed()): a report from before the storm's day 0 cannot be placed on its clock. Flagged reports are kept, as in the main analysis, because most flags are benign (see validation/validation_dirs.csv). Chapters 5 to 7 (causes, power, exposure) use every row. |
| `strict` | everything standard drops, and every report whose report_status is flagged (keeping ok and known_fcc_inconsistency) | The sensitivity display 'without flagged reports': only reports that reconcile with their printed totals, or whose one inconsistency is a checked FCC misprint (manifest/known_fcc_inconsistencies.csv). It drops benign flags too (spelling variants, a footnote, causes over sites out), so it is cautious rather than a list of errors; serious flags alone are in validation/validation_dirs.csv. |

## Report counts

From the manifest to the reports in `dirs_county_day.csv` (4.0.0):

| Step | Reports | Which |
|---|---|---|
| In the manifest (`code/manifest/dirs_reports.csv`) | 181 | every FCC report listed from the FCC's storm pages (Nicholas's rows are in two of Ida's reports) |
| Out of scope | 3 | Fiona 2022-09-24 (DOC-387555A1); Fiona 2022-09-26 (DOC-387584A1); Dorian 2019-08-29 (DOC-359363A1): outside the study area (Puerto Rico; Dorian's also the U.S. Virgin Islands); not parsed |
| Validated (step 4) | 178 | parsed and checked |
| Excluded | 0 | none |
| Outside the study states | 4 | Irma 2017-09-07 (DOC-346607A1); Irma 2017-09-08 (DOC-346626A1); Irma 2017-09-09 (DOC-346632A1); Irma 2017-09-10 (DOC-346634A1): county rows only outside the ten study states |
| Used (in `dirs_county_day.csv`) | 174 |  |

In `storms.csv`, `n_reports` sums to 176, not 174: DOC-375778A1 and DOC-375808A1 are shared by Ida and Nicholas and counted for both.

## County-level cause columns, by storm

Which reports print sites out by cause (damage, transport, power) on each county row, as parsed into `dirs_county_day.csv`. Reports without them print state totals only, or no causes at all. (Olukola et al. 2026 describe causes as state-level; in these reports, from 2019 on, they are printed per county.)

| Storm | DIRS activation | Reports | Reports with county causes | County rows | Rows with causes | Reports with backup power |
|---|---|---|---|---|---|---|
| Harvey | 2017-08-25 | 11 | 0 | 497 | 0 | 0 |
| Irma | 2017-09-06 | 8 | 0 | 603 | 0 | 0 |
| Nate | 2017-10-08 | 1 | 0 | 8 | 0 | 0 |
| Florence | 2018-09-12 | 11 | 0 | 849 | 0 | 0 |
| Michael | 2018-10-09 | 16 | 0 | 1,039 | 0 | 0 |
| Barry | 2019-07-12 | 2 | 2 | 146 | 146 | 0 |
| Dorian | 2019-08-27 | 5 | 5 | 363 | 363 | 0 |
| Laura | 2020-08-24 | 15 | 15 | 1,874 | 1,874 | 2 |
| Sally | 2020-09-14 | 7 | 7 | 136 | 136 | 0 |
| Delta | 2020-10-08 | 5 | 5 | 216 | 216 | 1 |
| Zeta | 2020-10-28 | 4 | 4 | 387 | 387 | 0 |
| Ida | 2021-08-29 | 22 | 22 | 951 | 951 | 0 |
| Nicholas | 2021-09-14 | 2 | 2 | 30 | 30 | 0 |
| Ian | 2022-09-27 | 13 | 13 | 517 | 517 | 13 |
| Nicole | 2022-11-09 | 2 | 2 | 68 | 68 | 2 |
| Idalia | 2023-08-29 | 6 | 6 | 160 | 160 | 6 |
| Beryl | 2024-07-08 | 6 | 6 | 33 | 33 | 6 |
| Debby | 2024-08-04 | 5 | 5 | 339 | 339 | 5 |
| Francine | 2024-09-11 | 3 | 3 | 105 | 105 | 3 |
| Helene | 2024-09-25 | 24 | 24 | 2,584 | 2,584 | 24 |
| Milton | 2024-10-07 | 5 | 5 | 260 | 260 | 5 |
| Isaias | 2026-10-08 | 3 | 3 | 131 | 131 | 3 |

## Reporting-regime boundaries

The rule periods in `rule_period` (by DIRS activation date) and which storms fall in each:

| Period | From | To | Storms |
|---|---|---|---|
| Voluntary DIRS, voluntary Framework | 2016-01-01 | 2024-04-30 | Barry, Delta, Dorian, Florence, Harvey, Ian, Ida, Idalia, Irma, Laura, Michael, Nate, Nicholas, Nicole, Sally, Zeta |
| MDRI in force, DIRS voluntary | 2024-05-01 | 2025-02-19 | Beryl, Debby, Francine, Helene, Milton |
| MDRI + mandatory DIRS | 2025-02-20 | 2026-06-29 | none in scope |
| Mandatory DIRS, with FCC 26-34 in effect from 2026-06-30 (its revised reporting list, 47 CFR 4.18, not yet in effect) | 2026-06-30 | open | Isaias |

- **Mandatory DIRS (FCC 24-5).** The Federal Register notice 2025-00495 (90 FR 6839) was published on January 21, 2025 and reads: "Effective February 20, 2025. Compliance with 47 CFR 4.18 ... is required as of February 20, 2025." No storm in scope has a DIRS activation in that period.
- **FCC 26-34.** 47 CFR 4.18 is the mandatory DIRS reporting rule itself. The Federal Register publication 2026-13155 (91 FR 39516, June 30, 2026) reads: "Effective June 30, 2026, except for amendatory instruction 3 (47 CFR 4.18), which is delayed indefinitely." In force from June 30, 2026 (amendatory instruction 2): daily reports from facilities-based providers even when nothing changed, no DIRS final report, and no reporting by providers without their own facilities (FCC 26-34, paras. 26 and 41). Delayed (instruction 3): the restated list of what each provider type reports and new paragraph (c), public safety voice and broadband networks, after Paperwork Reduction Act review and a Public Notice, not before November 30, 2026 (para. 52). The streamlined filing itself (a dynamic form, fewer fields, finer location) waits for changes to DIRS announced by a further Public Notice (para. 41); none was found in the Federal Register through 2026-11-25 (the FCC's own site refuses automated requests and was not checked). So the stored label "Streamlined DIRS (FCC 26-34)" overstates what was in force when Isaias 2026, the only storm after the date, was reported (October 2026); it is shown here as "Mandatory DIRS, with FCC 26-34 in effect from 2026-06-30 (its revised reporting list, 47 CFR 4.18, not yet in effect)", and `results.json` keeps the stored label until the next major version.
- **Layout.** Every storm from Barry (2019) on, including Isaias, prints cause columns on county rows; backup-power columns appear from Ian (2022) on (and in a few earlier reports, table above). Isaias's reports carry the same county-row columns as 2024's (cause and backup power, table above).

## `data/analysis/results.json`

Nested JSON, one key per chapter (`chapter_1` to `chapter_9`, then `v2_1_public_record_misses`, `v2_2_backup_power`, `v2_3_power_cell_timing`, `v2_5_groups`, `v2_5_network_redundancy`, `v2_1_1_report_card`). Each number is stored with its interval (`ci_low`, `ci_high`), `n`, `unit` and `method` where it has them. Floats are written to 10 significant digits (since 2.2.0). The README maps each page section and figure to its key and script.

Intervals: The county bootstrap (chapters 3 to 6 within each storm; chapters 8 and 13 across storm-counties) resamples counties as if they were independent. Counties hit by the same storm share its wind, flooding, power grid and networks, so their outcomes are correlated, and these intervals may be somewhat narrow. The storm bootstrap (medians and pooled shares across storms, chapter 7's zone shares, chapter 12) resamples whole storms, and the models in chapters 7, 8 and 13 use storm- or county-clustered intervals. This is a note on the method, not a change to any result.

### Page chapters and results.json keys

The page numbers its chapters 1 to 12 (since November 25, 2026); the keys of `results.json` keep their original numbering and did not change. Dated entries in `docs/decisions.md` use the chapter numbers the page had when they were written (the last column).

| Page chapter | results.json key (unchanged) | Chapter number on the page before |
|---|---|---|
| The data (unnumbered) | `chapter_1` | 1. The question and the data (its heatmap is now in 10) |
| 1. Anatomy of a storm: Isaias, October 2026 | `chapter_2` | 2 |
| 2. How much goes dark | `chapter_3` | 3 |
| 3. How fast it comes back | `chapter_4` | 4 |
| 4. Why sites go dark | `chapter_5` | 5 |
| 5. The power coupling | `chapter_6`, `v2_3_power_cell_timing` | 6 (and 12, now a subsection) |
| 6. Running on backup power (Exploratory) | `v2_2_backup_power` | 11 |
| 7. Exposure | `chapter_7` | 7 |
| 8. Social vulnerability | `chapter_8` | 8 |
| 9. Mobile providers (Exploratory) | `v2_5_network_redundancy`, `v2_5_groups` | 13 |
| 10. Where the reports stop (Exploratory) | `v2_1_public_record_misses`, `chapter_1` | 10 (its heatmap was in 1) |
| 11. How complete the reports are (Exploratory) | `v2_1_1_report_card` | 14 |
| 12. Did the rules help? | `chapter_9` | 9 |
