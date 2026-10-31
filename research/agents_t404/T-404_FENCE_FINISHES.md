# T-404 Boundary fence finishes, face by face (development villa; method every villa)

Worker 2 (lane A), 2026-10-31, claim 16:41 UTC. Research row: no engine, rule, knowledge, method, registry or candidate
line changed; nothing released. ERS applied: s.2.1 (composite element split into faces, top, ends, layers), s.2.2
(printed > drawn; owner method beside the drawing reading), s.2.3 (own reading of p.12), s.2.4 (freelancer closed in m2),
s.2.7 (no new owner question: the open item is already with the owner, see s.6), s.3 (physical face vs finishable face
vs layer; build before deduct), s.4 (rules + tests), s.7 (lesson). Built on merged T-396 (runs, 2.65 height, lower band),
T-361 (gates), T-263 (buried coating), T-305 / T-337 (house facade ledger), T-360 / T-091 (no material note in the set).
Files cited by Drive folder and title; no image, coordinate, client name or note text is committed.

## 0. What was read this run (Drive "Alsenan chalet project", read-only; private copy in .work/private only)

| Source | Read for |
|---|---|
| Alsenan_Architectural_P7757_Pages_11-12.pdf p.12 (60 dpi whole page, 300 dpi crops; nothing scaled) | FENCE SECTION, FENCE ELEVATION, FENCE PLAN: every line, hatch and note on the fence faces, top and ends |
| merged ledgers (values only, read in the repo) | T-396 ALSENAN_FENCE_INPUT.json (band lines by handle, elevation fence-end tops 2.65, court line +0.15); T-337 BINDING_T337.csv (109 house face keys); T-263 s.1 (ST p.14 prints no coating); T-360 SHEET_CENSUS (0 material notes) |
| freelancer exterior plaster + Sigma workbook, sheet 'البيان' rows 87-90 (tests/alsenan/registers_b1, quantities only) | his fence rows |

What p.12 shows (described, not copied): the SECTION draws the wall '265' above the lower ground line, '50' + '215'; the
ground band on the other side is drawn HIGHER than the dimension base (its level is not printed) and the '50' band is
hatched like the ground bands and continuous with the higher band; the wall top is a plain 0.20 end: **no coping, no
drip, no render line, no note**. The FENCE ELEVATION (street side) draws a curved dip carrying an X railing and a
rounded top at the gate end with the house number; the gate-end top is drawn lower than the corner end; none of it is
dimensioned; the 2.50 gate runs from the fence end to the house wall (ground strip only); **no hatch, texture or note
on any fence face**. The FENCE PLAN prints '580' + '250' and no finish. With T-091 (0 finish notes on the plans),
T-360 (0 of 675 DXF texts name a material) and RFI-B-A12 (no finishes schedule or specification issued): **no sheet
prints any finish layer of the fence.**

## 1. The physical element (ERS s.2.1)

| Component | Unit | Owner | This task |
|---|---|---|---|
| OUTSIDE face per run (street / neighbour / sea) | m2 | BOUNDARY WORKS finishes | measured (geometry) |
| PLOT face per run | m2 | BOUNDARY WORKS finishes | measured (geometry) |
| stop-end at a gate jamb where the fence ends | m2 | BOUNDARY WORKS finishes | measured, HELD (shaped top) |
| far jamb of G-01 = the house wall | - | house facade ledger (T-305 / T-337) | not counted |
| wall top | m.l, m2 | BOUNDARY WORKS finishes | measured |
| coping | m.l | - | **NOT_DRAWN** on any sheet: named, no quantity |
| coat below N.G. on the boundary G.B | m2 | T-263 (HELD, gross 35.256) | not counted again |
| coat below N.G. on the boundary masonry | m2 | waterproofing | HELD blank (depth not printed, no note) |
| finish LAYERS on each face: plaster, Sigma / paint | m2 | finishes | **HELD** at most the face (R-T404-5) |
| arrises / corner beads of the fence | m.l | T-405 (B4-09) | named for T-405, not measured here |

## 2. Face table (FACES_T404.csv; acceptance a)

Corner rule (R-T404-1): outside faces run to the external corner point (outside length = outer band line); plot faces
stop at the internal corner (outer - 0.20 per corner). Height 2.65 printed (T-396 R-T396-2). Gates deducted by id at
full height (no wall drawn over them).

