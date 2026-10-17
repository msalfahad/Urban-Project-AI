# Hybrid PDF topology

*Round 2. The deterministic-vector kill criterion fired, so the
architecture changed on purpose:*

```
RASTER / VISION          ->  SPACE TOPOLOGY HYPOTHESES
VECTOR / CAD-LIKE PDF    ->  PRECISE BOUNDARY SUPPORT + MEASUREMENT
AI / DOCUMENT            ->  SEMANTICS + DIMENSIONS + SYMBOLS
DETERMINISTIC CODE       ->  VALIDATION + SNAPPING + QUANTITIES + RELEASE
```

The round's one-line result: **the raster finds the rooms the vector path
could not, and the vector path still cannot close their boundaries.** That
is a real answer to the round's primary question, and it is not the answer
either "success" or "failure" alone would describe.

---

## 1 · What was kept

Every vector stage survives unchanged and changes role. Frame and scale,
source extraction, wall bands, wall polygons, the established/diagnostic
split, fragment recovery, portal evidence, the source-independence model,
geometry-vs-identity, measurement bases, run lineage, the release matrix,
frozen controls, quantity trace and the conservative refusals are now
**measurement and cross-check layers**. None of them is responsible for
discovering every room any more.

## 2 · Three objects, three questions

`engine/space_objects.py`. Separate TYPES, not three values of one status
field, so passing a region where a released space is required is a type
error rather than an optimistic read.

```
TOPOLOGY_REGION           is there one connected physical space here?
                          Area named APPROXIMATE. Carries NO released mm.
MEASURED_SPACE_CANDIDATE  can its boundary be measured from source
                          geometry, interval by interval?
RELEASED_PHYSICAL_SPACE   may a quantity be built on this polygon?
```

Each states what it is NOT, because every previous round's failures were a
status being read as the next one up. The three counts are reported side by
side and explicitly as **not one funnel of the same object**.

Boundary interval sources, in the production priority order:

```
VECTOR_WALL_FACE   VECTOR_OPENING_JAMB   VECTOR_EXTERNAL_BOUNDARY
RECOVERED_FRAGMENTED_VECTOR_GEOMETRY     <- production-eligible
DOCUMENT_SUPPORTED_DIMENSION   DIAGNOSTIC_VECTOR_GEOMETRY  <- diagnostic
RASTER_ONLY   UNRESOLVED                 <- never a measurement
```

`RASTER_ONLY` is absent from the production set by construction: a pixel may
localise a wall and may never measure one.

## 3 · The automatic topology

`engine/raster_topology.py`. Built from the drawing render and the
**established** wall solid only — no golden region, no human overlay, no
room list, no benchmark. Those may score it afterwards and may never build
it.

- Established wall material is rasterised into the barrier mask as **strong**
  evidence, and it separates rooms the porous vector solid merges.
- Diagnostic wall hypotheses are reported as **soft proposals** and are not
  in the mask: a hypothesis may not manufacture a room.
- Accepted portal openings are **reopened** in the mask. A doorway is how two
  rooms connect, and closing it would manufacture the separation this stage
  exists to detect.

Output: 63 regions with masks, centroids, adjacency, 209 candidate openings,
barrier provenance, a crude compactness confidence, and a hash of the whole
automatic result. Every quantity is named approximate; the record lists what
it may not supply (wall coordinate, thickness, opening width, released area
or perimeter).

The rasteriser needed two fixes worth recording. A per-pixel predicate over
each union component's bounding box cost **minutes** (the components are
comb-shaped and their boxes span the building); a per-row scanline that
replaced it was both slow — 97 s for one component — and **wrong**, at 68 108
pixels where 75 512 was correct. Wall geometry is rectilinear, so the parts
are now cut into rectangles by a sweep over their own x-coordinates: **4 ms,
and exact**.

## 4 · The boundary matcher

