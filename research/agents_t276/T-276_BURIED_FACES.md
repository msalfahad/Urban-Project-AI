# T-276 Buried-concrete liquid waterproofing r2: every buried face traced once (Alsenan; rule for every villa)

Worker 2 (lane A), 2026-10-24, run session_01KC3nKr8LoBDJ22DkmR2iRn (r1); r2 narrow rework 2026-10-24 21:45 UTC (run
unknown) of the Checker rejection of 2026-10-24 20:59 (gate e / h). Research ledger + unwired modules, NOT wired into
any method version: released ARCH_TAKEOFF_V2.9 + route G and the V3.0.x candidate are unchanged; nothing released.
Drawings named by Drive folder and title; members by DXF handle / run id; values only (no coordinates, no client data).
Builds on T-263 (MERGED c0ab564d, R-WP-BURIED-1); T-219 faces (footing underlay / sides, lift pit) are never counted.
ERS applied: s.2 steps 1-4, s.3 (each face once; build before deduct), s.4 (rule + test), s.7 (lesson row).

Files: `t276_extract.py` (drawing read, writes `ALSENAN_FACE_TRACE.json`, values only), `face_trace.py` (the boundary
walk, shapely), `buried_faces_v2.py` (rules, stdlib, imports T-263's `buried_wp_v1`), `t276_alsenan_check.py` (runner,
committed inputs only), `LEDGER_T276.csv` (one row per traced face piece), `SIDE_COMPARE_T276.csv` (per run side:
run length vs traced length and what stands beyond the face line), `NECK_ZONE_T276.csv`, `summary.json`; tests
`tests/t276_buried_faces` (villa P by hand, mirrored and rotated, adverse cases, Alsenan pinned).
Repeat: `.work/venv/bin/python -I research/agents_t276/t276_extract.py <ST7757 dxf.dxf>` then
`python3 -I research/agents_t276/t276_alsenan_check.py [--write]`.

## 0. r2: the Checker's two defects, the rule behind them, and the re-trace (governs every number below)

Checker 20:59 (own analytic re-measure on 'ST7757 dxf.dxf'): (1) band 177+7CD frames into ring ARC 158 with its two
edge LINES ending on r 2.550 at 220.32 / 211.97 deg, but the span polygon was cut square at the shorter edge's station:
an invented earth pocket on GS-23 (+0.3708 m of 'convex face' DC, a 0.2799 m 'end face', side A 0.219 m short);
(2) the 'band strip beside COL:255' (0.5948 m2 DC) is a 0.052 mm drafting offset: the 0.70 m face is COL:255's own.

Root cause (physical element first). `pair_straight` gives a band as the OVERLAP of its two edge lines; the plan solid
was built from those overlaps. Wherever a member's two edges end at different stations (oblique or curved carrier,
staggered columns, a re-entrant corner) the concrete between the square cut, the longer edge and the carrier was lost,
so the boundary walked round a notch that is not there. Separately, owners thinner than a drafting tolerance were
treated as members. Same construction everywhere, so r2 re-traces every band, not only the two the Checker found.

Rule R-WP-BURIED-1.1 r2 (any villa; provenance Checker 2026-10-24 20:59 on this set; research rule, not yet a
registry version):
- A member ends on its carrier's drawn face on EACH of its own edges (`face_trace.close_band_ends`): an edge end on
  other drawn concrete (within SNAP_TOL 1 mm) is closed there; an edge end in the open runs along its own line to the
  first concrete within one band width (else OPEN, nothing added); the restored piece = band rectangle beyond the
  overlap MINUS all other drawn concrete, admitted only when ENCLOSED by the strip, other concrete and the band's own
  edges (else, with one band width more for a re-entrant corner; else OPEN, held by name). A span END face is admitted
  only at a closed end (`buried_faces_v2.check_end_face`: a square cut at the shorter edge is refused).
