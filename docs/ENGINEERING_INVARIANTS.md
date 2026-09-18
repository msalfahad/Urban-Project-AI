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

## 51 · A GENERAL VOCABULARY IS NOT A PROJECT-SPECIFIC RULE

Round 2 asserted that `KITCHEN` must classify **exactly** like the nonsense
word `QQZZX`. That was the wrong invariant. It made the semantic layer
blind, and a blind layer cannot tell a kitchen from a street — which is
precisely why a street label seeded a physical room.

The invariant is narrower:

    NO PROJECT-SPECIFIC STRING MAY BE HARDCODED TO FORCE A RESULT

`kitchen` and `مطبخ` mean a kitchen on every drawing in the world.
Refusing to know that is not rigour; it is a different error.

So architectural language lives in a general vocabulary — 53 concepts, 332
English and Arabic terms, matched **exactly on a normalised form** (no
stemming, no substring: `STORE` must not match `STOREY`). Two tests keep it
honest:

- every real project word must reach its class **through the vocabulary**,
  by the same lookup any other term takes;
- **no concept may be named by a single term.** A one-term concept matching
  one project's spelling is that project's rule wearing a general name.

Breadth is the evidence. The vocabulary is required to recognise ward,
classroom, showroom, riser, loggia, atrium, vestibule, مصعد, عيادة, بهو —
none of which appears on any drawing here.

**UNKNOWN stays a first-class answer**, and by §10 an unknown NAME never
invalidates a correct GEOMETRY.

## 52 · TWO LABELS IN ONE PLACE ARE USUALLY ONE NAME WRITTEN TWICE

Round 2 blocked every room on P7757 with
`IDENTITY_AMBIGUOUS_MULTIPLE_LABELS`, because it counted strings. Each stamp
carries an English label and an Arabic one. `SALOON` and `صالون` are not two
identities in conflict; they are one identity stated twice, and seeing both
should make it STRONGER.

```
SAME_CONCEPT               one concept, two statements - identity strengthened
COMPATIBLE                 one known, one UNKNOWN - nothing contradicts
DIFFERENT_FUNCTIONAL_ZONE  a zone within a space, not a rival room
CONFLICT                   two different ROOM concepts - releases nothing
UNKNOWN                    neither recognised - honest
```

Grouping needs **spatial coincidence AND block lineage**: two stamps of
different rooms can fall within two metres of each other near a shared wall,
and merging those would invent a conflict out of a layout accident.

On P7757 this took identity from **0 established to 17, with 0 conflicts**.

## 53 · A ROOM IS CLOSED BY THE WALLS IT NEEDS, NOT THE WALLS IT HAS

A site wall and a partition are both two parallel faces a consistent
distance apart. The paired-face test cannot separate them: it asks how a
line is DRAWN, and the difference is what the line DOES.

So §6's rule is implemented directly:

> Take the outermost boundary of everything the drawn lines enclose. Remove
> the bands lying on it and look again. If every room observation is STILL
> enclosed, that ring was never holding a room in — it bounds ground. If
> removing it leaves a room unenclosed, the building boundary coincides with
> it and it stays eligible.

That is containment, and it reads no area, so a plot far larger than its
building and one barely larger are handled identically.

**Do not overcorrect.** An external building wall MAY form a room side —
where there is no site line the outermost boundary IS the envelope, removing
it opens the rooms, and it stays eligible. Rejecting envelope walls would
make every corner room unmeasurable.

Enclosure runs **twice**: first offering only bands that divide the fabric,
and only if that fails offering the outermost boundary. The first pass is
the nearest supported cycle, and a site line cannot appear in an enclosure
that never used one. "Smallest" is topological throughout — no area is
compared and no room-size prior exists.

Two ways this went wrong before it went right, both caught by synthetic
cases rather than by a client drawing:

- **counting ray crossings is not a nesting depth.** An open partition adds
  crossings on one side only, so a point between the plot and the building
  scored the same depth as a point inside a room.
- **short is not irrelevant.** Excluding runs under 300 mm from room
  boundaries — a rule meant to keep ticks out of ring detection — stripped
  1,313 of 2,877 bands from a drawing whose wall runs average 462 mm, after
  which nothing enclosed at all. Short runs are kept out of the ring model
  and still allowed to form a room side.

---

## 54 · NO RELATIONSHIP MAY CROSS A DRAWING

*Round 4, §1. `STABILITY_SELECTED_DRAWING_REGION_ISOLATION_V1`,
`DRAWING_REGION_HASH bd1c391980507d3e18f5d9db`.*

One model space can hold twelve unrelated drawings. P7757's holds five
plans of the same footprint, 45 m apart along one strip, plus fragments.
Round 3 ran its containment tests across all of them at once and reported
the cost itself: **zero site bands found**, because "the outermost boundary
of everything the lines enclose" spanned the whole strip, and removing it
could not free a room that an elevation's label was never inside.

    NO WALL, PORTAL, ENCLOSURE, ADJACENCY OR CONTAINMENT RELATIONSHIP MAY
    CROSS A DRAWING REGION.

The regions come from the frozen ladder sweep, which reports where the
partition is STABLE rather than choosing a distance. What this invariant
adds is a stated selection rule and one structural correction:

- the most stable plateau; **ties to the finer partition**; the rung
  nearest that plateau's geometric middle;
- **a group lying wholly inside another group's extent is merged into it.**

Ties go finer because the two errors are not symmetric. Splitting one
drawing in two costs measurement — some rooms go unmeasured. Merging two
drawings INVENTS relationships that do not exist. Nesting is the exception
and it is evidence, not a distance: a plot boundary and the villa inside it
are one drawing, and separating them hides the site line from the building
it encloses.

A region is not a floor. `floor_name` is UNKNOWN and stays UNKNOWN; title
text is gathered as evidence and never becomes an identity.

## 55 · A GAP IS NOT AN OPENING, AND AN OPENING IS NOT A WIDTH

*Round 4, §2–§5. `CAD_OPENING_EVIDENCE_CLASSIFIER_V1`,
`CAD_OPENING_CLASSIFIER_HASH 336c6f1bc5bb0a3ea42bb698`.*

The obvious fix for a room that will not close is to bridge the hole in its
wall. It is also the one move that destroys the whole method, because it
asserts material and topology nobody drew.

    WALL GAP ALONE CANNOT CREATE A ROOM-PARTITION PORTAL.

So openings are HYPOTHESES with GRADES, and the grade decides what each may
do:

```
GRADE A  one transformed INSERT supplies the door, reveals agree
GRADE B  a leaf or a swing, in a supported wall interruption
GRADE C  the wall is pierced and its reveals are drawn — but no door is
GRADE D  a gap, and nothing else
```

`MAY_CLOSE_BOUNDARY_FROM = GRADE_C`. `MAY_PARTITION_FROM = GRADE_B`, and
doors only. **Grade D closes nothing, anywhere, ever.**

Three rules hold the class apart from the size:

- **the class never follows the width.** There is no table of plausible
  door widths in the module, and a test asserts there is none.
- **a name never promotes a grade.** `if block starts with "D": portal =
  True` is forbidden; the transformed geometry has to land in a real
  interruption. Width is reported three ways — geometric, block-name (read
  as both millimetres and centimetres, authority NONE), authored dimension
   — compared and **never averaged**.
- **every tolerance is an earlier freeze.** The enclosure's junction reach
  and collinearity tolerance; the profile's wall-thickness band. A test
  asserts each equality. A fresh tolerance chosen while looking at a client
  drawing is that drawing's rule wearing a general name.

Three things a real drawing taught this classifier, each a comparison
between two quantities measured on that same drawing and none of them an
absolute size:

- **a door symbol must SPAN its opening.** A 10.23 m wall line ending near
  a jamb was read as a leaf and graded doors across a drawing; a 900 mm
  leaf beside a 9.45 m hole accounts for 900 mm of it. Leaf plus the
  measured frame inset either side must equal the measured width.
- **the symbol sits IN the opening, not ON its corner.** Door leaves hang
  inside the frame — 60 mm on P7757 — so a coincidence test against the
  jamb point missed almost every real door. The test is containment in the
  opening's own footprint, grown by the thickness of that same wall.
- **a gap narrower than the wall it pierces is a break in a drawn line.**
  Nothing passes through an opening narrower than the wall around it. It is
  classified as such, and it is NOT bridged.

## 56 · A WINDOW IS NOT A DOOR, AND A DOORLESS OPENING DECIDES NOTHING

*Round 4, §6–§9, through the frozen `space_topologies` model.*

```
                    material      room partition         navigable
door (A/B)          zero          TWO_DISTINCT           yes
doorless (C)        zero          UNRESOLVED             yes
window              zero          boundary continues     NO
wall gap (D)        —             nothing closes         —
```

A validated door closes the room boundary with `MATERIAL_PRESENT_LENGTH =
0`. A **doorless opening resolves neither relation** — it may close the
polygon and it leaves `ROOM_PARTITION_RELATION_UNRESOLVED`, which blocks
release and asserts neither one space nor two. A **window may never become
a room-to-room passage and may never leak a room polygon to exterior
space.**

