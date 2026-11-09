# T-650: B9-02 lintel payable form restated, 60 / 60 openings, one form and one owner line each (R-T650-1 1.0.0)

Worker 2, lane A, claim 2026-11-09T02:43Z, engine base af50c864. Research only, unwired: no engine module, method, rule /
knowledge version, registry, frozen, candidate or statement file changed; nothing released; V2.9 + route G untouched.
Files: `t650_payable_form.py` (rule R-T650-1 + training-villa builder over merged, sha-pinned records: T-644 piece table
and jamb evidence, T-453 lintel ledger, S8.6 schedule transcription; T-519 and T-524 through their own `build()`),
`out/T650_PAYABLE_FORM.json` (ids, widths, m3, causes; numbers only), `tests/t650/` (24 tests). Ruling applied: register
PRECAST LINTEL PAYABLE FORM RESTATED (Lead 2026-11-09 00:15, F-T644-1). Development villa; not an accuracy claim.

## 1. Physical element and the decision order (ERS s.2.1 - 2.3)

One lintel over one masonry opening. The payable form follows the AGENT_BRIEF resolution order (drawings before OWNER
CONFIRMED company rules), decided per opening, never by the larger or the freelancer-closer figure:

| step | evidence | form | owner line |
|---|---|---|---|
| 1 | head in a curved band, or no masonry at either jamb | STRUCTURAL_LINE (FLAGGED) | the structural line carrying the head |
| 2 | printed schedule covers the wall's block type AND a printed band covers the width (a width bound only if no printed gap lies inside it) | RC_CAST_M3 (m3 + bars, cast to length) | the opening's STR.CONC.LINTEL line, B9-02 |
| 3 | schedule covers the block type, width in a band gap / above the last band | SYSTEM_HELD (SCHEDULE_SILENT, designer) | STR.CONC.LINTEL, HELD |
| 4 | no schedule: WHITE | PRECAST_PCS (owner rule, R-T644-1 class) or STRUCTURAL_LINE if FLAGGED (> 4.00 m, no bearing, shared pier, head room) | B9-02 pcs line |
| 4 | no schedule: BLACK | SYSTEM_HELD (company rule defers to the drawings; Q-60 atab white only) | STR.CONC.LINTEL, HELD |

| | owner manual method (precast) | drawing-derived (governs here) |
|---|---|---|
| system | stock piece 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m, pcs | ST p.13 LINTEL SCHEDULE: RC, B = block-wall width, D by band (L1 / L2 20 cm, L3 30) |
| bearing | 0.15 m minimum | printed MIN 40 cm (LINTEL DETAIL), against the masonry measured beside each jamb |
| quantity | pcs by stock length | m3 = B x D x L, L in [w + 2 x 0.40, w + a_s + a_e]; deficit ends by R-T524-1 |

## 2. Result on the training villa

