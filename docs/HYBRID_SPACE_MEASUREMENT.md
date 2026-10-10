# Hybrid space measurement

*Round 3. The correction: stop matching raster contour runs to vector
objects. The region says WHICH space; the vector says where its boundary
is.*

The round's result in one line: **the mechanism works exactly as specified
on rooms whose walls are all drawn, and AR-00 has three of them.**

---

## 1 · The freeze came first

`docs/ENCLOSURE_FREEZE.json`, committed before AR-00 was evaluated:

```
ALGORITHM              SUPPORTED_LINE_ARRANGEMENT_FLOOD_FILL_V1
FREEZE HASH            01ff128e7ffdab820805dce1
synthetic fixtures     14 built, 14 pass
refusals delivered     4 of 4
```

Every threshold is justified from geometry or from the medium's measured
noise floor, and each states its own reason in `frozen_parameters()`. The
self-test re-asserts the freeze on every pipeline run, so AR-00 is an
evaluation dataset and cannot quietly become a tuning dataset.

## 2 · The mechanism

A flood fill through an **arrangement of supported lines**. Take the drawn
faces, end caps and jambs near the region; cut the neighbourhood into cells
on their coordinates; block a cell edge only where a line is actually DRAWN
across it; flood from a point inside the region. What the flood cannot
escape is the enclosure.

Three properties hold **by construction, not by a rule**:

- **A fixture is invisible.** A bathtub is not a boundary candidate, so it
  cannot block a cell edge and cannot indent a result. There is no
  detour-rejection test because a detour cannot arise.
- **A wall that stops short does not close.** A line blocks only over its
  drawn extent, so the flood escapes through the gap. Nothing is extended
  until it hits something.
- **A corner is an intersection, not an invention.** Vertices are where two
  blocked edges meet. A corner with only one side supported cannot appear.

The seed is the region's pixel **medoid**, not its centroid: an L-shaped
room's centroid can fall outside the room.

## 3 · The fourteen fixtures

Each room is built in millimetres, so its answer is arithmetic. Alongside
each, the area the traced raster contour of the same room would have given:

```
                                            enclosed   contour   truth
BEDROOM WITH FURNITURE                        12.000     8.760   12.0
BATHROOM WITH BATHTUB / WC / BASIN             4.625     2.985    4.625
ROOM WITH DOOR OPENING                         7.500     7.170    7.5
ROOM WITH DOOR AND NO VALIDATED PORTAL        REFUSED    7.170    —
L-SHAPED ROOM                                 17.000    16.280   17.0
MIXED WALL THICKNESSES                        10.080     9.760   10.08
ROOM WITH WINDOW                              13.440    13.224   13.44
OPEN-PLAN LIVING / DINING                     44.840    41.480   44.84
SHAFT BESIDE BATHROOM                          0.810     0.630    0.81
PARTIAL / MISSING WALL                        REFUSED    8.620    —
STAIR NOSING INSIDE REGION                    11.200     9.688   11.2
CORNER FROM TWO FACES THAT REACH               7.200     7.200    7.2
CORNER, A FACE STOPS 50 mm SHORT              REFUSED    7.200    —
CORNER, ONLY ONE SIDE SUPPORTED               REFUSED    7.200    —
```

The contour is wrong on 9 of 14 by **11.5 m² in total** and **35% on the
bathroom** — which is why Round 2's contour-matching could never measure
one. The enclosure is exact on all ten that should close and refuses all
four that should refuse.

One expectation was mine and wrong: OPEN-PLAN was written as 45.0 and the
algorithm returned 44.84. The free-standing column is material standing in
the room, so a clear internal floor area **deducts** it — it came back as a
0.16 m² hole. The algorithm was right.

## 4 · Evidence tiers: orthogonality is not independence

Round 2 required two SOURCE_INDEPENDENCE classes for a VALIDATED portal,
which meant no doorway on a single architectural sheet could ever be
validated. That is not how a professional takeoff works.

Two axes now, recorded separately:

```
SOURCE INDEPENDENCE      SAME_PRIMITIVE / SAME_DRAWING /
                         SAME_DOCUMENT_SET / INDEPENDENT_SOURCE
EVIDENCE ORTHOGONALITY   DRAWN_GEOMETRY / DRAWN_SYMBOL /
                         PRINTED_ANNOTATION / DOCUMENT_STRUCTURE
```

A render relays the geometry it renders; a model relays what it read.
Neither adds a channel — so the Round 2 finding that *was* right survives: a
wall measured twice off one polyline is one observation wearing two hats. A
gap plus a swing arc is two things a draughtsman drew separately, which
could have disagreed.

Portal grades: DRAWING / DOCUMENT / SOURCE validated. **An ordinary doorway
with exact jamb geometry and orthogonal same-drawing support may carry a
production quantity** — no site visit. An opening wider than 2.6 m is held
for human QA, because at that width a wrong call moves square metres rather
than a jamb. Exact coordinates still come only from drawn geometry: the tier
decides whether the opening is *there*, never where it is.

