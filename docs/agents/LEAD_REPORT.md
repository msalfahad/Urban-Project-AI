# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

## LEAD REPORT 2026-10-31 16:30 UTC

Drive readable: nothing created or modified in the Urban BOQ private data folder or the Alsenan project folder since
31 Oct 12:00 (search empty; no photo review task). Repositories: attached Urban-Project-AI checkout (main eafbb0f6);
`.work` prepared by `status` (auto). Working branch 94d85fc7 -> 6c219179 (four Checker 'engine push' merges: T-391,
T-392, T-390 at 13:01; T-396, T-394 at 14:05; T-284 at 15:57); no owner commit. Self-check: codemap PASS, pytest t061
PASS, freeze PASS (0). OWNER_SESSION_CHANGES: no new entry since my last run; nothing undone.

HEADLINE: the ceilings are in the candidate (V3.0.32, fifth Gate B first pass in a row): interior ceiling falls from
403.16 to 362.01 m2 measured from the drawings. Six pieces passed the Checker first time this window; columns now trace
to 0.000 m3 unexplained. Three structural / safety pieces wait for the Checker (at the target of 3).

ALSENAN, per trade (released V2.9 + route G unchanged: concrete 92.77 vs freelancer 111.81 m3, -17.03 %; reinforcement
10,250.168 kg; whole verified lines 1 (CONC.SLAB, candidate), released 0; candidate of record V3.0.31 -> V3.0.32):
- CEILINGS (m2; Gate B PASS 15:57): interior FIN.CEILING 403.163 -> 362.006 m2 DRAWING-CONFIRMED (-41.157, -10.21 %;
  8 lines moved, the 1F living group carried once, dressing 2.970 added; Checker own re-measures AGREE incl. 1F bedroom
  19.050 / 7.4692 with 0.1449 m2 beam strips named); bulkheads 27.9345 m2 and ceiling paint 389.941 m2 ASSUMED -
  OWNER-APPROVED (Q-48 A / Q-57 A mod); stair soffits x2 and dome intrados x2 BLANK (not drawn). Freelancer ceiling
  rows: in the finishes workbook over the connector limit: not compared (NEEDS FIXING 2).
- CONCRETE (m3), by family against the freelancer (research; no candidate quantity moved yet):
  columns (MERGED): CL-GF +0.530, CL-1F +2.520, CL-LIFT -2.400, all traced, unexplained 0.000 (joint and head owned by
  the column to the slab top +2.694 / +1.080; five annex columns HELD -2.063; his lift ring through the lift columns
  -0.750; one 1F section CONFLICT -0.138). Proposals verified: 15 CONFLICT lines become ranges (GF 2.070 .. 2.475,
  1F 5.964 .. 7.644), a new HELD lift-pit wall line (1.100 m2 x depth D-43).
  ground slab / ground beams and ring / pool fourth side (MERGED): as reported at 12:30 (22.664 m3 -> traced -4.844 /
  HELD -13.251 / unexplained -4.569).
  beams (READY): BM-GF -3.554, BM-1F +5.535, BM-2F -1.758 = six labelled marks he omits +9.882 (engine right) +
  upstands +0.240 + drawn runs beyond his rows +2.119 + through-support lengths -5.029 (rule difference: the column owns
  the joint) + dome ring +0.755 (to stairs / domes) + HELD -7.376 + untraced -0.367. Depth basis 0.000 (both full depth
  on a net slab).
  stairs / domes / pump (READY): -11.383 = traced -0.328, HELD -5.788 (pump room drawn nowhere -3.480), unexplained
  -5.266 (curved flight ST-02 -3.974, his flight 2.00 m beyond the drawn 3.30 run -2.016, dome area +0.561, landing
  +0.162).
- BOUNDARY FENCE (m2, MERGED, research): plane 97.9705 m2 DRAWING-CONFIRMED (36.97 m x 2.65 printed) vs freelancer
  74.40 m2 (-24.2 %): his height 2.00 vs 2.65 printed -24.031, a corner twice +0.40, typing +0.06: residual 0. Block
  net / type HELD (Q-65 C), below-ground masonry MISSING (HELD), sea / passage HELD. Not yet in the candidate.
- RAILINGS (m.l, READY): main stair balustrade 15.953 drawable per segment (was 16.153 all HELD); two turns HELD; one
  corner listed twice found; internal 19.766 vs freelancer 18.95 (+4.3 %): 1.042 named, -0.226 unexplained.
