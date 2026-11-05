# T-520: B9-04 perimeter joint mortar at column faces, beam-drop sides and soffits (R-T520-1, PERIMETER_JOINT_V1)

Worker 1, lane S, claim 2026-11-05 11:23 UTC, base engine 9a28e927 (candidate of record ARCH_TAKEOFF_V3.0.58).
Research only: `perimeter_joint_v1.py` (project-agnostic rule), `t520_extract.py` (drawing reader, inputs outside the
repository), `t520_alsenan.py` (training-villa builder, `--check` reproduces), `out/` (numbers and ids only, stations
along a run, no plan coordinate), `tests/t520_perimeter_joint/`. No engine, rule, knowledge, registry or candidate
file changed; nothing released (released default V2.9 + route G). Drawings cited by Drive folder and title only.
ERS read: s.2.1 - 2.4, s.2.7 (no owner question: every open item is a drawing / supplier data item already HELD), s.3,
s.4, s.7.

## 1. Physical element (ERS s.2.1)

The mortar that fills the joint between the last block and CONCRETE: vertically at an RC column face, at the side of a
beam drop (where the member over a neighbouring length is deeper) and at a lintel end; horizontally over the last
course under the beam / slab soffit. Wall thickness b, joint j = 10 mm (owner 2026-10-29, ASSUMED - OWNER-APPROVED; no
sheet prints a joint). It is NOT a new volume beside the panel mortar: the R-T367-1 panel figure A b (1 - w h / W H)
already gives every module cell one bed and one head joint, so part of every perimeter joint is inside it. The
quantity is the INCREMENT over the panel figure (installed, wet, before waste).

## 2. Evidence (hierarchy s.2.2)

1. Drawings (decoded this run into .work/private): Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip ->
   P7757.dxf (sha ab54dd55), 675 text records, and 'ST7757 dxf.dxf' (sha 9f9d1179), 2,339 text records: 0 hits for
   joint / movement / fire / compressible / filler / sealant / foam / mastic / soffit / packing / mortar / expansion
   (and the Arabic terms for joint, fire, mortar, insulation). Independent of the T-365 census, same result. ANSWER to the
   engineering question: no movement or fire-stop detail is printed at any block-to-soffit or block-to-column junction,
   so the mortared joint of the owner's method applies everywhere; nothing is NOT_APPLICABLE on that ground.
2. Wall geometry: merged T-274 run pieces (every run cut at columns / beam bands / slab faces, member depths), the T-261
   drawn-extent pieces (1F-W13 / W17 / W18 / W24, 2F-W05; heights tied to T-274 stations within 2 mm, asserted), T-215
   junction closes (GF-W21 -0.0311, GF-W33 +0.0311 m), T-488 storeys (GF 4.50, 1F 4.20 DRAWING-CONFIRMED; 2F 4.25 - b_r,
   D-39 HELD), T-516 jamb bearings (lintel ends), T-506 wall set and buckets.
3. NEW drawing reading (`t520_extract.py`, END_CONDITIONS_T520.csv): what lies 0 .. 20 mm beyond each run end across the
   wall thickness (column outlines of the architectural plan; storey masonry of T-516). T-274 cuts a run at a column it
   CROSSES, but cannot see a column standing in the wall a run ENDS on. Four black-wall ends meet a column outside the
   run pieces (column cover 1.0000): 1F-W09 start, 1F-W23 start, 2F-W01 start, 2F-W08 start (F-T520-1 below).
4. Owner rules: Q-75 (39 x 19 face, 40 x 20 module; owner answer 2026-11-02 confirms it for 0.20 m only: T-506),
   owner 2026-10-29 10 mm joint, Q-78 A (1:4, 8 bags + 1.1 m3 sand per m3), Q-55 C (door hole 2.20 m), UP-QTY-STATUS-001.

## 3. Reconstruction (owner manual method and drawing-derived method side by side)

Owner manual method: none separate for perimeter joints; the Checker's F-T367-1 bound counts every concrete joint whole,
(L b + n H b) j (soffit length L, n column faces of height H), no module credit.

