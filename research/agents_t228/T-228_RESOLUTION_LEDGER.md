# T-228: blockwork resolution 4/4: wall register v2 (resolution ledger) and after-coverage

Worker 2, 2026-10-24 04:44 UTC claim, lane A, gate 2 (owner programme BLOCKWORK_RESOLUTION_PROGRAMME.md, 2026-10-23
15:45, items 6, 7, 9, 10). Base: working head fee98d9a. Development villa; not an accuracy claim. Drawings cited by Drive
title and entity handle only (hex handles); no coordinate, image or client name is committed. Released default
unchanged (V2.9 + route G); nothing integrated into a candidate (a later lane I package names this register under
`integrates:`). ERS: read; s.2 steps 1-6 (element, evidence, reconstruction, reconciliation in units, status), s.3
(installed vs procurement, build before deduct, one element once), s.4 (rule + test), s.7 row below.

## 0. Rework r2 (worker 2, 2026-10-24 10:45 UTC; Verifier 09:59 REJECTED gate e + h, narrow scope only)

Physical element first: the ST-01 dog-leg stair rises in a 2.50 m shaft beside the lift, GF +1.00 -> landing +3.50 ->
1F +5.50 -> landing about +7.6 -> 2F +9.70 (T-184). Its outer wall is ONE tall shaft wall on the GF-W10 / 1F-W10 / 2F-W02
line; the storey floors +5.50 / +9.70 meet the shaft at its far end, not on this wall. The finding F1 (GF-W10 stair-foot
piece HELD) therefore applies to the same 2.500 m piece on every storey of the line.

Evidence, own read this run (ST7757 dxf, sha 9f9d1179, by handle): '(With Stair)' is printed exactly 3 times: 6B6 on the
GFRS frame beside B3 6B7 (BM-GF-015), 6B8 on the FFRS frame beside B3 6B9 (BM-1F-001), 1826 on the GFRS frame beside B3
1827 over CB3 span 2 (BM-GF-057, the round stair ST-02). SFRS prints a plain B3 (79D, BM-2F-001). BM-GF-015 / BM-1F-001 /
BM-2F-001 and BM-GF-057 / BM-1F-023 span 2 sit at one plan position on every frame (T-110 x / y: one frame step for all
pairs, within 0.01 m; tested). On SL-1 no floor-level member is printed on that span on any frame; section A-A cuts no
slab at +5.50 / +9.70 on the stair-wall line (Verifier 09:59). On SL-2 the GFRS frame prints CB3 20x75 (the floor-level
band) under span 2 beside the cranked 'B3 (With Stair)' stair beam (T-110, T-084), so the 1F floor exists there.

Rule R-T228-3 (register_v2.stair_line_flags, any villa): a '(With Stair)' mark on ANY storey frame of a member line holds
every wall piece under the line unless a floor at the piece's own basis is printed on that line at its storey (slab cut,
or a floor-level member beside the stair mark), and also when the piece's top member is the stair member with no
floor-level member printed with it. Findings may only hold (R-T228-2).

| Wall | Piece on the stair line | Check | v2 r1 | v2 r2 |
|---|---|---|---|---|
| GF-W10 | B3 2.500 m (SL-1) | HELD (base +0.30 landing, top stair member) | net HELD, gross SS 50.845 | net HELD, gross HELD (figure 50.845 kept); eastern pieces as their own figure: CB2 3.470 x 4.00 + CB2 3.350 x 4.00 + B24 3.550 x 3.75 = 40.5925 - W05 / W06 / W07 1.440 = **39.1525 m2** on the +1.00 basis (Checker 09:59; r1 text said 39.155 with B24 3.540: the pieces close to 12.870 m only with 3.550) + W.C. 0 .. 0.945 HELD |
| 1F-W10 | B3 2.500 m (SL-1) | HELD (base: no +5.50 floor; top: the stair member) | net 44.929 SOURCE-SUPPORTED | net HELD, gross HELD; CB9 pieces 10.370 m x 3.70 = **38.369 m2** (figure, not a quantity); B3 piece 9.500 m2 on the +5.50 basis HELD; W21 / W22 / W23 / W25 2.940 not assigned to pieces, so no net is formed |
| 2F-W02 | B3 2.500 m (SL-1) | HELD (base: no +9.70 floor) | HELD (BM-2F-015 depth) | HELD, both causes named (F4) |
| GF-W03 | 2.650 m under CB3 / B3 (SL-2) | HELD (GF base under the flight not printed) | HELD (D-03, Q-61 (2)) | HELD, F5 named |
| 1F-W06 | CB11 span 2 2.64 m (SL-2) | not held: floor-level CB3 printed under the piece | 54.487 SS | unchanged (Q-61 (2) open: if the designer removes CB3 from span 2 the check re-runs) |
| 1F-W22 | 0.14 m under CB11 (SL-2) | not held (same) | unchanged | unchanged |

