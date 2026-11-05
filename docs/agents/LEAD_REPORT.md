# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)


## LEAD REPORT 2026-11-05 08:15 UTC

Drive read OK (no file created in the project folders since 04:00 UTC, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.58 c9570e6c / master 1.55.0 (NOT RELEASED), no candidate quantity moved since 04:15; released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %).
- Lintels (structural, Gate A, research): built jamb bearing measured on 16/16 lintels, 32 ends: 21 BOUNDED >= 0.40 m, 10 FLAGGED_DEFICIT 0.000 .. 0.259 m (RC column, cross wall, 0.238 m shared pier), 1 HELD; Checker own DXF re-measure AGREE (one end +3.7 mm, tolerance method, no state moved). 0.514 m3 of ledger lintel concrete not buildable as drawn (designer item, HELD, never 0). Bars unchanged: 63.162 kg AT_LEAST.
- Pool-court build-up (architectural, Gate A, research): finish 4.519172 m2 DRAWING-CONFIRMED extent (Checker 0.000000 difference); falls screed HELD on 4.906867 m2 (no thickness / fall / outlet printed, confirmed over 675 texts); insulation / protection UNKNOWN; if wired FIN.ROOF.FINISH 202.220 -> 206.739 m2 (+2.23 %). Freelancer one roof line 285.00 m2: UNRESOLVED (no comparable cell).
- Materials (Gate A, research): 92 producer keys / 13 factors traced, 0 unsourced factor applied; owner Q-45 5 % confirmed ASSUMED - OWNER-APPROVED; 2 defects: FINISH V1-V5 put the 5 % inside installed mortar (10 m2 dry floor 0.315 vs 0.300 m3), the blockwork / finish binding marks the +5 % bed as INSTALLED (0.206291 vs 0.196467 m3); +1 cement bag if item ceilings are summed.
- Learned (lessons rows PROPOSED): a FLAGGED_DEFICIT bearing is never defaulted to the printed minimum; a loss factor lives in its own account in every producer AND every binding.
- Gate 2 (integration). 10 Nov end-to-end BOQ: HIGH RISK, unchanged (about 10 Gate B packages left in 4.7 days; all blocked by the wrapper item).
- Team health: 3 merged, 0 rejected since 04:15; every run closed with a final line; 3 EMPTY worker runs 06:44-07:20 (Lead fault: no TODO left behind the 3 pieces) -> fixed: 6 new Gate A rows, 2 per lane, none needing the wrapper. Self-check codemap / t061 / freeze PASS. Queue check: 18 actionable rows, 0 flagged, 0 stall checks.

OWNER PACKAGE: none (no engineering item meets standard s.2.7).

NEEDS FIXING (owner only, unchanged since 04:15, not re-notified): the run wrapper (scripts/agent_env.sh on main, line 211) still lets `run` start only tools/alsenan_scoreboard.py and tools/alsenan_keymap.py; every integration package (blockwork materials, ceiling / paint fixes and about 8 more) needs its research/agents_t*/ scripts. Needed: widen `run` to research/agents_t*/*.py, or name another approved path. Meanwhile workers do research pieces that run through pytest only. Also open: venv install cut off at session start; Kuwait 1990 spec over the connector limit; repository privacy switch; PyMuPDF decision; PR #3 clean-up.

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
