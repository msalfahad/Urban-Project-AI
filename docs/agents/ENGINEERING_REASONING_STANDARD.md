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
| 2026-10-23 | Necks: released 10.855 vs freelancer 8.805 m3 (+2.0505, +23.3 %) looked like one height difference | Four causes mixed in one total: scope he prices that the engine holds (-1.350), his wider C11 (-0.165), two necks he omitted (+0.720), and two different wrong height bases (+2.8455: released top at the FFL = finished-as-structural; his flat 1.50 = the p.9 minimum founding depth, a design limit, not a member length) | Decompose a total difference into scope / count / section / datum components before any verdict; a design limit or minimum printed in the notes (founding depth, cover, spacing limit) is never a member dimension (every villa) | tests/t205_neck_ends (19; adverse: limit used as a length, finished level as structural datum) | VERIFIED (Checker 11:52, re-derived 0.0 %) |
| 2026-10-23 | The sunken wet-slab panels looked like two different sets (GF 19.396 + 1F 5.400 m2 in T-139 / D-41; 1F x5 + 2F x1 in T-206) | Two storey conventions for a slab element: named by its slab sheet vs by the floor it carries | Declare the storey convention of every slab element and match sets by geometry (hatch / outline), never by storey label; one element per physical panel (every villa) | tests/t213_sunken_panels (storey matching never forced; adverse: label-only match refused) | proposed (T-213 READY) |
| 2026-10-23 | The owner's rough wall-tile form '(face - door widths) x H' gives 14.67 m2 less than the opening-by-opening net on 11 wet rooms (T-209) | Deducting a door by its width over the full tile height also removes the built and tiled band above each door head | Deduct each opening by its own area (width x height) from the face it pierces (Q-73); a width-only deduction is shown beside as the owner's rough check, never released (every villa) | tests/t209_wet_wall_tiles (adverse: width x full height deduction refused as the net) | proposed (T-209 READY) |
| 2026-10-23 | The T-202 guard sweep's importer index skipped `from .x import y`, so a relative import of a producer was invisible | The index resolved only absolute module paths | A guard sweep resolves relative and bare-stem imports and run-time loads (importlib / __import__ strings) before it reports 'no importer' (every module) | tests/t212_guard_property (6 import forms, transitive chain) | proposed (T-212 READY) |
| 2026-10-23 | A guard test went red on the working branch with the block-wall merge (T-108 r2, 01eeafd0) although the task head was green (Checker 09:59, G-T206-2); no quantity affected | The T-202 sweep pins its merge window but scans importers on the live tree, so any later legitimate importer breaks a snapshot assertion; gate b ran the guard tests on the task head, not on the head merged with the working branch | A guard or sweep test either reads its pinned commit or checks a PROPERTY over the live tree (every new module classified; no candidate / released method reaches an unguarded producer), never a live-tree snapshot; gate b runs the guard tests on the task head MERGED with the working branch before the push (all engine/source changes; Lead 10:20, proposed) | T-212 (tests/t212_*: normal = a producer importing a producer allowed; adverse = unclassified module, candidate importing an unwired producer) | PROPOSED (T-212 TODO) |
| 2026-10-23 | The lift pit was reported 'not drawn' (inventory T-188) although the structural PDF details it (p.14 typical: ring 1.600 m2 gross, 1.100 m2 net) | The search read the DXF only; the PDF detail page has no text layer, so a text search cannot see it | An element is NOT DRAWN only after every sheet of every format was searched, including image-only PDF pages read visually (extends the 2026-10-23 format-signature row; every villa) | T-204 tests (normal: detail found on an image-only page; adverse: absence claimed with a sheet unsearched -> refused) | VERIFIED (Checker 09:11, own read 0.0 %) |
| 2026-10-23 | Shuttered windows W11 / W12 billed at 7.800 m2 by the freelancer vs 4.290 m2 each between the shutter leaves | His height was the frame / fabrication height, not the opening | Opening size (between the leaves or reveals) and fabrication / frame size are separate quantities; window m2 takes the opening, the frame size belongs to procurement (every villa) | T-207 tests (normal + adverse frame height offered as opening -> refused) | VERIFIED (Checker 09:11, ENGINE_RIGHT) |
| 2026-10-23 | Lift walls / pit and the roof water tank have no structural BOQ line in ANY state (released A, V3.0.5, V3.0.6), while the freelancer prices lift walls (T-188, Checker 08:02 own re-read: lift footing FF + 4 columns drawn, no LIFT / PIT / TANK detail) | Totals were compared line by line; nobody inventoried every drawn element across disciplines and storeys first, so an element with no line was invisible | Inventory every element (stair, lift, shaft, void, column, pool, tank, dome, ramp, parapet) across disciplines and storeys BEFORE comparing totals; an absence counts only with the sheets SEARCHED, else UNKNOWN; an element with no line is a finding, never 0 (every villa) | tests/t188_element_continuity (villa K, 40) | rule + test MERGED fb3a4623; lift / tank lines T-204 |
| 2026-10-23 | Necks taken to the FFL +1.00 and B20 / B23 tops at the FFL (T-200, Checker 07:00): released necks 10.855 m3 PROVISIONAL vs freelancer 8.805 m3 | The structural set prints only the architect's finished levels; a finished level was used as a structural datum | Every level is a named physical datum (FFL, structural top, soffit, beam bottom, footing top, formation); a finished level never feeds a concrete dimension; an unprinted structural level is HELD with the missing item named (proposed UP-LEVEL-DATUM-001; every villa) | tests/t200_level_chain (26, adverse: finished-as-structural, conflict, limit) | rule proposed, test MERGED d699b650; necks T-205, ST PDF levels T-206 |
| 2026-10-23 | 21 window heads called 'not drawn' for two days while a never-opened vector DWF of every sheet printed them (T-201, Checker 07:00: W09 / W10 / W24 0 mm) | Project files identified by name and extension, not by format signature; one drawing format never opened | Identify every project file by its format signature and open each format before calling a value not drawn (proposed UP-OPEN-GEOM-001; every villa) | tests/t201_* (reader vs DXF, one translation, scale 1.000) | rule proposed, test MERGED 5dade783 |
| 2026-10-23 | Three new third-party importers crossed the K1 boundary unseen (T-202: arch_v302 ezdxf, masonry_centreline_v2 shapely, concrete_overlap_ownership numpy) | Whole-repo guard tests already red stop at the first offender, so later offenders are hidden | A red guard is tracked by a known-failures ledger; every READY row's gate b states 'known_failures check: NEW 0'; an unexplained failing id refuses the ledger (every task) | tests/t202_guard_sweep (adverse: NEW id exit 1) | rule + test MERGED 210ce4f0; K1 / pymupdf / gitdir follow-ups T-210 |
| 2026-10-23 | Block m2 rejected (T-108 r1, Checker 07:13): the hand run length used where the physical run governs (T stems through the face) | The comparison method (hand run) was used as the measurement basis | Block length = the physical MASONRY_CENTRELINE_V2 run, T stems stop on the face, overlap 0 by construction; the hand run is shown beside, never used (Q-69 B; every villa) | tests/t108_masonry_area (module refuses a centreline T stem) | rework r2 READY 07:56 |
| 2026-10-23 | Pool base mats counted only at max spacing + 1 (T-191, Checker 03:58; R1 low end 839.34 vs about 824.89 kg) | The '/m' meaning proven for FOOTINGS (T-171: maximum spacing) was carried to a pool mesh without that element's own evidence | A notation's meaning is established per element type; a '/m' mesh carries count A (bars per metre x width) .. B (max spacing + 1) unless the element's own drawing fixes it (any villa) | T-191 r2 adverse case: open mesh where A != B, closed loop where A = B | rework (Lead 04:20) |
| 2026-10-23 | Candidate 1F 'winder stair' 4.451 m3 is a dome outline (T-196 finding, T-187 identified; Lead register ruling 04:20) | Element type inferred from linework shape (radiating lines from one point) without checking the element's levels and the structural detail it belongs to | An element is typed from its drawing evidence (label, detail, levels), never from a shape heuristic alone; a radial pattern with no riser levels is not a stair; the misread line is HELD and retired, never relabelled (any villa) | to be added by T-193 (adverse: radial dome outline offered to the stair reader) | open (Gate B on T-187, retirement in T-193) |
| 2026-10-23 | Register-v0 holds about 3 COL elements per physical column (T-196, Checker 02:08: GF C2 12 vs 4 drawn) | Engine pieces / per-sheet outlines / storeys not collapsed into one physical element | One physical element per storey; engine pieces are its components; no count from the register is quoted before this holds (any villa) | T-196 r2 adverse cases: one column with three engine lines -> one element; two storeys of one mark -> two sets | rework (Lead 04:20) |
| 2026-10-23 | W01 / W03 sill and head 1.85 / 3.85 vs 1.00 / 3.00 above FFL (T-194 found, T-198 fixed, Checker 03:57 own DXF) | Elevation dimension chain read from the drawing's ground line, not from the floor's own level marker (+1.00 floor) | Every elevation chain is re-datumed from the level marker of the floor the opening sits on before a sill / head is recorded (any villa) | tests/t198_census_r3 (adverse: raised floor) | fixed (MERGED 57bb0411) |
| 2026-10-23 | Stale docs/CODEMAP.md at handoff twice (D-T179-2, D-T191-1) with the self-gate saying PASS | Map built before the last file / branch merge | Regenerate the map as the LAST commit and run `codemap check` on the pushed head (every task) | process check by the Checker gate c | rule in every row (Lead 04:20) |
| 2026-10-22 | Pool walls 2.710 vs 2.828 m3 (T-183, Checker 12:05) | The printed 1.15 m is the FINISHED water depth (rim to tile); it was taken as the RC wall height although the cut draws a 50 mm build-up over the structure line | RC wall / slab height = to the STRUCTURAL surface read from the section's structure line; a finished depth or level is never a concrete dimension without its build-up; both kept, labelled (any villa; pools, tanks, sunken slabs) | T-183 r2 (adverse: finished depth taken as structural height) | rework (T-183 r2) |
| 2026-10-22 | Column joint faces +12 % (COL-GF-19 1.124 vs 1.004 m2; T-163, Checker 12:05) | A beam running through / flush with a column face counted as covering the full face width; oblique framing mis-handled | Face covered by a framing member = that member's own width on that face; the remainder stays open formwork (any villa) | T-163 r2 (adverse: beam narrower than the column face, running through) | rework (T-163 r2) |
| 2026-10-22 | Corners handed in as m2 again after the 07:10 correction (T-162 r1) | Work claimed before the correction, not re-read before hand-in | A handoff is checked against every owner-session entry newer than its claim before READY (any task) | T-162 r2 adverse case (corners stay m.l) | fixed in T-162 r2 (READY), Checker to confirm |
| 2026-10-22 | Engine pool 3.495 vs own 7.084 m3 (Checker T-180) | Defaults (floor 0.25 m, walls 1.60 m, 6.045 m2) used and only the straight strip of a curved wall ring read, while the structural detail printed 0.40 m and the architecture gave the levels and the full ring | DEFAULT GUARD: before any default, search and reconcile every relevant drawing, section, schedule and detail; a fallback only when the documents genuinely do not establish the value; partial footprints flagged (any villa, any element) | T-186 | rule recorded (owner 2026-10-22); guard to build |
| 2026-10-22 | Pool concrete 3.50 (engine) vs 12.348 m3 (freelancer) | To establish (T-183); his total includes a pump room (3.48 m3) and 1.8 m walls | Every pool is reinforced concrete by component (blinding, base, walls once at the junction, steps, rebar, formwork, joints / waterstops, waterproofing, finishes); never blockwork; scope (pump room) only if drawn (any villa) | T-183 | investigation |
| 2026-10-22 | Stair + dome 12.01 vs 21.833 m3 | To establish (T-184 / T-185); his figure = main stair 8.131 + 'stair 2' 5.510 + entrance 1.411 + 3 domes 6.780 | Inventory every staircase on every plan with a unique id; continuity floor by floor; architectural flight matched to structural detail; landings never twice with slabs (any villa) | T-184 | investigation |
| 2026-10-22 | Dome lines removed from the BOQ after a client request (Q-29) | A client-requested change applied to the approved-design baseline | Keep approved design (S0), client-requested change (S1) and consultant revision (S2) as separate scenarios; S1 never released as the approved design until S2 exists (any villa, any element) | T-185 | rule recorded (owner 2026-10-22); Alsenan: client request only, consultant revision NOT issued (owner confirmed 2026-10-22) |
| 2026-10-22 | Freelancer corners: an itemised list summed 1,370.85 m.l against his 1,297.35 | The main chat's summary counted the boundary wall's stop-end column (73.65 m.l) twice (once in "stop-ends 547.47", once in "boundary wall 165.09") and rounded 48.15 to 48: 73.65 - 0.15 = 73.50. His workbook: column A 547.47 (formula SUM A51:A90) + column B 749.88 (SUM B51:B92) = 1,297.35, no residual | Reconcile a total from its source cells and formulas, never from a re-typed summary (any workbook) | T-172 | arithmetic explained (main chat, from the workbook cells), accepted by the owner 2026-10-22; physical classification and measurement of the affected items: Checker to verify independently (T-172) |
| 2026-10-22 | "2 m = 1 m" read as corners converted to m2 of plaster | A payment convention (half payable length) read as a physical conversion | Physical, contract, payable, rate and amount kept separate (any trade) | T-172 | rule recorded; test in T-172 (READY d7f81ef), Checker to verify |
| 2026-10-21 | Q-71 option B recommended partly as "more conservative" | Notation meaning not established before rounding | Notation meaning first; N = ceil(L_eff / s_max) + 1 only when "/m" is shown to be a maximum spacing and L_eff is the bar-position length inside the covers (footings only until shown for others) | T-171 | investigation done, READY (a0b23b0): '/m' = maximum c/c spacing, N = ceil(L_eff/s)+1; 2,769.06 .. 2,829.83 kg HELD on the unprinted leg diameter (designer); Checker to verify |

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
