# T-546 B8 wet-room floor waterproofing vs the freelancer, room by room (research, unwired)

Worker 2 (lane A), 2026-11-06, claim 02:43 UTC. Files: `t546_room_table.py` (R-T546-1, any villa), `t546_inputs.py`
(candidate line ids / values, his per-room cells as numbers by sheet row, hand basis; no coordinate, no client name),
`tests/t546_wet_floor_wp_reconcile/` (23 tests, incl. the pantry drawing check on P7757.dxf). No engine module, method,
rule / knowledge version, registry or candidate file changed; no quantity moves. Drawing by Drive title and handle only
("Alsenan chalet project", P7757_DXF_COMPRESSED.zip -> P7757.dxf, decoded this run into .work/private).

## 1. Physical element and the two bases

Element: the membrane on the structural floor of every wet room (UP-WET-001, owner Q-06 A basin-only spaces, Q-30
kitchens, Q-37 A pantry), to the drawn wall / column faces, plus its 0.20 m wall upturn (UP-WP-002 2.0.0, owner Q-03,
walls only Q-35 C). Doorway segments are their own HELD rows (T-310 policy V3, detail not printed); an open edge with no
wall takes a termination, not an upturn (T-303).

**F-T546-1: his sheet is per room.** His waterproofing sheet has 17 room rows (GF 10, 1F 6, roof floor 1), each with
perimeter C, area D, multiplier F = 1, G = C x F, H = D; H39 = SUM = 72.01 m2, G40 = SUM = 144.61. His summary row (H51 =
G43 + G40) labels the upturn unit **m.l**: the multiplier 1 is not a height, **his "upturn" is the room perimeter in lm**,
never m2 (the board's "144.61 m2 (perimeter x 1.00)" is that lm). So the upturn pair reconciles lm against lm: the
engine's own m2 lines / its own rule height 0.20 (named source), never his 1.00.

Candidate: 18 FIN.WP.FLOOR lines (V3.0.57 index = V3.0.58: T-507 moved only roof lines) = **85.575710 m2**. The
scoreboard's 85.621 is V3.0.41 (pantry 13.500 before T-310's column ruling): 85.620710 = 85.575710 + 0.045.

## 2. Floor: engine 85.575710 - freelancer 72.010 = +13.565710 m2 (+18.84 %), exact, residual 0

| Room | engine | his | delta | cause |
|---|---|---|---|---|
| GF pantry (Q-37 A wet) | 13.455 | - | +13.455 | RULE_DIFFERENCE: owner wets the pantry; he keeps it in his dry reception row (T-153). 4.50 x 3.00 - column 2FAE edge 0.900 x 0.050, re-read this run |
| GF basin space by the stair | 1.485 | 1.70 | -0.215 | RULE_DIFFERENCE -0.220 (his 1.55 x 1.10 takes the 0.20 passage reveal = threshold piece UP-WP-003) + TOLERANCE 0.005 |
| 1F laundry | 10.151 | 10.00 | +0.151 | ENGINE_RIGHT (printed 347 x 300 / 185 less the W.C. corner; his typed) |
| GF kitchen | 9.630001 | 9.55 | +0.080001 | ENGINE_RIGHT (300 x 270 + 105 x 150 - piers 0.045) |
| GF core W.C. 245 x 167 | 2.36761 | 2.30 | +0.06761 | ENGINE_RIGHT (wedge, shoelace on drawn faces) |
| 1F W.C. by the laundry | 2.646 | 2.59 | +0.056 | ENGINE_RIGHT (printed 180 x 147; his 1.80 x 1.44) |
| 2F roof-floor W.C. | 5.55 | 5.62 | -0.070 | ENGINE_RIGHT (printed 300 x 185; his 1.875) |
| 1F west baths A / B | 5.0225 x 2 | 5.00 x 2 | +0.045 | ENGINE_RIGHT (printed 245 x 205) |
| 1F bath by the laundry | 3.5775 | 3.60 | -0.0225 | ENGINE_RIGHT (drawn jamb 0.45 x 0.05) |
| GF master bath | 3.717683 | 3.70 | +0.017683 | ENGINE_RIGHT (diagonal-wall corner 0.483) |
| GF wash by the reception room | 3.1325 | 3.15 | -0.0175 | ENGINE_RIGHT (column corner; column is not floor, T-310) |
| 5 rooms (lobby wash, core W.C. 289, stair W.C., W.C. by reception, 1F east bath) | | | +0.018416 | TOLERANCE (his 2-dp truncation, each < 0.010) |
| GF driver W.C. | 1.95 | 1.95 | 0 | AGREE |

