# T-229 Beam runs at planted columns and at members that do not support them

Worker 1 (lane S), 2026-10-23, run started 16:21 UTC. Development villa, not an accuracy claim. ERS read; s.2 steps 1-5,
s.3 (one element, several geometries; build before deduct), s.4 (quantity + rule + test) and s.7 applied. Files:
`research/agents_t229/*`, `tests/t229_beam_support/*` only. No engine module, method version, route G output, rule /
knowledge file, registry or released quantity changed. Sources (Drive "Alsenan chalet project"): 'ST7757 dxf.dxf'
(sha256 9f9d1179...38079, the route G input), read with `research/agents_t217/t217_extract.py` (column outlines +
S-COL.HAT hatch per slab plan); route G band polygons from the committed overlays (`research/agents_t110/scripts/bands.py`,
fit 0.6 mm); ST7757.pdf p.15 detail as cited by T-220 (Checker-verified 15:52). Committed: DXF handles, band ids, areas,
shares and lengths only (no coordinates, no drawing content). Scratch renders of the B27 and T.C areas were viewed and
not committed.

## 1. Result in engineering terms

Concrete, beams, Alsenan (m3). Released V2.9 + route G beams 64.820 m3 vs freelancer 65.97 m3 (-1.150, -1.74 %; T-110).
This task measures what the released beam lines lose or bill twice at the members they meet; nothing is wired.

| Beam / finding | Released route G | Drawing-derived (this task) | Delta | Cause | Status |
|---|---|---|---|---|---|
| GF B27 90x85 under PC-1F-A (P.C 20x70) | 2.5025 released + 0.8406 HELD (span 2 'unlabelled span across support') | **4.1918** (hand: 0.90 x 0.85 x 5.4686 = 4.1835, + 0.0083 corner slivers against B1 / CB8) | +0.8487 on the pieces; the 0.8406 hold is resolved | cut at the carried P.C 0.4418 (0.519 m2: 0.140 under it, 0.380 beside it); both oblique ends square-cut 0.1787 + 0.2282 against the C11 / D.C faces | DRAWING-CONFIRMED, NOT RELEASED |
| GF B26 65x85 under PC-1F-B (P.C 20x50) and into the T.C at C8 | 3.1039 released + 0.6832 HELD | **4.0846** | +0.2975 on the pieces; the 0.6832 hold is resolved | cut at the P.C 0.1163; the piece stops at the turned upper part of C8 (pattern 31B), 0.3193 .. 0.336 m short of the GF column face: 0.1812 | DRAWING-CONFIRMED |
| GF B28 at the T.C at C8 | 0.1509 (piece) | 0.2121 | +0.0612 | stops at the turned part, 0.3255 m short of the GF column face | DRAWING-CONFIRMED |
| 9 support cuts beside a narrower column (GF CB8, CB1, B20, B24; 1F CB12, CB13, CB11 x2, B23) | cut full width at the column | +0.4760 | +0.476 | the beam is wider than the column; the part beside it inside the drawn edges is billed by no line (crossing B6 share deducted at CB12) | DRAWING-CONFIRMED (B20 / B24 / B23 spans stay HELD by route G for their own labels) |
| 1F CB10 beside C (D-02 width conflict) | - | plan 0.0595 m2 | HELD | exists only on the 0.30 reading | HELD |
| 15 oblique square-cut ends (B27 x2, B17 0.0442, B21 x2, B13 x2, B25, B5, B11, B29, B1, B4, 1F B1, B6) + 1F B19 at C9 (0.0289) | square ends | +0.5409 | +0.541 | route G cuts a piece square where the beam meets its member obliquely; the drawn edges run on to the face | DRAWING-CONFIRMED |
| 6 GF columns under a beam billed through them (C under CB1, B9, CB7, B2, CB8; C3 under CB7) + 1F C9 4 % under B19 | column full interval AND beam band | billed twice **0.2778** | -0.278 on the beam lines | route G did not split these bands at the column (its own basis says 'column footprint split out'); precedence column > beam | DOUBLE (both lines released) |
| PC-2F joint under B7 (T-220) | B7 through; no PC line | counted once | 0 | T-220 record stops at the B7 soffit (beam owns); the T-119 ledger joint COL-2F-59 0.0599 is DOUBLE and is superseded | resolved |

Totals of confirmed beam concrete no line bills: cut at carried 0.5581 + end at carried 0.2425 + beside support 0.4760 +
oblique ends 0.5120 + short of member 0.0289 = **1.8175 m3**; plus route G holds resolved on B27 / B26 1.5238 m3; billed
twice 0.2778 m3. If lane I wires all three: 64.820 + 1.818 + 1.524 - 0.278 = 67.884 vs freelancer 65.97 (+1.914, +2.90 %),
with every other T-110 CONFLICT / HELD record still outside both sides; that is not a verdict on the total (his workbook
has no per-beam lines to compare). Against the reference register T-110 (merged): B27 one span 3.7872 -> 4.1918
(+0.4046 = the two oblique ends T-110 took from route G); B26 3.9048 -> 4.0846 (+0.1798 = the T.C end; the run without it
is 3.9034, -0.0014 = overlay fit).

