# T-085: beam binding V2 (planted columns, a missed mark, upstands)

Worker 3, 2026-10-20. New policy `engine/source/beam_binding_v2.py` (BEAM_BINDING_V2) beside the frozen
MEMBER_DETECTION_V1 (`engine/source/member_detection.py` and `concrete_completeness.py` read only). **Not wired**: no
released method calls it, so the released Alsenan run is unchanged by construction (nothing it imports changed).
Diagnostic: `alsenan_v2.py` (read-only; `--ring-fallback BEAM:B4:1F:"owner Q-44 A"`; replays the route's own captured inputs through V1 and V2; V1 replay is
identical to the route on every slab sheet). Data: Drive "Alsenan chalet project" / "ST7757 dxf.dxf" (sha256
9f9d1179...38079), read in the scratchpad, never copied here. Runs: conventions V6 without profile (scoreboard basis,
949 structural lines) and V3 + the committed route G profile (M4 basis of the T-043 span list, 1101 lines): same
changes on both.

## 1. Planted columns (GF B26, B27)

Cause: `split_at_supports` (member_detection.py:841) cuts a band at every column outline it overlaps. The two outlines
that split B26 and B27 are the planted columns of the labels 'P.C 20x50' and 'P.C 20x70'. On this drawing each label
has a landing line under it, a leader to a circle drawn round the column, and the circle's centre is inside the
column outline; drawn 0.20 x 0.50 and 0.20 x 0.70 = printed. Both lie inside their beam's two faces.

V2 rule (`planted_columns` + `split_at_supports_v2`): a column outline LINKED to a planted-column label by its leader
(landing within one text height under the text, chain end on a circle round the column or inside the outline,
route tolerance 0.012 m) whose drawn size is the printed section (column size tolerance 0.02 m, the existing one)
and which lies inside the band's width does not cut the band. No leader / leader to no support / size differs /
two columns -> reported, the column still cuts (V1).

| GF beam | V1 (route) | V2 | Hand |
|---|---|---|---|
| B26 (0.65 x 0.85) | 2 pieces: 5.6179 m BOUND 3.1039 m3 + 1.2366 m inherited (held line) 0.6832 m3 | one span 7.0675 m BOUND **3.9048 m3** | 7.0675 x 0.65 x 0.85 = 3.9048 |
| B27 (0.90 x 0.85) | 2 pieces: 3.2713 m BOUND 2.5025 m3 + 1.1027 m inherited (held) 0.8406 m3 | one span 4.9505 m BOUND **3.7872 m3** | 4.9505 x 0.90 x 0.85 = 3.7871 |

The V2 span is longer than the two V1 pieces by the planted column's projection on the beam axis (an axis-aligned
box w x d on an axis at angle a projects as w|cos a| + d|sin a|): B26 0.5 x 0.0262 + 0.2 x 0.9997 = 0.213 m, B27
(inclined -53.6 deg) 0.7 x 0.594 + 0.2 x 0.805 = 0.5765 m; that concrete (0.1177 + 0.4441 = 0.562 m3) is beam
concrete under a column the beam carries. T-043 released only the engine's held pieces (0.683 + 0.841 m3).
Side effect: CB8 (BAND0039) junction ownership with the now longer B27 band: -0.0035 m2, -0.0026 m3.