Drawing-derived method (R-T520-1), from a block count: a panel L x H between two concrete faces under a soffit holds
(L - j)(H - j) / (W H) units, not L H / (W H). With kappa = w h / (W H) = 0.0741 / 0.08 = 0.92625:
increment = kappa b j (L + H) - kappa b j^2 (one top corner). In general, per course band dz and course SEGMENT (a run
of units between two stops), the module credits ONE head joint; the joints that exist are one per end touching
concrete (C) or a mortared block face (O); a free end, jamb or glazing (F) has none. Hence: c = 2 -> +dz exact;
c = 1 with F -> 0 exact; c = 1 with O -> RANGE [0, dz] (butt or bonded T / L junction: no detail printed); c = 0 -> no
concrete junction (NOT_APPLICABLE; the panel's free-end / jamb tolerance is a different item, T-176 s.3); an unknown
stop (top not drawn, lintel bearing DEFICIT) -> HELD with bound. The soffit adds kappa b j per metre of block under a
drawn soffit. Factor kappa b j: 0.0018525 m3/m (0.20 m), 0.00138938 m3/m (0.15 m).

Why the Checker's bound is an upper bound (reconciled in units on GF-W01, bound 0.093640 vs 0.058854 m3): -7.375 % of
the whole joints because the strip was already 7.375 % mortar in the panel (kappa); -15.35 m of column face because
the module credits one face per course segment (4 segments x 3.75 + the 0.35 band of the last one); +0.35 m at the CB1
drop side (a beam side, not in the bound); -5 j^2 top corners. 0.093640 - 0.006906 - 0.028436 + 0.000648 - 0.000093
= 0.058853 (residual -0.000001 = rounding of the five terms).

## 4. Result, wall by wall (PERIMETER_BY_WALL_T520.csv; junction bands JUNCTIONS_T520.csv, 71 rows)

| Wall t | T-367 panel m3 | soffit m | vertical exact m | range m | perimeter m3 (low .. high) | % panel | Checker bound m3 | status |
|---|---|---|---|---|---|---|---|---|
| GF-W01 0.20 | 0.916919 | 16.4700 | 15.35 | 0 | 0.058854 | 6.42 | 0.093640 | COMPUTED |
| 1F-W02 0.20 | 0.039235 | 0.7000 | 3.80 | 0 | 0.008318 | 21.20 | 0.016600 | COMPUTED |
| 1F-W03 0.20 | 0.212400 | 3.9000 | 7.25 | 0 | 0.020618 | 9.71 | 0.036800 | COMPUTED |
| 1F-W09 0.20 | 0.100890 | 1.8000 | 3.80 | 0 | 0.010355 | 10.26 | 0.018800 | COMPUTED |
| **0.20 carried (= T-498 stage set)** | **1.269444** | 22.87 | 30.20 | 0 | **0.098145** | **7.73** | 0.165840 | COMPUTED |
| 0.15 carried, 15 walls (beside: module HELD) | 1.975440 | | | | 0.078582 .. 0.089890 (point 0.079138) | 4.01 | | HELD |
| GF-W22 0.15 (D-27 on its parent) | 0.143050 | 2.9795 .. 2.9825 | 0 | 0 | 0.004140 .. 0.004144 | 2.89 | 0.004331 | HELD |
| 2F-W01 / W05 / W06 / W08 (D-39) | 0.482178 | 1.80 / 1.00 / 3.90 / 3.00 | | | 0.010448 - 0.001852 b_r; 0.008966 - 0.001853 b_r; 0.021452 - 0.003705 b_r; 0.004168 (+ range 0.002015) | | | HELD |

0.15 m rows (figures beside, the 0.15 m panel itself is HELD-0.15-MODULE in T-506): GF-W19 0.003237, GF-W21 0.001379,
GF-W28 0.008485 .. 0.008763 (lintel D-GF-13 reaching the column or not), GF-W29 0.001876, GF-W33 0.001788, 1F-W12
0.005175, 1F-W13 0.006919 .. 0.008016, 1F-W17 0.002731 .. 0.003203, 1F-W18 0.012810 .. 0.018423, 1F-W19 0.002501 ..
0.002973, 1F-W20 0.008510 .. 0.009330, 1F-W21 0.002709, 1F-W22 0.007510 .. 0.007857, 1F-W23 0.011018 .. 0.012754,
1F-W24 0.001934 .. 0.002407. HELD bands by name (never 0): dome-opening pieces of 1F-W13 / W17 / W24 (top not drawn),
DEFICIT lintel ends D-1F-03 / 04 / 07 / 10 and D-GF-10 (T-516: bearing b <= a < 0.40, position not buildable as
drawn), the D-1F-09 lintel (inside the held dome piece).

## 5. Reconciliation (m3, to the named cause)

- T-498 stage (1.269444 m3 PROV, GF-W01 + 1F-W02 / W03 / W09): + 0.098145 m3 perimeter = 1.367589 m3 installed
  (+7.731 %). Same 4 walls, same 0.20 m module; cause = the joints the panel figure omits: soffit 0.042367 + vertical
  0.055779 (incl. -0.000167 for 9 top corners). Cement / sand of the increment (Q-78 A): 0.785 bags, 0.108 m3 sand, as its
  OWN producer key 'B9-04 PERIMETER JOINT MORTAR (T-520)', never inside the T-453 / T-498 panel key.
- T-367 (3.870113 m3, 24 walls, contract basis V3.0.26): GF + 1F 20 walls 3.387934 panel -> perimeter 0.180867 ..
  0.192179 m3 (point 0.181423, +5.36 %); 2F 4 walls 0.482178 panel -> perimeter HELD (D-39), expressions above. The
  Checker's 'about 0.2 .. 0.5 m3' is the whole-joint bound; at the low end because of kappa, the module credit (one face
  per segment) and the c = 1 walls (one column face only: 0).
