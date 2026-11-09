# T-578 Handrails / balustrades / guards and stair nosing vs the freelancer in lm and nr (lane A, research only)

Worker 2, 2026-11-07, branch `agents/task-T-578`, candidate of record ARCH_TAKEOFF_V3.0.58 (= V3.0.57 for every code
read here: V3.0.58 moved only roof WP lines, T-507). No quantity, line, method, rule or registry file changed; nothing
released. Development villa, not an accuracy claim; R-T578-1 is for every villa. Build:
`research/agents_t578/t578_alsenan.py [--check]` -> `out/T578_RAIL_NOSING_RECONCILE.json` (pinned: line index V3.0.57,
FREELANCER_RAW_ROWS, T-412 nosing table, T-476 flight census). Sign throughout: **his - ours** (as the task states).

## 1. Physical elements (ERS s.2.1)

- WALL_HANDRAIL (B7-10): a rail fixed to a wall beside a flight, only where drawn (UP-STAIR-013).
- BALUSTRADE (B7-09): the guard on the open side of a flight, installed along the pitch line first to last nosing
  (sqrt(plan^2 + rise^2)), continuing as level pieces where the same band runs along a landing / well end / void edge.
- GUARD (B13-08): a separately drawn floor, roof or terrace edge guard, horizontal.
- NOSING: one front edge per riser (the arrival edge of a landing or floor included); lm = drawn front edge - drawn notch.

## 2. His rows (re-read this run from the pinned raw rows; labels checked by hash, no text copied)

- Railing: ONE row in all 885 rows of his six workbooks, finishes cover row 39 'internal railing', **18.95 lm**, a typed
  constant (no formula, no detail row behind it). No external / roof / balcony / fence railing row anywhere (scan of every
  cell for the railing word: the cover title and this row only). Confirms T-164 / T-393, which could not open the workbook.
- Nosing: no nosing row. The only lm he carries along the nosing edges is each step row's count x width in his marble
  sheet (booked in its area column, T-577 F-T577-3): main stair 63 x 1.20 = 75.60, inner (round) stair 28 x 1.20 = 33.60,
  entrance 5 x 2.80 = 14.00 -> **123.20 lm, 96 pieces**. His stair-side pieces (96 nr) and stair skirting (29.87 lm)
  belong to T-574; his door steps (7.70) to T-577 / T-584.

## 3. Rails (lm)

Ours valued: B7-09 **33.319174** (RL-05 16.324, RL-07 15.953174, RL-08 1.042) + B13-08 **21.550** (RL-01 6.262,
RL-02 4.921, RL-03 7.967, RL-06 2.400) + B7-10 0 (RL-12 NOT_APPLICABLE) = **54.869174**. His 18.95. **his - ours = -35.919174.**

| Cause | lm | Verdict proposal |
|---|---|---|
| roof / terrace guards RL-01..03: our list only (his row is 'internal', no external row) | -19.150 | ENGINE_RIGHT on scope (12.888 Checker VERIFIED) |
| ST-01 balustrade RL-07: outside his figure under every decomposition | -15.953174 | ENGINE_RIGHT on scope |
| D1 lobby rail RL-08 (decomposition A: his = ST-02 system + D-23) | -1.042 | ENGINE_RIGHT on scope |
| unexplained: 18.95 - (16.324 + 2.400) | +0.226 | UNRESOLVED (no breakdown) |
| HELD B7-09 (T-MS1-N >= 0.857 chord, T-MS2-LD >= 0.261, RL-09 0..?, RL-11 0..?, F-T476-1 0..1.875) | 0 (bound 1.118 .. unbounded) | HELD |
| HELD B13-08 (RL-04 0..7.500, RL-10 0..?) | 0 (bound 0 .. unbounded) | HELD |
| pitch vs plan: tested; plan length would lower ST-02 by 1.205719 and leave +1.432 (worse fit) | 0 | ENGINE_RIGHT (pitch) |
| both sides vs one: no wall rail drawn on any wall side | 0 | AGREE |

