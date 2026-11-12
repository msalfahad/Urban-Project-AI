# T-740 paint area rule UP-FIN-PAINT-002 1.0.0 on ARCH_TAKEOFF_V3.0.74 (lane A, research, unwired)

Worker 2, 2026-11-12. Owner rule 2026-11-12 (main chat): "... the difference is with the corners outside maybe only
and lm for windows doors and corners, so the Area is the same"; paint stops at the false ceiling (Q-72 kept); no paint
on tiles. Nothing wired, no candidate line moves, no default changes; wiring is a later hub package.

## Files

- `rules/rulebook/URBAN_COMPANY_RULEBOOK_1.2.0.json` (new version; built by `build_rulebook_1_2_0.py`, `--check`):
  1.1.0 records byte-equal + UP-FIN-PAINT-002 1.0.0 (OWNER_CONFIRMED, level 3). 1.0.0 / 1.1.0 / knowledge 1.7.0
  (UP-FIN-PAINT-001) untouched (hash-pinned in the test). Registered AUTHORED in `tools/m9_rules_manifest.py`;
  `tools/codemap.py` now lists the newest company rulebook in `docs/RULES_INDEX.md` (it listed none before).
- `t740_rules.py`: R-T740-1 `paint_face` / `paint_faces` (HELD stays HELD, AT_MOST when a band / tile part is unknown,
  NO_PAINT_FACE for a wholly tiled face, edges lm beside the m2); R-T740-2 `band`, `opening_band_part`,
  `beam_end_split`; R-T740-3 `allocate`.
- `t740_alsenan.py` -> `out/T740_PAINT_RULE.{json,md}` (inputs sha-pinned: line index V3.0.74, T-292 opening ledger,
  T-709 terms). `tests/t740_paint_area_rule` (18): synthetic villa V740 by hand + development-villa pins.

## Result (m2; every non-excluded FIN.PLASTER / FIN.PAINT line once; census = the board's figures)

| | plaster | engine paint | rule paint (UP-FIN-PAINT-002) | rule - engine |
|---|---|---|---|---|
| total | 1,495.533 .. 1,690.753 | 822.198 .. 927.215 | 841.261 .. 929.205 | +19.062 / +1.990 (+2.32 / +0.21 %) |
| released paint lines (4) | | 217.2081 | 217.20815 | +0.00005 rounding |
| held paint lines (38) | | 604.990 .. 710.006 | 624.052 .. 711.997 | |
| GF | 659.480 .. 822.521 | 326.224 .. 407.438 | 336.268 .. 405.123 | |
| 1F | 654.888 .. 678.321 | 370.157 .. 386.529 | 376.686 .. 390.835 | |
| 2F | 181.165 .. 189.911 | 125.817 .. 133.247 | 128.307 .. 133.247 | |

Gap plaster - engine paint 673.335 (low) / 763.539 (high), allocated 100 %, residual 0.000000 at both ends:

| cause | low | high |
|---|---|---|
| BAND above the false ceiling: dry rooms | 142.294 | 151.807 |
| BAND: wet-room bands above the ceiling (no paint) | 75.315 | 122.008 |
| BAND: stair shaft 2F decor line 0.15 x 12.90 lm + returns 0.015 | 1.950 | 1.950 |
| VOID_NO_CEILING: GF-08 band strip over the void painted in the double-height band (R-T709-1) | -2.505 | -2.654 |
| TILED: wet-wall render under full-height porcelain | 433.319 | 488.437 |
| TILED: 5 returns with wet rooms both sides (not established) | 3.900 | 0 |
| RETURN_RULE_RESTATED: 22 dry returns, engine low end 0 -> rule = plaster | -20.250 | 0 |
| OPENING_BASIS_MISMATCH 1F-11 W17 (paint on the pre-Q-76 outline) | +0.861 | -4.305 |
| OPENING_BASIS_MISMATCH GF-01 W11 + W12 (paint: W12 4.29 low, pre-T-207 basis high) | +0.011 | +2.315 |
| BEAM_END_BELOW_CEILING GF-08 B26 / B27, 2F-01 B15 (beam deeper than the band) | +0.315 | 0 |
| LEDGER_ROUNDING (GF-15, GF-08, 2F-01 0.00005; 1F-13 0.0002 untraced) | +0.00025 | +0.00025 |

(engine - rule terms enter the gap with a minus sign.) Under the rule the difference plaster - paint is the bands + the
tiled faces only; the engine paint differs from that by the four named item causes, all computed from their own ledger
items (geometry from T-292 / T-556), never back-solved from a total except the two stale paint deductions (W17, W11 +
W12), which are read off their paint lines and labelled so.

## Findings / verdict proposals

- F-T740-1 ENGINE_WRONG 1F-11 paint L-cda2d2..: deducts W17 8.74 .. 9.00 (old outline) vs the plaster's Q-76 A bound
  4.4361 .. 9.858: rule 60.601 .. 66.023 vs engine 61.463 .. 61.718 (range too narrow, high end -4.305).
- F-T740-2 ENGINE_WRONG GF-01 paint (extends F-T717-1): rule 36.901 .. 54.611 vs engine 36.912 .. 56.926.
- F-T740-3 BEAM_END_BELOW_CEILING: a beam deeper than the ceiling band hides wall below the ceiling (GF-08 0.155, 2F-01
  0.16 at the low end); the paint lines do not deduct it.
- F-T740-4 READING (not an owner question): door / window returns. Owner words say "the Area is the same" (reading A:
  return paint m2 = return plaster m2, 20.25 fixed + 0 .. 3.90 wet-both-sides); the board paraphrase lists "reveals"
  among the lm items (reading B: 0 m2 + lm). Reported on A, both shown, HELD for the Checker / Lead.
- Exterior: 3 facade lines and 8 fence plaster / paint pairs are HELD blank in the candidate: rule = face by face,
  nothing to restate (Sigma = the exterior plaster area, owner notes 2026-10-21). FIN.PAINT.CEILING (31 released) has no
  plaster soffit line (false ceilings): outside this restatement.
- Released paint unchanged (4 lines agree with the rule to 0.00005).

## Checker re-measure suggestions (3 faces)

1F-04 (false ceiling, 17.40 lm, band 11.136 = 17.40 x 0.64, no part in the band), GF_07 (wet wall: render 32.3422 =
tiled, paint 0) and one exterior face (fence F-STREET outside: plaster / paint pair both blank: confirm no value exists).

## Lessons register row (proposed, ERS s.7)

2026-11-12 | T-740 | paint vs plaster gap | a paint line computed on its own opening ledger drifts from the plaster's
when an opening basis is restated (W17 Q-76, W11 / W12 T-207) | rule: paint = plaster of the same face - band - tiled,
derived from the plaster ledger, never a second opening ledger | test tests/t740_paint_area_rule.
