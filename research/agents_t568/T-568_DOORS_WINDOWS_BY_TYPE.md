# T-568: doors and windows by type vs the freelancer, nr and m2 apart, on ARCH_TAKEOFF_V3.0.58

Worker 2, 2026-11-06, lane A, non-candidate (research only; no engine, rule, registry, frozen or candidate file
changed). Files: research/agents_t568/* and tests/t568_doors_windows/* only. Development villa; not an accuracy claim.
Drawings and workbooks are cited by Drive folder / title only; no drawing, workbook row table or client name is
committed (his row sizes appear only as compared values, as in T-181 / T-559).

Overlap closed by name: T-181 (MERGED, 2026-10-22) held a type table on the T-150 r2 register when 21 window heights
were still HELD; T-201 / T-207 / T-238 / Q-76 A settled them since. This run supersedes T-181's figures with the
candidate's own lines and spends the rest on T-559's +6.30 m2 opening counts.

## 1. Result in engineering terms (ours = candidate V3.0.58 lines; his = aluminium workbook, sheet الكميات)

| Class | Unit | Ours (settled) | Ours HELD | His | Ours - his | Signed causes (close exactly) |
|---|---|---|---|---|---|---|
| Aluminium doors | nr | 6 (GF 5, 2F 1) | 0 | 5 | +1 | +1 ENGINE_RIGHT (a drawn GF leaf he omits) |
| Aluminium doors | m2 | 12.760 | 0 | 12.000 | +0.760 (+6.3 %) | +1.720 ENGINE_RIGHT (omitted door +2.200 / +1.980; two 0.90 doors -0.240 each: masonry ends 0.900 both faces, his 1.00 = the frame) ; -0.960 RULE_DIFFERENCE (head Q-55 C 2.20 vs his 2.40 on 5 doors) |
| Aluminium windows | nr | 28 | W02 count 1 .. 2 | 29 | -1 | -1 HELD (W02: drawings 1, render 2; D-53). On the drawn count 29 = 29 |
| Aluminium windows | m2 | 76.256 | W02 (no figure), W17 9.870 .. 11.515 | 116.900 | -40.644 | -36.669 HELD (W02 his 27.219; W17 his 9.450) ; -3.975 ENGINE_RIGHT (printed / drawing-confirmed heights vs his flat 2.00: W08 / W09 -0.750, W10 / W25 / W27 -0.500, W24 -0.775, W14 -0.980, W29 -0.600, W26 -0.360; W11 / W12 +0.390, W13 +0.360; W18 +0.600) |
| Windows like for like | m2 | 76.256 on 27 | - | 80.231 | -3.975 (-4.95 %) | as above |
| Windows with Q-76 A on W17 | m2 | 86.126 on 28 | - | 89.681 | -3.555 (-3.96 %) | W17 3.29 x 3.00 = 9.870 vs his 3.15 x 3.00 = 9.450: +0.420 ENGINE_RIGHT (Q-39 C outer arc width) |
| Internal doors (PVC) | nr | 20 (GF 8, 1F 10, 2F 2) | areas of 5 HELD (widths) | none in his supply workbooks | NOT COMPARABLE as supply | count cross-check below |
| Main entrance | nr / m2 | HELD 1 / 5.000 | D-53 | none | NOT COMPARABLE | - |
| Lift landing openings | nr | 3 (excluded: lift supply) | heights HELD | none | NOT COMPARABLE | - |

Count cross-check of internal doors (his only door rows are masonry opening deductions, no supply row; h 2.40):
20 drawn vs his 18: +2 ENGINE_RIGHT (D-1F-02 / D-1F-10 on the stated pairing); m2 28.600 settled vs 36.960 ->
+3.960 ENGINE_RIGHT, -9.840 HELD (5 doors with a held width), -2.480 RULE_DIFFERENCE (heads 2.20 vs 2.40, and
D-GF-08 1.00 drawn vs his 1.10 = the Q-04 wall-opening minimum, which UP-DOOR-OPEN-003 keeps apart from the measured
width).

## 2. The +6.30 m2 of T-559 (opening counts, UNRESOLVED) taken to physical causes

| T-559 part | m2 | Physical element and evidence | Verdict proposal |
|---|---|---|---|
| GF: 5 external doors vs his 4 | +1.98 | P7757.dxf model space, read this run: 5 external door leaves on GF (D120:15E, d220:1B5, D120:192, D120:33E, D120:3FF), each between its own masonry ends; the S8.6 census ties each to its jambs; his aluminium workbook also lists 4 | count ENGINE_RIGHT |
| his 1.00 vs 0.90 (D-GF-03 / -09) | -0.24 | wall-face ends 0.900 apart on both faces at both inserts (the D120 / d220 block is the frame) | ENGINE_RIGHT (width) |
| his 1.10 vs 1.00 (D-GF-08) | -0.24 | drawn 1.000 between the masonry ends; his 1.10 = nominal + 0.10 (Q-04 minimum) | RULE_DIFFERENCE |
| 1F W18 (+1.08) and his sixth 0.60 x 0.80 (-0.48) | +0.60 | not a count: his sixth bath window IS W18 (T-181 tie, his aluminium row of 6); W18 prints 0.50 wide (sheet04 chain) and 2.16 high (NW chain 84 / 216) | ENGINE_RIGHT (size) |
| 1F: 10 doors vs his 8 | +3.96 | 10 door leaves drawn on 1F, each with its swing in its own wall (rendered this run: D315 x 5, D115 x 2, D215 x 2, d220 x 1) | count ENGINE_RIGHT |
| his 0.90 vs 1.00 | +0.24 | the D115 doors are 1.000 between masonry ends | ENGINE_RIGHT (width) |
| **Total** | **+6.30** | ENGINE_RIGHT +6.54, RULE_DIFFERENCE -0.24; residual 0.000 | UNRESOLVED 6.30 -> 0 |

Which drawn door his rows leave out is not identifiable (his rows carry no id). R-T568-1 (d): the class total does not
depend on the pairing; the T-559 pairing (D-GF-05 paired, D-GF-03 omitted) vs the T-181 pairing (the reverse) moves
only +0.020 m2 ENGINE_RIGHT / -0.020 RULE_DIFFERENCE inside the aluminium-door class (printed in the run JSON).

A third record, the owner's cost summary by category (Drive "Alsenan chalet project", the by-category workbook), lists
6 aluminium doors (ours 6, his 5: supports the count) and 18 internal doors (ours 20 drawn, his 18). It is a
procurement record, not a drawing: it does not move a drawn count; the 1F count of 10 rests on the drawn leaves and is
for the Checker's own count (the 18 may follow his takeoff or an as-built change).

## 3. Findings for the Lead

- F-T568-1 (integration gap): the candidate's 1F window m2 line is still HELD 9.870 .. 11.515 for W17 although owner
  Q-76 A (2026-10-24 23:53) fixes 3.29 x 3.00 = 9.870 m2. Wiring it moves 1F ARCH.WINDOW m2 23.285 -> 33.155 settled
  (HELD line retired); no other line moves. Needs a Gate B row (stream F).
- Counts: windows 29 drawn = his 29 (W02 render HELD); aluminium doors 6 vs 5 and internal doors 20 vs 18 are his
  omissions on the drawings.

## 4. Rule (proposed) and lesson

R-T568-1 (every villa; t568_rules.py docstring): one opening = one id on one storey (a second plan reading merges, a
second storey is refused); type table per class with nr and m2 never mixed; causes per pair split width / height by
the height basis (Q-55 C RULE_DIFFERENCE; printed / drawing-confirmed / Q-32 A / Q-76 A ENGINE_RIGHT); our-only
openings classed by an independent read of the drawn leaf; pairing invariance stated and checked.

Lessons-register row (proposed): 2026-11-06 | T-559 left +6.30 m2 as 'counts UNRESOLVED' because his rows carry no id |
a count difference is settled by reading the drawn leaves (door blocks with swings / glazing) independently, not by
naming a pairing; a pairing only splits m2 between width and count terms and must not change the class total |
R-T568-1 | tests/t568_doors_windows (B568 by hand; adverse two storeys, area as nr, row arithmetic, unit twice,
class / storey mismatch, HELD with an area, mm, pairing that changes a total) | proposed.

## 5. Validation

tests/t568_doors_windows 15 passed (the private comparison test runs only with the decoded workbooks); t559 / t181
folders and t061 re-run; freeze 0; codemap rebuilt and checked. Re-run: `t568_alsenan.py --write` (private workbooks in
.work/private).
