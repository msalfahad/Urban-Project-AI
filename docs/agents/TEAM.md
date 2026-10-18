# Team: who leads, who does what, who checks (owner, 2026-10-18)

The owner put the Lead in charge of the **whole engine**: the BOQ engine, the 17 product agents in `agents/`, and the
Claude skills in `.claude/skills/`. Every scheduled agent reads this file after MISSION.md. The owner decides; the Lead
plans and supervises; workers build; the verifier checks; the scout researches.

## Plan and daily targets

`docs/agents/PLAN.md` (owner, 2026-10-18) sets the goal (an engine right on any villa; Alsenan is one sample), the
milestones M1-M5 and each agent's daily target. Every agent reads it after this file and works to its row.

## Parallel work (owner, 2026-10-18: no idle agents)

Schedule (UTC): worker 1 at :19, worker 2 at :39, worker 3 at :59 every hour; verifier at :49 every hour; lead every
2 h at :09; research scout daily. Rules every agent follows:
- One task, one worker: claim it on the board (push first) before any work; a rejected push means someone else moved;
  fetch, re-read, claim another.
- No two CLAIMED tasks change the same engine file. The lead writes "Files:" in each row; a worker skips a TODO whose
  files overlap a CLAIMED row and takes the next one.
- A run that outlasts the hour is fine: the next run of the same worker simply claims a different task.
- Workers start each task branch from the latest working branch. If the working branch moved and the task now
  conflicts (usually docs/CODEMAP.md only), do NOT make a merge commit (the session permission check refuses merging
  another branch into a task branch, seen 2026-10-18 on T-019): create a fresh branch from the current working branch,
  re-apply your own task changes, regenerate CODEMAP with the tool, re-run the tests and push that branch
  (agents/task-<id>-r2), naming it on the board.
- Verifier: before checking a READY task, mark it "VERIFYING (verifier, UTC time)" on the board and push; another
  verifier run skips tasks marked VERIFYING less than 2 h ago.
- Lead keeps 8-12 TODO tasks (at most 2 Track B) so no worker finds an empty board.

Owner questions and anything the owner must check (owner, 2026-10-18): plain words, a real example from the drawing
he can check by hand, simple choices; see OWNER_QUESTIONS.md "How to write a question for the owner".

## Chain of command

```
Owner (answers OWNER_QUESTIONS.md, gates 5-7, final say)
  └─ Lead planner (scheduled, every 2 h)  — plans, prioritises, supervises the team, never writes code
       ├─ Workers 1-3 (each hourly, staggered) — one board task per run, on agents/task-<id>, never merges
       ├─ Verifier (scheduled, hourly)    — checks every READY task, merges or rejects, keeps the scoreboard
       └─ Research scout (scheduled, daily)  — ideas into RESEARCH_LOG.md and the board's Ideas
```

The 17 product agents and the 6 skills are not scheduled; they are **parts of the product** that this team maintains.
They are led the same way as engine code: the Lead writes tasks for them, a worker changes them, the verifier checks.

## Repositories every scheduled agent attaches

| Repository | What | Access |
|---|---|---|
| msalfahad/Urban-Project-AI | engine, product agents, skills, this board (`agents/control`) | push (never `main`) |
| msalfahad/urban-boq-private-data | client drawings, freelancer BOQ, development villas | read-only; never copied into the public repo |
| msalfahad/UrbanProjectsManager | the Flutter web app (how projects, BOQ lines and cost items are stored and shown) | read-only; never changed (a push to main deploys) |

Attachments: no agent hands files to another. The Lead names the exact private path in each task row; the worker reads
it from a folder outside the public clone.

## Two tracks on one board

**Track A: BOQ engine quantities (priority).** Gates 0-4 in MISSION.md, lowest gate first, then money at risk.

**Track B: product agents and skills.** At most **one** Track B task in TODO at a time, so Track A is never starved.
Order: A1 Extractor and A2 Reviewer first (they produce quantity records and overlap the plan reader, PLAN_READER.md),
then A7 Quotation (prices and contracts, pinned to the strongest model), then A9 Orchestrator (routing), then the
client agents A3-A5, then A6/A8/A11-A13, then the marketing chain A10/A14-A17. Track B tasks use the same row format
(gate column: `B`), and every task names the agent folder, the change to `prompt.md` / `schema.py` / `agent.py`, and
a test case added to `agents/<name>/tests/` with a known correct output.

Product-agent rules (agents/README.md): an agent reads something ambiguous or writes something a person reads; it
**never** computes a total, applies a rate or checks its own arithmetic (the engine does). A2 never sees A1's records.
No agent calls another agent. Tests run offline with a stub model (`python3 -m pytest agents/<name>`); no API key and
no network in tests.

First Track B task (Lead adds it): census of all 17 agents and 6 skills: per agent, offline tests pass or fail, what
code calls it (grep), model pin in `agents/base.py`, last change, overlap or conflict with MISSION.md (A1/A2 vs the plan
reader, A7 vs BOQ output), proposed next task. Docs only, table in `docs/agents/research/AGENTS_CENSUS.md`.

## Who checks whom

| Work | Checked by | How |
|---|---|---|
| Worker task (either track) | Verifier | MISSION.md gates; for Track B also `pytest agents/<name>` and the base runner tests pass, the rule above holds, no live API call in tests |
| Verifier merges | Lead | each run: re-read the last merges on the working branch; a merge that broke a gate becomes a fix task at the top of its track |
| Lead's plan | Owner | the Lead's 3-5 line notification; the owner can overrule in OWNER_QUESTIONS.md or a session |
| Team health | Lead | each run: list the scheduled tasks (list_triggers) and check each agent's last run (failed, not run on time, could not attach a repository, claim older than 12 h, READY older than 24 h); report problems in the notification and fix what the board can fix |
| Owner's own Claude Code sessions | Lead | new commits on the working branch close matching board tasks (DONE, owner session) |
