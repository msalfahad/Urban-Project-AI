# T-218: floor-area residuals and the ground-floor kitchen's wet scope

Worker 2 (lane A), 2026-10-23 12:42-13:30 UTC. Gate 2. Development villa (Alsenan) + a non-Alsenan fixture. Research
piece, unwired: no released or candidate quantity changes. ERS read and applied: s.2 steps 1-4 (element first, evidence
hierarchy, first-principles reconstruction from printed dimensions, reconciliation in units with every part named),
s.3 (scope before numbers; one physical strip, one line; installed vs procurement; physical vs status).

Data (Drive "Alsenan chalet project", decoded into the private folder, never committed): P7757_DXF_COMPRESSED.zip
(P7757.dxf sha256 ab54dd55...), "ST7757 dxf.dxf" (9f9d1179...), p7757_arch_sheet04.pdf, sanitary-7757.pdf (p.2, 1F
drainage plan). Runs (scratch): released ARCH_TAKEOFF_V2.9 + route G (`tools/release_baseline.py run
research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json`: REPRODUCED, 1,455 lines, BOQ_LINES.csv b96185d4) and the
candidate base ARCH_TAKEOFF_V2.13 (the base method of every V3.0.x candidate, `arch_v30.BASE_METHOD`; V3.0.1 .. V3.0.7
add pieces that do not touch floor-finish or strip lines: grep of `engine/source/arch_v30*.py`, only the stair-residue
piece reads floor lines and the kitchen has no stair). Engine head e866328a.

## 1. (c) The GF kitchen: wet in every line except its floor item

Element: GF kitchen GF-RA3AD49 (label KITCHEN, annex at +0.30), owner rule UP-WET-001 1.1.0 (KITCHEN is a wet code:
wet-area floor item, full-height wall tile, no paint, no skirting, marble threshold, membrane) and Q-30 A (kitchens
waterproofed like a bathroom). The engine's room lexicon types a kitchen SERVICE; `arch_measure.FINISH_KIND` maps
SERVICE -> DRY for the floor item only, while the room's own `finish_scope` is WET (UP-WET-001) and drives every other
line. Found by reading every line of the room in both states (released V2.9 and candidate base V2.13: identical):

| Line | Engine (both states) | With the wet class | Change | Rule | Status |
|---|---|---|---|---|---|
| floor item | FIN.FLOOR.PORCELAIN 9.6300 m2 (dry item) | **FIN.FLOOR.WET_TILE 9.6300 m2** | class only: wet sub-line +9.630, dry -9.630, floor total 0 | UP-WET-001, Q-30 A | ASSUMED - OWNER-APPROVED (class), DRAWING-CONFIRMED (area) |
| membrane floor | FIN.WP.FLOOR 9.630 | 9.630 | 0 | UP-WP-001 | DRAWING-CONFIRMED |
| membrane upturn | FIN.WP.WALL_UPTURN 2.700 m2 | 13.50 lm x 0.20 = 2.700 | 0 | Q-35 C (walls only), UP-WP-003 1.1.0 | DRAWING-CONFIRMED |
| doorway piece | FIN.WP.DOORWAY 0.200 | 1.00 x 0.20 = 0.200 | 0 | rules/ UP-WP-003 1.1.0 | DRAWING-CONFIRMED |
| doorway transition | 0 .. 0.200 BOUNDED | 0 .. 0.200 HELD | 0 | UP-WP-DOOR-001 (no detail) | HELD |
| marble threshold OP-025 | 0.200 | 0.200 | 0 | UP-THR-001 wet | DRAWING-CONFIRMED |
| skirting / paint | NOT_APPLICABLE (wet) | same | 0 | UP-CER-004 / UP-FIN-PAINT-001 | - |
| wall tile | BLOCKED_RFI | HELD (G2 annex height; T-209 READY 41.34 m2 owner-manual candidate) | 0 here | UP-FIN-WALL-001, Q-48 A | HELD |
| penetrations | BLOCKED_RFI | HELD | 0 | UP-WP-004 | HELD |
| bed under the tile | dry 3 .. 4 cm: 0.2889 .. 0.3852 m3 | wet 4 .. 6 cm: **0.3852 .. 0.5778 m3** | +0.0963 .. +0.1926 m3 | Q-45 (PROVISIONAL) | ASSUMED - OWNER-APPROVED |
| cement (50 kg) / sand | 2.31 .. 3.08 bags / 0.318 .. 0.424 m3 | **3.08 .. 4.62 bags / 0.424 .. 0.636 m3** | before 5 % waste | G4 (8 bags + 1.10 m3 per m3) | ASSUMED - OWNER-APPROVED |
| adhesive (20 kg) | 1.926 bags | 1.926 bags | 0 | Q-45 (5 m2 / bag) | ASSUMED - OWNER-APPROVED |
| membrane rolls (V2.13) | 2 rolls | 2 (T-074 strips along x 14.56 m2) | 0 | Q-49 A | procurement, not here |

