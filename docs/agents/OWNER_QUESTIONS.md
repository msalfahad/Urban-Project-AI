# Questions for the owner (at most 5 open; answer under "Answer:")

Lead 2026-10-18 20:05 (owner session): Q-06, Q-07, Q-09 answered by the owner (see Answered); no question open. Lead 2026-10-18 21:25: Q-10 (development project 2 DWG) answered; Q-11 answered (owner uploads the Alsenan DXFs); no question open. Lead 2026-10-18 15:40: no new question; Q-06 and Q-07 still open (no owner answer yet). The T-019 wall-length basis finding is settled by UP-WALL-GEOM-001 (masonry run = centreline, owner-approved), so it became task T-027, not a question. Lead adds questions an agent cannot decide from drawings, rules or evidence. Answered questions move to the bottom.
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
