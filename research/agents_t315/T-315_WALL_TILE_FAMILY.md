# T-315: INTEGRATION PACKAGE ARCH_TAKEOFF_V3.0.21, the WALL TILE family (FIN.WALL.TILE) face by face from the merged T-312 face ledger (development villa; every villa by R-WALL-TILE-FAMILY-1)

Worker 3 (lane I), claim 2026-10-29 01:01 UTC, run unknown. Gate B integration package: `integrates: T-312`. Base =
the candidate of record ARCH_TAKEOFF_V3.0.20 (T-244 Gate B PASS, MERGED 59dbfd0e). Released default stays V2.9 +
route G; nothing here is released, nothing is VERIFIED by this task. ERS 2026-10-22 applied: s.2.1 (the physical
element first), s.2.2 (owner manual method beside the drawing-derived method on every line), s.2.4 (reconcile in m2
to named causes), s.3 (one face, one owner trade; a rule's scope before its arithmetic), s.4 (rule + normal and
adverse tests), s.7 (lesson row, section 9).

## 1. The physical element and what the candidate carried

Wall tile = porcelain / ceramic on a WALL FACE (one drawn wall seen from one room) from the finished floor to the tile
top, less the part of each hole inside that band (UP-CER-005, Q-73). Scope by the owner rules: a wet room tiles every
face full height (UP-FIN-WALL-001; tile top = underside of the 0.15 decor ceiling, Q-48 A: GF 3.65, 1F / 2F 3.35);
an open pantry tiles only the host walls of its installation, each whole, the open edge nothing (UP-PANTRY-001 ..
004). A tiled face carries no paint (UP-FIN-PAINT-001); the substrate behind the tile is its own line
(UP-FIN-PAINT-001 logic `substrate`), never inside the tile figure.

V3.0.20 carried 17 FIN.WALL.TILE lines, ALL BLOCKED_RFI with no figure (WALL_FINISH_HEIGHT_NOT_ESTABLISHED), and no
tile line in the pantry engine room GF-RC06FED (T-312 NO_LINE, 6 faces, 32.3422 m2).

## 2. What V3.0.21 does (engine/source/arch_v3021.py, piece WALL_TILE_FAMILY)

