# T-374 Straight-bar cutting schedule (B11-02 bar bending schedule, shape code 00) for the 7 populations T-371 found SCHEDULABLE_NOW (development villa; rules for every villa)

Worker 1 (structural lane S), 2026-10-30, run session_01E6cPndAZoV3Hdbj7bmdmfg, branch `agents/task-T-374`. A
schedule built on the candidate's own figures: **no candidate line, rule, method or released quantity changes**; B11-02
stays PARTIAL. Drawings are named by Drive folder and title only; nothing private is in the repository.

## R2 (2026-10-31, worker 1): rework of the Verifier 2026-10-30 21:08 REJECTED at (f) / (h)

**Fault fixed.** The 38 line ids of the unresolved Checker downgrade record **DG-a97ec2ea66e02194** (verdicts/V3.0.20 ..
V3.0.29 DOWNGRADES.json, state HELD, resolved false, UNSUPPORTED BASIS: footing mesh BOTTOM_LONG / BOTTOM_SHORT run
side - 2 x 70 mm = the p.8 note-22 MINIMUM cover as bar-end position, with the p.13 boxed-bar leg of unprinted diameter
between bar end and face) were SCHEDULED with cut lengths and procurement in r1. A cutting length is exactly what the
record says has no supported basis. In r2 they are **HELD_DOWNGRADE by the record id**: cut length, count, bar mark and
procurement BLANK; the candidate value 874.862227 kg (= the record's engine_qty) only in the audit columns
`audit_kg_low/high` labelled `UNSUPPORTED BASIS (DG-a97ec2ea66e02194): candidate upper value, audit only`. The record is
a re-issue of DG-eba2b0b8c7397b9a / DG-d0012905259e345c / DG-1b0eacce2d68f2a5 (V3.0.19 / .18 / .17, same 38 ids); the
row names the record of the latest verdict set and lists the re-issues.

**All records read** (R-T374-6): every verdicts/V3.0.x/DOWNGRADES.json (V3.0.16 .. V3.0.29, 20 records, all unresolved)
is snapshotted with its file sha256 in `T374_BOUND_DOWNGRADES.json` (record ids, states, line ids only; regenerate with
`--snapshot-from <board>/docs/agents/verdicts`; a test compares it with the board when the board worktree is present).
Join of the 442 schedule lines to all 20 records: only DG-a97ec2ea66e02194 (and its three re-issues) touches them, 38
lines; the five lap / bar-end records (DG-30f5.., DG-8afa.., DG-a941.., DG-aaab.., DG-64e1..: 373 line ids) and the
concrete records touch none of the 442 (the lap / development lines were never in the schedule: R-T374-2).

**The 10 FTG '/m' lines (r1 SCHEDULED_BOUNDED).** Answer: **yes, the same basis.** All 10 (F8, F12, F13, F14, FF, long +
short) carry in their own formula `n x (side - 2 x 70 mm)` and cover text `MINIMUM 70 mm (... note 22 ...)`, exactly the
record's stated basis; they are not in its line list (they were BOUNDED for the Q-71 count). Booked **HELD_SAME_BASIS**
(R-T374-6b) naming DG-a97ec2ea66e02194 as the basis, cut length / count / procurement blank, candidate range
1,606.069136 .. 1,655.560494 kg in the audit columns. The signature is checked against the record: every one of its 38
lines carries it, else the build stops (test). Proposed to the Checker: extend the record to these 10 ids
(**DGP-T374-FTGM**); never edited here. FF (lift-pit raft) additionally sits under the DG-3521554d2fd011b9 blinding
question, which does not change its bar basis.

**Restated result (acceptance (a), (b)).** 442 lines bound: 125 SCHEDULED + 32 RUN_PART = **157 lines on 131 bar
marks**; 38 HELD_DOWNGRADE + 10 HELD_SAME_BASIS (FTG-BOT-MESH has no schedulable line now); 1 SHAPE_NOT_00; 65 HELD + 33
HELD_DEFINED; 17 BOUNDED_NO_ROW; 121 NA_SUPERSEDED.

| Population | Scheduled net kg (r2) | Candidate kg | Diff (named) | Held by downgrade (audit only) |
|---|---|---|---|---|
| FTG-BOT-MESH | **0** (was 874.862222 + 1,606.069 .. 1,655.560) | - | - | 874.862227 (DG-a97.., 38) + 1,606.069136 .. 1,655.560494 (same basis, 10) |
| COL-MAIN-BODY | 1,874.488889 | 1,874.486000 | +0.002889 (3 dp storage) | - |
| CB-BOTTOM | 731.755785 | 731.755000 | +0.000785 | - |
| CB-SUPPORT-TOP | 390.302044 | 390.303000 | -0.000956 | - |
| GB-MAIN | 1,252.908222 | 1,252.907000 | +0.001222 | - |
| **All** | **4,249.454940** | **4,249.451000** | **+0.003940** (storage rounding, 125 + 32 lines) | 874.862227 + 1,606.069 .. 1,655.560 |

4,249.454940 = 5,124.317162 - 874.862222 (the Checker's figure; this join reproduces it as the sum of the population
figures; the unrounded n x L x d^2/162 sum is 4,249.4549405.., display rounding only). The r1 "-0.000005 kg footing"
cause disappears with the footing rows.

**Procurement re-nested** (12 m stock ASSUMED - OWNER-APPROVED OD-V3-3; 459.947 kg on the two runs over 12 m stays
without procurement, lap HELD): on **3,789.508275 kg** of exact net with a procurement view (was 4,664.370), per mark
(no reuse) 287 stock bars = 5,458.370 kg; nested per diameter (FFD) **221 stock bars = 4,245.926 kg** (offcut 456.418
kg = 10.75 %; ø14 2.3 %, ø16 12.7 %, ø18 7.2 %; ø12 no longer present: all ø12 bars were footing mesh), lower bound
199 bars. No procurement figure enters any BOQ line.

**F-T374-2 text fixed.** r1 said "under A: SB1 top 118.300 kg ...". Wrong use of the answer: Q-74 is ANSWERED A (owner
2026-10-22) for the strap CONCRETE length only ("bars, formwork and excavation derived separately"); it sets no strap
bar length. The r1 'under A' kg figures are withdrawn as a re-booking proposal; the SB1 - SB3 bar lines stay
BOUNDED_NO_ROW on their own bar-end / section basis. The candidate text "owner Q-74 open" is quoted unchanged in the
CSV with an appended note naming the answer (9 lines).

**T-371 erratum**: `T371_ERRATUM.md` (E-1 FTG-BOT-MESH under DG-a97ec2ea66e02194, E-2 COL-TWIST-EXTRA); SCHEDULABLE_NOW
becomes 5 populations / 389 lines; merged T-371 files untouched.

**Tests** (`tests/t374_straight_bbs`, 16): r1's 11 kept (regression updated to r2 figures) + adverse: a line under an
unresolved record is never SCHEDULED (resolved record holds nothing; re-issue named); a run member under a record
refuses the run; a same-basis footing line HELD, a printed-length footing line kept, a record line without the stated
basis stops the build; the committed CSV has no scheduled line under any unresolved record; snapshot = board files.

Sections 1 - 8 below are r1; where they give FTG-BOT-MESH schedule rows, the 205 / 179 / 5,124.317162 totals, the
r1 procurement figures or F-T374-2's 'under A' figures, **this R2 section supersedes them**.

## 0. Inputs and binding

- Candidate lines: the merged T-297 extract `research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json` (ARCH_TAKEOFF_V3.0.16
  = V3.0.17, 2,505 reinforcement lines, sha256 2f28367b.., pinned in the builder) and the merged T-371 population
  binding (`LINE_BINDING_T371.json`, same sha). **Bound to V3.0.27 by projection**: V3.0.27 re-books exactly the 196
  slab lines of the merged T-318 inputs (98 development + 98 top-over-support); the builder imports
  `research/agents_t318/t318_inputs.py` and refuses any of its line ids; none of the 442 is among them (test). T-373
  (READY, reproduced V3.0.27 json f7972540 from the Drive copies) found every other rebar line id and figure unchanged
  (2,643 = 2,505 + 138 T-318 part lines). V3.0.27 itself was not re-run here: Checker re-measure item 1.
- Shape status: `research/agents_t371/T371_MATRIX.csv`; lap status per population: `research/agents_t366/T366_MATRIX.csv`.
- Source ledgers (read, not changed): T-148 `T148_COLUMNS.csv`, T-149 `T149_BEAMS.csv`, T-138 `T138_MEMBERS.csv`.
- Drawing re-read this run: Drive "Alsenan chalet project" / 'ST7757.pdf' (sha of the decoded copy in the private folder
  only), sheet 15 'TYP. DETAIL OF TWISTED COLUMN' (both variants) at 400 dpi (F-T374-1).
- Files: `t374_straight_bbs.py` (STRAIGHT_BAR_SCHEDULE_V1, stdlib), outputs `T374_STRAIGHT_BBS.csv` (one row per bound
  line, 442) and `T374_SUMMARY.json` (per population, the bar runs, procurement by diameter). Tests
  `tests/t374_straight_bbs` (11). Repeat: `python -I research/agents_t374/t374_straight_bbs.py --csv .. --json ..`.

## 1. Physical element and method (ERS s.2.1, s.3)

A schedule row is ONE physical straight bar shape (shape code 00): mark, diameter d, number n, cut length, net kg; the
procurement view (stock bars, offcuts, procurement kg) sits in separate columns. Installed (net) and procurement are
never mixed; laps are neither (OWNER_RULE_REBAR s.4: net, separately measured laps, procurement waste kept apart).

- **Cut length** = the line's drawn straight length less the printed covers only, exactly as the candidate measured it:
  footing bars side - 2 x 70 mm (p.8 note 22 cover against soil); columns the storey interval (T-148: height +
  controlling beam depth, bars through the joint); continuous-beam bottom bars the clear span face to face; support top
  bars 0.22 Ln1 + support + 0.22 Ln2 (p.11 / p.12); ground beams face to face (T-138). The end parts that need an
  authority (beam / GB bar ends, column storey laps, CB bottom overlap) belong to OTHER lines, HELD by T-366 / T-373:
  the row shows the bar without them and its lap column says so by name. No lap is ever borrowed.
- **Unit mass** d^2 / 162 kg/m (the candidate's own: rebar_unit_mass D2_OVER_162; footing lines print 0.888889 for
  d 12, checked). All lengths in integer 0.1 mm, so decimal-text boundaries are exact.
- **Procurement**: 12 m stock, ASSUMED - OWNER-APPROVED (OD-V3-3; printed nowhere, T-366). Two views: per mark (whole
  cut bars per stock bar, no offcut reuse: an upper bound) and per diameter nested (first-fit-decreasing across marks;
  a cutting plan, not a rule), with the lower bound ceil(sum / 12 m).
- **Runs through interior columns** (R-T374-5): T-138 r2 carries the main bars of three bands straight through their
  interior columns ('through column' ledger lines). The physical bar is the RUN, not the span segment: the segments are
  scheduled as RUN_PART of one mark. Runs over 12 m need splices: the splice COUNT follows from L, S and the lap
  range (owner s.2 formula), the cut lengths and procurement stay HELD with the lap.

Owner manual method vs drawing-derived method: the owner has no recorded BBS method; his lap convention (40 d / 60 d,
s.2) is a proposal under assessment and is never applied (owner s.4 (3)); his stock / splice formula is used only for
the splice COUNT, which needs no lap value inside the stated lap band. The drawing-derived reading is the only one.

## 2. Result per population (acceptance (a), (b))

442 lines bound: 163 SCHEDULED + 32 RUN_PART + 10 SCHEDULED_BOUNDED = **205 lines on 179 bar marks**; 1 SHAPE_NOT_00
(F-T374-1), 65 HELD + 33 HELD_DEFINED (no schedule kg, blank, never 0), 17 BOUNDED_NO_ROW (bar not fixed; candidate
range carried by name), 121 NA_SUPERSEDED (route G provisional lines the hand ledgers replaced: no bar).

| Population | Lines | Scheduled (marks) | Net kg (schedule) | Candidate kg | Diff (cause) | Not scheduled, by name |
|---|---|---|---|---|---|---|
| FTG-BOT-MESH (p.13 / p.9) | 51 | 38 exact + 10 bounded (48) | 874.862222 + bounded 1,606.069136 .. 1,655.560494 | 874.862227 + 1,606.069136 .. 1,655.560494 | -0.000005 (6 dp storage, 44 lines) | 3 HELD (two-mark footing, clipped outlines) |
| COL-MAIN-BODY (p.9) | 120 | 31 (31) | 1,874.488889 | 1,874.486000 | +0.002889 (3 dp storage, 31 lines) | 28 HELD (25 defined), 61 NA |
| COL-TWIST-EXTRA (p.15) | 2 | **0** | - | 12.642 released | **SHAPE_NOT_00** (F-T374-1) | 1 SHAPE_NOT_00 (12.642 kg carried), 1 HELD |
| CB-BOTTOM (p.11 / p.12) | 58 | 25 (25) | 731.755785 | 731.755000 | +0.000785 (3 dp storage) | 6 HELD_DEFINED, 27 NA |
| CB-SUPPORT-TOP (p.11 / p.12) | 77 | 13 (13) | 390.302044 | 390.303000 | -0.000956 (3 dp; 1 line also the 0.1 mm length print: CB1 8 x 3.3732 m) | 32 HELD ('0.3 Ln2' end bars unsized), 2 HELD_DEFINED, 3 BOUNDED 0 .. 27.156 kg, 27 NA |
| GB-MAIN (p.13) | 131 | 56 + 32 run parts (62) | 1,252.908222 | 1,252.907000 | +0.001222 (3 dp storage, 87 lines) | 23 HELD, 14 BOUNDED 549.901 .. 911.596 kg (section candidates D-33 / D-34, straps Q-74 / D-38), 6 NA |
| SLAB-TEMP (p.15) | 3 | 0 | - | blank | - | 3 HELD (no 160 mm row in the p.15 schedule) |
| **All** | **442** | **205 lines, 179 marks** | **5,124.317162** + 1,606.069 .. 1,655.560 | **5,124.313227** + same | **+0.003935 kg** | 12.642 kg SHAPE_NOT_00 by name |

(b) reconciled: every exact line's difference is checked line by line and named (KG_STORAGE_ROUNDING: the candidate
stores hand-ledger kg to 3 dp and footing kg to 6 dp; LENGTH_STORAGE_0.1MM: the ledger prints the length to 0.1 mm
but computed kg from the unrounded length); any larger difference stops the build. The population sums differ by
+0.002889 kg (columns) and +0.001222 kg (ground beams), above 0.001 kg, both wholly the named storage rounding of 31
and 87 lines. No difference is invented or absorbed.

