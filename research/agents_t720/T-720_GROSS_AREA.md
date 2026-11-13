# T-720 gross / covered floor area per storey: missing family B2-03 (lane A, research, unwired)

Worker 2, 2026-11-12. A drawn denominator for every per-m2 check, with an own drawing read and a reconciliation to the
released engine's floor plate; not a verification; nothing wired or released; V2.9 + route G unchanged; no engine, rule /
knowledge version, registry or candidate file touched. Files: `t720_extract.py` (own DXF read by handle + the V2.9 run's
floor areas -> `T720_DRAWN.json`, handles / lengths / areas only), `t720_rules.py` (R-T720-1 .. -5, every villa),
`t720_alsenan.py` (builder, input sha256-pinned, `--check`), `out/T720_GROSS.{json,md}`, `tests/t720_gross_area`
(11 tests). Drawing read this run: Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (decoded by the wrapper
into `.work/private` only) and a V2.9 run on it kept there.

## Physical element (ERS 2.1)

Gross floor area of a storey = plan area inside the outer face of its external envelope (walls, columns on or proud of
the face; the outermost glazing line where glazing is the envelope). Voids, shafts, stair wells inside are named, not
deducted. No municipal convention is applied (none is assumed; a convention would be a separate HELD figure).

## Result (m2; full table in out/T720_GROSS.md)

| storey | own gross (handles) | engine plate V2.9 | named cause | residual |
|---|---|---|---|---|
| GF | house 217.788972 + annex 60.477319 = **278.266291** | 284.1465 | engine closes the side passage (2 PASSAGE thresholds) -5.880 | -0.000209 |
| 1F | **209.839104** | 209.8017 | straight opening B61 / 2FD8 bridged on the face, engine on frame line C37 (80 mm x 0.467) +0.037384 | +0.000020 |
| 2F roof structures | **55.080000** | 55.0800 | none | 0 |
| all storeys | **543.185395** | | | |

Second source: five printed dimensions (A67 15.000, 598 8.300, 5F9 15.970, D87 10.600, 143C 6.770) equal the own
face-to-face distances to < 0.001 mm; the three frames align on 2BC / AC9 / 1274 and 9B / AF3 / 1287 (0 mm).

GF ground (plot 470.550 to the boundary outer face; 192.284 outside the GF envelope): side passage 5.880 beside the gross
(R-T720-4, Q-67 A conditional), 4.080 under the 1F floor, 1.800 HELD (GF-roof panel per Q-67, cited); COVERED_BY_FLOOR
entrance zone 17.480 + pool-court strip / curved bay 8.465 = 25.945; slab projections named without an outline here
(Q-68 pool court 18.393 / VOID 4.373, eaves 6.791): HELD, so OPEN_TO_SKY is HELD (upper bound 160.459), never 0.
1F roof not under the 2F 154.759 (a roof); GF roof not under the 1F 98.452.

## Findings and verdict proposals

1. ENGINE_RIGHT on the plates (F-T720-1): every engine plate equals the own read after one named cause per storey.
2. ENGINE_WRONG, reconciliation only (F-T720-2): the north-arrow block NR1 (inserts 1612 / 19A2 / 19A3) has lines on
   layers 1 / 5 and is read as a second wall network on every plan: plate_top_level and the face categories carry
   0.6581 m2 per plan (1.974 m2) that is not building. No BOQ line uses it today; a future reader of the categories would.
3. RULE_DIFFERENCE (F-T720-3): the engine plate holds the side passage 5.880; Q-67 A keeps it outside. Q-67's 5.64 is
   to the inner face of the boundary wall (1.20 x 4.70); here 5.880 to the outer face line 86 (+1.20 x 0.20).
4. Freelancer: no gross-area row known; not compared. Q-68 porch 19.181 vs the 17.480 under the 1F floor: the 1.701
   difference is the slab beyond the 1F walls (Q-68 reading, not re-read here).

## Missing / uncertain

- Slab projections over the GF ground (pool-court canopy with the V-02 oval, eaves, the GF-roof panel over the passage)
  need their outlines from the structural slab plan: COVERED_BY_SLAB stays HELD.
- Garden band 13.986 inside the GF outer wall line (D-48 designer classification) is inside the gross as drawn.
- The OQ-04 courts (167.714, inside the boundary walls) are not reconciled to the 192.284 outside the envelope here.

## Rules and lessons row (ERS s.7, proposed)

R-T720-1 .. -5 (t720_rules.py). Lessons row: "A bulged LWPOLYLINE glazing (bulge 0.867) drawn on the window layer made the
GF east face a 6.995 m2 concave bay that a straight-line render hides (T-720): read every polyline with its bulges before
judging an outline from a picture (any villa); test `test_normal_curved_external_wall_hand_calc`." Second row: "A north
arrow drawn on the wall layer became a 0.658 m2 wall network on every plan (T-720): a closed figure inside a symbol block
is never floor or wall area (any villa); test `test_symbol_never_floor_area_and_components_add`."