Verdict proposals (for the Checker): B27 / B26 / B28 continuous runs ENGINE_RIGHT for the drawing-derived method once
wired (hand above, DXF edge lines), released route G wrong (cut at members it carries, square-cut oblique ends);
beside-support and oblique-end shortfalls ENGINE_RIGHT (drawn edges); the 6 through-column joints a released-line
DOUBLE (not a freelancer difference). Freelancer per beam: not compared.

## 2. Physical element and evidence (ERS s.2.1-2.3)

- **What supports a beam.** Slab-plan legend (p.3-p.6), as read by T-217 / T-220: on each roof-slab plan a column outline
  with SOLID hatch is the column UNDER that slab (it supports the slab's beams); a pattern hatch (ANSI35) marks a member
  that STARTS on that slab: the planted columns P.C (GF 329, 386; 1F 77B) and the turned upper part of a T.C (GF 31B at
  C8, 322 at C9). ST7757.pdf p.15 'BEAM CARRYING PLANTED COL. DETAIL': the beam runs at full depth under the column.
  A beam also rests on a beam it frames into (beam-on-beam) and stops free at a cantilever / slab edge.
- **Drawn beam plan.** Beam edge lines on layers 1 / 5 / S-BEAM. B27's two S-BEAM edges (handles 325, 326, 0.900 apart)
  run continuously from the C11 column at its south end (37D) to the column 35C at its north end, straight through the
  P.C 329 (whose outline carries the X of the P.C symbol); B26's edges 387 / 388 (0.650 apart) run from C10 (371)
  through the P.C 386 to the face of the GF column at C8 (36E), through the turned part 31B; B28's edges (431 and 2C5 /
  the 31B face) start at the same GF column face. The B4 / B5 line stops at B27's edges at the P.C (B27 owns that
  junction, billed through).
- **Route G basis.** Bands are cut at every S-COL.BON outline, whatever its hatch; the band beside the cut keeps its
  label, the piece across the 'support' is held ('unlabelled span across support'). Square ends at oblique members.
  Bands billed THROUGH 6 GF column outlines (no split), column lines at the full storey interval (0.45 / 0.5625 m3).

## 3. Census (CENSUS.csv, 238 rows; ALSENAN_BEAM_SUPPORT_INPUT.json)

127 straight pieces (GF 65, 1F 43, 2F 19) + 9 ring / arc bands (not cut-checked, listed); 59 supports, 5 carried
members. Every route G cut between two pieces of one band (36), every piece end (182) and every column under a piece (11):

| Class | n | Status |
|---|---|---|
| SUPPORT_CUT (cut over a supporting column, share >= 0.95) | 22 | PASS |
| SUPPORT_CUT_BESIDE | 10 | 9 BEAM_SHORT 0.476, 1 HELD (CB10, D-02) |
| CUT_AT_CARRIED (B27 at 329, B26 at 386) | 2 | BEAM_SHORT 0.5581 |
| PROJECTION_CUT (outer 0.20 strips north of B20 / B23) | 2 | HELD (D-26, section unprinted) |
| END_AT_SUPPORT / END_AT_BEAM / END_AT_JUNCTION_OWNER / END_AT_OVER_SUPPORT / END_FREE | 73 / 71 / 15 / 1 / 3 | PASS |
| END_SHORT_AT_CARRIED (B26, B28 at the T.C at C8) | 2 | BEAM_SHORT 0.2425 |
| END_SHORT_OBLIQUE | 15 | BEAM_SHORT 0.5120 |
| END_SHORT_OF_MEMBER (1F B19 at C9) | 1 | BEAM_SHORT 0.0289 |
| END_AT_PROJECTION (1F B23 west end) | 1 | HELD |
| under a piece: DOUBLE / DOUBLE_PARTIAL / PASS (carried 77B under B19, 322 under B16 / B21; 778 by T-220) | 9 / 6 / 5 | double 0.2778 released, 0.3378 ledger |

A shortfall is claimed only where the beam's drawn edges cover both sides of the region (>= 0.9); a side covered < 0.5
means the drawn beam ends at the billed face (PASS); in between HELD. 2F has no carried member and no shortfall.

## 4. Rule, module, tests

