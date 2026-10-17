# Task board (Lead writes; workers claim one row; verifier records the verdict)

Status: TODO -> CLAIMED (worker, branch) -> READY (worker done) -> MERGED or REJECTED (verifier, reason).

| Id | Priority | Trade | Task | Status | Branch | Verdict |
|---|---|---|---|---|---|---|
| T-001 | 1 | scoreboard | Build `tools/alsenan_scoreboard.py`: engine vs freelancer per trade from the private data repo; write SCOREBOARD.md | TODO | | |

## Ideas (from the research scout; the lead turns useful ones into tasks)

From the 2026-10-17 BOQ engines study, which the owner supplied (see RESEARCH_LOG.md and research/2026-10-17_BOQ_ENGINES_STUDY.md). Ranked for the Alsenan scoreboard:

1. Visible deduction rows per wall (`D1 2 x 1.0 x 2.1 = -4.20 m2`, tied to the DXF block): makes blockwork and plaster gaps explainable.
2. Measured, waste-adjusted and order quantity as three columns: shows whether a gap comes from measurement, the waste rule or rounding.
3. Net, gross and centreline variants per room or wall, side by side, matching whichever basis the freelancer used.
4. Recipes per unit (block wall per m2 expands to blocks, glue, lintels, plaster and labour) in one rule source.
5. Provenance on every quantity: file, layer, entity handle, rule version, reviewed.
6. Overlap check: shared floor = sum - union must be 0.
7. Three-band confidence: commit, withhold with location (an owner question), or reject.
8. Skirting = perimeter minus stated door widths, with the inputs recorded.
9. DXF revision diff that flags affected BOQ lines (needed for the second villa).
