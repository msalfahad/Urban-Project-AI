# T-172 Corners and parapet edges as physical items (development villa; rule for every villa)

Worker 2, 2026-10-22. Lane A, gate 2. Research files and a regression test only: no engine, rule, method or released
quantity changes; the released default (V2.9 + route G) is untouched. Governing texts: ENGINEERING_REASONING_STANDARD.md
(sections 2, 3, 4, 7), OWNER_NOTES_SIGMA_2026-10-21.md (2026-10-22 correction: corners are their own m.l line, "2 m = 1 m"
is half-rate pricing), URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1 (OD-V3-4: corner beads / profiles are separate lm items
wherever geometry supports them, never buried in plaster), owner Q-07 (bands slab top to slab top), Q-65 (boundary wall /
parapet block HELD), Q-67 A cond. (passage faces exterior), Q-68 (slab edges), WORKFLOW_CONTROLS section 5 (statuses).

Evidence read (Drive "Alsenan chalet project", read-only, scratch copies only): architectural DXF
(P7757_DXF_COMPRESSED.zip: plans, SE and NW elevation frames), p7757_arch_sheet10.pdf (section A-A),
p7757_arch_sheet09.pdf (NE elevation), the freelancer exterior-plaster workbook ("المساح الداخلى والسجما.xls", sheet 1 rows
50-97, invoice sheet rows 24-26; all 33 cells used here re-read from the file: 0 mismatches, A93 = 547.47, B93 = 749.88).
Built on the merged T-159 face table (FACADE_SIDES_T159.csv) and the released engine's wall reading (ARCH_WALLS, external
walls 0.20 m; one 2F wall 0.15 m).

## 1. The physical element (standard 2.1)

Section A-A (sheet 10) draws every roof parapet as the plain upward continuation of the external wall: a rectangle the
wall's width (0.20 m; scan width 0.21 m at 1:100), 0.50 m above the annex, GF and 2F roofs and up to 1.30 m above the 1F
roof, flat top, no coping, no drip, no projection; slab edges are flush with the wall face. So one metre of parapet is:

| Component | Unit | What the drawings show |
|---|---|---|
| Outer face (continues the facade) | m2 | drawn; already inside the T-159 facade faces (not counted again) |
| Inner face (roof side) | m2 | drawn (section); NOT in the facade measure |
| Top surface | m2 | plan centreline x wall thickness |
| Outer top arris | m.l | the outer run |
| Inner top arris | m.l | the inner run (outline offset by t, mitred, cut where the parapet meets higher construction) |
| Stop-end (free end only) | m.l | 2 vertical arrises (h each) + top edge (t) |
| Inner base junction with the roof | m.l | an internal angle / plaster termination at the waterproofing upturn: NOT an external arris |
| Drip, coping, upturn | - | none drawn in section A-A; the elevations draw a 0.20 m top band on the 2F NW face and on the 1F SE wave (profile and material not specified: UNKNOWN) and rounded corners on several parapet ends and the 2F block (radius not dimensioned) |

Whether the specification requires corner beads, stop beads, drip profiles, top plaster or coping: **UNKNOWN** for every
item; no specification or finishing schedule for this project is on Drive. The only Kuwait source found earlier (T-162
section 4) that measures corners is the owner's Urban cost PDF, which prices them as their own m.l line.

## 2. Parapets, component by component (PARAPET_COMPONENTS_T172.csv)

| Roof (parapet) | Outer top arris m.l | Inner top arris m.l | Top surface m2 | Inner face m2 | Ends | Status |
|---|---|---|---|---|---|---|
| Annex +4.30 -> +4.80 | 29.342 | 28.428 | 5.777 | 14.214 | both ABUT (passage wall to +5.50; 1F SE face on the annex roof) | DRAWING-CONFIRMED |
| GF house +5.50 -> +6.00 | 28.770 | 27.970 | 5.674 | 13.985 | ABUT (1F NW face); passage-mouth end UNKNOWN: stop-end HELD 0 .. 1.20 m.l | DRAWING-CONFIRMED + HELD end |
| 1F +9.70 -> +11.00 printed (NE / SW), waves (NW / SE, CAD top line) | 50.569 | 48.784 | 9.935 | 52.082 .. 57.185 | both ABUT (2F faces) | DRAWING-CONFIRMED; heights HELD on NE-1 / SW-1 returns and SW-2 (0.385 .. 1.60) |
| 2F +13.90 -> +14.40 (closed ring) | 29.800 | 28.300 | 5.415 | 14.150 | none | DRAWING-CONFIRMED (t 0.20, NE side 0.15) |
| **Total** | **138.481** | **133.481** | **26.801** | **94.431 .. 99.534** | | |

- The outer runs agree with T-162 (138.481). The inner runs are new: the 1F niche (0.08 m deep returns of the window
  recess) does not move the wall's inner face; the concave pool-court bay grows to r + t (2.135 m).
