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
