# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

## LEAD REPORT 2026-11-03 16:17 UTC

Drive read OK (no file created in the project folders since 12:00, no photo task). Training villa: candidate of record still V3.0.46 35d70129 (NOT RELEASED); released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %). No quantity merged since 12:20.
- Skirting (stream F, Gate B) sent back for 3 test faults only; the engineering agrees: stair-room skirting 189.819 -> 203.369 lm (+13.550 lm: hall 4.650, back lobby 1.400, 2F lobby 3.350, 2F arrival 4.150), Checker's own DXF read of all 4 children. Rework set with the exact faults.
- Ruling: one of the 3 faults is in the registry guard itself (it calls a package 'merged' as soon as its commit is on its own branch, so every package fails). Fixed once in a separate small task, not by each package; lessons row proposed.
- Waiting for the Checker (4, measured but not verified): tile adhesive by size, held 148.457 .. 247.428 bags until a tile size is printed; entrance / stair-hall stone floor not applicable on the issued drawings (0 m2 new); plaster mix as an estimate, cement / sand still HELD (sensitivity 30.18 .. 48.88 bags, 1:5 .. 1:3); site preparation: boundary 92.740 lm, clearance 470.550 m2, the duration items HELD with formulas (no programme).
- Not measured / held: earthworks still unwired (pits backfill 119.96 .. 128.64 m3 PARTIALLY VERIFIED 7 / 8); disposal HELD.
- Gates: Gate 0 none; Gate 1 guard fix (new); Gate 2 stream S earthworks wiring, stream F skirting rework.
Team health: 2 runs stopped without a final line (Worker 3 13:01 on earthworks wiring, Checker 13:52), cause not known, nothing pushed, no partial merge; 3 later runs idled on their locks, so the Checker lost about 2 h and READY rose to 4. Locks have expired; the 16:49 Checker and 16:59 Worker 3 runs take over. Every other run closed with self-check PASS. 10 Nov AT RISK: 0 packages merged this afternoon.

OWNER PACKAGE: none (no item meets standard section 2.7).

NEEDS FIXING (only you): the Kuwait 1990 specification is over the 10 MB connector limit, so its plastering chapter cannot be read: a split or zipped copy under 6 MB would let the plaster mix move from HELD to a sourced value. Still open: repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.

## LEAD REPORT 2026-11-03 12:20 UTC

Drive read OK (nothing created or modified since 08:00, no photo task). Training villa: candidate of record now V3.0.46 35d70129 (NOT RELEASED); released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %).
- Structure (stream S Gate B PASS): GF lift tie beam 5.500 m (Checker own DXF AGREE) and house block below ground AT_LEAST 11.389 m2 added as HELD lines (section D-43, annex D-35); 4,856 lines byte-identical; L4 0 fail.
- Earthworks (piece, unwired): pits backfill 115.55 .. 128.62 -> 119.96 .. 128.64 m3, PARTIALLY VERIFIED 7 / 8 (necks 5.154, straps 0.180 m3 AGREE exact; residual D-33 / D-35 8.650 + C8 0.030 m3 named). Wiring claimable now.
- Blockwork: materials r2 merged (glue L-2fdc 444.47 .. 451.22 kg RANGE-NET; black 0.20 1,346.55 nr unchanged). Conditions settled from the structural drawings: 8 2F walls under the roof HELD U - L x b_r on D-39 (52.776 m2 carried today = the b_r 0.05 what-if, it leaves the determinate total at wiring), GF-W22 CONFLICT 12.931 .. 12.944 m2, parapet NW-2 0 .. 3.167 m2. Checker 3 / 4 re-measured. Wiring -> new T-488.
- Plaster materials (piece, unwired): dry mortar 4.727 m3 ESTIMATED (236.35 m2 x 0.020), wet render >= 5.105 m3 (340.30 m2 x >= 0.015), spatter 576.65 m2; Checker re-derived exact. Cement / sand HELD (no mix).
- Registry 1.43.0: 39 packages promoted; families in the candidate 13 -> 44, stale blocks 21 -> 0.
- Decision: Q-79 (plaster mix) WITHDRAWN, not ERS s.2.7 (non-critical procurement parameter; level-4 estimate allowed; the 1990 specification was only read to a 97,008-character cut) -> T-489. New: T-488, T-489, T-490 (B3-03 stone floor), T-491 (site preparation, your 17:20 item 6). 2 register rulings, 4 lessons rows (3 ADOPTED from Checker-endorsed verdicts).
- Gates: Gate 0 none; Gate 2 stream S T-350 r3 next, stream F T-443 r2 rebasing.
Team health: since 08:18 every closed run wrote STARTED + final line (Worker 1 x1, Worker 2 x2, Worker 3 x3 incl. the 07:01 run, Verifier x4), self-checks PASS, no refusals; Checker 6 merged / 0 rejected. Open: Worker 1 11:20 (in lock). Stream F delivered 0 packages since 22:50 (rebase after the stream S merge): 10 Nov AT RISK; 4 Nov review stands. Self-check PASS; queue check 22 actionable, 0 flagged, 0 stall.

