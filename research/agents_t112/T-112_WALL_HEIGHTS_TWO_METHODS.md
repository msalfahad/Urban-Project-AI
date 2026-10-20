# T-112: wall heights of every Alsenan room by the owner's manual method and by the drawings, side by side (NO REPO CODE)

Worker 3, 2026-10-20 14:00-15:20 UTC. Gate 2 (plaster, paint, wet-wall tile heights). Development villa (Alsenan), not an
accuracy claim; nothing released changes. Table: `ROOMS_T112.csv` (32 rows, the T-088 / T-090 ids), produced by
`calc.py` (standard library, every input typed in it with its source). No client names, no coordinates, no images.

Rules: owner Q-43 (manual height method) and Q-48 A (wet-wall tiles to the 0.15 decor ceiling), preserved by the owner
correction 2026-10-20 12:15 (OWNER_SESSION_CHANGES.md); Q-52 C modified (drawing-derived, per room, plaster and paint
separately, unknown ceiling = HELD, never a common height); Q-54 B (annex datum HELD until shown to be the structural
slab); Q-14 (slab 16 cm where the drawings confirm it; separate FFL, slab top, soffit, clear height); Q-29 / Q-44 (dome
positions are open skylights, ring beams stay); UP-QTY-STATUS-001 (held never 0). Ceilings are not in this table (Q-57).

## 1. What was read in this run (second drawing for every input used)

| Evidence | Source (Drive "Alsenan chalet project") | How | Result |
|---|---|---|---|
| Slab thickness | ST7757 dxf.dxf, general notes (layer S-NOTE, Arabic SHX decoded with the repository decoder) | text | "all slabs cast 16 cm thick unless stated otherwise": **0.16 m DRAWING-VERIFIED**; the only other thickness printed is T=10cm on the ground-floor plan (court slab), none for a roof or floor |
| Levels | ST7757 dxf.dxf (LEVEL texts), P7757.dxf (LEVEL, elevations) | text | structure prints only the ground marks (+0.15 / +0.30 / +1.00) and +9.70; no slab-top or soffit level on any floor or roof plan |
| Section A-A | p7757_arch_sheet10.pdf, rendered 400 dpi, measured (157.4 px per m, checked on the printed "420") | picture + pixel profile | level marks sit on the TOP of one undifferentiated slab band; the band is drawn 0.22-0.23 m deep (16 cm structural + something, not split); no beam below a slab, no false ceiling, no build-up layer |
| Section B-B, annex | Alsenan_Architectural_P7757_Pages_11-12.pdf p.11, 400 dpi | picture + pixel profile | see section 2 |
| Beams over each room | ST7757 dxf.dxf roof-slab plans laid on P7757.dxf plans by pure translation, found from the column outlines (S-COL.BON) in both files: GF 31 / 30, 1F 20 / 20, 2F 9 / 9 columns coincide | overlay pictures (scratchpad only) | confirms T-088: CB6 crosses the dewaneya; B26 and B27 (0.85) cross the GF open room; B19 (0.75) crosses the 1F bed room 380 x 430. New: B6 (0.50) also crosses that room; B2 (0.40) crosses the 2F maid room; the two 1F-roof dome openings lie over 1F rooms (below) |
| Opening heads | research/agents_t083/OPENINGS.csv (merged, hand-read elevations) | table | heads above the room floor: GF master bed room W03 4.30, 1F east master bed room W17 crown 3.70, 1F living W15 >= 3.10, 1F bath W18 3.00, 1F west master W14 2.80, GF entrance D01 2.50 |
| Ceilings / finishes | research/agents_t091 (merged census of all 12 architectural pages and the DXF) | table | no ceiling level, false ceiling, bulkhead, cornice or floor build-up printed anywhere |

## 2. Annex datum (owner Q-54 B): what +4.30 is on the drawings

- Section B-B: the +4.30 arrow ends on the top line of the annex roof band; the "400" chain runs from the top of the floor
  band (+0.30) to that line; the "480" chain from +-0.00 to the top of the balustrade (+4.80, measured 0.50 m above the
  band). The roof band is drawn like every floor band (about 0.23 m, one hatch, no layers).
- On the main house the same kind of band top carries the FINISHED floor marks (+5.50, +9.70 = FFL, owner Q-43), and the
  plans print the roof terraces at the same value as the next FFL (1F plan: terraces +5.50; 2F plan: 1F roofs +9.70):
  the architect's marks are finished-surface marks.
- The sanitary drainage plan prints SLOPE 1 % on the +4.30 roof (T-091 F1): a falls screed exists above the slab, its
  thickness is not printed; the structural set prints no level for the annex roof slab.

