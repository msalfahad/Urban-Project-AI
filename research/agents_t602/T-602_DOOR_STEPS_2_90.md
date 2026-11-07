# T-602 External door steps: his UNRESOLVED 2.90 lm (lane A, research)

Worker 2, 2026-11-07, branch `agents/task-T-602`, candidate of record ARCH_TAKEOFF_V3.0.58. No quantity, line, method,
rule or registry file changed. Development villa, not an accuracy claim; the method R-T602-1 is for every villa.
Signs: **ours - his**.

Build: `t602_extract.py --dxf <P7757.dxf> --write` (own read of the architectural DXF by handle, Drive 'Alsenan chalet
project' P7757_DXF_COMPRESSED.zip decoded into `.work/private` only) -> `T602_DRAWN.json` (handles, lengths, storey,
level figures, distances; no coordinate); `t602_alsenan.py [--check]` -> `out/T602_DOOR_STEPS.json` (inputs pinned in
`PINS.json`: T602_DRAWN, T-592 output, T-361 gate table, T-150 opening census, his marble-sheet cells).

## 1. Physical element and the question (ERS s.2.1)

An external door step is a change of finished level at an exterior opening, built as a front (nosing) edge + riser.
This villa draws every step the same way: a layer-5 front edge with a layer-2 companion 0.050 on the higher side
(T-412 flights, T-584 / T-592 doors). Question: which physical step edges do his 2.90 lm stand for (statement V8: his
7.70 lm / 6 nr = HELD 2.80 + gate 1.00 + D-GF-05 1.00 + UNRESOLVED 2.90), or is none drawn?

## 2. Every exterior opening (own region read, R-T592-1 (d)) and step yes / no

| Opening | Storey | Side levels (in / out) | Edge pair at it | Decision | lm | riser m | m2 |
|---|---|---|---|---|---|---|---|
| D-GF-01 dewaneya -> court | GF | +0.30 / +0.15 | 172 / 173 | STEP (T-592) | 1.000 | 0.15 | 0.150 |
| D-GF-03 driver -> court | GF | +0.30 / +0.15 | 1C6 / 1C7 | STEP (T-592) | 0.900 | 0.15 | 0.135 |
| D-GF-05 kitchen -> passage | GF | +0.30 / +0.15 | 19C / 19D | STEP (T-592) | 1.000 | 0.15 | 0.150 |
| D-GF-09 stair hall -> walk | GF | +0.30 / +0.15 | 3FD / 3FE | STEP (T-592) | 0.900 | 0.15 | 0.135 |
| D-GF-15 sea gate | GF | +0.15 / +-0.00 | 8E / 8F | STEP (T-592) | 1.000 | 0.15 | 0.150 |
| **G-01 street gate gap** | GF | **+0.15 / +-0.00** | **10F / 110** | **STEP (new)** | **2.500** | **0.15** | **0.375** |
| D-GF-06 pantry -> E1 landing | GF | +1.00 / landing +1.00 (T-260) | none | NO_STEP (equal) | - | - | - |
| D-GF-07 main door -> E1 landing | GF | +1.00 / landing +1.00 (T-260) | none | NO_STEP (equal) | - | - | - |
| SX-01 pool court east 4.521 | GF | court +0.15 (40D) / +-0.00 | none | NO_STEP (low wall drawn through: 8D / B7) | - | - | - |
| SX-03 pool court north 1.000 | GF | +0.15 (40D) / +0.15 | none | NO_STEP (equal) | - | - | - |
| W15 / W16 living -> terrace | 1F | +5.50 / terrace +5.50 (1251, D1D) | none | NO_STEP (equal) | - | - | - |
| W17 master bed, curved | 1F | +5.50 / void over the pool | none | NO_STEP (no walking surface) | - | - | - |
| D-2F-01 lobby -> roof | 2F | +9.70 / +9.70 | none | NO_STEP (equal) | - | - | - |

The census list is the merged T-150 opening census's exterior set (doors, gate, leafless openings, floor-level windows;
asserted in code) plus the boundary gap G-01 (T-361), which no door census carries. Where a strict region read finds no
figure on one side, the figure printed in the same open space is quoted beside (evidence only, never a riser).

