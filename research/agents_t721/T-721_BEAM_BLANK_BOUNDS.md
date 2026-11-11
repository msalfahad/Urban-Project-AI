# T-721 concrete beams blank: 12 HELD BLANK STR.CONC.BEAM lines on V3.0.71 (lane S, research only)

Worker 1, 2026-11-11, branch `agents/task-T-721`. Nothing wired, released or VERIFIED; no AT_MOST; no floor summed into a
released total. ERS s.2-7; R-CONC-OWN-1; R-T660-3; R-T711-3; R-T712-1; UP-QTY-STATUS-001; R-T696-1. Rules `t721_rules.py`
(R-T721-1 .. 3), ledger `t721_alsenan.py` -> `out/T721_LEDGER.json` + `out/T721_CENSUS.md`, tests
`tests/t721_beam_blank_bounds` (44).

## What the 12 lines are (correction to the row text)

The row names D-02 / D-03 / D-04 / D-27 / D-30 / D-44: those items belong to the **14 bounded** lines (5.983229 ..
8.412710 m3, untouched here). The **12 blank** lines are 11 roof-edge projection strips / boxes (D-05 / D-26: GF 3, 1F 7,
2F 1; plan 6.9471 m2) and the east dome-opening ring (D-28). None has a schedule / drawing size disagreement, so the
row's 'smaller of two printed readings' case does not arise on Alsenan; it is written as R-T721-3 for every villa and
tested (normal + adverse), not applied.

## Own reads this run (Drive 'Alsenan chalet project', read-only; private copies only)

- 'ST7757 dxf.dxf' (sha 9f9d1179) ST p.5 first-floor roof slab: four 'SEE DETAIL' texts 1A1D / 1A1E / 1A1F / 1A20 lie
  ON the east ring band (circle 649 r 2.2111, arcs 64A-64D r 2.4111): the ring is referenced to the dome detail.
- ST p.7 'DETAIL OF DOME' (N.I.S.): ring section with **top 3T16 (1A47), side 2T14/20cm (1A37), bottom 3T18 (1A4B),
  links 8T8/m (1A29)**; the bar circles sit on two shared verticals (x -63185 / -62525: bottom y 29563, sides 30563 /
  31563, top 32973; mirrored section identical). Depth dimension 182F overridden 'AS PER ARCH'. No cover is printed in
  the sheet set (text search 'COVER': none). T-660 recorded this ring as 'no bars': the bars ARE printed (new finding).
- Architect's section B-B (Pages_11-12, p.11) cuts both first-floor-roof domes: each springs from the roof line, NO ring
  is drawn and no depth printed; section A-A (sheet 10) and elevations p.6-p.9 print the dome 441 x 215 only. So the
  'AS PER ARCH' reference resolves to nothing printed.
- Projection edges re-measured on the DXF: BAND0014 5E7 / 5E5 7.500 x 0.200; BAND0031 2C6 / 2C7 and BAND0013 5E1 / 5E6
  0.200 apart; BAND0025 5DE / 629 0.2983; BAND0023 5C1 / 619 0.300 = T-660 widths. No section prints a strip depth; A-A /
  B-B end the outline at the beam's outer face (T-660 finding 1, re-confirmed on the architect's B-B: no strip cut).

## Result per line

| Class | Lines | Before | After | Basis |
|---|---|---|---|---|
| East dome ring L-ab37afa1 | 1 | blank | **AT_LEAST 0.115155 m3** | R-T721-1 bar stack: depth >= 2 x 0.008 + 0.016 + 0.014 + 0.018 = **0.064 m** (cover not printed, not added); plan in-bay **1.7993 m2** (line) / own 1.7994065 (T-160 bay faces, shapely) -> least; slab stops at r_outer (T-160), opening inside r_inner, B25 / CB12 / B6 x2 own the corners: counted once |
| Projection strips / boxes | 11 | blank | **BLANK_NAMED** | R-T721-2 / R-T660-3: no section, mark, bars or material; may be slab-cast, parapet base or non-concrete (T-319 F-T311-C2 'material UNKNOWN') -> no floor; m3 per m of depth = plan 0.435 / 0.105 / 0.569 / 0.1048 / 1.5441 / 0.5998 / 0.5997 / 1.4999 / 0.82 / 0.2698 / 0.40 = **6.9471 m2**; one-family guard (beam OR parapet / projection) |

Census 12 / 12 by id: 1 AT_LEAST (0.115155 m3 beside), 11 BLANK_NAMED; none 0, none a range. Family after: 14 bounded
5.983229 .. 8.412710 (untouched) + 1 AT_LEAST 0.115155 + 11 blank.

Not adopted for the ring (shown, never used): 0.75 scaled from the N.I.S. detail; 0.50 (B4, no mark on this ring, Q-61
C(3)); 0.16 roof-slab thickness (ST p.8 note 18: no sheet ties the ring depth to the slab); 0.40 from reading '/20cm'
as a layer pitch (it is a maximum spacing, not a depth).

## Owner manual method beside the drawing-derived method

Freelancer workbook: no row for the projections or the ring (T-660 / T-160). Owner Q-44 A: the ring stays (membrane
upturn carrier) at B4 0.20 x 0.50 'from the slab plan'; Q-61 C(3) limits B4 to rings marked B4 -> the B4 candidate
0.8997 m3 stays the designer's answer to D-28, our floor 0.115155 lies below it (consistent). Verdicts: ring
UNRESOLVED (D-28; floor only), projections UNRESOLVED / NOT_COMPARABLE (D-05 / D-26). No ENGINE_RIGHT claimed.

## For the Checker (own re-measure of 2 lines)

1. Ring L-ab37afa1: ST p.7 bars 1A47 / 1A37 / 1A4B / 1A29 and their circles on shared verticals; 'SEE DETAIL' 1A1D-1A20
   on the east ring; 2 x 0.008 + 0.016 + 0.014 + 0.018 = 0.064; 1.7993 x 0.064 = 0.1151552 -> 0.115155.
2. Projection L-a9d5e7dc (1F BAND0014): 5E7 / 5E5 7.500 x 0.200 (line 1.4999 from f2f 7.4996); no section crosses it.
Uncertain: whether 2T14 '/20cm' means one bar per face per level (read so: 1 level counted). Any other reading only
adds levels and raises the true depth: the floor stays valid.

## Proposed for others

- T-714 (formwork): the ring formwork line follows this floor (AT_LEAST), the 11 strip formwork lines stay blank.
- Rebar (T-664): the east ring has printed bars (3T16 / 3T18 / 2T14 per level / T8 at 8 per m): a detailed takeoff is
  possible for the longitudinal bars on the in-bay arcs; links / side levels need the depth (held).

## Lessons row (ERS s.7, proposed)

| 2026-11-11 | the east dome ring sat blank recorded as 'no bars' though its referenced detail prints them | a held member's
section was searched for a depth only, not for what its printed bars guarantee | a member whose referenced section
prints its bars but not its depth carries AT_LEAST = least net plan area x (2 link + stacked bar diameters), cover
added only when printed; an edge strip with no section, mark, bars or material stays blank with its plan area and the
one-family guard; two disagreeing printed sizes give AT_LEAST on the smaller, never a mean (every villa; R-T721-1 .. 3)
| tests/t721_beam_blank_bounds | PROPOSED |
