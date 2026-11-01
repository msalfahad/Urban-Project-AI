# T-400 Integration package: B13-04 boundary fence and gates into ARCH_TAKEOFF_V3.0.35 (Gate B)

Worker 3 (lane I), 2026-11-01. Integration package for Checker Gate B. Candidate ARCH_TAKEOFF_V3.0.35 built on the
candidate of record V3.0.34 (json `4c7f581c`, reproduced byte for byte in this run); NOT RELEASED; the released default
stays ARCH_TAKEOFF_V2.9 + route G (rollback: run V2.9). Drawings named by Drive folder and title only; no coordinate,
image, client name or note text in any committed file. ERS 2026-10-22 applied: s.2.1 (the boundary wall defined as a
composite element, component by component), s.2.2 (printed > drawn; only geometry a merged verdict re-measured carries a
figure), s.3 (plane vs block net vs layers vs procurement kept apart), s.4 (rule R-T400-1 + normal / adverse tests).

## 0. Inputs and reproduction

Drive folder "Alsenan chalet project": 'ST7757 dxf.dxf' (sha256 `9f9d1179`), P7757_DXF_COMPRESSED.zip -> P7757.dxf
(`ab54dd55`), private copies in `.work/private` only.

```
python3 -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757 dxf.dxf> --out <private>/t167
python3 -I research/agents_t400/v3035_run.py <P7757.dxf> <ST7757 dxf.dxf> --out <private>/t400 --t167 <private>/t167
```

`t400_inputs.py` builds URBAN_V3035_INPUTS_V1 ONLY from Checker-merged files pinned by sha256 (an edited file stops):

| Task | Merge | Checker verdict | File read |
|---|---|---|---|
| T-396 | e129577d | Verifier 2026-10-31T14:05Z Gate A PASS (own re-measure north 31.370, street 5.600 m, '265' printed, plane 97.9705 m2 AGREE) | research/agents_t396/LEDGER_T396.csv, CROSS_TRADE_T396.csv |
| T-403 | a72a7282 | Verifier 2026-10-31T17:58Z Gate A PASS (upper G.B 3.5256 m3, band split 44.07 / 3.50 / 44.37 m, masonry AT_LEAST 17.628 m2 AGREE) | research/agents_t403/summary_t403.json |
| T-404 | 698282e4 | Verifier 2026-10-31T17:58Z Gate A PASS (faces 83.1305 + 82.0705 m2 DC, every layer HELD AGREE) | research/agents_t404/FACES_T404.csv, ITEMS_T404.csv |
| T-361 | e8d0bb06 | Verifier 2026-10-30 15:37 UTC Gate A PASS (G-02 = D-GF-15 once, G-01 leaf HELD) | research/agents_t361/GATES_T361.csv |

T-407 (READY at the time of the claim, MERGED 8c0e8349 since) is NOT input: the block under the house ground beams is
house masonry, not this family (register ruling 2026-10-31 20:20).

## 1. The physical element and where each component goes (R-T400-1)

| Component | Line / record in V3.0.35 | State | Evidence status |
|---|---|---|---|
| Masonry above N.G., wall plane per run | 4 new EXT.FENCE.WALL lines | north 83.1305, street 14.840 m2 MEASURED; sea, passage BLANK | DRAWING-CONFIRMED / HELD |
| Block net per run | 4 new EXT.FENCE.BLOCK lines | BLANK (at most the plane on north / street) | HELD (columns M4, lower 0.50 band) |
| Block type and count | 1 new EXT.FENCE.BLOCK_COUNT (pcs) | BLANK | HELD (Q-65 C) |
| Masonry below N.G. (44.07 m band) | 1 new EXT.FENCE.MASONRY_BELOW_NG | BLANK, AT_LEAST 17.628 m2 beside | HELD (formation a printed minimum) |
| Pads 1.30 x 0.80 x 0.30 | 1 new STR.CONC.BOUNDARY_PAD (m3) | BLANK, 0.312 m3 per pad beside | HELD (count not printed) |
| Upper G.B 20 x 40 | existing `L-fb7a6431fede62e93fd5` restated (HELD_BOUND) | BLANK, range 0 .. 3.5256 m3 | HELD (column joints M4) |
| Lower G.B band (whole 91.94 m) | existing `L-6290a9f3d93f38cd46d6` BOUND, unchanged | SOURCE_DERIVED 7.2204 (Checker downgrade at export) | HELD (fence share 3.3976 .. 5.2884 inside it) |
| Physical faces per side | 9 new EXT.FENCE.FACE lines | north outside 83.1305 / plot 82.0705 MEASURED; street, sea, passage, G-01 stop-end BLANK | DRAWING-CONFIRMED / HELD |
| Plaster / render, paint / Sigma per face | 8 + 8 new EXT.FENCE.PLASTER / .PAINT | BLANK, at most the face beside | HELD (p.12 prints no finish) |
| Wall top | 2 new EXT.FENCE.TOP (lm) | north 31.37 m MEASURED; street BLANK, at least 5.60 | DRAWING-CONFIRMED / HELD |
| Street gate G-01 | 1 new EXT.FENCE.GATE (pcs) | BLANK, opening 2.50 m beside | HELD (no leaf drawn) |
| Sea gate G-02 = D-GF-15 | 1 new EXT.FENCE.GATE (pcs) | BLANK, opening 1.00 m beside | HELD (Q-63 C) |
| X railing in the street dip | existing `L-78babf2c6da600cb800e` RL-10 BOUND, unchanged | BLANK | HELD |
| D-GF-15 threshold strip | existing `L-56acf34557c315f65bb1` BOUND, unchanged | BLANK | HELD |
| Coping | RECORD | NOT_DRAWN | UNKNOWN |
| G-01 far jamb | RECORD (house facade ledger) | OTHER_OWNER | - |
| G.B coating below N.G. | RECORD (T-263) | OTHER_OWNER | - |
| Masonry coating below N.G. | RECORD | NOT_DRAWN | UNKNOWN |

