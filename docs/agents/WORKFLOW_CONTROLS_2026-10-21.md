# Workflow controls (owner approval, 2026-10-21)

Owner approved these controls in his main chat on 2026-10-21. They bind every agent from their next run, with or
without a prompt change; where an older line in TEAM.md, PLAN.md or a prompt disagrees, this file wins. The team stays
at eight agents on the existing schedules. The released default stays ARCH_TAKEOFF_V2.9 + route G until the owner
authorises a switch. Frozen methods and the owner's manual methods are never edited in place.

## 1. Two verification gates (Checker)

**Gate A: single pieces.** Before integration, the Checker independently verifies each READY task's engineering
calculations and drawing interpretations (re-measure from the drawing; never take the worker's number as the expected
value). Existing MISSION.md gates still apply.

**Gate B: the integrated V3.0 BOQ.** After Worker 3 sets an integration package READY (Trade column `lane I` and the
words "integration package"), the Checker verifies the complete V3.0 output:

1. Automated first: freeze check (0 differing), regression tests at the level `impact` gives, duplicate-ownership
   check, coverage census, and a line-by-line before / after BOQ diff of V3.0 against the previous V3.0 and against
   V2.9 + route G.
2. Automated checks passing is not enough. Then independent hand spot-checks, by these rules:
   - **Always checked by hand** (no sampling): every line that is at least 2 % of its trade total; every line that
     moved at least 5 % against the previous V3.0 or V2.9; every new calculation method; every missing or newly
     introduced BOQ scope; every unit conversion and dimensional assumption; every structural safety-relevant element
     (footings, columns, beams, slabs, stairs, retaining / pool / tank walls, reinforcement); every cross-trade
     dependency or possible double count; every material classification change.
   - **Plus 2 random lines** per package from the remaining lines. Reproducible selection: sort the remaining line ids
     ascending; take the first 8 hex characters of the package's merge-candidate commit sha as a number N; pick
     positions N mod L and (N div L) mod L (L = number of remaining lines; if both land on the same line, take the next
     one). Record the sha, L and the two line ids in the verdict.
   - **Discrepancy:** hand vs engine differs by more than 1 % on a line -> investigate; that line and every quantity
     depending on it become HELD. Hold the whole package only when the cause may affect other lines or cannot be
     isolated safely. A difference of 1 % or less is not proof of correctness; the verdict says what was checked.
   - Unverified quantities are never released. A material discrepancy goes into the Checker's final RUN_LOG line and
     the MAIN daily update.
3. Thresholds 2 % / 5 % / 1 % are initial operational values. The Checker records, per package, how many lines each
   rule caught and how many real defects it found, so the owner can review the thresholds with actual results.

**Priority between queues.** A READY integration package may go ahead of Gate A tasks, but a critical Gate A task
(gate 0-1, a structural safety element, or one that blocks integration) is never delayed more than 2 Checker runs. The
Lead orders both queues by engineering risk, dependencies and delivery impact in its VERIFIER QUEUE note.

## 2. Element register (Lead)

The Lead owns the shared project element register: element definitions, drawing references, cross-trade ownership and
conflicts between trades. Worker 3 builds and maintains the supporting tools (T-134). The register grows incrementally:
each Lead run adds or settles the elements touched by CLAIMED and READY tasks first. The register never stops other
work. When two tasks measure the same element for different trades, the Lead names the owner trade in the register and
in both task rows before either is merged.

## 3. Checker backlog

Target: at most 3 READY. While READY is above 3:

- Workers do not hand in new standalone READY pieces.
- Workers may: correct REJECTED work, improve the evidence of their own READY tasks, build unblocked infrastructure,
  resolve integration dependencies, and work tasks the Lead marks "backlog-permitted".
- The Lead tags every READY row with its delay cause: CHECKER-RUNS (Checker runs failing or silent), CAPACITY (Checker
  ran but had no time), EVIDENCE (incomplete evidence), OVERSIZED (too large for one Checker run). OVERSIZED tasks are
  split into checkable parts.
- First lever: restoring reliable Checker execution (repository-attached migration, section 7), before any change in
  its capacity.

## 4. Approved fallbacks

