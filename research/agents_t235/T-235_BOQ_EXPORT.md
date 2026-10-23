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
