# T-454: B2 plaster material ledger beside candidate V3.0.45 (not in it)

Worker 2, 2026-11-03. New opt-in table `engine/source/plaster_materials_table_v1.py` (PLASTER_MATERIALS_TABLE_V1,
UNWIRED_PRODUCER) + reader `t454_plaster_materials.py` + `out/` + `tests/t454_plaster_materials/`. No candidate, released
(V2.9 + route G), rule, knowledge or registry file changed; no line moves. Inputs sha256-pinned: line index V3.0.45
(T-479, 16920d3c) and the merged T-349 spatter binding (c8da1b8a). Rebuild: `python3 -I research/agents_t454/
t454_plaster_materials.py` (byte-identical; tested).

## Physical elements (ERS s.2.1)
- Dry interior face: spatter (bond coat) -> two-coat cement plaster (first coat + finishing coat) -> paint.
- Wet tiled face: spatter (plasterer) -> levelling render (tiler) -> adhesive + porcelain (UPC-WETWALL-001; the
  candidate wet-room FIN.PLASTER backing line IS this render, T-331 / T-457). No second fixing bed.
- Per layer: area (the candidate line, unchanged) -> mortar m3 = area x thickness -> cement / sand by the mix. Physical
  area, installed mortar and procurement kept apart; no waste or dry-volume purchase factor applied (none sourced).

## Sources (evidence hierarchy)
- Project drawings / specification: no plaster thickness or mix found by any merged task (T-080, T-329, T-335).
- Company rulebook 1.0.0: UPC-CEMENT-LAYERS-METHOD-001 leaves every value null (method only).
- Level 4 documented reference: Kuwait Society of Engineers 'Bayt Al-Omr' (2023), finishing list (Drive: Engineering
  Sources / 01 Kuwait References; text in visual order, digits read reversed and checked on the item numbers):
  item 57 spatter with fine aggregate per the specification (no thickness, no mix); item 60 first coat 1.5 cm; item 62
  second coat 0.5 cm; item 75 wet-wall render under ceramic not less than 1.5 cm. Mix ratio: none.
- Kuwait General Specification 1990: the connector returns only the first 97,008 characters (to ch. 02230), so the
  plastering chapter is not readable (same as T-080). Finishes book (Al-Jund): no text layer.

## Rules
- R-T454-1 class from the merged binding (all INT_DRY_LINE = dry; all INT_WET_* = wet; none / mixed = HELD).
- R-T454-2 area label VERIFIED-NET only for a VERIFIED_WHOLE line (none of the plaster lines), else PROVISIONAL-NET;
  HELD lines HELD with range x thickness as a bound beside; EXCLUDED lines no material.
- R-T454-3 bond coat on every plastered / rendered face, same m2 as the coat above.
- Wall plaster 0.020 m EXACT (ESTIMATED-NET, never VERIFIED); render 0.015 m MINIMUM -> AT_LEAST bound, line HELD (a
  printed minimum is a bound, lessons register 2026-11-02); bond coat thickness HELD; cement / sand / water HELD
  (NEEDS_MIX). 1:4 (Q-78) and 1:3 (Q-53) are never borrowed.

## Result on V3.0.45 (83 plaster lines read: 13 EXCLUDED, 70 in the table)
| layer | released area m2 | lines HELD / unclassified | mortar m3 | cement / sand |
|---|---|---|---|---|
| wall plaster (dry, 25 lines) | 236.3481 PROVISIONAL-NET | 11 HELD (8 with ranges: bounds 0.0216 .. 3.5761 m3 each) | 4.726962 ESTIMATED-NET | HELD |
| levelling render (wet, 12 lines) | 340.3038 PROVISIONAL-NET | 6 HELD | >= 5.104557 (bound, HELD) | HELD |
| bond coat (spatter, 37 lines) | 576.6519 PROVISIONAL-NET | 33 not in sum | HELD (no thickness) | HELD |
| unclassified (16 lines) | 8 reveal lines (3.93 m2 released on 5, 3 HELD) + 8 fence lines HELD | all | HELD | HELD |
Not in scope (named): FIN.EXT.FINISH 3 lines, FIN.STAIR.SOFFIT 2 lines, 120 exterior spatter faces of T-349.

Hand checks (Checker reproduces): 1F_01 dry L-af9621f4 51.415 m2 x 0.020 = 1.028300 m3; 1F-07 wet L-2948639f
52.529 m2 x 0.015 = >= 0.787935 m3; bond coat 576.6519 = 236.3481 + 340.3038 (0.0000 residual).

Mix sensitivity (NOT a quantity; owner Q-53 derivation convention: dry factor 1.33, cement 1,440 kg/m3, 50 kg bag;
per m3 of mortar 1:3 9.576 bags + 0.9975 m3 sand, 1:4 7.661 + 1.064, 1:5 6.384 + 1.108): dry plaster 4.726962 m3 ->
45.27 / 36.21 / 30.18 bags; wet render >= 5.104557 m3 -> >= 48.88 / 39.10 / 32.59 bags. Mortar sensitivity: 0.2363 m3
(dry) and 0.3403 m3 (wet) per mm of thickness.

## Freelancer
Not compared: the material lines of the freelancer workbook were not opened in this run (area lines unchanged; the
plaster areas' freelancer comparison stays with T-317 / T-349). Verdict proposal: UNRESOLVED (mix not sourced).

## Open
- Mix per layer (Q-79). Bond-coat thickness. Water. Purchase factor and waste. Reveal class (8 lines). Exterior render.

Lessons row (proposed): a reference value printed as a minimum ('not less than') gives an AT_LEAST bound beside a HELD
material, never the quantity; a coat thickness from a reference book is level 4 (ESTIMATED-NET) whatever the area's
label (provenance T-454).
