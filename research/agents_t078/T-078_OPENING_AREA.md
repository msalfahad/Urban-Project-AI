# T-078: door and window areas in m2 from the plan width and a printed height (method piece, not wired)

Worker 2, 2026-10-19 16:40-17:05 UTC. New files only: `engine/source/opening_area.py` (method piece, imported by no
released method), `tests/t078_opening_area/` (hand villa, 23 cases), this folder (runner + this note). No frozen file,
rule or knowledge version, key map or released quantity changed. Development villa (Alsenan), not an accuracy claim.
Rules: UP-OPEN-SCHED-001 (width within 0.03 m; unknown height -> width released, area held), UP-DOOR-AREA-001
(AS_DRAWN view, never added to the owner view), UP-DOOR-HGT-001 (schedule before elevation; a fallback height is never a
confirmed area), UP-QTY-STATUS-001 (every opening once, never 0), owner Q-32 = A (arched: to the top of the arch,
enclosing rectangle), owner Q-33 = A (a window is aluminium unless the drawing says otherwise).

## What the piece does (engine/source/opening_area.py)

`measure(plan_openings, views, floors=..., curved_width_basis=None)`; `read_view(doc, box, unit_m, view_id)` reads one
elevation frame of a DXF (lines, polylines, arcs, block contents; model-space dimensions).

1. Printed value of a dimension = its shown number through its effective DIMLFAC, used only when it equals the defpoint
   geometry rounded to its own last digit (Alsenan prints whole centimetres, DIMLFAC 0.1: "269" for 2691.5 mm is a
   rounded print; a print more than half a unit off the defpoints is STALE and never used).
2. View mapping x_view = s (xy . a) + c from at least two printed widths at different places that match plan
   openings by width (0.03 m) and position (0.03 m); one match proves no position, ties are ambiguous -> no mapping.
3. Drawn opening = two jamb lines at the projected ends with one foot (surrounds over several storeys dropped, jambs
   drawn in pieces joined).
4. Printed height = a vertical dimension with both witness origins inside the opening, from the jamb foot to the
   jamb top (RECTANGULAR); an arch (curves above the jambs) runs to the highest curved point through consecutive
   printed dimensions (Q-32 A); not reached -> HELD ARCH_TOP_NOT_PRINTED.
5. Stacks: drawn openings at one range go to the plan openings of that range floor by floor only when the counts agree
   and no floor has two (front and back face) -> else HELD STACK_NOT_BOUND.
6. Interior doors (the run finds a space on both sides) are never looked up on an elevation (HELD INTERIOR_OPENING).
7. A curved-on-plan opening needs the owner's width basis (owner question below): HELD CURVED_WIDTH_BASIS with every
   candidate area until then.

## Alsenan: engine vs freelancer (aluminium workbook, sheet "الكميات")

Run: working branch 2c86de1, Python 3.11 venv, `tools/urban_boq_m9.py arch --drawings P7757.dxf --method
ARCH_TAKEOFF_V2.9 --conventions engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json` (exit 0), then
`python3 -I research/agents_t078/run_opening_area.py P7757.dxf RUN`. Views: SH01 = NORTH WEST elevation, mapped
not mirrored on 3 printed widths (155, 155, 269 = 1F OP-016, OP-017, COP-001 chord); SH02 = SOUTH EAST elevation,
mapped mirrored on 2 printed widths (120, 245 = the stair stack and 1F OP-022). 51 + 49 printed dimensions usable.

| Floor | Opening | Width m (plan) | Printed height (view, dims) | Engine m2 | Freelancer | Diff | Verdict proposal |
|---|---|---|---|---|---|---|---|
| GF | OP-022 stair | 1.20 | 2.00 (SE "200", rectangular) | **2.400** | 1.20 x 2.00 = 2.400 | 0.000 (0.0 %) | AGREE |
| 1F | OP-021 stair | 1.20 | 2.30 (SE "230", rectangular) | **2.760** | 1.20 x 2.00 = 2.400 | +0.360 (+15.0 %) | ENGINE_RIGHT: 2.30 printed, he used 2.00 |
| 1F | OP-022 master bedroom | 2.4498 | 1.60 (SE "160", rectangular) | **3.920** | 2.45 x 2.00 = 4.900 | -0.980 (-20.0 %) | ENGINE_RIGHT: 1.60 printed, he used 2.00 |
| 1F | OP-016 living, sea side | 1.5523 | 3.10 = "300" + "10" to the arch crown (NW, arched, Q-32 A) | **4.812** | 1.55 x 3.00 = 4.650 | +0.162 (+3.5 %) | ENGINE_RIGHT proposal: the crown is printed 0.10 above the 3.00 (verifier: re-read) |
| 1F | OP-017 living, sea side | 1.5523 | none inside its width (drawn the same size as OP-016) | HELD | 1.55 x 3.00 = 4.650 | - | NO_PRINTED_HEIGHT; same drawn size as OP-016 listed as evidence, not released |
| 1F | COP-001 curved, master bedroom | chord 2.6917 / inner arc 2.9767 / outer arc 3.2895 | 3.50 = "305" + "45" (NW, arched): the owner's own Q-32 example | HELD (basis) | 3.15 x 3.00 = 9.450 | chord 9.421 (-0.3 %) / inner arc 10.418 (+10.2 %) | owner Q-39: width basis of a window curved on plan |
| 2F | OP-008 stair | 1.20 | "170" + "5" end at 0.50 m below the drawn arch crown; the "88" lies outside the window | HELD | 1.20 x 2.00 = 2.400 | - | ARCH_TOP_NOT_PRINTED (UNRESOLVED; the earlier hand reading "170 to the springing + 88 rise" does not meet the drawn arch) |
| GF | OP-019 saloon glazing 6.33 | 6.3316 | no jamb pair at its place on NW (the "430" chain is not bound) | HELD | 6.33 x 4.30 = 27.219 | - | NOT_DRAWN_ON_THIS_ELEVATION |
| GF | OP-023, OP-024, OP-028, OP-029 | 1.00, 1.50, 1.9549 x 2 | no jamb pair at their places on NW / SE | HELD | | - | NOT_DRAWN_ON_THIS_ELEVATION |
| other 15 windows | | | no elevation of their face in the DXF (SW, NE are PDF-only and print no heights, T-040) | HELD | | | NO_ELEVATION_OF_THIS_FACE |