Effect (net installed blockwork, development villa): established net 494.189 -> **449.260 m2** (-44.929, 1F-W10 now
HELD); SOURCE-SUPPORTED net 404.587 -> 359.658; VERIFIED 4.458 and PROJECT-SPECIFIC 85.144 unchanged; m3 established
89.660 -> 80.674; walls net HELD 38 -> 39 of 76; gross HELD 329.209 -> 427.923 m2 (GF-W10 50.845 + 1F-W10 47.869 move
from SOURCE-SUPPORTED, figures kept, never 0). 1F white 0.20 established net 148.896 -> 103.967 against the freelancer's
1F external 165.621 (comparison only; not like for like: 1F-W04 and 1F-W10 held, his 41.25 projections). Length identity
unchanged (no wall length moved). Register row identity kept (one row per v1 wall): the eastern GF-W10 figure is carried in
the row's bounds text and in STAIR_LINE_CHECK.csv, not as a new row (a split row would be a worker number, R-T228-1).
Everything else in v2 is re-used as is. Section 4 below is the r1 text (its 39.155 is superseded by 39.1525 here).

Lessons row proposed (ERS s.7): "A finding about one piece of a multi-storey element (a stair shaft wall) is checked on
every storey of the same plan line before hand-in; the check is a test (R-T228-3), not a reading."

## 1. What the register now says (net installed blockwork m2, development villa)

Register v2 = register v1 (T-225) + 55 checker-merged changes + 1 hold from this run's own drawing finding
(CHANGE_LOG_V2.csv). v1 is untouched; every change names its merge commit or the Checker verdict it comes from.

| | v1 (T-225) | v2 (this run) | change |
|---|---|---|---|
| Net with an established figure | 337.410 | **494.189** | +156.779 (+46.5 %) |
| of which VERIFIED (Checker re-measured length, height and deductions) | 0 | **4.458** (GF-W07) | +4.458 |
| of which SOURCE-SUPPORTED PENDING INDEPENDENT CHECK | 252.815 | 404.587 | +151.772 |
| of which PROJECT-SPECIFIC (Q-55 C door height in the deduction) | 84.595 | 85.144 | +0.549 (GF-W32, T-215) |
| Gross VERIFIED (length + height Checker re-measured) | 0 | **101.236** on 4 walls (GF-W01 62.155, GF-W07 4.458, 1F-W05 23.223, 2F-W08 11.400) | |
| Walls with net HELD | 44 of 74 | 38 of 76 | -6 |
| Established m3 (net x drawn thickness; D-12 range not applied) | 58.365 | 89.660 | +31.295 |
| Wall rows / total physical length | 74 / 287.713 m | 76 / 289.688 m | +1.975 m, all listed (s.3) |

By floor x thickness x type (AFTER_COVERAGE.csv carries every class column v1 and v2 and the reconciliation identity):

