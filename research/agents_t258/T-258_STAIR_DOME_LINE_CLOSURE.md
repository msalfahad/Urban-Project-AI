# T-258 Whole-line closure: CONC.STAIR_DOME, closable components vs named blockers, every component once (Alsenan; every villa)

Worker 1 (lane S), 2026-10-24, run session_013rPYKgwyqy8tvEsbjEQbAg. Research piece, not wired: no engine, candidate or
released line changed; integration is a lane I package after the Checker's verdict. Development villa, not an accuracy
claim. Drawings named by Drive folder and title; members by DXF handle; lengths, areas, volumes only (no coordinates
committed). ERS s.2.1-2.4, s.3, s.4 A/B/C, s.7 applied; the T-248 pattern (closable component + named blockers), no new
measurement method: every value is the owner formula already merged (Q-19, Q-47 A, Q-62 A cond, R-CONC-OWN-1 / -1a,
R-STAIR-LAND-1, T-185 shell solid), recomputed from its printed primitives by `t258_stair_dome_line.py`.

## 0. Inputs and runs (own, this task)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179... (= manifest) | own re-read of the ST-01 half landings and flight edges on p.4 / p.5 by handle (`t258_extract.py`, lengths only): the MS2-LD conflict closes (s.3) |
| "P7757_DXF_COMPRESSED.zip" -> P7757.dxf | ab54dd55... (= manifest) | the candidate run (s.5) |
| freelancer RC workbook | committed cells | tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, sheet 'السلم' G11 / G12 / G13 / G20 / G21, B25 = 'ورقة1'!E22 21.8328 (key CONC.STAIR_DOME, items STR.CONC.STAIR + STR.CONC.DOME) |

Merged evidence built on and cited, not re-derived (WORKFLOW_CONTROLS s.10 item 5): T-184 inventory (924c2bd), T-189
heads (3369f30e), T-192 feet / knees / rev3 (86fd5f42), T-185 domes S0 / S1 (94e39ee6), T-187 Gate B (8a6d604a: MS2-U
own, MS2-LD both halves own), T-193 Gate B (e866328a: dome shells in the candidate, the 4.451 'winder' retired as
DOME-B), T-234 slab ledger (3224f68a: arrival landings in GF-077 / 1F-062, stair zones out), T-248 columns (567dc972).

Files: `t258_stair_dome_line.py` (STAIR_DOME_LINE_V1, pure rules, stdlib), `ALSENAN_STAIR_DOME_INPUT.json` (printed
primitives + handles + the freelancer cells), `t258_alsenan_check.py` -> `LEDGER_T258.csv` (46 rows) + `summary.json`,
`t258_extract.py` (private DXF -> lengths, for the Checker); tests `tests/t258_stair_dome_line` (18: Villa D hand
fixture + adverse + Alsenan pinned).

## 1. The physical elements and the line (ERS s.2.1)

Key CONC.STAIR_DOME = freelancer 'ورقة1' row 22 = 'السلم'!B25 21.8328 m3 = STR.CONC.STAIR + STR.CONC.DOME. Inventory
(T-184, re-checked against the slab plans this run): **ST-01** dog-leg beside the lift GF +1.00 -> turn -> +3.50 -> 1F
+5.50 -> +7.516 / +7.684 -> 2F +9.70 (ends at 2F); **ST-01b** lobby flight in the same shaft +0.30 -> +1.00; **ST-02**
round reception stair GF +1.00 -> 1F +5.50; **ST-03** entrance flight +0.15 -> +1.00; **DOME-A / DOME-B** terrace
domes on the +9.70 roof (approved design S0, Q-27 A); **DOME-3** upper-roof dome (architectural only). The client's
no-dome request (Q-29) is scenario S1 beside, never in this line (T-185).

Convention (each intersection once, stated before any number): a flight is billed by the owner method (steps + waist
between the first and last riser lines, Q-62 wedges deducted once); a head or foot inside a full-depth member billed
through the junction belongs to that member (R-CONC-OWN-1 / -1a); landings at a floor level inside a floor-slab panel are
slab (R-STAIR-LAND-1); the dome ring is a beam-line member (T-241 / T-252 bands), the shell starts on the ring-top plane.

## 2. Component ledger (LEDGER_T258.csv; m3)

