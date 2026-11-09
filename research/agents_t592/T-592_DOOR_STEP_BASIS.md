# T-592 External door step: one payable length, the D-GF-09 riser, the gate (lane A, research)

Worker 2, 2026-11-07, branch `agents/task-T-592`, candidate of record ARCH_TAKEOFF_V3.0.58. No quantity, line, method,
rule or registry file changed. Development villa, not an accuracy claim; the method R-T592-1 is for every villa.
Signs: **ours - his**.

Build: `t592_extract.py --dxf <P7757.dxf> --write` (own read of the architectural DXF by handle, Drive 'Alsenan chalet
project' P7757_DXF_COMPRESSED.zip decoded into `.work/private` only) -> `T592_DRAWN.json` (handles, lengths, level
figures; no coordinate); `t592_alsenan.py [--check]` -> `out/T592_DOOR_STEPS.json` (pinned: T592_DRAWN, T-325 ledger,
T-584 output).

## 1. Physical element and evidence (ERS s.2.1, s.3)

The step at a house door is the threshold stone's outer nosing + riser (ELEMENT_REGISTER, FR-T584-3). The stone fills
the WALL GAP (the masonry opening between the drawn wall-line ends); the door frame jambs (0.050 each, door block
geometry) stand inside that gap, so the plan draws the stone's exposed front edge only BETWEEN the jambs. No door or
threshold detail / section exists in the set (DXF: 24 distinct model-space texts; T-360 sheet census: plans,
elevations, sections A-A / B-B, fence sheet), so the gap and the edge are the printed evidence; UP-THR-001 (owner rule:
one strip through the wall at the doorway, full door width) and the T-325 strip widths already measure the gap.

## 2. Per opening (own read by insert handle)

| Opening | Wall gap (ends) | Edge / companion | Jambs in gap | In / out level (region) | Pay lm | Nosing (attr.) | Riser m2 | Status |
|---|---|---|---|---|---|---|---|---|
| D-GF-01 | 1.000 (10A / 10C; 138 / 139) | 172 / 173 0.900 | 0.05 + 0.05 | +0.30 (401) / +0.15 (394, 4AE) | 1.000 | 0.900 | 0.150 | DRAWING-CONFIRMED |
| D-GF-03 | 0.900 (121 / 122; 11D / 11E) | 1C6 / 1C7 0.800 | 0.05 + 0.05 | +0.30 (403) / +0.15 (394, 4AE) | 0.900 | 0.800 | 0.135 | DRAWING-CONFIRMED |
| D-GF-05 | 1.000 (A3 / A2; A5 / A4) | 19C / 19D 0.900 | 0.05 + 0.05 | +0.30 (405) / +0.15 (407, 409) | 1.000 | 0.900 | 0.150 | DRAWING-CONFIRMED |
| D-GF-09 | 0.900 (2B9 / 2B8; 26F / 26E) | 3FD / 3FE 0.900 | 0.003 + 0 | +0.30 (4AC) / +0.15 (394, 40B, 4AE) | 0.900 | 0.900 | 0.135 | DRAWING-CONFIRMED (was riser HELD) |
| D-GF-15 gate | 1.000 (B9 / B8, inner face; outer face line 8E runs through) | 8F 0.900 (companion) | 0.05 + 0.05 | +0.15 (40B) / +-0.00 (A88, A89, A8A) | 1.000 | 0.900 | 0.150 | DRAWING-CONFIRMED geometry; NO_LINE |

Every house-door pay length equals its T-325 strip width (asserted in code). Totals: house **3.800 lm, nr 4, riser
0.570 m2** (3.80 x 0.15); visible nosing 3.500 lm kept as an attribute; gate 1.000 lm / 0.150 m2 (nosing 0.900).

D-GF-09 drawing conflict (named): the door block spans 1.000 but the wall gap is 0.900 (block drawn over the masonry
0.047 / 0.053); the drawn edge (0.900) matches the gap less the 0.003 jamb inside it to -0.003 m (drafting, within
0.010). The stone fills the gap; the door size is the door schedule's question (T-237 census 0.9), not this line's.

## 3. The riser's outside level (F-C-T584-2 closed)

