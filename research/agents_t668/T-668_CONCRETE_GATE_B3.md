# T-668 CONCRETE GATE B ROUND 3: integration package ARCH_TAKEOFF_V3.0.64 (junction squares, boundary band, pool blinding)

Worker 3 (lane I), 2026-11-10, branch `agents/task-T-668`. **Integration package for Checker Gate B.** Opt-in
candidate only: the released default V2.9 + route G is untouched; nothing is released; no rule, owner decision or
frozen file changes. Development villa, not an accuracy claim. ERS s.2-5, WORKFLOW_CONTROLS s.1 / s.5, UP-QTY-STATUS-001.
Base: the published T-665 merge (V3.0.63, Gate B PASS, b5df949c), then the working branch with T-670 (91a74d45) and
T-669 (8cb64551, merged 09:56 during this run) merged in.

## 0. What was wired, from what

| Source (Checker-merged) | Merge | Checker run | Lines | Wired as |
|---|---|---|---|---|
| T-666 ledger (`research/agents_t666/out/T666_LEDGER.json`, sha 99a906c2) | 06e2e736 | Verifier 2026-11-10 05:56 Gate A PASS (own DXF: 3 of 5 lengths, band under 4 stretches) | 5 + band | 5 beam pieces BOUND to the drawn lengths with their junction-square owners; band owned once (levels disjoint) |
| T-659 ledger (`research/agents_t659/out/T659_LEDGER.json`, sha 50e51242) | 907ace46 | Verifier 2026-11-09T21:54Z Gate A PASS | 1 | band bound 5.6392 .. 11.0328 |
| T-667 ledger (`research/agents_t667/out/T667_LEDGER.json`, sha 4adfc23d) | b89ea23f | Verifier 2026-11-10 05:05 Gate A PASS (own pool outline / overlap) | 2 | NEW pool blinding line (ADD_LOWER_ONLY); pool steps CONFIRM |
| T-669 ledger (`research/agents_t669/out/T669_LEDGER.json`, sha e3f2dd96) | 8cb64551 | Verifier 2026-11-10 09:56Z Gate A PASS (own DXF corner re-read) | 1 + 2 | F-T665-1 corner square: BAND0012.1 LOWER_ONLY floor restated; BAND0012.2 / BAND0015 CONFIRM |
| T-665 line index V3.0.63 (`research/agents_t665/out/LINE_INDEX_V3_0_63.json`, sha cd062bfe) | 12acd3d4 | (binding) | 5,073 | binding, asserted again on the live run |
| T-469 downgrade snapshot (sha 81732639): DG-6dd9f1caba1ca77d (Verifier 2026-10-30, 1 line, APPLIED on V3.0.63) | (binding) | | 1 | materialised whole (R-T665-1 (g)) |

**Findings made while binding the ledgers to the CANDIDATE (T-661 / T-665 lesson):**

1. **The band L-6290a9f3 is RELEASED 7.2204 m3 in the candidate** (60.17 m x 0.20 x 0.60, one plot side lost) and HELD
   only at export by the Checker downgrade DG-6dd9f1caba1ca77d (content-bound, 1 line, engine_qty 7.2204). The T-666 /
   T-659 ledgers and the line index read it as HELD 7.2204 .. 7.2204. Restated under R-T665-1 (g): RELEASED -> HELD
   BOUNDED 5.6392 .. 11.0328, the downgrade (its only line) materialised and kept in the record; after the change it
   is STALE_CONTENT with nothing left to hold (census V3.0.64 confirms).
2. **F-T668-1 (T-669 ledger):** `a_corner_square.owner.line_id` = `L-6bf14711ae0b84d0f8b9` is NOT a candidate id (typed
   in `t669_alsenan.py` L_OWNER); the census row of the same ledger carries the real id `L-6bf14711798e5af93594`
   (BAND0012.1, same 10-character prefix and member). Bound by the census row; the builder asserts prefix + member +
   both floors. No quantity effect; the T-669 ledger is left as merged (lane S may correct its constant).
