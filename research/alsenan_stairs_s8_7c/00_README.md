# S8.7C: stair design resolution study

Baseline HEAD `0cda418`. Date 2026-10-10. State: `FROZEN_BEFORE_COMPARISON` (`13_S8_7C_FREEZE_MANIFEST.json`).

This is an engineering research and design-comparison exercise. **It is NOT approval to change the drawings.** No
arrangement here is approved or selected. S8.7, S8.7A and S8.7B are read and never written. All 28 earlier freezes
verify unchanged. **Release delta: 0 m3 concrete, 0 kg reinforcement.** S8.7's frozen release
(0.516582788 m3 / 59.020862261 kg) is untouched, and the production BOQ is not updated.

Every value carries a status:

- `MEASURED_DRAWING_FACT` is read from the drawings by handle.
- `PRINTED_ON_DRAWING` is printed on a drawing.
- `SCALED_FROM_SECTION (indicative)` is measured on the 1:100 section render.
- `PROPOSED_MODIFICATION (not drawn)` is a change that no drawing shows.
- `GEOMETRICALLY_POSSIBLE_ONLY_WITH_MODIFICATIONS (unverified)` means it would work only with stated changes and has not been checked by an engineer.

## The answer

**The GF -> 1F arrangement most consistent with the drawings is B-27-S: section A-A's 27 risers.** It is 10 risers,
then a five-riser winder turn, the landing at +3.50, then 12 risers. Each riser is 166.6666667 mm.

It is the only arrangement that matches all three of these:

1. **The printed half-landing.** Fifteen equal risers reach the printed +3.50 exactly.
2. **The section's winder treads.** Section A-A draws five dashed treads in the turn at +2.671, +2.836, +3.005, +3.171, +3.336. 27 equal risers put
   the treads after risers 10 - 14 at +2.667, +2.833, +3.000, +3.167, +3.333, each within 5 mm. The structural sheet's 28 would put its four turn treads
   at +2.929, +3.089, +3.250, +3.411.
3. **The drawn ends of the flights.**
   - Its foot, y 16761.9, is the architectural GF plan's and the ground-beam plan's first
     riser. Section A-A's foot scales at y 16728.
   - Its 12-riser upper flight is the structural sheet's, and section A-A's, which scales 3300
     mm and arrives at y 16112.

**It still conflicts with the drawings in four places.**

- **B20.** Removing one riser does **not** remove the beam interference. The last upper riser is still
  200 mm inside B20, because the clash comes from the upper flight (12 risers at 300 mm),
  not from the total.
- **The plan turn.** Both plans draw four turn risers (three radial plus the closing riser). The section needs five:
  four radial plus the closing riser. Five treads on the drawn quarter give a 218.5 mm
  going on the 600 mm walking line.
- **Each plan agrees on one flight only.** The structural sheet's lower flight has 12 risers, with its foot 600 mm
  south. The architectural plan's upper flight has 11 risers, stopping 100 mm short of B20.
- **The riser height.** 166.667 mm is above the owner's preferred 150 - 160 mm.

**Two smallest changes would resolve it.** Both are proposals; neither is drawn.

- **(a) Lower B20.** Drop or crank B20 locally under the top tread, by about one riser (166.7
  mm). This is for the engineer.
- **(b) Shorten the upper goings.** This is **B-27-SM**: upper goings of 272.7 mm leave a 100 mm
  strip before B20, as on the architectural plan. This is for the architect.

Either way, the plan turn must be redrawn with four radial risers.

**The owner's provisional 28 (A-28) conflicts with the drawings in three independent ways.**

- **The landing comes out at +3.571**, 71.4 mm above the printed
  +3.50.
- **The last riser is 200 mm inside B20.**
- **The foot is 600 mm south** of the architectural plan, the ground-beam plan and the section.

Shortening the upper goings (A-28-M) clears B20 but leaves the landing conflict. No 28-riser arrangement with equal
risers reaches +3.50.

## A. GF -> 1F: 27 vs 28 risers