- Physical external arrises per metre of parapet: 1.95 .. 1.97 (outer + inner), never 3.
- Inner faces (94.4 .. 99.5 m2) are a plastered surface outside the T-159 facade figure: a scope item for the exterior
  plaster package, kept here as m2 (no number moved into any released line).

## 3. Vertical corners (VERTICAL_CORNERS_T172.csv)

Every junction of each floor outline, convex or concave from the outward normals, height = overlap of the two faces'
bands AT the corner (GF portion under the 1F plate -> +5.50; 1F over the annex roof -> from +4.30; 1F parapet end
heights on the wavy sides not printed -> HELD up to +11.30).

| Item | Count | m.l DRAWING-CONFIRMED | HELD |
|---|---|---|---|
| Convex external arrises GF / 1F / 2F | 13 / 9 / 4 | 66.900 / 39.000 / 18.800 = **124.700** | 1F parapet end parts <= 11.900; pool-court plinth 3 x 0.70 .. 0.85; 1F slab edges below +5.50 at 5 corners (Q-68) |
| Wall ends at the two side-passage mouths (facade side + passage side, 4 ends) | 8 | **43.100** (to the +5.50 passage wall top) | exterior status follows Q-67 A cond. |
| Concave internal angles (not arrises) | 11 | - | - |

T-162 (READY, not verified) gave 128.984 m.l with one arris per mouth end; this table counts the passage-side arris too
(the passage faces are exterior under Q-67 A cond.) and caps the mouth ends at the passage wall top so the GF parapet's
stop-end is not counted twice.

## 4. The freelancer's 1,297.35 m.l, cell by cell (RECONCILIATION_T172.csv)

His invoice line "corners, joints and rounded edges, m.l" = column A "arrises and ends" 547.47 (SUM A51:A90) + column B
"corners" 749.88 (SUM B51:B92). Item by item against the drawing (m.l):

| His cells | His m.l | Drawing m.l | Difference and cause | Verdict proposal |
|---|---|---|---|---|
| Parapet tops B78 / 79 / 83 / 84 (2 x L) | 280.59 | outer + inner top arrises 271.962 | +8.628: he takes both edges on one run (his L = the inner runs: 48.47 vs 48.784, 28.40 vs 28.428, 27.20 vs 27.970) and rows 83 + 84 carry 63.40 m against 56.270 m drawn (+7.130 m of parapet that is not on the drawings) | RULE_DIFFERENCE; rows 83 / 84 UNRESOLVED |
| Parapet third line A78 / 79 / 83 / 84 (1 x L) | 140.27 | no external arris; the inner base junction (termination) is 133.481 | a counting convention: 3 lines per metre of parapet; a plain parapet has 2 arrises | RULE_DIFFERENCE |
| Vertical corners B65 + B66 | 148.00 | 105.900 GF + 1F (+ 2F 18.800, + HELD <= 14.45, + mouth ends 43.100) | no corner list in his cells | UNRESOLVED |
| 2F corners B77 | 12.60 = 3 x 4.20 | 4 x 4.700 = 18.800 | he stops at the +13.90 slab; the arris runs to the +14.40 parapet top (the 2F walls continue as the parapet, section A-A); the 4th corner continues the house's SE / SW corner from the ground | ENGINE_RIGHT on the height |
| NW frame B75 | 17.55 = 2 x 8.775 | drawn arch lines 9.316 + 7.893 = 17.209 (one arris per line) .. 34.077 (each line a 50 mm moulding) | -0.341 at one arris per line; profile not detailed | RULE_DIFFERENCE (dimension); HELD profile |
| SE frame A61 | text "8.3.1" = 0 in his SUM | three nested arch lines 28.308 + 26.947 + 25.538 = 80.793 .. 161.103 | **a text cell inside SUM(A51:A90) silently drops the SE frame** | freelancer omission; quantity HELD (profile) |
| Pool-court ceiling B73 | 18.00 | soffit edge of the circular void 6.810 (void 3.6901 m2, verified T-154) | 18.00 matches no drawn edge; the slab-edge arrises over the open court are HELD (Q-68) | UNRESOLVED |
| Facade rows A51-A70 (14 cells) | 281.70 | candidates: opening edges (T-162: 189.630 measured + 58.600 ASSUMED door jambs + jambs HELD on 20 openings) and band lines | 7 of 14 cells decode as 2-5 x his facade length or height, 7 do not; no descriptions | UNRESOLVED per cell |
| 2F facade A77 | 51.85 | - | not decomposable | UNRESOLVED |
| Boundary wall A87 / B87 / B88 | 73.65 + 75.34 + 16.10 = 165.09 | drawn wall lines: neighbour side 31.37 outer / 30.97 inner, street side 8.30 / 5.60 (t 0.20); height not printed | A87 = 37.65 + 15 x 2.40 (one line + 15 vertical edges of 2.40 m); B87 = 2 x 37.65 + 0.04; B88 not decomposable | HELD (Q-65; not a house face; height unprinted) |
| Drip edge B92 | 181.70 | none drawn | NOT IN THE DRAWING | HELD (designer item) |
| **Total** | **1,297.35** | | | |

