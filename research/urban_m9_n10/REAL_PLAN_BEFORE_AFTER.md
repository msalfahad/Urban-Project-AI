# Real-plan before / after: ARCH_TAKEOFF_V2.8 → V2.9 (aggregates only)

The private drawing set is the same as in Phase 2B-9: the reference plan, the villa and its mirror. Each was run in two modes:

- **Mode U**: no facts;
- **Mode A**: roles declared and the project facts file.

Both runs come from the full private snapshot at the N10 code (`n10_a`). Only item totals and line counts are reported: no room, no layer, no identity. V1 – V2.8 are byte-identical to the Phase 2B-9 final snapshot (`REGRESSION_AND_FROZEN_EVIDENCE.md`).

## 1. Reference plan, Mode A (roles and facts)

Lines: 487 → 517 (+30).

| Item | V2.8 | V2.9 | Change | Why |
|---|---|---|---|---|
| ARCH.WINDOW | 26 | 27 | +1 | the curved first-floor window is an opening (UP-OPEN-CURVED-001) |
| ARCH.WINDOW_REVEAL | 26 lines (blocked) | 27 lines (blocked) | +1 line | its reveal |
| FIN.PLASTER (certain) | 474.6357 m² | 532.5835 m² | **+57.9478 m²** | the room behind the curved window is measured with the window's width on its face; the plaster range narrows from [482.60, 534.79] to [429.59, 471.91] |
| FIN.PAINT (certain) | 230.3342 m² | 288.2820 m² | **+57.9478 m²** | the same room; the range narrows from [378.64, 419.49] to [325.62, 356.61] |
| FIN.SKIRTING | 288.9481 m certain | 288.9481 m certain | 0 certain | one more bounded line; range high +3.29 m (the window's sill is not established) |
| ARCH.FACADE_RUN | — | 191.8556 m (3 floors) | new, PROVISIONAL | exterior outline per floor; each floor also has a thin second outline (RFI) |
| ARCH.FACADE | — | held (3 floors + plinth) | new, RFI | no next-floor F.F.L. on a bound section band |
| FIN.EXT.FINISH | — | held (3) | new, RFI | no exterior finish stated |
| ARCH.WALL_PANEL / ARCH.WALL_VOLUME | — | held (7 + 7) | new, RFI | no T.O.S. / U/S SLAB on a bound section band |
| everything else | — | — | 0 | unchanged |

No floor area changed: the curved window's room closes on its face, outside the curve.

## 2. Reference plan, Mode U (no facts)

Lines: 476 → 506 (+30).

The curved window is read here too: ARCH.WINDOW 26 → 27. Skirting gains one bounded line.

The facade run is the same: 191.8556 m, PROVISIONAL. Facade area, finish and masonry are held.

Plaster and paint are unchanged: without facts no wall height is known.

## 3. Villa and mirror (both modes)

| Drawing | Lines | Change |
|---|---|---|
| villa (U / A) | 105 → 116 / 108 → 119 | + facade run 78.40 m (2 floors, SOURCE_DERIVED); facade area, finish, masonry held |
| villa mirror (U / A) | 105 → 116 / 108 → 119 | identical to the villa: 78.40 m (the mirror changes nothing) |

No other quantity changed on either drawing.

## 4. Conservation and invariance on the real plans

- On every reference-plan floor, the facade outline's plate equals the engine's existing gross floor plate (difference 0.000000 m²). The outline ring equals the recorded perimeter.
- The villa and its mirror give the same facade run.
- V2.9 is deterministic: 362 output files, 0 differ between two runs.

## 5. What it means

- **Measurable gains:**
  - one curved window and its room are now measured on the reference plan;
  - plaster and paint each gain 57.9478 m² of certain quantity (previously a range);
  - the facade run exists for every floor of every plan.
- **Not gained:** masonry and facade *areas* on the real plans. The drawings do not carry the section levels the rules need, and nothing was defaulted.
