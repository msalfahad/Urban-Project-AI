# T-709 paint / plaster residuals round 2 on ARCH_TAKEOFF_V3.0.70 (lane A, research, unwired)

Worker 2, 2026-11-11. Candidate of record V3.0.70 (T-693 line index). A RECONCILIATION with own drawing reads, not a
verification: freelancer agreement is never proof; nothing is wired or released; V2.9 + route G unchanged; no engine,
rule / knowledge version, registry or candidate file touched. Files: `t709_extract.py` (own DXF read by handle ->
`T709_DRAWN.json`, lengths / widths / handles only), `t709_rules.py` (R-T709-1 .. -4, every villa), `t709_alsenan.py`
(builder, every input sha256-pinned, `--check`), `out/T709_RESIDUALS.{json,md}` (all tables, 30 return rows by id),
`tests/t709_paint_plaster_residuals` (20 tests). Drawings read this run (Drive "Alsenan chalet project", decoded by the
wrapper into `.work/private` only): P7757_DXF_COMPRESSED.zip (P7757.dxf: GF / 1F / 2F plans by handle) and
p7757_arch_sheet10.pdf (section A-A, raster, looked at only, never scaled).

## (a) The shaft residual 54.00 m2 (his rows 8 and 24, both workbooks)

**Physical element (ERS 2.1).** SHAFT = ST-01, the dog-leg stair beside the lift: four faces W / E (the lift-shaft
wall's stair side) / N / S (GF only), each one face from its lowest floor to the roof soffit (Q-72 owner answer,
T-173 / T-680); the open south side above +5.50 is no face; the lift shaft's own inside is no finish face (no engine
line, not in his rows). Plaster to the roof soffit, paint 0.15 below (Q-48 A). Engine lines unchanged. The 0.20 / 0.10
red outline in the ST-01 well (layer 5, handles 150-157 / A8E-AC4 / 1356-1364, 2.80 .. 3.35 m long on every plan) is the
well handrail / stringer edge: section A-A draws an open railing there, no wall (raster looked at, not scaled), so the
well holds no plastered face.

**His row 8 'stair wall' 11.25 x 3.60 = 40.50 -> IDENTIFIED, not a shaft face.** R-T709-2 binds it to exactly one drawn
run: the ROUND-STAIR (ST-02) WELL WALLS on the 1F plan, west 4.000 (DIMENSION E3E) + south 7.020 (D7B) + the three
column returns proud 0.05 of the south face inside the well (300E x 2, 3008) = **11.170 lm vs his 11.25 (+0.08 lm,
+0.7 %)**. No shaft run matches (W+E 10.40, N+W+E 12.90, GF stair-hall piece 12.30, lobby 4.60). The ST-02 well is the
double-height stairwell over the GF reception (void 5.87 x 4.00; T-184: ST-02 rises +1.00 -> +5.50 round the void);
he prices one storey (his 3.60) above the GF. The engine carries these faces ONCE, in the 1F living line 1F-13
(L-9b4a7bab plaster / L-be48ea84 paint), whose chain 1F-LIV.ours walks 'the void zone walls' (T-606) at the 1F
heights. Verdict: ENGINE_RIGHT on scope; the 40.50 moves out of the shaft bridge into the 1F-13 room comparison (his
three 1F-zone rows 15 + 16 + 8 = 60.85 lm vs the drawn 39.45 lm; T-552 ENGINE_RIGHT on length stands). Whether his
living row 15 also carries the well walls cannot be read from his rows (no outline): named, no engine effect.
SENSITIVITY (for the Checker): the binding uses the column returns; at the bare 4.00 + 7.02 = 11.02 his row is 0.23 m
(2.1 %) over and R-T709-2 would return UNRESOLVED. The physical identification (the only 'stair wall' that runs
through a storey outside the ST-01 box) does not depend on it; the tolerance call does.

**His row 24 (paint row 25) 2.50 x 5.40 = 13.50 -> UNRESOLVED.** Four drawn faces are 2.50 m wide (ST-01 N, ST-01 S
GF, the walls facing the 1F and the 2F arrivals) and all are already carried (shaft lines, 1F-13, 2F-01): length
AMBIGUOUS; no printed level interval of section A-A (+0.30 / +1.00 / +3.50 / +5.34 / +5.50 / +7.516 / +7.684 / +9.70 /
+13.74 / +13.90) is 5.40 +- 0.05. His row cannot be bound to a physical face; never added, never 0 on the engine side.

**Shaft residual: 54.00 UNRESOLVED -> 40.50 IDENTIFIED (ST-02 well, in 1F-13) + 13.50 UNRESOLVED.**

