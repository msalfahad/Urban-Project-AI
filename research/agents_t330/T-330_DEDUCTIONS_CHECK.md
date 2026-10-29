# T-330: canonical deductions check and guarded export (export integrity; every villa)

Tooling only: no engine, method, rule / knowledge version, registry, frozen file or candidate line changed. Development
villa, not an accuracy claim. Drawings cited by Drive title only. Worker 1, 2026-10-29.

Run identity: Drive "Alsenan chalet project" P7757.dxf (from P7757_DXF_COMPRESSED.zip) `ab54dd55`, 'ST7757 dxf.dxf'
`9f9d1179`; own run `research/agents_t167/v304_run.py` -> `research/agents_t244/v3020_run.py` (Python 3.11.18):
V3_0_20_BOQ_LINES.json **`097a80b6`** (= the candidate of record) and V3_0_19 `b35475bf`, both byte for byte.
Check: `python3 -I tools/t330_deductions_check.py check --lines V3_0_20_BOQ_LINES.json --json .. --csv ..`
(report json `2c8fb5d0`, exit 1 = FLAG only, 0 REFUSED). Findings, one row per line:
`V3_0_20_DEDUCTIONS_FINDINGS.csv` (engine ids and quantities only). The T-315 r2 candidate (V3.0.21) is not merged:
not run (acceptance (a) "when merged").

## 1. What the check tests (every villa)

For every line with a numeric gross and a measured_net, in the line's unit, tolerance 0.0005 (the export's own
QTY_MATCH_TOL): `gross - sum(deductions) + sum(additions) = measured_net`, and every deduction names what it deducts and
carries one non-negative number the export can read. REFUSED: mixed units, negative deduction, deductions above the gross.
FLAG: non-numeric, empty list with gross != net, not summing, export total blank (the export's own reader
`boq_export_v1._deductions` gets no total), missing id. Held / excluded / no-gross lines are NOT_APPLICABLE, never OK.
Deductions found only under `calculation.inputs` are reported as a diagnostic "shadow" list and never pass a line.

## 2. Result on the candidate of record V3.0.20 (3,705 lines)

92 lines carry arithmetic (gross and net numeric), 3,613 do not (all 3,613 carry no gross; no line has a gross without
a net). 62 pass; **30 fail
(30 FLAG, 0 REFUSED)**, in four causes:

| Family (unit) | Lines failing / checked | Gross | Net | Gross - net | Cause (physical / data) |
|---|---|---|---|---|---|
| FIN.PLASTER (m2) | 4 / 4 | 259.510 | 217.208 | **42.302 m2 (19.5 % of net)** | EMPTY_DEDUCTIONS: the opening deductions (3 per line) sit only in calculation.inputs.owner_manual_method; their sum explains the gap exactly on all 4 |
| FIN.PAINT (m2) | 4 / 4 | 259.510 | 217.208 | **42.302 m2 (19.5 %)** | the same 4 room faces, same cause |
| FIN.SKIRTING (lm) | 11 / 11 | 262.559 | 185.517 | 77.042 lm | 9 NOT_SUMMING: the list omits the floor-level window-threshold length that the net also leaves out (moved to a separate range line); residual = inputs.window_threshold on all 9, **13.569 lm**; all 11: EXPORT_TOTAL_BLANK + MISSING_ID |
| FIN.FLOOR.PORCELAIN (m2) | 2 / 11 | 143.489 | 143.489 | 0.000 | NOT_SUMMING: gross was set equal to the settled net while the list still carries the face's void / stair deductions (**39.308 m2**): a consumer computing gross - deductions under-reads the two floors by 39.308 m2 (1F room: 33.711 - 31.114 = 2.597) |
| ARCH.WALL_RUN (lm) | 7 / 7 | 337.849 | 216.931 | 120.918 lm | arithmetic exact; EXPORT_TOTAL_BLANK + MISSING_ID |
| FIN.CEILING (m2) | 2 / 28 | 202.911 | 170.901 | 32.010 m2 | arithmetic exact (the 16.005 m2 void); EXPORT_TOTAL_BLANK + MISSING_ID |

Export cross-check (plain `tools/boq_export_v1.py` on the same lines): **every one of the 22 rows with a canonical
deduction list shows deductions_n > 0 and a BLANK deductions_total** (the lists use unit-named keys {"m2": x} /
{"lm": x} and a 'what' text, which the export's reader does not read), and 8 rows (plaster / paint) show gross != net with
deductions_n 0. The guarded export (`t330_deductions_check.py export ...`) refuses the record: exit 2, nothing written.

## 3. The fill (next lane I package; named, not done here)

1. FIN.PLASTER / FIN.PAINT, 8 lines: copy the owner-method opening deductions into the canonical list (opening id +
   m2 each); shadow sum = gap on all 8.
2. FIN.SKIRTING, 9 lines: list the window-threshold length (13.569 lm in all) as its own deduction, naming the range
   line that carries it.
3. FIN.FLOOR.PORCELAIN, 2 lines: either restate gross as the face area before the listed deductions, or list the
   settle / wet-part / landing steps so that gross - deductions = net (a formula decision for lane I; the net is not
   in question here).
4. All 22 listed lines: give each deduction an id and a quantity key the export reads (or extend the export's reader to
   unit-named keys as a new export version); until then BOQ.csv deductions_total stays blank.

## 4. Lesson (proposed for ENGINEERING_REASONING_STANDARD s.7)

| 2026-10-29 | 30 of 92 V3.0.20 lines that carry gross and net do not reconcile in their canonical 'deductions' field (plaster / paint 42.302 m2 each listed only in the owner-method inputs; skirting 13.569 lm missing from the list; porcelain gross written equal to net beside 39.308 m2 of listed deductions); every listed deduction is unreadable by the export (deductions_total blank on 22 rows) | lines were revised in their calculation inputs and net, never in the canonical deduction list, and no check tied gross, list and net together | every exported line satisfies gross - deductions + additions = net in its own unit, each deduction with an id and a number the export reads; held lines are not checked, never passed; the export refuses otherwise (every villa) | tests/t330_deductions_check (normal: listed and summing, additions, no-opening line; adverse: empty list, short list, gross = net with a list, above gross, mixed / unit-keyed units, negative, range, no id, duplicate ids, guarded export writes nothing) | check DONE; fill = next lane I package |
