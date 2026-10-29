# T-329: WET-ROOM PLASTER BACKING under wall tile and the band ABOVE the tile, face by face, tied to the 17 blank wet-room FIN.PLASTER lines (development villa; every villa by R-T329-1 .. 4)

Worker 2 (lane A), claim 2026-10-29 04:41 UTC, run unknown. Integration dependency of the PLASTER line (SCOREBOARD
CLOSABLE rank 3: "17 wet-room plaster lines blank"). Research only: no engine module, rule or knowledge file, candidate
line, released line or V2.9 cell changed; released default stays V2.9 + route G; nothing released, nothing VERIFIED
here. ERS applied: s.2.1 (physical element first), s.2.2 (evidence hierarchy; owner manual and drawing-derived methods
side by side), s.2.4 (reconcile in m2), s.2.7 (no owner question: the answered rules resolve it), s.3 (one face, one
owner; installed vs procurement), s.4 (rule + tests, normal and adverse), s.7 (lesson row, section 8).

## 1. Inputs (merged; no drawing re-read, no private file needed)

- T-312 MERGED 8943b5ed: FACE_LEDGER / OPENINGS / ROOM_CLOSURE / LINE_SUMMARY / RECONCILIATION_T312.csv (every wet-room
  and pantry face once, 115 tiled + 2 open sides; the Checker re-measured every tile face in T-315 r1, own 340.2484 m2).
- The candidate of record's FIN.PLASTER lines: research/agents_t311/CANDIDATE_V3019_T311.json (V3.0.19 json `b35475bf`,
  3,705 lines; line ids are version-independent hashes, equal on V3.0.20 `097a80b6`, T-313 s.3a).
- Runner `t329_alsenan.py --write | --check` (byte-identical rebuild); rules `t329_backing_rules.py`; tests
  `tests/t329_wet_backing` (Python 3.11.18).

## 2. The physical element (the engineering question answered from the rules, not from a default)

What is behind the tile? **A cement-sand backing coat, 20 mm, 1:4, then the tile adhesive, then the tile.**

| Evidence (ERS s.2.2 rank) | What it says | Effect |
|---|---|---|
| UP-FIN-PAINT-001 (owner rule, knowledge 1.8.0), logic `substrate` | "the cementitious substrate / plaster behind porcelain is its own line" | the coat EXISTS on every tiled face and is its own line: not inside the tile line, never painted |
| Owner answer Q-45 B (2026-10-19 21:40) | "wall mortar behind wall tiles 0.02 m, mix 1:4" (practice value accepted, PROVISIONAL); adhesive 20 kg / 5 m2 its own line | the layer is a 20 mm cement-sand coat; engine/source/finish_materials_table.py WET_WALL bed 0.02 m reproduces it |
| Owner answer Q-43 + Q-48 A | plaster and paint count to 3.65 (GF) / 3.35 (1F, 2F); wet-wall tile to the underside of the 0.15 decor ceiling = the same 3.65 / 3.35 | owner method: plaster top = tile top |
| Q-52 C MODIFIED (owner directive 2026-10-20) + URBAN-PLASTER-TO-MASONRY-TERMINATION@v1 (drawing method) | plaster and paint heights per room, apart; "plaster may run above the false ceiling while paint stops at it, depending on the specification" | drawing method: a band above the tile up to the soffit, HELD until a specification says so |
| URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1 | spatter dash (m2) and reveals are separate items | neither is in this line |
| Practice reference (Drive folder "حساب كميات جلال", the comprehensive grey-structure and finishes takeoff PDF; another villa, read only) | its summary sets paint = plaster faces - wall-tile area, i.e. plaster counted behind the tiles | corroborates (rank 6, not a source of any figure) |

Conflicts named, not chosen by preference: (a) T-211 s.5.4 / T-292 held the backing as "plaster under tile is not an
owner rule"; that reading did not consult UP-FIN-PAINT-001 `substrate` or the Q-45 B wall-mortar value, which together
answer it. (b) ARCH_QUANTITY_TRUTH_V1 `plaster_paint()` gives a full wet-tiled face "neither plaster nor paint
(spatter / tile preparation only)": an engine convention with no owner source; the owner rule governs. (c) The
freelancer prices no plaster on wet walls; his wet-wall row is a spatter-dash coat (طرطشة) of the same area, a
different, separate layer.

