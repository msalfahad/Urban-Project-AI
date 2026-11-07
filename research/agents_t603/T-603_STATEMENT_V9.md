# T-603 reconciled-quantities statement V9 (research, unwired; for the 12-13 Nov scorecard)

Worker 3 (lane I, non-candidate, backlog-permitted), 2026-11-07. Files: `t603_adapters.py` (R-T603-1), `t603_build.py`
-> `out/RECONCILED_STATEMENT_T603.json` / `.md` (`--check` rebuilds identical), `tests/t603_statement_v9/` (20). The
T-594 builder is imported read only; the build first rebuilds V8 and refuses to run unless it equals its committed
JSON and markdown, then checks every V8 key is carried byte-equal (lists extended as a prefix only). Sources sha256-
pinned (T-590, T-591, T-598 outputs, manifest V10). No drawing, workbook or client data; no candidate, rule, knowledge
or registry file; no quantity moves; nothing released (V3.0.58 not released; V2.9 + route G unchanged).

## Physical question (ERS s.2)

A RULE_DIFFERENCE row says: same element, both measured, the gap is a convention. T-590 / T-591 (merged, Checker
ACCEPTED) found which of those rows have a recorded Urban rule on our side. The statement must carry that class, per
row, without moving any delta or total; and the stair flight skirting, measured under two forms, must count once.

## Restated sections (totals unchanged, rows re-add, evidence kept from each row's own verdict)

| Section (restates) | Unit | Moved rows | Effect |
|---|---|---|---|
| T-545/beams@V9 (@V7) | m3 | 3 THROUGH_SUPPORT RD -> UNRESOLVED (+4.915076); GF B7 UNTRACED +0.120452 RD -> UNRESOLVED **counted apart** (F-C-T590-2) | RD 0 |
| T-551/columns@V9 (V4) | m3 | GF / 1F JOINT_HEAD -2.28125 / -0.385 RD -> UNRESOLVED; T-566 reading ranges restated (RD 0, UNRESOLVED -3.10125) | RD 0 |
| T-576 GF / 1F @V9 + the two 10E0 C7 readings | m3 | 9 + 4 (+ 9 + 5 alternative) per-mark JOINT_HEAD rows -> UNRESOLVED | nested / alternative: never added to the record |
| T-560/rebar@V9 (V5) | t | 6 groups 34.814694 t RD -> UNRESOLVED (HIS_SIDE_UNREADABLE: typed lump) | no % |
| T-574/skirting-room@V9 (V6) | lm | A-1F-01 arch jambs 0.30 RD -> **ENGINE_WRONG** (PV; owner method includes doorless jambs) | RD 43.62 -> 43.32 |

Joint rows of record: 5, **+2.248826 m3 signed** (7.581326 gross) + 0.120452 apart = T-590's +2.369278 (7.701778). All
37 joint rows (32 in record / nested / alternative sections + 5 in superseded ones, beside) stay UNRESOLVED with the
pointer **T-599 REJECTED** (UP-CONC-JOINT-001 not in RULES_INDEX); they return to RULE_DIFFERENCE SOURCED only when
T-599 merges with that rule (R-T603-1 (b), tested).

T-591 provenance: 117 live rows = **40 SOURCED / 76 SOURCED_RECITE / 1 NONE** re-added per unit to the T-591 counts;
115 annotated beside their row of record (governing source + refused citation, valued 0), 1 overtaken (D-GF-09 lintel
read, already UNRESOLVED in V8). F-T591-2: 8 plaster / paint rows re-cite UP-OPEN-SCHED-001 1.4.0, Q-73 refused;
F-T591-3: 2 dome rows re-cite Q-24, Q-29 refused.

Beside (valued 0): T-598 nosing supersedes the T-578 cross-reference: his 123.20 lm vs ours 107.371440 lm (85 edges),
his - ours **+15.828560** (was +35.85) = UNRESOLVED 8.400 (7 pieces) + HELD 4.800 + ENGINE_RIGHT 2.628560 (width 4.000,
notches 0.250, curtail -1.621440), residual 0; ours HELD 4.600 .. 6.992620 lm; nr 96 vs 85 + 4 HELD, gap 7 UNRESOLVED.
T-598 additions by status after F-C-T598-1: DRAWING-CONFIRMED 2.300, ASSUMED - OWNER-APPROVED 16.571440 lm.

F-C-T593-1 guard: 13 two-form pieces = ONE element, range **17.009049 .. 23.300481 lm** (ST-01 12.238505 .. 16.793338,
ST-02 3.300000 .. 4.457143, ST-03 1.470544 .. 2.050); each stair's flight row low equals its element low and its high
is at least the element high; the sum over forms 40.309530 lm is refused anywhere in the statement.

## Findings

- F-T603-5: T-551's beside column / beam pair (copied by T-590 and the T-600 row as 'reference - engine') is printed
  engine - reference. In the statement sign the pairs are GF **+0.620464**, 1F **+1.208362**, 2F **+0.420000** m3 (2F on
  the T-545@V7 reading, F-C-T590-1, not -0.532760). T-600 should start from these signs.
- F-T603-6: V4 sections T-551/columns (30.72 %) and T-545/beams (-0.34 %) carry a % beside HELD rows, which R-T579-1 (e)
  refuses; their @V9 restatements drop it (pct_was kept).

## Lesson row proposal (ERS s.7)

| 2026-11-07 | a provenance audit and a measurement merged on the same rows: a statement could promote a row's evidence with its
class, or sum two forms of one skirting | a reclass is a class move only (delta, name, unit, evidence kept; pointer to the
unmerged rule task), and a two-form element enters once as a range | R-T603-1 (a)-(f) (every villa) |
tests/t603_statement_v9 | PROPOSED |
