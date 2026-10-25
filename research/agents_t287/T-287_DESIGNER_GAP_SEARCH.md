# T-287 Designer RFI gaps G1 - G3: the sheet search behind each row (Alsenan; every villa)

Worker 1 (lane S), 2026-10-25, run session_0171PkwPC8HmAmYCzQMahdJc. Research only, not wired: no engine, candidate,
released line or register changed; nothing released. Drawings named by Drive folder and title; entities by DXF handle;
no coordinates committed (regions are built at run time from anchor handles; the architectural plans are registered to
the structural frames at run time by matching level marks). ERS s.2 (search every sheet first), s.2.7 / s.6 (only
genuinely unresolved items go to the designer), s.3, s.7 applied.

## 0. Inputs (own, this run)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179... (= manifest) | ST p.1 - p.7 (frames CAP, FP, GBP, GFRS, FFRS, SFRS, pool / dome detail; the schedules p.9 - p.12 share those frames), 4,461 entities |
| "P7757_DXF_COMPRESSED.zip" -> P7757.dxf | ab54dd55... (= manifest) | GF / 1F / 2F plans (2,198 entities registered) and every other sheet (sections, elevations: 3,765, searched as whole sheets) |
| "ST7757.pdf" | 74da1523... (= T-195 register) | the pages the DXF does not carry: p.8 (raster notes, 24 items read), p.13 - p.16 (details; no paper space in the DXF), p.7 (dome detail), rendered and read by hand this run |

Registration (runtime, `t287_alsenan.read_arch`): arch GF = ST p.3 by 14 agreeing level marks (all 14 of the sheet; T-200
found the same pairing); arch 2F = ST p.6 by its 2 '+9.70' marks, same row (y offset identical to GF); arch 1F at the equal
pitch between them, accepted only because its five '+5.50' marks then fall inside the building extent (the three
architectural plot stamps sit at that same 44.85 m pitch). The 13 RTEXT entities of the two files are plot / date stamp
fields (read as raw tags: `$(edtime ...)`, `$(getvar ...)`), not drawing content.

## 1. Method (DESIGNER_GAP_SEARCH_V1, `t287_search.py`)

For each question: the region = the extent of the element's own drawn lines (anchor handles from the merged ledgers
T-184 / T-248 / T-258 / T-185) plus a stated margin, mapped onto every plan sheet at the same plan position. Every entity
of the sheet inside the region is counted; the question is **FOUND** only when a printed value that answers it lies
inside (a text / tag matching its evidence pattern, a dimension lying wholly inside the region, or for an opening a
circle / arc of at least 1.0 m); otherwise **MISSING** with no value. A long dimension chain passing through the region,
a callout bubble, the anchors themselves never count. Whole-sheet word searches (structural level / neck, thickness /
waist, winder / turn / soffit, dome / ring / drum) run over every sheet of both files, sections and elevations included.
The PDF-only pages are a hand reading (MANUAL_PAGES in `t287_alsenan.py`). Output: `ALSENAN_SEARCH_T287.json`
(verdict, per-sheet entity counts, evidence handles and printed values only).

## 2. G1 (CONC.COLUMN): the CB5-line columns C5 (GFRS 35F) and C3 (365) - SETTLED from the drawings, not asked

Physical element: the GF column runs from the ground-beam top (= neck top, R-NECK-ENDS-1) to the 1F floor slab top
+5.45 (T-248, DRAWING-CONFIRMED; 1F columns 685 / 68B stand on both). T-248 held them 1.2375 .. 1.4300 m3 because "the
annex (+0.25) and main (+0.95) ground slabs meet" on the CB5 line.

Search (G1-a, margin 1.5 m): no structural level, neck end, T.O.S / N.G.L or section cut at either column on ST p.1
(41 entities), p.2 (32), p.3 (40), p.4 (52), p.5 (35), p.6 (16) or the arch GF plan (103); whole-sheet search: no
structural level word anywhere in either file; p.13 - p.16 have no two-level ground-beam detail; p.8 no level note.
**MISSING as a printed structural level.** What the sheets do print beside the columns (two independent readings):

| Column | ST p.3 bay reading (marks reached across its own ground-beam band only) | arch GF plan space reading (marks in the same floor space as a probe 0.60 m beyond the outline, no drawn line between) |
|---|---|---|
| 365 C3 | 1B4 '+0.30' (W, annex lobby), 1B6 '+0.15' (E, side passage) -> base +0.25 | W / NW / SW / S: 405 '+0.30'; E / NE / SE: 407 / 409 '+0.15' -> base +0.25 |
| 35F C5 | 1B6 / 1B8 '+0.15' only (its SW bay, the annex kitchen, prints no mark of its own) -> MISSING | SW: 405 '+0.30' (the kitchen is open to the lobby that prints it: no wall, step or door line between); E / NE / SE: 407 / 409 '+0.15' -> base +0.25 |