- FINISH FACE LENGTHS (MERGED): 0.000 m2 change (walk-tolerance artefacts).
- REINFORCEMENT (kg), FORMWORK, ROOF, SANITARY: no change since 12:30.
Development project 2: paused, not measured.

WHAT IMPROVED / WHY: ceilings now from the drawings room by room (the old line carried rooms at the wrong size or
twice); columns fully explained; a missing category (boundary fence) measured with a printed height. WHAT GOT WORSE:
nothing measured moved the wrong way. WHAT WAS LEARNED: at every slab / beam / column junction one element owns the
intersection and a family takes each member's printed section; a site wall is three trades on one element. WHAT IS
MISSING: lift pit / shaft structure, held beams, boundary wall below ground and its finishes, kitchen / laundry / pantry
wall tiles (verified, not yet integrated), corner beads, skirting, WP fixes, exterior plaster, earthworks, foundation WP,
masonry accessories. GATES: lowest open gate 2 (integration); reconciliation gate 3. Milestones: week 2 (3 Nov) roof,
formwork and ceilings delivered; M3 11 Nov on track; M4 25 Nov at risk on consultant items (D-16, D-34, D-35, D-43).

DECISIONS THIS RUN: T-397 TODO first in integration, scope extended with the verified column ranges and the held
lift-pit wall line; NEW T-399 (integration: kitchen / laundry / pantry wall-tile zones, verified, missing category),
T-400 (integration: boundary fence + gates), T-401 (lift pit and shaft structure), T-402 (held beam items one by one),
T-403 (boundary wall below ground), T-404 (fence finishes), T-405 (plaster corner beads, a separate item by the Urban
finish-extras rule), T-406 (concrete roll-up after beams / stairs merge). Element register: three rulings (lift pit and
shaft; plot boundary wall = three trades on one element; tile zones). VERIFIER QUEUE: T-395 > T-398 > T-393, then Gate B
T-397. Queue check: 49 actionable rows, 0 flagged, 0 stall checks. TODO claimable: S 3, A 2, I 1 (serial); READY 3.

LESSONS REGISTER: two rows adopted in the standard s.7 (junction ownership / section per member, from T-391 / T-394; a
site wall enumerated by component and trade, from T-396). Proposed from READY work, adopted after the Checker: 'beam
length face to face only where the column line carries the joint (never both, never neither)' (T-395); 'one physical
corner listed once even when two runs meet in it' (T-393).

TEAM HEALTH (12:23 - 16:30): every STARTED line has a final line (Worker 1 x2, Worker 2 x2, Worker 3 x2, Checker x4
incl. one overlap-guard exit at 15:50); all self-checks PASS; scheduler last runs SUCCEEDED (Worker 2 14:39, Worker 3
14:59, Checker 15:49, Main 04:31, Dashboard 12:54; Worker 1 from RUN_LOG 15:20 - 15:36). No idle slot. Fault repeated:
two READY stamps ahead of the clock (Worker 2 15:35 for a run closed 14:55; Worker 3 16:20 for 15:14); rows annotated,
FEEDBACK again; if it recurs it needs prompt wording by the main chat. Refusals: Checker's first full-suite launch
('pytest path must be under tests/ or agents/: tests', re-run correctly) and a decode name with a space (re-run);
Worker 1's 13:20 write of drawing-derived outline sizes into the repo refused (kept in .work/private: privacy guard
working). Scout paused (your 28 Oct choice).

OWNER PACKAGE (unchanged, no new decision):
- T-383 waterproofing completeness join (your 31 Oct item 5): own row (A, recommended) vs inside T-310 (B); full ERS s.6
  text in my 00:45 report (archive); no quantity impact either way; on 'A' it becomes TODO for worker 2.
- Q-78 (mix for the black block-joint mortar) still open, not urgent.

