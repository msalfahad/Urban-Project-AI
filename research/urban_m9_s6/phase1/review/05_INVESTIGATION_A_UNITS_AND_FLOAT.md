# Investigation A: metres vs millimetres, and the float-boundary defect (S6P1-NEW-05)

**Verdict: the defect is not a units problem. It is a strict float comparison at a threshold that equals a common drafted length.**
- Millimetre drawings have it too.
- The frozen millimetre result on the reference plan is itself wrong: it misses one door and one window.
- Converting to millimetres first does not fix it. Neither does quantisation or integer geometry.
- The only fix that works in every case tested is a tolerance-aware predicate.

Everything here was run on scratch copies; no production code was changed.
- Reference-plan evidence (sites, room names, crops) is in the PRIVATE part of the review package.
- The synthetic fixtures and harnesses are in `fixtures_investigation_A/`.

## A.1 Which comparison causes the differences

Method:
- Every lower-bound threshold on the band path was replaced by an instrumented copy (`scripts/threshold_probe.py`).
- Each copy logs every comparison whose value lies within a relative 1e-6 of its threshold.
- The instrumented run is byte-identical to the committed run (V1: `BOQ_LINES.json` sha matches; V2: `BOQ_LINES`, `ARCH_OPENINGS`, `ARCH_WALLS`, `ARCH_ROOMS` and `FINISH_COVERAGE` shas match).
- Each threshold was then given a 1e-9 relative slack, separately (`face`, `overlap`, `gap`) and all together.

Near-threshold decisions on the reference plan (distinct subjects):

| Comparison (code location) | Threshold | mm run | metres run | Changes an output? |
|---|---|---|---|---|
| `opening_census.face_lines`: `if L < min_len: continue` (`opening_census.py:95`).<br>Called with `min_len = 100.0 * k` from `arch_plan._bands` (`arch_plan.py:280-281`), `lintel_measure.openings` (`lintel_measure.py:66-67`) and `lintel_measure.wall_layers` (`:46`) | 100 mm drafted face piece | 4 pieces dropped (`L` = 99.999999999651 … 99.999999999884 mm) | 14 pieces dropped (the same 4 + 10 more) | **Yes**: the only one that does |
| `opening_census.wall_bands`: `if hi - lo < min_overlap` (`:143`), from `arch_plan._bands` | 300 mm overlap | 1 dropped (299.99999999710 mm) | 1 dropped | No |
| `band_gaps`: `if g < min_gap` (`opening_census.py:217`, `opening_gaps.py:31`), from `layer_roles` | 500 mm gap | 1 dropped (499.99999999895 mm) | 1 dropped | No (layer-role evidence only) |
| `_split_at_columns`, `_small_rects` (column side) | 0.5 m / 0.15 m | none near the threshold | none | No |

Slack per threshold, compared with the run without slack:

| Slack on | mm result | metres result |
|---|---|---|
| face piece only | +1 door, +1 window, +0.20 m wall run, one small space 0.08 m² smaller | identical to mm-with-slack on every room, opening and quantity line |
| overlap only | unchanged | still differs from mm |
| gap only | unchanged | still differs from mm |
| all | same as face only | same as face only |

The one remaining difference between metres and mm with slack is a strip **id**: `SITE-<hash>` hashes raw drawing coordinates. That is a separate, small id-stability defect (S6R-A3).

## A.2 Are the two extra openings genuine? Yes

Both lie at one site of the reference plan's ground floor (private crop `PRIVATE/A_SITE_S1.png`).

**A 1.0 m door**, masonry jamb at both ends:
- a door block with a swing arc, an 890 mm leaf drawn open and a frame;
- jamb lines on the wall layer at both ends.

**A 1.0 m window**, masonry jamb at both ends:
- a window block with four 900 mm glazing lines and a frame;
- jamb lines on the wall layer at both ends.

In both, the lower jamb's second wall face is exactly one drafted 100 mm piece: the face running from the jamb down to a cross wall or column. The piece's stored coordinates give 99.999999999651 mm and 99.999999999884 mm. The drafted length is 100 mm.

Without the piece:
- the second face of the wall band starts above the opening;
- the band's common extent excludes the opening;
- no gap is found;
- the door and the window disappear silently, together with 0.20 m of wall run;
- the small space between them takes the strip area.

