# T-271 Ceilings r2: the room-by-room ceiling ledger rebased on the verified floor pieces (Alsenan; any villa)

Worker 2 (lane A), 2026-10-24; **r2b 2026-10-24 21:30 UTC** (Verifier 19:59 REJECTED narrow, gate e / h: the GF
light-well no-ceiling area; section 6 below gives the correction, the figures in sections 1 - 5 are restated). Research piece, unwired: no engine, rule, frozen, registry or candidate file changes; no
released or candidate quantity moves. Integration is lane I's (one candidate line family for ceilings) after the
Checker's Gate A. Development villa, not an accuracy claim. Drawings named by Drive folder and title only.

## 0. Inputs and method

| Input (Drive "Alsenan chalet project") | sha256 | Used for |
|---|---|---|
| P7757_DXF_COMPRESSED.zip / P7757.dxf | ab54dd55... | ARCH_TAKEOFF_V2.9 run (the released architectural method): the floor faces = the floor pieces the Checker re-measured (T-180 floor batches 2026-10-23 21:15 .. 2026-10-24 01:12, T-269), the engine's own FIN.CEILING lines, the floor strips; the pantry split line B3 / AD |
| "ST7757 dxf.dxf" | 9f9d1179... | the three roof-slab plans: T-139 faces (`research/agents_t139/slab_faces.py`, classes in `PANELS.csv`), column-fit translation (`research/agents_t147/scripts/align.py`: 30 / 20 / 9 columns, spread 0.000 m) |
| merged ledgers | committed | CONC.BEAM ledger r2 (`research/agents_t252/LEDGER_T252.csv`, live rows: status and depth per member), T-110 register (span binding), freelancer FIN workbook sheet 'decor' (`tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json`, cells D13 .. D63, H31 / H65 / G31 / G65) |

Pipeline: `t271_extract.py <v29.pkl> <st_faces.json> <align.json> <P7757.dxf> ALSENAN_T271_INPUT.json <ST7757.dxf>` (areas,
lengths, ids, statuses only: no coordinates, no texts) -> `t271_alsenan_check.py` (stdlib) -> `CEILINGS_T271.csv`
(296 rows: one per piece and surface), `RECONCILE_T271.csv` (piece -> ceiling, engine line, floor-piece status),
`FLOORS_T271.csv`, `VS_FREELANCER_T271.csv`, `STRIPS_T271.csv`, `summary.json`. Rules module `ceilings_r2.py`
(CEILINGS_R2: `overlay`, `free_edge`, `ledger`, `reconcile`). Tests `tests/t271_ceilings` (31: villa Z hand fixtures,
mirror / rotation 37 deg / translation / mm, adverse cases, the byte-for-byte rebuild of every committed output).

**Physical element (ERS s.2.1).** Per floor piece: what is built under the slab above it. (1) Horizontal gypsum decor
ceiling at decor level over the piece's own polygon (wall face to wall face), less what the slab plan above draws with
no ceiling plane (light well / lift X box), less the stair soffit over it (stair finish), less an open dome position
(Q-44 A); (2) wet-room board type; (4) vertical bulkhead faces where a beam piece lies inside the room below the
ceiling; (5) cove returns and drops at opening edges; (6) paintable gypsum; (7) concrete ceiling plaster. Soffits over
outside air stay apart (Q-68 C; candidate T-127 lines). Doorway strips are not ceiling pieces (head soffit = opening
reveal). OWNER MANUAL METHOD (Q-43 line + Q-48 A: ceiling 0.15 under a beam deeper than the 0.60 allowance -> face
D - 0.60) and DRAWING-DERIVED METHOD (ceiling 0.15 under the slab soffit -> face D - 0.16; no ceiling level printed,
D-40) are kept side by side; the second is a HELD candidate, never a total.

## 1. Result in engineering terms (m2 of horizontal ceiling unless stated)

