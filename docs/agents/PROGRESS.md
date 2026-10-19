# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-19 14:30 UTC (Lead). Previous version: 2026-10-19 12:20 UTC.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | done: Alsenan measured on the newest code, capability matrix, synthetic villas with hand truth; the apartment waits by your order (its conversion check is written) | done for Alsenan |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | the 11 lost Alsenan spaces are held and visible; the roofs can now be measured on your rule (inside the parapet + 20 cm upturn, gaps covered); wet / dry evidence rules and the door / window m2 lines are next | at risk |
| 2 | Blockwork, plaster, paint, tiles, waterproofing, doors, windows within target | 11 Nov | all 12 architectural sheets listed, printed floor levels read (+1.00 / +5.50 / +9.70, roof +13.90); your membrane purchase table (every wet area, rolls to buy) is on the board with a hand table of every Alsenan wet area | started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | new concrete ledger built (finished, waiting for the checker): the footing band is back to its drawn 91.94 m and the pool ring is right; footings split by member by hand; pool now set by you (flat, 1.15 m); stairs, beams and foundation levels are next | started |
| 4 | Read scanned and PDF plans | 9 Dec | the PDF plan reader stays on the plan as a general capability; the renovation preparation is dropped (no test villa) | waiting its turn |

## Engine vs freelancer BOQ: Alsenan Chalet (latest measured run, commit 8774071; no new measurement this run)
The released run did not change since 12:10. The new concrete ledger below is a worker result that the checker has not
yet verified; it is opt-in and does not change the released run.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.77 | 111.81 | -19.04 (-17.03 %) | none | within 2 % | footings -0.37; stairs + domes -9.83; pool -8.85. With the new ledger (not yet verified) footings and pool become HELD until their section / depth rules are applied, leaving 1 compared line (stairs + domes 12.01 vs 21.83) |
| Footings by member, by hand (not yet in the engine) | m3 | isolated footings 64.346 (= engine register) | 65.634 | -1.29 (-2.0 %) | new | within 2 % | engine right on two counts: the freelancer counts one footing twice (0.672 m3) and one at its schedule size while drawn larger (asked as an RFI) |
| Foundation straps, by hand | m3 | 3.391 by hand (engine run 3.781) | 3.3925 | hand = freelancer; engine +0.39 untraced | new | within 2 % | the +0.39 m3 in the engine is traced next |
| Boundary band at foundation level | m | 91.94 drawn (released run 60.17) | 71.7 | released run -11.53 m | new ledger recovers the drawn length (not yet verified) | - | 21.45 m runs inside footings; which section (20 x 60 or 20 x 40 with pads) and whether the part inside footings counts: your new question; volume held until then (8.46 m3 on the recommended option vs freelancer 8.60) |
| Boundary ground beam at natural ground | m3 | 3.526 by hand | 7.560 | -4.03 (-53.4 %) | new | within 2 % | printed 20 x 40 over 44.07 m; the freelancer uses 30 x 60 over 42 m; the engine line is checked next (possible silent omission) |
| Concrete, the other 5 lines | m3 | held | - | - | none | within 2 % | 167 sub-lines release only through the controlled data file you approved (on the board) |
| Pool | m3 | 3.50 (released) | 12.35 | -8.85 | your answer: flat floor at the printed 1.15 m depth, 0.40 m floor | within 2 % | new ledger has the ring right (wall plan 2.357 m2, floor 10.936 m2); volumes from the printed sizes are next |
| Domes | m3 | held (by your order) | 6.78 (3 domes) | - | you confirmed three domes | - | you wrote the domes will not be concrete while the structural sheets draw two shells: new question |
| Rebar | t | not re-measured | 44.19 (earlier, not re-checked) | earlier estimate 26.24 t (-40.6 %) | none | within 3 % | not started |
| Blockwork | m | not re-measured | - | earlier estimate about 140 m short (-36.5 %) | none | within 3 % | gate 2 |
| Wet-area waterproofing | m2 | not re-measured | - | earlier estimate -19.1 % | none | within 3 %, no wet room missed | membrane table per wet area (your requirement) and a hand table of every wet area are on the board |
| Roof waterproofing | m2 | none (roofs held, not lost) | 285 (roofs and annexes) | hand trace: 204.10 inside the parapets (-28.4 %), + upturns | your rule set (like a bathroom) | within 3 % | the engine piece is next; the 30.70 m2 under the domes waits on the dome question |
| Wall tile | m2 | not re-measured | - | earlier estimate about -15 % | none | within 3 % | same |
| Plaster | m2 | held | 1151.14 | - | none | within 3 % | floor levels read; heights from the sections next |
| Paint | m2 | held | 1191.13 | - | none | within 3 % | same |
| Floor area | m2 | held | not compared | - | none | within 1 - 2 % | 3 rooms wait on wet / dry; 11 labelled spaces held instead of lost |
| Doors, windows (aluminium) | m2 | refused | 12.0 / 116.9 | - | none | exact | engine counts pieces, freelancer measures area; area lines and a tag census on the board |

## Engine vs freelancer BOQ: development project 2 (apartment)
Not measured, and paused by your order (Alsenan first). The conversion check is written; your re-exported DXF must pass it
before anything is measured.

## What the team has learned so far
- There is no basement on the Alsenan drawings; the freelancer's "basement" concrete is two stairs and three domes.
- The footing band is drawn closed all round the plot (91.94 m); the released engine loses one whole side (60.17 m kept).
- The freelancer counts one footing twice and another at its schedule size although drawn larger; the engine is right on both.
- Footings drawn as inserted blocks or as open outlines are not seen as footings by the engine yet (8.05 m of band affected).
- The pool is D-shaped with a 0.40 m floor, flat at 1.15 m (your answer); the engine counted only half of its ring.
- 11 of 41 Alsenan room labels lie in no closed room (yards, roofs, pool, void); they are held, not dropped. The roof
  outlines are on a layer the room builder ignores, and the parapet lines stop 7.5 - 40.5 cm short of the walls.
- Arabic SHX notes can be decoded (121 of 121).

## Being worked on now
- Checker (next run): the new concrete ledger and the footings-by-member reading; both merge if they pass.
- Worker 3: foundation levels, column and neck heights read by hand from the structural sheets.
- Next free workers: your membrane purchase table (every bathroom, roof and wet area, rolls to buy) with a hand table of
  every Alsenan wet area as its proof; roofs measured on your rule; pool and dome concrete from the printed sizes; stairs
  as steps, waist and landings; foundation members at the plot edge as separate lines; beams by hand.
- Research scout (tonight): section heights, schedules, footings drawn as blocks, and roll cutting with offcuts reused.

## What is missing
- Printed wall heights per floor (from the architectural sections).
- Two architectural PDF parts (pages 3-4 and 9-10) are too big for the Drive reader; the stair section may be there.
- Workers 2 and 3 still cannot run the engine's code (they do hand-reading tasks meanwhile).
- The apartment's DXF (paused by your order).

## Waiting for the owner
- Boundary band at foundation level: which section, and is the part inside a footing counted again (new; recommendation:
  the 20 x 60 schedule beam, not counted again inside footings: 8.46 m3).
- Domes: concrete or a finish, and does the roof membrane run under them (new; recommendation: not concrete, membrane
  stops at each dome base with a 20 cm upturn, RFI to the designer).
- Kitchens: waterproofed like a bathroom, floor only, or not at all (new; recommendation: like a bathroom).
- Upload the architectural PDF pages 3, 4, 9 and 10 as single pages.