R-T592-1 (d): the outside level is the figure printed in the step's OWN open region, reached from a point 0.08 m
beyond the face without crossing ANY drawn line (all model-space lines / polylines / arcs except the TEXT layer, plus
the exploded door and arch blocks), directly or via one waypoint of a 0.25 m grid. D-GF-09 opens onto the 1.30 m side
walk between the house and the boundary fence (fence lines 13A / BA / 98, gate wall 8E / B8 / B9): it reaches only
+0.15 (40B in the walk, 394 / 4AE around the house) and nothing else, so the riser is +0.30 - +0.15 = 0.15 m, not the
0 .. 0.30 bound from the plan's lowest figure. Every other low side also reaches exactly one figure (+0.15), the gate's
outer side only +-0.00 (three datum marks); the high sides reach +0.30 (house) and +0.15 (gate). A more permissive
read (layers 1 / 2 / 5 only, no door blocks) leaked through open doors into +0.30 rooms: the strict blocker set is the
one used, and a leak can only produce HELD (two figures), never a false single figure.

## 4. Engine vs freelancer and before / after

| Measure | Before (T-584) | After (T-592) | His | ours - his |
|---|---|---|---|---|
| House steps lm | 3.500 (edge) | 3.800 (piece) | 7.70 (6 pieces, no door id) | -3.90 lm UNRESOLVED (SCOPE) |
| + gate lm | 0.900 | 1.000 | ? | with gate -2.90 lm, nr 5 vs 6 |
| Riser m2 | 0.390 + HELD 0 .. 0.270 | 0.570 (+ gate 0.150) | none (his m2 cell = count x length, UNIT) | not compared |

No % (scope unresolved). Verdict proposals: payable basis ENGINE_RIGHT on our side (piece = wall gap, drawn); D-GF-09
riser ENGINE_RIGHT 0.15 (region read); his door-step rows UNRESOLVED (no ids; matching by figure stays refused).

## 5. Fix rows (manifest style; nothing wired)

- FR-T592-1 (replaces FR-T584-2): on the owning threshold lines L-b3933a51bd95e9bc542b (D-GF-01), L-74cd61b430eec9933d15
  (D-GF-03), L-c8b5c7f742b22388339e (D-GF-05), L-8111095f6db78f0e674b (D-GF-09): step payable lm = the line's own strip
  width (3.800 lm, nr 4) + riser m2 beside (0.570); nosing 3.500 lm attribute only; no second step line; material by the
  strip's specification (HELD).
- FR-T592-2: gate D-GF-15 has no strip line (T-325 NO_LINE UNBOUND): drawn gap 1.000 x fence depth 0.200 = 0.200 m2,
  step 1.000 lm, riser 0.150 m2, nosing 0.900 attribute; owning trade (boundary vs threshold family) for the Lead.
- OBS-T592-1: T-325 strip depth 0.18 at D-GF-03 / D-GF-09 vs 0.200 between the drawn faces and the frame depth: not this
  task's measure; named for the threshold m2 owner.

## 6. Rule, tests, lessons row (proposed)

R-T592-1 (t592_rules.py). Tests `tests/t592_door_step` (20): fixture Villa K592 (door 0.90 clear in 1.00 masonry:
stone 1.00, nosing 0.90, riser 0.15 x 1.00 = 0.150 m2; mm = m; two doors 1.90 lm, never 1.70 or 3.60); adverse: both
lengths on one line refused, riser from a level outside the region refused, two figures in one region HELD with bound,
no figure HELD (never 0), nosing longer than the stone refused, equal levels refused, units / None refused; Alsenan pins
(byte-identical rebuild, totals, D-GF-09, gate, edited input stops the build, no coordinates).

Lessons row: | 2026-11-07 | door step paid on the visible edge while the strip paid the gap; riser bounded by the plan's
lowest level | the plan draws only the exposed edge between the frame jambs, and the nearest-text read stopped at 6 m
| R-T592-1: one piece, one payable length = the wall gap (edge kept as an attribute); the outside level is the one
figure printed in the step's own drawn region | tests/t592_door_step | PROPOSED |

Missing / uncertain: the stone specification (not printed); his door-step rows' doors (no id); the gate's owning trade.
