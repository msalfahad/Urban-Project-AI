# A cycle is not a room: geometry, identity, and the real clear-internal polygon

*Round after the first SPACE_BOUNDARY E31A run. Project 23010, drawing AR-00.*

---

## 1 · The regression that set the agenda

The last report said:

```
WSH-01  ->  VALIDATED_PHYSICAL_FACE
```

WSH-01's associated raster region is the **hatched shaft beside the washroom** —
established several rounds ago and recorded in the topology overlay as
`region_identity: FAILED`. The engine had found a genuinely sound 1.981 m²
cycle and called it a validated washroom.

Nothing about the geometry was wrong. **One field was answering two questions:**

| | question | answer for WSH-01 |
|---|---|---|
| `VECTOR_FACE_GEOMETRY_STATUS` | is this a valid closed face? | `VALIDATED_GEOMETRIC_FACE` |
| `PHYSICAL_SPACE_IDENTITY_STATUS` | is this face the room we named? | `IDENTITY_REJECTED` |

`PHYSICAL_SPACE_GEOMETRY_ACCEPTED` now requires **both**, and is unreachable
from either alone. This run:

```
geometry VALIDATED, identity insufficient    3
identity REJECTED                            1   (WSH-01)
PHYSICAL_SPACE_GEOMETRY_ACCEPTED             2   (BED-03, MBTH-02)
```

The 1.981 m² cycle is a valid face. It is **not** the washroom, and the real
washroom's geometry has still never been recovered. WSH-01 is back on the
hard-case list.

**One label inside one cycle is a candidate, never a validation.** A face
holding exactly one label can still be a shaft, a closet, an adjacent
enclosure, a wrongly nested cycle, or the wrong side of a wall. Identity needs
independent families — and a *stated contradiction* outranks any amount of
supporting evidence, because the support is exactly what was mistaken.

---

## 2 · The scalar area conversion is retired

Last round converted centreline area to clear-internal area with:

```
CLEAR ≈ CENTRELINE − PERIMETER × MEAN_HALF_THICKNESS
```

It has **no corner term**, and inside and outside corners contribute with
opposite sign. On the L-shaped fixture:

```
centreline            21.00 m²
scalar conversion     18.80 m²
measured polygon      18.84 m²      five outside corners +0.01, one inside −0.01
```

Mixed 100 / 150 / 200 mm walls break it again — there is no single thickness to
halve. It survives only as `DIAGNOSTIC_APPROXIMATE_BASIS_CONVERSION`.

---

## 3 · The clear-internal polygon is now built, not derived

`engine/clear_internal.py` walks

```
room-facing wall face → portal closure on the SAME basis → next room-facing face
```

and takes each corner as the **intersection of consecutive offset lines**,
which is what makes inside and outside corners both come out right with no
special case for either.

**Wall-side ownership** is decided on evidence, never by being nearer: probe
each way from the edge midpoint and test containment in the face the graph
produced. A single-face band returns `OWNERSHIP_AMBIGUOUS` — *never invent the
missing half*.

**Portal closures follow the host wall's room-facing face.** Closing a
finish-face polygon to a centreline endpoint would put a step half a wall wide
into the boundary at every door.

This run:

```
candidates                              5
complete clear-internal polygons        2
ownership VALIDATED                    23
ownership UNRESOLVED                    8   ← the whole reason 3 are incomplete
portal closures on the clear face       2
```

The centreline face is kept alongside, and nothing converts between them.

---

## 4 · The bounded-area total was a category error

```
bounded area = 1102.64 m²
```

That figure added a 989 m² cycle to the cycles **inside** it. Cycles are now
classified by containment first:

| class | n | area |
|---|---|---|
| `BUILDING_ENVELOPE` | 1 | 989.16 m² |
| `ATOMIC_SPACE_FACE` | 5 | — |
| `ENCLOSURE_CYCLE` | 2 | — |
| `HOLE` | 3 | 2.79 m² |
| `WALL_CAVITY` | 4 | 0.96 m² |
| `MICRO_FACE` | 1 | 0.28 m² |
| `UNRESOLVED_NESTED_FACE` | 3 | 66.98 m² |

**Atomic area: 42.47 m²**, holes deducted, checked for overlap and nesting
before being added. `assert_additive` refuses a total over a face set that is
not atomic.

SF-V2-0001 is a `BUILDING_ENVELOPE_CANDIDATE` holding 27 labelled rooms — not
"a room whose dividing walls are missing". Calling it that would send the next
round hunting for a wall the building never had.

---

## 5 · The two multi-room cycles are not missing a wall

| cycle | rooms | divider cause |
|---|---|---|
| SF-V2-0003 (32.66 m²) | BED-01 + BTH-02 | `FACE_NESTING_ARTIFACT` |
| SF-V2-0004 (31.52 m²) | BED-NW + BTH-01 | `FACE_NESTING_ARTIFACT` |

**They overlap each other** without either containing the other. No wall band
and no rejected wall face lies on either candidate divider line, and every
portal on both cycles is hosted. So the walk itself is suspect before any wall
is blamed — which is precisely why "assume a missing wall" was the wrong
default.

---

## 6 · The controls were frozen before the answer

Selected by rule from the space map alone — no area, no error, no face, no
cycle took part, and the selector **raises** if handed one:

> the lowest-numbered IN_SCOPE space of each required room type, excluding
> spaces with a stated prior defect

| type | control | vector face | clear polygon |
|---|---|---|---|
| BATHROOM | BTH-01 | — | — |
| BEDROOM | BED-01 | — | — |
| STORE | STR-01 | — | — |

**All three produced nothing.** BTH-01 and BED-01 are inside the two
overlapping enclosure cycles; STR-01 has no cycle at all. That is the honest
result of freezing the set before looking at it, and it is a much better
measure of where the engine is than the rooms that happened to work.

---

## 7 · Geometric comparison, where and only where bases match

| room | vector clear | IoU | vector-only | raster-only |
|---|---|---|---|---|
| SHF-01 | 1.173 m² | 0.837 | 0.191 m² | 0.000 m² |
| REC-01 | 1.173 m² | 0.842 | 0.184 m² | 0.000 m² |

Both are shafts whose identity is `IDENTITY_AMBIGUOUS`, so these are shape
measurements, not room accuracy. `raster_only = 0` in both cases: the vector
polygon **contains** the raster region and is about 0.19 m² larger.

Three rows say `comparable: false` and why, rather than scoring. Comparing
across bases raises rather than returning a number, and `IoU` exists because
area alone cannot see a polygon of the right size in the wrong place.

**No acceptance threshold is defined.** One project is not a population.

---

## 8 · Still deferred

Structural quantities, concrete, rebar, AAC / ACICO, solid block, lintels,
شرمات, plaster and paint recipes, MEP recipes, waste %, pricing.

```
VALIDATED GEOMETRY → VALIDATED QUANTITY → APPROVED RECIPE
  → CALCULATED MATERIAL → PROCUREMENT ALLOWANCE → COST
```

A cycle becomes a room quantity only when its geometry is valid, its identity
is valid, its clear-internal boundary is built from actual room-facing wall
faces, it is not an envelope / hole / nested cycle / cavity, and it does not
overlap another accepted atomic space.
