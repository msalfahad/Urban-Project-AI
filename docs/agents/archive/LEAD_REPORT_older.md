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

