# T-235 r1: one-command BOQ export (XLSX + CSV + manifest) from the canonical candidate lines

Worker 3 (lane I), 2026-10-23, run started 23:00 UTC. Hand-in **r1 = parts (1)-(3)**: export, quantity states, partial
lines; **VERIFIED 0 by construction** (no V2 verdict and no completeness input on the CLI). r2 = the V2 verdict schema
file, its validator, the CLI flag and the 'verdict add' helper. Part (4) (the T-233 line) waits for r2 + T-236.
A read-only tool, NOT a method version: no engine quantity is computed, changed or approved; nothing in `engine/`
imports it; released default stays ARCH_TAKEOFF_V2.9 + route G.

## 1. What was built

| File | What |
|---|---|
| `tools/boq_export_v1.py` (new, `DEFAULT_GUARD_CLASS = "TOOLING"`) | `export()` / CLI: one canonical row list -> `BOQ.csv`, `BOQ.xlsx` (sheets BOQ, Trade summary, Manifest; zip / core.xml times fixed by `engine/reporting_v3/book._repack`), `BOQ_TRADE_SUMMARY.csv`, `EXPORT_MANIFEST.json` (input sha256s, candidate version, project id, revision set, BOQ_LINES sha256, code commit, output sha256s, row counts by state, semantic sha256) |
| `tests/t235_boq_export/test_probes.py` | ADVERSARIAL_PROBE probes 5b, 10, 11: strict xfail in commit 29f11c90 (they fail on the merged head: no tool), markers removed in 24da9dd9 (pass) |
| `tests/t235_boq_export/test_boq_export.py` | hand-made synthetic villa (not the development villa) + the footing-shaped partial line + every adverse case of the row |

Rules the tool applies (each a test): rows sorted (trade, item code, floor, element id, line id); refused, nothing
written: two project ids or two revision sets, not the expected pair, an inventory of another project, a quantity
line at 0 with no gross and no numeric input (HELD is never 0), a duplicated line id, a sealed benchmark input
(`refuse_if_sealed`), an empty BOQ, a row count that differs from lines + unmeasured elements. Quantity states one
column each: VERIFIED, VERIFIED ZERO, VERIFIED COMPONENT, MEASURED UNVERIFIED, HELD (blank + reason + range), UNMEASURED
(inventory element with no line), EXCLUDED (blank + reason); an unknown is an empty cell in CSV and XLSX. A quantity
line with an open convention range (low < high) keeps the range in `open_range_low / high` (found on the real run,
section 3). VERIFIED only from a bound V2 record (project, revision set, candidate version, BOQ sha, unit, engine qty,
element scope all equal to the exported line, else STALE / SCOPE_DIFFERS / BINDING_INCOMPLETE; > 1 % = DISCREPANCY ->
the row becomes HELD) AND, for WHOLE, a passing completeness record (inventory = element scope, missing / duplicated /
held 0); COMPONENT verdicts give single VERIFIED COMPONENT rows and never a VERIFIED line; V1 records show as
`V1_NOT_BINDING`. Owner status class per row: VERIFIED / PROJECT-SPECIFIC (line states ASSUMED - OWNER-APPROVED,
PROJECT_OWNER_FACT or OWNER_FACT) / SOURCE-SUPPORTED PENDING INDEPENDENT CHECK / OWNER DECISION REQUIRED (only an
explicit `rfi.owner_decision_required`) / HELD / EXCLUDED.

## 2. Synthetic villa (hand calculation, before running)

Footings F1 1.200 + F2 0.800 + F3 2.000 = 4.000 m3 MEASURED UNVERIFIED; slab S1 HELD 5.000 .. 6.000, S2 HELD no range;
lintel EXCLUDED; paint 40.000 m2 PROJECT-SPECIFIC; block W0 0.000 m2 kept (gross 4.000 - deduction 4.000). 8 rows,
VERIFIED 0. Footing-shaped line: 25 COMPONENT verdicts (subtotal 0.51 + ... + 0.75 = 15.750 m3) + F10X HELD
0.216 .. 1.960 + band B1 OWNER DECISION REQUIRED + FN9 inventory-only = PARTIALLY VERIFIED 25 / 28, subtotal 15.750 apart,
held and unmeasured components named; WHOLE over 25 of 26 lines -> SCOPE_DIFFERS; removing F10X from the input -> it
appears as UNMEASURED (row count stays 28). 30 tests pass.

## 3. Real development-villa run (private scratch only; counts and hashes, no client data)

Inputs: Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip (P7757.dxf ab54dd55) and "ST7757 dxf.dxf" (9f9d1179);
T-167 chain + `research/agents_t211/v309_run.py`: **V3_0_9_BOQ_LINES.csv 63b350cf reproduced** (= T-211 Gate B),
json 1dee622c, 3,583 lines.

