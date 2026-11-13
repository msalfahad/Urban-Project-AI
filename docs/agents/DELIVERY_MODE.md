# DELIVERY MODE (owner 2026-11-13; binds every agent; wins over MISSION.md, TEAM.md, WORKFLOW_CONTROLS and the ENGINEERING_REASONING_STANDARD wherever they differ)

Owner, 2026-11-13: "we have been working on the project for more than 2 weeks and we havent reach a good progress. What
i mean by progress is reaching the level where i can send a project in pdf, dxf, dwg and i get the boq closer or more
accurate to the freelancer excels. Fix the issues and re arrange to reach the progress." And: "I think they are working
a lot of the tiny things thats why there is no progress."

Diagnosis (main chat, from the candidate's own line index): 3 Nov -> 13 Nov the candidate moved concrete +1.6 m3,
formwork +33 m2, added masonry materials, corrected the plaster height; verified whole lines unchanged (2); external
plaster still 0; 39 BOQ families still have no line; 1,350 commits and 530 merges, nearly all censuses, statements,
reconciliations and lessons. The method optimised proof per line, not the BOQ. This file changes the method.

## 1. The goal, in the owner's terms

Drawings in (PDF / DXF / DWG) -> one BOQ workbook out, every trade, every line with a figure, each trade compared with
the freelancer's workbook. Progress is measured ONLY by two numbers per trade: (a) lines in the candidate with no
figure (target 0, rebar excepted), (b) candidate vs freelancer per trade in units and %, every difference labelled
ENGINE_RIGHT / FREELANCER_RIGHT / RULE_DIFFERENCE / UNRESOLVED. The workbook docs/agents/boq/ (built by
docs/agents/boq/build_boq.py from the newest LINE_INDEX_V3_0_*.json) is the scoreboard; a Lead report is 15 lines of
those two numbers per trade. Runs, merges, censuses and lessons are not progress and are not reported.

## 2. Three streams, in this order (dates are targets, not promises)

- FILL (now -> 17 Nov): every line of the Alsenan candidate gets a figure by the fallback order (section 3). Rows
  T-760 .. T-771 on the board, one family group per row; a row is done when its families have 0 blank lines in the
  candidate. External render + paint first (0 today), then concrete blanks, formwork, plaster / paint / tiles, roof +
  earthworks, masonry blanks, stair finishes, waterproofing, openings + ceilings, fence + site, missing families (MEP
  last). Rebar stays parked (owner 2026-11-11): approximate tons at the very end.
- GENERALISE (18 -> 22 Nov): T-772 runs the engine from the drawings end to end (tools/urban_boq_m9.py --arch, then
  tools/boq_export_v1.py) and compares with the workbook; every candidate line that exists only as an Alsenan line-id
  restatement (the arch_v30xx chain) and not as a rule is listed; those rules are written as engine rules tested on the
  synthetic villas. Then T-773: the candidate becomes the released default (owner authorises on the board; nothing
  switches before his word).
- SECOND VILLA (23 -> 27 Nov): T-774 runs development project 2 (finishing-only, DWG + PDF, its freelancer file)
  through the same command; per-trade comparison; generic defects only. Then the owner's blind test.

## 3. How a quantity is obtained (fallback order; owner 2026-11-13 "never stop")

1. drawing geometry (the engine);
2. manual read of the PDF / printed dimensions / hand calculation (dimensions x calculator);
3. COMPANY DEFAULT (BOARD.md "Rules in force": beam depth same mark / adjacent span / 0.60; lintel bearing 0.15;
   schedule governs a column; exterior GB same mark; lift walls 0.20; parapet 1.20; equal risers 0.15-0.175; false
   ceiling = clear height - 0.90 (wet rooms 2.70); floor bed 3.5 cm dry / 5 cm wet; sill 0.90 / 1.60 wet; head = nearest
   printed, else 2.20; roof build-up screed 7.5 cm avg + membrane + 5 cm insulation + 5 cm protection; one WP
   penetration per fixture; plan dimension governs a facade; wardrobe 2.40; kitchen base 0.85 / wall 0.70);
4. ratio or area allowance from THIS villa (formwork m2 per m3 of the same element type; a layer = the area it covers;
   disposal = excavation - backfill; paint = plaster face minus ceiling band and tiles);
5. the safety allowance.
Every line carries its method label: MEASURED / DRAWING-READ / DEFAULT / ESTIMATE / SAFETY. Only MEASURED can become
VERIFIED. A blank line is allowed only while its row is CLAIMED, never as an end state. HELD is never 0.

Materiality (owner 2026-11-13 14:00): a concrete piece KNOWN to be below 0.05 m3 is ignored and logged by line id in
IGNORED_SMALL (docs/agents/boq/IGNORED_SMALL.md); anything larger that geometry cannot read is hand-calculated, never
ignored. Safety line = 1 m3 if the ignored sum is below 1 m3, else the sum. Other units: nothing below 1 % of its line
is investigated. Report to 0.01 m3 / 0.1 m2 / 0.1 lm; never six decimals.

Heights: printed levels govern (FFL +1.00 / +5.50 / +9.70 / +13.90: storeys 4.50 / 4.20 / 4.20). Plaster height =
storey - slab thickness (4.34 GF, 4.04 upper floors; owner 2026-11-13). Paint = plaster face - band above the false
ceiling - tiled faces; edges and corners in lm (owner 2026-11-12).

## 4. One run, one family group (workers)

1. Claim the row (board commit). Hand-in point: 50 minutes after STARTED, whatever is done (READY rN), never an IDLE
   overrun into the next slot.
2. For every line of the family group: apply the fallback order, write the figure, the label and the one-line basis
   (dimension chain or default id) into the row's fix-row JSON (research/agents_t<ID>/out/FIX_ROWS.json: line id, item,
   unit, before, after, label, basis). No census, no statement, no lessons row, no new rule version unless the owner rule
   itself is new (then ONE rule file + ONE test with a normal and an adverse case).
