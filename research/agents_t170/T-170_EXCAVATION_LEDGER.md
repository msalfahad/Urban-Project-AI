# T-170 Excavation and backfill ledger: foundation level arrangement per footing and per ground beam

Worker 3 (taking the lane S row by the Lead's 06:15 note), 2026-10-25. Development villa, not an accuracy claim. ERS
s.2-4 and s.7 applied. No engine module, method version, route G, rule / knowledge file or released quantity changed.
New: `excavation_ledger_v1.py` (EXCAVATION_LEDGER_V1, unwired, stdlib), `ALSENAN_EXCAVATION_INPUT.json` (values,
Drive titles, DXF handles and DXF coordinates only, read this run), `t170_alsenan_check.py` -> `summary.json`,
`LEDGER_T170.csv` (one row per pit / trench), tests `tests/t170_excavation_ledger/` (19 pass: non-Alsenan hand
fixture villa T170-K + development-villa checks).

## 1. The physical element (ERS s.2.1)

Earthworks for the foundations, BOQ families B1-02 excavation (m3), B1-03 backfill and compaction (m3), B1-04 disposal
(m3): NOT_IMPLEMENTED / not in any method or candidate line today; the freelancer's workbook has no excavation,
backfill or disposal row either (searched FREELANCER_RAW_ROWS: no row), so this is a category MISSING FROM BOTH BOQs,
not a difference between them. Element per isolated footing: a PIT from the existing ground to the excavation
formation; in it, bottom up, the 10 cm plain-concrete blinding projecting 0.10 m beyond the footing, the 7 cm underlay
(5 cm screed + 2 cm membrane), the footing L x W x H, the neck, the ground beams near the top; the remainder is
BACKFILL. Per ground beam / strap: a TRENCH under the beam to the bottom of its own 10 cm blinding.

| Level (owner Q-21 C list) | What the drawings print | Status |
|---|---|---|
| Existing ground | '+-0.00' plot datum (P7757 block LEL x6 on the plot boundary, ST SH08 the same 6, SECTION A-A both ends; T-200) | DRAWING-CONFIRMED as the datum; no survey inside the plot (T-195) |
| Excavation formation | ST p.9 boxed note 1: excavation level NOT LESS THAN 1.5 m below the existing plot level; p.8 note 12: founding level fixed on site after the soil check | HELD (AT_MOST -1.50: a bound, never a depth) |
| Blinding bottom / top | formation / formation + 0.10 (p.13 '10cm Plain con.') | relative DRAWING-CONFIRMED, absolute HELD |
| Footing bottom / top | formation + 0.17 / + 0.17 + H (underlay 0.07 VERIFIED T-206; H p.9) | relative DRAWING-CONFIRMED, absolute HELD |
| Neck start / end | footing top -> ground-beam top (R-NECK-ENDS-1, T-205) | HELD (b and d) |
| Ground-beam top | 'Ground Floor slab level' (a name, p.13) = FFL +1.00 minus an unprinted build-up | HELD |
| Finished floor | GF +1.00, annex +0.30, courts +0.15 | DRAWING-CONFIRMED (not an excavation datum) |

Per footing type above the formation (m): F, F3, FN 0.10 / 0.17 / 0.47; F2 0.52; F4, F5, F15 0.57; F6, F8, F11, F13,
F14 0.67; F9 0.72; F12 0.87 (blinding top / footing bottom / footing top). FF (lift): footing bottom HELD (p.14 prints no
membrane thickness) and its formation is the lift-pit floor ('as per lift manufacturer', T-204).

## 2. What was read (sheets searched)

- Drive "Alsenan chalet project" / ST7757.pdf p.13 (both typical isolated-footing details, the four ground-beam
  sections), p.14 (lift footing, boundary wall), p.9 via T-206 (footing schedule H, notes 1 / 2 / 4).
- ST7757 dxf.dxf (sha256 9f9d1179..., the route G input): every S-FOOTINGS entity and every INSERT 'F' block outline in
  the FOUNDATION PLAN field (min corner + size), matched one to one to the 26 FOOTINGS rows of the route G register by
  position; the 1.00 x 1.00 S-FOOTINGS square at x 111 187.8 (handles 80B..80E, tag 'CN/FN' 808) is the FN at
  149 912.2 repeated on the ground-beam plan (offset +38 724.4 mm, T-205's column-plan translation): not a 27th footing.
- Reused with citation (merged, Checker-verified): T-206 (underlay 0.07, formation limit, p.13), T-200 (no structural
  level printed; +-0.00 datum), T-205 (neck ends), T-219 (underlay area 109.85 m2 on 24 outlines), T-174 / Q-74 (straps),
  D-32 (FN clipped by F9), element register 1B1B (F10 / F).

## 3. The ledger (development villa; LEDGER_T170.csv per line)

| Measure | Value | Status |
|---|---|---|
| Footing elements | 26 (F x4, F2 x2, F3 x2, F4 x2, F5 x2, F6, F8, F9, F11, F12, F13, F14, F15, FF, FN x4, F10/F) | |
| Neat pit plan (blinding extent (L + 0.20)(W + 0.20)), 24 pits | 129.570 m2 gross; 129.234 m2 net of the two real overlaps (0.336 m2) | DRAWING-CONFIRMED |
| Footing footprint, 24 pits | 109.99 m2 gross; 109.85 m2 net of F9 / FN (0.40 x 0.35 = 0.14) = **the Checker-verified T-219 underlay area exactly** | DRAWING-CONFIRMED (independent cross-check 0.000 %) |
| FF lift pit | footprint 20.70 m2; neat plan HELD (p.14: blinding projection and membrane thickness not dimensioned); depth = lift-pit depth (manufacturer) | HELD |
| F10 / F (open outline 1B1B, two tags) | plan HELD (Q-31 C designer item) | HELD |
| Buried structure in the 24 pits (soil displaced) | blinding 12.957 m3, underlay 7.699 m3, footings 52.961 m3; necks HELD; ground beams in pits HELD | DRAWING-CONFIRMED / HELD |
| Ground-beam trenches, 58 route G GROUND rows | neat plan 97.145 m2 (length x (0.30 + 0.20), p.13 '10 / 30 / 10') | DRAWING-CONFIRMED plan (route G band lengths, not re-measured here) |
| Strap trenches SB1 / SB2 / SB3 | footprint 7.889 m2 (L x b); neat plan HELD (no strap section prints a blinding projection) | HELD |
| Excavation m3 (87 lines) | BLANK: plan x D with D = 0.00 - formation, formation HELD (bound AT_MOST -1.50) and working space HELD | HELD, never 0 |
| Backfill m3 (87 lines) | BLANK: excavation - buried structure; material printed 'Well graded clean compacted fill from excavation material' (p.13 x2, p.14) | HELD; material DRAWING-CONFIRMED |
| Disposal m3 | not computed (excavation - backfill re-used) | HELD |

Pit overlaps (defect L-N10-03), as drawing facts independent of the working space:
- real neat overlaps: F9 / FN (outline 180C) 0.330 m2 (footings themselves overlap 0.14 m2, D-32: F9 owns it);
  F8 / FN (10F0) 0.0056 m2 (blinding corners only; the footings are 0.175 m apart);
- pits merge for a working space above w* = half the clear gap between neat plans: F14 / F5 and F8 / F9 at 0.025 m,
  F3 / F (166A) 0.100, F13 / F6 0.125, F3 / F (1667) 0.250, F8 / FN (180C) 0.275 m; 30 pairs merge at w* <= 1.00 m
  (summary.json `overlaps`). So with any practical working space, the east block (F5, F8, F9, F14, FN) is one
  excavation, not separate pits: summing pits would count the shared soil twice.

## 4. Methods side by side

| Method | Excavation | Status |
|---|---|---|
| Owner manual method | none recorded for excavation (OWNER_QUESTIONS_ANSWERED searched: Q-21 C hold the founding level; measure excavation, disposal, replacement fill, compaction, blinding, footings, necks, backfill SEPARATELY; no working-space or pit-vs-bulk rule) | - |
| Released V2.9 + route G | no excavation line; `struct_n10.excavation()` (unwired tool) gives footing pits and trench footprints, volume HELD without depth and working space (UP-EXC-001 REQUIRES_CONFIRMATION) | NOT_IMPLEMENTED in the BOQ |
| Freelancer | no excavation / backfill / disposal row | omitted (silent omission on his side) |
| Drawing-derived (this task) | per pit: plan (neat or + ws) x (EG - formation); per trench: L x (b + 0.20) x (EG - GB top + d + 0.10) | plans DRAWING-CONFIRMED; volumes HELD on the formation, the working space and the GB top |

The excavation volume is linear in the unprinted depth: each metre of depth over the 24 neat pits is 129.23 m3 (net),
before working space; this is a coefficient for the designer item, not a quantity.

## 5. Findings and verdict proposals

1. Backfill material IS printed: 'Well graded clean compacted fill from excavation material' (p.13 both details,
   p.14), 'COMPACTED SOIL' under the ground beam (p.13 right). Owner Q-21 C warned against assuming the fill; the
   drawing settles the material (re-used excavated soil, graded, clean, compacted), not the quantity. DRAWING-CONFIRMED.
2. Waterproofing: 'Two layers liquid water proofing ... applied to all surface in contact with earth' (p.13) means every
   backfilled concrete face is a waterproofing face first (WATERPROOFING.FOUNDATION, T-263): backfill comes after it.
3. The typical boundary wall (p.14, N.I.S.) has a ground beam 'AS PER EXCAVATION DEPTH BELOW N.G. LEVEL' on a 0.80 m
   base with 0.10 blinding: a separate earthwork element, not on the foundation plan; whether it is in the villa scope
   is not established here (named, not measured).
4. Verdict proposals: excavation / backfill / disposal = UNRESOLVED (formation and working space unprinted; designer
   item RFI S1 / P-4 and OQ-13), not FREELANCER_RIGHT (he has no line). Footprint net 109.85 m2 = ENGINE_RIGHT cross-check
   of T-219 by an independent route (DXF outlines, not the T-219 ledger).
5. No owner question: ERS 2.7 not met for the formation (a designer value, RFI S1). The working space and the pit-vs-
   bulk measurement basis are a contractual measurement decision already catalogued as OQ-13 / UP-EXC-001
   REQUIRES_CONFIRMATION: the Lead decides whether OQ-13 goes into the owner's next daily package (section 6 format);
   the ledger gives him the overlap facts (w* per pair) so the question can be put with quantities.

## 6. Rule and lessons row (proposed)

R-EXC-LEDGER-1 (proposed; any villa; provenance T-170, Q-21 C, UP-EXC-001): an excavation line is built from the
printed level chain only: the neat pit / trench plan from the printed blinding projection, the depth from the existing
ground to a formation PRINTED AS A VALUE; a 'not less than' note is a bound and yields no depth; the working space is a
stated fact or HELD; pits are never summed without their pairwise overlap (real intersections deducted, w* reported);
a sloping ground needs every corner level or the pit is HELD; backfill = excavation - every buried element below the
existing ground, HELD while any of them (necks, ground beams) is HELD. Adoption = a new rule version (lane I / Lead).

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-25 | Excavation / backfill missing from both the engine BOQ and the freelancer's; the only tool summed pits as an upper bound and had no positions | The excavation geometry was never separated from the concrete geometry: no plan from the printed blinding projection, no formation-vs-limit distinction, no pit positions | R-EXC-LEDGER-1 (any villa): neat plan from the printed projection, depth only from a printed formation value, working space a stated fact, overlaps by position (w*), sloping ground by corners, held stays blank | tests/t170_excavation_ledger (normal: 3 footings + 1 beam hand-calculated, sloping ground; adverse: missing corner, formation only a bound, formation above the limit, formation above ground, no working space, unprinted underlay / projection, conflicting footing, undeclared unit, mirror) | proposed |

## 7. For the Checker (re-measure from the drawings)

1. ST7757.pdf p.13 right detail: '10 | L x W | 10' under the blinding (projection 0.10 each side) and the fill note.
2. Footing F12 (outline 1ABF, 4400 x 3200 at 131 342.2, 43 598.0; schedule 4.40 x 3.20 x 0.70): neat 4.60 x 3.40 = 15.64
   m2, chain 0.10 / 0.17 / 0.87. Footing F9 (180F, 3400 x 2700) and FN (180C, 1000 x 1000 at 146 262.2, 46 648.0):
   footing overlap 0.40 x 0.35 = 0.14 m2, neat overlap 0.60 x 0.55 = 0.33 m2.
3. F14 (1B1A at 140 062.2, 36 348.0, 3800 x 3300) / F5 (INSERT 166D at 144 112.2, 36 948.0): clear gap 0.25 m between
   footings, 0.05 m between blinding edges -> w* 0.025 m.
4. p.14 lift detail: no blinding projection or membrane thickness dimensioned (FF neat plan HELD).

## 8. Not done / uncertain

- Ground-beam trench lengths are the route G band lengths (not re-measured); trench depth per beam needs the depth
  class by span (p.13) and the GB top (HELD); trench / pit overlaps at beam ends are named, not netted.
- Whether the contractor digs pits or a general (bulk) excavation over the east block is a method / contract matter
  (OQ-13); the w* facts make the choice quantifiable.
- No candidate line, no wiring (lane I after the owner's integration order).
