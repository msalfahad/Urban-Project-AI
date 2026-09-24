# The generic takeoff core: root causes, the entity model, and how it is held

**Package** — `engine/qs_core` · **Adapter** — `research/qs_wall_treatment_01/pa09/alrashed/regression_r2.py`
**Tests** — `tests/test_qs_core_*.py` (74) and `tests/test_pa09_alrashed_regression_r2.py` (16)

The brief was not to correct one villa's BOQ. It was to make the engine solve the underlying problems by itself,
with that villa used only as a regression fixture. So the algorithms live in a package that has never heard of a
project, the project lives in an adapter, and an executable audit proves the boundary holds.

---

## 1. Root causes

### 1.1 Identity was a position in a list

`COMPONENT_REF` was `f"{floor[:2]}-{k:03d}"`, where `k` was the index of the component in the order a grid scan
happened to produce. Insert one component — or move a wall five millimetres so the grid gains a line — and every
reference after it shifts. An owner decision recorded against a reference then lands on a different room in the
next revision, silently.

The deeper cause: **identity was derived from the extraction process rather than from the thing extracted.**

### 1.2 Openings were pooled and shared out

`blockwork_audit` summed a floor's openings and distributed them across wall-thickness bands in proportion to
wall length (`share = ln / confirmed_len`). The floor total survived exactly, so no total-based check could see
it; the split between two separately priced lines did not.

The deeper cause: **the engine measured walls without ever asking which wall each hole was in.** A pro-rata rule
is what you write when that question has no answer in the data model.

### 1.3 A room was whatever fragment held its label

Components came out of a flood fill; a label was attached to the component containing its text; every other
component was "unnamed". A room cut in two by a grid line, a virtual closure or a column therefore became one
named room plus one unnamed space, and the unnamed one drifted into a pending pile.

The deeper cause: **there was no semantic layer.** Geometry components were being used as rooms, so a room could
never be more than one of them.

### 1.4 The checks could not fail

Fifteen QA rows recorded a PASS the generator had decided. A check that cannot disprove the interpretation it
describes is documentation, not verification.

---

## 2. The entity model

Three kinds of object, never conflated:

| Entity | What it is | Identity | Where |
|---|---|---|---|
| **Geometry component** | A connected piece of the drawing: floor cells, a wall band, a column, a sliver | `COMPONENT_REF` from the extractor, plus a geometry `UID` and a `PERSISTENT_ID` | `entities.GeometryComponent` |
| **Semantic space** | What a person would call a room: one or more floor components that continue into one another | `ROOM_ID`, its own `PERSISTENT_ID` | `entities.SemanticSpace` |
| **Measurement object** | What a trade is measured on: a floor finish, a wall line, an opening | `MEASUREMENT_OBJECT_ID` | `entities.MeasurementObject` |

Every one of them carries `SOURCE_REVISION`, `EVIDENCE` (a rule plus its detail), `CONFIDENCE`
(`PROVEN` / `STRONG` / `WEAK` / `NONE`) and `STATUS`. A measurement object also carries the six DS-01 fields —
quantity, unit, waste, procurement quantity, rate, amount — of which this task fills exactly one.

**A geometry component is not a room.** It becomes part of one when the seam evidence says so, and a wall band,
a column or a sliver never does.

---

## 3. Problem A — identity that survives a redraw

Three separate ideas, deliberately not merged:

- **Fingerprint** — a hash of the geometry itself (kind, floor, thickness, axis, every rectangle to 0.1 mm).
  Identical input gives identical identity on any machine, which is what makes a rerun diffable.
- **UID** — `uuid5(namespace, revision|fingerprint|ordinal)`: the immutable handle a store keeps.
- **Persistent ID** — what an owner decision attaches to. It is *carried forward* by matching geometry between
  revisions, never by position.

