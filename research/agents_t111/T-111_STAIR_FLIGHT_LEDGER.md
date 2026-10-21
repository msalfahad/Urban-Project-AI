# T-111 Alsenan stairs flight by flight, and the stair / landing intersection ledger (NO REPO CODE)

Worker 1 (structural lane), 2026-10-21. Development villa, not an accuracy claim. Nothing is wired and no released
quantity changes: these are checked pieces for the V3.0 candidate (lane I).

Sources (Drive "Alsenan chalet project", scratchpad copies, never committed): architectural DXF
(P7757_DXF_COMPRESSED.zip, sha ab54dd55), structural DXF (ST7757 dxf.dxf, sha 9f9d1179), p7757_arch_sheet10.pdf
(section A-A), Alsenan_Architectural_P7757_Pages_11-12 (section B-B), p7757_arch_sheet03.pdf / sheet04.pdf (GF / 1F
plans), ST7757.pdf. Second source for the structural side: the frozen study research/alsenan_stairs_s8_7c (by DXF
handle). Rules: owner Q-19, Q-20, Q-46 A, Q-47 A, Q-50 A cond, Q-51 A cond, Q-62 A cond, Q-66 B, Q-70 A cond,
UP-STAIR-002, UP-STAIR-009, UP-KB-PREC-001, UP-QTY-STATUS-001.

Files: `stair_flight_ledger.py` (the ledger; reads no drawing), `read_stair_cad.py` (re-derives the plan readings
from the architectural DXF: counts, pitches, lengths, dimension values only), `FLIGHTS.csv` (one row per flight,
owner and drawn method side by side), `INTERSECTIONS.csv` (the Q-62 ledger), `ledger_summary.json`.

## 1. Result in engineering terms (concrete, m3)

| Stair | Freelancer | Owner method as approved (STAIR_CONCRETE_V1) | Owner method after the intersection ledger | Drawing-derived method after the ledger | Held, never 0 |
|---|---|---|---|---|---|
| Main stair, GF -> 1F -> 2F | 8.131 | 5.011 (-38.4 %) | **4.920** (-3.211, -39.5 %) | **4.746** (-3.385, -41.6 %) | winder steps (cand. 0.120 .. 0.130), slab under the winders (cand. 0.230 .. 0.250, NEW line), 1F->2F closing riser, 2 'B3 (With Stair)' beams, head clash 0.115 |
| Entrance flight | 1.411 | 0.357 (-74.7 %) | 0.357 (unchanged) | 0.357 | waist (no thickness printed); arrival wedge 0.071 shown, not deducted |
| Hall -> +0.30 lobby flight | no row | 0.126 | 0.126 | 0.126 | waist; arrival wedge 0.032 shown, not deducted |
| Round reception stair | 5.510 | all HELD | - | CALCULATED 1.620 - 0.059 ledger = **1.561** (straight flight, corner landing, short flight) | 12 curved treads (cand. steps 0.330 + helicoid soffit not drawn), beam CA junction |

Change since the last report (T-105 / T-056 run: main 5.011, round all held): main stair -0.090 m3 of concrete counted
twice is now located and assigned (and -0.174 more by the drawing geometry); the round stair's straight flight, corner
landing and short flight are verified flight by flight and can be CALCULATED under Q-50 A (1.561 m3 net).

## 2. Flight table (one row per flight; FLIGHTS.csv has the evidence text)