No '+1.00' is reached from either column in either reading: the main-house floor (+1.00, mark 1C0) lies beyond the
1.20 m side passage and the C11-line ground beam (bands at +1.325 .. +1.625 m east of the CB5 line on ST p.3). The east
side of the CB5 line is the side passage at the court level +0.15 (T-200 court ground DRAWING-CONFIRMED; the A9 / D-55
passage), i.e. exterior ground, exactly the ST p.13 exterior ground-beam condition ('Ground Floor slab level' inside,
'Outer normal ground level' outside). **The only building floor beside both columns is the annex, FFL +0.30 -> slab top =
ground-beam top = column base +0.25 (T-214 build-up 0.05). The +0.95 reading has no drawn support at these columns.**

Quantity (each once; the column / neck solid is unchanged, only its boundary is fixed):

| Member | A (m2) | before (T-248) | after (this run) | change |
|---|---|---|---|---|
| GF C5 35F | 0.150 | 0.675 .. 0.780 HELD (h 4.50 .. 5.20) | **0.780** (h 5.45 - 0.25 = 5.20) DRAWING-DERIVED | range closed at its upper end |
| GF C3 365 | 0.125 | 0.5625 .. 0.650 HELD | **0.650** DRAWING-DERIVED | range closed at its upper end |
| **two columns** | | **1.2375 .. 1.4300** | **1.4300** | +0.1925 vs the low end, 0.000 vs the high end |
| neck 10BD (C5) | 0.18 | >= 0.1944, cause FORMATION + TWO_GROUND_SLAB_LEVELS | >= 0.1944 (top +0.25; h = 1.08 + d) | cause TWO_GROUND_SLAB_LEVELS removed; still HELD on Q-21 C (formation) |
| neck 10C5 (C3) | 0.15 | >= 0.192, same | >= 0.192 (h = 1.28 + d) | same |

Candidate V3.0.9 carries these two at 4.50 m inside its 'annex / boundary 3.7125' PROVISIONAL (= 1.2375 on them): -0.1925
m3 (-13.5 %) against the drawing. Downstream: T-280 (column cores / starters) takes the neck top +0.25 for both; T-248's
P-7 blocker list loses G1. Status DRAWING-DERIVED until the Checker re-runs the G1 search (s.8); then the two lines are
closable like the 19 GF DRAWING-CONFIRMED columns.

## 3. G2 (CONC.STAIR_DOME): ST-01 winder turn, 1F turn riser, flight waists - partly settled, the rest a package row

| Question | Sheets searched (entities in the region) | Result |
|---|---|---|
| G2-a MS1-T winder turn: outline, level, wholly-contained dimension, 'winder / landing / S.S.L / soffit' (margin 0.10) | ST p.3 13, p.4 16, p.5 19; arch GF plan 40, 1F plan 36; whole-sheet word search both files (0 hits); p.16 typical section (no winder, no turn); p.8 (no stair note) | **MISSING**. Printed there: the 3 wedge lines 2F6 / 2F4 / 2F5 + closing line 2F3 (plans) and **'T 16' (tag 580) on the turn itself**. Arch dimensions 5.00 / 2.50 / 0.20 / 0.075 (GF) and 2.50 / 1.20 / 3.30 / 0.20 / 0.075 (1F) only pass through (hall, lane and wall dimensions) |
| G2-c MS2-TR 1F turn riser between the half landings (margin 0.10) | ST p.4 15, p.5 11, p.6 7; arch 1F 24, 2F 20 | **MISSING** (no level; +7.516 / +7.684 are by count, T-258); 'T 16' tag 74A on the 1F flights |
| G2-w waist / slab thickness per flight (margin 0.15) | each flight on its own sheet (9 .. 30 entities) | **FOUND 'T 16'** on MS1-L, MS1-T, MS1-LD, MS1-U (tag 580, p.4), MS2-L, MS2-TR, MS2-LD, MS2-U (74A, p.5), RS-S, RS-LD, RS-A (5B6, p.4); **MISSING on D1** (p.3, 9 entities), **E1** (p.3, 15) and **RS-C** (p.4, 28; nearest print 'T 16' 5B6 2.574 m away on RS-S); no thickness print within 3 m of D1 / E1 (the only ground-slab callouts 'T=10cm' 1690 / 169D are farther) |

Settled by the search (reported, not asked): every ST-01 flight, half landing and the turn print 'T 16' (Q-47 A already
applies it; T-258 uses 0.16: no quantity moves). So G2's "unprinted waist per flight" narrows to **D1, E1 and RS-C**; the
MS1-T turn keeps only its geometry open (thickness printed).

