# T-350 r2: calculated earthworks quantities, development villa (lane S piece for Checker Gate A)

Worker 3, 2026-11-03, run unknown. Development villa, not an accuracy claim. Owner sessions 2026-11-02 17:20 / 17:45 /
18:00 and the RFI RE-REVIEW 2026-11-02 (S01 / S02 ESTIMATED) applied; ERS s.2-4, s.7. This round CALCULATES the
quantities that replace the all-HELD V3.0.43 earthworks lines; it does NOT wire them (no engine module, method version,
hub, registry or released quantity changed). The wiring (V3.0.46, lane I) follows the Checker's verdict on this piece.

Files: `earthworks_qty_v1.py` (EARTHWORKS_QTY_V1, stdlib, every villa: depth from EXISTING ground only, exact union of
pit plans, neat excavation + named working space, backfill = excavation - displacement, layers = ceil(zone depth /
lift), loose / compacted / truckloads only with a sourced factor, dry-mass balance with procurement from the placement
target density and an acceptance-density refusal, HELD propagation, never 0); `t350r2_alsenan.py` (merged ledgers only:
T-170 / T-347 pits, T-320 displacement, T-189 / T-183 pool, T-205 necks, T-253 / T-242 runs, T-478 F10 + F scenarios)
-> `FILL_T350R2.csv` (one row per V3.0.43 zone line + 4 coverage-gap rows), `summary_t350r2.json`;
`t350r2_beam_over_pits.py` (own route-G read of the structural DXF from the Drive copy, sha 9f9d1179) ->
`BEAM_OVER_PITS_T350R2.csv` (per ground-beam run: strip and beam plan over the pits zone, by pit) and
`ZONE_INPUT_T350R2.json` (zone plan cross-check, plot rectangle, upper boundary G.B over the pits). Tests
`tests/t350r2_earthworks_quantities/` 31 pass (owner examples, villa E350R2 by hand + adverse, development villa).

## 1. Physical elements and level basis (ERS s.2.1)

Excavation = in-situ soil from the EXISTING ground EG +-0.00 (T-170 / T-253 / T-357 DERIVED) to the formation over
the excavation plan (pit = footing + the printed 0.10 blinding projection, overlapping pits once). Backfill = finished
compacted soil returned up to EG = excavation minus every permanent solid below EG at its position, once. S01
ESTIMATED (owner-accepted): footing underside = the p.9 note 1 minimum -1.50 with the printed chain under it (underlay
0.07 + blinding 0.10, T-206) -> formation -1.67, sensitivity +-0.10. The printed minimum (formation -1.50) stays the
hard lower bound. The pool formation -1.50 is printed (T-183 r2 chain from the rim): a value, not S01.

## 2. Results (m3 unless stated)

| Line (V3.0.43 zone) | V3.0.43 | Proposed | Status / basis |
|---|---|---|---|
| B1-02 pits (24) | blank, >= 188.017207 | **208.164757** (-0.10: 195.699801; +0.10: 220.629712); >= 186.974333 at -1.50 | ESTIMATED (S01); plan 124.649555 m2 x 1.67 |
| B1-02 pool envelope | blank, >= 17.776576 | **17.776576** | DRAWING-CONFIRMED (printed -1.50) |
| B1-02 main exterior GB trench | blank | **1.391722 .. 1.418002** (2.79956 less 1.381558 .. 1.407838 dug with the pits) | DRAWING-CONFIRMED geometry |
| B1-02 F10 + F (S02, three scenarios) | blank | 7.2645 .. 9.352 (F10 alone 7.2645 .. 7.515; F10 + F 8.7675 .. 9.352; outline 8.39175) | ESTIMATED range, scenarios never mixed |
| B1-02 lower GB row (p.13 two-beam) | blank | not required under S01 (2.45 <= 2.50 m); REQUIRED at +0.10 (2.55) | ESTIMATED, flips inside the sensitivity |
| B1-03 pits (24) | blank | **115.553920 .. 128.622353** (before beam solids 130.636230 .. 130.666230) | ESTIMATED range |
| B1-02 FF / annex / court / straps / boundary / D-33; B1-03 pool, ext trench, other trenches, Z2; B1-04 | blank | unchanged HELD (pool and ext-trench backfill: neat part calculated 0, the backfill lies wholly in held working space / projection) | HELD by name |

Pits backfill displacement (m3): blinding 12.464956 (one layer, = 0.10 x plan; T-320 ledger route 12.464902), underlay
7.542559, footings 51.917740, 29 necks at S01 height 5.153642, C8 section conflict 0.24 .. 0.27, strap ends inside the
pits' projection strip 0.179630 (SB1 one end, SB2 / SB3 two), ground-beam solids over the pits 2.043877 .. 15.082310:
main exterior blinding run ends 1.381558 .. 1.407838 (own per-run read), upper boundary G.B 0.136008 (0.340020 m2 x
0.40), annex exterior D-35 0.422531 .. 5.346018, annex interior D-33 0.103780 .. 1.019116, main interior D-33 0 ..
7.173330, main interior with a printed class 0 (above EG). The range width is the D-33 / D-35 beam sections (designer
items): high end = shallowest reading, low end = the solid down to the pit blinding. Information, NOT adopted: the
printed class titles read as the D-33 sections -> 128.547719.

