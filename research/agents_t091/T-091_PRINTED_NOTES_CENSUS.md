# T-091: census of printed finishing notes, tile sizes and door heights on the Alsenan sheets (NO REPO CODE)

Worker 1, 2026-10-20 08:25 - 09:40 UTC. Reading only: no engine, rule, test, fact file or quantity changed. Development
villa (Alsenan), not an accuracy claim. No image, client name, plot or personal data is committed: every architectural and
sanitary sheet carries the owner's name and the plot in its title block; those fields were read and are NOT copied here.
Rules: drawing-first directive and precedence (MISSION.md), UP-KB-PREC-001, UP-QTY-STATUS-001 (held, never 0), owner Q-04
(door widths), Q-42 (joints), Q-45 (beds and falls), Q-48 A (wet-wall height), Q-55 / Q-56 / Q-57 / Q-59 (open).

Tables: `PRINTED_NOTES.csv` (16 rows: every note found, with location and the exact text) and `LIVING_1F_SPLIT.csv`
(the first-floor living / corridor / landing split, owner Q-56).

## 1. What was read (every sheet, read or not read, with the reason)

| Drive "Alsenan chalet project" title | Page / view | Read | How |
|---|---|---|---|
| Alsenan_Architectural_P7757_Pages_01-02 | p.1 GF + 1F AREA PLAN 1:200; p.2 2F AREA PLAN 1:200 | read | 4672 x 6624 px scan, whole page + area tables |
| Alsenan_Architectural_P7757_Pages_03-04 | p.3 / p.4 | **not read from this file**: the Drive connector closed the connection ("a message from the server was too large", 6 789 743 B, one try); read from the single sheets below | - |
| p7757_arch_sheet03.pdf | p.3 GROUND FLOOR PLAN 1:100 | read | whole page + three full-resolution quarters (west rooms, east wet rooms / pool, reception / saloon) |
| p7757_arch_sheet04.pdf | p.4 1st.FLOOR PLAN 1:100 | read | whole page + full-resolution crops (living / void / stair, corridor / main stair) |
| Alsenan_Architectural_P7757_Pages_05-06 | p.5 2nd.FLOOR PLAN 1:100; p.6 SOUTH EAST ELEVATION 1:100 | read | whole page |
| Alsenan_Architectural_P7757_Pages_07-08 | p.7 SOUTH WEST ELEVATION; p.8 NORTH WEST ELEVATION | read | whole page |
| Alsenan_Architectural_P7757_Pages_09-10 | p.9 / p.10 | **not read from this file** (6 371 489 B, over the connector limit seen by T-063); read from the single sheets | - |
| p7757_arch_sheet09.pdf | p.9 NORTH EAST ELEVATION 1:100 | read | whole page |
| p7757_arch_sheet10.pdf | p.10 SECTION A-A 1:100 | read | whole page |
| Alsenan_Architectural_P7757_Pages_11-12 | p.11 SECTION B-B 1:100; p.12 FENCE PLAN / ELEVATION / SECTION 1:100 | read | whole page |
| P7757_DXF_COMPRESSED.zip / P7757.dxf (sha256 ab54dd55...31cc4 = SOURCE_MANIFEST) | model space and every block definition | read | all 276 TEXT / MTEXT / ATTRIB (blocks exploded, Arabic SHX decoded with the repository's shx_arabic decoder: 121 DECODED, 155 Latin), all 566 texts inside block definitions, dimension text overrides (0), all 7 hatch groups |
| sanitary-7757.pdf (cross-check, 3 pages, vector, no text layer) | GF / 1F / 2F DRAINAGE PLAN 1:100 | read | rendered at 150 dpi |

All 12 architectural pages and the 3 sanitary pages were read; 0 unreadable (two 2-page parts replaced by their single
sheets, as the owner's data note says).

## 2. Result: no Alsenan sheet prints a finishing material, a tile or stone size, a skirting, a wall-tile height, a false ceiling, an expansion joint, a threshold or a door schedule

| Searched for | Architectural PDF (12 pages) | Architectural DXF (842 texts) | Sanitary PDF |
|---|---|---|---|
| tile / stone size (60x60, 120x60, 160x80 ...) | 0 | 0 | 0 |
| floor finish per room (porcelain, ceramic, marble, granite, bartash, parquet) | 0 | 0 | 0 |
| skirting | 0 | 0 | 0 |
| wall-tile height or wall-tile note | 0 | 0 | 0 |
| false / decor ceiling, cornice, cove | 0 | 0 | 0 |
| expansion joint | 0 | 0 | 0 |
| threshold | 0 | 0 | 0 |
| door or window schedule, door type marks | 0 | 0 (door blocks D115 / D120 / D215 / D315 / d220 carry no text) | 0 |
| door height | 1: GF main entrance 2.00 x 2.50 (SE elevation, as T-083) | 0 | 0 |
| any note naming a material | 0 | 0 | 1: manhole (drainage item, N15) |
| other notes | 3 x "تعوية صناعية" (artificial ventilation) on the GF plan | same 3 (DXF spelling تهوية صناعية) | falls, drains, pipes, "not to scale" note (N09 - N16) |

What IS on the sheets: room names (Arabic + English), plan dimensions, level marks, storey chains, area tables (p.1 - 2),
fence sizes (p.12), and graphic hatches without text: a square grid (NET, 317.5 mm on the plot) on the 11 bath / W.C.
floors (GF 6, 1F 4, 2F 1), a different grid (ANGLE) on the GF kitchen, a pattern in the pool, parallel lines on the roofs.
A hatch pitch is a drawing scale, not a tile size: it is recorded as VISUAL and never used as a size.

Rooms with and without a printed finish: **29 labelled interior rooms** (5 master bedrooms, 5 baths, 7 W.C.s, 2 wash
spaces, diwaniya, driver, kitchen, pantry, dining, reception, saloon, living area, laundry, maid room) and the unlabelled
stair halls, 1F corridor and 2F lobby: **0 with a printed finish, 29 + all unlabelled without**. Exterior: court, garden,
pool, 4 roofs: 0 with a printed finish.

## 3. Findings that move a quantity or a question

**F1. Roof falls are printed: SLOPE 1 %, not 0.5 %.** The sanitary drainage plans print "SLOPE 1%" on the first-floor
roof at +9.70 (four arrows, one to each rain-water pipe, p.3), on the annex roof at +4.30 and on the sea-side terrace strips
at +5.50 (p.2). Owner Q-45 gave roofs "0.5 % per metre toward each drain" and asked us to check the drawn slope. Under the
drawing-first precedence a project drawing outranks a generic Urban value on the same subject, so the roof screed falls for
Alsenan are 1 % (the roof bed thickness, and so its mortar, roughly doubles against 0.5 %). The roof bed is still HELD
(Q-41 / Q-45: thickness from falls not built yet); no number changes today. For the Lead: tell the owner his 0.5 % does not
match this drawing; no new owner question is needed (precedence settles it) unless he meant 0.5 % as an Urban minimum.

**F2. "Not to scale" is printed.** The sanitary sheets' NOTES box: "THE BUILDER TO WORK WITH STATED DIMENSIONS NOT TO SCALE
DRAWING." Doors drawn on the sections and elevations (B-B: 4 on 1F, 3 on GF, 1 roof door; A-A; NE) carry no dimension, so
their height cannot be taken by scaling. This supports Q-55 option C (hold every door without a printed height).

**F3. The freelancer's stair-marble total counts the court twice.** In his finishes workbook ("الارضيات+العازل+الديكور+الرخام",
sheet "رخام+حوش") the stair-and-landing total H44 = SUM(H13:H41) = 295.44 m2 starts with H13 = 151.80 m2, the court paving.
His cover sheet then lists "ارضيات الحوش" 151.80 m2 AND "اجمالي الدرج والبسطات" 295.44 m2 (marble): the court is in both.
Stairs and landings alone = 295.44 - 151.80 = **143.64 m2**. Inside that, his "درج" rows are step count x width (63 x 1.20
= 75.60; 28 x 1.20 = 33.60; 5 x 2.80 = 14.00), i.e. metres of step, added to m2 of landings: mixed units. Verdict proposal:
**FREELANCER_WRONG on the 151.80 m2 double count** (proof: his own formulas), stair marble not comparable by unit (engine
39.49 m2 of treads + risers + landings, T-086).

**F4. 1F living room split (owner Q-56) from the printed dimensions on p7757_arch_sheet04.pdf** (`LIVING_1F_SPLIT.csv`):

| Piece | Printed | m2 |
|---|---|---|
| Living area, gross | 480 x 520 | 24.96 |
| less the arriving flight of the round stair, inside the 4.80 | 1.15 (= 702 - 587, the chain 587 + 480 = 702 + 365 closes) x 240 | -2.76 |
| **Living, net floor** | | **22.20** (21.96 if the printed "125" is taken: conflict C-1, 125 + 365 = 490 does not close on 480) |
| Corridor strip along the void | 587 x 120 | 7.044 |
| Main dog-leg stair arrival landing (top step to the bedroom wall, +5.50) | (120 + 10 + 120) x 195 | 4.875 |
| Connector under / beside the lift | depths 125 and 240 printed, lengths from CAD only | 4.80 (CAD, not released) |
| Printed pieces | | 34.12 |
| With the CAD connector | | 38.92 |

What this changes: Q-56 says the freelancer's 38.96 m2 is the living room "by its printed size" and that 5.91 m2 of corridor
/ landing is in nobody's line. The printed living room is only **22.20 m2 net (24.96 gross)**; his 38.96 m2 equals living +
corridor strip + landing + connector (38.92 m2, -0.04 m2, -0.1 %). So his "معيشه" row already holds the corridor and the
landing. The engine face (44.87 m2) is 5.95 m2 larger than all hand pieces; the likely part is the 1.47 x 3.05 = 4.48 m2
passage to the middle bedroom (T-086 / T-088), not hand-checked here. No sheet prints a finish at the landing (porcelain or
marble): 0 notes. Verdict proposal: living row **UNRESOLVED** (engine 44.87 vs freelancer 38.96 m2, +5.91 m2, +15.2 %) with
the cause now located; for the Lead: Q-56 option (B) as written ("living porcelain about 38.96, landing 5.91 to marble")
would count the landing twice; the options should read living 22.20 + corridor 7.04 + landing 4.88 + connector (CAD) 4.80.

## 4. Each freelancer finishing row against the printed notes (who-is-right proposals)

Freelancer = finishes workbook (cover "الغلاف", sheets "سيراميك", "رخام+حوش", "ديكور", "العازل") and aluminium workbook.
Engine figures from T-074 / T-086 / T-083 (not re-run: the engine run is outside this run's execution authorization).

| Freelancer row | His value | Printed support | Engine | Verdict proposal |
|---|---|---|---|---|
| Floors "سيراميك" (cover; rooms 337.57 + wet 72.01) | 409.58 m2, material "ceramic", no size | none: no material, no size on any sheet | dry floors released 200.75 m2 (+ open plan HELD), wet 72.12 vs 72.01 m2 (+0.16 %); the engine's "porcelain" item name is an Urban rule label, not printed | m2: as T-086; material and size: **UNRESOLVED** (neither side has a printed source); tile count stays HELD (no size, Q-59) |
| Skirting "نعلات" ceramic | 282.85 lm | none (no skirting note or height) | not built | **UNRESOLVED** |
| Wet walls ceramic at 3.00 m | 433.83 m2 (144.6 lm x 3.00) | no tile height printed | HELD (candidate 403.02 m2) | **RULE_DIFFERENCE** on height (owner Q-48 A: 3.65 / 3.35 m; his 3.00 printed nowhere) |
| Pool floor / walls ceramic | 21.00 / 19.80 m2 | none (pool has a graphic hatch only) | not built | **UNRESOLVED** |
| Court paving "ارضيات الحوش" + skirting | 151.80 m2 + 81.32 lm | none (elevation ground hatch is a symbol) | not built | **UNRESOLVED** |
| Stairs and landings marble | 295.44 m2 (incl. 151.80 court) | none | 39.49 m2 (treads + risers + landings, T-086) | court part **FREELANCER_WRONG** (double count, F3); stairs not comparable (his step rows are lm) |
| Marble skirting / "تواشيح" | 29.87 lm / 96 nr | none | not built | **UNRESOLVED** |
| Decor (gypsum) ceilings + cornices | 337.57 + 72.01 m2; 282.85 + 144.61 lm | none (no ceiling plan, no ceiling line on A-A or B-B) | HELD (Q-57) | **UNRESOLVED** (owner Q-57) |
| Waterproofing wet / roofs | 72.01 m2 + 144.61 lm; 285 m2 + 194 lm | no membrane note; roof falls 1 % printed (F1); one floor drain per wet room (N13) | wet 72.12 m2, roofs 204.11 m2 (T-093) | as T-074 / T-093; no printed note changes them |
| Internal railing | 18.95 lm | railings drawn on A-A and the terraces, no note | not built | **UNRESOLVED** |
| Doors (aluminium) | 12.0 m2 (4 x 1.00 x 2.40 + 1.00 x 2.40) | only the GF main entrance prints a height: 2.00 x 2.50 = 5.00 m2; his 2.40 is printed nowhere; "not to scale" (F2) | 1 door measured (5.00 m2), every other door HELD | **UNRESOLVED** under owner Q-55 (recommend C) |

## 5. Door heights

Printed: 1 (GF main entrance 2.00 x 2.50, SE elevation, T-083). Not printed: every other door: the 27 door elements of the
T-083 table (all interior doors, the court / annex doors, the roof door). They stay HELD on owner Q-55; none is filled with a
typical height, the freelancer's 2.40 or a scaled reading (F2).

## 6. What is missing or uncertain

- No sheet gives a material or a size, so tile counts, skirting, ceilings and pool / court finishes have no drawing source on
  Alsenan: they need the owner (Q-55, Q-57, Q-59) or an architect's finish schedule. A request to the architect for a finish
  schedule and a door schedule would close most of this table.
- C-1: the printed "125" of the arriving round-stair flight does not close on 480 (0.24 m2 between the two net living
  readings); the CAD dimension spans the stringers.
- The 4.80 m2 connector is read from CAD end points, not printed; the engine's extra 5.95 m2 is not hand-traced.
- Not read: the structural set (no finish notes expected there; not in this task) and the DWF.

Files: `PRINTED_NOTES.csv`, `LIVING_1F_SPLIT.csv`, this note. Inputs read in the session scratchpad from Drive, never copied here.
