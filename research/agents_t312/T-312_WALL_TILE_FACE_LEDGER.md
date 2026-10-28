# T-312: WALL TILE FACE-TO-LINE LEDGER, every tiled wall face once against the candidate's FIN.WALL.TILE line ids (development villa; every villa by R-T312-1 .. 4)

Worker 2 (lane A), claim 2026-10-26 04:41 UTC, run unknown. Integration dependency of a MISSING category (T-255 Gate B:
"no FIN.WALL.TILE integration row"): a lane I package can now add the wall-tile family face by face. Research only: no
engine module, rule or knowledge file, candidate line, released line or V2.9 cell changed; released default stays V2.9
+ route G; nothing released, nothing VERIFIED by this task. ERS read and applied: s.2.1 (physical element first), s.2.2
(owner manual method and drawing-derived method side by side), s.2.4 (reconcile in m2 to named causes), s.3 (one face,
one owner; build before deduct; a rule's scope before its arithmetic), s.4 (rule + tests, normal and adverse), s.7
(lesson row, section 8). Builds on merged T-209 (room nets, Q-48 A), T-250 (drawn faces), T-292 r2 (face-to-line rows of
the 18 wet rooms), T-286 (pantry box and counters), T-296 (pantry base = wall tile), T-303 (wet set = 18, door widths);
none of their quantities is re-derived, each is bound to a line and re-checked under the new rules.

## 1. Run and identity

Own run, Python 3.11.17, Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and
'ST7757 dxf.dxf' (`9f9d1179`): research/agents_t167/v304_run.py, then research/agents_t255/v3019_run.py:
**V3_0_19_BOQ_LINES csv `ef63b73b` / json `b35475bf` (3,705 lines) = the candidate of record** (T-255 Gate B; the json equals the Checker's own V3.0.19 b35475bf). Extract
`t312_alsenan.py --extract <run>/t255/v3019` -> CANDIDATE_V3019_WALL_TILE_LINES.json (the 17 FIN.WALL.TILE lines, the 17
'paint above wall tile' lines and every line of the pantry engine room GF-RC06FED: id, item, floor, room, element,
unit, state, quantities, RFI head). `--geometry P7757.dxf` -> PANTRY_HOSTS_T312.json (handles and lengths only).
Ledger `--write`; `--check` rebuilds byte for byte; tests `tests/t312_wall_tile_ledger`.

## 2. The physical element and the candidate's lines

Wall tile is porcelain / ceramic on a WALL FACE (one drawn wall seen from one room) from the finished floor to the tile
top, less the holes in that band. The owner rules decide WHICH faces carry it:

- every wall face of a WET room, full height (UP-FIN-WALL-001; tile top = underside of the 0.15 decor ceiling,
  floor-to-floor - 0.60 - 0.15 - 0.10, Q-48 A: GF 3.65, 1F / 2F 3.35, annex HELD G2 / Q-54 B);
- in an open American pantry (UP-PANTRY-001) only the HOST walls of the installation, each as a whole wall
  (UP-PANTRY-003 FULL_WALL), never the perimeter of an imaginary closed pantry; an open edge tiles nothing
  (UP-PANTRY-002); the height is the project / owner height, never assumed (UP-PANTRY-004; here Q-48 A 3.65);
- no tile on a dry face, an exterior face or an open side; no paint on a tiled face (the candidate's 17 'paint above
  wall tile' lines are NOT_APPLICABLE_WITH_EVIDENCE, agreed).

The candidate carries **17 FIN.WALL.TILE lines, one per wet room of the released route, all BLOCKED_RFI with no
quantity**, and **no wall-tile line for the pantry** (engine room GF-RC06FED carries floor, membrane, plaster and paint
lines only; T-292 found the same on V3.0.15). Door jamb / head surfaces are not wall faces: they are the reveal family
(T-313), never in this ledger.

## 3. Pantry: which walls are tiled (UP-PANTRY-003, read on P7757.dxf)

Pantry box 3.000 x 4.500 (T-286: DIMENSION 5D5 / 5E1), west wall face AE / AF / window W10 / W09 (GF-W16), south wall
A6 (GF-W01), north wall 158 / door D120 / 159 (GF-W05) with the column 2FAE notch 0.90 x 0.05, east edge B3 / AD
(layer 5) OPEN to the dining. Installations (layer 5 outlines; no sink block on the DXF, the floor drain is on
sanitary-7757.pdf):

| Run (leg) | Back (fixed along) | Back length | Depth | Host of |
|---|---|---|---|---|
| west counter, west leg (335 / B1) | west wall face | 3.066 m | 0.50 | GF-W16 |
| west counter, north leg (15C / 33F) | column 2FAE face 0.90 + north wall 158 0.50 | 1.45 m | 0.45 .. 0.50 | column face, GF-W05 |
| east counter, south leg (B2 / AA) | south wall A6 | 1.400 m | 0.50 | GF-W01 |
| east counter, east leg (B4 / 15D) | the OPEN edge B3 (a peninsula, stools beyond) | 3.000 m | 0.50 | nothing (open edge) |

**Every drawn pantry wall hosts a counter run** (west 3.066, south 1.400, north 0.500 + column 0.900 m): by UP-PANTRY-003
each is tiled as a whole wall; the open edge (4.49 m) is NOT tiled (UP-PANTRY-002). So the T-209 / T-292 pantry figure
(all walls but the open edge, 10.491 m x 3.65 less D120 2.20 and W10 / W09 1.50 / 2.25 = **32.3422 m2**) is confirmed
under the pantry rules, not only under Q-37 A's "wet": both methods agree here (owner manual: Q-48 A height; drawing:
the host walls). The two T-250 perimeter pieces not tied to one wall (OFF:WALL 0.165, walk residual 0.001) are tiled
because every wall hosts (R-T312-1: were one wall not a host, they would be UNRESOLVED, never tiled by default).
**But the candidate has no line to carry it: NO_LINE, a named MISSING line, 6 faces, 32.3422 m2.**

## 4. Every wet-room face once (FACE_LEDGER_T312.csv)

115 face pieces in 18 rooms + 2 open edges (pantry 4.490, wash lobby 1.245 m); every piece TILED or OPEN_EDGE
(no wet-room wall is untiled; nothing UNRESOLVED). Per room the pieces close to the T-074 / T-128 r3 walked contour,
**residual 0.0000 m in all 18 rooms** (ROOM_CLOSURE_T312.csv). Every opening once per room side (OPENINGS_T312.csv,
35 rows; the T-292 merged sizes), each deduction re-derived as its part inside [0, tile top] and equal to T-292's to
1e-6: doors 0.80 / 0.90 / 1.00 x 2.20 (Q-55 C), windows w x (head - sill) with every head below its tile top (2.50 /
3.00 < 3.15 / 3.35 / 3.65). W18 (1F east bath, sill 0.84 / head 3.00 printed) is deducted once, 1.080 m2, on the tile
side (T-255 had it as the HELD wall-tile side with no carrier: it now has one). No window lies above a tile top on this
villa, so R-T312-3's "no deduction above the tile" changes no Alsenan figure (it is tested on the fixture).

| Line (engine room <- room) | Faces | Candidate | Ledger (owner method) | Status |
|---|---|---|---|---|
| 11 lines: GF-12 / GF-13 / GF-14 / GF-16, 1F-02 / 1F-03 / 1F-07 / 1F-08 / 1F-09 / 1F-12, 2F-02 | 67 | blank (BLOCKED_RFI) | **307.9616 m2** | ASSUMED — OWNER-APPROVED |
| 4 annex lines GF-02 / GF-03 / GF-05 / GF-06 | 29 | blank | blank (owner 3.15 PROVISIONAL shown as information only) | HELD (G2, Q-54 B, D-39) |
| 2 lines GF-10 / GF-11 (W.C. by the stair, basin space) | 13 | blank | blank | HELD (room level +0.30 / +1.00 not drawn, T-088) |
| **NO_LINE** (pantry GF-07) | 6 | **no line** | **32.3422 m2** | ASSUMED — OWNER-APPROVED; MISSING line |

Owner method total, determinate: **340.3038 m2** on 12 rooms (307.9616 in lines + 32.3422 with no line); 6 rooms HELD,
never 0. The 1F-09 figure is 23.2201 (D-1F-07 at the drawn block width 0.80, T-292 / T-303) against T-209's 23.33
(0.75 rebate face), -0.110 m2, named. Drawing-derived method beside (dwg columns, T-292): HELD on every face except the
1F W.C. 147 x 180 (T-209 22.55 .. 23.20 DRAWING-CONFIRMED bounded): the roof datum DCR-6 (D-39 item 3), the sunken
wet panels over five GF rooms and the 1F laundry (T-206 / T-209), the floor build-up b (DCR-7). It is never used to
fill a blank.

Shower / bath recesses and boxed ducts: P7757.dxf draws no tub, tray or duct box inside a wet room (the fixture blocks
are WC / WASH2 symbols and room-label blocks); the recesses that exist (the wash-lobby basin niche, column faces proud
in 6 rooms, wall stubs off the straight bands) are their own face pieces in the T-250 walk, each once.

## 5. Engine vs freelancer (RECONCILIATION_T312.csv)

His wall-tile item = his wet-wall rows, his boundary lm x 3.00 m, no opening deducted (T-010 / T-086 / T-209), 433.83
m2 in 17 rows, no pantry row. On the 11 rooms both have established:

| Step | m2 |
|---|---|
| Freelancer, 11 rooms | 295.44 |
| Length (drawn faces vs his rounded lm, x 3.00; wash lobby -3.699: his 9.50 lm closes the 1.245 m open side) | -2.652 |
| Height (owner 3.65 / 3.35 vs his 3.00) | +43.193 |
| Doors (13 openings x 2.20 head, Q-55 C) | -23.100 |
| Windows (9 windows, T-201 / printed) | -4.920 |
| Own (owner method) | **307.9616** |
| Residual | 0.0002 (4-dp face rounding) |

**Engine ledger vs freelancer +12.52 m2 (+4.24 %) on 11 rooms** (T-209 had +12.63 / +4.28 %; the -0.110 is the 1F-09 door
width). Pantry: ours 32.3422, his none (SCOPE: ENGINE_RIGHT by Q-37 A + UP-PANTRY-003 host walls). The 6 held rooms (his
138.39 m2) are not compared. Verdict proposals: height RULE_DIFFERENCE (Q-48 A owner rule vs a flat 3.00 printed
nowhere); openings ENGINE_RIGHT (UP-CER-005 / Q-73 A: no tile on a hole; he deducts none); lobby length ENGINE_RIGHT
(open side, no wall); pantry scope ENGINE_RIGHT.

## 6. For the lane I package and for the Checker

Consumer shape: FACE_LEDGER_T312.csv (face, room, class, piece, length, scope + rule, host m, openings, owner height and
source, owner status and net, held item, drawing status, engine room, line id or NO_LINE), LINE_SUMMARY_T312.csv (each of
the 17 lines once + the NO_LINE row: candidate state, ledger figure, status, held item), OPENINGS_T312.csv (each opening
once per room side with its band part). The package needs ONE NEW LINE for the pantry wall tile (GF, 32.3422 m2, 6
faces) and fills 11 blanks; 6 stay blank HELD with their items.

Re-measure (Gate A): (1) the pantry hosts on P7757.dxf: counter legs 335 / B1, 15C / 33F, B2 / AA, B4 / 15D against the
faces AE / A6 / 158 and the column 2FAE (hosts 3.066 / 1.400 / 0.500 + 0.900 m, east leg on the open edge B3); (2) one
wet room by hand: 1F-12 = 8.70 x 3.35 - D315 0.80 x 2.20 - W18 0.50 x (3.00 - 0.84) = 29.145 - 1.760 - 1.080 =
26.305 m2; (3) the GF-14 closure 8.267 + open 1.245 = 9.512; (4) two random face rows against T-250 FACE_LENGTH.

## 7. Rules and tests

- R-T312-1 .. 4 (t312_wall_tile_rules.py, any villa): scope (wet room full height; open pantry host walls only, a run's
  BACK on the wall over >= 5 cm, an end against a side wall no host, open edge nothing, no installation drawn ->
  UNRESOLVED; enclosed pantry = wet room); height per face with a source (universal / default refused, mm refused,
  missing -> HELD, never 0); openings once per room side by their part inside the tile band (window above the tile top
  deducts nothing, a claimed deduction refused); each tiled face in exactly one line or NO_LINE, closure per room.
- Tests (tests/t312_wall_tile_ledger): villa T hand fixture (not Alsenan): a 2.40 x 3.00 bath with a door 0.80 x 2.10
  and a window above the 2.60 tile top (26.40 m2); an American pantry 3.00 x 2.00 with one open edge, an L counter (north
  run + west return), nothing on the east wall (12.18 m2); adverse: universal height, window above the tile deducted,
  open edge tiled, imaginary closed pantry, dry face tiled, face in two lines, opening twice, open closure, mm units,
  held as 0; mirror / rotation / shift invariance of the hosts; a corner touch and a back 3 cm off the face are no host.
  Alsenan pins: byte-identical rebuild, 18 rooms close, 17 lines once, pantry NO_LINE 6 faces, hosts, named totals,
  freelancer residual, no coordinates.

## 8. Lessons-register proposal (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-26 | The open pantry's wall tile (32.34 m2) was measured in every merged ledger (T-209, T-292) but the candidate has no FIN.WALL.TILE line for it; and its scope rested only on "the pantry is wet" (Q-37 A, a waterproofing answer) while the owner's pantry rule tiles only the host walls of the installation (UP-PANTRY-003) | The wet-room tile scope was applied to the pantry as a room; the released route makes tile lines only for rooms on its wet list, so an open zone gets none | Tile scope in an open pantry / kitchen zone is decided wall by wall from the drawn installation (a run's back on the wall = host, whole wall tiled; no host = not tiled; open edge nothing; no installation drawn = UNRESOLVED), and a measured scope with no carrier line is reported NO_LINE (a MISSING line), never dropped (every villa) | tests/t312_wall_tile_ledger (pantry host walls normal; imaginary closed pantry, open edge tiled, no installation -> all walls refused) | PROPOSED |

Files: `t312_wall_tile_rules.py` (rules), `t312_alsenan.py` (runner), CANDIDATE_V3019_WALL_TILE_LINES.json,
PANTRY_HOSTS_T312.json, FACE_LEDGER_T312.csv, ROOM_CLOSURE_T312.csv, LINE_SUMMARY_T312.csv, OPENINGS_T312.csv,
RECONCILIATION_T312.csv, summary.json; tests `tests/t312_wall_tile_ledger`. Drive inputs read in the private folder only;
nothing copied here.
