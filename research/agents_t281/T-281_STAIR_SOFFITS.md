# T-281 Stair soffits per flight and landing, from the drawn goings, risers and landing polygons (Alsenan; every villa)

Worker 1 (lane S), 2026-10-25, run started 03:20 UTC. Research piece, not wired: no engine, candidate, released line,
rule or knowledge file changed; integration is a lane I package after the Checker's verdict. Development villa, not an
accuracy claim. Drawings named by Drive folder and title; members by DXF handle; lengths, areas and angles only (no
coordinates committed). ERS s.2.1-2.4, s.3, s.4, s.7 applied. Governing: OWNER_RULE_STAIRS_2026-10-21 (S-1 drawing
governs) and 2026-10-24 (S-9 no generated winders / walking line; corrections 1-2 actual polygons; one verified stair
geometry for every BOQ item; HELD blank), UP-STAIR-002, Q-47 A (waist = printed T 16), Q-50 A cond (ST-02 riser), Q-51,
Q-61 C ('B3 (With Stair)'), Q-62 A cond, R-STAIR-LAND-1, R-STAIR-LANE-1, R-STAIR-LANDING-EDGE-1.

## 0. Inputs (own reads this run)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179... (= manifest) | p.4 GF roof slab plan (ST-01 GF -> 1F, ST-02), p.5 1F roof slab plan (ST-01 1F -> 2F), p.3 ground-beam plan (lobby flight D1, levels +0.30 / +1.00) by handle (`t281_extract.py`); T-139 faces re-polygonised from the same file (`research/agents_t139/slab_faces.py`) for the zone reconciliation |
| "P7757_DXF_COMPRESSED.zip" -> P7757.dxf | ab54dd55... (= manifest) | GF plan of the ST-01 shaft (column-fit translation of T-271): what is below each MS1 piece (court-door lobby +0.30, lobby flight, hall floor +1.00), the architectural MS1-L riser lines |

Merged evidence built on, cited, not re-derived: T-184 inventory (924c2bd), T-258 stair ledger r2 (lanes, landing
plates, riser bases, MS2-LD split, column 374, R-STAIR-LANE-1), T-139 slab faces, T-271 r2b ceiling ledger (789ebbb4:
GF stair zone 7.402 + strips 2.451, 1F stair zone 10.725 HELD as stair soffit; GF stair room 12.475 kept apart), T-248
column CONFLICT list (D-16: GF 380, 1F 691).

## 1. The physical element (ERS s.2.1) and the two methods

The soffit of a stair is the underside of its waist (an inclined plane parallel to the pitch line, the waist thickness
below the line through the inner step corners) and of its landing plates (flat). It is a finish surface of the stair,
seen from the space below it, never a decor ceiling of that space. Its plan-projected area is what a ceiling ledger
must not ceil; its true (developed) area is what a finish is applied to.

No owner rule measures a stair soffit, so both methods are shown and nothing is chosen for size (ERS s.2.2):