Why the lower band is bound, not split: the line carries the Checker line-content downgrade of the T-356 band
(verdicts/V3.0.29/DOWNGRADES.json, binding LINE_CONTENT_V1); any change to its content breaks that downgrade, and a
second fence-share line would count the fence share twice (it is inside the 7.2204). The split by owner class (fence
3.3976 .. 5.2884 / pool 0.24 .. 0.42 / house 2.0016 .. 5.3244 m3, T-403, sums 5.6392 .. 11.0328 = T-356) waits for the
Checker to re-issue the downgrade on the split lines (WAITING LOWER_BAND_SPLIT_DG).

Why G-02 gets a gate line: D-GF-15 is in NO door count line of the candidate (DOOR.* lines list D-GF-01 .. -14 only;
D-GF-15 appears only in a held reveal plaster and a held threshold strip), so before V3.0.35 the gate was counted zero
times. It is now counted once, in B13-04; `check_boundary` asserts that no DOOR.* line names D-GF-15.

## 2. Per BOQ line: before / after, method side by side (the 5 valued lines and the restated line)

| Line | Element | V2.9 | V3.0.34 | V3.0.35 | Terms | Owner manual method | Drawing-derived method |
|---|---|---|---|---|---|---|---|
| L-c67c20465860c34dd052 | FENCE:F-NORTH:WALL_PLANE | none | none | 83.1305 m2 | 31.37 x 2.65 | run x height (blockwork) | layer-5 outer 99 + 98 = 31.370; p.12 '265' |
| L-68135cb06855cb135a04 | FENCE:F-STREET:WALL_PLANE | none | none | 14.8400 m2 | 5.60 x 2.65 | run x height less the gate | 10F 8.300 - gate 2.500 - corner 0.200 |
| L-c21c5a88b12bf69e0df1 | FENCE:F-NORTH:FACE:OUTSIDE | none | none | 83.1305 m2 | 31.37 x 2.65 | per face where a note names it (none) | outside face to the external corner |
| L-2987b2641ee6a599d651 | FENCE:F-NORTH:FACE:PLOT | none | none | 82.0705 m2 | 30.97 x 2.65 | as above | plot face stops at the internal corner |
| L-480833d5a8a07203d2b6 | FENCE:F-NORTH:TOP | none | none | 31.37 m | 31.37 | - | p.12 plain 0.20 top |
| L-fb7a6431fede62e93fd5 | upper boundary G.B | (in its own V2.9 line set) | BLOCKED_RFI blank, no range | BLOCKED_RFI blank, range 0 .. 3.5256 m3 | 44.07 x 0.20 x 0.40 | member by member (Q-61 C) | S-BOUN 7FE / 7FC / 810, A-A 20 x 40 |

The 35 blank lines: see V3_0_35_INTEGRATION_LEDGER.csv (each with its held reason and the figure beside). Every
added line is NOT RELEASED.

Valued totals added: EXT.FENCE.WALL 97.9705 m2 (= T-396 plane), EXT.FENCE.FACE 165.201 m2 (= T-404 north faces),
EXT.FENCE.TOP 31.37 m. Held, never 0: block net (at most 97.9705), masonry below N.G. (at least 17.628), finish layers
(at most 165.201 on north + 30.21 on street), sea element (6.36 comparison only per face / plane), passage closure, pads,
both gate leaves, street top / stop-end.

## 3. Diff and identity (the run on the drawings)

- V3_0_34 json `4c7f581c` = the T-399 Gate B candidate of record, REPRODUCED.
- V3_0_35 json `b011bace` / csv `59436bf4`, diff csv `5f79857e`, ledger csv `4379bec9`; outside-rows sha `2353642c`
  (the 4,689 unchanged lines); the stage re-run from V3_0_34 alone gives `b011bace` again.