## 5 · A bug that had made three mechanisms inert

`PortalPartitionBarrier` carries a `ring`. Three consumers asked for
`.polygon` through `getattr` and silently got `None`, so on the real
drawing:

- no opening jamb ever entered the boundary-candidate pool,
- no portal was ever reopened in the segmentation mask,
- every portal graded UNVALIDATED for "geometry not from source lines".

Each synthetic fixture supplied a `.polygon` attribute, so every test passed
while the real path did nothing. **Round 2's report claimed portals were
reopened on AR-00; they were not.** The geometry now lives on the object that
owns the ring, and `tests/test_barrier_polygon_contract.py` exercises the
real class so a fixture cannot diverge from it again.

With jambs actually present, AR-00 gains 38 jamb candidates and 19
DRAWING_VALIDATED portals.

## 6 · Three portal treatments, and the difference matters

Fixing the bug forced a question Round 2 never had to answer. Reopening
*every* portal merged rooms through their doorways and dropped topology
recall to 58.3%.

The distinction that resolves it: **carving a barrier out of the mask
deletes ink the drawing actually contains** — a door leaf, a threshold — on
the strength of a portal nobody validated. Declining to *add* an unsupported
barrier is not the same act. So:

```
supported portal      CLOSES the partition. That is what a barrier is for.
unsupported portal    LEFT ALONE. The render speaks; its ink is not deleted.
explicit reopen       available, and a caller must ask for it by name.
```

This restored recall to 75.0%, which is uncomfortable — the justification
must not be the number. It is not: deleting drawn evidence is a stronger act
than declining to add an inference, and that argument holds whichever way
the recall moves. All three treatments are asserted synthetically.

## 7 · AR-00, after the freeze

```
regions                        66
topology recall ALL            27 of 36   75.0%
topology recall IN_SCOPE       13 of 17   76.5%
split errors                    0
merge errors                    0
ROOM_CANDIDATE_PRECISION       27 of 27  100.0%
UNCLASSIFIED_REGION_COUNT      39 of 66   (cavities, outside areas, gaps)

enclosures attempted           66
ENCLOSURE_COMPLETE              8
ENCLOSURE_ESCAPED              58
complete measurement ALL        3 of 36    8.3%
complete measurement IN_SCOPE   2 of 17   11.8%
release eligible ALL/IN_SCOPE   0 of 36 / 0 of 17
```

**Three labelled spaces are completely measured from drawn geometry**, at
100% vector support, where Round 2 produced none:

```
BTH-02   4.623 m²   printed 2500 x 1850 = 4.625 m²
BTH-03   4.529 m²   printed 2450 x 1850 = 4.533 m²
MBTH-03  4.849 m²   printed 2850 x 1700 = 4.845 m²
```

Each agrees with the architect's printed dimensions to within **1–2 mm per
side**, compared after selection and never tuned to. That is the whole
measurement chain — frame, scale, face extraction, enclosure — confirmed by
a channel it does not control.

Release stays at zero, and correctly: part of each of those boundaries rests
on DIAGNOSTIC vector geometry rather than established material, so the
conservative rule refuses. Two enclosures reach 100% production-eligible
support, and both are small recesses holding no labelled space.

## 8 · Why 58 escaped

Every leak has one reason: `A_WHOLE_SIDE_HAS_NO_DRAWN_LINE` — 220 of them.
Not a tolerance, not a near miss, not a fixture: a whole side of the room
where the sheet carries no established face at that coordinate. That is the
same population Round 2 measured from the other direction (median 968 mm to
the nearest covering line), now stated as what a human would have to
confirm.

## 9 · The controls

```
BTH-01   found as its own region, enclosure ESCAPED
BED-01   found as its own region, enclosure ESCAPED
STR-01   not found: its centroid lands in no automatic region
```

None received benchmark geometry. The frozen BED-01 diagnostic result is
untouched — the freeze guard reports FROZEN_RESULT_HELD at 21.034 m².

## 10 · The decision

§20 requires BOTH:

```
A  synthetic fixtures prove detour rejection and refusal    YES  14/14, 4/4
B  materially more complete measured spaces, or a control   YES  0 -> 3
   recovered without raster-derived millimetres                  (no control)
```

**DECISION: FULL AUTOMATION CONTINUES — narrowly, and not alone.**

Three of thirty-six is a beachhead, not a solution. What changed is the
kind of failure: Round 2 could not measure a room *even where every wall was
drawn*, and now it can, exactly, with independent dimensional confirmation.
What has not changed is that most of this sheet does not carry a complete
set of drawn faces for most of its rooms, and no amount of inference will
conjure them.

So the honest product answer is both architectures at once, which is what
the enclosure's output is already shaped for: automatic topology, automatic
measurement where the drawing supports it, and **human confirmation of the
named unsupported side** where it does not — 220 specific leaks, each with
its axis, coordinate and extent, rather than an opaque failure.
