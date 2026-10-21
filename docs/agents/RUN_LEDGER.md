# Run ledger: one row per scheduled run (owner, 2026-10-20 17:30)

The owner asked for a status on every scheduled run:

| Status | Meaning |
|---|---|
| SUCCESS | Self-check passed in full and the task was delivered. |
| BLOCKED | At least one authorised step was refused. Hand work may still have been delivered. |
| FAILED | Nothing delivered. |
| INCOMPLETE | The run started but left no RUN_LOG line. |

A silent run is never counted as a success. The owner's main chat (the auditor) updates this file once a day (owner decision 2026-10-20 20:10).

**Evidence and its limits.**

- Run start and end times come from each scheduled task's last-run record. That record only shows the latest run, so
  an older silent run cannot be inspected after the next one starts.
- The result comes from each agent's RUN_LOG line and commits.
- The auditor cannot read the transcripts of scheduled sessions. For an INCOMPLETE run, the last command executed and
  the cause (approval card, timeout, environment, other) are **NOT KNOWN**. They are not assumed.
- Each agent's start-of-run line (proposed below) is what will make the cause visible.

## 2026-10-20, 10:00 to 19:30 UTC (code-running agents)

| Slot (UTC) | Agent | Status | Evidence |
|---|---|---|---|
| 10:19 | Worker 1 | BLOCKED | logged 10:34; self-check passed, but `codemap.py route` [Code from External] and the Drive DXF decode [PII Data Handling] were refused; the Alsenan figure was NOT MEASURED |
| 10:39 | Worker 2 | INCOMPLETE | still PENDING 50 min later (auditor 11:29); no line, no commit |
| 10:49 | Verifier | SUCCESS | logged 11:36; 4 merged, full self-check passed |
| 10:59 | Worker 3 | INCOMPLETE | no line, no commit |
| 11:19 | Worker 1 | SUCCESS | logged 11:50 |
| 11:39 | Worker 2 | SUCCESS | logged 12:05; one chained push was refused [Modify Shared Resources] and redone in steps |
| 11:49 | Verifier | BLOCKED | logged 11:53; codemap / pytest / freeze refused [Code from External] |
| 11:59 | Worker 3 | SUCCESS | logged 12:19 |
| 12:19 | Worker 1 | BLOCKED | logged 12:42; `uv pip install -r requirements.txt` refused [Code from External]; hand task delivered |
| 12:39 | Worker 2 | SUCCESS | logged 12:56 |
| 12:49 | Verifier | SUCCESS | logged 13:28; 4 merged |
| 12:59 | Worker 3 | INCOMPLETE | no line, no commit |
| 13:19 | Worker 1 | SUCCESS | logged 13:51 |
| 13:39 | Worker 2 | BLOCKED | logged 14:45; freeze check [Code from External] and task-branch write [Sensitive-Source Provenance] refused; board-only handoff |
| 13:49 | Verifier | SUCCESS | logged 14:52; 4 merged |
| 13:59 | Worker 3 | SUCCESS | logged 15:22 (wall heights, both methods) |
| 14:19 | Worker 1 | SUCCESS | logged 14:43 |
| 14:39 | Worker 2 | INCOMPLETE | no line, no commit |
| 14:49 | Verifier | SUCCESS | logged 15:10; 1 merged, 1 rejected |
| 14:59 | Worker 3 | SUCCESS | logged 15:21 (stair floor residue) |
| 15:19 | Worker 1 | SUCCESS | logged 15:57 |
| 15:39 | Worker 2 | FAILED | logged 15:46; venv [Untrusted Code Integration] and claim commit [Auto-Mode Bypass] refused |
| 15:49 | Verifier | BLOCKED | logged 15:52; venv / codemap / freeze refused [Code from External] |
| 15:59 | Worker 3 | SUCCESS | logged 16:55 |
| 16:19 | Worker 1 | INCOMPLETE | no line, no commit |
| 16:39 | Worker 2 | INCOMPLETE | no line, no commit |
| 16:49 | Verifier | INCOMPLETE | no RUN_LOG line and no board write, but it merged T-116, T-109 and T-117 to the working branch (merge commits; Lead 18:25 marked the rows MERGED from them) |
| 16:59 | Worker 3 | BLOCKED | logged 17:48; self-check passed, but the Drive zip decode was refused [Untrusted Code Integration]; Alsenan figure NOT run |
| 17:19 | Worker 1 | INCOMPLETE | the scheduled run ended SUCCEEDED after 4 min 55 s (17:19:51 to 17:24:46), but left no line and no commit; cause NOT KNOWN |
| 17:39 | Worker 2 | SUCCESS | ran 17:39:45 to 18:07:22, logged 18:08; self-check clone / venv / codemap / t061 / freeze all PASS; T-121 READY (soffits over outside air 45.632 m2 CALCULATED, finish HELD) |
| 17:49 | Verifier | SUCCESS | logged 18:34; self-check clone / venv / codemap / t061 / freeze all PASS and Drive zip decode PASS; merged the waterproofing candidate (opt-in), rejected the soffit census (pool-court void drawn 3.689 m2, not 4.373) |
| 17:59 | Worker 3 | INCOMPLETE | the scheduled run ended SUCCEEDED after 6 min 2 s (17:59:18 to 18:05:21), no line, no commit; cause NOT KNOWN |
| 18:19 | Worker 1 | INCOMPLETE | the scheduled run ended SUCCEEDED after 5 min 25 s (18:19:44 to 18:25:09), no line, no commit; cause NOT KNOWN |
| 18:39 | Worker 2 | SUCCESS | ran 18:39:15 to 18:58:29, logged 19:10; self-check all PASS; stair-landing task READY |
| 18:49 | Verifier | INCOMPLETE | the scheduled run ended SUCCEEDED after 2 min 19 s (18:49:29 to 18:51:48), no line, no commit; old prompt (no STARTED step yet); cause NOT KNOWN |
| 18:59 | Worker 3 | INCOMPLETE | fired 19:00:12 on the OLD prompt (the STARTED step was added 19:03), ended SUCCEEDED after 3 min 54 s, no line, no commit; cause NOT KNOWN |
| 19:19 | Worker 1 | SUCCESS (counted in the 19:30-04:30 block below) | first run on the new prompt: STARTED 19:19, final 19:48, facade task READY |

