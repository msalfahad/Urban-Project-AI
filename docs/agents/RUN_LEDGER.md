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
| 03:39 | Worker 2 | BLOCKED | scheduler 03:39:26 to 03:42:04; agent report relayed by the owner: full clone of agents/control and the commit / push of the STARTED line refused "[Instruction Poisoning]"; docs-only clone worked (read only); no line written, GitHub connector deliberately not used |
| 03:49 | Verifier | SUCCESS | STARTED 03:50, final 04:05; 3 merged, 1 rejected; t061 refused twice [Code from External] then ran |
| 03:59 | Worker 3 | BLOCKED | scheduler 04:00:07 to 04:04:10; agent report relayed by the owner: full and docs-only clone refused "[Untrusted Code Integration]"; building the RUN_LOG edit refused "[Instruction Poisoning]"; no line written |
| 04:09 | Lead | SUCCESS | STARTED 04:10, final 04:20 |
| 04:19 | Worker 1 | SUCCESS | STARTED 04:20, final 04:30; ground-beam steel rework READY |

**Totals, 42 slots:**

| Status | Runs | Share |
|---|---|---|
| SUCCESS | 27 | 64 % |
| BLOCKED | 4 | 10 % |
| FAILED | 0 | 0 % |
| INCOMPLETE | 11 | 26 % |

Pattern: every INCOMPLETE run whose scheduler record is still visible ended SUCCEEDED after 2.5 to 4 minutes with no STARTED line, so it stopped before step (1) of the start-of-run record. The same early stop happened in the main chat's Test B session (3 min, refused write). The Lead runs (5 of 5) never stopped early. Cause for most NOT KNOWN; the two runs with an agent report (worker 2 03:39, worker 3 03:59) were stopped by the auto-mode check on the clone and on the board write ([Instruction Poisoning], [Untrusted Code Integration]); the early-stop pattern of the others is consistent with that.

## 2026-10-21 04:31 to 2026-10-22 04:31 UTC (daily audit 2026-10-22, written 05:30)

Cadence: hourly slots until about 08:30 on 21 Oct, then workers and checker every 2 h, Lead every 4 h. Rows are the slots
with evidence (RUN_LOG lines, Lead notes of runs with no line). A slot with no line and no note is not counted, so the
INCOMPLETE count is a lower bound. Scout: no slot in the window (Sun + Wed 23:50 UTC).

