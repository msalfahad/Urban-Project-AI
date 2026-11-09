# T-622 B4 wet-room wall tile: the 47 UNKNOWN rows re-measured from the drawing (research, unwired)

Worker 2 (lane A), 2026-11-08, claim 08:43 UTC. Files: `t622_rules.py` (R-T622-1, every villa), `t622_extract.py`
(drawing read by handle), `T622_DRAWN.json` (handles and lengths only), `t622_alsenan.py` (builder),
`out/WALL_TILE_REMEASURE_T622.json`, `tests/t622_wall_tile_remeasure/` (15 tests). No engine module, method, rule /
knowledge version, registry or candidate file changed; no candidate line moves. Drawings by Drive title and handle only
("Alsenan chalet project": P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256 ab54dd55..., sanitary-7757.pdf).

## 1. Physical element and method

Porcelain on the inner faces of each wet room, finished floor to the tile top H (Q-48 A owner formula: GF 3.65,
1F / 2F 3.35, ASSUMED - OWNER-APPROVED G1), net of every opening's part inside the band (Q-73), open sides untiled,
reveals measured separately (Q-73 answer), no paint / skirting on a tiled face (owner 2026-11-02). Faces: the room's
drawn face chain by handle (R-T606-1 / R-T621-1 geometry; the 11 bath / W.C. / laundry chains are T-621's merged
chains, re-measured; the pantry chain AE / A6 / B3 / 158 is new), column returns included, less each open side measured
as its OWN drawn line. Openings: the gap between the layer-1 face pieces on their own chain edge (masonry width), a
window gap must be filled by layer-W frame lines, any undeclared gap on a tiled edge is refused. Heights: doors 2.20
(Q-55 C), 0.60 windows 1.70 / 2.50 (T-201, elevation geometry), W18 0.84 / 3.00 (printed DIMENSIONs 2EEC / 2EFA, read
this run), pantry W09 / W10 1.00 / 2.50 (T-201, section A-A). The sanitary sheet (3 drainage plans) prints no tile
height and no fixed unit that excludes tile (fixtures and floor drains only).

## 2. Result: 47 / 47 rows own value; 42 DRAWING-CONFIRMED, 5 DIFFER (two rooms)

Every face length, opening width and window band in 10 of the 12 rooms agrees with the stated rows within 0.010 m2
(largest CAD noise: GF-16 diagonal corner 7.624665 vs 7.625 m, -0.001173 m2). Two rooms differ:

| Room | Stated (T-312 ledger) | Own (drawing, handles) | Effect |
|---|---|---|---|
| GF-14 wash lobby | contour 9.512 = face 8.267 + open 1.245 | chain 9.498855 (31B 31A 324 318 BE D2 222); open side = threshold line 2DB (layer 2) 1.255652 from wall face 222 to wall end BC; face 8.243203 | line 26.6544 vs own 26.567691: **line +0.086709 m2 too high** (ENGINE_WRONG). Rows 7 open 3.735 -> 3.766956, 8 length -0.036 -> +0.003435 (now TOLERANCE), 9 height -5.37355 -> -5.358082, 11 rounding 0.00015 -> -0.086709 |
| GF-07 open pantry | face 10.491 (T-312 walk, F-T351-1) | box 3.00 x 4.50 (DIMs 5D5 / 5E1): west 4.45 + south 3.00 + north 3.00 + column 2FAE return 0.05 = 10.500; open edge B3 4.50 | own 32.375 vs line 32.3422: **line -0.0328 m2 short** (ENGINE_WRONG); row 46 -32.3422 -> -32.375. F-T351-1 closed by handles |

The T-312 face pieces were T-250 band-run walks (OFF-LINE and WALK-CLASS residual metres); the handle chain closes on
the drawn faces themselves (exact vertex joins), which is why only the two rooms with walked residuals move.

## 3. The UNKNOWN signed delta -44.86380 m2 (reference - engine), split exactly

| Cause | Stated (V10) | Own (this run) |
|---|---|---|
| RULE_DIFFERENCE (height Q-48 A vs his flat 3.00; pantry Q-37 A) | -75.53560 | -75.552613 |
| ENGINE_RIGHT (openings he does not deduct +28.020, Q-73; GF-14 open side +3.766956; drawn lengths -1.045530) | +30.672 | +30.741426 |
| ENGINE_WRONG (GF-14 line +0.086709 high, pantry line 0.0328 short) | 0 | -0.053909 |
| TOLERANCE (per-face rounding / CAD noise) | -0.00020 | +0.001296 |
| **Sum** | **-44.86380** | **-44.86380** |

Room deltas are fixed by the two figures (his cell, the line), so the total is unchanged; the re-measure re-splits it.
Physical engine on the 12 rooms: 340.3038 - 0.086709 + 0.0328 = **340.249891 m2** (if the two lines are corrected by an
integration package; no line moved here). HELD rows (6, 138.39 m2) untouched: GF-02 / 03 / 05 / 06 wait on the annex
tile top (+4.30 roof mark, G2, Q-54 B HOLD; GF-02 also arch A-GF-01 head), GF-10 / GF-11 on the floor level +0.30 or
+1.00 (T-088; GF-11 also doorway P-GF-01 head).

## 4. Verdict proposals, rule, lesson, open items

- GF-14 line: ENGINE_WRONG +0.086709 m2 (face and open side by handle; the wall end BC 0.15 m is a reveal, separate).
- Pantry line: ENGINE_WRONG -0.0328 m2 (drawn faces 10.500 m). All other 42 rows: class unchanged, DRAWING-CONFIRMED.
- R-T622-1 (t622_rules.py): faces from the drawn chain, open sides by their own named line (closing one with the
  nearest wall refused), openings from face gaps, low-wall band and HELD cap, one finish per face (tile + paint refused).
- Lesson proposal (ERS s.7): *an open side is measured on its own drawn line (threshold / step / counter front), never
  as a walk residual; the walk residual hid a 0.0868 m2 line error on GF-14.* Tests: K622 bathroom with a half-height
  wall + window + door (normal), open lobby read at 0 / 37 / 211 deg and mirrored, tile + paint refused (adverse).
- Open: the 1F west bath pair is congruent (same faces / openings): its door / window ids follow T-312; values do not
  depend on the pairing. Window heights other than W18 rest on T-201's drawn readings (not re-read this run).
- Checker: re-measure 1F-07 laundry (52.529), GF-07 pantry (32.3422 -> 32.375) and 2F-02 W.C. (30.255).
