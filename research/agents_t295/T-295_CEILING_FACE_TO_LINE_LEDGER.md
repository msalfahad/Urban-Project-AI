# T-295: ceiling face-to-line ledger, every face of the merged ceiling ledgers against the candidate's ceiling line ids (development villa; every villa by R-T295-1)

Worker 3 (lane I), claim 2026-10-25 13:03 UTC. Integration dependency of T-284. Research only: no engine module, rule
or knowledge file, candidate line or released line changed; released default stays V2.9 + route G; nothing released.
ERS read: s.2.1 (physical element first), s.2.4 (reconcile to named causes), s.3 (one element, several geometries;
build before deduct), s.4 (rule + test, normal and adverse), s.7 (lesson row). Pattern: T-291 (R-T291-1).

## 1. Run and identity

Own run, Python 3.11.17, Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and
'ST7757 dxf.dxf' (`9f9d1179`): research/agents_t167/v304_run.py, then research/agents_t270/v3015_run.py:
**V3_0_15_BOQ_LINES.csv `a4dc01dd` REPRODUCED** (3,699 lines). The T-245 V3.0.16 lines are byte-identical to it (T-290
row), and V3.0.17 (T-254, MERGED 7c49e890 during this run) changes 48 column / ground-beam lines and adds 1, every other
line byte-identical (T-254 report s.1): no FIN.CEILING line moves, so these ids and states are the current candidate's.
Extract: `python3 -I research/agents_t295/t295_alsenan.py --extract <run>/v3015` -> CANDIDATE_V3015_CEILING_LINES.json
(36 FIN.CEILING lines + the stair / dome lines read to prove there is no soffit or dome-finish line: id, item, room /
element id, unit, state, quantity, gross, deductions, RFI text; no coordinate, no name). Ledger: `--write`; `--check`
rebuilds byte-identical. Inputs (committed, merged): T-283 CEILING_LEDGER_R3_EXPORT.json (39 pieces), T-281
LEDGER_T281.csv + summary.json (stair soffit rows and zone reconciliations), T-271 RECONCILE_T271.csv (chord residuals),
and the Checker's one-owner rulings of the T-281 / T-283 batch (Verifier 05:32 / 05:34).

## 2. Physical element and what the candidate measures

Under every slab, per floor piece, exactly one owner surface: the horizontal decor ceiling; a bulkhead vertical face
(owner method, Q-48 A + Q-43); the underside of a flight or landing (stair soffit, a stair finish); no ceiling (outlined
slab opening, shaft, stair well); an open dome position (DCR-4); a held part. The formwork soffit is a form, not a
finish area, and owns no face. The candidate measures the ceiling as **one FIN.CEILING line per room = the room's plan
area** (less a void it deducts), PROVISIONAL; it has no bulkhead, stair-soffit, dome or edge line. Read from the lines:

- the GF stair room (GF-R31F8AE) and the 2F stair hall (2F-R4D1B62) have ONE line each, 'stair-well ceiling / soffit
  (section)', **BLOCKED_RFI with no quantity**: their 'before' is BLANK, never 0;
- the 1F living (1F-R78C367) has TWO lines: floor face less its own void 59.978 + the double-height ceiling over the void
  16.005 (= its piece 75.983); the per-line split of its faces is not established: they bind to the LINE GROUP;
- the GF open + pantry (GF-RC99C2A) is one line 110.9227 = 126.9277 less the void it deducts 16.005;
- five FIN.CEILING lines are EXTERIOR soffits over outside air (SOFFIT:GF:PL-01 / -02 / -03, SOFFIT:1F:PL-04 / -05,
  SOURCE_DERIVED, T-121 / T-127): no interior face lies in them (listed UNMATCHED with that reason);
- the 1F dressing (1F-RFFE7AF, decor 2.970 m2 DRAWING-CONFIRMED) has NO candidate ceiling line: a missing scope;
- the stair (FIN.STAIR.FLIGHT, lm, BLOCKED) and dome (STR.CONC.DOME, m3) lines are not finish areas: no soffit or dome
  finish line exists, so every stair-soffit face outside the GF stair room and every dome face binds to NO line.

## 3. The ledger (CEILING_FACE_LINE_LEDGER_T295.csv: 79 faces, each once; LINE_SUMMARY_T295.csv: 36 lines, each once)

