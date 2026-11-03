# T-422 Integration package: skirting quantity release into ARCH_TAKEOFF_V3.0.44 (Gate B)

Worker 1 (stream F), 2026-11-02. Split row (a) of T-246. Candidate ARCH_TAKEOFF_V3.0.44 built on the candidate of record
V3.0.43 (T-350, MERGED 3077469a), reproduced in this run from the Drive copies; NOT RELEASED; the released default stays
ARCH_TAKEOFF_V2.9 + route G (rollback: run V2.9). Drawings named by Drive folder and title only; no coordinate, image,
client name or note text in any committed file. ERS 2026-10-22 applied: s.2.1 physical element first, s.2.2 evidence
hierarchy (merged sill record, then the engine), s.2.4 reconcile in lm to named causes, s.3 one owner per wall base.

## 0. Inputs and reproduction

Drive folder "Alsenan chalet project": 'ST7757 dxf.dxf' (sha256 `9f9d1179`), P7757_DXF_COMPRESSED.zip -> P7757.dxf
(`ab54dd55`), decoded into `.work/private` only. Python 3.11.18.

```
python3 -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757 dxf.dxf> --out <private>/t167
python3 -I research/agents_t422/v3044_run.py <P7757.dxf> <ST7757 dxf.dxf> --out <private>/t422 --t167 <private>/t167
```

V3_0_43_BOQ_LINES.json of this run = the candidate of record **`6f534d5e`** (byte for byte); V3_0_44_BOQ_LINES.json
**`8b2fe2b6`** (summary_t422.json: identity, every row before / after, totals moved). Diff vs V3.0.43: 4,848 SAME
(outside rows sha256 `b277f656..`), 9 CHANGED, 1 ADDED; totals moved only in FIN.SKIRTING|lm. T-330 check
(tools/t330_deductions_check.py, unchanged): V3.0.43 6 FLAG / 0 REFUSED -> V3.0.44 6 FLAG / 0 REFUSED (the same 6
V3.0.32 ceiling lines; no new FLAG).

`t422_inputs.py` builds URBAN_V3044_INPUTS_V1 ONLY from the merged T-296 files, pinned by sha256 (an edited file stops):
WINDOW_CAUSES_T296.csv (`4ed39b96`), LINE_LEDGER_T296.csv (`cd76f184`), ROOMS_T296.csv (`2fc2ca2c`); T-296 MERGED
57c31ae4, Verifier 2026-10-25 16:08 UTC Gate A PASS (own re-measure 1F-01 15.900 lm, W14 sill 1.40 AGREE). The ledger
read V3.0.17; the module binds every line to the V3.0.43 candidate (state, gross and net to 1e-6, range to 1e-6, the
listed window halves by census id): all 9 bound lines still stand as the ledger read them. One reading was already
applied by a later merged package and is set aside by name, never applied twice: W09 (wet pantry GF-07) left the GF
open-plan range in V3.0.21 (T-315 base-ownership SPLIT 1.500 lm, 7.831578 -> 6.331578).

## 1. Physical element and rule (R-T422-1, every villa)

Skirting is a strip at the foot of a finished DRY wall / column face at floor level (UP-SKIRT-001 1.4.0, UP-CER-002 lm,
UP-CER-003 doors deducted). Under a window it exists only where the wall continues below the sill:

| window base | skirting | action in V3.0.44 |
|---|---|---|
| sill established above the floor (> 0.02 m) | yes, the wall continues under the sill | RELEASE: listed halves out, net + edge; range line counted in the line |
| sill at the floor (floor glazing) or the base of an owner wet room | no | RANGE_NARROW: edge out of the held range |
| sill not established | unknown | unchanged: whole edge held in the range |
| dry room with no skirting line | yes, not measured | MISSING: HELD BLANK line, never 0 |

## 2. Before / after, line by line (V3.0.43 -> V3.0.44)

| Line | Room | Window (sill, status) | Before | After | Change |
|---|---|---|---|---|---|
| L-bb0ea965 | GF-04 driver | W04 0.600 (1.70, DRAWING-CONFIRMED T-201) | 10.200 lm | **10.800** | +0.600 |
| L-9b43782b | GF-04 range | W04 | held 0 .. 0.600 | NOT_APPLICABLE (in L-bb0ea965) | -0.600 held |
| L-c021ae79 | 1F-01 | W14 2.449774 (1.40, PRINTED T-175) | 13.450226 | **15.900000** | +2.449774 |
| L-049dd2e6 | 1F-01 range | W14 | held 0 .. 2.449774 | NOT_APPLICABLE (in L-c021ae79) | -2.449774 held |
| L-2f58111e | 1F-04 | W24 1.552320 (1.00, DRAWING-CONFIRMED T-201) | 14.047680 | **15.600000** | +1.552320 |
| L-5438f973 | 1F-04 range | W24 | held 0 .. 1.552320 | NOT_APPLICABLE (in L-2f58111e) | -1.552320 held |
| L-d057b5b0 | 2F-03 maid | W29 1.200 (1.00, DRAWING-CONFIRMED T-201) | 16.000 | **17.200** | +1.200 |
| L-b557f284 | 2F-03 range | W29 | held 0 .. 1.200 | NOT_APPLICABLE (in L-d057b5b0) | -1.200 held |
| L-079bc766 | 1F living + ST-1F range | W15 / W16 1.552320 each (0.00, floor glazing, T-238) | held 0 .. 5.304640 | held **0 .. 2.200** (W13 1.2 + W25 1.0) | -3.104640 held |
| new L-4a85470b | 1F dressing 1F-RFFE7AF | none | no line (MISSING) | BLOCKED_RFI, blank; engine boundary 6.90 m beside | named, never 0 |