**Bar runs (R-T374-5), from the T-138 r2 'through column' lines:**

| Run (mark) | Bars | Run length | Net kg | Splices / bar | Cut length, procurement |
|---|---|---|---|---|---|
| 7D4-F8 top (GB049) / bottom (GB048) | 3 / 6 ø16 | 10.10 m (5.45 + 0.40 + 4.25) | 47.881 / 95.763 | 0 | 10.10 m, 1 per stock, offcut 1.90 m each |
| 170-7C3 top (GB034) / bottom (GB033) | 3 / 6 ø16 | 13.77 m | 65.280 / 130.560 | 1 for any lap up to 10.23 m | HELD (lap HELD, T-366 GB-MAIN; splice position not printed) |
| 7D0-FC top (GB047) / bottom (GB046) | 3 / 6 ø16 | 18.57 m | 88.036 / 176.071 | 1 for any lap up to 5.43 m | HELD |

The splice counts agree with T-273 s.3 (merged). 459.947 kg of scheduled net sits on the two runs over 12 m and has no
procurement figure until a ground-beam lap authority exists.

**Procurement (separate from net; 12 m stock ASSUMED - OWNER-APPROVED):** on the 4,664.370 kg of exact net that has a
procurement view, per mark (no reuse) 384 stock bars = 6,585.481 kg; nested per diameter (FFD) **298 stock bars =
5,148.148 kg** (offcut 483.778 kg = 9.4 %; ø12 2.3 %, ø14 3.3 %, ø16 12.7 %, ø18 7.2 %), lower bound 274 bars. The
ø16 offcut is driven by the 4.20 / 4.50 m column bars (two per stock bar, 3.0 - 3.6 m left). The footing '/m' rows
(bounded) add 2,068.444 .. 2,135.407 kg per mark. No procurement figure enters any BOQ line.

