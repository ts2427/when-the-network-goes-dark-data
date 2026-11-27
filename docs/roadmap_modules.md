# Roadmap: later extensions as separate modules

Written 2026-11-27 (release 4.0.0). Planning only: no data are added or changed by this note.

## The rule

Each later extension is a **separate module** with its own version and DOI, its own committed analysis plan and its
own files. Every module uses the core panel's schema (`dirs_county_day.csv`: the same columns, names, types and
units, plus any module-specific columns at the end). A module never changes a file of the core release. So the core
numbers for the 22 storms of 2017-2026 stay as they are when a module is added; the core changes only through its
own versions, under the versioning policy (`CHANGELOG.md`, `docs/update_procedure.md`). Pooling a module with the
core is an analysis of its own, with its own plan.

## Planned modules

| Module | Events | What is known (not yet read here) | Why separate |
|---|---|---|---|
| Pre-cause era | Hurricane Matthew, 2016 (the only 2016 activation, per Tim's outside research) | 8 reports; county tables of sites served, out and % out; no cause columns | Before the core's 2017 start; a layout the parser has not been checked on |
| Territories | Hurricane Maria, 2017-2018 (Puerto Rico municipios and the U.S. Virgin Islands); later territorial activations | The FCC's 2017 season report (DOC-353805A1, para. 45) counts 107 Maria reports; no cause columns. GAO-21-297 gives territory-level cause shares and is the planned comparison | Territories are outside the ten study states; municipios are county equivalents with their own FIPS |
| Other hazards and territories, 2020-2026 | e.g. the Puerto Rico earthquakes (2020), California power shutoffs (2019), Henri (2021), the Puerto Rico power outage (2022), Fiona (2022), Mawar (2023), Maui (2023), Ernesto (2024), Winter Storm Fern, Sinlaku, Bavi and Lowell (2026) | See `docs/dirs_activations.csv`; Maui used DIRS-Lite with no county table, and Mawar's public reports stopped at the Guam governor's request | Different hazards and geography; the core's exposure measures (wind, distance to track) do not apply to most |

## Open covariates for later

Each would be added under a committed plan, as a context or covariate table with its own terms checked first.

- **Storm surge:** NHC Tropical Cyclone Report surge values, storm by storm (not yet collected).
- **Coastal change:** USGS coastal-change data release doi:10.5066/P9Z362BC (Ian, Helene). The DOI resolves
  (doi.org, 2026-11-27, to coastal.er.usgs.gov); its contents are not yet read.
- **Landslides (Helene):** USGS data releases doi:10.5066/P14CHGKS and doi:10.5066/P134ERB9. Both DOIs resolve
  (doi.org, 2026-11-27, to ScienceBase items); their contents are not yet read.
- **GAO-21-297** (for the territorial module): its page at gao.gov refused an automated request (HTTP 403,
  2026-11-27), so it is not yet verified here; it is cited only after it is read and marked VERIFIED in
  `docs/literature.md`.

## Not usable

- **PowerOutage.us** cannot be used in the public release: its terms allow personal, noncommercial use only, and
  forbid redistribution (the project brief; Tim's note, 2026-11-27). EAGLE-I (CC BY 4.0) stays the power source.