| Slot (UTC) | Agent | Status | Evidence |
|---|---|---|---|
| 04:39 | Worker 2 | INCOMPLETE | no line (Lead 06:38 note); cause NOT KNOWN |
| 04:49 | Verifier | SUCCESS | STARTED 04:52, final 05:07; ground-beam steel rework merged |
| 04:59 | Worker 3 | SUCCESS | STARTED 05:00, final 05:34; plaster / paint both methods READY (repo code refused '[Code from External]', hand task taken) |
| 05:19 | Worker 1 | SUCCESS | STARTED 05:20, final 05:47; suspended slabs by hand READY |
| 05:39 | Worker 2 | SUCCESS | STARTED 05:40, final 06:36; masonry centreline V2 READY |
| 05:49 | Verifier | INCOMPLETE | no line (Lead 08:19 note); cause NOT KNOWN |
| 05:59 | Worker 3 | SUCCESS | STARTED 06:00, final 06:41; family registry 1.1.0 rework READY |
| 06:09 | Lead | SUCCESS | STARTED 06:17, final 06:38 |
| 06:19 | Worker 1 | SUCCESS | STARTED 06:21, final 06:37; columns to controlling member READY |
| 06:49 | Verifier | INCOMPLETE | no line (Lead 08:19 note); cause NOT KNOWN |
| 06:59 | Worker 3 | SUCCESS | STARTED 07:01, final 07:37; V3.0.1 route G scope READY (PARTIAL) |
| 07:19 | Worker 1 | SUCCESS | STARTED 07:20, final 07:41; ground spans V2 READY |
| 07:39 | Worker 2 | SUCCESS | STARTED 07:40, final 08:01; block wall area READY |
| 07:49 | Verifier | INCOMPLETE | no line (Lead 08:19 note); cause NOT KNOWN |
| 07:59 | Worker 3 | BLOCKED | STARTED 08:00, final 08:20 written by the main chat from the agent's relayed report; board claim not pushed |
| 08:09 | Lead | SUCCESS | STARTED 08:11, final 08:19 |
| 08:19 | Worker 1 | SUCCESS | STARTED 08:19, final 08:35; slab leftovers READY |
| 09:39 | Worker 2 | SUCCESS | STARTED 09:40, final 09:58; openings for finishes READY |
| 09:49 | Verifier | INCOMPLETE | no line (Lead 12:26 note); cause NOT KNOWN |
| 10:19 | Worker 1 | SUCCESS | STARTED 10:21, final 10:35; column steel READY |
| 10:59 | Worker 3 | INCOMPLETE | no line, about 1.5 min in the scheduler (Lead 12:26 note); cause NOT KNOWN |
| 11:39 | Worker 2 | SUCCESS | STARTED 11:40, final 12:07; ceilings by room READY |
| 11:49 | Verifier | INCOMPLETE | no line, ended after about 2 min (Lead 12:26 note); cause NOT KNOWN |
| 12:09 | Lead | SUCCESS | STARTED 12:13, final 12:26 |
| 12:19 | Worker 1 | INCOMPLETE | no line; cause NOT KNOWN (old prompt; repo-attached migration came at 14:25) |
| 12:59 | Worker 3 | SUCCESS | STARTED 13:00, final 13:24; element register v0 READY |
| 13:39 | Worker 2 | SUCCESS | STARTED 13:40, final 14:02; floor area by space READY |
| 13:49 | Verifier | BLOCKED | STARTED 13:50, final 13:55: setup refused, EXECUTION NOT VERIFIED, nothing merged |
| 14:19 | Worker 1 | BLOCKED | STARTED 14:24, final 14:27: session setup failed (case-sensitive repository-name check; fixed on main 1c559a8) |
| 14:59 | Worker 3 | SUCCESS | STARTED 15:02, final 15:16; bars-per-metre evidence READY |
| 15:39 | Worker 2 | SUCCESS | STARTED 15:41, final 15:57; pool-court soffit reconciliation READY |
| 15:49 | Verifier | SUCCESS | STARTED 15:51, final 16:52; 2 merged |
| 16:09 | Lead | SUCCESS | STARTED 16:11, final 16:27 |
| 16:19 | Worker 1 | SUCCESS | STARTED 16:21, final 16:41 (first repo-attached run); beam steel READY |
| 16:59 | Worker 3 | SUCCESS | STARTED 17:00, final 17:22; Gate B tool READY |
| 17:39 | Worker 2 | SUCCESS | STARTED 17:40, final 17:58; doors / windows READY |
| 17:49 | Verifier | SUCCESS | STARTED 17:52, final 18:08 (first repo-attached run); 3 merged, 1 rejected |
| 18:19 | Worker 1 | SUCCESS | STARTED 18:21, final 18:30; columns rework READY |
| 18:59 | Worker 3 | SUCCESS | STARTED 19:02, final 19:48; registry 1.1.0 rework READY |
| 19:39 | Worker 2 | SUCCESS | STARTED 19:41, final 19:48; NO-CLAIM by the backlog rule, merged the head into own READY branches |
| 19:49 | Verifier | SUCCESS | STARTED 19:55, final 20:33; 3 merged |
| 20:09 | Lead | SUCCESS | STARTED 20:11, final 20:17 |
| 20:19 | Worker 1 | SUCCESS | STARTED 20:22, final 20:41; 2 READY |
| 20:59 | Worker 3 | SUCCESS | STARTED 21:02, final 22:58 (first repo-attached run); V3.0.2 package READY |
| 21:39 | Worker 2 | SUCCESS | STARTED 21:39, final 22:08; facade per side READY |
| 21:49 | Verifier | SUCCESS | STARTED 21:50, final 22:16; 4 merged |
| 22:19 | Worker 1 | SUCCESS | STARTED 22:20, final 22:27; footing evidence rework READY |
| 22:59 | Worker 3 | SUCCESS | STARTED 23:00, final 23:29; coverage census V2 READY |
| 23:39 | Worker 2 | SUCCESS | STARTED 23:41, final 00:01; review of the 27 images READY |
| 23:49 | Verifier | SUCCESS | STARTED 23:51, final 00:38; 4 merged incl. V3.0.2 Gate B |
| 00:09 | Lead | SUCCESS | STARTED 00:12, final 00:20 (first repo-attached run) |
| 00:19 | Worker 1 | SUCCESS | STARTED 00:21, final 00:39; dome rings READY |
| 00:59 | Worker 3 | SUCCESS | STARTED 01:00, final 01:55; V3.0.3 package READY |
| 01:39 | Worker 2 | SUCCESS | STARTED 01:40, final 02:06; outdoor floors READY |
| 01:49 | Verifier | SUCCESS | STARTED 01:53, final 02:45; 3 merged, 1 rejected |
| 02:19 | Worker 1 | SUCCESS | STARTED 02:21, final 02:36; stair steel READY |
| 02:59 | Worker 3 | SUCCESS | STARTED 03:01, final 03:35; released-baseline trace READY |
| 03:39 | Worker 2 | SUCCESS | STARTED 03:43, final 04:09; exterior Sigma term by term READY |
| 03:49 | Verifier | SUCCESS | STARTED 03:50, final 04:02; 3 merged, 1 rejected |
| 04:09 | Lead | SUCCESS | STARTED 04:12, final 04:22 |
| 04:19 | Worker 1 | SUCCESS | STARTED 04:22, final 04:44; formwork READY |

