# S6.1 CHANGELOG: superstructure beam rebar delta release over frozen S6

**Round:** `S6.1` · **Policy:** `SUPERSTRUCTURE_BEAM_REBAR_S6_1_DELTA_V1` · **Frozen baseline:** `research/alsenan_superstructure_beam_rebar_s6/S6_FREEZE_MANIFEST.json` (sha `c29a28bc6633`, stamp `d39f5f6+code:add76dd5f5e9c59a`)
**Preceded by:** S4.1 freeze (`468e90d96575`) · **Built by** `build_superstructure_beam_rebar_s6_1.py` (blind, byte-identical rebuild)

S6 is unchanged. Every S6 code, input and output hash was checked first, and no S6 file was written. This file is
BASELINE + DELTA.

## Headline

| | kg |
|---|---|
| Frozen S6 known | 3630.1493 |
| Longitudinal delta: B3 WITH STAIR + B26 base bars | 372.6063 |
| Planted-column extra (B26, horizontal projection) | 12.0099 |
| Stirrup core-path delta | 1332.2643 |
| **S6.1 known** | **5347.0297** |

Every released quantity is a LOWER_BOUND. Nothing was raised to VERIFIED.

## What was released

1. **Single closed link: 80 stirrup sets.**
   - Source: the p.15 typical beam section and the p.13 labelled sections draw one closed link.
   - CORE_PATH = 2(b-2c-d) + 2(h-2c-d), with c = 25 mm (note 22), b and h from the schedule row, and d the
     scheduled link. It is multiplied by the released count.
   - Class `GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY`, all four rule-B conditions true.
   - Hook extension stays `SHAPE_FOUND_LENGTH_BLOCKED`.
2. **STR2: 8 stirrup sets.**
   - Topology SOURCE_FOUND: 2 links, 4 legs. Only the outer link's core path is released.
   - The inner link stays blocked: width, location and height. The REMARKS icon draws the inner rectangle offset
     [114.7] units from the outer one, so it is a symbol, not a section, and no leg of it is bound to the cover
     lines. No equal subdivision was used.
3. **New stirrup counts: BM-1F_ROOF-B3-BL023-6B9:SPAN1 = 15, BM-GF_ROOF-B26-BL014-4CC:SPAN1 = 74, BM-GF_ROOF-B3-BL033-6B7:SPAN1 = 15, CBO-GFRS-CB7-BL003:SPAN1 = 39, CBO-GFRS-CB7-BL003:SPAN2 = 41.**
   - CB7: both surviving reading directions give the same diameter, rate, span and count.
   - B3 / B26: ceil(rate x clear run), no +1.
   - CB13 was tested the same way and fails: reversing the reading direction swaps Ø8 / Ø10, so its counts stay
     blocked.
4. **B3 WITH STAIR (BM-1F_ROOF-B3-BL023-6B9 / BM-GF_ROOF-B3-BL033-6B7).**
   - The p.16 callouts equal the B3 row, so the base components release: 2Ø12 top and 4Ø16 bottom over the plan
     clear run, 6Ø8/m count and core path.
   - The plan run is a lower bound of the cranked bar. CRANK_EXCESS and END_BENDS stay blocked.
   - The stair extra becomes NOT_APPLICABLE: the detail adds no bars.
5. **B26 (BM-GF_ROOF-B26-BL014-4CC).**
   - BASE_B26: 6Ø14 top and 19Ø18 bottom over the clear run, 10Ø10/m count 74, and the STR2 outer-link
     core path.
   - PLANTED_COLUMN_EXTRA: COUNT_TOTAL 4, Ø16. Each bar runs DEPTH (850 mm) past each column face, so
     the released lower bound is the horizontal projection 2 x DEPTH + 200 mm (the smaller planted-column
     side), = 12.0099 kg.
   - Row allocation is not inferred (not 2 + 2). It does not change the projection.
   - Crank excess and hooks stay blocked.
   - Side bars stay blocked (S6-11).

## What was recorded but not released

- **CB end-support top-bar legs (14 components).**
  - The 90° leg to the bottom-bar level is SOURCE_FOUND, and its geometry is derivable.
  - But the bar that carries it is in conflict (Q2): the frames put the leg on the per-span top bar, the typical
    on a separate, unlabelled end-support bar.
  - Its count and diameter are therefore not candidate-invariant, so rule B fails (NO_CONTRADICTING_PROJECT_SOURCE)
    and the leg carries no kg.
- **Not resolved:** CB3 against B3 WITH STAIR, the five width conflicts, the CB4 / CB5 / CB8 spans, the B1
  candidate bindings, the curved and CA beams (brief §20).

## Counts

- Delta rows: 2111, covering all 2002 frozen components.
- Stirrup topology rows: 118.
- Unresolved: 1108 rows (999 carried from S6 with their S6.1 status, 109 new named portions).
- Blocked hook / path portions remaining: CRANK_DIAGONAL_EXCESS 1, CRANK_EXCESS 4, END_BENDS 4, END_HOOK_1 1, END_HOOK_2 1, HOOK_EXTENSION 90, INNER_LINK 8, CB_END_LEG_MASS 14.

## Files

| File | Content |
|---|---|
| `S6_1_DELTA_COMPONENTS.csv` | one row per frozen component (plus named portions), with all brief §2 fields |
| `S6_1_STIRRUP_TOPOLOGY.csv` | one row per stirrup set: topology, legs, section, core path, count, mass state |
| `S6_1_RELEASE_SUMMARY.json` | baseline, deltas, new totals, counts, conservation, flags |
| `S6_1_UNRESOLVED.csv` | carried S6 rows with their S6.1 status, plus new blocked portions |
| `S6_1_PROVENANCE.jsonl` | per delta row: frozen row, formula, inputs, evidence ids, class, conditions |
| `S6_1_FREEZE_MANIFEST.json` | S6.1 frozen before S5.1 |