**Totals, 36 finished slots (to 19:30):**

| Status | Runs | Share |
|---|---|---|
| SUCCESS | 17 | 47 % |
| BLOCKED | 6 | 17 % |
| FAILED | 1 | 3 % |
| INCOMPLETE | 12 | 33 % |

The verifier finished 9 runs: 5 SUCCESS, 2 BLOCKED, 2 INCOMPLETE.

**Pattern (auditor 18:30).** Worker 1 left nothing in its last three runs (16:19, 17:19, 18:19). Each of the last three
silent worker runs that the last-run record can still show (worker 1 17:19 and 18:19, worker 3 17:59) ended as SUCCEEDED
after 5 to 6 minutes, with no RUN_LOG line, no claim and no commit. A run that ends normally that early, without writing
its line, stops before step 2 (claim) and step 10 (log). The cause is NOT KNOWN without the start-of-run line below.

## 2026-10-20 19:19 to 2026-10-21 04:30 UTC (daily audit 2026-10-21 04:31)

| Slot (UTC) | Agent | Status | Evidence |
|---|---|---|---|
| 19:19 | Worker 1 | SUCCESS | STARTED 19:19, final 19:48; GF facade run task READY |
| 19:39 | Worker 2 | SUCCESS | STARTED 19:40, final 20:04; membrane offcut task READY |
| 19:49 | Verifier | INCOMPLETE | scheduler 19:49:56 to 19:52:34 (2 min 38 s) SUCCEEDED; no STARTED or final line, no commit; cause NOT KNOWN |
| 19:59 | Worker 3 | SUCCESS | STARTED 20:00, final 20:21; beam register task READY |
| 20:09 | Lead | SUCCESS | STARTED 20:10, final 20:18; lanes S / A / I applied on the board |
| 20:19 | Worker 1 | SUCCESS | STARTED 20:20, final 20:47; route G scope task READY |
| 20:39 | Worker 2 | SUCCESS | STARTED 20:40, final 21:07; 2F stair arrival task READY |
| 20:49 | Verifier | SUCCESS | STARTED 20:51, final 21:07; 4 merged |
| 20:59 | Worker 3 | SUCCESS | STARTED 21:00, final 21:54; V3.0 skeleton READY |
| 21:19 | Worker 1 | SUCCESS | STARTED 21:20, final 22:05; rebar-firewall rework READY |
| 21:39 | Worker 2 | INCOMPLETE | no line at all; cause NOT KNOWN |
| 21:49 | Verifier | SUCCESS | STARTED 21:49, final 22:10; 2 merged |
| 21:59 | Worker 3 | INCOMPLETE | STARTED 21:59, no final line (UNCLOSED); cause NOT KNOWN |
| 22:09 | Lead | SUCCESS | STARTED 22:11, final 22:17 |
| 22:19 | Worker 1 | INCOMPLETE | no line at all; cause NOT KNOWN |
| 22:39 | Worker 2 | SUCCESS | STARTED 22:40, final 23:02; stair flight once READY |
| 22:49 | Verifier | INCOMPLETE | STARTED 22:51, no final line (UNCLOSED; noted by the next verifier run); cause NOT KNOWN |
| 22:59 | Worker 3 | SUCCESS | STARTED 23:00, final 00:21; coverage registry 1.1.0 READY |
| 23:19 | Worker 1 | SUCCESS | STARTED 23:20, final 23:42; beam section cuts READY |
| 23:39 | Worker 2 | BLOCKED | STARTED 23:41, final 23:43; the board claim could not be committed and pushed; no work done |
| 23:49 | Verifier | SUCCESS | STARTED 23:50, final 23:56; 2 merged, V3.0 skeleton rejected |
| 23:59 | Worker 3 | SUCCESS | STARTED 00:00, final 01:46; V3.0 rework READY |
| 00:09 | Lead | SUCCESS | STARTED 00:10, final 00:15 |
| 00:19 | Worker 1 | SUCCESS | STARTED 00:21, final 00:38; footing steel READY, new owner Q-71 |
| 00:39 | Worker 2 | INCOMPLETE | no line at all; cause NOT KNOWN |
| 00:49 | Verifier | BLOCKED | STARTED 00:50 (clone refused; line written with the GitHub connector), final 00:52: EXECUTION NOT VERIFIED, nothing merged |
| 00:59 | Worker 3 | SUCCESS | STARTED 01:00, final 01:45; membrane coverage proof READY |
| 01:19 | Worker 1 | SUCCESS | STARTED 01:20, final 01:50; stair ledger READY |
| 01:39 | Worker 2 | INCOMPLETE | no line at all; cause NOT KNOWN |
| 01:49 | Verifier | SUCCESS | STARTED 01:50, final 02:31; 3 merged incl. the V3.0 opt-in candidate, 1 rejected |
| 01:59 | Worker 3 | INCOMPLETE | no line at all; cause NOT KNOWN |
| 02:09 | Lead | SUCCESS | STARTED 02:10, final 02:16 |
| 02:19 | Worker 1 | INCOMPLETE | no line at all (Lead: 2-4 min in the scheduler); cause NOT KNOWN |
| 02:39 | Worker 2 | SUCCESS | STARTED 02:40, final 02:56; pool-court soffit READY |
| 02:49 | Verifier | INCOMPLETE | no line at all; cause NOT KNOWN |
| 02:59 | Worker 3 | INCOMPLETE | no line at all; cause NOT KNOWN |
| 03:19 | Worker 1 | SUCCESS | STARTED 03:20, final 03:41; ground-beam steel READY |
| 03:39 | Worker 2 | INCOMPLETE | scheduler 03:39:26 to 03:42:04 (2 min 38 s) SUCCEEDED; no line; cause NOT KNOWN |
| 03:49 | Verifier | SUCCESS | STARTED 03:50, final 04:05; 3 merged, 1 rejected; t061 refused twice [Code from External] then ran |
| 03:59 | Worker 3 | INCOMPLETE | scheduler 04:00:07 to 04:04:10 (4 min 3 s) SUCCEEDED; no line; cause NOT KNOWN |
| 04:09 | Lead | SUCCESS | STARTED 04:10, final 04:20 |
| 04:19 | Worker 1 | SUCCESS | STARTED 04:20, final 04:30; ground-beam steel rework READY |

