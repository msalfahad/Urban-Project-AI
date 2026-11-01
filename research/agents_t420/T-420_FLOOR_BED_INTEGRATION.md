# T-420 Integration package: B3-05 floor bed into ARCH_TAKEOFF_V3.0.37 (Gate B)

Worker 3 (lane I), 2026-11-01. **Integration package** for Checker Gate B. Candidate ARCH_TAKEOFF_V3.0.37 built on the
candidate of record V3.0.36 (json `d462203f`, reproduced byte for byte in this run); NOT RELEASED; the released default
stays ARCH_TAKEOFF_V2.9 + route G (rollback: run V2.9). Integrates T-414 only (MERGED 4f81eda1, Verifier
2026-11-01T05:25Z Gate A PASS, with its finding F-C-T414-1). Drawings named by Drive folder and title only; no coordinate,
image, client name or note text in any committed file. **No V3.0.36 line, state or total moves**: the package only ADDS
the missing B3-05 category.

## 0. Inputs and reproduction

Drive folder "Alsenan chalet project": 'ST7757 dxf.dxf' (sha256 `9f9d1179`), P7757_DXF_COMPRESSED.zip -> P7757.dxf
(`ab54dd55`), private copies in `.work/private` only. Python 3.11.18.

```
python3 -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757 dxf.dxf> --out <private>/t167
python3 -I research/agents_t420/v3037_run.py <P7757.dxf> <ST7757 dxf.dxf> --out <private>/t420 --t167 <private>/t167
python3 -I research/agents_t420/t420_summary.py <private>/t420 [--write]      # stops unless V3.0.36 = d462203f
```

V3_0_36_BOQ_LINES.json of this run = the candidate of record **`d462203f`** (checked by `t420_summary.py`);
V3_0_37_BOQ_LINES.json **`733f2efb`** (4,810 lines; full sha256 in `summary_t420.json`).

