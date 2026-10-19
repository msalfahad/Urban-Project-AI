# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-19 12:20 UTC (Lead). Previous version: 2026-10-19 10:15 UTC.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | done: Alsenan measured (re-measured today on the newest code), capability matrix, synthetic villas with hand truth merged. The apartment (development project 2) waits by your order; why its first conversion lost 57 % is now found and a check every new conversion must pass is written | done for Alsenan |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | the 11 Alsenan labelled spaces that were silently lost are now held and visible (guard merged, not yet in the released run); why the roofs, pool and void have no closed room is being traced; wet / dry evidence rules (your label-first answer) and the door / window count are next | at risk |
| 2 | Blockwork, plaster, paint, tiles, doors, windows within target | 11 Nov | heights rule set by you (slab 16 cm unless shown; heights only from sections); reading the 12 architectural sheets for levels is next | not started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | footing-edge guard and curved pool strips merged; next: put both into one new concrete run and measure Alsenan; foundations split by member (your answer), typed-value file, foundation levels | started |
| 4 | Read scanned and PDF plans | 9 Dec | started early for your renovation test (old building only as a PDF): the PDF plan reader and synthetic old / new villa pairs are now on the board | started |

## Engine vs freelancer BOQ: Alsenan Chalet (latest measured run, re-measured today on commit 8774071)
No merged change has reached the measured run yet (the new guards are not wired), so the numbers did not move.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.77 | 111.81 | -19.04 (-17.03 %) | none (rounding only: was shown 92.78) | within 2 % | footings -0.37; stairs + domes -9.83 (domes held and visible by your order; stairs to be split into steps, waist, landings); pool -8.85 (printed 0.40 m floor and D shape not yet used) |
| Concrete, footing edge band (inside the footing line) | m | 60.17 (released run) | 71.7 | -11.53 m | the new guard is now merged (not yet in the run) | - | guard reads a 91.94 m band: 78.54 m measured (9.425 m3) + 13.40 m held under footings and columns (1.608 m3); which part is boundary-wall footing, ground beam or isolated footing is identified next (your answer: report them separately) |
| Concrete, the other 5 lines | m3 | held | - | - | none | within 2 % | 205 sub-lines held; 167 can be released only through the controlled data file you approved, next on the board |
| Rebar | t | not re-measured | 44.19 (earlier, not re-checked) | earlier estimate 26.24 t (-40.6 %) | none | within 3 % | freelancer uses kg per m3 allowances; rebar work not started |
| Blockwork | m | not re-measured | - | earlier estimate about 140 m short (-36.5 %) | none | within 3 % | gate 2 |
| Waterproofing | m2 | not re-measured | - | earlier estimate -19.1 % | none | within 3 %, no wet room missed | wet / dry evidence rules on the board (label first, sanitary drawing second) |
| Roof waterproofing | m2 | none (roofs held, not lost) | 285 (roofs and annexes) | hand trace, not the engine: 204.10 inside parapets (-28.4 %) or 226.21 to their outer face (-20.6 %); +30.70 under the two domes | new | within 3 % | waits on your answer on the edge, the domes and closing small drafting gaps |
| Wall tile | m2 | not re-measured | - | earlier estimate about -15 % | none | within 3 % | same |
| Plaster | m2 | held | 1151.14 | - | none | within 3 % | heights to be read from the architectural sections |
| Paint | m2 | held | 1191.13 | - | none | within 3 % | same |
| Floor area | m2 | held | not compared | - | none | within 1 - 2 % | 3 rooms wait on wet / dry; 11 labelled spaces now held instead of lost |
| Doors, windows (aluminium) | m2 | refused | 12.0 / 116.9 | - | none | exact | engine counts pieces (2 doors, 27 windows), freelancer measures area; area lines and a tag census are next |

## Engine vs freelancer BOQ: development project 2 (apartment)
Not measured, and paused by your order (Alsenan first). Found: the free converter used so far keeps only 16 bits of each
object number, so 12,567 objects collide and 57 % of the drawing is lost; with that fixed, 48,574 of 48,576 objects come
through exactly. A conversion check is written; your re-exported DXF must pass it before anything is measured.

## What the team has learned so far
- There is no basement on the Alsenan drawings; the freelancer's "basement" concrete is two stairs and three domes.
- The pool floor is 0.40 m on the drawing (the engine used 0.25 m) and the pool is D-shaped; the engine counted only half.
- The footing edge band was lost because the engine tested 5 sample points, not the covered length; the new guard keeps
  every face (measured, or held under a footing), never lost.
- 11 of 41 Alsenan room labels lie in no closed room (yards, roofs, pool, void); they are now held, not dropped.
- A plain "PUMP" room is not the pool pump room (your answer); Alsenan has no pool pump room.
- Arabic SHX notes can be decoded (121 of 121); a converted DWG can hide thousands of invisible texts inside door and room
  blocks that a reader must skip (none on Alsenan).
- No Urban rule exists yet for renovation work (demolition, retained walls); asked you before any measuring.

## Being worked on now
- Worker 2 finished why the Alsenan roofs, pool and void have no closed room (the verifier checks it next): roof
  waterproofing by hand is 204.10 m2 inside the parapets or 226.21 m2 to their outer face, against the freelancer's
  285 m2 (-28.4 % / -20.6 %); which edge counts is your decision (new question).
- Worker 1: reading the 12 architectural sheets (levels per floor, pool depth, stairs, lift, domes).
- Next free workers: splitting the footing line into boundary-wall footing, ground beam and isolated footings; putting the edge guard and
  curved strips into one new concrete run and measuring Alsenan with it; doors and windows in m2 and a tag census.
- Verifier: checking the apartment conversion study, then each new result; scoreboard re-measured after every merge.
- Research scout (tonight): floor and ceiling levels from sections, structural schedules, and comparing an old PDF plan
  with a new CAD plan for the renovation test.

## What is missing
- Printed wall heights per floor (being read from the architectural sections next).
- Worker 3 cannot push its work (permission refusals in three runs); the other two workers cover its tasks.
- Rules for the renovation test (your answer).
- The apartment's DXF (paused by your order).

## Waiting for the owner
- New: roof waterproofing edge (inside the parapet or to its outer face) and the domes (A / B / C and i / ii / iii;
  recommendation A with ii, domes as their own line when the detail shows it).
- New: may a parapet line that stops 0.075 - 0.405 m short of the wall be closed (recommendation: yes up to 0.50 m, each
  closure listed).
- New: which items the renovation BOQ must contain and how retained walls are finished (A / B / C and i / ii / iii;
  recommendation A with iii).
- Worker 3's permission setting (see the lead report).