## 4. G3 (CONC.STAIR_DOME): tower dome, rings, drums - a package row

| Question | Sheets searched | Result |
|---|---|---|
| G3-a structural opening / ring / drum / dome at the tower dome position (arch 2F hidden circle 1300, r 2.205; margin 0.30) | ST p.5 50, p.6 52, arch 2F plan 52; whole-sheet word search: 'DOME' only on ST p.7 (1A18 'DETAIL OF DOME'), no 'RING' / 'DRUM' text in either file | **MISSING**: ST p.6 draws the +13.90 slab there as a flat B2 panel (bars 7 d10 / 6 d10) with no opening, ring, circle or note; the only circle within reach on p.5 is the 0.82 m P.C callout bubble 77E (not an opening) |
| G3-b drum material / thickness at the terrace domes (ST p.5 ring arcs 5FE / 5FF, circle 649; margin 0.50) | ST p.5 165, p.6 81, arch 1F 250, 2F 104 | **MISSING** (only the arch 1F 'VOID' tag B7A) |
| ST p.7 (PDF) | hand | one generic 'DETAIL OF DOME (N.I.S)': chord 442, rise 190, shell 10, d12 / 15 cm, ring 20 wide, depth 'AS PER ARCH'; no dome named, no drum |
| ST p.8 note 4 (PDF) | hand | every opening on the architectural drawings must exist on the structural drawings; refer details to the structural engineer |

## 5. Package rows (CLARIFICATIONS_CONSULTANT format; for the Lead to place under P-8; G1 needs no row)

| # | Ref | Element / location | Drawing reference | Conflict or missing information | Quantity held | Readings the drawings allow | Search |
|---|---|---|---|---|---|---|---|
| G2 | C-ST-3 (+ waists) | ST-01 winder turn MS1-T (GF, top of the west flight) and the 1F turn riser MS2-TR between the half landings; waist / support of D1 (stair-hall flight +0.30 -> +1.00), E1 (entrance flight +0.15 -> +1.00) and the curved part RS-C of the round stair | ST p.4: wedge lines 2F6 / 2F4 / 2F5, closing line 2F3, 'T 16' (580) on the turn; arch section A-A: 5 risers in the turn (T-184) vs 3 wedges + closing line on the plans; ST p.5: step line 5E2 / S-OPENING 633 between plates at +7.516 / +7.684 (by count); ST p.3: D1 riser lines 1C4 .. 1C7, E1 18A .. 179, no thickness; ST p.4 RS-C: 12 wedge lines 2DF .. 2EA and arcs 2DD / 2DE, no thickness ('T 16' 5B6 on the straight part only); ST p.16 typical stair section: waist 'THICK.' with no value, no winder or curved flight | the turn's riser count (5 or 4), riser heights and soffit form (flat plate at which level, or stepped / warped under the winders); the level of the 1F turn riser; D1 / E1: a waist slab (thickness) or steps on fill over the 'T=10cm' ground slab; RS-C: the helicoid soffit and its thickness | MS1-T treads 0.12 .. 0.13 + turn slab 0.2304 .. 0.2496 m3 (T-258); MS2-TR, D1 waist, E1 waist, RS-C treads (0.330 information only) and helicoid waist: no value; stair soffit finish under them (T-281: winder 1.495 m2 plan, RS-C 4.443 m2 plan, true areas HELD) | MS1-T: 3 winders + closing riser as planned, or 5 risers as the section shows; 'T 16' plate following the winders or a flat plate at the half-landing level. D1 / E1: steps cast on fill over the 'T=10cm' slab-on-grade, or a self-supporting waist (ST p.8 note 18 '16 cm' is written for roof slabs, not stairs). RS-C: 'T 16' continued round the curve, or another section | T-287 (ALSENAN_SEARCH_T287.json: G2-a, G2-c, G2-w), T-184, T-258, T-281 |
| G3 | DOME-3 / D-21 (+ T-185 item 7) | tower dome over the 2F maid room (+13.90 roof); drums of the two terrace domes on the +9.70 roof (to the springing +11.00) | arch 2F plan: hidden circle 1300 r 2.205 over the maid room; SE elevation 441 / 215 (T-185); ST p.6: flat B2 slab panel, no opening, ring or circle; ST p.7: one generic DETAIL OF DOME 442 / 190 / 10, ring 20 'AS PER ARCH', no drum, no dome named; arch section B-B: drum '130', material / thickness not printed (T-185); ST p.8 note 4 | is the tower dome a reinforced-concrete shell over a new opening in the +13.90 slab (opening, trimmer beams or ring, shell section: the p.7 rise 1.90 vs the elevation 2.15) or an architectural cap on the flat slab; the drums' material and wall thickness | tower dome: no value (outer surface 29.797 m2 from the elevation, T-185; the freelancer's third dome 2.260 m3); its opening / ring / trimmers UNKNOWN; 2 drums no value (outer face 18.061 m2 each, geometry only) | (a) the p.7 detail serves the tower dome too (shell 0.10, ring 0.20) on the elevation's 4.41 / 2.15 cap with an opening in the p.6 slab; (b) an architectural cap on the flat slab as p.6 draws; drums: reinforced-concrete wall or blockwork, thickness to state | T-287 (G3-a, G3-b), T-185, T-258, T-112 (D-21) |