Where several identities sit inside one geometric face with no supported
partition between them, the answer is ONE PHYSICAL SPACE with FUNCTIONAL
ZONES. **No wall and no portal is manufactured between them, and no
identity is discarded.**

At every opening the four lengths stay apart:

```
SPACE_BOUNDARY_LENGTH    the room's perimeter, including the portal span
OPENING_LENGTH           the portal width, clipped to what lies on THIS face
MATERIAL_PRESENT_LENGTH  zero across the opening
HOST_WALL_GROSS_LENGTH   only where host continuation is independently
                         established
```

The room polygon's perimeter is **not** the material wall length, and an
opening's contribution to one room is the part of it that lies on that
room's boundary — summing whole widths once produced 11.05 m of opening on
a 9.4 m perimeter.

## 57 · A ROOM DOES NOT NEED A NAME TO EXIST

*Round 4, §11–§12. `REGION_LOCAL_ROOM_PARTITION_GRAPH_V1`,
`ROOM_PARTITION_GRAPH_HASH 6bd4f2ff9ac748948e441baa`.*

Every round before this started from a label: find a room stamp, flood from
it, see what closes. That made measurement hostage to the text layer — and
on P7757 sixteen of thirty-three identities are Arabic in an SHX font this
decoder returns as mojibake.

    DERIVE SUPPORTED BOUNDED PHYSICAL-SPACE CANDIDATES FROM GEOMETRY FIRST.
    THEN ATTACH SEMANTIC IDENTITY.

The region's eligible bands plus the portals that earned the right to close
something form one local arrangement; **its bounded faces ARE the
candidates**; the frozen enclosure measures each from a point inside it;
identity is attached last. A face with no readable label reports
`PHYSICAL_SPACE_VALIDATED_IDENTITY_UNKNOWN` — it exists, it is measured,
and it still may not RELEASE, because a face with no label can never be a
`PHYSICAL_ROOM_CANDIDATE`. Round 2's safety is untouched.

A face whose **mean thickness** — twice area over perimeter — is no more
than the profile's maximum wall thickness is the inside of a wall, not a
space. A bounding box will not do this: a perimeter wall's ring has the
bbox of the whole building and is still 200 mm of blockwork.

Hosts are matched **locally or not at all**. Six named checks, no global
nearest-wall search; where two openings claim the same door geometry the
answer is `PORTAL_HOST_AMBIGUOUS`, which blocks release through that portal
and **does not decay into a guess**.

## 58 · A PRESERVED HASH IS A PROPERTY OF ITS RUN, NOT A RECOMPUTATION

*Round 4, §18.*

`PROJECT_2_CAD_BASELINE_HASH`, `PROJECT_2_CAD_ROUND2_HASH` and
`PROJECT_2_CAD_ROUND3_HASH` are properties of the runs that produced them
and they live in those runs' artefacts. A later round that changes what is
measured will recompute a DIFFERENT number under the same name. That is not
a violation of "preserve unchanged" — overwriting the artefact would be —
but reporting it as though it were the preserved value is.

So a round-4 run declares the preserved values, checks the files still
carry them, chains its own hash from the preserved STRING, and reports its
recomputations separately under `recomputed_under_round_4`.

Only a hash that is a property of the CODE — `ROUND_3_SYNTHETIC_HASH`,
`ROUND_4_SYNTHETIC_HASH` — must still compute to the same value later, and
only those may be asserted by a test.

**Round 5 sharpened this, and corrected how round 4 had phrased it.** Four
objects, never one:

```
HISTORICAL_ARTIFACT_HASH      what the run recorded, at the time. Immutable
CODE_HASH_AT_FREEZE           the module hashes it recorded beside it
DEPENDENCY_HASHES_AT_FREEZE   what those modules stood on, then
CURRENT_REPLAY_HASH           what the same self-test computes TODAY
```

Round 2's `ROUND_2_SYNTHETIC_HASH` is `de1caf07e16e738b3e34dcc5` and always
will be. Round 3 rewrote the semantic seed classifier, so replaying round
2's twelve cases under round-3 code computes `55b221fa624f5e2d5d8ba32b`.
Round 4's report called that "round 3 did not preserve the hash", which is
the wrong description and invites the wrong fix — going back and editing an
old record until a number matches.

    A HISTORICAL FREEZE IS IMMUTABLE. A REPLAY IS A DIFFERENT OBJECT, AND
    A DIVERGENCE BETWEEN THEM IS INFORMATION, NOT A FAILURE.

A PROJECT output hash is not replayable at all: it is a property of a run
over a client drawing. It is recorded and never recomputed.

`engine/freeze_manifest.py` carries all four objects for rounds 1–4 in
committed code, because `data/runs/` is gitignored and a record that lives
only there leaves with the container. It verifies the declared values
against the artefacts whenever those are present, and
`assert_no_artifact_was_rewritten` fails loudly if an artefact ever stops
saying what it said.

---

## 59 · A WALL'S IDENTITY MUST SURVIVE THE FRAGMENTATION OF ITS FACES

*Round 5, §2–§3, §5. `FRAGMENT_TOLERANT_PHYSICAL_WALL_BAND_V1`,
`PHYSICAL_WALL_BAND_HASH 35449c817a74f5c1e3e45cf1`.*

One built partition reaches this engine as two continuous faces, or one
continuous face and a fragmented opposite, or fragments on both sides, or a
run broken at every junction it passes, or a run broken for no reason at
all by whoever drew it. On P7757, 1,804 of 3,272 wall bands have a
half-drawn span and 1,965 have an undrawn gap.

The chain is kept whole and no link may be skipped:

```
CAD primitives -> wall-face OBSERVATIONS -> wall-BAND hypothesis
  -> PHYSICAL WALL hypothesis -> opening subtraction -> room boundary
```

    NEVER: two collinear lines -> invent a wall.
    NEVER: a gap -> bridge the gap.

Pairing is required, using the profile's own structural test, so a lone
line stays a line. A wall's extent is then held in three registers that
never merge — `OBSERVED_FACE` (what is drawn),
`INFERRED_PHYSICAL_WALL_EXTENT` (what it appears to occupy),
`MATERIAL_QUANTITY_AUTHORITY` (only the spans where both faces are drawn).

A SHORT OVERHANG IS A CORNER, NOT A MISSING FACE. Where a ring's outer face
wraps past its inner one the overhang is the wall's own thickness, and a
first version of this model "recovered" every corner of every building
before a synthetic case caught it. A face running METRES past its partner
is the opposite case and is exactly what §5 exists for.

## 60 · FALSE SUBDIVISION IS AS DANGEROUS AS FALSE MERGING

*Round 5, §4, §7–§11, §16. `NAMED_EVIDENCE_PARTITION_CONTINUITY_V1`
(`PARTITION_CONTINUITY_HASH f9b9742aa125bfd028b75166`) and
`SUPPORTED_PARTITION_FACE_SUBDIVISION_V1`
(`FACE_SUBDIVISION_HASH 1313a956a735565e0905a42e`).*

Five answers, and the default is the unhelpful one:

```
ESTABLISHED_CONTINUATION   one face runs across it, or another wall's
                           material occupies it
SUPPORTED_CONTINUATION     another wall terminates into it
OPENING_INTERRUPTION       a door, window or supported archway is there
NO_CONTINUATION            the wall ends
UNRESOLVED_GAP             none of the above is established
```

    THERE IS NO `bridge_collinear_gap()` AND THERE MAY NOT BE ONE.

Ten evidence tokens are named on every span; none is weighted and nothing
is summed. **Only two may raise a verdict** — another wall's material
occupying the span, or another wall terminating into it. Collinearity,
matching ends, a repeated band and shared CAD provenance are consequences
of one fact, that runs exist either side, and a rule resting on them is
`bridge_collinear_gap()` under another name. A first version let them
through and recovered a plain unexplained gap immediately.

**Openings are tested FIRST and outrank every positive sign.** A door drawn
across a span is the reason the span is empty; no material is ever
recovered there.

The same discipline governs splitting a face:

    SEMANTIC OBSERVATIONS MAY DIAGNOSE UNDER-SEGMENTATION.
    THEY MAY NOT CREATE THE MISSING GEOMETRY.

A polygon holding several reconciled room concepts is flagged
`POSSIBLE_UNDERSEGMENTED_SPACE` and classified on geometry alone —
`ONE_PHYSICAL_SPACE`, `MULTIPLE_PHYSICAL_SPACES` or
`ROOM_PARTITION_UNRESOLVED`. A face is never split because it holds many
labels, because its area looks too large, because a room "should" be there,
or because an expected count says so. A Gulf villa is full of open plan,
and splitting a kitchen from a dining area that share one supported polygon
would invent two rooms and two sets of walls nobody built.

## 61 · TOPOLOGY AUTHORITY IS NOT MATERIAL AUTHORITY

*Round 5, §6, §10.*

A recovered span can be strong enough to say TWO ROOMS ARE SEPARATE and too
weak to let anybody measure blockwork across it. Every span carries both:

```
TOPOLOGY_AUTHORITY   VALIDATED | SUPPORTED | FROM_A_PORTAL | NONE
MATERIAL_AUTHORITY   ESTABLISHED | CANDIDATE | BELONGS_TO_ANOTHER_WALL
                     | ABSENT_AT_AN_OPENING | NONE
```

