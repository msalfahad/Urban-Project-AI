# Task board (Lead writes; workers claim one row; verifier records the verdict)

Status: TODO -> CLAIMED (worker, branch) -> READY (worker done) -> MERGED or REJECTED (verifier, reason).
BLOCKED-DATA = needs `urban-boq-private-data`; BLOCKED-OWNER = needs an answer in OWNER_QUESTIONS.md.
Order: lowest gate first, then money at risk. Statuses from the master study are claims: check them against code first.

| Id | Gate | Trade | Task | Status | Branch | Verdict |
|---|---|---|---|---|---|---|
| T-001 | 0 | scoreboard | `tools/alsenan_scoreboard.py`: engine vs freelancer per trade and unit: coverage, silent omissions, WAPE, signed error, false positives; writes SCOREBOARD.md. Synthetic tests in tmp | BLOCKED-DATA (code + tests can start) | | |
| T-002 | 0 | baseline | Capability matrix from the code and the BOQ family registry vs the study's `03_CAPABILITY_MATRIX` (e.g. blockwork "UNSUPPORTED" there); triage the 377 known suite failures into private-input-absent vs real | TODO | | |
| T-003 | 4 | plan reader | `tools/plan_reader/`: text layer of PLAN_READER.md (pdfplumber, pypdfium2, Tesseract eng+ara pinned by SHA-256); `plan_reading.json`; tests on generated bilingual sheets (rotation, scan noise, missing scale -> NOT_SCALABLE) | TODO | | |
| T-004 | 1 | rooms, doors, windows | Census check: every room label and opening tag in CAD text and in the plan reading appears in the engine output as measured / held / unsupported; list silent omissions | TODO (after T-003 for PDF sheets) | | |
| T-005 | 1 | floor area, windows | D-P9-01 curved glazing without wall gap loses the room; D-P9-02 curved window closes at glazing line (0.438423 m2 reveal strip in floor). New method version | TODO | | |
| T-006 | 1 | floor area | D-P9-04 zone-bounded space 3.832 vs 4.731 m2: cell-by-cell face decomposition; then audit the 23 explained-unverified changes | TODO | | |
| T-007 | 2 | blockwork | Blockwork m2 / m3 by thickness from wall runs x evidenced soffit / beam height, minus openings and column / beam intersections; HOLD when height absent | TODO | | |
| T-008 | 2 | doors, windows | L-P9-01 rotated schedule header; schedule match by id + width + geometry, ambiguous row rejected | TODO | | |
| T-009 | 3 | rebar, concrete | Read structural schedules and tables (bar marks, element populations) so rebar is counted per population, never a kg/m3 proxy as measured tonnage | TODO | | |
| T-010 | 1 | wet areas | L-P8-01 WC-sized chair classified as toilet: symbol class + context, adversarial fixture | TODO | | |
| T-011 | 1 | doors | Knowledge 1.5.0 (new version file, 1.4.0 untouched): owner answer Q-04 / D-16 resolves owner_questions[4] and rules[15]: minimum = nominal door opening (ordinary 1.00 -> 1.10, bathroom 0.90 -> 1.00 wall to wall, both confirmed), drawn size used when wider, main door as drawn. Use the urban-rule-reconciliation skill; new method version only if behaviour changes | TODO | | |
| T-012 | 4 | intake | Intake the owner's other villas (AutoCAD + PDF, no full structure) into `urban-boq-private-data/dev_villas/`: inventory each sheet, run the CAD audit and the plan reader, record rooms / openings census. Development set for architectural trades only | BLOCKED-DATA | | |

## Later (lead promotes when the gate is reached)
Revision delta between drawing issues; push released BOQ lines to the Firestore app; facade finishes; roof build-up;
formwork; excavation.

## Ideas (from the research scout; the lead turns useful ones into tasks)

From the 2026-10-17 BOQ engines study, which the owner supplied (see RESEARCH_LOG.md and research/2026-10-17_BOQ_ENGINES_STUDY.md). Ranked for the Alsenan scoreboard:

1. Visible deduction rows per wall (`D1 2 x 1.0 x 2.1 = -4.20 m2`, tied to the DXF block): makes blockwork and plaster gaps explainable.
2. Measured, waste-adjusted and order quantity as three columns: shows whether a gap comes from measurement, the waste rule or rounding.
3. Net, gross and centreline variants per room or wall, side by side, matching whichever basis the freelancer used.
4. Recipes per unit (block wall per m2 expands to blocks, glue, lintels, plaster and labour) in one rule source.
5. Provenance on every quantity: file, layer, entity handle, rule version, reviewed.
6. Overlap check: shared floor = sum - union must be 0.
7. Three-band confidence: commit, withhold with location (an owner question), or reject.
8. Skirting = perimeter minus stated door widths, with the inputs recorded.
9. DXF revision diff that flags affected BOQ lines (needed for the second villa).
10. (scout 2026-10-17) Rebar: link every schedule value to (element, location, parameter) and hold it for review before tonnage (Li et al. 2026; T-009).
11. (scout 2026-10-17) Rebar: bar-mark and count-expression parser tested on dxfstructure notation (`[1] - #12 L=2120`, `2*2#12-[4]`); own code only, GPL source (T-009).
12. (scout 2026-10-17) Blockwork: sandbox test of pygeoops.centerline (BSD-3) on wall polygons as an independent wall-length check (T-007).
13. (scout 2026-10-17) Blockwork / finishes: girth diagnostic, external girth - 4T vs engine external-wall centreline, per floor (K.C. Tang centre-line rules).
