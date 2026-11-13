# T-760 F-01 external render + external paint to figures (worker 2, 2026-11-13, DELIVERY MODE fix-row set)

Input: `LINE_INDEX_V3_0_79.json` of T-314 r3 (agents/task-T-314 @ 597d2820, READY, stacked on V3.0.78; sha256[:16]
0582aac58defff74, pinned in the builder). Builder: `t760_fill.py <index> [--check]` -> `out/FIX_ROWS.json`
(81 rows: line id, item, unit, before, after, label, basis). Worker 3 wires it after T-314 r3 merges. No drawing was
opened; every figure is a merged ledger figure (T-305, T-324, T-337, T-737, T-751, T-754, T-756) or a company default.

## Lines without a figure (families of the row) and totals after

| item | lines | blank before | ranged before | after (no blank, no range) |
|---|---|---|---|---|
| FIN.EXT.FINISH m2 | 18 | 1 | 17 (1008.58 .. 1085.61) | **1054.00** |
| FIN.EXT.PAINT m2 (= render face by face) | 18 | 1 | 17 | **1054.00** |
| FIN.EXT.PAINT.EDGE lm | 38 | 3 | 35 (280.62 .. 281.82) | **317.10** |
| ARCH.FACADE m2 (geometry register, never added to render: F-T737-3) | 4 | 4 | 0 | 946.98 |
| ARCH.FACADE_RUN lm 'facade outline 2' | 3 | 3 | 0 | 0 NOT_APPLICABLE_WITH_EVIDENCE (L-N10-01 drawing element) |
| ARCH.EXTERIOR m2 | 1 | 0 | 0 | 9.10 already released |

## The figures that decide the total (m2)

- GF storey 391.25: W02 hole 6.33 printed x 2.20 drawn at section B-B = 13.93 (cap was 28.49); D-GF-07 hole
  2.00 x 2.50 printed plan tag = 5.00 (plan dimension governs; F-T737-1). DRAWING-READ.
- 1F storey 249.95: the three arched step returns (1.78) are built faces. DRAWING-READ.
- 1F parapet outer 58.25: NE-1 / SW-1 / SW-2 at parapet 1.20 (DEFAULT).
- Parapet inner x 4 (11.90 / 11.05 / 49.22 / 11.32): R-T324-1 with c = 0.10 above the membrane (roof build-up
  default: 5 cm insulation + 5 cm protection) -> exposed upturn 0.10 of 0.20 = the midpoint; 1F also carries its
  held exposed height at mid (ESTIMATE).
- Plinth 71.75: NW-4 arc on the pool rim +0.30, the ends on the court +0.15 (T-751 DXF lines). DRAWING-READ.
- Slab edges: 1F 6.90 (runs x 0.60 default depth + the porch-mouth band 1.84 of T-754), GF 3.64 (ring x 0.60). DEFAULT.
- Edges: W02 10.73, W03 15.26, W17 9.29 lm (2 jambs + head); GF parapet stop-end at the open passage mouth 1.20.

## Engine vs freelancer (reference, not verification)

Net render 1054.00 vs his 1469.97 m2 = -415.97 (-28.3 %); gross 1170.71 (1054.00 + holes 116.72) vs 1502.84 =
-332.13 (-22.1 %). Paint = render, same %. Proposal RULE_DIFFERENCE (as T-314 r3 / T-747): domes excluded (owner),
half-opening deduction a freelancer practice, boundary wall HELD (Q-65), drip edge excluded. Corners 317.10 lm vs his
1,297.35 lm (2 lm = 1 m2 convention): RULE_DIFFERENCE.

## Uncertain (labelled, replaced when the designer answers)

D-39 roof datum (1F parapet inner height), D-53 W02 count (one drawn), Q-68 C slab-edge depth (0.60 default),
1.80 m of 1F SE-1 behind the annex valued at the default depth.
