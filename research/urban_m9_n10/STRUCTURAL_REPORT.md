# Structural report (Phase N10)

## 1. Scope

```
python3 -I tools/struct_n10.py --run OUT --out DIR [--facts FACTS.json]
```

The tool runs `engine/source/struct_n10.py`. It reads the route G registers of a `tools/urban_boq_m2.py` run, read only:

- `PROVISIONAL_REGISTER.csv`;
- `UNRESOLVED_REGISTER.csv`;
- `VERIFIED_REGISTER.csv`.

It writes FORMWORK.json, FORMWORK_FACES.csv, EXCAVATION.json and REBAR_AUDIT.json. It never changes a concrete or steel quantity. Route G and the frozen M1 pipeline (CRITICAL) are untouched, and a test checks that every route G file's SHA-256 is unchanged after a run.

## 2. Concrete

Concrete is unchanged: route G's own volumes. The face sets are checked against them (conservation):

- soffit × depth = the beam's volume;
- sides / perimeter + slab thickness = the column's height;
- sides / (2 (L + W)) × L × W = the footing's volume.

These hold for every element of synthetic villa seeds 3 and 5.

## 3. Formwork faces (UP-FW-001, REQUIRES_CONFIRMATION)

| Element | Face | State | Rule |
|---|---|---|---|
| slab (structural) | soffit | MEASURED | the slab face area (members' overlap deducted) |
| slab | free edges | HELD | edges are not in the register (OQ-12) |
| ground slab | soffit | MEASURED = 0 | on grade |
| beam | soffit | MEASURED | net plan (width × clear length, columns and junctions out) |
| beam | sides | CONDITIONAL | BELOW_SLAB: 2 × L × depth; TOTAL: 2 × L × (depth − t) (OQ-11; route G's own BEAM_DEPTH_CONVENTION) |
| column | sides | UPPER_BOUND | perimeter × (storey height − slab thickness); faces covered by framing beams not deducted (OQ-12) |
| footing / ground beam | sides | CONDITIONAL | FORMED / EARTH_CAST (OQ-10) |
| footing / ground beam | base | MEASURED = 0 | on blinding |
| neck, stair, lintel, unresolved row, other | — | HELD | with the reason (e.g. NECK_HEIGHT, STOREY_HEIGHT_NOT_PRINTED) |

Conditional alternatives are reported side by side and never summed. A held face is never zero.

| Proof | Expected (design spec) | Engine |
|---|---|---|
| seed 3: footing sides (FORMED) | 62.40 m² | 62.40 |
| seed 3: column sides | 163.072 m² | 163.072 |
| seed 3: slab soffit | 236.38 m² | 236.38 |
| seed 3: beam soffit | 36.32 m² | 34.76 measured + 1.56 held (two unlabelled spans, 0.78 m² each) |
| seed 5: footing / column / slab | 47.36 / 157.248 / 348.955 m² | equal |
| seeds 1 – 8 | footing, column and slab faces equal the design on all 8 seeds (slab soffit to 1e-4: route G's rounding) | — |

**Structural reference drawing** (private, aggregates only):

- faces produced for 112 beams, 26 footings, 3 ground beams and 75 slabs;
- 115 column faces held: the storey heights are not printed (route G's own concrete is unresolved for them too) and the neck heights are not given;
- 59 ground beams held: unbound in route G.

## 4. Excavation and backfill (UP-EXC-001, REQUIRES_CONFIRMATION)

- Pit per footing: (L + 2 ws) × (W + 2 ws). Trench per ground beam: clear length × (width + 2 ws).
- Volume = plan × depth, **only** when the depth (or NGL and the founding level) and the working space are stated facts.
- Several pits give an UPPER_BOUND: pit positions are not in the register, so overlapping neighbours are not merged.
- Backfill is held: it needs the buried concrete below ground level, necks included.

| Proof | Expected | Engine |
|---|---|---|
| 1.8 × 1.6 m footing, ws 0.30, depth 1.50 | (2.4 × 2.2) × 1.5 = 7.92 m³ | 7.92 |
| no facts | held; footprint 2.88 + 1.50 m² | held; 4.38 m² |

The structural reference drawing has 29 pits / trenches. The volume is held (no levels, no working space).

## 5. Reinforcement audit

- Unit mass: d²/162 against π/4 × d² × 7850 kg/m³ for d 6 – 32 mm. The site rule is within 0.2 % (it is +0.12 %). The project's method (engine.source.rebar_unit_mass) is compared row by row, with a deviation of 0.
- Derivation of every reinforcement row:
  - D2_OVER_162 (count × length × d²/162);
  - COUNT_X_LENGTH (a physical-bar model);
  - RATIO (kg/m³);
  - UNSTATED (an unresolved row with no formula).
- A ratio labelled as a measured or source-complete quantity is a **violation**.

| Run | Rows | Violations |
|---|---|---|
| synthetic villa seeds 3, 5 | all D2_OVER_162 / COUNT_X_LENGTH | 0 |
| structural reference drawing | 390 D2_OVER_162, 75 COUNT_X_LENGTH, 30 UNSTATED (unresolved, no quantity) | 0 |

No ratio is labelled as measured anywhere.

## 6. Not done (structural)

- Formwork, excavation and backfill are not yet lines of the BOQ workbook. They are separate files.
- Beam–column adjacency and slab free edges: these need the structural plan (OQ-12).
- Stair, lintel and neck formwork: held.