- SNAP_TOL = 1 mm: an owner polygon thinner than 1 mm is a drafting offset, never a member (`face_trace.check_owners`
  refuses it); its boundary steps fall to the member it lies against. The traced solid is closed by 0.5 mm only (r1:
  T-242's 5 mm, which also filled the acute wedge ARC 158 / LINE 7C3 over ~25 mm of arc); T-242's 29 panels are still
  reproduced from T-242's own construction first (ids, areas, bordering runs), then mapped to the r2 solid.
- Steps 1 mm (r1 5 mm); a step's face is the side line NEAREST to it (r1 gave the 12 mm at each corner of a free end to
  the sides: 1811+1812#1 end 0.276 -> 0.300 m); a column perimeter step is covered when the point 1 mm outside its face
  is within 0.5 mm of another member (r1: any member within 2 mm, +2 mm cover per corner: COL:220 0.304 -> 0.300 m).

Band ends re-traced (ALSENAN_FACE_TRACE.json `band_end_closures`; edge stations apart, restored plan area): 177+7CD end
on ARC 158 219.1 mm, 0.0313 m2; 17E+17F start at COL:1EF 220.2 mm, 0.0242 (a piece, no span ends there); 17E+17F end
on 176+7E6 300 mm, 0.0450; 180+181 start on 176+7E6 300 mm, 0.0450; 180+181 end on 180D+180E 189.6 mm, 0.0450 (LINE
181 drawn 110.4 mm short of LINE 180D: closed along its own line, named); 1811+1812 start under COL:1E8 500 mm,
0.0250; 170+7C3 end over COL:17C0 to COL:1E8 300 mm, 0.0492; 182+183 start into the re-entrant corner of 15D+7C8 /
170+7C3 69.9 mm, 0.0318 (needed the corner room). All 8 CLOSED, 0 OPEN, no two restorations overlap. 28 sub-mm slivers
(2.5 .. 36.7 mm2, 0.3 .. 1.0 m long, e.g. COL:255 / 7D0+FC 36.7 mm2) are listed, not members. Panels lose the
invented pockets: GS-17 -0.0899, GS-25 -0.0450, GS-22 -0.0317, GS-23 -0.0312, GS-20 -0.0241 m2; GS-10 +0.0002, GS-06
+0.0001 (the wedges); one void of 0.013 m2 between five members stays below the 0.05 m2 panel limit (named, UNKNOWN).

Result (DRAWING-CONFIRMED unless stated; D 0.95 / 0.40 and slab 0.10 reused from the merged T-253 / T-263 verdicts):

| Item | r2 | r1 | Checker own 20:59 | Cause of r1 -> r2 |
|---|---|---|---|---|
| Ring ARC 158 building face, GS-10 | 4.2460 m | 4.2197 | 4.2490 | wedge at LINE 7C3 no longer closed (+0.0263 m) |
| Ring ARC 158 building face, GS-23 | 1.6569 m | 2.0191 | 1.6565 | pocket closed: 177+7CD frames into the ring (-0.3622 m) |
| Ring building face | 5.9029 m x 0.85 = **5.0175 m2** | 5.3030 | 5.9055 m, 5.0197 m2 | -0.04 % vs Checker (64-chord arc, 1 mm steps) |
| COL:255 north face | 0.699 m NECK, HELD | 0.5948 m2 beam DC | 0.700 m column face | 0.05 mm offset is not a member |
| 170+7C3#2 side A on GS-22 | 0 (182+183 frames in over 0.265 m) | 0.2549 m, 0.2167 m2 | not sampled | same construction, found by the re-trace |
| 7D0+FC#1 side B | GS-07 2.4998 + GS-05 0.1740 = 2.6738 m | 2.6744 | 2.675 | agrees |
| 7D0+FC#3 side B on GS-15 | 3.1008 m, 2.6357 m2 | 3.0991 | 3.100, 2.6350 | agrees |
| 17C+7E3#1 lift-ring end pieces | 1.2999 + 1.3000 m (+ sides 1.9269 x 2) | 1.295 x 2 | 3.228 m per side | agrees (3.2268 / 3.2269) |
| **WP.BURIED ground-beam faces DC** | **45.4682 m2** (77.805 m, 32 pieces) | 46.5208 | bound <= 45.6108 (+0.0249) | -1.0526 m2, below |
| HELD faces | 118 pieces, 244.283 m | 125, 245.339 | - | pockets and invented end faces gone |
| EXCLUDED above ground | 17 pieces, 51.771 m | 18, 51.633 | - | 170+7C3#4 notch closed (outside face 3.55 m) |
| Column faces on a boundary (neck line, HELD) | 33.349 m | 33.936 | - | |
| Neck beam-zone deduction DC | 13 necks, 16.5604 m2 | 14, 18.853 | C11 not re-measured | COL:255 1.90 -> 1.305; COL:238 HELD (its 0.30 m face is 114+115+7DF#1's, depth held: r1 used a 13.5 mm2 sliver's depth); COL:17BA 1.042 -> 0.877 (outer face free on GS-10, as the trace has it); 1 mm corners |

r1 46.520845 -> r2 45.468200 m2 (-1.052645), every step to its cause: -0.594830 COL:255 offset = neck face; -0.307870
ring GS-23 pocket; -0.216660 170+7C3#2 A on GS-22 (182+183 frames into the corner); +0.022360 ring GS-10 wedge;
+0.013770 170+7C3#4 A on GS-10 (other face of the wedge); +0.030585 1 mm steps and slivers no longer owners, over 26
faces, none above 0.007 m2. Residual 0. Against the Checker: its bound 45.6108 on r1's construction, + 0.0249 (its
GS-10 4.2490) + 0.0068 (its GS-23 1.6565 vs r1 - 0.3708 = 1.6483) = 45.6425 on its own ring reading; r2 45.4682 =
45.6425 - 0.2167 (the 182+183 corner, same rule, outside its sample) - 0.0022 (ring 5.9029 vs 5.9055 m) + 0.0138 (the
7C3 face of the wedge) + 0.0306 (1 mm steps / slivers): residual 0.0000.

Engine vs freelancer: no line in released A / V3.0.14, no row in the freelancer's workbook: -45.468 m2 each
(FREELANCER_WRONG omission, engine silent), no %. Verdict proposal unchanged (ENGINE omission + FREELANCER_WRONG); r1's
46.521 is superseded (RULE_DIFFERENCE inside our own work: square-cut strip vs closed member ends).

Tests r2: tests/t276_buried_faces/test_band_end_closure.py (villa Q, not Alsenan, by hand: a band on a curved carrier
closes on the arc, restored area = int (-sqrt(R^2 - y^2) + 2163.33) dy, sides 3.8367 / 4.0558 m, END only at the free
end, mirrored and rotated identical; a band into a re-entrant corner (quadrilateral by hand); a ray closure 110 mm;
ADVERSE: square cut at the shorter edge leaves an invented end face and `check_end_face` refuses it; an edge 400 mm short
of any carrier stays OPEN; a 0.05 mm column offset kept as an owner is refused and the face goes to the column, while a
2 mm strip IS a member); test_alsenan_ledger.py re-pinned with the r1 -> r2 reconciliation above.

Lessons row proposed (s.7): 2026-10-24 | T-276 r1 built the ground-beam solid from band overlaps: 177+7CD framing into
ring ARC 158 left an earth pocket (0.3708 m of ring face + a 0.28 m end face), 182+183 into a re-entrant corner coated
0.255 m of 170+7C3; a 0.05 mm offset strip took 0.595 m2 of a column face | A member ends on its carrier's drawn face on
each of its own edges; a square cut at the shorter edge invents an earth pocket and an end face; a sub-mm offset between
outlines is not a member | close every band end on its carrier per edge (enclosed, else OPEN by name); SNAP_TOL 1 mm for
members; check every band end, not the sampled one (any villa; every face-tracing trade: waterproofing, formwork,
plaster) | tests/t276_buried_faces/test_band_end_closure.py (adverse: square cut refused; sliver owner refused) |
PROPOSED.

Checker re-measure list r2 (not in its 20:59 sample): 182+183 start: LINE 182 on 15D+7C8's face, LINE 183 on 170+7C3's
face, 69.9 mm apart, 0.265 m of 170+7C3#2 side A (LINE 7C3) covered, restored 0.0318 m2; 17E+17F end into 176+7E6 at
45 deg: 0.424 m of 176+7E6#1 side B (LINE 7E6) covered on GS-25 (0.30 / sin 45), restored 0.0450 m2.

Sections 1-7 below are the r1 text; where a number there differs, this section governs.

## 1. Source read this run

Drive "Alsenan chalet project" / "ST7757 dxf.dxf" (sha 9f9d1179, = the route G input), GROUND BEAMS PLAN frame:
layer-1 band edges and the 4 arcs, S-COL.BON outlines (36), S-BW lift ring; FOUNDATION PLAN S-COL.BON outlines (36,
moved by the frame pitch) for the neck pairing. The bands, spans, columns, arcs, ring and the 29 slab panels are rebuilt
with T-242's own code path; every panel GS-01 .. GS-29 reproduces T-242's area and bordering runs (the run stops
otherwise). Second drawing: the architectural room cover on the panels (T-242, P7757.dxf placed by its 14 LEVEL marks):
GS-10 Master bedroom 1.000, GS-23 living 0.9885 (used for the ring side, section 3).

## 2. The physical element and the gap T-263 left (ERS s.2.1)

In plan the ground-beam system is one solid of concrete (straight bands, curved bands, the columns standing in them,
the lift ring). Earth can stand only against its BOUNDARY: each slab-panel hole (the fill under the slab on grade) and
the outer boundary (ground outside). Where a beam frames into another beam's face, or a column stands against it, the
face has concrete against it. T-263 measured each run's two faces on the run's face-to-face length and took each
side's panel from the middle 80 % of the run: so (a) the 0.30 m under every tee was coated, (b) a side bordering two
panels was held whole when one of them is held, (c) junction / GAP pieces and the ring's building side were not traced.

Method (R-WP-BURIED-1.1, proposed): walk every boundary in 5 mm steps, give each step to the ONE drawn member nearest
to it (span side A / B by the band frame and the drawn face LINE handle, span end, curved band, column, band piece in no
span, lift ring); the pieces of a boundary sum to its length (checked, 1 mm), no piece has two owners. Height per piece
by R-WP-BURIED-1 (T-263): panel side D - 0.10 slab; outside max(0, N.G. - soffit). Which side a face looks into is the
boundary it lies on, never "convex" / "concave" by assumption.

Closure: 32 boundaries (29 panels, main house, annex, lift pit), 424.9337 m of face = 79.0318 DRAWING-CONFIRMED +
245.3391 HELD + 51.6334 EXCLUDED above ground + 14.9932 lift ring (T-219) + 33.9362 column faces (neck line). Max
distance step -> member 2.9 mm. One sliver hole of 0.0128 m2 between five members is below the 0.05 m2 panel limit
(T-242): a drafting void, its faces not traced (named residual, UNKNOWN, < 0.6 m of face).

## 3. Results per acceptance item

**Ring building-side face (ARC:157+158, main house).** The CONVEX face (arc handle 158) is the boundary of panel holes
GS-10 (4.2197 m) and GS-23 (2.0191 m); the CONCAVE face (157) lies on the outer boundary (6.5648 m, the pool court, T-242
"ring round the pool court"). Second drawing agrees: the architectural rooms cover GS-10 (Master bedroom) 100 % and
GS-23 98.85 %. So the building side is CONVEX: 6.2388 m x (0.95 - 0.10) = **5.3030 m2 DRAWING-CONFIRMED** (D 0.95 at the
N.G. datum, T-253, the basis of the 11 main exterior faces T-263 released); T-263 readings were 5.4979 (full convex arc
6.4681) / 4.8508: the traced length is 0.229 m shorter (columns CN 17BA / 17BD stand in the band). Concave face EXCLUDED
(soffit +-0.00 at natural ground: a plinth face to the court, 6.2366 m2 shown). Annex arc ARC:139+13A: concave face on
the Majlis panel GS-02 1.5699 m, convex outside 2.04 m: both HELD (annex depth CONFLICT D-35).

**Column / GAP pieces split into beam / neck / column faces.** 36 columns: every perimeter piece is assigned (beam framing
in, another column, the lift ring, free on a panel, free outside), NECK_ZONE_T276.csv. Column faces on a boundary
(33.9362 m) belong to the NECK line (T-205: the neck runs footing top -> ground-beam top and owns the footprint through
the beam depth): HELD with the neck height, never in the beam line (refused in code). Band pieces in no span: 29 pieces;
those with a free face are beam faces of their own band: 17C+7E3 lift-ring end 2 x 1.295 m (0.7769 m2, = T-263's
run-length value for that run within 0.002), the strip of band 7D0+FC beside C10 COL:255 0.6998 m (**0.5948 m2**, new),
the rest HELD on their band's depth (15D+7C8 lift end, 180+181, 182+183, 17E+17F at COL:1EF, 13D/13E at COL:211,
10B+7D1 annex corner).