Note for the Lead: row A7 already carries the D-21 part ("is there an opening and dome here", 2F maid-room dome) and P-8
lists it beside G3: G3 above contains it with its structural questions; send it once (drop the D-21 part from A7 or mark
A7's D-21 'see G3').

## 6. Verdict proposals (who is right)

| Item | Proposal |
|---|---|
| G1 two columns 1.430 m3 | ENGINE_WRONG (candidate V3.0.9 4.50 m basis, 1.2375) / T-248 HELD range RESOLVED by the drawing: base +0.25 for both (DRAWING-DERIVED, two readings agree on C3, the space reading settles C5) |
| G1 necks 10BD / 10C5 | cause TWO_GROUND_SLAB_LEVELS withdrawn; UNRESOLVED on Q-21 C only (lower bounds 0.1944 / 0.192 unchanged) |
| G2 ST-01 / ST-02 straight waists | ENGINE_RIGHT (T-258 0.16 = printed 'T 16' on every flight, landing and the turn); no move |
| G2 MS1-T, MS2-TR, D1, E1, RS-C | UNRESOLVED (designer, row G2) |
| G3 | UNRESOLVED (designer, row G3); the freelancer's third dome 2.260 m3 stays scope-UNKNOWN |

## 7. Rules (proposed; scope and provenance) and lessons-register row

- **R-RFI-SEARCH-1** (process, any villa; T-287): a designer row is drafted only after a reproducible search lists, per
  sheet, the entities inside the element's own outline plus a stated margin and finds no printed answer; a printed
  answer settles the item (reported with its status, never asked); a missing answer stays HELD, never a default.
  Tests: test_search_fixture (found / missing / just outside / mirror / turned / cm units / callout vs ring / missing anchor).
- **R-COL-BASE-ADJ-1** (geometry rule, any villa; T-287, builds on R-NECK-ENDS-1 and T-214): the GF column base on a
  ground-beam line is the slab top of the one building floor printed in the spaces beside the column (FFL - build-up);
  exterior ground beside it (the court level) is not a building slab; two different building floors beside it are the
  designer's (UNRESOLVED, both readings named); none printed -> HELD. Regression: test_settle_column_base (normal annex +
  passage -> SETTLED; adverse annex + house -> UNRESOLVED; exterior only -> MISSING; build-up missing -> MISSING; bay
  reading stops at the next band; space reading only through an open side).
- Lessons row (proposed): "A held range named 'two levels meet' was carried for a day without checking what is actually
  printed on each side; the side the range assumed (+0.95) is a 1.20 m exterior passage | before holding a member
  between two datums, print the levels in the spaces that touch it (both sheets) and name the space each datum belongs
  to | test_settle_column_base + test_alsenan_search G1 | PROPOSED."

## 8. Checker re-run (one search)

`python3 -I research/agents_t287/t287_alsenan.py <private ST7757 dxf> <private P7757.dxf>` reproduces
ALSENAN_SEARCH_T287.json byte for byte (test_rerun_on_the_private_drawings_reproduces_the_committed_file). Suggested own
re-measure: G1 on ST p.3 by hand: from C3 365 the west bay prints 1B4 '+0.30', the east bay 1B6 '+0.15'; the C11-line band
(edges 10A / 7C9) separates the passage from 1C0 '+1.00'; on the arch GF plan nothing is drawn between the kitchen (C5's
south-west) and mark 405 '+0.30'.

## 9. Not done / uncertain

- The architectural sections and elevations are searched as whole sheets (words), not by region: the plans are
  registered, the sections are not (no common marks). The turn's 5 risers on section A-A are T-184's merged reading.
- C5's settlement rests on the space reading (the kitchen is open to the +0.30 lobby on the arch GF plan); its ST p.3 bay
  alone prints no mark. If the Checker reads a partition between kitchen and lobby, C5 returns to HELD (C3 stays settled).
- The PDF-only pages are a hand reading (vector SHX text does not extract).
