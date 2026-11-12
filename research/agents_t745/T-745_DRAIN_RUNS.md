# T-745: B12-02 drainage and water supply runs, lm census (research only, nothing wired)

r1 2026-11-12 (V1, REJECTED by the Checker 20:25Z: scaled plan lengths labelled MEASURED on sheets that disclaim their
scale). r2 Worker 1, 2026-11-12 (V2). Method `research/agents_t745/t745_runs.py` (DRAIN_RUN_CENSUS_T745_V2);
development-villa driver `t745_alsenan.py`; r2 restatement `t745_restate_r2.py`; committed result
`out/T745_ALSENAN_RUNS.json` (V2) restated from `out/T745_ALSENAN_RUNS_V1_REJECTED.json` (r1 records, kept as the
input; run ids, systems, diameters, statuses, lm; no coordinates).

## r2: length basis (verdict FIX 1-4; Lead ruling 2026-11-12 20:14; rule R-T380-1 of the merged T-380)

Physical quantity vs source: a pipe run's installed length is a physical fact; what this set gives is a single-line
route on sheets whose NOTES box says, read by eye this run on p.1, p.2 and p.3 (rendered 300 dpi; the sheet text is
outlined vectors, no text layer): "THE BUILDER TO WORK WITH STATED DIMENSIONS NOT TO SCALE DRAWING." The sheets are
also plotted at 1:108.2 under a 1:100 title. R-T380-1: a run is MEASURABLE only on a printed dimension or printed
levels at both ends, and a route is never scaled under a not-to-scale note. The only printed lengths on the sheets are
the plot sides (31.37 / 15.00 m); no pipe run is dimensioned. So:

- every plan run (all 3 floors) is HELD_SCHEMATIC_NOT_TO_SCALE; its r1 scaled length is kept only as
  `scaled_info_lm`, labelled "SCALED FROM NOT-TO-SCALE SCHEMATIC, never released", never in `lm`, never summed with
  a valued row (the 4 lengths the Checker reproduced are unchanged, now information);
- the sheet basis is read from the notes (`sheet_basis`); an unread notes box is refused (no assumed basis); a run
  with a printed dimension (`Run.stated_m`) is MEASURED at that printed value on any sheet;
- risers between printed levels at both ends stay as r1 (FIX 2);
- T-692 class for B12-02 on this villa: risers MEASURABLE FROM PRINTED LEVELS, plan runs HELD SCHEMATIC_NOT_TO_SCALE;
  designer item 16 (DESIGNER_QUESTIONS.md, dimensioned drainage layout) is the route to a measured plan length.
  T-692 "MEASURABLE FROM DRAWINGS" and the row's "lm along its drawn centreline" hold only for a sheet that keeps its
  scale (`BASIS_SCALED`) or prints the run's dimension; this set has neither for plan runs.

1F 'P 4in B.T.T.S.' (1F-M03): one drawn magenta segment, 6.054 m scaled info. Measured on the vector pens this run:
the WC branch (0.508 m drawn) tees in 5.587 m from the segment's upper end, so 0.467 m lies past the tee; r1 read the
4in label over the whole segment, so the 0.467 m piece carries 4in only by continuity of the one drawn line.

Residual named for the Checker (not changed, FIX 2 keeps the risers): T-380 classed the RWP verticals SCHEMATIC_ONLY
because the top is an outlet on a roof laid to 'SLOPE 1%' whose outlet level is not printed; r1 / r2 measure each RWP
from the printed roof level (+9.70 / +5.50 / +4.30) to the printed discharge level + 0.15 m. The residual between the
two is the unprinted fall from the printed roof level to the outlet (and the outlet body), which shortens the vertical;
28.20 m is therefore the length between printed storey levels, not the outlet-to-discharge pipe. No engine, tool, rule, knowledge or frozen file changed; no BOQ line produced or changed. MEP is
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

Plan rows (V2): lm = none (HELD_SCHEMATIC_NOT_TO_SCALE); the last column is the scaled information figure only,
SCALED FROM NOT-TO-SCALE SCHEMATIC, never released (row sums of the 3-decimal run values).