| Scenario | Risers | Riser (mm) | Lower / turn / upper | Foot y | Landing | B20 clearance | Section turn treads | Drawing changes to resolve | Status |
|---|---|---|---|---|---|---|---|---|---|
| A-28 | 28 | 160.714 | 12 / 4 / 12 | 16161.9 | +3.571 (+71.4 mm) | -200 mm | no | 4 | CONFLICTING |
| A-28-M | 28 | 160.714 | 12 / 4 / 12 (upper going 272.7) | 16161.9 | +3.571 (+71.4 mm) | 100 mm | no | 4 | CONFLICTING (landing) even with the modification |
| B-27-S | 27 | 166.667 | 10 / 5 / 12 | 16761.9 | +3.500 (0 mm) | -200 mm | match | 3 | CONFLICTING |
| B-27-SM | 27 | 166.667 | 10 / 5 / 12 (upper going 272.7) | 16761.9 | +3.500 (0 mm) | 100 mm | match | 3 | GEOMETRICALLY_POSSIBLE_ONLY_WITH_MODIFICATIONS (unverified) |
| B-27-P | 27 | 166.667 | 11 / 4 / 12 | 16461.9 | +3.500 (0 mm) | -200 mm | no | 5 | CONFLICTING |
| B-27-U | 27 | 166.667 | 12 / 4 / 11 | 16161.9 | +3.667 (+166.7 mm) | 100 mm | no | 4 | CONFLICTING |
| REF-25 | 25 | 180 | 10 / 4 / 11 | 16761.9 | +3.520 (+20 mm) | 100 mm | no | 2 | REFERENCE_ONLY |

Conflicts and modifications for each scenario are in `02_GF_1F_27_VS_28_GEOMETRY.csv`. That file keeps **what the
drawings show** (DRAWN_BY, the FACT columns) apart from **what would have to change**: MODIFICATIONS_NEEDED for the
arrangement itself, and CHANGES_TO_RESOLVE drawing by drawing. Every change listed is a proposal; none is drawn.
REF-25 is the architectural GF plan as drawn: 180 mm risers, shown for reference only.

What would have to change for each of the three main candidates to be shown consistently:

- **A-28:**
  - architectural GF plan: lower flight 10 -> 12 risers (foot 600 mm south); upper flight 11 -> 12 risers
  - section A-A: lower flight 10 -> 12 risers (foot 600 mm south); turn 5 -> 4 risers (4 -> 3 radial); printed half-landing +3.50 -> +3.571
  - ground-beam plan: first riser 600 mm south
  - B20 (structural, S6): lowered / cranked locally under the top tread by about 160.7 mm
- **B-27-S:**
  - structural GF roof sheet: lower flight 12 -> 10 risers (foot 600 mm north); turn 4 -> 5 risers (3 -> 4 radial)
  - architectural GF plan: turn 4 -> 5 risers (3 -> 4 radial); upper flight 11 -> 12 risers
  - B20 (structural, S6): lowered / cranked locally under the top tread by about 166.7 mm
- **B-27-SM:**
  - structural GF roof sheet: lower flight 12 -> 10 risers (foot 600 mm north); turn 4 -> 5 risers (3 -> 4 radial); upper goings 300 -> 272.7 mm
  - architectural GF plan: turn 4 -> 5 risers (3 -> 4 radial); upper flight 11 -> 12 risers; upper goings 300 -> 272.7 mm
  - section A-A: upper goings 300 -> 272.7 mm

B-27-S is the only candidate that needs no change to section A-A or to the printed level. Its changes fall on the
plans' turn and counts, and on B20 (or, as B-27-SM, on the goings of all three drawings instead of on B20).

### Where each conflict comes from

**The +71.4 mm landing (A-28).**

- A-28 has 12 lower risers plus 4 turn risers, so 16 risers stand below the landing.
- 16 x 160.7142857 = 2571.4 mm, which puts the landing at +3.571.
- Reaching +3.50 would need 2500 / 160.714 = 15.56 risers.
- With 28 equal risers, +3.50 falls between riser 15 (+3.411) and riser 16 (+3.571).
- Only 27 (and 36) of the counts 20 - 40 reach +3.50 exactly.

**The 200 mm B20 interference (A-28 and B-27-S alike).**