**Runs not yet face-traced.** All 59 runs and both arcs are now traced piece by piece. The 19 main-house interior runs T-242
holds (D-33 'a beam ends on it mid-span', D-34 title vs length basis) keep their faces HELD on depth, now on traced
lengths: HELD candidates 81 pieces 43.876 .. 49.764 m2 (T-263: 49 faces 45.785 .. 51.665, shown, never summed).

## 4. Engine vs freelancer, and T-263 -> T-276 reconciled in units

| Item | T-276 (traced) | T-263 (run length) | Released A / V3.0.14 | Freelancer | Cause |
|---|---|---|---|---|---|
| Ground-beam buried faces DRAWING-CONFIRMED | **46.5208 m2** (79.03 m of face) | 35.4044 | no line | no row | missing category in both (FREELANCER_WRONG omission, engine silent) |
| HELD faces | 125 pieces, 245.34 m | 85 faces | - | - | depth D-33 / D-34 / D-35, held panels GS-12 / GS-16, split GS-08 |
| Neck rate correction | -18.853 m2 fixed on 14 necks (DRAWING-CONFIRMED) | perimeter x h | - | - | beam-zone faces with concrete / air against them |

T-263 35.4044 -> 46.5208 (+11.1165 m2), each step to a physical cause:
+5.3030 ring building face (traced, convex); +2.2945 109+7CB#2 side A on GS-09 (2.6994 m, fill; T-263 held the whole side
because GS-08 split-level is also on it, the GS-08 1.3997 m stays HELD); +1.8057 7D0+FC#2 side B on GS-05 (2.1244 m; the
GS-12 court 3.3193 m stays HELD); +2.6342 7D0+FC#3 side B on GS-15 (3.0991 m; GS-12 2.9493 m HELD); +0.5948 the 7D0+FC strip
beside COL:255; **-1.5158** faces that are not earth: tees 7D0+FC#1 B (109+7CB#1, 0.30 m), 7E0+FD#1 B (184+7CF#3, 0.30),
170+7C3#2 A (15D+7C8, 0.30), 170+7C3#3 A (175+7DE 0.30 + 176+7E6 0.13), 170+7C3#4 A (0.28 m beside the pool court is
OUTSIDE, + ring 0.02 + sliver 0.035), 109+7CB#1 both sides (span overlaps 0.13 / 0.10 at 0.30), and 10 sub-0.004 m2
column-edge / rounding pieces. Residual 0.000000.

