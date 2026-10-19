# Questions for the owner (at most 5 open; answer under "Answer:")

Worker 1 2026-10-19 16:43: one new no-assumptions question from the lost-window trace (T-077): Q-38 (width basis of a curved glass wall in a straight wall opening).
Lead 2026-10-19 16:15: two new no-assumptions questions: Q-35 (wet-room upturn across the door opening: your Q-30 example vs registry UP-WP-DOOR-001) and Q-36 (the new project folder on Drive: open it or not). Q-31 (footing F10) was filed under Answered with no answer: moved back to Open. Open now: 6 (Q-31 to Q-36; all no-assumptions questions, so more than 5).
Worker 1 2026-10-19 15:40: two new no-assumptions questions from the door / window area check (T-040): Q-32 (arched windows: area to the arch top, to the springing, or the true shape) and Q-33 (are windows aluminium by default). Verifier 2026-10-19 15:12: one new no-assumptions question from the footing verdicts (T-065 / T-042): Q-31 (footing F10 drawn 3.25 x 1.40 vs scheduled 2.80 x 1.40). Open now: 1. Worker 2 2026-10-19 14:10: one new no-assumptions question from the foundation split (T-065): Q-28 (boundary-wall band section and its overlap with footings). Open now: 6. Worker 1 2026-10-19 12:39: two new no-assumptions questions from the architectural sheet census (T-063): Q-26 (pool floor flat at 1.15 m or sloped), Q-27 (two or three domes). Open now: 5. Lead 2026-10-19 12:20: one new no-assumptions question Q-23 (renovation BOQ scope and retained-wall finishes, asked before the sealed test as the owner directed). Lead 2026-10-19 12:30: two more no-assumptions questions from the roof trace: Q-24 (roof waterproofing edge and domes), Q-25 (closing a parapet drafting gap). Open now: 3. Lead 2026-10-19 (owner reply): Q-22 answered A (only a pool-named space or block is the pool pump room; plain "PUMP" listed "use not stated"); no question open. Lead 2026-10-19 10:15: the owner answered Q-12, Q-13, Q-14, Q-15, Q-16, Q-17, Q-20 and Q-21 in the main chat (08:51); all eight moved to Answered with their tasks updated (T-065, T-010, T-063 / T-013, T-066, T-043, T-064, T-056, T-042). One new no-assumptions question: Q-22 (which pump room is the pool's). Open now: 1. Lead 2026-10-19 (owner reply): Q-18 answered (c) held and always visible; Q-19 answered for stairs and pools (see Answered); new Q-20 (stair waist and landings). Lead 2026-10-19 04:10: two new questions Q-18 (dome size basis) and Q-19 (may engine conventions release concrete when the drawing prints nothing); eight are open (Q-12 to Q-19): the list is long because each one stops an assumption. Q-12 now has the T-037 hand calculation (see its note). Lead 2026-10-19 02:20: three new questions Q-15 (development project 2 plans file), Q-16 (unlabelled beam span), Q-17 (typed drawing sizes in the concrete score); with Q-12, Q-13 and Q-14 six are open: the list is long because each one stops an assumption. Lead 2026-10-19 00:15: no new question; Q-12 (concrete verdicts) and Q-13 (toilet lines vs chair) open. Window / aluminium door m2 is covered by UP-OPEN-SCHED-001 and UP-DOOR-AREA-001, so it became task T-040, not a question. Lead 2026-10-18 20:05 (owner session): Q-06, Q-07, Q-09 answered by the owner (see Answered); no question open. Lead 2026-10-18 21:25: Q-10 (development project 2 DWG) answered; Q-11 answered (owner uploads the Alsenan DXFs); no question open. Lead 2026-10-18 15:40: no new question; Q-06 and Q-07 still open (no owner answer yet). The T-019 wall-length basis finding is settled by UP-WALL-GEOM-001 (masonry run = centreline, owner-approved), so it became task T-027, not a question. Lead adds questions an agent cannot decide from drawings, rules or evidence. Answered questions move to the bottom.
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

## Owner instruction on merging (via the owner's main chat, 2026-10-19)

The owner changed the permission mode of the scheduled tasks and asked why verified tasks wait for him. Merging is not an
owner job. The verifier merges a verified task into the working branch right away. When the merge conflicts only in the
generated files docs/CODEMAP.md and docs/ROUTING.md, regenerate them with `python3 -I tools/codemap.py build` (never by
hand), check with `codemap.py check` and the freeze check, then merge. Lead: put T-052 back to TODO and stop writing
"NEEDS FIXING by the owner" for merges. If a step is still refused, write the exact refusal text in your report to the
owner's main chat in the same run. The Lead also answers in its next report: why the verified tasks (T-036, T-033, T-029,
T-034, T-011, T-037, T-041, T-044-r2) were not merged earlier, and how many are merged now.

## Owner data note (via the owner's main chat, 2026-10-19 09:25 UTC)

The architectural PDF is now on Drive in the folder "Alsenan chalet project" as six files under 10 MB, 12 sheets in all:
Alsenan_Architectural_P7757_Pages_01-02, 03-04, 05-06, 07-08, 09-10, 11-12 (each about 6 MB). The 37.5 MB original and
TEST_PAGE_01.pdf are not needed. Lead: remove "PDF over the 10 MB limit" from NEEDS FIXING, and give a worker the task of
listing the elevation and section sheets and the levels they print. The DXF for development project 2 is coming from the owner.