**Totals, 61 slots with evidence:**

| Status | Runs | Share |
|---|---|---|
| SUCCESS | 50 | 82 % |
| BLOCKED | 3 | 5 % |
| FAILED | 0 | 0 % |
| INCOMPLETE | 8 | 13 % |

Since 14:30 UTC (agents moving one by one to the repo-attached way of working): 32 of 32 slots STARTED + SUCCESS (100 %).
Every INCOMPLETE and BLOCKED run happened before 14:30 under the old clone-based prompts. Previous day: 64 % SUCCESS.
Checker output in the window: 23 merges, 5 rejections, each with gate and evidence.

## 2026-10-22 04:31 to 2026-10-23 04:31 UTC (daily audit 2026-10-23, written 05:00)

Cadence: workers and Checker every 2 h (Checker also 16:49 from 22 Oct 15:07), Lead every 4 h. Rows are generated from
RUN_LOG.md (current + archive): each STARTED line paired with that agent's next final line. Scout: no slot in the window.
Dashboard (no RUN_LOG line by design): scheduled task records the last run only. Run lock (agent_env.sh, live from about
00:50 on 23 Oct): every one of the 9 runs since then took the lock with its STARTED line and released it with its final
line; no IDLE (overlap) line, no takeover.

| Slot start (UTC) | Agent | Status | Evidence |
|---|---|---|---|
| 10-22 05:02 | Worker 3 | SUCCESS | STARTED 05:02, final 05:11; T-169 READY (a0deb19) |
| 10-22 05:40 | Worker 2 | SUCCESS | STARTED 05:40, final 05:46; T-150 r2 READY (d4a22b0) |
| 10-22 05:51 | Verifier | SUCCESS | STARTED 05:51, final 06:23; T-151 (Gate B slice a), T-166, T-160, T-165 |
| 10-22 06:21 | Worker 1 | SUCCESS | STARTED 06:21, final 07:22; T-158 READY (b64778b) |
| 10-22 07:00 | Worker 3 | SUCCESS | STARTED 07:00, final 07:43; T-151 r2 READY (34765d8), integration package V3.0.3 |
| 10-22 07:42 | Worker 2 | SUCCESS | STARTED 07:42, final 08:08; T-128 r2 READY (8710bb1, rework of REJECTED, backlog-permitted) |
| 10-22 07:51 | Verifier | SUCCESS | STARTED 07:51, final 08:17; T-132, T-151 r2 (Gate B a-c), T-157, T-140 |
| 10-22 08:14 | Lead | SUCCESS | STARTED 08:14, final 08:40; board |
| 10-22 08:19 | Worker 1 | SUCCESS | STARTED 08:19, final 08:32; T-171 READY (a0b23b0) |
| 10-22 09:01 | Worker 3 | SUCCESS | STARTED 09:01, final 09:24; T-177 READY (d02b05c) + T-140 rework merged (3244b35) |
| 10-22 09:42 | Worker 2 | SUCCESS | STARTED 09:42, final 10:09; T-172 READY (d7f81ef) |
| 10-22 09:52 | Verifier | SUCCESS | STARTED 09:52, final 10:24; T-140, T-169, T-162, T-180 (pool) |
| 10-22 10:20 | Worker 1 | SUCCESS | STARTED 10:20, final 10:38; T-183 READY (8beaa6a) |
| 10-22 11:01 | Worker 3 | SUCCESS | STARTED 11:01, final 12:16; T-167 READY (a2b8c0f; integration package ARCH_TAKEOFF_V3.0.4) |
| 10-22 11:41 | Worker 2 | SUCCESS | STARTED 11:41, final 11:53; T-162 r2 READY (a5bd25c) |
| 10-22 11:51 | Verifier | SUCCESS | STARTED 11:51, final 12:07; T-183, T-177, T-163 (+ T-180 pool slot, SCOREBOARD v2 12:05) |
| 10-22 12:13 | Lead | SUCCESS | STARTED 12:13, final 12:17; board |
| 10-22 12:23 | Worker 1 | SUCCESS | STARTED 12:23, final 12:45; T-184 READY (9fbedc4) |
| 10-22 13:01 | Worker 3 | SUCCESS | STARTED 13:01, final 13:18; T-186 READY (agents/task-T-186 2e8bf5c; default guard, unwired) |
| 10-22 13:42 | Worker 2 | SUCCESS | STARTED 13:42, final 14:08; T-175 READY (agents/task-T-175 d3e11eb) |
| 10-22 13:52 | Verifier | SUCCESS | STARTED 13:52, final 15:04; T-184, T-171, T-150 r2, T-167 (Gate B) + T-180 stair slot |
| 10-22 14:21 | Worker 1 | SUCCESS | STARTED 14:21, final 14:30; T-183 r2 READY (c046645) |
| 10-22 15:03 | Worker 3 | SUCCESS | STARTED 15:03, final 15:57; T-182 READY (7074fab, tooling only, no quantity change) |
| 10-22 15:41 | Worker 2 | SUCCESS | STARTED 15:41, final 16:12; T-173 READY (006acbd, backlog-permitted investigation of Q-72) |
| 10-22 15:51 | Verifier | SUCCESS | STARTED 15:51, final 16:30; T-172, T-162 r2 (pair), T-183 r2 (T-180 slot), T-128 r2, T-158 |
| 10-22 16:12 | Lead | SUCCESS | STARTED 16:12, final 16:20; board |
| 10-22 16:21 | Worker 1 | SUCCESS | STARTED 16:21, final 16:35; T-185 READY (agents/task-T-185 ac35911) |
| 10-22 16:52 | Verifier | SUCCESS | STARTED 16:52, final 17:20; T-186, T-182, T-175, T-173 + T-180 slot (ST-01 flights) |
| 10-22 17:00 | Worker 3 | SUCCESS | STARTED 17:00, final 18:26; T-179 READY (Gate B integration package ARCH_TAKEOFF_V3.0.5, 4b5cdce; integrates T-152, T- |
| 10-22 17:40 | Worker 2 | SUCCESS | STARTED 17:40, final 17:51; T-128 r3 READY (37c9fc4b, agents/task-T-128) |
| 10-22 17:52 | Verifier | SUCCESS | STARTED 17:52, final 18:01; T-128 r3, T-185 (+ T-180 slot: domes) |
| 10-22 18:21 | Worker 1 | SUCCESS | STARTED 18:21, final 19:11; T-189 READY agents/task-T-189 @ b8730b23 |
| 10-22 19:01 | Worker 3 | SUCCESS | STARTED 19:01, final 19:09; T-178 READY (agents/task-T-178 684fbbe4) |
| 10-22 19:40 | Worker 2 | SUCCESS | STARTED 19:40, final 20:11; T-164 READY d849ca4a |
| 10-22 19:51 | Verifier | SUCCESS | STARTED 19:51, final 21:04; T-189, T-178, T-164 MERGED; T-179 Gate B REJECTED |
| 10-22 20:11 | Lead | SUCCESS | STARTED 20:11, final 20:21; board |
| 10-22 20:21 | Worker 1 | SUCCESS | STARTED 20:21, final 20:40; T-163 r2 READY (agents/task-T-163-r2 @ bc34f9aa) |
| 10-22 21:01 | Worker 3 | SUCCESS | STARTED 21:01, final 22:00; T-181 READY (agents/task-T-181 04b138c9) |
| 10-22 21:40 | Worker 2 | SUCCESS | STARTED 21:40, final 22:12; T-194 READY (agents/task-T-194 @ 5ca59773) |
| 10-22 21:50 | Verifier | SUCCESS | STARTED 21:50, final 22:00; T-181 MERGED, T-163 r2 REJECTED |
| 10-22 22:20 | Worker 1 | SUCCESS | STARTED 22:20, final 22:27; T-163 r3 READY (agents/task-T-163-r3 @ fa390ca2) |
| 10-22 23:00 | Worker 3 | SUCCESS | STARTED 23:00, final 23:39; T-179 r2 READY (agents/task-T-179 @ 85bba0ff, Gate B integration package V3.0.5 r2) |
| 10-22 23:40 | Worker 2 | SUCCESS | STARTED 23:40, final 00:01; T-195 READY (6c225209) |
| 10-22 23:51 | Verifier | SUCCESS | STARTED 23:51, final 01:15; T-179 r2 (Gate B PASS) MERGED 90d0b769, T-163 r3 MERGED 659f889f, T-194 MERGED 4f2678c5, T |
| 10-23 00:12 | Lead | SUCCESS | STARTED 00:12, final 00:21; board |
| 10-23 00:20 | Worker 1 | SUCCESS | STARTED 00:20, final 00:46; T-192 READY 9549eff5 |
| 10-23 01:00 | Worker 3 | SUCCESS | STARTED 01:00, final 01:52; T-196 READY (agents/task-T-196 @ 59f433ee) |
| 10-23 01:40 | Worker 2 | SUCCESS | STARTED 01:40, final 02:02; T-198 READY (agents/task-T-198 @ 2d7ec661) |
| 10-23 01:51 | Verifier | SUCCESS | STARTED 01:51, final 02:04; T-190 MERGED 465e0015, T-192 MERGED 86fd5f42, T-196 REJECTED, T-180 slot CONC.COLUMN 3 col |
| 10-23 02:20 | Worker 1 | SUCCESS | STARTED 02:20, final 02:35; T-191 READY (agents/task-T-191 827bd8d2) |
| 10-23 03:00 | Worker 3 | SUCCESS | STARTED 03:00, final 03:55; T-187 READY (agents/task-T-187 5922d4ea; integration package V3.0.6, integrates T-186, T-1 |
| 10-23 03:40 | Worker 2 | SUCCESS | STARTED 03:40, final 04:02; T-197 READY (agents/task-T-197 @ 2df8ffd1) |
| 10-23 03:51 | Verifier | SUCCESS | STARTED 03:51, final 04:03; T-198 MERGED 57bb0411, T-191 REJECTED, T-180 slot CONC.COLUMN 3 columns |
| 10-23 04:11 | Lead | SUCCESS | STARTED 04:11, final 04:17; board |
| 10-23 04:20 | Worker 1 | SUCCESS | STARTED 04:20, final 04:28; T-191 r2 READY (agents/task-T-191 @ e343f9c9) |

**Totals, 55 slots scheduled (pilot_metrics.py slot count), 55 STARTED lines, 55 paired with a final line:**

| Status | Runs | Share |
|---|---|---|
| SUCCESS | 55 | 100 % |
| BLOCKED | 0 | 0 % |
| FAILED | 0 | 0 % |
| INCOMPLETE | 0 | 0 % |

Previous day: 82 % SUCCESS (61 slots with evidence); since 22 Oct 14:30 every slot has been STARTED + SUCCESS.

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