Windows measured: **4, 13.892 m2** vs the freelancer's 14.350 m2 for the same four (-0.458 m2, -3.2 %); was 0 m2
(no m2 line in V2.9). That is 11.9 % of his 116.9 m2 window total; with COP-001 released on either basis the share
becomes 19.9-20.8 %. 23 windows HELD (reasons above), 0 at 0 m2; the 2 windows the plan run loses (GF curved pool
glazing, 1F bath 0.50) are T-077's, not in this piece's input.

Doors: 0 m2 measured vs the freelancer's 12.0 m2 (not comparable). 22 doors are interior (HELD INTERIOR_OPENING, their
height comes only from a schedule or section, none exists); the outdoor ones: GF driver door OP-005 and 2F roof door
OP-001 sit on faces with no elevation in the DXF; GF OP-021 (2.00 double, main-entrance candidate) is under the SE porch:
the SE view draws its left jamb with the printed "250" (+1.00 to +3.50) but its right jamb is hidden behind the porch
column, so the pair is not drawn: HELD (candidate 2.00 x 2.50 = 5.00 m2 AS_DRAWN, not released). The driver door 0.90
AS_DRAWN vs the owner 1.00 (Q-04 / UP-DOOR-OPEN-002) stays a RULE_DIFFERENCE carried by door_standards.door_scenarios
(this piece never adds the two views).

Material: every measured window ALUMINIUM by owner Q-33 = A (no window material is written on the 12 sheets).

## Hand checks (verifier: re-read on the Drive DXF, SE = frame SH02, NW = frame SH01)

1. GF stair: SE jambs (W lines) 1.20 apart, foot +2.00 -> "200" (8670 -> 10670 drawing mm) -> 1.20 x 2.00 = 2.400.
2. 1F stair: SE "230" (13170 -> 15470) between the same jamb columns one storey up -> 1.20 x 2.30 = 2.760.
3. 1F master: SE "245" wide (printed width, plan 2.4498), "160" (13571 -> 15170 = jamb foot to jamb top) -> 3.920.
4. 1F living OP-016: NW jambs 12170 -> 14331, arch crown line at 15271; chain "300" (12170 -> 15170) + "10" (15170 ->
   15271, 101 mm) -> 3.10; 1.5523 x 3.10 = 4.812.
5. COP-001: NW chord "269", jambs 12170 -> 14389, crown 15674; "305" (12170 -> 15220) + "45" (15220 -> 15674) -> 3.50
   (= the owner's Q-32 example 2.69 x 3.50 = 9.42).
6. 2F stair: SE jambs 17470 -> 18543, drawn crown 19670; printed "170" (-> 19170), "5" (-> 19219), "88" (19219 ->
   20096, witness at x 17566, 31 mm outside the window): no printed witness at 19670 -> HELD.

## Tests (non-Alsenan hand villa SV-T078, tests/t078_opening_area, 23 cases)

East view in mm, west view in m and mirrored, cm prints (DIMLFAC 0.1 / 100), a rounded print (2603 mm -> "260"),
stacked storeys with a two-storey surround, an arched window (to the crown) and its variants (one dimension from the
foot; springing printed but no arch drawn = rectangular; arch top not printed; head above the jambs with no arch),
plan rotated 30 and -123 degrees and mirrored, stale print, text override, width conflict (2.45 printed vs 2.40),
one printed width only (no mapping), a missing storey (stack held), front and back windows on one range (held),
schedule height over the elevation (REVIEW kept), schedule height without an elevation, curved window with and without
the owner basis, no dimensions at all, missing width, an unsupported kind, a held twin (evidence only), a jamb drawn in
two pieces, a railing above a window (not its arch), and a DXF round trip through `read_view`. Hand total: windows
13.860 m2, door 2.500 m2.

Validation (working branch 2c86de1 + this branch): tests/t078_opening_area 23 passed; L2 for the doors / windows
topics (t078 + m9_p2b9/test_p2b9_openings + m9_p2a + m9_p2b2 + m9_kb): 300 passed, 1 xfailed (pre-existing), exit 0;
freeze check: 0 differing; `codemap.py build` + `check`: stale none.

## Learned / limits

- The drawing prints arch crowns as separate small chain parts ("10", "45") above a common head line (+8.50): Q-32 A
  is readable from the chain only when a printed witness sits at the drawn crown.
- Tolerances are the 0.03 m of UP-OPEN-SCHED-001 throughout; the SE 1F stair window has frame mitre lines 27 mm above
  its jamb tops (within 0.03 m, read as rectangular): a drawing with deeper mitres would need the verifier's eye.
- Not done: wiring into a method version (a new ARCH_TAKEOFF version + key map V2 rows, T-079 queue); door heights from
  sections; the "430" GF glazing binding (needs a printed width or jamb pair on NW); PDF-only elevations.
