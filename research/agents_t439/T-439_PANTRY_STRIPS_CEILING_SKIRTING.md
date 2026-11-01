# T-439: ceiling and skirting of the two GF pantry strips (T-435 SILENT items)

Worker 2 (lane A), 2026-11-01, run session_01E6cPnebZk9g8ZqLNpYQ7GQ. Development villa, not an accuracy claim. Research
only: research/agents_t439/* and tests/t439_strip_owner/*; no engine module, method, rule / knowledge version,
registry, candidate or released quantity changed. ERS read for s.2.1 (element first), s.2.2 (evidence), s.2.4
(reconcile in units), s.7 (lesson). Drawings: Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip -> P7757.dxf
(sha256 ab54dd55) and "ST7757 dxf.dxf" (9f9d1179), decoded into the private folder only. Own released ARCH_TAKEOFF_V2.9
run of the DXF (strips, faces); own T-139 slab faces and T-147 column-fit (GF / 1F / 2F: 30 / 20 / 9 columns, spread
0.000 m); own T-271 overlay re-run reproduces the merged pantry rows (GF-RC06FED B27 0.3524 / CB8 1.600 m; pantry part
B27 6.8969 m). Only handles, layers, lengths, areas, ids, marks and statuses are committed (EXTRACT_T439.json).

## 1. The physical element (ERS s.2.1)

Both strips lie inside the printed GF open pantry (GF-07, 450 x 300, owner Q-37 A: wet within the box). The engine cut
them out of the pantry floor along lines the drawing does not draw (T-286, T-427):

| Strip (floor line) | m2 | Where | Edges, drawn handle (P7757.dxf) | What it is physically |
|---|---|---|---|---|
| GF-SITE-0a31aaa10796d33a (L-6c83b9fc, wet tile 1.100) | 1.100 | under the east counter L (1.0999 m2 inside the counter outline) | south 1.400 A6 (layer 1, pantry south WALL face); east 1.300 B3 (layer 5, the pantry's OPEN edge to the dining); north 0.500 none (engine zone line); inner 0.800 / 0.900 / 0.500 B4 / AA / B2 (layer 5, counter outline) | pantry floor under the counter; ceiling of the pantry over it |
| GF-OP-003-NO-OPENING (L-50307dd9, wet tile 0.600) | 0.600 | a 3.00 x 0.20 band across the pantry: the part inside the box of V2.9 strip SITE-baa7db7fb0d465b6 (OP-003 THRESHOLD 1.964 m2, the garden-band edge prolonged 3.80 m west, T-427) | west 0.200 AF (layer 1, pantry west WALL face); east 0.200 B3 (open edge); north 3.000, south 0.500 + 2.500: none (engine zone lines; the band lines A8 / A9 / 4B4 stop 3.80 m east of B3) | pantry floor in the middle of the room; ceiling of the pantry over it |

Jamb search: no door or window insert and no jamb line bounds either strip (inserts within 0.5 m of the box: door D120
33E 3.2 / 3.4 m away in the north wall, two furniture / level blocks); no strip edge lies on a jamb. So neither is a
doorway strip (R-T286-1): both are ROOM PIECES of the pantry. The pantry box closes: 13.455 net of column 2FAE =
GF-RC06FED 2.800 + GF-RC99C2A part 8.955 + 1.100 + 0.600 (residual -0.000001 m2).

What the structural roof slab (ST7757, GF roof plan, column-fit) draws over them: strip 1.100 = slab 0.649 + beam B27
(BM-GF-048, D 0.85, r2 CALCULATED) 0.311 + CB8 (BM-GF-040, D 0.75) 0.140; strip 0.600 = beam B5 (BM-GF-016, D 0.50)
0.443 + B27 0.039 + two UNREGISTERED beam pieces GF-151 / GF-152 0.068 + 0.049 (a 0.588 x 0.20 rectangle at the east
end of the B5 band, split by a diagonal line; no register row). No opening, void, stair or dome over either strip:
nothing removes the ceiling plane.

## 2. Result in engineering terms (TABLE_T439.csv, summary.json)

**Ceiling (both strips: ENGINE_WRONG, missing line).** The pantry ceiling continues over both strips. Before: the
pantry box ceiling carried 2.800 (L-1624ef49) + 8.955 (pantry part of L-eb3be58f) = 11.755 of 13.455 m2; after the
proposal **13.455 m2 = the box net (closure 0.000)**.

| Strip | Decor ceiling (DRAWING-CONFIRMED area) | Owner-method bulkhead faces (ASSUMED — OWNER-APPROVED, Q-43 + Q-48 A) | HELD | No face |
|---|---|---|---|---|
| 1.100 | 1.100 m2 | B27 0.842 m x 0.25 = 0.2105 m2; CB8 1.400 m x 0.15 = 0.2100 m2 | - | - |
| 0.600 | 0.600 m2 | B27 face to B5 0.2485 m x 0.25 = 0.0621 m2 | 0.812 m (B27 / GF-151 / GF-152 faces inside the strip) | B5 D 0.50 (under the 0.60 allowance) |
| on the strip's zone lines | - | - | 1.177 m (B27 faces toward GF-151 / GF-152 on y 1.30 / 1.50) | B5 faces |
| **Total** | **1.700 m2** | **0.4826 m2** | **1.989 m** (Q-61 C, never 0) | |

Paintable gypsum (owner method) +2.1826 m2; board type HELD (wet room, Q-57 A mod (2)); cove HELD (no detail); the
drawing-derived bulkhead candidate stays outside every total (D-40).

Beam-face reconciliation in units (measured on the WHOLE pantry ceiling, R-CEIL-R2-3 applied to the box, not the piece):
B27 free edge over the box 9.7164 m = carried 0.3524 (L-1624ef49) + 6.8969 (L-eb3be58f) + in the strips 1.2905
(0.842 + 0.2485 valued, 0.200 HELD) + on zone lines 1.1766 (HELD) - residual 0.0000; CB8 3.000 = 1.600 carried + 1.400
(strip 1.100) - residual 0.0000. The 1.400 + 0.842 + 0.2485 m were measured by no ledger: the per-piece overlay of T-271
never saw the strips (they were not faces of any room), and faces lying on an engine zone line are excluded by both
neighbouring pieces as 'room boundary'.

**Skirting (both strips: NOT_APPLICABLE_WITH_EVIDENCE, no skirting line).** Wall-face edges: A6 1.400 (GF-07|GF-W01) and
AF 0.200 (GF-07|GF-W16) = **1.600 lm**, both faces of the pantry wall-tile line L-f5c5a1a9 (FIN.WALL.TILE 32.3422 m2,
all pantry walls but the open edge, T-312 / T-315 r2 MERGED): the porcelain owns the base (Q-48 A, UP-PANTRY-003,
R-T440-1). This is exactly the "counter cells 1.6 lm, no line" of the T-315 r2 base closure (1.9 + 3.5 + 1.6 = 7.000
lm): it now has its owner by name, and the pantry base 7.000 lm closes with no skirting. Other edges carry no base:
open edge B3 1.500, counter outline 2.200, undrawn zone lines 6.500 (no wall). Skirting family: no change.

## 3. Lane I proposal (one row; nothing applied here)

1. ADD one FIN.CEILING line "GF pantry strips (counter strip + OP-003 strip part)", element e.g.
   `HL:CEILING:WET:GF:GF-PANTRY-STRIPS`, class WET, decor 1.700 m2 DRAWING-CONFIRMED + owner bulkhead 0.4826 m2
   ASSUMED — OWNER-APPROVED apart (same structure as L-1624ef49 after T-284 / T-335), held list: board type, 1.989 m
   beam edges (GF-151 / GF-152 unregistered), cove. One m2 one line: the strips are in no other ceiling line (V2.9:
   no FIN.CEILING element names OP-003 or either strip; T-435 on V3.0.37: SILENT). Alternative with the same
   quantities: extend L-1624ef49 (the counter-cell face) by the strips; lane I's choice, not both.
2. Skirting: record the two strips OWNED_NOT_APPLICABLE on L-f5c5a1a9 (no new line, no figure); the T-435 / T-446 join
   reason code TILE_OWNS_BASE citing L-f5c5a1a9.
3. Floor lines L-6c83b9fc / L-50307dd9 unchanged.

## 4. Freelancer (quantities only)

His ceiling row (409.58 m2, T-283) and his GF reception / pantry figures cover these strips by area (T-435 / T-427): the
engine ceiling was SHORT by 1.700 m2 of built ceiling: ENGINE_WRONG (missing line), FREELANCER_RIGHT on scope; no rule
difference. Skirting: he runs a dry skirting along the pantry walls (T-106 / T-315): RULE_DIFFERENCE by Q-37 A / Q-48 A
(wall tile owns the base), as recorded in T-315 r2; nothing new.

## 5. Rule, tests, lessons row (proposed)

R-T439-1 (any villa; module strip_owner_v1.py, no villa constant): a strip bounded by jambs on two edges is a doorway
strip (ceiling = opening soffit; a room ceiling on it is refused without a drawn soffit); a strip inside a printed room
box is a room piece: the room's ceiling continues over it (plan area + owner bulkhead faces of the beam faces in it that
no line carries, D - max(0.60, D_neighbour); unregistered / not CALCULATED -> HELD lm); per edge, a wall face of a
full-height-tile room is the wall-tile line's base, a wall face elsewhere is skirting (behind a fixture: HELD), open edge
/ fixture outline / undrawn zone line carry no base; beam faces are measured on the whole room ceiling.

Tests tests/t439_strip_owner (31): villa K439 (not Alsenan): counter piece in a wet tiled kitchenette (decor 0.96,
bulkhead 0.18, held 0.30, BK2 no face, tile owns 1.20 lm, no base 3.20), dry strip 2.00 lm, doorway strip, step face
against a deeper beam, carried face not re-counted, edge roles under rotations 0 / 37 / 90 / 211 deg x mirror, box
closure; adverse: 'door strip given a room ceiling with no drawn soffit' refused, strip outside the box HELD with area
kept, held dry wall lm, wall behind a fixture HELD, tiled room without its tile line refused, unknown role refused, mm
units refused (strip / edge / segment), beam not CALCULATED and missing depth -> HELD edge, closure with a None piece
refused, an engine zone line is not a drawn line; committed Alsenan table reproduces and pins.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | two pantry strips (1.700 m2) carried a floor line and no ceiling; 2.49 m of beam faces over the pantry (B27 / CB8, 0.48 m2 owner method) were measured by no ledger | ceiling and bulkhead ledgers were built per engine face; strips cut out by undrawn zone lines were no face, and a beam face lying on a zone line was excluded by both neighbouring pieces as 'room boundary' | R-T439-1 (any villa): a strip inside a printed room box takes the room's ceiling; beam faces are measured on the whole room ceiling (box), never per engine piece | tests/t439_strip_owner | proposed |

## 6. For the Checker (re-measure, not from this file)

1. P7757.dxf: the 1.100 strip's six edges against A6 / B3 / B4 / AA / B2 and the undrawn north edge; the 0.600 strip:
   AF (0.200) at the west wall, B3 at the east, no line across the pantry at either long edge (the band lines A8 / A9 /
   4B4 start 3.80 m east of B3); no jamb on any edge.
2. ST7757, GF roof slab: B27 (BM-GF-048 D 0.85) diagonal face across the counter strip: 1.1944 m from the south wall
   to the B5 band, of which 0.3524 in GF-RC06FED (carried) and 0.842 in the strip; CB8 (BM-GF-040 D 0.75) north face
   3.000 m along the south wall, 1.600 carried, 1.400 over the strip. By hand: 0.842 x 0.25 + 1.400 x 0.15 + 0.2485 x
   0.25 = 0.4826 m2.
3. The box closure 13.500 - 0.045 - 2.800 - 8.955 - 1.100 - 0.600 = 0.000; the tile line L-f5c5a1a9 faces include A6
   and AF (T-315 FACE map).
4. `python3 -I research/agents_t439/t439_alsenan.py --check`; with the drawings, re-run t439_extract.py.

## 7. What is missing

The identity of the unregistered pieces GF-151 / GF-152 (B5 continued or B27 split by a drafting line): 1.989 m of
beam edge HELD until the structural register reads them (lane S, beam register); the wet board type (HELD, Q-57 A
mod (2)); the V3.0.39 candidate was not re-run here (the strips carry no ceiling line in V3.0.37, T-435; V3.0.38 /
V3.0.39 added only the stair-room parts and the lift threshold): T-446 re-runs the join. No owner question: ERS s.2.7
not met (all items are drawing reads or lane I line work).