3. **F-C-T667-1 (Checker residual 0.00005 m3 on the pool floor):** the ledger's 0.915529 is wired and the METHOD stated:
   the shared pit-layer area 2.695761 m2 is the T-597 integral that values the VERIFIED pit line itself, so the
   netting uses the same measure as the line it nets against; the Checker's sampled 0.915479 is beside the line.

Not wired, named (never 0): T-669 (b) roof-column lower ends (5 2F columns 1.6362 .. 2.295 m3, R-T669-2: a lane I row;
the 6 upper-only column lines keep their V3.0.63 state); F-C-T669-1 (9th 2F column outline 778) and F-C-T669-2 (49
HELD STR.CONC lines outside B10: lintels B9-02, stairs B7-12) are Lead items.

## 1. One physical element once (ERS s.2.4)

- **Junction squares (R-T666-1, R-T669-1).** Each 0.20 x 0.20 (0.30 x 0.30 at the annex) square has ONE owner, named in
  the line record and asserted across all entries (a square two entries claim is refused): 4 piece ends (BAND0008.1 /
  0011.1 south, BAND0006.1 SW, BAND0001.3 NE) owned by their piece; 3 crossing squares inside columns 418 / 41E / 424
  owned by the column lines L-53f223b0 / L-33a9b772 / L-c10e2945 (UP-CONC-JOINT-001, CONFIRM: HELD blank, unchanged);
  1F BAND0005.1's B23 square owned by the released span L-5ca0573b (1.11375 = 3.30 x 0.45 x 0.75, bound, not touched);
  annex SE corner owned by BAND0012.1 (its neighbours BAND0012.2 / BAND0015 CONFIRM).
- **Band vs building G.B (R-T666-2).** The band is drawn under all four building stretches (43.60 m centre line); the
  band line bills the foundation-level prism, the G.B lines the N.G.-level prisms: disjoint, deduction 0, nothing
  removed, nothing counted twice.
- **Pool blinding vs the 6 baseline blinding lines (T-667 ledger, Checker-checked).** Footing (pit) layer L-98eb2d58
  (RELEASED 12.734438, bound): 2.695761 m2 under the pool (F8 1.931845 + F4 + FN) is ONE layer, netted out of the new
  line. FF lift raft L-16b95607, F10 + F L-080c97f5, straps L-35382b18, ground beams L-7a5214a3 (nearest 0.4998 m),
  boundary base L-d0313e5d (band stops at the pool back): NOT TOUCHED. Beyond the plot line L-10032bf9: same designer
  item D-14, the pool's own strip 0.037 m3 is beside the new line, not in either. **F4 under the pool (T-667 handoff)**
  is inside the 2.695761 netted share. Pool steps L-b62a7065: HELD blank, CONFIRM.

## 2. Owner manual method beside the drawing-derived method

| Element | Owner / freelancer manual method | Drawing-derived method (wired) |
|---|---|---|
| Unlabelled beam piece | face-to-face length x one section | drawn edge length to the square it owns x 0.20 x 0.40 .. 1.20 (R-T660-2, R-T666-1) |
| Boundary band | B.W 20x60 over the run (freelancer 71.7 m x 0.20 x 0.60 = 8.604) | 70.49 m free x 0.20 x 0.40 .. 91.94 m closed x 0.20 x 0.60 (T-659) |
| Pool blinding | none (a plot plate) | grown base in plot 11.851050 m2 - pit share 2.695761 m2 = 9.155289 m2 x 0.10, AT_LEAST (projection C4, levels C6) |
| Annex SE corner | one section x span | span to the outer corner 1.50 x 0.30 x 0.25 literal floor (D-35 high open) |

## 3. Evidence status (WORKFLOW_CONTROLS s.5)

- VERIFIED: none new. DRAWING-CONFIRMED bounds, HELD: 5 beam pieces, the band.
- HELD blank with the drawn floor beside: NEW pool blinding (AT_LEAST 0.915529), BAND0012.1 (AT_LEAST 0.1125).
- Beside, never in a range: 0 .. 0.014 (NE corner gap) and 0 .. 0.0405 (1F piece under B23).
- UNCHANGED (CONFIRM, byte-identical): 3 columns, 2 ground beams, pool steps. ASSUMED - OWNER-APPROVED: none. UNKNOWN: none.