- Lines 4,690 -> 4,730: **SAME 4,689 (byte-identical), CHANGED 1 (the upper G.B range), ADDED 40, REMOVED 0**.
- Against released V2.9: the 40 added lines are NOT_IN_RELEASED; every other line keeps its V3.0.34 relation.
- Totals moved only in the ten new codes; STR.CONC.GROUND_BEAM code totals unchanged (a BLOCKED range is not summed).
- House facade / blockwork overlap 0.000 m2: T-404 face keys shared 0 (merged check), T-396 layer-1 guard 0; asserted
  in `check_boundary` (no line outside B13-04 names a FENCE: element). Above / below N.G. split at the upper G.B top:
  0.000 m2 shared (T-403 s.5).
- File hashes and the identity block: summary_t400.json.

## 4. Freelancer (quantities only; from the merged reconciliations, nothing new)

| Item | Freelancer | V3.0.35 | Diff | Verdict proposal (merged) |
|---|---|---|---|---|
| Fence blockwork ('السور') | 74.40 m2 (37.20 x 2.00) | plane 97.9705 m2 (block net HELD) | -23.5705 m2 (his figure 24.1 % below the plane) | ENGINE_RIGHT on the plane (height 2.65 printed vs 2.00; corner counted twice +0.40); block net UNRESOLVED (HELD) |
| Fence plaster + Sigma | 107.24 m2 at 2.40 on three faces | faces 165.201 m2 DC; layers HELD | not a like-for-like figure (he omits one north face) | height ENGINE_RIGHT (-10.8625 m2); scope RULE_DIFFERENCE (which faces) |
| Upper boundary G.B | 7.560 m3 (42 x 0.30 x 0.60) | range 0 .. 3.5256 m3 (gross DC) | -4.0344 m3 on the gross (-53.4 %) | ENGINE_RIGHT on width and depth (printed 20 x 40) |
| Masonry below N.G., pads, gates | none | HELD blank | not compared | existence ENGINE_RIGHT (drawn in A-A); quantity UNRESOLVED |

## 5. Regression and checks

- tests/t400_boundary_fence (41 = 24 module + 12 registry 1.30.0 + 5 inputs): Villa V400 hand fixture (plane 43.200 + 13.920 = 57.120 m2, faces 85.920 m2, top
  18.00 m, upper G.B 0 .. 2.544 m3), order invariance; adverse: typed figure not its terms, held with a value, block net
  valued, held as 0, mm as m, gate wider than the face, a component twice, drawn-only height valued, stale binding,
  bound not the drawn gross, low end not 0, facade face shared, total not the verified total, applied twice, a non-fence
  line naming a fence element, a gate counted twice (as a fence gate and as a door count); the development-villa inputs
  pinned (40 rows, totals, gates, no coordinates); registry 1.30.0 (builder, copies, ownership census at full strength).
- Registry census set-aside (tests/t284_ceiling_integration/test_family_master_1_27_0.py, test_family_master_1_29_0.py):
  the 1.26.0 pattern (a module newer than the registry is judged by the newer registry, which runs the same guards at
  full strength: test_full_census_every_written_code_and_literal_owned). No assertion was removed.
- L4 FULL SUITE to the end (tests/ dirs in two halves + tests/test_*.py + every agents/ folder, in parallel) on
  1237acaa (code = the final head; later commits add only summary_t400.json, the report and the maps): vs
  research/agents_t202/known_failures.json: KNOWN 395, NEW 2 = t374 snapshot-vs-board (pre-existing F-T328-3, carried
  by T-411, NEW on every L4 since T-328) and tests/codemap test_repository_maps_are_current (transient: the maps were
  rebuilt while the suite ran; re-run on the final head 6a3d2e55: pass, with t400 / t399 / t284), ABSENT 1 (christiannp
  builder passes), as on T-399. Final head: freeze 0 differing, codemap stale none, registry 1.30.0 --check clean, rules
  manifest drift none.

## 6. Held / missing (WAITING in V3_0_35_RUN.json) and downstream

FENCE_COLUMNS_M4, FENCE_LOWER_050_BAND, FENCE_STREET_PROFILE, FENCE_FINISH_LAYERS, LOWER_BAND_SPLIT_DG,
BOUNDARY_BLINDING, BELOW_NG_COATING, HOUSE_SOUTH_GB_BLOCK. Downstream: no existing line depends on the new lines; the
export joins verdicts/V3.0.29/DOWNGRADES.json unchanged (the downgraded band line is byte-identical). Designer facts
(rfi/B, already filed by T-396 / T-403 / T-404; none new): p.12 section location and lower '50' band, boundary column
count, street dip profile, passage closure top, sea element, formation level, lower G.B depth.

## 7. Rule, lesson

R-T400-1 (every villa) in engine/source/arch_v3035.py. Lessons-register row proposed: | 2026-11-01 | The sea gate
G-02 (= D-GF-15) was in the opening census by id but in no count line: counted zero times through 34 candidate versions,
while its threshold and reveal were held lines | an opening census row was taken as a counted item | an opening is
counted once by asserting the count line that carries it (by id) across every family that could, never by its presence
in a census (scope every villa; provenance T-400) | tests/t400_boundary_fence/test_arch_v3035.py::
test_adverse_fence_gate_also_a_door_count | PROPOSED |
