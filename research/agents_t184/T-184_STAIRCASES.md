# T-184 Every staircase identified project-wide and reconstructed (development villa; every villa)

Worker 1 (lane S), 2026-10-22. Research + an unwired module + tests; no engine, rule, knowledge or method file changes,
nothing is released. Engineering reasoning standard (ERS) s.2-4 and s.7 applied. Drive "Alsenan chalet project" read
this run (read-only, private copies in `.work/private`, never committed): ST7757.pdf (16 pages, all looked at; p.3-6 and
p.16 read in detail), ST7757 dxf.dxf (sha 9f9d1179), P7757_DXF_COMPRESSED.zip (P7757.dxf sha ab54dd55),
p7757_arch_sheet03.pdf (GF), p7757_arch_sheet04.pdf (1F), Alsenan_Architectural_P7757_Pages_05-06.pdf (2F plan, SE
elevation), p7757_arch_sheet10.pdf (section A-A). Rules: owner Q-19, Q-20, Q-46 A, Q-47 A, Q-50 A cond, Q-51 A cond,
Q-61 (2), Q-62 A cond, OWNER_RULE_STAIRS S-1..S-3, UP-STAIR-002.

## 1. Result in engineering terms (stair concrete, m3; domes are T-185)

| Stair (id) | Freelancer | Engine (released baseline A) | Own, drawing-derived, net of the Q-62 ledger | Held, never 0 |
|---|---|---|---|---|
| ST-01 dog-leg beside the lift, GF -> 1F -> 2F | 8.131 (flights 7.123 + landings 1.008) | 2.786 (GF -> 1F only) | **4.746** (GF -> 1F 2.148 + 1F -> 2F 2.598) | winder turn 0.120 .. 0.130, slab under it 0.230 .. 0.250, closing riser 1F -> 2F, head clash 0.115 (B20 / B23), 'B3 (With Stair)' beams (Q-61) |
| ST-01b lobby flight D1 in the same shaft, +0.30 -> +1.00 | no row | none | **0.126** (steps) | waist (no thickness printed) |
| ST-02 round stair in the reception, GF -> 1F | 5.510 ("stair 2") | 0.901 (a winder region only) | **1.561** CALCULATED (straight flight, corner landing, short flight; Q-50 A cond) | 12 curved treads (candidate steps 0.330), helicoid soffit (not drawn), beam CA junction 0 .. 0.09 |
| ST-03 entrance stair E1 (outside), +0.15 -> +1.00 | 1.411 | 0.948 | **0.357** (steps) | waist (not printed; the engine's 0.591 is a 0.175 m convention) |
| Stairs total | 15.053 | 4.635 | **6.790** measured + held parts | |
| Domes (T-185) | 6.780 (3 x 22.6 x 0.10) | 7.372 (2 domes, convention shell) | T-185 | third dome, scenarios S0 / S1 |
| Reference line "stair + dome" | 21.833 | 12.007 | stairs 6.790 + domes (T-185) | |

Own vs freelancer, stairs: -8.263 m3 (-54.9 %). Own vs engine, stairs: +2.155 m3 (+46.5 %). These are development
figures (the freelancer is not ground truth, MISSION.md).

## 2. Inventory: every stair on every plan, with continuity (ERS s.2.1)

| Id | Where (physical) | Levels joined | Continues above its top? | Evidence |
|---|---|---|---|---|
| ST-01 | the 2.50 m shaft whose east wall is the LIFT shaft's west wall on GF, 1F and 2F | GF +1.00 -> turn -> landing +3.50 -> 1F +5.50 -> 1F->2F lower flight -> landing +7.516 / +7.684 -> 2F +9.70 | **No: ends at 2F** | 2F plan draws no flight leaving +9.70 (the lanes it draws are the 1F -> 2F flights seen through the opening, T-111); ST p.6 (2F roof slab) covers the shaft with slab panels (the north one 'T 18', T&B mesh, under the 'WATER TANK PLACE' cloud), no stair opening; section A-A: no flight above +9.70, the tower is roofed at +13.90 |
| ST-01b | same shaft, under the GF half landing (court-door lobby) | +0.30 -> +1.00 | n/a (one flight) | GF plan 4 solid riser lines; ST p.3 '+0.30' in the shaft; section A-A |
| ST-02 | reception, wrapped round the void | GF +1.00 -> (12 curved) -> +2.929 -> (11 straight) -> corner landing +4.696 -> (5) -> 1F +5.50 | **No: ends at 1F** | 1F plan: the short flight arrives at +5.50 (arrow), nothing leaves; ST p.5 (1F roof slab) and the 2F plan draw no stair there (slab panels, roof, domes) |
| ST-03 | outside, court to the GF entrance | +0.15 -> +1.00 | n/a | GF DXF 5 riser lines 2.800 m; ST p.3 4 lines, no slab panel |

Not a stair: the radial 20-line circle r 2.41 m on the 1F slab sheet (engine finding "could be DOMES or STAIRS"):
ST p.5 labels both radial circles "SEE DETAIL" (the dome detail on p.7) and no architectural plan draws a stair there:
it goes to T-185 (domes).

**Identity of "the stair beside the lift" (owner's ST-02 question): it is the dog-leg stair ST-01 itself.** On every
plan (GF, 1F, 2F architectural; ST p.4 and p.5 structural) the lift box (1.80 x 1.80 inside; B14 / B7 / B1) shares
its west wall with the dog-leg shaft. The round reception stair is NOT beside the lift (it is across the hall, in the
reception void). So the villa has TWO interior staircases, not three: ST-01 (the stair beside the lift = the
contractor's "main stair", 4 flights + 3 landings) and ST-02 (the round stair = his "stair 2", one continuous run,
width 1.2), plus the lobby flight inside ST-01's shaft and the outside entrance stair. Cross-trade (ELEMENT_REGISTER
line "Main stair ST-01 and the stair beside the lift ST-02"): proposal for the Lead: rename to ST-01 = dog-leg beside
the lift, ST-02 = round reception stair; T-173's shaft walls are ST-01's shaft (the lift-shaft wall is shared).

## 3. The last structural page (ST7757 p.16 "DETAILS (4)"): which stair each detail belongs to

| Detail on p.16 | What it shows | Belongs to |
|---|---|---|
| TYPICAL STEEL LAYOUT - STAIR SECTION (N.T.S.) | two straight flights 0.00 -> landing S.S.L +2.00 -> +4.00 / +3.95 S.S.L, treads 30, waist marked "THICK" (no value), landing with a 20 x 40 edge beam (2 d12, 4 d16), foot on a ground beam 30 wide (2 d14/30, d8/15 cm, 4 d16) on 10 cm plain concrete; bars 8 d16/m bottom, 6 d14/m top, d12/20 cm distribution, 6 d12/m landing, 1 d12 + d8/15 per step | NO Alsenan stair by geometry: its levels (2.00 + 2.00 straight, mid landing) match neither ST-01 (4.50 m GF -> 1F through a winder turn, 4.20 m 1F -> 2F) nor ST-02 (curved, 4.50 m). It is the TYPICAL reinforcement arrangement for the 'T 16' stair panels of p.4 / p.5 (both ST-01 and ST-02), not a dimensioned section. The waist value comes from the plans' 'T 16' (Q-47 A), never from this sheet. |
| TYPICAL DETAIL OF STAIR BEAM | a cranked beam following the flight between two columns (2 d12 top, 4 d16 bottom, 6 d8/m) | the 'B3 (With Stair)' members on p.4 (ST-01 north edge, ST-02 edge) and p.5 (ST-01): HELD under owner Q-61 (2), never duplicated with the flight concrete |
| DETAIL OF RIBS SOLID PART + TORSION STEEL FOR RIBS | rib / beam solid part, sections A..G | ribbed slabs, not stairs |
| TYPICAL DETAIL FOR OPENING IN BEAM | stirrups round a beam opening | beams, not stairs |

So "p.16 typical only" (earlier work) is CONFIRMED, now with the reason: no printed level or dimension on p.16 fits any
Alsenan stair. One NEW clarification for the consultant (no quantity changed): the typical section draws a 20 x 40
landing edge beam at the flight / landing junction; the Alsenan slab plans draw none at the ST-01 half landings or the
ST-02 corner landing. Drawing-first: no landing beam is measured; consultant item C-ST-1 asks whether it applies.

Owner stair rule as a CHECK (S-1, drawn governs): ST-01 GF -> 1F 4.50 m: rule 29 risers, drawn 27 x 0.1667 FLAG;
1F -> 2F 4.20 m: rule 27, drawn 25 x 0.168 FLAG; ST-02 4.50 m: rule 29, drawn 28 x 0.1607 FLAG (0.7 mm over);
ST-01b 0.70 m drawn 4 x 0.175 FLAG; ST-03 0.85 m drawn 5 x 0.170 FLAG (as D-56). Every Alsenan riser exceeds the owner's
0.16 m maximum: a designer finding (C-ST-2), quantities unchanged (S-1).

## 4. Reconstruction (from first principles; the T-111 readings re-derived by a new independent module)

Formulas (owner rules): steps n x 1/2 r g w (Q-19); waist w x t x hypot(goings x g, goings x r) between the first and
the last riser line (Q-47 A, T = 0.16); landings L x W x t; arrival wedges inside a plate / landing deducted once
(Q-62 A cond). `t184_alsenan_ledger.py` reproduces T-111 to 1e-4 m3 on every stair (test).

ST-01 per storey: GF -> 1F = MS1-L 0.270 + 0.593 + landing 1.20 x 1.20 x 0.16 = 0.230 + MS1-U 0.360 + 0.725 - 0.030
(head wedge in B20 / 1F slab) = **2.148**; 1F -> 2F = MS2-L 0.363 + 0.726 + landing 2.50 x 1.20 x 0.16 = 0.480 + MS2-U
0.363 + 0.726 - 0.030 (head) - 0.030 (lower flight's top wedge in the landing) = **2.598**. The floor arrival landings
(1F and 2F, 2 x 1.95 x 2.50 = 9.75 m2) are inside the floor-slab panels at floor level: FLOOR SLAB concrete, counted
once there, never stair (test).

## 5. Reconciliation (units, to a cause)

**ST-01, freelancer 8.131 -> own 4.746 (+3.385 m3, closes to 0.000):**
- flights 7.123 vs own 4.036 (+3.088): (a) LENGTH: his 4 x 5.3 = 21.2 m against the drawn sloped flight lengths
  3.089 + 3.775 + 3.782 + 3.782 = 14.428 m: +2.275 m3 (1.20 x 0.28 x 6.772). His 5.3 m matches the 1F / 2F plan
  dimension chain 1.95 (floor landing) + 3.30 (flight) = 5.25 m: the floor landing (slab concrete) inside a flight
  length (consistent with the drawing; not confirmed from his workbook). (b) THICKNESS: his 0.28 m against the drawn
  equivalent 0.233 m (waist 0.16 + steps, per m2 of sloped flight): +0.812 m3.
- landings 1.008 vs own 0.710 (+0.298): area 3 x 1.2 x 1.4 = 5.04 vs drawn 1.44 + 3.00 = 4.44 m2 (+0.120 at 0.20);
  thickness 0.20 vs printed T 16 (+0.178).
- Not in his figure explicitly and HELD in ours: the winder turn and its slab (0.35 .. 0.38), the closing riser, the
  head clash 0.115.

**ST-02, freelancer 5.510 -> own 1.561 CALCULATED + held curved part:** his 1.2 x 16.4 x 0.28. No drawn length of
this stair reaches 16.4 m: walking line 8.868 m plan / 9.944 m sloped, outer string 9.887 m plan / 10.863 m sloped;
**5.54 m of his run is on no drawing (unexplained residual)**. Width 1.20 agrees with the straight flight (DXF 1200;
the short flight is 1.25, the curved treads 1.15). Thickness 0.28 not printed (T 16 is). Indication only (not a
quantity, Q-51 step 5): a helicoid soffit along the walking line would be about 1.15 x 0.16 x 4.01 = 0.74 m3; with the
candidate curved steps 0.330 the stair would still be about 2.6 m3, far below 5.51.

**ST-03, freelancer 1.411 -> own 0.357 steps + waist HELD:** his run 1.8 m vs drawn plan run 4 x 0.30 = 1.20 m
(+0.60 m; sloped 1.471 m); his 0.28 m is printed nowhere; width 2.80 agrees (DXF 2800).

**Engine (released A) 4.635 -> own 6.790 measured:**
- ST-01 2.786 vs 4.746 (-1.960): **D-T184-1 SILENT OMISSION, -2.598 m3**: the structural completeness pass folds the
  1F -> 2F flights drawn on the 1F roof slab plan (ST p.5) into the GF -> 1F flights of the GF roof slab plan (ST p.4)
  as "drawn again on" the other sheet (`concrete_completeness.py` twin rule: same layer, same box, levels ignored);
  they appear in no line and no exposure. On the GF -> 1F storey the engine is +0.638 above own 2.148: the 0.175 m
  waist convention (printed T 16), the 0.165 m riser convention and the winder turn measured by convention where the
  ledger holds it.
- ST-02 0.901 vs 1.561: the engine measures only an 8.37 m2 winder region on the ground-beam plan; the arcs and lines
  drawn at the stair on ST p.4 (finding CC-13011ac02f) are an exposure 0 .. 1.872, not measured.
- ST-03 0.948 vs 0.357: the engine adds a 0.175 m convention waist that no drawing prints (should be HELD: T-186
  default guard).
- ST-01b: none vs 0.126 (small omission).

## 6. Who is right (verdict proposals for the Checker)

- ST-01: ENGINE (own ledger) RIGHT against the freelancer on geometry (hand calc above, every term from the drawing);
  RULE_DIFFERENCE on his 0.28 / 0.20 thicknesses. Against the released engine: own RIGHT (the engine loses a storey).
- ST-02: UNRESOLVED while the curved part is held (owner Q-50 / Q-51); his 16.4 m is on no drawing.
- ST-03: UNRESOLVED (waist not printed; the run difference 1.8 vs 1.2 m is ENGINE_RIGHT on geometry).
- ST-01b: HAND_FOUND (no freelancer row).

## 7. Rules (general, any villa; proposed, labelled; a rule change is a new rule version)

- R-STAIR-ID-1: a staircase is identified by its plan place and the levels it joins on every plan, section and slab
  plan, never by a name in a contractor's sheet or a description ("beside the lift"): read the lift / shaft walls on
  the plans before naming.
- R-STAIR-STACK-1 (fixes D-T184-1): two drawings at the same plan place are one physical flight only when they join the
  same levels; different levels -> two flights (stacked core); a level range unknown on either -> UNDETERMINED (held),
  never merged.
- R-STAIR-CONT-1: a stair continues above a floor only when a flight leaving that floor is drawn (plan of that floor,
  slab plan above, section); a lower plan never implies it, and an upper plan showing flights through the opening is
  not a new flight.
- R-STAIR-LAND-1: a landing at a floor level inside the floor-slab panel is floor-slab concrete (once); intermediate
  landings are stair concrete.
- R-STAIR-TYP-1: a typical (N.T.S.) stair section gives reinforcement arrangement, never a project dimension; an element
  it draws that the project plans do not (landing edge beam) is a consultant clarification, not a quantity.

## 8. Regression tests (tests/t184_stairs, 20 pass)

Synthetic villa Q (not Alsenan; 3.60 m storeys, a dog-leg core and a straight stair): stacked flights kept apart under
rotation / mirror and the seen flight counted once (normal) vs the released twin rule losing the 1F -> 2F flights
(adverse, the exact Alsenan failure); unknown levels -> UNDETERMINED; two staircases inventoried, none omitted (normal)
vs the second omitted and reported (adverse); a stair ending at one floor vs continuing, and continuation never
inferred from a lower plan (adverse); floor landing -> slab, intermediate -> stair, floor-level landing outside a slab
panel stays stair (adverse); architectural vs structural conflict kept with both values; hand-calculated flight /
landing concrete; missing waist HELD never 0; mm / cm / m and a refused unit; owner stair rule as a check (4.48 m ->
28 risers); the development-villa ledger re-derives T-111 and keeps the 1F -> 2F storey; the freelancer reconciliation
closes to 0.000.

## 9. Consultant / designer list (no quantity changed)

C-ST-1 landing edge beam of the typical section (20 x 40) at the ST-01 half landings / ST-02 corner landing: applies or
not. C-ST-2 every drawn riser exceeds the owner's 0.16 m maximum (0.1607 .. 0.175). C-ST-3 the winder turn of ST-01
(soffit, well strip) and the ST-02 helicoid soffit: no detail. C-ST-4 access to the water tank on the 2F roof slab over
the ST-01 shaft: no stair or ladder drawn (scope, not a stair quantity). Existing: B20 / B23 head clash (Q-46 RFI), CA
level, 'B3 (With Stair)' (Q-61).

## 10. Lessons-register row proposed (ERS s.7)

| 2026-10-22 | Stair concrete 4.635 (engine) vs 6.790 m3 own; "stair beside the lift" taken as a third staircase | (1) the released structural pass treats a stair drawn at the same place on two storeys' slab plans as one drawing ("drawn again on"), ignoring the levels: the whole 1F -> 2F storey of the dog-leg (2.598 m3) vanished; (2) a stair named from a description, not from the plans | A stair is identified by plan place AND levels joined; stacked flights with different levels are separate, unknown levels are held; continuation only from a drawn flight leaving the floor (any villa) | tests/t184_stairs (adverse: released twin rule loses the upper storey; second stair omitted; continuation inferred from a lower plan) | rule proposed; engine fix for lane I (new method version) |