Rule proposal **R-BEAM-CONT-1** (`R-BEAM-CONT-1.json`, any villa): a beam is measured over its drawn plan from support to
support; it is cut only at a member that supports it and only over that member's footprint; a cut at a member it carries
is refused (continuous, owns the region; a hold 'unlabelled span across support' there is resolved); a piece square-cut
short of an oblique member or stopping at a carried member's face is short by the drawn beam up to the receiving face;
a column footprint billed by both a beam piece and the column line is DOUBLE, precedence column > beam; a column record
to the soffit of a beam billed through it is not double; claims only on drawn edges, HELD otherwise, never 0.
Adoption = a new rule version (Lead / lane I). Relation to R-CONC-OWN-1: applies its 'gap never closed by a zero' and
precedence to beam runs; consistent with R-PLANTED-COL-1 (T-220).

Module `beam_support.py` (BEAM_SUPPORT_V1, stdlib, unwired): plan geometry (convex clip, rotated / mirrored rectangles),
`piece_from_quad`, `collinear`, `gap`, `extension` (oblique-face trapezoid), `shares`, `classify_gap`, `classify_end`,
`joint_ownership`, `beam_run`, `check_claim`, `check_joint_claims`. `t229_census.py` (private DXF + overlays, shapely for
the beyond-face booleans) -> `ALSENAN_BEAM_SUPPORT_INPUT.json`; `t229_alsenan_check.py` -> `summary.json`, `CENSUS.csv`.

Tests `tests/t229_beam_support`: synthetic Villa Q (two-bay beam 0.40 x 0.80 with a P.C at mid-span: continuous 2.464 =
billed 2.368 + gap 0.096 by hand; adverse: the cut kept refused, joint owned twice / by none refused, 0 refused, edges
not drawn / no member / no depth / projection / width conflict HELD; rotation 0 / 30 / -47.5 mirrored / 90; m / cm / mm;
oblique end trapezoid 0.16 m2 by hand; beside support 0.048; crossing beam share deducted; through column DOUBLE 0.060 vs
soffit record PASS; non-collinear pieces refused) + the development villa (values above).

## 5. For the Checker (re-measure from the drawing)

1. B27: S-BEAM edges 325 / 326 (0.900 apart), support outlines 35C (north) and 37D (south) on the GF roof-slab plan; P.C
   outline 329 (0.70 x 0.20, X symbol), text 544 'P.C 20x70'. Hand: axial length between the two column faces along the
   edges = 4.40 / sin 53.57 deg = 5.4686 m; 0.90 x 0.85 x 5.4686 = 4.1835 m3; route G bands BAND0048.1 (released 2.5025) and
   BAND0048.2 (held 0.8406).
2. B26 at the T.C at C8: edges 387 / 388 (0.650) end on the face of 36E (the GF column), the band BAND0047.2 stops at the
   face of the pattern outline 31B (0.3193 .. 0.336 m before it); B28 edges 431 / 2C5 start at the same 36E face.
3. One beside-support cut: GF B20 BAND0043.1 / .2 at column 368 (0.80 x 0.25, flush with B20's north face): beside
   0.80 x 0.15 = 0.120 m2 x 0.75 = 0.090 m3; and one through column: GF 350 (C3) under CB7 BAND0014 (share 0.996).
4. Re-run: `python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g <bands.json>`,
   `python3 -I research/agents_t229/t229_census.py <ST7757 dxf> <bands.json>` (prints counts; `--write` rewrites the
   input), `python3 -I research/agents_t229/t229_alsenan_check.py`.

## 6. Lessons row (proposed)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-23 | Released beams lose 1.818 m3 of drawn beam concrete (B27 alone 4.192 vs 2.503 released + 0.841 held) and bill 0.278 m3 twice | The band splitter treats every column outline as a support (also members that START on the beam: planted columns, turned column parts), cuts full beam width at a narrower column, cuts square at oblique members, and skips the split where a band runs over a column | A beam is cut only at a member that supports it and only over that member's footprint; a member it carries never cuts it; the measured plan is the drawn plan between the beam edges up to the receiving faces; a column footprint is billed by one line (every villa) | tests/t229_beam_support (adverse: cut at a carried member kept, joint in two lines or none, missing as 0, edges not drawn) | proposed |

## 7. Not done / uncertain

- Formwork and rebar of the affected beams (beam sides / soffit lengths follow the drawing-derived runs; B27 / B26 extra
  4 ø16 and 10 cm stirrups under the P.C, p.15): for T-163 / lane S later.
- The 9 ring / arc bands (dome rings, void ring) are listed, not cut-checked.
- Route G holds at REAL supports (B20, B24, B23 'unlabelled span past a column') stay HELD; only the two at carried
  members are resolved here.
- Beam depths are the route G / schedule depths (D-16 / D-63 / D-65 untouched); the downstand basis (D - t) of the
  non-overlapping model is not applied here (gross basis, as T-110).
- The 0.2778 m3 double is allocated by precedence column > beam (R-CONC-OWN-1); the integrated candidate must take it
  out of the beam lines, not the columns.
