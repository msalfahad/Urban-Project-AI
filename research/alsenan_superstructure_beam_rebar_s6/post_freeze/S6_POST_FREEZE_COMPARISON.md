# S6 post-freeze comparison (comparison only - S6 is not tuned)

Run after the freeze commit 652878f; `post_freeze_comparison.py` refuses to run unless `S6_FREEZE_MANIFEST.json`
still matches (verified: True, stamp `d39f5f6+code:add76dd5f5e9c59a`). References read only
here: old Urban R3 beam / CB registers, christiannp `REBAR_EVIDENCE.csv` (sha256 `5a56ed585b03f864...`),
the freelancer lineage and the U-C4N / multi-engine oracle file. No reference value entered S6.

## Headline (matching scope only)

* S6 known source-derived: simple 2824.46 kg, CB 805.69 kg (MID 265.21),
  total 3630.15 kg - straight known segments only (lower bound).
* Old Urban R3 simple beams (75 rows matched by tag; 3 unmatched):
  verified 3534.3 kg (longitudinal 2680.9, stirrups
  853.4) + provisional 404.7 kg.
* Old Urban R3 CBs (11 of 13; CB2 and CB10 absent): verified 1362.0 kg
  (longitudinal 830.4) + provisional 866.2 kg.
  Multi-engine BEAMS row (old Urban released): 4115.9 kg.
* christiannp: 63 simple-beam strips, longitudinal 3588.9 kg + stirrups
  1214.3 kg (assumed perimeter); every CB EXCLUDED.
* Freelancer: BEAMS steel 9.89 t as one lump on 65.97 m3 gross concrete -
  SCOPE_DIFFERENCE, no kg difference or percentage reported. U-C4N: project total only - SCOPE_DIFFERENCE.
  The 150 kg/m3 rough profile (5638.1 kg) is estimating sanity only.

## Old Urban vs S6, by class

| class | rows | S6 kg | reference kg (verified / provisional) |
|---|---|---|---|
| ANCHORAGE_MISSING | 158 | 0.0 | 0.0 / 329.4 |
| ASSUMED_COMPONENT | 22 | 0.0 | 0.0 / 199.6 |
| BAR_RUN_CONVENTION | 48 | 1632.7 | 1773.1 / 129.0 |
| BINDING_DIFFERENCE | 12 | 0.0 | 107.8 / 24.4 |
| DETAIL_APPLICABILITY | 8 | 0.0 | 340.6 / 26.4 |
| HANGER_MISSING | 11 | 0.0 | 0.0 / 0.0 |
| HOOK_MISSING | 66 | 0.0 | 0.0 / 150.5 |
| MID_EXTENT | 9 | 265.2 | 0.0 / 284.1 |
| OCCURRENCE_DIFFERENCE | 47 | 372.5 | 175.5 / 155.9 |
| SAME | 132 | 1114.2 | 1114.2 / 136.1 |
| SIDE_REBAR_SEMANTICS | 33 | 0.0 | 0.0 / 0.0 |
| STIRRUP_GEOMETRY_MISSING | 92 | 0.0 | 1385.0 / 148.3 |
| WIDTH_SOURCE_CONFLICT | 1 | 0.0 | 0.0 / 16.7 |

## christiannp vs S6, by class

| class | rows | S6 kg | reference kg |
|---|---|---|---|
| BAR_RUN_CONVENTION | 42 | 813.1 | 852.3 |
| BINDING_DIFFERENCE | 6 | 0.0 | 18.8 |
| DETAIL_APPLICABILITY | 4 | 0.0 | 355.3 |
| OCCURRENCE_DIFFERENCE | 58 | 1486.0 | 1785.1 |
| SAME | 40 | 525.4 | 525.4 |
| SCOPE_DIFFERENCE | 13 | 805.7 | 0.0 |
| STIRRUP_GEOMETRY_MISSING | 63 | 0.0 | 1214.3 |
| WIDTH_SOURCE_CONFLICT | 2 | 0.0 | 52.1 |

## Root causes

1. **Stirrup mass (largest single cause):** old Urban and christiannp price an assumed link perimeter / legs; S6
   releases counts only (Q7: legs, path, hooks). STIRRUP_GEOMETRY_MISSING + HOOK_MISSING.
2. **End anchorage allowances:** old Urban adds a provisional end extension on every bottom / top bar; S6 keeps
   DEVELOPMENT_1/2 blocked with no default (Q1). ANCHORAGE_MISSING.
3. **Bar-run convention:** same bars, different length - old Urban / christiannp lengths vs S6 support face to
   support face (simple) or clear span + support + bound 7.5 cm (CB). BAR_RUN_CONVENTION.
4. **Member segmentation:** christiannp strips often cover several S6 spans; old Urban misses S6-recovered
   occurrences (PRE-S6 binding / census) and vice versa. OCCURRENCE_DIFFERENCE.
5. **Blocked by S6 evidence rules:** width conflicts (B6, B21, B29, CB2, CB10), candidate bindings and B3/CB3,
   WITH STAIR / planted-column candidate details, curved rings and the cantilever, CB span conflicts.
   WIDTH_SOURCE_CONFLICT / BINDING_DIFFERENCE / DETAIL_APPLICABILITY.
6. **CB top bars and MID bars:** old Urban held frame top bars and MID bars PROVISIONAL with assumed extents; S6
   blocks top bars (Q2 / Q3) and releases MID bars on 0.22 x Ln (axis to axis, the drawing's definition).
   ASSUMED_COMPONENT / MID_EXTENT.
7. **Hangers and side bars** are unquantified on every side (HANGER_MISSING, SIDE_REBAR_SEMANTICS).

No class is UNKNOWN. No S6 value is changed by this comparison; a correction needs an issue, source evidence, a
regression and a new version (S6.1), never an edit of the frozen outputs.
