# Scoping note: earlier years and other events

Written 2026-11-25. Scoping only: nothing was downloaded beyond index pages, and nothing was built. **The reading
stopped at the first request**: www.fcc.gov refused it (HTTP 403 for https://www.fcc.gov/matthew; a request for
https://www.fcc.gov/hermine, sent in the same batch before the refusal came back, was refused too). Following the rule,
no other fcc.gov page was requested, and no other route to the same pages was tried (no transition.fcc.gov
substitutes, caches or changed headers). The decision log records the refusal.

## What exists, as far as is known without reading the FCC pages

| Item | Question | Known | Not known |
|---|---|---|---|
| (a) Hurricane Matthew, 2016 | Daily status reports, PDFs on transition.fcc.gov; do the county tables match our parser? | Tim's note: the FCC lists daily status reports at fcc.gov/matthew, with PDFs on transition.fcc.gov. Our earliest parsed layout is Harvey's (August 2017): county rows of sites served, out and percent out, with state totals, and no cause columns | The number and dates of Matthew's reports, their link pattern and their table layout: nothing was read |
| (b) Other 2016 storms (e.g. Hermine) | DIRS status reports? | Nothing | Whether DIRS was activated, and whether reports are listed |
| (c) 2012 (Isaac, Sandy) | County-level reports, or aggregate statements only? | From Alexis Kwasinski's CV (read 2026-11-25, for the related-work check): an FCC filing (Docket 11-60) and a Network Resiliency workshop talk on Sandy's effects (February 2013). That says nothing about the FCC's own report format | Whether the FCC published county tables in 2012 |
| (d) Non-hurricane activations (e.g. Winter Storm Fern, January 2026) | Same county tables? | Nothing (not requested after the refusal) | Whether DIRS was activated and the layout |

## The layout question, and how it could be answered without fcc.gov

Our parser handles the layouts of 2017 to 2026 (`src/dirs_parser.py`), including the cause-less tables of 2017-2018.
Whether Matthew's 2016 tables match needs one report read per storm (a document, not an index page), so it is
outside this note's limit either way. Possible routes, each for Tim to decide:

1. Tim reads the index pages in his browser (as for the Michael report's DOC number) and pastes the report list:
   titles, dates and document numbers or URLs.
2. With that list, one sample report per storm is downloaded through the logged download step (docs.fcc.gov or
   transition.fcc.gov, if they answer), and its table is compared with the parser's layouts. That is a download and
   needs Tim's approval.

## Effort, if the reports exist and look like 2017's

- Adding the 2016 storms to the manifest: small (the manifest and storm-page lists are hand-checked tables).
- Parsing: small if the layout matches Harvey 2017; medium if it differs (a new layout branch, with tests, as for each
  earlier layout change).
- Covariates: EAGLE-I begins in 2014 (2016 is covered by the figshare collection already cited); HURDAT2 covers 2016;
  SVI 2022 and ACS 2022 would be used as for 2017; the FCC Broadband Data Collection starts in 2022, so 2016 storms
  would have no provider counts, as 2017-2021 storms have none now.
- Rule periods: 2016 falls in the voluntary period already defined.
- Versioning: adding storms changes published numbers (counts, pooled shares, recovery curves), so it is a major
  version.
- 2012 and non-hurricane events: not estimable until their report format is known.

Nothing here is computed or planned for a release; any addition needs its own committed plan addendum.
