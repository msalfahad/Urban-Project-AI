---
name: urban-boq-proof
description: Prove an Urban BOQ quantity end to end with the verification chain (owner rule -> source drawing -> geometric interpretation -> formula -> independent expected result -> engine result -> difference -> pass/fail -> BOQ impact), with the expected value never taken from the implementation under test.
---

# Urban BOQ proof

## Purpose
Show that a quantity (floor, wall, skirting, waterproofing, doors, thresholds, membrane rolls) is right, and why, so
that a reviewer can check every step without trusting the engine.

## Trigger
A new or changed measurement method; a disputed BOQ line; an owner asks "where does this number come from"; any
test that compares the engine with an expected value.

## Inputs
- the owner / project rule (registry `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json`, `rules/`, the project rules
  sheet) with its id and version
- the source drawing (synthetic for shareable proofs; private drawings only in the private work area)
- the engine's output for that quantity

## Tools
- hand derivation written as typed literals (no computation from the engine), e.g. `tests/m9_p2b5/install_cases.py`
- an independent reference calculator that imports only the standard library (and other independent references),
  e.g. `tests/m9_p2b3/proof_reference.py`, `tests/m9_p2b4/construct_reference.py`, `tests/m9_p2b5/install_reference.py`
- one adapter that is the only module reaching the engine, e.g. `tests/m9_p2b5/install_engine.py`
- the chain generator, e.g. `python3 -s research/urban_m9_p2b5/make_p2b5.py` (WORKED_EXAMPLES.md, VERIFICATION_CHAIN.csv)

## Safety
- The expected value never comes from the implementation being tested; never edit an expected value to make a test
  pass - find the cause, and record it if the engine is right and the hand derivation was wrong.
- No arbitrary waste percentage: waste is the sum of classed offcuts (or the rule's own value, cited).
- Frozen methods (V1 - V2.6 as published) are not changed to pass a proof; corrections go to a new opt-in method.

## Outputs
Per quantity the chain row: rule id, source, interpretation, formula, expected, engine, difference, PASS / FAIL,
BOQ impact; a markdown page and a CSV.

## Tests
`tests/m9_p2b5/test_p2b5_independence.py` (imports and literals), `tests/m9_p2b5/test_p2b5_examples.py`,
`tests/m9_p2b3/` proof tests.

## Escalation
A rule that is ambiguous for the case at hand goes to `urban-rule-reconciliation`; a missing project value (heights,
product data) is an RFI, never an assumption written into the expected value.
