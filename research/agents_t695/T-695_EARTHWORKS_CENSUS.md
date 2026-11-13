# T-695: B1 earthworks census of ARCH_TAKEOFF_V3.0.68 by cause, and the zones the drawings measure now (lane S)

Worker 1, 2026-11-11. Development villa (Drive "Alsenan chalet project", 'ST7757 dxf.dxf' sha 9f9d1179), not an
accuracy claim. Research piece for the Checker (Gate A); nothing is wired, no candidate line moves, released default
V2.9 + route G untouched. Owner rules: 2026-11-02 17:20 / 17:45 / 18:00 (geometry always, material by dry mass with
measured densities only, 150 mm lift OWNER-PROVISIONAL, 95 % MPD PROPOSED-SPEC), RFI re-review S01 / S02 ESTIMATED,
R-T505-1, R-T350-1 / -2.

Files: `earthworks_census_v1.py` (EARTHWORKS_CENSUS_V1, pure, every villa), `t695_extract.py` (own DXF read, values
only -> `STRAP_TRENCH_INPUT_T695.json`), `t695_alsenan.py` (-> `CENSUS_T695.csv`, `ZONES_T695.json`,
`summary_t695.json`). Tests `tests/t695_earthworks_census/` (34: villa E695 by hand + adverse, Alsenan pinned).

```
.work/venv/bin/python -I research/agents_t695/t695_extract.py <.work/private>/st7757.dxf
.work/venv/bin/python -I research/agents_t695/t695_alsenan.py
```

## 1. Census (20 STR.EARTH lines of V3.0.68, reconciled by id to LINE_INDEX_V3_0_68, d1de50cb)

| Family | MEASURABLE NOW | DESIGNER | NEEDS TEST | OWNER RULE (primary) |
|---|---|---|---|---|
| B1-02 excavation (12) | 5: pits 24 (VALUED 208.164757), pool (VALUED 17.776576), ext GB trench (1.069269 .. 1.176467), INT-GB-MAIN-ZERO (**0.000 calculated**), STRAPS (**9.950299 .. 16.121241 new**) | 7: F10F (Q-31 C), FF (S14 / D-43 lift supplier), INT-GB D-33, ANNEX (D-33 / D-35; AT_LEAST 0.877899), COURT (no section), BOUNDARY (S2 / Q-28), LOWER-GB-ROW (S1, unbounded at +0.10) | - | - |
| B1-03 backfill (7) | 3: pits 24 (119.963335 .. 128.643547), pool and ext GB trench (**neat 0.000 calculated**, working space OQ-13 beside) | 4: OTHER-TRENCHES (straps part now bounded, split proposed), F10F, FF, Z2 | - | - |
| B1-04 disposal (1) | - | - | 1: ASTM D1557 MDD, in-situ dry density, loose density, suitability, placement target | - |

Secondary causes are in the CSV (OWNER_RULE secondary: working space OQ-13 on the pool / ext trench backfill, Q-28
on the boundary). No primary OWNER RULE gap: every held quantity waits on a designer item or a test.

## 2. New measurements (physical element first; owner manual method beside)

**A. Z1-TRENCH-STRAPS (SB1 70x50, SB2 100x50, SB3 50x40, p.10).** Element: the trench between the pit plans in
which each strap is cast, from EG +-0.00 to the strap formation. Soffit flush with the footing soffits (T-230, 5 / 5
ends) = -1.50 under S01. Plans (own read, route G frame, every deeper zone removed: pits zone 124.649469 m2 reproduced,
F10 / F, FF, pool): strap concrete 6.633533 m2 (F10 / F drawn outline 1B1B) .. 7.508569 (route-G box end); strip
+-0.10 sides 8.530189 (= T-356 merged 8.530149 + 4e-5 rounding) .. 9.655236. Owner manual method: plan x depth;
drawing-derived: the 12 scenarios below, never mixed.

| reading (D-15) | plan | formation | cut m3 (drawn .. box end) |
|---|---|---|---|
| R1 none (as drawn) | B | -1.50 | 9.950299 .. 11.262487 |
| R2 blinding 0.10 | B + 0.20 | -1.60 | 13.648303 .. 15.445376 |
| R3 footing chain (underlay 0.07 + blinding) | B + 0.20 | -1.67 | 14.245415 .. 16.121241 |

Backfill = cut - strap concrete outside the pits (3.164229 .. 3.601747) - blinding / underlay of the reading - ground
beams below EG over the trench (annex SB3: 13F+7D3, 13E+7D6 D-33 low = blinding only, high = down to the strap top;
13C+7D9 D-34 0.30 / 0.40; main interior 184+7CF#3 D-33 0 .. down to the strap top; 109+7CB#1 printed class: above EG,
0) = **6.437519 .. 10.952471 m3**. Layers @ 0.15: 8 (R1, 1.10 m over SB3) .. 10 (R2 / R3, 1.50 m beside the strap).
Compaction footprint 6.633533 .. 9.655236 m2. S01 sensitivity on the cut: -0.10 -> 9.286946 .. 15.155717; +0.10 ->
10.613652 .. 17.086765. Shared cut: main exterior GB 7D0+FC#3 / #4 blinding (-0.10 .. 0) over SB1 0.030019 m2 (box
end only) = 0.003002 m3, netted in the strap zone so the valued EXT-GB-MAIN line stays byte-identical. No strap part
lies beyond the plot or on the boundary band (0.000 m2).

