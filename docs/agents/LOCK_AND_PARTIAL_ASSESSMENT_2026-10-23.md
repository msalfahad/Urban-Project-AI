# Lock ownership safety and verified partial quantities: assessment (owner request 2026-10-23 21:00)

Written by the owner's main chat (auditor). Nothing implemented: the owner asked for the assessment first. No engine,
rule, quantity or schedule change.

## 1. Lock ownership: what the current code does (probe, `dashboard/lock_probe_2026-10-23.sh`, main ccbe7876)

The probe runs the current `scripts/agent_env.sh` against a local copy of the board (copied locks cleared); it never
writes to the real board or engine branch.

| Case | Expected | Actual today | Result |
|---|---|---|---|
| L1 lock past its TTL, not taken over; the holder commits a verdict | refused | published | FAIL |
| L2a lock taken over by a new run; the old run commits a verdict | refused | refused ('run lock lost') | PASS |
| L2b same; the old run pushes a merge to the engine branch | refused | pushed (the merge push is a plain `git push`, no lock check) | FAIL |
| L3 lock valid but 1 minute from expiry; the holder commits a verdict | refused (no safety margin) | published | FAIL |

Causes: `require_lock` compares the token only (no expiry, no margin); the Checker prompt's step 7 pushes the merge with a
raw `git -C .work/engine push`, which never calls `require_lock`.

## 2. Proposed minimal isolated fix (scripts/agent_env.sh on main + one Checker prompt line)