3. Validate: the builder's own check, targeted tests of any module changed, freeze check 0. Not the full suite.
4. Hand in: READY, handoff <= 600 characters = the two numbers of section 1 for the family group (blank lines before /
   after; vs freelancer where a reference row exists). Worker 3 wires READY fix-row sets into the candidate (T-770),
   up to three family groups per package, the next ARCH_TAKEOFF_V3.0.x number written in its Branch cell at claim time
   (version reservation, owner 2026-11-11); a clash means the later package waits, never renumbers mid-run.

## 5. Checker (Verifier) in delivery mode

- Gate A (a fix-row set): no frozen or version-file edit, no weakened test, no client data; freeze 0; the labels and
  bases present on every line; THREE lines re-measured by hand (random, the largest included). PASS or REJECT within
  the run; no rework for differences below materiality.
- Gate B (a wiring package): freeze 0; targeted tests of the changed modules; every line outside the package
  byte-identical; the export tool runs; the workbook rebuilt (build_boq.py) and committed to the board with the
  verdict. The FULL suite runs ONCE a day, in the 04:50 slot only, in the background; a failure becomes a fix row.
- Scoreboard = the per-trade table of section 1 only (candidate vs freelancer, lines without a figure). No restatement
  of superseded versions.
- Merge in the same run as the PASS; publish with `engine push`; write MERGED only after `ls-remote` shows the sha.

## 6. Lead in delivery mode

- Reads: this file, BOARD.md "Rules in force" + the live rows, LEAD_STATE.md, RUN_LOG.md since its last run. Nothing
  else unless a row needs it.
- Creates rows ONLY from: (a) a family with blank lines in the newest workbook, (b) a trade whose freelancer difference
  is unexplained, (c) a Checker fix row, (d) streams G and S when FILL is done. Never a census, statement,
  reconciliation, readiness, manifest or lessons row. Every row names the families, the method step expected and the
  acceptance "0 blank lines in <families>".
- Keeps every worker queue 3 rows deep; no idle slot. Report: 15 lines, the two numbers per trade, then blockers.
- Owner questions: only a contradiction between two printed drawings or a missing safety-critical design, in the
  section 6 format of the standard; everything else takes a default and is labelled.

## 7. Owner-only items (the main chat cannot change these)

- Scheduled-task frequency: recommended Workers every 2 h, Checker every 2 h, Lead every 4 h (today hourly / hourly /
  2 h): same output per day at half the usage, now that each run is one family group with a 50-minute hand-in.
- The designer list (DESIGNER_QUESTIONS.md, 18 items): sending it turns DEFAULT lines into DRAWING-READ lines.
- Google Drive must be connected for manual PDF reads; the repository privacy switch and the freelancer workbooks
  (floors, railings) are still open.
- Authorising the release switch (T-773) and the blind-test villa.