1F label 'P.C 20x50': its leader circle is round a 0.20 x 0.40 outline that is not a support box of the route (it
cuts nothing in V1 either): LEADER_NO_COLUMN, nothing changes. Drawn 20 x 40 vs printed 20 x 50: designer RFI
candidate (the generic route's planted-column item takes 20 x 50 from the label).

## 2. GF B7 strip (the missed mark): cause traced, code fault fixed, no tolerance added

`bind_marks` (member_detection.py:792) skips the text-angle test for ARC bands (`band_axis_deg` is None for arcs).
The horizontal 'B7' is 0.064 m from the 1.70 m strip (BAND0006) and 0.274 m from an arc piece of the void ring
(BAND0050, tangents 44.5 - 63.7 deg); 0.274 - 0.064 = 0.21 m <= the ambiguity margin (text height 0.30 m), so V1 held
it AMBIGUOUS. V2 (`bind_marks_v2`) gives an arc band the tangent directions it takes over its angular range and uses
the SAME 12 deg angle tolerance as for straight bands: the arc is 44.5 deg off, the strip binds.
**BAND0006 B7 BOUND 0.34 m2 x 0.75 = 0.255 m3** (= T-043 hand 0.255).

Second change from the same rule: the rot-306 'B7' was AMBIGUOUS between two arc pieces; only BAND0053 is parallel
(1.2 deg; BAND0050 61.9 deg), so V2 binds **BAND0053 B7 0.08755 m2 x 0.75 = 0.0657 m3**. The four rotated B7 texts in
the void then bind one arc piece each (0050, 0051, 0052 already in V1). T-043 had BAND0053 UNRESOLVED ("not
parallel": it compared the text with the tangent at the nearest point, 15.8 deg). Verdict proposal: ENGINE_RIGHT
under the binder's own distance and angle rules (four labels, four pieces, symmetric); the verifier decides, since
the board's acceptance listed it among the spans to stay HELD.

## 3. Upstands from printed sections

`section_profile` reads a dimensioned rectilinear section outline: beam = widest strip stack, upstand = narrower stack
above it; every length must be printed by a dimension whose two origins are outline vertices (DIMLFAC: entity override
> style > header); the unit is proven by the schedule (printed 40 / schedule 0.40 m = cm); one drawing scale (0.025)
for all. `section_cuts` finds the cut line (crosses a band face to face at a right angle and is crossed by view arrows
whose nearest titled letter is the section letter); `upstand_lines` = w x h x the clear span crossed.

| Section | Plan | Printed | Span crossed | Upstand |
|---|---|---|---|---|
| A-A | GF, BAND0043.1 (0.40 wide; rows B19 / B20 both 40 x 75) | beam 40 x 75, upstand 20 x 20 | 3.000 m | **0.120 m3** |
| B-B | 1F, BAND0031.1 (0.45 wide; rows B17 / B21 / B23 45 x 75) | beam 45 x 75, upstand 20 x 20 | 3.000 m | **0.120 m3** |
| C-C, D-D | - | - | cut line found twice / ambiguous | HELD |

Total 0.240 m3 = T-043 hand. The section prints no mark, so the beam row for these spans stays open (T-043 matched
B20 / B23 by the printed bars); the upstand needs only the printed section and the span.

## 4. Ring beams round the 1F dome openings (owner Q-44 = A)

The 1F slab plan draws two rings 0.20 m wide (r 2.211 / 2.411 m) round the two structural dome openings. Ring 1:
inner and outer faces as arcs, 'B4' printed twice on its arc pieces. Ring 2: inner face one full CIRCLE, outer face
4 arcs, no mark of its own. V1 pairs ARC entities only, so ring 2 has no band at all (silent), and ring 1 is 4 short
arc bands (1.124 m2; 2 bound B4, 2 unbound; in no total).

`ring_beams`: every concentric face pair whose gap is a scheduled width; the ring's concrete = annulus less the full
width of the straight beams / columns it runs into, keeping only pieces whose every contact with the two circles is
drawn (the bulge of ring 1 beyond the far face of the right-hand beam, 0.12 m deep, is undrawn and dropped); a piece
half drawn makes the ring PARTIAL (nothing changes). Section from the mark bound to its arc pieces, or from an
owner answer passed by the caller.

| Ring | Basis | Annulus | Kept (not in straight beams, drawn) | B4 0.20 x 0.50 |
|---|---|---|---|---|
| 1 | PRINTED_MARK (B4 on its arcs) | 2.9042 m2 | 1.5105 m2 (4 pieces) | **0.7553 m3** (replaces its 4 arc bands) |
| 2 | OWNER_RULE (Q-44 A: B4 round each opening; no mark printed on this ring) | 2.9042 m2 | 1.7994 m2 (1 piece) | **0.8997 m3** |

Hand check: annulus pi x (2.4111^2 - 2.2111^2) = 2.9042 m2 = 14.52 m x 0.20 (the Q-44 hand 1.45 m3 gross per
opening); an independent 5 mm grid over the same drawing (annulus less beam bands and columns, slivers kept) gives
1.6445 / 1.8104 m2, i.e. ring 1 kept + the undrawn bulge segment (circle R 2.411, height 0.122: 0.125 m2) and ring 2
within 0.011 m2. The rest (1.39 / 1.10 m2) lies inside straight beams and columns, already counted there (no double count), or is undrawn.
Third dome position (upper roof): no structural drawing, HELD. The 2F slab plan draws two single circles r 2.211 m on
a boundary layer (no second face, no mark): no ring, reported for the Lead. GF void rings and the two ground-level
rings are PARTIAL (faces open): unchanged.

## Effect (diagnostic, not wired)

GF slab plan beams BOUND: 41.7616 -> 42.6413 m3 (+0.880 = B7 0.255 + B7 arc 0.066 + B26 0.118 + B27 0.444 - CB8
0.003); held GF bands 5 -> 3. As released lines (the inherited pieces are held UNLABELLED_SPAN_ACROSS_SUPPORT lines
in route G): beams +2.406 m3 (B7 0.255, B7 arc 0.066, B26 +0.801, B27 +1.285), rings +1.655 m3 (0.755 + 0.900),
upstands +0.240 m3: about **+4.30 m3** of beam concrete once a method wires V2. The Alsenan beam line is HELD on the
scoreboard, so engine vs freelancer for beams is not measured; the concrete total (92.77 vs freelancer 111.81 m3,
-17.0 %) would move by up to +4.30 m3 (about -13.2 %), to be measured by the wiring task, not claimed here. 2F and
ground beams: no change. Still HELD: the rest of the T-043 list (CB10 width conflict, CB3 / B3 two marks, unlabelled
spans past a column, the 0.20 strips north of B23 / B20, facade strips).

## Validation

`tests/t085_beam_binding` 38 cases (metres and mm, mirror, rotation 30 / -127 / 60 deg, supporting mid column, no
leader, section mismatch, column wider than the beam, tip inside outline, leader to nothing, arc beside a straight
mark, arc-parallel mark unchanged, arc without range, wrap of the tangent range, sections with / without upstand,
unprinted height, unit not proven, depth differs, a dimension at another scale, cut line rotated, wrong-width cut,
untitled letter, ring with mark in m / mm / mirror, full-circle face held then owner rule, half-drawn ring,
half-drawn piece PARTIAL, unscheduled ring width). L3: t085 + the member_detection importer folders (cad_limit_census, m2, m3, m5, m7, m9_s4) + t061:
289 passed, 0 failed (one m7 test needs full git history; passes after `git fetch --unshallow`). Freeze 0.