- FILL (11 lines, same line ids): each line takes the sum of its faces, each face = length x its own height (with
  the height's source) - each opening's part inside the band, once per room side; the face lengths + open edges +
  not-tiled faces close to the room contour (0.0000 m on every room); state PROVISIONAL, evidence ASSUMED -
  OWNER-APPROVED with the owner source on the line (Q-48 A height, Q-55 C door heads; OWNER_RECONCILIATION G1).
- HELD (6 lines): asserted blank (BLOCKED_RFI, no figure, no range) and the record supplies none; the line is not
  changed (byte-identical), its reason is in the ledger: annex GF-02 / GF-03 / GF-05 / GF-06 (owner height not
  established: G2, Q-54 B HOLD, D-39), GF-10 / GF-11 (room level not drawn, T-088). Never 0.
- ADD (1 line): the open pantry (GF-07, engine room GF-RC06FED) gets ONE new FIN.WALL.TILE line, same item / trade /
  subtrade / documents as the family, element `GF-RC06FED#WALL_TILE:GF-07`, 32.3422 m2 on 6 faces (refused if the room
  already had a tile line).
- The whole family at once: every candidate FIN.WALL.TILE line is named by exactly one record (a line left out is
  refused). Cross-trade per face (section 5). The merged default guard (arch_v307) runs again over the result and may
  not flag a filled or added line. Every other line is byte-identical to V3.0.20 (asserted on every run).

## 3. Run and identity (own run, Python 3.11.18)

Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and 'ST7757 dxf.dxf' (`9f9d1179`),
decoded into the private folder only: research/agents_t167/v304_run.py, then research/agents_t315/v3021_run.py
(tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.21 --v3021-inputs`), one process, every earlier version
reproduced on the way: **V3_0_19 json `b35475bf` / csv `ef63b73b` and V3_0_20 json `097a80b6` / csv `ca90351b` = the
candidates of record** (T-255 / T-244 Gate B). **V3_0_21_BOQ_LINES json `d5327df4` / csv `e9a9c34d`**, 3,706 lines =
3,705 + 1. research/agents_t315/v3021_direct.py runs the V3.0.21 step alone on a finished V3.0.20 run (same module
functions, same files, json `d5327df4`).

Identity (V3_0_21_RUN.json): replaced 11, added 1, outside rows 3,694 = identical to V3.0.20 (asserted, sha
`f4e0bb49`); DIFF vs V3.0.20: SAME 3,694, CHANGED 11, ADDED 1; family: 18 lines, 12 valued 340.3038 m2, 6 blank.
Totals moved by code: ONLY FIN.WALL.TILE|m2 (17 lines, 17 blocked, 0.0 m2 -> 18 lines, 6 blocked, 340.3038 m2).
Default guard re-run over the 3,706 lines (arch_v307 inputs of V3.0.7, unchanged): no finding on a filled or added
line, no guard change to any line (held_live_new none, silent omissions none; the recorded-only findings are the
V3.0.7 set).

## 4. Line by line (before V3.0.20 -> after V3.0.21; released V2.9; freelancer)

Owner manual method = face length x owner height (Q-48 A) - each opening's part inside the band (doors 2.20 head Q-55
C, windows printed heads T-201); drawing-derived method beside on every line (`drawing_derived_method`: the T-292
dwg status per face: HELD on the roof datum DCR-6 / sunken panels / floor build-up b, never used to fill a blank).
V2.9 carries no figure on any of these lines (BLOCKED_RFI; GF-14 and the pantry NOT_IN_RELEASED).

| Room | Line | Action | Faces | Run m | H m | Openings | V3.0.20 | V3.0.21 m2 | Status | Freelancer m2 | Engine - freelancer |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GF-12 | L-c34694477f67800ae2e3 | FILL | 5 | 7.414 | 3.65 | 1 | blank | 25.3011 | OA | 22.20 | +3.1011 (+13.97 %) |
| GF-13 | L-a3cb2c8a9b6080769ebc | FILL | 8 | 6.810 | 3.65 | 2 | blank | 22.6165 | OA | 20.10 | +2.5165 (+12.52 %) |
| GF-14 | L-fa408571a8adcfaf1a1f | FILL | 8 | 8.267 (+1.245 open) | 3.65 | 2 | blank | 26.6544 | OA | 28.50 | -1.8456 (-6.48 %) |
| GF-16 | L-ca4e74c59364f665b102 | FILL | 6 | 7.625 | 3.65 | 2 | blank | 25.5912 | OA | 22.80 | +2.7912 (+12.24 %) |
| 1F-02 | L-a34d09209fb5aad3eb63 | FILL | 6 | 9.000 | 3.35 | 2 | blank | 27.9101 | OA | 27.00 | +0.9101 (+3.37 %) |
| 1F-03 | L-88ed2535c1975adb702e | FILL | 4 | 9.000 | 3.35 | 2 | blank | 27.9100 | OA | 26.70 | +1.2100 (+4.53 %) |
| 1F-07 | L-b2077eee5a71a975bd74 | FILL | 11 | 16.940 | 3.35 | 3 | blank | 52.5290 | OA | 50.55 | +1.9790 (+3.91 %) |
| 1F-08 | L-1090bb5c8226afec2235 | FILL | 5 | 6.540 | 3.35 | 2 | blank | 19.6691 | OA | 19.44 | +0.2291 (+1.18 %) |
| 1F-09 | L-086e72207311265f81ab | FILL | 5 | 7.600 | 3.35 | 2 | blank | 23.2201 | OA | 22.80 | +0.4201 (+1.84 %) |
| 1F-12 | L-82cd58d4a16fb94ddfc6 | FILL | 5 | 8.700 | 3.35 | 2 | blank | 26.3051 | OA | 26.10 | +0.2051 (+0.79 %) |
| 2F-02 | L-065bafe1b98e3a43881c | FILL | 4 | 9.700 | 3.35 | 2 | blank | 30.2550 | OA | 29.25 | +1.0050 (+3.44 %) |
| GF-07 pantry | L-f5c5a1a9c9ee2b644cb5 (NEW) | ADD | 6 | 10.491 (+4.49 open) | 3.65 | 3 | no line | 32.3422 | OA | no row | SCOPE (he has none) |
| GF-02 / GF-03 / GF-05 / GF-06 | L-d0858b30... / L-96d9839b... / L-88c11c5d... / L-c330b8dc... | KEEP HELD | - | - | - | - | blank | blank (HELD: annex height G2 / Q-54 B / D-39) | HELD | 21.60 / 22.50 / 16.74 / 43.05 | not compared |
| GF-10 / GF-11 | L-1341e041... / L-de4088e7... | KEEP HELD | - | - | - | - | blank | blank (HELD: room level not drawn, T-088) | HELD | 18.60 / 15.90 | not compared |

OA = ASSUMED - OWNER-APPROVED (Q-48 A height, Q-55 C door heads, OWNER_RECONCILIATION_2026-10-20 G1); no line is
VERIFIED (the Checker's T-312 re-measure of 1F-12 and the pantry verified length / openings, the height stays OA).

**Wall tile, engine vs freelancer:** on the 11 rooms both measure, **307.9616 vs 295.44 m2, +12.52 m2 (+4.24 %)**
(was: no engine figure, every line blank); causes in m2 (T-312 RECONCILIATION, re-added here): length -2.652 (drawn
faces vs his rounded lm; the GF-14 wash lobby open side -3.699), height +43.193 (owner 3.65 / 3.35 vs his flat 3.00),
doors -23.100 (13 x 2.20 head), windows -4.920, residual 0.0002 (4-dp face rounding). Pantry +32.3422 m2 where he has
no row. Determinate engine total 340.3038 m2 on 12 rooms; 6 rooms HELD (his 138.39 m2), never 0. Verdict proposals
(T-312, Checker 21:20 confirmed): height RULE_DIFFERENCE, openings ENGINE_RIGHT, lobby open side ENGINE_RIGHT, pantry
scope ENGINE_RIGHT.

Hand re-derivation in this run (not the ledger's arithmetic): 1F-12 8.700 x 3.35 = 29.145 - 0.80 x 2.20 - 0.50 x
(3.00 - 0.84) = 26.305; 2F-02 9.700 x 3.35 = 32.495 - 1.76 - 0.48 = 30.255; GF-12 7.414 x 3.65 = 27.0611 - 1.76 =
25.3011; 1F-07 16.940 x 3.35 = 56.749 - 3.74 - 0.48 = 52.529; GF-16 7.625 x 3.65 = 27.83125 - 1.76 - 0.48 = 25.5913;
pantry 10.491 x 3.65 = 38.29215 - 2.20 (D-GF-06 1.00 x 2.20) - 1.50 (W10) - 2.25 (W09) = 32.3422. All agree with the
lines to 1e-4.

## 5. Cross-trade (V3_0_21_CROSS_TRADE.csv, 79 rows: 73 faces + 6 held rooms)

| Check | Result |
|---|---|
| A tiled face in two tile lines | none (each of the 73 faces in exactly one line; asserted) |
| Paint on a tiled face | none: the 12 tiled rooms' and the 6 held rooms' paint lines carry NO figure (17 NOT_APPLICABLE_WITH_EVIDENCE 'paint above wall tile' + the pantry HL line BLOCKED_RFI); a figure would be refused |
| Skirting on a full-height tiled face | none: the 17 wet rooms' skirting lines are NOT_APPLICABLE; a figure would be refused |
| Plaster backing behind the tile | the 17 wet rooms' FIN.PLASTER lines are BLOCKED_RFI (UP-CER-009 height), the pantry HL plaster line BLOCKED_RFI; UP-FIN-PAINT-001 (owner rule, logic 'substrate') makes the backing its own line; no merged ledger measures it: HELD by name (WAITING WALL_TILE_BACKING) |
| Pantry base / engine-room split (r2, section 11) | r1 called GF-RC06FED "shared" from its OPEN_PLAN note and left its skirting unattributed: REJECTED at Gate B (F-T315-C1 / C2). r2: the pantry lies in GF-RC06FED wholly and in GF-RC99C2A in part (merged T-262); every pantry wall base is carried by the wall tile once (T-296), by the lines' own source entities |

## 6. Missing, held, downstream

- HELD, blank, never 0: 6 tile lines (annex G2 / Q-54 B / D-39; GF-10 / GF-11 level T-088).
- Backing plaster / render behind the tile: own line by UP-FIN-PAINT-001, not measured by a merged ledger (73 faces,
  340.30 m2 of tile face once a ledger binds them): proposed Lead row (lane A ledger, then lane I).
- The pantry HL paint line (L-c3f7e68ce91a436802e2, BLOCKED_RFI) is now physically NOT APPLICABLE (every pantry wall
  tiled full height): it carries no figure, so no double count; its state is left byte-identical here (not this
  package's line), named for the Lead.
- The pantry base: settled in r2 (section 11): 1.9 + 1.0 lm NOT_APPLICABLE, 3.5 + 1.5 lm carried off the open-plan
  lines, the open-plan rest kept; 1.6 lm of the pantry base lies on no engine room boundary (no line carries it).
- Tile procurement (cartons, adhesive, grout, waste): HELD, no product / waste rule applied.
- 1F-12 per-face split (T-250 walk 2.125 / 2.250 / 2.145 / 2.100 / 0.080 vs the Checker's rectangle): the room total
  8.700 m agrees 0.000 and one height carries every face, so the line figure does not depend on it (named on the
  record).

## 7. Regression and validation

- tests/t315_wall_tile_family: 41 passed (villa W315 hand fixture, not Alsenan: bath 26.04 FILL, held bath BLANK,
  open pantry 16.75 ADD with an open edge and a not-tiled wall; adverse: held as 0, paint under tile in a tiled bath
  and in a held wet room, skirting on a full-height tiled face, face in two lines, opening twice, mm height, height
  without source, missing height, face net wrong, value not the faces' sum, room not closing, open edge tiled, ADD
  into a room with a tile line, a candidate tile line not named, stale fill on a line with a figure, VERIFIED without
  run, OA without source, declared drift, second tile line in one room; shared engine room not attributed vs not
  shared refused; face order / ids invariance; Alsenan input pins incl. an edited ledger stops the build; master
  1.16.0 equals its builder and checks clean).
- tests/t212_guard_property (the GUARD_HOST class reaches the default guard), t244, t312: pass.
- Full suite (every folder under tests/) on the task head 15661710 (one session): 395 test ids FAILED / ERROR; the same
  395 ids re-run on the base head f8180b18 (the working branch before this package): all 395 fail there too, 0 new
  failures (comm of the two id lists empty). They are the known private-input and environment failures: the
  Qortuba / Alrashed private-workpaper suites (test_pa08_*, test_pa09_*: 371), the rebuild-byte-identical packages
  that need private drawings, the ezdxf import-boundary checks (r8_*) and one control-plane gate.
- Freeze 0 differing; codemap stale none; rules manifest drift none.

## 8. Reproduction on the merged head

The task branch merges the working head (T-313 r2, T-322, T-324 research merges; CODEMAP conflict only, maps rebuilt by
the tool). On the merged head f3421887 the full CLI run (v3021_run.py, one process) reproduces V3_0_20 json
`097a80b6` / csv `ca90351b` and **V3_0_21 json `d5327df4` / csv `e9a9c34d`**, DIFF `b167bc99`, INTEGRATION_LEDGER csv
`fd367556`, FACES `63081f77`, CROSS_TRADE `b3067d8b`: byte-identical to the run on the task head.

## 9. Lessons-register proposal (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-29 | An integration ADD into an engine room called 'shared' from its OPEN_PLAN note double-counted the pantry base: 1.9 lm skirting released + 0 .. 1.0 lm bounded under full-height wall tile (Gate B F-T315-C1), and the open-plan line's pantry share was unchecked (F-T315-C2) | cross-trade attribution by room name / note instead of by the finish line's source entities and the merged room split | a finish line is attributed to a tiled room by its source entities lying on the tiled faces and by a merged room-split ledger (WHOLE / PART), never by an engine room's open-plan note; an engine room wholly inside the tiled room is the tiled room's; a PART room keeps a figure only with its tiled share carried off by source entity; one owner per base (every villa) | tests/t315_wall_tile_family/test_base_ownership.py (unnamed line of a WHOLE room refused; unnamed PART skirting / range / paint refused; the open-plan rest kept 12.00 lm; NOT_APPLICABLE on a line with a rest refused; SPLIT to 0 refused; foreign entity, stale figure, non-tiled face refused) | PROPOSED (Checker 03:45); ACCEPTED when r2 passes Gate B |

## 10. For the Checker (Gate B)

Branch agents/task-T-315 (head in the board row). Re-measure: (1) the pantry new line 32.3422 m2 (6 faces, hosts,
open edge 4.49 not tiled) and one more room by hand, e.g. GF-12 7.414 x 3.65 - 1.76 = 25.3011; (2) every line moved
>= 5 % and every new scope = all 12 valued lines (each moved from blank) + the new pantry line; (3) the cross-trade
table: no figure on a paint / skirting line of a tiled room; r2: the four base lines of section 11 (entities and
lengths by hand on P7757.dxf; t315_base_split.py reproduces them); (4)
the 6 HELD lines stay blank; (5) the scoreboard wall-tile row restated from these lines (not from this report);
plus 2 random lines by the WORKFLOW_CONTROLS s.1 rule on the merge-candidate sha.

Files: engine/source/arch_v3021.py; tools/urban_boq_m9.py (V3021 wiring); research/agents_t315/t315_inputs.py,
v3021_run.py, v3021_direct.py, build_master_1_16_0.py; rules/coverage/BOQ_FAMILY_MASTER_1.16.0.json; rules/RULES_MANIFEST.json;
tools/m9_rules_manifest.py; tests/t315_wall_tile_family; maps by the tool. Drive inputs read in the private folder
only; nothing copied here.

## 11. r2: one owner per wall base (Gate B 2026-10-29 03:45, F-T315-C1 / C2)

**The physical element.** The open pantry GF-07 is tiled full height on every drawn wall (UP-PANTRY-003, Q-37 A /
Q-48 A): its wall BASE is porcelain from 0 to 3.65 m, so it carries no skirting (one owner per base, T-296 MERGED
57c31ae4: ROOMS_T296 GF-07 NOT_APPLICABLE, base 7.000 lm of wall + column). The engine's skirting lines are keyed by
ENGINE room, and the pantry lies in two of them (T-262 MERGED c8dba740, ENGINE_ROOM_XWALK): GF-RC06FED (the counter
cell, GF-07 = 0.209 / 1.000: WHOLLY inside) and GF-RC99C2A (the dining / living / reception open zone, GF-07 = 0.665 /
0.070: in PART). r1 left both engine rooms' skirting as it was, so V3.0.21 r1 carried the pantry base twice.

**Drawing-derived split (own walk, research/agents_t315/t315_base_split.py on P7757.dxf ab54dd55 + the run's v29
ARCH_ROOMS.json).** Each boundary edge of the two engine rooms laid on the drawn entity it runs along (parallel,
<= 5 mm), kept where it lies inside the pantry walls (west wall face to the open edge, south face A6 to north face
158): handles and lengths only, no coordinate here.

| Engine room | On the pantry's tiled faces (entity: lm, face) | Sum | Its line | Engine runs agree |
|---|---|---|---|---|
| GF-RC06FED | 2FAB 0.2 + A6 1.4 (south GF-W01; the column top face is collinear with A6's first 0.2 m), AF 0.2 + B0 0.1 (west GF-W16) | 1.9000 lm | L-af6fb2d3 SOURCE_DERIVED 1.9 lm | wall 1.8 + column 0.1 = 1.9 (the 0.2 m shared edge split in halves) |
| GF-RC06FED | W10 frame 3C9 0.05 + 3CC 0.90 + 3D3 0.05 (GF-W16, OP-023, sill 1.0 m: tiled below) | 1.0000 lm | L-73ff85e3 BOUNDED 0 .. 1.0 | glazing 0.5 + threshold 0.5 = 1.0 |
| GF-RC99C2A | 159 0.3409 + 158 0.7591 (north GF-W05, either side of door D-GF-06 1.0 m, no base), 2FAE 0.90 (NW column face, OFF:COLUMN) + 0.05 (its return, OFF:WALL), AE 0.80 + AF 0.65 (west GF-W16) | 3.5000 lm | L-71e2e002 SOURCE_DERIVED 28.171589 lm | all on wall / column entities (each in the net wall + column) |
| GF-RC99C2A | W09 frame 3BC 0.05 + 3BF 1.40 + 3C6 0.05 (GF-W16, OP-024, sill 1.0 m) | 1.5000 lm | L-e7dcdc69 BOUNDED 0 .. 7.831578 (OP-019 6.331578 + OP-024 1.5) | by_window OP-024 1.5 |
| none | A6 1.4 + AF 0.2 (counter cells on no engine room boundary) | 1.6000 lm | no line | - |

Closure: 1.9 + 3.5 + 1.6 = 7.000 lm = T-296 GF-07 base_wc_m (0.0000). Every entity is a source entity of its line
(asserted), every part lies on a face of the pantry's tile record (asserted), the edges past the open edge (column
2FB4 / wall AC at the dining side) are not taken.

**Lines (before V3.0.20 -> after V3.0.21 r2; every other line byte-identical to r1, the tile family unchanged).**

| Line | Before | After | Evidence | Why |
|---|---|---|---|---|
| L-af6fb2d3474c5fbdb80a GF-RC06FED skirting | SOURCE_DERIVED 1.9 lm | NOT_APPLICABLE_WITH_EVIDENCE (no figure) | ASSUMED - OWNER-APPROVED (Q-37 A / Q-48 A), T-296 ruling | the whole line is the pantry base |
| L-73ff85e30e3a8c639e20 GF-RC06FED skirting range | BOUNDED 0 .. 1.0 lm | NOT_APPLICABLE_WITH_EVIDENCE | same | the whole range is the base under W10 (tiled) |
| L-71e2e002a3af624097f0 GF-RC99C2A skirting | SOURCE_DERIVED 28.171589 lm | SOURCE_DERIVED 24.671589 lm (-3.5, -12.42 %) | split DRAWING-CONFIRMED (own walk), rule OA | the pantry part off, the open-plan rest kept |
| L-e7dcdc69e1a2b24f8616 GF-RC99C2A skirting range | BOUNDED 0 .. 7.831578 | BOUNDED 0 .. 6.331578 | same | W09 base off, OP-019 range kept |

Family FIN.SKIRTING: released 185.516658 -> 180.116658 lm (-5.4, -2.91 %), bounded high 27.137649 -> 24.637649 lm
(-2.5). FIN.WALL.TILE unchanged 340.3038 m2 (12 valued, 6 blank). The open zone's paint / plaster lines
(L-c0ac22c9 / L-8cecb1d0 BOUNDED 152.05 .. 178.81 m2) name the T-128 room GF-08 (the dining faces, T-244): not the
pantry's faces, kept; GF-07's own paint / plaster lines (L-c3f7e68c / L-721a0f14) carry no figure.

**Freelancer.** His dry skirting row for the GF open plan (reception + dining + entrance hall, 58.16 + 14.76 lm gross
perimeter, no door deduction; T-106, not re-read here) does not separate the pantry; the engine now carries no
skirting on the pantry walls (wall tile owns them), which is the owner rule: RULE_DIFFERENCE where his row runs a
skirting along the pantry, else no difference; not measured line by line.

**Run (own, Python 3.11.18, Drive P7757.dxf ab54dd55 + ST7757 9f9d1179):** V3_0_19 json b35475bf / csv ef63b73b,
V3_0_20 json 097a80b6 / csv ca90351b (= candidates of record); V3_0_21 r2 json be22a4e4 / csv 3548e39c (3,706
lines): SAME 3,690, CHANGED 15 (11 tile + 4 skirting), ADDED 1, GONE 0; FACES 63081f77 (= r1), CROSS_TRADE 26c09eed,
BASE 2ac58582, DIFF 4e697192.

**Code.** engine/source/arch_v3021.py: split_rooms (WHOLE / PART; the 'shared' note refused), _check_base / base_line /
base_changes (NOT_APPLICABLE or SPLIT by source entity; refused: stale figure, entity not in the line, part on a
non-tiled face, NOT_APPLICABLE with a rest, SPLIT to 0, a line twice, an engine room outside the split), cross_trade
by split (an unnamed figure of a WHOLE room of a fully tiled room refused; an unnamed skirting / paint figure of a PART
room refused), integrate (the base piece replaces skirting / paint lines only; outside quantity, state, basis, notes
and deductions nothing changes), V3_0_21_BASE.csv. research/agents_t315/t315_inputs.py: the split from T-262, the
four base records under T-296 (pins asserted, closure 7.000), t315_base_split.py (the drawing measure, = the pins).
