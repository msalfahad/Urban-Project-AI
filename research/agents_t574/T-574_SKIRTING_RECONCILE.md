# T-574: skirting vs the freelancer by room / stair group, lm and nr apart, on ARCH_TAKEOFF_V3.0.58

Worker 2, 2026-11-06, lane A, non-candidate (research only; no engine, rule / knowledge version, registry, frozen or
candidate file changed; nothing released; released default V2.9 + route G unchanged). Files: research/agents_t574/*
and tests/t574_skirting_reconcile/* only. Development villa; not an accuracy claim. His figures are read as numbers
from the merged register tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (sheets keyed by a hash of the title;
unit labels checked by hash, R-T546-1; no workbook text committed). Deduction components are the merged T-460 V3.0.51
closure (gross / listed / added per line) split by opening id from T-296, plus T-422 / T-431 / T-440 / T-443 / T-483
/ T-508; flight figures from T-501. Nothing re-measured from the drawing this run. ERS read: s.2.1, 2.2, 2.4, 2.7 (no
owner question: no genuine contradiction; every open item is a designer RFI already held or his own unsplit row),
s.3, s.4, s.7.

## 1. Physical element and classes (ERS s.2.1, R-T574-1)

ROOM skirting = strip at the foot of a dry, untiled wall / column face at its floor level: outline less doors, lift
and passage openings, less faces with no wall base (floor glazing, open side, slab opening / shaft at that level),
less tiled faces (wet rooms, wet pantry); jambs take none. STAIR_FLIGHT = raking side, developed along the pitch
(zigzag B7-07 / sloped B7-08, one line per form, never additive). PIECES = his per-step count, nr, never converted.
OUTDOOR = a court base. Candidate V3.0.58 = V3.0.57 skirting lines: FIN.SKIRTING released **209.428592 lm** (18
lines), 7 HELD, 28 NOT_APPLICABLE; 44 flight lines HELD (22 pieces x 2 forms).

His side (rows asserted against his own totals): tiles sheet room perimeters C13..C29 = C31 = cover B16 = **282.85
lm** (12 dry rooms, gross, no deduction); marble sheet level skirting 4.37 / 23.10 / 2.40 = H45 = cover B25 = **29.87
lm** (entrance E1 / main ST-01 / inner round ST-02, T-084 pairing); pieces per step 5 / 63 / 28 = H46 = **96 nr**;
yard G13 = cover B23 **81.32 lm**. No wet-room skirting row.

## 2. ROOM table, ours - his, lm (out/T574_SKIRTING_RECONCILE.json; every group closes exactly)

| Group (his row) | ours | his | gap | causes |
|---|---|---|---|---|
| GF open room (13 + 15) | 28.571589 | 72.92 | -44.348411 | doors -5.000 RD; passages -12.22 + run back +1.40 RD; floor glazing W02 -6.331578, W03 -1.627277, open zone side -2.555652, wet pantry bases -3.500 and W09 -1.500 ENGINE_RIGHT; dining piece +3.900 ENGINE_RIGHT; outline -16.913904 UNRESOLVED (pantry box face line 7.60 NA outside the gross, stair zone, band D-48; his rows undimensioned) |
| GF dewaneya (16) | 18.127877 | 20.00 | -1.872123 | door + arch -2.000 RD; printed outline 20.127876 (R1.10 corner) +0.127876 ENGINE_RIGHT; +0.000001 rounding |
| GF master (14) | 14.632594 | 21.71 | -7.077406 | doors -1.800 RD; floor glazing W03 -5.10186 ENGINE_RIGHT; outline -0.175547 TOLERANCE (-0.81 %) + 0.000001 |
| GF driver (17) | 10.800 | 12.50 | -1.700 | doors RD; outline AGREE (printed 12.50) |
| 1F living (21) | 32.38536 | 43.78 | -11.39464 | doors -4.700, passage -1.000, stair-owned W13 / W25 -2.200 RD; floor glazing W15 / W16 -3.10464, shaft without floor at +5.50 -9.050 ENGINE_RIGHT (T-508); outline 52.44 vs 43.78 +8.660 UNRESOLVED |
| 1F curved room (22) | 17.161172 | 22.89 | -5.728828 | doors -1.700 RD; floor glazing W17 -3.289498 ENGINE_RIGHT; outline -0.73933 UNRESOLVED (T-218) |
| 1F 380 x 430 + dressing (23) | 19.400 | 21.40 | -2.000 | doors -1.700 RD; arches -2.000 / +2.000 AGREE (his outline subtracts them too); his arch reveals 2 x 0.15 -0.300 RD (no jamb skirting) |
| 1F 500 x 365 (24) | 15.600 | 17.30 | -1.700 | doors -1.800 RD; column notch faces +0.100 ENGINE_RIGHT |
| 1F west 425 x 450 (25) | 15.900 | 17.45 | -1.550 | doors -1.800 RD; printed 17.50 vs 17.45 +0.050 and notches +0.200 ENGINE_RIGHT |
| 2F maid (28) | 17.200 | 19.30 | -2.100 | doors -1.700 RD; printed 18.90 -0.400 ENGINE_RIGHT |
| 2F corridor = lobby + arrival (29) | 7.500 | 13.60 | -6.100 | doors + lift -2.900, slab-opening edge -2.500 RD; outline -0.700 UNRESOLVED (T-443) |
| 17 wet rooms | 0 | 0 | 0 | AGREE: tiled faces, no skirting either side |
| **Total** | **197.278592** | **282.85** | **-85.571408 (-30.25 %, not a verdict)** | RULE_DIFFERENCE -43.620; ENGINE_RIGHT -32.082629; UNRESOLVED -9.693234; TOLERANCE -0.175545 |

Gross vs gross (OUTLINE terms only): ours 276.159097 vs his 282.85 = **-6.690903 lm (-2.37 %)**; the rest of the gap is
deductions he does not make (doors / passages by owner rule, faces with no base or tiled).

## 3. STAIRS (lm) and pieces (nr), each its own comparison

| Stair (his row) | ours valued | his | gap | causes |
|---|---|---|---|---|
| ST-03 entrance E1 (18) | 0 | 4.37 | -4.37 | flight E1.S HELD 1.470544 .. 2.050 (-1.470544); -2.899456 UNRESOLVED (both sides or the 1.40 x 3.70 landing edge in his row? a landing base on a drawn wall would be an ENGINE_OMISSION: named, not valued) |
| ST-01 main (25) | 10.900 (landings 4.850 + GF hall 4.650 + back lobby 1.400) | 23.10 | -12.200 | flights HELD 12.238505 .. unbounded (winders MS1-T), landing faces / GF stair-room RFI pieces HELD 0 .. 7.45 (amount 0); +0.038505 UNRESOLVED (his row unsplit) |
| ST-02 round (32) | 1.250 (RS-LD) | 2.40 | -1.150 | RS-S HELD 3.300 .. unbounded (RS-C / RS-S.S0 unknown); +2.150 UNRESOLVED |
| pieces per step | none | 5 / 63 / 28 nr | - | RULE_DIFFERENCE on unit, no %; count check E1 5 = drawn 5, RS 28 = plan 28, main 63 vs 52 .. 54 risers drawn (T-084) |

Flight lower bounds total 17.009049 lm = the T-501 sloped figure of the 13 HELD-FORM pieces (asserted). No % on stairs.

## 4. Outdoor

His yard skirting 81.32 lm vs no candidate line: UNRESOLVED scope (court interlock under OWNER_RULE_OUTDOOR_FLOORS,
side walk porcelain 21.0142 m2, T-553; no drawing or owner text says the court walls take a base). Completeness item
for the Lead; never 0.

## 5. Verdict proposals, rule, lesson, missing

- RULE_DIFFERENCE: doors, lift and passages (UP-CER-003 / UP-SKIRT-001; he deducts none), stair-owned faces, the 2F
  slab-opening edge, arch reveals; ENGINE_RIGHT: floor glazing W02 / W03 / W15 / W16 / W17, wet pantry faces, 1F shaft
  with no floor, the dining piece, printed outlines (dewaneya, maid, 1F bedrooms); TOLERANCE: GF master outline;
  UNRESOLVED 9.693 lm room outlines (GF open room -16.914, 1F living +8.660, curved room -0.739, 2F corridor -0.700:
  his rows have no dimensions); stairs and yard as above. 0 ENGINE_WRONG found; 0 FREELANCER_RIGHT.
- R-T574-1 (t574_rules.py docstring, every villa): classes with their own units; row unit from its own label; jamb
  and tiled-face skirting refused; flight bounds by form; causes close exactly; % only without HELD / scope / unit
  causes; VERIFIED refused.
- Lesson proposal (ERS s.7): "2026-11-06 | a skirting total compared with a reference's perimeter total | his rows are
  gross room perimeters, ours a net of every opening and baseless face | compare OUTLINE terms (gross vs gross, -2.37 %)
  and DEDUCTION terms separately, every opening by id | tests/t574_skirting_reconcile | PROPOSED".
- Missing: an independent re-measure this run; his room dimensions; ORR-007 (flight form); GF stair-room RFIs a-c;
  winders (S-9); RS-C band; outdoor skirting scope; the dressing joinery 2.800 lm (HELD JOINERY_SCOPE_NOT_PRINTED,
  carried, no gap effect).

## 6. For the Checker

1. Rebuild: `python -I research/agents_t574/t574_alsenan.py --check` (byte-identical; pins in the JSON).
2. GF master: 21.534453 - 1.000 - 0.800 - 5.10186 = 14.632593 (+0.000001 polygon) vs his 21.71.
3. 1F living: 52.44 - (4.70 + 1.00 + 3.10464 + 2.20) - 9.05 = 32.38536 vs his 43.78.
4. Dewaneya outline: 2 x (4.00 + 6.30) - 2.20 + pi x 0.55 = 20.127876.