| Flight | Levels | Risers / riser | Treads drawn | Going | Width | Waist / landing | Structural ref | Owner m3 | Drawn m3 |
|---|---|---|---|---|---|---|---|---|---|
| MS1-L main GF -> turn | +1.00 -> +2.667 | 10 x 0.16667 (A-A) | 9 straight (2.70 m) | 0.300 | 1.20 | T 16 waist | GF roof panel T 16, 8 d16/m | steps 0.300, waist 0.659 | steps 0.270, waist 0.593 |
| MS1-T turn (NW quarter) | +2.667 -> +3.50 | 5 (A-A) / 4 wedges (plans) | 1.44 m2 quarter | - | 1.20 x 1.20 | soffit not drawn | none | HELD | HELD (0.120 .. 0.130) + NEW slab line HELD |
| MS1-LD half landing (NE quarter) | +3.50 | - | 1.20 x 1.20 | - | - | T 16 | panel tag | 0.240 (1.25 x 1.20) | 0.2304 (1.20 x 1.20) |
| MS1-U main landing -> 1F | +3.50 -> +5.50 | 12 x 0.16667 (A-A, counted this run) | 11 (plan 10) | 0.300 | 1.20 | T 16 waist | B20 40 x 75 at the head | steps 0.360, waist 0.741 | steps 0.360, waist 0.725 |
| MS2-L main 1F -> quarter | +5.50 -> +7.516 | 12 x 0.168 | 11 (3.30 m, DXF dimension 3300) | 0.300 | 1.20 | T 16 waist | 1F roof panel T 16 | steps 0.363, waist 0.743 | steps 0.363, waist 0.726 |
| MS2-TR closing riser | +7.516 -> +7.684 | 1 (A-A) | - | - | 1.20 | - | - | HELD | HELD |
| MS2-LD half landing | +7.516 / +7.684 | - | 2.50 x 1.20 | - | - | T 16 | panel tag | 0.500 (2.50 x 1.25) | 0.480 (2.50 x 1.20) |
| MS2-U main landing -> 2F | +7.684 -> +9.70 | 12 x 0.168 (A-A, counted this run) | 11 (plan 10) | 0.300 | 1.20 | T 16 waist | B23 45 x 75 at the head | steps 0.363, waist 0.743 | steps 0.363, waist 0.726 |
| E1 entrance | +0.15 -> +1.00 | 5 x 0.170 | 4 (floor = 5th) | 0.300 | 2.80 (DXF 2800) | waist HELD | not in a panel | 0.357 | 0.357 |
| D1 hall -> lobby | +0.30 -> +1.00 | 4 x 0.175 | 3 (floor = 4th) | 0.300 | 1.20 | waist HELD | - | 0.126 | 0.126 |
| RS-C round, curved | +1.00 -> +2.929 | 12 x 0.160714 | 12 tapered, 4.108 m2 | 7.79 deg | 1.15 tread lines | helicoid HELD | T 16 panel | HELD | HELD (cand. 0.330) |
| RS-S round, straight | +2.929 -> +4.696 | 11 x 0.160714 | 10 + corner landing | 0.300 | 1.20 (DXF 1200) | T 16 waist | CA 30 x 50 across (level not stated) | HELD | steps 0.318, waist 0.653 |
| RS-LD corner landing | +4.696 (reconstructed) | adds no rise | 1.25 x 1.15 - 0.0275 | - | - | T 16 | panel tag | HELD | 0.226 |
| RS-A round, short flight | +4.696 -> +5.50 | 5 x 0.160714 | 4 (floor = 5th) | 0.300 | 1.25 (DXF 1250) | T 16 waist | arrival plate C-T1 | HELD | steps 0.151, waist 0.272 |

## 3. What the drawing geometry settles (the owner's conditions)

**Round stair (Q-50 A cond), each check answered from the drawings:**
- Arrival floor is the last tread: yes. The 1F plan draws 5 riser lines in the short flight (0.300 pitch, 1.20 m
  first to last) and '+5.50' is printed at the arrival beyond the 5th line: 5 risers, 4 treads + the floor.
- The corner landing adds no rise: both its edges are drawn riser lines (the 23rd, last straight, and the 24th, first
  of the short flight); it is a tread of 1.25 x 1.15 m at +4.696.
- 12 curved, 11 straight, 5 further are distinct: three disjoint line sets: 12 radial lines about one centre (pitch
  7.79 deg on GF and 1F alike, tread ends r 1.581 / 2.731 m), 11 straight lines at 0.300 (3.00 m first to last), 5
  short-flight lines. 12 + 11 + 5 = 28 risers; treads 12 + 10 + landing + 4 + floor.
- Architectural and structural plans agree: GF and 1F architectural plans identical (the GF plan shows 4 of the 5
  short-flight lines, beyond its cut); structural GF roof sheet 12 + 11 + landing + 5 (S8.7c R-02).
- Start and end levels: '+5.50' printed at the arrival (1F plan). The foot is on the GF reception floor: no level is
  printed inside the reception, but the reception is open to the dining area where '+1.00' is printed 2.6 m from the
  foot, with no step, riser or wall line drawn between (DXF), and section B-B draws the GF floor at one level +1.00.
  Riser 4.50 / 28 = 0.160714 m holds on that evidence; the foot level is recorded as "+1.00 by the continuous GF
  floor, not printed at the foot".
- Independent re-derivation of the 0.469 m3: straight 11 x 1/2 x 0.160714 x 0.300 x 1.20 = 0.318214 (width = the
  DXF dimension 1200 measured across the flight), short 5 x 1/2 x 0.160714 x 0.300 x 1.25 = 0.150670 (width = DXF
  dimension 1250 wall to wall): **0.468884 m3, confirmed**. Labelled "reconstructed, no section".
- Curved part stays HELD (owner): candidate tread areas from the CAD boundaries, treads 1-11 0.3371 m2 each, tread 12
  (to the tangent point and the first straight riser) 0.3996 m2, total 4.1077 m2; candidate wedges 1/2 x 0.160714 x
  4.1077 = 0.330 m3; the helicoid soffit is not drawn (Q-51 step 5).