Verdict proposals: line ENGINE omission + FREELANCER_WRONG (omission) on 46.521 m2 DRAWING-CONFIRMED; T-263's 35.404 is
superseded by this ledger: RULE_DIFFERENCE inside our own work (run length vs traced face), the traced value is the
physical one; necks UNRESOLVED (height, Q-21 C), with the beam-zone deduction now fixed.

## 5. Necks: what 'perimeter x neck height' over-counts (finding for T-270 / the neck line)

The neck rises to the ground-beam top (T-205). Over the beam depth its face is in earth only where it is free on a panel
(below the slab) or outside below the natural ground. Per neck the fixed m2 with no earth against it = covered length x
the covering member's depth + panel length x 0.10 slab + outside length x (0.95 - 0.00). 14 main-house necks have every
depth established: **18.853 m2** (e.g. C11 COL:220: 0.80 x 0.10 + 1.40 x 0.95 + 2 x 0.30 x 0.95 = 1.98). 18 HELD
(annex depth CONFLICT 7; a framing depth held or a column-to-column contact 9; court 2), 4 lift necks EXCLUDED. Five ground-beam-plan outlines are
smaller than the scheduled foundation section (COL:204 / 207 / 20B / 214 0.12 vs C / C3 0.15, COL:1E8 0.125 vs C4 0.15):
GB_PLAN_SECTION_DIFFERS, held; proposed to the T-277 drawn-vs-scheduled census. Not deducted (named): the 0.10 blinding
under a covering beam against the neck (cast before or after the coat is not printed).

