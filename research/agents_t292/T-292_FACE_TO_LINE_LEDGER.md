# T-292: plaster / paint FACE-TO-LINE LEDGER, every wall face against the candidate's plaster, paint and wall-tile line ids (development villa; every villa by R-T292-1)

Worker 2 (lane A), claim 2026-10-25 10:41 UTC. Integration dependency of T-244 (lane I, plaster / paint whole line).
Research only: no engine module, rule or knowledge file, candidate line or released line changed; released default stays
V2.9 + route G; nothing here is released. ERS read and applied: s.2.1 (physical element first), s.2.2 (owner manual
method and drawing-derived method side by side), s.2.4 (reconcile in m2 to named causes, never a plug), s.3 (one element,
several trades: one finish owner per face; build before deduct), s.4 (rule + test, normal and adverse), s.7 (lesson row).

## 1. Run and identity

Own run, Python 3.11.17, Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and
'ST7757 dxf.dxf' (`9f9d1179`): research/agents_t167/v304_run.py (V3.0.3 `5ba4ae93`, V3.0.4 `d86de34a` REPRODUCED) then
research/agents_t270/v3015_run.py (V3.0.7 `197c5599`, V3.0.8 `57fe219a`, V3.0.9 `63b350cf` reproduced on the way):
**V3_0_15_BOQ_LINES.csv `a4dc01dd` = the T-270 r2 Gate B file** (3,699 lines; T-245's V3.0.16 lines are byte-identical
to it, T-290 / T-291 rows). Extract: `python3 -I research/agents_t292/t292_alsenan.py --extract <run>/v3015` ->
CANDIDATE_V3015_WALL_FINISH_LINES.json (132 lines of FIN.PLASTER / FIN.PAINT / FIN.WALL.TILE / FIN.EXT.FINISH: id,
item, floor, engine room, element, unit, state, quantities, RFI head; no coordinate, no name). Ledger: `--write`;
`--check` rebuilds byte-identical; tests `tests/t292_face_line_ledger`.

## 2. Physical element and the face universe

A wall FACE is one wall seen from one room: the stretch of the wall's face line the room touches (T-250, R-T250-1), from
the floor to the finish top, less its openings by their own area inside that height (Q-73). The candidate measures
room by room (one FIN.PLASTER and one FIN.PAINT line per V3.0.9 room record, T-211; one plaster + one wall-tile line per
wet room of the released route), with no wall key. So the ledger cuts every room into its face pieces:

| piece | source | count |
|---|---|---|
| WALL FACE, one per (room, wall) on the straight runs, open-side metres out | T-250 FACE_LENGTH (158 run rows) | 149 |
| COLUMN FACES PROUD 17 / WALL OFF A STRAIGHT BAND 22 / GLAZING OFF A BAND (W03 x 2, W17) 3 / DOORWAY REVEALS 10 | T-250 ROOM_CLOSURE off-line metres | 52 |
| WALK CLASS RESIDUAL (T-128 FACE_M - the T-250 pieces) | named per room | 17 |
| **total face pieces** (32 rooms) | | **218** |

Every room closes on T-128 r3's FACE_M (the length its lines were built on) to **0.0000 m** (ROOM_CLOSURE_T292.csv).
The residual pieces are named, not plugs: 16 rooms 0.001 .. 0.040 m where T-250 classes 5 mm samples at opening ends as
open side and T-128 as face (same contour, two classifications; at most 0.04 x 3.35 = 0.13 m2, 1F-13); **GF-16 -0.524 m**,
where T-128 takes the bath from the T-074 VERIFIED hand outline (7.625 m) and the T-250 walk of the T-147 region runs inside
the GF-W19 / GF-W31 strips onto the far faces (T-250 s.3, 3.252 m): the room keeps the verified outline.

**One owner per face (rule 2):** DRY rooms and the shaft -> FIN.PLASTER + FIN.PAINT; WET rooms -> FIN.WALL.TILE full
height (Q-48 A, UP-FIN-PAINT-001: no paint; the candidate agrees: its 17 'paint above wall tile' lines are
NOT_APPLICABLE) and FIN.PLASTER only as the HELD substrate question (plaster under tile is not an owner rule, T-211
s.5.4); exterior faces have no room (T-250 'NO ROOM ON THIS SIDE') and belong to FIN.EXT.FINISH / Sigma
(OWNER_NOTES_SIGMA_2026-10-21); open sides carry nothing. 436 face rows = 218 pieces x 2 item codes.

**Openings (rule 5):** 85 deductions, each once per room side by opening id on the face that hosts it
(OPENING_DEDUCTIONS_T292.csv), sizes = T-237 part 4 (merged T-175 -> T-201 -> T-207 -> T-238; doors keep the Q-55 C 2.20
head; D-GF-05 / D-1F-07 at the census frame width). Four T-237 by-name joins corrected by geometry (T-262 JOIN_WRONG:
W19 / D-1F-01 are in 1F-03, W20 / D-1F-04 in 1F-02; both rooms deduct one 0.60 window and one 0.80 door, nets unchanged).