**Main-stair winders (Q-51 A cond):** the 1.44 m2 is the real plan area of the turn on the same wall-to-wall basis as
the 1.20 m flights: the NW quarter from the 10th riser line to the north wall's inner face (DXF dimension 1200 on the
1F and 2F plans; GF 5000 = 1100 foot + 2700 flight + 1200) by west wall to central-wall face (DXF 1200). It holds no
landing and no void (the half landing is the NE quarter, 1.20 x 1.20, beyond the central wall). The narrower
tread-line basis (lines stop 50 mm short of the central wall) gives 1.3225 m2 in 4 drawn wedges (0.2944 / 0.3669 /
0.3674 / 0.2938 m2). The sum 1/2 x riser x total area does not depend on whether the turn has 4 treads (plans) or 5
(section). Not settled: the 0.10 x 1.20 m well strip between the quarter and the drawn closing riser (0.12 m2, turn
or landing), and no soffit is drawn for the wedge-over-uniform-waist model. So the turn stays HELD with candidate
0.120 .. 0.130 m3; and the slab under the winders is in NO line of the owner census (a silent omission, now a HELD
line, candidate 0.230 .. 0.250 m3 as a horizontal projection).

**Landing sizes:** the '125' the census read as the landing depth is the outer-wall dimension chain (north wall outer
face to the window jamb, 1.25 m; its DXF dimension is a text override with no measured length). The landings
measured on the CAD: GF -> 1F half landing 1.20 x 1.20 = 1.44 m2 (the same 1.44 the structural study finds by
handle); 1F -> 2F half landing 2.50 x 1.20 = 3.00 m2. Owner method 0.240 + 0.500 m3, drawn 0.2304 + 0.480 m3.

**Lower flight GF -> 1F:** the drawn straight run is 9 goings (2.70 m) up to the turn line, not the 10 goings (3.00 m)
of the census: the 10th riser's tread is the first turn tread. Owner method steps 0.300 / waist 0.659, drawn
0.270 / 0.593 (the 10th wedge belongs to the held turn; nothing is lost).

**Upper flights (Q-46 A):** counted again this run on the hatched cut flights of section A-A: 12 risers / 11 treads
on both storeys, each arriving with the floor as the 12th tread. The 1F and 2F plans print 1950 (floor landing) +
3300 (flight zone) + 1200 (turn) = 6450 m dimensions (DXF measured): the west flight fills the 3300 with 12 riser
lines; the east flight is drawn with 11 lines and stops 0.30 m short of the 1950 landing edge. Under the section
count the east flight's 12th riser lies exactly on that landing edge, so **the 0.4025 m2 strip (designer point D-13)
is the east flight's 11th tread plus its nosing band, a FLIGHT row, not landing**; the 1F landing stays 2.50 x 1.95 =
4.875 m2. On 2F the same dimension chain bounds the arrival: **Q-70 A polygon confirmed: 2.50 x 1.95 = 4.875 m2 from
the landing edge line, no overlap with the flight rows** provided the marble flight rows count 11 treads per upper
flight (the engine's tread lines count the plans' 10: 0.30 x 1.15 m per lane per floor is then in no row).

