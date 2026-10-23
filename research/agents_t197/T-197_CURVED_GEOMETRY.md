# T-197: curved and partial geometry completeness (residential review R4)

New unwired check `engine/source/curved_geometry_check_v1.py` (CURVED_GEOMETRY_CHECK_V1, standard library only, imports
no engine module). It moves NO quantity: ARCH_TAKEOFF_V2.9 + route G (released) and every V3.0.x candidate are
unchanged. ENGINEERING_REASONING_STANDARD s.2 (element first), s.3 (the basis of a measure before its arithmetic) and
s.4 (rule + test) applied. Data read this run: Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip (P7757.dxf,
sha256 ab54dd55...) and "ST7757 dxf.dxf" (sha256 9f9d1179...), into the private folder only.

Repeat: `python -I research/agents_t197/alsenan_t197.py extract <P7757.dxf> <ST7757.dxf>` (project venv; writes
ALSENAN_T197_INPUT.json, geometry relative to each element's arc centre, metres), then
`python3 -I research/agents_t197/alsenan_t197.py [--check]` (writes / compares LINES_T197.csv, ISSUES_T197.csv,
ELEMENTS_T197.json, summary.json). Tests: `tests/t197_curved_geometry` (24 PASS).

## 1. Physical question and what the check does

An element that follows an arc on plan (a wall, a face, a parapet, a slab edge, an opening, a room contour, a ring
beam, a pool wall) has several honest lengths and two honest plan areas. Which one a BOQ line needs depends on the
line (supply of a curved window = outer arc, owner Q-39 C; a concrete band = its true area; an elevation dimension =
the projected chord, identity only). The fault pattern is not "the wrong formula" but a line whose basis nobody named,
or a line that only saw part of the arc. For every line on a curved element the check computes, from the drawn
entities, every basis value (OUTER / INNER / FACE / CENTRELINE arc, the chord of each, the straight parts alone, true
area, chord polygon area) and reports which basis the line's value actually is:

| Code | Meaning |
|---|---|
| BASIS_UNNAMED | the line names no basis; the matching bases are listed (two within 1 cm = the ledger must say which) |
| BASIS_MISMATCH | a named basis, but the value is another basis or none |
| STRAIGHTENED | a chord on a QUANTITY line of an element that follows the arc (identity chords are not flagged) |
| PARTIAL | covers a strict subset of the arcs, equals the straight parts alone, is below every basis, or (element level) the lines of an expected BOQ family leave arc uncovered |
| OVER_OUTLINE | exceeds every basis of the true outline (a region tool leaking past the drawn face) |
| DOUBLE_ARC | two active quantity lines of one BOQ family on the same arc (same circle, overlapping sweep; for areas the material on the same side, so a shared boundary is NOT a double count) |
| NOT_MEASURED | an element of an expected family that no line of that family touches (information, never 0) |

Area of a loop with arcs = shoelace of the chord polygon + sign(sweep) x segment r^2 / 2 (theta - sin theta) per arc in
traversal order (exact; no sampling). A mirrored OCS (extrusion z < 0) maps x -> -x and the bulge side with it
(historical defect B1): tested on the module and through the K2 ezdxf route with a mirrored INSERT.

## 2. Hand fixture (villa K, not Alsenan) and adverse cases

Curved wall r 3.20 / 3.00, 90 deg: outer 5.026548, inner 4.712389, centreline 4.869469, chord 4.525483, true area
0.973894, chord polygon 0.620000. Curved window r 2.50 / 2.30, 60 deg: outer 2.617994, inner 2.408554, inner chord
2.300000. Slab 4 x 3 + outward bulge 0.5: r 2.5, segment 2.795595, area 14.795595, edge 14.636476 (chord 14, straight
parts 10). Ring r 1.2 / 1.0 drawn as two half arcs each: 1.382301 m2, half 0.691150. Adverse (all PASS): mirrored OCS and
mirrored INSERT keep the bulge outward (14.795595, never 9.204405); mm stated = same result, the same numbers as metres
refused; ARC of 359.9 deg = 6.281439 m at r 1 (not a full circle, not 0); bulge vs ARC entity of the same quarter
circle = same length and mid point; a straight wall 0.05 m from an arc never flagged; a slab sharing the ring's outer
circle is not a double count; a ring half superseded -> PARTIAL; bad inputs refused (unit, role, basis, chord face,
unknown element / piece, open loop, off-circle point, mid vs direction).

## 3. The development villa: the four known cases found by the check

Geometry rebuilt from the DXF entities by handle reproduces every merged verdict: west dome in-bay ring 1.510479 m2
(T-160 1.5105, Checker 0.7553 m3 / 0.50), route bands 0.258772 / 0.303422 m2 (route G 0.2588 / 0.3034), pool wall band
2.356726 m2, centreline 11.783628 m, base 10.935564 m2 (T-183 r2 VERIFIED), 1F-11 contour 22.150670 m and area
19.091545 m2 (Checker T-128 r3 22.1507 / 19.0915), W17 outer arc 3.289498 / face arc 2.976663 / face chord 2.691719 m
(T-194).

| Case | Element | Line (scenario) | Value | Finding | Engineering meaning |
|---|---|---|---|---|---|
| 1 | pool walls | engine A wall band (released V2.9 + route G, and still candidate V3.0.5) | 1.240 m2 | BASIS_UNNAMED + PARTIAL | below even the chord band 1.320; 1.117 m2 of the drawn band 2.357 not measured (the curved half) |
| 1 | pool base | engine A floor (same) | 6.045 m2 | BASIS_UNNAMED + PARTIAL | below the chord rectangle 6.125; 4.891 m2 of the drawn D 10.936 not measured |
| 1 | pool | T-183 r2 ledger: band, centreline, both faces, base | 2.356726 / 11.784 / 12.497787 / 11.069469 / 10.935564 | clean | each on its named basis |
| 2 | W17 | V2.9 COP-001 supply width | 3.2895 m | clean | OUTER_ARC, owner Q-39 C |
| 2 | W17 | T-194 NW elevation dimension | 2.6915 m | clean | PROJECTED_CHORD of the r 1.935 face, identity |
| 2 | W17 | T-159 facade opening deduction "COP-001 2.977" | 2.977 m | BASIS_UNNAMED | matches BOTH the inner (face) arc 2.9767 and the OUTER chord 2.9736 within 1 cm: the ledger must name it |
| 2 | W17 | T-175 sill | 3.290 m | BASIS_UNNAMED | matches the outer arc only; which face the sill runs on is not stated |
| 3 | 1F-11 | T-128 r2 walked contour | 22.350 m | BASIS_UNNAMED + OVER_OUTLINE | 0.1993 m past the drawn faces 22.1507 (the frame-cavity notches) |
| 3 | 1F-11 | T-128 r3 contour | 22.149 m | clean | FACE_ARC, -0.0017 m |
| 4 | west dome ring | released route bands BAND0033..0036 (4 lines) | 4 x sector, 1.1244 m2 | PARTIAL (element) | 5.180 m of the ring's inner arcs uncovered; 0.3861 m2 of the 1.5105 m2 in-bay ring not measured |
| 4 | west dome ring | V3.0.4 + T-160 ring line (the T-179 r1 state) | 1.5105 + 1.1244 m2 | DOUBLE_ARC x 4 | each band's arcs (2.588 / 3.034 m) measured again by the ring |
| 4 | west dome ring | V3.0.5 (bands SUPERSEDED, ring active) | 1.5105 m2 | clean | fixed by T-179 |

Identification note (case 4): the four route bands are identified as the annular sectors under the four drawn outer
arcs by area equality (0.258772 / 0.303422 vs route 0.2588 / 0.3034, to 1e-4 m2); the route overlay polygons themselves
were not re-read, and which BAND id is which quadrant is not established (only the pairing by area).

## 4. Engine vs freelancer, and who is right (concrete m3 at the merged heights; no quantity moved by this task)

| Item | Engine released | Drawn basis (merged ledger) | Freelancer | Proposed verdict |
|---|---|---|---|---|
| Pool wall band (plan) | 1.240 m2 (x 1.60 = 1.984 m3) | 2.3567 m2 (x 1.20 = 2.828 m3 VERIFIED) | 12 x 0.20 = 2.40 m2 (x 1.80 = 4.320 m3) | ENGINE WRONG (partial outline; fix is T-193); freelancer RULE_DIFFERENCE on length (12 vs centreline 11.784) + height (T-183) |
| Pool base | 6.045 m2 (x 0.25 = 1.511 m3) | 10.9356 m2 (x 0.40 = 4.374 m3 VERIFIED) | 4.32 m3 floor | ENGINE WRONG (partial outline; T-193) |
| W17 width | 3.2895 m (outer arc) | outer arc 3.2895 (Q-39 C) | 3.15 m (x 3.00 = 9.45 m2) | 3.15 matches NO drawn basis (nearest: centreline arc 3.1331, +0.017 m): RULE_DIFFERENCE (owner Q-39 C sets the outer arc); engine 3.29 x 3.50 = 11.51 m2 |
| West dome ring | route bands 0.5622 m3 (0.1294 + 0.1517 PROVISIONAL + 2 held) | 0.7552 m3 VERIFIED (V3.0.5) | no row | released route under-measures the ring by 0.3861 m2 x 0.50 = 0.193 m3 |

## 5. Rule, regression test, lessons (ERS s.4 / s.7)

Proposed rule UP-CURVE-BASIS-001 (any villa; provenance: T-197 from four development-villa defects; not yet in the rule
store, a new rule record is lane I / Lead): every BOQ or ledger line on an element whose drawn outline carries ARC
entities or polyline bulges names its basis (OUTER / INNER / FACE / CENTRELINE arc, the chord of a named face, TRUE or
CHORD area) and the arcs it covers; a chord on a quantity line needs a cited owner rule; two lines of one BOQ family on
the same arc (same side for areas) are a double count; a line below every basis of its outline is PARTIAL and stays
HELD until the missing part is measured or explained.

Regression tests: tests/t197_curved_geometry/test_curved_geometry_check.py (normal: named bases on villa K; adverse:
straightened, partial, over-outline, double arc, mirrored bulge, units, 359.9 deg, bulge vs ARC, straight wall near an
arc, shared boundary) and test_alsenan_curved.py (the four cases).

Lessons-register row (proposed): 2026-10-23 | curved elements measured as a straight strip, on an unnamed basis, on part
of the arc, or twice on the same arc (pool ring T-183, W17 T-194, 1F-11 T-128, dome ring T-179) | each ledger chose a
basis silently; no check compared a line with the drawn outline incl. its arcs | UP-CURVE-BASIS-001 above (any villa) |
tests/t197_curved_geometry (normal + adverse) | check built (T-197), wiring is lane I.

## 6. For lane I and the Lead (no file of theirs changed here)

- Pool: the released / candidate pool band and base stay PARTIAL until T-193 integrates the verified 7.202 m3 (no new
  work; the check confirms the T-193 premise).
- W17: T-159 (facade deduction 2.977) and T-175 (sill 3.290) should carry a basis column; 2.977 is ambiguous between the
  face arc and the outer chord. Proposed: name FACE_ARC (r 1.935, the face the facade is measured on) once the facade
  ledger's own convention is confirmed by the Checker; until then the facade opening deduction for W17 is BASIS_UNNAMED.
- Dome: V3.0.5 is clean; the released route bands stay PARTIAL (released default unchanged, as intended).
- Wiring the check into V3.0.x (a Gate B pre-check over every candidate line with curved geometry) needs per-line
  element ids from the candidate, which the candidate does not carry today: a lane I task.

Missing / uncertain: the T-159 facade side NW-2 arc length 3.5283 and the GF W03 curved glazing band were not run
through the check (outside the four known cases); east dome ring HELD (no depth), not checked; elements are built by
hand from handles, not discovered automatically from a whole drawing (a discovery pass over every ARC / bulge is the
natural next step for lane I or a later R4 part).
