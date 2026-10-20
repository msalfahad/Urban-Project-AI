# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Recurring causes (lead 2026-10-20 10:20)

1. **Merged pieces not wired into the released run** (still the main reason released numbers do not move): beam fix,
   typed drawing values, plot-edge members, tile count, room levels / wall heights are merged but read by no released
   method; released concrete 92.77 vs 111.81 m3 unchanged since 2026-10-19. Decision: wiring chain T-105 (carries the
   rejected T-097 ledger V3 and T-056 stairs) -> T-101 (typed values, queued); plaster / paint T-095 after the owner's
   height answers (T-096 now merged).
7. **New modules trip whole-repo guard tests that the task's own tests do not run** (new 10:20): T-097 and T-056 both
   passed their own and L2 / L3 tests but each failed the rebar-firewall declaration test in the L4 suite (any engine
   module mentioning rebar / reinforcement must be declared). Decision: T-105 fixes both; every new-module task row from
   now on adds "run tests/structural_comparison_engine/test_rebar_product_firewall.py" to its acceptance check.
2. **A new ledger version inherits the holds of the one under it**: T-097 V3 carries the V2 holds (footing band Q-28 A
   provisional, pool), so its compared concrete shrinks to stairs + domes (12.01 vs 21.83 m3) and its released total over
   all keys drops 236.27 -> 229.57 m3 while beams rise +4.02 m3. Decision: every ledger handoff states released and held
   m3 per key against the RELEASED route, not only against the previous ledger; T-101 checks it.
3. **Drawings that contradict themselves block whole lines** (new, structural): 18 beam pieces (4.25 - 9.18 m3) keep the
   beam line uncompared. Decision: printed section cuts first (T-102), the rest to the owner (Q-61).
4. **Execution refusals at random** (unchanged): since 06:20, 3 of 6 code runs refused (worker 2 07:06 venv, 07:43 clone;
   verifier 07:58 install), one worker run left no line (worker 1 06:19). Decision: three READY tasks ordered for the next
   verifier run with execution; BOARD.md cut from 375 KB to 80 KB so a refused run can still claim or log through the
   connector; owner setting still under NEEDS FIXING.
5. **Trades never started**: blockwork (old estimate about 140 m short, -36.5 %) and blinding (22.16 vs 47.06 m3) had no
   task. Decision: T-027 + T-103 (blockwork, heights Q-60), T-100 (blinding by hand).
6. **Offcut reuse and heights still need rules**: Q-52 to Q-59 open (membrane 1 roll, tiles 15 - 20 %, plaster 1151.14 /
   paint 1191.13 m2 held).

8. **Hand results that cannot reach a branch** (new 14:20): T-107's evidence was refused when written to a task branch
   ("[Sensitive-Source Provenance]"), so its handoff exists only as board text; worker 3's 12:59 run left no line and no
   commit. Decision: board-only handoffs are verified as hand evidence (the verifier re-reads the cited notes), and the
   next task on the topic writes the files (T-117); a run with no line stays a NEEDS FIXING item for the owner's setting.

## 2026-10-20 16:20 (lead run)

- **T-114 2F roof trim proof and pantry cutting plan: WORKED (MERGED 8c23eea, verifier re-measured the roof on the DXF).**
  Under your Q-58 A the 0.70 x 6.97 m side trim covers the 0.30 x 4.60 m step band: 17 rolls PROVEN on the second-floor
  roof (strict layout 18), but only with strips stopping at the opening edge and 16 flap pieces from the same roof's roll
  ends; pantry 2 rolls, so wet areas 19 -> 21. Engine V2.12 shows 17 / 18 = hand. Went well: every piece dimensioned
  (254 rows), separate re-measure by the verifier. Wrong: nothing; the 0.05 m start offset it recommends has no rule (not
  adopted). Decision: T-120 builds the release version, opt-in until you confirm the reconciliation.
- **T-116 stair openings and stair wells out of a room floor: WORKED, pending verification (READY 15:20; verifier 15:52
  refused execution).** 1F living porcelain released 44.869 m2 -> 38.459 .. 38.979 m2 HELD range (hand 38.588 .. 38.990,
  freelancer 38.96 inside); each deducted piece = hand to 0.01 m2; winder-step defect (0.296 m2) fixed; 24 other floor
  lines unchanged. New small closed element 0.1175 m2 beside the round-stair arrival (designer D-23). Decision: verifier
  checks it first at the next run with execution; the landing finish stays on Q-66.
- **T-109 open-air passage walls in the GF facade run: WORKED, pending verification (READY 15:56).** New piece 105.887 m
  vs released 98.887 m (+7.000 m) = the verifier's hand; the two passage "openings" are not building openings (2 -> 0).
  New finding: the first floor covers 4.08 of the passage's 5.64 m2 (a bathroom and a bedroom corner over outside air):
  soffit and slab over open air not measured anywhere. Decision: T-121 (census of every slab over outside air, NO REPO
  CODE), missing-scope M-07; verifier checks T-109 after T-116.
