# T-609 reconciled-quantities statement V10 (research, unwired; for the 12-13 Nov scorecard)

Worker 3 (lane I, non-candidate, backlog-permitted), 2026-11-07. Files: `t609_adapters.py` (R-T609-1), `t609_build.py`
-> `out/RECONCILED_STATEMENT_T609.json` / `.md` (`--check` rebuilds identical), `tests/t609_statement_v10/` (23). The
T-603 builder is imported read only; the build first rebuilds V9 and refuses to run unless it equals its committed JSON
and markdown, then checks every V9 key is carried byte-equal (lists extended as a prefix only). Sources sha256-pinned
(T-597, T-602, T-604 manifest V12, T-606, T-589 packs). No drawing, workbook, coordinate or client data; no candidate,
rule, knowledge or registry file; no total moves; nothing released (V3.0.58 NOT RELEASED; V2.9 + route G unchanged).

## Merged since V9 and taken in (claim 2026-11-07T19:04Z)

| Source | Section / block | Unit | Effect (reference - engine) | Evidence |
|---|---|---|---|---|
| T-602 (+ T-604 V12 family) | T-577/marble-lm@V10 | lm | door steps UNRESOLVED +2.90 = G-01 street-gate step +2.50 ENGINE_WRONG (ENGINE_OMISSION, FR-T602-1) + 0.40 UNRESOLVED (SCOPE); residual 0 | 2.50 V (Checker re-measure), 0.40 PV |
| T-606 | T-574/skirting-room@V10 | lm | 1F living outline UNRESOLVED -8.66 = -8.40 ENGINE_RIGHT (stair-well walls) - 0.20 ENGINE_WRONG (opening notch faces, merged split) - 0.06 UNRESOLVED; section UNRESOLVED 9.693234 -> 18.293234 (the offset is named, not new) | V / WP / PV |
| T-180 P02 2F, P03 1F | T-545/beams@V10 | m3 | evidence only: 2F THROUGH_SUPPORT 0.42 (still UNRESOLVED, joint pointer) and 1F RUN_COUNT -1.908946 WP -> V; no class or delta moves | V |
| T-180 P01, P02 1F / GF, P03 GF | beside | m3 | COUNT rows already V; P02 1F partial (CB10-12 open), P02 GF not read, P03 GF F-C-P03-2 ENGINE_WRONG -0.005295 m3 named, not applied | - |
| T-597 | beside T-565 NOT_COMPARABLE | m2 | pits union 129.234375 / zone 124.648614 / pool envelope 11.851050 m2 VERIFIED plan only; depths HELD S01; FF / F10F HELD; F-C-T597-1 drawn sum 129.43 / overlap 0.195625; engine -0.000941 m2 immaterial; his NO_ROW, no % | - |
| T-606 F-T606-1 | beside (pending fix) | lm | ENGINE_WRONG 11.170 lm (Checker; worker 11.22): FIN.SKIRTING 209.428592 -> 198.258592 (V3.0.58), 209.728592 -> 198.558592 after V12; no fix row yet, not applied | V |

Not merged at the r1 claim, so not taken in r1: T-599 r2 (READY), T-600, T-605 (TODO), T-607 (READY).

## r2 (rework after REJECTED r1; claim 2026-11-07T23:00Z, base engine 66d3ad9c)

r1 was refused on the merged tree only: T-599 r2 rewrote the V9 pointer `in_rules_index` (false -> true) in the T-603
JSON, so the r1 out/ no longer reproduced. r2 merges the working branch, rebuilds V9 (equal to its committed output),
and takes in everything merged since r1 (R-T609-1 (f)-(h) added). Tests 23 -> 36.