| Floor | t | Type | Walls | Net established v1 | Net established v2 | VERIFIED | SOURCE-SUPP. | PROJECT-SPEC. | Walls net HELD | Gross figure of held-net walls (not a quantity) | Gross VERIFIED |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GF | 0.15 | BLACK | 16 | 83.658 | 84.872 | 0 | 51.691 | 33.181 | 6 -> 6 | 60.887 | 0 |
| GF | 0.20 | BLACK | 8 | 62.155 | 62.155 | 0 | 62.155 | 0 | 7 -> 7 | 81.882 | 62.155 |
| GF | 0.20 | WHITE | 15 | 10.049 | 32.551 | 4.458 | 22.503 | 5.590 | 11 -> 9 | 147.609 | 4.458 |
| GF | 0.20 / 0.40 | strips | 2 | 0 | 0 | 0 | 0 | 0 | 2 -> 2 | 0 (1.500 m held length) | 0 |
| 1F | 0.15 | BLACK | 13 | 89.039 | 89.039 | 0 | 52.306 | 36.733 | 7 -> 7 | 84.238 | 0 |
| 1F | 0.20 | BLACK | 4 | 23.900 | 23.900 | 0 | 23.900 | 0 | 1 -> 1 | 11.321 | 0 |
| 1F | 0.20 | WHITE | 9 | 15.833 | **148.896** | 0 | 148.896 | 0 | 5 -> 1 | 10.553 | 23.223 |
| 2F | 0.15 | BLACK | 1 | 9.640 | 9.640 | 0 | 0 | 9.640 | 0 | 0 | 11.400 |
| 2F | 0.15 | WHITE | 1 | 0 | 0 | 0 | 0 | 0 | 1 -> 1 | 27.993 | 0 |
| 2F | 0.20 | BLACK | 4 | 21.660 | 21.660 | 0 | 21.660 | 0 | 2 -> 2 | 10.657 | 0 |
| 2F | 0.20 | WHITE | 3 | 21.476 | 21.476 | 0 | 21.476 | 0 | 2 -> 2 | 30.040 | 0 |

No 100 mm wall exists in any source (a count of 0 walls). Every group reconciles: gross figure = net VERIFIED + net
SOURCE-SUPPORTED + net PROJECT-SPECIFIC + deductions on established nets + gross figure of held-net walls (residual
<= 0.001 m2, rounding of 3-decimal rows).

## 2. What was applied, from which merged source (owner item 7)