## 4. B10 before -> after (m3; candidate code totals, V3.0.63 run of record 09ec4c1a -> V3.0.64)

| Code | Released | Held bounded low .. high (lines) | Held blank (lines) | Beside |
|---|---|---|---|---|
| STR.CONC.BEAM (137) | 66.870678 (unchanged) | 6.023085 .. 8.507278 -> **6.023229 .. 8.507710** (14) | 12 (unchanged) | +0 .. 0.0545 exposures named |
| STR.CONC.BOUNDARY_WALL (1) | 7.2204 -> **0** (the downgraded point) | 0 -> **5.6392 .. 11.0328** (1) | 0 | Q-28 A 8.459, freelancer 8.604 |
| STR.CONC.BLINDING (7 -> 8) | 12.734438 (unchanged) | 7.640374 .. 13.466198 (5, unchanged) | 1 -> **2** | NEW AT_LEAST 0.915529 |
| STR.CONC.GROUND_BEAM | unchanged | unchanged | unchanged | lower-only floors 5.069839 -> **5.092339** (+0.0225) |
| every other code | unchanged | unchanged | unchanged | |

Export / census view (downgrades applied): the band was already held at export, so released B10 at export does not
move; the band moves from the point 7.2204 .. 7.2204 to 5.6392 .. 11.0328. Reconciliation (exact): beam pieces
0.626256 .. 1.878768 -> 0.6264 .. 1.8792 (+0.000144 / +0.000432 = route G lengths 1.3993 / 1.3993 / 3.0997 / 1.1297 /
0.8002 -> drawn 1.40 / 1.40 / 3.10 / 1.13 / 0.80); asserted in the run by `check_totals` (changes alone).

## 5. Line-by-line diff vs V3.0.63 (every other line byte-identical, asserted)

| Line | Code | Action | Member | V3.0.63 | V3.0.64 | Hand check |
|---|---|---|---|---|---|---|
| L-dc8cbfc1 | BEAM | BOUND | 2F BAND0008.1 | 0.111944 .. 0.335832 | 0.112 .. 0.336 | 1.40 x 0.20 x 0.40 / 1.20 |
| L-7c3edce2 | BEAM | BOUND | 2F BAND0011.1 | 0.111944 .. 0.335832 | 0.112 .. 0.336 | 1.40 x 0.20 x 0.40 / 1.20 |
| L-d62d2fcf | BEAM | BOUND | 2F BAND0006.1 | 0.247976 .. 0.743928 | 0.248 .. 0.744 | 3.10 x 0.20 x 0.40 / 1.20 |
| L-8d031491 | BEAM | BOUND | 2F BAND0001.3 | 0.090376 .. 0.271128 | 0.0904 .. 0.2712 (+ 0 .. 0.014 beside) | 1.13 x 0.20 x 0.40 / 1.20 |
| L-f83c4a46 | BEAM | BOUND | 1F BAND0005.1 | 0.064016 .. 0.192048 | 0.064 .. 0.192 (+ 0 .. 0.0405 beside) | 0.80 x 0.20 x 0.40 / 1.20 |
| L-6290a9f3 | BOUNDARY_WALL | BOUND (DG-6dd9f1ca materialised) | band | 7.2204 (released) | 5.6392 .. 11.0328 | 70.49 x .2 x .4; 91.94 x .2 x .6 |
| L-6bf14711 | GROUND_BEAM | LOWER_ONLY | BAND0012.1 | blank (>= 0.09) | blank (>= 0.1125) | 1.50 x 0.30 x 0.25 |
| L-893c3db1 | BLINDING | ADD_LOWER_ONLY (NEW) | pool blinding | (none) | blank (>= 0.915529) | (11.851050 - 2.695761) x 0.10 |

## 6. Regression and validation

