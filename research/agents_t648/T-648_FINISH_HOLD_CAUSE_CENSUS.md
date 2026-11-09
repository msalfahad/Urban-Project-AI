# T-648 finishes HELD lines with no committed cause -> one named cause each (lane A, research, unwired)

Worker 2, 2026-11-09. Development villa trial BOQ T-636 (candidate V3.0.58 + manifest V17), finding F-T636-1. Nothing is
wired or released; V2.9 + route G unchanged; no rule / knowledge version file touched. ERS s.2 / s.3 / s.7 applied.

## Scope and result

198 lines = F-T636-1 finishes share B3 65, B8 48, B7 44, B6 14, B4 10, B2 2 (183) + the 15 B13 lines T-646 did not class
(fence block / wall / gate / top / count / below N.G., outdoor floor 2, pool water face, RL-10 guard). HELD lines with no
committed cause per trade and unit: before 198, after 0 (table in out/FINISH_HOLD_CAUSE_CENSUS_T648.md).

| Class | Lines | Main sources |
|---|---|---|
| OWNER_DECISION (answered) | 72 | Q-45 bed band 44 (re-computed area x band), Q-35 C doorway transition 14, Q-21 C / Q-31 C foundation WP 6, Q-63 C sea side 4, Q-65 C, Q-34, Q-50 / Q-51, UP-CER-001 |
| DESIGNER_ITEM (D-nn) | 63 | D-62 penetrations 17 + pool face, D-45 opening heights 11, D-10 7, D-54 6, D-53 4, D-07 4, D-43 4, D-16 2, D-40 2, D-48 2, D-01, D-35, D-67 |
| PRINTED_VALUE_GAP | 34 | stair formwork faces (T-352 / T-332 face basis) 10, stair marble exposure 5, lift surround 3 (landing door height), membrane edges 3, fence 6, foundation WP 2, stair concrete 3, skirting 3 |
| OWNER_OPEN (named, open) | 14 | ORR-007 stair skirting form 12, OD-1 outdoor floor 2 |
| DEPENDENCY (held line id) | 9 | 8 stair formwork lines on 5 HELD stair concrete lines; OP-020 strip on L-c57860d7 |
| ENGINE_DEFECT | 6 | 5 unattributed strips (T-325: wall bodies, not thresholds; D-V26-07), 1 'termination other' (T-303 finding 5) |
| CHECKER_DOWNGRADE | 0 | none of these 198 lines carries a downgrade record |

Fix row (DRAWING-CONFIRMED, not wired): L-868aee12 ARCH.THRESHOLD A-GF-01 (OP-027, floor continues, UP-THR-001)
1.000 x 0.150 = **0.150 m2**; the merged T-340 FILL row states the same value but no overlay ever carried it (blank in the
trial BOQ). No other line has every term printed: the exterior sill areas are printed but their finish is not (D-10).

## What I learned / for the Lead

- 195 of the 198 causes were already in merged ledgers (T-336, T-347, T-332, T-325 / T-340, T-500, T-508, T-232, T-400,
  T-474 / T-352) that T-636's cause reader does not read; the census pins and cites them by line id (the 3 shutter lines cite the designer register D-54 only). Proposal: T-649 adds
  this census (and the merged T-340 FILL row) to the overlay reader so F-T636-1 shrinks by 198.
- Two classes outside the row's five are used and labelled: OWNER_OPEN (ORR-007, OD-1 are open owner items, not answered
  decisions) and ENGINE_DEFECT (lines that are not physical pieces of their family). The Lead rules whether they stay.
- Engine vs freelancer: no quantity moves except the 0.150 m2 fix row (his threshold rows: none, T-325); no verdict
  changes. Verdict proposal for L-868aee12: ENGINE_WRONG (blank line, printed terms), fix 0.150 m2.

Lessons-register row (proposed, ERS s.7): 2026-11-09 | 198 finishes HELD lines showed 'no committed cause' in the trial
BOQ although 195 causes sat in merged ledgers | the trial reader reads a fixed source list, ledgers keyed by line id were
never joined | every HELD line's cause is joined by line id from every merged ledger, one class each, a freelancer figure
never a cause (every villa) | tests/t648 (normal: band, fix row; adverse: mid value, cm as m, unprinted term, freelancer
cause, held as 0, self / non-held dependency, line classed twice) | PROPOSED.
