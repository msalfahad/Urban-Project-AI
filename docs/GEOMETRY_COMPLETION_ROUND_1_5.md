# Targeted refactor round 1.5 — geometry completion and source-of-truth audit

Round 1 replaced the geometry spine and proved it worked on one control.
Round 1.5 asks the harder question: **what does this engine actually know,
and where does it only appear to know something?**

Almost every finding below came from making an instrument capable of
failing. Three of them then failed immediately, on the real drawing, in ways
their previous output had concealed.

---

## 1 · What a coverage number is allowed to mean

`source_coverage_pct: 100.0` was true and useless. Its denominator was the
accepted wall bands, so it said "every band we accepted became a polygon" —
and on a drawing where most of the wall length never reached the accepted
band set, a reader would take it for "every wall is captured".

It is now `accepted_band_polygonization_coverage_pct`, with
`coverage_denominator: ACCEPTED_WALL_BANDS_ONLY` beside it, and the metric a
reader actually wants is named and left open:

```
drawing_wall_representation_coverage: NOT_ESTABLISHED
```

It could not be established because its denominator was unknown, which is
what §2 fixes.

## 2 · 851 m of stroke is not 851 m of wall

The unpaired wall-pen population was reported as `SINGLE_LINE_WALL`. The pen
weight says a mark was drawn with the wall pen; an architect uses one pen for
more than one thing. So the population is named for what is known about it —
`UNPAIRED_WALL_STYLE_STROKE` — and classified on evidence, never on pen
weight alone (`engine/unpaired_strokes.py`):

| class | length | strokes |
|---|---|---|
| `CONFIRMED_SINGLE_LINE_WALL` | 434.8 m | 75 |
| `FRAGMENTED_MATE` | 289.0 m | 230 |
| `FIXTURE_OR_SYMBOL` | 88.7 m | 117 |
| `DUPLICATE` | 22.6 m | 20 |
| `UNRESOLVED` | 15.8 m | 20 |

723.8 m is wall-like; 127.1 m was never a wall. With that denominator,
drawing-level coverage becomes **45.9%**, and it carries what it still does
not claim: a wall drawn in a representation this engine cannot read at all
appears in neither term.

The difference between `CONFIRMED_SINGLE_LINE_WALL` and `FRAGMENTED_MATE`
matters more than either number. The first needs a new capability — the band
engine cannot express a single-line wall. The second needs a longer reach on
a capability that already exists. Reporting 851 m as one thing hid both.

## 3 · The free-space invariants, on the real result

All eight hold, with **absolute** tolerances (`engine/free_space_invariants.py`):

```
envelope 1000.0960 m2 = obstacles 117.3462 m2 + free space 882.7498 m2
residual  -0.0 mm2   against a tolerance of 10,000 mm2 (one square centimetre)
```

The tolerance is absolute and deliberately far tighter than any percentage,
because the failure being hunted is a **small absolute loss on a large
floor**: 0.02 m² lost from a 1000 m² envelope is 0.002%, which any percentage
tolerance waves through and which is still two hundred square centimetres of
floor that is neither wall nor room.

Each invariant has a positive control in the tests — a construction that
breaks it, asserted to be caught. An invariant nobody has seen fail is a
comment.

## 4 · An internal doorway must not move the floor

Rebuilt three ways:

| barriers applied | envelope |
|---|---|
| all accepted | 1000.0960 m² |
| external only | 1000.0960 m² |
| none | 1000.0960 m² |

`INTERNAL_BARRIERS_DO_NOT_MOVE_THE_FOOTPRINT`, delta **0.0 mm²**.

The first version of this test was vacuous and said `PASS`. It classified a
barrier as external by asking whether its host band belonged to the wall
solid's ring *component* — and that component carries 197 of the bands,
because every internal wall touching the external ring is part of the same
connected solid. All 19 barriers came out "external" and there was nothing
left to test. Classification is now by position relative to the envelope's
own boundary, all 19 are internal, and the pass is real.

## 5 · Accepted is not releasable

A barrier is accepted geometrically long before the opening it plugs is
proven to exist. `DIAGNOSTIC_PARTITION_BARRIER` and
`RELEASABLE_PARTITION_BARRIER` split that:

- 19 accepted barriers → **2 releasable, 17 diagnostic**
- 17 blocked on `PORTAL_EXISTENCE_PROBABLE`

BED-01's exact portals:

| portal | host | width | existence | geometry | release |
|---|---|---|---|---|---|
| `PT-BED-01-west-27124` | WB-00136 | 1200.2 mm | PROBABLE | PROBABLE | DIAGNOSTIC |
| `PT-GH27048-line-27348` | WB-00060 | 1000.2 mm | PROBABLE | PROBABLE | DIAGNOSTIC |

Both carry four evidence items — `SPAN_IN_THE_DOOR_RANGE`,
`PAIRED_BANDS_TERMINATE_FACING_EACH_OTHER`, `END_CAPS_AT_BOTH_JAMBS`,
`GAP_CLOSES_AN_OTHERWISE_COMPLETE_BOUNDARY`. All four look at the same gap in
the same way. **Four geometric observations of one gap are one family, not
four proofs.**

A component that no barrier bounds gets its own class,
`NOT_CONSTRAINED_BY_A_BARRIER`, because calling it releasable would turn
silence into a clearance — and 17 of AR-00's components are merged blobs no
barrier touches.

## 6 · Why BED-01 differs from its reference

Not a percentage. A decomposition (`engine/disagreement_map.py`), with every
piece given a cause A–G and a side to blame:

```
vector     21.0338 m2        IoU 0.802        delta -11.56%
reference  23.7838 m2
```

| cause | area | blame |
|---|---|---|
| F — the segmentation grew out through the doorway | 3.8370 m² | THE REFERENCE |
| A — its boundary stopped 83 mm short of the finish face | 0.5671 m² | THE REFERENCE |
| D — it carved around fixtures (60 holes) | 0.4859 m² | THE REFERENCE |
| | **4.8900 m²** | **100% the reference** |

Nothing unexplained, and **nothing attributed to the engine**. BED-01's
geometry is sound; the reference is a segmentation output whose boundary sits
wherever the pixels fell.

BED-01 was not tuned. Nothing here corrects the vector geometry, and the
comparison ran only after the polygon's hash was taken.

The same instrument on the other two controls, unprompted:

| control | IoU | blamed on the engine | cause |
|---|---|---|---|
| BED-01 | 0.802 | 0 m² | — |
| BTH-01 | 0.115 | 24.5871 m² | E — leaked past a missing separator |
| STR-01 | 0.005 | 733.9206 m² | E — it *is* the 738 m² blob |

BTH-01's 24.6 m² and the leak map's 50 mm hairline gap between BTH-01 and
BED-NW are the same defect found by two instruments that share no code.

Two raster-derived reference areas for BED-01 differ by 0.8578 m² purely on
whether the carved holes count as floor (23.7838 vs 24.6417 m²). Both are
reported. A fixture standing on a floor does not remove floor area.

## 7 · Which references may be opened at all

`engine/reference_mapping.py` resolves a reference row to a space only where
the mapping **and** the basis are unambiguous. On this project:

- **Raster segmentation region** — opened after the freeze, decomposed above.
- **Space map label rows** — all 36 map cleanly to a space and carry **no
  area**, so they stop at `NO_VALUE`: the mapping is recorded, the comparison
  is not.
- **Topology overlay** — human validation states, not measurements.
- **Sealed site benchmark** — **not opened**, refused by name in code so no
  future caller can reach it by passing a path.

A row labelled "Bedroom" on a floor with six bedrooms returns
`NAME_MATCHES_MORE_THAN_ONE_SPACE` and is never compared, never averaged and
never counted as agreement. A room **type** is never a resolution even when
it happens to match one room, because otherwise the rule would depend on how
many rooms of that type the floor happens to have.

## 8 / 9 · Where the space actually leaked

See **invariant 22**. In summary: the first leak map called 27 of 30
separations `NO_VECTOR_SEPARATOR` on a drawing whose walls are largely drawn,
through a midpoint probe, an axis read in the wrong frame, and a tolerance
around a biased point. Underneath those was a structural limit no tuning
would have reached — raster adjacency finds only where two rooms *face* each
other, and it located 8 apertures inside a component holding 22 labels, where
a spanning tree needs 21.

The merged polygon is now asked directly. Eroding it finds every passage by
construction and measures its width; where it was cut is *proven* by removing
the channel and checking the two sides fall apart; how far it extends is
refused where the erosion has consumed most of the floor.

What that found, which is not what the broken instrument claimed:

| passage | width | between |
|---|---|---|
| hairline junction gap | 50 mm | BTH-03 ↔ the blob |
| hairline junction gap | 50 mm | BTH-01 ↔ BED-NW |
| hairline junction gap | 100 mm | MBTH-02 |
| hairline junction gap | 150 mm | BTH-04 |
| hairline junction gap | 300 mm | BED-04 |

In all five, accepted wall bands run along the **whole** passage and free
space crossed anyway. Nothing is missing from the drawing: two wall polygons
fail to meet. No better reading of the source will ever close them, and the
repair is in how the wall solid is assembled.

A `partition_complete` check states what each component's label count
requires against what was reported. For the 22-label component it still reads
`complete: false`. The map says so itself.

## 10 · What a polygon spans against what was drawn

`engine/interval_fidelity.py`, over 615.098 m of wall polygon span:

| | length | share |
|---|---|---|
| both faces drawn | 446.383 m | 72.6% |
| one face, cap or junction to support it | 111.901 m | 18.2% |
| **one face, `UNRESOLVED_EXTENSION`** | **55.947 m** | **9.1%** |
| neither face drawn | **0.000 m** | 0% |

The invariant as stated holds: **no polygon silently bridges an undrawn
gap.** But the audit surfaced something larger. 55.9 m across 21 stretches is
carried by polygons whose own band records say
`UNRESOLVED_EXTENSION` — *"this band's extent beyond the paired interval is
NOT established material"*. The wall solid asserts masonry there that the
source does not establish. Every geometric invariant holds while it happens,
because none of them knows what the source drew.

## 11 · A measured snap tolerance

See **invariant 23**. The 0.05 mm grid was justified by ratio to a wall, so
it could be neither confirmed nor refuted. Measured on AR-00's 972
wall-polygon vertices, representation noise ends at 0.0087 mm with two empty
decades above it; the recommendation is **0.01 mm** and the 0.05 mm in use is
`SAFE_AND_WITHIN_AN_ORDER_OF_THE_MEASUREMENT`.

This settled §8's finding: the five hairline gaps are **5,000–30,000×** the
grid. They are not numerical artefacts, and raising the tolerance to reach
them would close every genuine 50 mm gap in the drawing.

## 12–15 · One authority, six stages, four statuses

See **invariant 24**. The workbook now names the free-space path as the
geometry authority on every sheet that carries geometry; the **Free Space
QA** sheet carries the authority's own rows and sits before Topology QA; the
manifest records six stages instead of two —

```
wall_polygon_run → wall_solid_run → portal_partition_run
                 → building_envelope_run → free_space_run
                 → space_resolution_run
```

— and the status line asks four questions instead of one:
`GEOMETRY_MECHANISM_PROVEN = PASS`, `PROJECT_SPACE_RECALL = PARTIAL`,
`TAKEOFF_COVERAGE_STATUS = VALIDATED_PARTIAL`,
`FINAL_BOQ_STATUS = BLOCKED`.

The obsolete E31A blocker is gone. It held the project on a diagnostic's gate
while leaving the condition that matters — whether the free-space invariants
hold — unstated.

## 16 · No AI semantics

Nothing in this round extracts a printed dimension, reads a room label or
runs a model. `engine/document_observations.py` still only *models* printed
dimensions with their evidence role fixed, and refuses use.

## 17 · Project 2

**No second drawing exists in the repository.** `tools/freeze_new_source.py`
is the intake path, ready: it hashes and freezes a source, runs the
representation audit, and refuses to measure anything. It also refuses, by
name, any document that carries answers — a benchmark, a qiyal sheet, a
previous BOQ, a contractor quantity, a quotation, a cost or rate export.

The artefact is blocked on the drawing being supplied. Until it is, nothing
in this repository says whether the engine reads **drawings** or reads
**this drawing** — every tolerance, pen weight and representation assumption
was chosen against one sheet.

And when it arrives: project 23010 must **not** be tuned using what the audit
finds. The second project is the only test of whether those choices
generalise, and tuning against it destroys the test.

---

## What this round did not establish

- **That this floor is measured.** Nine of seventeen in-scope spaces came
  out as their own polygon. The largest component holds **22** labelled
  rooms and 738.011 m2.
- **That the wall solid is right.** 55.9 m of it rests on extensions its own
  records call unestablished.
- **That the engine generalises.** One drawing.
- **That any quantity may be released.** `FINAL_BOQ_STATUS` is `BLOCKED` and
  names its blockers.
