# E31A built, and what it found

The status split was the unlock. Building the face engine on locally healthy
subgraphs was the right call, and the first run gives a clear — and negative —
answer about the drawing.

---

## A · E31A ENGINE STATUS

| | |
|---|---|
| `E31A_ENGINE_DEVELOPMENT_STATUS` | **READY_FOR_DIAGNOSTIC_RUN** |
| `PROJECT_TOPOLOGY_RELEASE_STATUS` | **BLOCKED** |

Blocked by: failing gates G3 / G5 / G8, and 11 components that can only
produce hypothesis faces.

**Production gates are not weakened.** `Face.releasable` returns `False`
unconditionally — not by policy but by construction, and a test asserts it.

---

## B · LOCAL FACE ELIGIBILITY

| verdict | components |
|---|---|
| `FACE_ELIGIBLE` | **1** |
| `FACE_HYPOTHESIS_ONLY` | **11** |
| `FACE_BLOCKED` | **103** |

All 103 blocked components are trees — zero independent cycles. A tree bounds
no face however much wall it holds, so nothing is lost by skipping them.

### A bug this found in my own code

`cycle_capacity` sorts components by cycle count; `components` sorts by length.
I joined them **by list position**, so every component was scored against
another component's cycle count. This is the identity-by-list-order error I
wrote a test against in `revision_entities` two rounds ago, committed in a
different module. A component now carries its own `independent_cycles`.

---

## C · FIRST DIAGNOSTIC E31A RUN

| | |
|---|---|
| half-edges | 232 |
| face walks | 27 |
| **bounded faces** | **6** |
| unbounded faces | 8 |
| `UNBOUNDED_FACE_UNRESOLVED` | 13 |
| unclosed walks | 8 |
| faces with holes | 1 |
| micro-faces | 3 (2 `WALL_CAVITY`, 1 `UNRESOLVED`) — **0 deleted** |

| face | area | perimeter | holes |
|---|---|---|---|
| FACE-0001 | **981.073 m²** | 128.4 m | **3** |
| FACE-0003 | 1.590 m² | 4.9 m | 0 |
| FACE-0007 | 1.367 m² | 4.9 m | 0 |
| FACE-0005 | 0.155 m² | 6.7 m | `WALL_CAVITY` |

**FACE-0001 is the building outline**, not a room: the perimeter walls form one
cycle enclosing the whole floor plate, with three holes. The internal partitions
are in separate components and never join it.

### Orientation, not size

The convention is fixed by the `next` rule and verified on a two-room fixture
where the answer is unambiguous (the outer walk's area equals the sum of the
interiors): **interior = counterclockwise, exterior = clockwise.**

My first attempt used *"the minority orientation in this component"* and read a
984 m² outer walk as a room. **Counting is not a convention** — that sentence is
now in the docstring with a test.

---

## D · POSITIVE CONTROLS — 0 of 4 reproduced

| space | type | raster | vector face | result |
|---|---|---|---|---|
| BTH-05 | BATHROOM | 3.295 m² | — | **NOT_REPRODUCED** |
| BED-01 | BEDROOM | 24.642 m² | — | **NOT_REPRODUCED** |
| STR-01 | STORE | 4.090 m² | — | **NOT_REPRODUCED** |
| OPEN-01 | SALOON | 127.723 m² | — | **NOT_REPRODUCED** |

Every one matched only FACE-0001 — the 981 m² outline — because that is the
only face containing their centroids. A face many times a room's size *contains*
the room rather than *being* it, and the control now says so: reporting a
29,676% area difference as "DIFFERS" would dress a total failure as a near miss.

**This is the headline. The face engine is correct on fixtures — L-rooms, shafts
as holes, disconnected blocks, door-gaps left open — and the AR-00 wall graph
cannot yet produce a single room face.** That isolates the problem cleanly: it
is connectivity, not the walker.

---

## E · BTH-01 / BTH-02 / BTH-03 — exactly what is missing

All three, identically:

> **2 of 4 sides have a wall run. North and south have NO WALL PAIR within
> 2 m that overlaps the side at all.**

The east and west walls exist and paired. The end walls never became wall
pairs — the face lines may be in the drawing without having paired. That is a
pairing failure, not an opening, and it is one specific thing to fix.

Not repaired. The raster region said *where to look*, never *what to find*.

---

## F · WASHROOM — still unresolved

> north: the wall covers **333 mm of a 1730 mm** side
> south: the wall covers **333 mm of a 1730 mm** side

No candidate face was generated. The printed 1500 × 2400 was **not** given to
the search; `compare_to_printed` returned `NO_CANDIDATE_GENERATED` and left the
dimension unused.

