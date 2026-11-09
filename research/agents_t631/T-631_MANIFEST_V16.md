# T-631 WIRING MANIFEST V16 + overlay dry run (R-T631-1; lane I, non-candidate)

Base: V15 (T-629, MERGED b0eb7f60) rebuilt in memory on the V3.0.58 copy (overlay V2 .. V15, 5,141 lines) and compared
row by row with the committed V15 output. V16 adds 9 ops in 3 new packages + 2 steps chained in the T-610 package.
Nothing is wired to the candidate; V2.9 + route G and V3.0.58 are untouched. Output: `out/WIRING_MANIFEST_V16.json`
(rebuilt by `tests/t631_manifest_v16` with `URBAN_T631_WRITE=1`; the test asserts committed == rebuild).

## Fix rows (each cites its merged verdict)

| row | line | before -> after | evidence | verdict |
|---|---|---|---|---|
| FR-T624-1 | GF B26 BAND0047.1 L-c6fa4992 | 4.0846 -> 4.089845 m3 (wedge 0.006171 m2 x 0.85) | PARTIALLY VERIFIED (piece AGREE; own 0.005261, -0.000016 immaterial) | T-624 11:58Z |
| FR-T624-2 | 1F B19 BAND0030.1 L-45e0d887 | 1.62356 -> 1.624624 m3 (0.001418 x 0.75) | PARTIALLY VERIFIED (piece AGREE) | T-624 |
| FR-T624-3 | GF CB8 BAND0039 L-7c1a1da8 (chained in T-610 pkg) | 0.714169 -> 0.717574 m3 (0.00454 x 0.75), supersedes FR-T614-H1 | PARTIALLY VERIFIED (piece AGREE) | T-624 |
| FR-T624-4 | FR-T610-1 companion (chained in T-610 pkg) | HELD 0 .. 0.001295 -> EXCLUDED (tip billed once inside B27 rect) | VERIFIED (item (c) AGREE) | T-624 |
| FR-T622-2 | GF-14 wall tile L-fa408571 | 26.6544 -> 26.567691 m2 (8.243203 x 3.65 - 2 x 0.80 x 2.20) | DRAWING-CONFIRMED (worker; Checker did not re-measure GF-14) | T-622 10:00Z |
| FR-T625-1 | GF porcelain L-7625f35c | 109.478417 -> 109.465145 m2 (footprint 6.124412 -> 6.137684) | VERIFIED (row 0 own) | T-625 12:59Z |
| FR-T625-2 | GF porcelain L-7625f35c + companion | low end 109.071302 + HELD 0 .. 0.393843 (strings) | HELD (UNRESOLVED range) | T-625 |
| FR-T625-3 | 1F living porcelain L-b06400d4 | stays 33.411036 + HELD 0 .. 0.376 (slab-edge margin) | HELD (UNRESOLVED range) | T-625 |

## Re-adds by hand

- B10 STR.CONC.BEAM m3: 66.392081 + 0.005245 + 0.001064 + 0.003405 = 66.401795 (a point; V15 read 66.392081 .. 66.393376).
  vs freelancer 66.093875: +0.307920 m3 (+0.466 %), ENGINE_RIGHT on the Checker's own calc for the three omissions.
- FIN.WALL.TILE m2: 340.3366 - 0.086709 = 340.249891 (HELD 6 blank unchanged).
- FIN.FLOOR.PORCELAIN m2: 295.390972 - 0.013272 - 0.393843 = 294.983857 released + HELD 0 .. 0.769843 (2 lines).
- Overlay 5,143 lines; 0 STALE; 0 two-package lines; 0 unexplained conflicts (1 EXPLAINED: 1F margin companion beside
  its line); only the three keys above move; stair census 89 edges, 0 doubles / 0 orphans.

## Listed, not wired

- 0 rows: T-626 (classes stand), T-629 (base), T-630 (dry run), T-632 (B20 ENGINE_RIGHT 0.120 m3; hatches 390 / 391
  HELD length only). Refused by name: T-627 (READY), T-628 (TODO).
- T-625 worker proposals not re-measured by the Checker: curtail 0.157787 m2, RS-A arrival band 0.0575 m2 (F-T631-2).
- Downstream (F-T631-1): the floor bed lines on the same hosts follow the floor area by rule and are NOT moved here:
  GF bed m2 L-20a8e714 109.478417, GF bed mortar m3 L-77a18286 HELD 3.284353 .. 4.379137, 1F bed m2 L-ebce765b
  33.411036, 1F bed mortar m3 L-eaa8f305 HELD. Gate B needs the same delta on them or their own verdict.

## Uncertain

- FR-T625-2 puts the GF porcelain at its low end (R-T619-1 (c)), lowering released porcelain by 0.393843 m2 on an
  UNRESOLVED string reading; the companion carries it. If the Lead prefers the line at the engine value for a
  designer-item range, that is a convention change (new rule version), not a V16 edit.