**NEW, ENGINE_OMISSION (small): the double-height band on the ST-02 well's south wall (R-T709-1).** Read by handle:
the 1F south face AEC runs the whole 7.020 well zone; on the GF, in the same plane (offset 0.0 mm, frames aligned on
the ST-02 arcs 23E / BA1), the wall is SOLID only over 3.997 m (wall face 336 2.650 + columns 2FD2 0.800 / 2FC6 0.547);
the other 3.020 m is the overhead line A8 over the curb / garden opening (no wall below: the 1F wall sits on a beam).
GF-08 stops at its soffit (+1.00 + 4.29 = +5.29, T-556) for plaster and at its ceiling (+1.00 + 3.65 = +4.65, G1) for
paint; 1F-13 starts at the 1F floor +5.50. In a stairwell there is no slab or ceiling between: the band is built and
finished (Q-72 owner answer, continuous exposed height through a stairwell).

| band | levels | m2 | status |
|---|---|---|---|
| plaster | +5.29 .. +5.50 over 3.997 m | **0.839 .. 0.871** (high adds the 0.15 lm of column returns) | BOUNDED, drawing-derived |
| paint | +4.65 .. +5.50 over 3.997 m | **3.345 .. 3.525** (low takes the ST-02 corner landing +4.696 over <= 1.15 m; high adds the returns) | BOUNDED |
| beam faces | south 3.020 lm, west 4.000 lm, below +5.50 | HELD by name (beam depth under the 1F well walls: structural GF roof slab plan, not read) | HELD, never 0 |

Named uncertainty: the band assumes GF-08 (T-147 region, face 53.188) carries the 336 face up to +5.29 / +4.65; the
T-612 gross chain runs to the facade 104 with 336 as an inside solid. If the T-147 region does not carry 336, the
omission is larger (3.997 x 4.29 plaster): lane I / the Checker to confirm against the T-147 region before wiring.

## (b) Returns -8.19 m2 -> RESOLVED (R-T709-3)

Element: a door return = the plastered faces inside the wall thickness, t x (2 x head + width) per door (T-634 re-read
26 by handle; OP-009 by T-676). His row 26: 14 doors x 0.20 x 5.70 = 15.96. Engine: 27 valued lines 24.150 (+3 blank
HELD: A-GF-01, A-1F-01, D-GF-15). Gap -8.190 closes exactly in two causes, both orders shown:

| cause | m2 (range over the two orders) | verdict |
|---|---|---|
| COUNT: he prices 14 doors; the drawings carry 27 returns; his own deduction list (row 44) counts 26 internal doors | -14.820 .. -11.628 | FREELANCER omission (ENGINE_RIGHT) |
| UNIT: his flat 0.20 x 5.70 = 1.140 per door vs the drawn mean 0.894 (19 of 26 doors in 0.15 walls; heads 2.20 Q-55 C / 2.50) | +3.438 .. +6.630 | RULE_DIFFERENCE |

The split depends on the order; the total does not. No engine change.

## (c) T-569 return paint, wiring form on V3.0.70 line ids (R-T709-4)

30 FIN.PAINT return rows keyed by the plaster face id (table in `out/T709_RESIDUALS.md`): 27 HELD with bound 0 .. the
face's plaster m2 (sum **0 .. 24.150**), 3 HELD by name (blank plaster returns). Since V8 one face changed: OP-009
(GF external door reveal) HELD -> RELEASED 1.08 (T-676), so it now carries a bound. 5 rows (1F OP-010, GF OP-017 /
OP-018, GF reveals D-GF-02 / D-GF-10: wet rooms both sides, T-634) are flagged NOT_ESTABLISHED (one finish per face,
R-T701-3). T-701's 'physically painted 19.17 .. 20.25' is the high end without those 5 doors, with / without OP-009.
The low end stays 0 until the frame-covered jamb depth is printed (frame / casing detail): a DESIGNER datum, not an
owner question. Never a value, never folded into a released paint line; gate B (lane I).

## (d) The 9 dry rooms not re-measured in T-701

Own re-read by handle (merged chains T-606 / T-612 / T-621, R-T606-1 outline with column notches; every gap on every
straight wall edge, window-framed or not), against the T-556 ledger:

