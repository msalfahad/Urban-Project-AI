# T-056: stair concrete as separate lines (STAIR_CONCRETE_V1), run on the development villa

Worker 3, 2026-10-20. New piece `engine/source/stair_steps_concrete.py` (not wired into a released method), tests
`tests/t056_stair_steps/` (15 tests, synthetic stairs, not a client drawing), census and run `alsenan_stair_census.py`
(printed dimensions and counts with their sheets; the values are the verified readings of research/agents_t084, the GF ->
1F count and turn cross-checked against the frozen structural study research/alsenan_stairs_s8_7c, arrangement B-27-S
by DXF handle). Development villa: not an accuracy claim.

## What the piece does (every villa)

Per stair, separate lines: STEPS (Q-19: n x 1/2 x riser x tread x width), WAIST (Q-47 A: width x hypot(goings x tread,
risers x riser) x thickness), LANDING (length x width x thickness), STAIR_BEAM, TURNING_STEPS / TURN_RISER (HELD),
FLOOR_LANDING (named, the floor slab owns it), later items FORMWORK / REINFORCEMENT / MARBLE_TREAD_AND_RISER / HANDRAILS
(named, not measured). The riser is the printed rise / the SECTION count (Q-46 A); plan counts are checks and every
difference is an RFI record; no section -> HELD (Q-50 open); winder and tapered steps -> HELD (Q-51 open, option-A
candidate shown, never released); a thickness is used only with a source and basis DETAIL or PANEL_TAG; a stair with
nothing measured totals None, never 0.

## Alsenan result (concrete, m3)

| Stair | Engine measured | Held lines (never 0) | Freelancer | Difference |
|---|---|---|---|---|
| Main stair, 2 storeys | 5.011 = steps 1.386 + waists 2.885 + landings 0.740 (= T-084 hand truth 5.011) | GF->1F winders (Q-51), 1F->2F turn riser (landing levels not printed), 2 'B3 (With Stair)' beams (length / levels not printed) | 8.131 | -3.120 (-38.4 %) |
| Entrance flight | steps 0.357 | waist (not in a slab panel, not printed) | 1.411 | -1.054 (-74.7 %), mostly the held waist |
| Hall -> +0.30 lobby flight | steps 0.126 | waist (not printed) | no row | hand-found, freelancer has none |
| Round stair | nothing measured | all: no section (Q-50), curved steps (Q-51), corner landing size not printed, B3 beam | 5.510 | not comparable (held) |
| Total | 5.494 | 15 held lines | 15.052 | - |

Verdict proposals: main stair RULE_DIFFERENCE / UNRESOLVED as in T-084 (his 5.3 m flights x 0.28 m "slab + steps" are not
on any drawing; the engine's figure is the owner-approved Q-46 A / Q-47 A basis, reproduced by the code exactly);
entrance UNRESOLVED (waist not printed); round stair UNRESOLVED (owner Q-50 / Q-51).

## Checks the run prints (never in a total)

- RFI riser counts: GF->1F section 27 vs plans 25 / 28; 1F->2F section 25 vs plans 27 / 24.
- Riser outside 0.155-0.165 (diagnostic only): 0.1667 (GF->1F), 0.168 (1F->2F), 0.170 entrance, 0.175 lobby flight.
- Arrival wedges at a floor slab (upper bound, shown not deducted): main stair 0.030 + 0.030, entrance 0.071, lobby 0.032.

## What we learned / open for the Lead

1. Double counting at junctions (owner Q-20 "no double counting" against the Q-46 A / Q-47 A figures): the wedge of a
   flight's last riser lies inside the landing or floor slab it arrives on, and the waist prism ends overlap the landing
   plates. On the approved basis both are counted; the piece computes the arrival-wedge part exactly (synthetic: 0.0245 m3
   per 1.10 m flight into a 150 mm landing) and shows it. Proposed owner question for the Lead (not asked by this run):
   deduct arrival wedges inside released landings / floors, or keep the approved prism basis.
2. On the GF -> 1F turn the five winders and the 1.20 x 1.25 landing at +3.50 share the same 1.20 x 1.20 corner of the
   plan (S8.7c by handle): when Q-51 releases winders, the winder plan area and the landing must not both carry concrete.
3. The frozen S8.7 release already carries 0.517 m3 of stair concrete (including a 0.2304 m3 landing at 160 mm): whoever
   wires STAIR_CONCRETE_V1 into a method must replace, not add to, the S8.7 stair lines.
4. Nothing of the round stair can be released until Q-50 and Q-51 are answered; its curved steps need a tapered-step rule.
