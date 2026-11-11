# T-686 plaster / paint round 3 (lane A, research, unwired)

Worker 2, 2026-11-10. Candidate ARCH_TAKEOFF_V3.0.66 (T-677 line index). Nothing wired or released; V2.9 + route G
unchanged; no engine, rule, knowledge or registry file touched. Rules R-T686-1 .. -4 in `t686_rules.py`; builder
`t686_alsenan.py` (`--check`); outputs `out/T686_ROUND3.{json,md}`; tests `tests/t686_plaster_paint_round3` (V686 by hand,
normal + adverse, plus the development villa pinned).

## 0. Counts restated on V3.0.66 (own filter: item code FIN.PLASTER / FIN.PAINT, class HELD)

V3.0.66 = V3.0.64 for these codes: FIN.PLASTER 24 HELD = 932.72581 .. 1006.77641 (14) + 10 blank; FIN.PAINT 10 HELD =
487.121 .. 542.8606 (7) + 3 blank. With the merged, unwired T-680 (+ T-676 OP-009): plaster 985.32981 .. 1054.74641 (15)
+ 9 blank, paint 537.7750 .. 589.0006 (8) + 2 blank. The builder asserts that the 11 blank lines are exactly this
task's targets: 6 annex Q-54 B (4 wet-room plaster + 2 dry-room paint), 2 stair-core wet rooms, 3 reveals.

## 1. Physical elements and heights

- Annex (FFL +0.30, roof mark +4.30): the roof slab top s is not printed (Q-54 B: +4.30 may be finished). It is
  bounded by the drawings: s >= 3.544 (R-T678-2, Checker MERGED f8515d4b: W08 drawn head +2.80 - 0.006 under CB6 0.75
  on one plane) and s <= 4.30 (a slab top never lies above its finished roof). Slab 0.16 (Q-14; the GFRS annex part
  prints no thickness). Plaster soffit S = s - 0.16 - 0.30 = 3.084 .. 3.84; paint / tile top (owner G1, Q-43 A / Q-48
  A: 0.60 beam + 0.15 ceiling below the structural top) H = s - 1.05 = 2.494 .. 3.25. The owner manual 3.15 lies
  inside; Q-54 B is respected: no point is taken, every line stays HELD with low .. high.
- Wet rooms: FIN.PLASTER = the tile-backing levelling render to the tile top (= finished ceiling, Q-48 A), the same
  convention as the released laundry / pantry backing lines (T-329 / T-399); spatter dash stays T-364 (HELD).
- Stair-core wet rooms GF-10 / GF-11 (R-T686-3): floor +0.30 or +1.00 not drawn (C-SH-2). Both are carried: the tile
  top lies between the highest established head (D-GF-10 2.20, ASSUMED - OWNER-APPROVED Q-55 C: a ceiling never lies
  below a door head) and the GF G1 ceiling +4.65 absolute - the lower floor option = 4.35. This replaces T-680's 'no
  two-sided bound' with a wide but drawn bound; the named datums stay open.
- Openings (R-T686-2): exact where sill / head are known; W11 / W12 (hole 2.20 drawn, sill held) 1.61 .. 2.20 m inside
  the band (the hole lies below S, S - H = 0.59); an arch / passage with no printed height 0 .. w x H.

## 2. Lines (m2; faces: T-312 / T-250 ledger for the wet rooms, T-128 r3 walked faces for the dry rooms)

