# T-539: masonry accessory ledgers V2 on END_CENSUS_V3 (F-T536-1), rule R-T539-1

Worker 1, lane S, claim 2026-11-05 23:21 UTC, base engine 322c1409 (candidate of record unchanged; released default
V2.9 + route G untouched). Research only, unwired: `accessory_ledger_v2.py` (project-agnostic rule), `t539_alsenan.py`
(training-villa builder on the merged ledgers' own code), `out/` (ids and numbers only), `tests/t539_accessory_ledger_v2/`
(fixture P539 + Alsenan pins, 26 tests). No drawing read in this task: every input is a merged ledger (T-274 pieces,
T-317, T-355, T-526, T-532, T-533). No registry, candidate, rule-store or merged research file changed.

## 1. Physical elements and the engineering question (ERS s.2.1)

Three separate optional items of Q-77 (owner 2026-10-29), never in the block m2 and never summed together:

| Item | Physical element | Unit | Depends on the course module? |
|---|---|---|---|
| SHARMAT tie | metal tie, column face to bed joint, one per 3rd course at each block-end / column-face junction | pcs | YES (count of levels) |
| Bed-joint MESH STRIP | strip in the bed joint over every 3rd course, ALONG the wall over the block present | m.l | YES (levels) |
| Plaster-stage JOINT MESH (B9-03) | vertical strip over the block-to-column joint inside each finished side | m.l | NO (a height) |

Correction to the row text: the "+40.90 m.l (owner band) / +44.10 (drawing band)" carried from T-526 is the T-317
plaster-stage V-joint mesh (third item), not the bed-joint strip. A run that ENDS on a column face with gap 0 keeps its
clear length (T-526: 0 m, 0 m2, 0 blocks), so it adds **0 m.l of bed-joint strip**: the strip stops at the column face.

## 2. Rule R-T539-1 COLUMN_END_ACCESSORY_LEDGER_V2 (every villa; provenance F-T536-1, F-C-T532-1, T-539)

1. Population = merged interior junctions (R-T355-3) + every R-T532-1 END junction; a key twice is refused; a census-HELD
   end stays HELD by name.
2. Course module only from R-T533-1 (type, thickness): 0.20 m black resolves to 0.19 + 0.010 = 0.200 m (UPC-BLACK-BLOCK-001,
   equal to T-355 PRIMARY, asserted); 0.15 m black has no sourced entry -> every tie and strip level HELD by name, the
   T-533 what-ifs S-A 0.200 / S-B 0.210 / S-C 0.250 shown beside, never summed; white HELD (Q-60).
3. Ties per junction = R-T355-1 levels on the block beside the column.
4. Strip at an END junction = 0 when d_length = 0 and gap <= one joint; anything else refused here.
5. V joint at an END, per finished side: owner = min(top, band top) - band bottom; drawing = top - FFL; an exterior Sigma
   side carries one band (owner = drawing), as the T-355 R-T355-4 class table does.
6. No head from a sliver (F-C-T532-1): an end piece < 5 mm never gives the head; when the next piece is under the SAME
   member with the same top (the sliver is a cut of that member's band) the member's soffit stands, otherwise HELD.
7. One proposed BOQ line per item (LINE_FAMILIES_T539.json).

## 3. Results on the development villa (out/SUMMARY_T539.json, END_ITEMS_T539.csv)

**Ties at the 12 + 1 ends** (T-526 carried +30 nr on T-355's 0.200 course):

| End | t / type | top | V2 | S-A / S-B / S-C what-if |
|---|---|---|---|---|
| 1F-W09 e0, 2F-W00 e1, 2F-W01 e0 | 0.20 black | 3.80 | **6 + 6 + 6 = 18 MEASURED** (ASSUMED — OWNER-APPROVED) | - |
| 1F-W23 e0 | 0.15 black | 3.70 | HELD (R-T533-1) | 6 / 5 / 4 |
| 2F-W08 e0 | 0.15 black | 3.80 | HELD (R-T533-1) | 6 / 6 / 5 |
| GF-W03 e0/e1, GF-W09, GF-W25, GF-W10 / W16 / W18 (white), GF-W20 (partial) | - | - | HELD by T-526's own names | - |

Reconciliation: +30 = 18 measured + 12 HELD at the S-A what-if (cause: the 0.15 m module is not sourced, T-533).
2F-W00 e1 carries an UPPER bound (lift door L-2F-01 in the same band; station not tied), as T-317 flags its V joint.

**Interior ties restated under R-T533-1:** T-355 measured 182 nr; the 23 junctions on 0.20 m black walls keep 133 nr
byte-equal; **8 junctions / 49 nr on 0.15 m walls move to HELD** (GF-W26, GF-W28, GF-W32, 1F-W14+15, 1F-W20, 1F-W23;
what-ifs 49 / 44 / 36, S-B equal to T-355's alt-210 column). **Ledger V2: 130 junctions, 26 measured = 151 nr, 104 HELD**
(white 69, 0.15 module 10, lift tie beam 11, top unknown 9, annex 4, partial 1).

**Bed-joint strip:** ends add 0.0 m.l. T-355's 543.4739 m.l splits into **175.4844 m.l measured (9 walls, 0.20 m)** and
**367.9895 m.l HELD on 25 0.15 m walls** (what-ifs S-A 367.9895 = T-355, S-B 357.6506 = T-355 alt-210, S-C 289.2131).
That is 67.7 % of the T-355 strip and 26.9 % of its ties resting on an unsourced module.

**Plaster-stage V-joint mesh (B9-03):** 6 ends measured, 14 end sides HELD. Owner band +40.90 m.l (= T-526). Drawing band:
T-317 raw +44.10 (= T-526); classed as the T-355 table does, **+44.20**: the residual +0.10 is GF-W16 end 0's exterior
Sigma side, one band 3.75 (owner = drawing) where the raw drawing band reads 3.65. By class (owner / drawing, m.l):
A 109.85 -> 119.90 / 216.62 -> 227.62; B 67.90 -> 77.95 / 111.02 -> 122.12; C 230.14 -> 233.89 (one band); MIXED
87.05 -> 94.05 / 174.44 -> 181.69; UNKNOWN 16.75 -> 26.80 / 26.12 -> 37.22. Neither band chosen (Q-77).

**Slivers:** 6 of the 13 end pieces are under 5 mm. 4 are cuts of the same beam as the next piece (2F-W01 e0 0.42 mm B1,
GF-W03 e0 / e1, GF-W18 e0): head kept. 2 are under another member/face (GF-W10 e1 FACE GF-011, F-C-T532-1; GF-W25 e0
CB7 beside a slab face): HELD, both were HELD on other causes already. Interior: 48 same-member slivers, 2 other-member
(GF-W01 @17.170, 1F-W04 @0.900), both with no top, so the merged ledgers never took a head from them.

**2F datum D-39** (T-317 / T-355 storey 4.20 vs T-488 4.25 - b_r): every measured 2F tie and strip row re-run with the tops
at -0.05 and +0.05 m: no count moves (2F-W00 6, 2F-W01 6, 2F-W06 24 nr; strip 10.80 / 2.30 / 23.40 m.l). The 2F end V
joints' drawing band is 7.40 per end on the T-317 basis, 7.50 - 2 b_r on the T-488 basis (named, not chosen).

## 4. Proposed BOQ lines (S package, unwired)

| Code | Family | Unit | Owner trade | V2 quantity (dev villa) |
|---|---|---|---|---|
| MAS.TIE.SHARMAT | B9-06 proposed (missing category) | pcs | masonry, blocks section, optional | 151 measured + 104 junctions HELD; SPECIFICATION HELD |
| MAS.MESH.BED_JOINT | B9-07 proposed (missing category) | m.l | masonry, blocks section, optional | 175.4844 measured; 0.15 m and white walls HELD |
| MAS.MESH.JOINT | B9-03 (existing, NOT_IMPLEMENTED) | m.l | plaster stage, separate | per class A / B / C lines, MIXED / UNKNOWN HELD, two bands |

## 5. Verdicts

Freelancer: no tie, strip or joint-mesh row (T-355 / T-317) -> RULE_DIFFERENCE, no % comparison. T-526 / T-532 deltas vs
V2: ties ENGINE_WRONG in part (12 nr counted on a module of another thickness) -> HELD; mesh AGREE (owner) and +0.10
named (drawing, classing convention). T-355 interior on 0.15 m walls: ENGINE_WRONG under R-T533-1 (merged later) -> HELD.

## 6. Lessons row (ERS s.7, proposed)

| 2026-11-05 | the board carried '+40.90 m.l mesh' from a column-end census as if it were the bed-joint strip, and 49 ties on
0.15 m walls stood MEASURED on the 0.20 m block's course | an accessory figure was read without its element and a course
module was carried across thicknesses | name the physical item before summing (strip along the wall vs V joint up the
joint); course module per (type, thickness) from R-T533-1 or HELD; never a head from a sliver of another member (every
villa; R-T539-1) | tests/t539_accessory_ledger_v2 (P539 hand count; sliver other / same member; unknown kind; partial;
mirror; 0.15 HELD; mm refused) | PROPOSED |

## 7. For the Checker (re-measure)

- 1F-W09 e0: block top 4.20 - 0.40 (B1) = 3.80; levels 0.6 .. 3.6 (3.61 < 3.80) = 6 ties; V joints 2 x (3.45 - 0.10) =
  6.70 owner, 2 x (3.80 - 0.10) = 7.40 drawing; strip 0.
- 1F-W23 e0 (0.15): top 4.20 - 0.50 (CB13) = 3.70: S-A 6 (3.61 < 3.70), S-B 5 (3.79 >= 3.70), S-C 4 (3.76 >= 3.70): HELD.
- GF-W16 e0 EXT side: min(3.75, 4.50) - 0.00 = 3.75 one band (raw drawing 3.75 - 0.10 = 3.65).

Reproduce: `bash scripts/agent_env.sh pytest tests/t539_accessory_ledger_v2` (the pins test rebuilds every output and
compares it byte for byte; on a difference it writes fresh copies to the temp folder).
