# Adversarial probe of the existing check modules (owner request 2026-10-23 19:00)

Written by the owner's main chat (auditor). Synthetic data only; nothing in the engine, the released V2.9 path or a
sealed benchmark was changed or read. Script: `dashboard/adversarial_probe_2026-10-23.py` (run on Python 3.11 against
working head 17ed6f92). Each FAIL is a gap the named task must close with an adverse test that is refused or flagged.
Existing check folders on 17ed6f92 (t134, t156, t165, t177, t182, t188, t195, t196, scoreboard): 197 tests, all pass.

| # | Injected fault | Expected | Actual today | Result | Owner of the fix |
|---|---|---|---|---|---|
| 1 | drawn element in the register, no BOQ line | MISSING_LINE | crosswalk MISSING_LINE | PASS | - |
| 1b | element never detected (absent from register AND BOQ) | detected | nothing reported | FAIL | T-236 (independent inventory as the element source) |
| 1c | same, a freelancer row names it | flagged | SCOPE_UNKNOWN | PASS (only with a reference BOQ) | T-236 |
| 2 | one footing carried by two lines | flagged | not flagged; totals sum both | FAIL | T-236 (element_register_v0 catches it only for the same item + unit + key) |
| 3 | one opening deducted twice in one wall line | refused / flagged | line accepted | FAIL | T-236 (gross - deductions = net; one opening id once per face) |
| 4a | beam depth change, volume +1 % | flagged | STRUCTURAL flag only | PARTIAL | T-168 |
| 4b | beam depth change, volume +8 % | flagged | MOVED_5PCT | PASS | - |
| 4c | blockwork net +4 % (non-structural) | flagged | no flag | FAIL | T-168 (VERIFIED_CHANGED, any change to a verified line) |
| 5a | window with no height emitted MEASURED, no qty | refused | refused | PASS | - |
| 5b | same, emitted as 0.0 | refused / held | accepted | FAIL | T-235 (export refuses a 0 on a line with missing inputs; HELD never 0) |
| 5c | BLOCKED line without its question | refused | refused | PASS | - |
| 6 | conflicting floor levels | CONFLICT | element_continuity DRAWN_OUTSIDE_SPAN for spanning elements (t188); no sheet-to-sheet level check | PARTIAL (not probed further) | T-236 (storey datum agreement per sheet) |
| 7 | line re-measured on another drawing revision | flagged | only changed_fields=['project'] | FAIL | T-168 (REVISION_MIX refused) |
| 8a/8b | verified line unchanged / +1 % | counted / stale | COUNTED / STALE | PASS (scoreboard only) | T-168 (tie to the change log) |
| 9 | whole PAINT trade absent from the BOQ | trade flagged | NOT_MAPPED (join pending) | PARTIAL | T-236 (a row for every principal trade) |
| 10 | a line of another project in the BOQ | refused | accepted; totals include it | FAIL | T-168 + T-235 (one project id and one pinned revision set) |
| 11 | same lines, different producer order | identical bytes | bytes differ | FAIL | T-235 (canonical sort) |
| 11b | same lines twice | identical | identical | PASS | - |
| 12a | sealed benchmark by its name | refused | refused | PASS | - |
| 12b | renamed copy of the sealed benchmark | refused | not refused (guard by file name; Qortuba not named; Gate B / scoreboard / baseline tools do not call it) | FAIL | T-168 (guard by project id + sha256) |

Summary of the 20 scripted probes: 9 PASS, 2 PARTIAL (4a, 9; the script counts them as passes), 9 FAIL; probe 6 is
not scripted (existing t188 coverage only).

Further findings (not faults of a module, but dependencies):
- The structured checker verdict file (`research/agents_t177/CHECKER_VERDICTS_DEV_VILLA.json`, URBAN_SCOREBOARD_CHECKER_VERDICTS_V1)
  was last changed 2026-10-22 09:23 (7 verdicts, no whole-line re-measure). Every verdict since (columns 31 / 59, GF-W07
  4.458 m2) is board text only, so no script can count it. T-235 needs whole-line verdicts written to that file.
- Byte-deterministic xlsx already exists (`engine/reporting_v3/book.py`: fixed core.xml times and zip entry times).
- Canonical lines already carry project id, revision set sha256, element id, source documents, formula, evidence and
  approval state (`engine/source/boq_line.py`); no new line schema is needed.
