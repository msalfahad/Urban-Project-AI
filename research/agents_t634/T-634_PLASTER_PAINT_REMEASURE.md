# T-634 B5 internal plaster + B6 internal paint: the 31 UNKNOWN rows re-measured from the drawing (research, unwired)

Worker 2 (lane A), 2026-11-08, claim 18:40 UTC. Files: `t634_rules.py` (R-T634-1, every villa), `t634_extract.py`
(drawing read by handle), `T634_DRAWN.json` (handles, lengths, widths, wall thicknesses only), `t634_alsenan.py`
(builder, `--check` rebuilds byte-identical), `out/T634_PLASTER_PAINT_REMEASURE.json`, `tests/t634/` (25 tests). No
engine module, method, rule / knowledge version, registry or candidate file changed; no candidate line moves. Drawing
by Drive title and handle only ("Alsenan chalet project": P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256 ab54dd55...).

## 1. Physical element and method

Two layers on one dry face, never mixed (Q-72): the plaster coat to the structural slab / roof underside and the paint
film to the finished ceiling (owner G1 3.65 GF / 3.35 1F, 2F, Q-48 A). Wet faces (owner 2026-11-02) carry no paint.
Faces = the room's drawn chain by handle (T-621 / T-606 merged chains, re-measured; arc at true length, column notches
included). Openings = the gap between the layer-1 face pieces on their own edge (window gaps must be framed by layer
W); the GF master bed room's curved glazing W03 = the layer-W face 27D (0.091681 + arc 5.010179 = 5.10186 m). Door
heads 2.20 (Q-55 C, ASSUMED - OWNER-APPROVED); W03 4.30, W14 1.40 / 3.00 (printed, T-175 / T-627), W24 / W29 1.00 /
2.50 (T-627 drawn outlines), D-GF-07 2.00 x 2.50 (printed). Door returns t x (2 head + w): the DXF draws no jamb cap
(the leaf is a block), so t = the offset of the opposite face piece ending at the same station (both jambs agree).

## 2. Result: 31 / 31 rows own value; 29 DRAWING-CONFIRMED, 2 DIFFER (one cause)

| Room | Face own / engine (lm) | Openings own / stated (m2 at G1) | Own paint net vs line | Q-72 plaster own vs T-556 |
|---|---|---|---|---|
| GF-15 | 21.534454 / 21.537 (chain 2B5 27D 2E2 2E0 319 2E7 2DE) | 22.581789 / 22.59695 (W03 drawn 5.10186 vs 5.106) | 56.018968 vs 56.0131 (line -0.005868, TOLERANCE) | 66.535828 vs 66.52899 (+0.006838; HELD on the roof build-up, T-556) |
| 1F-01 | 17.700 / 17.7 (C2A C1F C24 B40) | 7.879638 / 7.880 | 51.415362 vs 51.415 | 62.573362 .. 62.607362 (beam end B6) vs 62.573 .. 62.607 |
| 1F-04 | 17.400 / 17.4 (AE6 AF8 AE9 C1E) | 6.288480 / 6.285 (W24 gap 1.55232) | 52.001520 vs 52.005 (line +0.00348) | 63.137520 vs 63.141 |
| 2F-03 | 18.900 / 18.9 (1284 1292 1279 128B) | 5.540 / 5.540 | 57.775 = line | 69.775 = T-556 |
| GF-02 (wet, his dry rows) | 7.200 (11F 12B 118 12E) | - (paint refused, wet face) | - | - |

DIFFERS: the GF-15 opening row in both sections, own 22.581789 vs stated 22.59695 = **-0.015161 m2**: W03's room-side
glazing face is 5.10186 m on the drawing vs the 5.106 of the T-175 / T-292 ledger (-0.00414 m x 3.65). The face is
shorter by almost the same amount (-0.002546 lm), so the released line itself is within tolerance (own net 0.005868
above it). Every other row agrees within 0.010 m2 (largest 0.00348, W24 drawn 1.55232 vs 1.55).

Returns, all 26 valued doors re-read by handle (widths and wall thickness 0.15 / 0.20, both jambs): own 23.069556 vs
engine 23.07 (-0.000444: D-GF-10 drawn 0.797039 vs 0.80). Shaft residual 54.00: his two rows (2.50 x 5.40 + 11.25 x
3.60) still match no drawn face; the GF stair-hall / lobby outlines re-read (12.3 / 4.6 lm) lie inside the T-173 box.

## 3. Signed split (reference - engine), exact

Plaster UNKNOWN +112.3419 = own rows 112.339594 + room line residuals 0.002750 + return line residual -0.000444.
Paint UNKNOWN +135.4119 = own rows 135.409150 + line residuals 0.002750. Classes unchanged: RULE_DIFFERENCE (openings
he does not deduct, his flat heights, his wet wash row), ENGINE_RIGHT (lengths), ENGINE_WRONG (plaster height basis,
T-552 / T-556; paint returns omitted, T-569), UNRESOLVED (shaft 54.00, returns -7.11). HELD rows untouched (24 / 25).

## 4. Verdict proposals, rule, lesson, open items

- All 4 released dry lines: face lengths and openings DRAWING-CONFIRMED (TOLERANCE <= 0.0059 m2 per line); W03 width
  ENGINE_WRONG by -0.00414 m in the opening ledger only (no line effect beyond tolerance).
- Paint returns (T-569 omission 23.07): physically 19.17 .. 23.07 m2: 5 doors with WET rooms on both sides (D-1F-06,
  D-GF-02, D-GF-10, D-GF-11, D-GF-12, 3.899556 m2) meet tiled faces, where paint is not established (one finish per
  face); the plaster (render) return stays on all 26. Flag for the T-569 wiring.
- R-T634-1: plaster carries SLAB_SOFFIT, paint FINISHED_CEILING, each refused on the other basis; paint on a wet face
  refused; returns t x (2 head + w) with no head = HELD; exact row split.
- Lesson proposal (ERS s.7): *a door's wall thickness is read from the two face pieces ending at the jamb station when
  the drawing draws no jamb cap; and a curved glazing face is measured on its own layer, not taken from a ledger
  width.* Tests: P634 room with door, window and one tiled wall (normal), basis swaps / paint on tile / headless
  opening (adverse), outline at 0 / 37 / 211 deg and mirrored.
- Open: the shaft residual and the return residual need his rows by id (not a drawing question). Checker: re-measure
  1F-04 (dry) and GF-02 (wet face 7.20).
