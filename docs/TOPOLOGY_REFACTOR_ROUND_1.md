# The topology spine, replaced

*Targeted refactor, round 1. Project 23010, drawing AR-00 rev MAR2023.*

The domain and safety architecture is unchanged. What changed is the mechanism
that turns wall geometry into rooms.

---

## A · The old path, falsified

Six invariants of planar embeddings were added to the existing engine. **All
six fail on the real drawing.**

| invariant | violations |
|---|---|
| A · every half-edge in exactly one face walk | 1 — **92 of 696** half-edges in no walk |
| B · Euler `V − E + F = 1 + C` | 1 — `361 − 348 + 33 = 46`, but `1 + 55 = 56` |
| C · signed walk areas reconcile | 9 components |
| D · **no two bounded faces overlap** | **18 pairs** |
| E · no edge pair crosses without a shared node | **40 crossings** |
| F · no ambiguous equal-angle rotation at a node | **46 nodes** |

### The mathematical interpretation

A planar *graph* has cycles. A planar *embedding* has **faces**, and a face is a
connected component of ℝ² minus the embedded edges and vertices. Connected
components of any set are pairwise disjoint.

> **Two distinct bounded faces cannot overlap in area.** This is definitional,
> not empirical.

So the overlaps are proof that the objects produced are **not faces**. The
engine was enumerating cycles of the abstract graph and calling them faces.

**Root cause, in order of significance:**

1. **46 nodes with an ill-defined rotation system.** Two outgoing half-edges at
   *the same angle*, so the angular sort between them is arbitrary, so `next`
   is arbitrary. This is what a portal closure edge laid on its host wall's own
   centreline produces at every jamb — and what a duplicate band produces
   everywhere.
2. **40 crossings with no vertex.** Where a crossing has no node, walks pass
   *through* each other; the drawing is not a planar embedding at all.
3. Consequently 92 half-edges have no `next` and belong to no walk, Euler is
   off by 10, and areas do not cancel.

### A correction to last round

Last round reported SF-V2-0003 and SF-V2-0004 as overlapping each other, and
labelled it `FACE_NESTING_ARTIFACT`. **That was wrong.** It came from a weak
containment test (*any* vertex inside). Measured properly with GEOS:

```
18 of 18 overlap pairs involve FACE-0001 and nothing else
SF-V2-0003 and SF-V2-0004 do NOT overlap each other
```

The single defect is that **FACE-0001 — the 989 m² building boundary — was
walked counter-clockwise and classified BOUNDED**, so it overlaps all 17 rooms
inside it. One defect, not eighteen. The label hid it; the invariant found it.

These checks stay as a regression test. The theorem does not stop being true.

---

## B · Wall polygons

```
input bands       243
resolved          243
refused             0
```

Each band is now the **rectangle between its two drawn faces** — not an offset
from a centreline. A band whose second face was never drawn gets
`WALL_POLYGON_UNRESOLVED` and a stated reason; no thickness is ever
manufactured.

## C · The wall solid

```
valid            243 / 243        source coverage  100%
invalid            0              repaired          0
union area       116.695 m²
union components  46  (60 before node snapping)
```

**Node snapping, and why it is not gap-closing.** Two wall polygons that
genuinely touch came out of the coordinate pipeline **0.003 mm** apart — three
microns, on a drawing whose pixel is 10.8 mm and whose thinnest wall is 100 mm.
GEOS correctly reported them as disconnected, and free space leaked between
rooms sharing a wall.

Coordinates are snapped to a **0.05 mm grid** before the union: 1/200 of a
pixel, 1/2000 of the thinnest wall. It moved the total wall area by
**0.0003 m²** — three square centimetres — and merged 14 of 60 components.
0.05 mm is also where the effect saturates (0.01 → 49 components, 0.05 and 0.1
→ 46), so it is the smallest value that does the job rather than one chosen for
its answer. Anything above 1.0 mm is refused outright.

**The remaining 46 components are real disconnection**, and that is now the
dominant blocker.

## D · Portal partition barriers

```
accepted     19
rejected      4   (open-plan transitions — one physical space)
unresolved   15   (portal geometry not located)
```

A barrier spans the **host wall's own thickness** between the two jambs, so it
plugs exactly the hole the wall solid leaves at a doorway and the free-space
boundary runs continuously along that wall's drawn faces. §7's "same
finish-face basis" is achieved *by construction* rather than by a closure rule.

Every barrier carries `material_role = TOPOLOGY_ONLY_NOT_MATERIAL`.

## E · Building envelope

```
basis     OUTER_BOUNDARY_OF_THE_WALL_SOLID
area      1002.289 m²
```

Derived from the filled outer rings of the wall solid **plus the accepted
barriers** — the barriers matter, because a wall ring with a doorway in it is
not closed, and filling a C-shape's exterior returns the C. Every component is
kept, not just the largest.

Its caveat travels with every candidate: *this is where material is, not a
surveyed floor boundary.* An unresolved envelope refuses to produce free space;
a bounding rectangle is never substituted.

---

## F · Free space — the new production geometry

```
components                    26
occupiable candidates          8
overlapping pairs              0      assert_non_overlapping PASSED
free area                    882.749 m²
components with no wall support 0
```

