# T-441: wall-face lengths of the stair-room floor parts, for skirting (development villa; method every villa)

Worker 2 (lane A), 2026-11-01. Research only: `research/agents_t441/*`, `tests/t441_stair_room_skirting/*`; no engine,
rule, knowledge, method, registry or candidate file touched; no candidate or released quantity moves (lane I proposal
in s.7). ERS applied: s.2.1 element first, s.2.2 evidence, s.2.4 reconciliation in units, s.4 rule + test, s.7 lesson.
Rules: UP-SKIRT-001 1.4.0 (dry-room wall and column faces at floor level; not across door / passage openings;
doorless jambs by URBAN-SKIRTING-OPENING-METHOD), UP-CER-003, R-T246 (deductions by opening id), OWNER_RULE_STAIRS
(skirting along a flight = stair skirting, T-410), register rulings LIFT LANDING THRESHOLD and STAIR-ROOM FLOOR PART vs
LANDING BOUND, defect B12 (L-18: skirting along void / railing edges). No image, client name or drawing text copied.

## 0. What was read

| Source | Used for |
|---|---|
| Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55), decoded into `.work/private` only, read BY HANDLE on layers 1 / 2 / 5 / D / W / S-COL.BON / LEVEL | every face, opening gap, nosing / riser line, column, band |
| Released ARCH_TAKEOFF_V2.9 on the same DXF (read-only, this run) | the engine's own room polygons GF-R31F8AE / 2F-R4D1B62 (same frames as T-418), edge roles, opening ids OP-010 / OP-013 / OP-020 (GF), OP-001 / OP-002 / OP-007 (2F) |
| Candidate of record ARCH_TAKEOFF_V3.0.38, own run (research/agents_t167/v304_run.py + research/agents_t421/v3038_run.py on P7757.dxf + "ST7757 dxf.dxf" 9f9d1179) | the parent lines' states (summary.json `parents`) |
| Merged ledgers, cited not re-derived: T-418 (floor parts), T-421 (V3.0.38), T-410 r2 (stair side table and stations), T-413 (lift stations), T-393 / T-164 (railings RL-07 / RL-08), T-296 (skirting ledger), T-435 (derived-layer join), T-106 (freelancer skirting trace), T-250 (face walk) | see each row |

## 1. Physical element (ERS s.2.1)

A room skirting is a strip fixed to a vertical finished face (wall or column) at the FLOOR level of a floored space. In a
stair room it exists only along the faces that bound a floor part (T-418: GF hall +1.00, GF back lobby +0.30, 2F lobby
+9.70); along a flight the base is the stair skirting (B7-07 / B7-08, T-410), beside a void or a guard there is none, a
door or lift opening carries none, and a lift opening's jambs and band belong to the lift surround / threshold (B6-06 /
B6-07). One physical base, one owner: where the merged stair side table starts a stretch (its drawn station), the floor
part's face stops.

Station convention, proved on two flights: layer 5 draws the NOSING edges and layer 2 the RISER faces 0.050 behind them
in the UP direction (MS1-L rises north: DC 1.10 / DE 1.15; D1 rises south: 490 2.95 / 48A 2.90). T-410 stations are the
nosings; T-418's floor polygons stop at the nosing at D1 (2.95, 3.85) but at the RISER at the MS1-L foot (1.15). So the
0.050 of wall 298 between y 1.10 and 1.15 is in both; it stays with T-410 MS1-L.W1 (its station) and the hall's west
face stops at 1.10 (R-T441-2). No figure of either merged ledger changes.

## 2. Result: face tables (FACES_T441.csv; room-local metres, origin = the room's south-west inner corner)

**GF stair hall +1.00 (GF-ST-HALL, 4.8050 m2)**

