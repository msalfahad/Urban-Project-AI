# Engineering invariants

Repository-level rules. They exist because each was learned by getting it
wrong more than once, in different modules, by the same reasoning.

---

## 1 · ORDER IS NEVER IDENTITY

> **Domain entities may never be joined by array position.**

Every cross-module join must use a stable id, an explicit key, or validated
geometry identity.

### Where this has already cost us

| module | what happened |
|---|---|
| `revision_entities` | a space matched by list position changes identity the moment a room is inserted |
| `connectivity` / `face_eligibility` | `cycle_capacity` sorts by cycle count, `components` sorts by length. Joining them on index scored **every component against another component's numbers** |

The second one was found only because a downstream result was absurd. There is
no reason to expect the next one to be so obliging.

### The rule in practice

```python
# NO — two lists, one index
for i, c in enumerate(components, 1):
    cycles = cycle_data[i]["independent_cycles"]

# YES — the entity carries its own value
for c in components:
    cycles = c.independent_cycles
```

Where two collections genuinely must be related, relate them by id:

```python
by_id = {c.component_id: c for c in cycles}
```

`tests/test_engineering_invariants.py` scans the engine for the shapes this
error takes.

---

## 2 · OBSERVATION → EVIDENCE → HYPOTHESIS → INDEPENDENT VALIDATION → PHYSICAL FACT

> **Do not promote a proxy into physical truth.**

Every stage must be nameable, and nothing may skip a stage. The proxies that
have tried to become facts in this project:

| proxy | was read as | actually |
|---|---|---|
| same raster region | "not a doorway" | the recovery signal |
| 60–120 mm separation | "not masonry" | evidence about thickness |
| same region both sides | "validated doorway" | topology evidence only |
| three correlated signals | three proofs | one construction seen three times |
| degree 4 | "a four-way crossing" | often an L corner |
| a 1.14 pt pen | "a wall" | style evidence, one family |
| **nearest parallel line** | **"the other face of this wall"** | **the mate is the one it runs ALONGSIDE** |
| a comment saying "the axes swap" | the transform | they swap **and flip** |

The last two are this round's. The pairing proxy cost every room on the sheet;
the frame proxy silently mirrored an entire round of geometry comparison.

### The rule in practice

- Two **independent evidence families** before anything is VALIDATED.
- Correlated observations of one construction are one observation.
- A single family is a hypothesis and is reported as such.
- `UNRESOLVED` is always an acceptable answer.

---

## 3 · MEASURE THE FRAME, DO NOT REASON ABOUT IT

A coordinate transform written as a code comment is an assumption with good
handwriting. `engine/frames.py` fits the candidate transforms against the
raster wall mask and reports the score:

```
SWAP+FLIPY   1.000        rot270   0.142
swap         0.135        rot90    0.069
```

A 1.000 against a 0.142 runner-up is a measurement. The previous inline comment
— *"on a 270-degree rotation the axes swap"* — was half right, and half right
in a transform means mirrored.

---

## 4 · NEVER INVENT THE MISSING HALF

If one wall face exists, do **not** mirror it by an assumed thickness. If a
room's boundary does not close, do **not** join its ends. If the raster says a
room is there, that says **where to look**, never **what to find**.

A printed dimension validates a candidate **after** generation. It is never an
input to the search.

---

## 5 · A LENGTH WITHOUT A BASIS IS NOT A LENGTH

A doorway is **four facts at once**:

| | BTH-05 |
|---|---|
| material present | **0 m** |
| opening | 1.054 m |
| space boundary | 1.054 m |
| host wall gross | 1.054 m |

Collapsing them into one number makes at least three trades wrong. The
previous round's *"material_length_mm is the only length a quantity engine may
read"* was one such collapse: 23010's own manual benchmark measures **gross**
perimeter and deducts openings later, so the door span belongs to the gross
line.

Every quantity engine declares which basis it consumes (`engine/lengths.py`),
and asking for an unestablished basis **raises** rather than returning zero —
an unestablished basis and a measured zero are different facts.

**Never compare unlike bases.** The 102.70 m site benchmark is a gross
perimeter; comparing it against a length that already removed doors compares
two different measurements that happen to share a unit.

---

## 6 · MATERIALS COME FROM APPROVED RECIPES, NEVER FROM AREA

Recorded now, implemented later:

```
VALIDATED QUANTITY
  → APPROVED CONSTRUCTION RECIPE
    → MATERIAL REQUIREMENT
      → PROCUREMENT ALLOWANCE
        → COST
```

Never: *AI infers materials directly from a drawing area.* The owner supplies
and approves construction recipes before they become active — block dimensions,
blocks per m², mortar, connector spacing, lintel logic, waste factor.

**CALCULATED QUANTITY and PROCUREMENT QUANTITY are always shown separately.**
A waste or safety allowance is its own approved field, never folded into a
measurement.

---

## 7 · BBOX IS NEVER PHYSICAL GEOMETRY

A bounding box **contains** a space. It is not the space.

| space | fills its own bounding box |
|---|---|
| STR-01 | **67.6 %** |
| OPEN-01 | 69.4 % |
| BED-04 | 71.2 % |
| BED-01 | 77.3 % |
| BTH-05 | 89.4 % |

STR-01's "2606 mm missing wall" was never a missing wall. STR-01 is L-shaped,
and the east edge of its box runs through open space the building never
enclosed. The engine measured a room against a rectangle it is not, then
reported the difference as a construction fact.

A bounding box may **index, localise and debug**. It may never produce a room
side, room perimeter, room closure, room area, or a missing-wall conclusion —
unless that space has been *independently proven rectangular*, which is a
separate fact with its own evidence (`engine/bbox.py`). A fill ratio is not a
proof: the missing few percent is exactly where a notch or a stub wall lives.

**And the raster outline is not the replacement.** WSH-01 proves a raster
region can carry the wrong physical identity. A raster outline localises a
search and compares against a result. It never constructs one:

```
WALL BANDS + SUPPORTED PORTALS + PLANAR TOPOLOGY  →  physical space polygon
```

---

## 8 · EXISTENCE AND GEOMETRY ARE TWO QUESTIONS

*"Is there a door here?"* and *"do we know where its jambs are?"* have
different answers and different evidence.

`SYMBOL + DOCUMENT` — the schedule says D-04 and a swing symbol is drawn — can
prove a door **exists** beyond argument while saying nothing about where it
falls on the wall line. A space-boundary edge is a piece of geometry, so
`PORTAL_GEOMETRY_STATUS` gates it, not `PORTAL_EXISTENCE_STATUS`. No family
without coordinates may fix a closure line.

Evidence is also **monotonic**: adding an observation may never lower a status.
Exact-match combination lookup broke this — a swing arc added to an approved
`GEOMETRY + SYMBOL` pair produced a three-family set that matched no row and
fell through to a lower cap. The answer is now the strongest approved
combination *contained in* the evidence.

---

## 9 · AN OPENING BELONGS TO A NAMED WALL, OR TO NO GROSS LINE

Before an opening may join `HOST_WALL_GROSS_LENGTH` it must say which wall it
is a hole in: `portal_id`, `host_wall_band_id`, both jambs, the width, the
closure line and its basis.

An opening floating between two unrelated walls closes a space perfectly well
and belongs to **no** wall's gross measurement — because there is no wall there
whose gross line it could be part of. Its host-wall length is
`NOT_ESTABLISHED`, which is not zero.

