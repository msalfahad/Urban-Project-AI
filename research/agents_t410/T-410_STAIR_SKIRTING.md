# T-410 Stair skirting B7-07 zigzag / B7-08 sloped, side by side, every flight and landing (development villa; method every villa)

Worker 2 (lane A), 2026-10-31. Research files `research/agents_t410/*` and `tests/t410_stair_skirting/` only; no
engine, rule, knowledge, method, registry or candidate file touched; no candidate quantity changed (lane I proposal in
section 6). ERS applied (s.2.1 physical element first, s.2.2 evidence, s.2.4 reconciliation, s.4 rule + test, s.7
lesson). Rules: UP-STAIR-010 / -011 (library 1.4.0, both owner-confirmed), UP-VOCAB-005 (توشيح = stair skirting),
UP-STAIR-012 / -013, owner stair rules S-9 (never generate winders; release each quantity on its own evidence; HELD stays
blank), UP-SKIRT-001 1.4.0 (room skirting), URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1, WORKFLOW_CONTROLS s.5. No image,
client name, title text or workbook row text is copied here.

## 0. What was read

| Source | Used for |
|---|---|
| Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip (architectural DXF, sha ab54dd55), decoded into `.work/private` only, read BY HANDLE | wall faces (layer 1), windows (layer W), riser lines and bands (layer 5 / 2) of ST-01, D1, ST-02, ST-03 on the GF / 1F / 2F plans |
| research/agents_t184 (MERGED; riser counts, goings, Q-46 A) | flight counts and sizes (cited, not re-derived) |
| research/agents_t164 + agents_t393 (MERGED; railing runs) | which side of each flight is guarded (RL-05 .. RL-11) |
| research/agents_t398 (MERGED) | ST-02 curved flight UNRESOLVED (RFI-S27) |
| data/registry/OWNER_RULE_REQUESTS.json ORR-007; OWNER_QUESTIONS_ANSWERED (searched: no answer on the form) | which form a project takes is an open owner rule request |
| Freelancer FIN workbook (23.6 MB, over the connector limit): its stair-skirting rows read from the Drive search content snippet (read-only) | his unit and counts (section 4) |

| r2: P7757.dxf column layer S-COL.BON, every closed outline beside every side line (COLUMN_CENSUS_T410.csv) | column faces on every side (rule R-T410-4) |
| r2: Drive "Alsenan chalet project" ST7757 dxf.dxf (sha 9f9d1179), decoded into `.work/private` only, T-108 translations (GF 202.33 / 841.64 m, 1F 208.46 / 841.64 m) | the proud columns cross-read on the structural plan (same outline and size within 3 mm) |

T-393 reproduced first from the same DXF (`t393_alsenan.py`): unchanged output.

## r2 (2026-11-01, Checker gate e on r1): the column layer read on every side

