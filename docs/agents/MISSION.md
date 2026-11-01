# Mission: an Urban BOQ engine a QS can trust

North star (owner's master study, 17 Oct 2026, `URBAN_PROJECT_AI_MASTER_95PLUS`): from Kuwait villa drawings
(DWG / DXF / PDF / images), a floor-by-floor, room-by-room, element-by-element **unpriced** BOQ with evidence, at
**95 %+ independently demonstrated quantity accuracy, zero material silent omissions, and tighter limits on expensive
items** (concrete, rebar, waterproofing, openings, blockwork). Trades in scope now: concrete, rebar, blockwork, plaster,
paint, floor area, wet vs dry areas, waterproofing, tiles, doors and windows.


## Owner directive 2026-11-02: Goal B, priority order, blind test (binds every agent; read first)

**Goal B:** the engine produces a complete, priced BOQ for ANY villa from its PDF and AutoCAD plans, without a
freelancer doing a manual takeoff. Alsenan is the training sample, not the target. "Done" means:
1. V3.x is within +-3 % of the freelancer on every trade for Alsenan, AND
2. it passes a BLIND test on a new villa that no agent has seen.

**Priority order: SUPERSEDED by the owner follow-up directive below (same day); kept for the record.**
1. GENERALISE: turn per-project fixes into general rules that work on any villa.
2. MATERIALS: convert net quantities into purchase quantities (blocks, glue, mortar cement and sand, lintels, plaster
   cement and sand, tile boxes, adhesive bags, pallets).
3. VERIFY: move HELD or PARTIAL lines to VERIFIED.
4. RESEARCH: only when it unblocks 1-3.
Every new task names the BOQ line(s) it moves toward VERIFIED and states "every villa" or explains why it cannot.
Research-only merges with no line target are refused.

**Blind-test protocol:**
- Each project lives in its own Drive folder (PDF + AutoCAD + freelancer workbook).
- After Alsenan passes, the owner gives a NEW villa folder. Agents may read ONLY its drawings.
- The engine output is frozen (hash recorded on the board) BEFORE anyone opens that project's freelancer workbook.
- It is then scored once. No tuning on the blind villa before scoring. Afterwards any fix is a general rule
  (priority 1), never a per-project patch.

**Time stamps:** take every time written to the board, run log or reports from `date -u`; never type it by hand.


## Owner follow-up directive 2026-11-02 (supersedes the priority order and acceptance criteria above; binds every agent)

**Goal B** stays: a complete, priced BOQ for any supported Kuwait villa from its drawings and approved project inputs,
without a freelancer doing the takeoff. The training villa is the development benchmark, not the target.

**Priorities (the Lead ranks every task by these; research only when it unblocks one of them):**
- P0 SECURITY AND REGRESSION PROTECTION, before any major refactor: repository privacy and access check (owner
  actions; nothing destructive without the owner), E1 hash protection of released V2.9 (T-467), D1-D5 meaningful
  tests (T-462 .. T-466), the .gitignore gap (T-470), and confirmed unit / calculation defects that contaminate
  downstream quantities (C1 T-456, C3 T-458; a C-row is P0 only once its first step has reproduced the defect).
- P1 GENERALISATION AND VERIFICATION, two parallel streams. Generalisation: A2 config schema (T-450 part 1), A1 by
  trade (T-449), A4 project-independent scoring (T-452). Verification: independent re-measure of concrete, then
  reinforcement, then blockwork, then waterproofing, plaster, paint, tiles, ceilings, doors, windows, stairs and the
  rest (T-180 as the Checker's stream, T-469 scoring), plus the BOQ completeness matrix (T-471). The aim is more
  independently VERIFIED WHOLE LINES, not more measured lines. Remaining C-rows (T-457, T-459, T-460, T-461) here.
- P2 MATERIALS from verified or clearly labelled provisional net quantities (T-448, T-453, T-454, T-455). A material
  quantity is never VERIFIED just because its geometric area is.
- P3 CONTROLLED REFACTORING AND PRICING: A3 split into small regression-tested steps (T-451); the pricing framework
  (T-472); one status vocabulary (T-468).
- P4 RECONCILIATION AND BLIND ACCEPTANCE: full trade-level reconciliation and acceptance before the blind villa.

**A1: three classes for every project-specific correction.** (A) DRAWING-DERIVED RULE: reusable logic with tests.
(B) DECLARED PROJECT FACT in per-project config, each with value and unit, source, drawing / document reference,
approval status, date, affected BOQ lines, CONFIRMED or PROVISIONAL. (C) UNEXPLAINED PATCH (made only to match the
freelancer or an earlier engine result): removed. A1 passes when the training villa runs on generic logic plus
declared facts only. The +-0.5 % comparison is a diagnostic, not proof; a difference caused by correcting a genuine
error is documented and Checker-approved, never forced back to a known wrong number.

**Goal B acceptance (all four, per trade):**
- A QUANTITY: (engine - reconciled reference) / reconciled reference x 100, |variance| <= 3 %, same measurement
  boundaries and units.
- B COST: the same formula on cost, both sides on ONE approved pricing basis, |variance| <= 3 %; a low rate never hides
  an excessive quantity.
- C COMPLETENESS: every expected component is VERIFIED, HELD with a reason, EXCLUDED with evidence, or reported
  MISSING / UNMEASURED; nothing disappears silently.
- D LINE LEVEL: line-by-line reconciliation for high-value and safety-critical items (footings, columns, ground
  beams, suspended slabs, reinforcement, stairs, waterproofing, major openings); a right total from offsetting errors
  fails.
Report variance against BOTH the original freelancer workbook and the independently reconciled reference; the
freelancer is not ground truth and every material difference carries an explanation. Zero-reference quantities,
missing items and unmatched scope get an exception class (ZERO_REFERENCE, ENGINE_ONLY, REFERENCE_ONLY,
SCOPE_MISMATCH), never a division by zero or a silent drop. Goal B is not complete while material HELD or UNMEASURED
scope remains.

**Completeness matrix states (per project, from its own drawings and specifications; never invented scope):**
1 NOT_APPLICABLE (evidence), 2 APPLICABLE_VERIFIED, 3 APPLICABLE_HELD (reason), 4 APPLICABLE_UNMEASURED,
5 POSSIBLY_APPLICABLE (clarification needed). Task T-471.

**Verification record (the Checker reproduces; passing tests alone never promotes a line).** Every VERIFIED line
carries: drawing source and revision, sheet or CAD entity reference, dimensions and units, formula, rule and rule
version, deductions, net quantity, assumptions, independent calculation, difference from the engine, Checker decision.
VERIFIED COMPONENT is not a VERIFIED line; VERIFIED ZERO counts only with evidence of absence.
**Weekly metrics (headline = independently closed whole lines):** whole lines newly VERIFIED; verified quantity and
value by trade; % of expected scope verified; HELD by reason; UNMEASURED components; high-value open conflicts;
failed independent checks; reopened or downgraded lines.

**Three layers, never merged:** (1) net engineering quantities, (2) procurement quantities from documented
consumption rules (blocks, glue, cement / sand, adhesive, tile boxes rounded at project / material level with
room-by-room layout and waste evidence kept, lintels, mesh and ties, membrane rolls; rebar traced through geometry,
lengths, laps, hooks, anchorage, wastage), (3) cost from approved rates. Owner site rates are applied as owner rates
and flagged where product or supplier confirmation is still needed; they are not universal standards.

**Pricing:** a missing approved price is UNPRICED, never zero and never an invented market price. Material-only,
labour-only, installed and subcontract rates stay separate so an installed rate is never added to its own materials.
Owner overrides keep an audit trail. Rates and quotations live in access-controlled storage, not this repository.

**Blind-test readiness, before the blind villa is spent:** project-independent intake and scoring, meaningful
regression tests, protected frozen versions, independent verification, completeness checks, working materials,
controlled pricing, no hidden training-villa patches, explicit exception reporting. The villa must be genuinely
unseen. FINDING 2026-11-02 (main chat): the earlier "sealed" benchmark villa has development material in this
repository (128 tracked paths, including BOQ and pricing folders under research/qs_wall_treatment_01), so it is
REGRESSION ONLY, not a blind test. Protocol: admit drawings; freeze input hashes; run without viewing reference
quantities; freeze BOQ output and engine version hashes; reconcile the reference independently; score quantity, cost,
completeness and exceptions; publish the first pass unchanged. Later improvements are labelled POST-BLIND; the first
result is never silently rerun and replaced.


## Owner decisions 2026-11-02 (execution gate; binds every agent)

- ACCURACY: the official +-3 % quantity target is against the RECONCILED reference; the original freelancer variance
  is always reported beside it; no quantity is forced to an incorrect freelancer value. Cost-variance acceptance waits
  for approved, dated rates. Line-level engineering verification stays for every significant component.
- MATERIALITY: 1 % of trade value is the PRIORITISATION threshold for unresolved items. Safety-critical, structural
  and waterproofing items are material regardless of value. Materiality never turns an assumed quantity into VERIFIED;
  provisional allowances stay disclosed and never count as independently verified.
- VERIFICATION: the Checker keeps its own drawing-based reference calculations across candidate versions (a stored
  reference per line, re-used when the candidate moves) and never uses the engine output as its reference. VERIFIED,
  PARTIAL, HELD and UNMEASURED stay distinct. Acceptance is a SEPARATE acceptance record per task / line (T-468),
  added beside the existing MERGED workflow, not replacing it.
- COMPLETENESS OWNERSHIP: T-471 the overall matrix; T-383 the waterproofing check inside it; T-310 the export
  integration; no duplicate implementation.
- SCOREBOARD (next restatement, T-469): per trade, quantities and coverage for (1) expected BOQ lines, (2) measured,
  (3) independently verified whole lines, (4) held, (5) unmeasured, (6) provisional material quantities, (7) fully
  verified procurement quantities, (8) priced / unpriced. No overall accuracy from only the lines that were scored.
- GATES: Gate 0 = T-467, T-462 .. T-466, T-470, T-456 / T-458 (reproduce, then correct). Gate 1 = T-450, T-449,
  T-452, T-180, T-469, T-471. Gate 2 = T-448, T-453 .. T-455. Gate 3 = T-451, T-468, T-472.
- BLIND TEST: the exposed benchmark is regression-only. The owner provides a genuinely unseen villa when the engine
  passes the readiness gate; no agent accesses, searches for or prepares that villa or its reference workbook before.
- PR #3: merged by the owner after its diff, base branch, lock tests and absence of unrelated changes are confirmed.
- RFIs: B-S18 (document control) is the first proposed for issue; nothing is sent without the owner; the other RFIs
  keep their evidence and approval states.

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

Note (owner directive 2026-10-22): WHEN and HOW to ask the owner now follow ENGINEERING_REASONING_STANDARD.md sections 2.7 and 6; the no-assumptions rule above is unchanged.