Matching scores `0.60·IoU + 0.20·centroid proximity + 0.15·dimension similarity + 0.05·label equality`, and then
— crucially — **splits and merges are detected before one-to-one matching**, because half of a room that split
still overlaps its parent enough to look like the parent moved. Descent requires a substantial share of *both*
areas and a like kind, so a column standing inside a room is not a piece the room split into.

Lineage states: `UNCHANGED`, `MODIFIED`, `NEW`, `REMOVED`, `SPLIT`, `MERGED`, `REVIEW_REQUIRED`. Only the first
two carry decisions forward; a split, a merge or an ambiguous match sets `DECISIONS_CARRY_FORWARD: false` and
says why, because *which* of the parents' decisions survives is not a geometric question.

---

## 4. Problem B — an opening belongs to one wall

`assign_opening_host(opening, wall_bands, tolerance)` scores each candidate on five pieces of evidence —
containment, axis agreement, thickness agreement, span overlap, proximity — and assigns only when the leader
beats its rival by a stated margin **and** actually contains the opening along its own axis. Otherwise the
opening is `HOST_WALL_UNRESOLVED`, with its candidates and the reason recorded, and every wall line on that floor
is blocked from final pricing. **No branch divides a deduction.**

Two supporting pieces turned out to be necessary on real geometry:

- **Wall lines.** An extractor that stops a wall at each jamb hands over two segments; they are not two walls and
  the door is in neither of them. `build_wall_lines` groups collinear segments of equal thickness whose gaps are
  no wider than an opening could explain — a span the *caller* supplies, because it is a fact about the building.
- **The gross basis.** Some extractors draw a wall through its own doorway; others stop at the jamb. Get this
  wrong and every door is deducted twice. So `wall_band_quantities` takes `geometry_includes_openings` as an
  argument with no default, and `pipeline.run` raises if a caller asks for wall quantities without stating it.

---

## 5. Problem C — rooms assembled from evidence

`assemble_semantic_spaces(components, barriers, openings, labels, tolerance, sliver_min_dimension)` decides
membership at the **seam** between two pieces of floor. For each seam it measures what is physically there:

| Share of the seam | Relation | Consequence |
|---|---|---|
| Wall material > ½ | `SEPARATED_BY_WALL_MATERIAL` | two rooms |
| An opening > ½ | `CONNECTED_BY_AN_OPENING` | two rooms, with a door between them |
| A drawn gap with nothing in it > ½ | `CANDIDATE_OPENING_REVIEW_REQUIRED` | **not merged, and surfaced as a question** |
| Nothing at all > ½ | `CONTINUOUS_FLOOR` | one room: the label applies to all of it |
| none of the above | `REVIEW_REQUIRED` | not merged, surfaced |

The third row is what a virtual closure is: the source drew a break in a wall and did not say what fills it. A
doorway and an archway look identical there, so the engine asks instead of choosing.

Labels are then read over the assembled space, not over a fragment. One label names the whole space; none leaves
it `UNNAMED_ON_DRAWING`; two make it `CONFLICTING_LABELS` and `UNRESOLVED`, because two names in one continuous
area mean either a missing boundary or a misplaced label — and picking one would be inventing evidence.

Every component ends in exactly one of `ASSIGNED_TO_SPACE`, `NON_ROOM_GEOMETRY`, `EXTERNAL_OPEN_AREA`,
`UNRESOLVED`. There is no fifth outcome and no component may hold two.

---

## 6. The invariants

Fourteen, all evaluated from evidence, each returning its inputs, tolerance, result and method:

| | Invariant |
|---|---|
| INV-01 | every opening has at most one host |
| INV-02 | deductions reconcile with the canonical register |
| INV-03 | an unresolved opening is never silently allocated |
| INV-04 | no wall material becomes floor finish |
| INV-05 | every component ends in exactly one state |
| INV-06 | a space's area is the sum of its components |
| INV-07 | floor closure is preserved |
| INV-08 | revision order does not change identity |
| INV-09 | no comparison total or project name in production code |
| INV-10 | quantity, unit and pricing stay separate, and pricing stays empty |
| INV-11 | continuous floor is one space |
| INV-12 | an ambiguous host is never quietly assigned |
| INV-13 | every check is evidence-based |
| INV-14 | **every deduction sits on the band that hosts it** |