| Source (merge / verdict) | Walls | What it does in v2 |
|---|---|---|
| T-226 a04f8e21 (Checker 18:01) | GF-W07, GF-W10, 1F-W05, 1F-W11, 1F-W16 | member heights by printed depth (field diff of its delta against v1) |
| Checker ruling 18:01 (T-226 verdict f) | GF-W07, 1F-W05 | **the Checker's own numbers replace the worker's**: GF-W07 4.468 -> 4.458 VERIFIED (drawn band edges B1 0.950 x 4.10 + CB1 0.150 x 3.75; no opening); 1F-W05 gross 23.254 -> 23.223 VERIFIED, net 19.303 SOURCE-SUPPORTED (W14 height 1.60 not re-measured) |
| T-227 r2 ebce3d97 (Checker 21:05 / 20:14) | 32 rows | window heads from T-201 / T-207 (Checker re-measured the deductions): nets GF-W16 15.404, 1F-W00 12.863 (W15 / W16 arched outline 4.363 each), 1F-W06 54.487, 1F-W10 44.929; deductions on held-gross walls GF-W04 / GF-W18 / 2F-W02; annex and lift tests (still HELD, missing item refined) |
| Checker ruling 21:15 (GF-W10) | GF-W10 | deductions 3.420 (W05-W07 0.60 x 0.80 own read; D-GF-09 Q-55 C), 47.425 on the +1.00 basis + W.C. increment; **then held by finding F1 (s.4)** |
| T-215 8a9b4b48 (Checker 15:04) | GF-W13, W20, W21, W22, W31, W32, W33, W34 | 45 deg / column ends closed by drawn masonry area: +0.2855 m, +1.214 m2 established; GF-W22 / GF-W34 carry 0 .. 0.0128 / 0 .. 0.0139 m2 HELD (CB2 width CONFLICT, never picked) |
| T-222 769cad40 (Checker 20:14) | 1F-W25, new row 1F-W00/W01 BAY-ENDS, 1F-W14 + 1F-W15, new row GF P-GF-05 ABOVE-LINTEL | bay basis +0.4124 m / +1.481 m2 (1F-W25 0.581 -> 1.490; straight-band ends 0.572 as their own row: the split between the two runs of one band is not drawn, counted once); junction piece +0.077 m / +0.302 m2 (net stays HELD 11.273 .. 16.525 on P-1F-01); masonry above the P-GF-05 lintel 2.640 m2 (Checker re-measured as a component, 0.0 %) |
| T-238 242e50b2 (Checker 22:50) | 2F-W07 | W26 masonry deduction 2.040 -> 1.875 (true arched outline; gross HELD, so no net moves) |
| T-108 r2 01eeafd0 (Checker 07:13 / 09:11) | 2F-W08 | gross 11.400 VERIFIED; net 9.640 stays PROJECT-SPECIFIC (Q-55 C door height, ASSUMED — OWNER-APPROVED stays visible) |
| T-143 (Checker own spans / members) | GF-W01 | gross 62.155 VERIFIED; net SOURCE-SUPPORTED (the opening census of the run was not part of that check) |
| T-017 345f408b (Checker 23:08) | all 75 census walls | annotation only: census length, difference, cause, verdict per wall; the 9 corner squares carried as the proposed UP-MAS-CORNER-001 length beside the ledger length (**not applied**: a lane I rule version decides; same plan area; it moves 0.075 m of 0.20 wall into 0.100 m of 0.15 wall at GF-W02 / GF-W23, so those walls cannot be VERIFIED by thickness until it is adopted); GF-W30 length bound 1.193 .. 1.525 m |

Refused by construction (tests): a value from an unmerged branch, a worker number the Checker corrected (GF-W07 4.468,
1F-W05 23.254), VERIFIED from anything but a complete Checker ruling, two packages writing different values to one
field without a ruling.

## 3. Length identity (T-222 s.2 asked for it)

v2 - v1 total length = +1.975 m = T-215 ends +0.2855 + T-222 bay group +0.4124 + T-222 junction piece +0.077 + the
P-GF-05 piece above the lintel 1.200 (a 1.20 m piece over an opening, height 2.20, not a full-height wall). Nothing
else moved (test).

## 4. New finding this run (not applied as a number; the wall is HELD)

GF-W10 (0.20 white, north wall of the main house on the court, 12.870 m between column faces; pieces B3 2.500, CB2
3.470, CB2 3.350, B24 3.540). The Checker (21:15) accepted 47.425 m2 on the +1.00 floor basis and asked this package to
measure the W.C. stretch and check sections A-A / B-B. Own reads, Drive 'Alsenan chalet project':

- **F2, the W.C. stretch.** P7757.dxf GF plan: the W.C. behind W05 occupies 1.350 m of the wall's inner face (inner face
  lines 2AD / 271, between the column stub 213 and the W.C. partition face; W05 jambs 3E2 / 3E1). No level mark in the
  W.C. (nearest marks are the stair landing and the hall). Increment on the Checker's basis: 0 .. 0.70 x 1.350 =
  **0 .. 0.945 m2**, HELD (designer: W.C. floor level, D-45 family).
