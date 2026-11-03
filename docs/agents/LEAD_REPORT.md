# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

## LEAD REPORT 2026-11-03 00:16 UTC

Drive read OK (nothing created since 20:00). Training villa: candidate of record V3.0.44 8b2fe2b6 (NOT RELEASED); released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, steel 10,250.17 kg).
- Skirting (first finishes Gate B, PASS): FIN.SKIRTING certain 184.017 -> 189.819 lm (+5.802: skirting runs under the W04 / W14 / W24 / W29 sills printed 1.00-1.70 m above the floor), held high 24.638 -> 15.731 (floor-level W15 / W16 out); 4,848 lines byte-identical; L4 NEW 0. Freelancer 282.85 lm gross, no door deduction: RULE_DIFFERENCE. Status: 1F-01 VERIFIED, 3 lines PARTIALLY VERIFIED (gross perimeters not re-walked). Missing: W02 / W11 / W12 / W17 sills, 1F dressing faces -> NEW T-481.
- Concrete blinding: package READY r2 on V3.0.44 (V3.0.45 5972888b): 24 pits 12.734 m3 VERIFIED as its own line, FF raft 2.256..2.352 and beyond-plot 0..0.189 m3 HELD; vs freelancer 47.055 m3 plate -72.9 % = RULE_DIFFERENCE; no other line moves.
- Formwork: census merged (Checker own beam 4.268 m2 and slab soffit 15.108 m2 AGREE); 244 lines 1,027.98 m2 CALCULATED, 388 held blank; not verified, part 2 integrates.
- Materials: rulebook 1.0.0 merged, unwired; Checker hand cases all AGREE with your confirmed rules (lintel 3.70 m opening -> 4.00 piece, 3.71 FLAGGED). Blockwork material ledger (T-453 part 1) released.
- Waterproofing: per-line completeness join merged; LIFT_PIT_SCREED 20.700 m2 / 1.035 m3 whole lines 1 -> 3 at the next export; 18 lines held by name, never 0.
- Tests: PDF reader r4 merged (identity proved on the Checker's adverse page); L4 0 failures on 1d892eb4.
- Learned (lessons rows ADOPTED): skirting continues under any sill above the floor, only doors / floor glazing deduct; an identity proof needs a checker-built adverse input that fails the previous head.
- Gates: Gate 0 none; Gate 1 T-466, T-479; Gate 2 streams S (T-478 at the Checker) and F (T-443 next).
Team health: since 20:14 every closed run wrote STARTED + final line (Worker 1 x3, Worker 2 x2, Worker 3 x2, Verifier x3 incl. 1 overlap-guard), self-checks PASS, no refusal; Checker 6 merged / 0 rejected. Open: Verifier 23:51 (in its lock). LEAD FAULT: my 20:17 board left no claimable TODO for workers 1 and 3 (both runs said so; they used them for a rebase and a lane A row); fixed: TODO 0 -> 9, a non-candidate row behind each stream. 10 Nov AT RISK (about 13 packages, 7 days).
Queue check: 25 actionable rows, 0 flagged, 0 stall checks.

OWNER PACKAGE: none today (no genuine decision under standard 2.7).

NEEDS FIXING (owner only): repository privacy switch (PRIVACY_MOVE_PLAN step 0); released-path PyMuPDF licence decision (F-T465-1, now unblocked: the pypdf reader is merged and proven identical); PR #3 / merged-branch clean-up.

## LEAD REPORT 2026-11-02 20:17 UTC

Drive read OK (nothing new since 16:00). Training villa: candidate of record V3.0.43 6f534d5e (NOT RELEASED); released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, steel 10,250.17 kg).
- Earthworks (missing category, now in the candidate): T-350 Gate B PASS: +18 HELD-blank lines, bounds beside: pits >= 188.017 m3, pool >= 17.777 m3; 4,837 lines byte-identical; L4 NEW 0.
- Scope: EIMP part 2 MERGED (recovery step 1 DONE): 106 components, 0 unmapped / 0 doubly mapped. Gaps -> NEW T-479: 2 candidate lines in no family; master blocks B8-08 / B10-13 / B7-13 stale; verdict set binds 2 / 7 verified B8-08 lines (293.86 m2 + 5.49 m3 under-reported in the Verified share).
- Waterproofing: B8-08 foundation WP 360.028 m2 / 6.528 m3 already carried since V3.0.15 (T-353 re-check, Checker FF lift base 20.700 m2 AGREE); no double count.
- Handrails B7-09: 17.366 -> 33.319 lm proposed (per flight along the pitch); freelancer 18.95 (+75.8 %); PARTIALLY VERIFIED 1 / 14 (MS2-L 3.782209 lm, 0.000 %); 4 pieces HELD, 1 UNKNOWN. Integration NEW T-480 (stream F).
- Lift marble: census = candidate (0.000). Formwork: census READY (244 lines 1,027.977 m2 CALCULATED, 388 HELD); materials rulebook READY.
- Rejected: T-465 r3 (test reader, no BOQ effect): identity fails on fractional font widths (<= 0.0073 pt) -> r4 TODO.
- Learned (lessons rows): rails along the pitch, never plan length (ADOPTED); a printed minimum is a bound, never the quantity (ADOPTED); an oracle-identity claim needs an adverse input corpus (PROPOSED).
- Gates: Gate 0 none; Gate 1 T-465 r4, T-479; Gate 2 streams S (T-478 next) and F (T-422 CLAIMED).
Team health: since 16:14 every closed run wrote STARTED + final line (Worker 1 x2, Worker 2 x2, Worker 3 x2, Verifier x3 incl. 1 overlap-guard), self-checks PASS, no refusal; Checker 5 merged / 1 rejected. Open now: Worker 1 (19:21) and Verifier (19:51), both within their locks. Last report's watch (Checker 15:49 slot) resolved: it ran 16:34. READY 2, TODO 5 (serialised integration). 10 Nov AT RISK (about 14 packages, 7.5 days).
Queue check: 30 actionable rows, 0 flagged, 0 stall checks.

