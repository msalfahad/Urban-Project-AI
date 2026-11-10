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

## LEAD REPORT 2026-11-09 08:20 UTC

Drive read OK (no file created in the project folders since 04:00 UTC 9 Nov, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.59 / master 1.58.0 (NOT RELEASED); released V2.9 + route G unchanged. Gate B step 2 MERGED: the first quantities wired into the candidate since the 12:40 directive.
- Blockwork materials B9 (pcs / m3 / kg, WIRED into the candidate; the Checker re-added all 9 valued lines by hand): black units 1,075.80 pcs; black-block mortar 1.269444 m3 PROVISIONAL (1:4, Q-78); AAC glue 43.596 kg + range 842.06025 .. 861.32025 kg; 65 lines HELD blank by name; freelancer no comparable row (RULE_DIFFERENCE). Before -> after: B9 material lines 0 -> 74 (4,999 other lines byte-identical). F-C-T498-1: 0.15 m hosts 178.571 m2 still HELD 'module not stated' though Q-80 is answered -> valued in V19 (T-652), expectation 2,232.14 pcs before the stated rounding rule.
- Gate broken by that merge: t485 'a merged package never stays pending in the newest registry' FAILS on abc71ec6 (['T-498']; Lead reproduced) -> T-651 master 1.59.0 promotes V3.0.59, top of lane I, no quantity moves. Lesson PROPOSED: an integration package that merges must leave the registry promoted in the same merge (second time after T-507 / T-525).
- Rebar B11 (kg, paper, trial BOQ r2): calculated 9,787.750205 -> 9,628.462205 (-1.63 %, 4 validated downgrades HELD, D-39); 17 lines 51.574073 kg HELD COUNT-CONVENTION GAP (A / A+1 bars, both stated, never 0). Freelancer NOT_COMPARABLE (typed lump).
- Stairs B7 (paper): risers 1.96 -> 8.796036 m2, flights 0 -> 13.36392 lm; MS1-L tread / step downgrade PROPOSED (F-T645-1), not applied.
- Lintels B9-02 (m3): Checker re-measured D-1F-07 (START bearing 0.259 < printed 0.40: HELD BY NAME 0.036 .. 0.04377 m3, designer item) and L-GF-01; low 0.991692 m3, high OPEN unchanged.
- Statement / scorecard V12 (12-13 Nov input): VERIFIED rows 24 -> 52 (Checker own re-measure only), UNKNOWN 295 -> 155, lines UNKNOWN 17 -> 9; no quantity moved; F-C-T635-1 B10 beam COUNT rows 9.882457 m3 restate PARTIALLY VERIFIED.
- Trial BOQ r2: HELD with committed cause 2,351 / 2,744 (was 2,314 / 2,750); 393 still without (finishes part waits on T-648 r2). r3 for 10 Nov in T-652.
- Exterior plaster (T-314 stage, not checked): FIN.EXT.FINISH HELD blank -> 152.005 m2 point + 13 bounded lines, net 1,007.93 .. 1,085.61 vs freelancer 1,469.97 m2 (-31 .. -26 %, REFERENCE COMPARISON only).
- Learned: PROPOSED (1) no process-global numeric state in research modules (T-648 Decimal prec 40 broke two committed rebuilds; Checker now greps getcontext / prec), (2) registry promotion travels with the merge (T-651), (3) Gate B order is a claim rule too: a later step may not hold the shared hub while an earlier step is unclaimed (T-314).
- Gate: lowest open gate 0 (T-651). Next: T-651 -> T-423 r2 (Gate B 3) -> T-648 r2 -> T-652 trial BOQ r3 -> T-563 (4) -> T-314 r2 (5).
TEAM HEALTH: since 04:19 11 runs, all closed with a final line (Verifier 05:50 INCOMPLETE correctly by the run lock), 1 run with no claim (W3 07:00, correct: hub held by T-314); 4 MERGED, 1 REJECTED (T-648; the Checker pushed the merge before reading the combined result and reverted it in 2 min, self-reported), 1 INCOMPLETE stage; all ran code, self-check PASS; no 'No module named pytest' reported since 04:19 and none in this Lead run. Process fault: W2 claimed T-314 out of the owner's Gate B order -> written into the T-314 row. queue check: 15 actionable rows, 0 flagged, 0 stall checks (after fixing 2 Lead-made rows).
OWNER PACKAGE: none today (no section 2.7 decision).
NEEDS FIXING: (1) venv incomplete at first use (watch: not seen this cycle). (2) Scout paused since 27 Oct: no action unless you want it back.