- Run of record (Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) / 'ST7757
  dxf.dxf' 9f9d1179, decoded into the private folder only): own fresh t167 `v304_run.py` -> `research/agents_t668/v3064_run.py`
  (exit 0): every earlier version re-run and asserted, **V3_0_63 09ec4c1a (asserted = T-665 run of record)** -> **V3_0_64
  d227173a**, 5,074 lines; replaced 7, added 1, outside 5,066 byte-identical (asserted); diff vs V3.0.63: ADDED 1,
  CHANGED 6, CHANGED_TEXT_ONLY 1 (the corner floor), SAME 5,066; vs released V2.9: QUANTITY_DIFFERS 1,040,
  SAME_QUANTITY 552, NOT_IN_RELEASED 3,482; every
  earlier version's identity check re-ran on the result (A3063.integrate chain) and passed.
- `t479_registry_census.py` (unchanged; verdict set V3.0.44 b3b08dd7, downgrade snapshot 81732639) on V3_0_63
  reproduces `research/agents_t665/out/LINE_INDEX_V3_0_63.json` byte for byte; on V3_0_64 -> `out/LINE_INDEX_V3_0_64.json`,
  issues {}, complete map, 0 stale blocks against 1.65.0; DG-6dd9f1caba1ca77d now STALE_CONTENT.
- `t668_package_families.py` (T-483 attribute unchanged, chain 63 -> 64): B10-01 +1 added, B10-07 5 changed, B10-11 1
  changed; B10-04 record only (the corner floor beside a blank line). A dry promotion with a stand-in promotions
  source gave candidate V3.0.64, 0 problems (B10-11 HELD_IN_CANDIDATE).
- Tests `tests/t668_concrete_gate_b3`: hand villa V668 (pieces with a column-owned square, released band under its
  downgrade, a pool on a footing netted once, a lower-only corner floor) + adverse (square claimed by two lines,
  piece square owned elsewhere, owner line absent, exposure with a floor / unit slip, added element already carried,
  stale netted line, added line with a value / without its AT_LEAST, band without its downgrade, tampered added line,
  applied twice), inputs builder, master 1.65.0. L4 and the targeted results: in the handoff.

## 7. Registry: BOQ_FAMILY_MASTER_1.65.0 (pending now, promoted IN the merge)

`research/agents_t668/build_master_1_65_0.py`: 1.64.0 + V3.0.64 pending + B10-01 / B10-04 / B10-07 / B10-11 text
(0 problems). In the merge the Verifier runs (ADOPTED lesson, as T-661 / T-665):

    python3 -I research/agents_t668/t668_promotions_source.py --board .work/board/docs/agents --out research/agents_t668/out/PROMOTIONS_SOURCE_1_65_0.json
    python3 -I research/agents_t668/build_master_1_65_0.py --promote --write
    python3 -I research/agents_t668/write_manifest.py

## 8. Who is right (freelancer beside, never proof)

Band: freelancer 8.604 (71.7 m x 0.20 x 0.60) inside the drawn 5.6392 .. 11.0328: UNRESOLVED (Q-28 section and
founding level), his 71.7 m vs drawn 70.49 net / 91.94 gross. Pool blinding: ENGINE_RIGHT on scope (printed on ST p.7;
the freelancer has a plot plate only, NOT_LIKE_FOR_LIKE). Beam pieces and the annex corner: NOT_COMPARABLE (no row).
Pool steps: RULE_DIFFERENCE (his 0.228 m3 for an undrawn element).

## 9. Rule and lessons row (proposed)

R-T668-1 (engine/source/arch_v3064.py) = R-T665-1 + (h) exposures beside a bound are 0 .. x and never in its range; one
owner per junction square across all lines + (i) a printed element no line carries is ADDED held blank with its
AT_LEAST beside, every line it shares plan with bound and the shared area stated.

Lessons row (ERS s.7, PROPOSED): | 2026-11-10 | a merged ledger names its owner line by a typed id that is not a
candidate id (T-669 a_corner_square), while its own census row carries the real one | the id was typed, not read from
the index | an integration binds every id it wires to the line index and refuses a prefix match without member
agreement (every package; provenance T-668) | tests/t668_concrete_gate_b3/test_t668_inputs.py (test_corner_square_t669)
| PROPOSED |
