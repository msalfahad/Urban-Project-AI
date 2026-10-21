# Held-out evaluation: M2 engine vs M3 engine on unseen synthetic villas

The numbers come from `13_HELDOUT_EVALUATION.json`, the per-drawing records written by `evaluate_heldout.py score`.

**Drawings**
- 40 new layouts, seeds 501–540. No M1, M2 or M3 development or evaluation used these seeds before.
- Each layout is drawn three ways:
  - **clean:** the generator's design as drawn;
  - **defects:** the M2 drafting-noise set (overshoots, gaps, split lines, duplicate entities, open polylines);
  - **m3:** the M3 real-bug set, taken from what the ST7757 drawing actually did. In the defects column below, "stubs" are 10 mm intervening stubs: a 0.41 m line ending 10 mm inside a beam face at a line-end column. "Label-only footings" are footings drawn as a type label with no outline. The m3 set has 157 stubs and 40 label-only footings.

**Truth**
- Truth comes from the generator's design (`tools/synthetic_villa.py`), never from a DXF.
- The M3 defects change the drawing only; the truth is unchanged.

**Engines**
- **M2:** commit c5123a7, checked out in a separate worktree.
- **M3:** this branch.
- Each engine runs in its own process on the same files. Nothing was tuned to these drawings: the M3 rules were written against ST7757 failures and frozen before the set was generated.

| Set | Engine | End to end | Beam recall / precision | Beam concrete MAE (max) | Beam steel MAE | Footing concrete MAE (max) | Footing steel MAE | Panels recall | Unresolved items |
|---|---|---|---|---|---|---|---|---|---|
| clean | M2 | 40 / 40 | 0.9975 / 1.0 | 0.40 % (11.6 %) | 0.28 % | 0 | 0 | 1.0 | 30 |
| clean | M3 | 40 / 40 | 0.9975 / 1.0 | 0.40 % (11.6 %) | 0.28 % | 0 | 0 | 1.0 | 70 |
| defects | M2 | 40 / 40 | 0.9975 / 1.0 | 0.40 % (11.6 %) | 0.28 % | 0 | 0 | 1.0 | 30 |
| defects | M3 | 40 / 40 | 0.9975 / 1.0 | 0.40 % (11.6 %) | 0.28 % | 0 | 0 | 1.0 | 70 |
| m3 | M2 | 40 / 40 | **0.896** / 1.0 | **11.8 % (31.0 %)** | **11.5 %** | **8.0 % (16.5 %)** | **8.0 %** | 1.0 | 75 |
| m3 | M3 | 40 / 40 | **0.9975** / 1.0 | **0.43 % (11.7 %)** | **0.30 %** | **0** | **0** | 1.0 | 70 |

## Reading the table

- **No regression on drawings M2 already handled.** The clean and drafting-noise rows match to the last digit.
- **The extra 40 unresolved items in M3 are one per drawing**: `PLAIN_CONCRETE / BLINDING_THICKNESS_NOT_PRINTED`. The synthetic profiles print no blinding thickness. M3 therefore reports the blinding as UNRESOLVED with an exposure and never adds it to a total. M2 had no blinding family.
- **What the M3 defects did to M2:**
  - A 10 mm stub split the beam faces, so M2 dropped 166 beams (recall 0.896). Beam concrete was then under by 11.8 % on average and up to 31 % on one drawing.
  - A label-only footing had no outline, so M2 took no quantity for it: −8.0 % footing concrete and steel.
- **What M3 recovers:**
  - The stubs through `intervening_parts`.
  - The label-only footings through the schedule size (`FOOTING_LABEL_ONLY`, outline not confirmed).
  - Recovery is to the clean-drawing level (0.43 % vs 0.40 %). The small rise comes from the recovered pieces, which split a span at the stub's end.
- **The remaining 0.4 % beam error** is M2's documented residual. One untagged span per few drawings, and a type missing from the schedule, are unresolved by design. Precision stays 1.0 in every row.

## What this does not show

- **Synthetic drawings follow one drafting convention:** the generator's. A real set can fail in ways the generator does not draw.
- **ST7757 is not an independent test.** The M3 rules were written from its failures. On ST7757 the only comparison points are the M2 run and the frozen M1 replay (`01_FINAL_REPORT.md` §7). Accuracy against independent truth on a real villa is still unknown.

## Reproduce

```bash
python3 -I research/urban_engine_m3_recovery/evaluate_heldout.py generate --drawings H/clean   --seeds 501-540 --mode clean
python3 -I research/urban_engine_m3_recovery/evaluate_heldout.py generate --drawings H/defects --seeds 501-540 --mode defects
python3 -I research/urban_engine_m3_recovery/evaluate_heldout.py generate --drawings H/m3      --seeds 501-540 --mode m3
git worktree add M2WT c5123a7          # the M2 engine
for s in clean defects m3; do
  python3 -I research/urban_engine_m3_recovery/evaluate_heldout.py score --engine-root M2WT --drawings H/$s --seeds 501-540 --out RES/${s}_m2.json
  python3 -I research/urban_engine_m3_recovery/evaluate_heldout.py score --engine-root .    --drawings H/$s --seeds 501-540 --out RES/${s}_m3.json
done
```
