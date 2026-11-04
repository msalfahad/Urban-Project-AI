# T-500: tile bed mortar material table on candidate V3.0.53 (research, unwired)

Worker 2, 2026-11-04. `t500_tile_bed_mortar.py` (TILE_BED_MORTAR_TABLE_V1, UNWIRED_PRODUCER) +
`out/TILE_BED_MORTAR_T500.{json,csv}` + `tests/t500_tile_bed_mortar/` (20 tests). No engine, rule, knowledge, registry
or candidate file changed; no candidate or released (V2.9 + route G) line moves. Rebuild:
`python3 -I research/agents_t500/t500_tile_bed_mortar.py` (byte-identical, tested); `--check` exits 1 on any failure.

## 1. Physical element and what is measured

The 1:4 cement-sand bed under a floor tile (B3-05), one layer per tiled floor, carried since R-T420-1 as a measure pair:
FIN.FLOOR.BED.* m2 (= the floor-finish net) + m3 (owner band: DRY 0.03 .. 0.04 m, WET 0.04 .. 0.06 m, a range). This
table binds the m3 line and derives what the bed consumes: installed cement (50 kg bags) and loose sand (m3) = m3 x 8 /
x 1.1 at each end of the range; the owner's 5 % mortar waste as its own field; procurement = installed + waste; whole
bags only at project level and only over a determinate subtotal (R-T499-1).

Not here (one producer per material): the wet-wall levelling render and spatter dash (plaster trade, T-454 / T-489);
a tiled wet wall has no fixing bed (UPC-WETWALL-001, T-457). Stair beds (1:3), roof / balcony screeds, outdoor floors
(T-495) are refused as owned elsewhere.

## 2. Methods side by side and status

| | Owner manual method | Drawing-derived | Status |
|---|---|---|---|
| Bed area | tiled floor of the room | candidate floor-finish net (bed m2 = finish m2, 44 / 44 checked) | the line's own |
| Thickness | Q-45 band (OWNER CONFIRMED 2 Nov) | not printed (D-40 / D-41); dry drawn bound 0 .. b beside (R-T420-1), not used | range, never a mid value |
| Cement / sand per m3 | Q-45 B: 8 bags + 1.1 m3 per m3 of 1:4 (practice value accepted, PROVISIONAL); Q-78 A re-uses it | first principles 7.2 .. 7.7 bags, 1.00 .. 1.07 m3 (sanity only) | ASSUMED — OWNER-APPROVED |
| Waste | Q-45 B 5 % on mortar | - | separate field |

## 3. Result on V3.0.53 (0 failures)

V3.0.53 (36863f6c) = V3.0.51 (c0b6d664) + 60 STR.CONC.LINTEL lines, 4,876 rows identical (T-487 identity, asserted).

| | lines | area m2 | installed m3 | cement bags (installed) | sand m3 | procurement bags (+5 %) | to buy |
|---|---|---|---|---|---|---|---|
| DRY | 23 + 23 | 301.518472 | 9.045554 .. 12.060739 | 72.364 .. 96.486 | 9.950 .. 13.267 | 75.983 .. 101.310 | 76 .. 102 |
| WET | 21 + 21 | 85.575578 | 3.423023 .. 5.134535 | 27.384 .. 41.076 | 3.765 .. 5.648 | 28.753 .. 43.130 | 29 .. 44 |
| PROJECT | 88 | 387.094050 | 12.468577 .. 17.195274 | 99.749 .. 137.562 | 13.715 .. 18.915 | 104.736 .. 144.440 | 105 .. 145 |

Census: 88 / 88 lines accounted (44 m3 BOUND, 44 m2 NOT_APPLICABLE measure-pair partners); every m3 range reproduced
from area x band at 6 decimals (44 / 44). 58 floor-finish lines: 44 BEDDED, 13 NOT_APPLICABLE_WITH_EVIDENCE (finish
EXCLUDED: 12 doorway strips + the open-room porcelain part replaced by its wet pantry line), 1 MISSING_BED_LINE
(FIN.FLOOR.FINISH_HELD GF-R31F8AE:GF-ST-CN, area HELD 0 .. 0.230 m2, finish HELD: bed HELD, never 0; T-421 bedded the
hall and lobby parts only). 18 FIN.WALL.TILE lines: NOT_APPLICABLE, no bed line on any wall host.

Cross-checks: wet area and m3 = T-420 totals exactly; area / m3 = T-471 matrix row C-B3-05 (387.094 m2, 12.469 ..
17.195 m3); V1 `materials()` (waste folded in) = this table's procurement on all 44 rows within 1e-5.

Two lines for the Checker to re-derive: `1F-R0E919A:floor:bed` (DRY 16.34 m2): 0.4902 .. 0.6536 m3, cement 3.9216 ..
5.2288 bags, sand 0.53922 .. 0.71896 m3. `HL:FLOOR_SCOPE:WET:GF:GF-PANTRY-RC06FED:bed` (WET 2.800001 m2): 0.112 ..
0.168 m3, cement 0.896 .. 1.344, sand 0.1232 .. 0.1848.

Residual named: three floors carry a HELD 0 .. 0.200 m2 lift-threshold deduction (T-413) beside their net; the bed m3
uses the net, so the low end could fall by at most 3 x 0.200 x 0.03 = 0.018 m3 (0.144 bags) if every deduction applies
(the bed under the marble threshold then belongs to B6-07). Not widened: the candidate's m3 line is the figure bound.

## 4. Freelancer and verdict proposal

The freelancer's floors / waterproofing workbook has no bed, screed, cement or sand row (T-420 s.7): B3-05 materials
are engine-only. Verdict proposal: ENGINE_RIGHT on scope (Q-45 bed in every tiled room), quantity ASSUMED —
OWNER-APPROVED range; nothing of his to reconcile.

## 5. For the wiring row

- T-496 `NOT_IN_ANY_TABLE` still names FIN.FLOOR.BED.*: the binding map should read this table (T-496 file, not
  changed here).
- The bags to buy are a project figure; per-line bags are never rounded.
- The GF-ST-CN bed stays HELD with its finish.

## 6. Lessons row (proposed)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-04 | 88 bed lines had no cement / sand in any purchase quantity | the bed was integrated as installed volume only; materials stayed a T-086 view on hand areas | R-T500-1..5 (any villa): bind the m3 line of the measure pair, reproduce its range from area x band, cement / sand as ranges, waste separate, held stays held, completeness by host, no bed on walls | tests/t500_tile_bed_mortar (normal: hand villa P500, V1 agreement, candidate 88 / 88; adverse: held thickness, band drift, mm2 as m2, wrong unit, mirror / rotation / mm, double / lone line, bedded wet wall, owned-elsewhere code, missing per-m3 figure) | proposed |