`topology = VALIDATED, material = CANDIDATE` is the NORMAL result of a
one-face recovery. `SUPPORTED` may subdivide a face and may never release
one. A junction's occupancy is `BELONGS_TO_ANOTHER_WALL`, so the same
blockwork is never counted twice.

The room's own lengths carry the same separation, with three subtractions
rather than one:

```
SPACE_BOUNDARY_LENGTH
OPENING_LENGTH                         zero material across an opening
RECOVERED_BOUNDARY_LENGTH              a side nobody drew
MATERIAL_AUTHORITY_ESTABLISHED_LENGTH  what is actually measurable
```

On P7757 the four released rooms have 17.79, 9.00, 7.85 and 15.64 m of
boundary and 0.11, 3.00, 0.00 and 0.00 m of measurable material. They are
releasable as AREAS and not as BLOCKWORK, and a round that reported only
the perimeter would have created four sets of wall quantities out of lines
nobody drew.

## 62 · A SNAP TOLERANCE IS DERIVED FROM THE DRAWING, AND REPORTED

*Round 5, §12–§13. `DERIVED_TOLERANCE_JUNCTION_RECOVERY_V1`,
`JUNCTION_RECOVERY_HASH cbe777aa922d5ad948ad4189`.*

A drafter's line ends where the mouse let go. A partition that stops two
millimetres short of the wall it meets leaves a hairline slot a flood walks
straight through, and that is one of the ways a floor of rooms becomes one
face. But a real gap between two walls must never become a junction, and
the distance between those two statements may not be settled by a constant
taken from a client's drawing.

```
tolerance = max(drafting_resolution_mm, min(thickness_a, thickness_b))
```

The drafting resolution is READ OFF the drawing — the finest unit nearly
all of its coordinates sit on. The thickness is the thinner of the two
walls meeting: a miss smaller than that lands inside the junction's own
material, and a larger one is a space between two walls. **Every junction
reports the tolerance it was judged by**, and a test asserts the string
`7757` appears nowhere in the module.

A column is a closed figure whose BOTH extents lie inside the profile's
wall band. It may not become a room, it may not break a partition that
terminates into it, and observing one begins no structural quantity. This
is architectural topology only.

## 63 · ONE LINE IS ONE WALL FACE OVER ONE STRETCH

*Round 6, addendum §1. `ONE_LINE_ONE_WALL_PHYSICAL_BAND_V2`,
`PHYSICAL_WALL_BAND_HASH b6d79d2b5c5e2c13eb5d546d`.*

A wall is two faces a consistent distance apart. One line is a line. Accepting
every parallel neighbour a wall-like distance away lets ONE drawn line act as a
face of four different walls over the same stretch, and each of those phantom
bands then licenses a recovered span that slices a real room.

```
A line may face two walls over DISJOINT stretches, and never over the same
stretch.
```

That is explicit geometric evidence, not a tolerance. On P7757 it refused
2,883 of 3,272 offered pairs and left 389 bands.

Evidence is ORDERED, never summed:

```
AN_OPENING_IS_HOSTED_BETWEEN_THESE_TWO_FACES
A_REVEAL_CLOSES_THE_BAND_AT_BOTH_ENDS
A_REVEAL_CLOSES_THE_BAND_AT_ONE_END
EACH_FACE_IS_THE_OTHER_S_NEAREST_ADMISSIBLE_PARTNER
THE_SEPARATION_IS_A_THICKNESS_THIS_DRAWING_REPEATS
ANOTHER_WALL_MEETS_THIS_BAND
```

**A repeated thickness never defines a wall.** It ranks a contested pair, and
it can neither admit a pair the structural test rejects nor reject one it
admits. No millimetre figure anywhere in this engine is declared to be, or not
to be, a wall — 50 mm is P7757's most repeated separation and it is ranked like
any other.

## 64 · A BAND PAIRED ON NOTHING MAY RECOVER NOTHING

*Round 6, step 4. `NAMED_EVIDENCE_PARTITION_CONTINUITY_V1`.*

Continuity recovery is only as sound as the band it recovers across. A band
whose sole evidence is `THE_FACES_RUN_ALONGSIDE_EACH_OTHER` is proximity, and
proximity is not pairing:

```
weak -> UNRESOLVED_GAP,  TOPOLOGY_NONE,  MATERIAL_NONE
        Z_THE_BAND_ITSELF_IS_PAIRED_ON_NOTHING_BUT_PROXIMITY
```

This is §31 applied one level down. Round 5 already refused to treat
collinearity as evidence of a wall; round 6 refuses to treat adjacency as
evidence that there is a wall to be collinear WITH.

## 65 · UNKNOWN IS NOT VOID

*Round 6, step 3. `POSITIVE_EVIDENCE_CAD_SPACE_ROLE_V1`,
`CAD_SPACE_ROLE_HASH cf6191908829d6a7d3b022d1`.*

VOID and SHAFT are claims about what lies above and below a space. Nobody
having written a name inside it is not such a claim. Round 5 called 43 of 57
polygons VOID_OR_SHAFT by reading the round-2 ENCLOSURE role — whose
`VOID_OR_SHAFT` means only "not a room seed" — as an architectural verdict.
Two different questions had collapsed into one label.

```
UNNAMED_PENETRATION_NEEDS = (NO_OPENING_ANYWHERE_ON_ITS_BOUNDARY,
                             THE_SAME_FOOTPRINT_APPEARS_ON_ANOTHER_PLAN)
```

Both, or the space is `INTERIOR_SPACE_UNCLASSIFIED` — an honest "not known
yet", which is not releasable and is not a void. **No role is decided by how
big a space is.** On P7757, 40 spaces have no opening at all and 13 of those
repeat their footprint on another plan; only those 13 are called penetrations.

INTERIOR and EXTERIOR are decided the same way, by envelope evidence rather
than by area: the site ring minus the fabric ring is the exterior ground. Where
a drawing carries no site boundary — as P7757 does not, in any of its nine
regions — the engine enumerates ZERO exterior spaces and says so. A garden
strip that cannot be separated is reported as unseparated, never invented.

## 66 · A WALL IS WHERE THE SPACES STOP

*Round 6A, §2. `SPACE_STOPS_AT_THE_FACE_WALL_OWNERSHIP_V1`,
`WALL_FACE_OWNERSHIP_HASH a36a3169568d9858ca913fda`.*

P7757's kitchen measured 2.20 x 2.55 m against 3.00 x 2.70. The missing
800 and 150 mm are two kitchen counters:

```
CAD-310  x = -152339.9   the west wall's internal face
CAD-311  x = -151839.9   a 500 mm counter in front of it
CAD-283  y = -800593.5   the north wall's internal face
CAD-284  y = -801093.5   a 500 mm counter in front of it
```

The flood stops at the FIRST line it meets, and the first line it meets is
a worktop. Between 2700 mm of clear floor and 2200 mm of unobstructed
floor sits a counter, and only one of those two numbers is a floor area.

Two questions answer it, asked of every line and every pair:

```
IS THERE OPEN SPACE ON THE OTHER SIDE OF YOU?
IS THERE OPEN SPACE OUTSIDE EACH OF YOU, AND NONE BETWEEN YOU?
```

**No layer is trusted or distrusted.** The counter and the wall it stands
against are on the same layers as each other elsewhere in the same
drawing, and a module that read layer names would have to be retuned for
every client.

The reading is done from DRAWN COORDINATES, not from polygons. A wall's
interior is a closed cell only if every line round it meets every other,
and one 50 mm slot at a window turns the inside of a wall into the whole
floor plate — which is how the first version of this rule read P7757's own
kitchen wall as open floor. A strip wider than the profile's
`MAX_WALL_THICKNESS_MM` is space; anything narrower is not. No new
constant exists.

And the drawing is read TWICE, because the question cannot be answered
while a tile joint is still treated as something a room might stop at:
pair with no topology evidence, set aside every line that is a face of no
wall and has floor on both sides, then read again. A strip counts as the
inside of a wall only when the two lines bounding it are the two faces of
ONE established band — which is what separates a 200 mm wall from the
500 mm gap behind a worktop. Both are narrow; only one has a wall's two
faces around it.

## 67 · ONE WALL GIVES OPPOSITE FACES TO THE TWO ROOMS IT SEPARATES

*Round 6A, §3 and §4.*

Ownership is the side the space is on. A wall yields its low face to the
room on the low side and its HIGH face to the room on the high side, and
no boundary is ever drawn down the middle of a wall to be shared between
them. Every established face carries:

```
SPACE_LEFT / SPACE_RIGHT        which side of its own axis it faces
INTERIOR / EXTERIOR / UNKNOWN   from the envelope model
OPEN_SPACE / INSIDE_A_WALL / OUTSIDE_THE_DRAWN_ARRANGEMENT
```

Four measurement bases exist, and none is ever switched silently:

```
CLEAR_INTERNAL_FINISH_FACE   the only basis a floor quantity may use
STRUCTURAL_FACE              not measured on this drawing
WALL_CENTERLINE              never a floor area
EXTERNAL_FACE                envelope quantities only
MEASUREMENT_BASIS_NOT_ESTABLISHED
```