| Floor | Released engine FIN.CEILING (29 lines, PROVISIONAL) | **R2 horizontal decor ceiling** | Freelancer decor rows | R2 vs freelancer | T-147 (r1) |
|---|---|---|---|---|---|
| GF | 198.514 | **189.723** (dry 142.542 + wet 47.181) | 232.81 (197.33 + 35.48) | -43.087 (-18.5 %) | 207.01 |
| 1F | 179.749 | **142.925** (dry 114.891 + wet 28.034) | 143.87 (112.96 + 30.91) | -0.945 (-0.7 %) | 137.63 |
| 2F | 24.900 | **30.526** (dry 24.976 + wet 5.550) | 32.90 (27.28 + 5.62) | -2.374 (-7.2 %) | 43.50 |
| **Villa** | **403.163** | **363.173** | **409.58** | **-46.407 (-11.33 %)** | 388.14 |

R2 vs the released engine: **-39.990 m2 (-9.92 %)** (r2 before the r2b correction: 362.282, -40.881, -10.1 %). Status: every horizontal area DRAWING-CONFIRMED (piece geometry =
the Checker's floor piece where VERIFIED; the slab-above overlay is this task's own, not yet independently verified);
dry gypsum by Q-57 A mod; wet-room board type HELD (no sheet specifies a ceiling board).

Separately, never added to the horizontal total (each with its status):

| Item | Quantity | Status |
|---|---|---|
| no ceiling: GF light well = S-OPENING outline 16.005 less the round flight 2.379 and the pocket 0.233 inside it (r2b) | 13.392 m2 | DRAWING-CONFIRMED (deducted once) |
| no ceiling: GF pocket between the walls and the stair's outer arc, S-OPENING X 54B / 54C (r2b; 0.233 inside the outline + 1.318 south band) | 1.551 m2 | DRAWING-CONFIRMED (deducted once) |
| stair soffits: GF stair zone under the GF-roof slab 7.402 (round flight 2.379 inside the light-well outline, south band 4.333, east flight 0.690; r2b) + GF round-stair strips 2.451 + 1F stair zone 10.725 (ST 1F-016) | 20.579 m2 | HELD (stair finish line) |
| under the open dome positions (Q-44 A; west 11.581 + 1.423 + 1.241, east 14.036 + 0.447 + 0.342) | 29.069 m2 | HELD (designer DCR-4), never 0 |
| 2F stair-hall ceiling over the stair box (finish / height not printed) | 12.974 m2 | HELD (Q-72 investigation) |
| pieces whose class is not established: GF garden band 9.101 + merged band 4.885 (P-2; may be one of the T-127 candidate soffits: not added, no double count), unlabelled GF spaces 3.600 + 1.560 | 19.146 m2 | HELD |
| stair / lift pieces (GF stair 12.475, three lift shafts 9.720) | 22.195 m2 | kept apart (no decor ceiling) |
| passage strips (GF OP-001 / OP-003 / OP-007 / OP-011, 1F OP-007 / OP-011, 2F OP-002) | 3.514 m2 | UNKNOWN (opening head or open-zone ceiling) |
| door strips (under a door head) | 3.600 m2 | no ceiling (reveal) |
| bulkhead faces, owner method (beam ledger r2 CALCULATED, D > 0.60): GF 17.198, 1F 12.039, 2F 0 | **29.237 m2** | ASSUMED - OWNER-APPROVED (Q-48 A + Q-43) |
| bulkhead faces, drawing-derived candidate | 160.148 m2 | HELD (D-40), not a total |
| bulkhead edges on CONFLICT / HELD / unregistered beams (B29, B21, GF-159 'with stair', CB2 x 5 rooms, 1F B6 BM-1F-030, CB10, 2F BM-2F-018) | 58.290 m | HELD (Q-61 C) |
| bulkhead edges over held-class pieces (garden band: B1, CB8; merged cell: B22, B27, CB8) | 16.163 m | HELD |
| drops / returns at opening edges (light well, pocket, dome openings) | 49.134 m | HELD (height) |
| cove / cornice runs, closed rooms (dry 153.411 + wet 135.229) | 288.640 m | HELD (no detail; never 0.10 m strips) |
| paintable gypsum, owner method (horizontal + owner bulkheads) | 392.410 m2 | ASSUMED - OWNER-APPROVED |
| concrete ceiling plaster | - | NOT SPECIFIED (no item, not 0) |

Paint: 392.410 vs the freelancer's "decor paint with cove light" 452.33 m2 = -59.92 (-13.25 %); like for like without
his cove strips 42.75 (409.58): -17.17 (-4.19 %).

## 2. Reconciliation in units (ERS s.2.4)