`engine/region_boundary.py` traces a region into an ORDERED rectilinear ring
— order is the structure, because corners come from consecutive runs
meeting. The axis is read in DRAWING space, not pixel space: this sheet's
frame is `SWAP_FLIP_Y`, so a run that is vertical in the image is horizontal
in the drawing.

A traced ring is a pixel staircase — one real room came out as 292 runs for
a 25 m perimeter — so it is simplified rectilinearly first (292 → 8), keeping
the **longer** neighbour's coordinate on each merge because the dominant
line is the one the draughtsman drew.

`engine/boundary_match.py` then searches LOCALLY for each run:

- same axis, inside a stated window, sharing enough extent to be the same
  wall;
- among those, **higher source authority wins even when a lower one is
  nearer**. Global-nearest is a failure this project already had: the nearest
  line to a room's north wall can be the south face of the wall above it.
- every interval records candidates seen, the one chosen, distance,
  orientation difference, shared extent, and every alternative with the
  reason it lost.

**Fixture detours.** Ink-based segmentation is what finds the rooms, and it
also treats a drawn bathtub or kitchen unit as a barrier, so a region's
outline detours into the room around every fitting. Such a detour is
collapsed onto the drawn line that already spans it — recognised
structurally: the runs on both sides sit on the same line AND that line is
drawn continuously across the detour. At a doorway the drawn face STOPS, so
the coverage test fails and the opening is never bridged. That is the same
discriminator fragment recovery uses.

The polygon is then built from the chosen objects, all or nothing. A run
with no match leaves the candidate PARTIAL and produces **no polygon**: one
completed with pixel coordinates would carry raster millimetres into a
measurement.

## 5 · Document understanding

AR-00 contains **zero PDF text objects**, no fonts, no images. Every label
and dimension is vector outlines.

`engine/glyph_text.py` finds text geometrically, using the drawing's own
measured pen convention: a glyph is a **small black filled path**
(`fill=(0,0,0)`), while dimension arrowheads are dark-red fills and walls
are zero-thickness strokes. That test took the candidate population from
7 168 marks to 1 328 and from 443 runs to **150**. Localising is
deterministic, free and offline; `raw_text` stays empty and the status reads
`LOCATED_NOT_READ`.

`engine/document_reader.py` transcribes each located crop through a vision
reader, cached on the crop's own bytes so a re-run costs nothing.
`tools/read_document_text.py` did the one paid pass: **144 calls, 90 printed
dimensions all parsed, 94 room labels in Arabic and English, 6 crops
correctly returning no text.**

The evidence roles were fixed before the extraction existed, and they hold:
a printed dimension is SIZE evidence and `require_use` raises if anybody
asks it for IDENTITY. A printed 3.50 matching a measured 3497 proves the
size is right and says nothing about which room it is — a bedroom and a
bathroom can both be 3.50 m wide. Every observation is `SAME_DRAWING`:
reading this sheet's own glyphs corroborates nothing about the building.

## 6 · Two scores, never one

```
§16  CAN IT FIND THE ROOM?
     region recall                     75.0%   (27 of 36, one-to-one)
     region precision                  42.9%   (36 of 63 hold no label)
     split errors                          0
     merge errors                          0
     spaces not found                      9
     deterministic vector, for scale   13.9%   (5 of 36)

§17  CAN IT MEASURE THE ROOM?
     regions with a measured candidate     27
     complete measured polygons             0
     boundary measured, mean            64.1%
     production-eligible, mean          47.6%
     unresolved, mean                   35.9%
```

Zero splits and zero merges is the striking half: where the raster finds a
room it finds it cleanly. Precision is low because 36 regions hold no
labelled space at all — wall cavities, fixture gaps, and areas outside the
building — which is a property of segmenting all ink, not an error about
any room.

Topology is scored only after the automatic hash is taken.

## 7 · Why no boundary closes

