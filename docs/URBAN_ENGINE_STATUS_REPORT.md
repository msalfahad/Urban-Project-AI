# Urban QS Engine — status report

**Date:** 24 September 2026
**Project:** Urban Projects quantity-surveying engine (Kuwait villas)
**Latest measured project:** Ahmad Abdullah Ali Al Rashed — Sabah Al Ahmad, Block D4, Plot 247, 600.00 m² plot
**Frozen takeoff:** commit `3e847af`, digest `ae259eaba3203798` — unchanged by everything described below
**Report revision:** 2 (external audit corrections applied)

> This file is the plain-text twin of the HTML report. It is written so another AI assistant, or a colleague with
> no access to this repository, can understand the whole system from this one document.

---

## 0. One-paragraph summary

Two villas have now been measured from their own drawings — the second one blind, then checked against a
historical Excel workbook that was kept sealed until the measurement was frozen. The engine measures a villa end
to end and can defend every number down to the rectangles a room is made of. It cannot yet price one, store one,
or be run by anybody except the agent that built it. **I put the whole system at roughly 55% of the way to the
product**, with the measurement half strong and the application half barely begun.

Key figures: **135 connected components** — 64 spaces and 71 wall slivers, not 135 rooms — 184 rectangles,
0.000000 m² decomposition residual, 22 of 22 executable quality checks passing on the corrected workbook.

**Revision 2 corrects three claims made in revision 1**, after an external audit:

1. "135 rooms measured" was wrong. There are 135 connected components: 16 internal rooms, 12 wet rooms, 1 kitchen,
   9 stair/landing, 24 unnamed spaces, 2 external areas and **71 wall material or sliver components**.
2. 196.378 m² of stair, landing and unnamed floor area was exported as `PORCELAIN_FLOOR`. Its finish is not
   settled, so it is now `FLOOR_FINISH_UNCLASSIFIED` / `AR-FL-PENDING`, measured and kept but out of the base BOQ.
3. "0 engine errors" described **the historical validation only** — no difference against the historical workbook
   proved a frozen quantity wrong. It never meant the engine makes no mistakes; the audit went on to find four
   classification defects in the detailed export, all corrected here and now covered by tests.

Also provisional, and clearly marked as such: **skirting** (828.493 lm split into three decision buckets) and
**ceiling finish** (931.016 m² of area is final, the ceiling type is not).

---

## 1. Where we are

The single percentage is a weighted average of the capabilities below, not an impression.

| Capability | Weight | Done | Where it stands |
|---|---:|---:|---|
| Source ingest and identity (DWG decode, units, revision isolation) | 10 | 85% | Proved the drawing unit against a wrongly set `INSUNITS`; picked the issued revision out of nine plan windows by dimension containment, score 1.000 |
| Geometry and component recovery | 15 | 75% | Exact for axis-aligned plans: components are whole grid cells, areas are sums of exact products. Curved or angled plans are not handled at all |
| Semantic labelling (room names, roles, Arabic and English) | 8 | 60% | Labels matched through a fitted PDF↔DWG transform. 128.8 m² is still `UNNAMED_ON_DRAWING` — measured exactly, identity not stated |
| Openings | 10 | 65% | 35 doors and 7 windows, every width measured from the drawing. Heights still come from owner input or the size guide |
| The third dimension (heights from sections and elevations) | 7 | 25% | Every height in this project is an owner input. The engine cannot read a section yet, and refuses to guess |
| Trade measurement rules | 10 | 55% | Seven rules travel across projects. Most trades still need a project answer |
| Quantity output and schema | 10 | 80% | 13-sheet Arabic workbook with live formulas; 265-record JSON export with quantity, waste, procurement, rate and amount as five separate fields |
| Validation and QA | 10 | 70% | Blind protocol, freeze, 15 deterministic checks, 3,028 regression tests. Two villas is still a small sample |
| Pricing and procurement | 5 | 10% | Columns exist and are deliberately empty. No rate library, no waste standard |
| The web app itself | 10 | 5% | Nothing built. The data model and file formats it needs do exist |
| Generalisation | 5 | 35% | Two villas, one office. Each new project still needs a human to confirm the plan windows |