**B. Z1-TRENCH-INT-GB-MAIN-ZERO, calculated 0.000.** 13 runs (T-242, printed class, no D-33): top +0.95 ('Ground
Floor slab level', p.13; T-214 b 0.05 under +1.00), D <= 0.40 (LT5M / LT2_5M+LT5M), blinding 0.10 -> lowest bottom
+0.45. The T-214 condition 'b_wet <= 0.30' is discharged: the GROUND BEAMS PLAN draws 0 sunken-panel hatches
(S-HAT.BAT ANSI31; 14 on the slab sheets, where the 1F / 2F sunken panels are) and prints only the FFL marks +0.15 /
+0.30 / +1.00; the GB top is a structural datum, so a GF wet build-up changes the finish, not the beam. Margin 0.45 m.
The D-33 runs: 0 while D <= 0.85 m (stated beside, not bounded above).

**C. Z1-TRENCH-ANNEX, AT_LEAST 0.877899 m3.** Free strips (outside pits, F10 / F, FF, pool, strap trench at its widest,
boundary band) x minimum depth below EG: D-33 / D-35 0.10 (beam bottom on N.G.), D-34 interior 0.15 (D 0.30, top
+0.25). Upper bound none (D-33 / D-35). 5 pieces whose route-G length disagrees with the ledger run are left out (a
smaller AT_LEAST stays valid).

**D. Neat backfill of pool and ext GB trench = 0.000 calculated** (the shell / layers / water space and the blinding
fill their neat cuts), consistent with their VALUED / BOUNDED neat excavations; working space (OQ-13) beside.

## 3. Reconciliation and who is right

- Straps vs merged T-356: side-strip plan 8.530189 vs 8.530149 m2 (+0.000040 = float order of the clip, named).
- Strap cut range width 6.17 m3 = D-15 (no blinding vs blinding + chain: +4.30 .. +4.86) + S02 end at F10 / F (SB1
  0.875036 m2 x depth: +1.31 .. +1.88); no figure chosen because it is larger.
- No freelancer and no released earthworks line: verdict UNRESOLVED (no comparison); ENGINE_RIGHT not claimed for any
  ESTIMATED figure.

## 4. For lane I (proposals, nothing wired)

1. B1-02 STRAPS: HELD BLANK -> BOUNDED 9.950299 .. 16.121241 (ESTIMATED S01; D-15 / S02 named).
2. New B1-03 STRAPS line split out of OTHER-TRENCHES: BOUNDED 6.437519 .. 10.952471; OTHER-TRENCHES keeps annex,
   court, boundary, D-33.
3. B1-02 INT-GB-MAIN-ZERO: HELD BLANK -> CALCULATED 0.000 (geometry, evidence above).
4. B1-03 POOL and EXT-GB-MAIN: HELD BLANK -> CALCULATED 0.000 neat, working space beside.
5. B1-02 ANNEX: AT_LEAST 0.877899 beside the held line.

## 5. Held, never 0

Lift pit depth (S14), F10 outline (Q-31 C), D-33 / D-34 / D-35 sections (S8), court section, boundary band depth (S2),
the lower GB row at +0.10 (S1), working space (OQ-13), Z2 (enclosed plan measurable, D-33 solids and the GF slab
soffit: next row), every material quantity (tests named in the census).

Observation (not classified, no line): a 3.50 x 3.50 hatched box (S-HAT.BAT ANSI37 with a soil hatch inside) on the
GROUND BEAMS PLAN near the +0.15 court, absent from the foundation plan and from every merged earthworks ledger. The
Lead decides whether it is a buried element.

## 6. Rule and lessons row (proposed, ERS s.7)

R-T695-1 (every villa, PROPOSED; in the module docstring): zone value = envelope of admissible scenarios each computed
alone; a deeper zone owns a shared plan and the shallower cut is netted once; a calculated 0 needs a geometric proof
for every admissible section; material only with measured densities (tests named), balance by R-T505-1; metres only.

| 2026-11-11 | the 13 interior main GB runs and the strap trench stayed HELD BLANK four candidates after their geometry was
known | a zone held for one condition (b_wet, D-15) was never re-tested against the drawings once other rows settled
its inputs | census every held line by cause each round; discharge a condition by drawing evidence, bound a designer
item by its admissible readings (earthworks, every villa) | tests/t695_earthworks_census (normal E695 strap
2.52 .. 3.768; adverse solids > cut, mm depth, HELD as 0, missing row) | PROPOSED |
