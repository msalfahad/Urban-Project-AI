## 2026-10-29 20:30 (lead run; covers 16:30 - 20:30)

## Lead 2026-11-01 16:15 (since 12:20)

- T-428 concrete roll-up r4: WORKED (first pass; Checker reproduced r3 -> r4 by family delta, O-T428-1 ruled). Decision: T-433 TODO on the r4 HELD -116.428339 m3; the 9 no-owner unexplained parts (-2.594514 m3) become T-436 (ground slab -1.560570) and T-437 (other -1.033946).
- T-434 winder turn: WORKED (first pass; Checker own section raster 0.1667 m / riser). Decision: lane I items into T-429 (same family); subdivision to the designer list D-67.
- T-421 stair-room floors + lift marble (Gate B): WORKED (first pass, V3.0.38). Decision: T-429 TODO first in lane I.
- T-432 ST-02 length basis: WORKED (first pass; result UNRESOLVED by evidence, which met the acceptance). Decision: the worker's second-drawing conflict (27 vs 28 risers) becomes T-438 and D-68 (draft, not for sending).
- T-435 ceiling / skirting join: READY (not classified until the verdict). Provisional: T-431 acceptance creates the dining ceiling line; T-439 / T-440 / T-441 opened from its findings.
- Recurring cause (new): a dependent row stays QUEUED for up to 4 h after its dependency merges (Worker 1 idle 15:21). Decision: keep 3-4 independent TODO in lanes S and A; the claim-on-dependency rule is a main-chat item.

