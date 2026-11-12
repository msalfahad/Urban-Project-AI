# T-745: B12-02 drainage and water supply runs, lm census (research only, nothing wired)

Worker 3, 2026-11-12. Method `research/agents_t745/t745_runs.py` (DRAIN_RUN_CENSUS_T745_V1); development-villa
driver `t745_alsenan.py`; committed result `out/T745_ALSENAN_RUNS.json` (run ids, systems, diameters, statuses, lm;
no coordinates). No engine, tool, rule, knowledge or frozen file changed; no BOQ line produced or changed. MEP is
last in the owner order (2026-11-09): census only. Development villa: not an accuracy claim.

## Physical element and method

A pipe run = one drawn pipe between two fittings / ends (fixture outlet, floor drain, stack foot, clean-out, manhole,
junction), by system and printed diameter, in lm along its drawn centreline (plan length; the printed 1 % fall adds
0.005 %, not added). Risers are vertical, measured only between two levels the sheets print.

Reading the vector sheet: each system has its own pen. Segments of a pen are deduplicated (the export draws many lines
twice), joined where ends meet (0.6 pt), and a gap is bridged only when both loose ends face each other on one line
(2 deg) AND the gap carries a dot of the same pen (the dash-dot / dotted style of a pipe passing under something); a
gap at a floor-drain body (no dot) stays two runs. An isolated piece under 0.10 m is a symbol mark (stack-circle
stub), listed, not counted. Scale only from two printed dimensions measured on the same sheet, refused if they differ
by more than 0.5 %. A run whose diameter is not printed keeps its lm and is HELD_DIAMETER_UNPRINTED (never a
default diameter); a riser with an unprinted level is HELD (or BOUNDED between printed neighbour levels), never 0.

## Development villa (Drive 'Alsenan chalet project' / sanitary-7757.pdf p.1-3: GF, 1F, 2F drainage plans)

Reproduce: `bash scripts/agent_env.sh run --tree <tree> research/agents_t745/t745_alsenan.py <sanitary.pdf>
<private reading.json> --out <scratch>.json` (the reading with page points stays in `.work/private`).

Scale: plot sides printed 31.37 / 15.00 m, drawn 822.0 / 393.0 pt on all three sheets: 0.038165 m/pt (1:108.2; the
sheets say 1:100, plotted to fit; T-743 found 1:108 by a different fit). Agreement 0.01 %.

Pens (sheet reading; the legend names symbols, not pens): black 1.44 dash-dot = BUILDING_DRAIN (court collector,
labelled P 6in SLOPE 1 %); magenta 0.72 = SOIL_WASTE_BRANCH (WC / floor drain / stack foot to the collector, 1F
below the slab); red 0.60 = FIXTURE_WASTE (basin / tray / mixer to its floor drain); one blue 0.48 high-level stack
offset (label SS 4in F/A H/L) entered by hand. Soil and waste share one branch pen: the set is a single-stack system
(legend: SS soil stack only).

| Floor | System | Diameter | Status | Runs | lm |
|---|---|---|---|---|---|
| GF | BUILDING_DRAIN (MH to GCO 25.542 + GCO branch 8.259) | 6 in | MEASURED | 2 | 33.801 |
| GF | SOIL_STACK_OFFSET (high level) | 4 in | MEASURED | 1 | 0.801 |
| 1F | SOIL_WASTE_BRANCH below slab (P 4in B.T.T.S.) | 4 in | MEASURED | 1 | 6.055 |
| GF | SOIL_WASTE_BRANCH | not printed | HELD_DIAMETER | 16 | 37.469 |
| GF | FIXTURE_WASTE | not printed | HELD_DIAMETER | 13 | 14.873 |
| 1F | SOIL_WASTE_BRANCH | not printed | HELD_DIAMETER | 8 | 10.361 |
| 1F | FIXTURE_WASTE | not printed | HELD_DIAMETER | 8 | 12.077 |
| 2F | SOIL_WASTE_BRANCH | not printed | HELD_DIAMETER | 1 | 1.850 |
| 2F | FIXTURE_WASTE | not printed | HELD_DIAMETER | 2 | 1.882 |
| all | RAINWATER_PIPE riser (5 RWP) | 4 in | MEASURED (printed levels) | 5 | 28.200 |
| all | SOIL_STACK riser 2F to 1F (stack A, +9.70 to +5.50) | 4 in | MEASURED | 1 | 4.200 |
| all | SOIL_STACK riser 1F to GF (stacks A, B, C) | 4 in | BOUNDED | 3 | 13.500 .. 15.600 |
| all | SOIL_STACK feet (3) + stack D high level + drop | 4 in | HELD_LEVEL | 5 | none |
| all | COLD / HOT SUPPLY | | HELD_NOT_DRAWN | | none |
| all | VENT; manhole to public sewer | | HELD_NOT_DRAWN | | none |

