# T-642 fix rows (generated; research, unwired)

Candidate ARCH_TAKEOFF_V3.0.57 line index (= V3.0.58 for STR.CONC.BEAM / STR.CONC.PARAPET). Source Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..). Rules applied UP-CONC-JOINT-001, R-T610-1, R-T624-1, R-T619-1, UP-QTY-STATUS-001; no new rule.

| item | own (drawing) | candidate line | delta own - line m3 | verdict | fix row |
|---|---|---|---|---|---|
| (a) F-C-P04-1 CB12 @ 664 | 0.0325 m2 x 0.75 = 0.024375 | L-076a6d9e6df46aef97d1 1.079463 = 1.054688 + T-229 0.024763 | -0.000388 (vs the term) | ENGINE_RIGHT | FR-T642-1 NO_CHANGE (residual named) |
| (b) F-C-P02-14 strip N of 353 | 0.1 m2; B4 0.50 / B7 0.75 | L-efd3f7806bf10b6a8e98 HELD 0.04 .. 0.12 (route G piece BAND0030.2) | SET 0.05 + HELD 0 .. 0.025 | carried once as HELD; range narrowed | FR-T642-2 |
| (c) GF B11 oblique end | 0.915016 m2 x 0.75 = 0.686262 | L-b274a04546a58e0ecfdd 0.68655 = 0.68311 + T-229 0.00345 | -0.000288 | ENGINE_RIGHT | FR-T642-3 NO_CHANGE (residual named) |
| (d) F-C-P02-13 BAND0049 arc | 0.376991 m2 x 0.75 = 0.282743 | L-5bc1baae70fcc325abea 0.282743 | 0.0 | ENGINE_RIGHT (B7 printed: INSERT 47D / TEXT 482, 0.099489 m outside the arc at 51.0 deg) | FR-T642-4 NO_CHANGE (depth source named) |

## (e) STR.CONC.PARAPET

| line | element | runs | at least m3 | all-RC printed part m3 | + m3 per m b_edge |
|---|---|---|---|---|---|
| L-030538dda6a32c601c4c | 2F_ROOF#PARAPET_RC | 4 | 1.6245 | [2.7075, 2.7075] | 5.415 |
| L-1d419b64e8ca1af30fb4 | ANNEX_ROOF#PARAPET_RC | 7 | 1.799103 | [2.998505, 3.018505] | 6.03701 |
| L-9a2c81164ec6499cc28c | 1F_ROOF#PARAPET_RC | 11 | 2.949453 | [10.478455, 11.53235] | 9.84653 |
| L-b5ffc172a354375ca107 | GF_TERRACE#PARAPET_RC | 3 | 1.677887 | [2.796478, 2.83699] | 5.67398 |

Cause (each line): PARAPET_RC_MATERIAL: which printed detail governs each run (ST p.14 P1 brick on a 0.30 RC upstand with an RC cap 'AS PER ARC.', vs the architect's sections drawn cast concrete) is not keyed: designer item, owner Q-65 C, material HELD; + PARAPET_RC_B_EDGE: roof build-up depth at the edge (D-39) HELD; cap profile unprinted in the structural set

B10 effect: HELD line [0.04, 0.12] -> +0.05 m3 SET (FR-T642-2) + HELD companion 0 .. 0.025; closed with no change: F-C-P04-1, GF B11 -0.003159, F-C-P02-13.