| Side | Stretches (handles) | Deduction by id | Skirting lm | Status |
|---|---|---|---|---|
| south y 0 | wall 220 1.400 + wall 21F 0.100 | OP-010 1.000 (door to the open room, block D120 2C7) | 1.500 | DRAWING-CONFIRMED |
| east x 2.5 | wall 21C 2.000 (columns 2F90 / 2F93 flush) + wall 21B 0.050 | OP-020 0.900 (doorless, to the wet wash space GF-RD36087; wall ends 218 / 4AA, head 33C / 33D hidden) | 2.050 | DRAWING-CONFIRMED |
| west x 0 | wall 298 1.100 (y 0 .. 1.10) + 0.050 owned by T-410 MS1-L.W1 | - | 1.100 | DRAWING-CONFIRMED |
| D1 top / MS1-L foot | nosing 490 / riser DE, nosing DC | - | 0 | no face (flights, B7) |
| divider band (east face 1.900, west 0.100, end 0.200) | layer 5 4A4 / 157 / 155; rail band 151 / 47F; T-393 'solid to the cut', RL-07 / RL-08 | - | blank | **HELD** (guard upstand or wall face not established; B12) |
| divider zone y 0.45 .. 1.05 (east 0.600, west 0.600) | only hidden layer-2 outline 47C / 47E / 499 (the 1F band above); 2C8 / 2C9, diagonal 2F1D / 2F1E in the SW box | - | blank | **HELD** (T-418 reads SOLID; at the cut the band starts at 1.05) |
| OP-020 jamb returns 2 x 0.200 | column 2F93 north face, wall end 4AA | - | blank | **HELD** (URBAN-SKIRTING-OPENING-METHOD would add them PROVISIONAL; the reveal opens onto a full-height-tiled WET room, T-296 GF-11: tile or skirting owner not printed) |

Hall: **4.650 lm DRAWING-CONFIRMED** (gross face side 6.550 - openings 1.900); HELD, skirting blank: band faces 2.200
(cut outline) or 3.400 lm (T-418 outline) and the 0.400 jambs.

**GF back lobby +0.30 (GF-ST-LOBBY030, 1.3225 m2)**

| Side | Stretches | Deduction | Skirting lm | Status |
|---|---|---|---|---|
| east x 2.5 | wall 21B 1.150 (column 2F81 flush) | - | 1.150 | DRAWING-CONFIRMED |
| north y 5.0 | wall 26F / 2AC 0.1469 + wall 2AB 0.1031 | OP-013 0.900 (door to the north court; 3FD / 3FE, block D120 3FF on layer S-COL.BON) | 0.250 | DRAWING-CONFIRMED |
| south | D1 bottom nosing 481 | - | 0 | no face (flight) |
| west x 1.35 | nothing on layers 1 / 5 / S-COL.BON (hidden 49C / 2C6 / 49D only) | - | blank | **UNKNOWN** (T-418 strip GF-ST-CN unread; under-winder space at +0.30 open or closed not drawn; candidate 1.150 if the face stands on x 1.35) |

Lobby: **1.400 lm DRAWING-CONFIRMED**; HELD 0 .. 1.150 (extent beyond not established). The MS1-LD landing stretches
(T-410, +3.50) lie on the same wall lines in plan but 3.20 m higher: not the lobby's base (level test).

**2F stair lobby +9.70 (2F-ST-LOBBY, 2.5000 m2)**

| Side | Stretches | Deduction | Skirting lm | Status |
|---|---|---|---|---|
| south y 0 | wall 1283 2.000 | - | 2.000 | DRAWING-CONFIRMED |
| east x 4.5 | wall 1295 0.1016 + wall 1294 0.2484 | OP-007 0.900 (maid-room door, block d220 12C2) | 0.350 | DRAWING-CONFIRMED |
| north y 1.25 | wall 1289 0.400 + wall 128A 0.600 (column 2F72 flush) | OP-002 1.000 (lift ELV-01-2F, jambs 12AE / 12AF, T-413) | 1.000 | DRAWING-CONFIRMED |
| west x 2.5 | - | - | 0 | no face (continues into the arrival) |

Lobby: **3.350 lm DRAWING-CONFIRMED**, nothing held. The lift threshold band (12B3 front 1.000 on the wall line, 12B0
1.000 at y 1.45, jambs 12AE / 12AF 0.200 each) lies in the wall band outside the floor part: none of its edges is a
face (checked in code, R-T441-1; register LIFT LANDING THRESHOLD: B6-06 / B6-07).

