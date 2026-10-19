# Questions for the owner (at most 5 open; answer under "Answer:")

Lead 2026-10-19 04:10: two new questions Q-18 (dome size basis) and Q-19 (may engine conventions release concrete when the drawing prints nothing); eight are open (Q-12 to Q-19): the list is long because each one stops an assumption. Q-12 now has the T-037 hand calculation (see its note). Lead 2026-10-19 02:20: three new questions Q-15 (development project 2 plans file), Q-16 (unlabelled beam span), Q-17 (typed drawing sizes in the concrete score); with Q-12, Q-13 and Q-14 six are open: the list is long because each one stops an assumption. Lead 2026-10-19 00:15: no new question; Q-12 (concrete verdicts) and Q-13 (toilet lines vs chair) open. Window / aluminium door m2 is covered by UP-OPEN-SCHED-001 and UP-DOOR-AREA-001, so it became task T-040, not a question. Lead 2026-10-18 20:05 (owner session): Q-06, Q-07, Q-09 answered by the owner (see Answered); no question open. Lead 2026-10-18 21:25: Q-10 (development project 2 DWG) answered; Q-11 answered (owner uploads the Alsenan DXFs); no question open. Lead 2026-10-18 15:40: no new question; Q-06 and Q-07 still open (no owner answer yet). The T-019 wall-length basis finding is settled by UP-WALL-GEOM-001 (masonry run = centreline, owner-approved), so it became task T-027, not a question. Lead adds questions an agent cannot decide from drawings, rules or evidence. Answered questions move to the bottom.
Decisions still queued behind these (from the master study `14_OWNER_DECISIONS_QUEUE.csv`): D-17 review-space wet / dry,
WP-KITCHEN membrane scope, WP-JOINT details, WIN-REVEAL finish, STUB-LIMIT, MEAS-STD, ROOF-FIN, BLIND-AUTH.

## No assumptions (owner, 2026-10-18; applies to every agent)

