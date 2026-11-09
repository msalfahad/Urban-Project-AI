# T-613 scorecard tables from statement V10 (research, unwired; for the 12-13 Nov milestone)

Worker 3 (lane I, non-candidate, backlog-permitted), claim 2026-11-08T01:02Z, base engine 17559e1b; r2 claim
2026-11-08T03:00Z (rework of exactly the Checker 01:57Z verdict, F-C-T613-1; section "r2" below). Files:
`t613_scorecard.py` (R-T613-1 in its docstring) -> `out/SCORECARD_T613.json` / `.md` (`--check` rebuilds identical),
`tests/t613_scorecard/` (20). Reads only the committed statement V10 of record
(`research/agents_t609/out/RECONCILED_STATEMENT_T609.json`, sha256 pinned `dc2b25d6...`). No drawing, workbook,
coordinate or client data; no candidate, rule, knowledge or registry file; no total moves; nothing released
(V3.0.58 NOT RELEASED; V2.9 + route G unchanged). Development villa; not an accuracy claim.

## What the tables say (statement V10, of record)

- 74 sections in the statement; 48 of record (26 superseded, never read); 36 scored in 20 trade tables (one unit and
  one reference kind each), 12 apart (nested measured sets, conflict readings, the implied lintel count, cross
  references, bounds), never added.
- Lines (36): VERIFIED 1 (B12 aluminium doors nr), PARTIALLY VERIFIED 14, HELD 3 (necks, blinding, windows nr:
  every row HELD), UNKNOWN 18 (14 of the 16 V1-V4 lines; T-568 doors m2 and windows m2; T-573 cove; B11 rebar t).
- Residual rows (600): VERIFIED 21, PARTIALLY VERIFIED 52, DRAWING-CONFIRMED 0, HELD 192, UNKNOWN 335 (class confirmed
  pre-stamp 119, worker-proposed 128, no stamp 79, by reference 3, bare CHECKER_CONFIRMED evidence verdict 6).
- B11 reinforcement t (1 line): reference 44.19 (typed lump), engine valued 9.375306, difference 34.814694 =
  UNRESOLVED 34.814694 (class unchanged); line UNKNOWN 0 / 6; engine HELD inside the 6 rows beside the classes:
  798 HELD-blank lines, 2 ENGINE_OMISSIONs of a line (lift-pit walls, dome), engine HELD range 14.278249 .. OPEN
  (G6 pool: 20 HELD-blank lines, no range). No %, no agreement.
- Statement totals: all 18 `totals` entries reproduce exactly (reference, engine, difference); 17 by class EQUAL;
  T-545/beams by class SUPERSEDED by T-545/beams@V10 (RD 4.915076 / UNRESOLVED 0.120452 -> RD 2.66625 / UNRESOLVED
  2.369278 m3; difference -0.227179 unchanged).
- B10 m3 (6 lines): reference 230.530875, engine 166.526492, difference 64.004383 = ENGINE_RIGHT -10.995125 + HELD
  73.065230 + UNRESOLVED 1.934278 + RULE_DIFFERENCE 0: the joint rule's 2.66625 m3 sits + in beams and - in columns, so
  it nets to 0 in the trade (one cause, once); the residual of record is T-600's.
- B12 nr: difference 0 = -1 ENGINE_RIGHT (door, VERIFIED by the Checker's own census) + 1 HELD (window W02): a zero
  difference with a HELD part, never agreement.

## Findings

- F-T613-1: the V1-V5 stamp `CHECKER_CONFIRMED` records the Checker's WHO-IS-RIGHT class confirmation (its
  `verification_basis` texts say e.g. "FIN.WALL.TILE PARTIALLY VERIFIED (1 of 11 rooms)"), not a component re-measure;
  119 non-HELD rows carry it. The scorecard counts them UNKNOWN (class confirmed, quantity not stamped); a later
  statement version that stamps evidence on the V1-V4 sections would move them (R-T609-1 (h): no stamp invented here).
