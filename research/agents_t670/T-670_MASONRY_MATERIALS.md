# T-670: the held B9 masonry MATERIAL lines of ARCH_TAKEOFF_V3.0.63, line by line (lane A, research piece)

Worker 2, 2026-11-10. Research only: no candidate, no released line, no rule / rulebook version file changed. Files:
`research/agents_t670/*`, `tests/t670_masonry_materials/*`. No drawing, workbook, client name or coordinate here.

## 1. Physical element and method (ERS s.2.1)

What is laid to build the candidate's MAS.BLOCK lines: black block units, the 1:4 bed + head joint mortar between
them, the thin-bed glue between AAC units, the AAC units. Installed (theoretical) only; waste / procurement HELD (no
owner rule). Owner manual method: net wall m2 x 12.5 (40 x 20, Q-75 / Q-80) / x 3.5 or 4.5 kg glue; drawing-derived
method: the candidate's MAS.BLOCK net (drawn pieces x clear height - openings) minus the REQUIRED RC lintel faces
(w + 0.80) x D of the printed lintel schedule (T-453 r2 / T-487), x the same rates.

R-T670-1 (PROPOSED, every villa): (1) host = the MAS.BLOCK line, materials found by element id `MATERIAL:<host>`;
(2) REPRODUCE: the merged producer of V3.0.59 (`arch_v3059.material_base / black_rate / aac_bond_rate /
joint_m3_per_m2`, read-only) on the V3.0.63 host + lintel lines with rulebook 1.0.0 gives back every one of the 74
candidate figures (value, range, blank) - else stop (asserted: 0 mismatches); (3) RESTATE with rulebook 1.1.0 (T-615,
UPC-BLACK-BLOCK-001 0.15 = 40 x 20, Q-80 owner 2026-11-07); (4) a HELD host keeps its materials blank with ITS
committed cause (T-654 r4 per-line cause; a held line without a cause is refused); (5) AAC units: no project face and
no count rule -> HELD, the owner's two supplier faces (Q-60) BESIDE only; (6) F-T498-4 sensitivity beside, not applied.

## 2. Before (V3.0.63, 09ec4c1a) -> after (this statement), per code

| code | before | after | change |
|---|---|---|---|
| MAS.UNITS.BLACK pcs | AT_LEAST 1,075.80 (2) + 18 blank | **2,571.27625 (7) + range 698.66125 .. 702.91125 (1) + 12 blank** | +1,495.47625 pcs point (+139.0 %) + 1 range; 6 blank -> valued |
| MAS.MORTAR.BLACK m3 | AT_LEAST 1.269444 (2) PROVISIONAL + 18 blank | **2.59294 (7) + range 0.618315 .. 0.622076 (1) + 12 blank** | +1.323496 m3 (+104.3 %), PROVISIONAL (10 mm joint) |
| MAS.GLUE.AAC kg | 43.596 (2) + 842.06025 .. 861.32025 (3) + 12 blank | unchanged | reproduced exactly; 12 blank all on HELD hosts |
| MAS.UNITS.WHITE pcs | 17 blank | 17 blank | cause: AAC face (5) / host (12) |

The 12 restated lines (all six 0.15 m black hosts, units + mortar):

| host (0.15 black) | net m2 | REQUIRED lintel faces | base m2 | units pcs | mortar m3 |
|---|---|---|---|---|---|
| GF VERIFIED | 9.895 | - | 9.895 | 123.6875 | 0.109463 |
| GF DRAWING_CONFIRMED | 8.595 | - | 8.595 | 107.4375 | 0.095082 |
| GF OWNER_APPROVED | 24.2374 | D-GF-10 0.32 + D-GF-13 0.36 | 23.5574 | 294.4675 | 0.260604 |
| 1F VERIFIED | 52.318 | - | 52.318 | 653.975 | 0.578768 |
| 1F DRAWING_CONFIRMED | 25.2727 | - | 25.2727 | 315.90875 | 0.279579 |
| 1F OWNER_APPROVED | 58.2529 | D-1F-02/03 0.36, 04/07/10 0.32, 08 0.34 = 2.02; D-1F-09 HELD 0 .. 0.34 | 55.8929 .. 56.2329 | 698.66125 .. 702.91125 | 0.618315 .. 0.622076 |