## 3. Results

**Lines (LINE_SUMMARY_T292.csv): every one of the 132 candidate lines once.** 63 bound to faces; 69 listed with their
reason: 26 route room lines superseded by the V3.0.9 records (NOT_APPLICABLE, no figure), 17 'paint above wall tile'
(NOT_APPLICABLE: a tiled face is not painted), 22 door jamb / head lines (UP-FIN-PLASTER-001: surfaces perpendicular to the
wall, in no face length, own line), 3 FIN.EXT.FINISH facade lines (exterior faces, no room), and **the pantry paint line
L-c3f7e68ce91a436802e2 holds no face** (GF-07 is WET by owner Q-37 A / T-128; T-211 kept it HELD so no face was dropped).
Unmatched faces: the 6 pantry pieces for FIN.WALL.TILE (no candidate tile line in GF-RC06FED: V3.0.9b) - listed, not
dropped. Closure faces vs lines (owner method): plaster 612.3013 .. 659.1298 = lines, paint the same, tile 307.9616 =
lines: **residual 0.0000** each; line vs ledger after the named causes: max |residual| 0.0002 m2 (4-dp rounding of
the per-face figures).

**Before (candidate V3.0.15) -> after (this ledger), owner manual method of record (G1 heights, Q-43 / Q-48 A):**

| Line (engine room <- room) | Candidate | Ledger | Cause (opening, m2) | Status after |
|---|---|---|---|---|
| L-971f0bdaf68d / L-d9f4ecdb6ef9 1F-RED0D19 <- 1F-04 | 49.1375 .. 54.33 HELD | **52.0051** | W24 head DRAWING-CONFIRMED (T-201): HELD 0 .. 5.1925 -> 2.3250 | ASSUMED - OWNER-APPROVED |
| L-4ce74fc37a08 / L-5410f9045c80 2F-R1DB2D2 <- 2F-03 | 55.555 .. 59.575 | **57.775** | W29 head (T-201): 0 .. 4.02 -> 1.80 | ASSUMED - OWNER-APPROVED |
| L-9b4a7bab033d / L-be48ea84285b 1F-R78C367 <- 1F-13 | 110.1335 .. 114.3677 | **111.0175 .. 114.3675** | W15 / W16 4.3629 .. 4.805 -> 4.363 each (T-238 outline) | HELD (lift door) |
| L-31db3c835526 / L-349db74a70e1 1F-R3CFCFD <- 1F-11 | **59.4511 RELEASED (VERIFIED)** | **60.4351 .. 70.4591** | W17 3.286 x 3.35 = 11.008 -> HELD, cap 10.024 (T-238: 3.50 is the archivolt) | **HELD (BOUNDED)**: 8 faces stay VERIFIED, the W17 piece is held |
| L-ae0cdd794cc5 / L-c74cfb4e07bc 2F-R4D1B62 <- 2F-01 | 22.6502 .. 26.0002 | 22.6500 .. 26.0000 | rounding only | HELD (lift door) |
| GF-15, 1F-01, GF-08, 1F-10 | 56.0131 / 51.415 / 152.0505 .. 178.805 / 48.94 .. 52.29 | unchanged | none | as before |
| shaft GF / 1F (2 lines x 2 codes) | T-173 48.52 .. 62.01 / 42.48 .. 47.67 | CITED T-173 (reproduced) | owner method HELD (Q-72) | HELD |
| 11 wet-room tile lines (blank, BLOCKED_RFI) | no figure | **307.9616** (= T-209 A per room, Q-48 A) | the ledger replaces a blank | ASSUMED - OWNER-APPROVED |
| 6 wet tile lines (annex GF-02 / 03 / 05 / 06; GF-10 / 11) + 4 annex dry lines + 17 wet plaster lines + ST-2F + pantry | blank | blank | G2 / Q-54 B, T-088, plaster-under-tile, D-T173-1 | HELD |

Totals per code (plaster = paint; lines with a figure): candidate **166.8792 determinate + 8 HELD 529.4667 .. 595.0479**
(= T-211) -> ledger **217.2082 determinate + 7 HELD 486.0931 .. 551.6016**; together 696.35 .. 761.93 -> **703.30 ..
768.81 m2** (+6.96 lo / +6.88 hi). Wall tile: 0 -> 307.96 m2 on 11 of 17 lines. The 1F-09 tile figure is 23.22 against
T-209's 23.33: D-1F-07 at the census frame width 0.80 (T-237 rule d) instead of the 0.75 rebate face, -0.110 m2, named.