**Weighted total: 56%. I would tell a client 55%.**

---

## 2. How the engine works today

Nine stages. Each one can refuse: a stage that cannot establish something marks the item and moves on rather than
filling the gap with a plausible value. That single habit is why the validation found no engine error.

| # | Stage | What it establishes | How it fails safely |
|---|---|---|---|
| 1 | Decode | Entities, layers and blocks out of the DWG | Legacy Arabic font bytes are replaced, not guessed at |
| 2 | Units | 1 unit = 1 m, proved by wall pairs landing in the 50–600 mm band | A declared unit overrides `INSUNITS` only on physical evidence |
| 3 | Region isolation | Which three plan windows the issued PDF actually plots | A containment score below 1.000 means ask, not assume |
| 4 | Grid | Every wall face becomes a grid line; the plan is exactly a set of rectangles | A closure residual other than zero fails the check |
| 5 | Rooms | Connected cells, with doorways virtually closed up to 3.00 m | A room leaking through a doorway shows up as an absurd area |
| 6 | Labels | Room names, through a similarity transform that includes a reflection | No inliers → no labels, rather than wrong labels |
| 7 | Openings | Doors from jamb marks, windows from white wipeout rectangles | A symbol with no measurable gap keeps its type and loses its width |
| 8 | Quantities | Trade measurement under the rule ladder | A missing height blocks the quantity instead of inventing one |
| 9 | Output | Workbook, JSON export, digest, freeze | Every record leaves as `DRAFT`; the engine never approves itself |

### The four-layer model everything sits on

`PHYSICAL_GEOMETRY` → `TOPOLOGICAL_SITES` → `TRADE_MEASUREMENT_REGIONS` → `QUANTITIES`, and three quantity layers
that are never merged: `PHYSICAL_MEASUREMENT`, `COMMERCIAL_MEASUREMENT_RULE`, `FINAL_BOQ_QUANTITY`.

---

## 3. The rules it now carries

A number given for one villa stays with that villa. A rule approved by the owner travels to every future project.
The two are stored separately so the next project inherits the rule and not the number.

### The priority ladder (strict order; a lower rank is never used while a higher one can answer)

1. A dimension written on the drawing
2. A dimension measured from the drawing geometry
3. An explicit owner value for this project
4. An approved Urban standard
5. Ask the owner — nothing is invented at this rank

### The rule library

| Rule | What it says | Travels | Came from |
|---|---|---|---|
| `US-18` | A wet or service room takes porcelain to the floor and to the full wall height automatically; a fully tiled face takes no paint and no skirting | yes | AR-05 |
| `US-19` | The window size guide, as a fallback for heights only. A measured width always beats the guide's width | yes | Owner's guide table |
| `US-20` | Before any count or quantity is compared, both sides are reduced to the same population of objects | yes | A 36% door-count error that fell to zero once aluminium and steel leaves joined the wooden ones |
| `US-21` | An aluminium quantity taken from architectural drawings is published as drawing scope only, never as a supply quantity | yes | 7 glazed openings drawn against 34 objects on site |
| `US-22` | Every row of an opening schedule carries a floor. Where it is not established the value is `UNKNOWN` and the row is marked | yes | One missing header blocked 27 of 31 rows from comparison |
| `DS-01` | Quantity, unit, waste, procurement quantity, rate and amount occupy separate fields and separate columns. No cell ever holds a quantity and a price together | permanent | `=1100+325+430+150*2.5` — a cell from which no quantity can ever be recovered |
| `AR-01…AR-08` | 3.60 m wall height, 2.20 m doors, 2.00 m windows, 1.00 m parapet, structural and MEP out of scope, external areas measured by area | project only | The owner's answers for this villa |

One rule was **rejected**, which matters as much: the historical workbook's 0.75 m bathroom window did not replace
the guide's 0.60 m. One project's site frame is an observation, not a standard.

---

## 4. What it got right

These are checks the engine could not tune itself towards — figures produced by the architect or measured on site.