**2F west lane (T-135 held 0 .. 3.450 m2 / 0 .. 11.50 lm):** it is the 1F -> 2F lower flight seen through the stair
opening, not a 2F flight. On the 2F plan its nosing set has 12 lines over 3.30 m, line for line the 1F flight's set
(same along-flight positions; the 2F floor-edge line lies on its first riser line, which is why the engine read 10
treads and 0.300 m short); the 2F roof slab draws no stair (T-135). **Proposal: SEEN_ABOVE, 0 on 2F; once-only tread
lines 20.424 m2 / 68.028 lm (the low end of T-135's range) can be released.**

## 4. Intersection ledger (Q-62 A cond): each piece once

Model: each flight end in its vertical profile with the plate or beam it meets; the overlap area x the flight width is
the 3-D intersection (plates and head beams span the full width). Steps are the Q-19 wedges above the root line
(inner corners), the waist the strip under it (perpendicular 0.16), plates T 16, head beams from the structural plan
(S8.7c: the section's 12th riser lies 0.20 m inside B20 / B23).

| Flight end | Partner | Overlap m3 | Assigned to | Action |
|---|---|---|---|---|
| MS1-U head (1F floor) | B20 + 1F slab | 0.030000 | B20 / slab | DEDUCT from the stair (Q-62 A) |
| MS2-U head (2F floor) | B23 + 2F slab | 0.030240 | B23 / slab | DEDUCT |
| MS2-L top (flat quarter +7.516) | half landing MS2-LD | 0.030171 | landing | DEDUCT; **NEW**: both are measured lines of the 5.011; STAIR_CONCRETE_V1 checks arrival wedges only when the next census part is a LANDING, and a TURN_RISER part sits between |
| MS1-U head, last 0.20 m of tread 11 and waist | B20 (drawn clash) | 0.057261 | - | HELD: the section's flight runs into the beam; a design conflict (designer RFI, Q-46), not a convention |
| MS2-U head, same | B23 (drawn clash) | 0.057451 | - | HELD (same RFI) |
| MS1-T closing riser into the landing | MS1-LD | 0.029952 | landing | none now (turn HELD); deduct when the turn is released |
| E1 top | GF floor at the porch | 0.071400 | - | shown, not deducted: the GF floor there is on fill with no thickness printed and no measured concrete line to assign it to |
| D1 top | GF hall floor | 0.031500 | - | shown, not deducted (as E1) |
| RS-S top | corner landing RS-LD | 0.028928 | landing | DEDUCT (both CALCULATED here) |
| RS-A head | arrival plate C-T1 (S8.7 release) | 0.030133 | plate | DEDUCT when both are wired |
| RS-S at beam CA | CA 30 x 50 | 0 .. ~0.09 | CA | HELD: the CA level is not stated |
| every flight foot | plate below | 0 | - | the volumes only touch along the riser line; the soffit knee under each plate edge is 0.0005-0.0006 m3 (check, in neither line) |

Owner figures checked: "main stair 5.011 - 0.060 = 4.951" is **not confirmed**: the two floor-arrival wedges (0.060)
are real, but the 1F -> 2F lower flight's wedge on the flat quarter (0.030) is a third overlap inside the same 5.011,
so the main stair is **5.011 - 0.090 = 4.920 m3** on the owner basis, with 0.115 m3 more inside B20 / B23 held on the
clash. "0.163 m3 over all stairs" is **not confirmed as a deduction**: 0.090 (main) + 0.059 (round, when wired) are
deducted; the entrance and lobby wedges (0.103) have no measured partner volume and stay shown.

## 5. Who is right (proposals for the verifier)

- Main stair, owner basis 4.920 vs freelancer 8.131 m3 (-39.5 %): ENGINE_RIGHT on geometry / RULE_DIFFERENCE on
  method. Hand: the printed flight zone is 3.30 m horizontal (DXF dimension 3300, 1F and 2F), sloped 3.78-3.87 m; his
  5.3 m flights are on no drawing and his 0.28 m "slab + steps" depth is not printed (T 16 is). His 3 landings x 1.2 x
  1.4 x 0.20 vs drawn 2 half landings 1.44 + 3.00 m2 at T 16 plus the turn quarter.
- Entrance 0.357 vs 1.411 (-74.7 %): UNRESOLVED (waist not printed; his 1.8 m run vs drawn 1.20 m plan run).
- Round stair: UNRESOLVED while the curved part is held; on the verified part 1.561 m3 CALCULATED + held curved part
  vs his 5.510 m3 (1.2 x 16.4 x 0.28; the drawn walking-line length is not 16.4 m: 12 x 0.293 + 3.00 + 1.15 + 1.20
  = 8.87 m at the walking line).
- Lobby flight 0.126: HAND_FOUND, no freelancer row.

## 6. What we learned (every villa)

1. A printed number next to a stair is not a stair dimension until its dimension line is traced: the landing '125'
   was an outer-wall pier dimension (a text-override dimension with no measured length). Read the DXF dimension's
   definition points, not the text.
2. Arrival wedges sit inside the next plate wherever a flight ends on one, including a flat quarter reached through a
   turn riser: the check must look at the plate the last riser lands on, not at the next census part.
3. When the section adds a riser that the plan does not draw (12 vs 11), the extra tread lands on the floor-landing
   edge or inside the head beam: the plan's dimension chain (1950 + 3300 + 1200) shows which, and the beam overlap is a
   designer clash, never a deduction convention.
4. The sum of winder wedges is 1/2 x riser x the turn's plan area whatever the tread count, so a 4-vs-5 winder count
   conflict does not move the step concrete; only the turn area and its soffit do.
5. A turn (winder) zone needs its own slab line: no line covered it.

## 7. Held / missing (owner or designer)

- Winder turn: well strip (0.12 m2) turn or landing; soffit of the turn not drawn (designer detail).
- B20 / B23 head clash (0.115 m3) with the section's 12-riser upper flights (designer RFI, already under Q-46).
- 1F -> 2F closing riser and the two landing levels (+7.516 / +7.684 scaled, not printed).
- Entrance and lobby waists (no thickness printed) and their arrival wedges (no measured GF floor line).
- Round stair: curved treads and helicoid soffit (owner HELD), beam CA level (engineer), 'B3 (With Stair)' beams.
- No owner question is added: every hold above is an existing rule's HELD state or a designer point already open.