**Drawing-derived method, beside (dwg columns):** the 18 DCR-6 faces of T-237 are carried by face, HELD BLANK on D-39
item 3 (annex also Q-54 B), never at a guessed roof level: 16 of them have a straight face here; the other two (T-250
s.3d) are 1F-03 / 1F-W23 (label swap: the face is 1F-02's at the 1F-W23 free end) and 1F-11 / 1F-W25 (curved bay stub,
inside 1F-11's off-line wall metres). Beyond the 18 (which are only the faces T-237 could join to a register wall):
every face of a room lying 100 % under a finished roof mark (T-128 share 1.0) is HELD on DCR-6 too, and the faces of
the seven split rooms (GF-07 / 08 / 15 / 16, 1F-09 / 10 / 13) are HELD with the room share named, because which faces
lie under the roof is in no merged ledger. Only rooms wholly under a slab carry a drawing figure (HELD (BOUNDED) on the
floor build-up b 0 .. 0.10).

**RULE_DIFFERENCE, outside every total:** W03 is deducted by the finishes on the room-side glass line (T-128 6.731;
drawing 6.7291, Checker 6.7294) and kept on the window line at Q-38 A 6.5675: +0.1635 m x 3.65 = 0.597 m2 (owner method),
named on the GF-08 and GF-15 glazing pieces; no quantity moves.

## 4. Statuses

Face lengths DRAWING-CONFIRMED (T-250 geometry, Checker re-walk 2026-10-24 10:40 on W03). Owner method per face: VERIFIED
on GF-15 (Checker 02:40 / 16:11) and the 8 non-W17 faces of 1F-11 (Checker 18:05), ASSUMED - OWNER-APPROVED (G1) on the
other determinate faces, HELD (BOUNDED) where an opening head is not printed, HELD blank with the item elsewhere. Nothing
released, nothing VERIFIED by this task. No owner question (ERS s.2.7 not met: every open item is already a named
designer / owner item: D-39, Q-54 B, Q-72, T-088, plaster-under-tile).

## 5. Engine vs freelancer

The freelancer prices internal plaster 1,151.14 m2 net (1,209.39 gross) and paint 1,191.13 m2 net with one height per
storey and half deductions (T-211 s.3). Not compared as a whole: the candidate's plaster / paint lines still carry 7
HELD ranges and 25 blanks (whole-line rule). What the ledger changes for the comparison: 4 room lines move by named
openings, the 1F-11 line can no longer be released at 59.45 while T-238 holds W17, and the wall-tile item goes from 17
blanks to 307.96 m2 on 11 rooms (his wet-wall figures per room are in T-209 RECONCILIATION: height 3.00 vs Q-48 A
3.65 / 3.35 and no opening deductions, RULE_DIFFERENCE). Verdict proposals: 1F-04 / 2F-03 / 1F-13 ENGINE (candidate)
WRONG on a stale held head, ledger right by the merged T-201 / T-238 heads; 1F-11 ENGINE WRONG to release (T-238 holds
the archivolt); wet tiles ENGINE_BLOCKED / LEDGER_DETERMINATE.

## 6. For T-244 (consumer shape) and for the Checker

T-244 takes FACE_TO_LINE_LEDGER_T292.csv (face x item: line id via engine room, length, owner status and net, drawing
status and net, held item, rule difference) and LINE_SUMMARY_T292.csv (per line: candidate figure, ledger figure, causes,
residual) with LINE_CAUSES_T292.csv (per opening, line deduction vs ledger deduction). Re-measure: (1) 1F-04 W24 and 2F-03
W29 heads on T-201's sheets (sill / head) and the two nets 52.0051 / 57.775; (2) 1F-11: the W17 piece (3.286 m off-line
glazing, cap 10.024 from T-238) and that the other 8 faces keep 59.4511 + 11.008 - 10.024 .. 11.008 arithmetic; (3) one
wet room by hand (GF-12: 7.414 x 3.65 - D 0.80 x 2.20 - W 0.60 band = 25.3011); (4) random face rows from the csv
against T-250 FACE_LENGTH.

## 7. Rule, test, lesson

- R-T292-1 (face_line_ledger.py, any villa): drawn face lengths only; one finish owner per face and layer; a face binds
  once per item code to its room's line (declared shares or refused); statuses with held items, never 0; one opening once
  per room side; closures per room (m), per line (m2) and faces vs lines; the line - ledger difference split into
  named opening causes only.
- Tests (tests/t292_face_line_ledger, villa P hand fixture, not Alsenan): normal (room 38.67 = 12.00 + 7.11 + 10.56 +
  9.00; wet 19.92; held window 8.40 .. 12.00; one line holding two rooms by declared shares; rotation / order invariant);
  adverse (face in two lines, held face as 0, schedule / text / census / register / window width as a face length, mm,
  tiled face painted, exterior face plastered, open side finished, opening twice, open room closure, unexplained
  residual, VERIFIED without run, owner-approved without source); Alsenan pins (byte-identical rebuild, csv a4dc01dd,
  132 lines once, closures 0, 21 rooms = T-237 part 4, roof faces held blank, the named moves, no coordinates).
- Lesson (ERS s.7, proposed): "a released room line (1F-11, VERIFIED 59.45) kept an opening deduction that a later merged
  ledger (T-238) holds | the room line was built before the opening ledger changed and no one re-bound the opening to
  the line | bind each opening deduction to its face and line by id, so a merged change to one opening re-opens exactly
  the lines that carry it | tests/t292_face_line_ledger | OPEN until T-244 integrates".