Hand reconstruction (printed, GF plan): floor 3.00 x 2.70 + entrance 1.05 x 1.50 - piers 0.05 x 0.50 - 0.05 x 0.40 =
**9.630 m2** = engine; boundary of the L outline 2 x (2.70 + 4.50) + the 0.50 pier standing 0.05 proud (2 x 0.05) =
**14.50 lm** = engine; upturn walls only 14.50 - door 1.00 = **13.50 lm, 2.700 m2** = engine. The engine's runs split the
1.50 m window W08 into 0.75 window wall + 0.75 'glazing edge' because V2.9 has no sill; T-201 (MERGED) prints the sill
1.00 above the floor, so all 1.50 m is wall below a sill (eligible): the 13.50 lm stands on drawing evidence, not on
the split. Door OP-025: masonry gap 1.000 m between the wall ends (the width every threshold of the run takes), frame
jamb blocks 0.05 each, 0.90 m clear; wall 0.20.

D-C3 check (the attached cell 1.365 m2 through 'OP-002'): the cell is the printed 1.05 m wide entrance of the kitchen
(105 x 150): walls on three sides, the service door OP-025 in its outer wall, the +0.30 level mark inside it (the
kitchen's own level), no wall, door, glazing or step between it and the kitchen; 'OP-002' is the line from the free end
of the 0.50 pier across the 1.00 m to the opposite wall, not a built element. One room, one wet scope: BOUNDARY
CONFIRMED (worker reading, DRAWING-CONFIRMED; the Checker re-reads it).

Against the freelancer (FIN workbook, wet tiles sheet row 48 and membrane sheet row 20): he classes it WET (as Q-30 A):
floor 9.55 m2 / 14.35 lm. Engine 9.630 / 14.50: **+0.080 m2 (+0.84 %), +0.15 lm (+1.05 %)**, ENGINE_RIGHT on the printed
sizes (his values typed, no formula). Wet floors, engine vs freelancer: 62.4907 -> **72.1207 vs 72.01 m2 (+0.1107,
+0.15 %)** after the re-class (T-208 measured the -9.519 m2 gap; this is its cause). Floor-key total unchanged.

## 2. (b) The 1F / 2F doorway strips: one strip, one line

Every strip line of the two upper floors, classified by the two spaces it joins (`STRIPS_T218.csv`):

| Strip | Joins | Engine line | Proposed | Status |
|---|---|---|---|---|
| 1F OP-005 door 0.90 x 0.15 | living / 380 x 430 room (dry / dry) | FIN.FLOOR.PORCELAIN 0.135 | porcelain strip (UP-THR-001 dry) | DRAWING-CONFIRMED |
| 1F OP-006 door 0.90 x 0.15 | living / curved room lobby | FIN.FLOOR.PORCELAIN 0.135 | porcelain strip | DRAWING-CONFIRMED |
| 1F OP-020 door 1.00 x 0.15 | living / west room | FIN.FLOOR.PORCELAIN 0.150 | porcelain strip | DRAWING-CONFIRMED |
| 1F OP-007 opening 1.00 x 0.20 | living / lift shaft | FIN.FLOOR.PORCELAIN 0.200 | **lift landing threshold, HELD** (landing door + sill with the lift, UP-DOOR-CLS-005; the GF landing OP-011 is already an ARCH.THRESHOLD line) | HELD |
| 1F OP-011 arch 1.00 x 0.15 | 380 x 430 room / unlabelled dressing | FIN.FLOOR.PORCELAIN 0.150 | **HELD with the dressing** (type not established, UP-WET-002 never-dry) | HELD |
| 2F OP-007 door 0.90 x 0.20 | stair room / maid room | FIN.FLOOR.PORCELAIN 0.180 | porcelain strip | DRAWING-CONFIRMED |
| 2F OP-002 opening 1.00 x 0.20 | stair room / lift shaft | FIN.FLOOR.PORCELAIN 0.200 | **lift landing threshold, HELD** | HELD |
| 2F OP-001 door 1.00 x 0.15 | stair room / +9.70 roof (exterior) | FIN.FLOOR.PORCELAIN 0.150 PROVISIONAL | **exterior sill, HELD** (by specification; UP-THR-001 dry is for interior doorways) | HELD |
| 7 wet doors (1F OP-004 / 008 / 010 / 018 / 019, 2F OP-006) | a wet room on one side | FIN.MARBLE.THRESHOLD | unchanged | DRAWING-CONFIRMED |

So the engine-only strips are 1F 0.770 = porcelain 0.420 + HELD 0.350 and 2F 0.530 = porcelain 0.180 + HELD 0.350:
**0.700 m2 of released porcelain is a threshold / held item** (lift landings 0.400, exterior sill 0.150, the arch to the
untyped dressing 0.150). Two latent double counts found (BLOCKED_RFI today, so no released total is wrong yet): the
1F unattributed strip lines SITE-29faec (OP-005, face 0.166) and SITE-fd160f (OP-004, face 0.154) are ARCH.THRESHOLD
lines over the same strips the run already bills as porcelain 0.135 / marble 0.120; when Q-S6-1 gives a finish they
would bill 0.135 + 0.120 m2 twice. Only their residues (0.031 / 0.034 m2 beyond the opening box) are not in another line.

## 3. (a) The 1F bed rooms -1.379 m2: re-paired, closed to named parts

T-153 / T-208 paired the 380 x 430 room with his 'bed room 1' 17.29 and the curved east room with 'bed room 2' 19.46;
neither closed (+0.95, +0.44), so it stayed UNRESOLVED. Read again from the printed sizes:

- his 'bed room 2' **19.46 m2 = 380 x 430 room 16.340 + its dressing 1.65 x 1.80 = 2.970 + the arch strip 1.00 x 0.15 =
  0.150 = 19.460 exactly**, and his skirting / perimeter column for that row, **21.40, = the joined outline 2 x (3.80 +
  4.30) + 2 x (1.65 + 1.80) - 2 x 1.00 + 2 x 0.15 = 21.40 exactly**. Two independent exact matches: this is his row.
- his 'bed room 1' 17.29 / 22.89 is then the curved room. Engine 19.0165 = room to the curved face 15.062 (printed 4200 x
  4000, 3450 at mid height to the curved face) + OP-009 strip 1.30 x 0.15 = 0.195 + lobby printed 1.80 x 2.10 less a
  0.05 x 0.375 pier = 3.761. The 0.50 x 2.10 rectangle with one diagonal in the lobby (and the 0.50 x 1.80 one in the
  dressing) is joinery, not a shaft: nothing at that position on the GF plan below (outside the building there) or on
  the roof plan above, no fixture or drain on the 1F drainage plan; not deducted
  (URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1; his 19.46 includes the dressing one too). No reading reproduces his
  17.29 (drawn room 15.062; + strip 15.257; rectangle 4.20 x 4.00 16.800; 3.45 x 4.00 + lobby 17.580; all less the
  wardrobe 17.987; engine 19.0165): **+1.727 m2 (+9.99 %) UNRESOLVED**, his row typed with no dimensions.

| Part | m2 | Kind |
|---|---|---|
| dressing 2.970 HELD outside the floor key (type, T-153), inside his row | -2.970 | STATUS |
| arch strip OP-011 0.150: engine strip line, inside his row | -0.150 | SCOPE |
| curved room vs his 17.29 | +1.7265 | UNRESOLVED |
| west room: printed 4.25 x 4.50 = 19.125 less drawn column notches 0.075 = 19.050 vs his 19.00 | +0.050 | AGREE (+0.26 %) |
| 500 x 365: printed 18.250 = his; engine face less a drawn 0.035 column notch | -0.035 | RULE_DIFFERENCE (-0.19 %) |
| **sum = 72.6215 - 74.00** | **-1.3785** | residual **0.0000** |

## 4. The floor key (FLOOR.INTERNAL) like for like, after (a)-(c)

T-208's +0.044 m2 (+0.01 %) hid offsetting items: the dressing (-3.12 with its strip) against the curved room (+1.73)
and the engine-only strips (+1.30). With the proposals of section 2 applied (0.700 m2 out of porcelain into
threshold / held lines) and the dressing + arch strip taken as a scope item S5 (-3.120, in his row, HELD in the engine):
engine 384.9339 vs his 409.58 less S1-S5 (-27.1104) = 382.4696 -> **+2.4643 m2 (+0.64 %) like for like**, closed to
named parts (`FLOOR_KEY_T218.csv`, residual 0.0001 rounding): the curved room +1.7265 UNRESOLVED, the engine-only porcelain
door strips +0.600 (1F 0.420, 2F 0.180; his rows carry no strip), and T-208's other rows unchanged (GF +0.169 in seven
groups, 1F living +0.019, 1F wet +0.235, 2F maid -0.230, 2F W.C. -0.070), west +0.050, 500 x 365 -0.035. The kitchen
re-class moves no m2 in this key (wet 72.1207 vs 72.01, dry -9.630 vs his dry rows, which never held the kitchen).

