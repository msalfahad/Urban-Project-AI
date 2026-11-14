# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Lead 2026-11-14 20:14 (since 16:13)

- T-796 MAIN FILL overlay precedence + disposal: WORKED (MERGED de1aa003; board view disposal HELD 105.6 .. 115.5 -> 10.477 m3, Checker own B1 sum AGREE; held 5 -> 4).
- T-795 held ranges to points: WORKED (MERGED 26c0b41b; door tile edges 115.2 lm DEFAULT, stair corner 0.23 m2, two space points) -> wire in r11.
- T-788 r2 cornice: WORKED (MERGED c12c8eb4; 426.31 vs 427.46 lm, -0.27 %, PARTIALLY VERIFIED; outdoor pocket -4.138 lm Checker AGREE) -> r11; F-V788-1 adverse test -> NEW T-799 part 2.
- T-770 r10 (V3.0.87 / 1.87.0): WORKED (Gate B PASS 91072069 + promotion df770b00; 20/20 hand AGREE; beam 76.05 m3, upturn 228.99 lm) -> F-V770r10-1 column formwork faces -> NEW T-798.
- T-793 height provider: WORKED (MERGED 939bb281; villa-1 = R-T763-1 exactly, 0 candidate lines changed) -> F-V793-1 floor build-up + wiring into the run command -> NEW T-800.
- T-791 stairs: FAILED r1 (REJECTED: no regression test; GF divider counted as rail AND skirting possible, F-V791-1). Decision: r2 worker 1 first with the exact three fixes in the row; the 12 agreed figures stay.
- Recurring cause: number (b) still not produced on V3.0.86 / .87 (Checker 'not run' x4). Decision: r11 must commit COMPARE_V3.0.88.md from build_boq.py.

## Lead 2026-11-14 16:13 (since 12:19)

- T-770 r9 (V3.0.86 / 1.86.0): WORKED (Gate B PASS 9be5f69a + promotion cb3d2fb1; blank non-rebar 44 -> 18; dome shells 3 x 26.685 m2 Checker DXF AGREE).
- T-790 blockwork views / mesh / sharmat: WORKED (MERGED 28d6336e, wired in r9; block m2 counted once).
- T-786 concrete residuals: WORKED (MERGED a2001238; beam 79.24 -> 76.19 m3, UNRESOLVED 7.13 -> 3.48) -> wire in r10 with F-V786-1 (-0.141 m3).
- T-792 schedule-first column fix rows: WORKED (MERGED 9ff810ac; columns 33.92 -> 33.83 m3) -> r10; provider for a second villa -> NEW T-797.
- T-794 roof upturn: WORKED (MERGED 8f558cef; 232.97 -> 228.99 lm, gap split to causes, his lump -11.89 lm UNRESOLVED named) -> r10.
- T-788 cornice: PARTIAL (READY; result -29.1 % -> +0.70 % but the Checker could not re-measure: polygoniser outside the run allow-list) -> worker 2 adds a research/agents_t788 print script first; Checker first slot.
- Lead finding: board tools apply MAIN FILL overlay over newer wired lines (disposal 10.48 m3 in the index shown as HELD 105.6 .. 115.5) -> NEW T-796; held ranges left -> NEW T-795; number (b) now read from the workbook Compare sheet.

## Lead 2026-11-13 08:25 (since 04:15)

