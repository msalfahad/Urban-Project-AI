# T-700: earthworks round 2 (lane S): Z2 placed fill, lift pit FF, annex trench bound, census restated for wiring

Worker 1, 2026-11-11, run session_01E6cPnbrCDbsSDMiiKws44u. Development villa (Drive "Alsenan chalet project",
'ST7757 dxf.dxf' sha 9f9d1179), not an accuracy claim. Research piece for the Checker (Gate A): nothing is wired, no
candidate line moves, released default V2.9 + route G untouched. Owner rules: 2026-11-02 17:20 / 17:45 / 18:00
(geometry always, material by dry mass with measured densities only, 150 mm lift OWNER-PROVISIONAL), S01 ESTIMATED,
R-T505-1, R-T695-1, UP-QTY-STATUS-001.

Files: `earthworks_round2_v1.py` (EARTHWORKS_ROUND2_V1, pure, every villa; R-T700-1 .. 3 in its docstring),
`t700_extract.py` (own DXF read, values / ids / handles only -> `ZONE_INPUT_T700.json`), `t700_alsenan.py`
(-> `WIRING_T700.csv`, `ZONES_T700.json`, `summary_t700.json`). Tests `tests/t700_earthworks_round2/` (villa E700 by
hand with adverse cases; the development villa pinned).

```
.work/venv/bin/python -I research/agents_t700/t700_extract.py <.work/private>/ST7757_dxf.dxf
.work/venv/bin/python -I research/agents_t700/t700_alsenan.py
```

## 1. Z2: placed fill above EG under the GF ground slab (B1-03 Z2, HELD BLANK -> BOUNDED)

**Physical element.** The soil placed and compacted between existing ground EG +-0.00 (T-170 / T-253) and the
underside of the slab on grade ('T=10cm', 'COMPACTED SOIL' under it, p.13; no blinding under the slab, T-100 P7),
inside the ground-beam network. Measured per plan column, never merged with the Z1 backfill:

| Column | Depth | Source |
|---|---|---|
| slab panel | underside - EG; underside = FFL - 0.05 build-up (T-214 DRAWING-CONFIRMED, dry chains) - 0.10 | FFL from the GB-plan LEVEL marks |
| interior ground beam | (top - D - 0.10 blinding) - EG, >= 0; the 0.10 blinding projections above EG are solids in the panel fill | T-242 runs (L face to face, b 0.30, titles 0.30 / 0.40 / 0.60, D-33 / D-34) |
| exterior ground beam | the same over the beam + its outer projection | D-35 0.80 / 0.95 main; 0.10 / 0.25 + printed annex |
| column / neck face, lift shaft and ring | 0 (concrete or void from EG up) | route-G COLUMN / JUNCTION faces |

**Panel levels (own read, `ZONE_INPUT_T700.json`).** The route-G ground sheet splits into two separate beam
networks: the annex block (6 panels, 43.9454 m2, LEVEL marks 1B0 / 1B2 / 1B4 all '+0.30') and the main block (19
panel faces, marks 1BE / 1C0 / 1C2 / 1CD '+1.00' and one '+0.30', 1C9, inside cell c1089bdb). The 26 candidate
GROUND_SLAB lines (21.640885 m3 = 216.40885 m2 at T 0.10) are the plan:

| Class | Panels | m2 | Fill depth m | Fill m3 |
|---|---|---|---|---|
| main GF +1.00 -> slab +0.95 -> underside +0.85 | 19 (c1089bdb by OWN-007 / 010 / 047) | 147.49945 | 0.85 | 125.374530 |
| annex +0.30 -> +0.25 -> +0.15 (+ GS-28, printed +0.30, T-242) | 7 | 45.0854 | 0.15 | 6.762810 |
| GS-08 = OWN-009 stair hall: +1.00 (1C2) and +0.30 lobby (1C9), extents not printed | 1 | 11.52 | 0.15 .. 0.85 | 1.728 .. 9.792 |
| GS-12 'Garden / yard / court', GS-16 room-less: floored +1.00 or court on N.G. (+0.15 paving, T-320) | 2 | 12.304 | 0 .. 0.85 | 0 .. 10.4584 |
| **panels** | **29 terms** | **216.40885** | | **133.865340 .. 152.387740** |

| Beams (T-242) | Runs | L m | Fill m3 | Readings |
|---|---|---|---|---|
| main interior, printed class | 7 | 24.573 | 2.825895 | D 0.40: 0.30 x 0.45 - 2 x 0.10 x 0.10 = 0.115 / m |
| main interior D-34 | 6 | 10.0372 | 1.154278 .. 1.455394 | 0.30 / 0.40 |
| main interior D-33 | 13 | 47.2259 | -0.944518 .. 4.908485 | D >= printed title; low at D = 0.85 (blinding on EG: -0.02 / m) |
| main exterior D-35 (+ arc 157 / 158) | 17 | 55.9912 | 0 .. 0.559912 | 0.95 (on N.G.: 0) .. 0.80 (0.40 x 0.05 - 0.10 x 0.10 = 0.01 / m) |
| annex exterior D-35 | 9 | 29.7063 | 0 .. 0.297063 | literal 0.10 / 0.25 against printed 0.30+ (source conflict) |
| annex interior | 6 | 18.00 | 0 | top +0.25, D >= 0.30: below EG |
| court runs | 3 | 5.70 | 0 .. 1.045 | top +0.10 (court) .. +0.95, candidates per T-242 |

