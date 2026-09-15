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