A fallback is permitted only when it is explicitly recorded in an answered owner decision (OWNER_QUESTIONS_ANSWERED.md)
or the approved owner rule library. A quantity using it is marked **ASSUMED — OWNER-APPROVED** with a link to that
source. It stays distinguishable from drawing-confirmed and independently verified quantities. The owner's manual
method is never silently replaced. With no approved fallback and no adequate drawing evidence, the affected quantity is
HELD. No arbitrary assumptions are authorised. Agents do not ask the owner to repeat a rule that is already answered:
they search OWNER_QUESTIONS_ANSWERED.md and the rule library first.

## 5. Standard statuses

Evidence status (one per quantity):

| Status | Meaning |
|---|---|
| VERIFIED | independently checked, with documented evidence and scope |
| DRAWING-CONFIRMED | supported by drawing evidence, not yet independently verified |
| ASSUMED — OWNER-APPROVED | uses an explicitly approved fallback with its source; stays visible even after an independent check |
| HELD | known item intentionally withheld because a material issue is unresolved |
| UNKNOWN | scope or quantity cannot yet be established reliably |

Release status is separate (RELEASED / NOT RELEASED). A VERIFIED quantity is not automatically RELEASED; only the owner
releases. Totals report each evidence status separately; HELD and UNKNOWN never count as zero or as correct.

## 6. Dashboard indicators

The Dashboard reports five indicators, each from its own source, and shows **NOT YET MEASURED** wherever the
supporting evidence is unavailable (never an estimate):

1. BOQ coverage (SCOREBOARD v2, T-132)
2. Independent verification share (SCOREBOARD v2: VERIFIED share by trade and unit)
3. Integration into V3.0 (board: integration packages merged, lines added, Gate B results)
4. Unresolved scope (HELD + UNKNOWN by trade, with units)
5. Autonomous run reliability (RUN_LEDGER: STARTED + final status per agent, last 48 h)

## 7. Migration to the repository-attached setup

Order: Worker 1 -> Checker -> Worker 3 -> Lead -> Worker 2 -> Dashboard. The Scout and MAIN do not migrate. The next
agent moves only after the previous one shows a successful unattended run with a STARTED line and a final status line
on the board. Each agent's prompt is updated to these controls when it migrates. The main chat records each migration
in OWNER_SESSION_CHANGES.md and reports failures to the owner.

## 8. Project photos as evidence (owner, main chat, 2026-10-21 22:55)

Owner: "from now on I'll try to always send photos of the project, so that you can assign an agent to look at the photos
to give details and align what's in the plan with the photos." No new agent: photo review is a normal board task.

- WHERE: the owner puts photos on Drive in the project's folder (preferably a "Photos" subfolder, named by area or
  elevation when he can). Drive stays READ-ONLY. Photos are private client data: they are never copied into the
  repository, its commits, branches, tests, board text or any dashboard; the board refers to a photo only by its Drive
  folder and file title and DESCRIBES what it shows.
- WHO: the Lead, each run, searches the project's Drive folder for photos created since its last run; for each new batch
  it adds one PHOTO REVIEW task (lane A, or lane S when the photos show structure), backlog-permitted. A worker does the
  review; the Checker verifies it under Gate A (re-looks at the photos the task cites).
- WHAT a photo review delivers: per photo, what it shows (element, location, orientation), and a table photo -> plan
  element (element register id where one exists) with one of: AGREES with the drawing; DIFFERS (what, where, how much it
  could change which BOQ line); NOT IN THE DRAWING (an element the photo shows that the drawings do not); NOT VISIBLE.
  It names the BOQ lines each finding affects, with units.
- WHAT a photo may and may not do: a photo corroborates or questions the drawings; it never produces a quantity on its
  own and never silently changes one (dimensions are not scaled off photos). Drawing-first still governs (UP-STAIR-002,
  MISSION.md). A DIFFERS or NOT IN THE DRAWING finding that affects a quantity makes that line HELD with the finding as
  its cause, and goes to the owner (via the main chat's daily package) or the designer list, never guessed. Evidence
  statuses stay those of section 5; a photo is recorded as supporting evidence beside the status, not as a new status.
- The owner's photos of 2026-10-21 (domes): the first photo review; the owner says the chalet has no domes.
