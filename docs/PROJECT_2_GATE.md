# Project 2 — the gate, and what runs unchanged when it arrives

> **STATUS: the gate has been run, and it neither passed nor failed — it did
> not execute.** Project 2 arrived on 2026-09-15 as a 400 dpi scan of a
> stamped municipality submission (VILLA P7757), with zero vector content on
> every page. The pipeline stopped at stage 1. The frozen result and the
> full audit are in **`docs/PROJECT_2_RESULT.md`**; the generalisation
> questions below still have no second data point.

AR-00 development is **stopped**. No further AR-00-specific improvement is
permitted; the next automatic geometry capability waits for a second
project.

## What is frozen

```
ENCLOSURE ALGORITHM     SUPPORTED_LINE_ARRANGEMENT_FLOOD_FILL_V1
FREEZE HASH             01ff128e7ffdab820805dce1
synthetic fixtures      14 enclosure + 11 portal-topology, all passing
```

Every threshold states its own justification in `frozen_parameters()`, and
the self-test re-asserts the freeze on every pipeline run. Nothing in the
enclosure, the three-topology model or the evidence tiers was chosen by
looking at AR-00.

## The procedure when Project 2 arrives

1. **Freeze the source.** `tools/freeze_new_source.py` records the file, its
   hash and its representation before anything reads it.
2. **Run the current pipeline unchanged.** No parameter is touched, no
   AR-00-specific rule is added.
3. **Freeze all automatic outputs** — the topology hash, the three-topology
   hash, the enclosure results — before any human reference is opened.
4. Report the **source-representation audit**: does it have PDF text
   objects, what pen conventions, what wall representation, is text vector
   outlines or real text.
5. Report **topology** results.
6. Report **measurement** results.
7. **Only then** open any human benchmark or review.

## The metrics, with definitions unchanged

```
TOPOLOGY_RECALL_ALL / _IN_SCOPE
ROOM_CANDIDATE_PRECISION
UNCLASSIFIED_REGIONS
COMPLETE_MEASUREMENT_RECALL_ALL / _IN_SCOPE
RELEASE_ELIGIBLE_RECALL_ALL / _IN_SCOPE
MEAN / MEDIAN VECTOR BOUNDARY SUPPORT
DOCUMENT DIMENSION AGREEMENT
EXCEPTION RATE
```

All are computed by `engine/recall_matrix.py` and the enclosure summary
from one row set, with denominators printed beside the numbers. They are
not redefined for a second project — that is the point of fixing them now.

## Project 23010 baseline, for the comparison

```
TOPOLOGY_RECALL_ALL              27 of 36    75.0%
TOPOLOGY_RECALL_IN_SCOPE         13 of 17    76.5%
ROOM_CANDIDATE_PRECISION         27 of 27   100.0%
UNCLASSIFIED_REGIONS             39 of 66
COMPLETE_MEASUREMENT_ALL          3 of 36     8.3%
COMPLETE_MEASUREMENT_IN_SCOPE     2 of 17    11.8%
RELEASE_ELIGIBLE_ALL/_IN_SCOPE    0 / 0       0.0%
VECTOR BOUNDARY SUPPORT          mean 20.0%, median 0.0%
DOCUMENT DIMENSION AGREEMENT     28 AGREE, 0 DISAGREE, 16 AMBIGUOUS,
                                 1 NOT_PRESENT
ROOM PARTITION RELATION          1 TWO_DISTINCT_PHYSICAL_SPACES,
  (labelled spaces)              26 UNRESOLVED, 9 NO_REGION
ROOM PARTITION, pair level       27 established as two spaces,
  (135 region adjacencies)      108 unresolved relation
```

The median vector boundary support of **0.0%** is the honest shape of this
sheet: most regions are not rooms, and most rooms have at least one side
the drawing does not carry.

## What Project 2 should be

A different architect or consultant, a different drawing style, different
wall conventions. The generalisation questions it answers, which AR-00
cannot:

- Does the glyph-ink test (**a glyph is a small black filled path**) hold
  for an office that plots text differently, or does that sheet have real
  PDF text objects and skip the problem entirely?
- Does the wall-pen convention differ, and does anything depend on it?
  (Nothing production does: pen is diagnostic only.)
- Does a second sheet carry explicit open-plan evidence — a schedule row or
  a note declaring one space? AR-00 carries none, which is why every
  open-plan candidate on it is UNRESOLVED rather than one space.
- Do door graphics close pixels there? The partition must not care — that
  is invariant 41, and the two synthetic ink cases assert it.
- Is the wall solid porous in the same way, or is the enclosure's
  `A_WHOLE_SIDE_HAS_NO_DRAWN_LINE` an AR-00 property rather than a PDF
  property?

That last one decides the product. If a second sheet's rooms enclose where
this one's do not, the blocker is this drawing. If they do not enclose
either, the blocker is the medium, and the answer is automatic topology plus
human confirmation of the named unsupported sides.