(c) No row exists for any population T-371 called SCHEDULABLE_AFTER / GAP / OWNED_ELSEWHERE: the builder takes only the
7 NOW populations and refuses a row for any other status (test). (d) below. (e) The freelancer prices reinforcement as
one kg/m3 lump (44.19 t) with no bar, mark or shape: **RULE_DIFFERENCE, no %**.

## 3. F-T374-1: the twisted-column EXTRA bars are not shape 00 (T-371 corrected)

T-371 classed COL-TWIST-EXTRA SCHEDULABLE_NOW ('p.15 4ø16 EXTRA straight, 1M + 1M'). The merged T-148 ledger records
for BOTH twisted columns (COL-GF-09 and COL-GF-13) "top bend drawn without length: BLOCKED_DETAILING"; the candidate
extract kept that text only on the HELD line, so the released line (COL-GF-13, 12.642 kg) looked straight. Re-read this
run: ST7757.pdf sheet 15, both 'TYP. DETAIL OF TWISTED COLUMN' elevations, 400 dpi: the four extra bars inside the
spiral end at the bottom of the lower 1 M straight, and at the top of the upper 1 M each ends in a short inward
inclined bend, undimensioned (no leg length, no bend diameter: G-T371-0). Verdict: the bar is a bent shape, not 00;
**no schedule row; the 12.642 kg released net (4 x 2.00 m x 1.580247) is carried by name, unchanged** (the bend leg is
an additional HELD part, never 0). Correction for the T-371 matrix (Lead / lane I): COL-TWIST-EXTRA end_2 =
DRAWN_UNDIMENSIONED (p.15), bend_diameter NOT_PRINTED -> status GAP (G-T371-0); SCHEDULABLE_NOW becomes 6 populations /
440 lines. Generalised as R-T374-1b: the shape test reads the source-ledger row (cause / note), not only the
candidate extract; the cross-read of all 205 scheduled lines' ledger rows found this one bend only.

