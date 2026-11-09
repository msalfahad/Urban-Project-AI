# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

## LEAD REPORT 2026-11-09 20:16 UTC

Drive read OK (no file created in the Alsenan project folder since 16:00 UTC 9 Nov, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.61 / master 1.62.0 (NOT RELEASED); released V2.9 + route G unchanged; NO candidate quantity moved since 16:17 (every trade before = after).
- Owner 18:30 change of focus APPLIED: concrete -> rebar by ratio -> masonry -> plaster / paint -> tiles -> WP -> earthworks -> missing families. Concrete baseline (trial BOQ r4, B10 m3): released 284.62006 m3 on 294 lines (62.027098 WIRED with a Checker binding, 18.979328 overlay, 203.613634 unverified); 140 HELD = 95 bounded 37.518976 .. 73.227539 + 45 blank (necks 36, columns 29, ground beams 29, beams 27, blinding 6, parapets 4, lift 2, straps 2, footing / dome / pool / boundary pad / wall 1 each). Rebar baseline B11: released 9,628.462205 kg detailed; 799 HELD blank + 900 bounded 15,130.87 .. OPEN.
- New rows (each names its line ids, drawings, rules, fixture, Checker re-measure): T-657 necks (W1), T-658 columns + ground beams + straps + footing (W3), T-659 small elements (W2), T-660 beams (W1 next), T-662 rebar ratio calibration from this villa's counted members, ESTIMATE label, +3 .. 5 % as a range (W2 next), T-661 concrete Gate B + F-T655-1 helper (W3 after the first piece merges). T-314 r3 exterior plaster QUEUED after T-661 (stage kept, nothing abandoned).
- MERGED since 16:17 (all WORKED, 0 REJECTED): T-654 trial BOQ r4 (10 Nov, held as ranges, 2,730 / 2,742 with cause); T-655 master 1.62.0 (t485 green); T-656 t627 Decimal context. Checker VERIFIED T-180 P15 ext GB trench plan and P16 B10 beam COUNT rows GF 4.576422 / 1F 5.306035 m3 (own +0.014 / +0.017 %).
- Learned: PROPOSED (Lead process) an owner re-plan reaches the board within one Lead run AND, if the next worker slot is before it, as a one-line TODO note by the main chat: 4 empty slots 18:40-19:51 (W2, W3, W1, Checker) because the 18:30 re-plan had no rows. ADOPTED from 16:17: a rebased package promotes its merged predecessor (T-655 showed it); registry tests pick writers among governed files (t199 fixed, t328 / t284 in T-661).
- Gate: lowest open gate 1 (concrete pieces). Next Checker light run: T-180 P17 footings (64.304 m3), then P18 ground slab.
TEAM HEALTH: since 16:16 13 runs, all closed, 0 UNCLOSED; 4 MERGED, 0 REJECTED; 4 empty slots (correct: nothing claimable until this re-plan). All self-checks PASS (Lead too). READY 0.
OWNER PACKAGE: none (no section 2.7 decision; designer items keep their lines HELD with drawn bounds).
NEEDS FIXING: (1) The scheduled worker prompts still say 'never approximate steel rates'; the board / brief override them for this BOQ (main chat noted it cannot edit scheduled tasks): only you can align the prompts. (2) Scout paused since 27 Oct: no action unless you want it back.

## LEAD REPORT 2026-11-09 16:17 UTC

Drive read OK (no file created in the Alsenan project folder since 12:00 UTC 9 Nov, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.61 / master 1.61.0 (NOT RELEASED); released V2.9 + route G unchanged.
- Gate B step 4 MERGED (T-563 e04d99d9): plaster height to the slab / roof soffit (Q-72) wired into the 11 dry FIN.PLASTER lines. Released FIN.PLASTER 580.5819 -> 363.3738 m2 (-217.2081 m2, -37.4 %): 4 lines move from released to HELD 262.018 .. 262.052 m2 (+20.6 % on their old 217.21) because the roof build-up is not printed (D-39 / DCR-6, designer item, held never 0); 11 lines bound 840.646 .. 895.896 m2. FIN.PAINT 76 lines byte-identical. Checker own re-measure 1F-01 face 17.70 m AGREE 0.00; 4 / 11 rooms PARTIALLY VERIFIED, 0 new whole lines VERIFIED. Freelancer flat 3.60 / 3.40 / 3.50 m = RULE_DIFFERENCE (Q-72).
- Gate B step 3 MERGED (T-423 r3 62e18eed): 22 lines text-only (thresholds, dome ceiling lists, D-1F-04 1.760 m2 face move); 0 m2 / m3 / kg moved.
- Gate-0 fix MERGED (T-653 db8898c1): no process-global Decimal precision in 17 research modules; L4 21,843 pass 0 F. Lesson ADOPTED.
- Worse / found: t485 RED on the working branch since 14:31 (T-423 and T-563 pending in master 1.61.0; second time after T-498). New t199 helper false failure blocks T-314 (F-T314-2). Both -> T-655 gate 0, worker 2 first; T-314 r3 (step 5, exterior plaster 1,007.93 .. 1,085.61 m2 vs freelancer 1,469.97 m2, -31 .. -26 %, reference only) right after.
- Learned: PROPOSED a package rebased on a merged predecessor promotes it in its own master; registry tests pick writers among the files they govern.
- 10 Nov: trial BOQ r4 (T-654, worker 3 first at 17:00) on the newest master, carrying steps 3-4. Gate: lowest open gate 0 (T-655, T-656).
TEAM HEALTH: since 12:23 12 runs, all closed, 0 UNCLOSED; 3 MERGED, 0 REJECTED; 1 INCOMPLETE stage (T-314 r2, correct stop on a new failure, saved); 2 correct overlap-guard INCOMPLETE (Checker); 3 empty worker runs (W1 13:28 / 15:23, W3 15:01: no claimable row under the one-at-a-time Gate B order; all three lanes now have a TODO). All self-checks PASS. READY 0.
OWNER PACKAGE: none today (no section 2.7 decision).
NEEDS FIXING: (1) Scout paused since 27 Oct: no action unless you want it back. (2) venv incomplete at first use seen twice today: watch only.

## LEAD REPORT 2026-11-09 12:20 UTC

Drive read OK (no file created in the Alsenan project folder since 08:00 UTC 9 Nov, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.59 / master 1.59.0 (NOT RELEASED); released V2.9 + route G unchanged; no candidate quantity moved since 08:20.
- Registry (T-651 MERGED 26af97af): master 1.59.0 promotes V3.0.59 (B9-04 INTEGRATED); t485 green; Checker census AGREE (4,999 same + 74 added).
- Trial BOQ r3 for 10 Nov (T-652 MERGED 2e80c03f, non-candidate): HELD with committed cause 2,351 / 2,744 -> 2,728 / 2,740 (12 left = register lines). B9 0.15 m black hosts (pcs, Q-80 ASSUMED - OWNER-APPROVED 12.5 / m2): 2,194.1375 pcs + HELD 0 .. 4.25; my 2,232.14 counted RC lintel faces as block: ENGINE_RIGHT (Checker own re-add). B9 totals re-added: pcs 3,269.9375, mortar 3.387982 m3, glue 20.061 kg + HELD 852.22 .. 885.60 kg. D-1F-07 lintel HELD 0.036 .. 0.04377 m3 (designer item). MS1-L tread 3.105 m2 / step 10.35 lm -> HELD (shared riser count, C-ST-4).
- Finishes causes (T-648 r2 MERGED 57db7053): 198 -> 0 lines without cause; no quantity moved.
- Gate B step 3 (T-423 r3 READY bdbbb8db): V3.0.60 / master 1.60.0, 22 lines text-only (14 thresholds URBAN_METHOD, 5 dome ceiling lists, D-1F-04 1.760 m2 tile/plaster face move, 1 porcelain strip); 0 m2 / m3 / kg moved; engine vs freelancer unchanged.
- Worse / found: F-T648-2 global Decimal precision at import in 18 research modules + 1 m9 fixture -> t647 / t649 fail in full sessions (order-dependent) -> T-653 gate 0.
- Learned: ADOPTED registry promotion travels with the merge; Gate B order is a claim order; every HELD line carries a committed cause. PROPOSED no process-global numeric state (test in T-653).
- Gate: lowest open gate 0 (T-653). Next: T-423 r3 Checker -> T-563 (step 4, W3) -> T-314 r2 (step 5, W2 after T-653) -> trial BOQ r4 (T-654).
TEAM HEALTH: since 08:22 11 runs, all closed with a final line, 0 UNCLOSED; 3 MERGED, 0 REJECTED, 1 INCOMPLETE stage (T-423 r2, correct dependency stop, r3 READY 1h45 later); 1 correct no-claim (W2 10:40); all self-checks PASS; W3 11:05 hit an incomplete venv again (fixed by re-running setup). READY 1. queue check: see final line.
OWNER PACKAGE: none today (no section 2.7 decision).
NEEDS FIXING: (1) venv sometimes incomplete at first use (W3 11:05; setup rerun fixes it): watch only. (2) Scout paused since 27 Oct: no action unless you want it back.