The r1 table read wall faces on layer 1 only and called two stretches "no wall face drawn"; columns live on S-COL.BON.
r2 reads that layer beside EVERY side line (28 side lines on the GF / 1F / 2F plans + the RS-C arc): 5 outlines stand
PROUD of the side line (0.050 each), 9 FLUSH readings (8 outlines (inside the wall thickness, the wall line drawn across them: no change),
1 CROSSES a side at its end (2FC6 at the RS-LD east edge: its body, not a face), 0 on any OPEN side, 0 on the RS-C arc
(2FD2 lies beyond the arc's end angle). Two INSERTs on S-COL.BON are door blocks (D120 3FF, D315 339; contents on
layer D), not columns: a drafting layer slip, recorded, no face. Changes, by handle:

| Stretch | r1 | r2 | Effect |
|---|---|---|---|
| RS-LD.S2 (south, 336 end -> landing edge AF5) | UNKNOWN 0.550, "no face drawn" | WALL face column 2FC6 (0.600 x 0.250, ST 374), 0.050 proud: 0.550 + 1 return 0.050 at the 336 end (the east end runs 0.050 past the edge: no return on the landing) = **0.600 DRAWING-CONFIRMED** (horizontal, form-independent) | landings 1.800 -> **2.400 lm** (+0.600, +33 %) |
| RS-S.S1 (south outer, s 0.200 .. 1.000) | part of UNKNOWN 1.000, "no wall face" | WALL face column 2FD2 (0.800 x 0.250, ST 380), 0.050 proud of the flight edge A7, 3 risers (s 0.3 / 0.6 / 0.9), 1 return 0.050 at the 336 end: **HELD-FORM**, zigzag 1.332143 / sloped 0.978571 | form-held figures +1.332 / +0.979 |
| RS-S.S0 (s 0 .. 0.200) | part of the same UNKNOWN | UNKNOWN 0.200, 1 riser (s 0): neither layer draws a face, only the A7 / A9 band (RL-09); the 0.050 west return of 2FD2 waits on it | UNKNOWN 6.066 -> 4.716 m plan |
| MS1-L.W1 (west, s 0 .. 1.650) | WALL, one stretch | split at column 2FBD (0.250 x 0.500, ST 36B), 0.050 proud over s 0.400 .. 0.900, both ends on the wall face: 2 returns = +0.100 lm in both forms | +0.100 |
| MS2-L.W1 (west, s 0 .. 2.250) | WALL, one stretch | split at column 3005 (1F) / 2F78 (2F, stacked; one face), ST 691, 0.050 proud over s 1.000 .. 1.500: +0.100 lm | +0.100 |
| MS1-LD.N (cause only, status HELD unchanged) | "broken over 1.247 m" (2AD lies beyond 21B, off the landing) | 0.103 wall (2AB) + 0.900 opening (3FD / 3FE, door block D120 3FF in it) + 0.147 wall (26F / 2AC) = 1.150 | none |

The general rule (R-T410-4, section 7) is enforced in code: `check_faces` refuses a "no face" stretch that a column face
overlaps, a proud column inside a stretch not marked face 'column', and returns missing or counted twice.

Cross-trade notes (not this task's quantity; owner trade A unless named):
- B7-02 tread / landing marble: the four proud faces stand 0.050 INSIDE the drawn tread width (riser lines B43 .. are
  drawn through the column to A7): RS-S treads 1.150 -> 1.100 clear over s 0.200 .. 1.000 (4 treads notched, 0.800 x
  0.050 = 0.040 m2; risers at s 0.3 / 0.6 / 0.9 each 0.050 shorter = 0.150 lm of riser); RS-LD 0.550 x 0.050 =
  0.0275 m2 of landing; MS1-L 0.500 x 0.050 = 0.025 m2; MS2-L 0.500 x 0.050 = 0.025 m2. Total 0.1175 m2 of stone that a
  full-width tread / landing measure would overstate (pieces still cut from full slabs: procurement unchanged).
- B7-09 railing RL-06 (T-393): the RS-LD east side's first 0.050 is the body of 2FC6 (CROSSES), so a guard on that edge
  runs 1.100, not 1.150, if it stops at the column.

## 1. Physical element and the engineering question (ERS s.2.1)

A stair skirting is a strip fixed to a WALL face along a flight or an intermediate landing, at the treads. It exists only
where a wall face stands beside the stair at that height: an open side (balustrade B7-09, floor-edge guard, or an
unguarded edge) has nothing to fix it to and is never skirted; a landing at floor level is the room's skirting (B3-06).
Its length depends on the FORM: zigzag (follows every riser and going: sum of rises + goings, UP-STAIR-010) or sloped
(along the rake: hypot(plan run, total rise), UP-STAIR-011). Both rules are owner-confirmed because both forms are used;
which one a project takes is a project answer (ORR-007, still OWNER_RULE_REQUEST; no drawing on the set details it). So
every sloping wall stretch is **HELD (form)** with both form-conditional figures beside the blank; a horizontal stretch
(landing at one level) is the same in both forms and does not wait on the form.

A wall side is established where a wall face is drawn on the side on every plan that cuts the element's storey; a
stretch where an opening is drawn in that face (solid at the cut, or hidden above it) is HELD: the opening's sill / head
against the flight's level is not printed (the T-296 sill principle carried to stairs). Riser positions are the drawn
ones (S-9 (1): goings counted from the drawing, not n-1 by default).

## 2. Result: side table (a), lm (SIDE_TABLE_T410.csv, 33 stretches)

| Element | Side | Class | Plan | Risers | Zigzag | Sloped | Quantity / status | Evidence / cause |
|---|---|---|---|---|---|---|---|---|
| ST-01 MS1-L GF -> +2.667 | west shaft wall | WALL | 0.400 + 0.500 col + 0.750 | 2 + 1 + 3 | 2.750 (incl. 2 returns 0.100) | 2.039 | HELD-FORM | face 298; column 2FBD 0.050 proud (r2) |
| | west | HELD | 1.050 | 4 | (1.717) | (1.234) | HELD | GF window 352-354 in the face beside treads +2.00 .. +2.67 |
| | east well | OPEN | 2.700 | | | | not skirted | RL-07 MS1-L |
| MS1-U +3.50 -> 1F | east lift wall | WALL | 0.950 + 1.450 | 4 + 5 | 1.617 + 2.283 | 1.111 + 1.696 | HELD-FORM | GF 21B / 21C, 1F B16 |
| | east | HELD | 0.900 | 3 | (1.400) | (1.052) | HELD | GF hidden opening 33C / 33D above the cut, height not printed |
| | west well | OPEN | 3.300 | | | | not skirted | RL-07 MS1-U |
| MS2-L 1F -> +7.516 | west shaft wall | WALL | 1.000 + 0.500 col + 0.750 | 4 + 1 + 3 | 3.694 (incl. 0.100) | 2.737 | HELD-FORM | 1F AF1, 2F 12B7; column 3005 / 2F78 0.050 proud (r2) |
| | west | HELD | 1.050 | 4 | (1.722) | (1.230) | HELD | stacked 1F / 2F windows C5A-C / 12CF-D1 beside treads +7.18 .. +7.52 |
| | east well | OPEN | 3.300 | | | | not skirted | RL-07 MS2-L |
| MS2-U +7.684 -> 2F | east lift wall | WALL | 3.300 | 12 | 5.316 | 3.867 | HELD-FORM | 1F B16, 2F 129A, no opening |
| | west well | OPEN | 3.300 | | | | not skirted | RL-07 MS2-U |
| D1 lobby +0.30 -> +1.00 | east lift wall | WALL | 0.900 | 4 | 1.600 | 1.140 | HELD-FORM | GF 21B |
| | west well band | OPEN | 0.900 | | | | not skirted | RL-08 |
| MS1-LD +3.50 | east lift wall | WALL | 1.150 | 0 | 1.150 | 1.150 | **1.150 DRAWING-CONFIRMED** | GF 21B, 1F B16 |
| | north | HELD | 1.150 | | | | HELD | 0.103 wall + 0.900 opening (3FD / 3FE, door block 3FF) + 0.147 wall; 1F window above; head vs +3.50 not printed |
| MS1-T winder corner | west 1.200 + north 1.150 | HELD | 2.350 | 5 winders, rise 0.833 | | | HELD | 5 risers on A-A vs 4 wedges on plans (T-184); never generated (S-9) |
| MS2-LD +7.516 | west 1.200, north 2.500, east 1.200 | HELD | 4.900 | closing riser 0.168 | | | HELD | MS2-TR position not drawn (T-184 / T-393); north face also 1.000 window opening |
| ST-02 RS-S +2.929 -> +4.696 | south outer | UNKNOWN | 0.200 | 1 | | | UNKNOWN | neither wall nor column face (both layers read): only the 50 mm outer band (RL-09 role open) |
| | south outer | WALL (column) | 0.800 | 3 | 1.332 (incl. 1 return 0.050) | 0.979 | HELD-FORM | column 2FD2 0.050 proud of A7 (r2); ST 380 |
| | south outer | WALL | 2.000 | 7 | 3.125 | 2.321 | HELD-FORM | GF wall face 336 |
| | north void | OPEN | 3.000 | | | | not skirted | RL-05 |
| RS-LD +4.696 | south | WALL | 0.650 | 0 | 0.650 | 0.650 | **0.650 DRAWING-CONFIRMED** | 336 to its end |
| | south | WALL (column) | 0.550 + return 0.050 | 0 | 0.600 | 0.600 | **0.600 DRAWING-CONFIRMED** | column 2FC6 0.050 proud where 336 stops (r2); ST 374 |
| | east | OPEN | 1.150 | | | | not skirted | RL-06 (D-23) |
| RS-A +4.696 -> 1F | east / west | OPEN | 1.200 each | | | | not skirted | RL-06 / RL-05 |
| RS-C curved | outer, developed arc r 2.731 x 94.7 deg | UNKNOWN | 4.516 | 12 | | | UNKNOWN | outer band RL-09 role open; flight UNRESOLVED (T-398, RFI-S27); never a chord |
| | inner | OPEN | 2.531 | | | | not skirted | RL-05 |
| ST-03 E1 +0.15 -> +1.00 | south wall | WALL | 1.200 | 5 | 2.050 | 1.471 | HELD-FORM | GF wall face 15A |
| | north edge | OPEN | 1.200 | | | | not skirted | RL-11 (guard held) |

Annex: no stair is drawn there (T-184 inventory: ST-01, D1, ST-02, ST-03 only); no row.

**Totals (r2).** DRAWING-CONFIRMED (form-independent, landings): **2.400 lm** (MS1-LD 1.150 + RS-LD 0.650 + 0.600;
r1 1.800). Sloping wall stretches with complete geometry, form HELD: zigzag **23.767 lm** / sloped **17.360 lm** (r1
22.235 / 16.181: + 0.200 column returns on MS1-L / MS2-L + the RS-S column stretch 1.332 / 0.979); 54 risers on them.
HELD: 11.400 m plan (11 flight risers + the 5 winders + the closing riser), unchanged. UNKNOWN: 4.716 m plan (13 ST-02
risers: 1 on RS-S + 12 on RS-C; r1 6.066 / 16). Nothing is released; HELD and UNKNOWN stay blank, never 0.

Hand checks (independent of the code): MS2-U zigzag 3.30 + 12 x 0.168 = 5.316, sloped hypot(3.30, 2.016) = 3.867;
MS1-L wall part 1.65 + 6 x 0.16667 = 2.650, sloped 1.65 x hypot(2.70, 1.6667) / 2.70 = 1.939; E1 1.20 + 5 x 0.17 =
2.050, hypot(1.20, 0.85) = 1.471; RS-S wall part 2.00 + 7 x 0.160714 = 3.125. r2: RS-S column part 0.80 + 3 x 0.160714
+ 0.05 = 1.332, sloped 0.80 x hypot(3.00, 1.767857) / 3.00 + 0.05 = 0.80 x 1.160714 + 0.05 = 0.979; RS-LD 0.65 + 0.55 +
0.05 = 1.250. The totals pin test re-adds them.

## 3. Checks of acceptance (b)

- 0 sides both skirted and guarded: every OPEN row names its railing run; no WALL / HELD row does (refused in code; pin
  test over the table).
- Every ST-01 riser has exactly one wall side: 50 flight risers in WALL / HELD stretches + 5 winders + 1 closing riser =
  56 = 10 + 5 + 12 + 1 + 12 + 12 + 4 (pin test).
- Landing skirting is not room skirting: MS1-LD, MS2-LD, RS-LD are intermediate landings (stair elements); the 1F / 2F
  arrival landings are floor-slab panels (T-184 R-STAIR-LAND-1) and stay in B3-06. Cross-trade note for lane I: the
  room line "1F living + shaft" (T-296) carries a HELD "base along the stair shaft" piece; when B7-07 / B7-08 lines are
  wired, that held piece must be retired or bound to these stretches, never both (one physical base, one owner).

## 4. Freelancer comparison (c), quantities only

His stair-skirting rows are in PIECES (unit 'count' on his cover sheet), one piece per step with a nominal 1.00 in the
length column: entrance stair 5, main stair 63, inner (round) stair 28, total 96 pieces. The owner's unit is lm
(UP-STAIR-010 / -011): **RULE_DIFFERENCE on unit**; his 1.00 per piece is not a measured path (the zigzag path per step
here is going + rise = 0.47 m), so his rows are compared by count of skirted steps, not in lm.

| Stair | His pieces | Ours: risers on a wall side | Difference | Verdict proposal |
|---|---|---|---|---|
| ST-03 entrance | 5 | 5 (one wall side, south) | 0 | AGREE on count |
| ST-01 main (+ D1) | 63 | 56 (39 geometry-complete + 11 held + 5 winders + 1 closing riser) | +7 his | UNRESOLVED: 63 equals his own tread count of the same stair, not a drawn count (T-184: 52 risers + D1 4); one piece per step, so one side per step, which agrees with one wall side per flight |
| ST-02 round | 28 | at most 23, at least 10 (r2: 10 on a drawn wall / column face = 7 on 336 + 3 on column 2FD2; 1 UNKNOWN on RS-S + 12 UNKNOWN on RS-C; r1 7 + 4 + 12); RS-A 5 risers have NO wall side | +5 at least | ENGINE_RIGHT for RS-A (both sides guarded: RL-05 void band and RL-06 floor-edge guard, T-164 / T-393 merged); the curved part UNRESOLVED (outer band role open) |

His one-piece-per-step practice reads as a zigzag (stepped) piece per step; it is a contractor's practice, not an owner
rule, so it does not settle ORR-007 (ERS: never adopt the freelancer's convention as the rule).

## 5. What stays open (designer / owner facts; no owner question raised)

ERS s.2.7 is not met for a new question: the form is already an open owner rule request (ORR-007, registry) and the
geometry gaps are designer facts. Proposed rfi/B rows (drafts, nothing sent; the Lead places them):

1. Stair-shaft windows (GF 352-354, 1F C5A-C, 2F 12CF-D1, west face of ST-01; GF hidden opening 33C / 33D, east face):
   sill and head levels against the flights beside them (the 1F window sill at +6.50 would sit below the MS2-L treads at
   +7.18 .. +7.52 if it is the usual 1.00 m: a possible stair / window clash). Affects 3.000 m plan of skirting (11
   risers), also plaster / paint in the shaft.
2. ST-01 north face at MS1-LD (+3.50) and MS2-LD (+7.516): the GF opening / 1F window in that face, head level.
3. ST-02 outer 50 mm band (RL-09 / A7-A9): guard, string or wall finish (decides whether RS-C and the first 0.200 m of RS-S
   have a skirting at all, and the 0.050 west return of column 2FD2), already RFI-S27 / RL-09.
4. ORR-007 stays with the owner (registry): zigzag or sloped for this project. Size of the decision on the geometry-complete
   stretches: 23.767 - 17.360 = **6.407 lm** (37 % of the sloped figure; r1 6.054).

## 6. Lane I proposal (no candidate change in this task)

New lines under B7-07 / B7-08 (one family line set, never both forms valued): per stretch of SIDE_TABLE_T410.csv, the
three horizontal landing stretches valued 2.400 lm DRAWING-CONFIRMED (after Gate A), every sloping WALL stretch a blank
HELD line carrying its zigzag and sloped figures in the note, HELD / UNKNOWN stretches blank with their cause; OPEN sides
listed as not skirted (0 by rule). When the owner answers ORR-007 the sloping lines take the matching column, no
re-measure. Retire / bind the B3-06 "stair shaft base" held piece at the same time (section 3).

## 7. Rule, test, lesson

- **R-T410-1** (proposed, research, any villa): a stair skirting exists only on a wall side; each flight side is cut
  into stretches by plan run (WALL / HELD / OPEN / UNKNOWN) that cover the run once; zigzag = plan + rises of the risers
  standing in the stretch, sloped = plan x hypot(run, rise) / run; a sloping stretch with no fixed form is HELD with both
  figures beside; a horizontal stretch is form-independent. **R-T410-2**: an opening drawn in the wall face beside a
  flight (solid or hidden) holds that stretch until its sill / head is established. **R-T410-3**: curved sides on the
  developed arc, never a chord; winders never generated (S-9). **R-T410-4** (r2, from the Checker's gate e finding;
  proposed, research, any villa): a wall side is ANY vertical finished face on the side, a wall face OR a column face; read
  every layer that draws one (wall layer AND column layer) before classing a stretch "no face"; a column standing proud of
  the wall line by p adds a return p at each end that meets a WALL face (horizontal, form-independent, counted once), an
  end meeting a HELD / UNKNOWN stretch leaves its return held there, an end beyond the element has none.
- Tests `tests/t410_stair_skirting` (15 pass): Villa K410 hand fixture (zigzag 1.680 / sloped 1.203676 on the wall part,
  landing 1.400 confirmed, curved 2.827433); adverse: curved side as chord refused, open side skirted refused, winder
  generated refused, held as 0 refused, held without cause refused, mm as m refused, gap / overlap / short cover / double
  binding refused, stretch outside the run refused, split-point invariance, mirror / rotation invariance; Alsenan pins
  (reproduces from the committed sides file, totals hand-checked, no side guarded and skirted, 56 ST-01 risers).
  r2 (+6 tests): K410 second stair (column 0.050 proud on a flight: zigzag 1.040 / sloped 0.825578 with 2 returns; landing
  column running past the edge: 0.700 + 0.500 + 0.050 = 1.250); adverse: column face classed 'no face' refused, proud
  column in a 'wall' stretch refused, returns missing / double-counted refused, 'no face' flag on a non-UNKNOWN stretch and
  returns on a HELD stretch refused, projection in mm refused; Alsenan pin: the column layer is read on every side, the 5
  proud outlines each cross-read on the ST plan, RS-LD.S2 0.600, RS-S.S1 HELD-FORM with 3 risers.
- Lessons-register row proposed:

| 2026-10-31 | a side table read the wall layer only and called two column faces "no face" | wall faces were taken from layer 1, columns live on S-COL.BON | a wall side is any vertical finished face (wall OR column) on the side; read every layer that draws one before classing a stretch UNKNOWN; a proud column adds its returns (any villa) | tests/t410_stair_skirting (column adverse) | T-410 r2 |
| 2026-10-31 | B7-07 / B7-08 were idle arithmetic with no side table: nobody had said which side of which flight has a wall, and the form question (ORR-007) blocked everything | the form was treated as a precondition of the whole item; wall sides and openings beside flights were never read | separate geometry (side table, form-independent) from the form (one owner answer); hold only what the form decides; landings release on their own (S-9 (4)); openings in a face beside a flight hold that stretch (any villa) | tests/t410_stair_skirting | T-410 |

## 8. Self-gate and what is missing

self-gate: a (research + tests only; no engine / rule / candidate file) c (non-Alsenan hand fixture, adverse cases) d
(reproducible: `python3 -I research/agents_t410/t410_alsenan.py --dxf <P7757.dxf> --write`; `--check` without private
input) f (no new item code, nothing wired) h (no client data, no drawing content beyond handles and lengths) PASS.
r2 self-gate: a (research + tests + CODEMAP only) c (K410 column cases, adverse) d (`--write` from P7757.dxf; `--check`
re-runs the table AND the column census / face check without private input) f (nothing valued beyond the landings) h
(handles, run positions and projections only; no coordinates, no drawing text) PASS.
Missing: ORR-007 (form); the shaft windows' sills / heads; the ST-02 outer band's role; MS2-TR position; the skirting
height and material (not printed; not needed for lm).