Checker items behind the owner-accepted 73.50 m.l (OWNER_SESSION_CHANGES 2026-10-22 08:35): the boundary wall's stop-ends
are column A 73.65 (classified here: one line along the wall + 15 vertical edges of 2.40 m, consistent with the cell, not
provable) and column B 91.44 (75.34 + 16.10: the two top arrises of 37.65 m + 0.04, and a continuation not decomposable);
the 48.15 m.l of small items are the pool-court ceiling 18.00 (UNRESOLVED, drawn void edge 6.810), the NW frame 17.55
(drawn 17.209 .. 34.077) and the 2F facade 12.60 (3 x 4.20 against the drawn 4 x 4.70 = 18.80).

## 5. Four separate figures (standard section 3)

| Figure | Value | Basis |
|---|---|---|
| Physical length, measured here (house) | **439.762 m.l DRAWING-CONFIRMED**: parapet top arrises 271.962 + facade vertical arrises 124.700 + passage-mouth wall ends 43.100 | plus T-162 opening edges 189.630 (READY, not verified) + 58.600 ASSUMED; HELD: parapet end heights <= 11.900, pool-court plinth 2.10 .. 2.55, GF stop-end 0 .. 1.20, slab edges (Q-68), frames 98.002 .. 195.180 (profile), boundary wall (Q-65), drip (not drawn). Never 0, never summed into a release |
| Contract measurement quantity | his basis 1,297.35 m.l | Urban basis: the physical length of the edges the corner-bead item covers (OD-V3-4); which edges carry a bead (parapet inner edge, mouth ends, frames) is not specified for this project |
| Payable quantity | 648.675 m.l (his half) | a payment convention on the contract quantity; the physical length does not change |
| Urban PDF rate basis | 1,300 m.l x 1.25 KWD = 1,625 KWD | = 648.675 x 2.50 = 1,621.69 KWD; the 3.31 KWD is his 1,297.35 rounded to 1,300. Never m.l -> m2 |

## 6. Rule, test, lesson (standard section 4)

- General rule (any villa; research function `t172_edges.py`, proposed for a future rule version, not a rule file):
  a parapet is two faces (m2), a top (m2), an outer and an inner top arris (m.l, each on its own run), stop-ends only at
  free ends, and an inner base junction that is a termination, not an arris; a niche shallower than the wall does not
  move the inner face; a parapet end against higher construction has no stop-end; an end not shown is HELD. A workbook
  total is reconciled from its cells AND their types: a text cell inside a SUM range is a silent omission.
- Regression test `tests/t172_edges/test_t172_edges.py` (17 tests, non-Alsenan hand fixtures): closed 10 x 6 parapet
  (outer 32.00, inner 30.40, top 6.24 m2, 1.95 edges / m, never 3); two-sided chain against a higher storey; free end
  stop-ends; tangent convex arc and concave bay; niche with different heights either side; half rate never changes the
  physical length (full length x half rate = half length x full rate, no m2); L ring with one concave corner; rotation
  0 / 30 / -121 / 47 deg, mirror, millimetres; missing thickness HELD (refused, never 0); unknown end and held height
  stay ranges; arc thinner than the wall refused.
- Lessons-register row proposed (section 7): 2026-10-22 | Freelancer parapets counted at 3 lines per metre (420.86 m.l)
  against 271.962 m.l of physical top arrises; SE frame missing from his total | a counting convention read as physical
  edges; a text cell ("8.3.1") inside SUM(A51:A90) | parapet = outer + inner top arris on their own runs, stop-ends only
  at free ends, base junction is a termination; check cell types in every reconciled SUM (any villa, any workbook) |
  T-172 | rule recorded; test added.

## 7. Held, unknown, for the designer (no owner question: standard 2.7 not met; the open decisions are drawing items)

1. Profile of the SE stair-tower frame and the NW pool-court arch frame (projection, mouldings): 98.002 .. 195.180 m.l.
2. Whether a drip / throat exists under any slab edge or parapet top (freelancer 181.70 m.l; nothing drawn).
3. The 0.20 m top band on the 2F NW face and the 1F SE wave: coping or plaster band; radius of the rounded parapet
   ends ("rounded edges" in his line name).
4. GF house parapet at the NE passage mouth: stop-end or return (0 .. 1.20 m.l).
5. Boundary wall height and finish (owner Q-65 open in part).

Reproduce: `python3 -I research/agents_t159/t159_extract.py <plan DXF> <scratch> research/urban_m9_s2/SYNTHETIC_FACTS_S2.json`
then `python3 -I research/agents_t172/t172_alsenan.py <scratch>/t159_rings.json --workbook <scratch xlsx> --frames
research/agents_t172/FRAMES_T172.json`. Lengths, areas, levels and statuses only; no coordinates, no client data.
