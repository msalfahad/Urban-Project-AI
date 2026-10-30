# T-354 Soil treatment / anti-termite (B1-05): is it in drawn scope? (development villa; every villa)

Worker 1 (lane S), 2026-10-30, run session_01E6cPnedtPJCw1picM7SRyq. Research piece, not wired: no engine module, method
version, route G, rule / knowledge file, candidate line or released quantity changed. Development villa, not an
accuracy claim. Drawings named by Drive folder "Alsenan chalet project" and title; entities by DXF handle or PDF page;
note and sheet numbers only (no note text, no client data). ERS s.2 - s.4 and s.7 applied.

Files: `soil_treatment_v1.py` (SOIL_TREATMENT_V1, pure rules, stdlib), `ALSENAN_SOIL_TREATMENT_INPUT.json` (sheet / note
numbers, handles and hashes, read this run), `t354_alsenan_check.py` -> `SHEET_SEARCH_T354.csv`,
`RELATED_LAYERS_T354.csv`, `summary.json`; tests `tests/t354_soil_treatment/` (29 pass: 23 hand-fixture villa K354
incl. 15 adverse + 6 development-villa pins).

## 1. The physical element and the question (ERS s.2.1)

SOIL TREATMENT / ANTI-TERMITE (B1-05, m2, NOT_IMPLEMENTED; registry `source_needed: specification`): a chemical
(termiticide) barrier sprayed on the soil before the structure is placed on or against it: the top of the compacted
fill under a slab on grade and, if the source says so, pit / trench bottoms and sides and the backfill against buried
faces. It is NOT the earth-contact waterproofing, the membrane + screed under footings, the blinding, the fill, a
polythene sheet / DPM, or a cement type for concrete against soil: each of those is another physical layer with its own
line (section 3). Question: does any drawing note, specification line or answered rule require it; if so, which
surfaces and how much.

## 2. Evidence search (acceptance a) — `SHEET_SEARCH_T354.csv`, 31 sheets, every one 'absent'

| Set | Sheets | How read this run | Requires soil treatment |
|---|---|---|---|
| ST7757.pdf (structural) | p.1 - p.16 | all 16 pages at 110 dpi; p.8 RECOMMENDATIONS notes 1-24 read in full at 130 dpi; p.9 boxed notes 1-4; p.13 / p.14 every detail label; p.15 notes 1-3; the plan sheets' NOTES / parapet boxes / legends | absent on all 16 |
| Architectural PDF (P7757) | p.1 - p.12 | parts 01-02, 05-06, 07-08, 11-12 and single sheets 03, 04, 09, 10 at 40 - 60 dpi; SECTION A-A ground zone at 150 dpi | absent on all 12 (no note block on any sheet; sections print levels and dimensions only, no build-up under the GF floor) |
| sanitary-7757.pdf | p.1 - p.3 | NOTES block at 200 dpi (one note: work to stated dimensions) + legend | absent on all 3 |
| Both DXFs | 2 253 + 276 text records | `shx_arabic.records_from_doc`, Arabic decoded; English + Arabic keyword list (both letter orders) | 0 requiring hits: ST 1876 = pool build-up label (p.7), ST 1B33 = bearing-stress note (p.9), 10 title-block false positives |
| Specification | - | project Drive folder listed (52 files): drawings, freelancer workbooks, photos | none issued |
| Owner rules | OWNER_QUESTIONS(_ANSWERED), OWNER_RULE_* (4), DECISION_REGISTER, OWNER_SESSION_CHANGES, rfi/A-D, knowledge/, rules/ | grep | none |
| Freelancer | FREELANCER_RAW_ROWS (885 rows, incl. the 30-row insulation sheet and the concrete summary) | Arabic / English search | no row |
| References | two Drive engineering-reference folders + project folder, full text 'termite' | Drive search | no file |

DXF coverage limit (named): the ST DXF does not carry the p.8 RECOMMENDATIONS or the p.13 / p.14 detail labels, and
P7757.dxf carries only the plans and two elevations: those sheets were read on the PDF.

**B1-05 status: NOT_IN_DRAWN_SCOPE** (rule R-ST-2: every one of 31 sheets searched, no note / specification / answered
rule). Quantity: **None** (never 0, never a convention such as the plot 470.55 m2, the GF 319.99 m2 or a footprint).

## 3. Printed layers that look related but are other elements (`RELATED_LAYERS_T354.csv`)

| Sheet / ref | Printed layer | Owner line (not B1-05) |
|---|---|---|
| ST p.8 note 13 | sulphate-resisting cement for concrete in contact with soil and groundwater | concrete material specification |
| ST p.8 note 22 | 7 cm cover against soil | rebar |
| ST p.8 notes 10 / 12 | no foundation on fill; founding level and soil check on site | earthworks (Q-21 C; T-170 / T-347 / T-357) |
| ST p.13 (both isolated-footing details) | two layers liquid waterproofing on every surface in contact with earth | foundation WP (T-219 / T-263 / T-270 / T-353) |
| ST p.13 / p.14 | 5 cm screed + membrane + 10 cm plain concrete under footings | underlay / blinding (T-206 / T-233) |
| ST p.13 / p.14 | well graded clean compacted fill; compacted soil under the GF slab | backfill / Z2 fill (T-320 / T-347) |
| ST p.14 lift detail | 'Slab on grade.' named; membrane + protection board on the pit walls | GF slab; lift-pit WP |
| ST p.7 pool | 5 cm screed + 5 cm insulation membrane + 10 cm plain concrete | pool (T-309) |