OWNER PACKAGE: none today (no item meets standard section 2.7; Q-79 withdrawn, you may still give a company mix and it supersedes the estimate).

NEEDS FIXING (only you): repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.

## LEAD REPORT 2026-11-03 08:18 UTC

Drive read OK (nothing created or modified since 04:00, no photo task). Training villa: candidate of record V3.0.45 5972888b unchanged (NOT RELEASED); released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3).
- Earthworks (missing category, piece merged, not wired): pits excavation 208.165 m3 ESTIMATED on the owner-accepted formation (Checker own DXF re-measure 208.164, 0.0004 %); pool 17.777 m3 DRAWING-CONFIRMED; pits backfill 115.554 .. 128.622 m3 PARTIALLY VERIFIED 4 / 8; disposal HELD. Lower bound corrected 188.017 -> 186.974 m3 (F8 counted twice). No freelancer earthworks to compare. Wiring queued (stream S, after the lift tie beam); 4 backfill components -> new task.
- Blockwork materials REJECTED r1: REQUIRED RC lintel faces (w + 0.80) x D sat in the host material base as well as in lintel concrete; glue line L-2fdc 458.892 kg -> 444.470 .. 451.220 kg (not VERIFIED-NET); black 0.20 blocks 1,346.55 nr unaffected. Exact fix written; rework next.
- Registry (Gate B PASS, no quantity change): 0 lines outside families, 0 doubly mapped; found 38 merged packages unpromoted and B8-07 balcony WP / B9-02 lintels with no candidate line -> 3 new tasks.
- Skirting remainder (checked, unwired): certain 189.82 -> 198.83 lm proposed, held 15.73 -> 0; freelancer 282.85 lm RULE_DIFFERENCE. Wet walls: one fixing material only (checked).
- Learned (lessons rows): a material base must exclude every face another trade owns (lintel faces, PROPOSED, from F-C-T453-1); a printed lower bound must be re-derived when an overlap is found (188.017 -> 186.974, PROPOSED).
- Gates: Gate 0 none; Gate 1 T-485; Gate 2 stream S T-419 (CLAIMED), stream F T-443 (CLAIMED).
Team health: since 04:18 every closed run wrote STARTED + final line (Worker 1 x1, Worker 2 x2, Worker 3 x2, Verifier x4), self-checks PASS, no refusals; Checker 6 merged / 1 rejected. Open: Worker 3 07:01, Worker 1 07:20 (both in lock). Worker 1 now on stream F as ordered. 10 Nov AT RISK: 13 packages after the two claimed (S 4, F 9). Self-check PASS; queue check 24 actionable, 0 flagged.

OWNER PACKAGE: none today (no item meets standard section 2.7).

NEEDS FIXING (only you): repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.

