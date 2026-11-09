# T-591 RULE_DIFF provenance audit, architectural and finishes (statement V6, with the V7 finishes additions)

Worker 2, 2026-11-07, lane A, non-candidate, backlog-permitted. Files: `t591_rules.py` (R-T591-1), `t591_alsenan.py`
-> `out/T591_RULE_DIFF_PROVENANCE.json` / `.md` (`--check` rebuilds identical), `tests/t591_rule_diff_provenance/`.
Input: the committed statement V7 JSON (T-587; V6 carried byte-equal inside it; sha256-pinned), the repository rule
registers (docs/RULES_INDEX.md, company rulebook 1.0.0, owner method rules, BOQ family master 1.55.0) and the board's
answered-question index (snapshot in `t591_rules.py`). No drawing, workbook or client data; no candidate, rule, knowledge,
registry or frozen file changed; no quantity moves; nothing released. Structural sections (B1 / B10 / B11) are T-590's.

## 1. Physical question and method (ERS s.3)

A RULE_DIFFERENCE row claims: same element, both measured, the gap is a convention. That is a finding only when OUR
convention is a recorded Urban rule; otherwise it is an assumption. For every finishes RULE_DIFFERENCE row: (1) the rule
ids its own text cites; (2) the source that actually governs the cause, traced in the registers (rule text read, not the
title); (3) his convention, from his own figures as the row and its source report record them; (4) outcome SOURCED /
SOURCED_RECITE / NONE (-> UNRESOLVED, delta unchanged, never 0).

## 2. Result (117 live rows + 2 superseded V6 rows audited beside; units apart, no %)

| Unit | SOURCED as cited | SOURCED, citation to correct | NONE -> UNRESOLVED |
|---|---|---|---|
| m2 | 34 rows, signed +13.166962, gross 215.486862 | 46 rows, +390.715292, gross 421.051290 | 0 |
| lm | 6 rows, -15.029396, gross 40.541396 | 21 rows, +38.82, gross 57.02 | 1 row, +0.30 |
| nr | 0 | 9 rows, +95, gross 115 | 0 |

Every section's difference is unchanged; only T-574/skirting-room moves 0.30 lm RULE_DIFFERENCE -> UNRESOLVED
(43.62 -> 43.32; UNRESOLVED 9.693234 -> 9.993234).

## 3. Findings