**Released engine -> R2 (-39.990 m2), by cause.** The engine line is 'floor face less the part under the void above'
(arch_measure.py FIN.CEILING, O-P8-02).
- GF -8.791 (r2b; r2 said -9.682 on a wrong cause): the engine deducts the void outline 16.005, which IS the slab
  plan's S-OPENING light-well outline (5.820 x 2.750, to the mm; the r2 claim that the slab opens 23.237 is withdrawn,
  section 6). Beyond it the engine ceils what the slab plan draws as stair under the slab or as a second opening: the
  south band stair 4.333 + east flight 0.690 (stair soffit) **-5.023**, the pocket's south-band part 1.318 (S-OPENING
  X 54B / 54C, no ceiling) **-1.318**, the round-stair strips GF-131 / GF-132 / GF-145 (stair soffit) **-2.451**.
  Inside the outline the engine and R2 agree that 16.005 is not decor ceiling (R2 splits it: 13.392 no ceiling,
  2.379 round flight = stair soffit HELD, 0.233 pocket). The east-strip slab 0.891 is decor ceiling in both. Every
  other GF room line = R2 to 0.000 m2.
- 1F -36.824: the 1F stair zone 10.725 is a stair soffit, not a decor ceiling **-10.725**; open dome positions
  **-29.069** HELD; the dressing 1F-RFFE7AF (enclosed dry interior space, T-223 rule; the engine has only an
  ARCH.SPACE line) **+2.970**.
- 2F +5.626: the engine holds the whole 2F stair face (BLOCKED_RFI); R2 ceils its lobby part 5.626 (18.600 less the
  stair box 12.974 HELD).

**Freelancer -> R2 (-46.407 m2; r2 -47.298).**
- GF dry -54.788: his reception + dining + entrance 147.96 (D13 + D15) vs R2 open part 93.177: light well 13.392 +
  pocket 1.551 (no ceiling: the S-OPENING outlines of the slab plan; his row ceils them), the stair zone under the
  slab 7.402 + the round-stair strips 2.451 (stair soffit), pantry 11.755 (in R2's wet
  set, Q-37 A), garden band + merged cell 13.986 (HELD class), the Checker's doorway-zone 1.100 and OP-003 piece 1.964
  (floor strips, not ceiling pieces) and **+1.182 not traceable** (his row has no dimensions; T-147's own region gave
  147.898). Diwaniya 24.940 vs 24.84 (+0.4 %), master bed room 16.550 vs 16.66 (-0.7 %), driver 7.875 vs 7.87: agree.
- GF wet +11.701: the pantry 11.755 he prices dry; the rest -0.054 (agree).
- 1F dry +1.931: living +12.262 (R2 51.222: the double-height ceiling over the light-well footprint at the 1F roof,
  which he omits, less the stair zone and the east dome HELD), bed rooms 1-4 -13.301 (west dome 11.581 + east 0.342
  HELD; -1.378 room sizes, T-208 UNRESOLVED -1.9 %), dressing +2.970 (no row of his).
- 1F wet -2.876: dome openings over three baths 3.111 HELD; the rest +0.235.
- 2F dry -2.304: maid room 19.350 vs 19.58 (-0.230); his corridor 7.70 vs the lobby 5.626 (-2.074; the stair box is
  HELD apart). 2F wet -0.070.

**Piece -> ceiling.** `RECONCILE_T271.csv`: every one of the 38 V2.9 faces (GF-RC99C2A split at B3 / AD into the open
part 117.974 and the pantry part 8.955 = T-269) is in the ledger once; piece = horizontal + no-ceiling + stair soffit +
dome + held part, residual 0.000 m2 on every piece. Overlay line-work residuals (piece area not covered by a slab face:
drafting gaps of the structural linework) are named per row (largest +0.0124 m2, 1F bath 1F-R48CDA5) and stay in the
ceiling (the room is roofed). Chord residual of the split GF face (polygon 126.9286 vs exact 126.9277): +0.0009 m2.