## 4. Other findings for the Lead / Checker (no quantity changed)

- **F-T374-2** strap beams SB1 - SB3: the candidate lines still say "owner Q-74 open" and carry readings A / B / C, but
  Q-74 is ANSWERED A (axis length between footing faces, owner 2026-10-22). Under A: SB1 top 118.300 kg, bottom 50.331 kg,
  SB3 top 32.577 kg, bottom 25.740 kg; SB2 stays bounded on its own row conflict (issued 100 x 50 vs off-sheet 80 x 50,
  D-38). A lane I re-booking item; this schedule carries them BOUNDED_NO_ROW meanwhile.
- **F-T374-3** the T-371 SCHEDULABLE_NOW count includes 121 superseded route G lines (NA, no bar) and 98 HELD lines: the
  schedulable bar content of the 7 populations is 205 lines, not 442.

## 5. Acceptance (d): fixtures and adverse cases

Villa V374 by hand (not the development villa): footing FA 2.00 m, 10 ø12, cover 70 mm -> 1.86 m, 16.533333 kg; the
same footing with cover 75 mm -> 1.85 m, 16.444444 kg (cover change); procurement 2 stock bars (6 + 4), offcuts
0.84 m + 4.56 m, 21.333333 kg; a '/m' footing with counts 9 .. 10 x 1.36 m -> 10.880000 .. 12.088889 kg (range, never
collapsed); column 6 ø16 x 3.60 m -> 34.133333 kg, 2 stock bars, offcuts 2 x 1.20 m, lap HELD by name; a band of
7.00 + 0.50 + 6.50 = 14.00 m, 3 ø16 -> one bar, 66.370370 kg, 1 splice for any lap up to 10.00 m, cut HELD. Adverse:
a hooked bar presented as 00 refused; a bend recorded only in the source ledger -> SHAPE_NOT_00; a lap borrowed from
note 9 for column bars refused (the printed p.15 NOTE 1 lap accepted for temperature bars only); a non-NOW population
refused; a HELD line blank, never 0; a candidate kg beyond storage precision refused; a fractional count refused; a
run whose count changes along it refused; splice boundaries 12.00 / 12.01 / 22.80 / 22.81 m at a 1.2 m lap -> 0 / 1 /
1 / 2 from decimal text (owner T-273 s.6 (3)).