**The dashed hypothesis is formally retired**, not pending — see §M.

## G · BED-04 — still unresolved

> **0 of 4 sides** have a wall run covering them.
> north covers 1798 mm of 6218 · south has no wall pair within 2 m ·
> east and west end at unresolved termini.

No child face was generated and the printed 1600 × 3000 stayed unused.

---

## H · VECTOR ↔ RASTER

| relationship | count |
|---|---|
| `MANY_TO_MANY` | 6 |
| `RASTER_ONLY` | 13 |
| `ONE_TO_ONE` | **0** |
| `VECTOR_SPLITS_RASTER` | 0 |

Thirteen regions the segmentation found have no vector face at all. No face
reproduces a region one-to-one.

## I · FALSE SPLITS — none

> "no stable raster space was split by a vector face"

True, and it costs nothing to say so: there were no splits of any kind. The
control is in place for when there are.

---

## J · BUILDING ENVELOPE

| | edges |
|---|---|
| `EXTERNAL` | **8** |
| `INTERNAL` | 1 |
| `UNRESOLVED` | 255 |
| validated (2+ families) | 9 |
| resting on ONE family only | 148 |
| no evidence at all | 81 |

The first non-zero `EXTERNAL` in this project. It is small because the rule is
strict: **two independent evidence families**, and raster free space never
classifies alone — a terrace, a light well and an unclosed room all reach the
sheet border, while a courtyard reaches nothing and is outside.

148 edges rest on a single family. Those are hypotheses and are reported as
`UNRESOLVED`.

---

## K · CONNECTIVITY, PRIORITISED

Each component now records `affected_space_ids`, so effort can go where it
unlocks a room rather than to a 20 mm annotation fragment. The ranked work:

1. **BTH-01/02/03 end walls** — 3 in-scope rooms, one specific pairing failure
2. **BED-04's four sides** — 1 in-scope room, blocks a known defect
3. **The 103 tree components** — no cycles; mostly annotation

---

## L · QA WORKBOOK — 12 sheets

New **Topology QA** sheet: face id, component, status, area, perimeter, raster
regions, relationship, overlap %, dependent probable edges, micro-class,
candidate match, holes, blocker, notes. Faces appear **there and nowhere else** —
they touch no quantity, coverage count or release status.

| § | fix |
|---|---|
| 18 | `PROJECT_TRADE_RULE` ≠ `ROOM_TEMPLATE`. The E27 ceramic and plaster rules are no longer filed as templates |
| 19 | `SYSTEM_TOTAL_COUNT` gone. Every count names its basis: `observed_label_count`, `validated_physical_count`, `validated_in_scope_count`, `functional_zone_count` — and each manual column compares against the **same** basis |
| 20 | One `engine_status` became three: `measurement_role`, `geometry_validation_status`, `quantity_release_status`. Floor area now reads `NOT_A_RELEASED_BOQ_USE` — a fact about the use, not a defect in the measurement |
| 21 | `difference` / `difference_pct` / `checker_verdict` columns for the owner, plus `engine_source`. QA-only arithmetic on QA-only inputs |

---

## M · STALE-FINDING AUDIT

| class | rows |
|---|---|
| `CURRENT_DIAGNOSTIC` | 16 |
| `GOLDEN_KNOWN_DEFECT` | 1 |
| `LEGACY_HYPOTHESIS` | **1** |

**Both stale items you found are fixed.**

*E31A readiness* said "implement the G8 measurement" after G8 was measured. It
now reads, generated from the live gate record:

> "Clear the failing gates: G3-TERMINI, G5-EXPLAINED-DISCONNECTS,
> G8-CYCLES-IN-REAL-ROOMS. **Every gate is now measurable.**"

*The washroom dashed threshold* is retained as history, labelled
`LEGACY_HYPOTHESIS`, sorted **last** (priority 18 of 18), and carries its
`superseded_because`:

> "no dashed stroke exists anywhere on this sheet (every stroke path is solid)
> and the repeated short marks beside WSH-01 are the shaft symbol's hatch fill,
> 8 mm marks with 8 mm gaps."

The current supported fact sits at the top instead: *the physical washroom
geometry is unresolved; no validated boundary currently separates it.*

---

## Generalization (§24)

Every planar fixture is synthetic, and several are shapes AR-00 does not
contain: L-shaped room, room with a shaft as a hole, two disconnected blocks,
a door-sized gap that must stay open, a tree that bounds nothing. A test that
only ran on this project's drawing would prove the engine reproduces that
drawing.

---

## Not started

Pricing. Material recipes. Final E34. Client BOQ release. No diagnostic face has
replaced any geometry source.