**60 / 60 RC_CAST_M3** (every opening is in a block wall the schedule covers, widths 0.50 .. 2.45 m all inside L1 / L2 /
L3; D-GF-09's bound 0.90 .. 1.00 lies inside L1). PRECAST_PCS 0, STRUCTURAL_LINE 0, SYSTEM_HELD 0. W17 (curved band) stays
outside the 60 with the structural line (register CURVED-BAND OPENING HEAD). No opening carries both pcs and m3 (asserted).

**Governing precast pcs table: NOT_APPLICABLE on this villa** (no opening has the precast payable form; not a zero count).
The T-644 table (ESTABLISHED 13 pcs / 21.5 lm, AT_MOST 37 / 60.6 lm) moves BESIDE as the substitution reference only
(white walls only, Q-60). Proposed wiring for Worker 3: **no B9-02 pcs line on this villa**; the 60 STR.CONC.LINTEL lines
carry the payable form.

STR.CONC.LINTEL m3 lines restated (R-T516-1 end states on the merged T-644 jamb evidence, printed MIN 0.40 m):

| state | nr | openings | m3 |
|---|---|---|---|
| BOUNDED (REQUIRED, both ends >= 0.40) | 8 | D-1F-02, D-1F-08, D-2F-01, D-GF-13, W14, W15 (UNCHANGED, the 6 candidate lines reproduced exactly); A-1F-01, P-1F-01 (NEW, T-616 REQUIRED) | low 0.502 + 0.054 + 0.063 = 0.619; high OPEN (D-2F-01 END search capped) |
| HELD BY NAME (REQUIRED, an end < 0.40: R-T524-1 range) | 10 | D-1F-03, D-1F-04, D-1F-07, D-1F-10, D-2F-03, D-GF-06, D-GF-10, W18, pair D-GF-11 + D-GF-12 | 0.372692 .. 0.437542 (= merged R-T524-1 set, asserted) |
| HELD blank (existence not established: ledger hold 37, lift register 3, head room 2) | 42 | listed with cause in the JSON | never 0 |

B9-02 m3 set: **low 0.991692 m3; high OPEN** (known part 1.422882 m3 + D-2F-01 open). Candidate today: 6 bounded lines,
low 0.502 m3, high OPEN, 54 blank. Change in units: +12 lines gain a bound (+0.489692 m3 on the low end: A-1F-01 0.054,
P-1F-01 0.063, deficit set 0.372692); 42 lines stay HELD blank with the cause restated from 'precast governs' to their
existence cause. Hand checks: A-1F-01 0.15 x 0.20 x (1.00 + 0.80) = 0.054; P-1F-01 L2 0.15 x 0.20 x (1.30 + 0.80) =
0.063, high 0.03 x (1.30 + 0.449 + 2.265) = 0.12042; W14 L3 0.20 x 0.30 x 3.25 = 0.195, high 0.06 x (2.45 + 0.618 +
1.032) = 0.246; D-GF-13 0.03 x 1.80 = 0.054, high 0.03 x (1.00 + 1.503 + 1.260) = 0.11289.

Precast class vs RC state (why the two methods differ, per opening): 5 openings whose precast piece fits at 0.15 m are
HELD BY NAME under the printed 0.40 m (D-1F-03, D-1F-07, D-1F-10, D-2F-03, D-GF-10: cross-wall or column end 0.24 ..
0.26 m); 3 precast FLAGGED_NO_BEARING are RC HELD BY NAME with a column-owned end volume (D-1F-04, D-GF-06, W18); the
D-GF-11 / 12 shared pier is one pair occupying the pier once. A FLAGGED precast class on an RC-governed opening is not a
payable flag: it stays beside.

## 3. Evidence and controls

- R-T519-1 control: the 16 REQUIRED openings of T-519 give the same system (PROJECT_RC) and state (6 PRODUCED / 10 HELD)
  through this run's end check on the newer T-644 evidence (asserted in the builder).
- R-T524-1 conservation: the deficit set restated here = 0.372692 .. 0.437542 m3 (asserted).
- Drawing re-run this run: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha ab54dd55), decoded
  by the wrapper into the private folder; the T-644 jamb re-run test passed (fresh evidence byte-identical to the
  committed CSV).
- Second method (scratch, not committed: column outlines in a strip of full wall thickness from each jamb, no masonry
  union): P-1F-01 column face 0.450011 m (reader 0.449) AGREE; A-1F-01 no column within 3 m on either side (reader: an
  end of masonry 0.650 and a crossing 2.300, neither a column) consistent; lift doors L-GF / 1F / 2F-01 0.399956 /
  0.400044, 0.400011 / 0.399989, 0.399966 / 0.400034 m (reader 0.399 / 0.400): the doors sit centred between columns
  1.80 m apart (1.00 + 2 x 0.40), see F-T650-3.

## 4. Findings