- Wall-set causes between T-367 and T-498 are T-506's (2F D-39 0.482178, 0.15 module HELD, GF-W22 D-27, lintel faces);
  none is restated here.

## 6. Findings for the Lead / Checker

- **F-T520-1** (drawing): four black-wall run ends abut a column that is NOT a T-274 run piece (the run ends on the met
  wall's face): 1F-W09 start, 1F-W23 start, 2F-W01 start, 2F-W08 start. T-355's sharmat census (117 junctions) and
  T-317's V joints derive from the same T-274 column pieces and miss these 4 junctions (and any white-wall equivalent;
  not read here). 1F-W09 is a COMPUTED 0.20 wall: its perimeter is 0.010355 m3 with the column (0.003334 soffit only
  without it). Proposed: re-run the T-355 / T-317 junction censuses with END_CONDITIONS (lane S / A).
- **F-T520-2**: T-355 / T-317 HELD the GF-W01 @17.17 junction (2.6 mm strip between the architectural column face and
  the first drawn ST edge) and the three 1F-W18 junctions (T-261 heights 'not tied to stations'). Here: the column is
  concrete over the full storey on either reading, so the face joint exists (only its station moves 2.6 mm; the strip's
  AREA stays HELD in the area ledger); the T-261 1F-W18 pieces tie to the T-274 stations within 1.2 mm (asserted).
- Lintel perimeter joints (lintel bed at the bearings, R-T453-5 faces) are a separate HELD component: bearings are
  BOUNDED [0.40, a] or DEFICIT (T-516); only the lintel-end / column adjacency enters here (low .. high).

## 7. Verdicts

Freelancer (Drive 'Alsenan chalet project', the blockwork workbook): no mortar, cement or sand row (T-367 s.6) ->
RULE_DIFFERENCE, no numeric verdict. Checker F-T367-1 bound vs R-T520-1: ENGINE_RIGHT proposal for the method (bound
overcounts by kappa and the module credit, hand proof in tests/t520_perimeter_joint test_no_double_count: panel +
increment = the block-count joint volume to 1e-12 m3), the bound remains a valid upper limit.

## 8. Rule, test, lessons row

R-T520-1 (every villa; provenance Checker F-T367-1, T-520; research rule, not a rule-store version): perimeter joint
mortar of a mortared block wall = kappa b j x (block length under a drawn soffit + sum over course bands of
(joint-bearing segment ends - 1) dz) - kappa b j^2 per uncredited top corner, kappa = face / module; end classes C / O
/ F / U as s.3; a run end is classified from the drawing (column outline beyond the end), never from the run topology
alone; 0.15 m rows follow the panel's module status; storeys not printed stay HELD with an expression in the missing
datum; cement / sand only from a mix that names block-joint mortar (Q-78), as its own producer key.

Tests (tests/t520_perimeter_joint, 27): villa P520 by hand (wall A 3 columns / 2 segments / 1 soffit 0.02034045 m3,
wall B soffit only 0.003705), panel + increment = block-count truth for 3 lengths and the one-face case, one face + free
end 0, one face + block wall RANGE, beam-drop side face, mirror, held datum blank, held piece named, unnamed held refused,
opening position invariant inside a segment, lintel reaching a column = low scenario, unknown bearing HELD, mm / joint
units refused, module and masonry mix required, an opening reaching a soffit refused; Alsenan pins (reproduce, 24 walls
once, GF-W01 / 1F-W03 / 1F-W09 by hand, T-498 sum, held rows blank by name, drawing-read column ends, own material key,
stations only).

Proposed lessons row (ERS s.7): | 2026-11-05 | A column-face junction census (T-355 / T-317) missed 4 columns at wall
ends, and the perimeter-joint bound counted joints the panel mortar already held | a run's column pieces were taken as
every column the wall touches; a bound counted whole joints with no module credit | classify every run end from the
drawing (what lies beyond the end face), and measure a perimeter joint as the increment over the panel module (block
count), with c / o / f end classes per course segment (every villa; T-520) | tests/t520_perimeter_joint (column at a
T-stem end; one face + free end = 0; panel + increment = block count) | PROPOSED |

## 9. For the Checker (re-measure 2 junctions)

- GF-W01 last segment (column face 17.87 .. column 19.17): block 1.30 m under B1 (4.10) over 1.1477 m and CB1 (3.75)
  over 0.1507 m: vertical 3.75 (c = 2) + 0.35 (band 3.75 .. 4.10 between the column and the CB1 side) = 4.10 m; soffit
  1.30 m; increment (4.10 + 1.30) x 0.0018525 - 2 x 0.0018525 x 0.01 = 0.009966 m3.
- 1F-W09 (column at BOTH ends; the start one from the drawing): 1.80 m under B1 (3.80): (3.80 + 1.80) x 0.0018525 -
  0.0018525 x 0.01 = 0.010355 m3. Own check of the start column: P7757.dxf, the column outline at the T-stem end of band
  WB-FL0024-FL0025 on the 1F plan.