**Totals, 42 slots:**

| Status | Runs | Share |
|---|---|---|
| SUCCESS | 27 | 64 % |
| BLOCKED | 2 | 5 % |
| FAILED | 0 | 0 % |
| INCOMPLETE | 13 | 31 % |

Pattern: every INCOMPLETE run whose scheduler record is still visible ended SUCCEEDED after 2.5 to 4 minutes with no STARTED line, so it stopped before step (1) of the start-of-run record. The same early stop happened in the main chat's Test B session (3 min, refused write). The Lead runs (5 of 5) never stopped early. Cause NOT KNOWN.

## Refused commands (today, from RUN_LOG; exact refusal reasons)

| Refusal reason | Command (as the agents report it) | Agents |
|---|---|---|
| [Code from External] | `uv venv -p python3.11 .venv && uv pip install -p .venv/bin/python -r requirements.txt`; `python3 -I tools/codemap.py check` / `route`; `python3 -I tools/freeze_verify.py check --index ...`; `pytest -q tests/...` | verifier, workers 1-3 |
| [Untrusted Code Integration] | `git clone` of Urban-Project-AI (full and sparse); clone fast-forward; once the venv step; base64 decode + unzip of the Drive DXF zip | workers 1-3, verifier, lead |
| [Modify Shared Resources] | a chained `git add && git commit && git push` to agents/control | worker 2, worker 1 |
| [Auto-Mode Bypass] | `git add` / `git commit` of the board after an earlier refusal in the same run | worker 2 |
| [Sensitive-Source Provenance] | writing research files into a local agents/task-* branch | worker 2 |
| [PII Data Handling] | decode / unzip of the Drive DXF download in the scratchpad | worker 1 |
| [External System Writes] | `git push` | worker 1 (01:25) |
| "Blocked by classifier" | chained one-liners, a grep loop, a working-branch fetch | lead, verifier, worker 3 |