Bulkheads vs T-147 (32.78 -> 29.237 m2): +0.6 % on every crossing edge (R-CEIL-R2-3 below: Majlis CB6 now 8.000 m x
0.15 = **1.200 m2 = the printed 4.00 room width**, was 7.952 / 1.193); -4.38 GF where beam pieces now lie over the
held garden band / merged cell (B22, CB8, B27: 16.163 m of edge HELD with the class) and over the smaller pantry and
open parts; +0.84 1F (B19 pieces bound on both slab faces). Beam statuses: every member T-147 used has the same status
in ledger r2 (CB3 BM-GF-018 CALCULATED, CB2 / B21 / B29 / 1F B6 BM-1F-030 / CB10 CONFLICT, BM-2F-018 HELD).

## 3. Who is right (proposals for the Checker)

| Item | Engine (released) | Freelancer | R2 | Proposal |
|---|---|---|---|---|
| GF light well (r2b) | deducts 16.005 = the S-OPENING outline | ceils it | no ceiling 13.392 + round flight 2.379 (stair soffit) + pocket 0.233 = 16.005 | ENGINE_RIGHT on the light-well outline (the r2 'engine partly wrong' is withdrawn); FREELANCER_WRONG (ceils an opening) |
| GF face GF-130 outside the outline, 7.232 (r2b) | ceils it | ceils it | stair soffit 5.023 HELD, pocket 1.318 no ceiling, decor 0.891 | R2: the stair under the slab is a stair soffit (stair finish line), the X-marked pocket is an opening; ENGINE_WRONG / FREELANCER_WRONG on 6.341, all three agree on 0.891 |
| GF round-stair strips, 1F stair zone | ceiling 13.176 | ceils GF part | stair soffit HELD | RULE: stair soffit belongs to the stair finish line (not decor ceiling) |
| dome positions 29.069 | ceiling | ceiling | HELD | UNRESOLVED (designer DCR-4: what closes the opening) |
| 1F dressing 2.970 | none | none | dry ceiling | R2 (T-223 rule, Checker 22:05) |
| 1F double-height ceiling over the light well | ceiling | omits | ceiling | ENGINE_RIGHT vs freelancer (1F roof slab closed over the void) |
| GF pantry 11.755 | ceiling (dry scope) | dry row | wet set | class by Q-37 A (area agrees) |
| 2F stair hall | BLOCKED_RFI | corridor 7.70 | lobby 5.626 + box 12.974 HELD | UNRESOLVED on the box (finish); lobby R2 |
| bulkhead faces | none | none | owner 29.237 m2 OA | missing category in both: R2 |
| cove 42.75 m2 | none | 0.10 m x 427.46 m | runs HELD | RULE_DIFFERENCE (no detail, Q-57) |

## 4. Rules and lessons (ERS s.4)

- **R-CEIL-R2-1** (proposed, any villa; **amended r2b**): a ceiling is a slab-side quantity built on the floor piece:
  the piece's own polygon less only what the slab plan above draws over it (opening, light well, stair zone, dome),
  each once with its own status; never 'ceiling = floor area'. A structural face bounded by beam / column / edge
  linework is NOT a slab opening because an opening tag sits in it: the opening is only the outline the slab plan
  marks as one (opening-layer outline with its X and / or VOID tag); a stair drawn under the slab (hidden treads) is a
  stair zone; the rest of the face is slab, classified by what is below it (`ceilings_r2.split_structural_void`).
  Tests: `test_void_and_stair_strip_deducted_once`, `test_open_dome_held_never_zero`,
  `test_void_split_deducts_the_outline_only` (4 transforms), adverse `test_adverse_openings_counted_twice_refused`,
  `test_adverse_tagged_structural_face_is_not_the_opening`, `test_adverse_outline_without_mark_or_mark_on_the_stair_refused`,
  Alsenan pin `test_alsenan_gf130_void_split_r2b`.
- **R-CEIL-R2-2** (proposed): a bulkhead follows its beam's ledger status; CONFLICT / HELD / unregistered / two-depth
  members give HELD edge, never a candidate value. Tests: `test_adverse_conflict_or_held_beam_never_gives_an_owner_face`,
  `test_unregistered_piece_held_or_junction`.
- **R-CEIL-R2-3** (proposed): a free edge is measured segment by segment against the wall faces; no tolerance is cut
  from the ends of a crossing edge (the T-147 buffered difference lost 2 x 12 mm per crossing edge, -0.6 %). Test:
  `test_hall_crossing_beam_and_conflict_beam` (8.000 m, all five transforms) and the Majlis CB6 1.200 guard.
