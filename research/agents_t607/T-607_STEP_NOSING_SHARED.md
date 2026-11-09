# T-607 ST-01 steps and nosing: one shared residual (his 63 vs the governing 56), settled once by edge id

Worker 2 (lane A), 2026-11-07. Research files `research/agents_t607/*` and `tests/t607_step_nosing_shared/` only; no
engine, rule, knowledge, method, registry or candidate file touched; nothing released; no candidate quantity changed.
Development villa, not an accuracy claim; R-T607-1 is for every villa. Sign: **his - ours** (as T-578 / T-598 / V9).
ERS applied: s.2.1 element, s.2.2 evidence, s.2.3 first principles, s.2.4 reconciliation in units, s.2.6 statuses, s.2.7
escalation test (not met: no owner question), s.4 rule + test, s.7 lesson. Rules: R-T412-1, R-T434-1, R-T588-1 (d),
R-T584-1 (c), R-T598-1, UP-STAIR-008, OWNER_RULE_STAIRS_2026-10-24 S-9 / A8, Q-46 A.

Build: `t607_extract.py --dxf <P7757.dxf> --st <ST7757.dxf> --write` (own read by handle; Drive 'Alsenan chalet project'
P7757_DXF_COMPRESSED.zip and 'ST7757 dxf.dxf', decoded into `.work/private` only) -> `T607_DRAWN.json` (handles, layers,
lengths, angles, residuals, vote counts, printed level figures; no coordinate); `t607_alsenan.py [--check]` ->
`out/T607_SHARED_RESIDUAL.json` (pinned inputs; his cells as numbers through the merged T-577 reader).

## 1. Physical element and the "one element or two" answer

- Each ST-01 riser has ONE nosing edge (R-T412-1): 56 edges = GF->1F 27 (10 + 5 + 12) + 1F->2F 25 (12 + 1 + 12) + D1 4
  (section A-A, Q-46 A; T-434 / T-598 MERGED).
- On a TREAD / WINDER edge the commercial step piece (UP-STAIR-008: tread + riser + nosing) holds its own nosing: steps
  and nosing are ONE element there, priced once by the flight's step line (B7-06). On an ARRIVAL edge (landing / floor)
  there is no step piece: a nosing-only element, priced by B7-05. So the two lines PARTITION the 56 edges: 50 step
  edges (9 / 5 / 11 / 11 / 11 / 3 on the six step lines; MS1-L N10 fronts the first winder, MS1-T line) + 6 nosing
  edges, each claimed once (shared-edge table in the JSON, 56 rows, claims = 1); the MS2-L second-reading step line
  L-1e88.. claims none. No edge is priced twice within or across the two lines.
- His side: ONE row, MRB.B23 x C23 = 63 x 1.20 (his step row; he has no nosing row, T-578). Statement V9 compares that
  one cell twice: as steps (T-584/stair-steps lm / nr) and as the nosing census (T-598/nosing@V9, beside). The 7 pieces
  / 8.40 lm in both are therefore ONE cause, **C-T607-1**: entered once in each line it feeds (each line still closes)
  and counted ONCE in any total (7 nr / 8.40 lm, never 14 / 16.80). The same count also sits in his MRB.B26 (63 side
  pieces, T-574/skirting-pieces, RULE_DIFFERENCE whole): no third residual.

## 2. Completeness sweep: is any drawn ST-01 front missing from the 56? (own read, R-T607-1 (b))

Every LINE of a stair-front length (1.150 / 1.258652 / 1.626346, layers 5 / 2) in the stair shaft on the GF, 1F and 2F
plans was classed; plans registered on their wall lines (GF->1F 128 votes vs runner-up 40; 1F->2F 134 vs 36):

| Plan | CENSUS | DUPLICATE | SECOND_READING (coincides with) | NAMED_OPEN | UNMATCHED |
|---|---|---|---|---|---|
| GF | 34 | C4 (= 485), 49C (= 2C6) | 14 lines = 7 pairs, east lane south of D1 = MS1-U N05 .. N11 (<= 0.3 mm) | - | 0 |
| 1F | 46 | - | 8 lines BE4 .. BEB = the MS1-T fan seen below the cut (0.3 mm) | - | 0 |
| 2F | 24 | - | 23 lines, west lane = MS2-L N01 .. N12 seen below the cut (0.7 mm) | 2F1F / 2F20 (Q-ST-11) | 0 |

Second drawing (ST7757, by handle): ST p.4 west 12 + 3 radials + closing 2F3 + east 12; ST p.5 west 12 + closing 5E2 +
east 11 + **648**; no other stair line in either window. NEW: ST p.5 line 648 (1.626346, 45 deg) sits exactly where the
arch 2F diagonal face 2F20 sits relative to the closing face (0.0 mm): the Q-ST-11 diagonal is drawn on TWO drawings,
not one (T-598 s.5 item 3 said one). The section still admits one closing riser; it stays a designer item, never added.

**Result: no drawn ST-01 front exists outside the 56** (UNMATCHED 0 on three plans and two ST sheets). The only open
physical candidate is the Q-ST-11 diagonal (+1 at most).

## 3. His 7 extra pieces by mechanism (R-T607-1 (c); exact reproductions only, never a best fit)

