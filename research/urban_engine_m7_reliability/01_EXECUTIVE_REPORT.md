# 01 Executive report — M7 engine reliability

## A What the engine learned

1. **A quantity must not depend on how the drawing is drawn.** Translating, rotating, mirroring, exploding polylines,
   duplicating annotations, adding an unrelated layer or changing the unit changed quantities — 13 distinct causes,
   none caught by earlier tests (`04_GEOMETRY_AUDIT.md`). The engine now computes in a drawing-local frame and treats
   flush faces as touches, not as overlaps decided by floating noise.
2. **A class limit is read at the drawing's precision.** A 5.000 m span against a 5.0 m limit, a 1.000 m opening
   against a 100 cm lintel band: compared at full float precision they fell either side by 1e-10.
3. **A rectangle at a column's size is not a column without layer evidence**, and a rectangle set aside by that rule
   is still evidence to report — tightening a rule must never drop a signal silently (found the hard way, P2).
4. **A void label is not proof of a void** when the face it sits in holds beams, and bands that end at an undrawn
   support still close the cells (M6 W7 was half evaluator, half real: merged bays dropped as one opening).
5. **A column missing from one plan but drawn above is a contradiction**, reported with its exposure, not an absence.
6. **Direction is not meaning**: a continuous beam read right-to-left put the end anchorage on the interior support.
7. **A legend is a table of rows**: the nearest caption on the swatch's row, ambiguity recorded (M6 W5).
8. **"No silent error" is not "no shortfall"**: every missing m³ is now reported, but not every one carries a range.

## B Before / after numbers, with their validation

**Held-out synthetic set** — seeds 301–340 generated only after the engine freeze `af2822a`, run once; V4 = the M6
engine state, V5 = M7 (`08_INDEPENDENT_VALIDATION.md`):

| Measure (40 cluttered villas) | V4 | V5 |
|---|---:|---:|
| Silent family/storey quantity rows (of 286), development / held-out vocabulary | **47 / 51** | **0 / 0** |
| Silent under-count, m³ (columns + slabs), development vocabulary | 140.3 | 0 |
| Completeness: injected elements detected (of 479), both vocabularies | 478 / 478 | **479 / 479** |
| Completeness false findings, development / held-out vocabulary | 5 / 8 | **1 / 1** |
| Metamorphic properties held (10 villas × 10 operations) | 69 / 100 | **100 / 100** |
| Clean villas (20): silent rows | 0 | 0 (identical) |

Measured vs truth under V5 (development vocabulary): footings 646.0 / 646.0 m³; columns 463.6 / 474.8 (11.2 inside
unresolved ranges); slabs 1 199.6 / 1 454.8 (80.3 inside ranges, 50.6 ambiguous stair bays, 124.3 on missing plans);
beams 593.8 / 678.4 (31.1 inside ranges, 53.5 on missing plans).