Binding (R-T295-1 rule 2): owner surface + room -> the room's FIN.CEILING line for DECOR / BULKHEAD / HELD_CEILING;
STAIR_SOFFIT to the stair room's own 'stair-well ceiling / soffit' line where one exists (only GF-R31F8AE), else NO
line; VOID / DOME never in a line. Every face also names the line that books its plan area TODAY (`engine_books_in`), so
the 'before' of each line is decomposed by owner. 31 lines hold faces (29 measured + 2 BLOCKED), 5 exterior soffit lines
hold none (listed), 0 faces unbound without a reason.

| Owner / status | Faces | Plan m2 | Carried m2 | Where |
|---|---|---|---|---|
| DECOR / DRAWING-CONFIRMED | 32 | 362.0061 | 362.0061 | 29 room lines + the 1F line group; 5.6258 in the BLOCKED 2F stair-hall line; 2.970 (1F dressing) in NO line |
| BULKHEAD / ASSUMED — OWNER-APPROVED (Q-48 A + Q-43) | 14 | 27.9345 (vertical) | 27.9345 | addition to the room's line (the candidate measures no bulkhead) |
| STAIR_SOFFIT / DRAWING-CONFIRMED | 3 | 6.635 | 7.1837 (true, O = D) | MS1-LD 1.440 in the BLOCKED GF stair line; MS2-L 4.3037 and MS2-LD-E 1.440: NO line |
| STAIR_SOFFIT / HELD | 8 | 24.9757 | BLANK | MS1-U / MS2-U / MS2-LD-W (O vs D both shown), MS1-L CONFLICT C-ST-4 3.2256 .. 4.5015, MS1-T / MS2-TR (winder), ST-02 9.0138, the flight under the GF bands 1.7719 |
| STAIR_TOP / HELD | 2 | 4.990 | BLANK | GF stair top 1.750 (BLOCKED GF stair line), 2F shaft top 3.240 (no line) |
| HELD_CEILING / HELD | 6 | 32.2927 | BLANK | 2F stair box 12.9742 (BLOCKED 2F line), class P-2 19.146 (no line), B23 underside 0.1725 (1F group) |
| DOME / HELD (DCR-4) | 8 | 30.7181 | BLANK | no line: 29.0695 over six 1F pieces + 1.6486 over walls |
| VOID / DRAWING-CONFIRMED | 6 | 22.1109 | (no ceiling) | no line: GF light well + pocket 14.9434, light-well strip 0.0625, shafts 3.240 x 2, stair wells 0.315 / 0.310 |

Closures (rule 4): every one of the 39 pieces = its faces, residual 0.0000 m2 except the named ones (T-271 overlay chord
residuals GF-R7512EA -0.0011, GF-R75FBAE +0.0033, 1F-R3CFCFD +0.0021, kept in the ceiling; GF open -0.000079 = T-281
arc residual -0.000061 + T-283 rounding -0.000018; GF-R7512EA left 0.0001 = 4-decimal rounding). Against the sources
per status: decor 362.006092 = T-283 361.2287 + 0.777392 (0.000000); owner bulkheads 27.9345 (0.0000); no ceiling
22.110906 (0.000000); domes 30.7181 vs discs 30.718 (+0.0001, rounding of the over-piece split); stair zones 33.0755
(0.0000). Per line: engine + the deductions it re-measures nowhere - the plan of the faces it books = |remainder| <=
0.000983 m2 (GF-RC99C2A, the 126.9286 vs 126.9277 chord of the split face); every other line <= 0.000055.

