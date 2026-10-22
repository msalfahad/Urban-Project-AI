# T-185 Alsenan domes: approved design (S0) vs client-requested change (S1) vs consultant revision (S2)

Worker 1 (structural lane S), 2026-10-22, run session_01Wwii72uJHHzX7veRCVzAWh. Development villa, not an accuracy
claim. Nothing is wired; no engine, rule, registry or released quantity changes. Scenario S1 is never released.

Governing decisions: owner Q-27 A (three domes: two on the 1F roof, one on the upper roof), Q-18 (dome size basis held
until confirmed; nothing printed = HELD, no default), Q-29 (client wants no concrete domes, open skylights) with its
2026-10-22 refinement (client request only, NO consultant revision; never remove the domes from the approved baseline;
do not assume open skylights need no structural redesign), Q-44 A (ring round each opening stays as the skylight edge,
B4 0.20 x 0.50 from the slab plan), Q-24 (roof membrane + 0.20 upturn; dome higher than the slab -> upturn round it),
Q-61 C(2)/C(3); ENGINEERING_REASONING_STANDARD sections 2-4.

Sources (Drive "Alsenan chalet project", private copies in `.work/private`, never committed), re-read this run:
"ST7757 dxf.dxf" p.7 DETAIL OF DOME (DIM 1A38 "442", 1A6D "190", 19B1 "10", 182F "AS PER ARCH"; concentric shell arcs
182B / 182E 500 drawn units apart = 10 cm at the detail's 0.02 factor; bar texts 1A0E / 1A15 "ø12MM/15cm"; ring texts
1A47 "3ø16", 1A4B "3ø18", 1A37 "2ø14/20cm", 1A29 "8ø8/m"; the four "6ø12/m" texts above it belong to the DETAIL OF
SWIMMING POOL, not to the dome); "P7757_DXF_COMPRESSED.zip" (2F plan circles 12EB / 2F33 r 2211.1 on the +9.70 roof,
circle 1300 r 2205.0 HIDDEN inside the 2F maid room; SE elevation "441" / "215" / "193");
"Alsenan_Architectural_P7757_Pages_11-12" p.1 SECTION B-B ("130" roof -> springing, "420" +9.70 -> +13.90, "50"
parapet; both terrace domes drawn in view on a drum of thin unhatched double lines; the roof slab is hatched).
Merged team work used as input and re-checked, not copied: T-160 (in-bay ring partition), S8.3 (dome population,
conflicts CF-S8.3-01 .. -09), T-037 (engine conventions), T-139 (slab panels), T-149 (B4 link path).
Drive searched for a revised sheet (folder listing 2026-10-22 16:25 UTC): none; newest drawing files 2026-10-19 are
single-sheet extracts of the issued set; the 2026-10-21 photos are designer renders (T-161).

Files: `t185_dome_scenarios.py` (pure module: shell geometry, bar population, scenario ledger with the S0 guard),
`ALSENAN_DOME_INPUT.json` (the printed values and the change record), `T185_LEDGER.json` (output). Repeat:
`python -I t185_dome_scenarios.py ALSENAN_DOME_INPUT.json --json T185_LEDGER.json`. Tests: `tests/t185_dome_scenarios`
(synthetic, not Alsenan; 13 cases).

## 1. Result in engineering terms

| Line | Engine (released A) | S0 approved design (this piece) | S1 client request (this piece) | Freelancer |
|---|---|---|---|---|
| Dome shell concrete, 2 terrace domes | 7.372 m3 (2 x 3.686: rise = radius 2.211 and shell 0.12 by convention) | **5.081 m3** (2 x 2.5407, printed 442 / 190 / 10, exact) DRAWING-CONFIRMED | 0 (removed by the scenario, not released) | 4.520 (2 x 2.26) |
| Tower dome shell | none | **HELD** (no structural drawing; outer surface 29.797 m2 from the elevation 441 / 215) | 0 by the scenario; a NEW slab opening would be needed: UNKNOWN | 2.260 |
| Shell bars, per terrace dome | none | **HELD 298.34 .. 432.93 kg** (population ø12/150 hoops + meridians; at the drawn bar position 305.80 .. 403.36) | 0 | no row |
| Ring beam concrete | west ring 0.7552 in the beam register (T-160) | **HELD**: plan B4 band vs detail ring under the shell edge, depth "AS PER ARCH" (A 0.7552 .. 1.1422, B 0.8997 .. 1.3108 at 0.50 only) | A **0.7552** B4 edge beam (Q-44 A) DRAWING-CONFIRMED; B HELD 0.8997 (D-28) | no row |
| Drum 1.30 m (roof -> springing) | none | **HELD** (drawn, material and thickness not printed) | 0 by the scenario | no row |
| Roof membrane upturn at the dome / opening | none | 2 x 13.893 m (0.20 high, 5.557 m2) at the drum face (arch R221), CALCULATED | 2 x 13.893 m HELD (needs a kerb that no drawing shows) | in his roof sheet |
| Opening open to the sky | n/a | 0 (closed by the dome) | 2 x 15.359 m2 (+ tower: no opening drawn), glazing UNKNOWN | n/a |