## 6. Rule proposed (every villa; provenance T-374; a rule version only when adopted)

**R-T374-1** (straight-bar schedule): a shape-00 row only for a population whose shape census is SCHEDULABLE_NOW AND
whose line basis, including the merged source-ledger row, records no bent attribute; cut length = the drawn straight
length less printed covers; laps / development / starters never inside it unless PRINTED for that population; net kg
equals the candidate to its storage precision, every difference named; procurement (stock, offcut, nesting) in
separate columns, never in a BOQ line; a bar run through interior columns is one physical bar (splice count from L,
S and the lap band; cut lengths HELD while the lap is HELD).

## 7. Lessons-register row (proposed, ERS s.7)

| 2026-10-30 | a census classed the twisted-column extra bars straight (shape 00) although the drawing and the merged column
ledger show a short top bend | the census read the candidate extract and the drawing's dimensions, and the extract had
dropped the ledger's 'top bend drawn' text on the released line | read the source-ledger row and the drawn bar ends, not
only the extract, before calling a shape straight (every villa, T-374) | tests/t374_straight_bbs (bend only in the
ledger -> SHAPE_NOT_00; hooked bar as 00 refused) | PROPOSED |

## 8. Verdicts, self-gate, not done

Verdicts (r2): 157 scheduled lines ENGINE_RIGHT in net basis; the 38 DG-a97ec2ea66e02194 lines and the 10 same-basis
lines UNRESOLVED (HELD, cut length unsupported); r1 text: 205 scheduled lines ENGINE_RIGHT in net basis (n x L x d^2/162 = candidate to storage precision); COL-TWIST-EXTRA
shape ENGINE_WRONG in the T-371 census (bent, not 00), the 12.642 kg net unchanged; freelancer RULE_DIFFERENCE, no %.
Checker re-measure: (1) the 442 line ids against your own V3.0.27; (2) p.15 twisted-column top ends; (3) five rows by
hand: footing F5 BOTTOM_LONG 20 x 2.26 m ø12 = 40.177778 kg; column COL-GF-11 14 x 4.50 m ø16 = 99.555556 kg; CB8 span 2
bottom 7 x 5.745 m ø18 = 80.430000 kg; CB1 support top 8 x 3.3732 m ø18 = 53.971200 kg (candidate 53.972, length print);
run 7D0-FC bottom 6 x 18.57 m ø16 = 176.071111 kg, 1 splice. self-gate: a (real code + 11 tests) c (villa V374 by hand +
adverse) d (research / tests only, freeze 0) f (held blank, never 0; nothing released) h (442 lines bound once) PASS.
Not done: V3.0.27 not re-run this run (projection + T-373 reproduction); bent shapes (links, legs, starters) wait for
G-T371-0; offcut reuse is a procurement option, not modelled as a rule.