Layers (OWNER-PROVISIONAL 0.15 finished lift): pits zone depth 1.57 m (blinding top to EG) -> **11** (10 / 12 at -+0.10);
under the ext GB blinding 1.47 m -> 10. Formation compaction footprints: pits 124.649555 m2, pool 11.851051 m2, ext
trench 13.917 .. 14.180 m2 outside the pits ('COMPACTED SOIL', p.13). Fill plan beside the footings 16.898712 m2, above
them 119.519555 .. 119.549555 m2.

Computed zones together: excavation in situ 227.333055 .. 227.359335; finished compacted backfill 115.553920 ..
128.622353; displacement below EG 98.710702 .. 111.805415. DISPOSAL stays HELD: the dry-mass balance needs the in-situ
dry density, the placement target density, the suitable share (geotechnical evidence; the drawing prints the fill 'from
excavation material'), the loose densities and the Z2 draw (placed fill EG -> +0.85 under the GF slab, not formed).
The displacement is the geometric surplus only if compacted and in-situ dry densities were equal and nothing went to Z2;
neither is established. Loose m3, imported fill and truckloads: HELD (no measured bulking; owner figures illustrative).
Working space: HELD (not printed, no documented method); the neat quantity stands, the extra is named per zone.

## 3. Findings (for the Checker)

- **F-T350R2-1 (V3.0.43 bound high).** The V3.0.43 pits bound plan 125.344805 m2 removed only F8's pool-envelope part
  and removed F8's beyond-plot strip twice. Own geometry: F4 (outline at 148062, 48723) neat plan 0.735276 m2 and FN
  (146262, 46648) 0.028383 m2 lie inside the pool envelope too; F8's envelope part beyond the plot 0.067868 m2 was
  subtracted twice. Zone plan 124.649555 m2 (T-170 outlines + T-189 frame) = 124.649469 m2 (own route-G read): the
  AT_LEAST 188.017207 m3 beside the V3.0.43 line should read 186.974333 m3 (-1.042874, -0.55 %).
- **F-T350R2-2 (second footing / pool interface).** F4's FOOTPRINT enters the pool envelope 0.483190 m2 and the outer
  shell plan 0.282385 m2 (T-183 / T-189 / T-320 model F8 only). Like F8 it is a CONFLICT (two drawn solids in one
  volume at any founding level): its in-envelope footing / underlay (0.193276 / 0.033823 m3) are taken out of the pits
  zone and held with the pool interface; the pit chains below the pool formation under S01 0.458211 m3 HELD.
- **F-T350R2-3 (beam solids over pits).** About half the main exterior GB blinding (1.38 .. 1.41 of 2.80 m3) lies
  inside the pit plans (short runs between large pits): counted once, in the pits. The D-33 / D-35 sections now carry
  the widest uncertainty of the pits backfill (up to 13.0 m3), larger than the S01 sensitivity on backfill (+-12.0).
- **F-T350R2-4 (coverage gap).** B1-02 has F10 + F and FF zone lines; B1-03 has none: propose two HELD B1-03 lines
  (F10 + F per scenario before the C10 / C necks: 4.5951 .. 6.2912; FF: lift pit depth).
- **F-T350R2-5 (two-beam detail).** The p.13 lower GB row is not required under S01 (2.45 m) but is at +0.10 (2.55 m):
  the S01 sensitivity changes the element list, not only quantities.

## 4. Engine vs freelancer; who is right

Earthworks are absent from the freelancer's BOQ and from the released V2.9 + route G: no comparison; the engine now has
calculated, labelled quantities where both had nothing. Verdict proposal: UNRESOLVED for the HELD zones (formation for
FF, D-33 / D-35 sections, working space, densities); ENGINE_RIGHT is not claimed for any ESTIMATED figure.

## 5. Rule, regression, lessons (ERS s.7)

R-T350-2 (every villa, PROPOSED): depth from existing ground only; one excavation per union of pit plans; a solid that
lies in two zones belongs to the zone whose plan owns it (the pool envelope owns its plan to its formation, the pit owns
what lies below); a beam over a pit displaces pit backfill and its trench excludes that plan; layers from the zone's
backfill depth; no factor without a source; HELD propagates; a calculated 0 only from geometry. Regression: villa
E350R2 (normal) + adverse (overlap, straddling element, zero depth, missing factor / level / suitability, acceptance
density as procurement). Lessons row proposed: 2026-11-03 | a pit-vs-pool exclusion done for the one footing an
earlier ledger named | check every pit against every other zone plan, by geometry, not by the list of known
interfaces | F-T350R2-1 / -2.
