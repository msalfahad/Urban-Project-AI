# T-283 Ceilings r3: the R2 ceiling ledger made integration-ready (Alsenan; any villa)

Worker 2 (lane A), 2026-10-25. Research piece, unwired: no engine, rule, frozen, registry or candidate file changes; no
released or candidate quantity moves. Builds on T-271 r2b (MERGED 789ebbb4), which is imported and not edited.
Integration is lane I's (T-284). Development villa, not an accuracy claim. Drawings named by Drive folder and title only.
ERS read: s.2.1 (element), s.2.3 (first principles), s.2.4 (reconcile in units), s.3 (build before deduct), s.4, s.7.

## 0. Inputs and pipeline

| Input (Drive "Alsenan chalet project") | sha256 | Used for |
|---|---|---|
| P7757_DXF_COMPRESSED.zip / P7757.dxf | ab54dd55... | ARCH_TAKEOFF_V2.9 floor faces (re-run, pickled outside the repo), the pantry split B3 / AD |
| "ST7757 dxf.dxf" | 9f9d1179... | the three roof-slab plans (T-139 faces), the hidden tread lines (layer 2), the T-271 r2b GF-130 stair zone handles |
| committed | - | research/agents_t271 (ALSENAN_T271_INPUT.json, CEILINGS_T271.csv, RECONCILE_T271.csv), PANELS.csv (T-139), beam ledger r2 (T-252), T-185 dome S0 |

`t283_extract.py <v29.pkl> <st_faces.json> <align.json> <P7757.dxf> ALSENAN_T283_DELTAS.json <ST7757.dxf>` (ids, marks,
statuses, areas, lengths only) -> `t283_build.py` (stdlib; `--check` rebuilds byte for byte) -> `CEILINGS_T283.csv`
(one row per piece and surface), `BEFORE_AFTER_T283.csv`, `DOMES_T283.csv`, `CEILING_LEDGER_R3_EXPORT.json` (lane I),
`summary.json`. Rules module `ceilings_r3.py`. Tests `tests/t283_ceilings_r3` (20).