| Floor | System | Diameter | Status | Runs | scaled info (not lm) |
|---|---|---|---|---|---|
| GF | BUILDING_DRAIN (MH to GCO 25.542 + GCO branch 8.259) | 6 in | HELD_SCHEMATIC | 2 | 33.801 |
| GF | SOIL_STACK_OFFSET (high level) | 4 in | HELD_SCHEMATIC | 1 | 0.801 |
| 1F | SOIL_WASTE_BRANCH below slab (P 4in B.T.T.S.) | 4 in | HELD_SCHEMATIC | 1 | 6.055 |
| GF | SOIL_WASTE_BRANCH | not printed | HELD_SCHEMATIC | 16 | 37.467 |
| GF | FIXTURE_WASTE | not printed | HELD_SCHEMATIC | 13 | 14.872 |
| 1F | SOIL_WASTE_BRANCH | not printed | HELD_SCHEMATIC | 8 | 10.360 |
| 1F | FIXTURE_WASTE | not printed | HELD_SCHEMATIC | 8 | 12.075 |
| 2F | SOIL_WASTE_BRANCH | not printed | HELD_SCHEMATIC | 1 | 1.850 |
| 2F | FIXTURE_WASTE | not printed | HELD_SCHEMATIC | 2 | 1.882 |
| all | RAINWATER_PIPE riser (5 RWP) | 4 in | MEASURED (printed levels) | 5 | 28.200 |
| all | SOIL_STACK riser 2F to 1F (stack A, +9.70 to +5.50) | 4 in | MEASURED | 1 | 4.200 |
| all | SOIL_STACK riser 1F to GF (stacks A, B, C) | 4 in | BOUNDED | 3 | 13.500 .. 15.600 |
| all | SOIL_STACK feet (3) + stack D high level + drop | 4 in | HELD_LEVEL | 5 | none |
| all | COLD / HOT SUPPLY | | HELD_NOT_DRAWN | | none |
| all | VENT; manhole to public sewer | | HELD_NOT_DRAWN | | none |

Plan lm (V2): MEASURED none; HELD_SCHEMATIC_NOT_TO_SCALE 9 rows / 52 runs, scaled information 119.163 m (diameter
printed 40.657, unprinted 78.506; r1 called these MEASURED 40.657 + HELD_DIAMETER 78.512, the 0.006 m is row vs run
rounding). Risers: MEASURED 32.400 m, BOUNDED 13.500 .. 15.600 m, 5 HELD. Never summed across states or plan / riser.

Risers by printed levels: RWP-1 roof +9.70 to the court +0.15 + 0.15 (free discharge 15 cm above FFL) = 9.40;
RWP-2 +9.70 to the 1F east roof +5.50 + 0.15 = 4.05; RWP-3 +9.70 to the 1F west roof +4.30 + 0.15 = 5.25; RWP-4
west roof +4.30 to the GF west face, +-0.00 printed at the discharge, + 0.15 = 4.15; RWP-5 east roof +5.50 to the GF
SE face +-0.00 + 0.15 = 5.35 (sum 28.20). Stacks: positions coincide across sheets (all three sheets share the plot
frame to 0.01 pt, so a stack is the same point on each). The GF FFL in the wet rooms at stacks A / B / C is not
printed: the neighbour spaces print +0.30 and +1.00, so 1F +5.50 down to GF is 4.50 .. 5.20 m each (BOUNDED, not
released). The stack foot below the GF floor to the branch invert (inverts not printed), the high level of stack D and
its drop at the offset are HELD.

Level cross-check against the architectural drawing (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip,
own decode, all TEXT / MTEXT / block texts): 51 level texts, the same set as the sanitary sheets (+-0.00, +0.15,
+0.30, +1.00, +4.30, +5.50, +9.70); on the NORTH WEST ELEVATION the marks +1.00 and +5.50 stand 4.500 m apart and on
the SOUTH EAST ELEVATION +0.30 and +4.30 stand 4.000 m apart (insert heights), so GF +1.00 / 1F +5.50 and the low
wing +0.30 / roof +4.30 used by the risers AGREE between plan and elevation. +9.70 is printed on the 2F plan only (no
elevation mark). No level is printed inside the GF wet rooms of stacks A / B / C in either source (nearest: stair
landing +0.30, lobby +1.00), so their 1F to GF crossing stays BOUNDED.

End points (T-743 census): every floor-drain square inside the plot (GF 11, 1F 7, 2F 1 = 19 = the T-743 count) has a
drawn pipe ending at or passing through it (0 without). Printed diameter labels: 3 placed, 0 refused.

