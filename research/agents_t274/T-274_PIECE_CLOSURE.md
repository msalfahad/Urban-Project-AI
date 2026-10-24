# T-274: every block wall's height pieces close its census length (development villa; every villa by R-T274-1)

Worker 2, claim 2026-10-24 22:41 UTC, lane A, gate 2. Base: working head 789ebbb4. Register v2 (research/agents_t228),
T-215, T-222 and T-261 r3 ledgers are READ ONLY: nothing is applied, no BOQ line moves, released default stays V2.9 +
route G. Drawings cited by Drive title (and entity handle where named); no coordinate, image or client name committed.
ERS: read; s.2.1 (the physical element: the block under each length stops at the soffit of the member drawn over THAT
length, Q-60 A), s.2.3 (reconstructed from the drawings, not from the register or the freelancer), s.3 build before
deduct (an opening is deducted only where it pierces counted masonry), s.4 rule + test, s.7 row below.

## 1. Root cause (why 40 of 73 register piece lists do not close)

Register v2's height pieces come from the T-143 hand helper (research/agents_t143/scripts/heights.py), which
(a) sampled the BAND centreline, not the census RUN (L-corner extensions, crossings cut out by MASONRY_CENTRELINE_V2,
the T-215 / T-222 junction closures and glazed lines are not the band), (b) counted a 2 cm sample as 'under a beam'
within 3 cm OUTSIDE the band edge (TOL 0.03: every beam crossing widened by up to 0.06 m, e.g. B11 0.26 for a drawn
0.2006, B14 1.86 for 1.80), (c) rounded every piece to 0.01 m; the register then applied the weighted mean height of
those pieces to the census length. That mean silently spreads every residual over the members that were sampled.

## 2. Method (exact, reproducible; research/agents_t274)

1. `t274_runs.py`: the end points of every census run exactly as MASONRY_CENTRELINE_V2 measures it (V1's band class
   subclassed only to read its final end stations after L extensions and joins). 70 straight runs.
2. `t274_geom.py`: each run cut EXACTLY at every architectural column outline, every route G beam band (T-110 member
   register: mark, b x h; no tolerance) and every face of the structural roof-slab plans (T-139 slab_faces), after one
   translation per storey found from the column outlines (GF 30 / 30, 1F 20 / 20, 2F 9 / 9 columns matched, residual
   0.000 m). A drawn beam / junction face that the band polygon does not reach takes the band NEAREST to the point
   (a merged band + column face is not every band touching it). Drawings: Drive 'Alsenan chalet project' /
   P7757_DXF_COMPRESSED.zip (P7757.dxf, sha ab54dd55) and 'ST7757 dxf.dxf' (sha 9f9d1179), decoded this run.
3. `t274_export.py` -> T274_RUN_PIECES.csv (stations along each run, member, depth, face, class: numbers only) and
   T274_OPENING_GAPS.csv (57 drawn opening / glazing gaps: part inside a column, inside the runs).
4. `build_t274.py` (`--check` reproduces every output): heights on the register's own per-wall basis (storey less the
   member depth / slab thickness, the same 4.50 / 4.20 / 4.20 and annex datum figures), slivers < 1 mm joined (rule 4),
   T-215 junction pieces and the T-222 1F-W14 + W15 piece carried from their merged ledgers, T-261 r3 walls cited (its
   drawn-extent pieces already close: 11 walls).

## 3. Results (T274_SIBLING_CHECK.csv: all 76 rows)