## 6. Rule, tests, lessons row

Rule proposed R-WP-BURIED-1.1 (every villa; provenance T-276 on ST p.13 / the ground-beam plan of this set; adopted
as a new rule version): the length of a buried face is the length of the plan boundary of the buried concrete that the
member owns, traced once: a beam face under a tee or against a column is not an earth face; a side bordering several
panels is split by panel; the side a curved face looks into is the boundary it lies on; column faces belong to the neck;
lift / footing faces to their own lines; band pieces in no span take their own band's depth or stay HELD.
Tests: tests/t276_buried_faces (villa P 21.135 m2 by hand, identical mirrored and rotated 90 degrees; run length on a
covered face refused; closure double count / gap refused; mm-as-m and depth in mm refused; column face in the beam line
refused; held faces never 0; side from the boundary not the name; lift faces owned elsewhere; a piece never borrows a
crossing band's depth; neck deduction by hand; T-263 guards (T-219 footing side, coat above the slab underside) still
bind; Alsenan ledger, closure and reconciliation pinned to the committed files).

Lessons row proposed: 2026-10-24 | T-263 coated each ground-beam face over the run's face-to-face length and took a
side's panel from its middle: 1.516 m2 under tees / beside the pool court was coated and 6.735 m2 of fill faces was held
because a neighbouring panel on the same side is held | A run is not a face: a face ends where another member stands
against it, and one side can border several panels | Trace the boundary of the buried solid once, each piece to one
member; height per piece; side from the boundary (any villa) | tests/t276_buried_faces (adverse: run length on a covered
face refused; column face in the beam line refused) | PROPOSED.

## 7. Not done / uncertain

- Not integrated (lane I, T-270 WP.BURIED sub-line: take LEDGER_T276.csv DRAWING-CONFIRMED rows, 46.5208 m2).
- HELD stays HELD: interior depths (D-33 / D-34 designer items), annex (D-35 CONFLICT), court runs, GS-12 / GS-16 panels,
  GS-08 split level, necks (Q-21 C), footing tops (T-263), boundary G.B / straps (note scope), procurement (no product).
- The 0.0128 m2 sliver void and the 0.10 blinding under covering beams at necks are named, not measured.
- Checker re-measure list (not in its 17:59 sample): ring 157 / 158 building side and traced 6.2388 m (GS-10 4.2197 +
  GS-23 2.0191); run 7D0+FC#1 side B (LINE handle in LEDGER_T276.csv) 2.975 - 0.30 tee 109+7CB#1 = 2.675 m x 0.85 =
  2.2732 m2; run 7D0+FC#3 side B on GS-15 3.0991 m x 0.85 = 2.6342 m2; neck C11 COL:220 deduction 1.98 m2.
