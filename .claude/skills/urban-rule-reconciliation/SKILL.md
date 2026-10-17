---
name: urban-rule-reconciliation
description: Reconcile the owner and project rules that govern a quantity (knowledge registry 1.1.0, rules/ 1.5.0, the owner rule library, the project rules sheet, project facts) by the source-authority precedence, record every conflict with its provenance class, and turn real conflicts into owner questions instead of silent choices.
---

# Urban rule reconciliation

## Purpose
Make every quantity traceable to the rule that governs it, and make every conflict between rules visible.

## Trigger
Two rules give different answers for one surface (for example a wet room's skirting: UP-CER-004's exception keeps
skirting when the wall tile is not full height, while the owner's program says no skirting in wet rooms); a project
value overrides an owner standard; a synthetic test value appears where a project value is needed.

## Inputs
- the registry `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json` (rules, `precedence_rule`, `conflicts`),
  `rules/owner_decisions/URBAN_RULES_1.5.0.json`, `rules/owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json`
- the run's `PROJECT_RULES_SHEET.json` and `RUN_RULES.json`, the facts file used (heights)

## Tools
- read the rule records (`rule_id`, `logic`, `scope`, `exceptions`, `status`) with a short script
  (`python3 -I -c "import json; ..."`) - never edit `rules/`
- precedence: UP-KB-PREC-001 (source authority hierarchy); UP-RULES-001 (level A master standards, level B project
  rules within their scope); UP-DOOR-HGT-001's order for heights (schedule, section, elevation, dimension, project
  fallback, owner reference)
- provenance classes for each value: CAD_MEASURED, PROJECT_SPECIFIED, OWNER_STANDARD, ASSUMED, PROPOSED_MODIFICATION,
  UNRESOLVED_CONFLICT

## Safety
- Never resolve an owner decision silently and never change `rules/` or the registry to remove a conflict.
- A project override applies only within its scope; outside it the owner standard stands.
- A synthetic test value (the facts file used by Mode A) is never presented as a project value.
- A frozen historical result is never rewritten to clear a conflict; a changed rule reading goes into a new opt-in
  method version. A project rules sheet that names a client or a site stays private; a public conflict record cites
  rule ids and aggregate quantities only.

## Outputs
A conflict record per case: the rules involved (id, version, status), what each says, the precedence result, the
provenance class of the value used, the BOQ impact, and - for a genuine conflict - an owner question with its options.

## Tests
`tests/m9_p2b2/` rule-precedence tests, `tests/m9_foundation/` rule-store tests, and the Phase 2B-5 Stage C
register (`research/urban_m9_p2b5/REAL_ROOM_VERIFICATION.md`, D-C4 / D-C5).

## Escalation
Every UNRESOLVED_CONFLICT goes to the owner as one question with the alternatives and their quantities.
