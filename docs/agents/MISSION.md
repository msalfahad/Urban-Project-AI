# Mission: an Urban BOQ engine a QS can trust

North star (owner's master study, 17 Oct 2026, `URBAN_PROJECT_AI_MASTER_95PLUS`): from Kuwait villa drawings
(DWG / DXF / PDF / images), a floor-by-floor, room-by-room, element-by-element **unpriced** BOQ with evidence, at
**95 %+ independently demonstrated quantity accuracy, zero material silent omissions, and tighter limits on expensive
items** (concrete, rebar, waterproofing, openings, blockwork). Trades in scope now: concrete, rebar, blockwork, plaster,
paint, floor area, wet vs dry areas, waterproofing, tiles, doors and windows.

## How accuracy is scored (never "95 % of categories pass")

Per category and unit (never mix m2, m3, lm, t, nr):
- **Coverage**: reference lines the engine answered as RELEASED, HELD or UNSUPPORTED / all reference lines.
- **Silent omissions**: reference lines with no engine entry at all. Target 0. Worst kind of error.
- **WAPE** = sum|engine - reference| / sum reference, on released matched lines. 95 % accuracy means WAPE <= 5 %.
- **Signed total error**: diagnostic only (over and under cancel out).
- **False positives and duplicates**: engine lines with no reference, one surface counted twice. Target 0.
Working targets (not yet owner-approved, see OWNER_QUESTIONS): WAPE <= 5 % per category; concrete <= 2 %; rebar
<= 2-3 %; waterproofing <= 2-3 % with no wet room missed; doors and windows exact counts; floor areas <= 1-2 % with no
room lost; blockwork and finishes <= 3 % where sections and schedules exist.

## Who is right (owner, 2026-10-18)

The goal is every quantity correct. Matching the freelancer within 95 % is a floor, not the finish line: the engine may
become more accurate than the freelancer. For every difference the verifier records a verdict from the drawing and the
owner rules: ENGINE_RIGHT, FREELANCER_RIGHT, RULE_DIFFERENCE (different measurement basis) or UNRESOLVED (owner
question). Only FREELANCER_RIGHT and UNRESOLVED count against the engine; ENGINE_RIGHT needs a hand calculation
from the drawing, never the engine's own output.

## One engine for every villa, not a fit to Alsenan (owner, 2026-10-18)

The aim is an engine that is right on any Kuwait villa drawing, not one that reproduces Alsenan. Alsenan is one
development case among several. So:
- Every fix is a general rule (geometry, symbol, text, schedule or owner rule), never a project constant: no Alsenan
  layer names, coordinates, room names, counts or thresholds tuned until its numbers match. Project-specific facts go in
  a project fact file with their source, never in engine code.
- Every task's acceptance needs a hand-calculated synthetic fixture that is NOT Alsenan (other layouts, layer names,
  units, rotation, mirror, Arabic and English labels), plus the development villas (T-012) when available. A change
  that improves Alsenan but is untested elsewhere is not done.
- The scoreboard is kept per villa; a trade counts as improved only if no villa gets worse.
- The verifier rejects a change whose logic only holds for Alsenan.

## Alsenan is the DEVELOPMENT villa, not a blind test

The freelancer's BOQ is our development reference: we may tune against it, so it can never prove accuracy. Proof needs
new villas measured by an independent QS before seeing engine output. Agents never start a blind test, never touch a
sealed benchmark (`URBAN_BLIND_V2`), and never claim an accuracy figure for the product.

## Gates (master study §08); the lead works the lowest open gate first

| Gate | Content | Exit |
|---|---|---|
| 0 | Reproducible baseline: real HEAD, capability from code (not documents), triage the 377 known suite failures | baseline recorded |
| 1 | Geometry integrity, no silent omissions: D-P9-01/02 curved glazing, D-P9-04 0.899 m2, the 23 unverified changes; every labelled room and opening appears as measured / held / unsupported | 0 lost rooms or openings on the development set |
| 2 | Architectural coverage: blockwork m2/m3 by thickness, facade, roof build-up, ceilings, stairs, schedules | full architectural ledger, unsupported lines explicit |
| 3 | Structural coverage: concrete element census, rebar by bar population (no kg/m3 proxy as measured), formwork, excavation | structural ledger checked by hand |
| 4 | Intake: vector PDF, scanned PDF and images (plan reader), DWG, multi-sheet links | format matrix passes, nothing fabricated |
| 5-7 | Blind benchmark, pilot, product | **owner only** |

## Roles (scheduled agents; each run starts fresh and reads this folder first)

| Role | Writes | Never |
|---|---|---|
| Lead (planner) | BOARD.md (tasks by gate and cost of error), OWNER_QUESTIONS.md | writes engine code |
| Worker (one task per run) | code on its own branch `agents/task-<id>`, its BOARD.md row | edits frozen methods or version files in place; merges its own work |
| Plan reader (see PLAN_READER.md) | per-sheet census of what a QS sees: rooms, wet / dry, doors, windows, printed dimensions, Arabic and English | produces a BOQ quantity |
| Verifier | SCOREBOARD.md (coverage, silent omissions, WAPE per trade), verdicts; merges only when every gate passes | writes engine code |
| Research scout | RESEARCH_LOG.md, ideas into BOARD.md "Ideas" | installs or runs downloaded code |
| Owner (10 min/day) | answers in OWNER_QUESTIONS.md | - |

