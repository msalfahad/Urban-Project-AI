# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)


## LEAD REPORT 2026-11-05 04:15 UTC

Drive read OK (no file created in the project folders since 00:00 UTC, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.58 c9570e6c / master 1.55.0 (NOT RELEASED); released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %).
- Roof waterproofing (stream F Gate B PASS, every new line by hand AGREE): FIN.WP.ROOF 204.112 -> 209.019 m2 (+2.40 %: pool-court exposed slab 4.907 m2 DRAWING-CONFIRMED, ledge HELD 0 .. 0.64 m2); upturn 181.589 -> 186.783 lm; vs freelancer 285.00 m2 -28.4 % -> -26.7 % (diagnostic, not a keyed pair). Lines PARTIALLY VERIFIED.
- Lintel reinforcement (Gate A, research): printed span parts 63.162 kg AT_LEAST on 16 lintels; ends, bends, laps HELD by name; ceiling 106.95 kg only conditional on a 0.40 m bearing the drawing prints as a minimum -> new jamb-bearing census.
- Screeds / thresholds / outdoor bed (Gate A, research): walk bed 5.04 .. 6.72 bags cement; project cement known part >= 125.13 .. 164.62 bags (was 120.08 .. 157.90); 31 hosts HELD on unprinted mix, never 0. Pool-court build-up above the new membrane has no line (silent omission) -> new task.
- Ceiling / paint deductions: engineering AGREE (0 quantity moved, dome disc 15.359 m2 re-measured) but sent back for 3 new full-suite failures; blockwork materials (black 0.20 1,075.80 pcs, mortar 1.269 m3 PROV, glue 43.6 kg) staged twice, not finished.
- Learned: a status cell must start with its status word (a sent-back row read as REJECTED hid a TODO for a run); waste is its own account, never inside installed (factor provenance census opened).
- Gate: 2 (integration). 10 Nov end-to-end BOQ: AT RISK -> HIGH RISK: 8 Gate B merged since 4 Nov 00:20, about 10 left in 4.8 days, and every remaining package is blocked by the tooling item below.
- Team health: since 00:15 4 merged-or-checked (3 MERGED, 1 REJECTED), every run closed with a final line, 1 empty worker run (W1 03:21, row-format fault, fixed). Self-check codemap / t061 / freeze PASS. Queue check: 15 actionable rows, 0 flagged, 0 stall checks.

OWNER PACKAGE: none (no engineering item meets standard s.2.7).

NEEDS FIXING (owner only, blocks the critical path): the run wrapper (scripts/agent_env.sh on main, line 211) lets `run` start only tools/alsenan_scoreboard.py and tools/alsenan_keymap.py. Every integration package must run its research/agents_t*/ scripts (Drive chain, master build, binding and git-facts tools); Worker 3's temporary pytest runner was refused by the permission classifier as a bypass, and the Checker cannot reproduce a chain either. Tried: workers barred from bypasses; blocked packages parked; three standalone pieces given so no run is empty. Needed: widen `run` to research/agents_t*/*.py (same venv, same tree rules), or name another approved path. Also open: venv install cut off at session start (recurring); Kuwait 1990 spec over the connector limit; repository privacy switch; PyMuPDF decision; PR #3 clean-up.

## LEAD REPORT 2026-11-05 00:15 UTC

