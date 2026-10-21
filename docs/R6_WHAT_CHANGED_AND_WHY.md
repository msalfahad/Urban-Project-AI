# R6: what changed, why, and what it does to the numbers

R5 was not accepted. The grounds were specific and, checked against R5's own
registers, all twelve were right. This is what each one turned out to be, what
replaced it, and what the replacement costs. Nothing here was tuned toward the
frozen takeoff, the historical workbook, or any figure reported earlier; where a
quantity disappeared it stayed gone.

## The one that mattered most

R5's report said the thirty-five gaps in wall lines were things *"nothing in the
source names as an opening — no door block, no window block, no schedule row, no
layer that says opening."*

R5's own admission register, in the package that sentence was delivered in, gave
every one of those objects a `CAD_BLOCK_IDENTITY` of the form
`DOOR-<zone>::<ref>`. The source names them as doors. What R5 had actually
discovered was that each door's rectangle overlapped no wall material — which is
the *normal* condition for a door in a drawing that stops each wall at its
jambs, not evidence against its existence.

So R6 splits the question in two:

- **admission** asks *does the source say this object exists* — answered from
  naming provenance (a CAD block, a schedule row, a symbol or opening layer, a
  swing arc) and from **no wall geometry at all**;
- **host resolution** asks *which wall does it interrupt* — answered from the
  material *around* the opening, and allowed to fail without retracting it.

| object class | meaning |
|---|---|
| `OPENING_CONFIRMED_HOST_CONFIRMED` | it exists, and the wall it interrupts is proved |
| `OPENING_CONFIRMED_HOST_UNRESOLVED` | it exists; which wall is an open question, and the opening stays in the population and in every coverage check |
| `OPENING_CANDIDATE_UNRESOLVED` | the source has not said what it is |
| `NON_OPENING_GAP` | the source settles that it is not an opening |
| `DRAWING_NOISE` | below the drawing's own drafting resolution |

## Before and after, on the real drawing

The R5 column is read out of the delivered
`ALRASHED_5_GENERIC_ENGINE_VALIDATION.zip`, not off disk, so it can be checked
independently.

| R5 said | R6 says | objects | why it moved |
|---|---|---|---|
| `OPENING_CANDIDATE_UNRESOLVED` | `OPENING_CONFIRMED_HOST_CONFIRMED` | 23 | the CAD block names it a door, and two collinear wall ends bracket it |
| `OPENING_CANDIDATE_UNRESOLVED` | `OPENING_CONFIRMED_HOST_UNRESOLVED` | 12 | the CAD block names it a door; which wall hosts it is still a question |
| `CONFIRMED_OPENING` | `OPENING_CONFIRMED_HOST_CONFIRMED` | 7 | unchanged in substance; the class name now carries the host state |
| `DRAWING_NOISE` | `OPENING_CANDIDATE_UNRESOLVED` | 1 | a sub-resolution mark is not proof of *absence* either |
| `NON_OPENING_GAP` | `OPENING_CANDIDATE_UNRESOLVED` | 1 | nothing in the source settles it; saying so is not the same as settling it |

Forty-two of the forty-four objects the source carries are now physical
openings. Thirty are hosted. Twelve are openings whose host is a question — and
they are openings in every register, count and coverage check, which is the
point of §2.

## The other eleven, in one line each

1. **§3 no fabricated rectangle.** An opening is carried as what the source
   holds: insertion point, span, orientation, block identity, layer, swing,
   jamb marks, provenance. `footprint()` returns `None` until a host supplies
   the depth; the depth is then the host's own thickness and says so. A
   confirmed opening is itself the evidence that two collinear segments are one
   interrupted wall — and the host record names the two segments that face each
   other across the gap, so a run chopped into five pieces bridges the same gap
   as a run drawn in one.
2. **§4 ambiguity is preserved.** No nearest-wall rule. A host is decided by
   structural fit, parallel faces, jamb alignment, axis agreement, span fit and
   thickness match; proximity is weighted 0.05 and can never carry a decision on
   its own (`STRUCTURAL_FIT_MIN = 0.50`). Where two groups are within
   `DECISIVE_MARGIN = 0.15` the register publishes both, with their scores.