By class: RULE_DIFFERENCE +13.235 (pantry +13.455, reveal -0.220), ENGINE_RIGHT +0.307294, TOLERANCE +0.023416,
UNRESOLVED 0. Without the pantry (like for like, 17 rooms): +0.110710 m2 (+0.15 %), of which -0.220 is the reveal.
On V3.0.41: +13.610710 = the above + 0.045 ENGINE_WRONG (pantry column, fixed by T-310).

## 3. Upturn, in lm: engine 126.072925 (25.214585 m2 / 0.20) - his 144.61 = -18.537075 lm (-12.82 %), exact

| Component | lm | class | basis |
|---|---|---|---|
| doorway segments, 17 x 0.80 + kitchen 1.00 + laundry 0.90, per room side | -15.500 | HELD (own rows, detail not printed) | UP-WP-002 2.0.0 / T-310 policy V3 |
| open edges without wall: lobby to stair hall 1.256, basin to passage 0.90, arch to reception room 1.00 | -3.156 | RULE_DIFFERENCE (Q-35 C walls only; termination) | T-303 / T-074 |
| basin space: his perimeter takes the reveal (2 x 0.20) | -0.400 | RULE_DIFFERENCE | T-074 |
| his perimeters shorter than the printed / drawn faces (kitchen 0.15, W.C. 245 0.1098, 1F west B 0.10, laundry 0.09, W.C. laundry 0.06, master 0.0245, driver 0.02, W.C. 289 0.014; roof W.C. -0.05) | +0.5183 | ENGINE_RIGHT | T-074 hand boundaries |
| lobby 2-dp + engine run vs hand boundary less segments (T-303 item 6, door block width) | +0.000625 | TOLERANCE | |
| pantry upturn | HELD, outside both totals | HELD (open side 4.49, door not bound) | T-303 / T-310 |

Our upturn m2 (25.214585) stays UNIT_MISMATCH against his lm in the m2 pair; the lm pair above is the reconciliation.

## 4. Verdict proposals (Checker)
- Wet floor pair: RULE_DIFFERENCE (pantry, Q-37 A) for 99.2 % of the gap; 10 rooms ENGINE_RIGHT by printed size; 0
  FREELANCER_RIGHT; 0 UNRESOLVED. Basin reveal: RULE_DIFFERENCE (threshold piece, not floor).
- Upturn pair: restate as lm vs lm (-12.82 %): doorways HELD 15.50 + open edges 3.156 + reveal 0.40 by rule; 0.5183
  ENGINE_RIGHT; residual 0.

## 5. Rule, lesson, what is missing
R-T546-1 (module docstring): a per-room freelancer sheet is reconciled room by room; scope rows need a named cause;
TOLERANCE only < 0.010; HELD never 0 and never against his cell; his multiplier is a height only when his summary unit
is m2. Lesson proposal: read the freelancer's summary unit before naming a pair UNIT_MISMATCH (his 'height 1' was a
multiplier for lm). Missing: the doorway transition detail (15.50 lm HELD), the pantry upturn and door, a second
independent re-measure of the 17 rooms this run (values rest on T-074 + T-010 verifier; only the pantry was re-read).
