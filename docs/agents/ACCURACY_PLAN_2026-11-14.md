# Reassessment: what makes the BOQ inaccurate and the structural changes that fix it (owner ask 2026-11-14)

Evidence: Urban vs freelancer table of 2026-11-13; the blank-lines map; the held census (144 concrete lines: 103 designer
conflicts, 34 unprinted values, 7 measurable); the parallel run of the same engine; the two QS-office samples.

## 1. Diagnosis: three root causes, none of them measurement error

Where the engine and the freelancer both measure the same thing, they agree within 5 % (slabs, beams, plaster, wall tiles,
floor tiles, roof upturn). The inaccuracy is elsewhere:

1. **Coverage, not precision.** 1,350 blank + 1,228 held lines out of 4,348. Every big gap in the table (blockwork -63 %,
   ground beams -40 %, columns -31 %, render -42 %, paint -44 %) is lines with no figure, not wrong figures.
2. **The engine reasons per piece from plan geometry alone.** Heights, sections, levels and classifications live in
   schedules, sections, elevations and notes, which the engine reads badly or not at all. So every member whose height
   or section is not on the plan becomes a hold, and 76 villa-specific patch modules were written to restate them one by
   one. That is why the second villa is nowhere: the knowledge is in code, not in data.
3. **No single source per object.** Openings feed windows, doors, lintels, reveals, deductions, edges and WP transitions
   through seven separate families with seven separate holds. Rooms feed ten finish families the same way. One missing
   height stops seven lines.

## 2. The structural changes, ranked by what they close

| # | Change | What it closes | Effort |
|---|---|---|---|
| A | **Project inputs sheet** as the first object of every project: storey table (FFL, slab thickness, beam depth default, ceiling drop, tile height, plinth), grades, wastage %, scope switches (foundation WP yes/no, fence yes/no). Every height in the engine derives from it; the owner or the client fills it in 10 minutes, as the QS office does. | about 40 % of today's holds: plaster, paint, tiles, blockwork heights, columns, necks, formwork, annex, drops | 2 days: one table + one rule that reads it; the villa-specific height patches die |
| B | **Schedule-first structure**: read the column / footing / beam / GB schedules as tables (text layer of the structural PDF or DXF TEXT), bind marks to plan symbols by proximity, quantity = count x B x D x H. The plan supplies count and length only. Outline-vs-schedule conflicts become a one-page list for the designer; the BOQ is complete the same day. | the 80 blank + 114 held concrete lines; formwork follows by face ratios | 3 days; the T-075 schedule text rows and the D-66 list already exist |
| C | **Wall-band model for masonry**: centreline length per thickness per floor x (storey - slab - beam) - opening table. Thickness and material from layer / hatch; unknown material = owner default and flagged. The parallel run did this in one pass and landed 13 % under the freelancer with no holds. | blockwork, blocks, mortar, glue, plaster backing: 117 lines | 2 days |
| D | **One opening table** (id, floor, type, W, H, wall t, sill, head, source MEASURED / SCHEDULE / DEFAULT) built once from plan symbols + elevation outlines + schedule text, completed with defaults, and consumed by every family. | windows, doors, lintels, reveals, thresholds, shutters, paint edges, WP transitions, all deductions: 60 lines and the W02-type questions become one row each | 2 days; the T-238 census is 80 % of it |
| E | **One room table** (id, name, floor, zone, wet / dry, area, perimeter, doors, windows, ceiling type, heights from A). Every polygon gets a room and a type; "unallocated" is not allowed (default DRY, flagged). | floors, skirting, tiles, plaster, paint, ceilings, WP floor / upturn / penetrations; the 121 m2 unallocated of the parallel run | 2 days; the engine already has the polygons |
| F | **Two methods + a band instead of a hold.** Each trade is computed two ways (concrete by schedule and by outline; blockwork by band and by room perimeters; plaster by room and by band both faces). Agree within 5 % = released; disagree = flagged with both figures. Plus the plausibility bands per m2 of floor (Key quantities sheet). | replaces "hold until the designer answers" as the default behaviour | 1 day of rules once A-E exist |
| G | **Rebar by element ratio**, not one global number: footings 80-100, GB 100-130, columns 150-200, beams 120-160, slabs 90-110 kg/m3 on the per-element concrete; then a BBS text reader for the structural PDF tables (marks, dia, count, length) as the convergence check. | a defensible tonnage now; a real takeoff later without drawing-by-drawing bar tracing | ratio 1 hour; BBS reader 3 days |
| H | **Regression set**: Alsenan + the training villa + the two QS samples as fixed references. Every rule change runs against all; a change that moves a reference trade more than its band fails. This is what turns one villa into a system. | generalisation; the only way the second villa works first time | 2 days once A-E exist |

## 3. Tricks and loopholes that are legitimate

- **Harvest the dimension strings.** DXF DIMENSION and TEXT entities carry nearly every height, level and section the
  holds are waiting for. Bind each to the nearest member automatically (the arched-opening census did this by hand for
  27 windows). One harvester closes hundreds of "not printed on the plan" holds.
- **Layer and hatch names classify walls and finishes** (RC vs block, 15 vs 20, tile vs paint). Use them as the primary
  classification with a default when absent, instead of holding.
- **Elevation frames in the arch DXF** give window and door heights; read the outline chains once, feed the opening table.
- **Block / insert names** give sanitary fixtures, doors, windows and drains as counts without geometry (the drain recount
  in the parallel run used our own code).
- **A targeted vision second reader**: for the few questions geometry cannot answer (is this a window or two, is this wall
  block or RC), crop the PDF region and ask the model; it answers a cropped yes / no question reliably, a whole-sheet
  takeoff it does not. Keep it to that.
- **Client-side inputs**: send the designer the one-page inputs sheet and the conflict list instead of 80 owner questions.
  Most holds are a 10-minute answer for the person who drew the building.
- **An Urban method of measurement** (two pages): what is gross, what is net, what is deducted, units per trade. Then
  comparisons are like for like and the "rule differences" stop looking like errors to a client.

## 4. What this does to the numbers

Today: 7 trades within 5 %, 9 trades with holes, 4 rule differences. After A-E on Alsenan: every trade has a figure, the
holes close to the band, and the remaining differences are rule differences stated in the method of measurement. The
second villa becomes a data exercise (fill the inputs sheet, run, read the flags), not a code exercise.

## 5. Order (two weeks, agents on A-E in parallel, main chat on the inputs sheet and the method of measurement)

Week 1: A (inputs sheet) + D (opening table) + C (wall band) on Alsenan; B (schedule-first) started.
Week 2: B finished + E (room table) + F (two methods) + G (element ratios); H set up with the training villa.