| Reading | Pieces | Edge ids / basis | Physical? | Admissible? |
|---|---|---|---|---|
| R1 SECOND_READING: the GF east lane reads as one 11-step flight (D1 4 solid fronts + 7 dashed pairs at the same 0.300 rhythm) | +7 | the 7 dashed pairs 497/498, 48B/496, 48C/495, 48D/494, 48E/493, 487/492, 489/491 = MS1-U N11 .. N05 (already in the 56) | no | yes |
| R2 STOREY_ESTIMATE: ceil(storey rise / riser), riser 150.0 .. 155.0 mm, printed +0.30 / +1.00 / +5.50 / +9.70 | D1 5 - 4 = +1, GF->1F 30 - 27 = +3, 1F->2F 28 - 25 = +3 | no edge exists | no | yes |
| 7 further combinations (T607 JSON) | +7 | each needs a reading T-434 / T-598 rejected (4-riser plan turn, ST p.4 12 + 4, floor edges left out) | 4 of them include Q-ST-11 | no |

All 8 exact second-reading combinations contain the GF east 7 pairs. The storey estimate does not describe his other
two stairs (ST-02 would need 161.0 .. 166.5 mm, E1 170 .. 200 mm; he matches their drawn 28 / 5), which weighs toward
R1, but a reproduction is evidence of his method, not proof: **his mechanism stays named between R1 and R2, never
chosen (R-T434-1).**

## 4. Verdict proposals (who is right, per cause)

| Cause | nr / lm (his basis) | Before (V9) | Proposal | Hand check |
|---|---|---|---|---|
| C-T607-1 ST-01 pieces beyond the governing count | 7 / 8.40 | UNRESOLVED in steps AND UNRESOLVED in nosing (two entries) | **ENGINE_RIGHT** on 56, ONE cause entered once per line, once in totals; his mechanism R1 / R2 named | 63 - 56 = 7; 7 x 1.20 = 8.40; no drawn edge for any of them (s.2); R1 repeats 7 census edges; R2 adds undrawn risers |
| Steps vs nosing on one front edge | - | ELEMENT_REGISTER 'NOSING EDGE' question open in V9 | one element on a tread edge (step line), nosing-only on an arrival edge (B7-05) | 50 + 6 = 56, claims = 1 each |

Effect on the statement (lane I, nothing wired here): steps lm UNRESOLVED 8.4 -> ENGINE_RIGHT 8.4 (closure unchanged:
his 109.2 - ours 67.85 = 41.35); steps nr UNRESOLVED 7 -> ENGINE_RIGHT 7; nosing beside UNRESOLVED 8.4 -> ENGINE_RIGHT
8.4 with pointer C-T607-1 (beside, valued 0); headline UNRESOLVED lm drops by 8.4 once. T-574/skirting-pieces ST-01 row:
its count check text '52 .. 54 risers drawn (+9 .. +11)' (T-084) is superseded: governing 56, +7 = C-T607-1.

## 5. Findings for the Lead

- F-T607-1: Q-ST-11 2F diagonal face is also on ST p.5 (648, 0.0 mm): two drawings, not one (designer list, beside
  T-598 item 3). No count change (section A-A governs).
- F-T607-2: the 1F plan fan BE4 .. BEB and the 2F west lane are second readings (MS1-T, MS2-L), not pieces; the 1F
  fan also coincides with the 2F closing riser 12B4 / 12B5 (stacked turns): a future reader must not count it.
- F-T607-3: statement row T-574/skirting-pieces carries a stale count-check text (T-084 52 .. 54); restate as 56 /
  C-T607-1 in the next statement version.

## 6. Rule, tests, lesson

R-T607-1 (t607_rules.py docstring). Tests `tests/t607_step_nosing_shared` (30): Villa K607 (2 flights + landing, the
reference counts one extra piece that is the upper flight's front drawn dashed on the lower plan; registration at
0 / 37 / 90 / 211 deg and mirrored; extra = 1 settled ENGINE_RIGHT; storey estimate cannot reproduce an odd total of
two equal storeys); adverse: a valued winder front refused, one edge claimed by two step rows refused, an edge in step
and nosing / an arrival edge in a step line refused, orphan edge and a second reading claiming an edge refused, an
UNMATCHED drawn front keeps the extra UNRESOLVED, a physical-open or rejected-reading reproduction never ENGINE_RIGHT,
metres among millimetres never match, fractional pieces / m2 / two amounts under one cause id refused, ambiguous
registration refused, the shared cause summed per line refused. Alsenan pins: rebuild byte-identical, private re-read
SAME AS COMMITTED (skipped without private input), UNMATCHED 0, 56 edges with one line each, step-line ids equal the
merged T-584 table, the 7 by edge and by storey, only the GF east pairs admissible, totals once, no coordinates.

Lessons-register row (proposed): | 2026-11-07 | one freelancer cell (63 x 1.20) carried as an UNRESOLVED 8.4 lm in two
of our lines (steps and nosing) for a week, its 7 pieces never named | each task compared his row with its own trade's
edges; nobody swept every drawn line of the shaft on all plans or checked which of our lines a reference cell feeds |
before blaming a reference count: class every stair-family line of the shaft on every plan (census / duplicate / second
reading after wall registration / open / unmatched); test each mechanism for an EXACT reproduction; a cell that feeds
several lines is one cause, entered once per line and once in totals (any villa) | tests/t607_step_nosing_shared |
PROPOSED |

Self-gate: research + tests only; non-Alsenan fixture with adverse cases; reproducible (`--check` REPRODUCED; private
re-read SAME AS COMMITTED); nothing wired or released; no client data, no drawing text other than level figures, no
coordinates. Missing: his own breakdown (none in his row: R1 vs R2 stays named, not proven); Q-ST-11 (designer).
