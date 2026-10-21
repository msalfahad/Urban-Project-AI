# S5.1 CHANGELOG: ground-system rebar delta release over frozen S5

**Round:** `S5.1` · **Policy:** `GROUND_SYSTEM_REBAR_S5_1_DELTA_V1` · **Frozen baseline:** `research/alsenan_ground_system_rebar_s5/S5_FREEZE_MANIFEST.json` (sha `ff488a92f3ea`, stamp `cab778a+code:2dc78fc0ff285ba2`)
**Preceded by:** S4.1 (`468e90d96575`) and S6.1 (`c4744888ed22`) freezes · **Built by** `build_ground_system_rebar_s5_1.py` (blind, byte-identical rebuild)

S5 is unchanged. Every S5 code, input and output hash was checked first, and no S5 file was written. This file is
BASELINE + DELTA.

## Headline

| | kg |
|---|---|
| Frozen S5 known | 1457.9983 |
| Longitudinal delta (through-support portions) | 25.6000 |
| Stirrup core-path delta | 67.2553 |
| **S5.1 known** | **1550.8537** |

Every released quantity is a LOWER_BOUND. Nothing was raised to VERIFIED.

## Links (brief §16, §18)

- Each p.13 section draws one closed link (2 legs) with a hook. Three of the links carry Ø8/15cm; the <2.5 m link
  has no label, so its diameter and rate stay SOURCE_EXPECTED_NOT_LOCATED.
- **Released:** 4 GB stirrup sets and 2 strap sets (SB1 / SB3).
  - These are the only sets where width, depth, cover, diameter, rate, count and topology are all source-known.
  - CORE_PATH = 2(b-2c-d) + 2(h-2c-d), with c = 70 mm. That is the larger note-22 cover, so the result is a lower
    bound under either cover.
  - Hook extension and bend arc stay blocked.
- **SB1 / SB3** use the STR2 topology (4 legs): only the outer link is released. The inner link is not inferred.
  SB2 (str3) stays a SOURCE_CONFLICT.
- **Topology only, mass blocked:** 27 GB sets.
  - 19 are spans whose depth is FOLLOW ARCH (unresolved).
  - 8 are <2.5 m candidate spans (their link is not printed).

## Through-support runs (brief §17)

- Every GB support end is classified: BEAM_JUNCTION_END 46, END_SUPPORT 40, INTERIOR_CONTINUING_UNVERIFIED 20, THROUGH_SUPPORT 12.
- **THROUGH_SUPPORT** means the same drawn band continues through a column and both spans carry identical released
  bars.
  - Source: p.13 draws the GB bars unbroken through the column.
  - The two spans become one BAR_RUN. There is no termination at the column face and no development at the
    internal support: those development and hook components become NOT_APPLICABLE.
  - The bar inside the column is released at the column's smaller schedule side (S1), split half to each span.
- **Continuous runs:** 3, over 6 interior supports.
- End-support development stays unresolved (S5-02).

## Not resolved (brief §20)

SB2, the annex exterior-GB depth, and the GB band against the support face.

## Counts

- Delta rows: 1148, covering all 1104 frozen components.
- Unresolved: 872 rows (864 carried from S5 with their S5.1 status, 8 new named portions).

## Files

| File | Content |
|---|---|
| `S5_1_DELTA_COMPONENTS.csv` | one row per frozen component (plus named portions), with all brief §2 fields |
| `S5_1_RELEASE_SUMMARY.json` | baseline, deltas, new totals, end classes, continuous runs, conservation, flags |
| `S5_1_UNRESOLVED.csv` | carried S5 rows with their S5.1 status, plus new blocked portions |
| `S5_1_PROVENANCE.jsonl` | per delta row: frozen row, formula, inputs, evidence ids, class, conditions |
| `S5_1_FREEZE_MANIFEST.json` | S5.1 frozen |