Verifier, follow-up (owner's main chat, auditor 2026-10-19 10:30 UTC): at 10:02 you merged one task and left T-047-r2
"verified but map conflict". That is exactly the case the owner's instruction covers: regenerate docs/CODEMAP.md and
docs/ROUTING.md with `python3 -I tools/codemap.py build`, run `codemap.py check` and the freeze check, then merge. Merge
every verified task in one run, in the Lead's order, regenerating the maps after each merge, not one task per hour. If a
step is refused, write the exact refusal text in your handoff.

## Standing owner rule on merging (owner, main chat, 2026-10-19)

Every Lead run gathers all verified work and merges it all: tell the verifier (and do it yourself in the owner session if
a run is refused) to merge every verified task in one run, in the Lead's order, rebuilding docs/CODEMAP.md,
docs/ROUTING.md and docs/RULES_INDEX.md with the tool after each merge. Nothing verified waits for the owner. Merged by
the owner session on 2026-10-19: T-036 58468c6, T-033 a281ff4, T-037 864c28e, T-041 78c57b2, T-044-r2 02a7472,
T-029 980e489, T-034 faad086, T-011 aadced7, T-047-r2 6def656 (working branch head 6def656; maps stale none, freeze 0;
tests: t029, t034, t047, m9_kb and the importer folders of arch_plan.py all pass). Tasks still READY and not yet
verified: T-058, T-061, T-057 (in progress). The verifier checks them next and merges them the same way.

## Owner requirement: membrane purchase table (owner, main chat, 2026-10-19 14:15 UTC)

Owner's words: "3mx3m picture table is an example on how system calculates waterproof membrane measurements in each bathroom and tell me wach bathroom or kitchen or roof or any wet area on how many membrane needed. This way i can quickly see how many i buy." Also: the owner will NOT send a new villa (Q-23 cancelled; the sealed renovation test is withdrawn; drop the renovation-only preparation, keep the general plan reader of gate 4).
The BOQ must therefore include a MEMBRANE TABLE like his 3 m x 3 m picture, one row per waterproofed area (every bathroom, kitchen, roof, balcony, any wet area, each with its room name and floor): net area, upturn, strips of the 1.00 m roll with the 10 cm laps, installed membrane, consumed membrane with the cut edges, cutting waste, rolls if the area were done alone; and at the end the total rolls to buy for the project (from the cutting plan, offcuts reused across areas, shown next to the rolls-if-alone sum). Areas whose wet / dry status or outline is held show HELD with the reason, never 0. The engine already computes these numbers (waterproofing_system.schedule / cutting_plan); the task is the table in the BOQ output and its test on Alsenan and on a synthetic 3 m x 3 m bathroom.

## Owner direction: Alsenan first, then one sealed test on a new villa (owner, main chat, 2026-10-19)

1. Work fully on the Alsenan project now, to make the system right (every trade vs the freelancer, with verified evidence).
   Development project 2 and any new-villa work wait; do not start them. Exception: nothing.
2. Then the owner runs a test. If the Alsenan results are correct, the owner sends one NEW VILLA as a TEST ONLY. It is a
   RENOVATION: the OLD building exists only as a PDF; the NEW design has AutoCAD (DWG/DXF) and PDF. The owner will ask for a
   full engineering analysis from the agents: flooring area (wet: wall and floor; dry), wall plaster, wall paint, blocks
   for inner and outer walls, and the related items, from a study of the old building against the new one.
3. The new villa is a SEALED test: no agent opens, studies or tunes anything to it before the owner sends it; when it comes,
   it is used once, the method version is frozen first (see MISSION.md blind-test rules), and nothing is changed to fit
   its result. Agents prepare only general capabilities, proven on Alsenan and on synthetic fixtures.
4. Lead: plan the general capabilities a renovation needs, as tasks that can be proven WITHOUT the new villa (synthetic
   old/new fixtures, Alsenan): reading an old plan that exists only as a PDF (gate 4 plan reader), classifying each wall
   and space as retained / demolished / new by comparing old and new, flooring and finish areas split wet / dry, plaster,
   paint, inner and outer blockwork. Put the acceptance tests on the board. If a renovation rule is missing, ask the owner
   (no assumptions). Ask the owner before the test which items the renovation BOQ must contain.

## Owner instruction on task size and quality (via the owner's main chat, 2026-10-19)

Give each worker a task that takes at least 50 minutes of real work, not short ones. Quality first, speed second. Lead:
merge small slices that touch the same files or the same quantity into one work package (build, hand-calculated
fixture that is not Alsenan, adversarial cases, validation at the level `impact` says, freeze check, handoff with engine vs
freelancer figures). Do not split a task only to finish faster. Workers: use the whole run to finish the package properly
(read every relevant detail, cross-check against a second drawing, test the edge cases); never end a run early with a
partial handoff just to have something READY; if a task turns out smaller than 50 minutes, take the next related item of the
same topic in the same run. Verifier: check depth, not only gates. The owner prefers one well-proven result per run over
several thin ones.

## Owner data note 2 (via the owner's main chat, 2026-10-19 14:57 UTC)

The four architectural sheets that did not download are now on Drive in "Alsenan chalet project" as single pages of 3.1 to
3.4 MB: p7757_arch_sheet03.pdf (sheet 3), p7757_arch_sheet04.pdf (sheet 4), p7757_arch_sheet09.pdf (sheet 9) and
p7757_arch_sheet10.pdf (sheet 10), byte-identical to the sheets cut from the private repository copy. The sheet numbering
is the 12-sheet set order of the earlier two-page files. Lead: remove "upload pages 3, 4, 9, 10" from NEEDS FIXING and give
the stair, section A-A and founding-level reading (levels, risers, founding depth) to a worker. Use the single sheets,
not the 6 MB two-page files.

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

4. **How to write every owner question (owner, 2026-10-19).** The owner opens the drawing and decides, so each question has,
   in this order: (1) THE PROBLEM in one or two sentences: what the engine cannot decide and the exact number or element
   involved; (2) WHERE TO LOOK: the file, sheet or page, view, layer or area to open, and what to find there; (3) THE
   OPTIONS as A / B / C with the quantity each gives; (4) RECOMMENDATION: the option you advise and why, based on civil
   engineering practice for Kuwait villas, Kuwait Municipality / Ministry of Public Works rules or the project's own
   drawings. Cite a code clause only if you can name it exactly; otherwise write "practice, not a code clause". The
   recommendation is advice: the owner answers "A", "B", "C" or "A, and ..." with comments, and only the owner's words
   become the rule.

## Open

### Q-32 Arched windows: how is their area measured? (worker 1 2026-10-19 15:40; T-040; no-assumptions question)

THE PROBLEM: four Alsenan windows have a round (arched) top, and no Urban rule says whether the area runs to the top of
the arch, stops where the arch starts, or follows the true curve. Their areas stay held until you decide; the freelancer
takes width x full height for all of them (21.15 m2 together).
WHERE TO LOOK: Drive "Alsenan chalet project", "P7757 dxf.dxf" (or the architectural PDF): the NORTH WEST elevation, the
big arched window of the first-floor master bedroom over the pool: printed width "269", "305" from the sill to where the
arch starts, "45" for the arch rise; the same elevation shows the two first-floor sea-side glazed doors "155" wide with
"300" overall and a fan-light arch; the SOUTH EAST elevation shows the second-floor stair window "120" wide, "170" to
where the arch starts and "88" above it.
THE OPTIONS (master-bedroom window, 2.69 m wide):
(A) Rectangle to the top of the arch: 2.69 x (3.05 + 0.45) = 9.42 m2 (the freelancer's way: he wrote 3.15 x 3.00 = 9.45).
(B) Rectangle to where the arch starts plus the true arch piece: 2.69 x 3.05 = 8.20 + 0.82 = 9.03 m2.
(C) Rectangle to where the arch starts only: 2.69 x 3.05 = 8.20 m2, the arch piece listed apart (fan light).
RECOMMENDATION: (A) for the aluminium supply, because a fabricator quotes and cuts arched frames on the enclosing
rectangle (practice, not a code clause); (B) if you want the glass area itself.
WAITS ON: the area of 4 arched windows on Alsenan (freelancer 21.15 m2 of his 116.9 m2 windows) and every arched window or
door on later villas (T-040, the door / window area method).

Answer: A (owner, main chat 2026-10-19 16:40). Arched window area runs to the top of the arch (enclosing rectangle), e.g. the 2.69 m master-bedroom window = 2.69 x (3.05 + 0.45) = 9.42 m2. Applies to every arched window and door; released area follows this rule.

### Q-33 Windows: are they aluminium by default, like outdoor doors? (worker 1 2026-10-19 15:40; T-040; no-assumptions question)

THE PROBLEM: your door rule says a door that leads outdoors is aluminium, but no rule says what a window is made of, and
the Alsenan drawings do not write a window material anywhere. Without it the engine cannot put any window into an
aluminium line; the freelancer puts every window (29 windows, 116.9 m2) into his aluminium sheet.
WHERE TO LOOK: Drive "Alsenan chalet project", the architectural plans and elevations (no window note or schedule on any
of the 12 sheets) and the freelancer's aluminium workbook (sheet "الكميات": every window row is in it).
THE OPTIONS:
(A) Every window in an outside wall is aluminium unless the drawing or the project file says another material: on Alsenan
all 29 windows go to the aluminium line.
(B) The material comes only from the drawing or the specification; with none, the window count and size are released but
the material stays held (no aluminium line on Alsenan).
(C) Decided per project in the project facts file.
RECOMMENDATION: (A), because aluminium is the normal window material for Kuwait villas and it matches your outdoor-door
rule (practice, not a code clause); the drawing still wins when it says otherwise.
WAITS ON: the aluminium windows line on every villa (Alsenan freelancer 116.9 m2) (T-040, the door / window area method).

Answer: yes (owner, main chat 2026-10-19 16:40). Windows are aluminium by default, like outdoor doors, unless the drawing says otherwise (Claude's reading of 'yes': option A).


### Q-34 The second-floor top roof: which outline does the engine waterproof? (verifier 2026-10-19 16:10; T-071; no-assumptions question)

THE PROBLEM: the engine now measures the three roofs drawn on the plans, inside the parapet as you decided (Q-24): 55.56 +
32.72 + 115.83 = 204.11 m2 of membrane and 181.59 m of upturn. The freelancer has one roof line of 285.00 m2 (and 194.00 m
upturn), 80.89 m2 more. The biggest missing piece is the second-floor block's own top roof (level +13.90, 0.50 m parapet on
the elevations, the third dome on it): no plan sheet draws its outline, so the engine holds it and no Urban rule says
where to take it from.
WHERE TO LOOK: Drive "Alsenan chalet project", the architectural DXF (P7757_DXF_COMPRESSED.zip) or PDF: the second-floor
plan (outer walls of the 2F block; its floor plate is 55.08 m2 outside the walls) and the elevations / section A-A
(p7757_arch_sheet10.pdf) showing the +13.90 roof and its 0.50 m parapet; the freelancer's roof line is in his workbook
"الارضيات+العازل+الديكور+الرخام".
THE OPTIONS:
(A) Take the top roof from the second-floor plan outer walls, membrane inside the parapet like the other roofs (Q-24),
the third dome as an open skylight (Q-29): at most 55.08 m2 (less the parapet band), total at most about 259 m2; the
remaining difference to 285.00 m2 (about 26 m2) stays to be explained.
(B) Hold the top roof until a roof plan is supplied (RFI to the designer); the roof line stays at 204.11 m2 plus a held
top roof.
(C) A and B together: show A as a provisional figure (not released) until the designer confirms the outline.
RECOMMENDATION: (C), because the top roof slab normally sits on the 2F block walls, so A is a sound estimate, but no
drawing prints the outline and a drawing never assumed settles it (practice, not a code clause).
WAITS ON: the roof waterproofing membrane and upturn of Alsenan (about 55 m2 of the freelancer's 285 m2) and every villa
whose top roof is drawn on no plan (T-071 follow-up, roof wiring).

Answer: ask me later (owner, main chat 2026-10-19 16:40). Keep the second-floor top roof HELD (no number, never 0) and do not ask again until the Lead raises it at a milestone.

### Q-31 Footing F10: the drawn outline or the schedule size? (verifier 2026-10-19 15:12; moved back to Open by the Lead 16:15: it had been filed under Answered with no answer; T-065, T-042; no-assumptions question)

THE PROBLEM: at column C5 on the foundation plan, footing F10 is drawn as one open outline 3.25 x 1.40 m that carries
two tags (F10 and F), while the footing schedule gives F10 as 2.80 x 1.40 x 0.50 m. The two drawings disagree by
0.45 m in length, and no Urban rule says which wins. Today the engine holds this footing (no volume); the freelancer
has 1.96 m3 (the schedule size) plus a 0.216 m3 F pad counted inside his four F pads.
WHERE TO LOOK: Drive "Alsenan chalet project", "ST7757.pdf": the foundation plan (page 2) at column C5 on the lower
neighbour side, and the footing schedule (page 9, rows F10 and F).
THE OPTIONS:
(A) Schedule governs: F10 = 2.80 x 1.40 x 0.50 = 1.96 m3, and the separate F pad 0.90 x 0.80 x 0.30 = 0.216 m3 is
counted as well (2.176 m3 in all).
(B) The drawn outline is one combined footing: 3.25 x 1.40 x 0.50 = 2.275 m3, no separate F pad.
(C) Hold both (no volume) and send the designer an RFI; the footing line stays held until he answers.
RECOMMENDATION: (C) with the RFI, because two project drawings conflict and the owner directive says a drawing never
settles a conflict between two drawings; (A) is the freelancer's reading.
WAITS ON: 1.96 - 2.28 m3 of the Alsenan footing line (freelancer footing line 77.63 m3), and the rule for a drawn
footing outline that disagrees with its schedule row on any villa.

Answer: C, also flag it before the final BOQ (owner, main chat 2026-10-19 16:40). His words: "you can also choose the bigger area". Claude's reading: F10 stays HELD with a request for information to the designer, and is flagged in the final BOQ report; if a provisional figure is needed for totals, the bigger area (the drawn 3.25 x 1.40 m outline, 2.275 m3) may be used, marked PROVISIONAL and flagged, never silently.

### Q-35 Wet-room upturn at the door: does the 0.20 m upturn run across the door opening? (lead 2026-10-19 16:15; T-072, T-076; no-assumptions question: two rules disagree)

THE PROBLEM: your kitchen example (Q-30 answer) counts the 0.20 m upturn on the whole boundary, door opening included
(3 x 4 m kitchen: 14.00 lm of wall, 14.80 m2 of membrane surface). The registry rule for doorways (UP-WP-DOOR-001, from
your 2026-10-16 programme) says a doorway is never billed as door width x 0.20 m but is a transition built by detail. The
two rules give different upturn lengths and the engine must not pick one. On Alsenan's 14 measured wet areas: upturn on
the full boundary 123.13 lm vs the freelancer 122.61 lm (+0.4 %); walls only, doorways left out, 110.33 lm (-10.0 %); the
difference is 12.80 lm of doorways.
WHERE TO LOOK: the Q-30 answer below (your kitchen example); any bathroom door on the Alsenan architectural plans (Drive
"Alsenan chalet project", P7757 DXF or PDF part 01-02); the freelancer's waterproofing rows in his workbook
"الارضيات+العازل+الديكور+الرخام".
THE OPTIONS:
(A) Upturn on the full boundary, doorway included, as in your kitchen example: 123.13 lm on Alsenan; no separate doorway
line.
(B) Upturn on the walls only: 110.33 lm on Alsenan; each doorway becomes its own "doorway waterproofing transition" line,
counted per door (pcs, with its width), built to the detail (UP-WP-DOOR-001).
(C) Both, for different purposes: the membrane to BUY follows your strip method (strips cut 0.20 m longer at both ends,
whatever sits in the wall), while the BOQ upturn line is walls only (110.33 lm) plus a doorway transition line per door.
RECOMMENDATION: (C), because your strip method already decides how much membrane is bought, while a doorway needs a
threshold detail that a length x 0.20 line hides (practice, not a code clause). If you want a single upturn figure, (A)
follows your newest words.
WAITS ON: the wet-area upturn line on every villa (12.80 lm on Alsenan) and the doorway part of the membrane fold (T-076).

Answer: yes, and calculate wet area by wet area, not as a total (owner, main chat 2026-10-19 16:40). Claude's reading of 'yes': the recommendation, option C: the membrane to buy follows the owner's strip method per wet area (strips 0.20 m longer at both ends whatever is in the wall); the BOQ upturn line is walls only plus a doorway transition line per door; every figure is reported per wet area, with the total only as a sum of the areas.

Worker 3 addendum (2026-10-19 16:25, T-074 hand table of all 17 Alsenan wet areas incl. the three basin-only spaces and the
kitchen; numbers only, the options above are unchanged): full boundary 144.73 lm (freelancer 144.61 lm, +0.1 %); in it
14 doorways (12 x 0.80 + 1.00 + 0.90 = 11.50 lm), 2 open edges with no wall and no door (1.26 m lobby to the stair hall,
0.90 m basin space to the passage) and 5 doorways that lie BETWEEN TWO WET ROOMS (a W.C. opening into a hand-wash lobby or
into the laundry: 5 x 0.80 m), which the full-boundary sum counts once in each room. Walls only: 144.73 - 15.50 - 2.16 =
127.07 lm. Whatever you choose, please also say for the doorway between two wet rooms: (i) upturn on neither side (the
membrane runs straight through: 144.73 - 8.00 = 136.73 lm under option A), or (ii) on both sides as today. Recommendation:
(i), there is no wall to turn up against there (practice, not a code clause).

### Q-36 A new project folder appeared on Drive: may the team open it, and for what? (lead 2026-10-19 16:15; owner direction "Alsenan first", Q-23; no-assumptions question)

THE PROBLEM: at 15:27 UTC today a third project folder was created under "Urban BOQ private data" (next to the Alsenan
and apartment folders). It holds an earlier-approved architectural plan (PDF, 0.49 MB), an architectural + structural
plan "2" (PDF, 4.89 MB, uploaded twice), an all-floor-plans PDF (1.29 MB) and one photo: it looks like an old building
and its new design, i.e. a renovation set. At 14:17 you cancelled the renovation test and said no new villa will be sent,
and your direction is Alsenan only. No board task names this folder (Drive shows its files were opened 16:03 - 16:06 UTC,
by you or by a session). The Lead will not decide whether it is a working sample, a sealed blind test or not for the team.
WHERE TO LOOK: Drive "Urban BOQ private data", the folder created today at 15:27 UTC.
THE OPTIONS:
(A) Not for the team now: no agent opens it until you say; Alsenan only continues.
(B) A development sample: the team may read it (first for the PDF plan reader, gate 4); no freelancer comparison, nothing
counted as accuracy. Say which files are the old building and which the new design.
(C) A sealed blind test (owner only): no agent opens it; you run it yourself when the engine is ready.
RECOMMENDATION: (A) until you say, because opening a set that may be a blind test cannot be undone and your newest
direction is Alsenan only; if it is the renovation sample after all, answer (B) or (C).
WAITS ON: the PDF plan reader work (gate 4) and any renovation work; nothing on Alsenan waits on it.

Answer: ignore it (owner, main chat 2026-10-19 16:40). Nobody opens the third Drive project folder; it is not a sample and not a test.

### Q-37 The pantry next to the dining room: where does its waterproofing stop? (worker 3 2026-10-19 16:25; T-074, T-072; no-assumptions question)

THE PROBLEM: the ground-floor pantry is a wet area by your rules (pantry is on the wet list, kitchens are waterproofed like
a bathroom, Q-30) and the drainage plan shows a floor drain in it, but it has no wall on the dining side: the drawing
prints it 4.50 x 3.00 m and the dining floor continues past it, so the edge of the membrane is not drawn. The engine holds
it (no membrane, never 0); the freelancer has no pantry waterproofing at all.
WHERE TO LOOK: Drive "Alsenan chalet project", p7757_arch_sheet03.pdf (ground floor plan): the room "PANTRY / تحضير" at
+1.00 between the kitchen side and the DINING, printed 450 and 300; sanitary-7757.pdf, ground floor drainage plan: the
"FDø3"" floor drain in the pantry.
THE OPTIONS:
(A) Waterproof the printed 4.50 x 3.00 = 13.50 m2 like a kitchen: upturn on the three walls and across the 4.50 m open
side (2 x 3.00 + 2 x 4.50 = 15.00 lm, 3.00 m2 at 0.20 m), 2 rolls if done alone; the open side is listed as a threshold
line.
(B) Waterproof only a zone round the drain and the sink counter, size given by you or the designer; held until then.
(C) No waterproofing in the pantry (dry floor, as the freelancer did); the table shows it as "not waterproofed by owner
decision", 0 rolls.
RECOMMENDATION: (A), because a pantry with a floor drain takes water like a kitchen and the printed 3.00 m is the line the
designer drew the room to (practice, not a code clause); ask the designer for a step or a threshold detail at the open side.
WAITS ON: the pantry row of the membrane table (13.50 m2 under A, about 19 % on top of the 72.12 m2 of wet floors) and every
open-plan pantry or kitchen on later villas (T-072, T-074).

Answer: waterproof the surrounding of the pantry, enough (owner, main chat 2026-10-19 16:40). Claude's reading: option A, the pantry floor is waterproofed within its printed 4.50 x 3.00 m with the upturn around it, and the open side toward the dining room listed as a threshold line; if the owner meant a smaller zone, he will say so.

### Q-38 A curved glass wall set in a straight wall: which line gives its width? (worker 1 2026-10-19 16:43; T-077; no-assumptions question)

THE PROBLEM: the engine had lost the big curved pool glazing of the ground floor; it is now counted and held, but its width
cannot be measured without your rule, because four lines could be "the width": the glass is drawn as four curved lines
(6.66, 6.70, 6.75 and 6.79 m long), the architect printed "657" (6.57 m) on the inner face of the 0.20 m curved glazed
band (printed "20"; its outer face is 6.79 m), 8 cm inside the first glass line, and the
straight wall opening it closes is 4.95 m from jamb to jamb. The freelancer took 6.57 x 4.30 = 28.25 m2 (24 % of his
116.9 m2 of windows).
WHERE TO LOOK: Drive "Alsenan chalet project", p7757_arch_sheet03.pdf (ground floor plan), the curved glazing round the
end of the pool, printed "657"; the same in "P7757 dxf.dxf" (the 657 dimension measures the curved line inside the glass,
not one of the four glass lines).
THE OPTIONS:
(A) The printed 6.57 m (the architect's dimension governs): 6.57 m wide.
(B) The outer glass line: 6.79 m wide (+0.22 m, about +0.9 m2 at 4.30 m high).
(C) The middle of the frame (the mean of the glass lines): 6.72 m wide.
RECOMMENDATION: (A), because a printed dimension on the project drawing ranks above a measured line, and the fabricator
measures the frame on site anyway (practice, not a code clause); (B) if you want the largest frame line for supply.
WAITS ON: the width (and later the m2) of curved glass walls in straight openings on Alsenan and on every later villa (T-077,
then the door / window area method).

Answer:

## Answered

### Q-29 Domes: are they concrete at all, and does the roof membrane run under them? (lead 2026-10-19 14:30; Q-24 and Q-27 answers, T-049, T-071, T-072; no-assumptions question)

THE PROBLEM: in your roof answer you wrote "doom will not be concrete", but the structural drawings detail two dome shells
(printed 442 / 190 / 10) and the freelancer counts dome concrete for all three domes (3 x 22.6 m2 x 0.10 = 6.78 m3,
inside his stair + dome line of 21.83 m3). No Urban rule says whether a dome is concrete or a finish, nor whether the
roof membrane stops at a dome or runs under it. Both the concrete line and the roof membrane depend on it, so the dome
parts stay HELD until you choose.
WHERE TO LOOK: Drive "Alsenan chalet project": "ST7757.pdf", the dome detail with 442 / 190 / 10 (the two structural
domes on the first-floor roof); "Alsenan_Architectural_P7757_Pages_05-06", page 6 (SOUTH EAST ELEVATION): the third dome
on the upper roof, 441 wide and 215 high, which has no structural detail. The dome footprints together are 30.70 m2 of
the roofs (roofs inside the parapets 204.10 m2 without them).
THE OPTIONS:
(A) No dome is concrete (all three are a finish, for example fiberglass, measured later as their own item): no dome
    concrete (freelancer's 6.78 m3 becomes a rule difference); the roof membrane stops at each dome base with a 0.20 m
    upturn round it: roof membrane area 204.10 m2 plus upturns.
(B) Follow the structural drawings: the two detailed domes are concrete shells (about 2.54 m3 each by hand on the outer
    basis, held until you confirm the Q-18 size basis), the third (architectural only) is not concrete; membrane as in (A).
(C) Domes are not concrete, and the roof slab under them is continuous, so the membrane runs under the dome footprints:
    roof membrane 204.10 + 30.70 = 234.80 m2 plus the parapet upturn, a 0.20 m upturn round a dome base only where the
    dome stands higher than the slab.
RECOMMENDATION: (A), as your words say, with one RFI to the designer because the structural sheets still draw two
shells: a membrane that ends at a dome base with an upturn is what your answer describes, and a dome that is a
separate finish is measured once, as its own item.
WAITS ON: dome concrete lines and the roof membrane rows on Alsenan (T-049, T-071, T-072).

Answer (owner, main chat, 2026-10-19 14:45 UTC), his words: "Design confirm that 3 domes are concrete and rebar from plans. but after discussing with alsenan owner he said he want them to be not concrete and use the sun light as skylight space. so it will be an open area." = a CLIENT CHANGE to the design: none of the three domes is concrete (no dome concrete, no dome rebar); each dome position is an open skylight area. Lead (applied, not the owner's words): the dome concrete lines leave the BOQ as a recorded scope change (reason CLIENT_CHANGE_DOMES_TO_SKYLIGHT, shown, never silently dropped); the freelancer's 6.78 m3 is a RULE_DIFFERENCE (design scope vs client scope); the roof membrane stops at each opening with the 0.20 m upturn round it (Q-24 answer); what closes the skylight (glazing, frame) is not specified, so it is a HELD item of its own; whether the roof slab is drawn continuous under a dome (then the opening size is not printed) is checked from the drawings and asked if so.

### Q-30 Kitchens: waterproofed like a bathroom, floor only, or not at all? (lead 2026-10-19 14:30; membrane table requirement, T-072, T-074; no-assumptions question)

THE PROBLEM: your membrane-table instruction names kitchens with bathrooms and roofs, but no Urban rule covers kitchen
waterproofing: the wet-room rule (full floor plus a 0.20 m upturn on the whole boundary) is written for wet rooms, and
the registry has no kitchen line. Without your rule every kitchen row would be a guess, so kitchens show HELD in the table.
WHERE TO LOOK: Drive "Alsenan chalet project", the architectural plans (P7757 DXF, PDF part 01-02): every room labelled
kitchen (مطبخ). Worked example for a 4.00 x 3.00 m kitchen with one 0.90 m door.
THE OPTIONS:
(A) Like a bathroom: whole floor plus a 0.20 m upturn on the whole boundary, doorway included: 12.00 + 14.00 x 0.20 =
    14.80 m2 of membrane surface.
(B) Floor only, no upturn: 12.00 m2.
(C) Not waterproofed: the kitchen is listed in the table as "not waterproofed" with 0 rolls by your rule.
RECOMMENDATION: (A): your instruction puts kitchens in the same list as bathrooms, and a kitchen floor with a floor
drain and a sink takes water the same way; the bathroom rule then needs no new exception.
WAITS ON: the kitchen rows of the membrane table and the rolls to buy (T-072, T-074).

Answer (owner, main chat, 2026-10-19 14:45 UTC) = option A with his worked example, his words in short: "Waterproofing Membrane Example — Kitchen 3 m x 4 m. Roll 1 m wide x 10 m long. Overlap 10 cm. Wall upturn 20 cm, folded from the same membrane, not a separate strip. Across the 3 m width: strip 1: 1.00 - 0.20 upturn = 0.80 m floor coverage; strip 2: 1.00 - 0.10 overlap = 0.90 m; strip 3: 0.90 m; strip 4: 0.70 - 0.10 overlap - 0.20 upturn = 0.40 m; total 3.00 m. Length of each strip: 4.00 + 0.20 + 0.20 = 4.40 m. First 3 strips 3 x 1.00 x 4.40 = 13.20 m2; fourth strip 0.70 x 4.40 = 3.08 m2; total membrane cut 16.28 m2. Kitchen floor 12.00 m2; wall perimeter 14.00 lm; floor + upturn surface 14.80 m2; membrane cut including basic overlaps 16.28 m2; roll 10 m2; rolls required 2; remaining gross offcuts 3.72 m2. The wall upturn uses part of the same 1 m-wide membrane, reducing floor coverage; the 10 cm overlap also reduces it. Do not calculate membrane purchases using floor area / roll area alone. This example assumes a simple strip layout; extra corner reinforcement, drain detailing and additional manufacturer-required laps are not included." Lead (applied): kitchens are waterproofed like a bathroom; this example is the hand fixture of the membrane table (T-072) and the method of the hand table (T-074). It does not fix a rule for which way the strips run in other rooms: where direction changes the result, both are reported and the engine's cutting plan is compared, never one picked.

### Q-28 Boundary wall at foundation level: which section, and is the part inside a footing counted again? (worker 2 2026-10-19 14:10; T-065; no-assumptions question)

THE PROBLEM: the foundation plan draws a closed 0.20 m concrete band all round the plot, 91.94 m on its centre line
(2 x 31.17 + 2 x 14.80). Two drawings give it different sections, and 21.45 m of it runs through 10 isolated footings
that reach the plot line. No Urban rule says which section wins or whether the band is counted again inside a footing.
Today the engine keeps only 60.17 m (it loses the whole lower neighbour side) = 7.22 m3; the freelancer has 71.7 m =
8.60 m3, both at 0.20 x 0.60.
WHERE TO LOOK: Drive "Alsenan chalet project", "ST7757.pdf": page 2 (FOUNDATION PLAN: the hatched band on the plot
line; along the lower neighbour side see how C/F, F15, F11, F14 and F10 run into it); page 10 (Schedule of Simple Beams,
row "B.W": 20 x 60, 4 d16 bottom, 2 d14 top); page 14 ("TYPICAL BOUNDARY WALL" plan: GROUND BEAM (20x40), a pad
(130x80x30) at each 20x30 column, spacing "SEE ARCH PLAN"; section A-A: lower G.B 20 wide with no depth written on an
80 x 30 base). Page 1, note 2: the neighbour-side ground beams sit on black brick from foundation level, so the band
under the building is real.
THE OPTIONS:
(A) The band is the B.W beam 0.20 x 0.60 and is not counted again inside a footing: 70.49 m x 0.12 = 8.46 m3; the
21.45 m inside footings is listed (held) and not added.
(B) The band is the B.W beam 0.20 x 0.60 over its full 91.94 m: 11.03 m3 (the 21.45 m inside footings, 2.57 m3,
overlaps footing concrete).
(C) The typical section governs: lower ground beam 0.20 x 0.40 (91.94 m gross 7.36 m3, net of footings 5.64 m3) plus
one 1.30 x 0.80 x 0.30 pad (0.31 m3) at every boundary column, held until the designer gives the column positions.
RECOMMENDATION: (A), and send the designer one RFI to confirm. The B.W row and the 0.20 m band are the two
project-specific sources and they agree; the page 14 sheet is a "typical", not-to-scale detail. Counting the band
again inside a footing would count the same concrete twice (practice, not a code clause).
WAITS ON: the boundary-wall foundation line on Alsenan and the plot-edge member ledger the engine needs on every villa
(T-065 follow-up).

Answer (owner, main chat, 2026-10-19 14:45 UTC), his words: "The proposed calculation for option A is arithmetically correct: (91.94-21.45) x 0.2 x 0.6 = 8.459 m3. Option B is also arithmetically correct: 91.94 x 0.2 x 0.6 = 11.033 m3. But the critical question is whether the 21.45 m is genuinely already included in the footing concrete, and whether the 20 x 60 cm section applies to that entire beam. I would choose A provisionally, not as a released quantity, subject to the structural section and footing intersections being verified. Deducting a beam length simply because it crosses footings can also be wrong if the footing and beam occupy different elevations. The report's other boundary beam figure of 3.526 m3 relates to a 20 x 40 cm ground beam. These must be treated as potentially different structural members, not reconciled by choosing whichever figure resembles the freelancer's." = A PROVISIONAL, NOT RELEASED. Lead (applied): the band shows 8.459 m3 as PROVISIONAL (not in any total) until (1) a section or schedule proves 20 x 60 along the whole band and (2) at each footing crossing the top and bottom levels of band and footing are read from sections: only the overlapping volume is deducted, none where they sit at different elevations; the natural-ground 20 x 40 boundary beam (3.526 m3) is a separate member and is never matched to the freelancer's figure (T-073).

### Q-26 Pool: is the pool floor flat at the printed 1.15 m depth, or sloped? (worker 1 2026-10-19 12:39; T-063; no-assumptions question)

THE PROBLEM: the architectural drawing prints one pool depth, 1.15 m, but the structural pool detail draws a sloped floor
with a step and writes every depth "AS PER ARCH". So the engine cannot tell whether 1.15 m is the depth of the whole pool
or only of the deep end, and the pool wall concrete waits on it.
WHERE TO LOOK: Drive "Alsenan chalet project", "Alsenan_Architectural_P7757_Pages_07-08", page 8 (NORTH WEST ELEVATION):
under the arched opening the view cuts through the pool; the dimension "115" runs from the pool rim (+0.30) to the pool
floor (-0.85), and the floor is drawn flat. Then "ST7757 dxf.dxf" (or ST7757.pdf), "DETAIL OF SWIMMING POOL": sloped
floor, step at one end, floor 40 cm, depths "AS PER ARCH".
THE OPTIONS:
(A) The floor is flat at 1.15 m: pool walls 2.358 m2 (plan) x 1.15 = 2.71 m3; with the 40 cm floor (10.94 x 0.40 =
4.37 m3) the pool is 7.09 m3 (freelancer 12.35 m3, of which 3.48 m3 is a pump room you said does not exist).
(B) 1.15 m is the deep end only; the shallow depth comes from the designer: the walls stay held (shown, not scored) until
then; the floor 4.37 m3 can be released.
(C) Hold the whole pool until the designer confirms the pool section.
RECOMMENDATION: (B). The structural detail is the construction drawing and it clearly draws a slope; the architectural
view is cut at one place only. Practice, not a code clause: a villa pool with a step usually has a shallow and a deep end.
WAITS ON: pool wall concrete (and pool tiling and waterproofing heights) on Alsenan (T-063, T-049).

Answer (owner, main chat, 2026-10-19 14:05 UTC), his words: "flat, pool is small and cannot be sloped." = option A: the pool floor is flat at the printed depth of 1.15 m (architectural elevation: rim +0.30, floor -0.85); the structural detail's slope is not to be used. The 0.40 m floor thickness is the printed value of the structural detail. Claude's note for the Lead (not the owner's words): the structural detail still draws a slope and a step; record it as a drawing conflict resolved by the owner, and ask only if the walls' plan length or the floor area is unclear.
Lead 2026-10-19 14:30 (applied): pool and dome concrete task unblocked (T-049); dome concrete itself waits on Q-29.

### Q-27 Domes: two domes or three? (worker 1 2026-10-19 12:39; T-063, T-037; no-assumptions question)

THE PROBLEM: the architectural drawings show three domes, the structural drawings only two. The engine cannot decide which
drawing is right (a drawing never settles a conflict between two drawings), and the dome concrete count depends on it.
WHERE TO LOOK: Drive "Alsenan chalet project": "Alsenan_Architectural_P7757_Pages_05-06", page 6 (SOUTH EAST ELEVATION):
a dome on top of the second-floor block, width "441" on the parapet line (+14.40) and "215" high above it; the same dome on
page 8 (NORTH WEST, "215") and drawn behind the cut in SECTION B-B (page 11); page 5 (2nd FLOOR PLAN) shows it as a
dashed circle over the maid's room. Then "ST7757 dxf.dxf": the slab over the second floor is flat there (beams and mesh,
no dome, no ring beam); only the two domes on the first-floor roof (R221) have a "DETAIL OF DOME" (442 / 190 / 10).
THE OPTIONS:
(A) Three domes (architecture right): a third dome line on the second-floor roof, held for its size basis like the
others (your Q-18 answer); the structural designer must add its detail.
(B) Two domes (structure right): the top dome is decorative or not built; no concrete line for it.
(C) Hold the third dome as an open item (shown, not scored) until the designer confirms.
RECOMMENDATION: (C), and ask the designer: the architect drew it on three sheets, but no slab, ring beam or detail exists
to build it from, so neither a number nor a silent omission is safe. The freelancer counts three (3 x 22.6 m2 x 0.10 =
6.78 m3).
WAITS ON: dome concrete count (and roof waterproofing round the domes, Q-24) on Alsenan (T-049, T-071).

Answer (owner, main chat, 2026-10-19 14:05 UTC), his words: "3, 2 in the roof and 1 in the upper roof." = option A: three domes, two on the first-floor roof and one on the upper (second-floor) roof. Claude's note for the Lead (not the owner's words): the third dome has no structural detail, so its size basis stays HELD per the Q-18 answer (a printed size wins; nothing printed means held, no default thickness); keep it visible as its own line, and ask the owner or the designer for its thickness and ring beam only when you reach that quantity.
Lead 2026-10-19 14:30 (applied): pool and dome concrete task unblocked (T-049); dome concrete itself waits on Q-29.

### Q-23 Renovation test: which items must the renovation BOQ contain, and how are retained walls finished? (lead 2026-10-19 12:20; owner direction "Alsenan first, then one sealed test"; T-068; no-assumptions question)

THE PROBLEM: you asked the team to prepare for one sealed renovation villa (old building only as a PDF, new design as CAD
+ PDF) and to ask you first which items its BOQ must contain. No Urban rule covers renovation work at all (no demolition
rule, no rule for finishing a wall that stays, no rule for a new opening cut into an old wall), so today the engine could
only measure the new design as if it were a new build. Without your answer every demolition or retained-wall quantity
would be a guess, so it stays HELD.
WHERE TO LOOK: nothing to open yet (the test villa is sealed and no agent may look at it). A worked example on a
synthetic villa: an old internal wall 4.00 m long and 3.00 m high stays; a new door 1.00 x 2.10 m is cut into it; next
to it an old wall 3.00 m long is removed; a new wall 2.50 m long is built. Old wall faces: 4.00 x 3.00 x 2 sides =
24.00 m2; opening 1.00 x 2.10 = 2.10 m2 per side.
THE OPTIONS:
(A) Full renovation BOQ with every line tagged RETAINED / DEMOLISHED / NEW: demolition lines (walls 3.00 x 3.00 =
    9.00 m2 of block, plus the old floor and wall finishes they carried, cutting the new opening 2.10 m2), new works
    (blocks 2.50 m new wall, plaster, paint, floor tiles wet / dry, wall tiles in wet rooms, waterproofing), and on
    retained walls the finishes you choose in the second part below. Example: demolition 9.00 m2 + opening 2.10 m2;
    new block 2.50 m x 3.00 m = 7.50 m2.
(B) Only what you listed (flooring wet: floor and wall, dry floor; wall plaster; wall paint; inner and outer blocks) for
    the NEW design, with demolition shown as a separate information list (areas and counts, not BOQ lines). Example:
    new block 7.50 m2 in the BOQ; demolition 9.00 m2 and the opening 2.10 m2 listed for information only.
(C) The new design measured as a new build (ignore the old building), plus an old-vs-new change list for a person to
    price. Example: every wall of the new design gets new plaster and paint, the retained wall too.
Second part, retained walls (choose one): (i) paint only (no new plaster) unless the drawing marks it; (ii) new plaster
and paint on every retained wall face; (iii) as the drawing or specification says, otherwise HELD for you to decide per
wall. Example retained wall: (i) paint 24.00 - 4.20 = 19.80 m2, no plaster; (ii) plaster and paint 19.80 m2 each;
(iii) HELD unless a note says.
RECOMMENDATION: A with (iii). Practice, not a code clause: a Kuwait villa renovation contract normally prices demolition,
making good and new works as separate items, and whether an old wall is re-plastered depends on its condition, which
only the drawings, a site note or you can say; (iii) keeps every such wall visible instead of guessed.
Waits on: the renovation measurement capability that will be proven on synthetic old / new villas before the test
(flooring wet / dry, plaster, paint, inner and outer blocks, demolition) (T-068 builds the test villas; the measuring
tasks follow your answer).

Answer (owner, main chat, 2026-10-19 12:55 UTC), his words: "Dont worry about it later ill send you the new project." DEFERRED: no answer to the scope options now; the owner will send the new project (and the scope) later. Until then the team prepares only general capabilities proven on synthetic fixtures and Alsenan; no renovation scope is assumed, and the renovation measuring tasks wait for his answer.

Answer (owner, main chat, 2026-10-19 14:15 UTC), his words: "q-23 I DONT WANT TO SEND NEW VILLAH IGNORE IT." = CANCELLED: there will be no new-villa renovation test. Ignore this question and the renovation scope; no renovation BOQ capability is needed. (This replaces the earlier "deferred" note.)
Lead 2026-10-19 14:30 (applied): renovation pairs task cancelled; the PDF plan reader stays a general gate-4 task.

### Q-24 Roof waterproofing: measured inside the parapet or to its outer face, and under the domes or not? (lead 2026-10-19 12:30; T-062; no-assumptions question)

THE PROBLEM: the Urban rule says roofs are waterproofed over the drawn area, but not which edge bounds that area. On
Alsenan the roofs have a 0.20 m parapet, and two domes stand on the top roof. The two edges give different areas, and
the engine releases no roof waterproofing until you choose. Today the engine gives NO roof line at all (the roofs are
held, not lost); the freelancer has 285 m2 for roofs and annexes and 194 m of upturn.
WHERE TO LOOK: Drive "Alsenan chalet project", the architectural plans (P7757 DXF or the six
"Alsenan_Architectural_P7757_Pages_.." PDFs): the first-floor plan, the roof on the west side marked ROOF at level +4.30,
and the second-floor plan, the roof at level +9.70 with the two domes. Measure the west roof once inside the parapet and
once to the parapet's outer face.
THE OPTIONS (all three Alsenan roofs together; the 2F block's own top roof is on no plan sheet and stays held):
(A) Inside the parapet's inner face: 1F west roof 55.56 m2, 1F south-east strip 32.72 m2, 2F roof 115.81 m2 = 204.10 m2
    (-28.4 % against 285); upturn on the inner perimeter 153.81 m.
(B) To the parapet's outer face (A plus the 0.20 m parapet band): 61.90 + 38.66 + 125.66 = 226.21 m2 (-20.6 %).
(C) Another edge you name (for example to the structural slab edge as drawn on the structural plan).
Second part, the two domes on the 2F roof (2 x 15.36 = 30.70 m2 of footprint): (i) the roof membrane runs under the
domes (A 234.80 m2, -17.6 %; B 256.91 m2, -9.9 %; upturn round the domes adds 27.78 m, total 181.59 m with A);
(ii) the dome footprints are left out (the figures above); (iii) the domes get their own waterproofing line, separate
from the roof.
RECOMMENDATION: A with (ii), and the dome waterproofing as its own line when the dome detail shows it (iii). Practice,
not a code clause: in Kuwait villas the roof membrane is laid on the slab inside the parapet and turned up the parapet's
inner face (the upturn is measured separately), and the parapet top is a coping, not membrane; a dome cast on the slab
sits on the roof membrane only if the detail shows it, so it should not be added by assumption.
Waits on: roof waterproofing area and upturn on Alsenan and every villa with parapets (T-062 follow-up, T-071).

Answer (owner, main chat, 2026-10-19 12:55 UTC), his words: "roof calculated as the bathrooms same way (membrane + 20cm walls upturn, in the circle dome, doom will not be concrete, (change if plan he want it fiberglass or anything visible, lets say the circle doom is high than normal slab, then we add 20cm upturn around circle to secure the waterproof."
Owner addendum (main chat, 2026-10-19 13:50 UTC), his words: "calculating it should be full membranes and the edges to cut and not like skirting porcelain calculation linear m. Overlapping membrane is for example 10m length by 1m width. it will be 1m and overlap of 10cm overlapped between the next 1m." He also sent a picture of a 3 m x 3 m bathroom: roll 1.00 m x 10.00 m, strips of 1.00 m with a 10 cm overlap between neighbouring strips, a 20 cm upturn on the walls all round, material counted as whole strips with the edges cut. This matches UP-WP-001 (roll 1.00 x 10.00 m), UP-WP-002 (0.10 m lap between strips), UP-WP-003 (0.20 m upturn) and UP-WP-005 (material from the roll layout, never a flat rate or a linear-metre rate): roofs, domes' bases and every other membrane area use the same roll layout and cutting plan as a bathroom, never length x 0.20. Open point for the owner: the picture's table (3 strips x 3.20 m = 9.60 m2, 1 roll) does not visibly include the 20 cm upturn on all four walls or the effect of the two 10 cm laps on the width covered; the Lead should use the engine's layout as the reference and ask the owner only if he wants the table reproduced exactly.
Claude's reading for the Lead (NOT the owner's words; confirm or ask): the roof follows the same rule as a bathroom floor (UP-WP-003: membrane over the area plus a 0.20 m upturn on the walls and parapet); the domes are not concrete, so the membrane does not run under them unless the plan shows a different dome build-up (fiberglass or another visible finish: follow the plan); a dome that stands higher than the slab gets a 0.20 m upturn round its base. Anything the drawing shows differently wins (drawing over Urban rule).
Lead 2026-10-19 14:30 (applied, NOT the owner's words): roofs are measured like a bathroom floor: membrane over the area inside the parapet plus the 0.20 m upturn on the parapet and walls, as whole strips with 0.10 m laps (T-071, T-072). The dome part (concrete or not, membrane under the footprints or not) was not settled by the words "doom will not be concrete" against structural drawings that detail two dome shells: asked as Q-29; held until then.

### Q-25 A parapet line that stops a few centimetres short of the wall: may the engine close the gap? (lead 2026-10-19 12:30; T-062; no-assumptions question)

THE PROBLEM: on Alsenan each roof parapet line stops short of the wall it should meet, so no closed roof outline exists
and the roof cannot be measured from the drawing alone. The gaps are 0.075 m (2F roof), 0.200 m (1F west roof) and
0.405 m (1F south-east strip). No Urban rule says whether such a drafting gap may be closed.
WHERE TO LOOK: Drive "Alsenan chalet project", the P7757 DXF, the first- and second-floor plans: zoom to where the parapet
line of each ROOF meets the building wall; the parapet ends just before the wall (a door-layer line sits there).
THE OPTIONS:
(A) Close a gap up to a set limit (for example 0.50 m) by extending the parapet line in its own direction to the wall,
    record every closure with its length for review: all three Alsenan roofs become measurable (areas as in Q-24).
(B) Close only gaps up to a small limit (for example 0.10 m): the 2F roof (0.075 m) is measured, the two 1F roofs stay
    held (88.28 m2 on basis A).
(C) Never close: every roof with a gap stays held until a person draws it closed or confirms it.
RECOMMENDATION: A with a 0.50 m limit and every closure listed for a person to check. Practice, not a code clause: a
parapet that ends a few centimetres before the wall is a drafting habit (the line stops at a door or a column face), not a
gap in the real roof; a gap larger than a wall thickness could be a real opening, so the limit stays below 0.50 m and
each closure stays visible.
Waits on: measuring every roof, balcony and terrace outline that is drawn on a layer of its own (T-071).

Answer (owner, main chat, 2026-10-19 12:55 UTC), his words: "so there should be a overlap 10cm + 20cm upturn + the gap for the membrane."
Claude's reading for the Lead (NOT the owner's words; confirm or ask): the drafting gap is not left open: the membrane covers it, with a 0.10 m overlap at the join and the 0.20 m upturn; the gap length is added to the measured membrane. The owner named no size limit for the gap: do not assume the 0.50 m limit of the question; list every closure with its length, and ask the owner if a gap is large enough to be a real opening.
Lead 2026-10-19 14:30 (applied): every gap is closed by the membrane and listed with its length; a gap with an opening element drawn on it is not closed and is reported (T-071).

### Q-22 Pool check: which pump room is the POOL pump room? (lead 2026-10-19 10:15; T-057; no-assumptions question)

THE PROBLEM: your rule (Q-19 answer) says: whenever a villa has a pool, check for the pool pump room. Many villas also
have a pump for the house water (ground tank and booster pump). A space or label that only says "PUMP" does not say which
system it serves, and no Urban rule tells the engine whether such a room counts as the pool's. Nothing is measured here;
it decides whether the pool check says FOUND or NOT FOUND.
WHERE TO LOOK: Alsenan, architectural plans (Drive "Alsenan chalet project", the P7757 DXF or the six
"Alsenan_Architectural_P7757_Pages_.." PDFs): search for the text "PUMP". The verifier read that label as the house water
pump; you checked by hand that Alsenan has no pool pump room.
THE OPTIONS:
(A) Only a space or equipment block that names the pool counts (for example "pool pump", "pool filtration", "pool plant",
    "balance tank", or the Arabic for pool pumps / pool filter room). A plain "PUMP" room is listed as "pump room, use not
    stated" for a person to confirm, and the pool check shows POOL PUMP ROOM NOT FOUND. Alsenan: NOT FOUND (matches your
    hand check), plus one "use not stated" item.
(B) Any pump room on a villa that has a pool counts as the pool pump room. Alsenan: FOUND (contradicts your hand check).
(C) Plain "PUMP" labels are ignored. Alsenan: NOT FOUND, but on another villa a real pool plant room labelled only
    "PUMP" would be missed with no flag.
RECOMMENDATION: A. Practice, not a code clause: in Kuwait villas the house water pumps (ground tank and booster) and the
pool filtration plant are separate systems and are often in separate rooms; counting a house pump as the pool plant
would hide a missing pool plant room, while A keeps every uncertain case visible for a person to decide.
Waits on: the pool check list on every villa (T-057; no quantity changes).

Answer: A (owner, 2026-10-19, in the lead run chat). Only a space or equipment block that names the pool (pool pump, pool filtration, pool plant room, balance tank, or the Arabic equivalents) counts as the pool pump room. A plain "PUMP" room or label is listed as "pump room, use not stated" for a person to confirm and never makes the pool pump room FOUND; the pool check then shows POOL PUMP ROOM NOT FOUND. Alsenan: NOT FOUND plus one "use not stated" item. Task T-057.

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
Verifier 2026-10-19 05:00 (T-037, T-038 checked against the drawing): there is no basement and no lift on any sheet of
the two DXFs (lowest level printed 0.00). The freelancer's 2.40 m3 of lift walls (8 x 0.20 x 1.50) under his "basement"
heading cannot be checked: the architectural PDF on Drive is 37.5 MB, above the 10 MB the agents can read. A zipped
copy of that PDF in the same Drive folder would let an agent read the pool depth, the stair sections and any lift.

Answer: B, conditional on identifying the actual structural members (owner, main chat 2026-10-19). Do not assume every concrete member along the plot boundary is an isolated footing or ground beam: ST7757 page 14 shows the boundary-wall details, page 10 the beam schedule. Identify separately the boundary-wall ground beam (G.B), the boundary-wall base or footing (B.W), isolated footings and other continuous foundations or connecting beams, each with its section, length, location and purpose. Investigate the missing 31.77 m (91.94 m reported vs 60.17 m recognised) through CAD geometry and details; do not assume 91.94 m is right until independently verified. Do not force the engine to the freelancer figure. Report isolated footings, boundary-wall foundations and ground beams as separate quantities.

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

Answer: B, with the architectural room label as primary evidence (owner, 2026-10-19). P7757 says what a room is; Sanitary-7757 says where fixtures, drains and showers are. Process: identify the room from P7757, read its label and boundary, cross-reference the sanitary drawing, then decide wet or dry and apply the Urban finish and waterproofing rules. A toilet-like object in a room labelled lobby does not make it a bathroom. No label and ambiguous sanitary evidence: hold the classification. A real toilet need not show a drain in the same CAD view. Uncertain fixture recognition must never create bathroom ceramic, waterproofing or plumbing quantities. A missing fixture or drain in one drawing triggers a coordination check, not deletion of the bathroom class.

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

Answer: The structural slab is 16 cm unless a drawing or detail says otherwise (owner, 2026-10-19). Search slab plans, slab reinforcement details, sections, general notes and local slab and stair details; use 0.16 m where the drawing confirms it and the specific value where a slab or zone differs; do not apply 16 cm to stairs, balconies, depressed slabs, landings or special elements without checking their details. Distinguish ground level, FFL, slab top, soffit, floor-to-floor, clear height, false-ceiling height, plaster height and paint height. Example: FFL +1.00 and +5.50 give 4.50 m floor-to-floor; 0.16 m slab alone does not prove a 4.34 m clear height. Do not subtract an assumed floor build-up or false-ceiling depth; use elevations and sections. A false ceiling does not mean the wall above gets no plaster or paint. Per floor report: slab thickness, FFL, structural level, floor-to-floor, clear height where verified, plaster height, paint height, source drawing and detail. A missing value holds only the affected quantity.

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

Answer: A. Development project 2 (the apartment) is a completely separate project (owner, 2026-10-19). The owner can download the original DWG again, convert it to DXF and resend it. Keep separate project records and drawing registers; never mix quantities, rules, revisions, assumptions or benchmark data. Investigate why the earlier conversion reportedly lost 57 % of the content (entity types, XREFs, blocks, proxy objects, dimensions, geometric coverage) before accepting a conversion. This must not block the Alsenan BOQ.

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

Answer: A, but exhaust all drawing evidence before asking (owner, 2026-10-19). Read simple- and continuous-beam schedules, two- and three-span details, beam sections, reinforcement schedules, ground-beam details and structural plans. Procedure per unlabelled span: CAD geometry, floor and location, supporting columns, connected and adjacent spans, labels and schedule references, sections and reinforcement details, match to a documented beam type, continuous or separate span; assign a section only with sufficient evidence, otherwise record it unresolved. Do not copy the neighbouring depth because beams align: a continuous beam can change section between spans. Report each unresolved beam with floor, location, observed geometry, candidate sections, rejected alternatives and reason held. The same principle applies to footings, columns, slabs, stairs, pools and domes.

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

Answer: A, approved with verification requirements (owner, 2026-10-19). A value typed in from a drawing goes into a controlled project data file with: drawing filename, number and revision, sheet or page, exact note, dimension or detail reference, units, value, applicable floors or members, verification status and reviewer or source. Status words: DRAWING-VERIFIED, OWNER-CONFIRMED, DESIGNER-CONFIRMED, INFERRED (from verified values with documented logic), ASSUMED, HELD. The engine must not claim it extracted a value automatically when it was typed in, and manually supplied answers must not inflate automated-extraction accuracy.

### Q-20 Stairs: besides the steps, how is the concrete under them (the sloping waist slab) and the landings measured? (lead 2026-10-19; Q-19 answer, T-056)

What we found: your Q-19 answer gives the concrete of the steps (one step x the number of steps). A concrete stair also has
the sloping slab the steps sit on (the waist) and the flat landings, and the drawing prints neither thickness.
Real example: Alsenan, ground-floor stair (structural "ST7757 dxf.dxf", ground-floor slab plan): tread lines are drawn but
there is no stair section and no waist or landing thickness. For a 1.20 m wide flight with 10 steps of 0.30 x 0.16, the
steps alone are 10 x 1/2 x 0.16 x 0.30 x 1.20 = 0.288 m3; a 15 cm waist under the same flight would add about
1.20 x 3.40 (sloping length) x 0.15 = 0.61 m3.
How to check it yourself: open the stair on the ground-floor slab plan and look for a section or a note with a waist or
landing thickness.
Choices: (a) count the steps only, as in your answer; waist and landings are not a separate line; (b) steps + a waist slab
of a thickness you give (for example 15 cm) + landings of a thickness you give; (c) steps now, waist and landings held
(shown, not scored) until the designer prints them.
Waits on: stair concrete on every villa (T-056).

Answer: C for genuinely unknown dimensions, but first read every stair detail (owner, 2026-10-19). Typical values are reference only, not Alsenan dimensions: riser 15-17 cm, tread about 30 cm, width 1.10-1.20 m. Determine the real geometry from P7757, ST7757, sections and levels: connected floors, total rise, actual riser and tread counts, uniform risers per flight, tread depth, flight width, landings, structural stair sections, waist thickness from the detail. Treads are not automatically equal to risers; landings matter. Separate step concrete, sloping waist slab, intermediate and floor landings, stair beams and supports, formwork, reinforcement, marble tread and riser finish and handrails. No double counting of slab or landing concrete. Stair finish is marble unless the drawings or approved specification say otherwise. A missing stair dimension holds only the unresolved quantity; the waist slab and landings are not dropped because a dimension was not recognised.

### Q-21 Foundations: is the printed 1.50 m depth the bottom of the footing or the bottom of the blinding under it? (lead 2026-10-19 06:15; T-044, part of OQ-13; no-assumptions question)

What we found: the structural notes print a depth of 1.50 m below the plot level, but they call it the excavation level. The
engine treats it as the underside of the footing. If the 10 cm plain-concrete blinding sits inside those 1.50 m, every
footing is 10 cm higher and every neck column between footing and ground beam is 10 cm shorter.
Real example: Alsenan, structural "ST7757 dxf.dxf", schedules sheet, general note 1 (in Arabic): excavation level not less
than 1.5 m below the existing plot level; the engine uses a 10 cm blinding. 28 neck columns (10.856 m3 together)
take their height from this level.
How to check it yourself: open the foundation section or the schedules sheet and see whether the 1.50 m is dimensioned to
the bottom of the footing or to the bottom of the blinding.
Choices: (a) 1.50 m is the bottom of the blinding: footing underside at 1.40 m, necks 10 cm shorter; (b) 1.50 m is the
bottom of the footing: blinding below it, excavation to 1.60 m; (c) hold the neck and excavation heights (shown, not
scored) until the designer prints the footing level.
Waits on: neck column concrete, excavation and backfill on every villa (T-044, T-045, T-046).

Answer: C until the complete foundation level arrangement is verified (owner, 2026-10-19). The notes recommend excavation at least 1.50 m below the existing plot level; this does not by itself fix the founding level. The engine must understand the process, not subtract 10 cm. Distinguish: existing ground, excavation formation level, bottom and top of blinding, bottom and top of footing, column-neck start and end, finished ground and floor levels. Illustration only: formation -1.50 m with 0.10 m blinding gives footing underside -1.40 m; footing underside required at -1.50 m needs excavation to -1.60 m; neither is automatically right for Alsenan. Account for unsuitable or uneven soil needing extra excavation, approved replacement fill, compaction and blinding. Do not assume loose sand is suitable backfill, that deeper is better, or that extra fill or concrete strengthens a foundation; no change of founding level or fill material without engineering approval. Measure separately: excavation, disposal of unsuitable material, approved replacement fill, compaction, blinding concrete, footings, column necks, backfill. Do not compute the 28 column necks on an unresolved foundation datum.

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

Answer (owner, 2026-10-19, via the lead's run chat): (c) hold the domes until the designer confirms, AND keep it clearly
visible in every report that the dome size basis is NOT resolved, so it is never hidden. So: each dome line is HELD with
reason DOME_SIZE_BASIS_NOT_CONFIRMED (owner Q-18), listed by name in the BOQ, the scoreboard verdicts and every lead /
hub report as an open item; it is never a number and never 0, and it is never folded into a total silently. Tasks T-049.

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

Answer (owner, 2026-10-19, via the lead's run chat), recorded word for word in meaning:
- STAIRS: a step is about 15 cm high x 30 cm deep x 120 cm long; the length depends on the plan, and the height depends
  on the floor height, so it can be 16 or 16.5 cm etc. (the earlier owner example: the riser height of each floor comes
  from that floor's height). Concrete of the steps = the concrete volume of one step x the number of steps needed.
  Lead reading, tied to existing rules: riser height = floor-to-floor rise / counted number of risers (UP-STAIR-009,
  owner rule addendum 2026-09-17; the 0.155-0.165 m range is a sanity check only, never a quantity); tread depth and stair
  width are read from the plan (UP-STAIR-002: geometry from the drawing); one step = 1/2 x riser x tread x width;
  steps concrete = one step x number of steps. What the answer does NOT cover stays HELD and is asked as Q-20: the
  waist slab under the steps and the landings.
- POOL (same answer): pool depth is about 1.00 m or 1.15 m: CHECK it on the drawing (the expected range is a check, not a
  value to use); it is a normal pool, not an overflow pool. Alsenan has NO pool pump room (owner checked by hand). Rule for
  every villa: whenever there is a pool, always check for the pool pump room, and check where the house's main manholes are.
- A size printed on the drawing always wins (e.g. Alsenan pool floor 0.40 m printed, not the engine's 0.25), per
  UP-KB-PREC-001. Other "usual villa sizes" (pool walls, dome rise / shell) are NOT approved by this answer: lines that rest
  only on them stay HELD.
Tasks: T-056 (stair steps concrete), T-057 (pool check list), T-049 (printed pool sizes; domes held, visible).


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
