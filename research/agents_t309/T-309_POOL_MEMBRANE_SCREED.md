# T-309: pool membrane and protection screed, face by face on the verified pool shell (MISSING category)

Worker 2 (lane A), 2026-10-26. Development villa, not an accuracy claim. Nothing is wired; no candidate or released
quantity changes; V2.9 + route G stays the default. ENGINEERING_REASONING_STANDARD s.2 - s.4 and s.7 applied.

## 1. Physical element (ERS s.2.1)

POOL-1, GF pool room: an open RC tank, D on plan (straight back 3.50 on the boundary-wall line, sides 1.75, half circle
r 1.75 outer), walls 0.20, base 0.40 (Checker-VERIFIED shell, T-183 r2 / T-193; levels rim +0.30, structural base top
-0.90, base underside -1.30; owner Q-26 A flat floor). Two printed layers outside the concrete, each its own item:

| Layer | Print (Drive "Alsenan chalet project", "ST7757 dxf.dxf", DETAIL OF SWIMMING POOL, TEXT 1864) | Drawn extent (own read, entity by entity) |
|---|---|---|
| protection screed | TEXT 1874 '5cm SECREED.' (leader 1873) | HATCH 184E layer S-SECRH.D: one closed band between the concrete outer-face lines (187A, 1871, 18A5, 184B, 1927) and polyline 1854, under the whole base and up BOTH cut outer wall faces to the wall-top line (186D / 1843 / 1930) |
| membrane | TEXT 1876 '5cm INSULATION MEMBRANE.' (leader 1875) | HATCH 1851 layer S-INSU.D: the next band outward, between polylines 1854 and 184D, same extent: under the base and up both outer faces to the wall-top line; its bottom leg also runs under the vertical screed |
| plain concrete | TEXT 1877 '10cm PLAIN CONCRETE.' | HATCH 1855 S-PLAH.D: under the membrane only (not this task: T-183 line B) |

Order from the concrete outward on every drawn face: concrete | screed | membrane | soil (blinding under the base). No
hatch on the water side, on the water floor or on the wall top. The detail is N.I.S. (base '40' = 1,495.7 drawing units,
wall 995.7 units for a printed 20): no dimension is scaled off it; it fixes WHICH faces and the order, thicknesses come
from the printed '5cm'. The detail draws a sloped base (R1 / R2 ends); owner Q-26 A sets the floor flat, so the base
underside is one flat face at -1.30 and its plan area is its developed area.

What the print fixes: thickness 5 cm each, the words 'SECREED' and 'INSULATION MEMBRANE', the faces covered, the end at
the wall top. What it leaves open: the membrane's FUNCTION (waterproofing or thermal insulation; consultant S8.2, open),
product, laps, and the termination where the wall stands 0.15 above the +0.15 deck finish (T-183 C9).

## 2. Face ledger (every shell face once; m2 on the protected concrete face)

| Face | Shell m2 | Status | Membrane m2 | Screed m3 |
|---|---|---|---|---|
| BASE-U base underside | 10.935564 | COVERED | 10.935564 | 0.578469 (sheet 11.569380 m2 to the outer face of the vertical screed x 0.05) |
| OUT-BACK, -1.30 -> +0.30 (3.50 x 1.60; no deck behind) | 5.600000 | COVERED | 5.600000 | 0.288000 ((3.50 x 0.05 + 2 x 0.05^2) x 1.60) |
| OUT-SIDE-1 / -2, -1.30 -> +0.15 (2 x 1.75 x 1.45) | 5.075000 | COVERED | 5.075000 | 0.253750 |
| OUT-ARC, -1.30 -> +0.15 (5.497787 x 1.45) | 7.971791 | COVERED | 7.971791 | 0.404284 (pi/2 (1.80^2 - 1.75^2) x 1.45) |
| upstands +0.15 -> +0.30 on the deck edges (8.997787 x 0.15) | 1.349668 | UNRESOLVED | blank (0 .. 1.349668) | blank (0 .. 0.068072) |
| WATER-FLOOR (structural base top) | 8.578838 | NOT_COVERED (no hatch) | - | - |
| WATER-WALLS (11.069469 x 1.20) | 13.283362 | NOT_COVERED (no hatch) | - | - |
| WALL-TOP (band) | 2.356726 | NOT_COVERED (no hatch) | - | - |
| **closure** | **55.150949** = 10.935564 + 12.497787 x 1.60 + 8.578838 + 13.283362 + 2.356726 | residual **0.000000** | | |

Results (DRAWING-CONFIRMED, not verified; function HELD):