**Z2 = 136.900995 .. 163.479489 m3 compacted** (envelope; each term at its own readings; materials HELD).
Compaction footprint 215.00791 .. 277.51868 m2. Layers at 0.15: main 6 (0.85), annex 1 (0.15), under a main
interior beam <= 4 (0.55). EG sensitivity (whole zone re-run, not mixed): EG -0.10 -> 158.628211 .. 191.231357; EG
+0.10 -> 115.001720 .. 138.298548. No S01 term: every Z2 datum is a printed GF level.

**Owner manual method beside.** Plan x depth: 216.40885 m2 x 0.85 = 183.947523 m3 if the whole slab is taken at the
main GF level. The drawing-derived range is lower by 20.468034 .. 47.046528 m3; the cause in units: the annex and
GS-28 sit at +0.30 (45.0854 m2 x 0.70 = 31.559780), the lobby / court readings (GS-08 / 12 / 16: 0 at their high
ends, 18.522400 at their low ends) and the beam columns (+3.035655 .. +11.091749 net); closes to 0.000003. No figure chosen because it is larger or smaller.

## 2. Lift pit FF (B1-02 / B1-03 Z1-PIT-FF, HELD BLANK -> AT_LEAST)

Element (T-322 merged, p.14): '10cm Plain con.' / membrane / '5cm Screed' / raft 4.60 x 4.50 x 0.55 / pit walls on the
raft top (ring S-BW 10EB 2.20 x 2.20 outer, 10EA 1.80 inner), pit depth 'As Per Lift Manufactures recommendations'.
Own read: FF plan 20.70 m2 (projection 0) and 22.56 (0.10) overlap the pits zone, F10 / F, the pool envelope, every
strap and the plot outside by **0.000 m2** (L-N10-03 checked: nothing to net); ring outer 4.84 m2 wholly inside.

- Founding: p.9 note 1 'not less than 1.50 m below the existing plot level' (Q-21 C: a minimum). Read as the
  formation (smallest reading): excavation >= 20.70 x 1.50 = **31.050 m3**; raft top >= 0.80 below EG, backfill >=
  (20.70 - 4.84) x 0.80 = **12.688 m3** (base, screed, blinding and the plan outside the raft cancel; a drawn
  projection >= the side build-up keeps the bound valid, T-322 s.2: blinding drawn 0.150 beyond the face).
- S01 beside (underside -1.50): 34.155 / 15.067 m3. Upper bound: none (supplier depth). Never a value.

## 3. Annex trench (B1-02 Z1-TRENCH-ANNEX, HELD AT_LEAST -> BOUNDED)

Low unchanged (T-695): 0.877899 m3. High: every annex route-G piece (49.6364 m of route G covers the 47.7063 m of the
T-242 annex runs; 13D+7D2#2, left UNBOUND by the T-350 r2 binding, is taken), free strip (deeper zones removed) x the
deepest admissible formation: a ground beam's formation never lies below the formation of the foundation it frames
into, R3 under S01 = 1.50 + 0.07 + 0.10 = 1.67 m; D-34 interior runs at their printed 0.40 + 0.10 - 0.25 = 0.25 m.
**0.877899 .. 21.407259 m3** (S01 -0.10: 20.139618; +0.10: 22.674901). Without the S01 datum it stays AT_LEAST.

## 4. Wiring form (`WIRING_T700.csv`, one row per line, UP-QTY-STATUS-001 class)

20 B1 lines by id (equal in V3.0.68 and V3.0.69, asserted) + the T-695 strap-backfill split: 5 CONFIRMED (pits 24
208.164757, pool 17.776576, three CALCULATED 0.000 by geometry from T-695), 16 HELD, each naming its missing input.
New in this row: Z2 RANGE, FF AT_LEAST x 2, ANNEX RANGE; B1-04 stays BLANK with Z2 now formed beside and the five
tests named (MDD ASTM D1557, in-situ dry density, loose density, suitability, placement target).

## 5. Who is right

No freelancer earthworks / fill line and no released Z2 line (T-565: NO_ROW): verdict UNRESOLVED (no comparison).

## 6. Held, never 0

Lift pit depth (S14 / D-43, supplier), GS-08 lobby extent and slab-top levels (T-444), GS-12 / GS-16 floored or open
(T-242 architect item), D-33 / D-34 / D-35 and court sections (S8), working space (OQ-13), every material quantity.
Residuals named, not netted: blinding projections beside the GS-08 / 12 / 16 low-level readings (<= 0.01 m3 / m),
beam ends inside the lift junction face (0.0637 m2 x <= 0.55 = 0.035 m3), annex route-G strip corners counted twice
(only loosen the HIGH).

## 7. Rules and lessons row (proposed, ERS s.7)

R-T700-1 .. 3 (every villa, PROPOSED): Z2 is a placed-fill element measured per plan column from the printed FFL chain
with split / unprinted levels by their admissible extremes; a supplier-depth pit is AT_LEAST from the printed founding
minimum, its backfill = plan outside the shell x base-top depth; a designer-depth trench is bounded above by a printed
or owner-accepted foundation formation datum, else AT_LEAST.

| 2026-11-11 | Z2, the term that decides import vs export of soil (T-503), stayed HELD BLANK across eight candidates
although its plan (the 26 released slab lines) and every level were drawn | the zone was framed as one 'enclosed plan x
depth' needing every beam section first, so a single designer item held the whole zone | measure a placed-fill zone
per plan column (panel, beam strip, column) and bound each column by its own readings; one unknown section moves a
range, never blanks a zone (earthworks, every villa) | tests/t700_earthworks_round2 (normal E700 150 m2 x 0.60 = 90
m3, 4 layers; adverse: missing EG / FFL HELD, mm refused, slab below EG, solids > fill, overlap counted once,
HELD as 0 refused) | PROPOSED |