Every physical space names its basis, its boundary face ids, its wall band
ids, and the CAD entity and selection reason for EVERY side. A side nobody
can attribute is `MEASUREMENT_BASIS_NOT_ESTABLISHED`, and that withholds
the release rather than being filled in. The frozen enclosure is untouched
and is reported beside it as the OBSTRUCTED EXTENT — a diagnostic, never a
floor area.

## 68 · THE BUILDING AND THE SITE ARE TWO QUESTIONS

*Round 6A, §9.*

Whether geometry is inside the BUILDING is answered by the envelope. How
far the ground around it EXTENDS is answered by the site boundary, and
only by that.

```
INSIDE_BUILDING / OUTSIDE_BUILDING / BUILDING_EXTENT_UNKNOWN
SITE_EXTENT_ESTABLISHED / SITE_EXTENT_UNKNOWN
```

A drawing with no site ring — P7757 in all nine of its regions — can still
know that something lies outside its building. That space is
`EXTERIOR_EXTENT_UNRESOLVED`: enough to keep it out of an internal floor
finish, and not enough to measure a yard. **No site polygon is invented to
close the gap**, and no missing site ever makes outside-the-building
interior.

## 69 · ONE LINE, THREE AUTHORITIES, AND ONLY ONE OF THEM IS FREE

*Round 6B, §1–§6. `POSITIVE_EVIDENCE_SINGLE_LINE_PARTITION_V1`,
`SINGLE_LINE_PARTITION_HASH 2b9480e67e799c2b3d1f837f`.*

A 100 mm block wall drawn as one line is still a wall. A worktop drawn as
one line is still a worktop. Telling them apart is what this is for, and
the answer is never one thing:

```
TOPOLOGY_AUTHORITY        are these two spaces separate?
CLEAR_FACE_AUTHORITY      where exactly does each room's floor stop?
MATERIAL_WALL_AUTHORITY   how much blockwork, plaster, paint is there?
```

A supported single-line partition may establish TWO PHYSICAL SPACES
without establishing one millimetre of wall thickness. The three results
are never collapsed:

```
A  topology established, clear face established, MATERIAL NOT
B  topology established, clear face NOT,         MATERIAL NOT
C  unresolved
```

**§6 IS MANDATORY AND IT IS NOT A THRESHOLD.** A line has no thickness,
so every millimetre of boundary a partition holds is subtracted from the
measurable wall exactly as an opening is. It may not create blockwork,
plaster, paint, wall ceramic or waterproofing. On P7757, 213.4 m of
boundary is held this way and contributes zero.

**A SECOND FACE IS NEVER INVENTED.** The centreline is not substituted,
because half of an unknown number is still unknown. The clear face is
taken only from evidence outside the line: a band it continues, the
reveals of an opening drawn in it, or an authored dimension that ends on
it. A test asserts the module contains no `/ 2`, no `* 0.5` and no
"centre".

## 70 · DIVIDING A REGION IS NOT EVIDENCE OF BEING A PARTITION

*Round 6B, §3.*

That reasoning is circular, and it would make blockwork out of every
dimension line, hatch boundary and worktop. A partition is ANCHORED and
then CORROBORATED: one strong token and two in total.

```
STRONG       an opening hosted on it, the same line on another plan,
             a partition alignment it continues, or a named room on
             EACH SIDE of it
SUPPORTING   wall to wall, one end at a wall, a T or L junction,
             an authored dimension ending on it
```

**Running from wall to wall is SUPPORTING.** A worktop is fitted between
two walls; so is a wardrobe and so is a bath. Spanning the room is what a
fitting does, and treating it as strong brought P7757's kitchen counter
straight back as a partition.

Two corollaries the synthetic cases forced, both of which a real drawing
would have hidden:

* **A side is a half-plane only if you ask it badly.** "Is something named
  on each side of this line" is true of every line in a building. Each
  side reaches only as far as the next parallel line the drawing puts
  there; a worktop has nothing named in its 500 mm.

* **A CROSSING WALL IS NOT A REVEAL.** A reveal spans the band and stops.
  A wall's face runs on past. Counting the second made a worktop "closed
  at both ends" by the walls it is fitted between, on better evidence than
  the wall it stands against.

And a partition with a door in it is drawn as TWO PIECES, neither of which
has a room on each side. Collinear pieces are merged across a gap that an
opening on that very line explains, and across no other gap.

---

## 71 · MEASURING A POLYGON IS NOT KNOWING WHAT IT IS

Four areas, and adding any two of them together produces a number that
means nothing:

```
MEASURED_CANDIDATE_AREA        every polygon that has a boundary basis
PHYSICAL_SPACE_AREA            the ones that are spaces of the building
RELEASE_ELIGIBLE_GEOMETRY_AREA the ones the release gate passes
TRADE_MEASUREMENT_AREA         what a trade may price. A later round
```

On P7757 the first is 269.1838 m² over 40 rows and the third is 26.3085
m² over 6. Reporting the first as released floor area — which round 6B's
own report did — is the failure this invariant exists to prevent.

**A candidate's role is never inferred from its area.** A 1,020 m²
polygon is sheet content because it repeats in three drawing regions; a
1.2 m² polygon is refused because it is a stair tread. Neither verdict
would survive a size rule, in either direction.

---

## 72 · A ROOM QUANTITY IS REFUSED BEFORE IT IS COMPUTED, NOT AFTER

A room quantity taken from an elevation is not a small error. So every
drawing region is asked what it SHOWS and WHICH FLOOR it is, and only a
`FLOOR_PLAN` or a `ROOF_PLAN` **whose floor is also established** may
release room quantities.

`UNKNOWN` is not a floor plan by default. A region nobody has identified
releases nothing, which is the entire point of asking.

**A floor nobody stated is not derived from geometry.** P7757 carries no
decodable title text at all — its titles are drawn in an SHX font this
decoder does not resolve — so its floors arrive as a SUPERVISED
ASSIGNMENT, carried as supplied with `provenance = SUPERVISED_AUDIT` and
never as `DERIVED_FROM_THE_DRAWING`. The assignment is data, keyed on
what a region is; no region id appears in any module.

A title is read from text that is **not one of that region's own room
stamps** and is at least as big as the text the sheet repeats, and where
a string matches words of several roles the LONGEST match wins. Without
the first rule a room called PLAN ROOM retitles the drawing; without the
last, `SITE PLAN` is a floor plan.

---

## 73 · A FITTING HAS TWO FACES AND THEY DO NOT MEAN THE SAME THING

A band standing on another band is a fitting: two established bands that
share a face line over overlapping stretches, with their other faces on
OPPOSITE sides of it. The one that RUNS FURTHER is the wall — a lining is
fitted along part of a wall, never the other way round.

```
the SHARED face  is where it meets the wall. A space bounded there is
                 bounded by the WALL BEHIND it, and that is what every
                 wall lining in every building does
the FRONT face   stands out into the room. A candidate that stops at it
                 is the strip the fitting leaves over, not a room
```

**Only the front face blocks.** Blocking anything a fitting touches takes
the room with the strip: P7757's kitchen — 8.100 m², bounded at the
shared face by the wall behind its counter — was withheld by exactly that
mistake, alongside the 2.25 m² pantry strip the rule was written for.

---

## 74 · A CONTAINER OF ROOMS IS NOT A ROOM. A CONTAINER OF NOTHING IS

Counted both ways, a floor's area is its own double, so a candidate that
contains candidates **which are themselves spaces** is a SUPER_REGION and
releases nothing.

Containment alone is not that test. A room with a decorative rectangle
drawn inside it contains a candidate, and it is still a room: the
rectangle is not a space, and releasing the room double-counts nothing.
Which means the role decides the release and the geometry decides the
role — in that order, which is why it takes two passes.

---

## 75 · A LABEL BELONGS TO A ROOM, NOT TO THE SMALLEST BOX AROUND THE TEXT

A counter, a wardrobe, a vanity and a stair cell all contain text. The
room that text names is the one those things stand IN.

So the candidates for a label are the spaces containing it, and among
them the smallest that is not a super-region wins. Where the only
candidate is a subcell of something unresolved, and where two candidates
claim it and neither is inside the other, the answer is an EXCEPTION —
`THE_ONLY_CANDIDATE_IS_A_SUBCELL_INSIDE_A_LARGER_UNRESOLVED_SPACE` and
`SEVERAL_PHYSICAL_SPACES_CONTAIN_THIS_LABEL`. A smallest-polygon rule
would answer both, and half the time it would be wrong.

**An unknown word is not guessed.** A term the vocabulary does not know
keeps `UNKNOWN_TERM`: not translated, not matched to the nearest known
word, and not dropped. The space it names is still measured, because an
unreadable label must not destroy correct geometry.

---

## 76 · A STAIR IS A SPACE AND ITS PLAN RECTANGLE IS NOT A ROOM AREA

A stair arrives as a run of closed cells, one per tread, and two tread
lines 400 mm apart pair into a band as readily as a thin wall does — so a
tread can reach the register with a clear internal basis and 1.2 m² of
floor.

It is registered as a physical space and it releases no room area. A
stair's floor is measured on its going and its rise, never as a rectangle
on plan, and that is a quantity-surveying fact rather than a threshold.

---

## 77 · A WALL OWNS STRETCHES OF ITS LINES, NOT THE SPAN BETWEEN THEM