| line | room | before | after | terms |
|---|---|---|---|---|
| L-2211463b FIN.PLASTER | GF-02 wash | blank | 13.7028 .. 21.64 | 7.200 x H - D-GF-02 1.76 - A-GF-01 0 .. 1.0 x H |
| L-f43782d5 FIN.PLASTER | GF-03 W.C. | blank | 16.945 .. 22.615 | 7.500 x H - 1.76 |
| L-f179fc08 FIN.PLASTER | GF-05 driver W.C. | blank | 12.2064 .. 16.44 | 5.600 x H - D-GF-04 1.76 |
| L-595181aa FIN.PLASTER | GF-06 kitchen | blank | 31.720506 .. 42.6735 | 14.500 x H - W08 1.501 x (H - 1.0) - D-GF-05 2.20 |
| L-3f7fb1b3 FIN.PLASTER | GF-10 stair-core | blank | 11.40 .. 25.21 | 6.200 x 2.20 .. 4.35 - 1.76 - W05 0 .. 0.48 |
| L-a636dabc FIN.PLASTER | GF-11 stair-core | blank | 7.04 .. 19.555 | 4.900 x 2.20 .. 4.35 - 1.76 - passage 0 .. 0.9 x H |
| L-cdf7f5cd FIN.PAINT | GF-01 dewaneya | blank | 36.911738 .. 56.9257 | 20.127 x H - W11 / W12 - D-GF-01 2.20 - arch |
| L-d7d6d2f7 FIN.PAINT | GF-04 driver room | blank | 26.9586 .. 36.405 | 12.500 x H - W04 0.6 x (min(2.5, H) - 1.7) - 1.98 - 1.76 |

Closure checks: GF-03 7.500 = 2 x (1.50 + 2.25), area 3.375 = 1.50 x 2.25; GF-05 5.600 = 2 x (1.50 + 1.30), area 1.95;
GF-06 14.500 Checker re-measured in T-351. Levelling render materials (Q-79 1:4, 0.015 m MINIMUM): AT_LEAST per line in
the JSON (R-T676-3); water HELD.

Code totals: FIN.PLASTER 1078.344516 .. 1202.87991 (21) + 3 blank (+93.0147 / +148.1335); FIN.PAINT 601.645338 ..
682.3313 (10) + 0 blank (+63.8703 / +93.3307).

Still blank, datum named: A-GF-01 / A-1F-01 reveals (arch spring and rise, D-45; information only <= 1.302 / 1.347 m2
from crown <= soffit), D-GF-15 gate reveal (width / wall, D-53, T-313).

## 3. F-T680-1 (W25: section A-A raster +5.6 .. +7.36 vs SW elevation vector +5.50 .. +7.00)

R-T686-4: the vector governs. It is measured geometry with the view's own level ticks (issue check 0.006 / 0.013), its
1.501 height equals the window's own outline and the stacked W27 of the same type on both sources; the raster's 1.76 m
contradicts that outline and a raster is never scaled. Residual named, not applied: 1.00 x 0.26 = 0.26 m2 per finish on
the 1F shaft lines (D-45 class, designer).

## 4. Findings, freelancer, verdicts

- F-T686-1 (Lead): wet-room FIN.PLASTER lines stop at the tile top; the owner's 'plaster to the slab underside above
  false ceilings' leaves a band S - H = 0.59 m in the annex wet rooms (34.8 m x 0.59 = 20.532 m2 gross) that no line
  carries (the released laundry / pantry backing lines have the same gap). Not added here; it needs its own row.
- Freelancer: annex paint gross at his flat 3.60: GF-01 72.0 vs engine gross 50.197 .. 65.413 (-30.28 .. -9.15 %),
  GF-04 45.0 vs 31.175 .. 40.625 (-30.72 .. -9.72 %): RULE_DIFFERENCE (his height vs the owner G1 to the finished ceiling);
  lengths ENGINE_RIGHT (T-128 r3). Wet rooms: his rows are not itemised per room: UNRESOLVED.
- Lessons-register row (proposed): 2026-11-10 | 8 finish lines stayed blank because the annex datum was HOLD, though a
  verified concrete record already bounded the slab top | an owner HOLD on a point value was read as 'no number at all' |
  a held datum is first bounded from verified records of other trades; the bound is carried, never a point | R-T686-1 /
  -3 (every villa) | tests/t686 | PROPOSED.

## 5. For the Checker (re-measure two lines)

1. GF-06 kitchen: 14.500 x 2.494 - 1.501 x 1.494 - 2.20 = 31.720506; 14.500 x 3.25 - 1.501 x 1.50 - 2.20 = 42.6735.
2. GF-04 paint: 12.5 x 2.494 - 0.6 x 0.794 - 0.9 x 2.2 - 0.8 x 2.2 = 26.9586; 12.5 x 3.25 - 0.48 - 1.98 - 1.76 = 36.405.
