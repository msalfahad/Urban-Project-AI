# QS MEASUREMENT CLOSURE — architecture note

**Status: EVALUATION ONLY. Nothing here is implemented, and nothing here was
calculated against P7757.** No quantity, no area and no benchmark was opened
to write it. The figures quoted are counts already present in the frozen
E1.4 registers.

---

## 0. What the owner described, and why it matters

The manual AutoCAD workflow is:

1. remove or ignore door leaf and swing graphics
2. temporarily close wall openings
3. obtain closed measurable rooms / cells
4. calculate quantities
5. separately deduct the real doors, windows and openings by trade rule

Step 2 is the one this system has never had. A quantity surveyor closes an
opening **knowing it is open**, uses the closure to define a region, and then
removes the opening again by rule. The closure is a *measurement instrument*.
It is not a claim about the building.

Every version of this engine so far has had three layers —
`PHYSICAL_GEOMETRY`, `TOPOLOGICAL_RELATION`, `TRADE_QUANTITY` — and has
therefore had to obtain measurable regions from the first two. That is the
structural reason for a long run of failures documented below.

The proposal adds a fourth:

| | layer | answers |
|---|---|---|
| A | `PHYSICAL_GEOMETRY` | what physically exists |
| B | `TOPOLOGICAL_RELATION` | door, opening, glazing, open passage, connectivity |
| **C** | **`QS_MEASUREMENT_GEOMETRY`** | **synthetic zero-material closures that make a measurement region well-defined** |
| D | `TRADE_QUANTITY` | deterministic quantity after deductions, additions and rules |

**The assessment of this note is that C is correct, that it is the missing
layer, and that its main value is not closing more rooms — it is permitting
the physical model to stay honestly open.**

---

## 1. The evidence base

All counts below are read from the frozen E1.4 registers for the P7757
ground floor. They were computed by the run that produced them.

**Room closure, `E1_4_COMPLETENESS_REGISTER`:**

```
room candidates                              20
label seeds established                      20      (identity is not the problem)
ENCLOSED_BY_DRAWN_MATERIAL                    3
BOUNDARY_NOT_ESTABLISHED_BY_THE_DRAWING      17
rings that establish geometry                 3
```

The walk's own recorded reason for the 17: *"no walked ring encloses this
point, so the drawing does not establish a boundary for it."*

**Openings, `E1_4_GAP_ONTOLOGY_REGISTER` and
`E1_4_OPENING_DISCOVERY_REGISTER`:**

```
candidate gaps                               50
  CONFIRMED_DOOR_PORTAL                      31
  MATERIAL_CONTINUITY_GAP                     2
  CAD_JUNCTION_GAP                            2
  UNRESOLVED_GAP                             15

openings reconciled                          78
  CONFIRMED_BY_BOTH                          29
  CONFIRMED_DOOR_FIRST                       28
  CONFIRMED_GAP_FIRST                        21
  CONFLICT                                    0
  UNRESOLVED                                  0

portals with evidence                        31
door entities                               291
wall ends with something facing them        124
wall bodies paired (from 386 drawn pieces)  129
```

**One fact that shapes everything below:** only **one** pair of candidates
shares a physical region key. Over-merging — the "blob" failure of earlier
rounds — is *not* the dominant remaining problem. **Under-closure is**:
17 of 20.

---

## 2. Question 2 — which previous failures came from asking physical
## geometry to also serve as measurement geometry?

Taken first, because it is the question the record answers most directly.

**2.1 The engine already contains a measurement closure, in the wrong
layer.** `engine/raster_topology.py` takes `closing_barriers` that shut a
portal in the topology mask, and `portal_barriers` that reopen one. A
"closing barrier" *is* a measurement closure — a synthetic surface placed
across an opening so a region resolves. It lives inside the layer that
decides **connectivity**. So the same object that makes a room measurable
also changes what the model believes about whether you can walk between two
spaces. That is the category error in one file, and it is verifiable rather
than remembered.

**2.2 "Closure is not the measure" had to be written as a rule.**
`E1_4_COMPLETENESS_REGISTER` carries the line *"E1.4 does not succeed by
releasing more rooms, by matching any known area, or by closing more
regions."* A rule like that is only written because the pull existed. The
pull existed because closure was the only route to a measurable region.

**2.3 `CLEAR_ROOM_BOUNDARY_CAPABILITY != PLANAR_PARTITION_CAPABILITY`** —
the lesson preserved from the arrangement experiment. One capability was
being asked to serve two purposes: bounding a room for measurement, and
partitioning the plane. They are different questions and the conflation cost
a whole method.