None of them is a soil treatment and none may be renamed into B1-05 (that would double-count a priced layer).

## 4. Reconciliation (ERS s.2.4)

| | Lines / rows | m2 |
|---|---|---|
| Engine (released V2.9 + route G, candidate V3.0.25) | 0 | - |
| Freelancer | 0 | - |
| Drawings + specification + owner rules | require none | - |

Missing from both BOQs and NOT required by this set: no difference to reconcile, residual none. Verdict proposal:
**NOT_IN_DRAWN_SCOPE (both right to omit it on this set)**. This is not a statement that the building needs no
termite protection: that is a design / specification decision outside the issued drawings; if the owner or consultant
later issues one, the rules below produce the quantity.

## 5. If a source is issued later (acceptance b readiness; nothing summed)

| Zone | Surface | Ledger that gives its plan | State today |
|---|---|---|---|
| Z-S | top of the Z2 fill under the GF slab on grade (slab underside about +0.85 dry floors) | T-320 zone Z2 | NOT FORMED (enclosed plan, wet-floor b HELD) |
| Z-P | 24 footing pit bottoms at the formation | T-347 / T-357 Z1 in-plot 125.344805 m2 | formation a bound (AT_MOST -1.50) |
| Z-T | ground-beam / strap trench bottoms | T-170 / T-253 / T-320 | not restated |
| Z-W | pit sides | - | HELD (depth bound) |
| Z-POOL | pool envelope at -1.50 | T-347 / T-357 11.851051 m2 | DRAWING-CONFIRMED level |

Basis follows the source's words (R-ST-3): PLAN = Z-S plan once (pit / trench bottoms inside it NOT added);
SURFACES = each surface once at its own level, overlaps deducted only at a shared level.

## 6. General rules (SOIL_TREATMENT_V1, scope every villa, provenance T-354; research rule, not a rule-library version)

- R-ST-1 a quantity exists only when a cited drawing note, specification clause or answered owner rule requires it;
  usual practice, another project's specification, a reference book or a freelancer row is refused as a source.
- R-ST-2 NOT_IN_DRAWN_SCOPE only when every sheet is searched; an unsearched sheet = UNKNOWN; area None, never 0 or a
  convention.
- R-ST-3 basis PLAN vs SURFACES from the source; a pit bottom inside the slab plan is never added under PLAN; a
  vertical face has no plan area; plan-overlap deductions only between surfaces at one level.
- R-ST-4 a zone without area or level is HELD by name beside the determinate part; held as 0 refused.

Tests (`tests/t354_soil_treatment/`): normal PLAN 93.000 m2 and SURFACES 103.450 m2 + held sides on villa K354 (hand
calc in the test docstring), mirror / rotation / mm invariance, same-level deduction 24.500 m2; adverse: five
non-sources, a source without a note reference, a convention area, a quantity under NOT_IN_DRAWN_SCOPE, an unsearched
sheet, a requiring note without a source record, a pit bottom counted with the slab plan twice, a vertical face under
PLAN, a basis the source does not state, a held zone as 0, a zone twice, a deduction across levels, a non-treatment
layer, an unstated unit.

## 7. Lessons-register proposal (ERS s.7)

| Date | Problem | Root cause | General rule | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-30 | B1-05 soil treatment was an open MISSING category; the set prints several earth-contact layers (liquid WP, under-footing membrane, sulphate-resisting cement, compacted fill) that could be mistaken for it, and no sheet requires a termiticide (T-354) | a family name was searched for, not a physical layer with a required source; look-alike layers sit on the same details | a site-treatment item exists only from a cited note / specification / answered rule; look-alike earth-contact layers are bound to their own owner lines, never renamed into the treatment; the treated area's basis (plan vs surfaces) comes from the source's wording and a pit bottom inside the slab plan is never added under plan basis (every villa) | tests/t354_soil_treatment (non-source refused; pit bottom twice refused; held as 0 refused) | PROPOSED |

## 8. For the Checker (re-read)

1. ST7757.pdf p.8: notes 1-24 (130 dpi); confirm none requires soil / termite treatment (note 13 = cement type).
2. ST7757.pdf p.13 and p.14: every label (fill, compacted soil, liquid WP, screed / membrane / plain concrete,
   'Slab on grade.').
3. Architectural p.10 / p.11 (sections): no build-up label under the GF floor; sanitary p.1 NOTES block.
4. The DXF census: ST 1876 and 1B33 are the only ST keyword hits.

## 9. Not done / uncertain

- No quantity (none required). Z-S cannot be formed until T-320 zone Z2 is formed, if a source ever appears.
- The DXF census cannot see raster-only sheets; those were read on the PDF at 40 - 130 dpi (note blocks are legible
  at these resolutions; dense dimension text on plans was not the object of the search).
- Data access note: the Drive connector returned raw files (not base64); each was base64-wrapped in the session
  scratchpad and decoded with `agent_env.sh decode` into `.work/private`, as the flow requires.
