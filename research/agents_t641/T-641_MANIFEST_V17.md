# T-641 WIRING MANIFEST V17 + overlay dry run (R-T641-1; lane I, non-candidate)

Base: V16 (T-631) rebuilt in memory on the V3.0.58 copy (overlay V2 .. V16, 5,143 lines) and compared row by row with
the committed V16 output and its totals. V17 adds 106 ops in 5 new packages + 27 steps chained in RETURN_PAINT_FACES.
Nothing is wired to the candidate; V2.9 + route G and V3.0.58 are untouched. Output: `out/WIRING_MANIFEST_V17.json`
(rebuilt by `tests/t641_manifest_v17` with `URBAN_T641_WRITE=1`; the test asserts committed == rebuild).

## Fix rows (each cites its merged verdict)

| package | rows | before -> after | evidence |
|---|---|---|---|
| FLOOR_BED_FOLLOWS_FINISH (F-T631-1) | GF bed m2 L-20a8e714 | 109.478417 -> 109.465145 (FR-T625-1) -> 109.071302 low end (FR-T625-2) + HELD 0 .. 0.393843 | PARTIALLY VERIFIED / HELD |
| | GF bed mortar m3 L-77a18286 | HELD 3.284353 .. 4.379137 -> 3.283954 .. 4.378606 -> 3.272139 .. 4.362852 + HELD 0 .. 0.015754 | HELD |
| | 1F bed m2 / m3 L-ebce765b / L-eaa8f305 | lines unchanged; companions HELD 0 .. 0.376 m2 / 0 .. 0.01504 m3 (ruling) | HELD |
| FOOTING_BAND_RANGE (F-T628-1) | L-6290a9f3 band | HELD 7.2204 .. 7.2204 (UNSUPPORTED) -> HELD 5.6392 .. 11.0328 m3 | HELD |
| FORMWORK_HOLD_RELEASE (T-638) | 54 + 4 companions | 4 GF shafts 27.002 m2 + joint faces HELD 1.589365; 50 split faces 6.125058 m2 | VERIFIED / PARTIALLY VERIFIED (CALCULATED) |
| GF_COLUMN_MAIN_BARS (T-639) | FR-T639-1 .. -6 | 6 HELD blank -> 412.444445 kg (6 lines at 6 dp; census 412.444444) | VERIFIED |
| FINISH_HOLD_BOUNDS + 27 chained (T-640) | 33 A_BOUND | HELD blank -> HELD 87.234 .. 138.53962 m2 (bounds only) | HELD |

Mortar thickness 0.03 .. 0.04 m is proved from the candidate lines themselves (109.478417 x 0.03 / 0.04 = 3.284353 /
4.379137; 33.411036 -> 1.002331 / 1.336441: Q-45 floors), never typed.

## Re-adds by hand

- FIN.FLOOR.BED.DRY m2: 304.488472 - 0.013272 - 0.393843 = 304.081357 released + HELD 0 .. 0.769843 (= porcelain V16).
- FIN.FLOOR.BED.DRY m3 HELD: low 9.134654 - 0.012214 = 9.122440; high 12.179539 - 0.016285 + 0.015754 + 0.015040 = 12.194048.
- STR.CONC.BOUNDARY_WALL m3 HELD 7.2204 -> 5.6392 .. 11.0328; footing-line bound 77.1204 .. 77.8432 -> 75.5392 .. 81.6556.
- STR.FORMWORK m2: 1,027.977403 + 27.002 + 6.125058 = 1,061.104461 (+3.22 %); held blank 370 -> 316. No freelancer row.
- STR.REBAR kg: 9,375.30576 + 412.444445 = 9,787.750205 (+4.40 %); held blank 801 -> 795.
- B4 / B5 finish keys HELD bounds +87.234 .. +138.53962 m2 (FIN.PAINT, FIN.PLASTER, FIN.CEILING, FIN.CEILING.BULKHEAD).
- Overlay 5,151 lines; 0 STALE; 0 two-package lines; 0 unexplained conflicts (2 EXPLAINED: 1F bed companions); stair
  census 89 edges, 0 doubles / 0 orphans; every other line byte-equal to V16.

## Listed, not wired (R-T641-1 (f))

- T-626: roof residual TOLERANCE 0.001332 + UNRESOLVED 0.521668 m2 on his lump row: no engine line.
- T-627: windows ENGINE_RIGHT 3.975 m2; doors 0.580 m2 RULE_DIFFERENCE -> ENGINE_RIGHT (0.960 -> 0.380; -1.720 ->
  -1.140): engine = own 6.380 m2, a statement V12 class move (T-635).
- T-634: GF-15 W03 -0.015161 m2 opening ledger inside the line's TOLERANCE (-0.005868); returns 23.069556 vs 23.07;
  paint-return bracket 19.17 .. 23.069556 (5 wet-wet doors) listed: the T-640 per-line low 0 stands (Checker OP-021).
- T-640 FR-T640-30 / -31 RETIRE_CARRIED (1F living ceiling parents, carrier L-43bf1f86): not ruled, stay HELD blank.
- T-639 F-T639-1 (754.723 kg released bars on HELD concrete): T-643's row. T-638 strip D: no owning line.
- Refused by name: T-637, T-644 (READY), T-642, T-643 (TODO).

## Uncertain

- The paint-return low ends: T-634's bracket (low 19.17) and T-640's per-line low 0 differ on whether the non-wet
  returns are painted whole; V17 carries the verdict-backed per-line bounds; a raised low needs its own verdict.
- Rebar per-line rounding: 6 lines at 6 dp re-add to 412.444445 vs the census 412.444444 (+0.000001 kg).