| Face | Length m | Gross m2 | Gates (id: m2) | Physical face m2 | Status | of which lower 0.50 band | Finishable (exposed) m2 | Plaster / Sigma |
|---|---|---|---|---|---|---|---|---|
| F-NORTH / OUTSIDE (neighbour) | 31.370 (99 + 98) | 83.1305 | - | **83.1305** | DRAWING-CONFIRMED | 15.685 | HELD, at most 83.1305 (neighbour ground not printed) | HELD at most 83.1305 |
| F-NORTH / PLOT | 30.970 (13A) | 82.0705 | - | **82.0705** | DRAWING-CONFIRMED | 15.485 | HELD 77.425 .. 82.0705 (court +0.15 drawn at both run ends only; 30.97 x 2.50 lower bound) | HELD at most 82.0705 |
| F-STREET / OUTSIDE | 8.300 (10F) | 21.995 | G-01: 6.625 | HELD, **at most 15.370** | HELD (dip, rounded end undimensioned) | 2.900 | HELD at most 15.370 | HELD at most 15.370 |
| F-STREET / PLOT | 8.100 (13A 5.60 + gate) | 21.465 | G-01: 6.625 | HELD, **at most 14.840** | HELD (same profile) | 2.800 | HELD at most 14.840 | HELD at most 14.840 |
| F-SEA / OUTSIDE, PLOT | 2.400 solid (+ G-02 1.00) | - | - | HELD (owner Q-63 C) | HELD | - | HELD | HELD |
| F-LOWER passage closure, both faces | 1.200 | - | - | HELD (no height printed) | HELD | - | HELD | HELD |

Totals by status: physical faces **165.201 m2 DRAWING-CONFIRMED** (north, both faces); street faces HELD at most 30.210
m2; sea and passage faces HELD blank (no bound). Finish layers: **0 m2 DRAWING-CONFIRMED, all HELD** (never 0).

Other items (ITEMS_T404.csv; acceptance b): north top **31.37 m.l / 6.274 m2 DC** (geometry; layer HELD); street top
HELD, at least 5.60 m.l / 1.12 m2 (shaped top: developed length > plan); stop-end at G-01 HELD at most 0.530 m2;
coping NOT_DRAWN; below-N.G. coating: G.B faces owned by T-263, masonry faces HELD blank.

## 3. Owner manual method beside the drawing-derived method (ERS s.2.2)

- OWNER MANUAL METHOD (OWNER_NOTES_SIGMA_2026-10-21): exterior Sigma = the exterior plaster area, measured on the house
  elevations. The owner was asked whether the boundary wall is in Sigma: item 3, **"not answered yet (boundary wall stays
  HELD under Q-65)"**. Q-65 C holds the fence material. No owner rule names a site wall's finish. So the house method is
  NOT carried to the fence (R-T404-5).
- DRAWING-DERIVED METHOD: the faces exist and are measured (URBAN-FINISH-QUANTITY-INDEPENDENT-OF-MATERIAL@v1 releases a
  geometry independently of its material); which layer goes on which face is printed nowhere, so each layer stays HELD
  with the face as its bound.

## 4. Cross-trade (acceptance c): 0 shared faces

0 keys shared with the 109 T-337 house face keys. One house face stands on the boundary line (GF/NE-6x/EDGE/parapet,
annex parapet B34, band +4.30 .. +4.80): its level band does not meet the fence band 0 .. 2.65, overlap **0.000 m2**.
The far jamb of G-01 is the house wall (house ledger). T-396 plane, T-263 G.B faces and T-405 edges: each bound once.

## 5. Freelancer (quantities only; acceptance d)

His exterior plaster + Sigma rows 87-90: r87 'سور' 37.65 x 2.40 = 90.36; r88 'تابع' 5.80 x 2.40 = 13.92; r89 'تابع' 0.50 x
2.40 = 1.20; r90 'كتف' 4 x 0.20 x 2.20 = 1.76; **total 107.24 m2** (and 165.09 m.l of fence arrises, T-172: for T-405).
He carries **three** face lengths, not four: one north face is outside his take. Which one is not proven:

| Mapping | r87 is | r88 is | north face he omits | Ours on his scope | Diff |
|---|---|---|---|---|---|
| A | PLOT faces 30.97 + 5.60 = 36.57 | street OUTSIDE 5.80 (exact) | OUTSIDE (neighbour) 83.1305 | 112.8105 (at most) | -5.5705 |
| B | OUTSIDE faces 31.37 + 5.80 = 37.17 (his blockwork basis) | street PLOT at 5.80 (ours 5.60) | PLOT 82.0705 | 113.8705 (at most) | -6.6305 |

