# T-357 Existing ground reference, plot, built footprint and site clearance (B1-01) (Alsenan; every villa)

Worker 1 (lane S), 2026-10-30, run unknown. Research piece, not wired: no engine module, method version, route G,
rule / knowledge file, candidate line or released quantity changed; no figure in T-347 / T-350 moved. Development
villa, not an accuracy claim. Drawings named by Drive folder "Alsenan chalet project" and title; entities by DXF handle
or PDF page; lengths, areas and levels only (no coordinates, no note text, no client data). ERS s.2 - s.4, s.7 applied.

Files: `ground_reference_v1.py` (GROUND_REFERENCE_V1, pure rules, stdlib), `ALSENAN_GROUND_INPUT.json` (values /
handles / pages, read this run), `t357_alsenan_check.py` -> `LEVEL_REGISTER_T357.csv`, `SHEET_SEARCH_T357.csv`,
`EG_COEFFICIENTS_T357.csv`, `summary.json`; tests `tests/t357_ground_reference/` (16 pass: 10 hand-fixture villa P
incl. adverse + 6 Alsenan pins).

## 0. Inputs (own reads, this run)

| Drive file | sha256 / form | Read for |
|---|---|---|
| P7757_DXF_COMPRESSED.zip -> P7757.dxf | ab54dd55... | every TEXT / ATTRIB incl. nested blocks (276 records, Arabic SHX decoded with `engine/source/cad/shx_arabic`), LEL / level blocks, plot boundary lines |
| ST7757 dxf.dxf | 9f9d1179... (= route G input) | 2 253 text records, SH08 LEL blocks, S-BOUN extents |
| ST7757.pdf | 16 raster pages, no text layer | p.1 notes (160 dpi), p.8 notes 1-24 (130 dpi), p.9 boxed notes (150 dpi), all pages at 40 dpi for note blocks |
| Alsenan_Architectural_P7757_Pages_01-02 .. 11-12.pdf | 12 raster pages | p.1 / p.2 area plans (plot sides, storey areas, %), p.10 SECTION A-A ends (150 dpi), all pages at 45 dpi |
| sanitary-7757.pdf | 3 pages | GF drainage plan level marks and the notes box (170 dpi) |

## 1. Physical elements and the question (ERS s.2.1)

- EXISTING GROUND (EG): the plot surface before work; top of the soil that excavation removes, base of any fill
  placed above it. Not a finished level (+0.15 court paving, +0.30 annex, +1.00 GF FFL are finishes on EG + fill).
- PLOT: the parcel inside the printed boundary. SITE CLEARANCE (B1-01, m2, NOT_IMPLEMENTED): stripping vegetation,
  debris, obstructions, topsoil before setting out; a quantity exists only if a source puts it in scope.
- Question: is EG printed, as one value or several; what plot area / boundary is printed; is clearance in drawn scope.

## 2. Level register (acceptance a) — `LEVEL_REGISTER_T357.csv`, 29 rows

| Class | Value | Where (handles / pages) | What it labels | Status |
|---|---|---|---|---|
| Plot-edge ground | +-0.00 | P7757 GF plan LEL 37A (C1), A87 (C4), A86 (street mid) at 1.286 m outside the street boundary; A88 (C2), A89 (C3), A8A (sea mid) at 0.809 m outside the sea boundary | ground at the plot edge, all four corners | PRINTED (6) |
| Same, structural set | +-0.00 | ST SH08 (p.3) LEL 18B, 1CE, 1CF, 1D0, 1D1, 1D2: identical offsets after one translation (1D1 drafted 0.222 / 0.101 m from A89, same corner) | copied architectural marks (T-200: 19 / 20 SH08 marks coincide) | PRINTED (6) |
| Same, sanitary set | +-0.00 | sanitary p.1 GF drainage plan, street and sea edges | same marks, third discipline | PRINTED |
| Cut ground line | +-0.00 | P7757 SE elevation level 2439 / 2448, NW elevation 2A42 / 2A43 (both ends); ARCH p.10 SECTION A-A both ends on hatched earth | ground line under the building, both plot ends | PRINTED |
| Named, no value | - | ST p.9 boxed note 1 ("existing plot ground level", excavation >= 1.5 m below it); ST p.14 boundary wall 'N.G. LEVEL'; ST p.13 'Outer Normal ground level' (T-253) | the EG datum by name | NAMED_NO_VALUE |
| Finished | +0.15 / +0.30 / +1.00 | P7757 courts 394, 407, 409, 40B, 40D, 4AE; annex 401, 403, 405, 4AC; GF FFL 40F, 411, 413, A74; the same on SH08 | finishes, never EG | refused as EG (R-EG-REF-1) |