| Element | Component | Class / evidence | m3 | Source (handles / pages) | Blocker |
|---|---|---|---|---|---|
| ST-01 | MS1-L lower flight GF -> turn | **CONFLICT** | **0.863029 .. 1.054813** | p.4 45A .. 25E (12 straight) + 2F6 / 2F4 / 2F5 / 2F3 vs ARCH GF 10 + section A-A 15 | C-ST-4 (designer); owner 22-10 18:00 (4) |
| | MS1-T winder treads | HELD | 0.12 .. 0.13 | p.4 2F6 / 2F4 / 2F5 | Q-51 cond, C-ST-3 |
| | MS1-T-SLAB under the winders | HELD | 0.2304 .. 0.2496 | p.4 284 / 2F3 x 25E / 279 = 1.30 x 1.15 (inside the range) | C-ST-3 (warped soffit not drawn) |
| | MS1-LD half landing +3.50 | CLOSABLE VERIFIED | 0.230400 | p.4 2F3 -> 296 1.20 x 25B -> 279 1.20, T 16 | - (Checker 22-10 17:18) |
| | MS1-U flight to 1F | CLOSABLE VERIFIED | 0.997552 | p.4 25B .. 459, r 4.50 / 27 | - (Checker own 0.9976, D-CHK-T180-1, rev2) |
| | MS2-L flight from 1F | CLOSABLE VERIFIED | 1.033444 | p.5 646 .. 632, r 4.20 / 25; wedge into the 0.16 plate | - (Checker 01:57, T-187) |
| | MS2-LD-W half landing +7.516 | CLOSABLE DRAWING-CONFIRMED | 0.239200 | p.5 5E3 -> 5E2 1.30 x 632 -> 5C0 1.15 (own) | - |
| | MS2-LD-E half landing +7.684 | CLOSABLE DRAWING-CONFIRMED | 0.230400 | p.5 5E2 -> 5D4 1.20 x 62F -> 5C0 1.20 (own) | - |
| | MS2-TR turn riser + 0.10 x 0.05 well end | HELD (no bound) | - | p.5 5E2, 633; section A-A 25 risers | C-ST-3 (junction of two plates 0.168 apart not drawn) |
| | MS2-U flight to 2F | CLOSABLE VERIFIED | 1.001373 | p.5 62F .. 644 (+ arrival line 459 / section) | - (T-187 Gate B own) |
| | heads in B20 / B23, MS2-L foot in B20 | OWNED_ELSEWHERE BEAM | 0.057261 + 0.057451 + 0.025448 | T-189 / T-192 | counted once in B20 0.990 / B23 1.11375 |
| | 1F / 2F floor-arrival landings | OWNED_ELSEWHERE SLAB | (slab) | T-234 GF-077 + B20, 1F-062 + B23 | - |
| | 'B3 (With Stair)' | OWNED_ELSEWHERE BEAM (HELD) | - | p.4 / p.5 | Q-61 (2) |
| | shaft floor 11.52 m2 | OWNED_ELSEWHERE GROUND_SLAB (UNKNOWN) | - | p.3 '+0.30' | scope (lane A / Lead) |
| | column 691 into the MS2-L lane | OWNED_ELSEWHERE COLUMN (HELD) | exposure 0 .. 0.006684 inside MS2-L | p.5 691 | T-248 CONFLICT (D-16): deducted from MS2-L when it closes |
| ST-01b | D1 steps | CLOSABLE DRAWING-CONFIRMED | 0.126000 | ARCH GF 4 risers, section A-A, p.3 '+0.30' | - |
| | D1 waist / support | HELD (no bound) | - | | no thickness printed |
| ST-02 | RS-C 12 curved treads | HELD (no bound) | - (0.330 information only) | p.4 CC-13011ac02f | Q-50 / Q-51 |
| | RS-C helicoid waist | HELD (no bound) | - | | not drawn (Q-51 step 5, C-ST-3) |
| | RS-S straight flight | CLOSABLE ASSUMED — OWNER-APPROVED | 0.942732 | p.4 11 tread lines, w 1.20, T 16 | riser 4.50 / 28 by Q-50 A cond; geometry Checker own 0.9716 gross |
| | RS-LD corner landing +4.696 | CLOSABLE ASSUMED — OWNER-APPROVED | 0.225600 | 1.25 x 1.15 less column 374 corner | Q-50 A cond (level) |
| | RS-A short flight to +5.50 | CLOSABLE ASSUMED — OWNER-APPROVED | 0.392805 | ARCH 1F 5 risers, 1250 | Q-50 A cond; not Checker re-measured |
| | column 374 corner | OWNED_ELSEWHERE COLUMN | 0.004400 | p.4 374 | - |
| | CA junction | HELD | 0 .. 0.09 | p.4 535 / 536 | CA level not stated |
| | hidden pair 2CC / 2CD | UNKNOWN | - | p.4 layer 5 | designer (no mark) |
| ST-03 | E1 steps (net of the slab-owned wedge 0.001983) | CLOSABLE DRAWING-CONFIRMED | 0.355017 | ARCH GF 5 risers 2800, section B-B, p.3 18A .. 179 | - |
| | E1 waist / support | HELD (no bound) | - | | not printed |
| | E1 last riser in the GB band | OWNED_ELSEWHERE GROUND_BEAM (HELD) | exposure 0 .. 0.0714 inside the steps | p.3 178 / 7DB | GB levels (T-242 / T-253) |
| DOME-A / B | shell 442 / 190 / 10 | CLOSABLE VERIFIED | 2 x 2.540681 | p.7 DIM 1A38 / 1A6D / 19B1, arcs 182B / 182E | - (Checker 22-10 18:15, V3.0.7 Gate B) |
| | ring | OWNED_ELSEWHERE BEAM (S0 CONFLICT) | - | p.5 band vs p.7 ring, 'AS PER ARCH' | T-185 RFI item 7 |
| | drum +9.70 -> +11.00 | HELD (no bound) | - | section B-B '130' | material / thickness not printed |
| DOME-3 | upper-roof dome | HELD (no bound) | - | SE elevation 441 / 215; P7757 circle 1300 | Q-27 A + no structure (D-21) |
| beside | 6 soffit knees (T-192 s.5) | BESIDE, not summed | +0.113466 net | | owner method Q-47 A plumb cut |

