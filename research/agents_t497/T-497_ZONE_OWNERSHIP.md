# T-497 — excavation zone ownership: the external ground-beam trench (integration package, Gate B)

Source finding: Checker F-C-T350R4-1 (Gate B on T-350 r4, Verifier 2026-11-03 23:24 UTC; merged 5de697ff with the trench
line HELD-DEFECTIVE).

## Physical element

The external main ground-beam trench (B1-02, zone `Z1-TRENCH-EXT-GB-MAIN`) is the ground removed 0.10 m below the
existing ground for the blinding of the 17 main exterior ground-beam runs, **only where no other excavation zone already
removes it**. A footing pit dug to 1.67 m under the beam has already taken that 0.10 m; so has the F10F footing zone; the
pits' own beyond-plot strips are held with the pits.

## Rule R-T497-1 (every villa; research/agents_t497/zone_ownership_v1.py, EXCAVATION_ZONE_OWNERSHIP_V1)

One owner zone per excavated m3. Zones are listed in the dig sequence of the drawings (deeper / earlier first: pool
envelope, footing pits, other footing zones such as F10F, the lift raft FF, then shallow strips). Every zone subtracts the
plans of ALL earlier zones, in the plot AND beyond the plot line, by geometry — never from a list of known interfaces.
Asserted: owned plans pairwise disjoint and adding up to the union (every m2 once); own + given-up = plan per zone. A zone
wholly inside earlier zones owns a calculated zero (dug by another zone), never a missing value.

## Owner manual method vs drawing-derived method

| | owner manual method | drawing-derived (this task) |
|---|---|---|
| definition | plan of each pit / trench x depth from the existing ground to the formation; overlapping digs taken once, by the deeper dig | T-484 MAIN_EXT strip (27.919513 m2, columns removed) less pool envelope 0, pits 14.479847 (13.591177 in plot + 0.888670 beyond), F10F drawn outline 1.675 (1.340006 in plot + 0.334994 beyond), FF 0 |
| trench own plan | — | 10.692685 m2 in plot + 1.071981 m2 beyond |
| trench m3 (x 0.10) | — | 1.069269 .. 1.176467 (in plot .. with beyond-plot) |

## Reconciliation in units (V3.0.48 -> V3.0.50)

| | low (in plot) | high (with beyond) |
|---|---|---|
| V3.0.48 (pits-only subtraction) | 1.203269 | 1.432834 |
| less F10F overlap, in plot 1.340006 m2 x 0.10 | -0.134001 | -0.134001 |
| less F10F overlap, beyond plot 0.334994 m2 x 0.10 | — | -0.033499 |
| less pits' beyond-plot strips 0.888670 m2 x 0.10 | — | -0.088867 |
| V3.0.50 | **1.069269** | **1.176467** |

Residual 0 against the Checker's own corrected figures (drawn-outline scenario). The Checker's own strip in plot is 11.873941
m2 vs this geometry 10.692686: the 1.181 m2 residual (two stretches the r2 / T-253 run classes put in MAIN_INT_D, above EG,
no dig) was ruled "not a defect" by the Checker (T-253 ledger L x 0.50 = 27.9956 vs strip 27.9195, -0.27 %).

## Scenarios (owner 2026-11-02: one scenario, one consistent set)

The F10F line is a range over the S02 readings (7.2645 .. 8.39175 m3, unchanged). The trench line is stated in the
drawn-outline reading (the F10F line's high end). Under the other 10 readings (F10 alone, F10 + F unions) the trench owns
up to 0.037 m3 more in plot (0.047499 with beyond-plot): named beside, never added. STR.EARTH.EXCAVATION held bound
(trench + F10F): 8.467769 .. 9.824584 -> **8.333769 .. 9.568217** m3 (-0.134 / -0.256367); every consistent scenario total
(8.351769 .. 9.568217) lies inside it; the high end is exact.

## Statuses

Trench: HELD (BOUNDED_EXPOSURE), Checker-corrected figure reproduced (DRAWING-DERIVED on the S01 ESTIMATED depth basis).
Pits / pool / F10F / backfill / disposal lines: byte-identical. Beyond-plot ground (S06 / D-14) and working space HELD.

## Verdict proposal

No freelancer earthworks line: UNRESOLVED (no comparison); V3.0.48 trench vs V3.0.50: ENGINE V3.0.50 RIGHT by the hand
re-measure above (the 0.256367 m3 is ground already in the F10F line or held with the pits).

## Lessons register row (ENGINEERING_REASONING_STANDARD s.7, 2026-11-04) — test column

`tests/t497_zone_ownership/test_zone_ownership.py`: normal (disjoint zones each own their whole plan) and adverse (villa
E497: trench crossing a footing pit, a non-pit footing zone and a beyond-plot pit strip: 1.80 m2 owned, every m3 once;
the list-based way double counts 0.045 m3), plus mirror / rotation / mm units / wholly-dug zone / refusals.