- F-T613-2: T-573 stamps two rows CHECKER_CONFIRMED (light-well no-ceiling 14.9434 m2; cove strips 42.745 m2) while the
  Checker's T-573 Gate A says "no ceiling line VERIFIED" (light well + flight re-measured, pocket 1.551 not;
  paint arithmetic re-added): read PARTIALLY VERIFIED from the pinned verdict. The T-568 door-count rows are read
  VERIFIED from the Gate A own census (27 inserts AGREE). These six readings are quoted in `READINGS`.
- F-T613-3: thirteen V1-V4 sections print a % beside HELD rows (26.44, 62.89, 80.13, 100 ...; R-T579-1 (e) "NOT a
  verdict"); the scorecard suppresses each and quotes it; only T-546/floor -18.84, T-553/floor-tile 5.49 and T-568
  alu doors -20.00 / -6.33 carry a printed %, labelled NOT a verdict.
- F-T613-4: T-616 is merged on the engine branch (17559e1b) after V10 (board row READY at the claim); its lintel split
  touches T-571/lintel-count-implied@V8 (apart) and is listed pending with T-600 (open) and T-608 (merged, lines not
  in any V10 section); none folded in.

## r2 (Checker 2026-11-08T01:57Z, GATE A (f) FAIL: B11 t scored VERIFIED)

- Cause: the six T-560/rebar@V9 rows carry evidence_status CHECKER_VERIFIED with evidence_verdict a bare
  'CHECKER_CONFIRMED' stamp; r1 took the Checker citation from `class_basis` (the T-590 Gate A provenance / class text:
  '34.814694 t AGREE' is the difference arithmetic, not a re-measure of the engine tonnage) and never looked at the
  HELD content inside the rows or at the section's own 'PARTIALLY VERIFIED' verdict.
- Fix (R-T613-1 (d) / (e) r2, `t613_scorecard.py` `row_status`, `held_content`, `section_card`): (1) on the
  CHECKER_VERIFIED path only evidence_verdict / verification_basis / source_verdict can cite the Checker; a bare stamp
  behind a class text is UNKNOWN (class confirmed, quantity not re-measured), with nothing behind it refused; (2) a row
  with engine_held_blank_lines > 0, an engine_held_range or an engine_omission_of_a_line is at most PARTIALLY VERIFIED;
  (3) a section Checker verdict reading PARTIALLY VERIFIED caps the line at PARTIALLY VERIFIED n / m (it never raises a
  line), except where a later pinned Checker verdict accepts the line VERIFIED (`SECTION_READINGS`: T-568/alu-doors-nr,
  the 01:57Z verdict itself; its section text confirms door counts 3 / 3 storeys, the PV part being windows, widths, m2);
  (4) engine HELD inside non-HELD rows reported beside each line and table, never added, never 0.
- Effect: lines VERIFIED 2 -> 1, UNKNOWN 17 -> 18 (B11); rows VERIFIED 27 -> 21, UNKNOWN 329 -> 335; no other row or
  line changes status; no class, total, difference or table sum moves (every re-add identical to r1).
- F-T613-5 (statement note, not fixed here): the T-560 section's `engine_held.held_blank_lines` is 799 while its six rows
  carry 798, and its `held_range_t` high 19.646878 omits the unranged G6 pool row (20 lines); a later statement version
  should name the 799th line and carry the G6 high as OPEN.
- Pending list states refreshed (facts only): T-600 MERGED r2 61fef828 and T-616 MERGED 17559e1b, both after V10, so
  still not in V10 and not folded in.

## Who is right (proposals): none new; every class is the statement's own (R-T613-1 reads, never reclasses).

## Lesson row proposal (ERS s.7)

| 2026-11-08 | a scorecard read from a reconciled statement | an older section, a class-confirmation stamp, a % beside
HELD or a nested set could be counted as verified agreement | read sections of record only; status per row with HELD
first and VERIFIED only with a cited component verdict (never a class text, never with HELD inside the row, line capped by a section PV verdict); a pre-stamp class confirmation is UNKNOWN; % only as printed,
suppressed beside HELD or on a nested set; one unit and one reference kind per table; pending work beside |
R-T613-1 (every villa) | tests/t613_scorecard | PROPOSED |
