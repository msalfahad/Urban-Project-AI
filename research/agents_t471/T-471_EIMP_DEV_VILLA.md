# T-471 EIMP part 2: component register, completeness matrix and component -> BOQ line map (development villa)

Worker 2, 2026-11-02, run session_01E6cPneAKSwtdNtFVdvzZBe. Built on the Lead's scope list
(board `docs/agents/EIMP_SCOPE_2026-11-02.md`, part 1). Training villa = development benchmark: no accuracy claim, no
quantity, rule, method or released default changed. Drawings are named by Drive folder "Alsenan chalet project" and
title; entities by sheet / page / DXF handle / note number only (no note text, client names or personal data).

## Files

| File | What it is |
|---|---|
| `t471_completeness.py` | the tool (schema URBAN_T471_COMPLETENESS_V1; definitions in its docstring). Read only: imports no quantity code; reuses the T-469 line class and verdict / downgrade binding rules |
| `build_eimp_register.py` -> `EIMP_REGISTER_DEV_VILLA.json` | the EIMP register: 106 components (one per registry family of BOQ_FAMILY_MASTER 1.37.0, B10-10 split pool / lift pit / tank, plus 2 REGISTRY_GAP components), each with applicability, drawing evidence, method, rules, hierarchy level 1-5, formula, materials, exceptions, sources, moving row |
| `V3_0_42_CODE_OVERRIDE.json` | the one code whose totals moved V3.0.41 -> V3.0.42 (STR.CONC.GROUND_SLAB, from the merged T-442 summary) |
| `out/T471_MATRIX_V3_0_42.{json,md}` | the matrix on the candidate of record V3.0.42 (T-469 V3.0.41 counts + the T-442 delta), with the owner-gate table |
| `tests/t471_completeness/` | 16 tests: 13 on the hand fixture 'villa K471' (normal + adverse) and 3 pins of the committed register / matrix |

Run for any villa: write its register (same schema), then
`python3 -I research/agents_t471/t471_completeness.py --register R.json --lines BOQ_LINES.json --master
rules/coverage/BOQ_FAMILY_MASTER_1.37.0.json --verdicts V.json --downgrades D.json --version V --out M.json --markdown M.md`
(line level), or `--scoreboard T469.json [--override O.json]` (item-code level, used here).

## Method (what the matrix guarantees)

1. Every registry family has a component (else FAMILY_NOT_IN_REGISTER); every registry item code is claimed by exactly
   one component (test pin); a component may split a family by item code or element prefix.
2. Every candidate line is claimed exactly once: none -> UNMAPPED_LINE / _CODE, two -> DOUBLY_MAPPED (both reported,
   synthetic dropped + duplicated cases in the tests). Result on V3.0.42: **complete map, 0 unmapped, 0 doubly mapped**.
3. Applicability comes from the drawings (register), never from the candidate; APPLICABLE / NOT_APPLICABLE need
   evidence. A NOT_APPLICABLE component carrying a quantity line, or an APPLICABLE one whose lines are all excluded, is
   a reported conflict. Held quantities are never 0 and never summed into released; MEASURED is never VERIFIED.

## Result on the candidate of record ARCH_TAKEOFF_V3.0.42 (106 components)

| Five states | n | Owner gate | n |
|---|---|---|---|
| APPLICABLE_VERIFIED | 1 (suspended slabs 60.280 m3) | VERIFIED | 1 |
| APPLICABLE_HELD | 55 | HELD 50 + MEASURED 5 (wet floor tile, opening census, lift threshold, ground slab 21.638 m3, garden-band area) | 55 |
| APPLICABLE_UNMEASURED | 25 | MISSING | 25 |
| NOT_APPLICABLE | 5 (clearance, anti-termite, kitchen tile zones, cladding, wall handrail) | NOT_APPLICABLE | 5 |
| POSSIBLY_APPLICABLE | 20 | POSSIBLY_APPLICABLE | 20 |