Reproduction check: re-running T-271's own extractor on the same drawings reproduces ALSENAN_T271_INPUT.json to 1e-3 on
every field except one beam piece, 1F-070 (B4 BM-1F-004, D 0.50, in the 1F living): free edge 1.400 m here vs 5.100 m
committed (piece 0.120 m2 both; a sliver's polygonisation). D 0.50 <= 0.60: no owner face and no held edge either way,
only the drawing-derived HELD candidate (never in a total) would differ by 1.258 m2. Listed in summary.json, not used.

## 1. Physical element (ERS s.2.1)

Per floor piece, what is physically built under the slab above it: horizontal gypsum decor ceiling, bulkhead vertical
faces where a beam drops below it, opening edges (drop / return / well face), coves, the paintable gypsum, and apart
from them the stair zone (the flight's underside: the stair finish line), no-ceiling parts (light well, pocket, shaft) and
open dome positions. This task asks two questions R2 left open: (a) where a stair drawn under the slab extends BEYOND
its stair-class face (Verifier test-adequacy note on T-271 r2b), what is built under that part; (b) is every face counted
once across decor ceiling, stair soffits, dome finishes and opening edges.

**(a) Hidden stair beyond its face.** On the GF-roof and 1F-roof slab plans the flights are drawn as hidden tread lines
(layer 2, 1.150 m). They cross out of the stair face into beam bands:

| Plan | Flight (first .. last tread handle) | Beyond the stair face, over a floor piece | What is above / below |
|---|---|---|---|
| GF roof | south flight 2BA .. 2C4 + landing / east flight 2C8 .. 315 (T-271 r2b stair zone, built from its handles) | GF-159 band 'B3 (With Stair)' 1.3756 (whole band), CA BM-GF-039 crossings GF-144 0.1725, GF-158 0.1425, GF-143 0.0300, junction GF-161 0.0513: **1.7719 m2** in the GF open piece | the flight under the band: stair soffit, not decor ceiling |
| GF roof | main stair 459 .. 25B / 45A .. 25E | GF-066 B20 0.4025, GF-044 0.0225 | inside the GF stair piece (kept apart): no ceiling effect |
| 1F roof | west flight 646 .. 632 (12 treads) | 1F-045 B23 BM-1F-026: tread 646 at y 45.198 inside the band whose north face is 45.348, 0.150 x 1.150 = **0.1725 m2** in the 1F living piece | the first going under the band |
| 1F roof | east flight 644 .. 62F | none (644 at 45.448, inside 1F-016) | - |
| 2F roof | no tread line drawn | - | 2F stair box stays HELD (T-271, 12.974) |

Parts of the footprints over wall lines (in no slab face): GF 0.0196, 1F 0.0025 m2: named, no ceiling effect.
T-271's one-face split `split_structural_void(GF-130, ..., stairs)` kept 7.4025 of its 10.9432 m2 stair union. The
other 3.5407 m2: stair strips GF-131 / -132 / -145 1.6737 (already deducted whole by R2: no change), the bands inside
the GF open piece 1.7719 (now moved to the stair zone), band pieces over walls GF-154 / -156 / -163 0.0780 and over no
slab face 0.0171 (named, no ceiling effect); residual 0.000.

**(b) Beam edges facing an opening.** R2 measured a bulkhead on every free beam edge in the room. Where the decor
ceiling is absent on the open side of the edge (light well, pocket, stair zone, open dome), there is no bulkhead: the
beam face is the opening's edge (drop / return / well face). R2 then counted those metres twice: as an owner-method
bulkhead face (m2) or a held bulkhead edge (m), and again in the opening-edge row 'ceiling edge at an opening' (49.134
m, HELD). Measured run by run along each free edge (`border_segments`; a straight edge tangent to a dome circle is not
a border: its contact shrinks with the tolerance):

| Piece | Beam | R2 | R3 | Open side |
|---|---|---|---|---|
| GF open | B22 BM (CALCULATED, D 0.75) | owner face 12.800 m x 0.15 = 1.9200 | 8.8495 m -> **1.3274 m2** | light well + pocket 3.9505 m |
| GF open | B29 (CONFLICT) | held edge 13.9168 m | **7.7167 m** | light well 5.821 m, stair 0.379 m |
| GF open | B21 (CONFLICT) | held edge 16.4429 m | **14.8697 m** | stair strip GF-132 1.573 m |
| GF open | GF-159 'B3 (With Stair)' (no register row) | held edge 3.625 m | **0** | the band lies wholly over the flight: stair zone |
| 1F living | B23 BM-1F-026 (CALCULATED, D 0.75) | owner face 5.000 m x 0.15 = 0.7500 | 2.500 m -> **0.3750 m2** | stair face 1F-016 2.500 m |
| 1F living | CB12 1F-078 (D 0.75) | owner face 1.5721 m -> 0.2358 | **0** | east dome opening 1.5721 m (curved sliver on the circle) |
| 1F living | CB12 1F-089 (D 0.75) | owner face 4.9178 m -> 0.7377 | 4.2592 m -> **0.6389 m2** | east dome opening 0.6586 m |
| 1F master bed 1F-RB72F22 | CB10 (CONFLICT) | held edge 4.350 m | **3.0313 m** | west dome opening 1.3187 m |

Stair-side metres (8.0773 m) become a new HELD row 'beam edge at a stair zone' (stair-well face, with T-281); the
light-well, pocket and dome metres (13.305 m) stay ONLY in R2's opening-edge row, which now names them in its basis.

## 2. Result in engineering terms (m2 unless stated)

| Quantity | Released engine FIN.CEILING | R2 (T-271 r2b) | **R3 (this task)** | Freelancer |
|---|---|---|---|---|
| Horizontal decor ceiling, villa | 403.163 | 363.173 | **361.229** (GF 187.951, 1F 142.752, 2F 30.526; dry 280.464 + wet 80.765) | 409.58 |
| R3 vs | -41.934 (-10.40 %) | -1.944 (-0.54 %) | - | -48.351 (-11.81 %) |
| Bulkhead faces, owner method (ASSUMED - OWNER-APPROVED, Q-48 A + Q-43) | none | 29.237 | **27.935** (GF 16.605, 1F 11.330) | none |
| Paintable gypsum, owner method | - | 392.410 | **389.163** | 452.33 (with cove strips) |

Changes R2 -> R3, by cause (every other piece byte-identical in quantity): GF open decor 93.1766 -> 91.4047 (-1.7719,
stair under the bands); 1F living decor 51.2221 -> 51.0496 (-0.1725, first going under B23); owner bulkheads -1.3022
(B22 -0.5926, B23 -0.3750, CB12 -0.2358 -0.0988); held bulkhead edges 58.290 -> 45.573 m (-12.717 m: B29 -6.200,
B21 -1.573, GF-159 -3.625, CB10 -1.319). Residual 0.000 on every piece (horizontal = piece - no ceiling - stair - dome -
held part - stair beyond).

Status: horizontal DRAWING-CONFIRMED (floor pieces Checker-VERIFIED where RECONCILE says so; overlay not yet verified);
the stair parts beyond the face HELD (stair-soffit line, T-281), never 0.

## 3. Every face of 1F, 2F and the domes, with its status (export records)

| Piece | Room | Class | Floor piece | Decor (DC) | Owner bulkhead (OA) | Released engine | HELD on this piece |
|---|---|---|---|---|---|---|---|
| 1F-R78C367 | living | DRY | 75.983 | 51.0496 | 7.6612 | 75.983 | stair zone 10.725 + 0.1725 beyond; east dome 14.0359; stair-well edge 2.500 m; opening edges; coves |
| 1F-RB72F22 | master bed (west dome) | DRY | 19.050 | 7.4692 | 0.6375 | 19.050 | west dome 11.5808; CB10 edge 3.0313 m; coves |
| 1F-R3CFCFD | master bed | DRY | 19.0187 | 18.6747 | 0.1304 | 19.0165 | east dome 0.3418; coves |
| 1F-RED0D19 | master bed | DRY | 18.215 | 18.215 | 0.5475 | 18.215 | coves |
| 1F-R0E919A | master bed | DRY | 16.340 | 16.340 | 1.8459 | 16.340 | B6 CONFLICT edge (Q-61 C); coves |
| 1F-R26FA0D | laundry | WET | 10.151 | 10.151 | 0.2146 | 10.151 | board type; coves |
| 1F-R8BDA49 | bath | WET | 5.0225 | 3.5998 | - | 5.0225 | west dome 1.4227; board type |
| 1F-R48AA46 | bath | WET | 5.0225 | 3.7815 | - | 5.0225 | west dome 1.2410; CB10 edge; board type |
| 1F-R48CDA5 | bath | WET | 4.725 | 4.2778 | 0.2925 | 4.725 | east dome 0.4472; board type |
| 1F-RED23B8 | bath | WET | 3.5775 | 3.5775 | - | 3.5775 | held beam edge; board type |
| 1F-RFFE7AF | dressing | DRY | 2.970 | 2.970 | - | none | coves |
| 1F-R52AC05 | bath | WET | 2.646 | 2.646 | - | 2.646 | board type |
| 1F-RCCB686 | shaft | SHAFT | 3.240 | - | - | none | no ceiling (opening above) |
| 2F-R1DB2D2 | maid room | DRY | 19.350 | 19.350 | - | 19.350 | coves |
| 2F-R4D1B62 | stair hall | DRY | 18.600 | 5.6258 | - | 0 (BLOCKED_RFI) | stair box top 12.974 (Q-72 investigation) |
| 2F-RE83BED | bath | WET | 5.550 | 5.550 | - | 5.550 | board type |
| 2F-R2BDCEE | shaft | SHAFT | 3.240 | - | - | none | shaft top 3.240 |

**Domes (T-185 S0 approved design; Q-44 A; DOMES_T283.csv).** West: open disc 15.359 m2 (r 2.2111) = over floor pieces
14.2445 (1F-RB72F22 11.5808, 1F-R8BDA49 1.4227, 1F-R48AA46 1.2410) + over walls 1.1145. East: 15.359 = 14.8249
(1F-R78C367 14.0359, 1F-R48CDA5 0.4472, 1F-R3CFCFD 0.3418) + 0.5341. Plan area HELD (designer DCR-4: what closes the
opening), never 0 and never in FIN.CEILING; the S0 shell intrados 24.150 m2 per dome (T-185, CALCULATED) belongs to the
dome finish line and the scenario report, not to the decor ceiling: one surface, one line. The dome ring parts outside
the disc stay decor ceiling (R2). Beam edges on the dome circle: CB12 1.5721 + 0.6586 m, CB10 1.3187 m (opening edges).

## 4. Who is right (proposals for the Checker)

| Item | Engine (released) | Freelancer | R3 | Proposal |
|---|---|---|---|---|
| flight under the GF bands B3 'with stair' / CA (1.7719) and the 1F B23 first going (0.1725) | ceiling | ceiling (in his reception / living rows) | stair zone HELD | ENGINE_WRONG / FREELANCER_WRONG: the flight is what is built under the band (R-CEIL-R3-1) |
| bulkhead along an opening / stair / dome edge (B22, B23, CB12: 8.681 m, 1.302 m2) | none | none | opening edge only | R2 double count corrected (R-CEIL-R3-2); RULE: one edge, one surface |
| 1F living vs his 38.96 | 75.983 | 38.96 | 51.050 decor + 14.036 dome HELD + 10.898 stair HELD | unchanged verdicts of T-271 (double-height ceiling over the light-well footprint; his row omits it) |
| totals | 403.163 | 409.58 | 361.229 | not a verdict on a total while 29.069 (domes), 22.523 (stair zones incl. beyond), 19.146 (class) m2 stay HELD |

## 5. Rules, tests, lessons

- **R-CEIL-R3-1** (proposed, any villa): a stair drawn under a slab is one footprint distributed over EVERY slab face it
  crosses; parts sum to the footprint; parts over walls named; overlapping faces refused; a one-face split that loses
  area refused. Each part over a floor piece is a stair zone, deducted once from the decor ceiling, HELD for the
  stair-soffit line (T-281), never 0. (`stair_zone_parts`, `single_face_split_refused`, `flight_footprints`.)
- **R-CEIL-R3-2** (proposed, any villa): a bulkhead face only along a beam-edge run with decor ceiling on its open side;
  runs along a no-ceiling part, a stair zone or an open dome are opening edges, counted once in the opening-edge row;
  contact must be stable under the tolerance (a tangent is not a border). (`border_segments`, `contact`,
  `bulkhead_split`.)
- **tests/t283_ceilings_r3** (20): villa W (8 x 6 hall, stair face 2.4 x 3.0, flight 0.30 m beyond under band B1 D 0.75,
  dome r 1.00 with ring beam RB1 D 0.75) hand truth decor 37.2984, owner 3.1710, beyond 0.360, stair-well edge 2.400 m,
  dome edge 2 pi m counted once, under identity / mirror / 37 deg + translation / mirror + -90 deg; R2 figure and the
  two named causes; adverse: one-face split of a stair beyond its face refused, overlapping faces refused, part over a
  wall named not dropped, tangent not a border, dog-leg = two flights (not one hull), border split not closing refused,
  CONFLICT edge stays held on the decor side only, HELD as 0 refused, stair beyond larger than the decor refused, mm
  refused; Alsenan: rebuild, totals and causes, 39 pieces once, HELD never 0, dome closure, no coordinates committed.
- Lessons row (proposed, ERS s.7): 2026-10-25 | a hidden flight crossing out of its stair face kept 1.944 m2 under two
  beam bands as decor ceiling, and 21.38 m of beam edge facing a light well, a stair or a dome was a bulkhead as well as
  an opening edge (T-283) | the stair footprint was intersected with one face, and free edges were judged only against
  wall faces | a stair footprint is distributed over every face it crosses; a bulkhead needs decor ceiling on its open
  side; one edge, one surface (any villa; ceilings, formwork soffits, plaster returns) | tests/t283_ceilings_r3 | PROPOSED.

## 6. Checker re-measure (two 1F rooms and one dome; handles on Drive "ST7757 dxf.dxf", 1F-roof slab plan)

(a) 1F living 1F-R78C367: tread 646 (y 45.198, x 18.569 .. 19.719) vs band 1F-045 north face y 45.348 -> 0.1725 m2;
B23 piece 2.500 x 0.450 in the room, edge on the stair face 1F-016 2.500 m -> owner face 2.500 x 0.15 = 0.375 m2;
decor 51.0496. (b) 1F master bed 1F-R0E919A (unchanged 16.340 decor, B19 / B25 owner 1.8459 m2, B6 CONFLICT edge HELD).
(c) East dome: disc r 2.2111 at the T-110 centre -> 15.359; over pieces 14.8249 (living 14.0359); CB12 1F-078 / 1F-089
edges on the circle 1.5721 + 0.6586 m. Plus the GF open stair under the bands: GF-159 1.3756 (whole band inside the
T-271 landing / straight-flight boxes from 283, 2C4, 289, 315), CA crossings GF-144 / -158 / -143.

## 7. What stays HELD (by name; summary.json 'held_by_surface')

Domes 29.0695 m2 (DCR-4); stair zones 20.5786 + 1.9444 beyond (T-281); GF stair piece apart 12.475 (soffit 10.725, top
1.750); 2F stair box 12.974 (Q-72); held-class pieces 19.146 (P-2, two unlabelled GF spaces); shafts 3.240 x 3; wet-room
board type; bulkhead edges on CONFLICT / HELD beams 45.573 m + 16.163 m over held pieces; stair-well beam edges 8.077 m;
opening edges 49.134 m; coves 288.640 m; drawing-derived bulkhead candidate (D-40, never a total); concrete ceiling
plaster NOT SPECIFIED. Not re-derived: 1F curved room edge (T-223), floor-piece splits (T-240 / T-269).
