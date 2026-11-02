# T-456: given finish area multiplied by the drawing unit squared (owner directive 2026-11-02, C1)

Synthetic evidence only; no drawing, no client data. Scope: every villa.

## Physical element and unit contract

A finish surface (dry floor, wet floor, landing, roof, balcony) has one installed area in m2. FINISH_MATERIALS_TABLE_V1
takes that area in one of three forms: a given `area_m2`, a polygon in drawing units, or length x width in drawing
units. Only the last two need the drawing unit (`unit_m`, 1.0 for m, 0.001 for mm) squared. The given form is already
square metres: its key is `area_m2` and the V1 docstring says areas "come from the caller" verified.

## Step 1: reproduced (V1, engine/source/finish_materials_table.py:112, `_r(a * u * u)`)

| Case (DRY_FLOOR, hand 20 m2) | unit | V1 area m2 | V1 cement bags (high) | hand cement bags (high) |
|---|---|---|---|---|
| area_m2 = 20 | m | 20.0 | 6.72 | 6.72 |
| polygon 4 x 5 | m | 20.0 | 6.72 | 6.72 |
| area_m2 = 20 | mm | **0.00002** | **0.000008** | 6.72 |
| polygon 4000 x 5000 | mm | 20.0 | 6.72 | 6.72 |

Hand: mortar 20 x 0.03 x 1.05 = 0.63 .. 20 x 0.04 x 1.05 = 0.84 m3; cement x 8 = 5.04 .. 6.72 bags; sand x 1.1 =
0.693 .. 0.924 m3; adhesive 20 / 5 = 4 bags (owner Q-45 values carried by V1, PROVISIONAL). The defect shrinks the
area by 10^6 and every material after it collapses to the 6-decimal round-off (mortar prints 1e-06 m3, so cement is
8e-06 bags, not even a clean 10^6 shrink). Metres hide it (a x 1.0 x 1.0 = a exactly), which is why no test caught it.

## Reachability (research/agents_t456/t456_reproduce.py, out/T456_REPRODUCTION.json)

- Released V2.9 + route G: not in the 121-file protected set of RELEASED_PATH_V2_9_ROUTE_G.json (T-467 run-time trace
  on three synthetic drawings + static closure).
- Candidate of record V3.0.41: not in the static import closure of engine/source/arch_v3041.py + tools/urban_boq_m9.py
  (184 modules); arch_v3037.py names it in a docstring / string only.
- Run-time loaders in that closure: engine/source/rule_store.py:114 (fixed file tools/m9_rules_manifest.py) and
  tools/urban_structural_boq.py:128 (fixed adapter path); neither names the module, and their static closures (9
  modules) do not reach it. engine/freeze_manifest.py `_one` loads fixed module names, not this one.
- Method check: the static closure of the hub contains all 118 modules the T-467 RUN-TIME trace recorded (the two
  trace-harness files excepted), so the static answer is trusted for the released path.
- Only caller: research/agents_t086/alsenan_finish_table.py, which never sets `unit_m` (default 1.0): its committed
  T-086 figures are unaffected (a x 1.0 x 1.0 = a).

Conclusion: the defect is real code but moves NO current released or candidate quantity. It would contaminate every
finish material quantity (bed mortar, cement, sand, adhesive) of any caller that passes a measured area with mm
drawing units, so the fix is a precondition of the materials rows T-453 .. T-455.

## Step 2: fix as a NEW version (engine/source/finish_materials_table_v2.py, FINISH_MATERIALS_TABLE_V2)

One change: a given `area_m2` is never scaled. Everything else is V1's own code (polygon, length x width, wet wall,
stair flight, held / candidate, unit check, materials, sums, purchase rounding), imported, not copied, so V2 cannot
drift. V1 is unchanged (not frozen; kept byte-identical). V2 declares DEFAULT_GUARD_CLASS = UNWIRED_PRODUCER: nothing
imports it, no quantity moves until a lane I row wires it.

Tests (tests/t456_finish_area_units): 20 m2 stays 20 m2 with units m, mm, cm, inch, with the hand materials; V2 = V1
to the last digit in metres; V2 = V1 on every other branch in m and mm (polygon with hole, length x width, wet wall
with door and window, held wall with candidate, stair flight, held floor with candidate m2, no area); adverse: area 0,
negative, text, bool, NaN, inf -> HELD never 0; broken unit -> HELD as V1; area given as text "20" read as m2; area +
polygon -> area wins as V1; mixed mm table 20 + 12 = 32 m2 (V1: 12.00002) with a held row listed, never 0; duplicate
ids refused; reachability guard (fails if V1 is ever wired into the released or candidate path).

## General rule (proposed lessons row, ERS s.7)

A quantity whose key carries its unit (`*_m2`, `*_m3`, `*_m`) is never multiplied by the drawing unit; only raw
drawing coordinates are. Every unit-bearing method is tested with a mm fixture whose answer differs from the metre
fixture's raw numbers, because a metre-only test multiplies by 1.0 and hides a double conversion (provenance T-456).

## Same-class sweep (engine/ and tools/, head 775a8ffe)

`git grep` for a product times the unit squared (`* u * u`, `* unit_m ** 2`, `* scale * scale`, ...) outside V1: 58
hits in 17 files. Every operand is raw drawing geometry measured in the same function (shoelace / `poly_area` /
`overlap_area` / shapely `.area` / union area / arrangement face `area` / bounding-box product); the dict-key operands
were traced (e.g. concrete_completeness.py:1192 `e["area"]` is set at :542 from `_signed_area(ring)` of the hatch
ring, drawing units). The metre extras added beside them (generic_route.py:1620 free footings `(L + 2p) x (W + 2p)`,
route_g_scope_v1.py:331 / 365 `free_rel`, `fb`) are added AFTER the scaling, not scaled. tools/pdf_evidence.py:114 is
a Bezier parameter, not a unit. No second instance of a caller-given m2 being scaled was found; this is a text sweep,
not a proof for code that renames the unit (a caller-given area under another key would need its own test).

## Not done / out of scope

- V1 also uses 5 m2 per 20 kg adhesive bag for every porcelain size; the OWNER CONFIRMED register (MISSION, 2026-11-02)
  gives 3 m2 per bag for 120 x 60 and 160 x 80. That is a rule-value change for T-448 / T-455, not a unit defect; V2
  keeps V1's values unchanged.
- Wiring V2 into a candidate (lane I) and the materials rows T-453 .. T-455.