So: **status ASSUMED — OWNER-APPROVED** (UP-FIN-PAINT-001 + Q-45 B; the 20 mm / 1:4 values PROVISIONAL), faces
DRAWING-CONFIRMED through T-250 / T-312. No owner question: ERS s.2.7 is not met (the answered rules resolve it).

Installed vs procurement: the line is the installed m2 of the coat. Its mortar (m2 x 0.02 = 6.806 m3 on the 12
determinate rooms) is the procurement of the SAME layer, already the WET_WALL row of FINISH_MATERIALS_TABLE_V1 (T-086):
never priced twice.

## 3. Face by face (BACKING_FACE_LEDGER_T329.csv, ROOM_BACKING_T329.csv)

- Scope (R-T329-1): a backing face exactly where T-312 has a TILED face: 115 faces (wet rooms every face, the open
  pantry its three host walls + column + two perimeter pieces); the 2 open sides (pantry 4.490 m, wash lobby 1.245 m)
  carry none. Per room the faces + open sides close to the walked contour, residual 0.0000 m in all 18 rooms.
- Height (R-T329-2): backing top = the face's tile top (same record: G1 Q-43 / Q-48 A, GF 3.65, 1F / 2F 3.35).
- Openings (R-T329-3): the tile ledger's openings, same ids, same band parts (35 rows, each once per room side; doors
  w x 2.20 Q-55 C, windows w x (head - sill), W18 1.080 m2); reveals stay with T-313 / T-326.
- Closure (R-T329-4): **backing - tile = 0.0000 m2 in every determinate room**, face by face.
- The GF-16 walk-correction piece (-0.524 m, T-128 r3 verified outline) is carried as the named correction it is in
  T-312 (-1.9126 m2), so the room keeps 25.5912.

| Room | Faces | Backing, owner method (m2) | Band above tile, owner | Band, drawing-derived (HELD) | Status / held item |
|---|---|---|---|---|---|
| GF-12 / 13 / 14 / 16 | 5 / 8 / 8 / 6 | 25.3011 / 22.6165 / 26.6544 / 25.5912 | 0 | 0 .. 1.1120 / 1.0214 / 1.2399 / 1.1437 | ASSUMED — OWNER-APPROVED |
| 1F-02 / 03 / 07 / 08 / 09 / 12 | 6 / 4 / 11 / 5 / 5 / 5 | 27.9101 / 27.9100 / 52.5290 / 19.6691 / 23.2201 / 26.3051 | 0 | 0 .. 1.35 / 1.35 / 2.5410 / 0.9811 / 1.1399 / 1.3049 | ASSUMED — OWNER-APPROVED |
| 2F-02 | 4 | 30.2550 | 0 | 0 .. 1.4550 | ASSUMED — OWNER-APPROVED |
| GF-07 pantry (host walls) | 6 | 32.3422 | 0 | 0 .. 1.5736 | ASSUMED — OWNER-APPROVED |
| GF-02 / 03 / 05 / 06 (annex) | 29 | HELD | HELD | 0 .. 5.2196 | HELD: G2 annex height (Q-54 B, D-39), as their tile |
| GF-10 / 11 | 13 | HELD | HELD | 0 .. 1.6649 | HELD: room level not drawn (T-088), as their tile |

**Owner method: 340.3038 m2 on 12 rooms (307.9616 in the 11 wet-room lines + 32.3422 pantry), 6 rooms HELD (never 0);
band above the tile 0.0000 m2.** Hand check (1F-12): 8.70 x 3.35 = 29.145 - D-1F-10 0.80 x 2.20 = 1.760 - W18
0.50 x (3.00 - 0.84) = 1.080 -> 26.305 m2 (ledger 26.3051).