A band that reports the interval from its first millimetre to its last
claims everything in between, including stretches another wall is drawn
along. A wall owns a SET:

```
owned_mm    the stretches of its two lines it uses, taken in evidence
            order with every stretch another wall holds blocked out
drawn_mm    where BOTH its faces are drawn — where it IS a band
face_stretches(which)
            where THAT face is drawn, within what the wall owns
```

The gap a doorway leaves INSIDE a wall belongs to that wall. A stretch
the wall next door is drawn along does not. One interval cannot say
which is which, and a hull says the wrong one.

**Three readers, three questions, and crossing them costs a room.**
Where a face is drawn is what attributes a room's boundary. Where a band
IS a band is the evidence a single line continues. Which stretches a
wall uses is what an opening, a fitting and this invariant are asked
about.

**And two spans of the same coverage are not one span when a stretch
belonging to another wall lies between them.** Joining across that hole
is how a wall reports continuous ownership of a line it does not own.

---

## 78 · A FITTING'S FRONT FACE IS NOT WHERE A ROOM ENDS

A band that shares a face line with another band, stands on the opposite
side of it, and is DRAWN over a shorter run is a fitting: a counter, a
run of units, a wardrobe, a duct casing.

```
the SHARED face  is where it meets the wall. A space on that side is
                 bounded by the wall behind, which draws that line
the FRONT face   stands out into the room. No room ends there
```

A fitting gives no clear internal finish face, is not the inside of a
wall for the flood, and **cannot become a single-line partition however
much evidence it collects** — a counter runs wall to wall, continues an
alignment and has an opening beside it, and every one of those tokens is
true of it.

Which of two stacked bands is the wall is decided on HOW FAR EACH IS
DRAWN. How much of the shared line each ended up owning says nothing:
only one of them can own any given stretch of it.

---

## 79 · A PANTRY IS NOT ALWAYS A ROOM

```
PHYSICAL_SPACE  ->  FUNCTIONAL_ZONE  ->  TRADE_MEASUREMENT_ZONE
```

A functional zone creates no wall, no room and no quantity. One open
space may hold a saloon, a dining, an American pantry and a circulation
zone with nothing physical between them, and none of those boundaries
may ever become blockwork or a room polygon.

```
CLOSED_PANTRY            four sides of established wall face
OPEN_AMERICAN_PANTRY     it shares its space with the dining, saloon,
                         living or reception it serves
PANTRY_OPENNESS_UNKNOWN  a side no wall accounts for and nothing named
                         beyond it. Open to WHAT, nobody says
```

**An open edge tiles nothing**, and the zone is never closed virtually
to produce a fourth wall. **Without the units' own geometry the tiled
length is NOT ESTABLISHED**: which stretch of an open space's perimeter
is the pantry's is a question the units answer. **And no tile height is
ever assumed** — without an owner rule the height and every area resting
on it are an OWNER_RULE_REQUEST.

---

## 80 · A STAIR IS FIVE QUANTITIES AND A PLAN ANSWERS THREE

```
TREAD_M2   every tread from ITS OWN polygon — never a constant width
           times a constant going times a count
RISER_M2   width by height, and a PLAN CARRIES NO HEIGHT
LANDING_M2 what the flights leave between them
NOSING_LM  the exposed front edges
STAIR_SKIRTING_LM   separately again
```

Square metres and linear metres are never added. Where the stair finish
differs from the floor's — marble on the stair, porcelain around it —
**the same square metre may not appear in both**, and a stair's footprint
belongs to the stair.

Without section evidence every riser is `RISER_QUANTITY_NOT_ESTABLISHED`.
Neither `treads = risers` nor `treads = risers - 1` is derived anywhere.

A run of parallel lines at a tread's going is also a louvre, a grating
and a run of shelving. Four things separate a stair from them, each
stated as a share or as the module's own figure:

* **a stair fills its cell** — a run covering a small share of the cell
  it stands in, with no stair label, is refused;
* **two lines less than a going apart are one step's edge** — a nosing
  line in front of each riser line is not a second flight;
* **a walk is cut where the spans jump** — a room's own wall sits a
  going from the first tread and joins the walk;
* **runs in one cell are flights of one stair.**

Where two flights of one stair overlap, their treads cannot both be
marble and neither is chosen: the tread quantity is NOT ESTABLISHED.

---

## 81 · A MODEL HASH FREEZES A VOCABULARY, NOT A BEHAVIOUR

These hashes are computed from a module's model name, its evidence
tokens and its frozen parameters. Round 6D rewrote how three modules
DECIDE without touching any of those, and their hashes would not have
moved while the measured numbers did.

**A replay that matches while the numbers move is worse than useless.**
So a round that changes what a module concludes bumps that module's
MODEL name, the freeze replays as `REPLAY_DIVERGED_UNDER_LATER_CODE`,
and the reason is recorded against it in `PREDICTED_DIVERGENCES`.

The CASES are the score. The hash is the question.

---

## 82 · A RUN CANDIDATE IS NOT A PHYSICAL IDENTITY

Between the frozen 6C and 6D bundles, 68 `physical_space_id` values
appear in both and 17 of them change area by more than 5%. Areas
**swapped** between ids. Those ids were the order the flood happened to
enumerate faces in, and nothing else — and nothing else is what they can
carry. There are two:

```
RUN_CANDIDATE_ID          this run's enumeration. It may change on every
                          execution, and that is allowed
STABLE_PHYSICAL_SPACE_ID  the identity of a space of the building. It
                          survives ordinary geometry refinement
```

A stable id is carried forward **on evidence** — the region and floor, how
much of it the same polygon covers both ways round, its centroid relative
to its own region, the wall bands that bound it, what it is called — and
**never on area**: two rooms of 12.60 m² on one floor are two rooms, and
area is the one piece of evidence that cannot tell them apart.

Every space of a run gets one of nine answers: `UNCHANGED`, `RESHAPED`,
`SPLIT`, `MERGED`, `NEW`, `REMOVED`, `IDENTITY_CHANGED`, `ROLE_CHANGED`,
`UNRESOLVED_LINEAGE`.

**A split gives NEITHER child the parent's id.** Whichever child the
flood enumerates first is not the parent, and pretending otherwise is how
a revision comparison silently follows the wrong room. **A merge keeps
EVERY predecessor**, because a merged space is one identity with several
histories and losing one loses a revision.

---

## 83 · ONE AUTHORITATIVE RELEASE STATE

Round 6D reported a candidate as `PARTIAL_SPACE`, `is_physical_space`
false, `may_release` false — and `RELEASE_ELIGIBLE_GEOMETRY`, because
that string came from the measurement layer and nothing revised it.
Three fields that can contradict each other are not a decision.

`RELEASE_STATUS` is the only release answer. It is computed last, from
everything the register knows, and the measurement's own verdict is
carried beside it as `geometry_gate_status`, under a name that cannot be
mistaken for it. `RELEASED_FOR_ROOM_QUANTITY` may never coexist with
`may_release=false`, `is_physical_space=false`, or the roles
`PARTIAL_SPACE`, `DRAWING_ARTIFACT`, `SUPER_REGION`, `UNRESOLVED`,
`EXTERIOR`, `VOID`, `SHAFT`, `STAIR`. **A withheld candidate always says
why.**

---

## 84 · REPORT_METRIC == DETERMINISTIC_AGGREGATION(EXPORT)

Every headline number in a report is declared as an aggregation over a
named export table — a filter, a column, an operation — and recomputed
from the rows that were actually written. **Neither number is ever
changed to make them agree**: a disagreement means the report counts
something the export does not carry, or the export is missing rows the
report counted, and rounding one to the other hides which.

---

## 85 · AN EXPORT CARRIES WHERE IT CAME FROM, OR IT IS NOT EXPORTED

Before a table is written: the worktree is `CLEAN`, `HEAD` is recorded in
full, the **tree** hash is recorded, the tests are recorded as passed
with a count from a run that happened, and the input drawing is hashed by
its own bytes. An export from an unclean worktree cannot be reproduced
from its commit, so it is refused.

Two hashes per file, because they answer two questions:

```
RAW_FILE_SHA256           the bytes. Is this the same FILE?
CANONICAL_CONTENT_SHA256  sorted keys, no insignificant whitespace.
                          Is this the same ANSWER, however written out?
```

A manifest that gives one hash and calls it "the hash" is what this
exists to stop.

---

## 86 · A STAIR'S KIND IS WHAT IT DOES, AND A LANDING IS PART OF THE STAIR

A main stair **carries a storey**: it stands inside the building, it is
drawn on the plans of two established floors, and no wider interior stair
does the same. A run that climbs out of one plan into nothing established
is `STAIR_ROLE_UNKNOWN` however wide it is drawn — Round 6D called a
four-tread run of 2.80 m the MAIN stair of the building while the curved
stair that carries the storey came out SECONDARY. `SERVICE_STAIR` and
`LANDSCAPE_STEPS` need a rule or a label to say so; no arrangement of
lines on a plan tells them from the stair beside them. **And no stair is
marble because it is a stair.**

Each piece of floor between the flights is classified from its own
geometry:

```
STAIR_LANDING       it joins the ENDS of flights and is no larger than
                    the flights it joins
OPEN_VOID           it runs along their SIDES and meets the end of none
CIRCULATION_FLOOR   the room around the stair reaches it
FLOOR_PLATE         it is simply larger than the stair
```

Only a landing is stair quantity. Round 6D called an 11.93 m² plate —
7.0 m long beside a 1.25 m flight — a landing; the rest is reported
beside the stair as floor, so that no square metre is billed marble over
porcelain.

Stair coverage is reported **per floor**: a floor whose plans draw
stair-like geometry and yield no staircase has `STAIR_COVERAGE_FAILED`,
not coverage of one stair, and every unresolved observation is listed,
largest first, with what it covers.

---

## 87 · A RISER HEIGHT IS SEARCHED FOR, AND NEVER ASSUMED

A plan carries no height, so the whole architectural set is searched:
level marks, riser notes, section and elevation sheets. Each finding is
`PLACED` (it has coordinates the engine can attribute), a **LEAD** (it
sits in a representation this project cannot place), or refused.

A riser height comes from a floor-to-floor rise **between two named
floors** divided by a riser **count** that is itself established. Not
150, not 170, not 175, not "typical": a habit is not evidence. For P7757
the set does carry the answer — the DWF's W2D streams hold seven level
marks and the sheets SECTION A-A and SECTION B-B — and this project has
no W2D reader, so the riser height stays NOT ESTABLISHED with
`NO_READER_PLACES_THE_VERTICAL_EVIDENCE_THIS_SET_CARRIES`.

**An area printed on a drawing is still the sealed take-off.** A text
that states a quantity is refused by name, so that nobody reads it by
accident.

---

## 88 · AN OWNER RULE IS A RECORD, AND IT NEVER SUPPLIES GEOMETRY

Owner knowledge lives in a versioned library, not in a constant in an
engine file. Every rule carries `rule_id`, `rule_name`, `trade`, `scope`,
country context, default-or-mandatory, `owner_confirmed`, `version`,
`effective_date`, `source`, whether a project may override it,
`required_geometry`, `calculation_method`, `unit`, `exceptions` and
`unknown_behavior`. **A record missing any of those is refused**: a rule
nobody can date, version or source is a habit somebody typed in.

```
PROJECT DRAWING / SPECIFICATION     what this building actually is
PROJECT-SPECIFIC OWNER OVERRIDE     what the owner said about THIS one
URBAN PROJECTS OWNER STANDARD       what the company does by default
UNKNOWN / ASK OWNER                 and nothing below it is invented
```

A default never bypasses geometry. Where a rule carries a dimension and
the drawing establishes another, **the drawing wins** and the resolution
says so. Where the geometry a rule needs is not established, the answer
is the rule's own `unknown_behavior` — a named refusal or an
`OWNER_RULE_REQUEST` carrying the exact term, its place in the drawing
and the question that would settle it. **Never a silent guess.**

---

## 89 · A STAIR IS MARBLE BY PROJECT RULE, AND THE MARBLE RISER IS NOT THE RISE

For Urban Projects' Kuwait villa and chalet workflow the finish rule is
MARBLE on tread (نايم), riser (قائم) and landing (استراحة), and it
applies to **every stair assembly the engine detects** — main, secondary,
service, roof, external steps — not only the main staircase. A drawing,
specification or owner statement for a particular stair overrides it. The
rule is applied to stairs that were DETECTED: a stair-like observation
nobody reconstructed stays unresolved, never marble.

The step rises by one figure and shows another. The tread's marble sits
on top of the step, so the face that is clad and seen is

```
VISIBLE_RISER_HEIGHT = step_rise − tread_build_up
RISER_VISIBLE_M2     = stair_width × VISIBLE_RISER_HEIGHT
```

The owner's worked example — 1.20 m wide, 0.30 m going, 0.16 m rise,
0.03 m tread, giving 0.360 m² + 0.156 m² = 0.516 m² per step — is
arithmetic, not a constant. **0.13 m is never hardcoded.** Without both
the rise and the build-up detail the visible riser is
`VISIBLE_RISER_HEIGHT_NOT_ESTABLISHED`.

`GEOMETRIC_MEASUREMENT_UNIT` and `CONTRACTOR_COMMERCIAL_PRICING_BASIS`
are separate fields: a contractor may quote stair work by the step while
the physical marble stays an area, and neither ever stands in for the
other.

---

## 90 · AN ELEVATOR SURROUND IS A POLYGON, AND A STATION IS A DOOR

One elevator serving four floors is **four** landing stations; two doors
on one floor are **two** assemblies. The shaft is never the count, and a
typical station stands for many only once the doors, surrounds, detail
and finish are established equal — with every station id preserved.

Marble surrounds the outer landing door on LEFT, TOP and RIGHT, 0.50 m
wide by Urban Projects default and by the drawing wherever it says. It is
bought by area, and the area comes from the **union of the three bands**,
because three sides times a width is wrong in both directions: along the
door edge it misses both top corners (2.60 m² for a 1.00 × 2.10 door with
0.50 m sides), and as three full bands it counts them twice (3.60 m²).
The union is 3.10 m². `ELEVATOR_SURROUND_AREA_M2` and
`ELEVATOR_SURROUND_EDGE_LM` are kept apart and neither substitutes for
the other.

The marble threshold at the door is its own object, never merged into the
vertical surround, and `ELEVATOR_THRESHOLD_MARBLE_AREA ∩
PORCELAIN_FLOOR_AREA = 0 m²`. Its depth is **not** an owner-confirmed
default: where neither drawing nor detail establishes it, the run asks.

---

## 91 · A TREAD HAS FOUR EDGES, AND ONLY ONE OF THEM IS THE NOSING

```
FRONT / NOSING   across the WIDTH, at the front of the step
BACK             across the WIDTH, against the next riser
INNER SIDE       along the GOING, at the inner string — an ARC on a winder
OUTER SIDE       along the GOING, at the outer string — an ARC on a winder
```

Round 6E gave a winder tread its **outer arc** as the nosing length:
378.1 mm on a tread 1250 mm wide. Fifteen treads of PS-STAIR-002 measured
18.450 m of front edge and were exported as 8.058 m of nosing. On a
winder the width is the radial front edge and the going is the arc; they
are different lengths and **only the first is a nosing**.

So the nosing length is **read off the front edge** rather than computed
beside it, and every tread carries an edge audit in which the two cannot
disagree.

---

## 92 · GEOMETRY AND COMMERCE ARE TWO TRUTHS, AND BOTH ARE KEPT

```
GEOMETRY     TREAD_AREA_M2  RISER_AREA_M2  VISIBLE_RISER_AREA_M2
             LANDING_AREA_M2  NOSING_LENGTH_LM
COMMERCIAL   STAIR_STEP_COMMERCIAL_LM  LANDING_COMMERCIAL_M2
             STAIR_SKIRTING_COMMERCIAL_LM
```

Urban Projects buys marble steps by the **linear metre of step width**,
and that rate covers tread, riser and nosing together. So

```
STAIR_STEP_COMMERCIAL_LM = SUM(width of each UNIQUE physical step)
```

**never derived from a tread area** — a winder's treads are wedges and
the going is not constant — and **never counted twice**: the same
staircase drawn on the ground and the first floor plan is one staircase,
and the steps are summed on the PHYSICAL assembly after the cross-plan
reconciliation. The landing is an area and the skirting a length; neither
is multiplied by the step basis, and no total spans the units.

---

## 93 · A RATE IS NOT A RULE

Three things that look alike and are not:

```
A  CONSTRUCTION VOCABULARY   نايم is a stair tread
B  MEASUREMENT RULE          its commercial quantity is the sum of the
                             unique step widths, in lm
C  COMMERCIAL RATE           15 KWD/lm, on one quotation, on one date
```

The rule library holds A and B, each record carrying `rule_kind`, and
**refuses any record that carries a currency**. C lives in a project rate
card with its supplier and its date, and nothing in the measuring engine
reads one. A price inside a measurement rule is a price that goes stale
without anybody noticing.

---

## 94 · A STRONG RUN THE DETECTOR CANNOT BUILD IS A QUESTION

A flight's worth of tread lines (`MIN_TREADS + 1`), every pitch a tread
going, over a width at least as great as the deepest going this module
recognises, is **`STAIR_OBSERVATION_UNRESOLVED`** when no staircase was
reconstructed from it — not `NOT_A_STAIR_ON_EVIDENCE`. P7757's ROOF plan
refused five such runs in Round 6E and reported nothing; four of them are
11–12 lines at 250–400 mm over 1150–1350 mm of width.

Weak runs — hatching, three short lines in a corner — stay answered. And
a stair register is about **plans**: an unresolved run on an elevation or
a section is counted apart, never as a missing staircase on a floor.

---

## 95 · A SECOND DESIGN SET IS ITS OWN SOURCE, AND ITS ALIGNMENT IS A CLAIM

The architectural drawing says where the walls are; the sanitary drawing
says where the water and the drainage are. They are two representations
of one building, so the sanitary set is registered as **DESIGN_SANITARY**
with its own hash and its own coordinates, and it never replaces or
overwrites the architectural decode.

