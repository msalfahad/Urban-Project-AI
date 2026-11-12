# T-708: earthworks round 3 (lane S): Z2 plan x depth reconciled term by term, the disposal / import balance restated on the T-695 / T-700 geometry, dry-mass inputs, wiring form for T-509

Worker 1, 2026-11-12. Development villa (Drive "Alsenan chalet project", 'ST7757 dxf.dxf' sha 9f9d1179), not an
accuracy claim. Research piece for the Checker (Gate A): nothing is wired, no candidate line moves, released default
V2.9 + route G untouched. Owner rules: 2026-11-02 17:20 / 17:45 / 18:00, R-T505-1, R-T700-1, UP-QTY-STATUS-001.

Files: `balance_restate.py` (pure, every villa: `reconcile_plan_x_depth` R-T708-1, `restate_terms` R-T708-2,
`break_even_yield`, `dry_mass_inputs`; DISPOSAL_BALANCE_V2 called unchanged, no new method version),
`t708_alsenan.py` (pinned inputs `PINS_T708.json` -> `RECON_Z2_T708.csv`, `BALANCE_T708.json`, `WIRING_T708.csv`,
`summary_t708.json`). Tests `tests/t708_disposal_restated/` (villa E708 by hand + adverse; development villa pinned).

```
.work/venv/bin/python -I research/agents_t708/t708_alsenan.py
```

## 0. Evidence re-read

- 'ST7757 dxf.dxf' downloaded (read only), sha 9f9d1179 = T-700's; `t700_extract.py` re-run on it reproduces
  `ZONE_INPUT_T700.json` byte for byte and `t700_alsenan.py` reproduces `ZONES_T700.json` / `WIRING_T700.csv` (git
  clean after both runs).
- Own text census of the ST DXF (409 distinct texts, model space, layouts, blocks): 'T=10cm' (x2), 'B.C Kg/cm' /
  '2.20 kg/cm' (bearing capacity), nothing on fill density, compaction, Proctor, soil report or disposal. The densities
  therefore have no drawing source: HELD, the tests named (s.3).