NEEDS FIXING (only you or the main chat):
(1) RFI EVIDENCE REGISTER (your 31 Oct item 4): writing drawing-derived evidence into the public repository is refused by
the platform (23:39, 01:55). Needs your decision on where it may be kept. The checker will not retry until then.
(2) The freelancer finishes workbook (23.6 MB) is over the connector limit: a .zip copy on Drive would let his finish rows
(ceilings, railings, tiles) be reconciled.
(3) From my 00:45 report: whether to rewrite git history for the freelancer rate already pushed (agents may not).
(4) Workers keep stamping board lines ahead of the clock (4 cases today): a one-line prompt wording fix ("stamp from
`date -u` at the moment of writing") is a main-chat change; I do not edit prompts.

## LEAD REPORT 2026-10-31 12:30 UTC

Drive readable: nothing created or modified in the Urban BOQ private data folder or the Alsenan project folder since
31 Oct 08:00 (search empty; no photo review task). Repositories: attached Urban-Project-AI checkout (main eafbb0f6);
`.work` prepared by `status` (auto). Working branch df170b8d -> 94d85fc7 (three Checker merges via 'engine push'); no
owner commit. Self-check: codemap PASS, pytest t061 PASS, freeze PASS (0). OWNER_SESSION_CHANGES: no new entry since my
last run; nothing undone.

HEADLINE: the roof build-up is in the candidate (V3.0.31, fourth Gate B pass in a row); the concrete comparison is now
honestly closed by cause, and the two largest unresolved parts (ground slab and ground beams, 22.7 m3) have been measured
from the drawing: only 4.6 m3 of them is still unexplained. Three pieces wait for the Checker (at the target of 3).

ALSENAN, per trade (released V2.9 + route G unchanged: concrete 92.77 vs freelancer 111.81 m3, -17.03 %; reinforcement
10,250.168 kg; whole verified lines 1 (CONC.SLAB, candidate), released 0; candidate of record V3.0.30 -> V3.0.31):
- ROOF BUILD-UP (m2 / m3; Gate B PASS 11:52): 16 lines (4 roofs x 4 layers). Roof finish 202.220 m2 MEASURED (54.920 +
  31.643 + 115.656; Checker re-measured 115.651, -0.004 %); screed one line per roof HELD (thickness not printed, D-39),
  insulation / protection 8 lines UNKNOWN blank, top roof HELD (Q-34). Freelancer: one roof line 285.00 m2: NOT
  COMPARABLE per layer (his line mixes layers; no % stated). Change: 0 -> 202.220 m2 in the candidate; released unchanged.
- CONCRETE (m3): comparison of the candidate (V3.0.29 structure) vs the freelancer, residual -114.464 m3, now split by
  cause (merged 11:00): traced causes +0.252, HELD named items -77.593 (they are not errors: the engine has no value yet),
  unexplained -37.124 (11 unresolved parts -36.652 + pool-wall height 0.471 not on any drawn level). Change since last
  report: the earlier '0.000 unexplained' was withdrawn; same numbers, honest split.
  Ground slab and ground beams (waiting for the Checker): ground slab -12.309 m3 = his slab plate runs over beam / column
  strips -7.188 (engine right: those strips are beam / column concrete) + panels inside an engine HELD cell -3.561 +
  stair-zone panel -0.837 (unresolved) + his area beyond the drawn network -0.639 (unexplained) + small reads -0.085.
  Ground beams -10.355 m3 = held runs -9.690 (53.8 m: consultant items D-34 / D-35, court) + section: exterior beams
  0.95 m deep vs his 0.60 (+5.797, engine right) and interior 0.40 vs 0.60 (-3.444, engine right) + his longer run
  length -3.008 (unexplained). Net: of 22.664 m3 unresolved -> traced -4.844, held -13.251, unexplained -4.569.
  Found: the held ground-slab cell includes the 1.80 x 1.80 lift shaft; its range should be 0 .. 3.561 (was 3.930):
  correction proposed for integration after the check. The slab under the ground-floor flight is printed nowhere:
  designer fact (rfi), not your question.
  Ring / pool fourth side (waiting for the Checker): ring B7 0.218 m3 located on the drawing, billed once, agrees; the
  0.0026 m3 'slivers' are a real small gap, not rounding; CB8 beam end 59 mm into B27 (double 0.0028 m3) and short at the
  other end (gap 0.0034 m3): proposals, immaterial; the pool's fourth side is 3.50 m of pool wall plus 1.668 m of PLOT
  BOUNDARY WALL whose above-ground blockwork is in no BOQ line -> new missing-category task.
- FINISHES (m2): the three wall-face length residuals (pantry -0.120, GF-08 -0.140, GF-14 -0.045 m) are artefacts of the
  face-walk tolerance, not drawn walls: the candidate's faces were right; 0.000 m2 change (waiting for the Checker).
- REINFORCEMENT (kg), RAILINGS, FORMWORK, SANITARY: no change since 08:30.
Development project 2: paused, not measured.

WHAT IMPROVED / WHY: one more missing category (roof layers) in the candidate with every blank named; the concrete gap
is now explained by physical cause: the freelancer's ground slab runs through beam strips and his ground beams use one
0.60 m depth where the drawing prints 0.95 / 0.40. WHAT GOT WORSE: nothing measured moved the wrong way. WHAT WAS
LEARNED: a reconciliation must stop at traced causes; a held range must exclude voids drawn inside it (the lift shaft).
WHAT IS MISSING: column height basis, beams, stairs / domes (new tasks), boundary fence blockwork (new), ceilings (next
in integration), skirting, WP fixes, exterior plaster, earthworks, foundation WP, masonry accessories. GATES: lowest open
gate 2 (integration); reconciliation gate 3. Milestones: Week 2 (3 Nov) formwork + roof delivered, ceilings next; M3 11
Nov on track; M4 25 Nov (structural ledger) at risk but better: 18.1 of the 36.7 m3 unresolved now traced or held.

DECISIONS THIS RUN: T-284 ceiling line TODO (next in integration, bind to V3.0.31, no surface counted twice with the dome
soffit formwork or roof finish); NEW T-394 (columns: height basis and section), T-395 (beams: depth and length basis),
T-398 (stairs / domes / pool-pump scope + the flight-on-grade designer fact), T-396 (BOUNDARY FENCE BLOCKWORK, missing
category, block type HELD under your Q-65 C), T-397 (integration of the verified structural corrections from the ground
slab and ring checks). Element register: pool fourth side = 3.50 m pool wall + 1.668 m plot boundary wall, never both.
Queue check: 47 actionable rows, 0 flagged, 0 stall checks. TODO claimable: S 3, A 2 (+T-383 owner-held), I 1 (serial);
READY 3.

LESSONS REGISTER PROPOSALS (standard s.7):
'2026-10-31 | a held cell's bound included a lift shaft and its strips (not slab) | the bound took the cell outline,
not the drawn panels | a held range is the sum of drawn panels inside the cell, voids out | T-391 R-T391-5 tests |
PROPOSED';
'2026-10-31 | a neighbour-overlap deduction came from a fitted band set, not the drawn cells | fitted geometry used as
evidence | deductions from drawn cells only; report beyond / short of a carrier face apart | T-392 R-T392-1..4 tests |
PROPOSED';
'2026-10-31 | a face-length residual was a walk tolerance artefact counted as wall | geometric face taken from a
tolerance-booked walk | face length = contour less every open-side run incl. tolerance-booked samples | T-390 R-T390-1
tests | PROPOSED'.

TEAM HEALTH (08:19 - 12:30): every STARTED line has a final line (Worker 1 x2, Worker 2 x2, Worker 3 x2, Checker x4
incl. one overlap-guard exit at 11:50); all self-checks PASS; scheduler last runs SUCCEEDED (Worker 2 10:39, Worker 3
11:00, Checker 11:50, Main 04:31, Dashboard 00:54). No idle slot this window. Worker 3's last final line is stamped 12:48
though written at about 11:19 (clock stamp ahead; asked to stamp from date -u). No refusal this window. Scout paused
(your 28 Oct choice).

OWNER PACKAGE (unchanged, no new decision):
- T-383 waterproofing completeness join: own row (A, recommended) vs inside T-310 (B); full ERS s.6 text in my 00:45
  report (archive); no quantity impact either way; on 'A' it becomes TODO for worker 2.
- Q-78 (mix for the black block-joint mortar) still open, not urgent.

NEEDS FIXING (only you or the main chat):
(1) RFI EVIDENCE REGISTER (your 31 Oct item 4): writing drawing-derived evidence into the public repository is refused by
the platform (23:39, 01:55). Needs your decision on where it may be kept. The checker will not retry until then.
(2) The freelancer finishes workbook (23.6 MB) is over the connector limit: a .zip copy on Drive would let his finish rows
be reconciled.
(3) From my 00:45 report: whether to rewrite git history for the freelancer rate already pushed (agents may not).


## LEAD REPORT 2026-10-31 08:30 UTC

Drive readable: nothing created or modified in the Urban BOQ private data folder or the Alsenan project folder since
31 Oct 04:00 (search empty; no photo review task). Repositories: attached Urban-Project-AI checkout (main eafbb0f6);
`.work` prepared by `status` (auto). Working branch b25b77b2 -> df170b8d (Checker merges via 'engine push'); no owner
commit. Self-check: codemap PASS, pytest t061 PASS, freeze PASS (0). OWNER_SESSION_CHANGES: no new entry since my last
run; nothing undone.

HEADLINE: formwork, railings and shutters are now in the candidate (V3.0.30, third Gate B pass); two candidate-wide
consistency checks merged; the per-family concrete comparison was sent back because 11 unresolved parts (about 36.7 m3)
had been booked as explained. My fault this cycle: two worker slots idled on an empty board; refilled.

ALSENAN, per trade (released V2.9 + route G unchanged: concrete 92.77 vs freelancer 111.81 m3, -17.03 %; reinforcement
10,250.168 kg; whole verified lines 1 (CONC.SLAB, candidate), released 0; candidate of record V3.0.29 -> V3.0.30):
- FORMWORK (m2; Gate B PASS r3 05:54): 1,065.833 m2 CALCULATED (= checker-verified face ledgers, 0 mismatches); 378 lines
  HELD blank (60 formed / earth-cast pairs never summed, OQ-10; 24 parapet faces). Freelancer: no formwork row (not
  comparable). Change: 0 -> 1,065.833 m2 in the candidate; released unchanged.
- RAILINGS (m.l): 38.916 lm in the candidate, 12.888 VERIFIED (checker's own DXF, 0.0 %); internal railing 19.766 lm vs
  freelancer 18.95 m.l = UNRESOLVED scope (+0.816 m.l, +4.3 %, not an error % until his runs are matched); ST-01
  balustrade 16.153 m and the GF sea strip 6.127 m HELD, never 0 -> new railing-scope task. Shutters 6 leaves, m2 HELD.
- CONCRETE (m3): per-family comparison REJECTED r1. Checker-confirmed: second F3 footing ENGINE_RIGHT (+0.672 m3; two
  C3/F3 labels each with its own 1.40 x 1.60 block); pool base 4.374226 and walls 2.828071 m3 from the drawing. Not
  closed: 11 UNRESOLVED components, -36.652 m3 together (ground slab -12.309, ground beams -10.355, column height basis,
  beams, stairs, domes, lift / pump scope); pool walls carry a further 0.471346 m3 on the wall-height basis named by no
  cause. Ownership census (merged): 525 lines, 0 unbound, 317 valued 285.0266 m3, no double count found; GF B27 own
  re-measure 4.1927 vs line 4.1918 m3 (-0.02 %, agree). Open: ring B7 0.2182 + 0.0235 m3, T-146 slivers 0.0026 m3
  (immaterial), the out-of-pool part of the pool's fourth side (owner trade not named).
- REINFORCEMENT (kg): record DG-df07eb3d issued: 10 footing '/m' lines HELD (1,606.069 .. 1,655.560 kg leave the bounded
  figure); released 10,250.168 kg unchanged. Bounded candidate range after it: per the checker's V3.0.29 restatement.
- FINISHES (m2): face-consistency check merged: every opening deducted once per trade per face (65 / 65); no reveal or
  threshold double count. Found: 10 door holes on the wrong face piece (room totals 0.000 m2; D-1F-04 1.760 m2),
  face-length residuals pantry -0.120 m (tile and backing -0.438 m2 each, 1.35 %), GF-14 -0.045 m (-0.164 m2), GF-08
  -0.140 m (plaster / paint -0.511 m2, inside its HELD bound); checker's own read GF-W01 3.000 m drawn vs 3.015 m used.
  Pantry paint line should be NOT_APPLICABLE (tile owns the wall).
- SANITARY: the shower 11 and gratings 24 are Urban's own cost record (WEB-018 / WEB-019), not the freelancer: B12-01
  has NO freelancer comparison (it had been reported -5 pcs / -45 %); drawn 6 showers stand.
Development project 2: paused, not measured.

WHAT IMPROVED / WHY: a missing category (formwork) and the metalwork family entered the candidate with every quantity
traceable; the candidate now has a structural ownership proof and a wall-face proof. WHAT GOT WORSE: nothing measured
moved the wrong way; the concrete reconciliation turned out less closed than claimed (honest restatement, not a loss).
WHAT WAS LEARNED: 'closes to 0.000' must count only traced causes; a documented deduction below tolerance is named,
never 'rounding'; a benchmark's source (freelancer vs Urban cost record) is named before comparing. WHAT IS MISSING:
roof build-up (next), ceilings, skirting + face fixes, WP fixes, exterior plaster, earthworks, foundation WP, spatter,
masonry accessories, mortar (lane I, serial). GATES: lowest open gate 0 (cost-record relabel, no quantity); quantity work
gate 2 - 3. Milestones: Week 2 (3 Nov) formwork delivered, roof expected 1 Nov, ceilings at risk; M3 11 Nov; M4 25 Nov at
risk on the unresolved concrete parts.

DECISIONS THIS RUN: T-328 roof build-up TODO (first lane I; adds: registry owns every V3.0.x code incl. EXT.* /
WP.FOUNDATION.* / FLOOR.*, guard rails their own metalwork family by my register ruling); T-385 -> TODO r2 (exact fault);
NEW T-389 (gate 0 A, cost-record relabel, guard baseline to 0), T-390 (A, face-length causes), T-391 (S, ground slab +
ground beams re-measure, about 22.7 m3), T-392 (S, ring / slivers / pool fourth side owner trade), T-393 (A, railing
scope); T-246 gains the T-388 face fixes. Board text corrected for the shower / gratings provenance. Element register:
6 rulings (guard rails, planted column on B27, T-146 slivers, pool fourth side, showers, wall-face attribution). Queue
check: 45 actionable rows, 0 flagged, 0 stall checks. TODO claimable: S 3, A 3, I 1 (serial) + T-383 owner-held; READY 0.

LESSONS REGISTER PROPOSALS (standard s.7):
'2026-10-31 | a reconciliation reported 0.000 unexplained while 11 untraced parts (-36.652 m3) were summed as named causes
| closure by construction | cause closure counts only traced causes; untraced parts print as unexplained | T-385 r2
adverse tests | PROPOSED';
'2026-10-31 | a census called documented sub-tolerance deductions "rounding" | one ledger read, not every ledger that
wrote the line | reconcile to every merged ledger (formula field first); name a deduction below tolerance | T-392 adverse
case | PROPOSED';
'2026-10-31 | an Urban cost-record count was reported as a freelancer residual (-45 %) | source class not named | name the
benchmark source and register id before comparing; undefined basis = UNRESOLVED scope | t386 guard + T-389 | PROPOSED'.

TEAM HEALTH (04:30 - 08:30): every STARTED line has a final line (Worker 1 x2, Worker 2 x2, Worker 3 x2, Checker x4
incl. one overlap-guard exit at 07:51, Lead x1 open = this run); all self-checks PASS; scheduler last runs SUCCEEDED
(Main 04:31, Worker 2 06:40, Worker 3 06:59, Dashboard 00:54). Idle: Worker 1 07:21 and Worker 3 07:01 found no TODO
(Lead cause, fixed). Worker 2's final-line stamps run ahead of the clock (07:58 written at about 07:50; also 01:22 vs
00:54 merge): cosmetic, the Checker already corrects them; no refusal this window except the known private-data ones.
Scout paused (your 28 Oct choice).

OWNER PACKAGE (unchanged, no new decision):
- T-383 waterproofing completeness join: own row (A, recommended) vs inside T-310 (B); full ERS s.6 text in my 00:45
  report (archive); no quantity impact either way; on 'A' it becomes TODO for worker 2.
- Q-78 (mix for the black block-joint mortar) still open, not urgent.

NEEDS FIXING (only you or the main chat):
(1) RFI EVIDENCE REGISTER (your 31 Oct item 4): writing drawing-derived evidence into the public repository is refused by
the platform (23:39, 01:55). Needs your decision on where it may be kept (e.g. only in the private workspace, cited by
Drive title and page). The checker will not retry until then.
(2) The freelancer finishes workbook (23.6 MB) is over the connector limit: a .zip copy on Drive would let his finish rows
be reconciled (the shower count is no longer one of them: it was Urban's cost record).
(3) From my 00:45 report: whether to rewrite git history for the freelancer rate already pushed (agents may not).