**2.4 `SINGLE_LINE_PARTITION_CANDIDATE` (round 6B) and the 34 unresolved
polygons.** The pressure to admit a single drawn line as a physical wall,
so that a region would close, is precisely the prohibited *"use a synthetic
closure to repair missing physical geometry"* — reached by necessity rather
than by choice, because there was no other layer to put the closure in.
E1.4 later withdrew 20 312.651 mm of boundary length that E1.2 would have
admitted. That withdrawal was correct and it made closure worse, which is
the trade-off in its purest form.

**2.5 The kitchen polygon at 2.20 × 2.55 (round 6A).** A physical polygon
under-measuring a room, because the only available boundary was the drawn
faces and the drawn faces stop at the openings.

**2.6 Space leaks and merged blobs (rounds 5–6).** Free space leaking
through doorways is the *correct* behaviour of a physical model — the
doorway really is a hole. It was then repaired with portal barriers, i.e.
with measurement closures, inside the physical/topological model.

**2.7 Method 1b, the arrangement experiment.** An attempt to obtain a planar
partition (measurable cells) from physical geometry. It failed under its own
pre-frozen survival criteria: 674 edges, 116 cells, 2 of 7 cases meaningful,
3 of 6 criteria. The cause was located and was not repairable by widening.

**2.8 SAFETY_SAMPLE_03, frozen today.** The semantic layer hit the same wall
from the other side. An opening is an **absence** of geometry; the sampling
unit is built from **drawn intervals**; so across three independently
designed rounds the blind reference established exactly **one**
`OPENING_IN_SEPARATOR` each time. The reference was not failing. A
feature-based unit can only offer an opening where the drawing gives the
opening its own ink.

> **The pattern across 2.1–2.8 is one error wearing eight costumes: an
> opening is a hole in the physical model and a line in the measurement
> model, and the system has only ever had one model to put it in.**

---

## 3. Question 1 — does `QS_MEASUREMENT_GEOMETRY` solve part of the
## historical room-closure problem?

**Yes, and the part it solves is precisely bounded — which is the useful
answer, not the flattering one.**

It solves the case where the boundary walk runs out **at an established
opening**. There the two jamb endpoints exist, the opening is established
with evidence, and a synthetic segment between them is a well-defined,
reversible, zero-material instrument.

It does **not** solve the case where the walk runs out because material is
missing, ambiguous, or never resolved. Bridging there would be inventing the
building. The registers keep these apart already:

```
CONFIRMED_DOOR_PORTAL   31   ← a closure may be defined here
UNRESOLVED_GAP          15   ← a closure may NOT be defined here
```

**What I cannot claim, and will not:** how many of the 17 open rooms would
close under measurement closure. That requires running the walk with
closures admitted at the 31 confirmed portals and counting — a calculation
against P7757, which is out of scope under the current instruction. Any
number offered here would be a guess wearing a register's clothes.

**The measurement that would settle it**, for when it is authorised:

> For each of the 20 candidates, re-run the boundary walk twice — once as
> now, once admitting a closure only at gaps classed `CONFIRMED_DOOR_PORTAL`
> — and report, per candidate: closed-before, closed-after, the closure ids
> used, and for each still-open candidate the class of the gap that stopped
> it. The headline is the count that moves from `BOUNDARY_NOT_ESTABLISHED`
> to `CLOSED_BY_MEASUREMENT_CLOSURE`, reported beside the count still open
> for want of physical evidence. Those two must never be summed.

---

## 4. Question 3 — can this reduce the need for a universally closed
## PHYSICAL room polygon?

**Yes. This is the largest prize in the proposal, and it is larger than the
closure statistics.**

A universally closed physical room polygon is not a description of this
drawing. "17 of 20 rooms are not enclosed by drawn material" is a **true and
useful statement**. Every past attempt to drive that number toward zero
degraded the physical model — admitting single lines as walls, patching
junctions, widening tolerances — because the physical model was being held
responsible for an obligation that belongs to measurement.

With layer C present:

- **A** may be honestly incomplete, and says so.
- **B** may leave a site `UNRESOLVED`, and says so.
- **C** produces a closed region *for a stated trade and basis*, or declines.
- **D** deducts by rule.

The physical model stops being graded on closure. `closure_is_not_the
_measure` stops being a warning that fights the architecture and becomes a
description of it.

**This also changes what "release" should mean.** A room released for
*floor area* under a measurement closure at a confirmed door is not thereby
released for *blockwork*. Release becomes per-trade, which it always was in
practice.

---

## 5. Question 4 — for which trades is measurement closure appropriate?

Appropriate where the quantity is a property of a **region** whose boundary
happens to be interrupted by an opening.

