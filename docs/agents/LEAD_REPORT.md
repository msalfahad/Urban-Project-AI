# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

## LEAD REPORT 2026-11-04 04:17 UTC

Drive read OK (no file created in the project folders since 00:00, no photo task). Training villa: candidate of record now V3.0.50 d40c4ec5 (NOT RELEASED); released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %).
- Earthworks (stream S Gate B PASS, Checker own raw-DXF re-measure): external ground-beam trench 1.203 .. 1.433 -> 1.069 .. 1.176 m3 (-0.134 .. -0.256 m3 double count removed), excavation held part 8.468 .. 9.825 -> 8.334 .. 9.568 m3; valued excavation 225.941 m3 unchanged; 4,875 lines identical. General rule (every zone subtracts every other zone's plan) and its lessons row ADOPTED. No freelancer earthworks line: no comparison.
- Disposal (piece, unwired): one dry-mass balance; no-reuse end at least 234.333 m3 in situ, import at least 128.644 m3; reuse ends HELD (no soil report on Drive). Loss terms missing (Checker F-C-T503-1) -> new piece before any reuse end is valued.
- Material totals (piece, unwired): any subtotal over a HELD row is now HELD with an AT_LEAST known part (was 0.0 on 5 adhesive codes; wall tile 340.30 m2 over 12 / 18 lines). The plaster table has the same defect (4.727 m3 shown over 25 / 52 rows) -> new piece. Materials link map: 1,202 links, 0 wrong.
- Not measured / held: wet-area waterproofing (engineering AGREE, rebase left), skirting remainder +9.010 lm (rebasing), landings +10.588 m2 and pool-court WP 4.907 m2 (unwired), lintels, blockwork, materials not wired.
- Gates: Gate 0 none; Gate 1 t485 registry promotion (red on the working branch, in T-483 r2); Gate 2 three packages building (two finishes, one structural).
Team health: 9 runs since 00:20 all closed with a final line (Worker 2 INCOMPLETE by design: a merge landed mid-run; nothing lost). Checker 4 merged / 1 rejected (test faults only). Worker 1 run open on its lock. Stream F has merged 0 packages since 3 Nov 20:12: 10 Nov AT RISK (about 14 packages in 6 days); 12:00 scope review stands. Self-check PASS (codemap, pytest t061, freeze); queue check 22 actionable, 0 flagged, 0 stall.

OWNER PACKAGE: none (no item meets standard section 2.7).

NEEDS FIXING (only you): the Kuwait 1990 specification is over the 10 MB connector limit, so its plastering chapter cannot be read: a split or zipped copy under 6 MB would let the plaster mix move from HELD to a sourced value. Still open: repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.

## LEAD REPORT 2026-11-04 00:20 UTC

Drive read OK (no file created in the project folders since 20:00, no photo task). Training villa: candidate of record now V3.0.48 33a81c53 (NOT RELEASED); released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %).
- Earthworks (stream S Gate B PASS): first earthworks quantities in the candidate: excavation valued 0 -> 225.941 m3 (pits 208.165 ESTIMATED, Checker AGREE; pool 17.777 DRAWING-CONFIRMED); backfill HELD 119.963 .. 128.644 m3 PARTIALLY VERIFIED 6 / 8; 4,869 lines identical. No freelancer or released earthworks line: no comparison.
- Found by the Checker: the external ground-beam trench bound 1.203 .. 1.433 m3 counts up to 0.256 m3 already dug by the footing and beyond-plot zones; line HELD, corrected scenario 1.069 .. 1.176 m3; fix package first in stream S, general rule (every zone subtracts all other zones) and lessons row.
- Measured and checked, unwired: 4 stair landings 4 / 4 AGREE (B7-04 10.102 -> 20.689 m2 proposed); pool-court slab 4.907 m2 with no waterproofing line (ENGINE_WRONG omission; balcony WP otherwise 0 m2 missing); outdoor floor materials as bounds (finish HELD).
- Skirting remainder (certain 203.369 -> 212.379 lm, +4.43 %) is right in engineering but collided with the earthworks version: rebase + a registry gate fix (one test red on the working branch since 3 Nov 20:12).
- Not measured / held: disposal (now a material-balance task by your 17:45 rules), materials not wired (blocks, mortar, glue, plaster, tiles).
- Gates: Gate 0 none; Gate 1 t485 registry promotion (in the rebase), held-as-0 tile subtotals (to reproduce); Gate 2 three packages in parallel.
Team health: since 20:18 every run closed with a final line; Checker 4 merged / 0 rejected; Worker 3's staged hand-in worked. Worker 1 23:20 found no task (board had 0 TODO): now 8 TODO. 4 Nov review applied: stream F merged 1 package since 2 Nov, so waterproofing / exterior plaster wiring moved to worker 2. 10 Nov AT RISK (about 15 packages left in 6 days). Self-check: codemap PASS, freeze PASS, pytest t061 FAIL (this session's venv has no pytest; board work only); queue check 24 actionable, 0 flagged, 0 stall.

OWNER PACKAGE: none (no item meets standard section 2.7).

NEEDS FIXING (only you): the Kuwait 1990 specification is over the 10 MB connector limit, so its plastering chapter cannot be read: a split or zipped copy under 6 MB would let the plaster mix move from HELD to a sourced value. Still open: repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