Every inclined census piece recomputed from plan + rise (straight flights to 1e-6; RS-C curved per going accepted only
between its pitch line 3.226974 and plan + rise, R-T480-1). Line vs pieces: RL-05 +0.000287, RL-08 +0.000067 (3 dp line
rounding), RL-07 0. % withheld (SCOPE / HELD causes). Like for like under hypothesis A: 18.724 vs 18.95 (+0.226), a
hypothesis about his scope, not a % claim.

## 4. Nosing (lm and nr; census T-412, no candidate line: T-424 QUEUED)

| Stair | his (count x width) | ours confirmed | his - ours | causes |
|---|---|---|---|---|
| ST-01 main (+ D1) | 63 x 1.20 = 75.60 | 48 edges 55.10 | +20.50 | +8.40 count (7 pieces beyond the 56 risers, UNRESOLVED); +9.60 his share opposite 8 HELD (drawn beside 7.594 on 6, 2 not drawn); +2.40 width 1.20 vs drawn 1.150 (ENGINE_RIGHT); +0.10 notches (ENGINE_RIGHT) |
| ST-02 round | 28 x 1.20 = 33.60 | 16 edges 18.25 | +15.35 | +14.40 his share opposite 12 HELD RS-C (drawn beside 13.85; Q-50 A cond); +0.80 width; +0.15 notches |
| ST-03 E1 | 5 x 2.80 = 14.00 | 5 edges 14.00 | 0 | AGREE (0.00 %) |
| **Total** | **123.20** | **87.35** (+20 HELD) | **+35.85** | count 8.40, HELD 24.00, width 3.20, notch 0.25 |

nr: his 96 vs ours 69 confirmed + 20 HELD; +27 = 20 HELD + 7 UNRESOLVED (ST-01). The candidate's FIN.STAIR.STEP_LM
(67.85 valued, 5 held, 2 excluded) is a different element (step basis per tread, UP-STAIR-008) and is named, not used.

## 5. Findings for the Lead

- F-T578-1: his railing figure is now proven to be a lone typed constant (raw rows re-read): no future task can
  decompose it further from his workbook; his scope stays a hypothesis.
- F-T578-2: the nosing has no candidate line (T-424 QUEUED behind T-423); until then the engine-vs-freelancer nosing
  figure is the research census 87.35 lm, DRAWING-CONFIRMED, never released.
- F-T578-3: ST-01 +7 pieces stays the only UNRESOLVED nosing cause (8.40 lm); the 20 HELD edges carry 24.00 of his lm.

## 6. Rule, tests, lessons row (proposed)

R-T578-1 (t578_rules.py): rail piece kinds INCLINED (pitch, plan refused) / HORIZONTAL / TURN (HELD, chord lower bound);
families kept apart; nosing one per riser, drawn edge - notch; his lm = his count x his width; causes close exactly; HELD
blank with bound, never 0; % only without HELD / SCOPE / UNIT; VERIFIED refused. Tests `tests/t578_rail_nosing_reconcile`
(25): fixture flight going 3.00 rise 1.80 = 3.498571 lm vs plan 3.00 kept apart, mm, rotation / mirror, Villa F closure,
nosing fixture, curved bounds; adverse: plan length billed for a flight refused, HELD winder edge / turn as 0 refused,
horizontal with a rise, inclined without a rise, VERIFIED, unnamed residual, fractional count; Alsenan pins (byte-identical,
totals, closures, no workbook text, edited input stops the build).

Lessons row: | 2026-11-07 | four tasks reconciled 18.95 lm of railing against decompositions of his scope without his
rows | the workbook was over the connector limit, so 'no breakdown' stayed a report, not a fact | read the pinned raw
rows first: a typed constant with no rows is classed as such once, and every decomposition of it is labelled a
hypothesis with its residual | tests/t578_rail_nosing_reconcile | PROPOSED |
