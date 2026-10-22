# T-175: opening deductions by physical scope (blockwork, plaster, paint, reveals, sills, thresholds, lintels)

Worker 2, 2026-10-22 13:47 - 14:05 UTC, run session_013nud3o8krkp4hSffAL8Hbn. Lane A, gate 2. Owner rule Q-73 (CONFIRMED
2026-10-22, final): "Deduct the full area of every actual opening from the relevant blockwork. Apply the rule only to
masonry that physically exists. Measure reveals separately where applicable and prevent double counting." New opt-in
module OPENING_SCOPE_V1 (`engine/source/opening_scope_v1.py`, imported by nothing, not wired); no released quantity, rule
file, frozen method or registry changed. Development villa (Alsenan), not an accuracy claim. No drawing, client name or
personal data committed; drawings are cited by Drive title. ERS: read; sections 2 (element, evidence, reconstruction,
reconciliation, status), 3 (build before deduct; physical vs payable; installed vs procurement) and 4 (quantity + rule +
test) applied.

## 1. Result in engineering terms (development villa, block walls, m2)

| Floor | Gross block, T-143 (Q-60 A x Q-69 B) | Established deductions | HELD openings inside the gross | Gross less established deductions (not a net) | Walls with a net now | their gross -> net |
|---|---|---|---|---|---|---|
| GF | 460.071 | 26.160 (12 doors 23.760 ASSUMED — OWNER-APPROVED + W01 2.400 DRAWING-CONFIRMED) | 14 (16.00 m of width) | 433.911 | 25 of 40 | 296.433 -> 278.833 |
| 1F | 371.829 | 31.705 (10 doors 19.140 + W13 / W14 / W15 / W18 12.565) | 10 (9.10 m) | 340.124 | 14 of 26 | 152.141 -> 144.221 |
| 2F | 123.727 | 7.980 (3 doors 5.940 + W26 2.040) | 4 (3.80 m) | 115.747 | 4 of 9 | 54.916 -> 53.156 |
| **All** | **955.627** | **65.845** (25 doors 48.840 ASSUMED — OWNER-APPROVED; 6 windows 17.005 DRAWING-CONFIRMED) | **28 (28.90 m)** | **889.782** | **43 of 75** | **503.490 -> 476.210** |

Net of the 43 walls by evidence status (WORKFLOW_CONTROLS s.5; HELD never 0):

| Status | Walls | Net m2 | Net m3 (x drawn t) | By type / thickness |
|---|---|---|---|---|
| DRAWING-CONFIRMED (no opening in the wall; gross CALCULATED) | 24 | 271.592 | 48.282 | black 0.15: 120.727; black 0.20: 107.715; white 0.20: 43.150 |
| ASSUMED — OWNER-APPROVED (door heights Q-55 C 2.20) | 8 | 86.470 | 13.250 | black 0.15: 80.880 (7 walls); white 0.20: 5.590 (GF-W05) |
| HELD: net computed on a PROVISIONAL gross (annex datum Q-54 B / lift tie beam note 19) | 11 | 118.148 | 21.415 | black 0.15: 44.288; black 0.20: 48.966; white 0.20: 24.894 |
| HELD: net not computed (a held opening or a partly held gross) | 32 | - | - | per row in T175_NET_BLOCK_BY_WALL.csv, with bounds where they exist |

Before this task the net block was HELD on every one of the 75 rows (no Urban masonry opening rule). Now 32 walls carry a
net with a s.5 status (358.062 m2, 61.53 m3), 11 more a net on their provisional gross, and every held one says why.

Against the freelancer: his block deductions total **122.39 m2** (doors 60.96 + windows 61.43, BLK sheet rows 41-51,
84-90, 111-115, 185-192, 222-223); ours established **65.845 m2** + 28 HELD openings. Reconciled in units in section 5.

## 2. The physical element and the rule (standard s.2 step 1, s.3)

One opening id has SEPARATE consequences, each in its own unit and owned by its own trade line, never merged:

