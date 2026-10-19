# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-19 10:15 UTC (Lead). Previous version: 2026-10-19 08:45 UTC.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | measured on Alsenan; capability matrix done; synthetic villas built and waiting for the verifier's merge; the apartment's drawing must be re-exported by you (your answer), the team is finding why the first conversion lost 57 % | at risk |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | room-label census merged: 11 of 41 Alsenan room labels (4 yards, 4 roofs, 2 pool, 1 void) are in no closed room; a guard is being built; your wet / dry answer turned into a new task; 9 finished checks wait for the verifier's merge | at risk |
| 2 | Blockwork, plaster, paint, tiles, doors, windows within target | 11 Nov | your answer on heights (slab 16 cm unless the drawing says otherwise; heights only from sections) and the readable architectural PDF unblock the height work, which starts now | not started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | curved strips merged; footing-edge guard finished (not yet merged); your answers on foundations, beams, typed values, stairs and founding level turned into five tasks | started |
| 4 | Read scanned and PDF plans | 9 Dec | the six architectural PDF parts are now read sheet by sheet (first real use) | not started |

## Engine vs freelancer BOQ: Alsenan Chalet (latest measured run, commit b5475db)
No engine change reached the measured run since the last report, so every measured number is unchanged.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.78 | 111.81 | -19.03 (-17.0 %) | none | within 2 % | footings -0.37; stairs + domes -9.83 (domes held by your order, stairs now to be split into steps, waist and landings); pool -8.85 (printed 0.40 m floor and D shape not yet used) |
| Concrete, footing edge band (part of the footing line) | m | 60.17 (frozen engine) | 71.7 | -11.53 m | new finding, not yet in the score | - | the new guard (not merged, not wired) reads 78.54 m measured (9.425 m3) + 13.40 m held under footings and columns (1.608 m3) of a 91.94 m band; which part is the boundary-wall footing, ground beam or isolated footing is now being identified (your Q-12 answer) |
| Concrete, the other 5 lines | m3 | held | - | - | none | within 2 % | 205 sub-lines held; 167 can be released only through the controlled data file you approved (Q-17), being built now |
| Rebar | t | not re-measured | 44.19 (earlier, not re-checked) | earlier estimate 26.24 t (-40.6 %) | none | within 3 % | freelancer uses kg per m3 allowances; rebar work not started |
| Blockwork | m | not re-measured | - | earlier estimate about 140 m short (-36.5 %) | none | within 3 % | gate 2 |
| Waterproofing | m2 | not re-measured | - | earlier estimate -19.1 % | none | within 3 %, no wet room missed | wet / dry rewritten on your answer (label first, sanitary drawing second) |
| Wall tile | m2 | not re-measured | - | earlier estimate about -15 % | none | within 3 % | same |
| Plaster | m2 | held | 1151.14 | - | none | within 3 % | heights to be read from the architectural sections (your Q-14 answer) |
| Paint | m2 | held | 1191.13 | - | none | within 3 % | same |
| Floor area | m2 | held | not compared | - | none | within 1 - 2 % | 3 rooms wait on wet / dry; 11 labelled spaces in no closed room |
| Doors, windows (aluminium) | m2 | refused | 12.0 / 116.9 | - | none | exact | engine counts pieces (2 doors, 27 windows), freelancer measures area |

## Engine vs freelancer BOQ: development project 2 (apartment)
Not measured: you will re-export its drawing to DXF (your Q-15 answer); meanwhile the team finds why the first conversion
lost 57 % of the drawing, and writes the check every new conversion must pass.

## What the team has learned so far
- There is no basement on the Alsenan drawings; the freelancer's "basement" concrete is two stairs and three domes.
- The pool floor is 0.40 m on the drawing (the engine used 0.25 m) and the pool is D-shaped; the engine counted only half.
- Arabic notes drawn in SHX fonts can now be decoded (121 of 121 in the real test); a second Arabic font family on the
  architectural room labels (47 labels) is still unread.
- The footing edge band was lost because the engine tested 5 sample points, not the covered length: members cover only
  29 % of the removed face, yet the whole 31 m face was dropped with no record.
- A size printed on the drawing always beats a usual size; where nothing is printed the line is held (your order).
- Your answers today: room label first for wet / dry; slab 16 cm unless shown otherwise, heights only from sections;
  beams, stairs and foundations sized only from drawing evidence, else held; typed values only through a controlled file
  with a status on every value; the founding level is held until the full level arrangement is verified.

## Being worked on now
- Worker 3 finished the footing-edge guard (the 31 m silent loss is now either measured or held, never lost); the
  verifier checks it next, then it is wired into the concrete run.
- Worker 2 is reworking the pool check list (pump room and main manholes) so a house water pump is not taken as the
  pool's pump room.
- Next for the workers: reading the 12 architectural sheets for levels, pool depth, stairs and any lift; splitting the
  footing line into isolated footings, boundary-wall footing and boundary-wall ground beam; the controlled data file for
  typed drawing values; the wet / dry evidence rules; why the apartment conversion lost 57 %.
- Worker 1 (after three idle runs) is building the room-label guard: every labelled space with no closed room becomes a
  held line instead of vanishing.
- Verifier: merging the 9 finished checks that wait only on the generated map (your instruction), then the guard.
- Research scout (tonight): reading floor and ceiling levels from sections, Arabic SHX font tables, storey detection.

## What is missing
- Printed wall heights per floor (being read from the architectural sections now).
- The apartment's DXF (from you).
- Your answer on the pool pump room question (new today).
- Nine finished checks are not yet on the working branch (merge order given to the verifier).

## Waiting for the owner
- New: how to tell the pool pump room from the house water pump room (A / B / C; recommendation A).
- The apartment's re-exported DXF (your Q-15 answer).
