# AGENT BRIEF (every run reads this; everything else is reference only)

At most 6 KB; owner words win over this brief. Since 2026-11-13 the team runs in DELIVERY MODE: read
DELIVERY_MODE.md first; it wins over MISSION.md, TEAM.md, WORKFLOW_CONTROLS and the reasoning standard wherever they
differ. Authoritative registers: OWNER_QUESTIONS_ANSWERED.md (grep the Q-id), OWNER_SESSION_CHANGES.md, progress.md.

## Goal and the only two progress numbers (owner 2026-11-13)
- Drawings (PDF / DXF / DWG) in -> one BOQ workbook out, every trade, every line with a figure, each trade compared
  with the freelancer. Per trade: (a) lines with no figure (target 0; rebar parked), (b) candidate vs freelancer in
  units and %, each difference labelled ENGINE_RIGHT / FREELANCER_RIGHT / RULE_DIFFERENCE / UNRESOLVED.
- Streams: FILL (rows T-760..T-771, to 17 Nov) -> GENERALISE (T-772, T-773, to 22 Nov) -> SECOND VILLA (T-774).
- The workbook docs/agents/boq/ (build_boq.py on the newest LINE_INDEX_V3_0_*.json) is the scoreboard.

## Hard rules (one line each)
- NEVER STOP: geometry -> manual PDF / hand calc -> company default -> ratio / area allowance -> safety; every line gets
  a figure with its label MEASURED / DRAWING-READ / DEFAULT / ESTIMATE / SAFETY; a blank line is never an end state.
- Materiality: a concrete piece KNOWN < 0.05 m3 is ignored and logged (IGNORED_SMALL); larger unread pieces are
  hand-calculated; safety line = 1 m3 if the ignored sum < 1 m3, else the sum; other units: nothing below 1 %.
- One run = one family group; hand in at 50 minutes (READY rN); handoff <= 600 characters = the two numbers.
- No census, statement, reconciliation, manifest, readiness or lessons rows. A new owner rule = ONE rule file + ONE
  test (normal + adverse). Validation = builder check + targeted tests + freeze 0; the full suite once a day (Checker).
- HELD is never 0 and never dropped. Only MEASURED becomes VERIFIED. Never edit a frozen file or a version file in
  place. Never switch the released default without the owner's word on the board (T-773).
- No client data, names, drawings or personal data in the repo; Drive is read-only; decode only through the wrapper.
- Times come from `date -u`. Rebar is PARKED (owner 2026-11-11): no rebar rows; approximate tons at the end.

## OWNER CONFIRMED rules (id | value | source)
| id | value | source |
|---|---|---|
| Company defaults | beam depth same mark / adjacent span / 0.60; lintel bearing 0.15 each side; schedule governs a column; exterior GB = same mark; lift walls 0.20, lift tie = nearest printed; parapet 1.20; equal risers 0.15-0.175, tread 0.28-0.30; false ceiling = clear height - 0.90 (wet rooms / kitchen 2.70); floor bed 3.5 cm dry / 5 cm wet; sill 0.90 (wet 1.60); head = nearest printed else 2.20; wall under a dome to the ring-beam soffit; sunken wet room: recess + 0.30 up; roof: screed 7.5 cm avg + membrane + 5 cm insulation + 5 cm protection; one WP penetration per fixture; plan dimension governs a facade; projecting beam ends = concrete of the beam; wardrobe 2.40; kitchen base 0.85 / wall 0.70; drainage runs at MEP | owner 2026-11-13 (DEFAULT label; replaced by the designer's answer) |
| Heights | printed FFLs govern: storeys 4.50 / 4.20 / 4.20; plaster = storey - slab thickness (4.34 GF, 4.04 upper); paint to the false ceiling; stair shafts full exposed height | Q-72, owner 2026-11-02 / 2026-11-13 |
| Paint area | = plaster area of the same faces, inside and outside, minus the band above a false ceiling and minus tiled faces; corners and window / door edges are lm items | owner 2026-11-12 |
| Plaster / render / spatter mix | internal plaster 1:4, external render 1:4, spatter dash 1:2 | Q-79, owner 2026-11-09 |
| Black blocks | 12.5 per m2, 40 x 20 face, 20 cm and 15 cm blocks; waste separate | Q-75, Q-80, owner 2026-11-07 |
| Black-block mortar | 1:4 (about 8 x 50 kg cement + 1.1 m3 sand per m3) | Q-78 |
| White AAC glue | 25 kg bag: 15 cm block 3.5 kg/m2, 20 cm block 4.5 kg/m2 | owner 2026-11-02 |
| Lintels | precast 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m; min 15 cm bearing each side; shortest standard length that fits; one per opening; over 4.00 m FLAGGED; a printed RC schedule governs | owner 2026-11-02, F-T644-1 |
| Tile adhesive | 20 kg bag: 60x60 5 m2; 120x60 3 m2; 160x80 3 m2; ceil per purchasing group; waste separate | Q-45 |
| Tile bed | 3-4 cm floors, 4-6 cm bathrooms, 1:4 (default 3.5 / 5 cm) | Q-45, owner 2026-11-13 |
| Wet-area walls | spatter dash + levelling render + adhesive and porcelain; no second bed; no paint or skirting on tiled faces | owner 2026-11-02 |
| Openings | full deduction of every actual opening from blockwork | Q-73 |
| Backfill | max 150 mm finished compacted lift, OWNER-PROVISIONAL; drawings / geotechnical spec govern where they differ | owner 2026-11-02 |
| Wet-room wall tiles | 3.00 m high from F.F.L. in every wet room (replaces the decor-ceiling tie for tile height only) | owner 2026-11-13 |
| Rebar | BOQ figure = ratio 120-140 kg per m3 of structural concrete (ESTIMATE, never VERIFIED); the detailed takeoff continues as a parallel check that must converge on it; no rebar rows for workers | owner 2026-11-11 / 2026-11-13 |

## Checker gates (DELIVERY_MODE.md section 5)
- Gate A (fix-row set): no frozen / version-file edit, no weakened test, no client data; freeze 0; labels and bases on
  every line; three lines re-measured by hand (the largest included). No rework below materiality.
- Gate B (wiring package, up to three family groups): freeze 0; targeted tests; lines outside the package byte-identical;
  export runs; workbook rebuilt and committed with the verdict; MERGED only after `ls-remote` shows the sha.
- Full suite once a day (04:50 slot, background); a failure becomes a fix row.

## Lead duties (DELIVERY_MODE.md section 6)
- Rows only from: blank lines in the newest workbook, an unexplained freelancer difference, a Checker fix row, streams
  G / S after FILL. Each row: families, expected method step, acceptance "0 blank lines in <families>".
- Queues 3 deep per worker; `board check` clean; LEAD_STATE.md <= 5 KB; report 15 lines = the two numbers per trade.

## Drive (read-only): ids in progress.md section 1