## Minimum permissions needed (proposal; nothing changed, owner confirmation needed)

Only these commands, scoped to this repository, its branches and its own tools:

1. **Git.**
   - `git clone` / `git fetch` of msalfahad/Urban-Project-AI, branches agents/control,
     claude/access-permissions-setup-ii24ws and agents/task-*.
   - `git checkout` / `git merge` in that clone.
   - `git add` / `git commit`.
   - `git push origin agents/control` (docs/agents only) and `git push origin agents/task-<id>`.
   - Verifier only: `git push origin claude/access-permissions-setup-ii24ws` for a verified merge. Never a force push.
2. **Python environment.**
   - `uv venv -p python3.11 .venv`.
   - `uv pip install -p .venv/bin/python -r requirements.txt` (the repository's pinned file only).
3. **Project checks**, with `.venv/bin/python` only:
   - `-I tools/codemap.py (check|route|impact|build)`;
   - `-I tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl`;
   - `-m pytest -p no:cacheprovider -q tests/<folder>`;
   - `-I tools/alsenan_scoreboard.py`.
4. **Drive copies.** Decoding a downloaded Drive file into the session scratchpad (base64 decode, unzip) for reading
   only. Never into the repository.

Not requested: unrestricted execution, other installs or downloads, other repositories, secrets, force push, branch
deletion, Drive writes.

**Where this applies.** Allow rules in `.claude/settings.json` are read only by a session that has exactly one
repository. Today's scheduled sessions attach two (Urban-Project-AI and UrbanProjectsManager; worker 2 session record,
17:52), so a settings file would not be read. Options, for the owner to choose:

- (a) Repo-attached Claude Code scheduled tasks with Urban-Project-AI only (UrbanProjectsManager is needed only for
  app-shape tasks).
- (b) Stop agents adding UrbanProjectsManager by default, then test whether a settings file is honoured. Not yet tested.

## Start-of-run line (APPROVED by the owner 18:45; added to the five agent prompts 18:50)

Unclosed-run rule (owner): a STARTED line with no final line from the same agent and run is an UNCLOSED run, counted
INCOMPLETE. The scheduler's "succeeded" never makes it a success.

Original proposal:

At the start of every run, before the self-check, each agent writes:

`- <time> | <agent> | STARTED | <session id> | self-check pending`

At the end it replaces that line with the final one. A run that stops leaves a STARTED line with no end, and its
last-written step shows how far it got.
