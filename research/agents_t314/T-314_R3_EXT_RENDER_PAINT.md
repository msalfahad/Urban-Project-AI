# T-314 r3 — exterior render + exterior paint integration package (ARCH_TAKEOFF_V3.0.79, lane I, 2026-11-13)

Owner gap #1 of the 2026-11-13 delivery reset: external plaster / render was 0 lines on the candidate (B4-07
FIN.EXT.FINISH three storey lines HELD blank). This package wires the Checker-merged **T-756 face ledger** (MERGED
e121e0b4, Verifier 2026-11-13T10:00Z, GATE A PASS) into the same opt-in candidate, stacked on T-738 (V3.0.78, Gate B
READY on 49d21678). Nothing opens a drawing here; every face figure is a merged ledger figure. No client name, drawing
or coordinate is in this folder.

## Physical element

Each external rendered face band — a storey band (F.F.L. → next level), a parapet outer / inner / top face, a plinth,
a slab-edge band — with its gross m², its openings deducted once on the face that holds them (Q-73 A), bound to ONE
FIN.EXT.FINISH line of the candidate by element id. Exterior paint (Sigma) is the render of the same faces
(OWNER RULE PAINT 2026-11-12, UP-FIN-PAINT-002: paint m² = plaster m² of the same faces; edges / corners are lm).

## What changed (engine vs candidate, V3.0.78 → V3.0.79; run of record base f0c3a619 → aa0ec38a, 5242 → 5275 lines)

- **Exterior render (FIN.EXT.FINISH, B4-07):** 3 storey lines HELD blank → HELD BOUNDED as the **sum of their face
  rows** (GF 376.69 .. 410.18, 1F 248.18 .. 249.95, 2F 117.305); **12 parapet / plinth / slab-edge render lines added**
  (parapet outer / inner / top ×4 each, plinth, GF & 1F slab edge). Net render **1008.575254 .. 1085.612926 m²**
  (was 0). The 1F slab-edge line stays **HELD BLANK** (6 faces HELD by name: raster-only NE-1/SW-1/SW-2, hidden
  NW-4/NW-5, SE-1 unbound porch band) with its valued part 0.535 .. 2.00625 m² beside, never summed, never 0.
- **Exterior paint (FIN.EXT.PAINT, NEW item code on B4-07):** one m² line per render line, **= render face by face**
  (UP-FIN-PAINT-002); same figures and states (17 bounded + 1 blank, 1008.58 .. 1085.61 m²). 18 lines, 0 before.
- **Exterior corners (FIN.EXT.PAINT.EDGE):** one line restated by the merged T-754 verdict (F-T754-1: NW-1/NW-2 and
  NW-2/NW-3 above +9.70 are NOT_A_CORNER): 9.185812 → **6.585812 lm** (−2.60). Code total 283.218063 .. 284.418063 →
  280.618063 .. 281.818063 lm. The other 37 edge lines KEEP (statements).
- Released V2.9 + route G and every other candidate line byte-identical (asserted by `integrate`); no line is VERIFIED
  or released here (HELD only). The V3.0.64 .. V3.0.78 state checks re-run on the result.

## Engine vs freelancer (reference comparison, not verification)

Freelancer exterior Sigma net 1,469.9675 m² vs engine render/paint **1008.58 .. 1085.61 m²** (−31.4 % .. −26.0 %):
**RULE_DIFFERENCE** (unchanged from T-567 / T-747): domes excluded (owner: no domes), half-opening deduction is a
freelancer practice not an owner rule, boundary wall HELD under Q-65, drip edge excluded. Corners: freelancer 1,297.35
lm (2 lm = 1 m²) vs engine 176.94 .. 178.14 lm verticals + 103.68 lm windows + 0 .. 12.20 lm doors + T-337 horizontals:
**RULE_DIFFERENCE** (the 2-lm-per-m² convention is FLAGGED, not an owner rule). No face explains more; verdict proposal
**RULE_DIFFERENCE** for both.

## Validation

- Run of record: `research/agents_t314/v3079_run.py` on the Drive copies (P7757.dxf ab54dd55, ST7757 9f9d1179), exit 0;
  base **V3_0_78 = f0c3a619** = the T-738 run of record (asserted by its line index). `check_totals` confirms only
  FIN.EXT.FINISH / FIN.EXT.PAINT / FIN.EXT.PAINT.EDGE moved, each exactly by the changes; released quantity 0-delta.
- T-756 re-check on V3.0.78: `t756_alsenan.py --recheck LINE_INDEX_V3_0_78.json` exit 0 (no mapped id changed).
- Tests: `tests/t314_ext_render_paint` 18 pass (villa W314 by hand: two-F.F.L. ground floor by face not run×height,
  paint = render, totals, byte-identical, mirror order; adverse: parapet band folded into a storey line, face on two
  lines, held face as 0, face sum ≠ ledger, blank with a figure, VERIFIED, stale, wrong reserved id, applied twice,
  mm² slip, paint ≠ render, released line restated).

## Stacked / merge-order (registry at the T-738 merge)

Base registry **1.79.0 is PENDING on T-738** (candidate of record still V3.0.77). By the merge-order rule
`build_master_1_80_0.build_pending` refuses until T-738 promotes 1.79.0. So the registry artefacts are produced **at the
T-738 merge, by this package's own tools**, exactly as every stacked package ("version allotted at merge"):

1. `research/agents_t314/t314_promotions_source.py` → `out/PROMOTIONS_SOURCE_1_80_0.json`
2. `research/agents_t314/t314_package_families.py` → `out/T314_PACKAGE_FAMILIES.json`
3. `research/agents_t314/build_master_1_80_0.py --promote --write` → `rules/coverage/BOQ_FAMILY_MASTER_1.80.0.json`
   (adds FIN.EXT.PAINT to B4-07; candidate → V3.0.79)
4. add `coverage/BOQ_FAMILY_MASTER_1.80.0.json` to `tools/m9_rules_manifest.AUTHORED`, then
   `research/agents_t314/write_manifest.py`
5. rebuild `research/agents_t459/T459_CANDIDATE_BINDING.json` by its tool; regenerate `docs/CODEMAP.md` by the tool.

The Verifier regenerates `out/LINE_INDEX_V3_0_79.json` at Gate B with the canonical V3.0.44 verdict set (the committed
copy here uses the V3.0.40 snapshot — identical line classes for FIN.EXT.*, which bind no verdict). If T-738 r2 is
rejected or changes, rebase on its new head by re-running the tools, never by hand.

## Held / missing (never 0)

1F slab-edge render & paint (L-22e75c39 + its paint line) HELD blank, valued part beside. MISSING by name: parapet
blockwork ×4 (no MAS.* parapet line), parapet-top arrises ×4 (T-337 horizontals), passage substrate split. Open
verdicts carried, not decided here: F-T754-1 (8.40 lm inside L-1f1149d7), F-T751-2 (NE-2 parapet top), SE-1 slab-edge
1.840 m² ownership.

## Lessons register row (proposed, ERS s.7)

2026-11-13 | T-314 r3 | an exterior finish line valued as run × one storey height | a two-F.F.L. ground floor valued by
run × storey height is +7.4 .. +9.6 m² wrong and blind to parapets / plinth | value every exterior finish line as the
**sum of its drawn face rows** (one element per line, holes once by face), carry paint = render face by face
(UP-FIN-PAINT-002), and hold a blank face by name with its valued part beside, never 0 | tests/t314_ext_render_paint.