Every measurement, count, quantity or classification follows the Urban rules the owner has set: the rule registry
(`rules/`, 1.5.0), the knowledge registry, `research/urban_m9_n10/OWNER_DECISIONS_REGISTER.md` and every "Answered"
entry in OWNER_QUESTIONS.md. Nothing else.
- Do not assume, guess, infer a convention, borrow a value from the freelancer's workbook, or pick a default "for now".
- If an Urban rule covers the case, cite its id in the task, the code comment or the handoff.
- If no rule covers it, or the rule is unclear, ambiguous or conflicts with another: stop that part and ask the owner
  at once (worker: set BLOCKED-OWNER with the question; verifier: UNRESOLVED; lead: an owner question and a line under
  "QUESTIONS FOR OWNER" in the report to the owner's main chat). Work that needs no such rule may go on.
- A quantity that depends on an unanswered rule stays HELD or UNSUPPORTED. It never becomes a number and never 0.
- A question is one sentence with the options and what it blocks. Such a question is always asked, even when five
  are already open; the lead tells the owner when the list is long.

## Owner instructions (via the owner's main Claude Code chat, 2026-10-18)

The owner's main contact for the whole team is the owner's Claude Code chat (the session that built N10 and the private-data
repository `urban-boq-private-data`). It can fix what the board cannot (code, repository access, the private data, scheduled-task
settings). Instructions:
1. **DWF files are ready on Drive.** Folder "Alsenan chalet project": the architectural DWF (title ends `2026-05-06T113026.059.dwf`, 2.65 MB,
   same bytes as the registered DWF `7d440a57...`). The owner sends two more DWFs later; they go into the same folder. Every agent may read
   Drive DWF/DWG/DXF/PDF files there (read-only, downloads up to 10 MB; larger files as .zip). Nothing blocks on DWF access now: if a
   task needed a DWF and was BLOCKED-DATA, move it to TODO. The DWF is a viewing format: use it to cross-check the DXF/DWG reading, never
   as the measured source.
2. **Reports and questions.** Lead: end every run with a short report (what merged, what is blocked, the one thing you need) and write each
   question into this file as usual. The owner answers in the main chat, and the answer is written under "Answer:" here.
3. **If you cannot do something** (repository not attachable, Drive file unreadable, a setting only the owner can change), say exactly what
   in the first line of your report; the main chat will fix it.

## How to write a question for the owner (owner, 2026-10-18; every agent follows this)

The owner must understand the question without opening the code. Write it in plain words, like talking to a site
engineer, and always give the real case from the drawing so he can check it by hand:

1. **What we found** (1-2 short sentences, no code words, no file paths, no rule ids in the sentence).
2. **The real example**: project folder and file title on Drive, sheet / floor, room or element name as written on
   the drawing, and the numbers (size, area, count) with the simple sum, e.g. "1.20 x 2.10 = 2.52 m2".
3. **How to check it yourself**: what to open and what to measure or count (e.g. "open the ground floor plan, the
   bathroom next to the kitchen, measure the door gap wall to wall").
4. **The choices**: (a) / (b) / (c), each one short sentence saying what the BOQ will then show.
5. **What waits on the answer**: the trade and the task in plain words (task id in brackets at the end).

Never send a question without a real example; if the agent has none, it finds one first. No client names or personal
data (the Drive folder title of a client project is a client name: say "development project 2" instead).

Example (Q-06 written this way):
"We found 3 small spaces with only a hand-wash basin (no WC, no shower). The plan does not say if they are wet or dry.
Real example: Alsenan, architectural plan, 3 basin-only spaces, 9.35 m2 together. Check: open the plan, find the
spaces with a basin and nothing else, add their areas. Choices: (a) wet: porcelain floor and walls full height,
waterproofing, marble threshold; (b) dry: plaster, paint, skirting, normal floor tiles; (c) you decide per space.
Waits on: floor, wall and waterproofing quantities of these spaces (T-030)."

## Open

### Q-12 Concrete: three places where the engine and the freelancer differ (verifier 2026-10-18 22:58; T-001b)

What we found: the first real concrete comparison (Alsenan) agrees on footings but the engine is well below the
freelancer on the pool and on stairs + domes. The verifier could not yet prove from the drawing who is right.
Real example (Drive "Alsenan chalet project", structural file "ST7757 dxf.dxf"):
- Pool: engine walls 1.98 + floor 1.51 = 3.50 m3; freelancer 12.35 m3 (8.85 m3 more).
- Stairs + domes: engine ground-floor stair 2.79 + two short stairs 0.90 + 0.95 + two domes 3.69 + 3.69 = 12.01 m3;
  freelancer 21.83 m3 = a basement sub-stair 13.70 + the main stair 8.13 (9.83 m3 more).
- Footings: engine 77.27 m3 vs freelancer 77.63 m3 only if the 7.22 m3 strip drawn at foundation level along the plot
  edge is the freelancer's "perimeter" footing; without it the engine has 70.05 m3.
How to check it yourself: open the structural drawing, the pool section (wall thickness, depth, floor thickness) and
the stair sections; check whether the chalet has a basement with its own stair, and whether the strip along the plot
edge at foundation level is a footing under the boundary wall.
Choices: (a) the drawing shows the bigger pool / basement stair: the engine is missing concrete and gets a fix task;
(b) the freelancer added items not on the drawing: the engine stays, the difference is the freelancer's;
(c) the edge strip is / is not the perimeter footing: it stays in / leaves the footing line.
Waits on: the concrete scoreboard verdicts for pool, stairs and footings (T-001b).
Lead 2026-10-19 04:10 (T-037 hand calculation, research/agents_t037/ on its branch): the drawing settles part of this.
Pool: the pool detail prints a 0.40 m floor (the engine used 0.25) and the pool is D-shaped (the engine kept only the
straight half): the engine is short, fix tasks T-048 / T-049; the pool depth is printed only as "as per architectural",
so the pool line stays open until the architectural PDF can be read. Stairs + domes: there is no basement on any sheet;
the freelancer's "basement" 13.70 m3 = entrance stair 1.41 + stair 2 5.51 + three domes 6.78; only two structural domes
are drawn (the third is a dashed circle on the architectural plan); the stair waist and risers are not printed (see
Q-19). Edge strip: it is the boundary-wall beam row "20x60" of the schedule on a closed band 91.94 m long; the engine
kept 60.17 m of it (two edges lost, task T-050), the freelancer 71.7 m. Choice (c) above is still yours.

Answer:

### Q-13 A toilet drawn as loose lines, or a chair against the wall? (worker 1 2026-10-18 23:40; T-010)

What we found: when a room has no name, the engine calls it a bathroom if it sees a wash basin plus a toilet drawn as
loose lines (an oval bowl touching a box on the wall). A chair of the same size with its back on the wall looks exactly
the same in the lines, so a dry room (a lobby with a basin and a chair) would get bathroom tiles and waterproofing,
with a review flag. Today the rule says a drawn toilet shape counts as proof; no rule says how to tell it from a chair.
Real example: the Alsenan plan is not affected (its toilets are not drawn as loose lines; checked in Phase 2B-8), so
the example is our test drawing: a 3.40 x 3.00 = 10.20 m2 lobby with a basin and, on the furniture layer, either a
toilet (bowl 0.40 x 0.60 touching a 0.50 x 0.20 box on the wall) or a chair (seat 0.40 x 0.55 touching a 0.45 x 0.15
back on the wall). Both give the lobby 10.20 m2 wet floor tile, 26.94 m2 wall tile and 10.20 m2 waterproofing.
How to check it yourself: on any villa plan you have, look at how the toilets are drawn: a named toilet block, loose
lines on a plumbing / sanitary layer, or loose lines on the furniture layer with no drain or soil-pipe mark.
Choices: (a) keep as now: a toilet-shaped outline next to a basin makes the room a bathroom, flagged for a person to
check; (b) loose lines count as a toilet only on a plumbing / sanitary layer or with a drain or soil-pipe mark next to
it; otherwise the room stays "to be checked" with no wet and no dry quantity (a real toilet drawn on the furniture
layer will also wait for a person); (c) you give a minimum box depth for a toilet cistern (for example 0.18 m): a
thinner back is a chair.
Waits on: wet or dry finishes and waterproofing of unnamed rooms with a toilet drawn as loose lines (T-010).

Answer:

### Q-14 Wall heights for internal plaster and paint (worker 2026-10-19 00:34; T-035)

What we found: the drawings give the finished floor levels but never the slab thickness, the floor finish build-up
(screed + tiles) or the false-ceiling depth, so the engine cannot work out how high the plaster and paint go.
Real example: Alsenan, ground floor, the open room "dining + living / saloon + pantry + reception": its floor is at
+1.00 and the first floor at +5.50, so 5.50 - 1.00 = 4.50 m between finished floors; plaster height = 4.50 - the
first floor's build-up - the slab thickness, and neither number is written on any sheet (architectural plans,
elevations, sections A-A and B-B, structural sections A-A to D-D).
How to check it yourself: open the structural drawing, sections A-A to D-D, and the architectural sections A-A and
B-B; look for a slab thickness (e.g. "20 cm") or the floor layers; you will find only levels and bar marks.
Choices: (a) you give, per floor (ground, first, second), the slab thickness, the floor build-up and the false-ceiling
depth from the designer, and the engine computes the heights; (b) you give the plaster height and the paint height
per floor directly; (c) Alsenan plaster and paint stay held (shown, not scored) until drawings print them.
Waits on: internal plaster (25 room lines) and internal paint (11 room lines) for Alsenan (T-035).

Answer:

### Q-15 Development project 2: which file holds the apartment's floor plans? (lead 2026-10-19 02:20; T-033)

What we found: the DWG you uploaded for development project 2 (name ends in -STR.dwg) is a structural drawing
(column jacketing, schedules) with the architecture only as a faint background, and converting it here loses more than
half of its contents. The 2-page architectural PDF in the same folder says it was printed from a different DWG.
Real example: Drive "Urban BOQ private data", development project 2 folder: the -STR.dwg has 48,576 drawing items, the
conversion keeps 21,072 (57 % lost); it has no English room names and no title for the upper floors; the PDF's print
stamp names another file.
How to check it yourself: open the PDF, look at the small print stamp in a corner (the DWG file name); see whether you
have that DWG.
Choices: (a) you upload that architectural DWG (or a DXF export of it, AutoCAD SAVEAS DXF 2018) to the same folder;
(b) only the -STR.dwg exists: the agents read the apartment from the PDF with the plan reader (T-003, moved earlier);
(c) you export the -STR.dwg to DXF from AutoCAD yourself and upload it.
Waits on: tiles, plaster, paint, floor area, wet / dry, doors and windows for development project 2 (T-033, T-003).

Answer:

### Q-16 A beam span with no label, in line with a labelled beam (lead 2026-10-19 02:20; T-036)

What we found: on the slab plans some short beam spans carry no label but sit in a straight line with a labelled beam
on the other side of a column or beam. No rule says which size to give them, so the engine holds them (no number).
Real example: Alsenan, structural file "ST7757 dxf.dxf", 11 such spans (ground floor 5, first floor 2, second floor 4),
4.67 - 6.00 m3 together, held. One of them: ground floor slab plan, a 3.0 m span drawn 0.40 m wide next to a labelled
beam 0.75 m deep: if it took the neighbour's size, 3.0 x 0.40 x 0.75 = 0.90 m3.
How to check it yourself: open the ground floor slab plan, find a beam line without a mark between two columns, and
see whether the beam continuing past the column has a mark.
Choices: (a) hold it until the designer labels it (as today; shown as "needs designer"); (b) give it the labelled
neighbour's size, marked "size taken from neighbour beam"; (c) take the neighbour's size only when the drawn width is
the same, else hold.
Waits on: 11 beam lines of the concrete beam total (T-036 follow-ups).

Answer:

### Q-17 May the concrete score use sizes a person typed in from the drawings? (lead 2026-10-19 02:20; T-036)

What we found: most held concrete (167 of 205 lines) is held only because storey heights, neck levels, the blinding
thickness and the typical ground-beam sizes are not read by the engine itself. A file typed by a person from the printed
drawings earlier holds them, and with it the engine releases columns, necks, ground beams and blinding. Most of its
values are printed on the drawing, but at least one is not (the deeper founding level, 2.0 m).
Real example: Alsenan, structural file "ST7757 dxf.dxf": with the typed file, columns 61 lines 35.29 m3, necks 10.86 m3,
ground beams 27.37 m3 and blinding 22.16 m3 (0.10 m thick, read from the general notes) are released; without it
they are held.
How to check it yourself: open the structural general notes (blinding thickness) and the foundation sections (founding
level); see which of these numbers are printed.
Choices: (a) yes, but only values a check (task T-044) finds printed on the drawing; any line that needs an unprinted
value stays held; (b) no: the score shows only what the engine reads by itself, the typed file is for diagnosis only;
(c) yes for every value in the typed file (you confirm them, including the 2.0 m founding level).
Waits on: the concrete score for columns, necks, ground beams and blinding (T-044, T-036).

Answer:

### Q-18 Dome sizes: are the printed 442 and 190 measured to the outside or the inside of the shell? (lead 2026-10-19 04:10; T-037, T-049)

What we found: the dome detail prints the dome width, its rise and the shell thickness, but not whether the width and
rise are taken on the outer or the inner surface, and that changes the concrete. No Urban rule says which.
Real example: Alsenan, structural drawing (Drive "Alsenan chalet project", "ST7757 dxf.dxf" and the ST7757 PDF), dome
detail: 442 wide, 190 rise, 10 cm shell. Outer surface basis: about 2.54 m3 per dome; inner surface basis: about
2.80 m3 per dome (two domes drawn). Today the engine uses its own rise and shell guesses: 3.69 m3 per dome.
How to check it yourself: open the dome detail on the structural drawing and see where the 442 and 190 dimension
lines end: on the outer line of the shell or the inner line.
Choices: (a) outer surface: 2 x 2.54 m3; (b) inner surface: 2 x 2.80 m3; (c) hold the domes until the designer
confirms (shown, not scored).
Waits on: the dome part of the concrete stairs + domes line (T-049).

Answer:

### Q-19 When the drawing prints no size, may the engine use its own "usual villa" sizes for concrete? (lead 2026-10-19 04:10; T-037)

What we found: for pools, domes and stairs the engine fills sizes the drawing does not print from its own list of usual
villa sizes (for example pool floors 20 - 30 cm, dome shells 10 - 15 cm, stair waists 15 - 20 cm) and releases the
concrete as a number. These sizes are not an Urban rule you approved, so under "no assumptions" they should not make a
number without your say.
Real example: Alsenan, structural drawing "ST7757 dxf.dxf": the ground-floor stair is released at 2.79 m3 with a waist
the drawing never prints; the pool floor was taken as 0.25 m although the pool detail prints 0.40 m; the domes at
3.69 m3 each from a guessed rise.
How to check it yourself: open the stair on the ground-floor slab plan and look for a stair section or a waist
thickness note; you will find tread lines but no section.
Choices: (a) a printed size always wins; where nothing is printed the line is held (shown, not scored) until the
designer gives it; (b) a printed size wins; where nothing is printed the engine may use its usual size, marked
"usual size, not on drawing", and the line counts in the score; (c) as (b) but the line is shown and not scored.
Waits on: pool, dome and stair concrete lines on every villa (T-049, T-037 follow-ups).

Answer:

## Answered

### Q-11 AutoCAD DXF files for the scoreboard (T-001b; added by the worker 2026-10-18 as Q-10, renumbered by the lead)
The Drive folder "Alsenan chalet project" has the DWGs but not the two DXF files the engine was always run on, and P7757.dwg cannot be
converted here: please (a) upload your existing AutoCAD exports P7757.dxf (about 17 MB) and ST7757.dxf (about 3 MB) to that folder,
(b) re-export both from AutoCAD (SAVEAS DXF 2018) and upload them, or (c) let agents score only the structural trades from a
LibreDWG conversion of ST7757.dwg (13 of 4473 entities lost) and leave the architectural rows unmeasured? Blocks T-001b (the first
real scoreboard). Lead: the same applies to development project 2 (its DWG has not been converted yet), so the DXF exports of its architectural DWG (and of the plans file its PDF title block names, if different) would avoid the same block there.
Answer (owner, 2026-10-18): (a) for Alsenan: the owner uploads the Alsenan DXF exports to the Drive folder "Alsenan chalet project". Development project 2: no DXF promised yet; a worker first tries its DWG with the pinned LibreDWG plus a read-only CAD audit, and the lead asks again only if that conversion is lossy.


### Q-10 CAD file for development project 2, the finishing-only apartment (added 2026-10-18)
Its architectural plan is only a PDF with no readable text (probably a scan): (a) you have the DWG / DXF and will add
it to the same Drive folder, or (b) there is none, so the agents read the PDF with the plan reader (T-003) and score
finishes from that. Blocks using the apartment for CAD-measured finishes (M2 / M3); (b) moves T-003 earlier.
Answer (owner, 2026-10-18): (a). The DWG is in the same Drive folder (file name ends in -STR.dwg). The first agent that opens it confirms with a read-only CAD audit (urban-cad-audit skill) that it holds the architectural floor plans; if it holds only structure, the lead re-asks.


### Q-09 Measurement basis for every BOQ line (MEAS-STD; added 2026-10-18)
Should the engine's quantities be (a) net geometric quantities from the drawing, with waste and rounding shown in a
separate column, (b) quantities with waste already included as the freelancer does, or (c) all three side by side
(measured, with waste, order quantity)? Blocks how the verifier classes freelancer differences (RULE_DIFFERENCE vs
FREELANCER_RIGHT) on every trade, from M2 onward.
Answer (owner, 2026-10-18): (c). Every BOQ line shows the measured quantity, waste in its own column, and the total (measured + waste). Task T-032.


### Q-06 Hand-wash spaces: wet or dry? (D-17; added 2026-10-18)
The three basin-only hand-wash spaces on Alsenan (9.35 m2 in all; the drawing does not establish their type) are:
(a) wet: porcelain floor, full-height wall porcelain, waterproofing, marble threshold; (b) dry: plaster, paint, skirting,
ordinary floor porcelain; or (c) answer per space. Blocks their floor, wall and waterproofing lines (Gate 1, wet vs dry).
Answer (owner, 2026-10-18): (a) wet. Basin-only hand-wash spaces are wet areas: porcelain floor, full-height wall porcelain, waterproofing, marble threshold. Task T-030.


### Q-07 Facade height convention (OQ-08 in research/urban_m9_n10/OWNER_DECISIONS_REGISTER.md; added 2026-10-18)
Is each floor's facade measured (a) F.F.L. to the next F.F.L. (engine default today), (b) slab top to slab top, or
(c) a stated height per floor? Blocks the external facade plaster / paint area (Gate 2, after section binding T-013).
Answer (owner, 2026-10-18): (b) slab top to slab top. Task T-031 (after T-013 section binding).


### Q-08 Other villas for the engine (T-012; answered 2026-10-18)
To make the engine right on every villa, the agents need 2-3 more villas (AutoCAD DWG/DXF + PDF). Where can they get
them: (a) you create the private repository msalfahad/urban-boq-private-data and upload them under dev_villas/<name>/
(agents can read it; it never goes into the public repo), (b) a Google Drive folder you name, or (c) not now (synthetic
villas only, T-019)? Blocks T-012, T-001b and every real-plan check beyond Alsenan.
Answer: (a). The owner created the private repository msalfahad/urban-boq-private-data and uploaded files to it so that every
agent reads them directly; all four agent prompts (lead, worker, verifier, scout) now attach it read-only next to
Urban-Project-AI (2026-10-18). Folder layout as the owner uploaded it; the lead lists it on its next run and moves T-001b
(and any other BLOCKED-DATA task whose files are there) to TODO.

### Q-01 Plan reader: may Claude look at the drawings? (answered 2026-10-18)
Answer: Yes, always. The visual layer of PLAN_READER.md is on for every project drawing.

### Q-02 Working accuracy targets (answered 2026-10-18)
Answer: The main target is to get everything correct. 95 %+ against the freelancer is a floor, not the goal: the engine
may become more accurate than the freelancer. So a difference from the freelancer is not automatically an engine error;
the verifier decides from the drawing who is right (MISSION.md "Who is right").

### Q-03 Waterproofing upturn (answered 2026-10-18)
Answer: 0.20 m. Already the current rule (knowledge 1.4.0 rules[41], UP-WP-003; 0.15 m is superseded, rules[47]). No change.

### Q-04 Door minimum, D-16 (answered 2026-10-18)
Answer: The minimum is the door opening: ordinary 1.00 m opening = 1.10 m wall to wall. These are minimums: when the plan
is drawn wider, the drawn size is used. The main door is measured as drawn. Matches the registry 1.1.0 reading
"wall opening = nominal + 0.10 m" (owner_questions[4], rules[13]); by the same rule a bathroom 0.90 m opening = 1.00 m
wall to wall (owner confirmed 2026-10-18, also "unless the measurements say more": drawn size when wider). Recorded
as a new knowledge version (task T-011).

### Q-05 Second villa and independent QS (answered 2026-10-18)
Answer: Yes. Other villas exist as AutoCAD and PDF, but without full concrete and rebar drawings. Use them as development
villas for architectural trades, the plan reader and silent-omission checks (Gates 1, 2, 4); not for concrete / rebar,
and not as blind proof until an independent QS measures one (task T-012).