## 5. Proposal for lane I (no tool or method edited here)

1. Floor item from the owner scope: a V3.0.x piece that re-codes a floor line FIN.FLOOR.PORCELAIN -> FIN.FLOOR.WET_TILE
   when the room's `finish_scope` is WET by a WET_RULES id (`wet_class_strips.floor_item`), same quantity, line id kept,
   ledger before / after; on Alsenan the GF kitchen 9.630 m2 only (`check_room_lines` run on all 38 rooms of each
   state, released and candidate base: the kitchen is the only finding).
2. Strip lines: 1F OP-007, 2F OP-002 -> ARCH.THRESHOLD lift landing (HELD); 2F OP-001 -> ARCH.THRESHOLD exterior sill
   (HELD); 1F OP-011 -> HELD with the dressing; floor key -0.700 m2 out of released porcelain into held threshold lines.
3. The unattributed ARCH.THRESHOLD lines of 1F OP-004 / OP-005 limited to their residues (0.034 / 0.031 m2) or retired,
   so that no strip is billed twice when Q-S6-1 resolves (`one_strip_one_line`).
4. Scorer (tools/alsenan_keymap.py): his 'bed room 2' row paired with the 380 x 430 room + dressing + OP-011 strip and
   'bed room 1' with the curved room (BEDROOMS_T218.csv).