- **Full candidate export: REFUSED** (`ExportError: lines of 2 project ids ...: one BOQ is one project`). The
  candidate carries two identities: 3,004 structural-route lines (revision set 297e913d) and 579 architectural lines
  (revision set db7b3eb8). One villa, two drawing sets, two revision hashes: the identity is per route, not per
  project. The refusal is the owner rule (19:00 (2), probe 10) doing its job; the fix is an identity defect in the
  candidate, not in the export (proposal below).
- Diagnostic export per identity (scratch only, not a BOQ): structural 3,004 rows = MEASURED UNVERIFIED 786, HELD
  1,632, EXCLUDED 586, VERIFIED 0; classes SOURCE-SUPPORTED 784, PROJECT-SPECIFIC 2, HELD 1,632, EXCLUDED 586;
  140 open-range quantity rows (110 beam, 28 ground beam, 1 footing, 1 stair). Architectural 579 rows = MEASURED
  UNVERIFIED 304, HELD 213, EXCLUDED 62; classes SOURCE-SUPPORTED 286, PROJECT-SPECIFIC 18. Reversed producer order:
  identical bytes on both. 0 zero-refusals on the real lines. Every trade NOT VERIFIED (0 / n whole lines), as it
  must be while no V2 verdict exists.
- CONC.FOOTING: 26 rows, 66.264 m3 measured unverified, of which the F10 / F outline row is PROVISIONAL 1.960 with
  open range 0.216 .. 1.960 (the T-239 defect: the owner reading is a CONFLICT with both drawn readings HELD); the
  export now shows that range instead of a bare 1.960. CONC.BLINDING: 4 rows, 15.179 unverified + 3 HELD 5.807 .. 10.784.
- 15 PLASTER, 15 PAINT and 5 CEILING lines sit under the structural identity: the same trades appear under two
  identities; a single-identity BOQ must decide per line which drawing set it rests on.

## 4. Who is right / proposals

No engine quantity changed; no freelancer comparison made (the export is not a scorer). Proposal for the next V3.0.x
slot (lane I, serialised with T-232 / T-239): one project id and one revision set for the whole candidate = sha256 of
the sorted drawing sha256s of BOTH sets (T-168 manifest), each line keeping its own source documents; until then the
real export stays refused, which is correct. Lessons-register row (ERS s.7): "a BOQ line set must carry one project
identity and one revision set covering every drawing it rests on; per-route identities make the BOQ unexportable"
(general, lane I, provenance T-235 r1 real run; test: probe 10 + test_two_revision_sets_refused).

# T-235 r2 + part (4): V2 verdict schema, validator, 'verdict add' helper, --verdicts-v2, T-236 report as completeness

Worker 3 (lane I), 2026-10-24, run started 09:00 UTC, on working head 74c966b1. Still a read-only tool: no engine
quantity is computed, changed or approved; released default ARCH_TAKEOFF_V2.9 + route G unchanged.

## 5. What was built

| Piece | Where | Rule |
|---|---|---|
| Schema URBAN_CHECKER_VERDICT_V2 (new; the V1 file and tools/scoreboard_v2.py untouched) | `schema_document()` in `tools/boq_export_v1.py`, published as `research/agents_t235/URBAN_CHECKER_VERDICT_V2.schema.json` (a test keeps them equal) | required: schema, verdict_id, project_id, revision_set_sha256 (64 hex), candidate_version, boq_lines_sha256 (64 hex), line_ids (unique), element_scope {ids unique, count = len}, unit (boq_line UNITS), engine_qty, checker_qty (non-negative numbers), evidence [{sheet + printed value}], checker {run_token, routine = Checker / Verifier, verdict_commit 6-40 hex}, scope WHOLE / PARTIAL / COMPONENT, time ISO UTC |
| Validator | `validate_v2(record)`, `validate_v2_set(file)`; CLI `verdict-validate FILE` (exit 1 on any problem) | `bind_verdict` now refuses any record that fails `validate_v2` (BINDING_INCOMPLETE) before binding; a routine that is not the Checker is invalid |
| Helper | `verdict_add(...)`, `verdict_set_append(...)`; CLI `verdict-add` (`--line-ids` or `--item-code [--unit]`, `--lock-file docs/agents/locks/checker.lock` gives run token + routine) | binding filled from the candidate lines; refused: unknown / repeated line id, held or excluded line, two units, two identities, COMPONENT over more than one line, an id already in the file; records sorted by id; deterministic verdict id from the binding |
| Export flags | `--verdicts-v2 FILE` (URBAN_CHECKER_VERDICT_V2_SET), `--completeness TRADE_COMPLETENESS.json` | both sha256 in the manifest; every record listed in `v2_verdicts` with its status (COUNTED / STALE / SCOPE_DIFFERS / DISCREPANCY / BINDING_INCOMPLETE / NO_LINE_IN_THIS_EXPORT / ACROSS_n_BOQ_LINES): none dropped |
| Part (4) | `report_check`, `report_unmeasured_rows`, `completeness_from_report` | see section 6 |

