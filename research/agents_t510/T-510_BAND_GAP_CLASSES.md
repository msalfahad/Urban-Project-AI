# T-510: band-path small-gap classification as a NEW version (BAND_GAP_CLASSES_V1)

Worker 3, claim 2026-11-04T17:02Z (`date -u`), branch agents/task-T-510, engine base f1ea10f5. Non-candidate, unwired:
no frozen file, released method, rule / knowledge version file, registry or candidate line changed. Input for the
development-villa census: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`), decoded
only into .work/private; outputs hold widths, classes, bounds and entity handles only.

## Physical element (ERS s.2.1)
A hole through a wall's masonry between two bounding elements, at any width. Not such a hole: a wall junction (a
crossing wall runs through the band; both band faces stop at its faces, masonry is continuous), the slivers between
the pieces of one column drawn as several boxes, a column face standing on a jamb, a face break with nothing bounding it.

## Defect (engine read only, T-460 C5, Checker-verified)
`opening_gaps.band_gaps` keeps a gap only when `g >= 0.50 m`, and `lintel_measure._split_at_columns` drops every
column-cut piece under 0.50 m ('the wall reach between a jamb and a column face is not an opening'). Development villa
1F W18 (0.467302 m, column face + masonry jamb, 8 glazing lines 1.939997 m) has no engine opening; per-project ledgers
(T-175 / T-274 / T-305 / T-388) restore it by hand. Any other villa loses such openings silently (against Q-73).

## Method R-T510-1 (`engine/source/band_gap_classes_v1.py`)
1. Every band gap down to the 2 mm numerical floor on the engine's own band path (same face lines, bands, merge and
   jamb tolerances; legacy or robust Geometry; boxes or V2.7.1 column polygons).
2. Column pieces JOINED first: the column obstacles inside the gap are projected on the band axis and joined where they
   overlap or stand within the engine's 30 mm jamb tolerance; the gap is then cut at each joined column; no piece is
   dropped for its width.
3. Each end bounded by COLUMN_FACE, MASONRY_JAMB, CLOSURE_JAMB, WALL_JUNCTION (R-T460-1 crossing-face test) or NONE.
4. Class (first that holds): NO_BOUNDING_ELEMENT (HELD) -> OPENING / WINDOW (glazing >= 0.5 x width) -> OPENING / DOOR
   (swing fits) -> WALL_JUNCTION (both ends; NOT_AN_OPENING) -> COINCIDENT_FACES (< 2 mm; NOT_AN_OPENING, listed) ->
   NO_DISTINCT_JAMBS (< 30 mm jamb tolerance; HELD) -> OPENING / UNMARKED.
5. Status: an OPENING the released path already lists is ENGINE (unchanged); others DEDUCT_MEASURED (width x printed
   height) or DEDUCT_HEIGHT_HELD (never 0). A >= 0.50 m gap the released path refuses for an unbounded end stays
   ENGINE_REJECTED (unchanged, listed); under 0.50 m the same class is HELD.
The width decides no class: 0.499 / 0.500 / 0.501 m windows are all OPENING / WINDOW; only the released path's flag flips.

## Development villa census diff (no project ledger; `t510_alsenan.py`, BAND_GAP_CLASSES_T510.csv, summary_t510.json)
| floor | engine openings | reproduced as ENGINE (max end diff) | new records |
|---|---|---|---|
| GF | 29 | 29 (0.0 m) | 1 COINCIDENT_FACES 0.000000 m (column face on a masonry jamb, NOT_AN_OPENING); 1 ENGINE_REJECTED 1.958 m (unchanged) |
| 1F | 22 | 22 (0.0 m) | **OPENING / WINDOW 0.467302 m** (COLUMN_FACE + MASONRY_JAMB, glazing 1.939997 m, height HELD: W18 without any ledger); WALL_JUNCTION 0.150 m (D2:2769/2770, D2:2774/2775); 1 ENGINE_REJECTED 3.059 m (unchanged) |
| 2F | 8 | 8 (0.0 m) | none |
differs_from_engine 0 on every frame: no other band changes. Candidate effect 0.000 m2 (W18 is already deducted by the
merged ledgers: blockwork 0.4673 x 2.160 = 1.0094 m2); when wired, the ledgers become checks instead of the only source.

## Agreement with T-460 (Checker-verified census)
Same two sub-0.50 m records on 1F (0.467302 window, 0.150 junction); GF/2F none apart from the 0 m coincident piece
(T-460's floor dropped it; now listed). Naming difference only: T-460 SUB_MIN_GAP_UNEXPLAINED (HELD) = here OPENING /
UNMARKED with the area HELD (a jambed gap is a hole by its bounding elements; the quantity effect is identical).

## Tests (`tests/t510_band_gap_classes`, 18, non-Alsenan villa M + T-460 villa K)
Normal: 0.467 m window beside a split column KEPT (deduct 0.467 x 2.16 = 1.008720 m2; net 24.000 -> 22.991280 m2),
0.150 m junction refused; reproduction (released path returns no opening). Adverse: column in 3 pieces (5 mm apart)
joined, no sliver; rotation 37 / 211 deg, mirror, m units; boundary 0.499 / 0.500 / 0.501; staggered face break with no
bounding element HELD (released path: no record); height missing HELD; units missing refused; robust path identical;
T-460 fixtures map one to one.

## Lessons-register row proposed (ERS s.7)
| 2026-11-04 | the band path drops wall gaps under 0.50 m, incl. column-cut pieces (W18 0.467 m lost) | a width minimum
stood in for the physical test (bounding elements) | classify every gap by its bounding elements after joining the
pieces of one column; no width decides existence; unbounded HELD (R-T510-1, every villa) | tests/t510_band_gap_classes |
PROPOSED |

## Missing / not done
Wiring into ARCH_TAKEOFF V3.0.x (a later stream F row): the new OPENING records need their kind and height from the
opening-schedule chain, and the four per-project W18 ledgers then become regression checks. Curved bands (arch_v29
MIN_GAP_M 0.40) are not covered by V1. Gap ids follow the band direction (a mirror reverses them).