| Consequence | Unit | Rule / evidence | Built-before-deduct condition |
|---|---|---|---|
| masonry deduction | m2 | Q-73: full opening area w x h | only if the host line is BLOCK and the opening lies INSIDE the measured gross run |
| plaster / paint / wall-tile deduction, per face | m2 | Q-73 + UP-GEN-003 (tile gross - openings); UP-OPEN-SCHED-001 caps it at the finish band top when the finish method gives one | a face exists (not on a glazed line) |
| reveal | m.l (+ depth) | Q-73 "reveals separately"; Q-64 B (no double count with the facade run) | length = 2 jambs + head (+ sill for a window); depth = wall thickness only when no frame is set in it, else HELD (frame position not on any plan; WIN-REVEAL finish still queued) |
| sill (window) / threshold (door, passage) | m.l | UP-CER-003 (skirting deducts door widths), Q-06 (wet thresholds marble) | width only |
| waterproofing interface | - | UP-WP-002 v2.0.0 / UP-GEN-003: the upturn runs across a wet doorway, NOT deducted | wet side (W.C., bath, wash / basin, laundry) |
| lintel band | m2 face, candidate | ST7757.pdf p.13 LINTEL SCHEDULE (depth by width band; "MIN.40cm" bearing), research/alsenan_lintels_s8_6 | concrete, not masonry: listed for the lintel line, never netted silently here |

Classes of host (what is physically built around the opening), Alsenan:

| Host | Openings | Masonry deduction |
|---|---|---|
| BLOCK, inside the gross run | 59 (27 doors, 26 windows, 2 arches, 3 lift-shaft openings, 1 passage) | yes (31 established, 28 HELD) |
| GLAZED line (the glazing span is already out of the Q-69 B physical run) | W02 saloon 6.33 (GF-W11), W03 curved pool glazing 6.57 (GF-W37), W17 concave bay 3.29 (1F-W25) | NO: no masonry is built there; deducting again would be a double deduction |
| BLOCK, outside any measured run | SX-01 4.521 and SX-03 1.00 (pool-court walls: no T-143 row carries their piers), P-1F-01 1.30 (the hand runs 1F-W14 / W15 stop at it) | NO (not in the gross); SX-01 / SX-03 finishes and reveals stay HELD |
| NONE (no building wall) | D-GF-15 fence gate, U-01 (identity not established), P-GF-02 .. P-GF-05 open sides 1.40 / 1.00 / 11.22 / 1.20 (split-out stretches, the Q-67 side passage) | NO |
| RC | none on this villa (the test fixture covers it) | NO masonry; finishes deducted |

## 3. Reconstruction (standard s.2 step 3), the binding and what it found

Binding (`build_hosts.py`, output `T175_OPENING_HOSTS.csv`): engine opening id (T-150 ENGINE_REF, ARCH_TAKEOFF_V2.12 on
P7757.dxf sha256 ab54dd55) -> the MASONRY_CENTRELINE_V2 run that carries it -> the T-143 row whose v2_runs lists it; five
closure doors by the V2 free-end doorway records (door element 0.41 .. 0.51 m from the wall end); glazed lines and
outliers by hand with the evidence in each row. Every engine opening (60: 59 band openings + 1 curved) is accounted for once
(the builder refuses otherwise). Check per row: the census widths inside a run add up to the hand plan-cut gaps
(T-143 L1 - L2b) within 0.011 m on 30 of the 36 rows that host an opening.

Residuals on the other 6 rows (none changes the gross, which runs through the openings; L2b is reference only in T-103):
- GF-W04 +0.15 (W04) and GF-W14 +0.20 (P-GF-01), traced on the DXF: the hand gap was read
  on the face where a cross wall ends against the jamb (W04: south face gap -0.45 .. +0.30 = 0.75, north face and the
  window frame -0.30 .. +0.30 = 0.60; P-GF-01: 1.10 on the east face where a 0.20 wall meets, 0.90 jamb to jamb on the
  west face). The masonry opening is the jamb-to-jamb gap on the face that has both jambs; the cross wall's end is that
  wall's masonry. Census widths kept.