- Lessons row proposed (section 7, r2b, the Verifier's wording): "a structural face bounded by beam / column linework
  is not a slab opening; the opening is the outline the slab plan marks (S-OPENING X + VOID tag) | T-271 GF-130 23.237
  vs 16.005 | R-CEIL-R2-1 amended | tests/t271_*" (worker's addition: hidden treads under the slab make a stair zone,
  not an opening and not a decor ceiling).
- Lessons row proposed (section 7): "Ceilings were called a missing category while the released run carries 29
  FIN.CEILING lines (403.163 m2, PROVISIONAL), 40.0 m2 (9.9 %; r2 40.9) above the drawing-derived ledger | the gap was copied
  from the r1 report, and the engine line deducts the architectural void outline and ceils stair zones and dome
  openings | R-CEIL-R2-1 + the 2026-10-24 gap-claim rule (a gap names the version it was measured on) | tests/t271_ceilings | OPEN: integration".

## 5. What is missing / held (no owner question: Q-57 A mod, Q-48 A, Q-44 A, Q-61 C, Q-68 C answer the method)

D-40 ceiling level (drawing-derived bulkheads HELD), DCR-4 dome openings 29.069 m2, the Q-61 C beams (58.290 m), the
held-class pieces 19.146 m2 (garden band class P-2; two unlabelled GF spaces), the 2F stair box top 12.974 m2 (Q-72
investigation), wet-room board type, cove / drop details, passage strips 3.514 m2 UNKNOWN. Not re-derived here: the
curved 1F room's edge (T-223), the 1F living floor split (T-269 / T-240).

**Checker re-measure (3 rooms + 1):** (a) bulkhead: GF Majlis GF-R7512EA 24.940 with CB6 BM-GF-030 (piece 0.20 x
4.00, ST GF-roof face GF-110) -> 1.200 m2; (b) wet: GF pantry part west of B3 / AD 8.955 with B27 BM-GF-048 (90 x 85,
ST face GF-142, S-BEAM lines 325 / 326) free edge 6.897 m -> 1.724 m2; (c) void (r2b): GF open part 117.974 less the light well 13.392 (S-OPENING 2CE / 2CF / 2D0 / 28A = 16.005, less the
round flight between the S-OPENING arcs 2DE r 1.5305 / 2DD r 2.7805 from 176 to 270 deg, 2.379, less the pocket 0.233),
less the pocket 1.551 (corner 28A / 283 outside arc 2DD, X 54B / 54C), less the stair zone 7.402 under the slab (round
flight 2.379 + south band 4.333 to tread 2C4 x 66.963 / landing + east flight to 2C8 .. 315, 0.690), less the strips
GF-131 / GF-132 / GF-145 2.451 -> 93.177 (r2 92.285 + the east-strip slab 0.891); (d) 1F bed room 1F-R0E919A 16.340 with B19 BM-1F-025
(ST face 1F-052, edges 6B1 / 6B2) and B25 BM-1F-027 (1F-075, edges 6BF / 6C0) -> 1.835 m2, and B6 BM-1F-030 CONFLICT (1F-024, edges 5CC / 5CD) 5.152 m HELD.

## 6. r2b: the GF light-well no-ceiling area (Verifier 2026-10-24 19:59, gate e / h)

**Finding accepted.** r2 deducted the whole T-139 face GF-130 (23.237 m2, class VOID+STAIR) as 'no ceiling'. GF-130 is a
structural face (polygonised from layers 1 / 5 / S-COL.BON / S-BEAM / S-BOUN), not the opening. Re-read on Drive
"Alsenan chalet project" / "ST7757 dxf.dxf" (sha 9f9d1179), GF-roof slab plan, and checked against the GF plan of
P7757_DXF_COMPRESSED.zip / P7757.dxf (column-fit translation GF (202.3333, 841.6415) m, spread 0.000 m on 30 columns):