Of 362 unresolved runs, only **8 (6.4 m)** have no drawn line covering them
at any distance. The rest have a covering line, and the median distance to
it is **968 mm** — which is not a tolerance question: a line a metre away on
the same axis is a different wall. Widening the search window from 40 mm to
200 mm changes nothing.

So the blocker is named and it is not tolerance: the traced outline runs
where no wall face is drawn, because ink-based segmentation follows
fixtures, thresholds, stair nosings and hatch edges as readily as walls.
Collapsing fixture detours onto their own drawn line lifted the mean from
68.5% to 71.3% on the pre-barrier run; it does not reach closure.

## 8 · The printed dimensions agree to the millimetre

The strongest single result of the round, and it comes from an evidence
family the geometry does not control. Comparing each room's **clear extent
between opposite matched faces** against the dimensions printed on it:

```
AGREE        28        DISAGREE  0
AMBIGUOUS    16        NOT_PRESENT  1
material disagreements blocking release   0
```

Every agreement is within 2 mm and most within 1:

```
KIT-01   width   printed 6250   measured 6249.9   0.1 mm
BED-04   width   printed 6250   measured 6249.9   0.1 mm
BTH-01   width   printed 2500   measured 2500.5   0.5 mm
MAID-01  depth   printed 3850   measured 3849.4   0.6 mm
SRV-01   both    printed 1800   measured 1800.4   0.4 mm
MBTH-01  width   printed 1500   measured 1500.3   0.3 mm
```

Across 20 rooms the architect's printed dimensions and the engine's
face-to-face measurements agree to within a millimetre. That is independent
confirmation that where the matcher pairs a boundary, it pairs the right
line: the measurement chain is sound, and what fails is closing the whole
ring — not the millimetres.

The 16 AMBIGUOUS are honest: a room on a busy sheet has several dimension
strings of the right orientation near it, and where none agrees, which
string belongs to this extent is not established. The two values are
reported side by side and never averaged.

## 9 · The controls

```
BTH-01   found by raster topology, as its own region
BED-01   found, its own region, PARTIAL — a NEW record with a NEW hash
STR-01   not found: its centroid lands in no automatic region
```

`HYBRID_BED01_RESULT` is a separate record of a separate measurement by a
different path. The historical frozen result keeps its own hash and its
21.034 m², unmutated, and the freeze guard still asserts it on every run.
The hybrid result was chosen by the matcher's own priority order — **not** by
which answer came closest to the raster mask or to any reference.

## 10 · Two false signals of my own, found and killed

Both were mine, both would have been reported as findings about the
drawing, and both are now invariants (35).

- **137 "material disagreements"** between printed dimensions and vector
  measurements — then 30 after the first fix. Two compounding errors of
  mine: comparing each printed dimension against each matched boundary
  INTERVAL (a room's side is routinely drawn as three), and pairing each
  extent with a string of the WRONG orientation, which checked every
  room's width against its own depth. Corrected, the same data reads 28
  AGREE and 0 DISAGREE. A comparison that pairs the wrong things reports
  the drawing as broken.
- **47 of 63 regions classified CIRCULATION**, BED-01 among them, from
  adjacency count alone — because a bedroom beside a bathroom, a corridor
  and a dressing room connects three regions too. Adjacency is now recorded
  as evidence and decides no role.

## 11 · The gate

§24 asks for one of three, and the failure condition is specific.

```
A  a control recovered as a complete measured space        NO
B  materially more complete measured spaces than before    NO  (0 vs 0)
C  significantly better topology recall                    YES (75.0% vs 13.9%)

failure condition: many regions whose boundaries cannot be
matched to vector evidence locally                          NOT MET
                   (mean boundary measured 64.1%, not < 50%)
```

**Verdict: SUCCESS on condition C.** The architecture change did what it was
asked to do on the half it was aimed at — finding the spaces global vector
topology missed — while every released millimetre still comes from vector
geometry, and nothing releases.

What is explicitly NOT claimed: that the hybrid path can measure a room.
Zero complete polygons is zero, and release recall is still 0 of 36.
