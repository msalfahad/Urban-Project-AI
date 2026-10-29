# T-331: integration package, ARCH_TAKEOFF_V3.0.22 = V3.0.21 + the WET-ROOM PLASTER BACKING (Gate B)

Worker 3 (lane I), claim 2026-10-29 09:01 UTC. **Integration package** for Checker Gate B. integrates: T-329 (MERGED
1c82807b, the backing ledger), T-312 (MERGED 8943b5ed, the openings by their part in the band), T-315 r2 (MERGED
b0041dd2, the wall-tile lines the backing is bound to). Opt-in candidate only: the released default stays ARCH_TAKEOFF_V2.9
+ route G; nothing here is RELEASED and nothing is VERIFIED by this package. ERS applied: s.2.1 (physical element
first), s.2.2 (owner manual and drawing-derived methods side by side), s.2.4 (reconciled in m2), s.2.7 (no owner
question: the answered rules decide it), s.3 (one face, one owner per layer; installed vs procurement), s.4 (rule +
normal and adverse tests), s.7 (lesson row, section 9).

## 1. The physical element and the rule (not re-derived: T-329 Gate A PASS)

Behind a wall tile is ONE layer of its own: the 20 mm 1:4 cement-sand backing coat (UP-FIN-PAINT-001 logic
`substrate`: the substrate / plaster behind porcelain is its own line; Q-45 B: wall mortar behind wall tiles 0.02 m,
1:4, PROVISIONAL), then the adhesive (its own line), then the tile. It covers exactly the TILED faces, floor to tile
top, less the same openings by the same parts as the tile, so **backing - tile = 0 on every face**. The band of
plaster ABOVE the tile top is a separate question: owner method 0 (Q-43 plaster height = Q-48 A tile top);
drawing-derived = the 0.15 decor zone x face length, HELD (Q-52 C: no specification prints whether plaster runs above
the ceiling). The coat's mortar (m2 x 0.02 = 6.806 m3) is procurement of the same layer (FINISH_MATERIALS_TABLE_V1
WET_WALL), never a second quantity.

## 2. What the module does (engine/source/arch_v3022.py, one piece + a note completion)

- **FILL** (12 lines): a blank FIN.PLASTER line (BLOCKED_RFI, no figure) of a tiled room takes the ledger figure, same
  line id, state PROVISIONAL, evidence ASSUMED — OWNER-APPROVED with its full owner source on the line
  (UP-FIN-PAINT-001, Q-45 B, Q-43, Q-48 A, Q-55 C). The record is **bound to the room's own FIN.WALL.TILE line in the
  run**: its faces must equal that tile line's faces (ids, lengths, heights, openings, nets) face by face, and a
  blank tile line cannot be backed (a held line is never filled). Each filled line carries `gross` (sum of length x
  height), the **canonical `deductions` list** (each opening by id, m2, unit, face: the T-330 format; gross -
  deductions = net) and the **HELD band beside the figure** (calculation.inputs.wet_backing_v3022.band_above_tile,
  formula and notes: owner method 0.0 m2; drawing-derived 0 .. high HELD, NOT RELEASED).
- **HELD** (6 lines): stay BLANK (BLOCKED_RFI, no figure, no range, never 0); only a note and a calculation record are
  added: the item that holds them (G2 / Q-54 B / D-39; T-088), that the backing is its own line, and the drawing band.
- **KEEP** (1 line): the superseded pantry room record GF-RC06FED:plaster (L-6470c6f2) is asserted to stay
  NOT_APPLICABLE_WITH_EVIDENCE (T-211 SUPERSEDE: the pantry backing is booked once, on the room-face line).
- **NOTE_COMPLETION** (2 lines, Checker cosmetic note 07:50): the base-rule text cut at '(Q-37 A / Q-4)' in the notes
  of L-af6fb2d3 / L-71e2e002 is completed from the line's own calculation.inputs.base_ownership_v3021.assumption (the
  cut fragment must be its exact prefix; notes only). The same truncation in L-71e2e002's `deductions[].what` text is
  not touched (outside the cosmetic note; quantity fields unchanged).
- Cross-trade (V3_0_22_CROSS_TRADE.csv, per room): tile + backing on one face = two layers by rule; the room's paint
  lines stay 0 **by rule** (UP-FIN-PAINT-001, named on every filled line); a paint figure on a backed room is refused.