**Owner method vs drawing-derived, the difference named:** the backing is the tile face in both methods (drawing-derived
HELD on every face, as the tile: roof datum DCR-6, sunken panels, build-up b). The difference is the band ABOVE the tile:
owner method 0 (plaster counted to 3.65 / 3.35 = the tile top, Q-43); drawing-derived: plaster to the slab soffit, tile
to the underside of the decor ceiling, so the band is the 0.15 m decor zone x face length, independent of the build-up
b (both tops move with it; T-292's 4.34 plaster top is the b = 0 case of the same chain): **0 .. 23.0970 m2 over the 18
rooms (0 .. 16.2125 on the 12 determinate rooms), HELD** because no specification prints whether plaster runs above
the decor ceiling (Q-52) and the beam faces on the wall line inside that band are not split. No window head reaches a
tile top on this villa (max head 3.00 < 3.15 / 3.35 / 3.65), so the band carries no opening here (the rule deducts it
on the fixture). Paint never goes on the band (it is above the finished ceiling): the 17 'paint above wall tile' lines
stay NOT_APPLICABLE_WITH_EVIDENCE.

## 4. Line map (PLASTER_LINE_MAP_T329.csv): every blank wet-room FIN.PLASTER line

| Lines | Candidate | Proposal |
|---|---|---|
| 11 wet-room `<engine room>:plaster` lines (GF-12 / 13 / 14 / 16, 1F-02 / 03 / 07 / 08 / 09 / 12, 2F-02) | BLOCKED_RFI blank (WALL_FINISH_HEIGHT_NOT_ESTABLISHED) | **FILL** with the room's backing = its T-312 tile figure, 307.9616 m2 in all |
| 6 wet-room lines GF-02 / 03 / 05 / 06, GF-10 / 11 | BLOCKED_RFI blank | **HELD by name** with the tile's item (G2 / Q-54 B; T-088) |
| pantry `HL:WALL_FINISH:GF_07:PLASTER` (L-721a0f1441436193978c) | BLOCKED_RFI blank ("whether plaster is laid under that tile is not an owner rule yet") | **FILL 32.3422** (the hold reason is answered by UP-FIN-PAINT-001 + Q-45 B) |
| pantry `GF-RC06FED:plaster` (L-6470c6f20f86e542a5ce) | NOT_APPLICABLE_WITH_EVIDENCE | kept: room record superseded by the room-face line (T-211 SUPERSEDE), booked once |

Each of the 17 wet-room lines is mapped exactly once (19 rows with the pantry's two). The dining room's dry line
(GF_08, L-8cecb1d010d5aafbf25d) carries no pantry face (T-292 binds none of the 6 pantry faces to it); booking the pantry
backing or band there as well is refused (test). Effect on the candidate's FIN.PLASTER totals if lane I applies it:
+340.3038 m2 ASSUMED — OWNER-APPROVED (12 lines), 6 lines stay HELD; no other line moves.

## 5. Engine vs freelancer (RECONCILIATION_T329.csv)

The freelancer has no plaster row on wet walls; his wet-wall area (boundary lm x 3.00 m, no deduction, 433.83 m2 in 17
rows) is his spatter-dash and wall-tile quantity. Compared by AREA on the 11 rooms both have established:
**backing 307.9616 vs his 295.44 m2, +12.5216 m2 (+4.24 %)** = length -2.652, height +43.193 (owner 3.65 / 3.35 vs his
flat 3.00), doors -23.100, windows -4.920, residual 0.0002 (4-dp rounding) - the T-312 tile reconciliation, because the
coat covers exactly the tiled faces. Pantry 32.3422 vs none (SCOPE). The 6 held rooms (his 138.39 m2) are not compared.
Verdict proposals: element = RULE_DIFFERENCE (he prices no backing coat on wet walls; UP-FIN-PAINT-001 makes it its own
line); height RULE_DIFFERENCE (Q-43 / Q-48 A vs 3.00 printed nowhere); openings ENGINE_RIGHT (the coat stops at the
hole; he deducts none); pantry scope ENGINE_RIGHT (UP-PANTRY-003 host walls). His spatter-dash row is a separate layer
(URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1): whether the candidate carries a spatter-dash line on wet walls was not
searched here (named for the Lead, not in this line).

## 6. For the lane I package and for the Checker

- Consumer shape: PLASTER_LINE_MAP_T329.csv (line id, room, proposal, m2, basis); per face BACKING_FACE_LEDGER_T329.csv
  (face, tile scope, openings, tile top, owner plaster top, backing, band, closure, status, drawing columns, plaster and
  tile line ids, mortar m3 as information).
- Re-measure (Gate A): (1) one wet room by hand, e.g. 1F-12 above (26.305) or GF-13 = 6.81 x 3.65 - D-GF-12 1.760 - W06
  0.480 = 22.6165; (2) the evidence chain: knowledge 1.8.0 UP-FIN-PAINT-001 `logic.substrate`, OWNER_QUESTIONS_ANSWERED
  Q-45 answer B (wall mortar 0.02 m 1:4), Q-43 (plaster height 3.65 / 3.35); (3) the 17 wet-room line ids against the
  V3.0.19 extract (element `<engine room>:plaster`, BLOCKED_RFI) and the pantry HL line; (4) closure 0.0000 per room.

## 7. Rules and tests

- R-T329-1 .. 4 (t329_backing_rules.py, any villa): scope = the tile ledger's TILED faces (open side / dry face / missing
  backing refused); backing top = tile top, plaster top a separate record per method, band = length x max(0, plaster top
  - tile top) less window parts in it (universal height / mm refused, missing -> HELD never 0); openings = the tile
  ledger's ids and parts (differing ids, twice, reveal inside refused); binding to the wet room's own FIN.PLASTER line,
  band never also in a dry line, never in a paint line; closure backing - tile = 0.
- tests/t329_wet_backing: villa B hand fixture (not Alsenan): bath 2.00 x 2.50, tile 2.40 under a 3.00 soffit, door
  0.80 x 2.10, window 0.60 straddling the tile top: backing 19.74 (= tile, closure 0), band 5.22; owner-method band 0;
  window above the tile off the band only; adverse: open side, dry face, missing backing, band in wet + dry lines,
  backing in paint, mm, universal height, openings differing / twice, reveal inside, held as 0, mirror order. Alsenan
  pins: byte-identical rebuild, 115 + 2 faces, 18 rooms close, 12 / 6 rooms, 19 lines once (12 FILL = the T-312 figures,
  6 HELD), named totals, the 1F-12 hand check, pantry band in the dining line refused, no coordinates.

## 8. Lessons-register proposal (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-29 | 17 wet-room plaster lines and the pantry plaster line sat blank / HELD as "plaster under tile is not an owner rule" for eight days, while UP-FIN-PAINT-001 (`substrate`: own line) and Q-45 B (wall mortar 0.02 m 1:4 behind wall tiles) already answer it | the owner rule's logic fields and the answered material question were not searched by physical element (the layer), only by trade name 'plaster'; an engine convention (ARCH_QUANTITY_TRUTH_V1 'neither plaster nor paint') sat beside them unflagged | the coat behind wall tile is its own line on exactly the tiled faces, its top = the tile top; the band between the tile top and the plaster top is the wet room's own plaster line (owner method 0 when plaster and tile share the height; drawing method bounded by the decor zone, HELD on the specification); search answered rules by the physical layer before holding (every villa) | tests/t329_wet_backing (fixture 19.74 / 5.22; adverse: open side, band in wet + dry line, backing in paint, mm, held as 0) | PROPOSED |

Not done here: the spatter-dash layer on wet walls (separate item; carrier not searched), the reveal surfaces of wet-room
openings (T-313 / T-326), the 6 HELD rooms (G2, T-088), the band's specification (Q-52; stays HELD).
Files: `t329_backing_rules.py`, `t329_alsenan.py`, BACKING_FACE_LEDGER_T329.csv, ROOM_BACKING_T329.csv,
PLASTER_LINE_MAP_T329.csv, RECONCILIATION_T329.csv, summary.json; tests `tests/t329_wet_backing`.
