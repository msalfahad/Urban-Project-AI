---
name: urban-freeze-integrity
description: Verify that frozen Urban outputs and published measurement methods (ARCH_TAKEOFF_V1 ... V2.6) are unchanged after any code change - freeze verifier, import closures, byte-for-byte snapshot comparison of every earlier method on the benchmark drawings - and keep new behaviour in opt-in methods.
---

# Urban freeze integrity

## Purpose
Guarantee that published results do not move: a change may add a method or an output, never alter what an earlier
method produces.

## Trigger
Before any commit that touches `engine/`, `tools/` or `rules/`; when a new method version is added; when a
regression is suspected.

## Inputs
- the change (git diff), the freeze index `research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl`
- a baseline snapshot of every method's outputs taken at the commit before the change

## Tools
1. `python3 -I tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl`
   -> "frozen artefacts differing from the index: 0"
2. `python3 -I tools/freeze_verify.py closure` -> no changed file inside a freeze manifest's functional closure
3. snapshot: run every method (V1 ... latest) on the benchmark drawings (synthetic villa, its mirror, and the private
   reference plan in the private area only), Mode U and Mode A, before and after the change, then `diff -rq` the two
   trees: every earlier method must be byte-identical; the new method compared field by field
4. determinism: the new method twice, byte-identical
5. the full test suite, with new failures reported separately from the baseline's known failures

## Safety
- Never rewrite a frozen result, an expected value or a historical source drawing to make a check pass.
- Do not edit `opening_census.py` or historical drawings; new behaviour goes into an opt-in method
  (`ARCH_TAKEOFF_V2.x`) behind its own keys.
- Snapshots of the private plan stay in the private work area.

## Outputs
A table: method, files compared, files that differ (must be 0 for every earlier method); the freeze verifier and
closure results; the test-suite delta.

## Tests
`tests/m9_p2b5/test_p2b5_trace.py::test_the_trace_changes_nothing_of_the_v25_layout`,
`tests/m9_p2b5/test_p2b5_cli.py::test_v2_6_keeps_every_boq_line`, the freeze-integrity tests under `tests/`.

## Escalation
A required change to a frozen method (a confirmed defect) is an owner decision: it is proposed as a new opt-in
method with a written patch proposal, never applied in place.
