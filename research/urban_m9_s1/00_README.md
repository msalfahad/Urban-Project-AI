# M9 S1 — General BOQ foundation: rule store, canonical lines, material layouts, room workbook

S1 is the foundation slice that the M9A roadmap proposed, extended by the owner's **M9 S1 addendum** (material
dimensions, waterproofing rolls, minimum-waste porcelain layouts, room-by-room workbook).

S1 is **measurement-neutral** for the structural route:
- `tools/urban_boq_m2.py` and every M2–M8 module are unchanged;
- `urban_boq_m9 run` writes the route G outputs byte for byte, then adds its own outputs in `OUT/m9/`.

Everything here is `MACHINE_ONLY`. The quotation gate stays **INCOMPLETE**. No prices appear anywhere.

## What S1 adds

| Piece | File | What it does |
|---|---|---|
| Rule store | `rules/`, `engine/source/rule_store.py`, `tools/m9_rules_manifest.py` | 1.4.0 is a byte copy of the owner library. 1.5.0 overlays the OWNER_APPROVED records, replacing by `rule_id`. Proposals are ignored unless asked for. Every result names its rule-set version and digest; the manifest catches any drift. |
| Material specifications | `rules/materials/URBAN_MATERIAL_SPECS_1.0.0.json`, `engine/source/material_spec.py` | Default roll 1.00 × 10.00 m with a 0.10 m minimum lap; a stricter data sheet wins, with its source. Tile sizes 120×60, 60×60, 160×80 cm plus custom. Box data is never guessed. |
| Canonical BOQ line | `engine/source/boq_line.py` | `URBAN_CANONICAL_BOQ_LINE_V1`: bilingual, one payable measurement per line, two state axes (evidence / approval). Adapters never raise a state; no price field. Route G items are adapted with their numbers unchanged. |
| Material result | `engine/source/material_result.py` | A cutting plan's material as a view of one line. Each part on its own: net, placed, joint, overlap, consumed, reusable offcuts, cutting waste, waste %, packs, packaging surplus, spare (NOT_SET), procurement. The balance is checked. |
| Tile layout | `engine/source/tile_layout.py` | Rectangle-exact cutting plan per size: orientations × start alignments, guillotine offcut reuse, minimum-waste search under the same constraints for every candidate. The selected size stays primary. |
| Membrane roll plan | `engine/source/membrane_layout.py` | Rectangle-exact: floor strips with side and end laps, upturn band lanes, doorway pieces, whole rolls. Corners and penetrations are counted, never guessed. |
| Room BOQ | `engine/source/room_boq.py` | Room schedule → lines + material results + comparisons + unresolved questions. |
| Coverage census | `engine/source/coverage_census.py` | All 99 BOQ families, each with a terminal run state and its reason. |
| Workbook | `engine/boq_room_workbook.py` | Freelancer-style room-by-room sheets; formula subtotals by room, floor and project. |
| CLI | `tools/urban_boq_m9.py` | `run`, `rooms`, `rooms-check`, `tiles`, `membrane`, `rules`. |
| Tests | `tests/m9_foundation/` | Rule precedence, schema, formulas, balance, workbook reconciliation, conflict pins C01–C24, wrapper no-regression, package hygiene. |

## Files in this folder

| File | Content |
|---|---|
| `01_TILE_COMPARISON_3x2_BATHROOM.md / .csv` | The owner's 3.00 × 2.00 m bathroom in all three sizes, with explicit assumptions. |
| `02_MEMBRANE_ROLL_LAYOUT_EXAMPLE.md / .csv` | The same bathroom on the default roll, roll by roll, plus the M9A fixture WP-1. |
| `03_SYNTHETIC_ROOM_BOQ.md` | The synthetic room schedule's lines, material results and unresolved questions. |
| `04_IMPLEMENTED_VS_FUTURE.md` | What is calculated now versus what is only an interface. |
| `05_S1_REPORT.md` | What worked, what failed, what is incomplete, and recommendations. |
| `SYNTHETIC_ROOMS_S1.json` | The synthetic room schedule (`URBAN_ROOM_INPUT_V1`). |
| `build_examples.py` | Rebuilds 01–03; the package test checks they match byte for byte. |
| `TEST_GATE_M9_S1.json` | The full-suite record. |

The room-by-room workbook (`URBAN_ROOM_BOQ.xlsx`) is generated, never committed. It ships in the S1 ZIP only.

## Run

```
python3 -I tools/urban_boq_m9.py rooms --rooms research/urban_m9_s1/SYNTHETIC_ROOMS_S1.json --out OUT
python3 -I tools/urban_boq_m9.py tiles --length 3 --width 2 --joint 0.002 --min-cut 0.1 --min-reusable 0.1 --selected TILE-120x60
python3 -I tools/urban_boq_m9.py membrane --length 3 --width 2 --door 0.8:0.2 --min-reusable 0.3
python3 -I tools/urban_boq_m9.py run --drawings NEW.dxf --out OUT --route G --conventions engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json [--rooms ROOMS.json]
python3 -I tools/urban_boq_m9.py rules --check
```

The workbook's formulas carry no cached values until a spreadsheet application recalculates them. Excel and
LibreOffice do this on open.
