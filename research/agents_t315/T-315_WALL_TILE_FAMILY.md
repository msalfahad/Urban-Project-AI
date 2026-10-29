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
| Shared engine room (GF-RC06FED = dining + living + pantry + reception) | its room-level lines that name no room (skirting 1.9 m SOURCE_DERIVED, skirting 0 .. 1.0 BOUNDED, plaster / paint NOT_APPLICABLE) are listed as NOT ATTRIBUTABLE to the pantry, never attributed; the two lines naming GF-07 (HL plaster / paint) carry no figure |

## 6. Missing, held, downstream

- HELD, blank, never 0: 6 tile lines (annex G2 / Q-54 B / D-39; GF-10 / GF-11 level T-088).
- Backing plaster / render behind the tile: own line by UP-FIN-PAINT-001, not measured by a merged ledger (73 faces,
  340.30 m2 of tile face once a ledger binds them): proposed Lead row (lane A ledger, then lane I).
- The pantry HL paint line (L-c3f7e68ce91a436802e2, BLOCKED_RFI) is now physically NOT APPLICABLE (every pantry wall
  tiled full height): it carries no figure, so no double count; its state is left byte-identical here (not this
  package's line), named for the Lead.
- The GF-RC06FED skirting 1.9 m: not attributable to the pantry from the line; Checker to confirm it lies on dining /
  living faces (no tiled pantry face).
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
| 2026-10-29 | An open pantry inside a merged engine room (dining + living + pantry + reception) gets its own wall-tile line, and the engine room's room-level skirting / paint lines could be read as the pantry's (a 1.9 m skirting would then be "skirting under tile") | Finish lines are keyed by engine room; one engine room can hold several drawn rooms, and a line that names no ledger room cannot be attributed to one of them | Cross-trade checks attribute a finish line to a tiled room only when it names that room, or names none in an engine room that is the room's alone; in a shared engine room an unnamed line is listed NOT ATTRIBUTABLE and checked by face, never attributed or refused on the room's scope (every villa) | tests/t315_wall_tile_family (shared engine room not attributed; the same line in an unshared room refused as paint under tile) | PROPOSED |

## 10. For the Checker (Gate B)

Branch agents/task-T-315 (head in the board row). Re-measure: (1) the pantry new line 32.3422 m2 (6 faces, hosts,
open edge 4.49 not tiled) and one more room by hand, e.g. GF-12 7.414 x 3.65 - 1.76 = 25.3011; (2) every line moved
>= 5 % and every new scope = all 12 valued lines (each moved from blank) + the new pantry line; (3) the cross-trade
table: no figure on a paint / skirting line of a tiled room, the GF-RC06FED skirting 1.9 m not on a pantry face; (4)
the 6 HELD lines stay blank; (5) the scoreboard wall-tile row restated from these lines (not from this report);
plus 2 random lines by the WORKFLOW_CONTROLS s.1 rule on the merge-candidate sha.

Files: engine/source/arch_v3021.py; tools/urban_boq_m9.py (V3021 wiring); research/agents_t315/t315_inputs.py,
v3021_run.py, v3021_direct.py, build_master_1_16_0.py; rules/coverage/BOQ_FAMILY_MASTER_1.16.0.json; rules/RULES_MANIFEST.json;
tools/m9_rules_manifest.py; tests/t315_wall_tile_family; maps by the tool. Drive inputs read in the private folder
only; nothing copied here.
