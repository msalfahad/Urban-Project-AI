# D1.2: S4 footing cover / bar-length authority audit

**Round:** `D1.2` · **Policy:** `FOOTING_COVER_AUTHORITY_AUDIT_V1` · **Baseline:** HEAD `1384bf3` · **Built by** `build_d1_2_footing_cover_audit.py` (blind, byte-identical rebuild)

S4 and S4.1 are unchanged; so are S5, S6, S5.1, S6.1, AD1 and D1.1. All eight freeze manifests were hash-checked
before anything was read. No cover was invented and no actual cover was assumed. PRE-S7 was not started.

## The cover rule

ST7757.pdf p.8, note 22 (raster page, read again for this audit):

> 22. يجب أن لا يقل سمك الغطاء الخرساني عن 2.5 سم في الأعمدة والبلاطات والجسور وعن 7سم في الخرسانة الملاصقة للتربة.
>
> "The concrete cover thickness shall **not be less than** 2.5 cm in columns, slabs and beams, and 7 cm in concrete
> in contact with the soil."

**Cover basis: `MINIMUM_PROJECT_COVER_70`.**
- The wording is a minimum ("لا يقل ... عن").
- The R4 rule register already scoped the rule as "minimum cover".
- Neither p.13 footing detail fixes the bar position:
  - no dimension is bound to a bar line (0 dimension ticks on any footing bar line);
  - the only dimensions in the footing body are the column-bar foot (Min. 30 cm, Max. 10 cm), the screed (5) and
    the plain concrete (10).
- No DXF text states a cover (2780 texts, attributes and dimensions scanned, legacy Arabic decoded).
- S4 had taken the value as an exact SOURCE_EXPLICIT cover.

## What it means for the bars

So the actual cover is >= 70 mm, and therefore:
- **Straight segment:** at most dimension - 2 x 70. The frozen straight length is the *maximum* the source allows
  (SOURCE_MAXIMUM_STRAIGHT_RUN). It is not a lower bound.
- **Rate counts (two-layer footings):** ceil(rate x (dimension - 2 x 70)). A larger actual cover can only lower the
  count; a bar at the far edge (+1, not established) can raise it. The count has no bound either way.
- **Legs / hooks / bends / end treatment:** these can only add length, and they stay BLOCKED_UNQUANTIFIED.

The three pull in opposite directions, so no bound survives on any of the 60 parts. The kg is a project-drawing
number at minimum cover (PROJECT_BASIS_NUMERIC). It is not the as-built mass.

| | Parts | kg at minimum cover |
|---|---|---|
| single-layer BOTTOM_LONG / BOTTOM_SHORT (printed counts) | 40 | 887.09 |
| two-layer TOP / BOTTOM LONG / SHORT (rate counts) | 20 | 2742.51 |
| **Total** | **60** | **3629.60** |

**Quantity change:** 0.00 kg. **Authority change:** 60 parts, LOWER_BOUND -> PROJECT_BASIS_NUMERIC
(`04_S4_1A_COVER_AUTHORITY_CORRECTION.csv`).

## Two figures, kept apart

| | Project-drawing basis | As-built lower bound known |
|---|---|---|
| S4.1 footings | 3629.60 (at the 70 mm minimum) | not established |
| S5.1 ground system (after D1.1 / AD1) | 1436.23 | 1436.23 |
| S6.1 superstructure beams (after D1.1) | 4014.77 | 4014.77 |
| **Combined** | **9080.60** | **5451.00** |

S5 / S6 kg does not use a cover:
- 97 released S5 and 165 released S6 components were checked; none uses a cover term.
- Their lengths are support-face or clear runs, column sides and printed projections.

## Files

| File | Content |
|---|---|
| `01_SOURCE_SEARCH.md` | the rule wording, the footing-detail and DXF searches, the classification |
| `02_COVER_BASIS.json` | the cover basis with its evidence |
| `03_FOOTING_COVER_AUDIT.csv` | every mass-bearing S4 / S4.1 footing part: dimension, diameter, count / rate, cover, length, cover authority, the three separate uncertainties, new states |
| `04_S4_1A_COVER_AUTHORITY_CORRECTION.csv` | the state corrections (0 kg each) |
| `05_CORRECTED_RELEASE_SUMMARY.json` | the two figures, conservation, flags |
| `06_PROVENANCE.jsonl` | one line per audited part and per correction |
| `source_search_inputs/D1_2_VISUAL_SEARCH.json` | the p.8 re-read and the p.13 detail reading (render hashes only) |
| `D1_2_FREEZE_MANIFEST.json` | hashes of the code, inputs and outputs |
| `TEST_RUN.md` | the targeted and full-suite runs |

## For the owner

A footing-specific cover (for example a dimensioned bar-to-face offset), or an engineer's statement of the cover as
detailed, would make the straight lengths exact. A lower bound of the as-built footing steel would also need the leg,
hook and edge-bar facts. Until then the footing kg stays a project-basis figure.