## 6. Rule, test, lessons row

Rule (scope: every villa, every room and doorway strip; provenance: UP-WET-001 1.1.0, Q-30 A, UP-THR-001, UP-WP-003 /
Q-35 C, UP-DOOR-CLS-005, Q-45 / G4): the floor item of a room follows its owner finish scope, never the room-type
lexicon alone; every line of one room carries one class; a doorway strip is billed by one line chosen from the two
spaces it joins (dry / dry porcelain, any wet side marble, lift landing or exterior sill or an untyped side HELD).
Tests: `tests/t218_floor_residuals` (27): villa T218-V hand fixture (kitchen 3.60 x 3.00: wet tile 10.800, upturn 12.30
lm / 2.460 m2, doorway 0.180, bed 0.432 .. 0.648 m3, cement 3.456 .. 5.184, sand 0.4752 .. 0.7128, adhesive 2.16);
adverse: wet class without a rule id, a wet rule on a room with no wet code, unknown scope (HELD, never dry), window
without a sill (upturn HELD with its range), missing door depth / floor (HELD, never 0), millimetres, bad strip sides,
one strip in two lines; the Alsenan ledger reproduces.
Lessons-register row proposal: 2026-10-23 | wet floors -9.519 m2 vs the freelancer while every other kitchen line was
already wet | the floor item took its class from the room-type lexicon (kitchen = SERVICE = dry), the other lines from
the owner scope (UP-WET-001) | one room, one class: the owner scope sets every line, including the floor item; a check
lists any room whose lines disagree (every villa) | tests/t218_floor_residuals | proposed (T-218 READY).
Second row: 2026-10-23 | 1F bed rooms -1.379 m2 UNRESOLVED for two days | freelancer rows paired by name and rough size;
his skirting column was never used as a second key | pair a typed row by two independent quantities (area AND its
perimeter / skirting) before any verdict; a pairing that closes neither is not a pairing (every villa) | ledger test |
proposed.

## 7. Missing / held / feedback

- Curved room +1.727 m2 UNRESOLVED (his row has no dimensions); the attached lobby stays PROVISIONAL until its boundary
  is confirmed by the Checker (same reading as the kitchen's: walls, door, no partition).
- Dressing 2.970 m2 HELD (type; designer list, T-153); evidence toward dry recorded (no fixture, no drain).
- Kitchen wall tiles: T-209 (READY) uses a 0.95 m door width for OP-025 (2.09 m2 deducted); the drawing gives a 1.000
  m masonry gap and 0.90 m between the frame jambs (FEEDBACK for T-209's Checker; not changed here).
- Not done: the GF pantry (Q-37 A wet, T-153) is outside this task's rows; GF strips (T-208).

Checker re-measure: (1) the kitchen perimeter on P7757.dxf (L outline 2.70 x 4.50 + pier = 14.50 lm; door gap 1.000)
and the entrance cell (1.05 x 1.30 through 'OP-002'); (2) the 1F 380 x 430 room + dressing 1.65 x 1.80 + arch 1.00 x
0.15 = 19.46 and its outline 21.40; (3) the curved room 4200 / 4000 / 3450 and the lobby 1800 x 2100 (19.0165).

Files: `wet_class_strips.py` (method, any villa), `alsenan_t218.py` (ledger, `--check`), `extract_t218.py`,
`ALSENAN_T218_INPUT.json` (ids, items, quantities, lengths; no coordinates), `KITCHEN_T218.csv`, `STRIPS_T218.csv`,
`BEDROOMS_T218.csv`, `FLOOR_KEY_T218.csv`, `summary.json`. Repeat: the two runs above into scratch, then
`python3 -I research/agents_t218/extract_t218.py RUN29 RUN213 --out research/agents_t218/ALSENAN_T218_INPUT.json` and
`python3 -I research/agents_t218/alsenan_t218.py`.
