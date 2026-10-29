# T-319: integration package, ARCH_TAKEOFF_V3.0.23 = V3.0.22 + the PARAPET RC family (Gate B)

Worker 3 (lane I), claim 2026-10-29 13:14 UTC (per date -u; the claim text says 13:20). **Integration package** for
Checker Gate B. integrates: T-311 (MERGED bd7b8c23, the parapet run ledger and the material reading), T-324 (MERGED
bc5df868, each run's top surface with the drawing corrections C1 .. C6, including the F-T321-02 annex run). Opt-in
candidate only: the released default stays ARCH_TAKEOFF_V2.9 + route G; nothing here is RELEASED and nothing is
VERIFIED by this package. ERS applied: s.2.1 (physical element first), s.2.2 (owner manual and drawing-derived methods
side by side), s.2.4 (reconciled in m3 to T-311), s.2.7 (no owner question: the open items are a designer detail
already answered HOLD, Q-65 C, and D-39), s.3 (one element, one owner per component; build before deduct), s.4 (rule +
normal and adverse tests), s.7 (lesson row, section 9).

## 1. The physical element and what is established (not re-derived: T-311 / T-324 Gate A PASS)

A parapet is a wall standing on the edge of a roof slab. Below the slab top it is the supporting edge beam, carried in
STR.CONC.BEAM to its scheduled depth, which ends at the structural slab top (ST p.14 P1 dimensions 'AS PER SCH.' from
the slab top down; R-T311-2). Above the slab top:

| Printed alternative | What it is above the slab top | Keyed to a run? |
|---|---|---|
| ST p.14 P1 (typical) | RC upstand '30' with its own cage, 'MUST BE MORE THAN THE HEIGHT OF ROOF FINISHING'; block wall above; RC cap 'as per arc.' | no |
| ST p.14 P2 / P3 | RC throughout | no |
| P7757 sections A-A / B-B | every parapet cut in the slab hatch (RC) | sections, no run key |

So the material above the upstand is HELD (Q-65 C: designer), and so is the roof build-up depth at the edge b_edge
(D-39; T-321: no roof layer thickness printed). What every alternative shares is **at least 0.30 m of RC above the
slab top** (Checker's own p.14 read on T-311). F-T311-C1 (Checker): the P1 note makes the upstand max(0.30, b_edge +
a margin), so 0.30 is a FLOOR, not "the" lower bound, while b_edge is held. The solid's height above the slab top =
the printed height above the FINISHED roof + b_edge.

## 2. What the module does (engine/source/arch_v3023.py, one piece)

- **ADD** one STR.CONC.PARAPET line per roof chain (annex roof +4.30, GF terrace +5.50, 1F roof +9.70, 2F roof
  +13.90), element `<chain>#PARAPET_RC`, floor = the storey whose roof slab carries it (the structural convention of
  the STR.CONC.BEAM / SLAB lines: annex and GF terrace = GF, 1F roof = 1F, 2F roof = 2F; the roof WP lines are labelled
  by the plan above, so the same roof reads 1F / 2F there). Each line is **BLOCKED_RFI: HELD, BLANK** (no
  measured_net, no bounded_range, no gross: never 0, never a midpoint). Its bound travels beside it:
  calculation.inputs.parapet_rc_v3023 (per run and per chain), the formula text (no concluding figure), the notes and
  the RFI question (which the export prints as the held reason):
  - top per run = drawn centreline x drawn thickness (T-324 TOP_SURFACE, the plan footprint);
  - **floor (AT_LEAST, for any b_edge) = top x 0.30**, status DRAWING-CONFIRMED (T-311 Checker run named);
  - lower bound = top x max(0.30, b_edge + margin): HELD on b_edge and the unprinted margin (F-T311-C1);
  - upper bound = all RC, top x (h + b_edge): the printed part top x h stated (h a range where the elevations
    disagree), plus top m3 per m of b_edge, open.
- **Exclusive / downstream named on every line**: the block alternative above the upstand (MAS.BLOCK, exclusive with
  the RC above the upstand, never added: T-333 binding); formwork faces (T-199 / T-332); reinforcement (HELD); faces,
  top and arrises (finish families, T-314 / T-324 items: none of them in this concrete line, acceptance 04:15 (ii));
  the upturn (roof WP lines); the edge beam (STR.CONC.BEAM, unchanged).
- Refused (tests): a run in two lines; a chain twice; a defaulted height (no source / missing); mm heights or
  thicknesses; a height range not HELD; a top that is not centreline x t; a missing top (0); RC above the upstand with a
  block area (RC OR block, never both) or a run read as block (the upstand would vanish); a missing block figure with
  no named reason; a concrete line of the run whose basis names a parapet (the run would be carried twice: beam to the
  slab top only) or a STR.CONC.PARAPET line already present; a floor without its printed source or a confirmed floor
  without the checker run; a material settled without a keyed detail; a declared total that is not the records' sum;
  a parapet line given a figure or a range (a held line summed into a total); any V3.0.22 line changed.

Wiring: tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.23 --v3023-inputs` (additive; every earlier method list
gets V3023, nothing else changes; the V3.0.22 option error now says 'V3.0.22 or later'). Inputs:
research/agents_t319/t319_inputs.py reads only the merged T-311 / T-324 files and pins them (25 runs, top 26.836476 ..
26.972520 m2, floor 8.050943 m3, T-311 24 runs and block 60.596453 m2): an edited ledger stops the build.

## 3. Run and identity (own run, Python 3.11.18)

Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and "ST7757 dxf.dxf" (`9f9d1179`),
decoded into the private folder only: research/agents_t167/v304_run.py, then research/agents_t319/v3023_run.py (one CLI
process), every earlier version reproduced on the way: **V3_0_19 json `b35475bf`, V3_0_21 json `be22a4e4` / csv
`3548e39c`, V3_0_22 json `7199c8b6` / csv `924a60b4` = the candidates of record** (T-331 Gate B). Final hashes of
V3_0_23 on the task head: section 10.

Identity (V3_0_23_RUN.json): 3,710 lines = 3,706 + 4 added; replaced 0; the 3,706 V3.0.22 lines byte-identical
(asserted; outside_rows_sha256 `ccacf45c`). DIFF vs V3.0.22: SAME 3,706, ADDED 4, CHANGED 0, GONE 0. DIFF vs released
V2.9: NOT_IN_RELEASED 2,116 -> 2,120 (the 4 new lines), QUANTITY_DIFFERS 899 and SAME_QUANTITY 691 unchanged. Totals
moved by code: ONLY STR.CONC.PARAPET|m3 (absent -> 4 blocked lines, released 0.0, held range none: blank by design).
Default guard over the 3,710 lines: findings by code identical to V3.0.22 (CONVENTION_WHERE_PRINTED 87,
PARTIAL_FOOTPRINT 2, PRINTED_VALUES_DISAGREE 75, SEARCH_INCOMPLETE 1,039), none on an added line, held_live_new none,
silent omissions none. No concrete line of the run names a parapet (asserted by the module before adding).

## 4. Line by line (before V3.0.22 -> after V3.0.23; released V2.9; freelancer)

Owner manual method beside the drawing method: no answered owner rule measures parapet concrete (Q-65 C holds the
material; Q-24 / Q-25 / Q-58 concern the membrane); the manual take-off of the set carries parapets only as blockwork
(BLK rows 172 / 177 / 178: 172.93 m2 at 1.00 / 1.80 / 1.00 m) and has **no parapet row in its RC sheet**. Drawing method:
section 2. Every line below is new (moved from absent: a hand-check line under s.1, rule 'new calculation method',
'newly introduced scope', 'structural element').

| Chain (roof) | Line | V2.9 | V3.0.22 | V3.0.23 | Runs | Top m2 | Floor m3 (any b_edge, DC) | All RC at b_edge 0, m3 | + m3 per m b_edge | Block alt. m2 (exclusive) |
|---|---|---|---|---|---|---|---|---|---|---|
| Annex +4.30 (GF) | L-1d419b64e8ca1af30fb4 | none | none | HELD BLANK | 7 | 5.99701 .. 6.03701 | 1.799103 | 2.998505 .. 3.018505 | 6.03701 | 0 .. 5.77702 (NE-6x not booked) |
| GF terrace +5.50 (GF) | L-b5ffc172a354375ca107 | none | none | HELD BLANK | 3 | 5.592956 .. 5.67398 | 1.677887 | 2.796478 .. 2.83699 | 5.67398 | 0 .. 5.67398 |
| 1F roof +9.70 (1F) | L-9a2c81164ec6499cc28c | none | none | HELD BLANK | 11 | 9.83151 .. 9.84653 | 2.949453 | 10.478455 .. 11.53235 | 9.84653 | 0 .. 43.335453 |
| 2F roof +13.90 (2F) | L-030538dda6a32c601c4c | none | none | HELD BLANK | 4 | 5.415 | 1.6245 | 2.7075 | 5.415 | 0 .. 5.81 |
| **Total** | 4 lines | | | **HELD** | **25** | **26.836476 .. 26.97252** | **8.050943** | **18.980938 .. 20.095345** | **26.97252** | **0 .. 60.596453 + NE-6x** |

Run by run: V3_0_23_RUNS.csv (25 rows; ranges where a run end stops on a D band, C1 / C2 / C6, or a 1F height is held,
NE-1 / SW-1 / SW-2). Evidence split of the family: VERIFIED 0, DRAWING-CONFIRMED floor 8.050943 m3 (beside a blank
line), ASSUMED - OWNER-APPROVED 0, HELD the line quantity (4 lines), UNKNOWN 0. Release: NOT RELEASED.

**Against T-311 (merged), in m3:** floor 8.040369 -> 8.050943 (+0.010574 = 0.30 x +0.035246 m2 of top: C5 NE-6x
+0.25999, C3 NW-2 chord -0.0887, C1 -0.04, C2 -0.01502, C6 -0.081024 on the low side); all RC high 20.08066 ->
20.095345 (+0.014685 = C5 0.25999 x 0.50 + C3 -0.0887 x 1.30); increment 26.80123 -> 26.97252 m3 per m (the top). The
T-311 'solid' low 19.033 vs 18.981 here: the same C-corrections on the low side; residual 0.000 after them.

**Hand checks (own, from the merged ledger figures, not the engine):** 2F = ring 8.100 x 6.800 - 7.700 x 6.450 = 5.415
m2 (the Checker's own T-311 re-measure); floor 0.30 x 5.415 = 1.6245 m3 (line 1.6245); all RC 5.415 x 0.50 = 2.7075
(line 2.7075). Annex NE-6x (C5) = centreline 1.300 x 0.200 = 0.260 m2 (ledger 0.25999), floor 0.078 m3 (run 0.077997).
GF = 3.854 + 1.540 + 0.198956 .. 0.279980 = 5.592956 .. 5.673980 m2; x 0.30 = 1.677887 on the low top (line 1.677887).

**Engine vs freelancer (concrete, m3):** parapet RC: engine HELD (at least 8.0509 m3, printed all-RC part 18.98 ..
20.10 m3 + 26.97 m3 per m of b_edge) vs freelancer: no row. Verdict proposals: SCOPE ENGINE_RIGHT (every printed
alternative carries >= 0.30 m RC above the slab top: Checker's own p.14 read; hand check 2F above), quantity
UNRESOLVED (material Q-65 C designer, b_edge D-39), freelancer omission of the RC part. The scoreboard does not score it:
no key of tests/alsenan/T001B / T001C maps STR.CONC.PARAPET (his RC sheet has no parapet row), so tools/alsenan_keymap.py
lists the 4 lines UNMAPPED (never a false positive, line_status HELD, qty None) and the SCOREBOARD v2 CONCRETE m3 cells
cannot move (no reference line answered by a parapet line). Not re-run here (the Checker owns the scoreboard).

## 5. Checker findings carried (T-311 / T-321 / T-324 verdicts)

- **F-T311-C1** (lower bound): carried as written: the line's bound says 'lower bound top x max(0.30, b_edge + margin):
  HELD', the 0.30 figure only as 'at least ... for any b_edge'; never the printed 0.30 alone (test: the bound text and
  the floor status).
- **F-T321-02** (B34, 1.400 m annex boundary parapet): carried as the T-324 run NE-6x (Checker-confirmed C5: centreline
  1.300, top 0.25999 m2, h 0.50 annex printed), in the annex line once; its block alternative is not in the merged
  block ledger (T-311 predates it): named 'not booked', never 0; its outer face on the boundary line AC7 stays HELD in
  the finish family (T-324).
- **F-T311-C2** (the second 0.200 strip on the 1F roof plan), classified from P7757.dxf (`ab54dd55`, own read this
  run): lines 12C4 / 12C7 (7.500 m, 0.200 apart), closed by 12C6 at the outer corner, a chamfer 12CA / arc 19A5 at the
  other end, cross lines 12E7 / 12E8. Its inner line 12C7 IS the outer face of the 1F run SE-1 (outer 12C7 7.500, inner
  12C9 7.100, centreline 7.300 x 0.200 = top 1.460 m2 = T-311 / T-324); 12C4 lies 0.200 further out. It bounds no roof
  on either side (the roof lies inside 12C9), has no inner face and stops at the parapet's outer corner: **a band
  projecting from the facade (frames / projections item, T-172: profile HELD), not a parapet run and not a roof
  upstand**. EXCLUDED from STR.CONC.PARAPET by that evidence, its material / profile UNKNOWN, never 0 (inputs
  'excluded'). Which frame (T-172 named the NW pool-court arch frame; by position it sits on the SE-1 face) is not
  settled by the plan alone: named for the frames item.
- The divider CEC / CED (0.200 x 1.300 m between the annex roof and the GF terrace, T-324): in no run, UNKNOWN by name.
- Acceptance 04:15 (i) **FF blinding**: the Checker's downgrade record DG-3521554d2fd011b9 (docs/agents/verdicts/V3.0.22
  /DOWNGRADES.json, binding LINE_CONTENT_V1) binds L-98eb2d58075c9eddf1b4 byte-identical in V3.0.23: tools/boq_export_v1.py
  with --downgrades on V3.0.23 writes it HELD in the contractual BOQ.csv (net blank, the reason 'HELD >= 2.070 m3 ...'),
  the engine 15.179437 m3 in BOQ_AUDIT_UNSUPPORTED_BASIS.csv only; manifest 'APPLIED (HELD, 1 line(s))' (and
  DG-a97ec2ea 38 lines) = the V3.0.22 export exactly. Nothing carried here (the record is the Checker's).

## 6. Export integrity

- tools/boq_export_v1.py (with the V3.0.22 verdict and downgrade sets) on V3.0.22 and V3.0.23: rows 3,706 -> 3,710
  (HELD 1,910 -> 1,914), every one of the 3,706 rows equal except the candidate-version column; the 4 parapet rows HELD,
  net blank, held reason = the RFI question with the bound ('HELD bound at least ... m3 ...'); CONCRETE trade summary:
  STR.CONC.PARAPET 4 rows, 4 held, measured 0; every other concrete row byte-equal.
- tools/t334_line_state_check.py: V3.0.22 OK 3,340 / REFUSED 351 / FLAG 15 -> V3.0.23 OK 3,344 / 351 / 15: the 4 new
  lines OK (no figure, no range, no concluding figure in the formula); the 351 / 15 are the pre-existing V3.0.3 'held:'
  texts on valued rebar lines and 15 formula figures (T-338's fix), unchanged.
- tools/t330_deductions_check.py: OK 74 / FLAG 41 unchanged; NOT_APPLICABLE 3,591 -> 3,595 (the 4 new m3 lines).

## 7. Missing, held, downstream

- HELD (never 0): the parapet RC volume of every chain (material per run Q-65 C designer; b_edge D-39 and the P1
  margin); the 1F heights NE-1 / SW-1 / SW-2; the D-band run ends C1 / C2 / C6.
- Not in this line (named): block alternative (MAS.BLOCK, exclusive; the blockwork binding T-333, sent back 13:30 for
  an unrelated door-height status label, carries 0 .. 60.5965 m2 on the T-311 runs; NE-6x owed by it); formwork
  81.589 .. 202.782 m2 (T-311 basis; T-199 / T-332, whose Checker pass 13:25 confirmed the 24 parapet rows HELD
  blank); reinforcement HELD; faces / top / arrises / coping (T-324 items, T-314); upturn (roof WP lines); the strip of F-T311-C2 (frames item); the divider.
- Downstream: SCOREBOARD v2 unchanged (unkeyed family, section 4); coverage registry: BOQ_FAMILY_MASTER 1.18.0 declares
  V3.0.23 PENDING (rule r3); once merged the B10-12 parapet family is HELD_IN_CANDIDATE (released_in_candidate none).

## 8. Regression and validation

- tests/t319_parapet_rc_integration (villa P319 hand fixture, not Alsenan: two roofs, a straight run, a quarter arc, a
  0.15 m run with a held height range, a 0.25 m run with its block alternative, a D-band run end; floor 1.478496 m3;
  adverse: run twice, defaulted height, mm, height range not HELD, top != centreline x t, top 0, RC and block on one
  run, block read as the material, missing block figure without reason, parapet named in a beam line, a second
  carrier, held line with a figure, floor without checker run / source, declared total edited, material settled,
  excluded item without evidence, a V3.0.22 line changed; mirror / order; the bound in the RFI; Alsenan pins incl. the
  2F hand check and an edited ledger stopping the build; master 1.18.0 = its builder, accounts for the module, adverse
  drop / family naming).
- tests/structural_comparison_engine/rebar_product_registry.py: arch_v3023 declared (it names reinforcement only as a
  waiting item); without it test_every_rebar_module_in_engine_is_declared fails (seen in the first full run).
- Validation results: section 10.

## 9. Lessons-register proposal (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-29 | A structural category with a firm floor but an open top (parapet RC: >= 0.30 m RC in every alternative, the rest held on the material and the build-up depth) had no candidate line for 22 versions, and the only line shapes on offer were a figure (which would release a floor as 'the' quantity) or a bounded range (which needs a finite high that does not exist) | the line model ties 'bounded' to a closed range, so an AT_LEAST quantity had no honest carrier and stayed MISSING | a missing element whose quantity is only bounded below is added as its own line, HELD BLANK, its bound beside it in the line's record and RFI (floor with its status, the lower-bound formula with what it waits on, the upper bound with its open part per unit of the held dimension), never a figure, never a fabricated high, never folded into a neighbouring member's line (every villa) | tests/t319_parapet_rc_integration (held line with a figure refused; parapet in a beam line refused; RC and block on one run refused; defaulted height refused) | PROPOSED |

## 10. Final run and validation on the task head

- **Full CLI run (research/agents_t319/v3023_run.py, one process) on the task head 1f6e107f** (the code of the hand-in;
  later commits are report / maps only): V3_0_19 json `b35475bf`, V3_0_21 json `be22a4e4` / csv `3548e39c`, V3_0_22 json
  `7199c8b6` / csv `924a60b4` (= the candidates of record, reproduced), **V3_0_23_BOQ_LINES json `0026800b` / csv
  `a819c9f8`**, DIFF `867c3003`, INTEGRATION_LEDGER csv `5c7dc89f` / json `8d2f6d20`, RUNS `0566e0a9` (=
  research/agents_t319/V3_0_23_RUNS_T319.csv), RUN `6799f5ca`: byte-identical to v3023_direct.py on the same V3.0.22.
- Export / checks on these lines: section 6 (export rows 3,710, every V3.0.22 row equal; the 4 parapet rows HELD with
  the bound in the held reason; FF blinding HELD by DG-3521554d; line-state OK 3,344 / 351 / 15; deductions OK 74 /
  FLAG 41 unchanged).
- **L4 full suite (tests/ + agents/, one session) on 88f4c3cf** (module, wiring, inputs, tests, master, maps): 396
  FAILED / ERROR; all 43 failing files re-run on the base head c4246877 (.work/engine): 395 fail there too; **NEW 1**:
  tests/structural_comparison_engine/test_rebar_product_firewall.py::test_every_rebar_module_in_engine_is_declared
  (arch_v3023 names reinforcement) -> fixed in 59d4a0b2 by declaring the module in the registry (as arch_v30 ..
  arch_v305); the 395 are the known private-input / environment failures (pa08 / pa09 private workpapers, the rebuild
  packages that need private drawings, r8_* import boundaries, one control-plane gate), the same 395 T-331 reported.
  Full suite again on c09b4dcb: FULL_SUITE_RESULT.
- Freeze 0 differing; codemap stale none (maps by the tool, last); rules manifest drift none; master 1.18.0 equals its
  builder, FMC problems none.
- Verdict / downgrade records: no record of docs/agents/verdicts/V3.0.22 binds a parapet line (they are new); every
  bound line is byte-identical in V3.0.23, so each record re-binds to the same content unchanged (no record edited here:
  the Checker owns them); the export shows DG-3521554d and DG-a97ec2ea APPLIED as on V3.0.22.
- self-gate: a c d f h PASS (a: only the new integration module, runner wiring, registry version file, rules manifest,
  the firewall registry declaration, research and tests/t319_*; no frozen / rule / knowledge file edited, no client
  data, no coordinate in tracked files (the DXF handles of F-T311-C2 only); c: freeze 0, maps by the tool; d: hand
  fixture P319 not Alsenan with adverse cases, missing never 0; f: every V3.0.22 line byte-identical, held stays held
  (4 blank lines); h: one owner per component, RC and block exclusive, no figure chosen, the floor never presented as
  the quantity).

## 11. For the Checker (Gate B)

Re-measure (WORKFLOW_CONTROLS s.1): all 4 lines are hand-check lines (new method, new scope, structural element).
Suggested own checks: the 2F floor 0.30 x 5.415 = 1.6245 m3 (your T-311 ring); the annex chain top 5.997 .. 6.037 m2 x
0.30 (your T-324 own) = 1.7991 .. ; the 1F NE-2 run 19.07 x 0.20 = 3.814 m2 x 0.30 = 1.1442 m3; that no STR.CONC.BEAM
line rises above the slab top (R-T311-2); the F-T311-C2 classification on P7757.dxf (12C4 / 12C7 / 12C9 / 12C6);
that the 4 lines are blank in the export with the bound in the held reason; plus 2 random lines by the s.1 rule on
the merge-candidate sha. Quick re-run: research/agents_t319/v3023_direct.py on a finished V3.0.22 run.