`t420_inputs.py` builds URBAN_V3037_INPUTS_V1 ONLY from the merged T-414 files pinned by sha256 (an edited file stops):
`research/agents_t414/ROOM_TABLE_T414.csv` (`7bc3752c`) and `summary.json` (`eadb730f`); the owner ranges are READ from
the merged `floor_bed_v1.py` (OWNER_BED, Q-45), not retyped; the one typed value is the Checker's F-C-T414-1 upper end
b = 0.051 for zone 1F-DRY (T-214 verdict: 0.049 .. 0.051 between sources). The T-414 table was read on V3.0.34; the
module binds every one of its 53 finish lines in V3.0.36 (item, element, state, net to the table's 4 decimals): 53 of
53 still stand (V3.0.35 / V3.0.36 restated only the porcelain GROSS fields, never a net).

## 1. What changed (R-T420-1)

| Kind | Beds | m2 (= the bound finish net) | Installed m3, owner Q-45 range (ASSUMED — OWNER-APPROVED) | Drawing bound beside (HELD) |
|---|---|---|---|---|
| DRY (FIN.FLOOR.BED.DRY) | 19 (17 DRAWING-CONFIRMED area, 2 ASSUMED — OWNER-APPROVED area) | **288.145972** | **8.644379 .. 11.525839** (0.03 .. 0.04 m) | 0 .. **14.5144** (b GF 0.05 / 1F **0.051** / 2F 0.05; tile thickness printed nowhere) |
| WET (FIN.FLOOR.BED.WET, incl. kitchen, pantry parts) | 21 (14 / 7) | **85.575578** | **3.423023 .. 5.134535** (0.04 .. 0.06 m) | none: wet / sunken level printed nowhere (D-41), HELD |
| NOT_APPLICABLE finish lines | 13 | no bed line (recorded by id) | - | - |
| **Total** | **40 beds, 80 lines added** | **373.72155** | **12.067402 .. 16.660374** | dry only |

Each bed is TWO lines of ONE physical item, a measure pair (`measure_pair.price_one_basis = true`): an m2 line (the
finish line's own state: SOURCE_DERIVED / PROVISIONAL, gross = net) and an m3 line in BOUNDED_EXPOSURE (low = area x
owner low, high = area x owner high, no value, no gross: never one chosen thickness, owner Q-45 "report every bed as a
range"). The drawing bound, its b, b_upper, the CONSISTENT check (owner high 0.04 <= drawn b on every dry bed) and the
missing tile thickness are in `calculation.inputs.floor_bed_v3037.drawing_bound`, never the line figure. Each line states
its WORKFLOW s.5 status in `calculation.inputs.evidence_status` (read by tools/boq_export_v1.py).

The dry bound total is 14.5144 summed per line at 6 decimals; the Checker's 14.5143 is the sum of the 4-decimal table
rows (107.0525 x 0.051 = 5.4596775 for 1F, +0.2141 over the handoff's 0.049). Owner totals likewise differ from the T-414
summary by rounding only (dry 8.6443 .. 11.5258 / wet 3.4229 .. 5.1347 on 4-decimal rows; here from the candidate's
exact nets).

Space with no floor-finish line: **no bed** (register ROOM WITH NO FLOOR-FINISH LINE). The T-418 stair-room floor parts
(GF stair hall 4.805 + 1.3225 m2, 2F lobby 2.500 m2): **bed follows T-421** (WAITING `T420_BED_FOLLOWS_T421`).

## 2. Methods side by side (ERS s.2 step 2) and evidence status

| | Owner manual method | Drawing-derived method | Status |
|---|---|---|---|
| Area | the tiled floor of the room | the floor-finish line's net (engine face, Checker-merged B3-01 lines) | m2: DRAWING-CONFIRMED (31 beds) / ASSUMED — OWNER-APPROVED (9 beds whose finish area is PROVISIONAL) |
| Thickness dry | Q-45: 0.03 .. 0.04 m (+ adhesive <= 3 mm, its own item, + tile) | t = b - t_finish - t_adhesive, b = FFL - structural top of the room's zone (T-214, SECTION A-A / B-B), t_finish printed nowhere -> 0 < t <= b | m3: ASSUMED — OWNER-APPROVED range; drawn layer HELD inside 0 .. b; CONSISTENT |
| Thickness wet | Q-45: 0.04 .. 0.06 m, falls 1 % (Q-41: the bed is the only layer over the membrane) | b of the wet / sunken zone printed nowhere (D-40 / D-41) | m3: ASSUMED — OWNER-APPROVED range; drawn layer HELD, no bound |
| Balcony | Q-41 screed, thickness not given | - | no balcony on this villa (every exterior slab floor is a B13-01 roof / terrace zone) |

Installed vs procurement: only the installed volume is a line; cement bags, sand and 5 % waste stay the
finish_materials_table view (T-086). Physical vs contract: Q-41 names the contract form (MORTAR_BED dry / wet, SCREED
balcony); whether a tiler's rate includes the bed is a pricing question, not answered here (the measure pair lets a
pricer bill m2 or m3, never both).

## 3. One layer, one item (no double count)

- `check_beds()` (asserted on the integrated lines): every bed line is bound to a valued FIN.FLOOR.PORCELAIN / WET_TILE
  line, one m2 + one m3 per bed, one bed per finish line; `changes_for()` stops if a candidate floor-finish line is not
  named by the table (53 of 53 named).
- Other layers on the same rooms: membrane lines B8-01 .. B8-03 (FIN.WP.*) are a different layer (reported, untouched);
  16 roof-layer lines (B13-01), the stair finish lines (B7), the outdoor paving lines (B13-02) carry no bed (T-414:
  `double_counted: []`). A roof / terrace / stair / pool / foundation / outdoor / balcony row is refused
  (OWNED_ELSEWHERE, tested).
- The open room's pantry part (8.954867 m2) is ONE wet bed on its own wet line; the open-room dry bed is on its net
  109.778417 (already net of the pantry part): 0.000 m2 shared.

## 4. Line-by-line diff and regression

- vs V3.0.36: **4,730 SAME, 80 ADDED, 0 CHANGED** (`V3_0_37_DIFF.csv`; every V3.0.36 line byte-identical, asserted;
  outside-rows sha256 in the summary). Code totals moved only in FIN.FLOOR.BED.DRY|m2 / |m3 and FIN.FLOOR.BED.WET|m2 /
  |m3 (asserted).
- vs released V2.9 + route G: the 80 bed lines are NOT_IN_RELEASED (V2.9 has no B3-05 line); the rest as V3.0.36
  (diff counts in the summary).
- T-330 deductions check: V3.0.36 113 OK / 5 EMPTY / 1 NOT_SUMMING -> V3.0.37 153 OK / 5 / 1 (the 40 m2 bed lines close
  gross = net; no new finding).
- Export (tools/boq_export_v1.py, unchanged) on V3_0_37: 80 bed rows; m2 MEASURED UNVERIFIED, m3 HELD with held_low /
  held_high = the owner range, stated status ASSUMED — OWNER-APPROVED; nothing as 0.
- Tests: tests/t420_floor_bed_fill (V420 hand fixture, not Alsenan: normal + adverse; registry 1.32.0 census);
  L3 folders and every family-master test (section 7 of the handoff).

## 5. Gate B hand-check list (WORKFLOW_CONTROLS s.1)

New scope (always by hand): the B3-05 family. Suggested re-measures, each from the drawing / the merged ledgers, not from
this file:

1. 1F-R0E919A bed: finish net 16.34 m2 (line L-c044aecc); owner 16.34 x 0.03 .. 0.04 = 0.4902 .. 0.6536 m3; bound
   16.34 x 0.051 = 0.83334 (1F b upper end, F-C-T414-1).
2. GF-RC99C2A (open room, the largest dry line): 109.778417 m2 = 118.733284 - 8.954867 (pantry part); owner 3.293353 ..
   4.391137; bound x 0.05 = 5.488921.
3. GF-RA3AD49 (kitchen, porcelain code but whole room under the membrane, Q-30 A -> WET): 9.630001 m2, 0.3852 .. 0.5778,
   no drawing bound.
4. 1F-R26FA0D (1F wet, sunken): 10.151 m2, 0.40604 .. 0.60906, no bound.
5. The 13 NOT_APPLICABLE finish lines carry no bed (ids in `summary_t420.json`).

## 6. Missing / held

- Drawn bed thickness: HELD (tile thickness printed nowhere, D-40); wet / sunken levels printed nowhere (D-41).
- Balcony screed thickness (Q-41): no balcony row on this villa.
- Bed of the T-418 spaces: follows T-421 (they have no floor-finish line yet).
- The dry area basis is inherited from B3-01: against the freelancer's tiled floors the dry area is -49.4242 m2
  (-14.6 %), of which 16.53 m2 is the stair hall / lobby without a finish line (T-418 / T-421), the rest traced in T-414
  s.4; wet +13.5656 m2 (+18.8 %): pantry RULE_DIFFERENCE (Q-37 A) + T-074 ENGINE_RIGHT.

## 7. Freelancer (quantities only; Drive "Alsenan chalet project", floors / waterproofing / decor / marble workbook)

He has **no screed, bed, cement or sand row**: B3-05 is MISSING on his side (an engine-only family), not a residual.
Verdict proposal: ENGINE_RIGHT on scope (the bed is built in every tiled room: Q-41 / Q-45 owner rules), quantity
range ASSUMED — OWNER-APPROVED; no figure of his to reconcile.

## 8. Rule and lessons row (proposed)

R-T420-1 (every villa; integrates R-T414-1): a bed line exists only beside a valued floor-finish line, bound to it by id;
m2 = that net; installed m3 = the owner range with the room's own-zone drawing bound beside (upper end of a drawn
range); a wet room never takes the dry b; owned-elsewhere floors refused; held never 0; m2 / m3 one measure pair.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | B3-05 had no candidate line; the bed existed only as research (T-414) and a T-086 material range | a layer with an unprinted thickness was left out instead of carried as an owner range with the drawn bound beside | R-T420-1 (any villa) | tests/t420_floor_bed_fill (normal: hand villa V420, upper-end bound, measure pair, byte identity, mirror order; adverse: roof / terrace bed, held as 0, bed ahead of a finish, unnamed finish line, stale binding, defaulted thickness, wet room with dry b, upper bound below b, mm as m, ledger mismatch, a line twice, applied twice, a valued m3 / lonely line) | proposed |