- **F1, the stair-foot piece (material).** The 2.500 m B3 piece between the west column (S-COL.BON 2F7E) and the column
  stub 213 / 21A holds D-GF-09 (the 0.900 m gap of the outer face). Inside it the plan prints **+0.30** (LEVEL insert 4AB,
  text 4AC) on the stair-foot landing, the court outside +0.15 (40A / 4AE). Section A-A (p7757_arch_sheet10.pdf; its cut
  passes through D-GF-09) prints the same **+0.30 landing** and **+0.15 court** at this wall, a printed **320** from the
  landing to a hatched (concrete) member on the wall line over the door, and no 1F slab on that line (it is the stair
  shaft). So this piece stands 0.70 m below the +1.00 basis and its top is the stair landing member, not B3 at +5.10:
  the 10.250 m2 (2.500 x 4.10) of the 50.845 gross and its D-GF-09 deduction 1.980 are not established. By the evidence
  rule (WORKFLOW_CONTROLS s.8; R-T228-2 below) GF-W10's net is HELD in v2, with 50.845 - 10.250 - 1.440 = 39.155 m2 on the
  three eastern pieces (+1.00 basis) and 8.270 m2 (stair-foot, +1.00 basis, not a quantity) written in its bounds for
  the Checker. Same family as the stair-shaft walls (Q-72 / T-173). Effect against the Checker's 47.425: established net
  -47.425 now; after the Checker's check of F1 the three eastern pieces (39.155) can return at once, the stair-foot
  piece needs the stair landing member's soffit (ST stair detail) and the +0.30 base.

## 5. Blockers that remain (owner item 10; BLOCKERS_V2.csv, 40 rows: 38 held-net walls + 2 held increments)

| Cause | Walls | Exact missing item | Who |
|---|---|---|---|
| annex datum (Q-54 B) | 11 (GF-W04 / GF-W18: openings resolved by T-227, the datum still holds them) | annex roof slab top / build-up; B-B puts +4.30 on a layer over the roof band (T-227) | designer D-39; owner Q-54 B HOLD stands |
| beam depth / register conflict | 6 | depth of the member above (T-110 register; GF-W03 two marks CB3 / B3 D-03) | designer (Q-61 C) |
| no member drawn above | 6 | top of wall under the dome openings / at column faces | designer (dome ring detail) |
| lift tie beam (ST p.8 note 19) | 4 | size b x h of the GF lift tie beam at +3.00; lift landing heads | consultant row 7 (send-ready, D-43) |
| held opening | 7 | head / size of an opening drawn on no sheet (D-GF-07, A-GF-01 arc, D-GF-14, L-1F-01, P-1F-01, A-1F-01, L-2F-01) | designer / consultant row 9 |
| stair-foot datum and top (F1) | 1 (GF-W10) | stair landing member on the wall line; +0.30 base (printed); W.C. level | Checker (F1), then lane A / S |
| glazed line / held strip | 3 | material, base and top of GF-H01 / GF-H02 / GF-W37 | designer |
| held increments | 2 | GF-W22 / GF-W34 CB2 width (0 .. 0.013 / 0 .. 0.014 m2) | designer (CB2) |

Each row names the smallest affected quantity (the bound width, or the gross figure on the established pieces, labelled
"not a quantity"). No owner question: none of these meets ERS s.2.7 (they are designer items or an existing owner HOLD).

## 6. Against the freelancer (comparison only; FREELANCER_COMPARISON_V2.csv)

| Floor / his section | His net | Engine net established v1 -> v2 | Engine walls net HELD | Like for like |
|---|---|---|---|---|
| GF external | 266.355 | 72.204 -> 94.706 | 10 | NO (held, missing not 0) |
| GF internal 0.15 | 167.800 (incl. fence 74.40 m2 gross) | 83.658 -> 84.872 | 6 | NO |
| 1F external | 165.621 (incl. projections 41.25 m2, no wall run) | 15.833 -> 148.896 | 1 (1F-W04) | NO |
| 1F internal 0.15 | 195.098 | 89.039 -> 89.039 | 7 | NO |
| 2F external | 86.575 | 21.476 -> 21.476 | 3 | NO |
| 2F internal 0.15 | 7.020 | 9.640 -> 9.640 | 0 | YES: +2.620 reconciled with no residual in T-108 (height Q-60 A ENGINE_RIGHT, door height RULE_DIFFERENCE Q-55 C) |

No verdict on a section total while a wall in it is held (an equal total is never agreement, ERS s.7). Per wall: GF-W07
and 1F-W05 heights by printed depth vs his one height per floor: RULE_DIFFERENCE under Q-60 A, ENGINE_RIGHT on the
Checker's own pieces.