**How much of the 12.01 vs 21.833 m3 "stair + dome" gap is domes:** freelancer - engine = 21.833 - 12.007 = +9.826 m3 =
stairs (15.053 - 4.635 = **+10.418**) + domes (6.780 - 7.372 = **-0.592**). The domes do not explain the gap: on domes the
engine is HIGHER than the freelancer; the whole gap (and 0.592 more) is stairs (T-184).

Own S0 vs each side, domes only (m3):

| Step | Engine 7.372 -> own 5.081 (-2.291, -31.1 %) | Freelancer 6.780 -> own 5.081 (-1.699, -25.1 %) |
|---|---|---|
| scope | 2 domes both (no change) | third dome: his 2.260 has no structural basis (S0 HELD, not compared): -2.260 |
| rise | rise = radius 2.211 -> printed 1.90: per dome 3.686 -> 3.204 (-0.482) x 2 = **-0.964** | - |
| thickness | 0.12 -> printed 0.10: 3.204 -> 2.670 (-0.534) x 2 = **-1.068** | 0.10 both |
| surface | outer-area x t -> exact solid between the spheres: 2.670 -> 2.541 (-0.129) x 2 = **-0.259** | his 22.6 m2 typed (no formula) vs mid-surface 25.402 m2: +0.280 x 2 = **+0.561** |
| closes | -0.964 - 1.068 - 0.259 = -2.291: **0.000** | -2.260 + 0.561 = -1.699: **0.000** |

His 22.6 m2 per dome is not a printed or derivable cap area (outer 26.685, mid 25.402, inner 24.150 m2); it is close
to 2 pi x 1.90^2 = 22.68 m2, a hemisphere whose radius is the printed RISE: a trace, not established (his cell is typed).

## 2. The physical element (standard s.2 step 1)

Each terrace dome (DOME-A west, DOME-B east, ST p.5 centres 16.380 / 30.828, 41.651) is: a 10 cm reinforced-concrete
spherical cap (outer chord 4.42 at the springing, rise 1.90 to the outer apex: R_o 2.2353, centre 0.3353 below the
springing plane) standing on a ring and a 1.30 m drum on the +9.70 roof (springing +11.00, apex +12.90), over a
4.42 m circular opening in the 1F roof slab that lights the 1F room below (west: the master bedroom and two baths;
east: the living area, D-20). The slab opening is the same in every scenario (T-139 / T-160: 14.982 / 15.328 m2 inside
the bay faces), so the slab, its framing beams and the slab steel do not change between S0 and S1: only what stands
above the slab and closes or edges the opening changes. The tower dome is an architectural cap (chord 4.41, rise 2.15,
springing +14.40) over the 2F maid room; the structural +13.90 slab there is flat, with no opening and no ring.

