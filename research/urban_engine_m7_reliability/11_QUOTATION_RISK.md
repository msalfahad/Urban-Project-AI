# 11 Quotation risk at 26.5 KWD/m³

The unit rate is the mission's reporting input. It multiplies quantities in this note and in the workbook
(`Dashboard!B2`, every money cell is a formula on it); the engine never reads it. Figures are ST7757 concrete under
V5 (post-discovery); reinforcement is reported in kg and not priced here.

## What the engine holds

| Bucket (release policy) | Items | m³ | at 26.5 KWD/m³ |
|---|---:|---:|---:|
| **Released** (ENGINEER_APPROVED) | **0** | **0** | **0** |
| Machine supported (every dimension drawn / printed; 31 of the 34 independently checked) | 34 | 79.571 | 2 108.6 |
| Provisional (at least one dimension from a convention) | 368 | 234.343 (range 227.932 – 254.263) | 6 210.1 (6 040.2 – 6 738.0) |
| **Measured total (planning)** | 402 | **313.913** | **8 318.7** |
| Unresolved — exposure range, never added | 86 (3 without a range) | 17.495 – 30.864 | 463.6 – 817.9 |

Concrete families measured: footings 66.26, beams 64.82, slabs 60.92, columns 47.57, ground beams 34.48, plain
concrete 22.16, ground slab 17.24, lintels 0.46 m³.

## What the engine does not hold (unpriced on purpose)

- **Families outside the generic scope on ST7757**: stairs, pool, domes, water tank, parapets are DETECTED_NOT_QUANTIFIED
  (drawn, no item); lift and walls NO_EVIDENCE_FOUND; necks and lintels PARTLY_QUANTIFIED. Their concrete is not in
  any figure above.
- **Completeness findings**: 90 findings (34 HIGH, 55 MEDIUM, 1 LOW). Only five carry a drawn-geometry volume
  (column outlines with no column item: 2.36 m³; column items with no outline on their plan: 2.27 m³). The other 85 —
  20 drawn-not-measured groups, 3 stairs, 4 excluded regions, 14 hatches on measured members, unread schedule rows,
  unconsumed labels — have **no volume**: their money exposure is unbounded by this package.
- **Storeys whose plan is missing** carry no range (M7-W21); none on ST7757, but the synthetic evidence shows the size
  of this gap (124 m³ slab over five drawings).

## What the M7 changes did to the money

| Change | m³ | KWD |
|---|---:|---:|
| V5 − V4 measured concrete on ST7757 (ground slab +0.486 from closed junction cells, slabs +0.040 / −0.087, lintels restored) | +0.439 | +11.6 |
| V5 − V4 unresolved exposure high | +0.122 | +3.2 |
| Synthetic held-out (40 villas, development vocabulary): silent under-count the M6 engine would have hidden | 140.3 → 0 | 3 716.8 → 0 |

On ST7757 itself M7 changes little money; its value there is that the same figures now come out whether the drawing
is translated, rotated, re-unitised, has duplicated annotations or an unrelated layer, and that every figure carries a
release state. The synthetic held-out shows what the M6 engine's silent errors were worth on drawings it had not seen.

## Verdict

**Not quotation-ready.** No quantity is released (no engineer has reviewed one); the only real project is
post-discovery; the second-villa blind test is blocked; out-of-scope families and 85 volume-less findings leave the
exposure unbounded; the test gate is INCOMPLETE. The measured total is a **planning** figure: 313.9 m³ ≈ 8 319 KWD,
plus a known unresolved range of 464 – 818 KWD, plus everything listed under "does not hold".