| Element (ST handles) | What the slab plan draws | GF plan below (arch handles) |
|---|---|---|
| light well 2CE / 2CF / 2D0 / 28A, X 2D1 / 2D2, VOID tag 2D3 | S-OPENING outline 5.820 x 2.750 = 16.005; bottom 2D0 and diagonal 2D2 stop on the inner stair arc 2DE | the same outline HIDDEN (overhead) 4B0 / 4B2 / 4B3, 4B0 also stopping at the inner arc |
| round flight between the S-OPENING arcs 2DE r 1.5305 and 2DD r 2.7805, 176 .. 270 deg | 12 HIDDEN treads 2DF .. 2EA, curtail 2EB / 2EC at the flight foot, '8 dia 16/m' 5BC on the flight | treads 240 .. 256 (layer 5, below the cut), handrail arcs 239 / 23A .. 23F, curtail 258 / 25A |
| straight flight, south band y 38.048 .. 39.248 | HIDDEN treads 2BA .. 2C4 (x 63.963 .. 66.963), '(With Stair)' 1826, '8 dia 16/m' 537, slab tag T 16 (5B6) | treads 22F .. 233 solid, 234 .. 238 / 13B .. 143 hidden (above the cut 147 / 22D) |
| quarter landing + east flight x 66.963 .. 68.113 | HIDDEN treads 2C8 (y 39.248) .. 315 (y 40.448), edge 289, '8 dia 16/m' 53D | hidden treads 144 .. 146 / 4B5 (y 39.498 .. 40.398) |
| pocket: corner of walls 28A / 283 outside the outer arc 2DD | S-OPENING X 54B / 54C | nothing drawn (open to above) |
| east strip x 66.913 .. 67.488 north of the top tread 315 | slab, no outline, no tread | nothing drawn: open room below |

**GF-130 23.2371 m2 reconciled in units** (`ALSENAN_T271_INPUT.json` 'void_split_r2b', `ceilings_r2.split_structural_void`):

| Part | m2 | inside the 16.005 outline | south band 5.651 | east strip 1.581 | Ceiling over the GF piece | Status |
|---|---|---|---|---|---|---|
| light well | 13.3925 | 13.3925 | - | - | none (open to the 1F roof) | DRAWING-CONFIRMED |
| pocket (X 54B / 54C) | 1.5509 | 0.2334 | 1.3175 | - | none (opening) | DRAWING-CONFIRMED |
| stair zone (round flight 4.403, straight flight 2.007, landing 0.302, east flight + its 0.05 m edge to 2CF 0.690; hand re-split from the printed handle values agrees with the ledger union to 0.0012) | 7.4025 | 2.3791 | 4.3334 | 0.6900 | stair soffit / flight underside: stair finish line, not a decor ceiling | HELD |
| slab | 0.8913 | - | - | 0.8913 | horizontal decor ceiling (open room below) | DRAWING-CONFIRMED |
| **total** | **23.2371** | **16.0050** | **5.6509** | **1.5813** | | residual 0.000 |

Hand check of the pocket: box (63.8788 - 61.0934) x (40.7784 - 38.0480) = 7.6053 less the quarter disc r 2.7805 inside
it (6.0722 less half the cap below 283, 0.0180) = 1.5511 (ledger 1.5509, polygon arcs at 1024 segments). The light-well
outline is stated once: 13.3925 + 2.3791 + 0.2334 = 16.0050. Sensitivity named: the GF plan puts the east flight's top
nosing 0.05 m south of the slab plan's 315 (40.398 vs 40.448): 0.05 x 0.575 = 0.029 m2 between stair zone and slab; the
slab plan governs the soffit, the difference is listed, not absorbed.

**Effect.** GF-open horizontal decor ceiling 92.285 -> **93.177** (+0.891); no ceiling 23.237 -> **14.943** (light well
13.392 + pocket 1.551); GF stair soffit HELD 2.451 -> **9.854**; drop / return edges GF 18.320 -> 23.301 m (HELD). Villa
horizontal 362.282 -> **363.173 m2**; vs released 403.163: -39.990 (-9.92 %); vs freelancer 409.58: -46.407 (-11.33 %).
No other piece moved (byte-identical rows outside GF-RC99C2A/open; the 1F rooms, domes and 2F are as handed in).

**What is still open.** The stair soffit 20.579 m2 (GF 9.854 + 1F 10.725) waits for a stair finish line (the stair
rules OWNER_RULE_STAIRS_2026-10-24 measure the stair concrete, not its soffit finish): HELD, never 0. The round flight
inside the light well (2.379) and the GF floor piece under it are the floor-area task's question (the V2.9 floor face
runs under the round stair), not changed here.