| Source | Section / block | Unit | Effect (reference - engine) | Evidence |
|---|---|---|---|---|
| T-599 r2 | T-545/beams@V10, T-551/columns@V10 | m3 | GF THROUGH_SUPPORT 2.901714 = matched joint 2.28125 RULE_DIFFERENCE + residual 0.620464 UNRESOLVED; 1F 1.593362 = 0.385 RD + 1.208362 UNRESOLVED; 2F 0.42 whole residual (matched 0), row unchanged; column JOINT_HEAD GF -2.28125 / 1F -0.385 UNRESOLVED -> RD. Of record: n 4, signed 0, gross 5.3325 = the T-599 headline; beam UNRESOLVED 2.369278 (2.248826 pair residual -> T-600 + GF B7 0.120452 apart) | matched PV (Checker 2 / 4 1F marks), residual WP, columns CV unchanged |
| T-599 r2 | T-576 GF / 1F + 10E0-C7 readings @V10 | m3 | 27 JOINT_HEAD rows UNRESOLVED -> RD, -5.16375 (2.03375 + 0.46 + 2.075 + 0.595 = the T-599 alternative readings); reported apart, never in the class shift of record; T-572 measured-column joint rows audited beside (not in the section of record) | unchanged (PV) |
| T-599 r2 | joint_rule_v10 | - | pointer restated MERGED (LEAD_ADOPTED under Q-62 A, not owner-approved); the V9 REJECTED pointer kept byte-equal in V9 | - |
| T-607 | T-584/stair-steps-lm@V10 / -nr@V10; T-598/nosing@V10 beside | lm / nr | ST-01 7 pieces beyond the 56 governing risers 8.4 lm / 7 nr UNRESOLVED -> ENGINE_RIGHT (C-T607-1, no drawn piece); the nosing beside UNRESOLVED 8.4 -> ENGINE_RIGHT (11.02856 with the 2.62856), the same cause once per line, 16.8 lm / 14 nr summing refused | PV (ST recount own; 56 census reused) |
| T-612 | T-574/skirting-room@V10 | lm | GF open room UNRESOLVED +16.913904 = -0.10 ENGINE_RIGHT (face vs outline, virtual edges) + 17.013904 UNRESOLVED (undrawn split 3.056952 .. 8.506952 CANDIDATE, never a reading); section UNRESOLVED 18.293234 -> 18.393234 | V / PV |
| T-605 | beside (T-551/footing-line predates the evidence stamps) | m3 / m2 | FN notch 0.042 m3 ENGINE_RIGHT row unchanged; pair concrete 5.307 = own, his 5.349; blinding union 129.234375 m2; side forms 7.46 .. 7.685 m2 HELD (OQ10) | pair 2 / 2 VERIFIED, line PARTIAL |
| T-610 | packs beside (P03 GF) | m3 | F-C-P03-2 restated: billed ONCE (UNDER), FR-T610-1 -0.005957 .. -0.007252 m3 PARTIAL, FR-T610-2..4 worker; not applied | - |
| T-611 | F-T606-1 beside | lm | FR-T606-1 in manifest V13: FIN.SKIRTING 209.728592 -> 198.558592; candidate V3.0.58 unchanged, so still not applied | V (4 / 4) |

Class moves of record in V10: lm UNRESOLVED -> ENGINE_RIGHT n 3 (-8.40, -0.10, +8.40), -> ENGINE_WRONG n 2 (+2.50,
-0.20); m3 UNRESOLVED -> RULE_DIFFERENCE n 4 (signed 0, gross 5.3325); nr UNRESOLVED -> ENGINE_RIGHT n 1 (7). No total
moves; nothing released. Still pending: T-600 residuals; FR-T606-1 / FR-T610-n wiring; P02 GF and the 1F CB10-12 read
(F-C-P02-3 not yet a merged task); T-608 (READY at the r2 claim).

## Findings

- F-T609-1: the -0.20 lm LIV-VOID part carries the merged ENGINE_WRONG class, but the Checker's F-T606-1 re-measure
  says column 3008's east return (0.05 lm) faces the 1F floor and keeps skirting; the split stays as merged (R-T609-1
  (a)); the fix row for F-T606-1 should restate it (0.15 ENGINE_WRONG + 0.05 ENGINE_RIGHT) when it is wired.
- F-T609-2: when FR-T602-1 is wired, the G-01 step enters as a HELD line at its point bound 2.500 lm (stone unprinted,
  like D-GF-01 / 03 / 09), so the next statement moves the 2.50 from ENGINE_WRONG to HELD, never to a valued line.
- F-T609-3: when F-T606-1 is wired the engine column falls 11.170 lm and his gross along the opening edges (no floor)
  becomes a new ENGINE_RIGHT row to name; the statement does not anticipate it.

- F-T609-4 (r2): `A8.restate` compares totals as strings and V9 printed T-551/columns@V9 'difference' unnormalised
  ('8.77' for 8.7700); r2 compares on the normalised value and keeps V9's text (value checked equal). A later statement
  should normalise once, in a new version, never by editing V9.
- F-T609-5 (r2): the nested T-576 GF / 1F sets carry the % printed in V7 (-10.18 / -21.74) through V9 into V10; a
  restatement prints no new %, so they stay; the scorecard (T-613) should not read a % from a nested set.

## Lesson row proposal (ERS s.7)

| 2026-11-07 | a statement restated merged splits and Checker pack readings on the same rows | a pack could be read as
promoting a class, and a merged split re-cut by the integrator | a merged split enters as merged (class from its
verdict, sign converted and checked); a pack moves evidence only, on a row it covered in full with every mark AGREE and
the marks re-adding to the row; pending fixes stay beside | R-T609-1 (a)-(e) (every villa) | tests/t609_statement_v10 |
PROPOSED |

r2: | 2026-11-07 | a merged rule explains part of a paired difference across sections of record, nested sets and
alternative readings | the matched part promoted with the remainder, or nested moves counted in the record shift | the
rule's matched magnitude alone moves class; the remainder stays its own residual; every joint row must carry the rule's
record; nested / alternative moves are reported apart; the of-record moves must re-add to the rule's own headline |
R-T609-1 (f) (every villa) | tests/t609_statement_v10 | PROPOSED |
