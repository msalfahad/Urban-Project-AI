# Real space polygons: the first run of E31A on both graphs

*Round after LENGTH_ONTOLOGY_V1. Project 23010, drawing AR-00 rev MAR2023.*

The bounding-box room model is retired. This round replaces it with a global
`SPACE_BOUNDARY_GRAPH` and runs the **unchanged** face walker over it, so that
any difference between the two results is caused by the input graph and not by
the engine being tuned toward the answer.

---

## 1 · What was built

```
MATERIAL_WALL_GRAPH                 243 physical edges, band ids as identity
  + geometry-supported host-wall openings   19 zero-material closure edges
  = SPACE_BOUNDARY_GRAPH            262 edges
```

Refused entry, and counted rather than dropped:

| refusal | n | why |
|---|---|---|
| `OPEN_PLAN_SEMANTIC_BOUNDARY_IS_NOT_PHYSICAL_TOPOLOGY` | 4 | an open-plan transition is one physical space |
| `PORTAL_GEOMETRY_UNRESOLVED` | 15 | the opening may exist; its jambs are not located |

Every edge carries `boundary_type`, geometry, its five length bases, source
band ids, portal id, host wall band id, evidence and validation status.

**Identity is by id.** An edge is joined to its noded split fragments through
`pair_id`. The material graph's edges were renumbered from positional `WP-0001`
names to wall-band ids for exactly this reason: `ORDER IS NEVER IDENTITY`.

---

## 2 · The same walker, two graphs

| | MATERIAL_WALL_GRAPH | SPACE_BOUNDARY_GRAPH |
|---|---|---|
| bounded faces | 14 | **19** |
| unbounded | 12 | 13 |
| unclosed walks | 48 | 46 |
| bounded area | 1000.26 m² | 1102.64 m² |

**Five faces exist only because doorways were closed.** That is the hypothesis
confirmed, on the one condition that made it worth testing: `engine/planar.py`
was not touched.

---

## 3 · What the 19 faces actually are

Containment of a labelled region's centroid in the face **polygon** — not
bounding-box overlap, which put every room in the villa inside the 989 m²
building face because that box contains every other box.

| verdict | n |
|---|---|
| `SINGLE_ROOM_CANDIDATE` | **5** |
| `MULTI_ROOM_FACE_DIVIDING_WALLS_MISSING` | 3 |
| `NO_LABELLED_ROOM_INSIDE` | 11 |

```
SF-V2-0001   989.16 m²   36 labelled rooms inside   the building envelope
SF-V2-0002    33.28 m²   BED-03                     closed via 1 portal
SF-V2-0003    32.66 m²   BED-01 + BTH-02            dividing wall missing
SF-V2-0004    31.52 m²   BED-NW + BTH-01            dividing wall missing
SF-V2-0005     3.69 m²   MBTH-02                    closed via 1 portal
SF-V2-0006     1.98 m²   WSH-01
SF-V2-0007     1.78 m²   SHF-01
SF-V2-0008     1.74 m²   REC-01
```

This is the honest state. The graph now produces polygons; most of them are not
yet **per-room** polygons, because interior walls are still missing from
extraction and several rooms remain merged into one face.

---

## 4 · Per-room accuracy — and a basis trap

A planar face walks **wall centrelines**. A raster region is the **clear
internal** opening between finished faces. They differ by half a wall thickness
all the way round, and on a 5.5 m bedroom that is ~10 % of the area — which
would be read as 10 % error by anyone who did not know the bases differed.

So the centreline area is brought onto the clear-internal basis before any
percentage is taken, by `MINUS_PERIMETER_X_MEAN_HALF_WALL_THICKNESS`, and the
adjustment is reported as its own column rather than folded in.

| space | centreline | adjustment | comparable | raster | abs % |
|---|---|---|---|---|---|
| BED-03 | 33.285 | −2.316 | 30.969 | 30.119 | **2.83** |
| MBTH-02 | 3.687 | −0.587 | 3.100 | 3.483 | 10.98 |
| REC-01 | 1.740 | −0.442 | 1.298 | 1.024 | 26.75 |
| SHF-01 | 1.777 | −0.455 | 1.321 | 1.024 | 29.06 |
| WSH-01 | 1.981 | −0.469 | 1.512 | 1.006 | 50.33 |

```
median abs %   26.75
p90 abs %      50.33
worst room     WSH-01
total (SECONDARY)  4.22 %
```

The total is the point of §22 made in one line: **4.22 % against a median of
26.75 %.** Over- and under-measurements cancel. A project percentage would have
reported this engine as accurate.

No acceptance threshold is defined. One project is not a population, and a
threshold set from this run would be a number chosen to pass.

---

## 5 · Portals: existence and geometry, separately

| | existence | geometry |
|---|---|---|
| VALIDATED | 2 | 2 |
| PROBABLE | 17 | 17 |
| CANDIDATE | 19 | 19 |

The two validated portals are the project's first, and they come from
`GEOMETRY + SYMBOL`: door **swing arcs**. Curves were previously counted and
discarded — correctly, since a flattened curve must never join the line pool
pretending to be a drawn line — but a symbol that is never read cannot
corroborate anything. Arcs are now kept as arcs, grouped per drawn path (a
swing is one path decomposed into several bezier items; measuring items
individually reads a quarter-arc as a small curve and throws the symbol away).

15 door-scale arcs on a sheet with far more doors than that: a swing is
**supporting evidence and never a condition**. Sliding doors, pocket doors and
open transitions have no arc at all.

37 of 38 portals name the wall band they are a hole in. The one that does not
may still close a space and contributes **nothing** to any gross line.

---

## 6 · The two controls that must not be forced

**STR-01 — first real concave control.** No face recovered. The 2606 mm wall is
**not** repaired, no rectangle is expected of it, and the raster outline was not
used to construct one. The test remains whether the space graph produces the
L-shape on its own.

**OPEN-01 — open-plan control.** One physical space, `NOT_CLOSED`, four
open-plan edges refused entry to the physical topology. Dining, saloon and
circulation remain functional zones with zero material **and** zero host wall.
A face invented between saloon and dining would be fiction.

---

## 7 · Closure is graded now

`"BED-01 closes"` was always a statement about the model. Three grades:

| space | grade |
|---|---|
| WSH-01 | `VALIDATED_PHYSICAL_FACE` |
| BTH-01 / BTH-02 / BTH-03 / BTH-05 / BED-01 | `DIAGNOSTIC_INTERVAL_CLOSURE` |
| STR-01 / OPEN-01 / BED-04 | `NOT_CLOSED` |

Only a planar face on the space graph earns `VALIDATED_PHYSICAL_FACE`. Interval
coverage over four sides earns `DIAGNOSTIC_INTERVAL_CLOSURE` and says why in
the same breath: the sides it covered came from a rectangle nobody proved.

---

## 8 · Recorded, not implemented

Future source hierarchy:

```
IFC / BIM  >  DWG / DXF  >  VECTOR PDF  >  RASTER PDF
```

PDF text arrives as **real text objects or as glyph/vector outlines**, so
future semantic and document extraction must support both — a drawing whose
room names are outlines is not a drawing without room names.

A future structural pipeline will parse column, beam, slab and reinforcement
schedules, dimensions, bar marks, diameters, counts and spacing. **No
structural quantity work begins until architectural geometry is stable.**

Still not started: pricing, material recipes, structural BOQ, production E34,
client BOQ release.