| candidate | area | labelled rooms inside |
|---|---|---|
| SG-V2-0001 | 738.011 m² | 22 — walls not yet joined |
| SG-V2-0002 | 37.788 m² | 3 |
| SG-V2-0003 | 30.638 m² | **BED-03** |
| SG-V2-0004 | 28.166 m² | 2 (BED-NW + BTH-01) |
| SG-V2-0005 | **21.034 m²** | **BED-01** |
| SG-V2-0006 | 8.213 m² | **BTH-02** |
| SG-V2-0007 | 4.849 m² | MBTH-03 |
| SG-V2-0008 | 3.312 m² | **BTH-05** |

Six single-label occupiable candidates, on the `CLEAR_INTERNAL_FINISH_FACE`
basis **by construction**: no centreline offset, no room-facing-face
determination, no corner correction, no mean-thickness adjustment. On the
L-shaped fixture the new engine returns 18.84 m² — the exact answer the scalar
formula missed by 0.04 m² — and it does not know what a corner is.

## G · Raster ↔ vector

Raster produces **hypotheses** and no millimetres. Every millimetre in this run
came from a drawn wall face.

The §10 distinction is now enforced in the output: `RASTER_SEGMENTATION_OUTPUT`
(36 regions, **automatic accuracy not established**) is reported separately
from `HUMAN_OR_GOLDEN_VALIDATED_REGION_STATE` (35 identity-validated, 33
topology-validated, from human review and the golden overlay). Quoting the
second as evidence for the first would credit the algorithm with a person's
work — and on an unseen project the human column starts empty.

---

## H · Frozen controls — and the exit gate

Selected by rule from the space map before any measurement, unchanged:

| control | result | area |
|---|---|---|
| BATHROOM → **BTH-01** | REFUSED · `MORE_THAN_ONE_LABELLED_ROOM_INSIDE` | 28.166 m² (with BED-NW) |
| BEDROOM → **BED-01** | **ACCEPTED AND FROZEN** | **21.034 m²** |
| STORE → **STR-01** | REFUSED · `MORE_THAN_ONE_LABELLED_ROOM_INSIDE` | 738.011 m² blob |

```
EXIT GATE: PASS
```

## I · The first accepted control

```
space_id           BED-01
geometry_hash      6ef3d4fc44a410d0fb1f2452
clear_internal     21.034 m²   perimeter 18.501 m
basis              CLEAR_INTERNAL_FINISH_FACE
bbox edges         0        raster millimetre edges  0
centreline offset  False    scalar conversion        False
bounded by         drawn wall faces + 1 supported portal barrier
```

The hash covers the polygon **and its provenance** — the same coordinates
reached a different way are a different result.

**Then, and only then, the reference was opened:**

```
vector clear area      21.034 m²
raster region area     24.642 m²
absolute difference     3.608 m²
area error              14.64%
```

The perimeter comparison is reported as **not comparable**: the raster
reference's boundary is 4.65× the perimeter of the square with its own area.
That is a pixel staircase around a ragged mask, and scoring against it would
report the reference's raggedness as this engine's error. No threshold is
defined from one room on one project.

---

## J · Old path vs new path, same frozen input

| | old graph path | new free-space path |
|---|---|---|
| mechanism | custom half-edge walk | GEOS union / difference |
| space objects | 19 cycles | 26 components |
| single-room candidates | 5 | 8 |
| **overlapping pairs** | **18** | **0** |
| clear-internal basis | offset from a centreline | by construction |
| failing planar invariants | A B C D E F | n/a — no rotation system |
| may release geometry | **no** | yes |

The old path is demoted to `DIAGNOSTIC_TOPOLOGY_PATH`, runs on the same input,
and cannot release geometry.

## K · Tolerance sensitivity

Node snap grid perturbed ±20% (0.04 / 0.05 / 0.06 mm):

```
resolved wall polygons   243   243   243
solid components          46    46    46
occupiable candidates      8     8     8
stable: True
```

## L · Second project — source audit ready, not yet run

The audit tool counts **representations, not errors**, so it may run on an
unseen project without spending its benchmark. On AR-00 it reports:

```
segments 74,148   curves 2,399   heavy pen 1.14 pt
DOUBLE_LINE_WALL   615.1 m paired
SINGLE_LINE_WALL   851.0 m unpaired wall-pen face length
verdict  PARTIALLY_SUPPORTABLE  (42% pairs)
```

That 42% is the most important number in this report after the exit gate. The
unpaired remainder is single-line wall, filled wall, or wall-pen marks that are
not walls — and the three need telling apart. **No project 2 file is in the
repository yet**; obtaining one is a prerequisite, not a task this round could
complete.

## CAD oracle

A hook, deliberately inert: `CAD_SOURCE_NOT_AVAILABLE`. Its shape is fixed now
so that when a DXF arrives it cannot quietly become an input to the run it is
meant to judge.

---

## What this round did not do

No architectural BOQ release, no structural quantities, no materials, no
pricing, no procurement. The owner-facing / diagnostics workbook split is
recorded as a principle and deliberately not built.