3. **§5 the eight opening cases** are tests, in
   `tests/test_qs_core_openings_source_objects.py`: a named door in a void;
   after translation and a quarter turn; one, two and many segment
   representations giving one answer; a junction door confirmed with an
   unresolved host; an unnamed gap that stays a candidate; a 2 mm mark that is
   noise; conservation of every named CAD object; and no admitted object lost
   because hosting failed.
4. **§6 root questions are not their consequences.** `RQ::<KIND>::<SUBJECT>`
   ids, one per unanswered fact, with a separate impact register for everything
   each fact holds up. **26 root questions, 565 impacts.** R5 reported 45
   questions of which 8 were the same objects counted twice.
5. **§7 evidence has a lifecycle.** A claim carries status, scope, effective
   revision, provenance, and — if retired — what superseded it and why.
   Eligibility is decided *before* authority, so a superseded owner input cannot
   beat an active standard inside the scope it was retired in, while still
   answering outside it.
6. **§8 window categories come from host rooms.** The project-wide
   `LIVING_ROOM` default is gone. Each window resolves its host room from the
   geometry, the room's label maps to a category, and where the room is
   ambiguous the register publishes the competing rooms and **no** category. On
   the ground floor: 7 windows, 4 categories resolved across 4 different room
   types, 3 left as questions.
7. **§9 shape is not material.** Two independent axes. Geometry identity comes
   from shapes, topology, thickness families and wall layers; material identity
   comes only from an annotation, a legend, a specification, an owner input or an
   active standard. Every material row carries
   `THICKNESS_FAMILY_PROVES_MATERIAL: false`.
8. **§10 the gate is twenty-one document-level checks**, each with a mutation
   test that must fail it, and the whole gate scores **0/21** on the committed
   R4 output.
9. **§11 row status is reported in three categories** — final, blocked,
   excluded — and `RELEASED_WALL_LINES` is renamed `NON_BLOCKED_WALL_LINES`,
   because an excluded line is not released work. The report now publishes the
   line-blocking counts beside the row counts *and* the arithmetic that
   reconciles them, so the 143-versus-111 contradiction cannot recur.
10. **§12 no PDF schedule extraction was attempted.** The CAD evidence was
    exhausted first: block identity, layer, jamb marks, swing, bracketing wall
    ends. That is what moved 35 objects.
11. **The R5 adapter no longer runs, by design.** It built each opening as a
    rectangle of a guessed depth, and that constructor is gone. A test asserts
    that it raises.

## What the numbers are now, and what is not on offer

| | R5 | R6 |
|---|---|---|
| physical openings | 7 | 42 |
| hosts resolved | 7 | 30 |
| openings existing with an open host | 0 (they were denied) | 12 |
| wall rows | 111 final, 19 blocked, 43 excluded | 0 final, 127 blocked, 23 excluded |
| published masonry subtotals | all null | all null |
| root questions | 45 (8 double-counted) | 26 |
| acceptance checks | 10 | 21, and 0/21 on R4 |

**No masonry or aluminium total is offered as a success criterion**, and the
drop from 111 final rows to 0 is not a regression to be argued away — it is the
§9 correction arriving. This drawing annotates no wall material anywhere. R5's
111 "final" rows were final because a 150 mm band was billed as blockwork for
being 150 mm thick. Once shape stops standing in for material, every band on
every floor is `MATERIAL_UNKNOWN`, and nothing is publishable as blockwork.

Four root questions unblock all of it: **what are the 0.05 m, 0.10 m, 0.15 m and
0.20 m walls built from?** One specification, legend or owner answer per
thickness family closes 127 rows. That is the deliverable of this round.

## What was not touched

The frozen blind takeoff (commit `3e847af`, digest `ae259eaba3203798`, file
SHA-256 `7e9a3eba…5493f`) was read and never written; its digest is recorded
before and after every run and the run asserts they are equal. Qortuba, the
pricing, the owner answers and the web app are untouched. The comparison with
the frozen artifact reports **differences**, and a figure this run declines to
state is not agreement and is not zero.