- Refused (tests): band written as 0 / as a bare number / missing / a range not HELD; backing on a paint line; a held
  line filled; a HELD record with a figure; one face backed twice; a face differing from the tile face; backing != tile
  on a face; mm height; a tile line of the run with no record; a stale (valued) plaster line; declared drift; a paint
  figure on a backed room. Inside a FILL line only quantity, state, rfi, gross, deductions, geometry confidence,
  calculation and notes change; inside a HELD / NOTE line only notes and calculation (quantity asserted equal); every
  other line byte-identical to V3.0.21 (asserted on every run); the default guard (V3.0.7 inputs, unchanged) re-runs.

Wiring: tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.22 --v3022-inputs` (additive; every earlier method list
gets V3022, nothing else changes). Inputs: research/agents_t331/t331_inputs.py reads only the merged T-329 / T-312
CSVs and pins them (12 FILL 340.3038 m2, 11 wet 307.9616, pantry 32.3422, 6 HELD, 115 faces, band high 23.0970 /
16.2125): an edited ledger stops the build.

## 3. Run and identity (own run, Python 3.11.18)

Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and "ST7757 dxf.dxf" (`9f9d1179`),
decoded into the private folder only: research/agents_t167/v304_run.py (24 min), then research/agents_t331/v3022_run.py
(one CLI process, 9 min), every earlier version reproduced on the way: **V3_0_19 json `b35475bf` / csv `ef63b73b`,
V3_0_20 json `097a80b6` / csv `ca90351b`, V3_0_21 json `be22a4e4` / csv `3548e39c` = the candidates of record**
(T-255 / T-244 / T-315 r2 Gate B). Final hashes of V3_0_22 on the task head: section 10.

Identity (V3_0_22_RUN.json): 3,706 lines = 3,706 (added 0); replaced 20 = 12 FILL + 6 HELD (text) + 2 NOTE (text);
outside rows 3,686 identical to V3.0.21 (asserted); DIFF vs V3.0.21: SAME 3,686, CHANGED 12 (quantity), CHANGED_TEXT_ONLY
8, ADDED 0, GONE 0. Totals moved by code: ONLY FIN.PLASTER|m2 (blocked lines 21 -> 9, live 234.9481 -> 575.2519 m2;
bounded range 489.481 .. 545.4606 unchanged). FIN.WALL.TILE unchanged (18 lines, 12 valued 340.3038 m2, 6 blank);
FIN.PAINT unchanged 217.2081 m2; FIN.SKIRTING unchanged. Default guard over the 3,706 lines: findings by code
identical to the V3.0.21 run (CONVENTION_WHERE_PRINTED 87, PARTIAL_FOOTPRINT 2, PRINTED_VALUES_DISAGREE 75,
SEARCH_INCOMPLETE 1,039), no change to any line, none on a filled line.

## 4. Line by line (before V3.0.21 -> after V3.0.22; released V2.9; freelancer)

Owner manual method = tiled face length x tile top (Q-43 = Q-48 A: GF 3.65, 1F / 2F 3.35) - each opening's part
inside (doors 2.20 head Q-55 C, windows by printed heads T-201) + owner band 0. Drawing-derived beside on every line:
backing HELD as the tile (roof datum DCR-6, sunken panels, build-up b), band 0 .. high HELD. Every line below moved
from blank (>= 5 % rule) and each valued line is >= 2 % of the family's live total: all are hand-check lines for Gate B.

| Room | Line | V2.9 | V3.0.21 | V3.0.22 (m2) | Band beside: owner / drawing (HELD) | Evidence | Freelancer (his wet-wall area) |
|---|---|---|---|---|---|---|---|
| 1F-02 | L-3eba04f2458578e7dc19 | BLOCKED_RFI | BLOCKED_RFI | 27.9101 | 0 / 0 .. 1.3500 | OA | 27.00 (+3.37 %) |
| 1F-03 | L-9473c0c6ce4e11e4d162 | BLOCKED_RFI | BLOCKED_RFI | 27.9100 | 0 / 0 .. 1.3500 | OA | 26.70 (+4.53 %) |
| 1F-07 | L-2948639faa08fa1cff81 | BLOCKED_RFI | BLOCKED_RFI | 52.5290 | 0 / 0 .. 2.5410 | OA | 50.55 (+3.91 %) |
| 1F-08 | L-005cb3310fbebd97d563 | BLOCKED_RFI | BLOCKED_RFI | 19.6691 | 0 / 0 .. 0.9811 | OA | 19.44 (+1.18 %) |
| 1F-09 | L-5e5e62e91688eebfb285 | BLOCKED_RFI | BLOCKED_RFI | 23.2201 | 0 / 0 .. 1.1399 | OA | 22.80 (+1.84 %) |
| 1F-12 | L-12b83d399be186804faf | BLOCKED_RFI | BLOCKED_RFI | 26.3051 | 0 / 0 .. 1.3049 | OA | 26.10 (+0.79 %) |
| 2F-02 | L-bec624729c89553f720f | BLOCKED_RFI | BLOCKED_RFI | 30.2550 | 0 / 0 .. 1.4550 | OA | 29.25 (+3.44 %) |
| GF-12 | L-2b9a85e1bedf161c0c21 | BLOCKED_RFI | BLOCKED_RFI | 25.3011 | 0 / 0 .. 1.1120 | OA | 22.20 (+13.97 %) |
| GF-13 | L-302f7235046bbe0b6c09 | BLOCKED_RFI | BLOCKED_RFI | 22.6165 | 0 / 0 .. 1.0214 | OA | 20.10 (+12.52 %) |
| GF-14 | L-910672305a87544d4d72 | NOT_IN_RELEASED | BLOCKED_RFI | 26.6544 | 0 / 0 .. 1.2399 | OA | 28.50 (-6.48 %) |
| GF-16 | L-ccc97166c57999d5a303 | BLOCKED_RFI | BLOCKED_RFI | 25.5912 | 0 / 0 .. 1.1437 | OA | 22.80 (+12.24 %) |
| GF-07 pantry | L-721a0f1441436193978c | NOT_IN_RELEASED | BLOCKED_RFI | 32.3422 | 0 / 0 .. 1.5736 | OA | none (SCOPE) |
| GF-02 | L-2211463bba5eeb2e4282 | NOT_IN_RELEASED | BLOCKED_RFI | BLANK (HELD: G2 / Q-54 B / D-39) | 0 / 0 .. 1.0799 | HELD | 21.60 (not compared) |
| GF-03 | L-f43782d52f32b53a6f1e | BLOCKED_RFI | BLOCKED_RFI | BLANK (HELD: G2) | 0 / 0 .. 1.1250 | HELD | 22.50 (not compared) |
| GF-05 | L-f179fc08a266294ad4a4 | BLOCKED_RFI | BLOCKED_RFI | BLANK (HELD: G2) | 0 / 0 .. 0.8398 | HELD | 16.74 (not compared) |
| GF-06 | L-595181aa140e7efb2ac7 | BLOCKED_RFI | BLOCKED_RFI | BLANK (HELD: G2) | 0 / 0 .. 2.1749 | HELD | 43.05 (not compared) |
| GF-10 | L-3f7fb1b37e68e6d6c7b7 | BLOCKED_RFI | BLOCKED_RFI | BLANK (HELD: level T-088) | 0 / 0 .. 0.9299 | HELD | 18.60 (not compared) |
| GF-11 | L-a636dabcd4bc7e59169a | NOT_IN_RELEASED | BLOCKED_RFI | BLANK (HELD: level T-088) | 0 / 0 .. 0.7350 | HELD | 15.90 (not compared) |
| (kept) | L-6470c6f20f86e542a5ce | - | NOT_APPLICABLE | NOT_APPLICABLE (kept) | - | - | - |
| skirting note | L-af6fb2d3474c5fbdb80a | 1.9 lm | NOT_APPLICABLE | NOT_APPLICABLE (note completed) | - | OA | - |
| skirting note | L-71e2e002a3af624097f0 | 28.1716 lm | 24.6716 lm | 24.6716 lm (note completed) | - | OA | - |

**Family FIN.PLASTER (m2):** V2.9 live 17.74 (27 blocked) -> V3.0.21 live 234.9481 (21 blocked) -> **V3.0.22 live
575.2519 (+340.3038, 9 blocked)**; bounded range 489.481 .. 545.4606 unchanged; **beside it, the band above the tile:
owner 0.0000, drawing-derived 0 .. 16.2125 on the 12 filled lines + 0 .. 6.8845 on the 6 held = 0 .. 23.0970 HELD**,
never added to the live figure and never written as 0. Evidence split of the +340.3038: ASSUMED — OWNER-APPROVED
340.3038, VERIFIED 0, DRAWING-CONFIRMED 0 (faces DRAWING-CONFIRMED through T-250 / T-312; heights and door heads OA).

**Hand checks (own, from the merged ledger figures, not the engine):** GF-13 = 6.81 x 3.65 = 24.8565 - D-GF-12 1.760 -
W06 0.480 = 22.6165 (line 22.6165); 1F-07 = 16.94 x 3.35 = 56.7490 - doors 3.740 - window 0.480 = 52.5290 (line 52.5290);
pantry = gross 38.29215 - D-GF-06 2.20 - W09 2.25 - W10 1.50 = 32.34215 (line 32.3422, 0.00005 = 4-dp rounding).

**Engine vs freelancer (11 wet rooms both carry, m2):** backing 307.9616 vs his wet-wall area 295.44 = +12.5216
(+4.24 %) = length -2.652 + height +43.193 (owner 3.65 / 3.35 vs his flat 3.00) + doors -23.100 + windows -4.920 +
residual 0.0002 (T-329 RECONCILIATION). He prices NO plaster on wet walls; his row of that area is a spatter-dash coat
(a separate layer). Verdict proposals (unchanged from T-329): element RULE_DIFFERENCE (UP-FIN-PAINT-001: the backing is
its own line), height RULE_DIFFERENCE (Q-43 / Q-48 A vs 3.00 printed nowhere), openings ENGINE_RIGHT (the coat stops at
the hole), pantry scope ENGINE_RIGHT (UP-PANTRY-003 host walls, 32.3422 vs none).

## 5. Export integrity (T-330 check, MERGED 16fa5f72 during this run; merged into this branch)

tools/t330_deductions_check.py `check` on V3.0.21 (be22a4e4) and V3.0.22: categories V3.0.21 OK 62 / FLAG 41 /
REFUSED 0 -> V3.0.22 OK 74 / FLAG 41 / REFUSED 0. FIN.PLASTER: checked 4 -> 16, OK 0 -> 12, FLAG 4 -> 4. **The 19
mapped lines: 12 OK (gross - canonical deductions = net, every opening named), 7 NOT_APPLICABLE (6 HELD blank + the kept
superseded record), 0 FLAG.** The 4 remaining plaster flags are the pre-existing room-face lines HL:WALL_FINISH (empty
canonical list; the next lane I fill named in T-330), not touched here. Test:
tests/t331_wet_backing_integration (the merged check reads the fixture's filled line OK and its held line
NOT_APPLICABLE).

## 6. Missing, held, downstream

- HELD (never 0): the 6 annex / undrawn-level rooms' backing (with their tile: G2 / Q-54 B / D-39; T-088); the band
  above the tile on all 18 rooms (Q-52 C specification).
- Not in this line (named): coat mortar 6.806 m3 = procurement of the same layer (never priced twice); adhesive (own
  line, Q-45 B 20 kg / 5 m2); spatter-dash coat on wet walls (URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1, carrier not
  settled); opening reveals (T-313 / T-326).
- Downstream: the SCOREBOARD CLOSABLE row 3 ("17 wet-room plaster lines blank") becomes 12 lines carried / 6 HELD by
  name, to be restated by the Checker from the lines; the export now reads gross - deductions = net on these lines.

## 7. Regression and validation

- tests/t331_wet_backing_integration (villa W331 hand fixture, not Alsenan: bath B1 19.56 m2 = tile, gross 21.60,
  deductions W1 0.36 + D1 1.68, band 0 / 0 .. 5.22 HELD; held bath BLANK with band 0 .. 4.00; dry living untouched;
  adverse: band as 0 / bare number / missing / not HELD, backing on a paint line, held line filled, HELD with a
  figure, face twice, face != tile face, backing != tile, mm height, tile line without record, stale plaster line,
  paint figure on a backed room, declared drift; mirror order; note completion and an already complete note refused;
  Alsenan input pins incl. the 1F-12 hand check and an edited ledger stopping the build; master 1.17.0 equals its
  builder and checks clean, dropping the entry is stale, a family naming it refused).
- tests/t315_wall_tile_family, tests/t329_wet_backing, tests/t212_guard_property: pass (section 10).
- L4 full suite: section 10. Freeze 0 differing; codemap stale none; rules manifest drift none.

## 8. For the Checker (Gate B)

Re-measure (WORKFLOW_CONTROLS s.1): every one of the 12 filled lines is a hand-check line (moved from blank, each >= 2 %
of the family); suggested own re-measures GF-13 (6.81 m contour) and 1F-07 (16.94 m), plus the pantry deductions by
id; the 6 HELD lines stay blank; the band record on every line (owner 0, drawing range = the T-329 room figure); the
two note texts; the binding: each filled line's faces = its tile line's faces (`wet_backing_v3022.tile_line_id`);
plus 2 random lines by the s.1 rule on the merge-candidate sha. Quick re-run: research/agents_t331/v3022_direct.py on
a finished V3.0.21 run (same module functions, same files).

## 9. Lessons-register proposal (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-29 | An integration that fills a layer behind another trade's line can drift from it (a backing figure that is not the tile's faces, a band carried as 0, or the band hidden), and a fill that cuts its own owner source in the note repeats the cosmetic defect it fixes | the layer was a free-standing figure, not bound to the line it lies behind; notes were truncated to fixed lengths | a layer behind a finish is bound face by face to that finish's line in the same run (faces equal, a blank host refuses the fill); its unresolved companion quantity (the band) travels beside the figure as a HELD range, never 0, never added; owner sources are written in full (every villa) | tests/t331_wet_backing_integration (face != tile face, backing != tile, held host filled, band as 0 / missing all refused; note completion) | PROPOSED |

## 10. Final run and validation on the task head

- **Full CLI run (v3022_run.py, one process) on the merged head f3bc2779** (task commits + the working branch with T-330
  MERGED 16fa5f72): V3_0_19 json `b35475bf`, V3_0_20 json `097a80b6`, V3_0_21 json `be22a4e4` / csv `3548e39c`
  (= the candidate of record, reproduced), **V3_0_22_BOQ_LINES json `7199c8b6` / csv `924a60b4`**, DIFF `68e643b3`,
  FACES `3fcc9791`, INTEGRATION_LEDGER csv `95ab68ed` / json `4ba9ff3a`, CROSS_TRADE `76878470`, RUN `63f3f92a`:
  byte-identical to the run on the pre-merge head e24f5201 and to v3022_direct.py on the same V3.0.21 run.
- **L4 full suite (every folder under tests/, one session) on 2f38cf9e**: 14,396 passed, 363 failed, 32 errors, 219
  skipped, 105 xfailed; the 395 failing / error ids re-run on the base head 1c82807b (the working branch before this
  package, .work/engine): all 395 fail there too, **NEW 0** (comm of the two id lists empty). They are the known
  private-input and environment failures (Qortuba / Alrashed private-workpaper suites test_pa08_* / test_pa09_*, the
  rebuild packages that need private drawings, the r8_* import-boundary checks, one control-plane gate) - the same
  395 T-315 reported. The later commits (e24f5201: the note carries the full owner source, the V3.0.7 guard inputs,
  the held band basis text; the merge of T-330; f3bc2779: report + one test) were validated at L3 on f3bc2779:
  tests/t331_wet_backing_integration (32), t315, t329, t330, t212, t061, m9_s6, m9_s5, m9_s4, m9_kb, m9_s3, m9_p2b0,
  m9_p2a, m9_p2b2, t240, t255, t244_finish_revision, t312: all pass.
- Freeze 0 differing; codemap stale none (maps by the tool, last); rules manifest drift none; master 1.17.0 equals its
  builder, FMC problems none.
- self-gate: a c d f h PASS (a: only the integration module, runner wiring, registry version file, manifest, research
  and tests/t331_*; no frozen / rule / knowledge file edited, no client data, no coordinate in tracked files; c:
  freeze 0, maps by the tool; d: hand fixture W331 not Alsenan with adverse cases, missing never 0; f: every other
  line byte-identical, held stays held; h: each layer one owner by face, paint 0 by rule, mortar not a second
  quantity).
