# T-597 B1 earthworks plan side (T-589 pack P13): pits, pool envelope, exterior ground-beam trench

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-07, branch `agents/task-T-597`. Research only: no engine
module, candidate line, released line, rule file or method version changed; nothing released. Development villa, not
an accuracy claim. ERS s.2 - 4 and s.7 applied; owner earthworks sessions 2026-11-02 17:20 / 17:45 / 18:00, Q-21 C,
R-EXC-LEDGER-1, R-T497-1, defect L-N10-03.

## 0. Sources and run

- Drive "Alsenan chalet project" / "ST7757 dxf.dxf", downloaded this run, decoded into `.work/private` only, sha256
  9f9d1179 (= the route G input). Read by layer and handle by `t597_alsenan.py` (own reader; no engine route, no
  earlier ledger read for geometry). Printed values cited, not re-read: ST p.13 blinding projection 0.10 each side
  (T-170 / T-206), p.7 pool screed 5 cm + membrane 5 cm (T-183 r2). Exterior-beam CLASS (which pieces are main
  exterior) taken from the T-253 ledger by piece number; the piece geometry is read here.
- Code: `pit_union_v1.py` (PIT_UNION_V1, R-T597-1 .. 4, every villa), `t597_alsenan.py` -> `out/T597_PLAN_SIDE.json`
  (handles, sizes, m2 only). Tests: `tests/t597_pit_union` (16).
- Run: `.work/venv/bin/python -I research/agents_t597/t597_alsenan.py .work/private/st7757.dxf`.

## 1. The physical element (ERS s.2.1)

The excavated footprint at formation, per zone. Pit = footing outline grown 0.10 on every side (the blinding slab,
straight edges, square corners). Pool envelope = outer RC shell grown 0.10 (screed + membrane wrap the shell: a
rounded offset). Exterior trench = beam band + 0.10 each side, 0.10 deep below EG (beam bottom on N.G., T-253), owned
only where no earlier (deeper) zone digs (R-T497-1). The depth is not measured here: the pits stay on S01 ESTIMATED.

## 2. Pits: 24 / 24 re-measured (16 new this run)

| Measure | Value (m2) | Note |
|---|---|---|
| outlines found / schedule sizes agree | 24 / 24 | FT / FTB W x H; 3 labels by nearest text (166A 0.003 m, 1667 0.128 m, 10F8 0.445 m), sizes confirm the type |
| 16 pits not checked before (F2 x2, F3 x2, F4 x2, F5 x2, F x4, FN x4) | 46.42 | no overlap among them |
| sum of 24 neat pits | 129.570000 | |
| union (one dig per overlap) | 129.234375 | overlap 0.335625 = F9 / FN 180C 0.330 + F8 / FN 10F0 0.005625 |
| beyond the plot line | 1.890000 | 8 boundary pits (F x3, F11, F14, F15, F8, FN 1100); HELD with S06 / D-14 |
| in plot | 127.344375 | |
| given to the pool envelope (exact arc) | 2.695761 | F8 1.931845, F4 0.735358, FN 180C 0.028558 (by integral) |
| **zone plan, owned** | **124.648614** | engine 124.649555: **-0.000941 m2** |

Union vs sum is the L-N10-03 defect: a summed plan (129.57) would count 0.335625 m2 of soil twice; the engine already
unites (T-350 r2), confirmed.

## 3. Pool envelope

Shell 7C6 (beams-plan frame, +38 724.4 mm, the plot rectangles 7FE / 1658): 3.50 x 1.75 + half circle r 1.75 =
10.935563 m2, perimeter 12.497787 m; the 3.50 back face lies ON the plot line. In plot: A + (P - 3.50) x 0.10 +
pi/2 x 0.10^2 = **11.851050 m2** (engine 11.851051: rounding); beyond 0.365708 HELD. x printed -1.50 = 17.776574 m3
(engine 17.776576, -0.000002 rounding).

## 4. Exterior main ground-beam trench