**Beside the task, for the parent line: 2F arrival +9.70 (B7 marble Q-70 A; skirting B3-06 per T-410 s.3)**: south 0.4158
(1282) + 1.0842 (1283), OP-001 1.000 deducted; east column 2F72 0.500 + wall 129A 0.200 (y 1.25 .. 1.95); west wall
12B7 1.950; north edge: MS2-U top 1.150 + slab opening 1.350 (guard RL-07 G-2F), no face = **4.150 lm DRAWING-CONFIRMED**.

Totals: task parts **9.400 lm DRAWING-CONFIRMED** (GF 6.050, 2F 3.350); HELD on the GF, blank, never 0: band faces
2.200 / 3.400, jambs 0.400, lobby west face 1.150 if it stands on x 1.35; arrival 4.150 lm beside. All 24 face / opening stretches re-read by handle on the DXF
(EXTRACT_T441.json `handle_checks`: drawn cover = stretch within 0.002 m; every opening a gap in the layer-1 wall line).

## 3. Closure in units (ERS s.2.4) against the engine's wall + column run of each stair room

GF-R31F8AE (V2.9 runs: wall 9.8 + column 1.3 = 11.100 lm): hall 4.650 + lobby 1.400 + T-410 west face y 1.10 .. 5.00
2.800 (wall 0.40 + column 2FBD 0.60 + wall 0.75 + wall 1.05; window OP-022 not a face) + T-410 MS1-T north 1.150 + strip
GF-ST-CN north face 0.200 (unread, T-418) + T-410 D1 east 0.900 = **11.100, residual 0.000**.

2F-R4D1B62 (wall 15.4 + column 1.5 = 16.900 lm): lobby 3.350 + arrival 4.150 + faces beside the slab opening with no
floor at +9.70: north 1.500, west 3.400, east 4.500 (the MS2-U lift wall, whose flight skirting is T-410's below +9.70) =
**16.900, residual 0.000**.

## 4. Candidate binding (V3.0.38, own run) and findings

Parents in the candidate of record (summary.json `parents`): GF skirting L-47fa825d BLOCKED_RFI, net blank (runs
wall 9.8 / column 1.3); 2F skirting L-b8d4a7f0 BLOCKED_RFI, net blank (wall 15.4 / column 1.5): both 'measured wall run
shown, no finish assumed' (Q-S6-4). Own run reproduces V3_0_38_BOQ_LINES.json sha256 57cca61c (= board pin) and V3_0_37
733f2efb (= T-420 pin). The floor parts' own lines in V3.0.38: GF hall L-f53d4986 FIN.FLOOR.FINISH_HELD 4.805 m2, GF
lobby L-b4441a1b FIN.FLOOR.FINISH_HELD 1.3225 m2, 2F lobby L-9bd25c0c FIN.FLOOR.PORCELAIN 2.200 m2 (2.500 less the 0.300
B6-07 threshold floor part). Nothing in V3.0.38 carries a skirting figure for these floor parts (T-435 SILENT list), so
these lengths add information; they change no candidate line.

Findings for other owners (no quantity moved here):

1. **Lift opening classed as a passage.** V2.9 records OP-002 (2F) as kind PASSAGE (to 2F-R2BDCEE). Under
   URBAN-SKIRTING-OPENING-METHOD a passage gets PROVISIONAL jamb skirting: wiring the 2F lobby line from the engine's
   roles would put 0.400 lm of skirting on the lift jambs that the register gives to B6-06. Lane I must deduct OP-002 as
   a lift opening with no jambs (refused in code: `check_jambs`). V3.0.38 already counts it as ARCH.PASSAGE L-c91732d6
   (1 pcs PROVISIONAL, note LIFT_ENTRANCE_CANDIDATE): a lane I / openings item (a lift landing opening is not a passage
   piece; T-413 owns it as ELV-01-2F).
2. **T-418 divider zone y 0.45 .. 1.05.** At the cut the band starts at y 1.05 (layer 5 155); 0.45 .. 1.05 is only the
   hidden outline of the band above, so 0.200 x 0.600 = **0 .. 0.120 m2** of the hall may be floor that T-418 counted
   SOLID. Cause not settled here (the SW box carries a diagonal pair 2F1D / 2F1E and lines 2C8 / 2C9 that no ledger has
   read; on 1F and 2F the band is visible from 0.45). Checker / lane A item, with the band's role (RFI: guard upstand or
   wall, finish).
