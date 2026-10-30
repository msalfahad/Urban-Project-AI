# T-347 Buried-structure displacement bound to the V3.0.24 lines; earthworks FILL table for T-350 (lane S)

Worker 3 (taking the lane S row: no lane I TODO), 2026-10-29 23:05 .. UTC, run session_01E6cPnbkVfxdL5YPfLRqNGP,
branch `agents/task-T-347`. Research ledger: nothing wired, no candidate or released line changed, no method version,
no quantity released. Integration dependency of T-350 (B1-02 / B1-03 / B1-04 earthworks are MISSING from both the
candidate and the freelancer's workbook): T-350 only wires the FILL table below. Development villa, not an accuracy
claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied.

## 0. Run, identity, sources

Own run, Python 3.11.18, Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (`ab54dd55`) and
'ST7757 dxf.dxf' (`9f9d1179`), decoded into `.work/private` only. `research/agents_t167/v304_run.py` then
`research/agents_t338/v3024_run.py`: **V3_0_24_BOQ_LINES.json `19394733`** (= the T-338 record of V3.0.24, the candidate
of record; 3,710 lines; 0 earthworks lines).

```
python3 -I research/agents_t347/t347_candidate.py <v3024 run> research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json
python3 -I research/agents_t347/t347_alsenan.py --write
```

Inputs read (all merged, read only): T-320 displacement ledger (5ddb2ba1), T-170 neat pits / trenches / overlaps
(2991be3d), T-253 run index, T-332 face -> line binding (61d5597e: run id -> V3.0.21 line id, re-checked in V3.0.24),
T-322 lift base (d3bcd9d4), T-342 pool D (AGREES), T-319 parapets (not buried). Outputs: `BINDING_T347.csv` (one row per
displacement component -> line), **`FILL_T350_T347.csv`** (the FILL table), `PITS_T347.csv` (neat plans, handles,
depth basis), `OVERLAPS_T347.csv` (30 pairs, w*), `summary_t347.json` (per-line closure, findings, changes since T-320).
Rules: `t347_rules.py` R-T347-1 .. 5. Tests: `tests/t347_earthworks_bind/` (12 rule tests on the hand villa T347-X +
8 on the committed outputs).

## 1. Physical element and the question (ERS s.2.1)

Element: the soil cut from the existing ground EG +-0.00 (T-170 / T-253, Checker Gate A) to the formation, the solids
and voids placed in that cut (DISPLACEMENT, no quantity of its own: each component stays its concrete / blinding / WP
line's, ELEMENT_REGISTER 'Buried structure'), the soil returned (backfill) and the surplus removed (disposal). Question
(ERS s.2.1): which V3.0.24 line owns each buried component ONCE, which excavation components the drawings print, and
which stay HELD by name.

## 2. Binding (acceptance a): 256 displacement rows -> V3.0.24 lines, double count 0

Each T-320 row is one physical component; two T-320 rows were split so that each part has ONE owner (R-T347-1):
the pool envelope (one T-320 row, closes to 1e-6) into its 9 components, and each 0.07 m footing UNDERLAY into its 5 cm
screed (WP.FOUNDATION.FOOTING_SCREED m3) and 2 cm membrane (WP.FOUNDATION.FOOTING_MEMBRANE m2) parts.

| Binding | Rows | Lines |
|---|---|---|
| BOUND (line has a quantity, closure checked) | 148 | footings 25, footing-layer blinding 25, screed 24 + membrane 24 (+ FF screed / membrane), GB 43, pool base / walls, straps 3 |
| BOUND_LINE_HELD (owner line blank: the ledger figure stays the ledger's, the line gives no number) | 87 | 36 necks, GB blinding line (31 rows: 17 exterior runs valued 2.79956 m3 + 13 ZERO_BY_BOUND), 16 GB, F10 / F, strap in F10 + F, 1B1B screed / membrane |
| BOUND_OVER_LINE (line below the displacement bound to it: a finding, section 4) | 9 | SB3 in F3, strap blinding, boundary lower band, 6 interior GB |
| NO_LINE (named) | 12 | pool water space (VOID), 5 pool p.7 layers + floor build-up (MISSING, T-310), pool blinding x2 (MISSING), lift-pit walls + void (no line; T-322 1.100 m3 / m of pit), brick below N.G. + pads (Q-28), lower GB row (conditional), ARC:139+13A (SPLIT_UNRESOLVED in two lines, no value) |

Binding keys (no reading of a number): footings by type + position after ONE frame translation (+75 968, +14 448 mm,
T-170 FOUNDATION-plan frame -> candidate GROUND-plan frame; derived from the footings whose element hash is shared,
spread <= 1 mm = integer-mm ids; F11 and F6 carry a different element hash in the candidate (109682 / cf553f vs e37220 /
33adbb): same type at the same outline position, bound and named); necks the same (36 / 36); ground-beam runs by the
Checker-verified T-332 face binding (run -> line); boundary runs R4-185.<run> -> the one BOUNDARY_GB_NG line; pool by
element id; underlay / blinding / straps by element id.

Closures (summary.json `per_line`): 24 footing lines 0.000000 m3 each (FN 222230 = 0.258 = 0.300 - the F9 / FN overlap
0.042 netted to FN by D-32, the candidate's clipped outline); footing screed 5.4925 m3 closes 0.000; footing membrane
109.85 m2 = T-219 exactly; footing-layer blinding 15.179437 m3 = 24 pits 12.923438 (incl. D-14 0.189) + the FF part
2.256 (HELD, DG-3521554d); pool walls 2.828071 = 2.121053 below EG + 0.707018 above; pool base 4.374226; straps
1.5925 / 1.1464 / 0.6516 each 0.000; ring L-7076482d 1.746943 vs the T-253 run 1.73488 (+0.012063: T-255 closed the
ends on drawn faces, line larger, inside capacity).

Lines with no displacement row (census, not an omission): WP.FOUNDATION.BURIED_LIQUID / FOOTING_SIDES / LIFT_PIT_BOARD
(coatings and boards: their thickness is not printed, an area measure, T-320 counts no volume); STR.CONC.GROUND_SLAB
(25 lines, above EG: they cap zone Z2, not Z1); two superseded pool scope lines NOT_APPLICABLE_WITH_EVIDENCE.

## 3. Elements changed since T-320 (acceptance a), before / after

| Element | T-320 | V3.0.24 / merged since | m3 effect on the displacement account | Cause |
|---|---|---|---|---|
| FF raft | 0 .. 11.385 below EG (pit depth) | raft 4.60 x 4.50 x 0.55 = 11.385 DRAWING-CONFIRMED on L-1590b76b; below-EG share still HELD | 0 (range unchanged) | T-322 |
| FF blinding | 0 .. 2.256 (F-T320-03) | HELD AT_LEAST 2.070 (projection not printed on p.14); DG-3521554d holds the FF part of L-98eb2d58 | low 0 -> 2.070 (bound), high 2.256 not supported (p.13 projection INHERITED for FF only) | T-322 + DG-3521554d |
| FF underlay | HELD whole (UNDERLAY_NOT_PRINTED) | screed 20.700 m2 x 0.05 = 1.035 m3 on L-e4789d76 (DRAWING-CONFIRMED); membrane area 20.700 m2, thickness HELD | screed 0 .. 1.035 (below-EG share HELD with the pit floor) | T-322 |
| Pool envelope / D outline | 18.3251; water 7.2920 | AGREES: water face 8.578838 m2 (T-342 hand D) x 0.85 = 7.292012 | 0.000 | T-342 |
| F12 pit (1ABF) | 12.6513 | AGREES (9.856 on its line; T-332 re-read 4.40 x 3.20) | 0.000 | T-332 |
| Parapets (T-319) | - | above the slabs: not buried, no row | 0.000 | T-319 |

## 4. Findings (lines below the displacement bound to them)

1. **F-T347-1 SB3 in F3, stale held range on L-c823e0db** (0.0295 .. 0.1181 m3 = the T-174 range): T-230 (merged
   before V3.0.8) showed one straight strap has one level, so the excess is 0.0295 .. 0.2683 m3 (T-233 finding 4,
   MERGED). Still not corrected in V3.0.24. Verdict proposal LEDGER_RIGHT; a lane I held-range correction (no released
   figure moves). The earthworks account carries 0.2683 as the high end.
2. **F-T347-2 strap blinding, two held bases**: ledger 0 .. 0.913 m3 (T-233, 9.13 m2 x 0.10, none printed, D-15) vs
   L-35382b18 0.3778 .. 0.7719 (ROUTE_G merge window, V3.0.2). UNRESOLVED (D-15); both kept.
3. **F-T347-3 boundary lower band, a single reading of an open question**: ledger 5.639 .. 11.033 m3 (Q-28 A
   PROVISIONAL) vs L-6290a9f3 7.2204 SOURCE_DERIVED (strip length x one schedule section). The line state is a question
   for the Lead / Checker (state, not quantity).
4. **F-T347-4 interior GB depth class (6 lines)**: T-242 holds D in [0.30, 0.40] (D-34); the T-320 above-EG figure and
   the two annex ranges take 0.40, the PROVISIONAL lines 0.30. On the main house the part below EG is 0 either way
   (ZERO_BY_BOUND): no displacement effect. RULE_DIFFERENCE inside a held range.

## 5. Neat plans and overlaps (acceptance b)

`PITS_T347.csv`: 26 footing elements, 24 neat pits DRAWING-CONFIRMED with their DXF outline handle (ST7757 dxf.dxf
FOUNDATION PLAN; ST7757.pdf p.13 projection 0.10): gross 129.570 m2, net 129.234375 m2 after the two real overlaps
F9 / FN (180C) 0.330 and F8 / FN (10F0) 0.005625 m2 (R-T347-4: each pair once, no point in three plans). FF and F10 / F
HELD (p.14 projection / Q-31 C). Printed depth: NONE as a value; 'not less than 1.5 m' (p.9 note 1) = AT_LEAST 1.50
(R-T347-3, Q-21 C: the founding level is fixed on site); the pool formation -1.50 IS printed (T-183 r2 chain);
exterior GB bottom on N.G. (T-253), its blinding -0.10 .. 0.00. `OVERLAPS_T347.csv`: 30 pairs with w* (east block F5 /
F8 / F9 / F14 / FN merge at w* <= 0.275 m: pits vs bulk, OQ-13).

## 6. FILL table for T-350 (acceptance c), `FILL_T350_T347.csv`, 18 rows, blank never 0

| Family / zone | m3 | lo | coef / m of d | Status | Held by name |
|---|---|---|---|---|---|
| B1-02 Z1 24 pits | blank | **188.017207** | 129.234 | HELD | formation (d), working space, pits vs bulk, D-14 1.890 m2 beyond the plot, F8 / pool 1.99957 m2 counted in the pool zone |
| B1-02 Z1 pool | blank | **17.776576** | 0 | HELD | blinding projection (>= 1.222), working space, 0.5486 beyond the plot |
| B1-02 FF / F10F / ext GB / annex / court / straps / boundary / lower GB row | blank | blank | - | HELD | pit depth; Q-31 C; working space + pit / trench end overlap; D-34 / D-33 / D-35; no section; D-15; Q-28; conditional |
| B1-02 interior GB main (13 runs) | blank | hi 0.000 | - | ZERO_BY_BOUND | condition b_wet <= 0.30 (T-214) |
| B1-03 pits / pool / ext GB / other / Z2 | blank | blank | pits 124.374 | HELD | excavation held; annex beams over pits unbounded (no backfill bound is proved); Z2 not formed |
| B1-04 all zones | blank | blank | - | HELD | bulking (no answered rule), Z2 re-use, excavation |

Hand check of the pits bound: (129.570 - 0.330 - 0.005625 - 1.890 - 1.99957) x 1.50 = 125.344805 x 1.50 = 188.017207 m3.
Why lower bounds hold: the excavation only grows with d >= 0 and with any working space or bulk dig; the regions
removed (beyond the plot, the F8 / pool overlap) only lower it. No upper bound exists (d unbounded). The exterior GB
trench has no bound either way (+ working space, - pit overlap). A backfill lower bound would need an upper bound on
every solid in the pits; the annex ground beams over pits (D-34 / D-35) have none, so B1-03 stays blank.

## 7. Methods side by side; evidence status

| Method | Excavation / backfill / disposal | Status |
|---|---|---|
| Owner manual method | Q-21 C: excavation, disposal, replacement fill, compaction, blinding, footings, necks, backfill measured SEPARATELY; founding level held; no working-space, pit-vs-bulk or bulking rule (OWNER_QUESTIONS_ANSWERED, OWNER_RULE_* searched for excavation / working space / bulking / disposal) | applied: separate families and zones, nothing assumed |
| Drawing-derived (this task) | neat plans DRAWING-CONFIRMED; depth AT_LEAST 1.50 (pits) / 1.50 printed (pool); every volume HELD or a proved bound | DRAWING-CONFIRMED plans, HELD volumes |
| Candidate V3.0.24 / released V2.9 | no earthworks line (B1-02 IMPLEMENTED_NOT_INTEGRATED, B1-03 / B1-04 NOT_IMPLEMENTED, master 1.19.0) | NOT_IMPLEMENTED |
| Freelancer | no excavation, backfill or disposal row (T-170 searched) | omitted on both sides |

Verdict proposals: excavation / backfill / disposal UNRESOLVED (designer items RFI S1 / OQ-13); the 188.017 / 17.777 m3
are lower bounds, never quantities. Evidence status of the FILL rows: HELD (bounds DRAWING-CONFIRMED in their parts).

## 8. Rules and lessons row (proposed)

R-T347-1 .. 5 (`t347_rules.py` docstring). Lessons row: | 2026-10-29 | the displacement account had no owner lines:
one T-320 row (pool envelope, 0.07 underlay) mixed components that different lines own, a member split across two
lines could not be bound, and four candidate lines sit below the displacement bound to them (one stale range carried
since V3.0.8) | displacement was ledgered by element, the candidate by line, and nothing tied the two | R-T347-1 one
owner per physical component (split by thickness / by component, never a share), R-T347-2 line capacity incl. the
above-EG part, area lines by area | tests/t347_earthworks_bind (normal: villa T347-X two overlapping pits, lift pit with
a printed floor, strap; adverse: overlap twice, triple point, printed minimum as founding level, held formation as 0,
one displacement on two lines, value through a blank line, over capacity, undeclared unit, default bulking, mirror) |
proposed |

## 9. For the Checker (re-measure)

1. F12 pit: 1ABF 4.40 x 3.20 -> neat 4.60 x 3.40 = 15.64 m2; footing 9.856 on L-88c5feea; screed 14.08 x 0.05 =
   0.704, membrane 14.08 m2.
2. FN 180C (146 262, 46 648 -> 222 230, 61 096 in the candidate frame): 1.00 x 1.00 x 0.30 - F9 overlap 0.40 x 0.35 x
   0.30 = 0.258 = L-d2c75eb1.
3. Pits bound: 188.017207 m3 by the hand line above; pool 12.216759 m2 x 1.50 = 18.325138 - 0.548562 beyond the plot =
   17.776576.
4. SB3 in F3: T-230 single-level excess 0.0295 .. 0.2683 vs L-c823e0db 0.1181 (F-T347-1).

## 10. Not done / uncertain

- No line wired (lane I T-350). Zone Z2 not formed (enclosed plan, wet-floor b, D-33 / D-34).
- Pit / trench end overlaps not netted (run-end positions against pit outlines are not in the merged inputs).
- Drainage, manholes, tanks (sanitary-7757.pdf) outside this structural account (none in any merged ledger).
