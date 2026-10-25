# T-291: blockwork wall-to-line ledger, register v4 wall by wall against the candidate's masonry line ids (development villa; every villa by R-T291-1)

Worker 2 (lane A), claim 2026-10-25 08:40 UTC, run session_01WjouVeSSK1Kz4CRHpPD7aN. Integration dependency of T-279.
Research only: no engine module, rule or knowledge file, candidate line or released line changed; released default
stays V2.9 + route G; nothing here is released. ERS read: s.2.1 (physical element first), s.2.4 (reconcile to named
causes), s.3 (build before deduct; installed vs procurement), s.4 (rule + test, normal and adverse), s.7 (lesson row).

## 1. Run and identity

Own run, Python 3.11.17, Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and
'ST7757 dxf.dxf' (`9f9d1179`): research/agents_t167/v304_run.py (V3.0.4 csv `d86de34a` REPRODUCED) then
research/agents_t270/v3015_run.py: **V3_0_15_BOQ_LINES.csv `a4dc01dd` = the T-270 r2 Gate B file** (3,699 lines; the
T-245 V3.0.16 lines are byte-identical to it, T-290 row). Extract: `python3 -I research/agents_t291/t291_alsenan.py
--extract <run>/v3015` -> CANDIDATE_V3015_MASONRY_LINES.json (28 masonry lines: id, item, storey, element, unit, state,
quantity, RFI text, wall-band entity count; no coordinate, no name). Ledger: `--write`; `--check` rebuilds byte-identical.

The masonry lines carry project id `development-villa-t131`, revision set `db7b3eb8...` (the architectural chain), not
the structural rows' identity T-289 cites (`297e913d...`): the one-identity fix is T-245 r2's; this ledger carries each
line's own identity and changes nothing there.

## 2. Physical element and what the candidate measures

A block wall is the masonry between its two faces, from its floor to the underside of the member over it, less the
openings built into it (Q-60 A, R-T274-1, R-T288-1). The register (v4, T-288 MERGED 643b310b) measures it wall by wall.
The candidate measures masonry as **one line per storey x thickness family x item** (UP-MAS-HEIGHT-001,
tools/urban_boq_m9.py `_v29_masonry`): ARCH.WALL_PANEL (m2, geometry), ARCH.WALL_VOLUME (m3), MAS.BLOCK (m2, the
material item) and ARCH.WALL_RUN (lm, the band run). It has no wall key.

**Finding: every one of the 21 m2 / m3 masonry lines of the candidate is BLOCKED_RFI with no quantity**
('MASONRY_NOT_MEASURED ... MASONRY_HEIGHT_NOT_IN_THE_DRAWING: no section of this floor gives T.O.S. and U/S slab';
MAS.BLOCK 'BLOCK_WALL_NOT_ESTABLISHED'). So T-279 does not correct an engine figure: it **replaces a blank** with the
register's carried walls, per line, status by status. The only masonry figures the candidate prints are the 7 run
lines (lm, PROVISIONAL).

## 3. The ledger (WALL_TO_LINE_LEDGER_T291.csv, 228 rows = 76 walls x 3 items)

Binding rule: storey + thickness family (census t) -> the line of that storey and family for each item. Every wall
binds to exactly one line per item (no wall straddles two families in the register; shares are supported by the rule and
tested on villa N); every one of the 21 m2 / m3 lines holds at least one wall; 0 unmatched walls, 0 unmatched lines.
Residual register - ledger = **0.0000** on every status, the U, the L and the conflict increments, for each of the three
items (summary.json `closures`).

MAS.BLOCK lines (the BOQ blockwork item; ARCH.WALL_PANEL carries the same m2, ARCH.WALL_VOLUME the same x t):

