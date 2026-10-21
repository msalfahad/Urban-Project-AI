# R5: what changed, why, and what it cost in published quantities

> **Correction (R6).** The claim below that the thirty-five gaps are objects
> "nothing in the source names as an opening" is **false**, and R5's own
> admission register — in the package that sentence was delivered in — said so:
> every one of them carries a `CAD_BLOCK_IDENTITY` of the form
> `DOOR-<zone>::<ref>`. What R5 had found was that their rectangles overlap no
> wall material, which is the normal condition for a door. See
> `docs/R6_WHAT_CHANGED_AND_WHY.md`. This document is kept as the record of what
> was reported, not as a statement of what is true.


R4 was rejected as an automation baseline, on ten specific grounds. This is what
each one turned out to be, what replaced it, and what the replacement does to the
numbers. Nothing here was tuned toward the frozen takeoff, the historical
workbook, or any previously reported figure; where a quantity moved away from
them it stayed moved, and where it disappeared it stayed gone.

## The short version

| | R4 | R5 |
|---|---|---|
| Wall rows published | 61 rows, **all blocked**, subtotals published anyway | 111 final, 19 blocked, 43 excluded; **every subtotal null** while questions remain |
| Masonry figures | 150 mm and 200 mm figures beside the frozen ones | none — the deliverable is a question register |
| Opening candidates | 44 carried, incl. a 2 mm object and a 0.60 m object with no host or height | 44 classified: confirmed, duplicate, noise, non-opening gap, unresolved |
| Window heights | `HEIGHT_M = null` on seven windows | resolved through the evidence hierarchy, with the record that answered and the records passed over |
| Wall continuity | any gap ≤ 3 m joined | joined only where a confirmed opening, continuation geometry or a declared CAD entity spans it |
| Opening basis | one Boolean for the whole revision | measured per wall line, with the openings tested |
| Band identity | anything with a thickness was billed (50 / 100 / 126 mm appeared) | five identities from annotation, topology, thickness family and shape |
| Blocking | one unresolved door blocked its whole floor | a dependency graph blocks the nodes whose value could change |
| Room assembly | "50 spaces assembled" — all single-component | graded: this drawing supplied no proven multi-component case |
| Checks | engine structures compared with engine structures | a 10-check gate on the published document, plus three metamorphic invariances, run on the real drawing |
| Package | a manifest containing its own hash | detached `SHA256SUMS`, four provenance facts kept apart, every entry verified after the zip was written |

## Why every subtotal is null

This is the headline and it is deliberate. The drawing contains 35 gaps in wall
lines that nothing in the source names as an opening — no door block, no window
block, no schedule row, no layer that says opening. Each one is equally a door,
an archway or a line the draughtsman did not close, and those are measured
differently. Any of them, if it is an opening, is deducted from the wall it sits
in. So they block the lines they lie in, those lines block their thickness
subtotals, and the subtotals are null.

R4 did not have this problem because it never asked the question: it carried
those gaps into host assignment, where they were answered confidently.

What survives: 111 of 173 wall rows are final and carry a net area; the
diagnostic sums are kept beside the nulls, under names that cannot be summed by
accident. If the 35 gaps are resolved — from the schedule, from a section, or by
the owner — the subtotals become numbers without any other change.

## Where the questions are

| kind | count | what it holds up |
|---|---|---|
| `OPENING_CANDIDATE_UNRESOLVED` | 35 | the net area of the wall lines each gap sits in |
| `UNRESOLVED_OPENING_NOT_ASSOCIATED_WITH_ANY_WALL` | 8 | nothing that can be identified; a completeness risk about the extraction |
| `WALL_IDENTITY_UNRESOLVED` | 2 | the 50 mm and 100 mm subtotals: each is one band whose thickness occurs once in the whole drawing |

Every one of them is answerable from the source documents or by the owner, and
every one names the quantity it blocks.

## What did not change

The frozen takeoff. It is opened read-only, its SHA-256 is recorded before and
after every run, and the regression asserts the two are equal. No quantity in
it was corrected, calibrated or written back.
