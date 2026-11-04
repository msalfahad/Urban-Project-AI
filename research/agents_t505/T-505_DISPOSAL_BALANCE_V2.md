# T-505: B1-04 DISPOSAL BALANCE V2, loss terms as their own accounts (DISPOSAL_BALANCE_V2, rule R-T505-1), lane S, non-candidate

From Checker F-C-T503-1 (T-503 MERGED b6133032). V1 (research/agents_t503/disposal_balance_v1.py) is untouched and
called. Research, unwired: nothing in the candidate moves.

## 1. Physical element

Dry mass of soil leaving (disposal) and arriving (import) for one villa. Two losses, each its own account (owner
2026-11-02 18:00 (3)): `loss_reuse` = share of the excavated soil TAKEN for reuse that is never placed (handling,
stockpiling, contamination), in in-situ m3; `loss_import` = share of the PROCURED import never placed, in t.

## 2. Method (owner manual method and drawing-derived method side by side)

| | owner manual method | V2 |
|---|---|---|
| reuse | excavated soil, if suitable, by dry mass | taken = min(s E, k D / (1 - lr)); placed = taken (1 - lr); loss = taken lr |
| disposal | E - reuse | E - taken (surplus never taken; payable in situ) |
| loss | separate account | loss_reuse in situ m3 beside; destination is a contract / site fact, not in payable |
| import | demand not covered | D - placed / k (net); procured t = net t / (1 - li); loss_import t beside |
| check | — | E = disposal + placed + loss; D rho_t = placed rho_i + import rho_t (asserted) |

Gates: s = 0 end = V1 byte for byte (asserted); an s > 0 end is HELD unless lr is sourced (measured / project
specification / documented reference read in full); li gates procurement mass only; a sourced 0 is a figure, an
unsourced loss is never 0; a HELD candidate line enters blank, its bound beside (never summed).

## 3. Source search for a documented loss

Drive "Engineering Sources", 01 Kuwait References: Kuwait MPW General Specifications for Buildings and Engineering Works
(1990), s.02220 (excavation and backfill for buildings) and s.02223 (excavation and fill for pavements and yards) read
in full incl. Part 4 measurement: no handling loss, no procurement loss, no bulking factor; measurement is geometric
(m3 to the drawn dimensions / levels), no loss allowance. Other reference folders: building codes, concrete and finishing
books, no earthworks estimating source. -> loss_reuse and loss_import HELD (level-4 figure not available).
Noted beside (not used, outside this task): s.02220 3.3 backfill lifts <= 250 mm at >= 90 % MDD (ASTM D1557); s.02223
3.4 <= 150 mm. The owner-provisional 150 mm lift stands where the project documents say nothing else.

## 4. Result on ARCH_TAKEOFF_V3.0.50 (T-497 MERGED 5f8814e8)

| end | disposal in situ | import compacted |
|---|---|---|
| s = 0 (no suitable soil) | at least 234.333083 m3 [ESTIMATED], = V1 | at least 128.643547 m3, = V1 |
| s = 1 | HELD: densities, geotech share, 6 fill + 9 excavation HELD lines, loss_reuse | HELD (same) |

The restated trench (1.069269 .. 1.176467 m3, HELD / BOUNDED_EXPOSURE) stays beside: if taken, the s = 0 end would read
235.402352 .. 235.509550 m3. State HELD_RANGE, never a number, never 0.

## 5. Hand fixture VILLA-D505 (E 130.0, D 100.0, k 1.1)

s = 1, lr 5 % measured, li 3 % specified: disposal 14.210526 m3 (single number), loss 5.789474, not placed 20.0
(= V1 20.0: when the supply is not binding the loss only reclassifies); import 0 calculated. s = 0.6: disposal 52.0
(= V1), loss 3.9, import 32.636364 m3 (V1 29.090909; +3.9 / 1.1), 61.03 t net, 62.917526 t procured, 1.887526 t loss.
Adverse: lr unsourced -> reuse end HELD (V1 gave 20.0 there), s = 0 end 130.0 unchanged; li unsourced -> procurement
HELD only; HELD bound in a sum refused; open sum -> no loss account; units (% / fraction), refusals. Regression: sourced
zero losses reproduce V1 on 16 scenario combinations. Defect found and fixed during the run: V1's payable / loose /
truckloads are re-derived from the V2 ends (they would have carried a loss-free figure on a HELD end).

## 6. Who is right

No freelancer disposal line and no released line: UNRESOLVED (no comparison).

## 7. Lessons row (proposed)

2026-11-04 | a reuse-end disposal could be valued with no loss term (F-C-T503-1) | V1 had no loss account | losses are
separate facts: reuse handling loss gates the s > 0 ends, import loss gates procurement only, the s = 0 end stays pure
geometry; derived outputs (payable, loose, trucks) are rebuilt from the final ends (earthworks, every villa) |
tests/t505_disposal_balance_v2 (normal all sourced 14.210526; adverse lr unsourced -> HELD, s = 0 unchanged) | PROPOSED