**So the millimetre results are wrong, in V1 and V2 alike.** V1's frozen outputs on the reference plan carry this error.

## A.3 Is it a units problem? No. Is it fixed by converting to mm first? No

Minimal synthetic fixtures (`fixtures_investigation_A/`). The geometry is one 200 mm wall with a 1000 mm opening, where one face below the opening is a drafted 100 mm return. The census is the engine's own `lintel_measure.openings`.

Decision procedures:
- **FROZEN**: the committed code.
- **ROBUST**: drop only when `L < 100 mm − 1e-6 mm`.
- **CANON_MM**: convert to millimetres first, then FROZEN.

| Fixture | Unit | How the 100 mm piece is placed | Stored-coordinate length (exact) | FROZEN | ROBUST | CANON_MM |
|---|---|---|---|---|---|---|
| A0 | mm | typed, at the origin | 100 | 1 | 1 | 1 |
| A1 | mm | block, rotated 90°, site offset | 100 | 1 | 1 | 1 |
| A4 | mm | typed, site offset | 100 | 1 | 1 | 1 |
| **A5** | **mm** | **block, rotated 30°, site offset** | **99.99999999998772…** | **0** | **1** | **0** |
| **A2** | m | typed, site offset | 0.09999999999999431… | **0** | 1 | 1 |
| A3 | m | block, rotated 90°, site offset | 0.10000000000002273… | 1 | 1 | 1 |
| **A6** | m | block, rotated 30°, site offset | 0.09999999999997685… | **0** | 1 | **0** |

The cell values are the number of openings found (1 is correct).

The independent calculation is the exact length of the stored binary coordinates, using `Decimal(float)` at 50 digits. It shows that the distance formula is exact. The error is already in the stored coordinates: decimal-to-binary conversion and the insert transform.
- No better length formula can fix it.
- Only the decision rule can.
- A0 and A5 are the same geometry moved and rotated, which makes them a translation/rotation **metamorphic violation in millimetres**.

## A.4 Which fix

`fixtures_investigation_A/a_method_comparison.py` (stdlib, deterministic):
- A drafted 100 mm piece is placed by an insert transform at 2000 random site offsets per case.
- It is tested by six decision procedures.
- Each cell is the fraction kept; 1.0 is correct.

| Case | FROZEN | CANON_MM | QUANT_1UM | INT_UM | **ROBUST_EPS** | LOCAL_ORIGIN |
|---|---|---|---|---|---|---|
| mm, 0° / 90° / 180° / 270° | 1.000 | 1.000 | 0.999 | 1.000 | **1.000** | 1.000 |
| mm, 30° | 0.867 | 0.867 | 1.000 | 1.000 | **1.000** | 0.867 |
| mm, 45° | 0.638 | 0.638 | **0.000** | **0.000** | **1.000** | 0.638 |
| mm, random angle | 0.496 | 0.496 | 0.504 | 0.504 | **1.000** | 0.496 |
| m, 0° | 0.772 | 0.941 | 0.998 | 1.000 | **1.000** | 0.772 |
| m, 45° | 0.400 | 0.495 | 0.000 | 0.000 | **1.000** | 0.400 |
| m, random angle | 0.497 | 0.518 | 0.516 | 0.517 | **1.000** | 0.497 |

| Option | Assessment |
|---|---|
| Scaled (unit-relative) tolerances (done in Phase 1) | Necessary: fixes the merge tolerance, which was 1 m in a metre drawing. **Not sufficient**: the defect is a threshold met exactly, independent of scale |
| Canonical conversion to mm before interpretation | Useful for clarity, logging and one constant set. **Does not remove the defect**: the rounding error is relative, and scaling keeps it (A6; m 45° 0.495) |
| Quantisation of coordinates (1 µm grid) | Fails worse on diagonal geometry. At 45° the snapped length is systematically below 100 mm (0.000) |
| Integer geometry (µm, exact squared lengths) | The same failure. Exact arithmetic cannot recover a drafted 100 mm after an irrational rotation, and it is a large rewrite |
| Local origin (translate before measuring) | Reduces magnitude but not the decision error: the noise comes from the rotation |
| **Robust predicate** (`L ≥ T − ε`, ε = 1e-6 mm in drawing units) | **Keeps 100 % in every case.**<br>ε sits about 4 orders above float noise at site scale (~1e-10 mm) and 3 below any drafting precision (≥ 1e-3 mm). It keeps the threshold's drafted meaning: "at least 100 mm" includes 100 mm |