**Existing-ground reference: DERIVED +-0.00.** No sheet prints a spot level INSIDE the plot labelled existing /
natural ground (no survey; the issued set has no site plan, T-195 MISSING row 2). EG is the flat plane through the
printed +-0.00 at all four plot corners (+ two mid-sides) in three disciplines, confirmed by the ground lines of two
elevations and SECTION A-A at +-0.00 at both ends; p.9 note 1, p.13 and p.14 name the same datum. Never assumed 0.00:
the value is printed at every corner. Residual named: interior undulation UNKNOWN (no spot levels), and the marks sit
0.8 - 1.3 m outside the boundary (street / sea edge), so a local step at the boundary line is not excluded by drawing.

## 3. Plot, boundary and built footprint (acceptance b)

| Measure | Value | Evidence | Status |
|---|---|---|---|
| Plot sides | 15.00 (street) x 31.37 (neighbours) x 15.00 (sea) | ARCH p.1 / p.2 area plans and sanitary p.1 - p.3 print all four; P7757 boundary lines (outer face of the boundary-wall line, layers 1 / 5: 85, 86, 9A, 105, 8A / 103; 98 + 99; 107 - 109, 10F, 341, 347; 8B - 8E, 261) span exactly 31.370 x 15.000; ST S-BOUN 7FE run #1 = 31.37 (T-253) | PRINTED |
| Plot area | **470.55 m2** = 15.00 x 31.37 (shoelace on the boundary polygon) | not printed as a number; the four printed coverage % (GF 68.00, 1F 44.24, 2F 11.70, total 123.95) are each the TRUNCATION of area / 470.55 to 2 decimals, and only 470.54 - 470.56 reproduces all four | DERIVED, cross-checked (two independent printed sources) |
| GF built area | 319.99 m2 (220.99 + 18.08 + 51.83 + 23.76 + 4.87 + 0.46) | ARCH p.1 | PRINTED (municipal gross built area; not a slab or fill plan) |
| 1F | 211.44 - 3.24 = 208.20 m2 | ARCH p.1 | PRINTED |
| 2F | 8.10 x 6.80 = 55.08 m2 | ARCH p.2 | PRINTED |
| Total | 583.27 m2 | ARCH p.2 | PRINTED (= the sum) |
| Plot not covered by the GF area | 470.55 - 319.99 = 150.56 m2 | arithmetic | geometric fact only (courts, pool, garden): NOT a clearance area |

Merged ledger cross-reference: `research/alsenan_arch_truth_05/registers/FLOOR_AREA_CONSERVATION_REGISTER.json`
carries the same printed GF 319.99 (architect_area_sheet_m2).

**Site clearance: NOT IN DRAWN SCOPE** (`SHEET_SEARCH_T357.csv`, 31 sheets, each 'absent'): ST p.1 - p.16 (p.1 three
notes, p.8 notes 1-24 read in full, p.9 boxed notes 1-4, legends and parapet boxes on the plan sheets), ARCH p.1 -
p.12 (title block owner box only, no note block on any sheet), sanitary p.1 - p.3 (one note: work to stated
dimensions); DXF text census of both files (2 253 + 276 records, Arabic decoded): no clearance, levelling, topsoil or
demolition text. Owner rules searched (OWNER_QUESTIONS_ANSWERED, OWNER_QUESTIONS, OWNER_RULE_*, DECISION_REGISTER,
OWNER_SESSION_CHANGES): only Q-21 C, no clearance rule. Freelancer: no clearance row (FREELANCER_RAW_ROWS, 885 rows,
Arabic / English search): missing from both BOQs, not a difference. B1-01 quantity: none (area None, never 0, never a
convention such as plot area or plot minus footprint).

## 4. Effect on the T-347 / T-350 bounds (acceptance c) — m3 per metre of EG rise, absolute printed levels fixed

| Component | Plan (m2) | Reference of its far face | m3 / m |
|---|---|---|---|
| Z1 24 neat pits, in-plot (T-347 lo 188.017207) | 125.344805 | 'not less than 1.5 m below the existing plot level' (p.9 note 1): moves WITH EG | **0.000** (the absolute formation limit moves 1 : 1) |
| Z1 24 pits once a formation VALUE is printed (RFI S1) | 125.344805 | HELD | None (would be +125.345) |
| Z1 pool envelope in plot (T-347 lo 17.776576) | 11.851051 | formation -1.50 from the printed finished chain (T-183 r2 / T-200) | **+11.851** |
| Pool walls below EG / above EG (2.121053 / 0.707018) | 2.356727 | rim +0.30 absolute | +2.357 / -2.357 (transfer, net 0) |
| Boundary upper GB at N.G. (3.5256 m3) | 8.814 | top at N.G. | 0.000 |
| Z2 fill above EG under the GF slabs; court bedding to +0.15 | not formed (T-347 D-33 / D-34) | slab soffit / finish absolute | None (would be -A per m) |