**G-01 (new).** The plot line 10F (layer 5) runs through the 2.500 street gap; the companion 110 (layer 2) lies 0.050
inside, on the plot side, over exactly the gap (= T-361 opening, p.12 '250'), the same pair as at the sea gate (8E / 8F).
The plot side reads one figure (+0.15, court), the street side one figure (+-0.00, datum LEL outside the plot): a
drawn step, riser 0.15. T-361 read 110 as a 'hidden' dashed line only: the layer-2 dash IS the villa's companion
convention. The gate leaf stays HELD (not drawn) and does not change the step.

**Completeness.** 128 edge pairs exist on the three plans. 6 stand at an exterior opening (the 5 known + G-01); the
other 122 are at least 0.259 m from every exterior opening, 79 carry a T-412 flight handle, the rest lie within 2.336 m
of a flight edge (stair copies, winder fronts, floor edges: T-412 / T-598), and none reaches an outdoor figure
(+0.15 / +-0.00) on either side: no other door or outdoor step is drawn (R-T602-1 (c)).

## 3. His 7.70 lm / 6 nr against the census (aggregate only, R-T602-1 (d))

| Measure | Ours (after) | His | ours - his |
|---|---|---|---|
| Steps nr | 6 (4 house + sea gate + G-01) | 6 (H36..H41) | 0 |
| Steps lm | 7.300 | 7.70 | -0.400 (-5.19 %) |
| Riser m2 | 1.095 (6 x 0.15 m) | none (his m2 cell is count x length) | not compared |

V8's UNRESOLVED 2.90 lm splits: **2.500 G-01 street-gate step, DRAWING-CONFIRMED, ENGINE_OMISSION** (no candidate line
carries it) + **0.400 UNRESOLVED**. Two drawn measures he may have read instead are named beside the 0.40, not
attributed: D-GF-09's door block 1.000 drawn over a 0.900 masonry gap (T-592 conflict, +0.10) and the sea-gate zone
drawn as a 1.30 panel on the NW elevation (27FA, T-361) against the 1.000 plan gap (+0.30). They sum to 0.40, but his
rows carry no opening id, so equal figures are not evidence. Verdict proposals: G-01 ENGINE_OMISSION; his count of 6
FREELANCER_RIGHT; the 0.40 lm UNRESOLVED. The E1 flight (his H16) is not in these rows (FR-T584-1 owns it).

## 4. Fix row (manifest style; nothing wired)

- FR-T602-1: B7 external step at the street gate G-01 (no threshold line exists for it): payable 2.500 lm, nr 1,
  riser 0.15 m = 0.375 m2 beside, DRAWING-CONFIRMED geometry; stone / finish HELD (not printed); owning trade with the
  gate family (FR-T592-2) for the Lead.

## 5. Rule, tests, lessons row (proposed)

R-T602-1 (t602_rules.py). Tests `tests/t602_door_steps` (21): fixture Villa K602 (door 1.00 lm riser 0.15 = 0.150 m2,
boundary gate 2.00 lm riser 0.30 = 0.600 m2, a third door at equal levels NO_STEP; mm = m; mirrored sides equal);
adverse: equal levels given a step refused, a pair between equal levels refused, a pair away from the opening refused,
an inverted companion refused, a passable level change with no edge HELD (never 0), a side with two figures HELD, a
quoted fallback never sets a riser, a step at a non-passable opening refused, figure matching refused, units / None
refused; Alsenan pins (byte-identical rebuild, census decided, G-01, closure 2.90 = 2.50 + 0.40, pairs away not door
steps, edited input stops the build, no coordinates). L2 with t592 / t584: all pass.

Lessons row: | 2026-11-07 | the boundary gate gap's step missed; his extra piece left UNRESOLVED | the census of steps
started from the door blocks; the fence gap has no door block and its companion was read as a 'hidden' line | R-T602-1:
census every exterior opening INCLUDING plot-boundary gaps, and every drawn edge pair; a pair at an opening with two
different single figures is a step | tests/t602_door_steps | PROPOSED |

Missing / uncertain: the stone / step specification (not printed); whether G-01 is paved as a step or a vehicle kerb
is not printed (the drawn convention is the step's); the 0.40 lm attribution (no ids in his rows).
