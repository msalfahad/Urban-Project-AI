# S7: restricted elevated slab rebar QTO (project-basis release)

Round S7, policy `S7_RESTRICTED_SLAB_REBAR_QTO_V1`. Baseline HEAD `ac7a477`; engine stamp `ac7a477+code:963a379b6a4a7e25`.

This is not the final slab total. It quantifies only the 476 PRE-S7.1 S7 candidate items,
which come from 309 components. Every other portion is listed in `02_S7_BLOCKED_ITEMS.csv`
with no kg. Excluded means not quantified, not zero steel.

The one total is **RESTRICTED_S7_PROJECT_BASIS_KG = 3,802.015 kg**, an equivalent bar length of
6,127.733 m. Every released item is `PROJECT_BASIS_QTO`. None is
`SOURCE_DERIVED_PHYSICAL` or `PROJECT_BASIS_NUMERIC`, and nothing is labelled verified, as-built or source-exact.

## How each item is measured

The quantities come from the frozen PRE-S7.1 local bar strips. PRE-S7.1's own code is re-run in memory, and each of
its registers is checked byte for byte against the frozen file.

- **Equivalent length:** `L_total = RATE x DENSITY_FRACTION x sum(strip width x local run)`, in metres.
  - On a rectangle this is `RATE x FRACTION x width x run`.
  - The equivalent bar count `RATE x FRACTION x WIDTH` is never rounded, has no +1, and no ceiling or floor.
  - `PHYSICAL_BBS_COUNT` stays `UNRESOLVED`.
- **Mass:** `kg = L_total x D^2 / 162`, from `rebar_unit_mass`. No kg/m2 or kg/m3 factor is used.
- **Bottom bars.** Measured face to face of the supports.
  - `BOTTOM_IN_PANEL`: full density.
  - `BOTTOM_CONTINUING_50`: half density, face to face.
  - `BOTTOM_CURTAILED_50`: half density, run less 0.125 x L at each stopping end.
  - `BOTTOM_SUPPORT_CROSSING`: the continuing half over a continuous support, counted once.
  - The part beyond each face (anchorage, transition, lap, stop zones at unresolved ends) is blocked and listed.
- **Top bars (plan note 2, 5Ø10/m).** Owned by the support, quantified once.
  - `TOP_OVER_SUPPORT_EXTENSION`: 1/3 x the local clear span, from the support face into each side panel.
  - `TOP_SUPPORT_CROSSING`: over the beam between the faces, counted once.
  - The p.15 rules 0.25 L1, 0.30 Lmax and "extend 50 %" are `OVERRIDDEN_PROJECT_SOURCE` for the same bar role, and
    nothing is added for them.
  - At SUP-GF_ROOF_SLAB-037 the local 3Ø16/Top replaces note 2. Its count is released but its length is not, so it
    carries no kg, and no general 5Ø10/m is measured there.

## Authority split (provenance correction)

- **S7-AC01, top extent.** The 1/3 ratio is `PROJECT_SOURCE` (plan note 2). Only the convention that measures it from
  the support face into each side's clear span is `URBAN_OWNER_MEASUREMENT_RULE`
  (`URBAN_QTO_TOP_OVER_SUPPORT_EXTENT_V1`). Note 2 states no origin and no span, and does not say whether the length is
  a total or per side.
- **S7-AC02, bottom curtailment.** The 0.125 ratio and the 0.5 / 0.5 density are `PROJECT_SOURCE` (p.15). So are its
  span basis (clear span) and origin (face of support). Two conventions are recorded beside them:
  - the local L along each bar line on an irregular panel (`URBAN_QTO_LOCAL_BAR_LINE_V1`);
  - the AD2-D15 treatment of a continuity-unresolved end.
- On every item these sit in separate fields: `SOURCE_RATIO*`, `SPAN_BASIS*`, `MEASUREMENT_ORIGIN*`, `SOURCE_RULE_IDS`
  and `URBAN_RULE_IDS`. Neither correction changes a quantity.

## Totals (kg)

| subtotal | kg |
|---|---|
| BOTTOM_IN_PANEL_FULL_DENSITY_KG | 155.660 |
| CONTINUING_BOTTOM_KG | 1,191.525 |
| CURTAILED_BOTTOM_KG | 970.457 |
| BOTTOM_SUPPORT_CROSSING_KG | 20.695 |
| **BOTTOM_MAIN_PROJECT_BASIS_KG** | **2,338.337** |
| TOP_EXTENSION_KG | 1,357.973 |
| TOP_SUPPORT_CROSSING_KG | 105.706 |
| **TOP_SUPPORT_PROJECT_BASIS_KG** | **1,463.679** |
| LOCAL_TOP_EXPLICIT_KG | 0.000 |
| SUPPORT_CROSSING_KG (cross-cut: bottom + top crossings) | 126.400 |
| **RESTRICTED_S7_PROJECT_BASIS_KG** | **3,802.015** |