- **Pool membrane: 29.582 m2** + **0 .. 1.350 m2 HELD** (upstand termination). T-183 r2's 30.932 m2 = 29.582 + 1.350:
  it included the upstand faces the architectural cut leaves exposed above the deck; this ledger keeps them blank.
- **Protection screed: 1.525 m3** (face 29.582 m2) + **0 .. 0.068 m3 HELD**. T-183 r2's 1.591 m3 vs 1.525 + 0.068 =
  1.593 m3: +0.068 upstand split out, and +0.0018 m3 from the two back corners taken square (t^2 each, as the drawn
  plan corners) instead of rounded (pi t^2 / 4): 2 x (0.0025 - 0.0019635) x (0.05 + 1.60) = 0.0018 m3.
- Information only (procurement side, never the measure): the membrane's own inner surface, offset by the screed,
  32.780 m2 (sheet 11.569 + vertical 12.854867 x 1.65, upstand included). The contract measure stays the protected
  concrete face, the convention of the merged foundation waterproofing family (T-219 / T-270: membrane on the footing
  outline).

Freelancer: no pool membrane or screed row found (search of the 885 raw rows in tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json for the pool words; his pool rows: RC sheet rows 11-16 concrete only; FIN rows 18-19 pool floor
21 m2 / walls 19.8 m2 ceramic). His silence is not absence (lessons row 2026-10-24, T-219): RULE / SCOPE difference, the
whole 29.582 m2 + 1.525 m3 is scope he does not carry. Engine: no candidate line (T-303 inventory keys
WP.POOL_TANK.POOL_MEMBRANE and .POOL_PROTECTION_SCREED both MISSING; engine/source/exterior_spaces.py holds the pool as
an exterior space with POOL_NO_MEMBRANE_RULE, which is the water side, not these layers).

## 3. Lane I consumer shape (POOL_MEMBRANE_LINES_T309.json)

| key | unit | quantity | status | held part | function |
|---|---|---|---|---|---|
| WP.POOL_TANK.POOL_MEMBRANE[m2]/POOL-1/BASE_AND_OUTER_WALLS | m2 | 29.582355 | DRAWING-CONFIRMED | 0 .. 1.349668 | HELD (S8.2) |
| WP.POOL_TANK.POOL_PROTECTION_SCREED[m3]/POOL-1/BASE_AND_OUTER_WALLS | m3 | 1.524503 | DRAWING-CONFIRMED | 0 .. 0.068072 | - |

The family name stays 'pool membrane'; it is never relabelled waterproofing or insulation without a source.

## 4. Open items (designer list; nothing for the owner under ERS 2.7: no owner method changes, the documents settle the
measured faces)

S8.2 membrane function / product (unchanged); C9 termination of screed + membrane at the 0.15 upstand along the 8.998 m
deck edge (p.7 draws them to the wall top; the architectural NW cut leaves the upstand face exposed above +0.15);
C6 the boundary-wall base under the back wall (T-183 interface 2): the membrane under the base and on the back face are
booked as drawn; if the B.W band sits under the pool base the designer states how the layers pass it.

## 5. Rule, tests, files

R-T309-1 (PROJECT-INDEPENDENT research rule, not a rule-file version): a pool / tank protective layer is booked face by
face on the verified shell: COVERED only where its hatch is drawn, NOT_COVERED with sheet evidence, UNRESOLVED (blank +
bound) where two documents disagree on its end; each face once; contract measure on the protected concrete face, layer
surface as information; a printed word fixes thickness, not function.

Files: research/agents_t309/t309_pool_membrane.py (core), t309_alsenan.py (--write / --check byte-identical; reads
research/agents_t183/ALSENAN_POOL_INPUT.json only), POOL_MEMBRANE_FACES_T309.json, POOL_MEMBRANE_LINES_T309.json;
tests/t309_pool_membrane (villa P309 rectangle and D309 D by hand: normal, deck upstands, hatch end below the rim, mirror
/ order; adverse: hatch extended to water faces / wall top / upstand refused, finished wall basis refused, base thickness
vs levels refused, missing layer HELD never 0, thickness 0 refused, function without source refused, mm refused, face
twice / open perimeter refused; development villa pinned).

Lessons-register row (proposed, ERS s.7): 2026-10-26 | pool membrane / screed MISSING from every line; the drawn extent
(T-183) counted the 0.15 upstand faces above the deck as covered | a layer's extent was taken from one detail without
comparing its end with the adjoining finished level of the other discipline | book a protective layer face by face on the
shell; where the detail's end and the adjoining level disagree, the face is UNRESOLVED (blank + bound), never in or out
by default (every villa: pools, tanks, planters, basement walls) | tests/t309_pool_membrane (upstand UNRESOLVED; booking
on it refused) | PROPOSED.