| trade | closure | note |
|---|---|---|
| **Floor area** | yes | the closure defines the polygon and contributes **zero area** |
| **Plaster / paint** | yes | gross perimeter continues across the opening; the door and window areas are deducted separately by rule |
| **Ceiling area / finishes** | yes | same region logic as floor |
| **Skirting** | qualified | region needed, but the skirting is *interrupted* at the threshold — the closure defines the room, then a rule removes its own length |
| **Waterproofing** | qualified, and inverted | may require membrane **continuation across** the threshold — the closure and the trade rule point in opposite directions, so the closure must not be read as the boundary of the membrane |
| **Screed / substrate** | yes | region property |

The worked plaster example in the directive is the shape of this exactly:
gross perimeter 20.60 m continues conceptually across the opening → 61.80 m²
gross → door 1.00 × 2.30 deducted → 59.50 m² net, **while the opening
remains physically open**. The closure created the region. The rule removed
the door. Neither pretended a wall was there.

---

## 6. Question 5 — for which trades would it be dangerous?

Dangerous wherever the quantity is a property of **material** or of
**connectivity** rather than of a region.

| trade / use | why it is dangerous |
|---|---|
| **Wall ceramic / wall tile** | only actual host walls carry tile. A closure contributing wall length invents tile across a doorway. `WALL_LENGTH_CONTRIBUTION = 0` is load-bearing here |
| **Blockwork, masonry, partitions** | a closure must never add wall volume, area or length. This is the failure mode that produces a wrong building |
| **Structural anything** | a closure is not a member |
| **Lintels / openings schedules** | the closure is defined *by* the opening; counting it as wall would delete the opening that justified it |
| **Egress, connectivity, circulation** | closing a doorway destroys the very topology being analysed. This is the `raster_topology` confusion in §2.1 |
| **Fire compartmentation** | a compartment boundary is a physical claim with a rating. A measurement closure has no rating and must never stand in for one |
| **Flooring across an OPEN_PASSAGE** | a true open passage between Salon and Dining may be **one** finish zone. Closing it splits one zone into two and changes the answer. The directive is right that closure must not be automatic |

The distinction that governs the table: **does the quantity accrue to the
region, or to the fabric?** Region → closure may help. Fabric → closure is
poison.

---

## 7. Question 6 — should future quantities be organised around physical
## topology + trade-specific measurement regions, rather than one universal
## room polygon?

**Yes.** The strongest argument is not elegance; it is that the single
universal polygon has already been tried across roughly six rounds and has
failed in a consistent direction, documented in §2.

Three further arguments:

1. **It matches how the work is actually done.** The owner's five-step
   manual workflow *is* trade-specific region construction. A system that
   models the practice will disagree with the practice less often.
2. **It makes disagreement legible.** Two trades legitimately measuring the
   same room differently stops being a contradiction to reconcile and
   becomes two regions with two declared bases.
3. **It removes the incentive to corrupt layer A.** No one needs to admit a
   doubtful wall to make a number appear.

The cost is real and should be stated: **region count multiplies by trade**,
provenance gets heavier, and every quantity must now carry its basis. That
cost is the correct one to pay, because it is the cost of saying what was
actually measured.

---

## 8. Evaluation of `QS_MEASUREMENT_REGION_BUILDER`

The proposed shape is right, including that **it must be code, not an
agent**. Inputs `PHYSICAL_GEOMETRY`, `TOPOLOGICAL_SITES`, `OPENING_REGISTER`,
`TRADE`, `MEASUREMENT_BASIS`, `URBAN_RULE_VERSION`; outputs
`MEASUREMENT_REGION`, `VIRTUAL_CLOSURES`, `PHYSICAL_EDGES_USED`, `OPENINGS`,
`GROSS_QUANTITY_BASIS`, `DEDUCTIONS`, `ADDITIONS`, `UNRESOLVED_ITEMS`.

This is consistent with the standing rule: **AGENTS EXTRACT AND EXPLAIN.
CODE CALCULATES. HUMANS APPROVE EXCEPTIONS.**

Two additions are recommended.

**8.1 `UNRESOLVED_ITEMS` must be able to refuse the whole region.** A builder
that always returns a region will, under pressure, return a bad one. It
needs `REGION_NOT_CONSTRUCTIBLE` with the gap class that blocked it — the
same discipline as `BOUNDARY_NOT_ESTABLISHED_BY_THE_DRAWING`.

**8.2 The closure set must be an output, not an implementation detail.** Two
quantities for the same room are only comparable if they used the same
closures. §10 makes this a comparison contract.

---

## 9. Proposed invariants — the prohibitions, made enforceable