**F-T650-1 (interpretation, for the Checker): 'FLAGGED under either rule' read as FLAGGED under the rule that governs
the opening.** On an RC-governed opening the precast FLAGGED classes (no bearing / shared pier) are beside only; the RC
deficit regime (R-T524-1, register LINTEL END VOLUME) governs and keeps the lintel on STR.CONC.LINTEL. No opening of the 60
has no masonry at both jambs (checked on the evidence: least end 0.000 at one jamb only, W06 / W18 / W22 / W29 / P-GF-01).
Head-room FLAGGED W13 / W26 stay on their lintel line HELD (the ledger says room exists under some pieces only).

F-T650-2: 26 of the 42 HELD-blank openings already show an end < 0.40 m beside (list in the JSON). When their existence is
established they need an R-T524-1 end-ownership assessment before any m3: designer items, not a lower quantity.

F-T650-3: the three lift landing doors read 0.399 m at one jamb because the reader truncates a 0.39996 m reach; the
strict R-T516-1 test then calls it FLAGGED_DEFICIT by 0.04 mm. Beside only today (register LIFT LANDING DOOR LINTEL
holds them); a bearing tolerance needs a Lead ruling before those lines are wired (R-T581-1 uses 5 mm for widths).

## 5. Freelancer (appendix only)

He has no lintel row (T-571 implied 54 pcs through the precast rule). Verdict proposals: payable form RULE_DIFFERENCE
(printed RC schedule governs; his implied pieces follow the company precast rule); quantity UNRESOLVED (no comparable
cell). 'Within 95 %' is not claimable for lintels.

## 6. Tests (`tests/t650`, 24; with t644 / t519_lintel_pieces / t524_lintel_end_ownership / t581_width_basis / t061: pass)

Villa X by hand (schedule for BLACK walls, bands 0-120 D20 / 121-250 D25): D1 BLACK 1.20 RC 0.080 .. 0.104 m3; W1 WHITE
0.90 precast 1.20 pc; W2 WHITE 3.80 -> 4.10 > 4.00 structural line; D2 1.205 in the printed gap -> SCHEDULE_SILENT; D3
deficit -> R-T524-1 record; D4 existence HELD -> blank; summary 0.19 .. 0.224 m3, never both; unscheduled black HELD;
curved band / no masonry -> structural; bound in one band covered, bound across a gap held; REQUIRED bound width held;
mirror + reorder invariance; capped end high OPEN. Adverse: scheduled opening given a precast piece refused; FLAGGED /
HELD / SCHEDULE_SILENT given 0 m3 refused; m3 outside the range refused; deficit without an R-T524-1 record refused;
mm / cm / 0 / negative / NaN / bool / text widths refused; duplicate, unknown block, line-set mismatch, width + bound
both given refused; freelancer figure as a cause refused. Training villa: rebuild == committed JSON; 60 RC; 8 / 10 / 42;
6 unchanged + 12 new bounds; conservation; control 16 / 16.

## 7. For the Checker (re-measure 4 openings on P7757 / ST p.13)

W14 (1F, L3 2.45 m, ends 0.618 col / 1.032), P-1F-01 (1F, L2 1.30, column 0.449 / 2.265), D-1F-07 (1F, L1 0.80, START
0.259 to a cross wall < 0.40 -> HELD BY NAME 0.036 .. 0.04377), L-GF-01 (GF, 1.00 between columns 1.80 apart). Run:
`bash scripts/agent_env.sh run research/agents_t650/t650_payable_form.py`.

## 8. Lesson row (proposed, ERS s.7)

| 2026-11-09 | two register entries gave the lintel two payable forms (precast pcs on every opening vs the printed RC schedule) and the T-644 piece table was built for one of them | a company rule was applied before checking whether a printed project schedule covers the opening | decide the payable form per opening by the resolution order first (curved band / no masonry -> structural; printed schedule in scope and band -> RC m3; silent -> HELD; else white precast / black HELD), then measure only in that form; the other method stays beside | tests/t650 | PROPOSED |
