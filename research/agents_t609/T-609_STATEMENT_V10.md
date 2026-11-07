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

Not merged at the claim, so not taken: T-599 r2 (READY), T-600, T-605 (TODO), T-607 (READY).

## Findings

- F-T609-1: the -0.20 lm LIV-VOID part carries the merged ENGINE_WRONG class, but the Checker's F-T606-1 re-measure
  says column 3008's east return (0.05 lm) faces the 1F floor and keeps skirting; the split stays as merged (R-T609-1
  (a)); the fix row for F-T606-1 should restate it (0.15 ENGINE_WRONG + 0.05 ENGINE_RIGHT) when it is wired.
- F-T609-2: when FR-T602-1 is wired, the G-01 step enters as a HELD line at its point bound 2.500 lm (stone unprinted,
  like D-GF-01 / 03 / 09), so the next statement moves the 2.50 from ENGINE_WRONG to HELD, never to a valued line.
- F-T609-3: when F-T606-1 is wired the engine column falls 11.170 lm and his gross along the opening edges (no floor)
  becomes a new ENGINE_RIGHT row to name; the statement does not anticipate it.

## Lesson row proposal (ERS s.7)

| 2026-11-07 | a statement restated merged splits and Checker pack readings on the same rows | a pack could be read as
promoting a class, and a merged split re-cut by the integrator | a merged split enters as merged (class from its
verdict, sign converted and checked); a pack moves evidence only, on a row it covered in full with every mark AGREE and
the marks re-adding to the row; pending fixes stay beside | R-T609-1 (a)-(e) (every villa) | tests/t609_statement_v10 |
PROPOSED |