| Line id | Storey / t | Walls | VERIFIED | DRAWING-CONF. | OWNER-APPR. | Determinate | Est. parts (B) | Drop walls U - L x d | HELD walls (blank) | Conflict incr. (outside) |
|---|---|---|---|---|---|---|---|---|---|---|
| L-0d9b9e89bb6455da475d | GF 0.15 | 16 | 9.8950 | 21.5261 | 24.2374 | 55.6585 | 0 | 29.4129 - 4.5131 d | 6 | 0.0607 |
| L-4165954ce4871eda30cc | GF 0.20 | 24 | 66.6220 | 5.1450 | 5.5900 | 77.3570 | 39.1525 | 17.3890 - 3.4000 d | 16 | 0 |
| L-ff06449b7f61f19c418d | GF 0.40 | 1 | 0 | 0 | 0 | 0 | 0 | - | 1 (GF-H01) | 0 |
| L-c22e309433e7b671cf2d | 1F 0.15 | 13 | 52.3180 | 19.7326 | 36.7513 | 108.8019 | 27.0417 | - | 3 (+3 parts) | 0.0340 |
| L-5ffa7157a2fe483dd008 | 1F 0.20 | 13 | 125.8760 | 2.0620 | 0 | 127.9380 | 44.7740 | - | 1 (+2 parts) | 0 |
| L-246f3c09de4c6b90efe5 | 2F 0.15 | 2 | 0 | 0 | 9.6400 | 9.6400 | 25.8850 | - | (1 part) | 0 |
| L-afe984a62285e133ec2f | 2F 0.20 | 7 | 43.1360 | 0 | 0 | 43.1360 | 19.7165 | - | 1 (+3 parts) | 0 |
| **Total** | | **76** | **297.847** | **48.4657** | **76.2187** | **422.5314** | **156.5697** | **46.8019 - 7.9131 d** | 28 walls | 0.0947 |