17 pieces read from the layer-1 edge pairs, split at the S-COL.BON columns: every straight piece length = the T-253
length (dL 0.000 on 16); the arc 157 / 158 piece 5.9658 m (T-253 6.0873, -0.1215: the common angular span 109.75 ..
259.84 deg cut at the columns; T-484 read the same 5.9658). Strip 27.937534 m2 (T-484 27.919513, +0.018: junction
handling), given to pits 14.497860, F10F drawn outline 1.675, pool 0, FF 0. **Owned: 10.692674 in plot + 1.072000
beyond = 1.069267 .. 1.176467 m3** (engine 1.069269 .. 1.176467: AGREE, 2e-6). Junction squares (beam faces drawn to
different ends) change the strip by +0.05 m2 but the owned trench by 0.000000: they lie inside pits.

## 5. Reconciliation in units (ERS s.2.4)

Pits zone plan, engine - own = +0.000941 m2 = the pits' share given to the pool envelope (2.694820 engine vs 2.695761
exact). Cause: the engine's envelope is a polygonised buffer (chords inscribed in the arc, `envelope_convergence` in
the output: quad_segs 16 -> 2.690714, 64 -> 2.695442, 4096 -> 2.695761 = the integral). Residual 0. At S01 1.67 m:
-0.001572 m3 (208.164757 -> 208.163185), and the pits backfill moves by the same -0.001572 (immaterial, -0.00075 %).

## 6. B1 rows (depth untouched)

| Row | Plan | Plan status | Depth |
|---|---|---|---|
| B1-02 Z1-PITS-24 | 124.648614 m2 | DESIGNER -> plan DRAWING-CONFIRMED | HELD by name: S01 ESTIMATED (RFI-S01, Q-21 C) |
| B1-02 Z1-POOL | 11.851050 m2 | DRAWING-CONFIRMED (re-measured) | printed -1.50 |
| B1-02 Z1-TRENCH-EXT-GB-MAIN | 10.692674 + 1.072 m2 | CLOSABLE -> plan DRAWING-CONFIRMED (class T-253) | 0.10 printed; beyond-plot HELD S06 / D-14 |
| B1-02 Z1-PIT-FF | footprint 20.70 only | neat plan HELD (p.14 projection undimensioned) | HELD D-43 |
| B1-02 Z1-PIT-F10F | none | HELD (open outline 1B1B, Q-31 C) | HELD |

Unchanged: annex / court / straps / boundary / D-33 / ZERO / lower GB row (sections or soffits not printed), every
B1-03 / B1-04 row; the 3 OWNER_RULE_GAP rows (B1-03 ext trench, B1-03 pool, B1-04) keep their owner rulings.

## 7. Who is right

His BOQ has no earthworks row (T-565: NO_ROW, 885 rows searched): no comparison. Engine vs own re-measure: pits plan
ENGINE_WRONG by 0.000941 m2 (arc polygonisation, immaterial; proposed fix in the next lane I candidate round: exact
arc / converged buffer); pool and trench AGREE.

## 8. Rules, test, lessons row (proposed)

R-T597-1 .. 4 in `pit_union_v1.py` (printed projection or HELD; union, never sum; plot clip stated apart; dig-order
ownership with closure). R-T597-5 (every villa): an area bounded by an arc is computed exactly (sector / segment
integral, Steiner offset) or by a buffer shown converged to 1e-6 m2; a coarse buffer is never the value.

| 2026-11-07 | pits zone plan 0.000941 m2 above the exact figure | the pool envelope buffered with coarse chords: arc parts inscribed, less given up | curved boundaries exact or converged (R-T597-5); union of pits, overlaps stated (every villa) | tests/t597_pit_union (normal E597 3 pits / 2 overlapping; adverse rotated, mirrored, mm, missing outline / projection HELD, sum refused, coarse buffer short) | PROPOSED |

## 9. Checker re-measure list

- One new pit by hand: F5 166D (2.40 x 2.10 at 144 112.2, 36 948.0) neat 2.60 x 2.30 = 5.98 m2; F4 1666 envelope part
  1.20 x 0.375 + integral 1.475 .. 1.85 of sqrt(1.85^2 - t^2) = 0.735358 m2.
- Trench piece 7E0+FD #2 (40 498 .. 43 748, 3.25) and the arc span.