An invariant must also know **when it applies**. `HOST_WALL_GROSS =
MATERIAL_PRESENT + HOSTED OPENINGS` holds for simple hosted openings on
axis-aligned boundaries measured on one basis. It does not apply to open-plan
transitions, curved geometry, mixed closure bases, or non-hosted virtual
boundaries — and reporting `holds: True` for a room the rule never covered is
a vacuous pass presented as evidence of correctness.

---

## 10 · A STRUCTURED FIELD MAY NOT BECOME PROSE AS `None`

The workbook carried:

> "source-path fragmentation is NOT the cause — only **None** of **None**
> short marks share a path with a long run"

A missing value had been formatted straight into a sentence, and the sentence
still read as a confident measurement. The number was absent; the claim was
not.

A narrative clause is emitted only when every value it needs exists, and the
export **refuses** a workbook whose narrative columns contain `None`, `null`
or `NaN`. An absent value belongs in an empty cell.

---

## 11 · A CLOSED POLYGON IS NOT A ROOM

The regression: `WSH-01 → VALIDATED_PHYSICAL_FACE`, for a genuinely sound
1.981 m² cycle around the **hatched shaft beside the washroom**.

Nothing about the geometry was wrong. One field was answering two questions,
and they fail independently:

| | |
|---|---|
| `VECTOR_FACE_GEOMETRY_STATUS` | is this a valid closed face? |
| `PHYSICAL_SPACE_IDENTITY_STATUS` | is this face the room we named? |

`PHYSICAL_SPACE_GEOMETRY_ACCEPTED` requires **both** and is unreachable from
either alone. A shaft can have perfect geometry and a rejected identity; a
bedroom can have a supported identity and no sound polygon to attribute to it.

**One label inside one cycle is a candidate, never a validation.** A face
holding exactly one semantic label can still be a shaft, a closet, an adjacent
enclosure, a wrongly nested cycle, or the wrong side of a wall. And a *stated
contradiction* outranks any amount of supporting evidence — the support is
exactly what was mistaken.

---

## 12 · A SUM OF CYCLES IS NOT AN AREA

`bounded area = 1102.64 m²` added a 989 m² cycle to the cycles inside it. That
is not an arithmetic slip; it is a category error.

**Not every counterclockwise bounded walk is one occupiable room.** A cycle can
be the building envelope, a room, a shaft, a wall cavity, a sliver, or a
nesting artefact — told apart by CONTAINMENT and by what they hold, never by
size or orientation.

Only the ATOMIC set is additive, and only after it is checked for overlap and
for atoms nested inside atoms. `assert_additive` refuses any other total.

---

## 13 · A MEASUREMENT BASIS IS CONSTRUCTED, NOT CONVERTED

```
CLEAR ≈ CENTRELINE − PERIMETER × MEAN_HALF_THICKNESS
```

has no corner term, and inside and outside corners contribute with opposite
sign. On the L-shaped fixture it is out by exactly 0.04 m² — five outside
corners at +0.01 and one inside corner at −0.01. Mixed wall thicknesses break
it again: there is no single thickness to halve.

A clear-internal boundary is **walked** along the actual room-facing wall
faces, and its corners are the intersections of consecutive offset lines. The
room-facing face is chosen on evidence, never by being nearer; a single-face
band is `OWNERSHIP_AMBIGUOUS`. A portal closes on the **same basis as the walls
it joins**.

---

## 14 · A CONTROL CHOSEN AFTER SEEING THE ERROR IS NOT A CONTROL

The control set is defined by a rule in committed code, applied to the space
map alone, and the selector **raises** if it is handed an area, an error, a
face id or an IoU. A control that produced no geometry stays in the set as a
row saying so — dropping it would quietly turn the set back into "the ones
that worked".

---

## 15 · AN ID BELONGS TO ITS OWN NAMESPACE

Topology QA showed `component = FACE-0003`. A GRAPH component (`GC-`), a
PLANAR component (`PC-`) and a FACE (`FACE-` / `SF-`) are three different
objects; an id in the wrong column is a diagnostic quietly pointing at the
wrong thing. An empty graph component stays empty and says so rather than
falling back to whatever id is in reach.

And **do not generate an action item from a zero.** "Reduce the 0 unexplained
components and the 85 unresolved termini" asks for work that is already
finished, which makes a reader distrust the half that is real.

---

## 16 · TWO BOUNDED FACES CANNOT OVERLAP

A planar *graph* has cycles. A planar *embedding* has **faces**, and a face is
a connected component of ℝ² minus the embedded edges and vertices. Connected
components of any set are pairwise disjoint.

So when the engine reported two bounded faces sharing 32 m², that was not a
curiosity to be labelled `FACE_NESTING_ARTIFACT` — it was **proof the objects
were not faces**. It had been enumerating cycles of the abstract graph.