- The upper flight's first riser is the landing edge, y 19411.9.
- From there to B20's north face (y 16311.9) is 3100 mm.
- At 300 mm goings at most 11 risers fit: 10 goings, leaving a 100 mm strip.
- The 12th upper riser, the arrival riser, therefore lands at y 16111.9, inside the B20 band
  (15911.9 - 16311.9).
- The last tread spans y 16111.9 - 16411.9. It sits one riser below the 1F floor, over 200 mm of B20.
- For 12 risers to clear B20 with a 100 mm strip, the goings would have to be 272.7 mm or
  less. With no strip, they would have to be 281.8 mm or less.

Section A-A draws the upper flight arriving at y 16112 and its nearest downstand at y
15604. **It draws nothing in B20's band**, so the section neither shows nor resolves the
clash.

### Finished levels at every transition

Equal finished risers are assumed, from GF +1.00 to 1F +5.50.

**A-28 (structural sheet):**

| Segment | Risers | Riser numbers | Starts at | Ends at | Plan y start -> end |
|---|---|---|---|---|---|
| lower flight | 12 | 1 - 12 | +1.000 | +2.929 | 16161.856 -> 19461.856 |
| turn (winders) | 4 | 13 - 16 | +2.929 | +3.571 | 19461.856 -> closing riser x 18387.9 |
| landing (NE quarter) | 0 | - | +3.571 | +3.571 | 19411.856 -> 19411.856 |
| upper flight | 12 | 17 - 28 | +3.571 | +5.500 | 19411.856 -> 16111.856 |

**B-27-S (section A-A):**

| Segment | Risers | Riser numbers | Starts at | Ends at | Plan y start -> end |
|---|---|---|---|---|---|
| lower flight | 10 | 1 - 10 | +1.000 | +2.667 | 16761.856 -> 19461.856 |
| turn (winders) | 5 | 11 - 15 | +2.667 | +3.500 | 19461.856 -> closing riser x 18387.9 |
| landing (NE quarter) | 0 | - | +3.500 | +3.500 | 19411.856 -> 19411.856 |
| upper flight | 12 | 16 - 27 | +3.500 | +5.500 | 19411.856 -> 16111.856 |

The other scenarios are in `03_GF_1F_TRANSITION_LEVELS.csv`.

**Landing footprint.** The NE quarter is 1200 x 1200 = 1.44 m2, at x 18387.9 - 19587.9 and y 19411.9 - 20611.9.

**Clearances** (`04_LANDING_BEAM_CLASH_AUDIT.csv`):

- **Column 36B** projects 50 mm into the lower flight over y 17111.9 - 17611.9. The clear width there is 1150 mm in
  every scenario.
- **The central wall** has tread lines that stop 50 mm short of both wall faces.
- **Foot support.** No ground beam is drawn under any foot; the drawn ground beam is 450 - 1050 mm south. The typical
  G.B on p.16 is not a project fact.
- **Headroom under B20** at A-28's foot is about 3.59 m, less the 1F floor build-up.

## B. 1F -> 2F (owner scenario 27 retained, provisional)

| Case | Basis | Risers | Riser (mm) | Lower / turn / upper | Landing | B23 clearance | Status |
|---|---|---|---|---|---|---|---|
| OWNER-27 | owner scenario = architectural 1F plan | 27 | 155.556 | 12 / 4 (winders: 3 radial + closing) / 11 | +7.989 | 100 mm | PROVISIONAL_OWNER_SCENARIO |
| FFRS-24 | structural 1F roof sheet; architectural 2F view (repeated) | 24 | 175 | 12 / 1 (flat quarter + closing riser) / 11 | +7.775 | 100 mm | MEASURED_DRAWING_FACT |
| SECTION-25 | section A-A (measured) | 25 | 168 | 12 / 1 (flat quarter + closing riser) / 12 | +7.684 | -200 mm | SCALED_FROM_SECTION (indicative) |

The owner's 27 is the architectural 1F plan: 12 risers, four winders, the landing, then 11 risers.

- **Riser:** 155.556 mm.
- **B23:** clear by 100 mm. S8.7's released strip A2-T1 fills that 100 mm.
- **Landing:** +7.989. It is **not printed**; section A-A scales its landing at
  about +7.69, about 0.30 m lower.
- **Plan capacity:** at 300 mm goings the drawn plan holds at most 24 risers with a flat quarter.
  It holds exactly 27 with the four-riser winder turn.