Rate 12.5 / m2 (UPC-BLACK-BLOCK-001 1.1.0, Q-80); joint 0.15 x (1 - 0.39 x 0.19 / 0.40 x 0.20) = 0.0110625 m3/m2.
Hand checks: 8.595 x 12.5 = 107.4375; 24.2374 - 0.68 = 23.5574 x 12.5 = 294.4675, x 0.0110625 = 0.260604.
Status: rate ASSUMED - OWNER-APPROVED (company rule, not printed); host area status unchanged beside (VERIFIED /
DRAWING-CONFIRMED / ASSUMED - OWNER-APPROVED); mortar PROVISIONAL. Not VERIFIED (no Checker re-measure yet).

## 3. Independent checks

- Second path: T-615's wall-level sums (merged, `out/WALLS_015_T615.csv`) per host line: residual 0 on 8 of 12, at
  most 5e-05 pcs / 2e-06 m3 on the other 4 (T-615 prints 4 decimals). Sum 2,194.1375 .. 2,198.3875 pcs = T-615.
- Lintel = face: every one of the 12 REQUIRED faces x host thickness equals its bound STR.CONC.LINTEL m3 exactly
  (e.g. D-GF-13 0.36 x 0.15 = 0.054), all 12 lintel lines RELEASED in V3.0.63: the face leaving the masonry is the
  concrete the B9-02 line carries, once.
- Q-80 condition (report a printed different 15 cm face): T-615 s.2 searched both DXFs; nothing differs. Not re-read.

## 4. Held after, named

12 black / 12 glue / 12 white blank on 15 HELD hosts: 2F roof datum D-39 (6 hosts), BLOCK_WALL_NOT_ESTABLISHED
(7: masonry height not in the drawing), MAIN_S (net AT_LEAST 11.389 m2, thickness / bottom not printed), ANNEX_S
(ground-beam soffit CONFLICT). 5 AAC unit lines on released white hosts: face not selected (62.5 x 25 -> 6.4 / m2 or
60 x 20 -> 8.33 / m2 beside, e.g. GF VERIFIED_WHITE 4.458 m2 -> 28.53 or 37.15 pcs). Waste / procurement: HELD.

**F-T670-1 (for the wiring row):** MAIN_S / ANNEX_S are BLACK block by their own cause (ST p.1 note 2), but their
element ids carry no colour, so the producer also opens MAS.GLUE.AAC and MAS.UNITS.WHITE lines on them (4 lines that
describe no physical material). Proposed: the wiring row splits the colour on these two hosts (2 black codes each),
never values the AAC pair. **F-T670-2 (sensitivity, F-T498-4):** if T-582's V2 lintel classes are wired (no lintel
RELEASED), each REQUIRED face becomes 0 .. face: units GF OA 294.4675 .. 302.9675, 1F OA 698.66125 .. 728.16125; glue
GF OA W 23.535 .. 25.155, 1F VW 444.4695 .. 458.892 (in the JSON per row). The wiring must re-run on its own lintels.

## 5. Freelancer, verdicts, lesson

Freelancer: blockwork in m2 only, no unit / mortar / glue rows (T-176 / T-367): RULE_DIFFERENCE, no %. Verdict
proposals: 12 restated lines ENGINE_RIGHT on the method (hand checks above), pending the Checker's re-measure of two
hosts; F-T670-1 UNRESOLVED (colour split). Lesson row (proposed, ERS s.7): "an owner answer recorded as a new rule
version is applied to the candidate by re-running the merged producer on the candidate's current lines, after first
asserting that the old version reproduces every current figure (every villa; T-670)".