* **Method O (owner region)**: the owner's concrete region carried over to the underside: a flight from its first to
  its last riser line (Q-47 A), or to the face of the beam it bears on / arrives into (Q-62 A cond: what is inside the
  beam is the beam's); landings = their drawn polygons (S-9 correction 2), flat. True area = plan x sec(theta),
  sec = hypot(going, riser) / going: needs only the riser and the going.
* **Method D (drawing-derived physical planes)**: the waist soffit z0 + (r / g) s - t sec meets a landing plate's
  soffit at the foot s = (g / r)(t sec - tL) past the first riser line and at the head s = g + (g / r)(t sec - tL) past
  the last one (the arrival wedge region: the sloped soffit runs on under the landing edge); on a ground slab it rises
  out of the slab at s = (g / r) t sec (the strip before it bears on the slab: no soffit); on a beam it stops on the face,
  checked above the beam bottom. Needs riser, going and the printed waist (T 16).

The plan is one partition: both methods only move strips between rows (flat <-> sloped, soffit <-> slab-borne);
`partition_check` refuses an unnamed residual.

## 2. Ledger (LEDGER_T281.csv, 29 rows; m2; nothing released)

**ST-01, dog-leg beside the lift.** Riser 4.50 / 27 (GF -> 1F) and 4.20 / 25 (1F -> 2F) printed (section A-A), going
0.300, waist T 16; sec 1.143959 / 1.146124.

| Piece | Plan O | True O | Plan D | True D | Status | Space below |
|---|---|---|---|---|---|---|
| MS1-L lower flight | 3.215 .. 3.935 | 3.677828 .. 4.501478 | 2.819648 .. 3.539648 | 3.225561 .. 4.049212 | **CONFLICT** (C-ST-4: structural 12 lines from 45A vs architectural 10 from DE, 0.600 later); slab-borne foot 0.395352 in D; column 36B 0.025 no soffit | GF stair room, west lane over the hall floor +1.00 |
| MS1-T winder turn | 1.495 | HELD | 1.495 | HELD | plan DRAWING-CONFIRMED; warped soffit not drawn (C-ST-3, S-9) | GF stair room, NW corner |
| MS1-LD half landing +3.50 | 1.440 | 1.440 | 1.440 | 1.440 | DRAWING-CONFIRMED | GF stair room, east lane over the court-door lobby +0.30 |
| MS1-U flight to 1F | 3.720 | 4.255527 | 3.720 | 4.248365 | DRAWING-CONFIRMED (25B -> B20 face 3.100; foot kink 0.041460 flat) | GF stair room, east lane over the lobby, lobby flight D1, hall +1.00 |
| GF well (open) | 0.315 | 0 | 0.315 | 0 | no soffit | open to above |
| MS2-L flight from 1F | 3.755 | 4.303695 | 3.755 (+ 0.410100 head kink) | 4.303695 (+ 0.470025) | DRAWING-CONFIRMED (B20 face -> 632; head kink 0.341750 under MS2-LD-W) | ST-01 shaft void over MS1-L / MS1-T |
| column 691 in the MS2-L lane | 0.025 | HELD | 0.025 | HELD | exposure HELD (T-248 D-16 CONFLICT) | same |
| MS2-LD-W +7.516 | 1.495 | 1.495 | 1.084900 | 1.084900 | DRAWING-CONFIRMED | shaft void over MS1-T |
| MS2-TR turn riser step + well end | 0.005 | HELD | 0.005 | HELD | junction of the two plates 0.168 apart not drawn (C-ST-3) | shaft void |
| MS2-LD-E +7.684 | 1.440 | 1.440 | 1.440 | 1.440 | DRAWING-CONFIRMED | shaft void over MS1-LD |
| MS2-U flight to 2F | 3.720 | 4.263581 | 3.720 | 4.256260 | DRAWING-CONFIRMED (62F -> B23 face; foot kink 0.041750 flat) | shaft void over MS1-U |
| 1F well (S-OPENING 62D / 62E) | 0.310 | 0 | 0.310 | 0 | no soffit | open to above |
| **ST-01 measured rows** | **17.070** | **17.197803** | **17.070** | **17.243246** | + MS1-L CONFLICT + winder / junction 1.500 plan HELD true | |

**ST-02, round reception stair.** Riser 4.50 / 28 ASSUMED — OWNER-APPROVED (Q-50 A cond), going 0.300, waist T 16,
sec 1.134456.

| Piece | Plan O | True O | Plan D | True D | Status |
|---|---|---|---|---|---|
| RS-C curved flight (12 curved treads, 2EA -> 2BA between arcs r 1.530511 / 2.780511, wall 283) | 4.443156 | HELD | 4.443156 | HELD | plan DRAWING-CONFIRMED; helicoid soffit not drawn (Q-51, C-ST-3, S-9) |
| RS-S straight flight, waist | 1.845 | 2.093071 | 1.845 (+ 0.195591 head kink) | 2.093071 (+ 0.221889) | ASSUMED — OWNER-APPROVED |
| RS-S: 'B3 (With Stair)' band underside | 1.100 | HELD | 1.100 | HELD | stair beam, Q-61 C |
| RS-S: CA member 54E underside | 0.345 | HELD | 0.345 | HELD | CA level not stated (T-258) |
| RS-S: column 380 exposure | 0.040 | HELD | 0.040 | HELD | T-248 D-16 CONFLICT |
| RS-S: hidden pair 535 / 536 | 0.270 | HELD | 0.270 | HELD | UNKNOWN (layer 5, no mark) |
| RS-LD corner landing +4.696, plate | 0.870394 | 0.870394 | 0.674803 | 0.674803 | ASSUMED — OWNER-APPROVED (level) |
| RS-LD: B3 band / 2CC pair / 535 pair / column 374 | 0.275625 / 0.118750 / 0.087731 / 0.0275 | HELD / HELD / HELD / none | same | | beam Q-61 C / UNKNOWN / UNKNOWN / column (T-258) |
| RS-A short flight to +5.50, waist | 1.320 | 1.497482 | 1.320 (+ 0.374173 head kink under plate C-T1, + 0.034016 pair) | 1.491542 (+ 0.424484) | ASSUMED — OWNER-APPROVED |
| RS-A: hidden pair 2CC / 2CD | 0.120 | HELD | 0.120 | HELD | UNKNOWN |
| **ST-02 soffit rows** | **8.478550** | **4.460946** measured + RS-C HELD | **8.852723** | **4.905788** measured + RS-C HELD | sub-pieces under members 1.720625 + 0.040, unknown 0.596481 |

Space below every ST-02 piece: the GF reception (V2.9 face GF-RC99C2A/open); 2.379 m2 of RS-C lies inside the
light-well outline (T-271 r2b).

## 3. Reconciliation of the slab-plan stair zones (units, to the cause)

* **GF-025 (ST-01 GF -> 1F zone) 10.725** = MS1-L lane inside the face (B20 face -> 25E) 3.755 + well 0.315 + MS1-T
  1.495 + MS1-LD 1.440 + MS1-U 3.720: **residual 0.000** (the face's 0.025 notch is column 36B). The MS1-L lane splits
  by reading: B structural 3.755 soffit (+ 0.180 under the B20 band in plan, outside the face); A architectural 3.215
  soffit + 0.540 hall floor open to the shaft above.
* **1F-016 inside the shaft (ST-01 1F -> 2F zone, T-271 '1F stair zone') 10.725** = MS2-L 3.755 + well 0.310 + well
  end 0.005 + MS2-LD-W 1.495 + MS2-LD-E 1.440 + MS2-U 3.720: **residual 0.000** (column 691 0.025 lies outside the
  face). The whole zone is the MS2 soffit: T-271's 10.725 HELD is confirmed as stair, not ceiling.
* **T-271 GF stair soffit HELD 9.853618** (GF-130/STAIR 7.402476 + GF-131 0.3325 + GF-132 1.856142 + GF-145 0.2625) =
  ST-02 pieces inside those faces **9.013781** + **0.777392** slab north of the top riser 315 (GF-131 0.155 + GF-132
  0.622392: the 1F arrival plate C-T1, no tread line, no stair) + **0.062506** strip between the light-well arcs' start
  (176.0 deg) and the first curved riser 2EA (177.0 .. 177.8 deg): floor below the light-well opening, no stair, no
  ceiling; **residual -0.000061** (T-271's arcs at 1024 segments, here 2048): named, not absorbed.
* **ST-02 plan 10.835656** (all rows less column 374) = 9.013781 inside the T-271 stair faces + **1.807875** under
  T-139 beam / column pieces (GF-159 'B3 (With Stair)' 1.375625, CA GF-143 / 144 / 158 0.345, GF-156 0.036, GF-161
  0.05125) + 0.014 inside column outlines 380 / 374 (in no face): **closure 0.000**.

## 4. Effect on the ceilings (T-271 r2b, GF reception; m2; for the lane I package, nothing changed here)

| | T-271 r2b | This ledger, method O | method D |
|---|---|---|---|
| horizontal decor ceiling (gypsum) | 93.1766 | **92.146117** (-1.807875 beam / CA / column-edge pieces that lie under the ST-02 lanes; +0.777392 slab north of 315) | **91.737928** (also -0.408189: the RS-A waist soffit runs on 0.340 m under plate C-T1) |
| no ceiling (openings, light well) | 14.9434 | 15.005906 (+0.062506 bottom-step strip) | same |
| stair soffit, GF | 9.8536 HELD | ST-02 rows 8.478550 plan + members 1.760625 + unknown 0.596481 (each own status) | 8.852723 + same |

Cause in one sentence: T-271 classified the slab-plan faces, not the stair: the faces drawn under the round stair's
lanes for the stair beam and the CA member are BEAMISH and went into the decor ceiling at bulkhead level, while two
'stair strip' faces run 1.55 m past the top riser under the 1F slab.

Engine (released V2.9 + route G): no stair-soffit line; the GF and 2F stair rooms carry FIN.CEILING with no value
(STAIRWELL_CEILING_SCOPE_NOT_ESTABLISHED), and the round stair's zone sits inside the reception's decor ceiling (T-271).
Freelancer: no stair-soffit row in any workbook; his ceiling rows ceil the GF stair zone (T-271 s.4). Engine vs freelancer
on this line: **not comparable, neither side has the line**; this ledger is the first measurement of it.

## 5. Findings for other lines (no quantity of theirs changed here)

* **F-T281-01 (ceilings, lane A / I):** 1.807875 m2 of the T-271 GF horizontal decor ceiling lies under ST-02 (stair
  beam band, CA, column edges): stair-side surfaces, HELD with Q-61 C / CA level, never gypsum ceiling; 0.777392 m2
  T-271 holds as stair soffit is slab (decor ceiling candidate, method O); 0.062506 m2 is no-ceiling.
* **F-T281-02 (concrete, lane S):** columns 380 (GF, D-16 CONFLICT) and 36B (GF) project 0.050 into the RS-S and MS1-L
  lanes over 0.80 / 0.50 m (0.040 / 0.025 m2); the T-258 waists take the full 1.20: waist exposure 0.040 x 0.16 x
  1.134456 = 0.007261 m3 (RS-S, HELD with D-16) and 0.025 x 0.16 x 1.143959 = 0.004576 m3 (MS1-L, inside its CONFLICT).
  Column 691 is already a T-258 exposure.
* **F-T281-03 (stairs):** the CA member 54E (0.300 x 1.150) crosses the RS-S lane under the flight and the hidden pairs
  535 / 536 and 2CC / 2CD (0.100 wide, layer 5, no mark) run along RS-S / RS-LD / RS-A: designer item for the C-ST-3 row
  (what is under the round stair's waist: a downstand, a rib, a balustrade line?). Their plan is listed, their true area
  HELD; the waist rows exclude them.

## 6. Verdict proposals (for the Checker)

| Item | Proposal |
|---|---|
| 1F stair zone 10.725 (T-271 HELD) | ENGINE (ceiling ledger) RIGHT that it is stair, not ceiling: = the MS2 soffit pieces, residual 0.000 |
| GF stair zone 9.853618 (T-271 HELD) | PARTLY: 9.013781 stair (RIGHT), 0.777392 slab (T-271 WRONG: north of the top riser), 0.062506 no ceiling |
| T-271 GF decor ceiling 93.1766 | T-271 WRONG on 1.807875 (stair-side member undersides under ST-02) and 0.777392 (the converse); method O 92.146117 |
| stair soffit true areas | RULE_DIFFERENCE between O and D (ST-01 17.197803 vs 17.243246 on the measured rows; ST-02 4.460946 vs 4.905788 incl. the C-T1 kink): no owner soffit rule; neither is released |
| freelancer | no line (MISSING SCOPE on his side and the engine's) |

No owner question (ERS 2.7 not met: the open items are designer items on the C-ST-3 / C-ST-4 rows, Q-50 / Q-51 / Q-61
are answered; the O / D choice is a measurement-method choice the Lead can put in the stair-finish line's package, and
both stay visible).

## 7. Rule, tests, lessons

Rule proposed (R-STAIR-SOFFIT-1, any villa; provenance T-281; a new rule version when adopted): a stair soffit is
measured on the stair's own geometry, one row per flight, landing, turn and junction, each with its plan area, its true
area (sloped by the printed riser / going; HELD where the riser is not printed or approved, where the waist is not
printed for method D, and for every curved or winder soffit that is not drawn) and the space below; the zone a slab plan
draws over a stair is reconciled to these rows in m2 and the rest of the zone goes back to its own class (slab ceiling,
no ceiling, member); a decor ceiling never covers a stair row or a member drawn under a stair lane.

Tests (tests/t281_stair_soffit, 20): Villa S hand fixture (L-stair with a quarter landing and a column notch, dog-leg
with a half landing) in both methods to 1e-9; adverse: riser unprinted -> HELD, never a convention riser (and a
'CONVENTION 0.165' riser refused, also on ST-02), waist unprinted -> only method D HELD, convention waist refused, beam
too shallow / kink past the plate -> HELD, winder / curved true area HELD and a held row without a reason refused, a
sub-piece outside its flight refused, two flights claiming one landing strip refused, a landing counted in two rows
breaks the zone, an unnamed zone residual refused; mirror, units (mm / cm / m, unknown refused); Alsenan pinned
(29 rows, both stairs, MS1-L both readings, zones closing to 0.000, ceilings effect) and the extract reproducing the
committed inputs from the private DXF (skipped when it is not decoded).

Lessons row (proposed, ERS s.7): 2026-10-25 | stair soffit missing as a finish line; the ceiling ledger held 20.579 m2
as 'stair soffit' by slab-plan face class | a slab-plan face classed STAIR / BEAMISH is not the stair: two 'stair strip'
faces run past the top riser under the slab (0.777 m2) and the member faces under the round stair's lanes went into the
decor ceiling (1.808 m2) | measure the soffit on the stair's own riser lines and landing polygons, reconcile every zone
face to those rows in m2 and send the rest back to its own class (any villa) | t281 test_zone_reconciliations_close,
test_adverse_a_landing_counted_in_two_rows_breaks_the_zone | PROPOSED.

## 8. Checker re-measure list ('ST7757 dxf.dxf', p.4 / p.5, by handle)

1. One flight: MS1-U, p.4 east lane 2F3 -> 296 1.200, 25B -> B20 face 2C6 3.100 (459 0.200 inside the band): plan
   3.720, true O 3.720 x hypot(0.30, 4.50 / 27) / 0.30 = 4.255527; method D foot kink (0.30 / 0.166667) x 0.16 x
   0.143959 = 0.041460 flat.
2. One landing: MS2-LD-W, p.5 632 -> 5C0 1.150 x 5E3 -> 5E2 1.300 = 1.495; method D less the MS2-L head kink 0.30 +
   1.785714 x 0.16 x 0.146124 = 0.341750 over 1.200 = 0.410100 -> 1.084900.
3. The T-271 GF zone: `python3 -I research/agents_t281/t281_extract.py <ST dxf>` (faces GF-130 / 131 / 132 / 145 x the
   ST-02 pieces; bottom-step strip 0.062506; north of 315 0.155 + 0.622392).
4. Re-run: `python3 -I research/agents_t281/t281_alsenan_check.py --write` (byte-identical LEDGER_T281.csv /
   summary.json).

## 9. Not done / uncertain

* The O / D choice for the finish quantity (no owner soffit rule); the finish type of a stair soffit (plaster / paint /
  marble) is not printed: this ledger gives surfaces, not a finish item.
* MS1-L stays CONFLICT, MS1-T / RS-C / MS2-TR true areas HELD (designer C-ST-3 / C-ST-4); the lobby flight D1 (ST-01b)
  and the entrance stair E1 (ST-03) have no printed waist or support (T-258): they are not rows here (D1 stands over the
  stair-hall ground slab GS-08, E1 over the court; whether either has an exposed underside at all is not drawn).
* The vertical faces of the stair beam, the CA member, the beam sides at B20 / B23 under the waist and the stringer /
  edge faces of the flights are not measured (member depths HELD or not drawn).