With EG DERIVED at +-0.00 no figure moves: the coefficients state what a printed survey level would change.

## 5. Methods side by side

| Method | EG | Plot / clearance |
|---|---|---|
| Owner manual method | Q-21 C: distinguish existing ground, formation, blinding; 1.50 m is a minimum; no clearance rule recorded | - |
| Released V2.9 + route G / candidate V3.0.x | no EG field; no B1-01 line | NOT_IMPLEMENTED |
| Freelancer | no excavation, backfill or clearance row | omitted on both sides |
| Drawing-derived (this task) | DERIVED +-0.00 from 4 corner marks x 3 sets + cut ground lines | plot 470.55 m2 DERIVED (sides PRINTED, % cross-check); clearance NOT IN DRAWN SCOPE |

## 6. Findings and verdict proposals

1. F-T357-1 citation: the 1.5 m excavation note is **ST p.9 boxed note 1**, not "ST p.1 note 1" as the T-357 row
   says (p.1 notes are slab thickness, neighbour-side ground beams on brick, stripping time). T-170 / T-347 cite p.9
   correctly. No quantity effect.
2. F-T357-2 p.8 note 10: no foundation may sit on filled ground; the contractor verifies the bearing capacity. With
   no survey, any existing fill depth is UNKNOWN: a formation below the 1.50 m minimum stays the RFI S1 item.
3. F-T357-3 p.8 note 15 (excavation support / protection designed by a specialist) and p.9 note 4 (groundwater at
   4.5 m; p.8 note 14 dewatering if found): earthwork scope items with no drawn extent; named, not measured. They
   are the printed source family B1-06 (dewatering / shoring / temporary works, item, BLOCKED_BY_SOURCE) lacks: the
   notes put both in the contractor's scope as conditional / specialist-designed items, with no extent (no quantity).
4. Verdict proposals: B1-01 clearance = NOT IN DRAWN SCOPE (no quantity; neither BOQ has a row: no verdict needed);
   EG reference = ENGINE_RIGHT-compatible (T-170 / T-347 already use +-0.00; this task upgrades its basis from
   "datum" to DERIVED with the four-corner evidence and the residual named).
5. No owner question: ERS 2.7 not met (the drawings settle EG and plot; clearance absence is evidence, not a
   conflict). Whether a contract adds clearance as a provisional item is a commercial decision outside the drawn
   quantities; the Lead may carry it in the RFI package as a scope confirmation only.

## 7. Rule and lessons row (proposed)

R-EG-REF-1 / R-EG-REF-2 / R-PLOT-1 / R-CLR-1 / R-EG-COEF-1 (any villa; provenance T-357, T-170 R-EXC-LEDGER-1,
T-200 UP-LEVEL-DATUM-001, Q-21 C): text in `ground_reference_v1.py` docstring. Adoption = a new rule version (Lead /
lane I).

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-30 | The earthworks bounds used EG +-0.00 as a "datum" without stating where the value comes from; B1-01 clearance and the plot area had no source record | Ground level marks (plot edge, cut lines) and finished levels were never separated by class, corner coverage never checked; clearance scope never searched sheet by sheet | EG only from ground-class marks; one value only with every plot corner marked and all equal, else SLOPING / HELD; plot area from the printed boundary, cross-checked against printed coverage %; clearance only from a printed scope, never a convention area; EG-shift coefficient by the reference of each far face (any villa) | tests/t357_ground_reference (normal: flat 4-corner plot, printed spot, rectangle / mirror / L plot, printed clearance note; adverse: two printed levels (no mean), corner missing, unprinted EG, finished level offered as EG, undeclared unit, % conflict, convention clearance area, unsearched sheet) | proposed |

## 8. For the Checker (re-measure from the drawings)

1. ARCH p.1: plot sides 15.00 / 31.37; GF 319.99 (68.00 %), 1F 208.20 (44.24 %); p.2: 2F 55.08 (11.70 %), total
   583.27 (123.95 %); compute area / 470.55 and truncate.
2. P7757.dxf GF plan: LEL inserts 37A, A86, A87 (street side), A88, A89, A8A (sea side), all '%%p0.00'; boundary
   lines 98 + 99 = 31.37, street side 10F + 109 ... = 15.00.
3. ST7757.pdf p.9 boxed note 1 and p.8 notes 1-24: no ground value, no clearance.
4. ARCH p.10 SECTION A-A: +-0.00 at both ground-line ends, +0.15 court above.

## 9. Not done / uncertain

- ARCH p.7 / p.9 / p.11 ground-line marks seen at 45 dpi only (values not read; not used).
- Interior ground undulation and any existing fill depth: UNKNOWN (no survey; p.8 note 10).
- No candidate line, no wiring; the EG coefficient table is for lane I (T-350) and the designer item RFI S1.