INV-14 is the one that catches pro-rata allocation: INV-02 passes on pro-rata output, because the total is right.
That is the whole point — a check on totals cannot see a misallocation, and the mutation test proves it.

---

## 7. How it is held: mutation tests

Six defects are re-implemented in `tests/test_qs_core_mutation.py` and run through the real invariants:

| Defect put back | What must object |
|---|---|
| Pro-rata opening allocation | INV-14 (and INV-02 must *pass*, proving totals cannot catch it) |
| Pro-rata allocation of an unresolved opening | INV-03 |
| Scan-order component ids | INV-08 |
| A label confined to its own fragment | INV-11 |
| A check citing a known total | INV-13 |
| Picking the leading candidate despite a tie | INV-12 |
| Wall material counted as floor | INV-04 |
| A component in no state at all | INV-05 |

---

## 8. The anti-calibration boundary

`tests/test_qs_core_audit.py` reads the production sources and fails on: any project name, any reference from a
real drawing, any previously reported total, any branch on which project is running, any import from a project
package, any threshold declared without a stated reason, and any source parameter that is not an argument.

That last one caught a real slip while this was being written: `pipeline.run` had `max_opening_span=3.0` as a
default. A default is a constant smuggled into the engine; it is now a required argument.

---

## 9. What R5 added, and why

Four stages now run before anything is measured, because each of them answers a
question the measuring stage was silently assuming.

1. **Admission** (`admission.py`). The three populations a real source offers -
   extracted geometry, the drawing's own opening register, the schedule - are
   normalised to one physical population. Every candidate leaves with one of
   five classifications and the provenance behind it. A candidate is admitted
   because something *names* it an opening, never because it is the right size.
2. **Continuity** (`openings.build_wall_lines`). A gap is closed only where the
   source says something spans it. The maximum opening span is a veto, not a
   proof.
3. **Basis** (`openings.evaluate_opening_basis`). Whether a wall's drawn
   material runs through its openings is measured per line, against the
   openings that lie in it, instead of asserted once for a whole revision.
4. **Identity** (`masonry.py`). What each band *is* - masonry, structure, a
   junction, a duplicate, or unknown - is settled from the drawing before
   anything measures it. The thickness families come from the whole source; the
   engine holds no list of acceptable thicknesses.

Two more stages changed what comes out. `dependency.py` follows opening ->
candidate hosts -> wall lines -> subtotal -> bill line and blocks only what an
answer could move. `quantities.py` makes a blocked row carry no summable value
and a subtotal with one blocked contributor null.

And two things now grade the result from outside it: `acceptance.py`, which
reads the published document and nothing else, and `transforms.py`, which asks
whether the same building described differently measures the same - on the real
drawing, not only on fixtures.

---

## 9. Running it

```bash
export PYTHONPATH=$PWD
python -m pytest tests/test_qs_core_*.py -o addopts= -v

# the project regression: reads the frozen takeoff, never writes it
python -m research.qs_wall_treatment_01.pa09.alrashed.regression_r5
python -m pytest tests/test_pa09_alrashed_regression_r5.py -o addopts= -v

# the deliverable package, verified after it is written
python docs/build_r5_validation_package.py
```

Artifacts land in `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/pa09_alrashed/`:
`ALRASHED_GENERIC_ENGINE_VALIDATION.json` and the registers beside it - opening
admission, per-wall opening basis, masonry identity, dependency and blocking,
space-assembly validation, final versus blocked quantities, opening to host,
component to room membership, entity lineage, and the anti-calibration audit.
