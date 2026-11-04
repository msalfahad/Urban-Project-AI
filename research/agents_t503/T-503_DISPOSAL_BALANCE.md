# T-503: B1-04 DISPOSAL as one material balance (DISPOSAL_BALANCE_V1, rule R-T503-1), lane S, non-candidate

Candidate of record ARCH_TAKEOFF_V3.0.48 (lines sha 33a81c53, T-350 r4 MERGED 5de697ff). Nothing in the candidate
moves: this is the research method plus its run on the candidate lines, for a later lane I wiring.

## 1. Physical element

Disposal = excavated in-situ soil that leaves the site = every in-situ m3 excavated minus the in-situ m3 of SUITABLE
excavated soil placed back as compacted fill (backfill round the buried structure, the raised fill Z2 under the GF
slab). Imported fill = the compacted demand the re-used soil does not cover. One balance gives both (owner 2026-11-02
17:20 (2), 17:45 (4), 18:00 (3)); payable disposal in situ unless the contract says loose; truckloads logistics only.

## 2. Owner manual method and drawing-derived method, side by side

| | owner manual method | drawing-derived (this run) |
|---|---|---|
| excavation E | sum of zone excavations | 12 B1-02 lines: 3 computed (pits 208.164757, pool 17.776576, F10F 7.2645 .. 8.39175) = 233.205833 .. 234.333083 m3 + 9 HELD (8 V3.0.43 blank zones + ext GB trench HELD PENDING T-497) |
| fill demand D | backfill + placed fill, compacted | 7 B1-03 lines: pits backfill 119.963335 .. 128.643547 m3 (PARTIALLY VERIFIED 6 / 8) + 6 HELD (Z2, pool, ext trench, other trenches, F10F, FF) |
| re-use | excavated soil, if suitable, by dry mass | reused in situ = min(s E, k D), k = rho_target / rho_insitu; s only from geotechnical evidence |
| disposal | E - re-use | E - min(s E, k D) |

## 3. Result on the candidate (in-situ m3)

| end | scenario | disposal in situ | imported fill, compacted |
|---|---|---|---|
| high | no suitable soil (s = 0) | at least 234.333083 (+ 9 held excavation lines, working space, beyond-plot parts) | at least 128.643547 (+ Z2 and 5 other held fill lines) |
| low | all suitable (s = 1) | HELD: in-situ dry density (measured), placement target density, suitable share (geotech), Z2 and 5 fill lines, 9 excavation lines | HELD (same inputs) |

State HELD_RANGE: never a single number, never 0. Closing form once the inputs exist (s = 1):
disposal_low = max(0, E_low - k x (D_high incl. Z2)). Loose m3: HELD (no measured bulking). Payable basis: in situ
(contract silent).

## 4. Reconciliation and what stays HELD

- The ext GB trench term is HELD PENDING T-497 (its V3.0.48 bound is HELD-DEFECTIVE, F-C-T350R4-1); the T-497 restated
  figure enters as a RANGED term when merged; it only moves the high end by its own m3 (Checker scenario 1.07 .. 1.18).
- The drawing's fill note (merged T-347 FILL row: fill "from excavation material") is design intent, not suitability:
  `suitability()` refuses a non-geotechnical status, so s stays 0 .. 1.
- Z2 (raised fill EG -> slab underside) is the term that decides whether the site exports or imports soil: its plan is
  not established (T-214 / T-221); the low end cannot be bounded without it, even with densities.
- E and D ranges are treated as independent (outer envelope, named); the s = 0 end needs no density.

## 5. Who is right

No freelancer disposal line and no released line: no comparison (UNRESOLVED; nothing to propose).

## 6. Tests (tests/t503_disposal_balance, 16)

VILLA-D503 hand fixture: normal all-suitable single number 20.0 m3 in situ, import 0 calculated, 25.0 loose, 2 loads;
partial s = 0.6 -> 52.0 disposal, 29.090909 m3 import, 54.4 t, 35.096774 loose; adverse: no geotech (range 130 high,
low HELD), no geotech with densities (20 .. 130), geotech all unsuitable (130 single, from evidence), held Z2 (low end
HELD), held trench (AT_LEAST), ranged envelope 19 .. 26.4, units (kg/m3), refusals (unit, unsourced density, estimated
bulking, drawing-note suitability, unbound / duplicate / held-valued terms, estimated in-situ density, acceptance
density as procurement), loose contract basis. Alsenan run pinned (summary_t503.json).

## 7. Lessons row (proposed)

2026-11-04 | disposal was HELD BLANK although its no-reuse end is pure geometry | a dry-mass balance with any HELD input
returned every output HELD | disposal and import are one balance over candidate lines with s, k, bulking as separate
facts; the s = 0 end is geometry, the s > 0 end waits for k and the fill demand; a low end bounded only from above is
HELD (earthworks, every villa) | tests/t503_disposal_balance (normal geotech single number; adverse no geotech range,
held Z2) | PROPOSED