Six invariants are now asserted rather than hoped for: every half-edge in
exactly one walk, Euler, signed areas cancelling, no face overlap, no crossing
without a node, no ambiguous equal-angle rotation. All six failed on the real
drawing. The root causes were **46 nodes with an ill-defined rotation system**
(two outgoing half-edges at the same angle — what a portal closure laid on its
host wall's centreline produces at every jamb) and **40 crossings with no
vertex**.

**A label is not a diagnosis.** `FACE_NESTING_ARTIFACT` named the symptom and
hid the theorem.

---

## 17 · DO NOT OWN A COMPUTATIONAL GEOMETRY KERNEL

Noding, intersection, union, difference, polygonization, validity, containment,
overlap and IoU are library operations. GEOS has twenty years of work in
exactly the robustness problems that broke the custom walker: collinear
overlap, coincident edges, floating-point angular ordering, degenerate
intersections.

This project owns **construction meaning, source provenance, evidence,
measurement basis and release logic**. It does not own numerical geometry.

An earlier round correctly said *"do not tune the face walker."* The conclusion
should have been *"do not own a face walker."*

---

## 18 · A ROOM IS A HOLE IN THE WALL SOLID

```
each band  →  the polygon between its two DRAWN faces
all of them →  WALL_SOLID (robust union)
envelope − solid − portal barriers  →  FREE SPACE
connected components  →  space candidates
```

The boundary of each component lies **on the drawn wall faces by
construction**, so the result is already on the clear-internal basis. No
centreline offset, no room-facing-face determination, no corner correction, no
mean-thickness adjustment — **the corners are right because nothing computed
them**.

Components of one geometry are disjoint by construction, which is precisely the
property the planar path could not provide.

A doorway is still four facts. A `PORTAL_PARTITION_BARRIER` serves only the
fourth — it stops free space flowing through the door, it spans the host wall's
own thickness, and it is tagged `TOPOLOGY_ONLY_NOT_MATERIAL`. An open-plan
transition gets none: it is one physical space.

---

## 19 · SNAPPING IS NOT GAP-CLOSING, AND THE MAGNITUDE IS THE ARGUMENT

Two walls that genuinely touch arrived **0.003 mm** apart — three microns, on a
drawing whose pixel is 10.8 mm. Coordinates are snapped to a **0.05 mm** grid
before the union: 1/2000 of the thinnest wall, and it moved the total wall area
by three square centimetres.

That is noise removal. Anything that needs more is a **real separation** and is
reported as one; above 1.0 mm the union refuses to be asked.

---

## 20 · SEGMENTATION OUTPUT IS NOT VALIDATED STATE

Project 23010's 35 identity-validated and 33 topology-validated regions were
established by **human review and a golden overlay**. Quoting them as evidence
that automatic raster segmentation is accurate would credit the algorithm with
a person's work.

They are counted separately, and the automatic figure carries
`automatic_accuracy_established: False`. This matters most just before
generalisation: on an unseen project the human column starts empty.

---

## 21 · FIX THE EVIDENCE ROLE BEFORE BUILDING THE EXTRACTION

```
PRINTED DIMENSION       →  SIZE evidence
ROOM LABEL / SCHEDULE   →  IDENTITY evidence
DOOR / WINDOW SCHEDULE  →  OPENING evidence
```

A printed 3.50 matching a measured 3497 mm proves the **size** is right and
says nothing about which room it is — a bedroom and a bathroom can both be
3.50 m wide. Letting a dimension match lift a room's identity would be the
WSH-01 error in a new costume: geometry agreeing, name still wrong.

The roles are fixed in code before any extraction exists, because that is where
the temptation lies.

---

## 22 · AN INSTRUMENT MUST KNOW WHAT IT CANNOT SEE

A diagnostic that cannot fail looks exactly like one that is working.

The first space leak map classified **27 of 30** expected separations as
`NO_VECTOR_SEPARATOR` on a drawing whose walls are largely drawn. Three
separate defects produced that number, and none of them was visible from the
output:

1. **A metres-long frontier was probed at one point.** A 6.8 m frontier asked
   whether a wall bracketed its midpoint. Walls running along its other six
   metres were invisible. Coverage is now an interval union over the whole
   frontier, and the cause is read at the **aperture** — the stretch the
   accepted wall material leaves open — because that is where free space
   crossed.
2. **The frontier's axis was read in raster space.** AR-00's frame transform
   is `SWAP_FLIP_Y`, so every frontier was transposed and the engine searched
   for walls *along* the line the two spaces divide. The axis, the extent and
   the dividing line are now all measured after the transform.
3. **The dividing line was a tolerance around a biased point.** A raster
   region stops short of the wall face it abuts by an unknown amount, so a
   fixed ±300 mm around the touch band's centre missed bands 500–850 mm away.
   The window between two spaces is now **measured** from the gap between
   them, and a pair further apart than the drawing's thickest wall is not a
   candidate separation at all.

The deeper failure was structural, and no amount of tuning would have reached
it. **Raster region adjacency finds only where two rooms face each other**,
and free space also leaks *around* structure. It localised 8 open apertures
inside a component holding 22 labels — and 8 passages cannot join 22 rooms,
because a spanning tree needs 21. The instrument was provably incomplete and
its own output looked complete.

So the merged polygon is asked directly. Eroding it and watching which labels
fall apart finds every passage by construction, and the radius at which a
pair separates **measures** the passage. Two things are then kept apart that
are easy to conflate:

- **Where it was cut**, proven by removing the channel and checking the two
  sides actually fall into different components;
- **How far it extends**, which only exists while the rooms either side are
  wider than the erosion. Beyond that the removed material is one connected
  sheet, and reading the drawing over it would return every band on the sheet
  and look like a confident answer. That case is **refused**, keeping the
  measured width and dropping the classification.

A `partition_complete` check states, for every component, how many passages
its label count requires and how many were reported. On AR-00 it still reads
`complete: false` for the 22-label component. That is the point: the map says
so itself.

What the corrected instrument found was not what the broken one claimed. The
largest single cause is **five hairline junction gaps of 50–300 mm** where
accepted wall bands run along the whole passage and free space crossed
anyway. Nothing is missing from the drawing there. Two wall polygons fail to
meet, and no better reading of the source will ever close it.

**A passage width measures the channel's narrow dimension.** A doorway is a
channel as deep as the wall is thick and as long as the door is wide, and the
erosion closes the depth first. A 200 mm passage is a wall's thickness, not a
200 mm door.

---

## 23 · A TOLERANCE NOBODY MEASURED CANNOT BE WRONG

The wall solid snapped vertices onto a 0.05 mm grid, justified as "one
two-thousandth of the thinnest wall". That is a ratio to a wall, not a
measurement of the coordinates being snapped, so it could be neither
confirmed nor refuted — and the next sheet is produced by different software
with different precision.

So it is measured (`engine/snap_tolerance.py`). Vertices that ought to be one
node are separated either by representation noise or by a real gap between
two walls that do not meet, and a decade histogram of near-coincidence
distances shows whether those two populations separate. On AR-00's 972
wall-polygon vertices, 235 pairs from different rings lie within a
millimetre:

```
<=1e-09 : 56      exactly coincident nodes
<=1e-03 :  6
<=0.01  : 173     representation noise, largest 0.0087 mm
<=0.1   :  0   ┐
<=1     :  0   ┘  EMPTY — nothing anybody drew comes this close
```

Two empty decades separate the noise from anything drawn. The measured
recommendation is **0.01 mm**; the 0.05 mm in use is 5× larger, still an
order of magnitude below the empty band, and is now reported as
`SAFE_AND_WITHIN_AN_ORDER_OF_THE_MEASUREMENT` rather than asserted.

Three rules survive any measurement:

- a recommendation may **never** exceed `MAX_DEFENSIBLE_SNAP_MM` (1.0 mm);
- a drawing whose near-coincidences run continuously to the ceiling gets
  **no** recommendation — `NOISE_AND_GAPS_NOT_SEPARABLE`, snap nothing and
  report the gaps;
- the result is recorded **per run** and must not be promoted to a project
  or engine default.

This immediately settled a question the leak map raised. The five hairline
junction gaps are 50, 50, 100, 150 and 300 mm — **5,000 to 30,000 times** the
grid. They are not numerical artefacts and will not yield to a larger
tolerance. Raising the grid to reach them would close every genuine 50 mm gap
too, which is how a wall appears between two rooms that were drawn open.

---

## 24 · FOUR QUESTIONS, FOUR STATUSES

The workbook reported geometry from two paths at once. The planar graph
face path and the free-space path both produced areas for the same rooms,
both plausible, with nothing saying which one a quantity would be measured
from. That is **mixed authority**, and it is worse than either path being
wrong, because a reader cannot tell that anything is undecided.

The free-space path is the **geometry authority**, stated once in
`engine/qa_workbook.GEOMETRY_AUTHORITY` and quoted on every sheet that
carries geometry. The graph path is a `DIAGNOSTIC` whose six invariants are
falsified on this drawing, and it may not release geometry. A **Free Space
QA** sheet carries the authority's own rows, and it sits *before* Topology QA
so a reader meets the authority first.

The same conflation had reached the status line. `FINAL_BOQ_STATUS` was
blocked, among other things, because *"the wall graph does not pass its E31A
gates, so room polygons cannot be reconstructed"* — a condition nothing
downstream depends on any more, standing in for the condition that actually
matters. So there are now four:

| Status | Question | AR-00 |
|---|---|---|
| `GEOMETRY_MECHANISM_PROVEN` | Does the **method** work? | **PASS** |
| `PROJECT_SPACE_RECALL` | How many of **this floor's** rooms came out as their own polygon? | **PARTIAL** |
| `TAKEOFF_COVERAGE_STATUS` | How much has been validated so far? | `VALIDATED_PARTIAL` |
| `FINAL_BOQ_STATUS` | May a bill of quantities be produced? | `BLOCKED` |

The first two are the pair that matters, and the confusion runs one way: a
round that proves the method reads as a round that measured the building. It
did not. `PASS` is earned by the free-space invariants holding and controls
being frozen and accepted *before* any reference was opened — it says the
mechanism works and **says nothing about how much of this floor it
resolved**. `PARTIAL` says nine of seventeen in-scope spaces came out as
their own polygon; the rest sit inside components holding several merged
rooms, and a merged component's area is not a room's area.

A mechanism that is proven and unproven are not the only two states. Where
the invariants were never run, the status reads `FAIL` with the reason
*"unproven — not failed, unproven"*, because a check nobody ran is not a
check that passed.

---

## 25 · PRODUCTION GEOMETRY MAY NOT REST ON A HYPOTHESIS

There were two wall solids' worth of material in one object. 446 m where
both faces were drawn, and 55.9 m the band engine itself records as
`UNRESOLVED_EXTENSION` — *"NOT established material"* — and every quantity
was measured against the union.

Now there are two, and admission is **per interval**, not per polygon,
because a band is usually part established and part not:

```
ESTABLISHED_WALL_SOLID            558.3 m   104.43 m2   432 intervals
DIAGNOSTIC_AUGMENTED_WALL_SOLID   614.2 m   116.63 m2   453 intervals
   the hypothesis adds                      12.20 m2   10.5%
```

Then the same free-space path ran on both, and the result is the reason this
invariant exists:

| | ESTABLISHED | DIAGNOSTIC_AUGMENTED |
|---|---|---|
| single-room candidates | 4 | 8 |
| largest merged component | **32 labels** | 23 labels |
| BED-01 | inside the 32-label blob | **its own 21.034 m² polygon** |

**BED-01 has a polygon of its own only because unestablished wall material
was treated as masonry.** Its boundary runs along 5.104 m of
`UNRESOLVED_SINGLE_FACE_EXTENSION` across three intervals (WB-00160,
WB-00030 ×2). The polygon is geometrically perfect and it is not a measured
room.

So `DIAGNOSTIC_GEOMETRY_ACCEPTED` and `PRODUCTION_GEOMETRY_RELEASED` are
separate verdicts, and a valid polygon earns only the first. On AR-00:

```
DIAGNOSTIC_SPACE_GEOMETRY_RECALL          9 / 17
RELEASE_ELIGIBLE_SPACE_GEOMETRY_RECALL    0 / 17
```

Nine rooms have a plausible polygon. **None** has one every boundary
contributor of which satisfies production-level evidence. The gap between
those two numbers is the size of the hypothesis, and reporting only the
first would let a guess count as a measured room.

---

## 26 · A LOCALISER POINTING AT SOMETHING IS NOT EVIDENCE IT MATTERS

Last round found five hairline gaps of 50–300 mm where accepted wall bands
run along the whole passage, and reported them as the dominant cause of the
merged components. That was asserted from the localiser's output. It is
wrong, and two instruments built this round say so.

**Junction patches, on evidence.** A gap is closed only by an explicit
`JUNCTION_PATCH` where local vector geometry proves a physical junction —
never by a larger snap, a buffer, morphological closing or generic gap
filling, each of which closes every gap of that size in the drawing and
leaves no record of where or why. Of the five:

| gap | width | verdict | the repair it actually needs |
|---|---|---|---|
| BTH-03/BED-02 | 50 mm | REFUSED | `REPAIR_IS_IN_WALL_FACE_PAIRING` |
| BTH-01/BED-NW | 50 mm | REFUSED | `REPAIR_IS_IN_WALL_FACE_PAIRING` |
| MBTH-02/BED-02 | 100 mm | **VALIDATED** | `REPAIR_IS_JUNCTION_ASSEMBLY` |
| BTH-04/BED-02 | 150 mm | REFUSED | `NOT_ONE_WALL_TWO_DIFFERENT_WALLS_MEET_HERE` |
| BED-04/BED-02 | 300 mm | REFUSED | `NOTHING_IS_DRAWN_HERE_THE_OPENING_IS_REAL` |

At two of them only ONE accepted band is anywhere within 800 mm, while the
raster shows solid (0.43, 0.50) and wall-like unpaired strokes lie right at
the gap. A wall **is** drawn there and never became a band: that is a
**pairing** failure, and a patch would have papered over an extraction bug.
At one, raster support across the gap is **0.00** — nothing is drawn, the
opening is real, and closing it would have invented a wall.

**The counterfactual.** The one validated patch was applied to the
established solid with nothing else changed:

```
single-room candidates   4 -> 4     (+0)
largest component       32 -> 32    (+0 labels)
verdict: REPAIRS_CHANGED_NOTHING_IN_THE_PARTITION
```

So the five gaps are not the dominant cause. They were never shown to be —
they were pointed at, and pointing is not proof. Every row of the merged
component work list now carries `NOT_MEASURED` until a counterfactual has
actually been run for it.

---

## 27 · A COVERAGE FIGURE MUST DIVIDE LIKE BY LIKE

`DRAWING_WALL_REPRESENTATION_COVERAGE = 45.9%` divided a **wall-band**
length by a **source-stroke** length. A two-face wall contributes about two
source-face lengths and one band length, so the numerator was deduplicated
and the denominator was not: the figure understated capture by roughly a
factor of two on exactly the population it claimed to measure, and it looked
like a careful number.

Every term is now source-stroke length, the parts must add to the total, and
the residual is reported rather than absorbed:

```
SOURCE_WALL_STYLE_STROKE_LENGTH_TOTAL        1912.5 m
  USED_IN_ACCEPTED_BANDS                     1061.5 m   55.5%
  FRAGMENTED_MATE                             289.0 m   15.1%
  NON_WALL                                    266.7 m   14.0%
  UNRESOLVED                                  214.5 m   11.2%
  CLASSIFIED_SINGLE_LINE                       58.1 m    3.0%
  DUPLICATE                                    22.6 m    1.2%
  UNACCOUNTED                                   0.0 m    0.0%
```

A deduplicated PHYSICAL length is reported separately (615.1 m from 243
accepted bands) and the two may never be divided into one another. No
physical length is derived for the unpaired population at all: a single
stroke establishes no thickness and no face positions, and **NEVER INVENT
THE MISSING HALF** applies to length as much as to thickness.

**Unknown stays unknown.** An earlier report added non-wall, duplicate and
unresolved together and called the sum "never a wall", which silently turned
214.5 m of UNRESOLVED from unknown into false. The three are reported apart,
and UNRESOLVED sits in neither the wall-like nor the non-wall figure on
purpose.

---

## 28 · "CONFIRMED" MUST NAME WHAT IT CONFIRMED

434.8 m carried the label `CONFIRMED_SINGLE_LINE_WALL`. A deterministic
blind sample — the manual expected-wall list not consulted — showed the
classifier had overreached by about **7.5×**.

The evidence rule had two holes. It never checked the **pen**: of 434.8 m,
only 155.6 m was drawn with this drawing's measured 1.14 pt wall pen, the
rest at 0.12–0.72 pt. And it never looked for a **parallel face** — the one
thing a single-line wall is defined by not having — because its "no mate"
test asked only for collinear neighbours on the *same* line. Sample members
had parallel faces 40–250 mm away. The longest "single-line wall" on the
sheet was a **50 m** stroke at 0.72 pt.

With pen, parallel-face, over-length and wall-network tests added,
`SINGLE_LINE_WALL_EXISTENCE_SUPPORTED` falls to **58.1 m in 2 strokes** —
and those two are 29 m runs at y = 2452 and y = 51200, outside the
building's own extent, almost certainly the sheet frame. The defensible
reading is that this drawing has **no established single-line wall
convention at all**. They are reported with that caveat rather than removed
by another rule chosen to remove them.

The claim is also split, because one stroke cannot support both halves:

```
SINGLE_LINE_WALL_EXISTENCE_SUPPORTED   a separator is probably there.
                                       May become a
                                       TOPOLOGY_SEPARATOR_HYPOTHESIS.
SINGLE_LINE_WALL_GEOMETRY_COMPLETE     thickness and both face positions
                                       independently established. Only
                                       this may create material geometry,
                                       and nothing produces it yet.
```

---

## 29 · SAFETY IS TOPOLOGICAL, NOT AREAL

The 0.05 mm snap grid was called safe because it changed the wall solid's
area by 0.0003 m². That is the wrong test. Snapping merges two vertices onto
one grid node, which **connects** two pieces of geometry — a topological
event with no area cost at all, so an area argument cannot see it. A
connection created by rounding is a wall the drawing does not have, and it
closes a space the drawing leaves open.

So both grids are run and every connection present at the coarser grid and
absent at the finer one is found and classified. On AR-00: 49 components at
0.01 mm, 46 at 0.05 mm, **2 joins**, both `NUMERICAL_NOISE_JOIN` within the
measured noise floor. The coarser grid is defensible here — but now it is
*proven* rather than inferred from an area that barely moved.

Production still builds the established solid on the **measured** tolerance,
and physical junctions are repaired by an explicit `JUNCTION_PATCH` that can
be listed, reviewed and removed. A tolerance cannot be.

---

## 30 · A DRAWN FRAGMENT IS MATERIAL; A MISSING FRAGMENT IS NOT

A draughtsman routinely draws one continuous wall face opposite several
collinear fragments — the mate is cut by a crossing wall, a door jamb, a
junction. The pairing engine assumed one face meets one face, so 289.0 m of
AR-00's wall-pen strokes were classified `FRAGMENTED_MATE` and dropped.

Recovering them is legitimate and bounded. **The material occupies the
intervals where both faces are actually drawn, and nowhere else.** Where one
face is drawn and the other is not, nothing is recovered: the gap is
reported, classified by what the drawing says accounts for it, and left
open.

```
PAIRED interval      both faces drawn      -> material, admissible
GAP, explained       a portal, a crossing wall, an end cap
                     accounts for the break in the face
                     -> still no material there, and the
                        GROUP may be VALIDATED
GAP, unexplained     nothing in the drawing accounts for it
                     -> the group is DIAGNOSTIC ONLY
```

Four refusals are absolute, and the self-test asserts each on a known
answer before the resolver is allowed near the real sheet: it may not
**bridge an opening**, **invent the missing half**, **change the wall
thickness**, or **move a wall face**. A fragmented-mate resolver that closes
doors is worse than no resolver, so a group whose paired material would
cover a supported opening is refused **outright, not trimmed to fit**.

Collinearity is decided by **proximity, not by a bucket**. `round(fixed /
tolerance)` splits two fragments 0.6 mm apart when they straddle a bucket
edge and keeps two 0.9 mm apart inside one, which makes the drawing's
geometry depend on where an arbitrary boundary fell. Single linkage asks the
only question the drawing can answer — is this fragment within tolerance of
the last one on this line — and because linkage can chain, separation
stability is still measured across the whole run: a chain of drifting
fragments is not one wall.

Room topology is **downstream evidence only**. Nothing in the resolver can
see a room, an area, a label or a benchmark, and no group is accepted
because it would close one.

---

## 31 · LENGTH IS NOT IMPORTANCE

214.5 m of AR-00's wall-pen strokes remain `UNRESOLVED`. Ranking them by
length and working down the list would spend a round on site hatching: a
long stroke outside the building is worth nothing, and a 300 mm stroke in
the aperture between two bedrooms is worth a room.

So the unresolved population is ranked by **where it sits relative to
measured separation failures** — an aperture that merges a frozen control,
then any aperture between two labelled spaces, then a frozen control's
frontier, then any frontier — and the tiers that have no members are
**declared**, not quietly omitted. On AR-00 both aperture tiers are empty
and only **7.08 m of the 214.5 m** lies at any measured separation failure
at all. Where the partition is open, nothing is drawn there to recover.

A place on that work list is **not evidence that the stroke is a wall**. It
carries no thickness, no finish-face position, and no admission to any wall
solid.

---

## 32 · A FREEZE THAT NOTHING CHECKS IS A HOPE

BED-01's diagnostic result is frozen at 21.034 m². A freeze recorded only
in a directive and a docs table is not enforced by anything, so the pin
lives in code and is asserted on **every run**.

The pin keeps two hashes, because the geometry hash changed once — at the
Round 1.5 geometry-authority unification, when the clear-internal polygon
was re-derived through one authority instead of two paths. **The area did
not move.** That distinction is the whole point:

```
area unchanged, known hash      FROZEN_RESULT_HELD
area unchanged, unknown hash    HELD_UNDER_A_RE_EXPRESSED_GEOMETRY
                                — needs a stated reason before the
                                  new hash joins the pin
area changed                    FROZEN_RESULT_MOVED — refused
control absent from the run     NOT a pass: a failure to check
```

The **area** is the invariant, because the area is the measurement. And if
independently supported recovery ever produces a different BED-01 polygon,
it becomes a **new geometry record with a new hash** — the frozen one is not
mutated, and the check is not widened to accept it.

---

## 33 · RASTER FINDS THE ROOM; VECTOR MEASURES IT

Global vector topology could not discover this floor: 32 of 36 labelled
rooms sat in one merged blob, because a wall solid built from drawn faces is
porous at every hairline gap and unestablished extension. A rendered image
does not care about a 0.3 mm gap in a polyline — ink is ink — so
segmentation separates rooms the solid merges. On AR-00 it finds **27 of 36
spaces as exactly one region each, with zero splits and zero merges**.

That does not make pixels a measuring instrument. The two roles are split
and the split is enforced by types, not by convention:

```
TOPOLOGY_REGION           where a connected space is.
                          Its area is named APPROXIMATE. No released mm.
MEASURED_SPACE_CANDIDATE  what its boundary measures, interval by
                          interval, each naming its source.
RELEASED_PHYSICAL_SPACE   whether a quantity may be built on it.
```

A pixel coordinate may become a drawing coordinate only as a **search
window**. The final polygon is built from the chosen vector faces, jambs and
end caps — the raster outline is never scaled, warped, offset or smoothed
into place, and a run with no match stays UNRESOLVED rather than taking its
coordinate from the pixels. A polygon that mixed the two would look
complete and measure the wrong building.

Selection is **local and priority-led, never global-nearest**. The nearest
line to a room's north wall can be the south face of the wall above it; an
established face beats a nearer diagnostic one. Every interval records the
candidates it saw, the one it chose, the distance, the shared extent and
every alternative with the reason it lost, because a QS quantity must be
traceable to the exact drawn geometry.

---

## 34 · FINDING A ROOM AND MEASURING IT ARE TWO SCORES

Mixing them is how a system reports "78% accurate" while unable to produce a
single releasable polygon. So there are two metric families that share no
term:

```
§16  CAN IT FIND THE ROOM?     region recall and precision, splits,
                               merges, adjacency accuracy
§17  CAN IT MEASURE THE ROOM?  boundary-source coverage, complete /
                               diagnostic / release-eligible counts,
                               area agreement
```

On AR-00 the honest pair is **75.0% topology recall and 0 complete measured
polygons** — a real advance on finding rooms and no advance at all on
measuring them. One number would have hidden whichever half the reader
cared about.

Topology is scored only **after the automatic output is hashed**. The human
overlay and golden regions may score the result; they may never build it, or
the metric measures itself.

---

## 35 · A COMPARISON MUST PAIR LIKE WITH LIKE

The printed-dimension cross-check first reported **137 material
disagreements** on AR-00. Every one was an artefact: it compared each
printed dimension against each matched boundary INTERVAL, and a room's side
is routinely drawn as three separate intervals, so a printed 3850 was
checked against three ~1283 mm pieces.

What a dimension on a plan dimensions is the **clear extent between two
opposite finish faces**. Comparing that instead, and treating a string more
than half the extent away as dimensioning something else, leaves a real
check: AGREE / DISAGREE / AMBIGUOUS / NOT_PRESENT, never an average, and a
material disagreement BLOCKS release rather than being split down the
middle.

The same discipline killed a second false signal: inferring CIRCULATION from
adjacency count put **47 of 63 regions** — BED-01 among them — into
circulation, because a bedroom beside a bathroom, a corridor and a dressing
room connects three regions too. Adjacency is recorded as evidence and
decides no role; whether a space functions as circulation is a functional
zone question, not a physical property.

---

## 36 · A DRAWING WITH NO TEXT OBJECTS IS NOT A DRAWING WITH NO TEXT

AR-00 contains **zero** PDF text objects, no fonts and no images. Every room
name, printed dimension and door tag on it is a cluster of vector outlines,
and a naive extractor reports an empty sheet.

The text is therefore found geometrically, and the discriminator is the
drawing's own pen convention, measured rather than assumed: **a glyph is a
small BLACK FILLED path**. Letters come back as `fill=(0,0,0)`, dimension
arrowheads as `fill=(0.54,0,0)`, and walls and dimension lines as
zero-thickness strokes. Without the colour and thickness tests, a cluster of
red arrowheads scored as a room label — and the reader was paid to answer
"no text".

Two mechanics that cost real debugging time, recorded so they are not
rediscovered:

- `get_drawings()` returns **unrotated mediabox** coordinates while
  `get_pixmap(clip=…)` expects the page's **rotated** coordinates. On this
  270° sheet the two differ, and clipping with the raw rect renders blank
  paper. The page's own rotation matrix is the conversion.
- Localising and reading are separate stages. The localiser is
  deterministic, free and offline; only transcription needs a model. So
  "no text found" and "nobody looked" are different statuses, and a run
  reads `LOCATED_NOT_READ` until something reads it.

What the reader may do is transcribe characters. It is never asked how big
anything is, where a wall runs, or which room it is looking at.

---

## 37 · THE RASTER SAYS WHICH SPACE; THE VECTOR SAYS WHERE ITS BOUNDARY IS

Round 2 matched every run of a region's raster contour to a vector object
and closed not one room. The diagnosis was not tolerance — the median
distance from an unmatched run to the nearest covering line was 968 mm —
it was that **a contour run over a bathtub has no wall to match.** The
region's outline follows baths, wardrobes, thresholds, stair nosings and
door leaves, and demanding a wall for each of them made every bathroom
unmeasurable.

So the region stops being a path:

```
THE RASTER ANSWERS    which space are we measuring?
THE VECTOR ANSWERS    where is every millimetre of its boundary?
```

The mechanism is a flood fill through an **arrangement of supported lines**.
Take the drawn faces, caps and jambs near the region; cut the neighbourhood
into cells on their coordinates; block a cell edge only where a line is
actually DRAWN across it; flood from a point inside. What the flood cannot
escape is the enclosure.

Three properties then hold **by construction, not by a test**:

- **A fixture is invisible.** A bathtub is not a boundary candidate, so it
  cannot block a cell edge and cannot indent a result. There is no
  detour-rejection rule because a detour cannot arise.
- **A wall that stops short does not close.** A line blocks only over its
  drawn extent, so the flood escapes through the gap. Nothing is ever
  extended until it hits something.
- **A corner is an intersection, not an invention.** Vertices are where two
  blocked edges meet — two independently drawn lines crossing. A corner
  with only one side supported cannot appear, because the other side never
  blocked anything.

Measured on fourteen fixtures built to have known answers: the enclosure
returns the arithmetic area every time, while the traced contour of the
same rooms is wrong by **11.5 m² in total** and **35% short on the
bathroom**. Material standing inside a room — a free-standing column — is
deducted as a hole rather than treated as a boundary or ignored.

---

## 38 · ORTHOGONALITY IS NOT INDEPENDENCE

Requiring two different SOURCE_INDEPENDENCE classes before a portal could
be validated was half right and wrong in its conclusion.

Right: a raster render of a PDF is the same drawing observed twice, and
counting it as two families is how a wall came to be confirmed by itself.

Wrong: that nothing on one drawing can validate anything. A professional
takeoff reads openings off a plan every day, and what makes that sound is
that the plan says the same thing in **differently authored ways** — a gap
in a wall, a swing arc, a leaf symbol, a printed width. Those are separate
draughting acts that *could have disagreed*, which is what makes their
agreement informative.

Two axes, recorded separately and never conflated:

```
SOURCE INDEPENDENCE      how far from this document did it come?
                         SAME_PRIMITIVE / SAME_DRAWING /
                         SAME_DOCUMENT_SET / INDEPENDENT_SOURCE
EVIDENCE ORTHOGONALITY   how differently was it authored?
                         DRAWN_GEOMETRY / DRAWN_SYMBOL /
                         PRINTED_ANNOTATION / DOCUMENT_STRUCTURE
```

A render relays the geometry it renders and a model relays what it read:
neither adds a channel. So a wall measured twice off one polyline is one
observation wearing two hats, while a gap plus a swing arc is two.

Portals are graded, not gated: DRAWING / DOCUMENT / SOURCE validated. **An
ordinary doorway with exact jamb geometry and orthogonal same-drawing
support may carry a production quantity** — no site visit. An opening wider
than an ordinary door is held for human QA, because at that width a wrong
call moves square metres rather than a jamb. What no tier changes: exact
coordinates come from drawn geometry, and the tier decides only whether the
opening is *there*.

---

## 39 · A RECALL WITHOUT ITS DENOMINATOR IS A SLOGAN

Round 2's report set "27 of 36 topology recall" beside "0 of 17 release
recall". 36 is every labelled space; 17 is the in-scope subset. A reader
comparing 75% with 0% was comparing two populations, and nothing on the
page said so.

Every recall is now reported twice, from one row set, with the denominator
printed beside the number: TOPOLOGY, COMPLETE_MEASUREMENT and
RELEASE_ELIGIBLE, each ALL and IN_SCOPE.

The same discipline applies to precision. Calling 42.9% "topology
precision" implied that 36 regions were false-positive rooms; they are wall
cavities, outside areas and fixture gaps, never claimed to be rooms.
**Classification comes after segmentation**, so ROOM_CANDIDATE_PRECISION is
measured among the regions that hold a label, and UNCLASSIFIED_REGION_COUNT
is reported as a count — not as a penalty.

---

## 40 · A DOORWAY MEANS THREE DIFFERENT THINGS

"Reopening every portal dropped topology recall from 75% to 58.3%" was not
a tuning problem. It was the symptom of one binary portal operation being
asked to serve three questions that have different answers:

```
MATERIAL_GEOMETRY        is there wall material across the opening?
                         NO. Zero. Blockwork, plaster, deductions.
ROOM_PARTITION_TOPOLOGY  are these two distinct physical spaces?
                         YES. The doorway closes the ROOM boundary
                         VIRTUALLY, still with zero material.
NAVIGABLE_FREE_SPACE     can a person walk through?
                         YES. Open. Circulation only.
```

A bedroom and its ensuite are **one opening, two rooms and one navigable
connection simultaneously**, and a system that holds only one of those keeps
trading it for another. Navigability may never define QS room identity:
treating an unproven doorway as navigable and calling the result one space
is what merged a bedroom with a bathroom.

`PORTAL_PARTITION_BOUNDARY` carries the room boundary across the opening
with `MATERIAL_PRESENT_LENGTH = 0` — not unknown, not small. It participates
in the room partition and may never enter a wall solid or a material
quantity.

**Uncertainty makes the partition diagnostic; it never merges the rooms.** A
gap with a portal nobody validated still separates two rooms — as
`ROOM_PARTITION_DIAGNOSTIC`. Only a gap with no portal evidence at all is
`ROOM_PARTITION_UNRESOLVED`, releasable as neither one space nor two.

---

## 41 · DRAWN DOOR INK IS EVIDENCE, NEVER A BOUNDARY

A leaf, a swing arc, a threshold or a jamb symbol may support the claim that
a portal exists. None of them may become the room's boundary because
rasterising the sheet turned its ink into a barrier.

This is the generalisation rule. One architect hatches thresholds and draws
leaves across both jambs; another leaves the leaf floating clear. A room
topology that depends on which is a room topology that does not travel
between offices — and the synthetic pair
`DOOR_LEAF_INK_THAT_TOUCHES_BOTH_JAMBS` and
`DOOR_GRAPHICS_THAT_DO_NOT_TOUCH` assert that both produce the identical
partition.

So the render's ink may LOCATE a frontier and decides nothing about it. The
room partition is built from wall material plus explicit graded portal
boundaries, and `answer_pair` has nowhere for a pixel to enter: its whole
signature is `(space_a, space_b, portal, material_between)`.

Measured on AR-00 under this rule: the localiser still finds 27 of 36 spaces,
and only **1** of them has a partition resting entirely on material or
validated portals. That is a reduction in what may be claimed, and it is the
honest number.

---

## 42 · UNRESOLVED IS NOT A WEAK VERSION OF EITHER ANSWER

The room partition returned `connected = True` for a gap with no evidence
at all, and anything reading that boolean saw **ONE SPACE**. That asserted a
physical-space relationship on no evidence — the same failure as calling a
shaft a washroom, in a different costume.

A boolean cannot express this, because a boolean has only two values and
the commonest honest answer on a real drawing is neither:

```
ONE_PHYSICAL_SPACE            needs explicit open-plan evidence:
                              a schedule row, a note, a single label
                              spanning the extent
TWO_DISTINCT_PHYSICAL_SPACES  needs supported separator evidence:
                              continuous material, or a graded
                              PORTAL_PARTITION_BOUNDARY
ROOM_PARTITION_UNRESOLVED     neither is established
```

`UNRESOLVED` covers three different situations and is not a lean towards
any of them: one open physical space, two rooms through a portal nobody has
resolved, or two spaces whose separator was never recovered from the
drawing.

So `PartitionAnswer` carries **no `connected` field at all**. A caller asks
`is_one_space` or `is_two_spaces`, and for UNRESOLVED **both are False** —
which means `not is_two_spaces` cannot silently become "one space".
`require_resolved()` raises rather than guessing.

**The absence of a separator is not evidence of open plan.** The same two
regions, with and without a schedule row declaring them one space, are
UNRESOLVED and ONE_PHYSICAL_SPACE respectively — the geometry is identical
and only the declaration differs.

On AR-00 under this rule: of 135 region adjacencies, 27 are established as
two distinct spaces and **108 have an unresolved relation**; of the 27
labelled spaces found, **1** rests on an established partition. Those 108
are overwhelmingly thin places in the render, not 108 doorways — which is
exactly why none of them may assert a room relationship.

## 43 · A SOURCE THE READER CANNOT SEE IS NOT A DRAWING WITH NO WALLS

Project 2 arrived as a **400 dpi scan of a stamped municipality
submission**: ten architectural sheets, `0` vector paths and `0` text
objects on every one of them. The pipeline stopped at stage 1, where
`engine/frames.py` refused to fit a frame:

```
no segments to fit with; a frame asserted without a measurement
is the assumption this module exists to replace
```

That refusal is the invariant. An empty stroke population is an
**UNREADABLE SOURCE**, and every reading of it as a fact about the building
is false:

| the empty input | the false reading | the true one |
|---|---|---|
| 0 wall-pen segments | "this sheet has no walls" | the reader cannot see this sheet |
| 0 bands | "no double-line wall construction" | nothing was read to pair |
| 0 supported lines | `A_WHOLE_SIDE_HAS_NO_DRAWN_LINE` | the side was never looked at |
| 0 spaces measured | `COMPLETE_MEASUREMENT_RECALL = 0%` | recall is NOT_ESTABLISHED |

The last row is the dangerous one, because `0 / n` is a number and prints
like a result. A run that STOPPED and a run that FOUND NOTHING are different
facts, and a stopped run therefore writes `run_outcome =
STOPPED_BEFORE_COMPLETION` with every metric `NOT_ESTABLISHED` — never a
zero.

The same rule covers the human label set. `load_space_map` returns a
`NoSpaceMap`, not an empty dict, because `0 of 0 labelled spaces found` is
not 100% recall and is not 0% recall — **it is no measurement of recall at
all**, and a plain empty list loses that distinction silently.

**What decides readability is which copy of the drawing you were handed, not
which office drew it.** The same project P7757 supplied, in one folder, a
scanned architectural set with no vector content and a structural set
plotted from CAD (`pdfplot11.hdi`) carrying full linework **and real PDF
text objects**. Representation is a property of the FILE. It must be
established per source, before anything reads it, by
`tools/audit_submission_set.py` — which is why that census reports
per page and not per document.

## 44 · AN ARCHITECT'S PRINTED AREA TABLE IS A KNOWN TOTAL

Project 2's submission set carries its own take-off on two sheets: floor
areas, deductions, totals and percentage-of-plot figures. That is the same
kind of object as a previous BOQ, a contractor quantity or a manual كيال —
a **KNOWN TOTAL** — and on a second project it is the only independent check
of whether the engine measured a real building.

So the set is split BEFORE anything reads it
(`tools/split_submission_set.py`), and the take-off part is registered in
`engine.reference_mapping.SEALED` so `refuse_if_sealed` refuses it **by
name**, from any path. A seal kept in memory is not a seal.


## 45 · A CLASS NAME IS NOT AN OBJECT, AND TWO DECODERS GIVE TWO ANSWERS

Project 7757's DWG was called AEC-custom-object work on the strength of its
readable strings — `AecDbDispRepPolygonTrueColour`, `WallSchem`,
`WindowAssembly`, `DoorRcp`, `AecBase70`. The class table says otherwise:
**244 AEC classes declared, every one with zero instances, none an entity
class.** AutoCAD Architecture registers its class registry in every drawing
it touches. The walls are plain lines; proxies: 0.

**Read the instance count, not the name.**

The same file gives two different answers depending which decoder is asked.
LibreDWG's DXF writer aborts inside `BLOCKS` and emits **no ENTITIES section
at all**; its JSON writer reports `SUCCESS` and decodes 10,796 entities. A
source is therefore never declared unreadable on one decoder's word, and
"the DXF had no entities" is not "the drawing has none" (§43 again, in CAD
clothing).

Two traps inside a decode that succeeded:

- **A decoder artefact is not drawing content.** The JSON carries 66,842
  BLOCK_BEGIN/BLOCK_END records for a file whose block table has 33 entries
  and 931 block references. Counting them inflates the drawing thirtyfold.
  They are excluded, and the exclusion is reported with its arithmetic.
- **An unnamed entity is not an unknown one.** The JSON leaves `entity`
  empty on most records while still carrying the numeric DWG type and the
  AcDb subclass, which name it exactly. Reading the empty string as
  "unidentified" discards ten thousand identified entities.

## 46 · THE PRINTED UNIT IS NOT THE DRAWING UNIT

`$DIMLFAC = 0.1` on project 7757 means every dimension on the sheet prints
one tenth of the distance it measures: **the geometry is millimetres and
the annotation is centimetres.** Its door blocks — `D115`, `D120`, `D200`,
`D315` — are widths in centimetres, and read as millimetres they would be
door openings 115 mm wide.

Any comparison of a printed dimension against measured geometry must apply
that factor. Omitting it is wrong by exactly ten and **passes review,
because both numbers look plausible**. So `declared_units()` reports the
factor whenever it is not 1, in the same breath as the unit.

The unit itself is established the way every measurement in this project is
— one declaration, proven on independent facts:

```
$INSUNITS = 4                      the author says millimetres
$LIMMAX = 84100 x 59400            exactly A1 (841 x 594) x 100, which only
                                   divides cleanly in millimetres
$DIMLFAC = 0.1 + D115/D120/D315    printed cm, and those are plausible door
                                   widths in cm and absurd in mm
```

And an absent variable is not an unrecognised one: `$MEASUREMENT` is missing
from this decoder's JSON output, which is reported as
`NOT_PRESENT_IN_THIS_DECODE` rather than as a reading of it.

## 47 · A COMPLETE ENCLOSURE OF THE WRONG THING PASSES EVERY GATE

Project 7757's CAD run released two spaces. One is labelled `W.C` and
measures **443.841 m² over 31370 × 15000 mm**, which is the plot — `31.37`
and `15.00` are the plot dimensions printed on the sheet. Its vector
boundary support is **100%**, because the site boundary is fully drawn.

It passed the release gate by satisfying every condition the gate tests:

```
enclosure complete          yes - the flood was genuinely stopped
identity established        yes - from an authored room-name block
no dimension disagreement   yes - nothing dimensions a plot-sized rectangle
```

**Nothing in the gate asked whether the measured space is plausibly the
space its label names.** A 443 m² washroom satisfies a gate that never
compares the result to its own seed. Completeness is a statement about the
boundary, not about the identification, and the two were being read as one.

Two source-general causes, both recorded rather than tuned away:

- **A paired-face test is a WALL test, not a ROOM-WALL test.** A majority of
  layer `1`'s 2078 m of axis-aligned length runs as parallel pairs 50–600 mm
  apart, so it is proposed wall-like — and it is very likely the site and
  plot layer. Feed a plot boundary to the enclosure as a wall face and a
  flood that escapes a washroom still closes, on the plot.
- **Text inside a block is not a room stamp.** `NEIGHBOUR`, `STREET`,
  `SEA VIEW` and the level marks are all text carried by placed blocks, so
  all passed the seed filter. 27 of 48 candidates are not rooms.

The fix for each must be structural: a room wall is a paired face that
participates in a **bounded circuit at room scale**, and a room stamp is
text in a block whose **other placements also sit inside bounded areas**.
Neither may be a name test, and neither may be chosen by watching P7757's
numbers improve.

## 48 · AN AUTHORED LAYER NAME IS AS UNTRUSTWORTHY AS A PEN WEIGHT

AR-00's 1.14 pt pen was a fact about one plot that nearly became a
production assumption. P7757 offers the same temptation with a better
disguise: a layer actually called `W`, holding 2,430 lines.

Writing `if layer == "W": wall` would have been right about this drawing and
would have picked **the least convincing of four candidates**. The
geometric test proposes four layers — `1`, `2`, `5` and `W` — and `W`'s
commonest face separations are **80 mm and 63.2 mm**, against layer 2's and
layer 5's clean **300 mm and 600 mm**.

So the split is enforced in code, not in discipline:

```
engine/cad_adapter.py    source-independent. Knows entity types,
                         transforms, coordinates. Matches NO name
engine/cad_profile.py    per source. Observes what each layer CONTAINS,
                         proposes a role, records the evidence and status
```

A profile may conclude that `W` strongly represents walls **on P7757**. It
may never conclude that a layer called `W` represents walls. Tests assert
that a layer named `ZZ-NONSENSE-NAME` is proposed wall-like on its geometry
and that a layer named `WALL` is not proposed when its lines are unpaired.

The same rule governs blocks. `SAL` is not saloon and `MB` is not master
bedroom; they are `LABEL_BEARING_SYMBOL` observations carrying the text they
carry. A block named `WC` is a block named `WC`.

## 49 · A CLOSED POLYGON IS NOT A ROOM, AND ITS SIZE MAY NOT DECIDE

Round 1 released a 443.841 m² polygon labelled `W.C`. It was the plot. Every
gate passed — complete, identified, undisputed by any dimension — because
none asked what KIND of enclosure it was.

```
SITE_OR_PLOT_ENCLOSURE   BUILDING_ENVELOPE   SUPER_REGION
PHYSICAL_ROOM_CANDIDATE  VOID_OR_SHAFT       DETAIL_OR_ANNOTATION
UNRESOLVED
```

**Only `PHYSICAL_ROOM_CANDIDATE` may ever be released.** The decision is
CONTAINMENT, which is scale-free — it fires the same way on a 2 m² shaft and
on a 500 m² plot. No area, no principal dimension and no expected room size
takes any part in it, and a test asserts `area_m2` does not appear in the
classifier at all.

Two independent structural tests, and on P7757 the second is what fired:

- **THE SUPER-REGION TEST.** A candidate containing several independently
  supported space observations **separated by supported partitions** can
  never be one physical room. Asked topologically — can you walk from this
  label to that one without crossing drawn material? — so it needs no size
  comparison. Two labels with nothing between them are NOT a super-region;
  that is what distinguishes one open space from several rooms.

- **THE INTERIOR-VOID TEST.** A polygon with a hole has something enclosed
  inside it that the flood could not enter. On the 443 m² plot there were
  **six**: the building's own rooms. Whether a void is a courtyard, a shaft
  or a column cannot be settled without comparing sizes, so the enclosure
  is UNRESOLVED rather than guessed at.

The second is deliberately conservative — a room with a column in it will
not release either. **FALSE RELEASE IS WORSE THAN ZERO RELEASE**, and if the
safe answer is zero released rooms, zero is the answer.

## 50 · TEXT INSIDE A POLYGON DOES NOT MAKE IT THE ROOM THAT TEXT NAMES

27 of round 1's 48 candidates were not rooms. A street name, a neighbour, a
view and a level mark are all text carried by placed blocks, and the rule
was "text carried by a placed block".

So a step was missing from the chain:

```
TEXT_OBSERVATION -> SEMANTIC_SPACE_OBSERVATION -> SPATIAL_SEED -> PHYSICAL_SPACE
```

`ROOM_LIKE · ZONE_LIKE · NON_SPACE_ANNOTATION · AMBIGUOUS`, and **AMBIGUOUS
releases nothing** — that is the whole point of having the class.

The tests are structural and language-independent, never lexical:

- **A ROOM IS NOT NAMED BY A NUMBER.** Once CAD decoration is stripped, a
  string that is a numeral is a level, a plot dimension or a setback. This
  one test removed 19 of P7757's observations, in Arabic and English alike.
- **A scale ratio marks a drawing title**, not a space.
- **A label outside the built fabric names something outside it** — decided
  by geometry the caller supplies, never by the words.

That no real string steers a decision is asserted two ways: an AST check
that no such word appears in a string literal the classifier can act on,
and a behavioural check that every real word classifies **identically to a
nonsense word** in the same position.

**A label is evidence for IDENTITY. It is never evidence for a BOUNDARY.**
