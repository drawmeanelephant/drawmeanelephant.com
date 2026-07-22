# Elephant outreach ledger

`elephant-ledger.csv` is a reviewable public snapshot generated from the private
workbook `The List - Draw Me An Elephant.xlsx`.

The workbook remains the source of truth. The CSV is deliberately public-safe:
it keeps names, city/state, outreach and drawing statuses, public profile URLs,
and links to existing site records, but omits street addresses.

## Status meanings

- `confirmed_date` — the workbook contains a date in `written`.
- `confirmed_yes` — the workbook explicitly says yes.
- `date_needs_review` — a non-standard date string needs cleanup.
- `recorded_needs_review` — a non-empty value exists but needs interpretation.
- `not_recorded` — blank in the workbook; this is not automatically proof that
  no letter was sent.

## Matching rules

Exact normalized name matches to `content/breweries/*.md` are linked. Fuzzy
matches are listed as candidates only and must be reviewed before they become
canonical relationships. The current site archive contains only a subset of
the places in the workbook.

The source workbook and one-off generation tooling remain outside the public
site repository. This snapshot is not a substitute for the workbook.

`instagram-mapping-review.csv` is a separate conservative queue for the 360
generic Instagram posts. It only suggests a place when an Instagram handle in
the caption exactly matches a handle in the workbook. A suggestion is not a
canonical relationship until the caption and images have been reviewed.

The mapping review is a conservative snapshot, not a canonical relationship
database.
