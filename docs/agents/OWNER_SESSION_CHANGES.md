# Changes made by the owner's main chat session (newest first)

Owner rule (2026-10-19): whenever the owner's main chat session changes anything (an agent's instructions or schedule, the
board, a rule, the working branch, a setting), it writes one line here at once, so the Lead is never surprised. Lead: read
this file at the start of every run, treat each entry as already decided, and do not undo or duplicate it. If an entry
conflicts with something you planned, say so in your report to the main chat instead of overriding it.

| UTC time | What changed | Where | Why |
|---|---|---|---|
| 2026-10-19 11:20 | READINESS CHECK, no change made: confirmed that workers 1-3 and the verifier already carry the RUN_LOG step (step 10) and the docs-only clone fallback that the owner and the Lead added at 11:10-11:13 on top of the 11:05-11:08 instructions; nothing of either was lost. Open owner questions: none (Q-22 answered A). Still open outside the agents: development project 2 DXF (owner), attaching the repository to each scheduled task as its source (owner, in the app) | all triggers; OWNER_QUESTIONS.md | Owner asked for a readiness check |
| 2026-10-19 11:13 | New rule and this file; Lead instructions: read this file every run; task size 50 minutes (was "about 1 hour"); gather and merge all verified work every run | Lead trigger; docs/agents/OWNER_SESSION_CHANGES.md | Owner: tell the Lead about every change |
| 2026-10-19 11:08 | Worker 2 and worker 3 instructions replaced: owner rules at the top (no assumptions, 50-minute packages, quality over speed, engineering-term reports), registry next version 1.7.0 (1.6.0 is taken), Drive folder list now has the six architectural PDF parts and the DXF zip, refusal text must be written out | worker 2 and worker 3 triggers | Owner rules reach the workers directly; same text as worker 1 |
| 2026-10-19 11:07 | Worker 1 instructions replaced with the same text as workers 2 and 3 (it was on the older version: private clone first, no parallel rule, no merge-before-push step) | worker 1 trigger | Lead NEEDS FIXING item 2 |
| 2026-10-19 11:05 | Verifier instructions replaced: merge EVERY verified task in one run in the Lead's order; on a conflict only in docs/CODEMAP.md, docs/ROUTING.md or docs/RULES_INDEX.md rebuild them with `python3 -I tools/codemap.py build`, check, freeze check, then merge; checks up to 4 tasks per run (was 2); depth check on very short runs; no writes to any dashboard (the refresher does it); reports in engineering terms | verifier trigger | Owner: nothing verified waits for the owner; Lead NEEDS FIXING item 1 |
| 2026-10-19 11:02 | MERGED into the working branch (head 6def656), each verified earlier, maps rebuilt, freeze 0, targeted tests pass: T-036 58468c6, T-033 a281ff4, T-037 864c28e, T-041 78c57b2, T-044-r2 02a7472, T-029 980e489, T-034 faad086, T-011 aadced7, T-047-r2 6def656. BOARD rows marked MERGED (commit 4c616d1). Not merged (not verified): T-058, T-061, T-057 | claude/access-permissions-setup-ii24ws; BOARD.md | Owner: merge if the Lead does not mind; the Lead's own report asked for it |
| 2026-10-19 10:30 | Verifier follow-up note: merge all verified tasks in one run | OWNER_QUESTIONS.md | Verifier left T-047-r2 on a map conflict |
| 2026-10-19 09:40 | Owner rule: tasks of at least 50 minutes, quality over speed | TEAM.md, OWNER_QUESTIONS.md | Owner |
| 2026-10-19 09:23 | Data note: the architectural PDF is on Drive as six parts under 10 MB (the owner uploaded them); project 2 DXF still to come | OWNER_QUESTIONS.md | Owner |
| 2026-10-19 08:51 | Owner answers recorded for Q-12, Q-13, Q-14, Q-15, Q-16, Q-17, Q-20, Q-21 and the drawing-first directive added | OWNER_QUESTIONS.md, MISSION.md | Owner's words in the main chat |
| 2026-10-19 08:50 | Merge instruction: the verifier merges verified tasks and regenerates the generated maps | OWNER_QUESTIONS.md | Owner |
| 2026-10-19 08:45 | Lead instructions replaced: reports in engineering terms, PROGRESS.md, question format, report delivered to the main chat each run; auditor check (hourly :28) created | Lead trigger; auditor trigger; PROGRESS.md; MISSION.md; TEAM.md | Owner |