Independent hand checks, r1 (scaled drawn lengths, information only under V2; in sheet points x 0.038165; coordinates stay in `.work/private`): collector
from the manhole face to the GCO, one straight line, 8 dashes + 7 dot-filled gaps = 669.2 pt = 25.54 m; GCO branch
28.6 (diagonal) + 187.8 pt = 216.4 pt = 8.26 m; 1F P 4in run 158.6 pt = 6.05 m; 2F branch 48.4 pt = 1.85 m: all
AGREE with the tool.

Freelancer: the Drive folder's workbooks (by title: masonry, aluminium, floors + waterproofing + decor + marble,
paint, internal plaster) carry no drainage / plumbing line (T-743 found no sanitary line): no comparison exists.

## Verdict proposals

- B12-02 plan lm: no engine line and no freelancer line; UNRESOLVED on this set (no stated dimension, not-to-scale
  sheets): HELD_SCHEMATIC_NOT_TO_SCALE, designer item 16. Not an owner question (ERS 2.7 not met: nothing released).
- B12-02 risers: RWP 28.20 m MEASURED and SS 4.20 m MEASURED between printed levels, 13.50 .. 15.60 m BOUNDED,
  5 HELD (as r1, Checker FIX 2); RWP residual = unprinted roof fall to the outlet, named above.
- Diameter of 48 branch / waste runs: UNRESOLVED (no per-run size printed); a designer item for pricing.

## Lessons-register row (ERS section 7, proposed)

| lesson | scope | provenance |
|---|---|---|
| L-T745-1: read a sheet's notes before its scale. A drainage / supply sheet that disclaims its scale ('work with stated dimensions', 'not to scale', 'N.T.S.') gives no MEASURED plan length: every plan run is HELD_SCHEMATIC_NOT_TO_SCALE with its scaled figure as labelled information only; a printed dimension is MEASURED on any sheet; risers between printed levels stay measurable; an unread notes box gives no basis. Tracing tools (pens, dot-bridged gaps, two-side scale check) still serve census, counts and information figures | every villa | T-745 r1 REJECTED (40.657 m labelled MEASURED on Alsenan's not-to-scale sheets), r2 under merged R-T380-1; tests/t745 adverse cases |

## Synthetic proof (not Alsenan): `tests/t745_drain_runs/` (33 cases: r1 20, r2 +13)

Villa N745, plot 20.00 x 10.00 m at 0.04 m/u, two bathrooms mirrored: dash-dot collector 15.600 m (one run, 7
gaps), WC branches 2 x 2.565685 m, dotted FD branch 2.400 m (one bridge), basin waste 1.400 m, a 0.04 m symbol
mark; RWP across two floors 6.850 m; stack with GF level unprinted HELD, bounded 2.60 .. 3.30. ADVERSE: rotated and
mirrored sheet give the same census; gap without a dot / off line / over 1.60 m / at a drain body not bridged;
duplicates counted once; a label in metres instead of sheet units refused; a label on two runs refused; distorted
plot, a side in mm and one dimension only refused; riser top below bottom refused; HELD rows unvalued (None, never 0);
plan and riser never summed; committed output re-adds row by row and holds no coordinates. r2: the same villa on a
sheet with a not-to-scale note gives no MEASURED and no valued plan row (scaled info 15.600 + 7.531 + 1.400 kept
apart, labelled); printed dimensions 12.40 / 2.50 m MEASURED on that sheet instead of the drawn 15.60 / 2.566;
GF scaled + 1F not-to-scale mirrored keep their own basis (GF 15.600 MEASURED, 1F HELD); notes-box classifier with
false-positive guards ('STATED DIMENSIONS ARE IN MM', 'PLANTS'); unread notes / unknown basis refused; a schematic
record carrying a value refused; the committed V2 equals the restatement of the V1 records, drawn lengths unchanged.

## What is missing

- Not wired: B12-02 has no candidate line; a later Gate B row may add the risers (printed levels) only; plan runs
  wait for a dimensioned drainage layout (designer item 16).
- The r1 private reading (page points) was not kept; V2 is restated from the committed r1 records. A rerun of
  t745_alsenan.py needs a new reading with 'sheet_notes'.
- Branch / waste diameters (78.512 m), GF FFL at the stack rooms, stack inverts and the stack D high level are not
  printed: designer items. Water supply is not drawn anywhere in the set (no supply sheet in the folder).
- Riser levels: plan marks cross-checked against the architectural elevations (above); the sections (sheets 9 / 10)
  were not read this run, and the roof outlet bodies / bends at the riser tops are not measured. Fittings (bends, tees, clean-outs, GCO, manhole) are pcs items, not counted here.