## 7. Rules, tests, lessons row (ERS s.4)

- **R-T228-1** (resolution ledger, any villa; provenance programme s.2 / s.5, WORKFLOW_CONTROLS s.1 / s.4 / s.5): a change
  enters only from a checker-merged package or a Checker ruling; conflicting values need a ruling; VERIFIED only from a
  ruling naming length, height (and deductions for a net); an owner fallback stays PROJECT-SPECIFIC after a re-measure;
  a range is carried as its common part + a HELD increment; every group reconciles to the gross.
- **R-T228-2** (finding hold, any villa; WORKFLOW_CONTROLS s.8, ERS s.2): new drawing evidence against an established
  figure may only LOWER it to HELD, moving the figure into the bounds text; it never writes a number or raises a class.
- Height pieces close to the census length (the Checker's 18:01 lessons row): `gross_from_pieces`.
- tests/t228_register_v2 (26): villa M (not Alsenan; hand truth in the docstring: coverage 30.000 = 10.000 + 10.500 +
  1.500 + 8.000; pieces 11.040 m2, mirror order) + adverse (unmerged worker value, VERIFIED without / with an incomplete
  ruling, conflict without a ruling, net mismatch, net on a held gross, held with a figure, duplicate piece, unknown
  wall, millimetres, finding that raises a class or writes a number, sampled pieces not closed, piece with no height) +
  Alsenan (outputs reproduce, v2 = v1 + logged merged changes only, the Checker's numbers not the worker's, the worker
  value without the ruling is not VERIFIED, GF-W10 held never 0, every group reconciles, length change = the listed
  resolutions, every HELD wall a named blocker, freelancer comparison only, no coordinates).
- Lessons row proposed: 2026-10-24 | a Checker-accepted wall net (GF-W10 47.425) rested on the storey's +1.00 floor while
  2.5 m of the wall stands on a printed +0.30 stair-foot landing under a stair landing member (plan LEVEL 4AB, section
  A-A) | the height basis was the storey datum per wall, not per piece, and the stair shaft was not searched for its own
  floor and members | each height piece takes the floor level printed on its own side of the wall and the member on its
  own line (stair landing members included); a printed level that contradicts an accepted basis holds the wall until
  the Checker rules (any villa) | tests/t228_register_v2 (finding only holds; adverse: a finding writing a number or
  raising a class refused) | PROPOSED.

## 8. For the Checker (Gate A; re-measure, never these numbers as expected)

1. F1 / F2 on P7757.dxf GF plan: inner face 26E / 2AB and 2AD / 271, column 2F7E, stub 213 / 21A, LEVEL 4AB / 4AC
   (+0.30), W05 jambs 3E2 / 3E1; section A-A on p7757_arch_sheet10.pdf: +0.30 / +0.15 at the north wall, the '320' and
   the hatched member over D-GF-09. Decide whether GF-W10's three eastern pieces (39.155 on the +1.00 basis) return.
2. Re-add v2 from v1 + the merged deltas yourself (CHANGE_LOG_V2.csv names every source): GF-W07 4.458, 1F-W05 23.223 /
   19.303, 1F-W00 12.863, 1F-W06 54.487, 1F-W10 44.929, GF-W16 15.404, 1F-W25 1.490, BAY-ENDS 0.572, P-GF-05 2.640.
3. Coverage identity per floor x thickness x type (AFTER_COVERAGE.csv) and the 1.975 m length identity.

Files: research/agents_t228/{register_v2.py, build_t228.py, BLOCKWORK_WALL_REGISTER_V2.csv, CHANGE_LOG_V2.csv,
AFTER_COVERAGE.csv, BLOCKERS_V2.csv, FREELANCER_COMPARISON_V2.csv, summary.json, this report}; tests/t228_register_v2.
Reproduce: `python3 -I research/agents_t228/build_t228.py --check` (also checks that every merge commit it cites is an
ancestor of HEAD).