| Check | Engine | Independent source | Difference |
|---|---:|---:|---:|
| First-floor penthouse area | 69.661 m² | 69.66 m² (architect's schedule) | +0.001% |
| Ground-floor coverage | 495.045 m² | 494.62 m² (architect's schedule) | +0.09% |
| Plot area | 600.16 m² | 600.00 m² (title) | +0.03% |
| Basement door leaves | 8 | 8 (site record) | 0% |
| Master bedroom window, second candidate | 3.00 m² | 3.06 m² (site frame) | −1.91% |
| Component decomposition | 184 rectangles | 135 frozen component areas | 0.000 m² |

Two further things went right that do not fit a table:

- The engine found and fixed **its own** 155 m² defect before any comparison with history took place.
- When a 348% aluminium gap appeared — exactly where an eager validator declares an engine error — it went back
  to the drawing, counted 1,859 and 1,334 drawn paths on the basement and roof plans, found **zero** glazed
  openings there, and classified the difference as scope rather than error.

---

## 5. What it got wrong

All of these were found and fixed inside the work. The pattern is more useful than any single case: the failures
are nearly always *a rule applied one level too confidently*, not arithmetic.

| ID | Defect | Cause | Fix | Lesson |
|---|---|---|---|---|
| DEF-01 | Rooms leaked through doorways — one "room" of 425 m², another of 560 m² | A door is a hole in a wall, and the flood fill read the hole as an absence of wall | Virtual closures: a gap up to 3.00 m is spanned for bounding a room and is never wall material | Topology and material are two different questions about the same line |
| DEF-02 | Tile preparation under-measured by 155 m² | The wall-face count required a wall line to span a whole grid cell, so fragmented walls were missed | Both trades take the same host: room perimeter less its own openings. Difference now 0.000 | When two measurements of the same physical face disagree, one is wrong — do not write a rule to excuse the gap |
| DEF-03 | 159 "openings" that were mostly junctions | Every gap in a wall line was read as an opening | An opening is a gap with a door or window symbol in it: 37 | Evidence, not absence |
| DEF-04 | Reported that window widths were unmeasurable, and proposed using the guide's widths | Dynamic blocks do not expand in the decode, and the path coordinates first used were in a different space from the text | The plot draws each glazed opening as a white rectangle through the wall — all 7 widths were measurable | "Not available" was a statement about my method, not about the drawing. It nearly let a standard replace a measurement |
| DEF-05 | The PDF→DWG transform returned nonsense (scale 0.012, rotation −52°) | A similarity transform with positive scale cannot express a reflection; PDF y runs down, drawing y runs up | Negate page y before fitting. Residual 0.021 m on withheld witnesses | |
| DEF-06 | Multi-word room labels invisible ("BED ROOM", "M.BED ROOM") | Words were grouped on a shared y; the plans are rotated 90°, so they share an x | Group on either axis | |
| DEF-07 | `CLOSE_AGREEMENT` used too generously — 3.8%, 5.9% and 9.1% reported as close agreement | A judgement where a threshold belonged | 2% is now arithmetic. Three of six comparisons left the class and each had to name its cause | Generosity in a validator is a defect, not a courtesy |
| DEF-08 | A floor inferred where none was stated (rows 5–21 read as basement) | The sheet carries one header at the top and nothing marking where the next floor begins | 4 rows of 31 have proof; the other 27 are `FLOOR = UNKNOWN`. `US-22` exists so Urban's own schedules never repeat it | |
| DEF-09 | A commercial basis called a quantity — 950.22 m² carried as "historical waterproofing quantity" | It is `SUM(F5:F24)` feeding `=1.5*F28`, and one of its twenty components is 600.00, the plot area | Recorded as `HISTORICAL_COMMERCIAL_BASIS`; it may not be compared against a measured area at all | |
| DEF-10 | Two tests asserted yesterday's world (no villa present; no workbook opened) | Both were true when written and false afterwards | Rewritten to assert the *rule* rather than the state of one afternoon | |
| DEF-11 | 196.378 m² of stair and unnamed floor area exported as `PORCELAIN_FLOOR` while the workbook used 734.638 m² | One role list answered two different questions: what is enclosed, and what takes porcelain | 33 records moved to `FLOOR_FINISH_UNCLASSIFIED` / `AR-FL-PENDING`, measured and kept, out of the base BOQ | An unsettled finish is a status, not a default material |
| DEF-12 | 135 connected components published as 135 rooms | No entity census; the geometric unit was given a use-based name | A census in every artifact: 135 = 64 non-sliver + 71 wall/sliver, with role counts | A component becomes a room when the drawing names it, not before |
| DEF-13 | Window AR-W-05 used the `LARGE_HALL` category in a 91.06 m² hall, band 35–60 m² | The guide's area band was advisory in code and absolute in principle | Every window carries an authority: a label supports its category; an area only inside the band. AR-W-05 is now `ASK_THE_OWNER` and `AR-AL-PENDING` | A fallback standard used outside its own scope is an assumption wearing a rule's name |
| DEF-14 | Ceiling finish published as plain and final with no ceiling plan | Area and finish were one status | Area stays `FINAL_QUANTITY_AVAILABLE`; the finish is `FINISH_CLASSIFICATION_PENDING` and provisional in the BOQ | Measuring a surface is not deciding what goes on it |

---

## 6. What it still cannot do, and how I would fix each one

| Limit | What breaks | Proposed fix | Size |
|---|---|---|---|
| Only axis-aligned plans | The exact decomposition assumes every wall face is horizontal or vertical. A curved or angled villa produces nothing — not a wrong answer | Keep the exact path for orthogonal plans; add a polygon-clipping path for the rest with the same closure check as the gate. The earlier P7757 work has the harder machinery | large |
| Heights come from the owner, not the drawing | Every wall, door and window height in this villa is an owner input. Without them, no vertical quantity exists | Read the section and elevation sheets: match level marks to floor labels and take the clear height as a measured dimension at rank 1 or 2 instead of rank 3 | large |
| 128.8 m² unnamed | Circulation, shafts and lobbies carry no label, so they are measured exactly and classified as unknown | Infer role from adjacency and shape as a *candidate* only, and put candidates in a review screen for one click each. Never write an inferred name into a quantity | medium |
| Drawing scope ≠ site scope | The drawings show 7 glazed openings; the site record lists 34 objects. Neither is wrong; they measure different things | Publish two registers side by side, kept apart by `US-21`. The site register needs a source Urban controls | medium |
| No ceiling, sanitary or MEP reading | Suspended ceilings, floor tanking and services are out of scope or undrawn | Ask for the ceiling plan and sanitary layout as inputs. Until they exist these stay `SOURCE_REQUIRED`, which is correct behaviour rather than a gap | small |
| No rates, no waste | The BOQ has empty price columns on purpose | A rate library with the same travel rule as the standards: an Urban rate that travels, a project rate that does not, and a date on both | medium |
| Two projects is a small sample | Generalisation unproven; each new villa needs a human to confirm which plan windows are the issued ones | Make the region-isolation score the gate — 1.000 proceeds, anything less asks — then run three more villas blind | medium |
| It runs only where the agent runs it | No upload, no storage, no login, no screen | See section 8 | not started |

---

## 7. What I need from the owner

Eight questions, none previously answered. Each unblocks a quantity or a rule.

1. **Skirting (النعلة) — in scope, and at what height?** 828.493 lm derived from the frozen geometry, split into
   three buckets: 381.535 lm dry named internal (candidates), 97.355 lm stair/landing and 349.603 lm unnamed
   (both blocked until the floor finish is settled). Every line is `DERIVED_NOT_IN_FROZEN_TAKEOFF` and
   provisional. If it is standard Urban scope it becomes a rule.
2. **What finish do the stairs and the unnamed spaces take?** 67.6 m² of stair and landing, 128.8 m² unnamed —
   nearly 200 m² of floor finish, more than a quarter of the internal area.
3. **The external and parking areas — 155.2 m². What material?** Area final, finish unstated under AR-08.
4. **What goes on the roof above the waterproofing?** 474.7 m², membrane measured, finish unstated.
5. **Is wet-room floor tanking standard Urban scope even when it is not drawn?** No detail on any of the three
   plans; 91.7 m² of wet and service floor here. This should end in a travelling rule.
6. **Who supplies the site-scope opening register?** The drawings support 7 windows; the site record listed 34
   objects. Both registers can be published, but the second needs a source Urban controls.
7. **Are there suspended or decorative ceilings?** 931.0 m² is measured as plain ceiling; no ceiling plan supplied.
8. **Waste percentages and rates — are there Urban standards?** The columns exist and are wired with formulas.
   Also: please send the window size guide PDF so the transcribed table can be checked against it.

---

## 8. The web app

Not started, on the owner's instruction. What already exists for it:

- **The data model.** The 265-record export *is* the database schema, `DS-01`-shaped: project, drawing revision,
  floor, room, trade, item, components, calculation, measured quantity, unit, waste, procurement quantity, rate,
  amount, source, rule id, status, approval status.
- **The rule store.** Urban standards, project values and schema rules are separate objects with a travel flag.
- **The audit trail.** Frozen artifacts with digests, plus a validation amendment that changes the record without
  touching the measurement — version history with a reason attached.
- **The review material.** Every quantity decomposes to rectangles a reviewer can check by eye.

What I would build, in order:

1. **Upload and identify** — drop a DWG and a PDF; the app runs decode, units and region isolation. One human
   step: confirm the plan windows when the containment score is below 1.000.
2. **Review the rooms** — the plan with each room's rectangles drawn over it, its area, and one click to name an
   unnamed space or correct a role. Every override recorded as an owner input, never silently merged into the
   measurement.
3. **Answer the blockers** — the open questions as a queue; the engine knows which quantities each answer unblocks.
4. **The BOQ** — the thirteen sheets as screens, same live formulas, same empty price columns until a rate library
   exists.
5. **Approve** — records leave the engine as `DRAFT` and only a person moves them to approved.

What I would not build yet: anything that prices automatically. A rate applied to a quantity nobody has reviewed
is how the historical workbook ended up with `=1100+325+430+150*2.5`, and that cell is the reason `DS-01` exists.

---

## 9. Deliverables and frozen quantities

| File | What it is |
|---|---|
| `ALRASHED_DETAILED_QUANTITY_TAKEOFF.xlsx` | 13 Arabic right-to-left sheets: ملخص الحصر، حصر المساحات، الأرضيات، كسوة الجدران، النعلة والبروفايل، العازل، الأسقف، الأبواب والشبابيك، المباني، المساح والصبغ، السطح والخارجي، BOQ حسب البند، المصادر والمراجعة |
| `ALRASHED_DETAILED_QUANTITY_EXPORT.json` | 265 draft records, one per component per trade, `DS-01` schema, with the component census, the floor-finish split and the aluminium split |
| `ALRASHED_QUANTITY_RECONCILIATION.json` | Machine-readable agreement table: JSON vs workbook vs BOQ vs frozen, line by line |
| `ALRASHED_VALIDATION_AMENDMENT_01.json` | The corrected validation record and the seven rule decisions |
| `FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json` | The frozen measurement — untouched by any of the above |

### Frozen quantities (Al Rashed villa)

| Quantity | m² | Quantity | m² |
|---|---:|---|---:|
| Internal floor | 734.638 | Internal plaster | 1,493.945 |
| Wet and service floor | 91.668 | Internal paint | 1,061.616 |
| Ceiling | 931.016 | External plaster and paint | 894.859 |
| Wall porcelain, net | 432.329 | Roof and waterproofing | 474.693 |
| Tile preparation | 432.329 | Parapet blockwork | 101.760 |
| Blockwork 150 mm | 190.289 | Parapet plaster / paint, each | 203.520 |
| Blockwork 200 mm | 963.188 | Aluminium, drawing scope | 14.330 |
| External and parking | 155.206 | Door openings (35 doors) | 73.280 |

Every figure traces to the Al Rashed permit drawings of 16-11-2025 or to an owner decision. No historical price,
quantity or formula entered any quantity in this report.