- Register v2 piece lists that do not close their census: **40** (of 73 with a list; 3 T-222 rows carry no list).
- Exact pieces: **54 CLOSED** (sum = census within 1 mm), **11 CLOSED by T-261 r3**, **4 CLOSED WITH HELD PIECES by
  name** (GF-W01 0.0026 m between the arch column face and the first drawn ST edge, up to 0.011 m2; GF-W03 CB3 / 'B3
  (With Stair)' depth not printed; 1F-W11 dome opening 1F-073; GF-W36 face GF-112, no member identified), **7 NOT
  CUT** (hand-census rows GF-W30 / W37 / H02, the arc band GF-W35, the T-222 rows 1F-W25, BAY-ENDS, P-GF-05).
  **No wall is left NOT CLOSED.**
- The Checker's flagged walls (own re-measures reproduced):

| Wall | Register v2 pieces | Exact pieces (m, member, h) | Register m2 | Exact m2 | Checker own |
|---|---|---|---|---|---|
| 1F-W20 | 4.55 + 1.20 + B19 0.46 = 6.21 on 6.125 | slab 1F-063 1.3062 (4.04) + B19 0.4037 (3.45; 0.40 / cos 6.9 deg + 0.8 mm junction) + slab 1F-023 4.4152 (4.04) | 24.477 | **24.5068** | 24.507 |
| 1F-W22 | 4.86 + CB11 0.14 = 5.00 on 5.075 | CB11 0.1004 (3.45) + slab 1F-084 4.8488 (4.04) + **B4 0.1258 (3.70, the missed strip at the L corner)** | 20.419 | **20.4010** | 20.402 |
| 1F-W08 | 2.80 + 0.60 = 3.40 on 3.600 | B23 2.9000 + B23 0.7000 (3.45, column 0.80 out) | 12.420 | **12.4200** | no area effect |
| GF-W19 | slab 1.78 + B4 0.22 | B4 0.2000 (4.00) + slab GF-018 1.7500 (4.34) + CB2 0.0500 (4.00) | 8.605 | **8.5950** | (flag) |
| GF-W21 | slab 1.02 on 0.993 | slab GF-039 1.0240 (4.34) on the V2 run + T-215 close -0.0311 (-0.1349 m2) | 4.309 | **4.3092** | (flag) |
| GF-W07 | (VERIFIED) | B1 0.9500 (4.10) + CB1 0.1500 (3.75) | 4.458 | 4.4575 | 4.458 VERIFIED, kept |
| 2F-W04 | B7 6.05 on 6.225 | B7 6.1248 (3.45) + 0.1002 corner shared with the undepthed BM-2F-015 band (rule 6: B7 0.75 >= every candidate 0.40 / 0.75; D-04 open) | 21.476 | **21.4763** | 21.476 VERIFIED, kept |

- Walls whose established net moves (T274_NET_BEFORE_AFTER.csv; nothing applied): GF-W11 -0.0010, GF-W16 +0.0316,
  GF-W19 -0.0100, GF-W20 -0.0162, GF-W28 +0.1224, GF-W31 +0.0115, GF-W32 +0.0634, 1F-W00 +0.0706 (W18, section 4),
  1F-W06 +0.0027, 1F-W12 -0.0005, 1F-W20 +0.0298, 1F-W22 -0.0180, 1F-W23 +0.0188. GF-W22 / GF-W34 stay on their
  T-215 bounded range (CB2 width CONFLICT), not moved. VERIFIED walls keep the Checker's figure (differences listed).
- **Established net (register v2 basis): 449.260 -> 449.5651 m2 (+0.3051, +0.068 %); m3 (net x t) 80.6744 -> 80.7254
  (+0.0510).** On the T-261 r3 basis (625.562 proposed) the same +0.3051 adds (no T-274 wall is a T-261 wall):
  625.8671 m2. HELD-gross walls change only as figures (largest: 1F-W07 +0.1389: register B7 1.89 + B19 0.98 + slab 0.36
  vs exact B7 1.800 + B19 0.8251 + slab 1F-063 0.5948; the 0.109 m junction face goes to B19, the nearest band). Sum of |delta| over all cut walls 0.650 m2: small here, as the Checker said; the rule
  matters because a 3 cm sampling halo per crossing grows with the number of crossings on another villa.
- Freelancer: no per-wall row (his one height per floor); RULE_DIFFERENCE stands on these walls (piece heights by
  printed member, Q-60 A); no total verdict while walls are held.

## 4. Openings inside a column outline (rule 5; T274_OPENING_SCAN.csv)

All 57 drawn opening / glazing gaps of the three floors scanned against the architectural column outlines and the
census runs: **one finding**, 1F-W00 W18 (band WB-FL0041-FL0042, glazing gap 6.4923 .. 6.9923 m along the band):
0.0327 m of the 0.500 gap lies inside the column outline the run already excludes (Checker's 2FD8). Deducted by its
0.4673 m inside the masonry x 2.160 = 1.0094 m2, not 1.080: 1F-W00 net 12.863 -> **12.9336 m2** (Checker own 12.935;
the 0.0013 is the register's 6.571 vs the run's 6.5708 m and rounding). 1F-W00 length 6.5708 m = run #1 of the band
(CB12 5.625 + 0.9458 between columns, all h 3.45); the run ends at the V2 bay cut (station 7.4708), so the BAY-ENDS caps
(inside the cut 7.4708 .. 10.7292) cannot overlap it: no double count. The stale 'W16 height HELD' text is corrected in
T274_TEXT_CORRECTIONS.csv (register v2 is not edited here).

## 5. Rule, test, lessons row (ERS s.4)

- **R-T274-1** (piece_close.py; any villa; provenance Checker T-180 slot 15:59 / 16:04 / 21:05 / 22:03): (1) pieces
  close the census within 1 mm, longer refused (OVER_CENSUS), shorter NOT_CLOSED until the residual takes the member
  drawn over it or is a HELD piece by name; (2) a piece is the member's extent along the centreline (skew: width /
  cos); (3) no weighted mean over non-closing pieces; (4) sub-mm slivers join a neighbour (beam first); (5) an opening
  is deducted by its part inside the counted masonry; (6) a corner square shared with an undepthed band takes the
  printed member's depth only when it is at least every recorded candidate, else HELD.
- **tests/t274_piece_close** (16): villa P (not Alsenan) hand truth 21.687580 m2 (slab + 30 deg skewed 30x60 beam +
  slab), mirror; adverse: normal width at a skew -> missed strip 0.046410 m found, gross refused; 2.55 m sampled piece
  -> OVER_CENSUS; weighted mean refused; residual HELD by name (never 0), unnamed refused; millimetres refused;
  slivers; opening jamb on / 0.03 m inside a column (0.50 vs 0.47); corner rule normal / deeper candidate / none;
  Alsenan: outputs reproduce, the Checker's 24.507 / 20.402 / 12.420 / 4.458, every cut wall closes or holds by name,
  W18 0.4673, no coordinates in the outputs.
- Lessons row (proposed): 2026-10-24 | 40 of 73 register piece lists did not close their wall (1F-W20 +0.030, 1F-W22
  -0.018, GF-W28 +0.122 m2) | the T-143 helper sampled the band (not the run) every 2 cm with a 3 cm halo outside each
  beam edge and the register spread a weighted mean over the census | cut the census run exactly at every drawn member
  edge; pieces close the census within 1 mm or a residual is HELD by name; no mean (any villa; blockwork, plaster,
  paint heights) | tests/t274_piece_close | PROPOSED.

Still HELD (unchanged, by name): GF-W03 member depth (D-03), 1F-W11 dome opening, GF-W36 face GF-112, GF-W01 2.6 mm
alignment strip, BM-2F-015 depth (D-04: rule 6 settles only the 2F-W04 corner), and every blocker of register v2 /
T-261. Next item, same topic: run the T-261 split walls through the same exact cut (their drawn-extent pieces were
read by hand; a machine cross-check of the 11 walls is the cheapest independent check), and the arc band GF-W35.

Reproduce: `python3 -I research/agents_t274/build_t274.py --check` (the geometry steps need the Drive drawings and
run outside the repository: t274_runs.py, t274_geom.py, t274_export.py, see each docstring).