So **the owner's 27 depends on the architectural winders.** The structural 1F roof sheet, the architectural 2F view
and section A-A all draw a flat quarter: the section shows no dashed winder lines in that turn.

**The architectural winders are not treated as structurally approved.** Their structural form, soffit and support are
not drawn.

Section A-A's own 1F -> 2F arrangement (13 + 12 = 25) repeats the GF -> 1F pattern: its 12-riser upper flight would be
200 mm inside B23.

## C. Round stair (observed 28; research scenario, not owner-approved)

| ID | Item | Value | Status |
|---|---|---|---|
| R-01 | foot level | +1.00 inferred | INFERRED_NOT_PRINTED |
| R-02 | riser count | 28 = 12 curved + 11 straight / corner landing / 5 | MEASURED_DRAWING_FACT |
| R-03 | finished riser | 160.7142857 mm (if +1.00 -> +5.50 and equal) | INFERRED_NOT_PRINTED |
| R-04 | curved flight: radial risers | 12 from 177.78 to 263.49 deg | MEASURED_DRAWING_FACT |
| R-05 | curved flight: goings | inner 215 / walking line 293 / outer 371 mm | MEASURED_DRAWING_FACT |
| R-06 | straight flight | 11 risers at 300, x 23757.9 -> 26757.9, width 1150 (tread lines) | MEASURED_DRAWING_FACT |
| R-07 | corner landing | 1150 x 1200 less column 374 (0.0275 m2); level +4.696 if equal risers | INFERRED_NOT_PRINTED |
| R-08 | short flight and arrival | 5 risers y 10211.9 -> 11411.9 to +5.50; arrival plate C-T1 (S8.7, released) | PRINTED_ON_DRAWING |
| R-09 | stair zone at the 1F floor | SP-GF_ROOF_SLAB-21 (STAIR_IN_VOID_ZONE) and -28 (STAIR_FLIGHT_ZONE) | FROZEN_RECORD |
| R-10 | beam CA | 30 x 50, across the straight flight between risers 15 and 16 (x 24357.9 - 24657.9) | REQUIRES_ENGINEER_CONFIRMATION |
| R-11 | south edge beam | B3 '(With Stair)' 20 x 40 on line BL022 along the straight flight | UNVERIFIED_ENGINEERING_INTERPRETATION |
| R-12 | main-stair landing levels | not applied | RULE |

**The round stair keeps its own levels.** The main stair's +3.50 is not applied to it.

- **Beam CA is the decisive open item.** CA (30 x 50) crosses the straight flight over the tread after riser 15. If CA
  is framed at the 1F floor, the clear height under it is about 1.59 m, less the build-up.
- **The south-edge beam is unverified.** The B3 "(With Stair)" beam on the south edge may be the p.16 cranked stair
  beam; that is not verified.

## D. Finishes and thickness

- **Marble:** 30 mm, a provisional owner scenario. Whether the 30 mm includes bedding is **unknown**.
- **Floor build-ups at GF / 1F / 2F:** **unknown**.
- **Structural waist and landing thickness:** **unknown**. On p.16, "THICK" has no value.

Every riser above is finished floor to finished floor. The first and last concrete risers follow S8.7B's datum
formula (`h + f_b - s`, `h - f_t + s`) once the build-ups are given.

**The 150 / 160 / 175 / 200 mm waists are a sensitivity grid only.** They are not approved dimensions.

## E. Conditional concrete, GF -> 1F (never released)

Every scenario uses the same scope and conventions:

- the two flights by the exact section integral, waist plus step wedges;
- the turn as plane-equivalent winders, with a flat-soffit upper bound;
- the column 36B cut-out and the B20 overlap zone kept as deductions;
- the S8.7 landing A1-L1 excluded, because it is already owned.

The arrival strip before B20, where one exists, is shown with its ownership unresolved and is never in a total.