**Line split** (summary.json):

| Component | m3 |
|---|---|
| **CLOSABLE** | **10.855885** = VERIFIED 8.344131 (MS1-LD, MS1-U, MS2-L, MS2-U, 2 shells) + DRAWING-CONFIRMED 0.950617 (MS2-LD W / E, D1, E1 steps) + ASSUMED — OWNER-APPROVED 1.561137 (ST-02 RS-S / RS-LD / RS-A, Q-50 A cond) |
| of which stairs / domes | 5.774523 / 5.081362 |
| CONFLICT | MS1-L 0.863029 .. 1.054813 |
| HELD with a bound | 0.3504 .. 0.4696 (MS1-T, MS1-T-SLAB, CA) |
| HELD / UNKNOWN with no value | 9: MS2-TR, D1 waist, E1 waist, RS-C, RS-C soffit, 2CC, 2 drums, DOME-3 |
| owned by other lines (listed, not summed) | beam 0.140161, ground slab 0.001983, column 0.0044, slab (arrival landings, plate) |

The line does **not** close as a whole (`line_closable` false): it is BLOCKED BY CONSULTANT on C-ST-3 / C-ST-4 (winder
turn, MS1-L riser count, MS2-TR, curved flight), the unprinted waists of D1 / E1 and the tower dome / drums, plus the
owner-approved Q-50 A cond riser on ST-02. The closable component 10.855885 m3 is what the Checker can re-measure now.

## 3. The one conflict this task closes: ST-01 upper half landing MS2-LD 0.4696 .. 0.480 -> 0.4696