- T-754 exterior paint edge residuals: PARTIAL (MERGED, 4/7 re-walked AGREE: corners 179.54 .. 180.74 -> 176.94 .. 178.14 lm research, not wired) -> NEW T-756 face ledger re-based for T-314 r3; the 3 unverified items re-walked there.
- T-738 tiles + stair finishes Gate B: PARTIAL (quantities AGREE by the Checker's own chain; FAIL only on the t459 binding not rebuilt) -> rework r2 with the exact fault; L-T738-1 PROPOSED.
- T-755 designer re-census: PARTIAL (coverage AGREE; 35 lines on a retired D-63 cause) -> rework r2 (live cause fields only); L-T755-1 PROPOSED; designer list counts not refreshed until it merges.
- Three idle worker runs 06:41-07:20 (each lane's only row READY) -> two reworks + T-756 give every lane a claimable row.

## Lead 2026-11-13 04:15 (since 00:13)

- T-749 paint rule Gate B (V3.0.77): WORKED (FIN.PAINT bounded 604.990 .. 710.006 -> 603.802 .. 687.847 m2; edges as lm lines; released unchanged); L-T749-1 ADOPTED.
- T-752 metalwork census: PARTIAL (9 beam ends counted, trade / kg HELD) -> designer item 17 (D-M1), register ruling; annex lattice railing id -> T-754.
- T-753 joinery census: PARTIAL (geometry by handle, heights / material HELD) -> designer item 18 (D-J1..3); no new task until answered.
- Three idle worker runs 02:40-03:21 (next rows all 'after' a just-READY task, lane S empty) -> T-738 and T-754 TODO, NEW T-755 designer re-census + concrete held-tail sweep for worker 1.

## Lead 2026-11-12 20:14 (since 16:20)

- T-729 formwork Gate B (V3.0.75): WORKED (formwork released 1,027.977 -> 1,061.104 m2) but F-V748-1: the roof membrane record was not applied -> carried by T-736 (one line), lesson L-T748-1 PROPOSED.
- T-743 sanitary census, T-744 tag-not-fixture fix, T-746 opening edges lm, T-748 readiness R6 + scorecard: WORKED (MERGED; no candidate line moved).
- T-747 exterior paint: WORKED as research (paint = render 1,006.633 .. 1,085.613 m2); open lm bounds -> NEW T-751.
- T-745 drain runs: FAILED r1 (scaled lengths from not-to-scale sheets labelled MEASURED, against merged T-380) -> TODO r2 with a Lead ruling; designer item 16; L-T745-1 PROPOSED.
- Worker 1 19:19 idle (no claimable TODO): queue too thin -> T-745 r2 + T-752 for worker 1, T-751 for worker 2, H4 package T-750 written.

## Lead 2026-11-12 16:20 (since 12:20)

- T-741 downgrade issue path: WORKED (MERGED 01f060bd; the Checker issued DG-a429c160, roof membrane L-636fd3ff RELEASED -> HELD).
- T-740 paint rule UP-FIN-PAINT-002: WORKED (MERGED 0f0e0cd0; 3 faces AGREE; paint 841.261 .. 929.205 m2) -> opening edges lm by the owner rule: NEW T-746; exterior paint: NEW T-747; wiring NEW T-749.
- T-739 r2 all-trade statement: WORKED (MERGED 0d3bf6a1; 5,155 lines, causes sha-pinned) -> restated on V3.0.75 in NEW T-748.
- T-742 parapet blocks census: WORKED as a census (MERGED 1370c295; 4 lines HELD on Q-65 C / D-39, designer items; no new question).
- T-743 sanitary census: READY (verdict pending); finding 9 phantom fixtures -> NEW T-744 after it; L-T743-1 PROPOSED.
- T-729 formwork + C10 Gate B: READY (Checker running).

## Lead 2026-11-12 12:20 (since 08:16)

- T-735 formwork conflict decider: WORKED (MERGED 870f15f5; 7 lines one live form each, Checker by hand AGREE) -> T-729 carries them.
- T-734 WP H4 evidence + roof membrane record: PARTIAL (band and +0.018026 m2 excess AGREE; record not issued: wrapper refuses tools/boq_export_v1.py) -> NEW T-741 issue path for the Checker; D-BAND -> designer item 15.
- T-717 plaster / paint Gate B r2: WORKED (MERGED e6481b43, V3.0.74; plaster held 1,106.949 .. 1,302.169, paint 604.990 .. 710.006 m2).
- T-737 exterior plaster readiness: WORKED (MERGED 891c14ea; 2F gross 125.160 m2 AGREE; 43 bead rows re-bound) -> T-314 r3 after T-736; D-GF-07 -> designer item 14.
- T-708 earthworks round 3: WORKED (MERGED a91a1dfe; Z2 reconciled over 90 terms, residual 2e-6; densities HELD) -> T-509 (H5).
- T-739 all-trade aggregation r1: FAILED on one gate (output stale after V3.0.74 merged; 4 hand cells AGREE) -> TODO r2 with the exact fault; L-T717-1 ADOPTED.

## Lead 2026-11-12 08:16 (since 04:17)

- T-731 stair MS1-L coherent reading: WORKED (MERGED in 067b0035; 16 risers by handle AGREE; highs only; F-T725-1 adopted).
- T-720 gross floor area B2-03: WORKED (MERGED 067b0035; 3/3 VERIFIED; no BOQ line -> register family in T-729's master).
- T-733 tiles H3 readiness: WORKED (MERGED 7146583d; treads ENGINE_RIGHT, V-07 NOT_A_VOID) -> wiring T-738.
- T-732 moved-member formwork: WORKED (MERGED 35c0c09e; 7/7 restated; F-T732-1 T-707 lows are upper-bound method) -> T-729.
- T-730 wiring map r5: WORKED (MERGED 6143f30d; 10/10 AGREE) -> C10 into T-729; 6 conflict lines + cap 0 -> NEW T-735.
- T-717 plaster / paint Gate B r1: FAILED on one gate (36/36 by hand AGREE; t459 binding not rebuilt for arch_v3074) -> TODO r2 worker 3 first, exact fault in the row; lesson L-T717-1 proposed.

## Lead 2026-11-12 00:16 (since 20:17)

- T-712 ground beams: WORKED (MERGED dfeb0240; 17 AT_LEAST 5.099845 m3 + 3 court blanks, hand AGREE).
- T-716 designer census: WORKED (MERGED 17aaab4b; per-item counts -> DESIGNER_QUESTIONS.md; F-V716-1 court lines -> D-35).
- T-721 blank beams: WORKED (MERGED 9e1ed6c5; ring AT_LEAST 0.115155 m3; F-V721-1 two drawn levels -> T-724; 0.378618 m2 strip in no line -> T-724).
- T-718 stair finishes r2: WORKED (MERGED 8052ca51; F-V715-1 closed, nosing datum).
- T-703 masonry Gate B: WORKED (MERGED da1a8906; V3.0.72, 28 / 28 by hand, L4 0 fail; F-T703-1 master left pending by T-704 -> lesson L-T703-1).
- T-714 formwork limits: PARTIAL (MERGED e6ebe28a; worker opened no drawing; F-V714-1 soffit ratio 0.2502 vs 0.250) -> T-724 (2); 20 stair formwork lines out of scope -> T-725.
- T-723 wiring readiness r4: WORKED (MERGED 5d00f738; F-T723-1..3 -> T-722 scope; 116 bead rows blocked -> T-728).
- T-719 voids: WORKED (MERGED 302e002d; floor 0.057 m2 double deduction + ceiling 16.005 m2 risk -> T-727; shaft -> T-726).
- Recurring cause: workers restating merged ledgers without a drawing read (T-714, earlier T-715); T-724 / T-725 acceptance asks for a drawing handle per figure.

## Lead 2026-11-11 20:25 (since 16:22)

- T-711 concrete blank tail: WORKED (MERGED 1e06f656; 11 AT_LEAST, 4 blanks named; lift pit walls >= 1.903 m3, freelancer 1.65 below the drawn floor).
- T-713 masonry rest: WORKED (MERGED aa4d8979; 2 parent one-ended bounds) -> wired with T-703 (scope added).
- T-704 r2 lintel Gate B: WORKED (MERGED b211b3a2; V3.0.71, R-T704-2, L4 0 fail).
- T-715 stair finishes: PARTIAL (MERGED a4e4277a; no drawing read in the worker run, F-V715-1 MS2-L skirting 2.25 vs 2.20 m, 5 lines AT_LEAST only) -> T-718.
- Recurring cause: raw Drive downloads refused by decode (PR #6 open) cost one worker its drawing read; owner item stays in NEEDS FIXING.

## Lead 2026-11-11 16:25 (since 12:21)

- T-706 slab / beam residual: WORKED (MERGED 11489726; -0.77 % closed by storey, 1F part a typed reference row; beam -0.128 reference slip).
- T-709 paint / plaster residuals r2: PARTIAL (MERGED fe461c6e; band omission found -> T-717 wiring; 13.50 m2 of the shaft residual UNRESOLVED, shown by name).
- T-704 lintel bounds Gate B: FAILED (REJECTED: new module undeclared in the rebar firewall) -> r2 TODO with ruling R-T704-2 (AT_MOST on one geometry).
- T-707 column tail: WORKED (MERGED f34a5baa; F-T689-1 settled from the drawing, +0.12724 m3; tank pair LOWER_ONLY).
- T-710 waterproofing r3: WORKED (MERGED 4a34ced0; 58 / 58 by cause; recess HELD 0 .. 13.335 m2 on D-41).
- T-705 wiring readiness r3: WORKED (MERGED 8294c146; 287 rows stale 0; hub order H1 -> H5; rulings F-T705-1 / -2 given).
- Owner 15:30: rebar parked (T-664, T-382 parked); designer list started (DESIGNER_QUESTIONS.md, T-716 fills it).

## Lead 2026-11-11 08:25 (since 04:20)

- T-689 column held ranges: WORKED (MERGED 66ffd421; low 0.303 -> 0.3287, 5 blank columns bounded +1.382780 .. 2.231250 m3). Wiring -> T-693 (now TODO).
- T-691 waterproofing round 2: WORKED (MERGED 5e4fdc33; roof 115.832 -> 115.814 m2 by the dome chords, unwired).
- T-692 missing-families census: WORKED (MERGED 8678ddfb; 38 = 32 + 6 by id).
- T-694 concrete statement r3: WORKED (MERGED 510f069d; = index to the digit; PC-2F a designer item D-66).
- T-696 masonry round 3: WORKED (MERGED 5b51924e; 61 blank B9 lines by cause, one-sided bounds). Wiring -> new T-703 (queued after T-693).
- T-687 plaster / paint Gate B r1: WORKED (V3.0.69 published 0b6d1bc2). Plaster >= +32.09 % / paint -31.25 .. -24.48 % vs freelancer -> new T-701 reconciliation.
- T-698 wiring readiness: PARTIAL (REJECTED: 59 held joint-mesh rows read 0 m; owner band called determinate). Decision: TODO r2 with exactly those two fixes + V3.0.69 host restatement.
- Recurring cause: a derived map dropped a ledger's HELD fields (ERS s.7 row PROPOSED).

## Lead 2026-11-11 00:20 (since 20:20)

- T-681 tiles census: WORKED (MERGED ebd8a77d after the Checker's own gate e DXF read). MEASURABLE_NOW 6 + WIRING_GAP 1 -> T-690.
- T-683 concrete statement round 2: WORKED (MERGED 85c1d7aa; V3.0.66 totals = index to the digit; F-T679-1..3 closed). 1F slab -0.556333 m3 UNRESOLVED -> T-688.
- T-685 waterproofing census: WORKED (MERGED 904cdff0; pantry omission measured, unwired). Checker F-V685-1 (released roof membrane above its drawn band, < 1 %) + 4 MEASURABLE_NOW + 18 OPEN_BOUND -> T-691.
- T-684 MS2 1F NW corner: WORKED (MERGED 8563a6fa; flat landing, 0 change; F-V680-1 closed). MS2-TR nosing 1.150 lm -> T-690.
- T-686 plaster / paint round 3: WORKED (MERGED ae9b3d6d; plaster blank 9 -> 3, paint 2 -> 0). F-T686-1 wet band above the ceiling 20.53 m2 -> register ruling (plaster owns) + T-690; wiring with T-687.
- T-180 P18 ground slab: PARTIAL by design (26 / 26 AGREE; GB part HELD). F-V-P18-2 -> T-688 (b).
- T-682 concrete Gate B round 6: READY, in review (CHECKER-RUNS 0).
- Recurring cause (5 runs): the decode wrapper does not accept the connector's raw-binary downloads (one run saw a silent short write): NEEDS FIXING for the owner; workers keep re-encoding and must compare byte counts.

## Lead 2026-11-10 20:20 (since 16:25)

- T-677 concrete Gate B round 5: WORKED (MERGED 8a28bce5, V3.0.66 published 11d94e99; 5,054 byte-identical, 21 changed, 1 added; one slab / BAND0038 double count removed). Closed.
- T-678 concrete open items: WORKED (MERGED f8515d4b; 9 of 22 OPEN BOUND bounded, 778 = PC-2F 0.1824 .. 0.350 m3, C3 low 0.41175). Wiring -> T-682 with F-V678-1 / -2 as acceptance.
- T-679 concrete statement: WORKED (MERGED 4c6726ce; V3.0.65 totals reproduced to the last digit). F-T679-1..3 -> T-683 (restated on V3.0.66). Handoff over 600 characters (flag only).
- T-680 plaster / paint round 2: WORKED (MERGED 707c624e). F-T680-1 -> T-686; Checker F-V680-1 (1F NW winder pattern vs T-184 landing) -> T-684 + register entry.
- T-681 tiles census: READY, Checker PARTIAL (a-d PASS; gate e 2-room re-measure owed because the run went to T-677 Gate B). No worker rework; Checker first slot.
- Worker 1 19:21 found no claimable row (W3 took T-679 while the hub was in review, W1 had T-678 done): Lead fault, the second lane S row was the one W3 takes. Fix: T-683 and T-684 both lane S plus T-682 in lane I, so W3 has its own row first.

## Lead 2026-11-10 16:25 (since 12:20)

- T-668 concrete Gate B round 3: WORKED (MERGED 033b52b9, V3.0.64 published; 5,066 lines byte-identical). Closed.
- T-671 concrete Gate B round 4: WORKED (MERGED 271ba60f, V3.0.65 published; COLUMN held 9.168 .. 13.602 -> 9.6702 .. 12.414 m3, 5 CN not applicable with evidence). Outline 778 UNRESOLVED -> T-678 (b); annex C3 low -> T-678 (c).
- T-673 concrete outside B10: WORKED (MERGED 15d03afc; census 49 = index; 16 lintels 0.925 .. 1.496412 m3 + ST-03 steps 0.355017 m3, Checker 3 / 17 re-measured). Wiring -> T-677; 22 OPEN BOUND -> T-678 (a).
- T-674 ground slab: WORKED (MERGED bb4ec90b; 5 lines 2.141320 -> 2.143747 m3; P18's -0.084731 was mostly own-read artefacts). Wiring with BAND0038 -> T-677; P18 closable after it.
- T-675 masonry round 2: WORKED (MERGED e0984b13; MAIN_S / ANNEX_S black by ST p.1 note 2). Added to T-672 scope.
- T-676 plaster / paint census: WORKED (MERGED cffefa0c; 57 HELD classed, OP-009 reveal 1.08 m2). F-T676-1 -> T-680; OP-009 to the plaster Gate B after T-672.
- Worker 1 15:23 found no claimable row (T-674 taken by Worker 3): Lead fault again, one row per research lane. Fix: two independent TODO rows per research lane (T-678 / T-679, T-680 / T-681), stated as 'independent' so the board check does not read them as WAITING.

## Lead 2026-11-10 12:20 (since 08:20)

- T-670 masonry materials: WORKED (MERGED 91a74d45; black units AT_LEAST 1,075.80 -> 2,571.28 pcs, mortar 1.269 -> 2.593 m3 PROVISIONAL; unwired). Into T-672; F-T670-1 -> T-675 (a).
- T-669 concrete close-out + census: WORKED (MERGED 8cb64551; corner square owned, residual 0; 5 2F column lows 1.6362 .. 2.295 m3; census 144 = master). Corner wired in T-668; column lows, CN x5, T-642 split -> T-671; F-C-T669-1 -> T-671; F-C-T669-2 (49 lintel / stair lines outside B10) -> T-673.
- T-372 research part: WORKED (MERGED dc1ac41e; 8 perimeter mortar lines 0.176727 .. 0.188035 m3, own re-measure AGREE). F-C-T372-1 .. -4 -> T-672 acceptance; F-T372-1 / -2 -> T-675.
- T-180 P18 ground slab: PARTIAL 21 / 26 (5 lines -0.084731 m3 below the drawn panels) -> T-674 drawing-only fix, then T-671 wiring.
- Worker 1 11:20 found no claimable row: Lead fault (board left with 1 TODO per lane after the 08:20 rows were all handed in by 10:51). Fix: 6 new rows, 5 TODO, two per research lane independent of each other.
- Worker 3 11:00 IDLE (own run lock, 09:01 run still active): correct stop.

- T-661 concrete Gate B: WORKED (published 7a9ccbff by the Verifier 04:21; row status corrected to MERGED by the Lead 08:16).
- T-667 pool blinding + steps: WORKED (MERGED b89ea23f; new HELD LOWER_ONLY >= 0.915529 m3, steps HELD; unwired). Into T-668.
- T-666 junction squares + boundary band: WORKED (MERGED 06e2e736; residual 0, band no double count, stays HELD; unwired). Into T-668.
- T-665 concrete round 2: WORKED (MERGED 12acd3d4, published b5df949c, V3.0.63). F-T665-1 corner square -> T-669 (a); F10 third reading not wired: no row (D-43 designer item, no released quantity moves).
- Verifier 07:51 INCOMPLETE (overlap guard): correct stop. Lesson PROPOSED 04:14 (MERGED only after engine push + ls-remote) was applied by the Verifier at 08:05: ADOPTED.

## Lead 2026-11-10 04:14 (since 00:20)

- T-658 r2 columns / GB / straps / footing: WORKED (MERGED 2cec1520; GB 9 bounded 1.173410 .. 5.096771 + 16 LOWER_ONLY 5.069839 + 4 blank; Checker own outlines AGREE). Into T-665 (worker 3).
- T-663 ratio wiring conditions: PARTIAL (MERGED b09d6ed4; conditions settled, 0 of 28 rows wiring-ready: no readable book prints kg/m3). Decision: T-664 BLOCKED-OWNER Q-81 (no new question).
- T-661 concrete Gate B: PARTIAL (Gate B PASS 03:43, V3.0.62; merge ea1533e4 NOT on origin; Verifier run 02:51 left no final line). Decision: READY PUBLISH-ONLY, Checker FIRST re-merges 6d40475f with `engine push`; lesson PROPOSED (MERGED only after the push is seen on origin). Follow-ups from its verdict: T-666 (F-T661-1 junction squares + boundary band), T-667 (pool blinding MISSING).
- Verifier 03:51 INCOMPLETE (overlap guard): correct stop.

## Lead 2026-11-10 00:16 (since 20:18)

- T-657 necks: WORKED (MERGED d96a2958; 36 lines 3.075 .. 15.375 -> 32 bounded 8.7724 .. 11.3460 + 4 lift LOWER_ONLY 0.9515 m3; 5 necks re-measured AGREE). Into T-661.
- T-659 small elements: WORKED (MERGED 907ace46; 6 bounded 13.279574 .. 24.498998 m3, band 5.6392 .. 11.0328; pool blinding MISSING found). Into T-661; pool blinding row after the hub.
- T-660 beams: WORKED (MERGED 9c91709f; 1 value 0.549624 + 14 bounded 5.983085 .. 8.412278 + 12 blank with plan 8.746 m2; 5 / 5 re-measures AGREE). Into T-661.
- T-662 rebar ratio calibration: PARTIAL (MERGED 169a4df2 as research; ESTIMATE 2,204 .. 2,909 kg; Checker named 3 wiring conditions; 6 types uncalibrated). Decision: T-663 (worker 2) clears the conditions; T-664 wires; owner Q-81 for the 6 types.
- T-658 r1 columns / GB / straps / footing: FAILED Gate A (oblique spans on the short edge; D-33 runs given a high from unloaded titles). Decision: r2 worker 1 FIRST with the exact fault; lessons row PROPOSED.
- W3 21:00 INCOMPLETE (commit refused '[Sensitive-Source Provenance]'): cause fixed by keeping raw drawing reads in .work/private; the re-run published at 23:10. No further action.

## Lead 2026-11-09 16:17 (since 12:23)

- T-423 r3 Gate B step 3: WORKED (MERGED 62e18eed, 22 lines text-only, 0 quantity moves). Left T-423 pending in the newest master (t485 red) -> T-655.
- T-653 Decimal precision fix: WORKED (MERGED db8898c1, L4 0 F). F-T653-1 (t627 relies on t568 context) -> T-656 worker 1.
- T-563 Gate B step 4: WORKED for the quantities (MERGED e04d99d9, 11 FIN.PLASTER lines = T-556 exactly, paint unchanged), PARTIAL for the registry (its master 1.61.0 kept V3.0.60 and V3.0.61 pending: F-C-T563-1) -> T-655 worker 2 FIRST. F-C-T563-2 -> T-654 now TODO.
- T-314 r2: PARTIAL (INCOMPLETE stage 080ccaa5, correct stop on F-T314-2, figures = r1). Decision: the t199 helper fix goes into T-655; T-314 r3 resumes after it, master 1.63.0.
- W1 13:28 / 15:23 and W3 15:01 no claim: correct under the one-at-a-time Gate B order; each lane now has a first TODO (T-656 / T-655 / T-654).

## Lead 2026-11-09 12:20 (since 08:22)

- T-648 r2 finishes causes: WORKED (local Decimal context, outputs byte-identical, 198 -> 0 lines without cause). F-T648-2 (same fault in 19 merged research files) -> T-653 W2 FIRST.
- T-651 registry gate fix: WORKED (master 1.59.0 promotes V3.0.59; t485 green; census AGREE). Lesson ADOPTED: promotion travels with the merge.
- T-652 V19 + trial BOQ r3: WORKED (HELD with cause 2,728 / 2,740; 0.15 m hosts 2,194.1375 pcs ENGINE_RIGHT vs Lead 2,232.14). F-C-T652-1 + F-T652-1 -> T-654 (r4 after T-563).
- T-423 r2: PARTIAL (INCOMPLETE stage, correct: master 1.60.0 needed T-651 merged). Decision: r3 done the same day, READY 12:08, Checker next.
- W2 10:40 no claim: correct refusal under the Gate B claim order; W2 now has T-653 first so its next run is not empty.

## Lead 2026-11-09 08:20 (since 04:19)

- T-498 blockwork materials (Gate B step 2): WORKED (V3.0.59 4,999 same + 74 added; Checker own chain + 9 valued lines by hand AGREE). F-C-T498-1 stale cause on the 0.15 m hosts (Q-80 answered) -> T-652 values them from FR-T615. Merge left t485 red (T-498 pending in master 1.58.0) -> T-651 FIRST in lane I.
- T-647 r2 structural causes: WORKED (17 B11 lines HELD COUNT-CONVENTION GAP, 51.574073 kg bound, R-T647-1 (e)/(f) normal + adverse). Decision: into V19 (T-652).
- T-649 V18 + trial BOQ r2: WORKED (Checker own re-add B11 9,628.462205 kg and B7 AGREE; HELD with cause 2,351 / 2,744). Decision: base of V19 + trial BOQ r3 (T-652).
- T-635 statement V12 + scorecard V12: WORKED (VERIFIED rows 24 -> 52, UNKNOWN 295 -> 155; Checker hand re-add AGREE). F-C-T635-1 (B10 beams COUNT rows PARTIALLY VERIFIED) -> T-652 restates.
- T-648 finishes causes: FAILED at the merge gate (global Decimal precision at import broke t647 / t649 rebuilds in one session). Decision: r2 W2 FIRST, local context, one-session run of the merged suites.
- T-314 exterior plaster (Gate B 5th): PARTIAL (INCOMPLETE stage 37bc1c27; claimed ahead of the owner order and blocked T-423 r2 / T-563 on the m9 hub). Decision: TODO r2 after T-648 r2; Checker only after T-563 MERGED.
- T-650 re-measure (Checker light slot): D-1F-07 HELD BY NAME 0.036 .. 0.04377 m3 (START bearing 0.259 < 0.40), L-GF-01 re-measured. Decision: into V19 (T-652).

## Lead 2026-11-09 04:15 (since 00:19)

- T-646 B13 roof layers + fence finishes 43 HELD blank: WORKED (43 / 43 classed; screed AT_LEAST 10.628996 m3 .. OPEN; Checker own ROOF-430 screed and F-NORTH faces AGREE). Decision: rows into V18 (T-649).
- T-525 registry gate fix: WORKED (master 1.57.0 promotes T-507 only, t485 green, Checker reproduced the Drive chain V3.0.58 c9570e6c). Decision: T-649 / T-498 build on master 1.57.0; F-T525-1 stale B8-06 text cleared in T-649.
- T-650 lintel payable form: WORKED (60 / 60 RC cast m3 under the printed schedule; B9-02 low 0.502 -> 0.991692 m3, high OPEN). Decision: V18 (T-649) after the Checker's two missing re-measures (D-1F-07, L-GF-01); F-T650-3 ruled by the Lead this run.
- T-647 structural HELD causes 183: PARTIAL (REJECTED narrow: 17 B11 fix rows 51.574 kg called DRAWING-CONFIRMED on a count the drawing does not print). Decision: r2 TODO W1 FIRST, those 17 rows HELD as a count-convention gap with an adverse test; the rest of ec383e02 kept.
- T-633 blockwork 39 UNKNOWN rows: WORKED (own 231.6726 vs stated 231.6737 m2, residual -0.0011 TOLERANCE; D-GF-06 head class RD -> ER proposed). Decision: class move into statement V12 (T-635).
- T-498 blockwork materials (Gate B, owner order 2nd): CLAIMED W3 03:01, still running at 04:15. Decision: Checker's first Gate B slot when READY; T-423 r2 waits on its files.