## Floors

| floor | S7 slab area m2 | S7 panels | released components | released items | project-basis kg | blocked components | S8 components |
|---|---|---|---|---|---|---|---|
| GF | 205.988 | 28 | 180 | 283 | 2,162.772 | 96 | 1 |
| 1F | 119.631 | 14 | 96 | 145 | 1,321.202 | 43 | 0 |
| 2F | 31.250 | 5 | 33 | 48 | 318.041 | 17 | 17 |
| ALL | 356.869 | 47 | 309 | 476 | 3,802.015 | 156 | 18 |

## Diameters

| diameter | kg/m | equivalent length m | kg | share |
|---|---|---|---|---|
| Ø10 | 0.617284 | 6,056.071 | 3,738.315 | 98.32 % |
| Ø12 | 0.888889 | 71.662 | 63.700 | 1.68 % |

## Not quantified (02_S7_BLOCKED_ITEMS.csv, no kg)

| category | items | components with such a portion | components with no kg at all |
|---|---|---|---|
| ANCHORAGE_END_COVER | 174 | 160 | 7 |
| BEARING_WALL_CANDIDATE_SUPPORT | 7 | 7 | 7 |
| CONTINUITY_UNRESOLVED | 152 | 116 | 0 |
| EDGE_WITHOUT_SUPPORT_RECORD | 24 | 24 | 24 |
| EXPLICIT_COUNT_LENGTH_BLOCKED | 5 | 5 | 5 |
| OBLIQUE_SUPPORT | 44 | 38 | 2 |
| OPENING_TRIM | 6 | 6 | 6 |
| S8_SPECIAL_STRUCTURE | 47 | 39 | 18 |
| SOURCE_CONFLICT_FAMILY | 5 | 5 | 5 |
| SUNKEN_EXTRA | 18 | 18 | 18 |
| SUNKEN_LEVEL_CHANGE_CONTINUITY | 90 | 54 | 0 |
| TEMPERATURE | 94 | 94 | 94 |
| TRANSITION_LAP_SPLICE | 74 | 54 | 0 |

- **Temperature steel** (160 mm and 180 mm): no exact table row, no interpolation, so it stays blocked.
- **Sunken panels:** the six base meshes are included. The step bars, edge extras and level-change details are
  blocked.
- **S8:** the water-tank panels 2F-01 and 2F-02, the GF-21 light well (its source conflict preserved) and the
  dome / stair-flight sides are all excluded.
- **Voids:** the three voids beside S7 panels have no trim or diagonal bars in the source, so those bars are blocked
  (§20).
- `11_S7_1_CANDIDATES.csv` lists 106 blocked items whose geometry is already fixed by the strips
  and that one owner or source decision would make quantity-ready. They carry 0 kg here.

## Files

| file | content |
|---|---|
| 01_S7_RELEASE_ITEMS.csv | the 476 mass-bearing items, with full formula, authorities, rules and blocked complements |
| 02_S7_BLOCKED_ITEMS.csv | every blocked, excluded (S8) and conflicting portion, and the §20 opening trims; no kg |
| 03_S7_COMPONENT_SUMMARY.csv | every PRE-S7 / AD2 component (and the §20 rows) with its S7 terminal lane |
| 04_S7_BAR_RUNS.csv | strip-level runs of every released item (width, run, boundaries, contribution, kg) |
| 05_S7_PANEL_SUMMARY.csv | every census panel: scope, area, panel-owned kg, and the top steel located there |
| 06_S7_SUPPORT_SUMMARY.csv | every support with an item: owned top / crossing kg, override, split, blocked kinds |
| 07_S7_FLOOR_SUMMARY.csv | GF / 1F / 2F and the total |
| 08_S7_DIAMETER_SUMMARY.csv | equivalent length and kg per diameter |
| 09_S7_PROJECT_SUMMARY.json | totals, counts, authority corrections, gates |
| 10_S7_PROVENANCE.jsonl | one record per item, run, blocked item and component |
| 11_S7_1_CANDIDATES.csv | opportunities found in S7, at 0 kg |
| 12_S7_FREEZE_MANIFEST.json | hashes of code, inputs, outputs, decision records and candidate registers |

The rebuild is `python3 -I research/alsenan_slab_rebar_s7/build_s7.py`, and it is byte-identical. S7 was frozen
before any reference was read. The comparison lives only in `post_freeze/`, which this builder neither reads nor
writes.
