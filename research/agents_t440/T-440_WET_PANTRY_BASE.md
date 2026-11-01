# T-440: wet-pantry wall faces inside the GF open-room skirting line L-71e2e002

Worker 2, 2026-11-01. Drawing: Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55)
and "ST7757 dxf.dxf" (9f9d1179), decoded into the private folder only. Candidate of record reproduced on those copies:
research/agents_t167/v304_run.py then research/agents_t421/v3038_run.py -> V3_0_37_BOQ_LINES.json 733f2efb (= the
T-420 pin) and V3_0_38_BOQ_LINES.json 57cca61c (= the board's V3.0.38 pin). Code: `wet_base_owner_v1.py` (R-T440-1),
`t440_alsenan.py` (extract / write / check), `EXTRACT_T440.json`, `FACES_T440.csv`, `summary.json`. Tests:
`tests/t440_wet_base_owner` (18). Nothing wired; no candidate or released quantity changes.

## 0. Result

**Over-count on L-71e2e002 = 0.000 lm in the candidate of record (V3.0.37 and V3.0.38), with proof face by face.**
The open pantry's wall base inside the open-room engine room GF-RC99C2A is **3.500 lm** (7 base faces), and the line
already takes exactly these 3.500 lm off by name: T-315 r2 (MERGED, Gate B) wrote one deduction row per face
(158 0.7591, 159 0.3409, 2FAE 0.90 + 0.05, AE 0.80, AF 0.65 = 3.500, source `base_ownership_v3021.on_tiled_faces`), so
the line reads V2.9 wall + column 28.171589 - 3.500 = **24.671589 lm** = the candidate's net (difference 0.000000). The
T-435 note "wet-pantry walls inside L-71e2e002 = possible over-count" was raised on the line's room boundary without
reading its deduction rows; it is closed by this table: no quantity to move. The base belongs to the pantry wall-tile
line L-f5c5a1a9 (FIN.WALL.TILE, PROVISIONAL, 32.3422 m2).

## 1. Physical element and rule (ERS s.2 step 1)

The base strip of a wall / column face. In the open pantry (GF-07, printed 450 x 300, T-286) owner Q-37 A puts the
whole box in the wet scope and Q-48 A / UP-PANTRY-003 tile its walls full height: the porcelain covers the base, so no
skirting is built there (one face, one owner layer, ERS s.2.2; UP-SKIRT-001 skirts dry rooms). The pantry has no wall on
its east side (B3 / AD, layer 5: the open edge to the dining). The engine keys skirting by ENGINE room: GF-RC99C2A holds
the pantry's north part (y from the OP-003 strip to the north face) together with the dry dining / living / reception.

## 2. Face table (own route: the engine's OWN edge roles + drawn handles)

Second route beside T-315 r2's drawing-entity walk: the released V2.9 run with a read-only wrapper around
`arch_rooms._one_sided_roles` records the roles of every boundary edge of GF-RC99C2A; each edge inside the pantry box
(west face AE to the open edge B3, south face A6 to north face 158) is laid on the drawn LINE / LWPOLYLINE it runs along
(layers 1, S-COL.BON, W; parallel within 5 mm).

| Face (engine edge) | Engine roles | Drawn handles | m | Base | Carried by L-71e2e002 in V3.0.38 | Base owner | Status |
|---|---|---|---|---|---|---|---|
| e043 north | COLUMN + WALL | 159 + 2FB4 (column face flush with the wall face) | 0.200 | 0.200 | 0 (row #159) | L-f5c5a1a9 wall tile | TILE_OWNS |
| e044 north | WALL | 159 | 0.1409 | 0.1409 | 0 (row #159) | L-f5c5a1a9 | TILE_OWNS |
| e045 north | DOOR_THRESHOLD | (gap, D-GF-06 / OP-008, D120 33E) | 1.000 | 0 | 0 (OP-008 deducted) | none | NO_BASE |
| e046 north | WALL | 158 | 0.7591 | 0.7591 | 0 (row #158) | L-f5c5a1a9 | TILE_OWNS |
| e047 NW column return | COLUMN | 2FAE | 0.050 | 0.050 | 0 (row OFF:WALL#2FAE) | L-f5c5a1a9 | TILE_OWNS |
| e048 NW column face | COLUMN | 2FAE | 0.900 | 0.900 | 0 (row OFF:COLUMN#2FAE) | L-f5c5a1a9 | TILE_OWNS |
| e049 west | WALL | AE | 0.800 | 0.800 | 0 (row #AE) | L-f5c5a1a9 | TILE_OWNS |
| e050 / e051 / e052 west | WINDOW + WINDOW_THRESHOLD | W09 frame 3BC / 3BF / 3C6 (OP-024, sill 1.0) | 0.05 + 1.40 + 0.05 | 0 (tile below the sill) | 0 (glazing half 0.75 listed, threshold half 0.75 unlisted F-17) | L-f5c5a1a9 | WINDOW_BASE_TILED |
| e053 west | WALL | AF | 0.650 | 0.650 | 0 (row #AF) | L-f5c5a1a9 | TILE_OWNS |
| **base in L-71e2e002** | | | | **3.500** | **0.000** | | over-count **0.000 lm** |

W09 on the range line L-e7dcdc69: BOUNDED 0 .. 6.331578 (= OP-019 only; its 1.5 m of W09 already off, T-315 r2).
Engine edge e042 (0.05 m east of B3, column 2FB4 / wall on the dining side) is outside the box: dining, kept.

**Reconciliation (units).** V2.9 runs of GF-RC99C2A: wall 20.546693 + column 7.624896 = 28.171589 lm (the engine net
is wall + column; windows and openings are off it). Less the 3.500 lm base faces above = 24.671589 = V3.0.38 net
(residual 0.000000). The named rows sum 3.500 = the base in the box (residual 0.000).

**Closure of the pantry's whole base (merged T-296 GF-07 base 7.000 lm of wall + column):** GF-RC06FED 1.900 (its
line L-af6fb2d3, NOT_APPLICABLE_WITH_EVIDENCE in V3.0.38; W10 range L-73ff85e3 NOT_APPLICABLE too) + GF-RC99C2A 3.500
(this walk) + no engine room 1.600 (counter cells, T-315 r2) = 7.000 (residual 0.000). No pantry base is skirted.

## 3. The T-431 +3.90 lm kept apart

T-427 / T-431 add +3.90 lm to the same line for the dining face GF-RFD4E1D. Its V2.9 base edges: wall 104 (GF-W01,
dining south wall) 0.275 + 2.425 = 2.70 and column 2FCF 0.05 + 1.10 + 0.05 = 1.20 = 3.90 lm; its two other edges are
zone lines (1.30 each). None of its edges lies inside the pantry box (0 of 7), and its wall is 104, not the pantry's
A6: the addition is dry dining base (R-T440-1 `additions_clear`: no flag). The +3.90 lm and this finding do not overlap.

## 4. Every villa (method) and the villa census

R-T440-1 (any villa): a skirting line keyed by an engine room carries a face's base only where the face lies in a
room that is not tiled full height; a base face in a full-height-tile room belongs to that room's wall-tile line, and
any length the skirting line still carries there is an over-count; a face whose room or class is not established is
UNRESOLVED (HELD, never 0, never moved); openings, zone lines and open edges carry no base; a later addition to the same
line is checked not to land on a tiled face. Census on the merged ledgers (T-262 xwalk x T-296 classes): the only Alsenan
engine room that holds a tiled room in part together with a dry one is GF-RC99C2A; every other wet room has its own
engine room and its own skirting line, already NOT_APPLICABLE_WITH_EVIDENCE (T-296). So the villa carries no tiled base
in any skirting line of V3.0.38.

## 5. Engine vs freelancer

No quantity moves: skirting family and L-71e2e002 (24.6716 lm, 28.5716 after T-431) unchanged. The freelancer's dry
skirting row for the GF open plan (T-106: gross perimeter, no door deduction, no pantry split) runs along the pantry walls;
the engine carries none there: RULE_DIFFERENCE by owner Q-37 A / Q-48 A (wall tile owns the base), as T-315 r2 recorded;
not compared line by line.

## 6. Lessons row (proposed, ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | a completeness join (T-435) flagged a 'possible over-count' of wet-pantry walls on a skirting line that had removed exactly those faces three days earlier (T-315 r2, 3.500 lm by name) | the join read the line's room boundary, not its deduction rows; an earlier merged split was not grepped | R-T440-1: an over-count is stated face by face against the line's own deduction rows and closed in units (V2.9 wall + column - named faces = candidate net) before it is raised; the T-315 split is the precedent | tests/t440_wet_base_owner | proposed |

Observation (no quantity): T-315 labels the 0.200 m north edge e043 as wall 159; the engine gives it COLUMN + WALL (the
south face of column 2FB4 is flush with 159). The base is tiled either way; length unchanged.

## 7. For the Checker (re-measure two faces, not from this file)

1. P7757.dxf: wall line 158 (layer 1) from the west face AE to the door gap (D120 33E): the visible part east of the
   NW column 2FAE = 0.759 m; and the west face AF from the W09 frame (3C6) to the OP-003 strip line = 0.650 m.
2. V3.0.38 (57cca61c) L-71e2e002: gross 56.006096, net 24.671589, the six `on_tiled_faces` rows (sum 3.500), and the
   V2.9 runs of GF-RC99C2A (wall 20.546693 + column 7.624896).
3. `python3 -I research/agents_t440/t440_alsenan.py --check` (committed rebuild) and, with the drawings, `--extract`.