What joins them is a **tested** alignment. A sheet plotted "to fit" has
no round scale — P7757's drainage plan is 38.0 mm per point, a 1:100 plot
reduced to 1:108 — so the scale is searched for, and the search must
produce a **winner**:

```
at least 60% of the plan's LONG walls matched, on BOTH axes, within 40 mm
and the winning scale ahead of every other scale by 15% of those walls
```

Otherwise `ALIGNMENT_AMBIGUOUS` or `ALIGNMENT_NOT_ESTABLISHED`, and
nothing is placed through it. An alignment that is nearly right puts a
floor drain in the wrong room.

**The architecture is subtracted before anything is counted.** A sanitary
sheet redraws the walls as its background; counting those lines as
drainage makes every room look plumbed.

**And a symbol is not a rule.** A drainage point near a pantry says water
arrives there. It does not say which wall is tiled, how high, or that
there is a sink. Linework spread evenly around a label **names no host
wall**, and the engine says so rather than picking one.

---

## 96 · A ZERO BY RULE IS NOT A ZERO BY IGNORANCE

A wet room whose wall ceramic runs full height takes **no** floor
skirting: the tile already reaches the floor. That quantity is `0.00 lm`
and it is `MEASURED_NET` — the rule decided it. A room whose wall ceramic
extent nobody established also reports no skirting, and that one is
`NOT_ESTABLISHED` with the missing fact named.

The two look identical in a total and mean opposite things. Every
finishes quantity therefore carries its **rule id**, its **unit** and its
**status**, and a quantity with no established geometry behind it returns
`None`, never `0`.

The same distinction governs the rest of the pack: an edge takes a mitred
45° finish **or** a steel profile and never both; a stair skirting
follows the **zigzag** or the **rake**, never the plan run beneath them;
a railing follows the **open edge** only, so a flight between two walls
takes none; and the waterproofing membrane **carries through the
doorway** — the one place in the pack where a door is not a deduction.

Four quantities stay apart everywhere: `MEASURED_NET`, `WASTE`,
`PROCUREMENT` and `CONTRACTOR_COMMERCIAL`. A contractor's convention
changes what is paid for, never what is built.

---

## 97 · A DELTA IS RECONCILED BY HYPOTHESIS, NEVER BY ADJUSTMENT

A take-off and a benchmark that differ are two measurements of one
building, and the difference is information. It is reconciled by finding
what the two SCOPES or BASES disagree about — and never by moving a
number toward the other.

The P7757 ground-floor open zone: 138.7867 m² of take-off against a
137.5000 m² benchmark, a gap of 1.2867 m² (0.94%). Every line of the
take-off checks out exactly. The gap has a candidate identity: the
take-off deducts **half** the pool's circular segment (1.2448 m²) where
the benchmark behaves as though the **whole** of it were deducted —
which leaves 0.0418 m², and 137.5418 rounded to the nearest half-metre
is 137.5.

That arithmetic is recorded as arithmetic. **It is not a reason to
prefer that reading** — see §98, which this section originally broke by
ranking the hypothesis first for landing on the number. **The applicable
fraction of a curved intrusion is evidence**: half a segment is deducted
when half of it falls inside the room, and which half that is comes from
the drawing. A fraction nobody established is refused — it is exactly
the kind of silent default that makes two honest take-offs differ by one
half-segment and nobody know why.

Nothing in the engine reads a benchmark. A comparison against one is
disclosed as benchmark-informed, and it changes no tolerance, no
threshold and no dimension.


---

## 98 · A BENCHMARK MAY NOT ANCHOR AN INTERPRETATION

A benchmark is the only independent check a project has of whether this
engine measures a real building. It stops being one the moment it
influences the interpretation it is meant to test — and **influence does
not need intent**: an interpreter who knows the expected area finds the
reading that produces it, and experiences that as having seen it.

```
BLIND INTERPRETATION   no human quantity, no reconstructed quantity, no
                       expected area, no benchmark-derived dimension, and
                       no previous numeric correction whose value would
                       reveal the target
FREEZE                 the candidate geometry is hashed and can no
                       longer move
RECONCILIATION         only now may a benchmark be opened, and only to
                       explain a difference — never to choose a reading
```

**A numerical coincidence with a benchmark is not geometric evidence.**
Where two readings of a curved boundary give different areas and one
lands on the benchmark, that landing is a fact about arithmetic and no
part of the case for that reading. What establishes a curve, an arc, a
segment, a fraction or a boundary: drawing geometry, a CAD entity, an
authored dimension, spatial topology, the specification, independent
visual evidence, or a human saying so.

Hypotheses raised after a reveal stay `UNCONFIRMED` until independent
geometric evidence supports them, and **they are never ordered by
closeness**. Where no evidence separates them they stay `UNRANKED`,
however neatly one of them lands.

This project broke that rule once, in the ground-floor open zone
reconciliation, and the breach is recorded in that document rather than
edited out of it.

---

## 99 · A BLIND PASS RECEIVES THE DRAWING, AND THE CONTRACT SAYS SO

A blind visual pass exists to answer one question: **can this agent see
the drawing**. It is not a test of whether an agent can find, somewhere
in this repository, an answer somebody has already worked out. The two
outcomes look identical — both produce a number that agrees with the
benchmark — and only one of them is evidence that the engine can read a
building.

So the input side is a contract, in `engine/blind_input_contract.py`,
rather than an intention.

```
MAY RECEIVE     the selected source drawing image; a whole-floor image
                and crops generated from it; drawing metadata that
                identifies the sheet and floor; approved Urban Projects
                GENERAL construction rules; project specifications that
                would be on the desk of anybody doing this for real
NEVER RECEIVES  a reconciliation file, a human quantity workbook, a
                manually reconstructed quantity, a correction note, a
                known target area, a previous agent's answer, an owner
                rule request whose text reveals the geometry it asks
                about, a hypothesis formed after a reveal, or previously
                corrected geometry for the spaces under test
```

Six gates stand between an input and the pass, because **a declared kind
is only as honest as the caller**: `DECLARED`, `KIND`, `PATH`,
`CROP_BASIS`, `EXISTS`, `CONTENT`. The path is checked as well as the
kind, so relabelling a reconciliation file as sheet metadata does not get
it through. An **undeclared kind is refused**, because a missing rule is
not a permissive rule.

**A crop drawn around the answer is the answer.** A box chosen from a
known target hands the pass the reading it was meant to find, in a form
no content scan can catch, so every crop declares what decided its box —
a uniform tiling, coordinates read off the drawing, or the agent asking
to look there — and a crop with no basis is refused.

**A specification about the space under test is not a specification.** A
surveyor on site has the spec; a pass being tested on whether it can see
the ground-floor open zone may not have the block that describes that
zone. The rest of the spec stays.

Refusal and contamination are different events. An input refused **at the
door** never reached the agent: the refusal is recorded and the run stays
`BLIND_RUN_VALID`. Prohibited information found **in the context** ends
the run — `BLIND_TEST_INVALID`, `stopped`, and every further offer
raises. There is no partial credit, because a pass that has seen the
answer cannot un-see it.

Every blind run writes `A18_INPUT_MANIFEST.json`: each input by
`RAW_FILE_SHA256` or `CANONICAL_CONTENT_SHA256`, what it is, which gates
it passed, what was refused and why, and a `MANIFEST_HASH` over the
whole record. A blind run is reproducible from that list and from
nothing else.

---

## 100 · A GATE YOU CAN WALK AROUND IS A NOTE, NOT A GATE

The input contract of §99 refused a file and the file reached the cold
agent anyway, because the sandbox was assembled with a copy command and
the contract was consulted afterwards. The contract was right and it
changed nothing.

So `engine/agent_sandbox.py` holds two properties, and the second is what
makes the first real:

```
THE ONLY WAY IN    bytes reach the sandbox through place(), which screens
                   the input first and WRITES NOTHING when the contract
                   refuses. A refused input raises
THE ONLY WAY OUT   immediately before launch, verify() walks the sandbox
                   on disk and requires

                       SANDBOX_CONTENTS == ADMITTED_INPUT_MANIFEST

                   byte for byte. Anything present that was not admitted
                   fails the launch, however it got there
```

The one exception is declared in advance: directories the agent writes its
own working files into. Those must be **empty at verification time**,
because "created after execution starts" is a claim that can be checked
rather than trusted — a working directory with files in it before launch
had them put there by somebody.

`launch_token()` is issued by verification, never asked for. A caller that
launches without one has not checked, and the token goes stale the moment
the sandbox changes.

**A procedural breach is not the same as a leak.** The review that found
this one said so explicitly: `INVALID_PROCEDURAL_INPUT_CONTRACT_BREACH`,
not a finding that a benchmark quantity reached the pass. The run was
preserved exactly, marked `PRESERVED_NOT_USED_AS_BLIND_SCORE`, and rerun
clean — the verdict recorded in a file of its own rather than edited into
the evidence.

And the scanner that caused it was fixed in the other direction too. The
word `expected` in *"a break is expected because a stair is its own
finish"* is English; `expected area` is a benchmark. A scanner that cannot
tell them apart gets switched off by whoever has to work around it, and a
switched-off scanner protects nothing — so a trigger word now counts only
where it is **attached to a quantity**, `actual` is not a trigger at all
because in construction prose it means *as drawn*, and `known` and
`reference` count only beside a word for an answer. What the content gate
cannot catch is a bare number with no trigger beside it; benchmark
**documents** are kept out by path instead, wholesale, before anything
reads them.