Flow per trade: plan reader lists what is on the drawings -> worker makes the engine measure it from CAD -> verifier
compares engine vs plan-reader census vs freelancer -> every mismatch becomes a fix task or an owner question -> lead
picks the next trade by gate, then by money at risk (rebar, concrete, waterproofing, aluminium first within a gate).

## Gates a task must pass before the verifier merges it

1. The scoreboard does not get worse on any trade (coverage down, silent omissions up or WAPE up all count as worse).
2. Tests at the level `python3 -I tools/codemap.py impact <file>` recommends (L1-L4, CLAUDE.md) pass on the task head.
3. Freeze check: `frozen artefacts differing from the index: 0`.
4. No client drawing or client data is committed to this public repository.
5. Definition of done (study §12): real code; a hand-calculated fixture with adversarial cases (mirror, rotation,
   units, missing data); no historical regression; released / held / unsupported handled; missing never becomes 0.

## Reporting results to the owner (owner, 2026-10-19; applies to every agent)

The owner reads results as engineering progress, not task numbers. Every handoff, verifier verdict, lead report and scout
answer says, in plain words and in this order:
1. **What the engine now gives against the freelancer BOQ**: project, trade, unit, engine quantity, freelancer quantity,
   difference in units and in %, and the change since the last report (for example "concrete 92.8 m3 vs 111.8 m3, -19.0 m3
   (-17.0 %), was -21.4 m3"). Measured, held (why) or refused (why) is always stated; a held quantity is never shown as 0.
2. **What improved or got worse, and why** (the cause in one sentence: a rule applied, a drawing read, a defect found).
3. **What the team learned** (a rule, a drawing convention, a failure mode now understood) and **what is still missing**.
4. **Which gate (0 - 4) this serves and how close the gate is to done.**
Task ids (T-nn) and file names go only in a closing line for the team, never as the content. The Lead keeps
docs/agents/PROGRESS.md in this form; the Verifier's SCOREBOARD.md supplies the measured numbers; workers put the
numbers of their task in their handoff in the same terms. Nothing is estimated: a number the run did not measure is
written "not measured".

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

## Data

Client drawings and the freelancer's original BOQ live in the private repository `msalfahad/urban-boq-private-data`
(never in this public repo). The freelancer's parsed rows are in `tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json`.

## Working rules

Use `docs/ROUTE_QUICK.md` and `route` / `impact` (CLAUDE.md). One task per run, small and reversible. Code and verified
quantities beat reports. Ask the owner only what an agent cannot decide from drawings, rules or evidence; at most 5 open
questions. A question goes into OWNER_QUESTIONS.md AND into the run's final message (push notification; no digest).
Answers are written back under "Answer:" in OWNER_QUESTIONS.md.

Cadence: research scout daily, lead every 6 h, worker every 2 h (one task per run), verifier every 3 h.
The verifier merges into `claude/access-permissions-setup-ii24ws` only clean merges; anything that conflicts with work
from an owner's own Claude Code session stays READY with a note.

## Owner directive: understand the drawings first (owner, main chat, 2026-10-19)

Read all drawings of a project together (architectural P7757, structural ST7757, elevations, sections, sanitary, foundation,
column, beam, slab, stair, pool and dome details, notes and schedules) as one coordinated design, before measuring.
Precedence: 1 confirmed project drawings, details, schedules and notes; 2 owner or designer decisions that do not conflict
with safety or regulation; 3 Urban measurement rules; 4 standard engineering practice (never silently turned into a verified
project dimension); 5 assumptions (only when allowed, labelled, otherwise hold). A project drawing overrides a generic Urban
rule on the same subject, never a safety requirement, and never settles a conflict between two drawings: record the conflict.
Sequence: intake, understanding, interpretation (match each member to its schedule and section), project rule resolution,
deterministic takeoff (agents interpret and verify, they do not invent measurements), cross-discipline checks, independent
QA, release with source, method and status. Every quantity traces: drawing, object, detail, rule, calculation,
verification, BOQ item. Before measuring, write a project understanding report (drawing register, geometry, structural
system, architectural and finishing system, sanitary and drainage, project rule register, conflict register, measurement
readiness). Project-specific rules stay inside that project; only rules proven on several projects go to the global base.
No hard-coded fixes to match a benchmark. Prices are not needed. Safety-critical items (founding level, fill, soil) need the
designer or geotechnical confirmation. Tests wanted: 16 cm slab vs local override; label vs misleading furniture; bathroom
drain cross-check; boundary base vs ground beam; unlabelled beam with and without a matching section; two- and three-span
beams; stair riser uniformity and landings; stair waist and steps without double counting; foundation datum ambiguity;
verified typed value vs assumption; project rule over Urban default; conflicting revisions; missing CAD geometry;
separation of projects. Each test records expected, actual and reason for any failure.