- **T-107 block type per wall: verifier REJECTED 15:10 (part 1 not done, no branch).** The hand typing (white 141.31 /
  black 136.00 m ASSUMED, black 57.54 m by the note, 125.35 m held) is kept as hand evidence. Decision: already reworked
  as T-117 (claimed 16:01 by worker 3); T-108 now waits on T-117 instead of T-107. No new cause.
- **Worker 2 (two runs): FAILED / no line.** 14:39 run left no RUN_LOG line and no commit; 15:39 run: venv refused
  ("[Untrusted Code Integration]") and the claim commit refused, so T-117 stayed free (worker 3 took it). Verifier 15:49:
  venv, codemap and freeze refused ("[Code from External]"). Recurring cause 4 / 8 unchanged: 3 of 7 runs in this window
  could not run code. Decision: enough NO REPO CODE rows on the board (T-110, T-111, T-119, T-121); the owner setting stays
  under NEEDS FIXING.

## 2026-10-20 14:20 (lead run)

- **T-112 wall heights by both methods: WORKED (READY 9e10d0d, not verified; came in during this run).** 32 rooms. Owner
  method on 4 dry rooms with verified datums 234.17 vs freelancer 258.40 m2 (-9.4 %; same-wall rooms -1.5 %, his flat 3.40
  vs 3.35); annex 102.78 vs 117.00 m2 not releasable (Q-54 B: +4.30 reads as a finished roof); every drawing-derived height
  HELD (no ceiling plane printed). Where the owner line meets a deeper beam (GF open room / pantry 0.10 m into B26 / B27;
  wash lobby, 1F bed room 380 x 430, dewaneya at the beam soffit) it is a method difference reported to the owner, not
  decided. Decision: designer rows D-17..D-22; the owner sees the four beam places in the report (his reconciliation is
  pending); closed wall runs of 7 dry rooms become a task when the board has room.
- **T-100 blinding and columns by hand: WORKED, MERGED 5fe31ca (14:05).** Blinding hand range 20.71-26.37 m3, engine
  22.155 inside it; freelancer 47.055 = one 15.00 x 31.37 x 0.10 plate under the whole plot, drawn nowhere: -24.90 m3
  (-52.9 %) is his basis (ENGINE_RIGHT on basis). Columns at the storey interval 34.446 vs engine 36.711 (-6.2 %: engine
  counts 5 columns the roof-slab plans do not draw, +2.268 m3) vs freelancer 28.547 (his 3.75 / 3.45 heights). What went
  wrong: the handoff says no Urban rule covers column height; URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 does (interval
  minus the deepest member framing into that column). Decision: T-119 (columns by that rule, column by column; no owner
  question needed); T-101 acceptance adds F10 blinding HELD and the 5 undrawn columns NOT_PRESENT; the other two cases
  (blinding past the plot line 0.189 m3, strap blinding 0.913 m3) and C8 30X80 vs 30 x 90 are designer rows D-14..D-16.
- **T-113 1F living traced: WORKED, MERGED c1f0467 (14:05).** Engine 44.869 vs hand 38.588 m2 (+6.281, +16.3 %) explained
  to 0.0001 m2: stair-opening and stair-well residues 4.635, round-stair quarter landing 1.353, tread-clipping defect
  0.296; freelancer 38.96 = hand 38.990 (-0.1 %). Decision: T-116 (general fix, new piece); the 0.4025 m2 flight foot is
  designer D-13; the landing finish conflicts between owner Q-56 A (porcelain PROVISIONAL) and UP-STAIR-005 (landing
  marble) -> owner Q-66.
- **T-016b, T-014, T-027, T-104: WORKED, MERGED 13:25 (head 60f1d8d).** GF facade passage: verifier read the drawing,
  HAND_RIGHT (98.887 vs 105.887 m, -6.6 %); T-014's "GF established" withdrawn (both readers bridged the passage mouth by
  width alone). Decision: T-109 promoted to TODO; the 0.10 m notch is owner Q-64 (verifier), carried as a range.
- **T-106 skirting audit: WORKED (READY 696b29d, not verified).** All 28 nets right; 20 lines leave 17.035 m unlisted (the
  F-17 window-frame credit); same on the synthetic villas, so general. Engine gross 262.56 vs freelancer 282.85 m (-7.2 %),
  certain net 185.52 m: RULE_DIFFERENCE (he deducts no door; UP-CER-003). Decision: T-118 queued (listing fix after merge).