The directive's prohibitions are correct. They will not survive contact with
a deadline unless they are machine-checked. Proposed, for the day this is
built:

1. `WALL_LENGTH_CONTRIBUTION == 0` and `AREA_CONTRIBUTION == 0` for every
   closure, asserted at construction, not by convention.
2. A closure exists **only** with a `SOURCE_OPENING_ID` naming an opening
   established at or above the confidence the trade rule requires. No
   closure may bridge an `UNRESOLVED_GAP`.
3. Closures live in a **separate namespace** from physical elements and can
   never be returned by a physical-geometry query. The `raster_topology`
   `closing_barriers` path in §2.1 is the migration target.
4. **`REVERSIBLE` is tested, not declared**: removing all closures must
   return the physical model byte-identical. A hash comparison, run in CI.
5. Every quantity output states the closures it used, by id, and the count.
6. No metric reported about **layer A** may improve because a closure
   exists. Closure counts and physical-closure counts are reported in
   separate fields and may never be summed.
7. A closure may not be created, widened or retimed to make a region close.
   Construction order is fixed: establish the opening → then construct the
   region. A test should assert the builder cannot see whether the region
   closed when it decides on a closure.

Invariant 6 deserves emphasis. The directive forbids using closures to
"improve room-release statistics". The way that happens in practice is not
fraud; it is a dashboard that counts both kinds of closed room in one
column.

---

## 10. Relation to A19, A21, A22

**A19** — its role gets *narrower and clearer*, which is the right
direction. It may say: *this site is a door opening / a glazed separator /
an open passage / a counter, not a wall*. It does **not** create the
closure. Note the current standing: A19 is `A19_NOT_READY` on one critical
false positive, and SAFETY_SAMPLE_03 stopped before re-testing it. **Layer C
must not be built on A19's output.** Its input is the deterministic
`OPENING_REGISTER` — 31 confirmed portals with evidence, which exist without
A19 entirely. A19 becomes a *candidate proposer for sites the deterministic
registers leave unresolved*, and a human approves those.

**A21** — a visual QS takeoff solver may reason as a surveyor does and
explain *"I treated this doorway as a measurement closure for gross room
perimeter, then deducted the approved door opening."* It **proposes**. The
builder reproduces deterministically or refuses.

**A22** — the owner's point is the important one and deserves to be a rule:

> **Two identical final numbers reached using different wrong assumptions
> are not evidence of correctness.**

So A22's comparison must be **structural, not scalar**. It must compare, and
fail on mismatch even when the totals agree:

```
which virtual closures were used      (by SOURCE_OPENING_ID)
which openings were deducted          (by opening id)
which height rule was used
which trade rule and URBAN_RULE_VERSION
which physical edges were used
```

A recommended verdict vocabulary: `AGREE_ON_DERIVATION`,
`AGREE_ON_NUMBER_ONLY` (explicitly **not** corroboration — it is a flag),
`DISAGREE`, `NOT_COMPARABLE_DIFFERENT_BASIS`. The middle one is the finding
A22 exists to catch.

---

## 11. Risks I would want on the record

1. **Layer C becomes the back door for every prohibited repair.** This is
   the main risk and it is not hypothetical — §2.4 is the system already
   doing it under a different name. Mitigation is §9, enforced in CI.
2. **Trade-specific regions multiply silently.** Without a register of which
   regions exist for which trade and basis, this becomes harder to audit
   than the single polygon it replaces.
3. **`OPEN_PASSAGE` is the hard case and will be got wrong first.** Whether
   a passage receives a closure is trade-dependent and sometimes
   task-dependent within a trade. It should require an explicit rule per
   trade, and default to **no closure** — defaulting to closure silently
   splits spaces.
4. **The opening register is the single point of failure.** Everything in
   layer C rests on it. Its 15 `UNRESOLVED_GAP` rows are the honest edge,
   and pressure will arrive to resolve them by assumption.
5. **Waterproofing inverts the logic** (§5) and should be treated as a
   separate design problem, not a variant of floor area.

---

## 12. Conclusion

The proposal identifies a layer this system has been missing since its first
round, and the record supports it more strongly than it supports most
architectural claims made here: the same category error is visible in eight
places, including one still live in `raster_topology.py` and one frozen
today in SAFETY_SAMPLE_03.

Its chief value is **not** that more rooms will close. It is that
`PHYSICAL_GEOMETRY` will finally be allowed to be an honest description of
the drawing — open where the drawing is open — while measurement gets its
own instrument, with its own provenance, that can be removed without trace.

**Not implemented. Not calculated against P7757. Recorded for evaluation.**
