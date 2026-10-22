# Engineering reasoning and problem-solving standard (owner directive, 2026-10-22)

Permanent methodology for the Lead, Workers 1-3, the Checker and the audit done by the owner's main chat. ONE authoritative
copy: this file. Agent instructions link here; nothing else restates it. It does not replace owner-approved measurement
rules, does not authorise changes to frozen methods, does not change the released default (V2.9 + route G) and does not
release any held quantity. Statuses stay those of WORKFLOW_CONTROLS_2026-10-21.md section 5.

## 1. The change

Engineering problems are not multiple-choice questions for the owner. Investigate first, calculate second, verify third,
escalate only when necessary. When two quantities disagree, find WHY: measurement basis, gross vs net, missing deduction,
drawing revision, dimensions / levels / units, double counting, a contractual or payment convention, an estimating
convention vs an as-built dimension, a misread schedule, a missing element, an assumption shown as drawing evidence.
Never pick a number because it is larger, more conservative, closer to the freelancer or recommended by another agent.

## 2. Investigation procedure (every material discrepancy)

1. DEFINE THE PHYSICAL ELEMENT: project, building, level, room / element and element id (ELEMENT_REGISTER.md), trade, BOQ
   description, unit, drawing + revision, section / schedule, method. What construction work does the quantity represent?
   Split composite elements (a parapet = two vertical faces, a top surface, arrises, beads, drip, upturns, coping):
   each is its own item in its own unit.
2. EVIDENCE HIERARCHY: (1) project drawings and printed dimensions, sections, details, schedules, revisions; (2) project
   specifications and consultant instructions; (3) owner-approved rules and decisions; (4) verified engineering
   references; (5) approved owner fallbacks; (6) independently documented interpretations, labelled provisional. Never a
   licence to override an owner-controlled method silently: keep OWNER MANUAL METHOD and DRAWING-DERIVED METHOD side by
   side and explain the difference.
3. RECONSTRUCT FROM FIRST PRINCIPLES: not from the freelancer or the engine. Show dimensions, units, formula, deductions,
   additions, overlaps, rounding, tolerance, result.
4. RECONCILE: freelancer -> scope differences -> dimension differences -> deductions -> overlaps -> rounding -> own result,
   in units, not only %. Name any unexplained residual.
5. VERIFY INDEPENDENTLY (Checker): from the original evidence, never the worker's number as the expected value: element,
   revision, dimensions, units, physical interpretation, formula, deductions, classification, no double count, no
   omitted scope, correct BOQ integration.
6. STATUS: VERIFIED / DRAWING-CONFIRMED / ASSUMED — OWNER-APPROVED / HELD / UNKNOWN; RELEASED separately. A verified
   calculation may still rest on an owner-approved assumption: record both.
7. ESCALATE ONLY WHEN: drawings and approved rules cannot resolve it; a finish or material is genuinely unspecified; a
   contractual measurement decision is needed; two authoritative project documents materially conflict; an owner method
   would change; a release or platform authorisation is needed. Otherwise resolve it by engineering work.

## 3. Separations that are always kept

- Physical length / area / volume vs contract measurement quantity vs payable quantity vs unit rate vs amount (a corner
  paid at half rate is still its full physical length; 1,300 m.l x 1.25 KD = 650 x 2.50 KD, not 650 m of corner).
- Installed (net) quantity vs procurement quantity (block units, waste, cutting, pallets come after net area, by a
  separately documented procurement method).
- One element, several geometries: concrete axis length, bar path and cutting length, exposed formwork faces and
  excavation geometry are derived separately.
- Build before deduct: establish what is physically built (blockwork, glazing, plaster, paint, reveals, sills,
  waterproofing) before applying a deduction rule; never invent masonry to deduct glazing from it.
- A notation's meaning before its arithmetic (for example "n ø d/m": density, maximum spacing, a count in a module?),
  established from the schedule, sections and notes of the same set; an interpretation of one element type is not
  extended to another (footings -> columns, slabs, stairs) without its own evidence.
- Unit mass of bars: from the Urban rebar rule / the bar table in force; d^2 / 162 kg/m is a check, not a source.
  Cutting length from the detail (bends, hooks, laps, anchorage); no arbitrary lap or waste percentage.
- Geometric scope before numbers: two quantities of different physical scope are not forced to agree (reconciliation
  table per component: boundary id, drawing reference, gross / net, in method 1?, in method 2?, finish, BOQ owner).

## 4. Every resolved discrepancy leaves three things

A. The corrected quantity with basis and evidence. B. A generalisable rule written for any villa (scope and provenance
labelled; never a project-specific assumption stored as universal; rule changes go through a NEW rule / knowledge version,
never an edit in place). C. A regression test that fails if the error returns, with a normal and an adverse case.
Then: check the rule against owner methods (conflict register), integrate the verified correction, re-run the affected
BOQ, update SCOREBOARD v2 and the coverage report. The lessons are listed in section 7 below (newest first).

