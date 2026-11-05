# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)


## LEAD REPORT 2026-11-05 12:20 UTC

Drive read OK (no file created in the project folders since 08:00 UTC, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.58 c9570e6c / master 1.55.0 (NOT RELEASED), no candidate quantity moved since 04:15; released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %). All results below are Checker-verified pieces, UNWIRED.
- Lintels (structural): project RC schedule governs 16/16: 6 PRODUCED, 10 HELD on short bearings; lintel concrete at the 10 short ends 0.514 -> 0.372692 .. 0.437542 m3 (0.037838 m3 already inside column lines, 0.01686 lintel-on-lintel once, 0.02176 not buildable as drawn: designer item, HELD). Checker found the curved-bay pier end W18 0.578 vs 0.478 m (no state moved) -> bearing V3.
- Black-block mortar (structural): joints at column faces and soffits +0.098145 m3 on 1.269444 m3 (+7.73 %, COMPUTED, Checker own DXF AGREE on 2 junctions); 0.15 m walls 0.0786 .. 0.0899 m3 HELD (module); 4 run ends at columns missing from the junction censuses -> new census row.
- Pool court (architectural): bath window sill '84' printed -> window upturn 0.500 lm MEASURED (roof upturn 186.783 -> 187.283 lm, +0.27 % if wired); ledge upturn 0 .. 3.528 -> 0 .. 0.552 lm + 2.977 lm glazing transition; ledge membrane 0 .. 0.640 m2 HELD (exposure rule needs a version from the drawn cover outline, not an angle).
- Materials: tile-bed mortar installed without the 5 % (20 m2 dry floor 0.600 .. 0.800 m3), loss its own account; project cement procurement AT_LEAST 130.82 .. 172.29 bags (was 120.66 .. 162.13); stair bed cement still HELD although your Q-53 answer (C) covers it -> FINISH V7 row. Freelancer: no cement / lintel rows (RULE_DIFFERENCE / UNRESOLVED, not compared).
- Learned (lessons rows PROPOSED): a printed value can sit in a DIMENSION block, not only in text (search both); an end volume inside another element is owned by that element's line once, never by default the minimum bearing.
- Gate 0 found: tests/t485 red on the working branch (merged pool-court WP package still 'pending' in the newest registry) -> fix row first in lane I. Gate 2 (integration). 10 Nov end-to-end BOQ: HIGH RISK (about 10 Gate B packages in 4.5 days, all behind the wrapper item; 9 verified pieces wait).
- Team health: 6 merged, 0 rejected since 08:15; every run closed with a final line; 0 empty runs; 7 new rows (S 3, A 2, I 2). Self-check codemap / t061 / freeze PASS. Queue check: see final RUN_LOG line.

OWNER PACKAGE: none (no engineering item meets standard s.2.7).

NEEDS FIXING (owner only, unchanged since 04:15, not re-notified): the run wrapper (scripts/agent_env.sh on main, line 211) still lets `run` start only the scoreboard and key-map tools; every integration package needs its research/agents_t*/ scripts, and the registry fix row may need one too. Needed: widen `run` to research/agents_t*/*.py, or name another approved path. Also open: Kuwait 1990 spec over the connector limit; repository privacy switch; PyMuPDF decision; PR #3 clean-up.

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