Result: the documents do NOT make +4.30 the structural slab top; by the drawing's own convention it reads as a finished
roof level. **Drawing-derived annex heights stay HELD** (6 rooms: dewaneya, wash, W.C., driver, driver W.C., kitchen).
The owner-method value is shown as his method gives it on the printed marks (4.00 - 0.85 = 3.15 m), labelled not
releasable while Q-54 B holds the datum. Designer request DCR-1 below.

## 3. Heights per zone

| Zone | Floor-to-floor (printed marks) | (a) Owner manual method | (b) Drawing: slab soffit above FFL, build-up 0 / 0.10 | (b) Paint and plaster height |
|---|---|---|---|---|
| GF main (+1.00) | 4.50 | 3.65 | 4.34 / 4.24 | HELD: no ceiling plane drawn |
| GF annex (+0.30) | 4.00 on marks, datum HELD | 3.15 (not releasable, Q-54 B) | HELD | HELD |
| 1F (+5.50) | 4.20 | 3.35 | 4.04 / 3.94 | HELD |
| 2F (+9.70) | 4.20 | 3.35 | 4.04 / 3.94 | HELD |
| Stair halls, GF W.C. 175 x 135 and basin space (level unclear) | - | HELD | HELD | HELD |

What the owner's formula means physically (useful for both methods): with his 0.10 floor build-up, slab-top - 0.60 beam
is a beam soffit, and 0.15 below it is the decor ceiling. So his line equals "0.15 under the soffit of a 0.60 m beam".
Where a drawn beam deeper than 0.60 m CROSSES a room, his line meets or passes that beam's soffit (section 4).

## 4. Owner line checked against the drawings (the method differences and the real conflicts)