## 5. Roles

- LEAD: define the engineering question, name drawings and rules, scope the investigation with acceptance criteria,
  review the reconciliation, find cross-trade consequences, decide integration readiness, challenge unsupported
  conclusions, escalate only genuine owner decisions (section 6 format).
- WORKER 1 (structural): concrete, rebar, schedules, formwork, excavation, foundations, columns, beams, slabs, stairs,
  pools, domes; detailed bar takeoff where bar details exist, never approximate steel rates.
- WORKER 2 (architectural): rooms, floors, wall finishes, plaster, paint, blockwork, openings, ceilings, stair finishes,
  waterproofing, doors, windows, facades; installed vs physical vs procurement always distinguished.
- WORKER 3 (integration): confirm inputs, element ids, units, owner rule, dependencies, no double count across trades,
  the whole BOQ changes as expected, held stays held; Gate B package.
- CHECKER: reconstruct material calculations from source; challenge the physical interpretation; record what was checked,
  how, whether the evidence is independent, what was found, what remains uncertain, whether it generalises, whether the
  regression test is adequate.
- AUDIT (the owner's main chat, in its daily update): repeated resolved mistakes, unnecessary owner questions, payable vs
  physical confusion, freelancer values accepted without evidence, assumptions shown as facts, unintegrated code, missed
  BOQ scope, rules not propagated into tests. Systemic weaknesses, not task counts.

## 6. Owner question format (replaces "a question is one sentence with the options", MISSION.md)

Issue (the exact physical or contractual uncertainty) · Evidence (drawing, schedule, section, owner rule) · Investigation
(what was independently established) · Alternatives (only the genuinely unresolved ones) · Quantity impact (units) ·
Recommendation (engineering reasoning and evidence) · Status (what stays HELD) · Next action (what continues without the
owner). Never "which total do you prefer". Understandable without the owner reconstructing the analysis.

## 7. Lessons register (newest first; each row: problem, root cause, rule, test, status)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-22 | Freelancer corners: an itemised list summed 1,370.85 m.l against his 1,297.35 | The main chat's summary counted the boundary wall's stop-end column (73.65 m.l) twice (once in "stop-ends 547.47", once in "boundary wall 165.09") and rounded 48.15 to 48: 73.65 - 0.15 = 73.50. His workbook: column A 547.47 (formula SUM A51:A90) + column B 749.88 (SUM B51:B92) = 1,297.35, no residual | Reconcile a total from its source cells and formulas, never from a re-typed summary (any workbook) | T-172 | arithmetic explained (main chat, from the workbook cells), accepted by the owner 2026-10-22; physical classification and measurement of the affected items: Checker to verify independently (T-172) |
| 2026-10-22 | "2 m = 1 m" read as corners converted to m2 of plaster | A payment convention (half payable length) read as a physical conversion | Physical, contract, payable, rate and amount kept separate (any trade) | T-172 | rule recorded; test pending |
| 2026-10-21 | Q-71 option B recommended partly as "more conservative" | Notation meaning not established before rounding | Notation meaning first; N = ceil(L_eff / s_max) + 1 only when "/m" is shown to be a maximum spacing and L_eff is the bar-position length inside the covers (footings only until shown for others) | T-171 | investigation |

## 8. What this directive changed on the board (2026-10-22, main chat)

- Q-73 ANSWERED by this directive (section 6) and CONFIRMED by the owner 2026-10-22 (final): full openings are deducted from blockwork, plaster and paint, subject to
  the physical construction scope (no masonry invented behind glazing). Implementation T-175.
- Q-74 ANSWERED by this directive (section 7) and CONFIRMED by the owner 2026-10-22 (final; 2.29 / 3.26 m to be verified against the drawings): the actual beam-axis length governs the concrete volume of angled straps,
  with the footing overlap treatment established from the drawings; bars, formwork and excavation derived separately.
  Implementation T-174.
- Q-71, Q-72, Q-75 reopened as INVESTIGATIONS (T-171, T-173, T-176). They return to the owner only under section 2
  step 7, in the section 6 format.
- MISSION.md "stop that part and ask the owner at once" / "a question is one sentence with the options": superseded for
  WHEN and HOW to ask by sections 2.7 and 6. The no-assumptions rule itself stands: no invented value, no freelancer
  value, no silent default; an unresolved quantity stays HELD, never 0.

## 9. Compliance check (owner, 2026-10-22)

Every agent's next unattended run is checked by the main chat: final RUN_LOG line states `ERS: read` and the section applied; material-discrepancy handoffs carry element, reconciliation, rule, test and a lessons row; owner questions in the section 6 format. Instruction-file edits need no quantity regression test. Resolved engineering questions are never returned to the owner.