- **F-T591-1 (NONE, candidate ENGINE_WRONG, Checker to read the arch):** T-574 skirting row 29, 1F bed room 2 dressing
  arch: his outline adds the two 0.15 m jamb returns (0.30 lm). Our row rests on R-T443-1 'door jambs never' and
  t574_rules.jamb_return refuses 'door / arch' jambs citing UP-SKIRT-001. The owner method says the opposite for a
  DOORLESS opening: URBAN-SKIRTING-OPENING-METHOD DOORLESS_OPENING real_floor_side_jambs INCLUDED (no door, real jamb,
  eligible side, floor reaches it, not a full-tile room); UP-SKIRT-001 1.4.0 'doorless_opening_jambs: included'. Only
  door jambs are excluded (DOOR_PRESENT jamb_skirting NONE). So the row has no rule on our side: UNRESOLVED 0.30 lm.
  Wider effect (no number here): the same refusal applies to every doorless opening in the skirting table (open
  passages OP-003 / OP-011, 1F OP-007, the dewaneya arch OP-027, the dressing arches); the candidate has one HELD jamb
  line (SKIRT-T443 OP-020 jambs) and no valued one. Condition check from the committed drawing-derived records (T-175
  opening hosts, T-296 skirting deductions; table in out/*.md): A-1F-01 (1F OP-011, the bed room 2 / dressing arch,
  masonry 0.15, no door, both sides dry, porcelain continues) meets every condition -> 2 x 0.15 = 0.30 lm, exactly his
  figure: verdict proposal ENGINE_WRONG 0.30 lm. A-GF-01 (dewaneya / wet wash) NOT_APPLICABLE (marble threshold at the
  jambs); GF OP-020 already a HELD line (0.40); GF OP-003 an open side, not an opening; GF OP-011 and 1F OP-007 have no
  host record: jamb depth HELD by name. Fix row proposed for the Lead: value the A-1F-01 jambs in a candidate package
  and read GF OP-011 / 1F OP-007 from the plan.
- **F-T591-2 (citation):** 8 plaster / paint opening-deduction rows (T-552 rows 5 / 11 / 14 / 26, T-561 rows 5 / 11 /
  14 / 26; +42.30195 m2 each section) cite Q-73 'full'. Q-73 (UPC-BLOCK-OPENINGS-001) governs blockwork. The finish
  deduction rests on UP-OPEN-SCHED-001 (the opening's own length x its band, OWNER_APPROVED) under UP-GEN-003. His side
  (half of his opening list) is a freelancer practice by the owner's own Sigma note item 1. Numbers stand; cite again.
- **F-T591-3 (citation):** T-541 dome footprints (+15.274758 +30.718026 m2) cite Q-29 'skylight'. Since 2026-10-22 that
  reading is scenario S1 only (approved design keeps the concrete domes). Q-24 (membrane stops at the dome base, 0.20 m
  upturn round it) gives the same deduction in both scenarios: re-cite Q-24.
- **F-T591-4 (class questioned, no reclass here):** T-534 MS1-LD 0.0625 m2 is a size difference (his 1.20 x 1.25 vs
  drawn 1.25 x 1.15), not a convention; T-577 DRY strips (-1.250 m2 / -7.7 lm / -10 nr) face his NO_ROW (R-T586-1 (a));
  boundary wall +74.4 m2 and pool soffit +12.834 m2 are placements in another family, not conventions.
- 76 rows cite no rule or only a method record (T-296 table, R-T559-1, R-T443-1 ...): each now names its rule in the
  JSON (`our_side`). Door heads rest on Q-55 (2.20 m ASSUMED fallback, OWNER-APPROVED; 'never his 2.40 without
  evidence'); blockwork heights on Q-60 (UP-MAS-HEIGHT-001 REQUIRES_CONFIRMATION beside); skirting on UP-CER-003 +
  URBAN-SKIRTING-OPENING-METHOD; stair pieces on UP-STAIR-004; lintel reads on UPC-LINTEL-001.

No owner question: the one gap is answered by the owner's own method record (ERS s.2.7 not met).

## 4. Rule, tests, lesson

- R-T591-1 (every villa; `t591_rules.py` docstring): accepted sources (RULES_INDEX rule not DEPRECATED, rulebook UPC,
  owner method URBAN-*, answered binding Q-, owner rule file + item, family code for placement only); refused: unknown
  id, deprecated, open / withdrawn / non-rule answers, scenario-only answers; method records and Lead register rulings
  never count alone; REQUIRES_CONFIRMATION labelled provisional; NONE -> UNRESOLVED with its delta; no %.
- tests/t591_rule_diff_provenance (32): K591 hand villa (door SOURCED, arch jambs NONE, closure 1.22 lm), adverse:
  Q-80 open, Q-79 withdrawn, Q-34 / Q-23 not a rule, unknown id, deprecated rule, method record / register / Q-29 alone,
  wrong-trade citation, empty his side, non-RD row, unit outside the list; training villa: rebuild identical, 119 / 117
  rows, one NONE, sections close, Q-73 never accepted for plaster / paint, pin drift refused, the doorless
  jamb check (0.30 = 2 x 0.15; unknown depth HELD, never 0).
- Lesson row proposed (ERS s.7): | 2026-11-07 | an arch's jamb returns were refused as 'door jambs' and a blockwork
  answer was cited for plaster / paint deductions | a RULE_DIFFERENCE was labelled from a worker method record, not
  from the owner rule text | every RULE_DIFFERENCE names the governing rule id read in its text, for that trade and
  that opening class (door vs doorless); a row with none is UNRESOLVED | R-T591-1 | tests/t591_rule_diff_provenance |
  PROPOSED |

## 5. Rebuild

`python3 -I research/agents_t591/t591_alsenan.py --check` (identical); the V7 JSON, rulebook 1.0.0 and family master
1.55.0, the T-175 hosts and T-296 deductions are sha256-pinned; RULES_INDEX and the owner method rules are read live (a removed or deprecated rule shows in the
rebuild test).