| Room | Check | Numbers (above the room's FFL; owner 0.10 build-up where marked) | Kind |
|---|---|---|---|
| GF open room (dining / reception / saloon) and pantry | B26 (0.65 x 0.85) and B27 (0.90 x 0.85) cross the ceiling | beam soffit 4.50 - 0.10 - 0.85 = 3.55 < owner line 3.65 (0.10 m into the beam) | METHOD DIFFERENCE: a flat ceiling at 3.65 cannot pass; bulkhead round the beams or the room at 3.40 (T-090 option C) |
| GF wash lobby (2 basins) | B11 0.75 crosses | soffit 3.65 = owner line: no room for the 0.15 decor under it | METHOD DIFFERENCE (bulkhead or 3.50) |
| 1F bed room 380 x 430 | B19 0.75 (and B6 0.50) cross | soffit 3.35 = owner line | METHOD DIFFERENCE (bulkhead or 3.20) |
| GF dewaneya (annex) | CB6 0.75 crosses | soffit 3.15 = owner line on the printed marks | METHOD DIFFERENCE, datum HELD |
| GF master bed room | W03 pool-side glazing +1.00 to +5.30 | head 4.30 vs owner line 3.65 (+0.65); vs slab soffit 4.24 (+0.06); vs B8 (0.75) soffit on the glazing line 3.75 even with no build-up (+0.55) | **CONFLICT** architecture vs structure (PROBABLE: that W03 is this glazing is T-083's reading): DCR-2 |
| 1F east master bed room | W17 crown 0.20 + 3.05 + 0.45 = 3.70 | +0.35 above the owner line 3.35; +0.25 above the CB12 (0.75) soffit 3.45 if CB12 runs on that wall (to check) | CHECK-HEAD (method) / possible CONFLICT: DCR-3 |
| 1F west master bed room 425 x 450 and its two baths | the west 1F-roof dome opening (ring 4.42 m, B4; open skylight by owner Q-29 / Q-44) lies over most of the bed room and part of both baths; the bed-room / bath partition runs under the opening | no slab over the opening: there is no ceiling plane there unless one is designed | DESIGN GAP: DCR-4 |
| 1F living area | the east dome opening lies over the room | same | DESIGN GAP: DCR-4 |
| 2F maid room | architecture draws the third dome over it; the structural slab is flat (no opening, no ring) | owner Q-27 A three domes + Q-29 open skylights, so an opening is expected where the structure has none | CONFLICT (C-1): DCR-5 |

No owner question is needed: none of these is an owner choice. The owner's line stays his method; the drawing column shows
where it meets a beam or a window, and the designer must answer the conflicts.

## 5. Results against the freelancer (gross wall m2, before opening deductions; nothing released)

| Set | (a) Owner manual method | (b) Drawing-derived | Freelancer | (a) vs freelancer |
|---|---|---|---|---|
| 4 dry rooms on verified datums (1F bed rooms 425 x 450, 500 x 365, 380 x 430; 2F maid room), 69.90 m of wall | **234.17 m2** (3.35 m) | HELD; envelope up to 282.40 m2 (4.04 m slab soffit, no build-up) | 258.40 m2 (3.40 m flat; 380 x 430 with the passage walls) | -24.23 m2 (-9.4 %); same-wall rooms only (425 x 450, 500 x 365, maid): 179.90 vs 182.58, -2.68 m2 (-1.5 %) |
| 2 annex dry rooms (dewaneya, driver), 32.63 m | 102.78 m2 on the printed marks, NOT releasable (Q-54 B) | HELD | 117.00 m2 (3.60 m) | -14.22 m2 (-12.2 %), UNRESOLVED |
| 6 dry rooms (T-090 set) | 336.94 m2 | HELD | 375.40 m2 | -38.46 m2 (-10.2 %) |
| Wet-wall tiles, 15 rooms with a length and a floor-to-floor | 450.10 m2 (annex 109.62 not releasable; verified datums 340.48) | HELD; envelope up to 408.67 m2 on the verified-datum rooms | 433.83 m2 (one total, 3.00 m) | not comparable room by room |
| Project internal plaster / paint | HELD (7 dry rooms have no closed wall run; stairs; nets wait on door heights, Q-55) | HELD | 1 151.14 / 1 191.13 m2 (nets) | - |

Change since the last report: no released quantity moves (still held). New: the drawing-derived column per room with its
envelope and status, the annex datum evidence, and five places where the owner line meets the drawings (section 4).

Difference between the methods, per room (column OWNER_MINUS_SOFFIT): on verified datums the owner line sits 0.59 m
below the slab soffit computed with his own 0.10 build-up (0.60 beam + 0.15 decor - 0.16 slab); for the 4 dry rooms
that is 69.90 x 0.59 = 41.24 m2 of wall between his paint line and the slab soffit, which plaster may or may not cover
(specification not printed, Q-52 "plaster may run above the false ceiling").

## 6. Who is right (proposals for the verifier)

- 1F / 2F dry rooms with the same walls (425 x 450, 500 x 365, maid room): lengths AGREE (printed); heights
  RULE_DIFFERENCE (owner method 3.35 vs freelancer flat 3.40, -1.5 %); drawing-derived UNRESOLVED (no ceiling plane drawn).
- Annex: UNRESOLVED (Q-54 B; freelancer 3.60 m on a storey printed 4.00 m on the marks).
- GF open room / pantry and the three rooms with a crossing 0.75 beam: owner line is a METHOD result; the drawing says a
  bulkhead or a lower ceiling is needed there: not a verdict, a design item.
- GF master bed room and 1F east master bed room: UNRESOLVED (CONFLICT, designer).

## 7. Designer clarification requests (proposed for docs/agents/DESIGNER_CLARIFICATIONS.md; the Lead files them)

- DCR-1 Annex roof: the structural slab top level of the +4.30 roof and the roof build-up (falls screed at 1 %,
  insulation, protection); is +4.30 the finished roof?
- DCR-2 GF master bed room: the pool-side glazing W03 is printed to +5.30, above the 0.75 m beam B8 drawn on the same line
  (soffit at most +4.75): which governs (beam upturned / moved, or a lower glazing head)?
- DCR-3 1F east master bed room: W17 crown +9.20 against CB12 (0.75) near the void: confirm the beam position and depth.
- DCR-4 1F dome positions (now open skylights): the west opening (4.42 m) lies over the 1F west master bed room and part of
  its two baths, with their partition under it; the east one over the living area. Ceiling and wall treatment under the
  openings (glazed skylight at the slab, at the drum top +11.00, or a closed ceiling below), and how the partition ends.
- DCR-5 2F maid room: architecture draws a dome over it, the structural slab is flat with no opening; confirm.
- General: a reflected ceiling plan or ceiling levels per room, and the floor build-up per floor, are needed before any
  drawing-derived plaster or paint height can be released (every room is HELD today).

## 8. What is missing

Ceiling levels (none printed: every drawing-derived height HELD); floor build-up (only the owner's 0.10 value);
the closed wall runs of 7 dry rooms (GF open room, GF master bed room, 1F corridor, 1F east master bed room, 1F living,
stair halls: a CAD outline task); door heights for every net (Q-55); the plaster-above-ceiling specification. Not done
here: scaled readings of doors in the sections (sheets carry "not to scale" notes, T-091 F2), the dome drum heights in
detail (T-063 has +11.00 and the dome rise).
