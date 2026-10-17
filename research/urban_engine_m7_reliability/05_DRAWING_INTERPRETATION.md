# 05 Drawing interpretation: legends, symbols, layers

## Legend reader V3 (`LEGEND_NEAREST_CAPTION`)

A legend swatch is a small fill off the building whose pattern and layer are used again on the sheet. V2 voted over
every caption within 3 m; with legend rows drawn close together every swatch saw every caption, the vote tied and the
legend became an unexplained fill group (M6 W5). V3 binds each swatch to the **nearest caption that names a family,
a caption on the swatch's own row first**, and records a state per swatch:

| State | Meaning |
|---|---|
| MATCHED | one caption, one family — the swatch names every fill of its pattern and layer on the sheet |
| AMBIGUOUS | two captions equally near (within 10 %) name different families, or one caption names two |
| NO_CAPTION | no caption within 3 m names a family |

"Detected" is the swatch itself; "supported" is a fill of the same pattern used on the plan; "unresolved" is AMBIGUOUS
or NO_CAPTION — the fills keep UNKNOWN with their candidates (never a guess). The states are written to the completeness
report (`legend`), only under V5.

Adversarial fixtures (`tests/m7_reliability/test_m7_legend.py`, expected values from the fixture geometry):

| Fixture | V2 | V3 |
|---|---|---|
| two rows 0.6 m apart, one caption each | no legend (tie) | each row its own caption |
| the caption on the left, a nearer caption of another family above the row | — | the row caption |
| two captions 0.2 m either side naming different families | — | AMBIGUOUS |
| a caption naming two families | — | AMBIGUOUS |
| a note naming no family | — | NO_CAPTION |
| a pattern used once on the sheet; a fill on the building | not a legend | not a legend |

Evidence on synthetic drawings: on the M6 V2 seeds where W5 appeared (233, 234) the false finding is gone in both
vocabularies and two of the four drawings now name both hatched cases; the other two draw no legend at all, so their
fills stay UNKNOWN — correctly. Held-out completeness (seeds 301–340, frozen engine): family RIGHT 341 → 350 (development
vocabulary) and 326 → 335 (held-out vocabulary); WRONG 16 → 12 and 21 → 19.

**Open (M6 W6):** a legend drawn on another sheet or only in the PDF is not read. ST7757's plans carry no swatch, so
its hatched cases stay UNKNOWN with candidates.

## Layer evidence for columns (`COLUMN_LAYER_EVIDENCE`)

A schedule-sized rectangle is a column only on a layer that shows columns: a layer named for columns, or one where at
least half its rectangles are column-like (at a scheduled section or holding a column mark). A furniture square that
happens to match a section — or that lands on a column mark — is not a member: it cuts no beam and closes no slab cell.

It is **not dropped**: after the held-out run, ST7757 showed that two column-sized outlines on a generic layer had
stopped being reported (post-freeze fix P2). The set-aside outlines now stay storey-presence evidence for the
completeness pass and are reported as COLUMN_PRESENCE_NOT_ITEMIZED at MEDIUM with "on a layer that shows no other
columns: confirm it is a column" (test `test_a_rectangle_set_aside_by_the_layer_rule_stays_evidence`).

## Column outline by section (`COLUMN_OUTLINE_BY_SECTION`)

A column mark binds to an outline at one of its scheduled sections before a nearer outline that is not (a lift-pit
square, pit walls, a plinth); inside a footing, the candidates are the outlines inside that footing at any distance. On
ST7757 three columns on the foundation plan that V4 bound to a 1.8 m footing outline (MEMBER_OUTLINE_SUSPECT) now bind
to their own sections.

## Stair treads (`STAIR_TREADS_ONE_LAYER`)

A flight is read from one layer's lines at a time and the largest family wins: lines of another layer between two
treads no longer break the going.

## What a symbol never does

A label, swatch, hatch or note never creates a quantity. It names a family, binds a section, or makes a finding; the
quantity still needs drawn geometry and a printed (or convention) dimension, and an uncertain reading stays UNRESOLVED
with its range.