Composite split (each its own item): shell concrete; shell bars (hoops, meridians, anchorage legs, laps); ring concrete;
ring bars (top, bottom, sides, links); drum; shell formwork (soffit, top); ring formwork; waterproofing (roof upturn at
the drum, the shell's own skin); internal and external finishes of the shell and the drum.

## 3. S0 approved design (drawings as issued), per terrace dome

| Item | Unit | Quantity | Status | Basis |
|---|---|---|---|---|
| Shell concrete | m3 | **2.5407** | DRAWING-CONFIRMED | V = pi/3 [h_o^2 (3R_o - h_o) - h_i^2 (3R_i - h_i)], h_o 1.90, R_i 2.1353, h_i 1.80 |
| Shell soffit (intrados) | m2 | 24.150 | CALCULATED | 2 pi R_i h_i: soffit form, internal finish |
| Shell extrados | m2 | 26.685 | CALCULATED | 2 pi R_o h_o: external finish / skin (finish not specified) |
| Hoops ø12/150 | kg | 155.23 .. 170.49 (drawn 157.81) | HELD (range) | 21 .. 22 hoops at equal spacing <= 0.15 along the meridian from the springing; bar sphere intrados .. extrados (cover not printed; drawn 2.1684 m) |
| Meridians ø12/150 | kg | 143.11 .. 262.44 (drawn 147.99 .. 245.55) | HELD (range) | 89 .. 93 bars round the springing circle; lower = curtailed continuously at the 0.15 maximum gap, upper = every bar to the crown as drawn (1A09 crosses the crown); curtailment not detailed |
| Shell bars total | kg | **298.34 .. 432.93** | HELD | hoops + meridians; d^2/162 (project method) |
| Hoop laps | kg | HELD | HELD | 5 .. 7 hoops exceed a 12 m bar; no lap length printed for shell bars |
| Anchorage legs into the ring | kg | HELD | HELD | drawn to the ring bottom (N.I.S); depth "AS PER ARCH" |
| Ring concrete | m3 | HELD (A 0.7552 .. 1.1422; B 0.8997 .. 1.3108 at 0.50 only) | HELD, CONFLICT | p.5 band r 2.211 - 2.411 (in-bay A 1.5105 / B 1.7994 m2) vs p.7 ring under the shell edge r 2.011 - 2.211 (in-bay A 2.2845 / B 2.6216 m2); depth "AS PER ARCH" (drawn 75 cm N.I.S, never used); A also tagged B4 20 x 50 |
| Ring bars 3ø16 + 3ø18 | kg | HELD 142.47 .. 155.97 (top + bottom only) | HELD | closed ring at centreline r 2.1111 (13.264 m) .. r 2.3111 (14.521 m); sides 2ø14/20cm and links 8ø8/m follow the depth; A's B4 tag gives 2ø12 / 4ø16 / 6ø8/m instead (CF-S8.3-04) |
| Drum 1.30 m | m3 | HELD | HELD | section B-B: roof +9.70 -> springing +11.00, unhatched thin wall; outer face 2 pi x 2.2111 x 1.30 = 18.061 m2 (geometry); RC or block, thickness: not printed |
| Roof membrane upturn at the drum | m | 13.893 (2.779 m2 at 0.20) | CALCULATED | Q-24: 0.20 upturn round a dome standing above the slab; drum face on the arch R221 circle |
| Shell top formwork | m2 | HELD | HELD | casting method not specified |
| Shell skin / external finish | m2 | HELD (area 26.685) | UNKNOWN finish | Q-24 "fiberglass or anything visible" |

S0 two terrace domes: concrete **5.081 m3 measured** + rings, drums HELD; shell bars **596.68 .. 865.86 kg HELD**;
tower dome all HELD. The S8.3 "released" 602.11 kg (a rate: mid-surface area / 0.150 per direction) sits inside the
population range near its lower end: it is the curtailed bound, not a count of the drawn bars.

## 4. S1 client-requested change (owner Q-29), per position; PROPOSED, never released

| Position | Removed (0 by the scenario) | Kept / added | Status |
|---|---|---|---|
| DOME-A | shell, shell bars, laps, anchorage, shell forms and finishes, drum | B4 edge ring 0.20 x 0.50 in-bay **0.7552 m3** (Q-44 A); its bars **62.60 .. 64.49 kg** (2ø12 + 4ø16 on 5.622 m of in-bay arc, 6ø8/m links A 36 / B 40 at the T-149 B4 path 1.200 m; end anchorage HELD); ring formwork **8.783 m2** (opening face 10.558 x 0.50 + outer downstand 5.865 x 0.34 + soffit 1.5105); open area 15.359 m2 | ring DRAWING-CONFIRMED; bars HELD; formwork CALCULATED (owner method in T-163) |
| DOME-B | as A | edge ring HELD (no section mark, D-28; candidate 0.8997 m3, bars 74.25 .. 76.15 kg); open area 15.359 m2 | HELD |
| A and B | | kerb / upstand for the 0.20 membrane upturn (none drawn): UNKNOWN; upturn 13.893 m each HELD on it; glazing / cover: UNKNOWN; drainage and wet treatment of the 1F rooms below: UNKNOWN | UNKNOWN |
| DOME-TOWER | shell (S0 HELD anyway) | a NEW opening in the flat +13.90 slab with trimmer beams, glazing, drainage of the room below: UNKNOWN | UNKNOWN |

S1 shell concrete 0 vs S0 5.081 m3 (-5.081, plus the held drums, the held tower dome and the S0 ring difference);
S1 new scope is mostly UNKNOWN. Nothing of S1 is released; the BOQ shows S0 and S1 side by side.

## 5. S2 consultant-revised design

UNKNOWN for all three positions: the owner confirmed (2026-10-22) that the consultant has issued no revised drawing,
and the Drive folder holds none. S2 is built only from a consultant-issued sheet that is on file
(`scenario_ledger`: a client record that names a drawing still leaves S2 UNKNOWN).

## 6. Owner manual method and drawing-derived method side by side

| Item | Owner / manual | Drawing-derived (this piece) | Difference and cause |
|---|---|---|---|
| Shell | freelancer 3 x 22.6 m2 x 0.10 = 6.780 | 2 x 2.5407 = 5.081 + tower HELD | -1.699: third dome scope (-2.260) + his area 22.6 vs mid-surface 25.402 (+0.561) |
| Dome plaster (his PLS row "dome inside and outside") | 6 faces x 3.14 x 9.65 = 181.806 m2 (30.30 m2 per face) | per terrace dome intrados 24.150 + extrados 26.685 = 50.835 (2 domes 101.67); tower extrados 29.797; drum faces HELD (18.061 outer each) | his per-face 30.30 = 2 pi r^2 with r = 2.197: a hemisphere on the opening radius, not the printed cap; finish not specified (owner: no domes in Sigma) |
| Ring per opening (S1) | Q-44 hand estimate "about 1.45 m3" (full annulus) | in-bay 0.7552 / HELD 0.8997 (T-160) | full annulus double-counts beams, columns and a slab panel (T-160) |
| Shell steel | (none in his RC steel) | population 298.34 .. 432.93 kg per dome | first measured population; rate 301.06 is the lower bound |

## 7. Cross-trade note for lane I (beam register and integration)

The beam register's west ring 0.7552 m3 (T-110 / T-160) is the p.5 B4 reading. It is the S1 edge beam (Q-44 A). Under
S0 the same ring is the dome's ring, whose section the issued set gives two ways (B4 vs the p.7 detail, depth "AS PER
ARCH"): in S0 that line is a CONFLICT, not a measured B4. Integration must tag the ring line with its scenario: the
register value stands for S1 and is HELD for S0. The slab, its opening and the framing beams are scenario-independent.
The engine's released STR.CONC.DOME lines (2 x 3.686) are convention values (A_NO_PROFILE_VALUE): T-186 (default guard)
should replace them with the printed-detail shell (2 x 2.5407) as S0, never with 0.

## 8. RFI for the consultant (project-specific, Alsenan only; not a general rule)

Before the client's change can be priced or released, the consultant must approve, with drawing references:

1. Opening geometry: the two 4.42 m openings in the 1F roof slab (ST p.5, dome bays between B6 / CB10 / CB13 and
   B6 / B25 / CB12) kept as they are? The opening circle crosses CB10, CB13 (and a column) and CB12 by 0.03 - 0.29 m2
   (T-160 s.7 item 3): confirm the beams stay whole.
2. Supporting / edge structure: the ring round each opening: B4 0.20 x 0.50 (p.5, west ring only) or another section
   (east ring unmarked, D-28); the p.7 ring (under the shell edge, depth "as per arch") and the 1.30 m drum disappear
   with the dome? Bars and anchorage of the edge ring into the framing beams.
3. Load path change: the dome, drum and ring loads (about 2 x 2.54 m3 of shell alone) leave the framing beams; any
   change to B6 / B25 / CB10 / CB12 / CB13 and the columns at the ring (ST p.5); the open area now carries no roof load
   but admits wind and rain.
4. Waterproofing and upstands: a kerb round each opening (none drawn) for the 0.20 membrane upturn the owner asks for
   (Q-44 A), its height, section and bars; flashing to the glazing if any.
5. Replacement system: glazing (fixed / opening, at the slab or on a kerb, which profile), or a truly open area: then
   drainage of the open area and the wet treatment of the 1F rooms below (west master bedroom and two baths, east
   living area: D-20), and the partitions under the west opening (D-42).
6. Tower position: the client's request covers all three domes, but no opening exists in the +13.90 slab over the
   2F maid room (ST p.6 flat panel; section A-A draws no dome there): is a new opening wanted (slab redesign, trimmer
   beams) or does the tower position simply have no dome? (D-21, CF-S8.3-01.)
7. For S0 itself (independent of the change): ring position and depth (p.5 band vs p.7 detail, "AS PER ARCH"),
   whether the drum is RC, the B4 tag vs the dome detail bars on the west ring, the crown curtailment of the meridians,
   laps of the 13.6 m hoops and the shell-to-ring anchorage (Q-S8.3-01 .. -04).

## 9. Verdict proposals (for the checker)

- Dome shells, 2 terrace domes: **HAND_RIGHT (drawing) / ENGINE WRONG**: 5.081 vs engine 7.372 (+2.291, +45.1 %:
  rise and thickness conventions where the detail prints 190 / 10). Freelancer 2 x 2.26 = 4.520 vs 5.081 (-0.561,
  -11.0 %): **FREELANCER area not established** (typed 22.6).
- Third dome: **UNRESOLVED** (Q-27 A: it exists; no structural drawing; HELD, never 0, never his 2.26).
- Dome share of the stair + dome gap: **-0.592 m3** (domes are not the cause; stairs +10.418).
- Shell steel: first population count, HELD range (bar position, crown curtailment, laps not dimensioned).
- Checker re-measure suggestion: one dome by hand: R_o = (2.21^2 + 1.90^2) / 3.80 = 2.23529; R_i 2.13529;
  h_i = R_i - 0.33529 = 1.80; V = pi/3 (1.90^2 x 4.80588 - 1.80^2 x 4.60588) = pi/3 (17.34923 - 14.92306) = 2.5407.

## 10. Rule, test, lessons row (standard s.4 B / C, s.7)

- Rule (any villa, any element; owner 2026-10-22, provenance: owner directive, not a project assumption): a change
  requested by the client and not issued by the consultant is a scenario S1 beside the approved-design baseline S0; S0
  is never edited by it; S1 is never released; S2 exists only from a consultant-issued drawing on file; new S1 scope
  without a printed value is UNKNOWN, never 0. Geometry rule (any villa): a dome shell is measured from its printed
  chord, rise and thickness as the solid between concentric spheres; rise = radius, a hemisphere of the rise or a
  default thickness are never used when the detail prints them; a dome without a structural detail stays HELD.
  Recording it as a rule version is lane I's (T-178); this piece holds the test.
- Test: `tests/t185_dome_scenarios` (13): S0 identical with and without the client request (adverse), S1 absent and
  unreleased, S2 UNKNOWN unless a consultant drawing is on file (adverse: a client naming a drawing), missing thickness
  HELD (adverse: never a default), no detail HELD, area is the printed cap not a hemisphere of the rise, rise never the
  radius, bars by population not a rate, mm = m.
- Proposed lessons row: | 2026-10-22 | Engine domes 7.372 vs drawing 5.081 m3; freelancer 6.780 with a typed 22.6 m2
  and a third dome without structure | Engine rise = radius and shell 0.12 by convention although the detail prints 190 /
  10; freelancer area not from the cap; earlier Q-29 application took the dome out of the baseline | Dome shell from the
  printed chord / rise / thickness (exact concentric solid), no detail = HELD; client change = S1 beside S0, S0 never
  edited, S1 never released, S2 only from an issued drawing (any villa) | T-185 (13 cases) | READY for the checker |

## 11. Held / not measured (never 0)

Tower dome concrete and support; both rings (position and depth); both drums (material, thickness); shell bar laps
and anchorage; crown curtailment; ring sides and links; shell top formwork; shell and drum finishes; S1 kerbs,
glazing, drainage, the tower opening, the east edge ring; all of S2.