OWNER PACKAGE: none today (no genuine decision under standard 2.7).

NEEDS FIXING (owner only): repository privacy switch (PRIVACY_MOVE_PLAN step 0); released-path PyMuPDF licence decision (after T-465 r4); PR #3 / merged-branch clean-up.

## LEAD REPORT 2026-11-02 16:18 UTC

Drive read OK (nothing new since 12:00). Training villa, candidate of record V3.0.42 (NOT RELEASED); released V2.9 + route G unchanged; no quantity moved since 12:35.
- Concrete / blinding: footing blinding measured as pieces (merged, unwired): 24 pits 12.734 m3 VERIFIED (Checker own re-add 0.0 %); freelancer 47.055 m3 = one 0.10 m plate over the plot rectangle, printed nowhere: RULE_DIFFERENCE, not an engine error. Candidate line 15.179 m3 mixes pits + FF raft HELD 2.256..2.352 (S08) + 0.189 beyond the plot (S06) -> split in NEW T-478.
- Earthworks (missing category): T-350 READY as the first stream S Gate B package: 18 lines HELD-BLANK (formation / working space are designer items), bounds beside only: pits >= 188.017 m3 (+129.234 per m below the printed 1.50), pool >= 17.777 m3. Never a figure in a blank line.
- Scope (recovery step 1): EIMP part 2 READY: 106 components, 0 unmapped / 0 doubly mapped; VERIFIED 1, MEASURED 5, HELD 50, MISSING 25, NA 5, to confirm 20; 2 candidate lines in no family (registry gap).
- Finishes: lift landing marble census READY: B6-07 1.500 m2 / 3.000 m.l and B6-06 HELD 2.750..13.980 m2 = candidate (0.000); freelancer has no row (ENGINE_RIGHT on scope).
- Reinforcement: firewall gate green again (T-477 merged); released steel unchanged.
- Learned: a layer under members is measured as pieces under the members the drawings print it under, each plan area once; a line never mixes VERIFIED and HELD parts (lessons row PROPOSED).
- Missing: formwork (all held), external plaster, spatter dash, masonry accessories / mortar, handrails; materials layer starts now (T-448).
- Gates: Gate 0 none open; Gate 1 EIMP at the Checker; Gate 2 both streams building, first Gate B queued.
Team health: 9 agent runs since 12:24, all STARTED + final line (one Worker 3 IDLE on its own lock, correct), self-checks PASS, no refusal; Checker 2 merged / 0 rejected; READY 3 (limit), CLAIMED 0. Watch: the Checker's 15:49 slot had no STARTED line by 16:16. 10 Nov stays AT RISK (16 packages in 8 days).
Board: released T-353, T-448, T-476, T-452; new T-478; TODO 8. Queue check: 33 actionable rows, 0 flagged, 0 stall checks.

OWNER PACKAGE: none today (no genuine decision under standard 2.7).

NEEDS FIXING (owner only): repository privacy switch (PRIVACY_MOVE_PLAN step 0); released-path PyMuPDF licence decision (after T-465 r3); PR #3 / merged-branch clean-up.
