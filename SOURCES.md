# Sources and attribution

Every input file, with its URL, retrieval time (UTC) and SHA-256, is listed in `data/input/INPUTS.csv`. Downloads
followed one rule: approved sources only, one request at a time at least 3 seconds apart, a generic User-Agent, and
no retry after a refusal.

## FCC Disaster Information Reporting System (DIRS)

Federal Communications Commission, Public Safety and Homeland Security Bureau. *Communications Status Report for
Areas Impacted by* [storm], 180 reports, 2017-2026, each cited by its EDOCS DOC number and date in
`data/input/INPUTS.csv` and `code/manifest/dirs_reports.csv` (https://docs.fcc.gov/public/attachments/DOC-<number>.pdf
and .txt). Retrieved 2026-11-22 (UTC; first file 19:55 UTC). U.S. government work; public domain in the United States.
The FCC's DIRS notices (activation, area changes, deactivation) are in `data/input/notices/`.

Each report carries this caveat: "The number of cell site outages in a specific area does not necessarily correspond
to the availability of wireless service to consumers in that area."

Rules cited for dates: FCC 22-50 (Mandatory Disaster Response Initiative, adopted June 27, 2022;
`data/input/rules/FCC-22-50A1_Rcd.pdf`), compliance from May 1, 2024 per the FCC's MDRI page
(https://www.fcc.gov/node/254876, accessed November 23, 2026; the formal compliance notice was not retrieved);
FCC 24-5 and DA 25-74 (mandatory DIRS from February 20, 2025; Federal Register 2025-00495); FCC 26-34 (adopted
May 20, 2026; Federal Register 2026-13155, 91 FR 39516, June 30, 2026; `data/input/rules/FCC-26-34A1.txt`).

## FCC Broadband Data Collection (counts only)

FCC Broadband Data Collection public data (National Broadband Map, https://broadbandmap.fcc.gov/data-download) were
obtained through the FCC's Public Data API under the FCC API terms of service accepted for the account, and are used
for provider counts only; no provider is named and the files are not redistributed. What is published here is
`data/input/bdc/bdc_county_provider_counts.csv` (counts by county and release, derived by `code/src/06e_bdc_counties.py`
and `06f_bdc_counts.py`) and the list of files used (`provider_summary_files.csv`, `storm_releases.json`).

## ORNL/DOE EAGLE-I

Brelsford, C., et al. (2024). A dataset of recorded electricity outages by United States county 2014-2022.
*Scientific Data*, 11, 271. https://doi.org/10.1038/s41597-024-03095-5.
Data: figshare, https://doi.org/10.6084/m9.figshare.24237376 (version 4, published 2026-02-25), files
eaglei_outages_2017.csv to eaglei_outages_2024.csv, MCC.csv, coverage_history.csv; licence CC BY 4.0, read from the figshare record of
version 4 on 2026-11-22 (the record that holds these file IDs; `code/manifest/eaglei_files.csv`). The 2025 release
(https://doi.org/10.13139/ORNLNCCS/3012826) was not used.
Modified: aggregated to county at report times. `data/input/eaglei/eaglei_extract.parquet` keeps only the study
counties and storm windows; `MCC.csv` and `coverage_history.csv` are unmodified. The year files are not
redistributed. Retrieved 2026-11-23 (UTC; first file 00:28 UTC).

## CDC/ATSDR Social Vulnerability Index

Centers for Disease Control and Prevention/ Agency for Toxic Substances and Disease Registry/ Geospatial Research,
Analysis, and Services Program. CDC/ATSDR Social Vulnerability Index 2022 Database United States.
https://www.atsdr.cdc.gov/placeandhealth/svi/data_documentation_download.html Accessed on 2026-11-23 (UTC; first file 01:12 UTC).

## OpenFEMA

This product uses the Federal Emergency Management Agency's OpenFEMA API, but is not endorsed by FEMA. The Federal
Government or FEMA cannot vouch for the data or analyses derived from these data after the data have been retrieved
from the Agency's website(s).
Dataset: Disaster Declarations Summaries v2, https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries, accessed
2026-11-23T01:14:00+00:00 to 2026-11-23T01:14:43+00:00 (UTC). Used as context only (`fema_declared`); no result uses it.

Datasets (v3.2.0): Registration Intake and Individuals Household Program (RI-IHP) v2,
https://www.fema.gov/api/open/v2/RegistrationIntakeIndividualsHouseholdPrograms, and Housing Assistance Program Data -
Renters v2, https://www.fema.gov/api/open/v2/HousingAssistanceRenters, one query per disaster number, accessed
2026-11-25T17:16:40+00:00 to 2026-11-25T17:20:19+00:00 (UTC). Context only (`data/analysis/context/`); no result uses them.

## NOAA NCEI Storm Events (v3.2.0)

NOAA National Centers for Environmental Information, Storm Events Database, bulk details files
`StormEvents_details-ftp_v1.0_d2017_c20261119.csv.gz` to `..._d2026_c20261119.csv.gz`,
https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/, retrieved 2026-11-25 (SHA-256 of each in
`code/manifest/downloads.csv`). No licence or use statement was found on the pages read, so the files are not
redistributed; only the derived county table is published. The 2026 file holds events through August 2026.
Zones are mapped to counties with the NWS zone-county correlation file `bp16ap26.dbx`
(https://www.weather.gov/gis/ZoneCounty, `data/input/nws/`, retrieved 2026-11-25 (UTC; first file 17:15 UTC); U.S. government work).

## FCC report on Hurricane Michael (v3.2.0)

FCC Public Safety and Homeland Security Bureau (2019). *October 2018 Hurricane Michael's Impact on Communications:
Preparation, Effect, and Recovery*. Report and Recommendations, PS Docket No. 18-339, DOC-357387A1,
https://docs.fcc.gov/public/attachments/DOC-357387A1.pdf (`data/input/rules/DOC-357387A1.pdf`). Used for the
external check in `docs/external_validation.md` only. U.S. government work.

## NOAA National Hurricane Center

Landsea, C. W., & Franklin, J. L. (2013). Atlantic hurricane database uncertainty and presentation of a new database
format. *Monthly Weather Review*, 141(10), 3576-3592. https://doi.org/10.1175/MWR-D-12-00254.1.
File: HURDAT2 Atlantic, `hurdat2-1851-2025-092326.txt` (1851-2025, NHC file version dated 2026-09-23 in its name),
https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-092326.txt, retrieved 2026-11-23. Isaias 2026 (AL092026) best track from the NHC GIS archive,
`al092026_best_track.zip`. U.S. government work; public domain.

## U.S. Census Bureau

This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau.
American Community Survey 5-year estimates, 2018-2022 (households, population 65 and over, broadband subscription),
county level, from api.census.gov (the key is not stored; the logged URL has it redacted). 2020 county list
(`national_county2020.txt`), 2020 Gazetteer counties and the 2022 cartographic boundary file (1:500,000) from
www2.census.gov. Retrieved 2026-11-23 (UTC; first file 00:29 UTC).

## Software on the page

D3 7.9.0 and topojson-client 3.1.0 (ISC License), used by the page's map; not part of this repository.

## Related work cited on the page

Olukola et al. (2026), arXiv:2609.10944, is used on the page only as a check on Helene; its dataset is not
redistributed here.
