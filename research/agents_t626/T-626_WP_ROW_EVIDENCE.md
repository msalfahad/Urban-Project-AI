# T-626 B8 waterproofing rows to drawing evidence (research, unwired)

Worker 2 (lane A), 2026-11-08, claim 12:40 UTC, run session_01E6cPnevDQYZYGUw6ktmHcx. Files: `t626_extract.py`
(drawing read by handle -> `T626_DRAWN.json`), `t626_rules.py` (R-T626-1, any villa), `t626_alsenan.py` (builder ->
`out/T626_ROW_EVIDENCE.json` / `.md`), `tests/t626_wet_roof_wp_evidence/` (18 tests). No engine module, method, rule /
knowledge version, registry, candidate or statement file changed; no quantity moves. Drawing by Drive title and handle
only ("Alsenan chalet project", P7757_DXF_COMPRESSED.zip -> P7757.dxf, decoded this run into .work/private).

## 1. Physical element
The membrane laid on each wet-room structural floor to the drawn wall / column faces (UP-WP-001 .. 005), and on each
roof field inside the inner parapet / wall faces less skylight openings (UP-WP-ROOF-001, Q-24 / Q-29); upturns and laps
are separate quantities and not in these m2 rows.

## 2. Wet-room floor: 18 / 18 rows DRAWING_CONFIRMED (statement T-546/floor, 72.01 vs 85.57571 m2, -13.56571)
- Own outline per room by handle (R-T606-1 geometry): 16 T-621 chains re-measured this run, 2 new chains: driver's
  W.C. 112 / 134 / 14E / 132 = 1.950 (printed 658 1.50 x 61E 1.30); pantry A6 / B3 (open east edge, layer 5) / 158 /
  AF = 13.455 (printed 5D5 3.00 x 5E1 4.50 less column 2FAE notch 0.045).
- Own total 85.575708 vs engine 85.575710: the engine's two 0.000001 polygons (W.C. 245 wedge, kitchen); every room
  own = engine within 0.000001.
- Second, independent read from printed DIMENSIONs whose definition points lie on the outline: 11 rooms (10
  rectangles + kitchen 523 x 635 + 641 x (605 - 635) - 0.045 = 9.630) agree to 0.000000; 7 rooms (lobby wash, basin
  space, master bath, two wedge W.C.s, wash by the reception room, laundry) are chain-only, printed sides listed.
- Wet basis per room: sanitary drawing fixtures (T-074) or owner rule (pantry Q-37 A); a label alone is refused.
- Classes unchanged: RULE_DIFFERENCE -13.235 (pantry -13.455 PIECE; basin reveal +0.22 PIECE from DIM 70F x 672),
  ENGINE_RIGHT -0.307294, TOLERANCE -0.023416; re-adds exactly.

## 3. Roof membrane: 5 / 6 rows DRAWING_CONFIRMED, 1 DIFFERS (statement T-541/membrane, 285 vs 209.65844, +75.34156)
| row | delta (ref - engine) | own read | evidence |
|---|---|---|---|
| top roof +13.90 (HELD, Q-34) | +34.390242 | inner faces 12B7 / 1292 / 1279 / 1283 7.700 x 6.450 = 49.665 - dome 1300 | DRAWING_CONFIRMED, class stays HELD |
| third dome 1300 | +15.274758 | r 2.205018498, pi r^2 | DRAWING_CONFIRMED |
| two +9.70 domes 12EB / 2F33 | +30.718026 | r 2.211091524 each | DRAWING_CONFIRMED |
| engine dome chords | -0.018026 | engine deduction 30.700 - own circles | DRAWING_CONFIRMED |
| pool court + ledge | -5.546440 | T-486 / T-494 net 4.906867 + T-529 own ledge 0.639575 (re-run) | DRAWING_CONFIRMED (0.000002) |
| RESIDUAL | +0.523 | 285 - own (32.721 + 55.560332 + 146.532 + 49.665) = 0.521668 | **DIFFERS 0.001332** |

**Finding F-T626-1:** the +4.30 annex roof line L-d57d2dc2 carries 55.559 m2; its own exact-arc area (T-321 handles,
corner arc B2B integrated) is 55.560332: the engine samples the arc (chord loss 0.001332 m2, 0.0024 %). Proposed
statement split of the residual: TOLERANCE +0.001332 (engine arc discretisation, B2B) + UNRESOLVED 0.521668; both
parts DRAWING_CONFIRMED; sum exact 0.523. Not an ENGINE_WRONG worth a fix (below 0.01 m2).

## 4. Verdict proposals (Checker)
Floor: all 18 classes stand (pantry RULE_DIFFERENCE Q-37 A; 10 rooms ENGINE_RIGHT by printed size); 0 FREELANCER_RIGHT.
Roof: classes stand; residual split as above; top roof HELD (Q-34), drawing bound 34.390242 m2.
Checker re-measure suggestion (3 largest): pantry 13.455, +9.70 domes 30.718026, top roof bound 34.390242.

## 5. Rule, lesson, missing
R-T626-1 (module docstring): wet only on fixtures or an owner rule; laid area to faces incl. room bays (shower
recess), less inside openings only, circles exact; residual split into named READING parts. Lesson proposal: a
residual row must be rebuilt from OWN areas, not engine lines: an engine arc-sampling loss hid inside 'UNRESOLVED'.
Missing: upturns not re-measured (lm, outside this m2 package); 7 wet rooms rest on one read (chain); the pool-court
reads re-run merged readers rather than a third method; the residual 0.521668 m2 stays UNRESOLVED (his lump row).