- **T-107 block type per wall: PARTIAL (READY, board-only).** No architectural sheet names a block type; structural notes
  do (neighbour-side ground beams black, walls with columns at column thickness). 93 runs typed: white ASSUMED 141.31 m,
  black ASSUMED 136.00 m, black PROVISIONAL 57.54 m, HELD 125.35 m; new scope M-05 (substructure black block 2 x 31.17 m).
  What went wrong: part 1 (code vs hand table) not done, freeze check and branch write refused. No-assumption check:
  fallback values marked ASSUMED, parapets / fence held and asked (Q-65): passes. Decision: T-117 (part 1, D-12 thickness
  conflicts, and the evidence files).

## 2026-10-20 12:20 (lead run)

- **T-103 blockwork metres by hand: WORKED, MERGED 79bd397.** Hand centreline minus columns GF 143.16 / 1F 120.75 /
  2F 39.78 m vs freelancer 134.28 / 120.31 / 39.10 m = +6.6 / +0.4 / +1.7 % (the handoff gave -6.2 / -0.4 / -1.7 %, the
  opposite sign; corrected on the row, auditor 10:29). Parapets 108.55 vs 108.85 m; fence 46.37 vs 37.20 m (no sea-side
  row in his BOQ). No-assumption check: passes (block m2 / m3 HELD on Q-60, now answered A). Decision: T-107 (engine piece
  vs this table, block type per wall from the notes), T-108 queued (block m2 / m3 / counts).
- **T-099, T-016a, T-091: WORKED, MERGED 677c740 / aee6803 / 6319aca** (classified at 10:20; verifier reproduced the
  census and the OP-010 reading on the Drive DXF). Decision: none new.
- **T-027 masonry centreline piece: PARTIAL (READY 1c9cb52, NOT VERIFIED).** Synthetic villas = hand (SV-A 54.60 m vs
  the V2.9 face run 44.40, -18.7 %); Alsenan metres not measured: the DXF decode was refused "[PII Data Handling]".
  Cause: one refused step, not the method. Decision: the Alsenan acceptance line moves to T-107 (TODO, with a hand
  fallback); the verifier judges the piece on its fixtures.
- **T-016b V2.8 -> V2.9, 14 changes by hand: WORKED (READY 98cf0ec, NOT VERIFIED).** 12 VERIFIED, 2 CONTRADICTED: GF
  facade run engine 98.887 vs hand 105.787 m (-6.5 %: a 1.20 m open-air side passage at +0.15 is bridged, +7.000 m;
  a reveal pocket -0.100 m) and the 1F curved-window hold reason (sill on the 1F floor; source trail cites another
  window). Decision: verifier settles the passage first; T-109 queued; trail defect in Later.
- **T-014 facade gaps (FACADE_GAP_CLOSURE_V1): PARTIAL (READY 0ecef42, NOT VERIFIED).** 1F 63.169 -> 63.009 m
  (-0.160 m, -0.25 %) = hand = independent reader; 39 tests. But it disagrees with T-016b on the GF: its reader
  "establishes" 98.887 m and keeps the 0.10 m pocket, where T-016b's hand reading gives 105.787 m and -0.100 m. Cause:
  both readers walk the same drawn lines, so they share the passage blind spot (directive Part 4 (6)). Decision: the
  question is put on both rows for the verifier, who reads sheet 03 himself; no owner question (a drawing reading).
- **T-104 membrane strips in every wall frame (MEMBRANE_FOLD_V4): WORKED on the worker's evidence (READY 17f27d6,
  not verified).** Wedge W.C. 5.95 -> 5.45 m = hand; 17 wet areas 19 rolls unchanged, 122.55 m (hand 122.50); 2F roof
  HELD 17 / 18 unchanged; a V3 patch-sizing tail (+1 roll in one unused layout) corrected inside V4. Decision: verifier
  after the other three; wiring with the next ARCH_TAKEOFF version.
- **Verifier 11:53: FAILED to execute** (codemap check, pytest, freeze check refused "[Code from External]"; static review
  only). Second refused verifier run of three today. Decision: the three READY pieces are ordered for its next run; all
  six new TODO tasks allow hand work so refused runs still produce evidence.
- **Owner directive (Q-50..Q-63) and 12:15 correction.** Decision: questions moved to Answered; DECISION_REGISTER.md and
  DESIGNER_CLARIFICATIONS.md (designer list, missing scope, status mapping) written; new tasks T-110 to T-114 by the
  directive's priority, each naming its answer; T-095 and T-115 wait for the owner's reconciliation; nothing released
  changes.

Recurring cause 8 (new, 12:20): two readers agreeing is not proof when they walk the same lines (T-014 vs T-016b on the
GF facade). Decision: when a hand reading contradicts an "independent" code reader, the verifier reads the drawing itself
before either merges.