**Recommendation** (S6R-A1, Phase 2, must-fix):
- One shared predicate module (`engine/source/geom_predicates.py`, stdlib): `at_least(v, T, eps)`, `less_than(v, T, eps)` and `at_most(v, T, eps)`, with `eps = GEOM_EPS_MM * 1e-3 / unit_m`.
- Every length / gap / overlap / side threshold on the V2 path goes through it. The census in A.1 lists the call sites on the band path.
- A crude grep census finds about 80 candidate threshold comparisons on the architectural path. Each one needs review, not a mechanical rewrite.
- Canonical millimetres stays a separate, optional clarity change.

Two longer-term points:
1. **Thresholds should not sit exactly on common drafted modules.** 100 mm is a typical return length, 500 mm a typical gap.
2. **Every threshold test needs a metamorphic fixture pair**: rotated at 30° / 45° and offset to site coordinates. The M7 metamorphic harness only translated by benign offsets and rotated by 90°, which is exactly the case that does not trigger this.

## A.5 Can it be fixed without changing frozen structural quantities?

| Consumer of the fragile comparison | Effect of the fix on the reference plan | Frozen? | Route |
|---|---|---|---|
| ARCH_TAKEOFF_V1 | +1 door, +1 window, +0.20 m wall run, one small space −0.08 m², skirting and strip classes | Yes (byte tests) | **Do not change V1**. Apply the fix in V2 only |
| ARCH_TAKEOFF_V2 | the same corrections | No (opt-in, not frozen) | Fix behind a versioned tolerance policy (`ROBUST_V1`), reviewed |
| M4 / route G architectural lintel evidence (`arch_evidence.lintel_openings`, called from `tools/urban_boq_m2.py:124` when a plan is supplied) | GF 27 → 29 openings (the same door and window) | Yes (route G / M4 freezes) | **Owner decision**: a versioned structural correction (new lintel-evidence rule id) with its own before/after record, never in place |
| S8.6 lintel census (`build_s8_6.py`, `face_lines(min_len = 1.0)`) | Not affected (1 mm minimum) | Yes | Nothing to do |

**Yes**, it can be fixed without changing frozen quantities:
- implement the predicate in a new module used only by V2;
- leave `opening_census.py` (S8.6 code digest) and `lintel_measure.py`'s default path untouched.

But the frozen route-G / M4 lintel evidence on this plan is **known to miss two openings**. That must be recorded as a known defect of the frozen release (S6R-A2), not hidden.

## A.6 Defect ids raised here

| Id | Defect | Class |
|---|---|---|
| S6R-A1 | strict float comparison at drafted thresholds (100 mm face piece; latent at 300 mm overlap, 500 / 400 mm gaps) | geometry defect, must-fix before Phase 2 |
| S6R-A2 | frozen V1 and route-G / M4 lintel evidence miss a drafted door and window on the reference plan | known defect of frozen results; record, do not edit |
| S6R-A3 | strip ids `SITE-<hash>` hash raw drawing coordinates, so the same strip gets a different id in another unit | id stability, small |
| S6R-A4 | the metamorphic harness never rotates by non-right angles or uses site-scale offsets | test gap |

## Reproduction

```
# scratch copy of the committed source (no production edits)
git archive c757d8a engine tools rules | tar -x -C WORK/src && ln -s $REPO/data WORK/src/data
python3 -I fixtures_investigation_A/make_fixtures.py OUT/dxf
python3 -I fixtures_investigation_A/eval_fixtures.py WORK/src OUT/dxf OUT/A_FIXTURE_RESULTS.json
python3 -I fixtures_investigation_A/a_method_comparison.py 2000 OUT/A_METHOD_COMPARISON.json
# reference plan (private): instrumented run, slack sets none | face | overlap | gap | all
python3 -I scripts/threshold_probe.py WORK/src PLAN.dxf OUT/mm_v2_face ARCH_TAKEOFF_V2 face GF=.. 1F=.. 2F=..
python3 -I scripts/qdiff.py OUT/mm_v2_none OUT/mm_v2_face
```
