# T-590 RULE_DIFF provenance audit, structural (B10 concrete, B11 reinforcement, B1 earthworks)

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-07, branch `agents/task-T-590`. Research only: no engine
module, candidate line, released line, rule / knowledge / registry file or method version changed; nothing released;
no quantity moves (a reclass is a statement label; every delta keeps its value, never 0). Development villa, not an
accuracy claim. ERS s.2 - 4 and s.7; R-T591-1 (merged, imported read only).

## 0. Inputs

- Statement V7 (`research/agents_t587/out/RECONCILED_STATEMENT_T587.json`, sha256 3cd55327, V6 byte-equal inside it):
  every section whose trade starts B10 / B11 / B1; the architectural sections are T-591's.
- Registers: docs/RULES_INDEX.md (live), company rulebook 1.0.0, URBAN_OWNER_METHOD_RULES.json, method register V3
  (pinned), family master 1.55.0; owner questions index agents/control @344858ff (answered Q-01..Q-78, open Q-80,
  withdrawn Q-79: unchanged since T-591).
- His side: own read this run of Drive 'Alsenan chalet project', the concrete + rebar workbook (sha256 ae608411 =
  T-560 / T-576 manifest), in `.work/private` only. Only sheet roles, row numbers, heights and typed figures already
  printed in merged reports are written here.
- Code: `t590_rules.py` (R-T590-1), `t590_alsenan.py` -> `out/T590_RULE_DIFF_PROVENANCE.json / .md`;
  tests `tests/t590` (11), with `tests/t591_rule_diff_provenance` 43 passed together.

## 1. The physical elements and the question

Each structural RULE_DIFFERENCE row refers to one of three things: (a) the cast COLUMN-BEAM JOINT volume (column
JOINT_HEAD rows: T-551, T-572, T-576; beam THROUGH_SUPPORT rows: T-545 / T-545@V7); (b) the installed bar population
of a reinforcement family group (T-560 G1..G6, t); (c) earthworks (B1). For each: which recorded Urban rule chooses OUR
convention, and what convention HIS own figures show.

## 2. Findings

**Column-beam joint (m3).** His figures: GF column rows 36-47 all 3.75 m = storey 4.50 (+0.95 -> +5.45) - 0.75; 1F rows
52-61 and 2F rows 66-71 all 3.45 = 4.20 - 0.75: clear height to a 0.75 beam soffit; his beam rows at full depth with
lengths through the supports (T-545). So his convention = BEAM owns the joint. Ours (V3.0.58 lines, R-T394-1): COLUMN
slab top to slab top, beams face to face = COLUMN owns the joint.
Our recorded sources for that choice: owner Q-62 (OWNER_DIRECTIVE_2026-10-20) requires 'the same concrete measured once
... under the chosen convention ... one convention for the whole project' but does not choose the owner (REQUIREMENT
only); R-CONC-OWN-1 (T-189) states column > beam but is 1.0.0-PROPOSED, 'not in force', in no rule register; the ERS
s.7 lessons row 2026-10-31 (Lead) says column owns; the ELEMENT_REGISTER entry 'COLUMN-BEAM JOINT' (Lead 2026-11-06
20:14, 'restates T-189 / R-CONC-OWN-1') says the BEAM owns the joint and the column runs floor-to-soffit = HIS
convention, opposite to the engine and to the rule it cites. Under R-T591-1 (b) worker / Lead records alone are not a
rule: outcome NONE -> UNRESOLVED, flagged CONVENTION_RECORD_CONFLICT.
Also: the pair does not cancel per storey (reference - engine: GF -0.620464, 1F -1.208362, 2F -0.532760 m3, T-551
beside): even with one rule only the matched part of each pair is a convention.

**Reinforcement (t).** Our side IS sourced: URBAN-REBAR-NET-AND-PROCUREMENT@v1 (method register V3, owner decision
OD-V3-3), Q-71, OWNER_RULE_REBAR_2026-10-24 s.1 (tons); the rows cite none (SOURCED_RECITE on our side). His side: the
summary sheet H17..H23 are typed constants 5.8 / 9.75 / 7.95 / 9.89 / 5.4 / 3.9 / 1.5 = 44.19 t, no formula, no bar row
on any of 8 sheets: no convention is readable. A RULE_DIFFERENCE needs two conventions; outcome HIS_SIDE_UNREADABLE ->
UNRESOLVED (T-560's own source_class already says 'quantity UNRESOLVED'). G2 / G5 also contain CONFIRMED engine
omissions (lift-pit walls, domes) and every group carries HELD-blank lines.

**Earthworks.** 0 RULE_DIFFERENCE rows: T-565/earthworks is NOT_COMPARABLE (his NO_ROW, Checker CONFIRMED); T-572
held-bounds carries families only.

## 3. Acceptance figures

| | rows | m3 signed (gross) | t signed |
|---|---|---|---|
| RULE_DIFF rows audited (all levels) | 44 | | |
| headline (live, reading of record, not nested) | 12 | | |
| with a recorded source on our side (headline) | 6 (rebar; his side unreadable) | | 34.814694 |
| without (NONE -> UNRESOLVED, headline) | 6 (4 beam + 2 column) | +2.369278 (7.701778) | |
| reclassed to UNRESOLVED (headline) | 12 | +2.369278 | 34.814694 |
| SOURCED / SOURCED_RECITE kept as RULE_DIFFERENCE | 0 | 0 | 0 |

Nested (T-576 measured set inside T-551/columns, 13 rows, -2.49375 m3), superseded (T-545/beams, T-572 columns, 5 rows)
and conflict-reading rows (14) are audited with the same outcome and never added to the headline. Every section's
difference is unchanged; RULE_DIFFERENCE after the reclass = 0 in every structural section.

## 4. Verdict proposals and what is open

- Not ENGINE_WRONG and not FREELANCER_RIGHT: both conventions measure the joint once where they are consistent; the
  class question is provenance only. UNRESOLVED until the Lead adopts one ownership as a rule version (Q-62 delegates
  the choice to the project: ERS s.2.7 not met, no owner question) and corrects the 2026-11-06 ELEMENT_REGISTER entry;
  then the 38 column / beam rows return to RULE_DIFFERENCE SOURCED by that rule.
- B11: stays UNRESOLVED while the reference is a typed lump; the engine's bars are checked against the drawings.
- engine/source/arch_v3012.py:84 lists R-CONC-OWN-1 under 'owner_rules' (a proposed worker rule): relabel in the next
  method version that touches it (frozen: never in place).

## 5. Lessons-register row proposed (ERS s.7)

| 2026-11-07 | The column-beam joint was carried as RULE_DIFFERENCE (beams +5.036, columns -2.666 m3) while no rule register
holds the ownership choice and two Lead records state opposite owners (T-590) | an owner REQUIREMENT ('once, one
convention', Q-62) read as if it chose the convention | a convention choice is sourced only by an adopted rule version;
a requirement-only owner answer is listed as a requirement; opposite records on the same junction = CONVENTION_RECORD_
CONFLICT, row UNRESOLVED; a typed-lump reference has no readable convention; every villa, every trade |
tests/t590 | PROPOSED |
