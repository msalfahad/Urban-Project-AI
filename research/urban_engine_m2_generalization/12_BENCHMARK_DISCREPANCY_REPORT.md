# Benchmark discrepancy report (no tuning)

## Order of events (the firewall)

1. Route G was committed (8c1e28e), then compared.
2. Every engine change made after the comparison is generic and named:
   - the frozen-CLI restore (180d9fc);
   - columns never binding to footing outlines (d23fe92), found on the synthetic demo; it left Alsenan's outputs byte-identical;
   - the intake cache (2c5ff19).
3. No convention, tolerance or rule was changed toward an external number. The Alsenan comparison CSVs were rebuilt after every later commit and are unchanged.
4. External estimates are read only by `build_m2_reports.benchmark_positions()`. It writes **positions only** (BELOW / INSIDE / ABOVE the generic planning range): no external value and no difference. The builder refuses to write any output that contains a firewalled number.

## 1. Against the frozen replay (our own accurate lane)

See `04_ALSENAN_GENERIC_VS_FROZEN.md`. The discrepancy classes are assigned from evidence, never from the size of the difference.

| class | families | meaning |
|---|---|---|
| SAME_OBJECTS_CLOSE_RESULT | beams | within 5 % on the same members |
| CONVENTION_DIFFERENCE | slabs, ground beams | same members, different section or thickness reading |
| DETECTION_GAP | footings, columns (and their steel) | members the generic route sees but cannot quantify (no outline, no schedule type) |
| SCOPE_DIFFERENCE | ground slab | different face population (06) |
| BAR_MODEL_DIFFERENCE | beam, column, slab steel | generic bar models against the stages' own BBS |
| GENERIC_MISSING_DATA | ground-beam steel | bars only in the PDF detail |
| NOT_IN_GENERIC_SCOPE | stairs, domes, lift, pool, tank, lintels, blinding, cantilevers, parapets, boundary wall | not quantified; listed in BOQ section C |

## 2. Against external estimates (positions only): `09_BENCHMARK_POSITIONS.csv`

The external estimates are the freelancer QS, christiannp-autocad and U-C4N (old Urban V3b is shown for the record). They use the M1 comparison groups.

| group | where the externals sit vs the generic range | vs M1's range | reading |
|---|---|---|---|
| footings | ABOVE (all three) | INSIDE / INSIDE / ABOVE | The generic route misses four footings (DETECTION_GAP). M1 has them. |
| ground beams + straps | ABOVE (all) | ABOVE (all) | Both of our routes sit below. Exterior depths and straps are a known open convention (S9A). |
| ground slab | ABOVE (all) | ABOVE (all) | Even with its extra faces, the generic route is below all three: consistent with PF-M1-02's "more cells". Not resolved here. |
| columns GF / 1F / 2F | mixed, mostly BELOW | the same as M1 | Externals count less column concrete than our routes on 1F and 2F. Same pattern as M1. |
| frame GF / 1F | INSIDE or one side, as M1 | — | Same positions as M1. |
| frame 2F | BELOW (two) | INSIDE (two) | The generic 2F range is narrower than M1's and sits above two external values that M1's wider range contained. Not explained yet (RFI M2-RFI-05). |
| beams, all floors | INSIDE / BELOW / BELOW | the same | Same positions as M1. |
| slabs, all floors | BELOW / ABOVE / ABOVE | ABOVE (all) | The generic slab is 5 % above M1, enough to put one external below it. |
| total RC | ABOVE (all) | INSIDE (all) | Expected: the generic total omits the out-of-scope families. The totals combine different scopes and are not an accuracy figure. |

**No external estimate is ground truth.** Where an external sits outside our range, the reason is recorded per group in M1's post-freeze report. M2 adds only where the generic route moved.

## 3. Against independent ground truth

The only independent ground truth available is the synthetic design truth (`11_GENERIC_TEST_RESULTS.md`). On it, the error is within 1e-6 for every family. That truth shares the generator's drafting assumptions: see that document's last section.