- 1F-W06 +0.152, 1F-W10 +0.15, GF-W32 +0.178: NOT traced to a cause this run. The jambs of W19, W20 (1F-W06) and W21
  (1F-W10) were checked on the DXF: clean 0.60 jamb lines on both faces, so the extra gap of the hand table lies elsewhere
  in those runs (likely the same cross-wall reading at another jamb). Census widths kept; for the Checker.
- 1F-W04 +1.357 (W13 1.20 printed): the stair west wall's drawn faces stop short of the node (T-103 note); not an opening.

Found and fixed in this ledger (reported to the census owner, T-150; no T-150 quantity changes because its area is w x h):
- **Two openings missing from the T-150 census**: P-GF-01, a 0.90 doorless opening with head lines in the GF stair-hall
  wall (inside GF-W14's gross: its deduction is HELD, height not printed) and P-1F-01, a 1.30 doorless opening with head
  lines in WB-FL0022-FL0023 (outside the hand runs). Both need reveals and finish deductions once their heads are known.
- **Sill basis mixed in the T-150 SILL_M column**: W01 carries 1.85 (the chain part from +0.15) and W03 1.00 (a level).
  Above the finished floor they are W01 1.00 (sill +2.00 - GF FFL +1.00, head 3.00) and W03 0.00. The module's
  HEAD_ABOVE_SOFFIT guard caught W01 (1.85 + 2.00 = 3.85 > the 3.75 clear height of GF-W15). Corrected here
  (`SILL_ABOVE_FFL_M`), evidence in the row.
- **A block scope gap**: the pool-court east-wall piers (0.632 + 0.247 m, T-154) and the north pier are in no T-143 row:
  masonry that exists and is not measured (for the block lane; not added here).

Hand examples (Checker re-derives two walls, acceptance):

| Wall | Gross (T-143) | Openings | Net |
|---|---|---|---|
| GF-W32 (black 0.15, W.C. core) | 12.726 m2 | D-GF-11 0.80 x 2.20 + D-GF-12 0.80 x 2.20 = 3.520 | **9.206 m2** ASSUMED — OWNER-APPROVED |
| 1F-W23 (black 0.15) | 23.968 m2 | D-1F-02 1.00 x 2.20 + D-1F-04 0.80 x 2.20 (free-end doorway) = 3.960 | **20.008 m2** ASSUMED — OWNER-APPROVED |
| GF-W05 (white 0.20, pantry outer wall) | 7.790 m2 | D-GF-06 1.00 x 2.20 = 2.200 | **5.590 m2** ASSUMED — OWNER-APPROVED |
| GF-W15 (white 0.20, entrance front) | 28.632 m2 | W01 1.20 x 2.00 = 2.400 DRAWING-CONFIRMED; D-GF-07 HELD (render F07c, candidate 5.000) | HELD, <= 26.232 |
| 1F-W00 (white 0.20, sea side) | 22.932 m2 | W15 1.55 x 3.10 = 4.805, W18 0.50 x 2.16 = 1.080; W16 HELD (D-45) | HELD, 11.700 .. 17.047 (bounds, not a quantity) |

Bounds (columns `net_bounds_m2`) are mathematical limits: the gross minus the established deductions (upper) and minus
each held opening's width x the clear height under the member above (lower). They are never a quantity.

## 4. Finishes, reveals, sills, thresholds, lintels (same ids, separate lines)

All floors (per opening in T175_OPENING_CONSEQUENCES.csv; full opening area, before the finish method's own band cap):

| Line | ASSUMED — OWNER-APPROVED | DRAWING-CONFIRMED | HELD |
|---|---|---|---|
| internal plaster / paint face deduction | 26 faces, 52.580 m2 | 5 faces, 15.925 m2 | 23 faces |
| external plaster / paint (Sigma) face deduction | 6 faces, 12.760 m2 | 6 faces, 17.005 m2 | 25 faces |
| wall-tile face deduction (wet side) | 18 faces, 32.340 m2 | 1 face (W18), 1.080 m2 | 11 faces |
| lift-shaft inside face | - | - | 3 faces (finish not specified) |
| reveal length | 25 openings, 132.20 m.l | 8 openings, 77.24 m.l (incl. the glazed lines W03 21.74 and W17 13.58: frame returns of the glazing, not masonry reveals) | 38 openings |
| reveal depth | frameless openings: the wall thickness (DRAWING-CONFIRMED); framed: HELD (frame position) | | |
| thresholds | 42.22 m.l (doors, arches, passages with a known width) | | |
| sills | 39.09 m.l (windows with a known width; material not specified) | | |
| wet doorways, upturn NOT deducted | 15 (UP-WP-002 v2.0.0) | | |
| lintel faces (structural lintel line, not masonry) | candidates at the printed MIN.40cm bearing: 31 openings, 11.345 m2, HELD (actual bearing limited by the masonry beside each jamb, research/alsenan_lintels_s8_6 06_LINTEL_CONCRETE_QTO) | | |

The finish deductions here are the full opening; the plaster / paint method (T-128, both methods side by side) applies
UP-OPEN-SCHED-001 with its own band top H (the module takes `finish_top_m` per face and caps there; test
`test_finish_band_cap_up_open_sched_001`). The owner manual method and the drawing-derived method keep their own H.

## 5. Reconciliation with the freelancer (standard s.2 step 4, units first)

| Item | Freelancer (his rows) | Ours | Difference | Cause | Verdict proposal |
|---|---|---|---|---|---|
| door count in block walls | 27 (incl. the main entrance) | 27 (incl. D-GF-07 and D-GF-14 HELD) | 0 | - | AGREE |
| door widths | 25.40 m | 25.00 m | +0.40 m | by wall group: his GF external 4 x 1.00 + 20 cm internal 4 doors; ours GF external 5 (1.00 / 0.90 / 1.00 / 1.00 / 0.90) + 20 cm 3 (one door is in another wall group in his sheet); his 1F 15 cm 4 x 0.80 + 4 x 0.90 vs ours with two 1.00 doors (D-1F-02, D-1F-03, jamb to jamb) | UNRESOLVED per door (his rows carry no door ids); totals within 1.6 % |
| door height | 2.40 on every door | 2.20 (Q-55 C), 2.50 printed main entrance | 22.20 m x 0.20 = 4.44 m2 on the 25 established doors | owner fallback vs his unprinted 2.40 | RULE_DIFFERENCE (T-150 verdict, unchanged) |
| doors m2 | 60.96 | 48.84 established + main entrance candidate 5.000 + master bath 1.518 .. 1.760, HELD | -12.12 m2 on the established set | height 4.44 + main entrance + master bath held + width +0.40 m x 2.40 | as above |
| 6 windows with printed heights (W01, W13, W14, W15, W18, W26) | 17.230 m2 (1.20 x 2.00, 1.20 x 2.00, 2.45 x 2.00, 1.55 x 3.00, 0.60 x 0.80, 1.20 x 2.00) | 17.005 m2 (2.400, 2.760, 3.920, 4.805, 1.080, 2.040) | -0.225 m2 (-1.3 %) | W13 2.30 / W14 1.60 / W18 0.50 x 2.16 / W26 1.70 printed vs his unprinted 2.00 / 0.80; W15 crown (Q-32 A) vs his springing 3.00; W01 agrees | ENGINE_RIGHT on W13, W14, W18, W26 (printed chains, T-144); RULE_DIFFERENCE W15 (Q-32 A); AGREE W01 |
| concave glazed bay W17 | deducts 3.15 x 3.00 = 9.45 m2 from his 1F external walls | 0: its glazing span is not in the physical run (1F-W25 L2a 0.537) | -9.45 m2 | build before deduct: no masonry there | ENGINE_RIGHT on our basis; whether his 1F lengths carry the bay span is not established from his unlabelled lengths: UNRESOLVED on his side (possible double deduction) |
| 21 other windows | 34.75 m2 at heights no sheet prints (0.80 / 2.00 / 3.00) | HELD (26.53 m of width; designer D-45 window schedule) | not comparable | his heights are not drawing evidence | UNRESOLVED (designer), never his number |
| saloon glazing W02, pool glazing W03 | no deduction (his runs leave the glass lines out) | no deduction (spans out of the physical run) | 0 | same physical basis | AGREE |

Residual not explained in units: the door-width split by wall group (+0.40 m) needs his door-by-door identity, which his
sheet does not give.

## 6. General rule, regression test, lessons row (standard s.4)

- **Rule (any villa; provenance: owner Q-73 CONFIRMED + standard s.3; Urban rule, new, not a project fact):** an opening
  is deducted from masonry only where masonry is physically built in that line AND the opening lies inside the measured
  gross run; the deduction is the full opening area (width jamb to jamb on the face that carries both jambs x height
  above the finished floor); the same id separately yields per-face finish deductions (capped by the finish band per
  UP-OPEN-SCHED-001), reveal m.l (+ depth: wall thickness only when frameless), a sill or threshold m.l, the wet
  doorway's upturn kept, and the lintel face as a concrete item of the lintel line. A held width or height holds the
  wall's net (bounded, never 0). Not yet a rule-registry version: proposed for the Lead as UP-OPEN-MASONRY-001 v1.0.0
  (a new rule version file, never an edit of UP-GEN-003 v1.1.0).
- **Tests:** `tests/t175_opening_scope/test_opening_scope.py` (16 cases: 20 m2 wall with a 3 m2 window -> 17; adverse:
  full-height glazed bay -> no block, no deduction; opening in an RC wall -> no block deduction, finishes kept; held height
  -> net None with bounds; opening outside the run -> not deducted again; head above the soffit -> capped and flagged;
  millimetres refused; non-s.5 status refused; one opening twice or on two walls refused; deductions above the gross
  refused; finish band cap; mirror) and `test_alsenan_ledger.py` (the committed ledger reproduces; invariants).
- **Lessons-register row proposed:** 2026-10-22 | Block net HELD on every wall; risk of deducting glazing from walls that
  never contained it | No masonry opening rule; opening census not bound to the wall runs | Build before deduct: bind each
  opening to its host run and gross first; deduct only masonry that exists inside the run (any villa) | T-175
  test_opening_scope (adverse: glazed bay, RC wall, outside-the-run) | READY (T-175), Checker to verify.

## 7. Held, unknown, missing (never 0)

- 28 openings inside a gross run with no established area: 21 windows with no printed head / sill (designer D-45), main
  entrance (photo F07c / D-53, candidate 5.000), GF master bath door (width 0.69 .. 0.80), 2 leafless arches (head not
  printed), 3 lift-shaft openings (lift CANDIDATE, UP-DOOR-CLS-005; head not printed), P-GF-01 (head not printed).
- Walls whose gross is PARTLY HELD / HELD in T-143 (member conflicts, dome openings, unlabelled beams) or PROVISIONAL
  (annex datum Q-54 B, lift tie beam): their net stays HELD by that cause.
- Reveal depths of framed openings (frame position), sill and threshold materials, lintel lengths beyond the minimum
  bearing, the pool-court piers' block scope, P-1F-01 / P-GF-01 in the census.
- T-150 is READY, not yet verified: its widths, heights and statuses feed this ledger unchanged except the W01 / W03
  sill basis; if the Checker changes a T-150 value, rerun `alsenan_t175.py` (it reads only committed files).

Files: `T175_OPENING_HOSTS.csv` (binding, one row per opening, 71), `T175_OPENING_CONSEQUENCES.csv` (every consequence
per opening), `T175_NET_BLOCK_BY_WALL.csv` (75 rows: gross, openings, deductions, net, bounds, s.5 status),
`summary.json`, `build_hosts.py` (scratch inputs, read-only Drive run), `alsenan_t175.py` (repository inputs only;
`--check` reproduces the three files byte for byte).