Drive read OK (no file created in the project folders since 20:00, no photo task). Training villa: candidate of record now ARCH_TAKEOFF_V3.0.57 25a8b406 / master 1.54.0 (NOT RELEASED); released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %).
- Waterproofing, wet areas and pool (stream F Gate B PASS, every moved line by hand AGREE): FIN.WP.FLOOR 85.6207 -> 85.5757 m2 (-0.05 %: pantry floor 13.500 -> 13.455 m2), upturn 25.1146 -> 25.2146 m2 (+0.40 %: 1F east bath 1.480 -> 1.580 m2), pool membrane 29.582355 m2 and protection screed 1.524503 m3 as new lines; 3 doorway terminations NOT_APPLICABLE, 3 doors HELD blank. Freelancer comparison unchanged (his WP rows are not like-for-like by line).
- Gate fix (Gate A): tests/t212 green again; an all-blank code now prints HELD (n blank lines), never 0.0; 0 quantity change. Census: 37 of 111 codes still print 0.0 in the candidate's code_totals summary path -> acceptance item of the next stream F package (T-507).
- Cement / sand (Gate A, research): 1,458 keys, 0 with two producers; project installed cement HELD, known part >= 120.08 .. 157.90 bags (block mortar 10.16, tile bed 99.75 .. 137.56, stair bed 10.18 bags on 35.43 m2, Checker re-measured one flight 3.450 m2 AGREE). Missing producers: 8.052 m3 released screed, threshold / lift and outdoor beds (new row T-514). RULE_DIFFERENCE vs freelancer (no cement rows).
- Learned: one producer per material key (lessons row ADOPTED by the Checker); a staged package must renumber at hand-in when another merges first (T-498 V3.0.57 -> next free; no engineering change).
- Missing: blockwork materials (T-498 in progress), ceiling / paint deductions (T-423 in progress), pool-court WP (T-507 next), disposal, landings, exterior plaster, nosing, spatter dash, accessories, band-gap wiring; lintel bars split (T-515). Gate: M3 / 10 Nov AT RISK (7 Gate B since 00:20 4 Nov, about 10 in 5.0 days).
- Team health: 3 merged, 0 rejected since 20:15; every run closed with a final line except Worker 3 (23:00) and Worker 1 (23:20), both still inside their locks; 0 empty runs. Self-check codemap / t061 / freeze PASS. Queue check: 15 actionable rows, 0 flagged, 0 stall checks.

OWNER PACKAGE: none (no item meets standard s.2.7).

NEEDS FIXING (owner only): (new) the run wrapper refuses research scripts ('AGENT_ENV FAIL: run allows only tools/alsenan_scoreboard.py or tools/alsenan_keymap.py'); Worker 2 ran a census script with the venv python directly, outside the pre-approved command: please allow research/agents_t*/ scripts in `run`, or confirm workers must call them only through pytest. (recurring) the session-start venv install is cut off (Checker 22:45 and 23:59: first selfcheck 'No module named pytest', fixed by re-running setup). Unchanged: Kuwait 1990 spec copy under 6 MB (plastering chapter unread); repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.

## LEAD REPORT 2026-11-04 20:15 UTC

Drive read OK (no file created in the project folders since 16:00, no photo task). Training villa: candidate of record now V3.0.56 4e25c54f (NOT RELEASED); released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %).
- Blockwork (stream S Gate B PASS, every moved wall by hand AGREE): MAS.BLOCK 579.1011 -> 467.7925 m2 (-19.2 %), volume 104.469 -> 84.630 m3; 8 roof-storey walls 98.3775 m2 HELD on the roof datum (D-39), GF-W22 CONFLICT 12.9311 .. 12.9439 m2 (D-27). No freelancer like-for-like until D-39 settles.
- Stair skirting (stream F Gate B PASS): FIN.SKIRTING 212.379 -> 209.429 lm (-1.39 %); shaft 9.050 lm ENGINE_WRONG retired; landings 6.100 lm DRAWING-CONFIRMED; 22 flight pieces blank (HELD-FORM, both forms beside).
- Tile bed mortar table (Gate A): 12.469 .. 17.195 m3 -> buy 105 .. 145 cement bags; unwired. Band-gap classes (Gate A): unwired, 0 m2 here; it left tests/t212 red on the working branch (F-C-T510-3) -> gate fix T-512 first.
- Learned: a wall with an unprinted top datum is HELD with its terms, never valued to a borrowed height (lessons row ADOPTED); a new engine module declares its guard class in the same package (PROPOSED). Register: stair-hall vs landing faces; band-path pier face ruled.
- Missing: blockwork materials (recompute from the new base), wet-area WP (rebase r7), ceiling / paint deductions, pool-court WP, disposal, landings, exterior plaster, nosing, spatter dash, accessories. Gate: M3 / 10 Nov AT RISK (6 Gate B since 00:20, about 11 in 5.2 days).
- Team health: 4 merged, 0 rejected since 16:17; every run closed with a final line. 3 empty worker runs 18:41-19:19 (no TODO left by the 16:17 plan): fixed, 5 TODO now, each worker has a second row. Self-check codemap / t061 / freeze PASS. Queue check: see final line.

OWNER PACKAGE: none (no item meets standard s.2.7).

NEEDS FIXING (owner only, unchanged): Kuwait 1990 spec copy under 6 MB (plastering chapter unread); repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.