| Scenario | waist 150: gross / NET / upper | waist 160: gross / NET / upper | waist 175: gross / NET / upper | waist 200: gross / NET / upper |
|---|---|---|---|---|
| A-28 | 2.364 / 2.305 / 2.577 | 2.472 / 2.409 / 2.681 | 2.632 / 2.565 / 2.839 | 2.900 / 2.825 / 3.101 |
| A-28-M | 2.288 / 2.282 / 2.501 | 2.393 / 2.386 / 2.602 | 2.549 / 2.542 / 2.755 | 2.809 / 2.801 / 3.009 |
| B-27-S | 2.242 / 2.181 / 2.558 | 2.343 / 2.279 / 2.655 | 2.495 / 2.427 / 2.801 | 2.748 / 2.672 / 3.045 |
| B-27-SM | 2.165 / 2.159 / 2.481 | 2.263 / 2.257 / 2.576 | 2.411 / 2.403 / 2.717 | 2.656 / 2.648 / 2.952 |
| B-27-P | 2.315 / 2.254 / 2.533 | 2.419 / 2.355 / 2.635 | 2.575 / 2.506 / 2.787 | 2.835 / 2.758 / 3.040 |
| B-27-U | 2.315 / 2.308 / 2.533 | 2.419 / 2.412 / 2.635 | 2.575 / 2.567 / 2.787 | 2.835 / 2.827 / 3.040 |
| REF-25 | 2.215 / 2.209 / 2.449 | 2.313 / 2.306 / 2.543 | 2.459 / 2.452 / 2.686 | 2.704 / 2.696 / 2.922 |

At waist 160, B-27-S's NET is 0.129 m3 less than A-28's: three fewer flight
risers, one more winder. The component split at waist 160:

| Component (waist 160) | A-28 gross | A-28 deductions | B-27-S gross | B-27-S deductions | Lane |
|---|---|---|---|---|---|
| lower flight | 1.0370 | 0.0065 | 0.8630 | 0.0067 | RESEARCH_SENSITIVITY_NOT_RELEASED |
| turn (winders) | 0.3977 | 0.0000 | 0.4254 | 0.0000 | CONDITIONAL_ESTIMATE_NOT_RELEASED |
| landing A1-L1 (NE quarter) | 0.2304 | 0.0000 | 0.2304 | 0.0000 | ALREADY_OWNED_BY_S8_7 (frozen; not counted again) |
| upper flight | 1.0370 | 0.0564 | 1.0548 | 0.0573 | RESEARCH_SENSITIVITY_NOT_RELEASED |
| TOTAL (new; S8.7 landing excluded) | 2.4717 | 0.0630 | 2.3433 | 0.0639 | RESEARCH_SENSITIVITY_NOT_RELEASED |

Every flag:

- `WAIST_UNKNOWN` on every row;
- `WINDER_SOFFIT_NOT_DRAWN` on every turn;
- `PROPOSED_TURN_GEOMETRY_NOT_DRAWN` on the five-riser turn;
- `B20_ZONE_OWNERSHIP_UNRESOLVED` where the last tread overlaps B20;
- `PROPOSED_GOING_NOT_DRAWN` on the modified goings.

## Reinforcement and double counting

- **Flight bars.** The 8Ø16/m main bars along the two flights are context only: A-28 113.6 kg, B-27-S
  104.1 kg. They are never released.
- **The turn** is blocked: its bar paths are not drawn.
- **Preserved ownership:**
  - S8.7 owns its released 59.020862261 kg over A1-L1 / A2-T1 / C-T1;
  - S7 owns its top extensions (71.895327413 kg);
  - S6 owns B20 and B23 (lower bounds 110 / 145.2 kg).
- **The B20 overlap zone** is never a stair bar zone.
- **Blocked families.** Ten typical-only families remain blocked, among them the 6Ø14/m and 6Ø12/m top bars,
  distribution, step and nosing bars, the starters, the edge, ground and cranked beams, and every anchorage, lap and
  bend.

See `08_REINFORCEMENT_DOUBLE_COUNT_AUDIT.csv`.

## What remains subject to engineer approval

1. **The governing GF -> 1F arrangement.** This is for the architect and engineer. It covers the turn redrawn with
   five winder treads, and the acceptability of the 218.5 mm walking-line going.
2. **The B20 head.** Either B20 is lowered or cranked locally by about one riser, or the upper goings are shortened
   to 272.7 mm or less.
3. **The 1F -> 2F winders.** Their structural form, soffit, support and bars, and the landing level (+7.989 with 27,
   not printed).