1. `require_lock` also reads `since_epoch` and `ttl_min` from the REMOTE lock (fetched fresh, as now) and refuses unless
   the token matches AND at least 10 minutes of validity remain ('run lock expired or within 10 min of expiry; publish
   nothing; end INCOMPLETE'). The 10-minute margin is what makes the check safe: a takeover is only possible after expiry,
   so a check that passes guarantees no other run can own the lock for the next 10 minutes, far longer than a push.
2. New subcommand `engine push`: `require_lock`, then `git push origin HEAD:<engine branch>` (never force, fixed branch),
   then re-read the lock; a loss detected after the push is logged as an INCIDENT line (should be impossible inside the
   margin). The Checker prompt step 7 uses `bash scripts/agent_env.sh engine push` instead of the raw push.
3. Board verdict publication already goes through `board commit` -> `require_lock`, so (1) covers stale verdicts.
4. Tests: `scripts/test_agent_env_runlock.sh` keeps its 6 cases and adds L1, L2b, L3 (refused), a valid holder publishing
   and pushing (allowed), expiry during a long run (refused at the next publish), a takeover between two publishes (second
   refused), and the INCIDENT path.

Scope: about 40 lines in one file, no new dependency, no permission widening (the new subcommand is narrower than the raw
push it replaces).

## 3. Objections and alternatives

- Check-then-push is not atomic. The margin bounds the window to a guaranteed-safe 10 minutes. A fully atomic alternative
  exists: engine and board are branches of the same repository and worktrees of one clone, so `git push --atomic` can push
  the merge together with a lock-witness commit on agents/control; any lock change rejects both. It costs a retry loop
  (the board is busy). I recommend the margin fix now and the atomic push only if an incident ever shows the need.
- Clock skew between containers: lock times come from different machines; the 10-minute margin also covers skew of
  minutes.
- The expiry check applies to every agent: a worker run longer than its TTL loses its hand-in commit. That is the TTL's
  intent, but work can be lost; the run writes INCOMPLETE and the next run picks the task up.
- Deployment timing: a change to agent_env.sh takes effect at each run's next call, so in-flight runs may switch mid-run.
  Deploy between Checker runs (just after a Checker final line) and re-run the full lock test on main first.
- The 110-minute rule stays as guidance; this fix is the enforcement.

## 4. Verified partial quantities (footing line)

Checker verdict 20:14 (T-233): 26 outlines re-measured; 25 footings 64.304 m3 VERIFIED as a component; F10 + F HELD
2.176 .. 2.275 (Q-31 C); the reference line CONC.FOOTING stays PARTIALLY VERIFIED (also straps SB3 D-15, boundary band C1
Q-28 A).

Independent check by the main chat (2026-10-23 21:10): the printed footing schedule on structural PDF sheet 9 (a plot, read
visually; independent of the DXF conversion both the engine and the Checker read) gives L x B x H for every type. With the
Checker's population (F 4, F2-F5 2 each, F6 F8 F9 F11-F15 FF 1 each, FN 4 with one notched to 0.86 m2) it reproduces
64.304 m3 exactly. The sizes are therefore confirmed from two independent sources. The POPULATION (which tag sits on which
outline) still rests on the DXF only; a tag count on the PDF foundation plan would make it independent too (proposed for
the Checker's next footing touch or T-236).

Coverage: every type in the schedule (17 rows; F7 unused) is accounted for (16 types on 26 outlines). That does not show
that no untagged footing or footing-like element exists elsewhere (boundary band C1, lift footing FF counted here, lift
pit by T-204). The blinding figure 15.179 m3 is the footing-blinding subset only: 14.990 inside the plot VERIFIED, 0.189
beyond the plot HELD (D-14); strap blinding 0.913 (D-15), ground-beam blinding (Q-21 C) and F10 + F blinding are outside it.

Gap found: the candidate's F10 line is a bounded range 0.216 .. 1.960 m3 that EXCLUDES both drawn readings (2.176 drawn
outline, 2.275 schedule rows F10 + F); the Checker noted it for lane I, and no board row carries it yet. An export would
show a HELD range that does not contain the plausible values.

Consultant items, can the drawings answer? D-32 was answered from the drawing (FN against F9). F10 + F: three readings
(drawn outline 4.55 m2, schedule F10 280 x 140 + F 90 x 80 = 4.64 m2, no combined-footing remark) disagree, so the drawings
cannot pick; it stays a designer item (Q-31 C provisional rule stands). Band C1 (Q-28): the overlap length with footing
outlines can be measured from the plan; whether the beam is cast with the footing needs a section. A drawing search
(foundation plan + p.13 details) should narrow it before escalation. D-14 (blinding past the plot line), D-15 (blinding
under straps) and Q-21 C (formation arrangement) are not answerable from the existing sheets (the drawings are silent or
the question is construction practice).

## 5. Footing population from the PDF, F10 readings and blinding reconciliation (owner 2026-10-23 21:30)

PDF foundation plan (ST sheet 2, a plot, read visually by the main chat; independent of the DXF): footing tags F 4
(two on the street side, two on the south boundary), F2 2, F3 2, F4 2, F5 2, F6, F8, F9, F11, F12, F13, F14, F15, FF 1 each,
FN 4 (three free-standing, one on the east boundary) = 25, plus ONE outline at the south-east corner carrying two tags
(F10 with C10 and F with C). F7 is not on the plan (unused in the schedule). Total 26 outlines: equal to the Checker's
DXF table. Columns marked CN on F4 and F8 sit on those footings (no FN of their own). The population is now confirmed from
two independent sources; sizes from the printed schedule (section 4); the footing component 64.304 m3 is reproduced from
the PDF alone.

F10 + F: one outline, two tags. Readings: (a) schedule rows as two pads 2.80 x 1.40 x 0.50 + 0.90 x 0.80 x 0.30 = 1.960 +
0.216 = 2.176 m3; (b) the drawn outline 3.25 x 1.40 at the F10 depth 0.50 = 2.275 m3. The candidate's range 0.216 .. 1.960
is F alone .. F10 alone and contains neither reading (cause: one tag per outline). T-239 corrects it to a CONFLICT 2.176
.. 2.275, HELD (Q-31 C).

| Blinding scope | Quantity (m3) | Status | Overlap rule | Double-count check |
|---|---|---|---|---|
| 25 footings, inside the plot | 14.990 | VERIFIED (Checker 20:14) | union of outlines + 0.10 (FN / F9 overlap 0.196 m2 once) | one layer, counted once |
| 25 footings, projection beyond the plot line (8 footings on it) | 0 .. 0.189 | HELD (D-14) | same union, clipped by the plot polyline | inside the 15.179 candidate figure, not added elsewhere |
| F10 + F | 0.552 (outline + 0.10) .. 0.590 (two pads + 0.10), before the D-14 clip | HELD (Q-31 C, T-239) | follows its footing | candidate excludes it; released V2.9 carries 0.480 (F10 alone): reported, not changed |
| Ground beams | 5.534 (union: none under footing blinding) .. 9.691 (own layer, also over 41.57 m2 of footing blinding) | HELD (Q-21 C) | the 41.57 m2 is exactly the double-count question | reading L excludes the overlap, reading R bills a second layer by the beam detail; never mixed |
| Straps SB1 / SB2 / SB3 | 0.913 ((B + 0.20) x clear length 4.55 / 2.294 / 3.259 m) | HELD (D-15) | clear length between footings | no overlap with the footing layer by construction; re-check the clear lengths against T-230 strap ends |
| Boundary-wall bases (band C1) | not measured | UNMEASURED (Q-28 A, count not printed) | - | must be an export row, never omitted |
| Pool | with the pool line | owned by the pool line | - | not in the footing or beam layers |

Freelancer 47.055 m3 is one plate under the whole plot (15.00 x 31.37 x 0.10); no sheet draws it; comparison only.

## 6. Lock-safety fix: as deployed (main eafbb0f6, 2026-10-23 21:2x, after the Checker run ended 21:11 and before the 21:49 run)

Changed files on main: `scripts/agent_env.sh`, `scripts/test_agent_env_runlock.sh`, `CLAUDE.md`, `.claude/settings.json`.
Checker prompt step 7: merges are published only with `bash scripts/agent_env.sh engine push`. No engine, rule, quantity,
V2.9 or schedule file changed; freeze check on the working head 63f4d90: 0 differing.

Guarded publication paths: `board commit` (verdicts; lock re-checked before every push and again by the pre-push hook at
push time), `board log` final lines (SUCCESS refused once the lock is lost or expired), `task`, `engine push`, and raw
`git push` of the engine branch, of `agents/task-*`, and of `agents/control` by a session that held a lock (pre-push hook).
Denied in settings: `--no-verify`, `core.hooksPath`, the internal-push marker, GitHub write tools.

Tests (complete runs): `scripts/test_agent_env_runlock.sh` ALL PASSED (the 6 original cases + hook install + 7 new:
valid publication; replaced ownership on verdict, engine push, raw engine push, raw task push and SUCCESS line; near-expiry
margin; expiry during a long run; takeover between publications; a 25-second pause after the lock check during which the
lock is taken over, for engine push and for a board verdict; a session with no lock record). `scripts/test_agent_env_autosetup.sh`
ALL PASSED. A first run found a real defect (the hook was written relative to the caller's directory); fixed with an
absolute path and a test that the hook is written inside the checkout.

Residual risks (not removed by this fix):
1. Not atomic: between the hook's check and the server accepting the ref there is a window of the push itself. The
   10-minute margin (1 minute for board pushes) makes a takeover inside it impossible unless the push takes longer than
   the margin or clocks differ by more than that. It is a margin, not a fence.
2. Client-side only: an agent that deliberately bypasses the script (a fresh clone, an edited hook, the internal-push
   marker, a GitHub API write) is stopped only by permission rules and its prompt, not by the server.
3. GitHub tools: the deny rules cover the known write tools by name; a new tool name would not be covered.
Smallest reliable fence (recommended next): server-side. Either (a) an atomic two-ref push (`git push --atomic` of the
engine ref together with a lock-witness commit on agents/control that fast-forwards only if the lock file is unchanged), so
any lock change rejects the merge; or (b) a GitHub branch rule on the engine branch allowing pushes only from a single
merge path. (a) is a contained change in agent_env.sh; (b) needs the owner's repository settings.
