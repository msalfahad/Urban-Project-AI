# T-153: Alsenan floor area space by space, the 11 held spaces settled or held by cause (NO REPO CODE)

Worker 2 (lane A, architectural and finishing), 2026-10-21 13:40-14:05 UTC. Gate 1 (no room missed; wet and dry right).
Development villa, not an accuracy claim; nothing is wired and no released quantity changes: a checked piece for the
consolidated ARCH_TAKEOFF_V3.0 candidate (lane I). Self-check of this run: clone, venv, codemap check (stale: none), t061
(20 passed), freeze check (0 differing): all PASS. No engine module was changed.

Data (Drive "Alsenan chalet project", scratchpad copies, never committed): P7757_DXF_COMPRESSED.zip (architectural DXF,
sha256 ab54dd55...), p7757_arch_sheet03.pdf (GF plan, read at 150 dpi). One unchanged ARCH_TAKEOFF_V2.9 run of the DXF
(its floor reconciliation ARCH_FLOOR_RECONCILIATION_V1: faces = categories BALANCED on all three floors) and one run of
`tools/label_census.py` (41 room labels: 28 MEASURED, 1 HELD, 1 UNSUPPORTED, 11 NO_ROOM = the T-061 eleven).
Merged / READY inputs used, never re-derived silently: T-074 wet hand table, T-086 finish table, T-088 printed sizes,
T-071 exterior spaces, T-111 / T-135 stair ledgers, T-116 stair floor residue, T-122 1F living rows (Q-66 B), T-123 side
passage, T-127 pool court, T-129 2F arrival (Q-70 A), T-147 room regions. New measurement this run: the GF courts and
the pool, by polygonizing the GF plan inside the plot boundary walls (rooms.py of T-147, branch agents/task-T-147, box = the
boundary walls' inner faces) and `scripts/yard_split.py`.

Rules: UP-SPACE-001 (interior / exterior evidence order), UP-SPACE-002, UP-WET-001, UP-WET-002, owner Q-06 A (basin-only
spaces wet), Q-37 A (pantry wet, printed 4.50 x 3.00), Q-66 B (1F arrival landing marble), Q-70 A (2F arrival marble,
condition met in T-129), Q-67 A (side passage exterior, condition met), URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1,
URBAN-WET-FLOOR-TILED@v1, URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1 (no cabinetry deduction anywhere), knowledge
OQ-04 (exterior finish scope unresolved), UP-QTY-STATUS-001. Defect B9 ("GARDEN inside a floor zone") is the GF garden band.

## 1. Result in engineering terms (m2; freelancer = FIN workbook tiles sheet)

| Floor | Dry porcelain (settled) | Doorway strips | Wet tiled | **Interior floor** | Held interior (not in totals) | Stair marble listed apart | Exterior measured |
|---|---|---|---|---|---|---|---|
| GF | 157.398 | 4.474 | 48.927 | **210.799** | garden band 13.986, closed face 1.373 | 20.669 (stair hall 12.475 + round-stair treads 8.194) | courts 167.714 + side passage 5.640 |
| 1F | 106.216 .. 106.333 | 0.770 | 31.145 | **138.131 .. 138.248** | unlabelled space 2.970 | arrival landing 4.865 | roofs 55.559 + 32.721 |
| 2F | 21.850 | 0.530 | 5.550 | **27.930** | - | arrival landing 4.875 | roof 115.832 |
| **Villa** | **285.464 .. 285.581** | **5.774** | **85.622** | **376.860 .. 376.977** | 18.329 | 30.409 | 377.466 |

Against the freelancer (his rows give names and areas, no dimensions):

| Line | Engine-side hand (this table) | Freelancer | Difference | Why |
|---|---|---|---|---|
| Wet floors | 85.622 | 72.01 | +13.612 (+18.9 %) | pantry 13.500 is wet by Q-37 A (he keeps it in his dry reception row); the other 17 areas +0.112 (+0.16 %, T-074) |
| Dry floors, raw | 285.464 + 5.774 strips = 291.238 | 337.57 | -46.33 (-13.7 %) | his dry rows also hold the pantry, the garden band, the stair treads and both arrival landings |
| Dry floors, like for like (his row contents rebuilt from ours) | 337.178 | 337.57 | **-0.392 (-0.12 %)** | ours + pantry 13.500 + garden band 13.986 + GF round-stair treads 8.194 + 1F landing 4.865 + 1F held strips 0.520 + 2F arrival 4.875 |
| per floor like for like | GF 197.552 / 1F 112.371 / 2F 27.255 | 197.33 / 112.96 / 27.28 | +0.222 (+0.1 %) / -0.589 (-0.5 %) / -0.025 (-0.1 %) | 1F: two bed rooms -1.385 (the 380 x 430 passage and the curved east room, both UNRESOLVED in T-086) |
| Courts (yard paving), measured, finish HELD | 167.714 (+ side passage 5.640) | 151.80 (one row "الحوش الأرضى", perimeter 81.32) | +15.91 (+10.5 %); +21.55 with the passage | not traceable: his row has no breakdown; OQ-04 gives no exterior scope (owner question proposal P-1) |
| Roofs (3 roof labels) | 204.112 | 285.00 (one row, all roofs) | as T-071 | unchanged here; the 2F top roof (Q-34) is still on no plan |

What changed against the released state: the released floor area is HELD as a total; it stays held (nothing wired).
What this table settles: all 41 labels have a row, 0 silent; the 11 labels the guard held are now 5 spaces with a status,
an area and a cause for every finish still held (section 2). The merged dry set "10 rooms 194.98 m2" re-adds to
177.431 .. 177.548 m2 under the owner's later answers, every m2 of the -17.55 .. -17.43 explained (section 4).

## 2. The 11 held labels (T-061 guard, ROOM_LABEL_NO_FACE) and the GARDEN label, settled or held by cause

| Labels | Space | Interior / exterior (evidence) | Area | Finish status |
|---|---|---|---|---|
| GF COURT + حوش (AT22, AT21) | west court beside the annex, to the inner face of the boundary walls | EXTERIOR: exterior word; open to the sky inside the plot walls (plot printed 31.37 x 15.00, walls 0.20) | **138.761** MEASURED; of which entrance porch under the 1F block 19.181 (T-121) and the entrance flight E1 footprint 3.360 (T-111: 4 treads 0.30 x 2.80, stair marble) | paving HELD (OQ-04), proposal P-1 |
| GF COURT + حوش (AT40, AT39) | north court strip along the master bed room block | EXTERIOR (same) | **21.348** MEASURED | HELD (OQ-04) |
| GF swimming pool + حمام سباحة (AT20, AT19) | pool court east of the curved glazing, under the 1F slab with its printed VOID | EXTERIOR (word; T-127 / Q-68: slab over outside air) | deck **7.605** = court face 17.007 - pool to its outer shell 9.402; pool water inside the shell r 1.55 = **7.548** (not a floor: EXCLUDED, pool scope) | deck HELD (OQ-04); pool finish no Urban rule |
| 1F ROOF (AT220) | GF annex roof at +4.30 | EXTERIOR (word; outside the 1F walls) | **55.559** (T-071 = T-062 hand) | membrane released (Q-24); screed / finish HELD (Q-41) |
| 1F ROOF (AT216) | GF south-east roof strip at +5.50 | EXTERIOR | **32.721** (T-071) | as above |
| 1F VOID (AT225) | 1F slab opening over the pool court (B7 ring inner faces; the 1F plan draws the same outline with VOID) | EXTERIOR, open to the sky | **3.690** (T-127, verifier 3.689) | EXCLUDED: no floor (not 0: no item) |
| 2F ROOF (AT379, AT385) | 1F roof at +9.70, one face, two labels | EXTERIOR | **115.832** (T-071, 2 open dome skylights out) | as above |
| GF GARDEN (AT48, held in V2.9 as RFI EXTERNAL) | band 1.30 m drawn (150 printed incl. the line) x 10.82 m printed, inside the reception south of the round stair | **HELD CONFLICT**: the word says exterior, but the band is inside the GF south facade wall (windows in it) and under the GF roof slab (the 1F plan's +5.50 roof strip, 1.30 m wide, lies exactly over it); UP-SPACE-001: a label alone never decides | **13.986** (V2.9 faces 9.101 + 4.885) | HELD: planter or floor? proposal P-2 (the freelancer floors it inside his reception row) |

Counted once: the four court labels are one connected open face (T-071 "4 labels, one face", 177.299 filled; this run
177.115 inside the boundary walls), split into west court / north strip / pool court along the building's north-west
corner line and the north wall's court face, so each label keeps its own space; the pool court is not added to the
courts twice (deck only, pool apart).

## 3. Every labelled interior space (49 rows in SPACES_T153.csv; finish family, rule and source on every row)

- GF dry: dewaneya 24.940 (V2.9 face 24.9403 = printed 400 x 630 less the R1.10 corner = this run's face 24.9391; his
  24.84, +0.4 % AGREE), driver 7.875 (printed 1.75 x 4.50; 7.87), master bed room 16.550 (16.66, -0.7 %), open room
  (dining, reception, saloon, entrance and the hall to the master bed room) **108.033** = V2.9 open-plan floor 118.733
  less pantry 13.500 plus the 2.800 cell west of the garden band (= T-086 candidate). Its south limit is the garden-band
  edge drawn on layers 2 / 5 (not walls): if P-2 says floor, the open room is 122.019.
- GF wet: 10 T-074 areas 35.427 + pantry 13.500 (Q-37 A) = 48.927; the basin-only spaces are wet (Q-06 A).
- GF held: closed face between the two wedge W.C.s 1.373 (no label, no door: duct or void, not stated; UP-WET-002 REVIEW).
- GF excluded / apart: stair hall 12.475 and round-stair treads 8.194 (stair line, T-111 / T-133), lift 3.24, side
  passage 5.640 EXTERIOR (Q-67 A). **Engine defect found**: V2.9 counts the passage's two faces (3.600 + 1.560 = 5.160 m2)
  as INTERNAL unallocated floor (internal_physical_floor 246.846 GF holds them); under Q-67 A they are exterior.
- 1F: living zone porcelain **33.594 .. 33.711** HELD range (T-122: designer D-23 0.1175), arrival landing marble 4.865
  (Q-66 B), void 16.005 excluded; bed rooms west 19.050 (his 19.00), east curved 19.017 (19.46, UNRESOLVED), 500 x 365
  18.215 (18.25), 380 x 430 16.340 (17.29, ENGINE_RIGHT on the room, passage UNRESOLVED); 6 wet areas 31.145; unlabelled
  space by the arch 2.970 HELD (type), lift 3.24.
- 2F: maid room 19.350 (19.58, -1.2 %), floor beyond the stair width 2.500 porcelain + arrival landing 4.875 marble
  (T-129; his "corridor" 7.70), W.C. 5.550 wet (5.62), lift 3.24.
- Cabinetry: kitchen, pantry, laundry and wardrobe joinery are not deducted anywhere
  (URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1); no floor finish note is printed on any sheet (T-091), so the porcelain /
  tile defaults apply (both PROJECT_SPECIFICATION-first rules, none found).

## 4. Re-add checks

| Check | Result |
|---|---|
| 17 wet areas (T-074, 72.12 m2) | this table's 17 rows 72.1217 (= 72.122 merged, -0.0003 rounding); with the pantry 85.622 = T-086 85.62 |
| 10 dry-tile rooms (T-086, 194.98 m2) | now 177.431 .. 177.548: 8 rooms unchanged (141.337); 1F living 44.869 -> 33.594 .. 33.711 (landing 4.865 to marble, held strips 0.520, treads / stair footprint the released line kept 5.890: T-116 / T-122); 2F "lobby 8.775" -> 2.500 (arrival 4.875 to marble, 1.400 wall inside the printed 450 x 195: T-129). 4.865 + 0.520 + 5.890 + 4.875 + 1.400 = 17.550 = the change |
| V2.9 floor reconciliation | GF plate 284.805 = categories (BALANCED); this table uses its faces for 23 of the GF rows |
| Courts, second route (printed / hand) | west court: 14.80 x 9.90 - annex corner 4.20 x 1.80 + (1.30^2 - pi 1.30^2 / 4) = 139.32, less the drawn 1.40 x 0.40 stub at the porch (0.36) = 138.96 vs 138.761 (-0.20, -0.14 %: column notches not hand-listed); north strip 1.30 x 16.17 = 21.021 + the 0.25 m step at the pool-court mouth (about 0.33) vs 21.348; pool court printed gross 16.5245 (T-127) vs drawn face 17.007 (+0.482: the drawn face runs to the curved frame, the printed 657 band face does not; T-127 SX-02 recess 0.561); T-071's independent run of the same face 177.299 vs 177.115 here (-0.184: its 0.232 closure) |
| Pool | r 1.75 and r 1.55 arcs about one centre on the GF plan (layers 5 and 2): outer to the boundary-wall face 9.402, water 7.548; T-127 printed radius 1.750 |
| Synthetic fixture (not Alsenan) | `python3 -I t153_floor_area.py --check`: bed room with wardrobe (not deducted), living split by a half wall (footprint deducted, one space), covered terrace, open court less a pool, bath, basin-only lobby (Q-06 A), unlabelled space, garden strip enclosed and roofed (HELD CONFLICT), hall with a light well; m / mm / rotated 37 deg / mirrored / both: **50 of 50 PASS**, held rows never 0 |

## 5. Who is right (proposals for the checker)

- Wet floors: AGREE / ENGINE_RIGHT per T-074; pantry RULE_DIFFERENCE (Q-37 A).
- Dry floors: like for like -0.12 %; GF open room RULE_DIFFERENCE (pantry wet, stair treads are stair marble, garden band
  HELD); 1F living and 2F corridor RULE_DIFFERENCE (Q-66 B / Q-70 A landings marble); 1F 380 x 430 ENGINE_RIGHT on the
  room (printed 3.80 x 4.30), its passage and the curved east room UNRESOLVED (as T-086).
- Courts 167.714 vs 151.80: UNRESOLVED (single row, no dimensions; scope OQ-04). Side passage: ENGINE DEFECT in V2.9
  (exterior counted internal), the hand row is right by Q-67 A.

## 6. Owner question proposals for the Lead (no-assumptions; not added to OWNER_QUESTIONS.md by this run)

- **P-1 (courts, OQ-04)**: the GF courts measure 167.714 m2 (west 138.761 incl. the 19.181 porch, north strip 21.348,
  pool deck 7.605) + the side passage 5.640 m2 (exterior by Q-67 A); no sheet prints an external finish and no Urban
  rule gives an exterior floor scope. Options: (A) external paving tiles, type by specification, on the whole area;
  (B) interlock on the open courts, tiles under the porch; (C) outside the architectural BOQ (landscape package).
  Blocks: the yard line (the freelancer has 151.80 m2). Practice in Kuwait villas: (A) or (B), the porch and the pool deck
  usually match the house entrance.
- **P-2 (garden band, defect B9)**: the 1.30 x 10.82 m band labelled GARDEN / حديقة inside the reception, south of the
  round stair, roofed by the GF roof slab and enclosed by the south facade: (A) a planter (soil, no floor finish; its
  edge is a curb); (B) floor, porcelain with the reception (+13.986 m2, the freelancer's reading); (C) ask the designer.
  Blocks: 13.986 m2 of GF porcelain and the open room's south limit.

## 7. Missing / held

Garden band 13.986 (P-2), GF closed face 1.373 and 1F unlabelled space 2.970 (type for the designer), 1F living range
0.1175 (D-23), the courts' finish (P-1), roof finish (Q-41), the 2F top roof (Q-34, on no plan), the floor under the GF
round stair beyond its drawn treads (T-116 NOT_ASSESSED, kept inside the open room), the freelancer's two 1F bed-room
differences (passage, curved edge).

Checker re-measure proposal (3 spaces, one formerly held): GF north court strip (formerly held: 1.30 x 16.17 + the
pool-court mouth step, 21.348), GF dewaneya (printed 400 x 630 less R1.10, 24.940) and the GF open-room porcelain
(V2.9 open-plan 118.733 - pantry 4.50 x 3.00 + 2.800 = 108.033).

Files: `SPACES_T153.csv` (49 rows: one per space, status, evidence, rule, source, freelancer row), `FLOORS_T153.csv`
(per floor), `summary.json`, `t153_floor_area.py` (ledger, totals, re-adds, `--check` fixture),
`scripts/yard_split.py` (court split; its cut boxes are client coordinates and stay with the private inputs).
Repeat: `python -I rooms.py P7757.dxf <inner box widened 0.035> faces.json`, then
`python -I scripts/yard_split.py faces.json cuts.json`, then `python3 -I t153_floor_area.py --out <dir>`.
