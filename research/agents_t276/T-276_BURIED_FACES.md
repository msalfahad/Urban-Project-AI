# T-276 Buried-concrete liquid waterproofing r2: every buried face traced once (Alsenan; rule for every villa)

Worker 2 (lane A), 2026-10-24, run session_01KC3nKr8LoBDJ22DkmR2iRn. Research ledger + unwired modules, NOT wired into
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