Causes (mapping A; B in FREELANCER_T404.csv), residual **0.000 m2** in both:

| Cause | m2 | Verdict proposal |
|---|---|---|
| height 2.40 vs printed 2.65 on r87 + r88 (43.45 m) | -10.8625 | ENGINE_RIGHT on the physical face; his 2.40 matches no printed or drawn level (2.65 above N.G.; 2.50 above the court) |
| r87 length 37.65 vs 36.57 (A) / 37.17 (B) | +2.862 / +1.272 | UNRESOLVED (typed figure, no formula) |
| r89 0.50 m row, no counterpart | +1.20 | UNRESOLVED |
| r90 four 'shoulders' 0.20 x 2.20 vs our one fence end 0.53 | +1.76 - 0.53 | UNRESOLVED (we have one fence-owned jamb; the gate's other jamb is the house) |
| one north face (83.13 or 82.07 m2) | not compared | RULE_DIFFERENCE (scope: which faces this contract finishes, owner item open) |
| dip / rounded end not deducted by him | not compared | ours HELD at most |

## 6. Owner / designer items (no new owner question)

The finish of the fence faces is genuinely unspecified (ERS s.2.7), but the question is ALREADY with the owner
(OWNER_NOTES_SIGMA item 3, under Q-65 C), so no duplicate is filed. For the main chat's package, the facts it needs:
(1) which faces this contract finishes (both north faces, or the plot face only: 83.1305 m2 at stake, the freelancer
carries one); (2) whether the fence takes the house system (plaster + Sigma) or another; (3) whether the top is
plastered (6.274 m2 north + the street top). Designer facts (rfi/B, nothing sent): the street fence top profile (dip
depth / chord, the rounded end radius and the gate-end top level): it holds 30.21 m2 of street faces, the street top
and the 0.53 end; the outside finished ground levels along the neighbour and street sides (the outside exposed height).

## 7. Rules, tests, lesson

Rules R-T404-1 .. -6 in `fence_finish.py` (research, every villa): faces per side with the corner convention; gates by id
on both faces, stop-ends only where the fence ends; physical vs finishable height per side; undimensioned profile held
at most / at least; layer authority (no house finish by default; coping NOT_DRAWN); freelancer by face. Tests
`tests/t404_fence_finish` (14): Villa M hand fixture (135.840 m2 faces, 41.580 / 17.430 finishable, 0.480 end, tops 4.000
/ 1.660), order invariance; adverse: house Sigma by default, one face for both sides, held as 0, gate wider than face,
repeated gate id, mm as m, house jamb as a fence end, level above the top, undimensioned dip / shaped top released,
shared key; development villa outputs reproduce and pin; no coordinate committed.

Lane I proposal (no candidate line here): BOUNDARY WORKS finish lines per face: physical face m2 (north outside 83.1305,
north plot 82.0705 DRAWING-CONFIRMED; street HELD at most 15.370 / 14.840; sea, passage HELD blank), layer lines
plaster and Sigma / paint HELD blank with the at-most beside, the top line (31.37 m.l DC + street HELD), coping
NOT_DRAWN named; bind G-01 / G-02 by id, the far G-01 jamb to the house ledger.

Lessons-register row proposed: | 2026-10-31 | The fence finish was carried by the freelancer as 107.24 m2 at a 2.40 m
height on three face lengths, and in the candidate as one HELD OTHER_TRADE row with no faces | the fence was a held
material question, never enumerated as faces per side, and the house facade finish was the only finish method in view |
a site wall's finishes are bound face by face (outside, plot, ends, top), each face measured as geometry; a layer exists
only by a printed note or an owner rule naming site walls, never by the house finish; the exposed height is taken per
side from that side's finished ground (scope: every villa; provenance T-404) | tests/t404_fence_finish (house Sigma by
default refused, one face for both sides refused, held as 0 refused) | PROPOSED |

## 8. Missing / uncertain

- Every finish layer (no note; owner item open). The street profile. Outside finished ground levels. Whether the court
  +0.15 runs along the whole north plot face (drawn at its two ends only: the plot face's finishable area is a range).
- The p.12 section is unlocated (T-396 residual risk); the 2.65 applies to north + street on T-396's DRAWING-CONFIRMED basis.
- The lower 0.50 band: hatched with the ground on p.12; if it is a concrete plinth or a paved upstand its finish may
  differ: shown per face (15.685 / 15.485 / 2.900 / 2.800 m2) so either reading can be bound.

Reproduce: `python3 -I research/agents_t404/t404_alsenan.py --check`.