- T-340 reveals / sills / thresholds FILL: WORKED (Gate A PASS 16:58; W02 head 6.331578 x 0.080 = 0.506526 vs 0.5064 own (0.025 %), D-1F-03 / D-1F-04 thresholds 0.000 %; D-GF-10 0.797 width proposal NOT ADOPTED: the wall line overruns the 0.800 frame by 2.961 mm). Decision: none; T-326 / T-327 consume it in lane I order.
- T-339 roof build-up FILL: WORKED (Gate A PASS 17:01; 1F terrace zone 38.355 / footprint 5.553 / finish hatch 31.6433 m2 own; D band ranged). Decision: none; T-328 consumes it.
- T-344 label census V2: WORKED (Gate A PASS 17:10; own run 41 = 28 / 1 / 1 / 11, SILENT_OMISSION 0, V1 byte-identical). Decision: none.
- T-345 porcelain trace: WORKED (Gate A PASS 19:02; 5.890817 m2 traced to 0.000000: concave winder clipped convex +0.353736, F1 / F4 overlap deducted twice -0.057558, residue 2.034669 + footprint 3.559930; net 33.711036 unchanged). Decision: T-246 SCOPE ADDED (consume the trace rows; write a re-netted line's list with its net in the new candidate version file).
- T-338 export line-state text (V3.0.24): WORKED (Gate B PASS FIRST TIME 20:14; 366 lines text / state only, quantities byte-identical; T-334 check 351 REFUSED + 15 FLAG -> 0; L4 NEW 0). Decision: T-343 TODO on V3.0.24, first in lane I; the 4 PROVISIONAL finish lines without canonical deductions go with T-246.
- T-333 r2 / T-346: READY 19:05 / 19:01 (CHECKER-RUNS). T-346 found no missing face (93.150 = 79.213 drawn + 9.000 double count + 4.937 named, residual 0); F-T346-1 -> NEW T-348.
- T-332 r2: NOT CLAIMED for 4 h. Cause: its status cell began 'REJECTED (rework r2 CLAIMABLE ...)'; Worker 1 at 19:21 read every row as non-claimable and idled. Decision: a CLAIMABLE rework now always begins with TODO (row fixed); worker 1 takes it first.
- Missing categories (BOQ_FAMILY_MASTER 1.19.0: 18 NOT_IMPLEMENTED): NEW T-347 earthworks binding + T-350 lines, T-349 spatter dash binding, T-351 kitchen / laundry / pantry tile zones, T-352 stair formwork, T-353 foundation WP lines, T-354 soil treatment evidence.
- Recurring (unchanged, every code agent): Drive raw binary vs base64-only decode (4 runs since 16:30 worked round by hand); the auto prepare left the venv without pytest once more (Worker 1 19:21, repaired by setup).

## 2026-10-29 16:30 (lead run; covers 12:30 - 16:20)

- T-342 M2 label binding: WORKED (Gate A PASS 14:39; Checker own census 41 labels reproduced; AT19 = pool by position inside the water D; pool is a D not a circle, deck 7.9392 -> 7.1058 m2; M2 MET on rooms and openings for P7757 on this ledger). Decisions: NEW T-343 outdoor floor lines (lane I, after T-338), NEW T-344 census tool v2 (lane A) so the tool stops printing SILENT_OMISSION for bound labels; lessons row ADOPTED (research scope).
- T-319 parapet RC line family: WORKED (Gate B PASS FIRST TIME 15:45; candidate of record V3.0.23; 4 lines HELD BLANK with bound >= 8.050943 m3; 2F ring 5.415 m2 -> 1.6245 m3 0.000 %; 3,706 lines byte-identical; L4 NEW 0). Decision: T-338 TODO on V3.0.23; F-T311-C2 band and divider CEC / CED placed in the element register.
- T-341 deductions FILL: WORKED (Gate A PASS 15:45; 40 / 41 lines close; 1F-01 plaster 51.415 own 0.000 %). PARTIAL element: 1F porcelain L-b06400d4 5.890817 m2 UNEXPLAINED, correctly left unfilled. Decision: NEW T-345 trace (lane S) before T-246.
- T-337 exterior plaster / Sigma FILL: WORKED (Gate A PASS 16:06; 2F ring 125.160 / 14.900 own 0.000 %; closure 1,017.948 residual 0). Freelancer rows 65 / 68 / 69 93.150 m2 with no drawn face. Decision: NEW T-346 investigation (lane A).
- T-332 formwork binding: PARTIAL (REJECTED 13:25, narrow r2: FILL writer turns 201 HELD rows into 0.000000 and 25 unbounded rows into 0 .. 0; every re-measure sound). Decision: rework r2 CLAIMABLE, worker 1 first; acceptance = blank m2 / bounds where no bound, test on the committed CSV.
- T-333 blockwork binding: PARTIAL (REJECTED 13:30, narrow r2: 3 established parts 47.3866 m2 deduct a Q-55 2.20 m door yet carry DRAWING-CONFIRMED). Decision: rework r2 CLAIMABLE, worker 3 first (blocks T-279); rule in binding_fill.py with normal + adverse test.
- T-339 roof layers binding / T-340 reveals binding: READY 16:21 / 16:02 (CHECKER-RUNS).
- Supervision note: the 12:30 lane order did not yet carry the two 13:25 reworks, so worker 1 took T-339 next (in its order) and the reworks waited 3 h: no fault of the worker; reworks now first in their lanes.
- Recurring (every code agent, every run): Drive connector saves raw binary, `agent_env.sh decode` accepts only base64; worked round by hand in scratch (5 runs today). The automatic prepare leaves the venv without pytest (Worker 1 16:21, Worker 2 13:44, Verifier earlier; fixed by one `setup`). Both stay in NEEDS FIXING (wrapper is the owner's main chat's file).

## 2026-10-29 12:30 (lead run; covers 08:20 - 12:30)

- T-330 export canonical-deductions check: WORKED (Gate A PASS 09:48; Checker re-ran on V3.0.21: 41 FLAG / 0 REFUSED, hand check L-af9621f4 +15.33 % over-read with an empty list). Decision: FILL table NEW T-341 (lane S) for T-246.
- T-331 wet-room backing fill: WORKED (Gate B PASS FIRST TIME 11:38, V3.0.22; 12 lines hand-checked <= 0.0002 m2, 1F-12 26.305 m2 0.000 %; L4 NEW 0). Decision: T-319 promoted to TODO on V3.0.22.
- T-334 line-state check: WORKED (Gate A PASS 11:42; 350 rebar lines 'held:' text reproduced, quantities consistent). Decision: NEW T-338 (lane I, text / state fix, after T-319); lessons row PROPOSED.
- T-335 ceiling binding: WORKED (Gate A PASS 11:41; kitchen ceiling own 9.630 m2 = decor). Feeds T-284 unchanged.
- T-336 wet-area WP binding: WORKED (Gate A PASS 11:58; pantry floor 13.455, thresholds 0.120 / 0.200 by own handle read, 0.000 %). Feeds T-310; the 10 window up-turns ASSUMED-OA with the drawing reading HELD 0 .. 1.380 m2 stay as passed.
- T-332 formwork binding / T-333 blockwork binding: READY 12:15 (CHECKER-RUNS). T-333 was taken by worker 3 (lane I had no claimable row): allowed by the cross-lane rule.
- Checker M2 census statement: written 10:00, M2 NOT MET on 8 room labels. Decision: NEW T-342 (lane A, gate 1, AT19 first).
- Recurring (every code agent, every run): Drive connector saves raw binary, `agent_env.sh decode` accepts only base64 and no spaces in names; worked round by hand; still in NEEDS FIXING. New this run: this Lead session's venv had no pytest after the automatic prepare (self-check t061 FAIL 'No module named pytest'), repaired by one `setup` (same as 28 Oct 20:20).

## 2026-10-29 08:20 (lead run; covers 04:15 - 08:20)

- T-325 (sills / thresholds ledger) WORKED: Checker own re-measure of 2 doors by their decimal door-symbol handle, W18 sill 0.040 m2, W15 / W16 0.2484 m2 outside the TERRACE-550 outline (no double count); materials UNKNOWN kept. Decision: T-327 (lane I) stays queued after T-326.
- T-315 r2 (wall-tile integration, Gate B) WORKED: candidate of record V3.0.21; pantry base owned once (skirting 185.52 -> 180.12 lm, -2.91 %), every split piece re-measured by hand 0.00 %. Decision: lessons row ADOPTED; cosmetic cut note text -> T-331.
- T-329 (wet-room backing plaster ledger) WORKED: 340.3038 m2 at tile height (owner method, ASSUMED — OWNER-APPROVED), band above tile HELD 0 .. 23.097 m2 (Q-52 C); Checker GF-12 own 25.3011 = ledger. Decision: NEW T-331 (lane I, first) with the Checker's 'band beside every fill' condition verbatim; lessons row ACCEPTED.
- T-330 (canonical deductions check) READY: 92 lines with gross+net, 30 FLAG (plaster / paint 42.302 m2 listed nowhere, skirting 13.569 lm, porcelain 39.308 m2). Decision: Gate A first; its fill folded into T-246.
- Idle runs (Workers 1 / 2 / 3, 06:41 - 07:22): the board had 0 TODO because lane I is serial on the integration files and lanes S / A had no unblocked rows. Decision: binding tables T-332 / T-333 / T-335 / T-336 / T-337 (the measured content each queued lane I package needs, on the current candidate's line ids) + T-334 line-state check; lane I packages then only wire.
- Checker observation (random draw): a STR.REBAR line SOURCE_DERIVED with a 'held:' formula string. Decision: NEW T-334 (population check, no line changed).
- Gap found by the Lead: verdict records (incl. downgrade DG-3521554d) not yet re-bound to V3.0.21 (no verdicts/V3.0.21 folder). Decision: Checker queue item (1).
- Recurring tool issue (unchanged, every code agent, every run): Drive downloads arrive raw binary, `decode` expects base64 (NEEDS FIXING (1)).

## 2026-10-29 04:15 (lead run; covers 00:15 - 04:15)

- T-313 r2 (opening reveal ledger) WORKED: 20 door reveals bound to FIN.PLASTER (17.740 m2 EQUAL), missing scope 13.637 m2 own-confirmed; D-GF-07 line low end 1.28 ENGINE_WRONG (printed 1.400). Decision: NEW T-326 (lane I, reveals into the candidate).
- T-321 (roof build-up) WORKED: T-221 ROOF-430 short by 2.0787 m2 and ROOF-970 on the outer face, both CONFIRMED. Decision: NEW T-328 (lane I).
- T-224 r2 (sunken-slab step) WORKED: free-edge concrete only from a printed step detail; Alsenan effect 0 m3. F-T224-C2 stays with the unwired module.
- T-324 (parapet components) WORKED: inner faces 94.123 .. 99.558, tops 26.836 .. 26.973 m2; coping / drip / beads UNKNOWN -> RFI A13.
- T-322 (FF / lift base) WORKED: the Checker DOWNGRADED the verified footing-blinding component 14.990 -> 12.734438 m3 + FF HELD >= 2.070. Decision: Checker-issued downgrade record on the candidate line; RFI S23; T-319 acceptance checks the export.
- T-323 (slab hatches vs panels) WORKED: no candidate line reads a hatch (ENGINE_RIGHT).
- T-315 Gate B PARTIAL (REJECTED narrow: pantry base carried twice, skirting under full-height tile; tile figures sound). Decision: TODO r2 with the Checker's 4 items, first in lane I; lessons row PROPOSED.
- T-325 (sills / thresholds) READY: 0 DIFFERS, 32 fill proposals, external materials UNKNOWN. Decision: Gate A first; then T-327; RFI A13.
- Recurring cause (new): cross-trade attribution by room name / note instead of by source entity (T-315). Decision: lessons row; T-329 / T-326 acceptance carry 'by id, never twice'.
- Recurring tool issue (unchanged): Drive downloads arrive raw binary, `decode` expects base64; every agent re-encodes by hand (NEEDS FIXING (1)).

## 2026-10-29 00:15 (lead run; covers 2026-10-28 20:15 - 2026-10-29 00:15)

- T-244 (Gate B, plaster / paint at the merged opening outlines, V3.0.20) WORKED: candidate of record V3.0.20; 1F-11 released 59.4511 m2 ENGINE_WRONG -> HELD 61.4626 .. 61.7177; paint released 166.8792 -> 217.2081 m2; Checker reproduced byte for byte. Decision: T-315 (wall tile) PROMOTED onto this base.
- T-312 (wall tile ledger) WORKED: Checker own 1F-12 26.305 = ledger, pantry 32.375 vs 32.3422 (+0.10 %). Decision: carried by T-315.
- T-311 (parapets / plinth) WORKED: parapet RC 8.040 .. 20.081 m3 MISSING confirmed by the Checker's own reading; F-T311-C1 (lower bound = max(0.30, build-up)) and C2 (second 0.200 strip) -> T-319 acceptance.
- T-316 (slab top-bar extent) WORKED: F-T316-01 / -02 ENGINE_WRONG -> T-318 acceptance (still BLOCKED-OWNER).
- T-317 (spatter dash / joint mesh) WORKED: spatter scope = every finished face (answered OD-V3B-4 .. 7). Joint mesh has no rule, note or specification -> OWNER PACKAGE item 2 (ERS s.2.7: contractual measurement decision).
- T-320 (backfill displacement) WORKED: 105.163 m3 established, closes 0.000; F-T320-03 (FF blinding) -> NEW T-322.
- T-313 r1 PARTIAL (REJECTED: door reveals booked NO_LINE although 22 FIN.PLASTER lines carry them = double count at integration). Rework r2 READY 23:59 (missing scope 36.78 -> 13.64 m2). Decision: Gate A first; thresholds -> NEW T-325.
- T-224 r1 PARTIAL (REJECTED narrow: free-edge web width a convention labelled DRAWING-CONFIRMED). Rework r2 CLAIMED by worker 1; F-T224-C1 (hatches cut by slab-tag circles) -> NEW T-323.
- T-321 (roof build-up) READY: no roof layer printed anywhere; falls-layer trade CONFLICT Q-41 vs Q-45 ruled by the Lead (one SCREED volume; Q-45 = mix); F-T321-02 (1.400 m boundary parapet) -> T-319.
- Recurring cause (new): a ledger searched one line family and called a component NO_LINE (T-313 r1). Decision: every ledger task row now asks for a search over every family by physical element before NO_LINE (lessons register 2026-10-28).