**The Checker's one-owner rulings (T-281 / T-283 batch, 05:32 / 05:34) applied, each piece once:** GF 0.777392 north of
riser 315 -> DECOR (in L-eb3be58f; not in T-283's 91.4047); the light-well bottom-step strip 0.062506 -> VOID; the
flight under band 'B3 (With Stair)' / CA 1.7719 -> ONE stair-soffit HELD row (decor vs soffit RULE_DIFFERENCE pending
the height test); T-281's member rows 1.760625 under the same lanes are listed as the ALTERNATIVE measurement, outside
every total (0.011275 apart: the two ledgers' piece sets, column 380 0.040 vs GF-156 0.036, not reconciled here); 1F
0.1725 -> the B23 underside over the MS2-L foot, ceiling trade, HELD, NOT a stair soffit.

## 4. Engine (candidate = released FIN.CEILING) vs this ledger, line by line (engineering terms)

Interior FIN.CEILING with a quantity (29 lines): **403.1629 m2** (PROVISIONAL, plan area of the room). This ledger carries
**362.0061 m2 decor DRAWING-CONFIRMED** (353.4103 in those lines + 5.6258 in the BLOCKED 2F line + 2.970 in no line):
**-41.1568 m2 (-10.21 %)**, every m2 named (villa_reconciliation_m2, identity residual 0.000000):

| What the 29 lines book besides decor | m2 | Why it is not decor |
|---|---|---|
| open dome positions | 29.0695 | DCR-4: plan HELD, never in FIN.CEILING (Q-44 A) |
| stair soffit pieces (ST-02 9.0138 + 1.7719 under the bands; ST-01 MS2 10.725 less its well) | 21.2007 | stair finish (T-281), not a room ceiling |
| no ceiling (light well + pocket, strip, 1F well) | 15.3159 | outlined slab openings / stair well |
| B23 underside over the stair foot | 0.1725 | HELD (ceiling trade, shaft finish undecided) |
| less the void the GF line already deducts | -16.005 | the engine's own deduction (light well 13.3925 + round flight 2.3791 + pocket 0.2334, T-271 r2b) |
| remainder (chord / rounding) | -0.0010 | polygon chord of the split GF face |

Then **+5.6258** decor in the 2F stair hall, whose only line is BLOCKED (engine BLANK: the line is 'replaced', not
'corrected'), and **+2.970** decor in the 1F dressing, for which the candidate has NO ceiling line (missing scope: a new
line for T-284, Gate B hand check). Freelancer decor 409.58: ledger -47.574 (-11.62 %); no verdict on a total while
domes 30.718, stair zones 33.076, class 19.146 and the 2F stair box 12.974 m2 stay HELD (T-283 verdicts unchanged).

The five EXTERIOR soffit lines (PL-01 19.181, PL-02 5.640, PL-03 12.834, PL-04 4.374, PL-05 2.417 = 44.446 m2,
SOURCE_DERIVED, finish HELD Q-68 C) hold no interior face and stay as they are. **POSSIBLE OVERLAP (named, nothing
double counted today):** T-271 s.2 says the HELD-class GF garden band 9.101 + merged band 4.885 'may be one of the T-127
candidate soffits'; both are HELD BLANK here, so the class decision (P-2) must be checked against PL-01 / -02 / -03
before either is carried.

## 5. T-284 consumer shape

One row per face (`face_id`, `physical_id`, `piece`, `room_id`, `owner`, `plan_m2`, `carried` (BLANK when HELD /
UNKNOWN), `status`, `plan_status`, `range_lo` / `range_hi` (both readings, never summed), `held_item`, `binding`
(LINE / LINE GROUP (SPLIT_NOT_ESTABLISHED) / NO_LINE / ALTERNATIVE), `line_id` or `line_group`, `engine_books_in`,
`basis`, `source`). Per line: LINE_SUMMARY_T295.csv (engine state and quantity, booked by owner, remainder, carried by
owner). Decisions T-284 must take (not taken here): (a) the 1F living's two lines: merge, or obtain the void overlay
split (never pro rata); (b) the GF stair room's line is FIN.CEILING 'stair-well ceiling / soffit': whether its stair
pieces stay in the ceiling family or move to a stair-soffit line; (c) the 1F dressing's new line; (d) bulkheads as a
component of the room line or a sub-line. Side table EDGES_AND_ALTERNATIVES_T295.csv: 55 edge / cove / junction rows (m,
nr; HELD; the candidate has no line for them) and 25 alternatives (24 drawing-derived bulkhead candidates, D-40, never in
a total; the T-281 member rows).

## 6. Rule, tests, lesson

- **R-T295-1** (ceiling_line_ledger.py, PROJECT-INDEPENDENT; provenance T-271 r2b / T-283 r3 / T-281 / Checker
  05:32-05:34 / R-T291-1): one owner surface per plan piece (alternatives declared, outside totals); binding by owner +
  room; VOID / DOME / formwork never ceiling; a piece in a multi-line room binds to the line group (no pro rata); HELD and
  UNKNOWN blank with the plan shown; ranges never summed; closure per piece and per status; line vs faces decomposed into
  named parts with the engine's own deductions, remainder reported with its sign.
- **tests/t295_ceiling_line_ledger** (26): villa C hand truth (hall 6 x 5 with stair 2.4 x 1.5 true 4.024922, well
  1 x 2, decor 24.400, bulkhead 5.000 x 0.150 = 0.750; bed 4 x 3.5 with a dome r 1 = pi HELD, decor 10.858407; lounge
  20.000 over two lines as a group; store 6.000 HELD in no line; decor 55.258407; line 28.000 + 2.000 - 30.000 = 0; order
  invariant; declared shares 16 / 4); adverse: one face in two lines, VOID / dome as ceiling, HELD as 0 (face and total),
  one stair piece as decor AND soffit, range summed, CONFLICT without both readings, formwork line, unnamed residual, pro
  rata, mm2, AOA without source, VERIFIED without run, unplanned face; Alsenan: byte-identical rebuild, csv a4dc01dd, 36
  lines once (5 exterior listed), 79 faces once, 39 pieces closed, source closures, Checker rulings, held blank, line
  states, no-line faces, villa reconciliation, no coordinates.
- **Lessons register row (s.7, proposed):** 2026-10-25 | the ceiling integration (T-284) was framed as 'carry decor +
  bulkheads into the ceiling line', but the candidate's ceiling lines are not one grain: two stair rooms have one BLOCKED
  'stair-well' line, the 1F living has two lines (floor face + double-height ceiling) with no face split, the 1F dressing
  has none, and 5 'ceiling' lines are exterior soffits | the target lines' grain and state were assumed from the ledger
  side (as T-291 found for blockwork) | before a face-to-line integration, extract the item family's lines, bind each
  face by owner + room, decompose each line's 'before' into the faces it books (engine deductions included), and list
  multi-line rooms, BLOCKED lines, missing lines and lines with no face | tests/t295_ceiling_line_ledger (normal: room
  in one line, group; adverse: a face in two lines, VOID as ceiling, pro rata) | OPEN (T-295 READY).

## 7. For the Checker (re-measure / re-derive)

1. Re-extract the FIN.CEILING lines from your own V3.0.15 run (csv `a4dc01dd`): 36 lines; L-2175a965bb7c48a50e6c and
   L-dd6930fd19ca1b908c56 BLOCKED_RFI blank; 1F-R78C367 = L-fc116bb666b184740090 59.978002 (gross 75.983002 less its own
   void 16.005) + L-35341ff2e6a848b9436b 16.005; 5 SOFFIT:* lines 44.446.
2. Re-add GF-RC99C2A (L-eb3be58fc760b39f0e38 110.922696): faces booked 126.928679 = decor open 91.4047 + pantry 8.955 +
   slab north of 315 0.777392 + stair 9.013781 + 1.7719 + void 14.9434 + strip 0.062506; + its deduction 16.005 ->
   remainder -0.000983 (chord of the split face 126.9286 vs 126.9277).
3. Re-derive GF-025 from T-281: MS1-U 3.720 + MS1-LD 1.440 + MS1-T 1.495 + MS1-L lane 3.755 ((3.30 - 0.15) x 1.20 -
   column 36B 0.025) + well 0.315 = 10.725, + stair top 1.750 = the GF stair piece 12.475; column 36B is the face's
   notch, outside it.
4. Confirm the 1F dressing (1F-RFFE7AF 2.970) has no FIN.CEILING line in the candidate.

## 8. What stays HELD (by name) and what is not done

HELD blank: stair soffit true areas (O vs D, C-ST-4, winder / helicoid C-ST-3, hidden pairs) 24.976 m2 plan; domes
30.718; class P-2 19.146; 2F stair box 12.974; stair / shaft tops 4.990; B23 underside 0.1725; the edges / coves / board
type / concrete-ceiling plaster rows of T-283. Not done here (T-284's): any line change, item-code mapping, the 1F
group split, the exterior-soffit overlap check against P-2, the height test of R-CEIL-R3-1 (Checker 05:32).