- Earthworks and ground-slab lines of the newest candidate V3.0.73 (T-722) equal V3.0.69 (T-700's record) and the
  V3.0.50 figures T-505 used (asserted line by line).

## 1. (a) Z2: owner plan x depth against the drawing-derived zone, term by term

**Physical element.** Placed, compacted soil between EG +-0.00 and the underside of the slab on grade, inside the
ground-beam network (T-700 s.1). **Owner manual method:** the slab plan (the 26 released ground-slab lines,
216.40885 m2) x one depth 0.85 (main GF +1.00 - 0.05 build-up - 0.10 slab) = **183.947522 m3**.
**Drawing-derived:** 29 panel terms (one per line; c1089bdb by its four own panels) + 61 ground-beam runs =
**136.900995 .. 163.479489 m3**. Every term is in `RECON_Z2_T708.csv` with its line id, owner m3, engine m3, delta and
its drawn cause.

| Cause (drawn element) | Terms | Low end m3 | High end m3 |
|---|---|---|---|
| main panels at GF +1.00: engine depth = owner depth 0.85 | 16 + 3 own | 0 | 0 |
| annex panels and GS-28 at +0.30: 45.0854 m2 x (0.15 - 0.85) | 7 | -31.559780 | -31.559780 |
| GS-08 lobby (+0.30 / +1.00), GS-12 / GS-16 (court on N.G. / floored +1.00): level not printed for the extent | 3 | -18.522400 | 0 |
| fill under main interior beams, printed D 0.40 (0.115 m3/m) | 7 | +2.825895 | +2.825895 |
| the same, D-34 runs | 6 | +1.154278 | +1.455394 |
| the same, D-33 runs (at D 0.85 only the blinding projections remain: negative) | 13 | -0.944518 | +4.908485 |
| main exterior D-35 runs | 17 | 0 | +0.559912 |
| annex exterior D-35 (literal 0.10 / 0.25 vs printed 0.30+) | 9 | 0 | +0.297063 |
| court beams (section and top not printed) | 3 | 0 | +1.045000 |
| annex interior D-33 / D-34 (below EG) | 6 | 0 | 0 |
| **engine - owner** | **90** | **-47.046527** | **-20.468033** |
| residual | | 0.000002 | 0.000002 |

Residual: rounding only (90 terms at 6 decimals against the owner total rounded once); the tool refuses any residual
above the rounding bound, and refuses a plan that differs from the panel sum (a plan difference is a cause, never a
residual). The difference is physical: the owner single depth over-states the +0.30 annex / GS-28 floor by 0.70 m and
the unprinted lobby / court extents by up to 0.85 m, and omits the soil under the ground beams (outside the slab plan).
On the 147.49945 m2 at the main level the two methods agree exactly (125.37453 m3). Neither figure is chosen because
it is larger; the owner figure stays beside as a check.

## 2. (b) the R-T505-1 balance restated on the T-695 / T-700 geometry

DISPOSAL_BALANCE_V2 (T-505) run twice, unchanged, every density, the suitable share and both losses HELD:

| | A: candidate of record (V3.0.73 = T-505) | B: T-695 / T-700 wiring rows taken |
|---|---|---|
| excavation E closed, in situ | 233.205833 .. 234.333083 (9 lines open) | 244.034031 .. 271.861583 (6 open) |
| fill demand D closed, compacted | 119.963335 .. 128.643547 (6 open) | 256.864330 .. 292.123036 (3 open) |
| disposal, s = 0 end (pure geometry) | at least 234.333083 m3 [ESTIMATED] | at least 271.861583 m3 [ESTIMATED] |
| import, s = 0 end | at least 128.643547 m3 | at least 292.123036 m3 |
| s = 1 ends | HELD | HELD |
| residual against the closed lines | 0 / 0 | 0 / 0 |

A -> B per line (R-T708-2): straps cut +9.950299 .. 16.121241 (ESTIMATED: D-15 x S02 on S01), annex trench +0.877899 ..
21.407259 (ESTIMATED: R3 datum under S01), Z2 +136.900995 .. 163.479489 (PARTIALLY VERIFIED: T-700 Gate A, readings
enveloped), three CALCULATED zeros (interior GB trench, pool backfill, external GB trench backfill). s = 0 change:
disposal +37.528500 (= 16.121241 + 21.407259), import +163.479489 (= Z2 high).
Beside, never summed: lift pit FF cut at least 31.050 and backfill at least 12.688 (supplier depth), the external GB
trench 1.069269 .. 1.176467 (BOUNDED_EXPOSURE, as T-505), the strap backfill split 6.437519 .. 10.952471 (no line id
until lane I mints it).

**What Z2 changes physically.** Break-even yield on the closed parts, k* = E / D (in-situ m3 per compacted m3 at which
the excavated soil exactly covers the fill), an indicator, never a quantity: A 1.812806 .. 1.953373, B 0.835381 ..
1.058386. With every excavated m3 suitable (s = 1), the closed parts of B export soil only if k = rho_target /
rho_insitu is below 0.835 .. 1.058 and need import above it. Which side the villa is on is decided by the two density
tests, not by the geometry: no default k is used.

## 3. Dry-mass inputs per zone (all HELD; `summary_t708.json` "dry_mass_inputs")

| Zone (T-700 marked *) | Volume basis | Volume m3 | Needs |
|---|---|---|---|
| Z2 * | compacted (placed) | 136.900995 .. 163.479489 | placement target dry density (project spec x MDD, ASTM D1557) |
| lift pit FF cut * | in situ | at least 31.050 | in-situ dry density (ASTM D6938 / sand cone), and the pit depth (supplier) |
| lift pit FF backfill * | compacted | at least 12.688 | placement target dry density, and the pit depth |
| annex trench * | in situ | 0.877899 .. 21.407259 | in-situ dry density |
| pits 24 / pool / F10F / straps cut | in situ | 208.164757 / 17.776576 / 7.2645 .. 8.39175 / 9.950299 .. 16.121241 | in-situ dry density |
| pits 24 backfill | compacted | 119.963335 .. 128.643547 | placement target dry density |
| 9 lines BLANK | | HELD | the zone volume first |

Each mass is an expression (volume x density), never a figure; a sourced density turns it into t (tested on E708).
Also needed for the s > 0 ends: the suitable share (geotechnical classification) and the reuse handling loss
(R-T505-1); for loose / trucks: a measured bulking; none exists for this villa.

**Scope note for the Checker (no change made):** the owner 150 mm lift (2026-11-02 18:00) is worded for
*foundation-adjacent backfill*. T-700 counts Z2 (under-slab placed fill, 0.85 deep) in 0.15 lifts (6 layers). Z2 is not
foundation-adjacent backfill in the literal sense; the layer count of Z2 is therefore OWNER-PROVISIONAL by extension,
and a project / geotechnical lift for under-slab fill governs if one appears. No quantity depends on it here (layers
are not a payable quantity in this round).

## 4. (c) Wiring form for T-509 (`WIRING_T708.csv`)

| Scenario | B1-04 disposal L-78d7c8a989ab34527a1c | import (no line) | precondition |
|---|---|---|---|
| A | HELD BLANK -> AT_LEAST 234.333083 m3 in situ, low end HELD | at least 128.643547 beside | T-509 as queued (candidate of record) |
| B | AT_LEAST 271.861583 m3, low end HELD | at least 292.123036 beside | only after the T-695 / T-700 rows are wired in the same or an earlier candidate |

T-509 must take scenario A unless the T-695 / T-700 rows land first, and must never mix the two (a B disposal on A
lines would value 37.5285 m3 of HELD excavation). Residual against the closed lines is 0 in both. loss_reuse stays
outside payable; no bulking factor.

## 5. Who is right

No freelancer earthworks / fill / disposal line and no released Z2 or disposal line: UNRESOLVED (no comparison). The
owner plan x depth vs engine: RULE_DIFFERENCE explained in full (s.1), not a defect of either.

## 6. Held, never 0

Every density (in situ, placement target, loose), the suitable share, both losses, the lift pit depth, the GS-08 /
12 / 16 levels and extents, D-33 / D-34 / D-35 and court sections, the boundary band, working space (OQ-13), the
strap backfill line id.

## 7. Rules and lessons row (proposed, ERS s.7)

R-T708-1 (every villa, PROPOSED): an owner single plan x depth for a placed-fill zone is reconciled term by term to the
per-column measurement: delta = A (d - d_owner) for a panel, the whole term for a column outside the owner plan; the
causes add to the difference at both ends; only a rounding residual is accepted; a plan difference is a cause.
R-T708-2 (every villa, PROPOSED): the disposal balance is restated on a wiring form only by line id (VALUE / RANGE /
calculated ZERO closed with their source status; AT_LEAST and id-less rows beside, never summed); the candidate-of-
record run stays beside and the scenario a candidate line uses is named in the wiring.

| 2026-11-12 | Z2 (163 m3 high) turns the villa from "export only" to "possibly a net importer": the s = 0 import grew by
163.479489 m3 and the break-even yield fell from 1.81 .. 1.95 to 0.84 .. 1.06, yet the disposal line queued for wiring
(T-509) was still computed on the pre-T-700 geometry | balances are run once on the candidate of their day and not
restated when the zones they sum are bounded later | restate the balance whenever a summed zone changes bound, keep
both runs, and name the scenario in the wiring row (earthworks, every villa) | tests/t708_disposal_restated (normal
E708 disposal >= 120, import >= 60, k* 1.833 .. 2.4; adverse: line missing from the form, HELD status on a closed
term, unsourced zero, missing density -> expression, never a mass or 0) | PROPOSED |