T-187 Gate B held MS2-LD over two readings: 2.50 x 1.20 x 0.16 = 0.480 (T-111) and the two drawn halves 0.2392 + 0.2304 =
0.4696. Own read of p.5 by handle (`t258_extract.py`): the west half runs from the MS2-L LAST riser line 632 to the north
edge 5C0 (1.150) and from the wall 5E3 to the step line 5E2 (1.300); the east half from the MS2-U FIRST riser line 62F to
5C0 (1.200) and 5E2 to 5D4 (1.200); 632 lies 0.050 north of 62F; the well (62D / 62E, 0.100) is closed by 633 exactly on
the 62F line; the step line 5E2 (1.150) separates two plates at +7.516 (= 5.50 + 12 x 0.168) and +7.684 (= 9.70 -
12 x 0.168): 25 risers = 12 + the turn riser + 12 (section A-A, Q-46 A). So the 0.480 reading starts the west half on
the other flight's first riser line: of its extra 1.30 x 0.05 x 0.16 = 0.0104 m3, **0.0096 is the MS2-L last going (1.20
x 0.05), already inside the VERIFIED MS2-L**, and 0.0008 is the 0.10 x 0.05 well end at the turn-riser junction (MS2-TR,
held). 0.4696 + 0.0096 + 0.0008 = 0.480: nothing lost, nothing twice. **MS2-LD = 0.4696 DRAWING-CONFIRMED** (both halves
equal to the Checker's own T-187 readings); the 0.480 reading is retired as a double count, the 0.0008 stays in MS2-TR.

Rule (proposed, R-STAIR-LANDING-EDGE-1, any villa): a landing that a flight arrives into starts at THAT flight's last
riser line; a landing reading that starts it at another line overlaps the flight's last going and is refused; where two
flights meet one landing at different riser lines, the landing is split at the drawn step line into its own plates,
each from its own flight edge (`resolve_landing_edge`).

## 4. Reconciliation to the freelancer, by component (m3; ERS s.2.4)

| Element | His cell | His | Drawing (this ledger) | Steps, in units | Residual |
|---|---|---|---|---|---|
| ST-01 flights | G20 4 x 1.2 x 5.3 x 0.28 | 7.1232 | closable 3.032369 + MS1-L CONFLICT 0.863 .. 1.055 | length 4 x 5.3 = 21.2 m vs drawn sloped 14.428 m +2.275333; 0.28 vs drawn equivalent 0.2331 +0.812307; heads / foot billed in B20 / B23 +0.140161 (beam line) | **0.000** at MS1-L reading A |
| ST-01 landings | G21 3 x 1.2 x 1.4 x 0.20 | 1.008 | 0.700000 (MS1-LD + MS2-LD W + E) | area 5.04 vs drawn 4.375 m2 +0.133; 0.20 vs T 16 +0.175 | **0.000** |
| ST-02 | G12 1.2 x 16.4 x 0.28 | 5.5104 | closable 1.561137 (Q-50 A cond) + held curved part | 5.537 m of his 16.4 m on no drawing (outer string sloped 10.863) +1.860373 | 2.088890 = curved treads + helicoid waist + CA (HELD, no value) and his flat 0.28 (T 16 printed): **UNRESOLVED** until Q-50 / Q-51 / C-ST-3 |
| ST-03 | G11 1.8 x 2.8 x 0.28 | 1.4112 | 0.355017 steps (+ 0.001983 slab) + waist HELD | run 1.8 vs drawn 1.2 m +0.4704; his 0.28 over the drawn run vs steps only +0.5838 (not an error size: the waist is held) | **0.000** (the waist decides how much of +0.5838 is real) |
| ST-01b | none | - | 0.126 | his sheet has no lobby flight | hand found |
| Domes | G13 3 x 22.6 x 0.10 | 6.78 | 5.081362 + DOME-3 HELD | third dome 2.26 (HELD, not compared); typed 22.6 vs mid-surface 25.402 m2 -0.561361 | **0.000** |
| **Line** | B25 | **21.8328** | closable 10.855885 + CONFLICT + HELD | not comparable as a total (held parts have no value) | by component above |

## 5. Engine sides (m3; NOT RELEASED candidate vs this ledger)

| Component | Released A (V2.9 + route G) | Candidate V3.0.11 (= V3.0.7 stair / dome lines, unchanged by V3.0.8 .. V3.0.11) | Drawing (this ledger) | Verdict proposal |
|---|---|---|---|---|
| ST-01 GF -> 1F | 2.786 (route line, conventions) | BLOCKED (2.786 information) | MS1-LD 0.2304 + MS1-U 0.997552 VERIFIED; MS1-L CONFLICT; turn HELD | candidate under-releases 1.227952 m3 of VERIFIED components (integration gap, lane I) |
| ST-01 1F -> 2F | 0 (D-T184-1 omission) | MS2-L 1.033445 + MS2-U 1.001373 released, MS2-LD HELD 0.4696 .. 0.480 | 1.033444 + 1.001373 + **0.4696** | equal on the flights; MS2-LD closes (s.3) |
| ST-01b | none | placeholder (blocked) | 0.126 DRAWING-CONFIRMED + waist HELD | ENGINE omission (small) |
| ST-02 | 0.901 (8.37 m2 winder region) | BLOCKED (0.901 information) | 1.561137 ASSUMED — OWNER-APPROVED + curved part HELD | candidate holds what Q-50 A cond already approves (1.561137) |
| **ST-03** | 0.948267 | **0.948267 RELEASED** | **0.355017** steps + waist HELD | **ENGINE_WRONG basis: the released line is 4 x 1/2 x 0.165 x 0.30 x 2.80 + 0.175 x 2.80 x hypot(1.20, 0.66) = 0.2772 + 0.6711: a convention riser 0.165 (drawn 0.85 / 5 = 0.170) and a convention waist 0.175 that no drawing prints (T-187: 'ST-03 prints no waist: not flagged'); should be 0.355017 DRAWING-CONFIRMED + waist HELD: -0.593250 m3 released** |
| Domes | 7.372 (rise = radius, 0.12) | 5.081362 released (2 VERIFIED shells) + DOME-3 blocked | 5.081362 + DOME-3 HELD | equal |
| Item total released | 12.007 | 8.064447 (stairs 2.983085 + domes 5.081362) | closable 10.855885 | a lane I package taking this ledger: -0.593250 (ST-03) + 0.4696 (MS2-LD) + 1.227952 (ST-01 GF) + 0.126 (D1) + 1.561137 (ST-02) = **+2.791439** |

Candidate figures are those recorded by the merged Gate B verdicts of V3.0.6 / V3.0.7 (T-187 8a6d604a, T-193 e866328a:
'STR.CONC.STAIR released 2.983085 unchanged, held 0.4696 .. 0.4800'); the V3.0.8 .. V3.0.11 reports (T-231, T-211,
T-232, T-239) name no STR.CONC.STAIR / STR.CONC.DOME line among their changed rows. The ST-03
composition is re-derived here from the line's own engine figure 0.9482675 (T-184 input `engine_baseline_A`): 0.2772 +
0.6711 = 0.9483 (the profile reading of 4 goings at 0.30 with riser 0.165, waist 0.175).

## 6. Verdict proposals (for the Checker)

| Item | Proposal |
|---|---|
| closable component 10.855885 m3 (13 components) | CLOSABLE: VERIFIED 8.344131 (citations in s.2) + DRAWING-CONFIRMED 0.950617 to re-measure (s.8) + ASSUMED — OWNER-APPROVED 1.561137 (Q-50 A cond, geometry partly Checker-verified) |
| MS2-LD | DRAWING-CONFIRMED 0.4696 (CONFLICT closed by the flight edge; 0.480 a double count of 0.0096 with MS2-L) |
| MS1-L | CONFLICT 0.863029 .. 1.054813 (C-ST-4), never one end |
| ST-03 candidate 0.948267 | ENGINE_WRONG (convention riser and waist released): HELD waist, steps 0.355017 |
| ST-01 GF / ST-02 / D1 in the candidate | ENGINE over-holds VERIFIED / DRAWING-CONFIRMED / owner-approved components (1.227952 + 1.561137 + 0.126) |
| freelancer ST-01 8.1312 | RULE_DIFFERENCE + FREELANCER length (5.3 m includes the floor landing) and thickness (0.28 / 0.20 vs T 16); reconciled to 0.000 |
| freelancer ST-02 5.5104 | UNRESOLVED (curved part held; 5.537 m of his run on no drawing) |
| freelancer ST-03 1.4112 | FREELANCER run 1.8 vs drawn 1.2 m (ENGINE_RIGHT on geometry, +0.4704); thickness UNRESOLVED (waist not printed) |
| freelancer domes 6.78 | FREELANCER area not established (typed 22.6 m2); third dome UNRESOLVED (Q-27 A) |

No owner question (ERS 2.7 not met: every open item is a designer / consultant item already on the list: C-ST-3, C-ST-4,
Q-50 / Q-51 (answered conditionally), D-21, T-185 RFI item 7).

## 7. Rule, test, lessons rows

General rule proposed (every villa; provenance T-258; a new rule version when adopted, R-STAIR-DOME-LINE-1): the stair +
dome line is closed only when (a) every staircase and dome of an engine-free inventory is split into physical components
(flights, landings, turns, junctions, waists, shells, rings, drums), each one row with one region; (b) each value is the
owner formula on printed primitives, the evidence status per component; (c) heads / feet / landings / rings that another
line bills are listed OWNED_ELSEWHERE and never summed; a floor-level landing is slab; (d) a winder / curved part without
a drawn soffit, a waist with no printed thickness and a dome without a detail are HELD, never 0 and never a convention;
(e) two drawing readings of one component are a CONFLICT range unless the drawing itself decides between them (here: the
landing edge rule, s.3); (f) a total is compared with another side component by component.
Test: tests/t258_stair_dome_line (Villa D: dog-leg with the landing partly inside a beam band, foot in a ground beam,
head in a floor beam, winder and curved flight held, floor landing in the slab, dome shell; adverse: landing in both slab
and stair refused, winder released without drawn geometry refused, a missing waist as 0 refused (three forms), CONFLICT
collapse / wrong range refused, landing edge overlap refused, owned-elsewhere naming the stair refused; units m / cm /
mm, unknown unit refused, metamorphic order; Alsenan pinned: 46 rows, classes, closable 10.855885, Checker figures
reproduced, MS2-LD 0.4696 + 0.0096 + 0.0008 = 0.480, freelancer ST-01 / ST-03 / domes reconciled to 0.000).
Lessons rows (proposed): (1) 2026-10-24 | the ST-01 upper half landing was HELD over two readings 0.4696 .. 0.480 for a
day | the larger reading started the landing on the other flight's first riser line, overlapping the arriving flight's
last going by 0.05 m | a landing starts at the arriving flight's own last riser line; two flights arriving at different
lines give two plates split at the drawn step line (any villa) | t258 test_landing_edge_overlap_refused,
test_ms2_landing_conflict_closed_by_the_flight_edge | PROPOSED. (2) 2026-10-24 | the candidate releases the entrance
flight at 0.948 m3 on a convention riser 0.165 and waist 0.175 while every other stair waist without a printed thickness
is held | the default guard checks a convention only where the drawing prints a competing value ('prints no waist: not
flagged'), so a convention with NO printed value passes | a dimension the drawing does not print is HELD (lessons
2026-10-24 'not printed for the member itself is HELD'), the guard must also refuse a convention where nothing is printed
(any villa) | t258 test_missing_waist_never_zero (ledger side); the candidate fix belongs to a lane I package | PROPOSED.

## 8. Checker re-measure list (handles on 'ST7757 dxf.dxf')

1. MS2-LD both halves (DRAWING-CONFIRMED): p.5 632 / 5C0 / 5E3 / 5E2 (1.150 x 1.300) and 62F / 5C0 / 5E2 / 5D4 (1.200 x
   1.200); 632 vs 62F 0.050; 633 on the 62F line; `python3 -I research/agents_t258/t258_extract.py <ST dxf>`.
2. D1 steps 4 x 1/2 x 0.175 x 0.30 x 1.20 = 0.126 (ARCH GF 4 riser lines, section A-A 4 risers, p.3 '+0.30').
3. E1 steps 5 x 1/2 x 0.17 x 0.30 x 2.80 = 0.357 less the slab-owned 0.001983 (T-192, Checker-verified) = 0.355017 (p.3
   18A .. 179, ARCH 2800, section B-B 5 risers).
4. The candidate ST-03 line 0.948267: its riser 0.165 and waist 0.175 against the drawn 0.170 and the unprinted waist.
5. Re-run: `python3 -I research/agents_t258/t258_alsenan_check.py --write` (byte-identical LEDGER_T258.csv / summary.json).

## 9. Not done / uncertain

- ST-02 RS-A and RS-LD were not re-measured by the Checker; they stay ASSUMED — OWNER-APPROVED on the conditional riser.
- The candidate run of this session (V3.0.11 on the Drive copies) did not finish inside the run; the candidate column
  rests on the merged Gate B records named in s.5.
- Formwork (T-163 r3 / T-192 43.777 m2), rebar (ST-01 294.73 .. 337.71 kg, shell bars 298.34 .. 432.93 kg / dome) are
  other lines; nothing released.
