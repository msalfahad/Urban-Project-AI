# T-624 beam-end open items after T-614 r2 / T-619 (research, unwired; lane S)

Candidate ARCH_TAKEOFF_V3.0.57 (= V3.0.58 for STR.CONC.BEAM). Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'
(sha256 9f9d1179..) read only in .work/private. Nothing released, no candidate line moved. Output:
out/T624_BEAM_END_OPEN_ITEMS.json / .md (`t624_alsenan.py <dxf> --write`); rules R-T624-1 (PROPOSED) in t624_rules.py.

## Physical element and method

Each item is a part of a drawn beam band beside a column or another beam (union of drawn outlines), owned once
(UP-CONC-JOINT-001 1.0.0, R-T600-1, R-T610-1, R-T614-1 (g)). Billing is read from the line's own terms: route G
rectangle(s) and the T-229 named terms. The T-229 census was re-run with its own unchanged code and the polygon of every
end region it measured was kept (areas reproduce `beyond_area_m2` to 1e-5); its frame is put on the route G sheet frame
by the median offset of the same pieces (spread GF 2.3 mm, 1F 1.1 mm, 2F 0.5 mm). A foreign region counts only where it
bills (T-229 status BEAM_SHORT) and after erosion by that spread.

## Results

| item | finding | verdict | m3 |
|---|---|---|---|
| (a) GF CB4 BAND0021.1.r2 +0.01355 | the r2 mean-length excess (2.5099 - 2.3744 = 0.1355 x 0.20 = 0.027103 m2) is the drawn triangle between CB4 faces 645 / 648 and B27 face 805 (0.027099 m2): outside every other member's rectangle, billed by no other line, in no other billed T-229 region, not a slab panel. T-614 r2's 'inside a neighbour rectangle' is not supported (its hull stopped at the shorter face) | ENGINE_RIGHT | 0 (diff +0.000002) |
| (b) GF B28 at C27 | strip 0.015961 m2 beside carried 31B lies wholly in B28's END_SHORT_AT_CARRIED region (0.081634 m2 x 0.75 = 0.061225 vs add 0.0612); the region's drawn content (band strip between support 878 and 31B's far edge, drawn all round) 0.081049 m2: +0.000439 m3 | ENGINE_RIGHT | 0 |
| (b) GF B26 at C27 | piece 0.147325 m2 inside B26's END_SHORT_AT_CARRIED region (0.213219 x 0.85 = 0.181236 vs 0.1812); 0.000052 m2 outside (0.000045 m3) | ENGINE_RIGHT | 0 |
| (b) GF B27 at C8 | 0.209768 of 0.210123 m2 owned in B27's END_SHORT_OBLIQUE region (0.210229 x 0.85 = 0.178695 vs 0.1787); 0.013237 m2 is the T-610 B1 zone (FR-T610-1, not again); 0.000355 m2 position offset, region area equals drawn area within 0.00009 m3 | ENGINE_RIGHT | 0 |
| (b) GF B26 at C25 | B26 is drawn 1.488 deg off the orthogonal column 371 (0.70 x 0.25); both faces end on the column; the rectangle stops at the column's far corner: wedge 0.6435 x 0.0167 / 2 + 0.25 x 0.0065 / 2 = 0.006171 m2 owned, T-229 END_AT_SUPPORT (no term), billed by nobody | ENGINE_WRONG OMISSION FR-T624-1 | +0.005245 |
| (b) 1F B19 at C15 | B19 is drawn 6.910 deg off column 667 (0.20 x 1.00); lower face 1713 runs 0.153 m past the rectangle end to the column: wedge 0.153 x 0.0185 / 2 = 0.001418 m2. T-229 called it square (<= SQUARE_MAX 0.002 m2, a fit tolerance) | ENGINE_WRONG OMISSION FR-T624-2 | +0.001064 |
| (c) F-T619-1 GF B27 tip 0.001524 m2 | the tip lies in B27's rectangle .1, which the run bills whole (2.944132 x 0.85 = 2.502512 = term 2.5025); route G deducts exactly 0.001524 m2 from B1 (owner BAND0048.1), B1 = (0.38 - 0.001524) x 0.40 = 0.151391 as printed; no T-229 region holds it | ENGINE_RIGHT, companion 0 | 0 |
| (d) F-T619-2 FR-T614-H1 0.00454 m2 | CB8 BAND0039's top face 684 stops 24.8 mm before col 2 (37D) inside B27's band; its bottom face 626 runs on past the column; the piece is enclosed by 626, B27 face 806 and column face 893 (drawn share 1.0): 0.0248 x (0.200 + 0.166) / 2. Owner: CB8 L-7c1a1da8 (run BM-GF-040#BAND0039 3.4502 m = hull to 684's end), billed by nobody | ENGINE_WRONG OMISSION FR-T624-3 (supersedes FR-T614-H1) | +0.003405 |

Run decompositions (R-T624-1 (b)): GF B26 4.0846 = 3.1039 + 0.6832 + 0.1163 + 0.1812; GF B27 4.1918 = 2.5025 + 0.8406 +
0.4418 + 0.1787 + 0.2282; GF B28 0.2121 = 0.1509 + 0.0612; 1F B19 1.6301 = 1.6012 + 0.0289 (residual 0 each). The
T-614 'UNPLACED / AMBIGUOUS' states came from matching the run's net value (+0.1798, +0.4046) or the add value against
drawn part subsets; the run value is its terms, each a region.

## B10 STR.CONC.BEAM (research, unwired)

V14 66.392081 .. 66.393376 -> 66.392081 (item (c): the high end double-counts the tip) + FR-T624-1..3 0.009714 =
66.401795 m3. Against his 66.093875: +0.307920 m3 (+0.466 %), every term a physical cause (ENGINE_RIGHT on own calc).

## General rule found (every villa)

A T-229 named term is a region built from the drawing: place a piece by rebuilding that region, never by matching a
value against drawn part subsets; a run value is the sum of its terms. Hull ends taken at the shorter face hide drawn
concrete where a crossing beam's face replaces one face (CB8 col 2) or a column edge carries the face (B28 at 31B).
A skewed band against an orthogonal column leaves a drawn wedge whatever its area; an area threshold for fit noise
cannot tell it from noise.

## Lessons-register row (ERS s.7, PROPOSED)

| 2026-11-08 | 5 beam-end pieces left UNRESOLVED / HELD by value matching and a hull artifact; 2 skew wedges and 1 end gap were
real omissions (+0.009714 m3), 3 pieces and 1 tip were billed once | a named add was placed by value, not by its own
construction; the band hull stopped at the shorter face; T-229 SQUARE_MAX treated drawn wedges as fit noise | rebuild
each named term's region from the drawing and test the piece inside it; read a band's end from each face line; a wedge
whose faces reach the column is measured whatever its area (every villa) | tests/t624_beam_end_open_items normal +
adverse | PROPOSED |