Each released net closes gross - list + additions (T-330 tolerance 0.0005): 12.500 - 1.700 = 10.800; 17.700 - (OP-004
0.800 + OP-020 1.000) = 15.900; 17.400 - 1.800 = 15.600; 18.900 - 1.700 = 17.200. Every released figure equals the
T-296 ledger figure and, for 1F-01, the Checker's own re-measure 15.900 lm.

FIN.SKIRTING totals: certain 184.016658 -> **189.818752 lm** (+5.802094); held high 24.637649 -> **15.730915 lm**
(-5.802094 carried once, -3.104640 floor glazing); range lines 8 -> 4; blocked lines 2 -> 3. The remaining 15.730915 lm
held is exactly W02 6.331578 + W11 / W12 3.909840 + W17 3.289498 + W13 1.200 + W25 1.000 (sill not established or
stair shaft): the T-246 UNRESOLVED list.

## 3. Owner manual method and drawing-derived method side by side

| | Owner manual method | Drawing-derived method (engine + merged readings) |
|---|---|---|
| Released rooms | room perimeter at floor level less each door / passage width; a window is deducted only where no wall continues under it | engine runs with the V3.0.36 list by opening id; the window halves leave the list when the merged sill is above the floor |
| 1F living range | the floor-glazing W15 / W16 bases carry no skirting | the range keeps only the windows whose base is undecided (W13, W25 on the stair shaft) |
| Dressing | perimeter less doors (not walked yet) | no engine line; held blank, engine boundary 6.90 m beside (engine figure, not independent) |

## 4. Engine vs freelancer

The freelancer's skirting is 282.85 lm = 12 dry-room gross perimeters with no door deduction (T-106). Candidate certain
184.02 -> 189.82 lm (+3.15 %); with every held range 208.65 -> 205.55 lm. Gap to the freelancer 98.83 -> 93.03 lm
(-34.9 % -> -32.9 %): RULE_DIFFERENCE (UP-CER-003 doors and passages deducted; he deducts none), never the target, no
accuracy figure. Verdict proposals: W04 / W14 / W24 / W29 ENGINE_RIGHT now (sill above the floor printed or
drawing-confirmed; hand: 1F-01 17.700 - 0.800 - 1.000 = 15.900); W15 / W16 ENGINE_RIGHT now (floor glazing out of the
range); dressing ENGINE_OMISSION named (held); W02 / W11 / W12 / W17 / stair shaft UNRESOLVED (no sill / no stair rule).

## 5. Held, not in this package

1. W02, W11, W12, W17 sills not established (T-144 / T-207 / T-238 designer items): edges whole in the ranges.
2. 1F living line keeps the ST-1F shaft wall bases (10.232 lm, T-250 walk) and W13 / W25: no owner rule for skirting
   along a stair; the T-296 ledger low 31.203 is NOT applied (needs the stair-skirting rule; WAITING T422_STAIR_SHAFT).
3. 2F-01 lobby 6.138 lm stays inside its BLOCKED_RFI stair line (a split is its own package).
4. Dressing: no merged independent walk; the line is held blank (WAITING via its rfi). A walk of the cell (wall bases,
   door by id) releases it.

## 6. Code, tests and regression

- engine/source/arch_v3044.py (new; RELEASE / ABSORB_RANGE / NARROW_RANGE / ADD_MISSING on FIN.SKIRTING only;
  check_skirting; every V3.0.43 line outside the 10 named rows byte-identical, asserted; totals moved only in
  FIN.SKIRTING, asserted). tools/urban_boq_m9.py: --method ARCH_TAKEOFF_V3.0.44 --v3044-inputs (the T-350 pattern).
- research/agents_t296/t296_skirting_opening_rules.py: the task-prefixed name of skirting_opening_rules.py (lessons
  2026-10-25), a new file; the merged file stays unchanged on disk (the T-296 tests import it); identity tested.
- rules/coverage/BOQ_FAMILY_MASTER_1.39.0.json = 1.38.0 + pending V3.0.44 + B3-06 evidence / reader / missing text
  (build_master_1_39_0.py --check: equal, no problem); RULES_MANIFEST + m9_rules_manifest registered.
- tests/t422_skirting_release: 33 (K422 hand villa: release 13.90 -> 15.10, range absorbed, R4 range 2.00 -> 0.80,
  floor glazing 4.00 -> 1.60, missing blank; adverse: sill at the floor, held sill, stale binding, partial listing,
  window not listed, CONSISTENT listing, window twice, mm / cm slips, narrow of a valued line, whole-range narrow, floor
  glazing without a sill, missing with a value / wet / present, applied twice, range line of another room, tampered
  release, other project; mirrored order; master 1.39.0; rules rename identity).
- L3 on the task tree: m9_s6, m9_p2a, m9_s2_arch, m9_s4, m9_s5, m9_kb, m9_p2b0/2/3/5, m9_foundation, m9_s3, t131 ..
  t211 arch chain, t246, t296, t330, t350, t400, t410, t420, t421, t429, t430, t431, t435, t440, t441, t442, t459,
  t463, t467, t469, t471, t106, t328, t344, t236, t130, t061, t422: exit 0. Freeze 0 differing; codemap stale none.

## 7. Lesson (proposed for ERS s.7)

| 2026-11-02 | a merged ledger read on V3.0.17 named a narrowing (W09 out of the GF range) that V3.0.21 had already applied | ledgers name readings, later packages apply some of them | an integration binds each reading to the current line value and sets aside, by name, a reading the candidate already carries; never applied twice | tests/t422_skirting_release test_stale_binding_stops; t422_inputs ALREADY_OUT | V3.0.44 |
