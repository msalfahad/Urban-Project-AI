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