---

## §101 — A layer says what to test. An entity says what it is.

E1 v1 profiled the drawing's layers, found that `1`, `5`, `W` and `2` hold
mostly paired faces, and then treated every line on them as a
`MATERIAL_WALL_FACE`. Its own provenance register said, in writing,

```
ENTITY_ESTABLISHED_ROLE = NOT_ESTABLISHED_PER_ENTITY
```

and it released boundaries built from those entities anyway. Layer `5`
carries the kitchen's wall **and** the kitchen's cabinet front, so the
released Kitchen ran along a run of base units 500 mm inside the room and
came out 2200 mm wide where the architect had dimensioned 2700.

So the hierarchy is fixed, and it is a hierarchy rather than a threshold:

```
LAYER_DEFAULT_ROLE       candidate-generation evidence ONLY
ENTITY_ESTABLISHED_ROLE  required before a segment may bound material
UNKNOWN                  never releases as a room wall
```

What separates the two, generally and without knowing what room it is in:

> **A WALL SEPARATES TWO SPACES.** It is drawn as two faces with the wall
> body between them, and its ends land on other walls.
>
> **CASEWORK STANDS INSIDE ONE SPACE.** It is a single face standing off a
> wall at fitted-unit depth — deeper than any ordinary wall, which is
> exactly why the two can be told apart — with short returns back to it.

Three details decided whether that rule worked at all on a real drawing,
and each was wrong first:

- **A dimension line runs parallel to the wall it measures.** In this
  drawing it does so 135 mm away, inside the wall-thickness band, so the
  cabinet front paired with a dimension line and became a wall. Only
  entities that could themselves be built material take part in the
  parallel reasoning.
- **A wall's two faces are rarely two lines.** An opening breaks one face
  into pieces while the other runs on, so the partner is matched against
  the **union** of the collinear fragments at one offset.
- **A line a hair off due west lands at 179.99°**, which rounded into a
  bin the lookup never visited. Two faces of one wall were stored apart,
  and 600 mm of wall beside a door was invisible.

## §102 — A doorway is not an open side, and a stamp is not a room

Three more corrections in the same iteration, each from the same mistake:
taking a token for the thing it names.

**The drawing is bilingual.** Every room carries an English stamp and an
Arabic one, and the Arabic comes back through an SHX font the decoder
cannot map — `ASVQBaL` beside `RECEPTION`. E1 v1 counted each as a
functional space, so a room labelled twice became
`MULTI_FUNCTION_PHYSICAL_REGION`. Script is now decided from the
drawing's own typography — the text style, whether the string is
generated backwards, whether the glyphs read as a word — and **no token
is mapped to a word anywhere in the code**. Only a readable stamp in a
different label group can make a region multi-function.

**A text insertion point is not the middle of the text.** It is where the
string starts, and for a right-to-left stamp it is at the other end. It
is weak evidence, and a label conflict may never be raised from it alone.

**A line drawn from the centre of a circle is how the circle was set
out.** E1 v1 fed the pool's radial setting-out lines to the same tracer
as the walls and polygonize cut the pool into wedges, two of which were
released as rooms. The arcs were never the problem. A winder tread points
at the same centre and **stops short of it**, running between two
concentric arcs — that one ratio keeps the pool's construction lines out
of the stair register and the pool's wedges out of the room register.

**A doorway is not an open side.** When the blind reading says a space is
open and CAD closes it with a door-width portal, that contradicts the
reading rather than confirming it — a doorway is a hole in a wall, and
the reading was that there is no wall. `CONFIRMED_BY_CAD` is no longer a
status: every agreement names *what* agrees — the identity, the topology,
or the boundary — because a closed ring containing the same text stamp
confirms none of the other two.

---

## §103 — A role belongs to an interval, never to an entity

E1.1 asked "what is this line?" and answered once per line. One CAD line
can be parallel to a wall face for 600 mm of its four metres, and that
600 mm of evidence established the whole entity as `MATERIAL_WALL_FACE`.

The unit of role is now the **atomic entity interval**: a stretch between
two evidence-change points, carrying its own role, confidence, evidence,
the partner intervals that support it and the evidence that contradicts
it. An entity is cut wherever the evidence could change — a partner's
overlap beginning or ending, a junction, a jamb, a portal, an
intersection, a casework return, a column boundary, a block boundary, a
semantic transition. Ninety-four entities on this floor carry more than
one role, and the register says which stretch is which.

**Evidence licenses the stretch it exists on.** A partner running along
600 mm of a 4 m line says what that 600 mm is and says nothing whatever
about the other 3.4 m. No role is ever written back onto the parent: an
entity's "role" is a summary of its intervals, not a fact about it.

Three consequences that are easy to get wrong:

- **The support of a counter-face is a UNION.** An opening breaks one
  face into pieces while the other runs on. Whether a band exists at an
  offset at all is asked once, of everything the fragments cover
  together; where it exists, every stretch it covers is supported. Every
  fragment stays in provenance — E1.1 recorded one partner where the
  decision came from three.
- **A wall face runs to the corner it meets.** Its partner turns the
  corner one wall thickness earlier, so the last stretch of a face is
  routinely unsupported and is still the same wall. A supported run may
  reach its own end when the tail is no longer than one wall thickness.
  Bounded by construction; it cannot become whole-entity promotion again.
- **Connectivity is a property of the band, not of a cut.** Because an
  entity is cut wherever evidence changes, an interval's end is usually
  in the middle of a wall. "Does this join anything?" is asked at the
  ends of the supported run, and the answer is carried to every interval
  inside it.

## §104 — Four things a closed ring does not prove

**A small closed loop is a question, not a column.** Furniture, a
fixture, a planter, a duct and a pier all draw one. E1.1 established 220
wall faces from loop size alone. A loop is now a `COLUMN_CANDIDATE` until
structural evidence agrees — a layer that holds almost nothing but such
loops, block lineage, a hatch inside it, a grid relationship with loops
of its own family, wall connectivity — and at least one of those must be
structural *in kind*, because repetition says "these are the same
object", not "this object is structural". Four identical wardrobes repeat
and line up too.

**Collinearity is not material.** Lying on the same infinite line as a
wall face is a fact about coordinates. E1.1 turned 69 entities into wall
that way, including a 1000 mm entity on the LEVEL layer. The relation is
now recorded as `COLLINEAR_GEOMETRIC_CONTINUATION`, and only becomes
`MATERIAL_WALL_CONTINUATION_ESTABLISHED` when the wall BAND continues
over the stretch too. A level mark, a dimension, a fixture or a cabinet
front never inherits a wall role.

**Double linework is not necessarily a wall.** Two parallel lines a
wall's thickness apart may be a wall, a counter, a bar, a run of
casework, a low partition or glazing — in plan they are the same drawing.
Where the band joins the wall network at neither end, CAD says
`AMBIGUOUS_PAIRED_BAND` and carries all eight readings as conflicting
evidence, rather than picking one. Closure is not evidence and neither is
the area it would produce.

**A note about the site is not a room.** E1.1 counted NEIGHBOUR,
NEIGHBOUR, STREET and SEA VIEW among twenty-four "functional
identities", which made the completeness denominator wrong and put four
permanent withheld rows in the register for things that were never
rooms. A label is now classed before anything asks it for a boundary,
from where it sits relative to the plot outline, how it is set beside the
room stamps, how it is turned, and whether its glyphs read at all. No
list of site words appears in the code.

## §105 — A layer that checks the drawing may not say it looked at it

E1.1 named its gate `visual_gate`, gave it a `sheet=` argument, checked
entity roles, dimensions, label counts and whether the raster had
registered — and returned `VISUALLY_CONSISTENT`. It never read a pixel.

That layer is now `DETERMINISTIC_DRAWING_QA`. Its states say what it
actually established: `DETERMINISTICALLY_CONSISTENT`, or a named
conflict. `VISUALLY_CONSISTENT` is not in its vocabulary and emitting it
raises.

Looking is done by a **cold challenger**, in two stages, because an
overlay anchors whoever sees it. **V1 sees the source sheet crop and the
identity text, and never the proposal**: it writes down what is drawn —
walls, open sides, doorways, glazing, counters, bars, casework, columns,
stairs, curves, low partitions, ambiguous lines, connected zones. V1 is
frozen. **V2 then sees the same crop, the frozen V1 observation and one
proposed boundary** and answers a single question: does this follow
actual physical enclosure?

The challenger may disagree and may veto a release. It may not move a CAD
coordinate, propose a corrected polygon, or return an area, a length or
any quantity — returns are screened for both. Correction is made in CAD,
by code, after the semantic evidence exists.

And **A18 is a challenger, not the answer.** E1.1 withheld any candidate
the frozen blind reading called open, which makes one witness final. A
disagreement is now arbitrated on the CAD interval evidence, the portal
evidence and the cold visual passes, and can be resolved *against* the
frozen reading. Only a conflict the evidence does not settle blocks
release.

Closure rate is not an optimisation target. A stricter evidence rule that
releases fewer regions has done its job.