**Post-freeze fixes, reported apart** (found on ST7757 after the held-out run): P1 lintel width bands at 1 mm (a
1.000 m opening had dropped out of the schedule's bands under the local frame); P2 column outlines set aside by the
layer rule stay weak evidence (two had stopped being reported); P3 the per-item checker compared a two-label footing
against the wrong type. The held-out completeness runs repeated on the post-fix engine are identical on every count
(`heldout/POSTFIX_COMPLETENESS.json`).

**Tests**: 42 new tests in `tests/m7_reliability/`, all passed. Full suite (`12_REGRESSION_RESULTS.md`): 7 476
passed (M6 7 434 + the 42), **0 code failures**, the same 376 tests blocked by missing data and 136 prerequisite
skips as at M6; M1–M6 package suites all pass, the M4 and M5 frozen records rebuild live on the M7 engine.
Gate: **INCOMPLETE**.

## C Second villa

**Blocked.** No second drawing set exists in the repository or the connected drive (metadata search only; nothing
opened). Nothing in this package is presented as second-villa evidence. `09_SECOND_VILLA_BLIND_TEST.md` lists what is
needed and the protocol, which `tools/urban_project_run.py` enforces (blind run, freeze, byte-identical check, compare
only after the freeze) and which was exercised end to end on a synthetic project.

## D ST7757 changes, with their basis

Post-discovery (the drawing's own invariance failures motivated several rules). Each change is attributed by removing
one V5 convention at a time (`st7757/ABLATION.csv`, `10_BEFORE_AFTER_QUANTITIES.csv`):

| Family / storey | V4 → V5 measured | V4 → V5 unresolved high | Basis |
|---|---|---|---|
| Ground slab, ground | 16.755 → 17.241 m³ (+2 cells) | 5.329 → 4.767 | `SLAB_JUNCTION_GAP_CLOSURE`: a support gap no longer merges two cells into an unresolved one (+30.0 kg bars) |
| Slabs, 1F | 20.005 → 19.918 m³ | — | `TOUCH_IS_NOT_OVERLAP` (−0.081): a band-gap sliver is a junction, not slab |
| Slabs, GF | 33.450 → 33.490 m³ | — | `COLUMN_LAYER_EVIDENCE` (+0.040): two outlines on a generic layer no longer close cells |
| Beams, 1F | 21.383 (same) | 7.081 → 7.453 | `TOUCH_IS_NOT_OVERLAP` (+0.27): a flush column no longer cuts an unresolved band; bars `CB_ENDS_BY_SHARED_SUPPORT` +1.45 kg |
| Beams, GF | 39.138 (same) | 4.981 → 5.293 | `COLUMN_LAYER_EVIDENCE` (+0.12), `TOUCH_IS_NOT_OVERLAP`; bars +5.3 / −5.3 kg net −0.01 kg |
| Lintels, GF | 0.216 → 0.216 m³ | — | the local frame would have dropped OP-002; `LENGTH_CLASS_AT_MILLIMETRE` (P1) keeps it |
| Completeness findings | 93 → 90 | — | 3 MEMBER_OUTLINE_SUSPECT resolved by `COLUMN_OUTLINE_BY_SECTION`; 2 column outlines reported at MEDIUM instead of HIGH (P2) |

Total measured concrete 313.474 → 313.913 m³ (+0.439); unresolved exposure high 30.742 → 30.864 m³.

## E What still fails, ranked by quantity risk

1. **Nothing is released**: 0 items engineer-approved; 313.9 m³ is provisional / machine-supported only.
2. **Unbounded exposure**: out-of-scope families on ST7757 (stairs, pool, domes, water tank, parapets drawn, not
   quantified; lift, walls not evidenced) and 85 of 90 completeness findings without a volume.
3. **Storeys whose plan is missing carry no range** (synthetic: 124 m³ slab, 54 m³ beams over 5 drawings) — M7-W21.
4. **Untagged beam spans** stay unresolved by convention: no synthetic beam row is EXACT (31 m³ of 678 inside
   ranges); ST7757 beam exposure 14.4 m³ — M7-W22.
5. **Legends drawn elsewhere** are not read: ST7757 fills stay UNKNOWN — M6-W6.
6. **Independent check coverage**: 58 ST7757 items not comparable (arcs, recovered panels) — M7-W23.
7. **Residual drawing sensitivity on ST7757**: an exploded clipped footing +0.042 m³; mirror −0.002 m³; −0.13 kg —
   M7-W9, M7-W20; RTEXT not read — M7-W19; ids change with the unit — M7-W18.
8. **One real project**, post-discovery.

## F Quotation-ready?

**No.** No quantity is released, the only real project is post-discovery, the second villa is blocked, the exposure is
unbounded for out-of-scope families and volume-less findings, and the test gate is INCOMPLETE. At 26.5 KWD/m³ the
measured ST7757 concrete is a planning figure of 313.9 m³ ≈ 8 319 KWD with a known unresolved range of 464–818 KWD on
top (`11_QUOTATION_RISK.md`).

## G M8 focus

1. A second real villa with an independent BOQ through the manifest runner — blind, frozen, then compared.
2. An engineer review of ST7757 with the release policy (approve / reject / exclude bound to the drawing's sha256).
3. Volume ranges for STOREY_PLAN_MISSING and for the volume-less finding kinds, so quotation exposure is bounded.
4. Quantify the out-of-scope families that ST7757 draws (stairs, tank, domes, parapets) from drawn geometry.
5. Legends across sheets and from the PDF; arc-exact independent checks; frame-free item ids.