Against register v4 (T-288 s.3): basis A determinate 402.7988 = VERIFIED 297.847 + OWNER-APPROVED 76.2187 +
DRAWING-CONFIRMED 28.7331 (the ledger's 48.4657 DC = 28.7331 + 1F-W18 19.7326, a basis-B wall established whole);
basis B determinate 579.1011 = 422.5314 + 156.5697 (the established parts of the 10 ESTABLISHED PART + HELD walls,
each with its held piece named, blank). The drop term 7.9131 x d is carried as a term on the two GF lines (4.5131 +
3.4000 m), never evaluated (d HELD, D-41). Every VERIFIED wall (18) cites its Checker run (T-180 slot, 2026-10-24 15:27
.. 2026-10-25 02:09); GF-W12 is HELD ON DROP, its VERIFIED withdrawn by the Checker 02:00. The six width-CONFLICT
increments (GF-W19 / W20 / W22 / W34, 1F-W11 / W16; 0.0947 m2: GF 0.0607 + 1F 0.0340) stay outside every total.

T-279 consumer shape: one row per (line id, wall), columns `carried` (blank when HELD / drop), `upper_at_d0`,
`drop_coefficient`, `status`, `part_status`, `verified_by`, `held_item`, `conflict_increment_outside`,
`opening_deductions`; LINE_SUMMARY_T291.csv gives each line's expression (e.g. GF 0.20: '77.3570 determinate +
39.1525 established parts + (17.3890 - 3.4000 x d) drop walls + HELD [17 walls / pieces, blank] m2').

## 4. Opening deductions by opening id (OPENING_DEDUCTIONS_T291.csv, 71 ids, each once)

32 DEDUCTED (in a carried net or a drop wall's U), 14 ON_HELD_WALL (established deduction on a HELD wall: shown,
summed nowhere), 5 IN_HELD_PIECE (D-GF-09, D-1F-09, W25, W27, D-2F-02), 9 HELD (the deduction itself not established),
3 NOT_APPLICABLE (W02, W03, W17: glazed hosts, build before deduct), 8 NO_HOST. Per wall, DEDUCTED + ON_HELD_WALL =
the register deduction to 0.0005 m2 (rule 4), e.g. 1F-W00 9.7354 = W15 4.363 + W16 4.363 + W18 1.0094; 1F-W06 3.28845 =
W19 0.48 + W20 0.48 + W24 2.32845 (drawn jamb 1.5523 x 1.50, T-288).

**W18 and W03 (the row's instruction to hold them as deductions with T-255): not applied, with the evidence.** W18's
masonry deduction is already in 1F-W00 by its part inside the masonry (0.4673 x 2.160 = 1.0094 m2, T-274 s.4), and
1F-W00 at 12.935 m2 is VERIFIED (Checker 2026-10-25 02:01, 'W18 by its part inside the masonry'). Holding it again
would hold a verified wall and count the opening twice. W03 sits in GF-W37, a glazed line with no masonry built
(T-175 / T-249 DELTA: NOT_APPLICABLE); a block deduction there would deduct from masonry that does not exist (ERS
s.3). What T-255 owns is their WINDOW supply lines (W18 0.50 x 2.16 = 1.080 m2; W03 6.57 x 4.30 = 28.251 m2 per owner
Q-76 / Q-38 A), not a blockwork quantity; both rows name T-255.

## 5. Engine vs register vs freelancer (engineering terms)

- Blockwork m2 / m3: the candidate gives **nothing** (21 lines BLOCKED); the register established 422.5314 m2
  determinate + 156.5697 m2 established parts (+ 46.8019 - 7.9131 d on six walls; 28 walls HELD). Freelancer: one
  height per storey, no per-wall row (T-288 s.4); no total verdict while 28 walls are HELD. Verdict proposal per line:
  **ENGINE_BLOCKED / REGISTER_DETERMINATE** (no engine figure to be right or wrong; UNRESOLVED on the held walls).
- Run (lm), comparison only (WALL_RUN_LENGTHS_T291.csv): engine band run vs register census length, GF 0.20 66.7041 vs
  92.6430 (-25.9389 m; engine 18 walls, register 24), GF 0.15 30.3348 vs 39.5990 (-9.2642), 1F 0.20 44.0325 vs 60.4330
  (-16.4005; 11 vs 13), 1F 0.15 44.2597 vs 56.8130 (-12.5533), 2F 0.20 22.3 vs 28.7 (-6.4), 2F 0.15 8.7 vs 10.9 (-2.2),
  GF 0.40 0.6 vs 0.6 (0). Named causes, not reconciled here: the engine run is the length where BOTH faces are drawn
  (opening widths and junction squares are left out) and misses whole walls on GF / 1F (the historical blockwork
  length deficit B8); the census runs through openings. The run lines are not carried by T-279 (the line is the
  panel's geometry, coverage_census B9-01); the difference is listed so nobody reads the run as the census.

## 6. Rule, tests, lesson

- **R-T291-1** (wall_line_ledger.py, PROJECT-INDEPENDENT; provenance T-288 / T-285 / T-274 / T-175 / T-227 / T-261):
  binding by storey + family per item, shares declared and closed; one status per row (VERIFIED needs its Checker run;
  HELD blank + named; drop term carried, never evaluated; established part + held piece named); closure 0 per status;
  openings once by id, summing to the register deduction; held never 0; conflict increments outside totals.
- **tests/t291_wall_line_ledger** (24): villa N hand truth (N-W1 3.000 x 4.000 - 1.000 x 2.000 = 10.000 VERIFIED;
  N-W2 6.000; N-W4 8.000 - 1.500 d; N-W5 5.000 = 3.750 + 1.250 in two line ids; one line holding five walls; m3 = m2 x
  t; order / mirror invariant); adverse: a wall in no line listed and the closure fails, a held wall as 0 refused, an
  opening twice refused, a drop term at d = 0 refused, a wall twice refused, VERIFIED without a run refused,
  millimetres refused, a conflict increment in a total refused, ambiguous lines without shares refused; Alsenan:
  byte-identical rebuild, csv a4dc01dd, 28 lines, 76 walls x 3 items, closures 0, register totals, drop 7.9131,
  18 VERIFIED with runs, 28 HELD blank, increments, 71 openings, every m2 / m3 engine line blank, no coordinates.
- **Lessons register row (s.7, proposed):** 2026-10-25 | an integration package (T-279) was framed as 'carry the
  register into the candidate's blockwork line' without anyone having read the line: all 21 m2 / m3 masonry lines are
  BLOCKED (no quantity) and aggregate per storey x thickness with no wall key | the target line's state and grain were
  assumed from the register side | before a wall-to-line integration, extract the target lines and bind each wall by
  storey + family + item, carrying the line's own state (a blank is replaced, a figure is corrected; both stated) |
  tests/t291_wall_line_ledger (normal: walls bound and closed per status; adverse: a wall in no line, a held wall
  summed as 0, an opening twice, a drop term evaluated) | OPEN (T-291 READY).

## 7. For the Checker (re-measure / re-derive)

1. Re-extract the 28 masonry lines from your own V3.0.15 run (csv `a4dc01dd`): all 21 m2 / m3 lines BLOCKED_RFI, no
   quantity; the 7 ARCH.WALL_RUN figures above.
2. Re-bind two walls by storey + census thickness: 1F-W06 (1F, 0.20, VERIFIED 54.4860, Checker 02:03) -> MAS.BLOCK
   L-5ffa7157a2fe483dd008; GF-W34 (GF, 0.15, HELD ON DROP 10.3982 - 1.7231 d, CONFLICT 0.0139 outside) ->
   L-0d9b9e89bb6455da475d.
3. Re-add one line: GF 0.15 MAS.BLOCK determinate 55.6585 = GF-W19 8.5950 + GF-W21 4.3090 + GF-W22 12.9311 +
   GF-W28 20.1384 + GF-W29 4.0990 + GF-W33 5.5860 (register v4 csv).
4. The W18 / W03 point of section 4 (1F-W00 verified with W18 inside; GF-W37 glazed).
