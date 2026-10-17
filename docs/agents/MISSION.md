# Mission: an Urban BOQ engine that matches a professional QS

Goal: on the Alsenan villa the engine's BOQ matches the freelancer's BOQ trade by trade (concrete, rebar, blockwork,
plaster, paint, floor area, wet vs dry areas, waterproofing, tiles, doors and windows), within agreed tolerances, with
every difference either fixed or explained as a scope or rule difference the owner accepted. Then repeat on a second
villa without project-specific code.

## Roles (scheduled agents; each run starts fresh and reads this folder first)

| Role | Writes | Never |
|---|---|---|
| Lead (planner) | BOARD.md (next tasks, priorities), OWNER_QUESTIONS.md | writes engine code |
| Worker (one task per run) | engine code on its own branch `agents/task-<id>`, its BOARD.md row | edits frozen methods or version files in place; merges its own work |
| Verifier | SCOREBOARD.md, the verdict on each task branch; merges a branch only when every gate passes | writes engine code |
| Research scout | RESEARCH_LOG.md, ideas into BOARD.md "Ideas" | installs or runs downloaded code |
| Owner (10 min/day) | answers in OWNER_QUESTIONS.md | - |

## Gates a task must pass before the verifier merges it

1. The scoreboard does not get worse on any trade, and the targeted trade improves or the task is explained as a fix.
2. Tests at the level `python3 -I tools/codemap.py impact <file>` recommends (L1-L4, see CLAUDE.md) pass on the task head.
3. Freeze check: `frozen artefacts differing from the index: 0`.
4. No client drawing or client data is committed to this public repository.

## Data

Client drawings and the freelancer's original BOQ live in the private repository `msalfahad/urban-boq-private-data`
(never in this public repo). The freelancer's parsed rows are already in `tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json`.

## Working rules

Use `docs/ROUTE_QUICK.md` and `route` / `impact` (CLAUDE.md). One task per run, small and reversible. Ask the owner only
what an agent cannot decide from drawings, rules or evidence; at most 5 open questions at a time.