3. **T-250 face walk 2F-W00**: records 128A as 0.43 m; the drawn line runs x 2.5 .. 3.1 = 0.600 (T-413 left landing face
   0.600 agrees). The 2F lobby north face is 1.000 lm, not 0.83.
4. **Station convention**: T-418's MS1-L foot edge (riser, 1.15) and T-410's station (nosing, 1.10) differ by 0.050 m;
   both merged; resolved here by owner per base (s.1), proposed as R-T441-2 for every villa.

## 5. Engine vs freelancer (quantities only; T-106 merged trace)

| Space | Freelancer | Ours (confirmed) | Difference | Components | Verdict proposal |
|---|---|---|---|---|---|
| 2F corridor (= our 2F lobby + arrival) | 13.60 lm (gross perimeter, no deduction) | 7.500 lm | -6.100 lm (-44.85 %) | openings he does not deduct 2.900 (OP-001 1.000, OP-007 0.900, OP-002 1.000); arrival north edge with no face 2.500 (slab opening 1.350 + MS2-U top 1.150); residual 0.700 (his outline 13.60 vs our 12.90; his 7.70 m2 vs 7.375 m2, T-418's 2F corridor residual) | RULE_DIFFERENCE 2.900 (UP-CER-003 / UP-SKIRT-001) + RULE_DIFFERENCE 2.500 (no skirting on a guarded / open edge, R-T410-1, B12) + UNRESOLVED 0.700 |
| GF stair hall + back lobby | no row | 6.050 lm | +6.050 lm (engine only) | his list has no GF stair-hall skirting (his open-plan row runs round reception, dining and entrance only) | ENGINE_RIGHT on the existence of the faces (drawn walls at floor level beside T-418 parts); material HELD with the floor finish |

The percentage is not an accuracy figure: two of the three components are owner-rule differences.

## 6. What still blocks each parent (and who answers)

- GF L-47fa825d: the material of the hall / lobby skirting follows their floor finish, HELD in T-418 (porcelain floor or
  marble landing; no printed landing depth, no finish schedule: designer item). The divider band's role and finish
  (guard upstand or wall) and the OP-020 reveal owner: designer RFI. The lobby's west boundary under the winders: designer
  RFI (with T-418's GF-ST-CN strip). The flight-side faces (west 2.800, MS1-T north 1.150, D1 east 0.900) are T-410's
  stair skirting, which waits on ORR-007 (form) and the shaft windows' sills.
- 2F L-b8d4a7f0: nothing blocks the lobby's 3.350 lm (finish porcelain ASSUMED — OWNER-APPROVED, Q-70 A; UP-SKIRT-001
  applies to a dry room with a tiled floor). The arrival 4.150 lm is drawn; its skirting material beside a marble landing
  is not stated (HELD material, lm DRAWING-CONFIRMED). The remaining 9.400 lm stand beside the slab opening at +9.70: no
  floor, no skirting by rule (owner reason, not a hold).
- ERS s.2.7 is not met for an owner question: the open items are designer facts (band role, reveal finish, under-winder
  enclosure, finish schedule) and an existing owner rule request (ORR-007). Proposed rfi/B rows for the Lead (drafts,
  nothing sent): (a) GF stair divider between MS1-L and D1: construction (solid upstand / wall / balustrade on a curb),
  its south end on the GF (y 0.45 or 1.05) and its finish; (b) the reveal of the doorless opening from the GF stair hall
  to the wash space: tile return or skirting; (c) the space under the MS1-T winders beside the +0.30 lobby: open or
  enclosed.

## 7. Lane I proposal (no candidate change in this task)

Split each parent so the floored parts carry their own lines, the parent keeping only the unresolved remainder:

| New child line | lm | Evidence status | Item / material |
|---|---|---|---|
| 2F stair lobby skirting (from L-b8d4a7f0) | 3.350 | DRAWING-CONFIRMED (after Gate A) | porcelain skirting, finish ASSUMED — OWNER-APPROVED Q-70 A |
| 2F arrival skirting (from L-b8d4a7f0) | 4.150 | DRAWING-CONFIRMED (lm) | material HELD (beside the Q-70 A marble landing) |
| GF stair hall +1.00 skirting (from L-47fa825d) | 4.650 | DRAWING-CONFIRMED (lm) | material HELD with the T-418 hall finish |
| GF back lobby +0.30 skirting (from L-47fa825d) | 1.400 | DRAWING-CONFIRMED (lm) | material HELD with the T-418 lobby finish |
| GF divider band faces | blank (2.200 .. 3.400 in the note) | HELD | role / finish (RFI a) |
| GF OP-020 reveal jambs | blank (0.400 in the note) | HELD | owner skirting or wall tile (RFI b) |
| GF lobby west face | blank (1.150 if on x 1.35) | UNKNOWN | RFI c |

Deductions by id (OP-010, OP-020, OP-013; OP-007, OP-002, OP-001); OP-002 as a LIFT opening (no jambs; finding 1). The
flight-side faces of both rooms are bound to the T-410 B7-07 / B7-08 stretches, never to a room line; the faces beside
the 2F slab opening are listed NOT_APPLICABLE_WITH_EVIDENCE (no floor). Each child is bound to its T-421 floor line
(V3.0.38 FIN.FLOOR / B3-01 parts) so a finish decision moves floor and skirting together.

## 8. Rule, test, lesson

- **R-T441-1 .. 4** (proposed, research, any villa; module docstring): faces per floor part, stretch by stretch,
  covering each side once; one base one owner at the merged stair station (level-aware); deductions by opening id; lift
  opening never skirted and its jambs never given passage-jamb skirting; HELD / UNKNOWN blank with cause, never 0; unit
  slips refused.
- Tests `tests/t441_stair_room_skirting` (15 pass): hand villa K441 (hall 5.840 lm, lobby 2.900 lm, jambs 0.500 apart,
  guard held blank); adverse: **lift threshold band counted as wall face** refused, lift-opening jamb skirted refused,
  face shared with a flight stretch refused (a landing above at another level is not an overlap), held as 0 / without
  cause refused, mm as m, gap, overlap and short cover refused, opening without id refused, door jamb skirted refused,
  stair-side stretch without its owner refused, face without a handle refused, mirror invariance; Alsenan pins (rebuild
  from the committed extract, hand totals, both closures 0.000, parents BLOCKED_RFI, held cells blank).
- Lessons-register row proposed (ERS s.7):

| 2026-11-01 | the stair rooms' skirting lines were BLOCKED whole, so the drawn faces of their floored parts (9.400 lm) had no length anywhere, and two merged ledgers stopped the MS1-L foot at different lines (riser 1.15 vs nosing 1.10) | a blocked parent line was read as 'nothing measurable'; floor partition and stair side table were never joined face by face | measure each floor part's faces stretch by stretch against the merged stair stations (one base one owner, level-aware), deduct openings by id, treat a lift opening as a lift (no jambs), hold only the faces whose role is open | tests/t441_stair_room_skirting | T-441 |

## 9. Self-gate and what is missing

self-gate: a (research + tests + CODEMAP only; no engine / rule / candidate file) c (non-Alsenan fixture K441, adverse
cases incl. the lift band) d (reproducible: `--extract <P7757.dxf> <V3.0.38 run dir>`, `--check` without private input)
f (no new item code, nothing valued, nothing wired) h (handles and room-local lengths only; no world coordinate, no
drawing text, no client data) PASS.
Missing: the band's role and its south end; the OP-020 reveal owner; the under-winder enclosure; the skirting materials
(follow the HELD floor finishes and the arrival marble); ORR-007 for the flight-side faces.

Checker re-measure suggestion: the 2F lobby (3.350 lm: 1283 2.000, 1295 0.1016, 1294 0.2484, 1289 0.400, 128A 0.600;
OP-007 0.900 and OP-002 1.000 deducted), or the GF hall (4.650: 220 1.400, 21F 0.100, 21C 2.000, 21B 0.050, 298 to the
MS1-L nosing DC 1.100).