4. **The waist and landing thicknesses**, and the support at both feet (no ground beam is drawn under them).
5. **The round stair's beam CA** (level and role) and whether B3 "(With Stair)" is the cranked stair beam.
6. **The typical-only bars, anchorage and laps** that apply.
7. **For the owner and architect, not the engineer:** the riser height (166.667 or 160.714 mm, both above 160), the
   marble bedding, and the floor build-ups.

## Short prioritised RFI

| Priority | To | Question |
|---|---|---|
| P1 | architect | GF -> 1F arrangement: section A-A draws 10 + 5-riser turn + 12 = 27 risers (166.667 mm) to the printed +3.50; the structural GF roof sheet draws 12 + 4 + 12 = 28 (landing +3.571, foot 600 mm south); the architectural GF plan draws 10 + 4 + 11 = 25. Confirm which arrangement governs. If it is the section's, redraw the plans' turn with five winder treads (four radial risers) and confirm the 218.5 mm walking-line going (600 mm from the fan centre) is acceptable. |
| P1 | engineer | B20 at the GF -> 1F head: every 12-riser upper flight at 300 goings (structural sheet, section A-A) puts the last riser 200 mm inside B20. Choose: lower / crank B20 locally under the top tread (about one riser), or let the architect shorten the upper goings to <= 272.7 mm (or 281.8 mm with no arrival strip). |
| P1 | engineer | Round stair beam CA (30 x 50) crosses the straight flight over the tread at +3.411: if it sits at the 1F floor it leaves about 1.59 m headroom. State its level (support under the flight or an error). |
| P2 | owner | Riser preference: 27 risers = 166.667 mm and 28 = 160.714 mm are both above 160 mm. Accept one of them; 27 is the count that matches the printed +3.50 with equal risers. |
| P2 | architect / engineer | 1F -> 2F: the owner's 27 needs the architectural four-riser winder turn; the structural sheet and section A-A draw a flat quarter. Confirm the winders, their structural form and the landing level (+7.989 with 27; section scales +7.69). |
| P2 | engineer | Structural waist and landing thickness (p.16 'THICK' has no value). |
| P3 | architect | Marble bedding / adhesive (is it inside the 30 mm?) and the floor build-ups at GF, 1F and 2F (they set the first and last concrete risers). |
| P3 | engineer | Applicable typical bars, anchorage and laps; whether the 'With Stair' B3 / CB3 beams are the p.16 cranked stair beam. |

## Diagrams (schematic, drawn from the coordinates; not drawings)

- **`14_DIAGRAM_GF_1F_PLAN.svg`** shows A-28 and B-27-S side by side: the riser lines with riser numbers, the turn
  (solid: the three radials read by handle; dashed: the proposed four-radial turn), the landing level, and B20 hatched,
  with the risers inside B20 in red.
- **`15_DIAGRAM_GF_1F_DEVELOPED_SECTION.svg`** shows both arrangements along the walking line against +1.00, the
  printed +3.50 and +5.50, with B20 under the 1F floor.

## Files

| File | Content |
|---|---|
| `01_SOURCE_EVIDENCE_REGISTER.csv` | Every cited position re-read by handle, the section A-A measurements, and the frozen records used |
| `02` / `03` | GF -> 1F scenarios; transition levels |
| `04` | Landing, beam, column, wall and foot clash audit |
| `05` | 1F -> 2F winder reconciliation and plan capacity |
| `06` | Round-stair geometry audit |
| `07` | Conditional concrete comparison (four waists, components, deductions, upper bounds) |
| `08` | Reinforcement and double-count audit |
| `09` | Prioritised RFI |
| `10` | Conservation checks |
| `11_RELEASE_SUMMARY.json` | Release summary |
| `12_PROVENANCE.jsonl` | Provenance |
| `14` / `15` | Diagrams |
| `13_S8_7C_FREEZE_MANIFEST.json` | Freeze manifest |

## Reproduce

```
python3 -I research/alsenan_stairs_s8_7c/build_s8_7c.py
```

The build needs the private drawings in `data/inputs/by_sha256` (never committed). The section A-A render goes to a
temporary folder and is deleted after measuring. Two builds are byte-identical.