| room | face lm (engine) | drawn - engine | openings (drawn gap -> ledger) | verdict |
|---|---|---|---|---|
| GF-01 | 20.127 | +0.0009 | D-GF-01 AGREE, A-GF-01 HELD (no height), W11 AGREE, **W12 DIFFERS** | LENGTH ENGINE_RIGHT; HEIGHT / DEDUCTIONS RULE_DIFFERENCE |
| GF-15 | 21.537 | -0.0025 | D-GF-13, D-GF-14 AGREE; W03 arc (T-634) | as above |
| 1F-01 | 17.700 | 0.0000 | D-1F-01, D-1F-02, W14 AGREE | as above |
| 1F-10 | 16.200 | 0.0000 | D-1F-08 AGREE, A-1F-01 HELD | as above (his +6.10 lm: the two 3.05 m passage walls are in 1F-13) |
| 1F-11 | 22.149 | +0.0017 | D-1F-09, D-1F-10 AGREE; W17 curved HELD | as above |
| 2F-03 | 18.900 | 0.0000 | W29, D-2F-03, D-2F-02 AGREE | lengths equal; HEIGHT / DEDUCTIONS RULE_DIFFERENCE |
| GF-08, 1F-13, 2F-01 | 53.188 / 39.45 / 9.009 | not re-measured | - | open zones: the face is the T-147 region clip; a gross chain is not that face (T-128 r2 stands) |

HEIGHT everywhere: his flat 3.60 / 3.40 / 3.50 vs plaster to the soffit (Q-72) and paint to the finished ceiling (G1,
Q-48 A): RULE_DIFFERENCE (engine on the owner rules). DEDUCTIONS: Q-73 full per room side vs his half list once:
RULE_DIFFERENCE. Per-room bridges (LENGTH / HEIGHT / DEDUCTIONS, both ends) are carried from T-701 into the JSON.

**F-T709-1 (ENGINE_WRONG, below materiality): W12 (GF-01) ledger 4.290 m2 vs drawn 1.95492 x 2.20 = 4.300824**: both
annex windows W11 / W12 have the same drawn gap 1.95492 m; the ledger takes 1.955 for W11 (4.301) and 1.95 for W12.
GF-01 plaster and paint lines are 0.010824 m2 too high (0.02 %); corrected deduction 4.300824 (lane I, with the next
GF-01 restatement; no wiring row of its own).

## Verdict proposals (Checker)

- Shaft 54.00: 40.50 IDENTIFIED (ST-02 well walls in 1F-13, ENGINE_RIGHT on scope), 13.50 UNRESOLVED (his row on no
  face). ENGINE_OMISSION: double-height band plaster 0.839 .. 0.871, paint 3.345 .. 3.525 m2 (+ beam faces HELD).
- Returns -8.19: RESOLVED: count FREELANCER omission, unit RULE_DIFFERENCE. Return paint: HELD 0 .. 24.150 on 30 ids.
- 6 dry rooms DRAWING-CONFIRMED lengths and openings (W12 -0.0108 named); 3 open zones not re-measured.

## Rule, test, lessons row

R-T709-1 double-height continuity band; R-T709-2 reference-row binding (one drawn run within max(0.10 m, 1 %));
R-T709-3 two-order return bridge; R-T709-4 return-paint row per plaster face id. Tests: villa V709 by hand (band 0.90 /
2.40 / 2.35, beam HELD, binding BOUND / AMBIGUOUS / UNRESOLVED, bridge -0.50 in both orders, paint rows) + adverse (mm,
negative, missing level -> HELD, lower top above the upper floor, contacts outside the band, blank / 0 / fractional
count, depth in mm, held return with a value, NaN) + development-villa pins and `--check`.
Lessons row (ERS s.7, proposed): 2026-11-11 | a 54 m2 'shaft' residual sat UNRESOLVED for three rounds | the reference
row was compared against the wrong element (the dog-leg shaft) while it described the OTHER stairwell (the round stair
over a double-height void), and the two room lines on either side of that stairwell each stopped at their own storey |
bind a reference row to a drawn run before calling it unbound (search every stairwell / void, not only the one its
neighbours suggest); a wall through a slab-free zone is one face: the band between the lower line's top and the upper
floor is measured, a beam face under it is HELD with its depth datum (every villa) | tests/t709 | PROPOSED.

## For the Checker (re-measure)

1. ST-02 well run, 1F plan: DIMENSION E3E 4000 (west, corridor edge to the south face), D7B 7020 (south, from the west
   face AF7), columns 300E (234 .. 1034 mm from the well's own frame, proud 50 mm) and 3008 (one return inside the zone)
   -> 11.170 lm; GF in the same plane: 336 (2.650) + 2FD2 0.800 + 2FC6 0.547 = 3.997 m solid, A8 hidden over the rest.
2. Room 1F-11 (random): chain 1F-CUR.ours, perimeter 22.15067 vs face 22.149; gaps 0.9 (D-1F-09) and 0.8 (D-1F-10).

Missing / held: his row 24 by id; the beam depth under the 1F well walls; the frame-covered jamb depth; the T-147
region's carriage of the 336 face; the three open zones' own re-measure; roof datum D-39 (heights of the 1F / 2F rows).