## 6. Completeness from the merged T-236 report (part 4)

The T-236 report has no project id or revision set. It is bound by line ids instead: a report that names a line id the
exported BOQ does not carry is refused (computed on other lines). Per BOQ line (trade, item, unit) the derived
completeness record passes only when: its lines map to one principal trade (`line_trade`); that trade maps to this one
BOQ line (not SPANS n BOQ LINES); every line of the trade is in the report and linked; the trade is
COMPLETE_AGAINST_INVENTORY with missing, duplicated, held, conflict, geometry_only, unresolved, register_only and
out_of_inventory_scope all 0; no refused deduction; inventory count (elements with an independent source) = element
scope count. The summary's new `completeness` column says PASS with the counts, or FAIL with every blocker. MISSING,
CONFLICT and geometry-only elements become UNMEASURED rows (blank quantity, reason, sources); a principal trade with no
line and no inventory is one UNMEASURED row under its principal trade id. `--inventory` (V1) and `--completeness`
together are refused.

## 7. Synthetic villa (hand calculation before running; not the development villa)

Footings FDN F1 1.50 x 1.00 x 0.80 = 1.200, F2 1.00 x 1.00 x 0.80 = 0.800, F3 2.50 x 1.00 x 0.80 = 2.000 = 4.000 m3;
schedule F1-F3 (PRINTED_SCHEDULE). Checker WHOLE 4.010 m3 (+0.25 %) + complete report -> F1 / F2 / F3 VERIFIED
1.200 / 0.800 / 2.000, line VERIFIED, subtotal 4.000; slab stays HELD 5.000 .. 6.000, paint MEASURED UNVERIFIED 40.000.
Adverse, each NOT VERIFIED or refused: schedule adds F4 (MISSING 1 -> F4 an UNMEASURED row; the WHOLE record no longer
covers the line's scope -> SCOPE_DIFFERS); strap ST1 scheduled with no line -> UNMEASURED under CONCRETE.STRAP; F3's line
also linked to F2 -> DUPLICATED 1; report with an extra line F7 -> refused; footing line also in m2 -> SPANS 2 BOQ
LINES; no report -> "completeness record missing"; a record for another candidate version -> STALE, listed; 12 broken
bindings (no sheet, no printed value, routine Worker 3, time 'yesterday', scope ALL, qty as text or bool, unit 'cubic',
count 4 for 3 ids, repeated id, short sha, V1 schema) -> validate_v2 problems -> never COUNTED; every required field
removed in turn -> named. CLI end to end (verdict-add -> verdict-validate -> tools/trade_completeness.py -> export):
VERIFIED 3 in CSV and XLSX, input sha256s in the manifest, two runs byte-identical.

## 8. Real candidate

Not run: the real V3.0.9 export stays refused by probe 10 until T-245 (one identity over both drawing sets) merges
(Lead 2026-10-24 00:10: r2 proves it on synthetic and adverse fixtures). No Drive file was read in this run. No V2
record exists yet on the board, so the real export would still show VERIFIED 0.

## 9. Residual risk / proposals

- The T-236 report carries no project id, revision set or BOQ_LINES sha256; the binding by line ids catches a report
  of other lines but not a report computed on the same line ids with other content. Proposal (T-236 follow-up, lane S):
  the runner writes `project_id`, `revision_set_sha256` and the lines' sha256 into TRADE_COMPLETENESS.json; the export
  then compares them (one more equality, no other change).
- Principal-trade rows with no line (NOT_MEASURED) are their own trade in the summary, so they never block the
  CONCRETE trade status; they stay visible as UNMEASURED rows. If the owner wants a NOT_MEASURED principal trade to
  hold its parent trade's status, that is a one-line change in `report_unmeasured_rows` (trade column).
- ERS s.7 lessons row proposed: "a verification record must carry the identity of the exact line set it verified
  (project, revision set, candidate, BOQ sha, unit, engine qty, element scope); anything less transfers a verdict to a
  quantity nobody checked" (general, lane I, provenance T-235 r2; tests test_v2_bound_to_another_line_is_never_verified,
  test_validator_refuses_a_broken_binding).