Plan lm: MEASURED 40.657 m; HELD_DIAMETER 78.512 m (lm drawn, diameter unprinted). Risers: MEASURED 32.400 m,
BOUNDED 13.500 .. 15.600 m, 5 HELD. Never summed across states or plan / riser.

Risers by printed levels: RWP-1 roof +9.70 to the court +0.15 + 0.15 (free discharge 15 cm above FFL) = 9.40;
RWP-2 +9.70 to the 1F east roof +5.50 + 0.15 = 4.05; RWP-3 +9.70 to the 1F west roof +4.30 + 0.15 = 5.25; RWP-4
west roof +4.30 to the GF west face, +-0.00 printed at the discharge, + 0.15 = 4.15; RWP-5 east roof +5.50 to the GF
SE face +-0.00 + 0.15 = 5.35 (sum 28.20). Stacks: positions coincide across sheets (all three sheets share the plot
frame to 0.01 pt, so a stack is the same point on each). The GF FFL in the wet rooms at stacks A / B / C is not
printed: the neighbour spaces print +0.30 and +1.00, so 1F +5.50 down to GF is 4.50 .. 5.20 m each (BOUNDED, not
released). The stack foot below the GF floor to the branch invert (inverts not printed), the high level of stack D and
its drop at the offset are HELD.

End points (T-743 census): every floor-drain square inside the plot (GF 11, 1F 7, 2F 1 = 19 = the T-743 count) has a
drawn pipe ending at or passing through it (0 without). Printed diameter labels: 3 placed, 0 refused.

Independent hand checks (drawn lengths in sheet points x 0.038165; coordinates stay in `.work/private`): collector
from the manhole face to the GCO, one straight line, 8 dashes + 7 dot-filled gaps = 669.2 pt = 25.54 m; GCO branch
28.6 (diagonal) + 187.8 pt = 216.4 pt = 8.26 m; 1F P 4in run 158.6 pt = 6.05 m; 2F branch 48.4 pt = 1.85 m: all
AGREE with the tool.

Freelancer: the Drive folder's workbooks (by title: masonry, aluminium, floors + waterproofing + decor + marble,
paint, internal plaster) carry no drainage / plumbing line (T-743 found no sanitary line): no comparison exists.

## Verdict proposals

- B12-02 lm: no engine line exists, so no ENGINE_RIGHT claim; census values MEASURED from the vector sheet. The
  Checker re-measures 2 runs (suggested GF collector MH to GCO 25.54 m and the 1F P 4in run 6.05 m).
- Diameter of 48 branch / waste runs (78.512 m): UNRESOLVED on this set (no per-run size printed; floor drains and
  stacks print 3 / 4 in, the runs do not). A designer item for pricing, not an owner question (ERS 2.7 not met:
  nothing is released).

## Lessons-register row (ERS section 7, proposed)

| lesson | scope | provenance |
|---|---|---|
| On a vector drainage sheet a dotted / dash-dot pipe is drawn in pieces: bridge a gap only when it is straight on with both ends and carries a dot of the same pen; a gap at a fitting body is two runs. Scale from two printed sides, refuse if they disagree | every villa | T-745, development villa: 7 collector gaps + 3 branch gaps bridged, FD-body gaps kept |

## Synthetic proof (not Alsenan): `tests/t745_drain_runs/` (20 cases)

Villa N745, plot 20.00 x 10.00 m at 0.04 m/u, two bathrooms mirrored: dash-dot collector 15.600 m (one run, 7
gaps), WC branches 2 x 2.565685 m, dotted FD branch 2.400 m (one bridge), basin waste 1.400 m, a 0.04 m symbol
mark; RWP across two floors 6.850 m; stack with GF level unprinted HELD, bounded 2.60 .. 3.30. ADVERSE: rotated and
mirrored sheet give the same census; gap without a dot / off line / over 1.60 m / at a drain body not bridged;
duplicates counted once; a label in metres instead of sheet units refused; a label on two runs refused; distorted
plot, a side in mm and one dimension only refused; riser top below bottom refused; HELD rows unvalued (None, never 0);
plan and riser never summed; committed output re-adds row by row and holds no coordinates.

## What is missing

- Not wired: B12-02 has no candidate line; a later Gate B row adds it from this census.
- Branch / waste diameters (78.512 m), GF FFL at the stack rooms, stack inverts and the stack D high level are not
  printed: designer items. Water supply is not drawn anywhere in the set (no supply sheet in the folder).
- Riser levels are read from the plan level marks of this sheet; a cross-check against the architectural sections was
  not done this run. Fittings (bends, tees, clean-outs, GCO, manhole) are pcs items, not counted here.