MISSING (applicable, no line), by moving row: earthworks B1-02/03/04 (T-350, READY), B1-06 support item (no row),
external plaster B4-04 own line (T-314), spatter B4-05 (T-364), corner beads B4-09 and tile edges B4-10 (no row),
gypsum board class B5-02 (no row), nosing B7-05 (T-424), stair skirting B7-07 (T-443), stair rebar B7-14 and
B11-02 / B11-03 (source-blocked), shower B8-04 (no own quantity by Q-40 A: correct as MISSING-by-rule, see F-3), lintels /
mesh / mortar B9-02/03/04 (T-453 / T-363 / T-372), laps B11-04 (T-382), registers B2-01 / B2-03 / B2-04 / B2-05 (no
BOQ line by nature, see F-3), MEP B12-01 / B12-02 (drawn, outside the scope freeze: stated, not dropped).

The owner-gate table (14 items) is in `out/T471_MATRIX_V3_0_42.md`.

## Findings (engineering terms)

- F-1 REGISTRY GAPS (2 components, 2 candidate lines outside every family): `EXT.POOL.WATER_FACE` (pool water-face
  finish, 1 line held UNKNOWN; the drawing prints no layer on the water side, T-309; the freelancer workbook carries
  pool floor / wall tile rows) and `ARCH.EXTERIOR` (garden-band register area 9.101 m2 released). The registry has no
  pool-finish family (F-T328-2 still open). Proposed: a new registry version with a pool-finish family and a home for
  exterior register areas; until then they are mapped to the two gap components, never dropped.
- F-2 GROUND SLAB is MEASURED on V3.0.42 (26 / 26 lines released, 21.638 m3, no held line), not HELD as the scope
  list (V3.0.41 counts) says: the scope list row B10-05 should read MEASURED, not verified.
- F-3 FAMILIES THAT ARE NOT BOQ LINES: B2-01 room register, B2-03 gross area, B2-05 voids and B8-04 shower (folded into
  B8-01 / B8-03 by Q-40 A) are applicable but carry no line by design; the registry should mark them as
  register / derived families so the scoreboard stops counting them as expected BOQ lines (4 of the 25 MISSING).
- F-4 ENTRANCE AND STAIR-HALL FINISHES: no marble floor is drawn or noted; the freelancer's "entrance marble" rows are
  steps + one landing, i.e. the E1 external stair already carried by B7-02 / B7-04 (OWNER_RULE_OUTDOOR_FLOORS: outside
  stairs marble). B3-03 stays POSSIBLY_APPLICABLE (finishes schedule RFI-B-A12), the stair-hall floor parts are B3-01.
- F-5 TANK: one 'WATER TANK PLACE' text on the structural DXF and a slab panel, no tank structure in either discipline:
  B10-10 tank POSSIBLY_APPLICABLE (never 0, never invented).

## Evidence basis and what is not done

- Own reads this run (structural and architectural DXF, Drive sha256 9f9d1179 / ab54dd55, text census only): pool
  texts on both DXFs, the tank text, the absence of architectural finish texts; the freelancer workbook titles / row
  headings for F-1 / F-4 (no values copied). Every other evidence cell CITES the merged research piece in `sources`
  (its drawing reads); it was not re-read in this run. Checker: sample 10 states (proposal: B1-05, B1-06, B3-03,
  B4-02, B7-10, B8-07, B8-09, B10-10-TANK, B10-05, GAP-POOL-FINISH).
- The map is at ITEM-CODE level (T-469 counts + the T-442 delta); a line-level map (line ids) needs the V3.0.42
  BOQ_LINES.json rebuilt from the drawings (`--lines`); the tool supports it and the tests run it at line level.
- Waterproofing slice (T-383) and ceiling / skirting slice (T-446) are rows C-B8-* and C-B5-* / C-B3-06 here; the
  export join stays T-310.

## Lessons-register row (proposal, ERS s.7)

| Date | Defect | Cause | Rule |
|---|---|---|---|
| 2026-11-02 | candidate lines written under item codes no family owns (pool water face, exterior area) were invisible to every per-family scoreboard | scoring keyed by family, not by line | map every line to exactly one component and report unmapped / doubly mapped lines; a component without a family is a REGISTRY_GAP, kept and reported (every villa) |
