# T-594 reconciled-quantities statement V8 (research, unwired; for the 12-13 Nov milestone)

Worker 3 (lane I, non-candidate), 2026-11-07. Files: `t594_adapters.py` (R-T594-1), `t594_build.py` ->
`out/RECONCILED_STATEMENT_T594.json` / `.md` (`--check` rebuilds identical), `tests/t594_statement_v8/` (16). The T-587
builder is imported read only; the build first rebuilds V7 and refuses to run unless it equals its committed JSON and
markdown, then checks every V7 key is carried byte-equal (lists extended as a prefix only). Sources sha256-pinned (T-581,
T-585, T-589, T-592, T-593 V10, T-595, T-577 outputs). No drawing, workbook or client data; no candidate, rule,
knowledge or registry file; no quantity moves; nothing released (V3.0.58 not released; V2.9 + route G unchanged).

## Restated sections (totals unchanged, residual 0, no %; evidence per row from the Checker verdict)

| Section (restates) | Unit | Ref / engine | Moved rows | Evidence |
|---|---|---|---|---|
| T-571 lintels@V8 (V6) | nr | 54 / 60 | D-GF-09 RULE_DIFFERENCE -> UNRESOLVED (DRAWING CONFLICT 0.90 masonry vs D120 1.00; 1.20 .. 1.50 piece), delta 0 nr; lm beside 91.5 -> **91.5 .. 91.8** (AT_MOST not an upper bound) | V (T-581 own read) |
| T-574 yard skirting@V8 (V6) | lm | 81.32 / 0 | 81.32 UNRESOLVED -> **RULE_DIFFERENCE (FREELANCER_SCOPE)**: his paving perimeter, no printed base; wall foot 59.582 NOT_IN_DRAWING, porch / pool court 0 .. 11.61 UNRESOLVED beside | PV |
| T-574 stair skirting@V8 (V6) | lm | 29.87 / 12.15 | MS1-T winders UNRESOLVED -> HELD +2.350 (2.350 .. 2.620191); ST-01 residual -0.038505 -> -2.388505; HELD 17.009049 -> **19.359049** (= T-585 flight low); E1 note: landing 3.500 NOT_IN_DRAWING (register) | PV |
| T-577 marble lm@V8 (V7) | lm | 21.7 / 56.83 | his door steps +7.70 UNRESOLVED -> HELD 2.800 (D-GF-01/03/09 strips = steps) + HELD 1.000 gate (PARTIAL) + PAIRED 1.000 (D-GF-05 = its valued WET strip, out of WET ENGINE_RIGHT -11.5 -> -10.5) + **UNRESOLVED 2.900** (his 6 pieces, no door id) | V / PV |

Beside (valued 0): T-589 closure classes B10 59 = 10 V / 30 CLOSABLE / 19 DESIGNER, B11 13 = 1 / 12, B1 19 = 1 / 15 / 3
OWNER GAP; T-595 ring side bars both faces: dome rows at least 0.767783 -> 0.789555 t (Checker 0.789554 from rounded
parts), G5 held at least 1.806943 -> 1.828715 t, residual vs his TYPED_LUMP at most 2.093057 -> 2.071285 t; F10 + F S02
2.176 .. 2.275 -> 1.960 .. 2.275 m3, footing bounded low 7.8445 -> 7.6285 m3, his 1.960 BELOW -> WITHIN.

## R-T594-1 (proposed, every villa; module docstring)

(a) split, never edit: parts re-add to the earlier row exactly, totals unchanged; (b) PAIRED parts (one element on our
side in another group) leave the rows as an agree pair and must net 0; (c) amend = same delta (class / name / bound / note
only), HELD never 0 without a bound; (d) earlier section byte-equal and superseded; (e) beside restatements state before
/ after, valued 0.

## Findings

- F-T594-1: the T-577 group split (WET / DRY / EXT) put D-GF-05's strip in WET (valued) and D-GF-15's in DRY (HELD), while
  the register now makes both door / gate STEP elements: V8 pairs D-GF-05 once (net 0) and moves D-GF-15 to the EXT gate
  row; marble nr is unchanged (his 6 nr vs our 5 elements stays beside).
- F-T594-2: the engine marble lm valued 56.83 already carries D-GF-05 (1.000); the house step total 3.800 lm is therefore
  1.000 valued + 2.800 HELD in the candidate today, not 3.800 missing.

Lesson row proposal (ERS s.7): | 2026-11-07 | a ruling that two line families are one element left a reference block
compared against one group while its counterpart was valued in another | restate by splitting rows and pairing the
cross-group part (net 0), never by editing a total | R-T594-1 (a) / (b) (every villa) | tests/t594_statement_v8 | PROPOSED |
