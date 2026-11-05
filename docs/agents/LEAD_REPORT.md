# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)


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

## LEAD REPORT 2026-11-04 16:17 UTC

Drive read OK (no file created in the project folders since 12:00, no photo task). Training villa: candidate of record now V3.0.54 c85c4630 (NOT RELEASED); released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %).
- Stairs / railings (stream F Gate B PASS): B7-09 guardrail 17.366 -> 33.319 lm (+91.9 %): flights had fallen out on re-keyed census ids; now flight by flight along the pitch line. RL-07 15.953 lm Checker hand AGREE; 2 turn rails + GF band HELD; PARTIALLY VERIFIED 6/8. Freelancer 18.95 lm: +75.8 %, RL-07 ENGINE_RIGHT, rest UNRESOLVED. 4,921 lines byte-identical.
- Walls (Gate A, unwired): band path drops gaps < 0.50 m on any villa (1F W18 0.467 m beside a column, rescued only by a project ledger; Alsenan 0 m2 effect). Fix as a new version: T-510.
- Status words (Gate A): one vocabulary for all quantity states; 0 quantity change.
- Finishes materials (READY, Gate A): tile bed 12.469 .. 17.195 m3 on 88 lines -> cement 99.75 .. 137.56 bags, sand 13.72 .. 18.91 m3, waste apart; freelancer has no bed row (ENGINE_RIGHT on scope proposed); 1 bed HELD (finish HELD).
- Learned (2 lessons rows ADOPTED): bind stair rails by floor + flight + treads, never by census id alone; classify a wall gap by its bounding elements, not width. Element register: B7-09 rail vs slab-edge balustrade ruled.
- Missing: blockwork wiring (CLAIMED), wet-area WP r6, stair skirting wiring, materials wiring, disposal wiring. Gate: M3 / 10 Nov AT RISK (4 Gate B since 00:20, about 13 packages in 6 days).
- Team health: since 12:19 every run closed with a final line except Worker 3 15:02 (open, inside its lock). No usage-limit failure since 11:14. Self-check codemap / t061 / freeze PASS. Queue check: 18 actionable rows, 0 flagged, 0 stall checks.

OWNER PACKAGE: none (no item meets standard s.2.7).

NEEDS FIXING (owner only, unchanged): Kuwait 1990 spec copy under 6 MB (plastering chapter unread); repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
