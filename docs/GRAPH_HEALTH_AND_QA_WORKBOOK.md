# Local geometry, the first real graph run, and the QA workbook

Round report. Three parts: the five graph corrections from the review, the
first authoritative full-sheet graph run on AR-00, and the read-only QA
workbook built in parallel.

---

## Part 1 — the five corrections, and the principle behind them

Every one of the five was the same mistake in a different place: a proxy
standing in for a physical fact. The principle is now in the module docstring
of `engine/wall_noding.py`, where the next person to change this code will
read it:

> **DO NOT PROMOTE A PROXY INTO PHYSICAL TRUTH.**
>
> | observation | is not |
> |---|---|
> | same raster region | "not a doorway" |
> | 60–120 mm separation | "not masonry" |
> | same region on both sides | "validated doorway" |
> | three correlated observations | three independent proofs |
> | degree 4 | "a four-way crossing" |

### 1 · The incidence allowance is now local

It was `tol + widest_wall_on_the_sheet / 2`. One 400 mm external wall
therefore loosened node detection around every 100 mm partition in the
building. It is now derived per relationship, from the separations of the
edges actually being tested.

### 2 · Coordinate clustering and wall incidence are separate questions

They shared one allowance, which is why the fix for one broke the other.

| question | what it asks | allowance |
|---|---|---|
| coordinate clustering | are these two candidate points the same *place*? | a coordinate tolerance |
| wall incidence | does this *wall* reach that place? | local, from the walls being tested |

Separating them re-opens the gap that the shared allowance had papered over: a
stem's centreline stops at the through-wall's **face**, half a separation short
of its centreline, so the stem's endpoint and the computed crossing are two
coordinate clusters of one junction. That gap is now closed by
`consolidate()`, which asks the wall question — and asks it as a **subset**
test, not a proximity test:

- one cluster's incident walls are a subset of the other's, **and**
- the distance between them is within what those same walls' separation explains.

Two stems 100 mm apart on one through-wall each carry a wall the other does
not, so neither is a subset and they stay two junctions however close they are.
Proximity alone merges nothing.

### 3 · Over-spread clusters are subdivided before they are refused

Refusal was the first answer; it is now the last. Five wall ends 50 mm apart in
a line are five nodes — refusing the chain throws away five usable nodes to
avoid one wrong one. The tolerance is halved and the question asked again,
recursively, down to a floor of **5 mm**, below which "two separate nodes" has
stopped meaning anything a drawing could have intended.

Three states, and only the first may cut a wall:

| status | meaning |
|---|---|
| `VALID_CLUSTER` | one point; may split an edge |
| `AMBIGUOUS_CLUSTER` | a dense smear, held for review |
| `REJECTED_CLUSTER` | beyond argument; fails closed |

Each node records its `subdivision_depth`, so the audit can see how hard the
graph had to work to resolve it.

### 4 · CORNER_OVERLAP is not a physical cross

The closed rectangle's corners **are** degree-4 nodes: each pair of centrelines
runs past the other to the far face of the wall it meets. Mathematically four
arms; physically an L. Handing planar extraction four outgoing half-edges where
there are two makes false rooms.

The test is which sectors hold real **arms**, and the allowance is derived, not
chosen: a sector counts only when the edge extends past the node by more than
the **crossing wall's** own half separation — which is exactly the overhang a
corner produces. A genuine crossing has arms far longer than that.

| fixture | before | now |
|---|---|---|
| T-junction | `T_JUNCTION` ✓ | `T_JUNCTION` ✓ |
| true crossing | `CROSS_JUNCTION` | `TRUE_CROSS_JUNCTION` |
| L corner | `L_JUNCTION` ✓ | `L_JUNCTION` ✓ |
| closed rectangle | **4 × `CROSS_JUNCTION`** | **4 × `CORNER_OVERLAP`** |

A test now runs the same rectangle at 100, 200 and 400 mm wall thickness and
requires that no thickness ever turns a corner into a crossing.

### 5 · Micro-edges: no hard deletion threshold

The 50 mm constant is now a **review trigger**, and it is local — a fragment
shorter than its own wall is thick is not a wall run. The decision is
topological, not dimensional:

| decision | when |
|---|---|
| `KEEP_REAL_OR_UNPROVEN_FEATURE` | an end carries a third wall; collapsing would fuse two distinct junctions |
| `COLLAPSIBLE_WITHOUT_TOPOLOGY_CHANGE` | no third wall at either end; recommendation only |
| `MICRO_EDGE_UNRESOLVED` | the ends are not both resolved, so the consequence is unknown |

`micro_edge_policy()` recommends. Nothing in the module deletes an edge, and a
test asserts the total length is unchanged by calling it.

---

## Part 2 — the first authoritative full-sheet graph run

`tools/graph_diagnostic.py`, committed, reproducible:
`python3 -m tools.graph_diagnostic`. Vector segments taken in **millimetres**
from the PDF's own geometry — no raster quantisation between the drawing and
the graph. Output frozen at `runs/graph/AR-00_graph_diagnostic.json`.

### It failed on the first attempt, and the failure was the finding

> `NodingError: noding changed total wall length by 23210.1 mm
> (387057.1 → 363847.0)`

**23.2 m of 387 m.** Duplicate merging removes length legitimately — the wall
was in the graph twice — but the invariant must not absorb that silently in
either direction. The removal is now accounted for, itemised per merged edge,
and added back explicitly in the assertion:

```
post_split_total + duplicate_removed  ==  pre_split_total
```

The invariant stays strict, the removal stays visible, and a test proves that
length lost with no duplicate to explain it is **still** a failure. Widening
the tolerance to 1 % would have hidden exactly this.

### AR-00, second floor

| stage | result |
|---|---|
| axis-aligned segments | 35,835 |
| after collinear merge | 23,066 — of which **15,396 still under 50 mm** |
| skipped | 38,313 not axis-aligned, 2,399 curves, 105 quads, 48 degenerate |
| wall pairs | 296 |
| separation bands | 190 × 60–120, 61 × 120–180, 30 × 180–260, 15 × 260–400 (no band excluded) |
| noded graph | 342 nodes, 264 edges, 25 splits |
| clusters | 342 valid, 26 subdivided, 0 ambiguous, 0 rejected, 86 merged by incidence |
| micro-edges | 6 flagged → 4 keep, 2 collapsible, **0 deleted** |
| length | 387,057.1 in → 363,847.0 + 23,210.3 duplicate = **0.2 mm difference** |

### Post-split junctions

| kind | count |
|---|---|
| `TERMINUS` | **228** |
| `COMPLEX_JUNCTION` | 45 |
| `L_JUNCTION` | 34 |
| `CONTINUATION` | 22 |
| `T_JUNCTION` | 8 |
| `CORNER_OVERLAP` | 4 |
| `TRUE_CROSS_JUNCTION` | 1 |
| `CROSS_JUNCTION` | 0 |

### The finding that matters, and it is not good news

> **115 graph components. 228 of 342 nodes are termini.**

The graph is in 115 disconnected pieces, and two thirds of its nodes are wall
ends that meet nothing. A planar face needs a closed cycle; most of this graph
has no cycles at all.

**E31A cannot be built on this graph as it stands.** A half-edge/DCEL
representation over a disconnected graph is correct and produces no faces —
the DCEL is not the problem and building it first would only prove that. The
next problem is **connectivity**, and it is upstream of E31A: 15,396 sub-50 mm
runs survive the collinear merge, which says the merge is not recovering the
faces the architect drew. That, not the DCEL, is where the next round should
go.

I am flagging this rather than proceeding to E31A on my own judgement, because
the review's order was noding → dashed topology → E31A, and this changes what
E31A would be worth.

---

## Part 3 — the read-only QA workbook

Built in parallel, as instructed. Two modules and a tool:

| file | role |
|---|---|
| `engine/qa_workbook.py` | decides what every cell says. **No engine imports at all** |
| `engine/qa_writer.py` | decides what it looks like. Adds no values |
| `tools/export_qa_workbook.py` | assembles the bundle from the engines and hands it over |

The split is the control. The data layer is *given* data, so it cannot reach
back into geometry even by accident — and that is asserted by parsing its own
AST for `engine.*` imports, not just written in a docstring.

### The four rules, and how each is enforced

**1 · Do not recalculate.** Every quantity cell is copied from the bundle. The
flooring sheet has a ceramic length column and a height column and still leaves
`ceramic_wall_area_m2` as `NOT_ESTABLISHED` — a test asserts it does not
print 20.64 from 8.6 × 2.4.

**2 · Zero is a result, not a blank.** `NOT_ESTABLISHED` is a *string*, so no
reader can sum a column containing it or coerce it to 0.0. A proved zero stays
a number: `opening_count = 0` means none was proved on this drawing, and the
sheet says so in a note rather than implying the room has no doors.

**3 · No project total that looks complete.** Coverage is per use, with blocked
beside ready. There is no completeness percentage and a test forbids the
columns one would live in.

**4 · No materials, recipes or pricing.** Enforced by a string scan.

### The seven sheets

| sheet | rows on 23010 | what it is for |
|---|---|---|
| Room Register | 36 | every space, including the ones the engine could not measure |
| Room Count Summary | 12 | counts by room type, with **manual-expected columns always present** |
| Flooring and Ceramic QA | 36 | each figure beside the release status that governs it |
| Wall Quantities | 36 | gross only, stated as gross |
| Exceptions | 46 | 2 known gaps, 6 undecided scopes, 36 blocked spaces, 2 graph blockers |
| Random QA Sample | 20 | stratified by room type, **seeded per project** |
| Takeoff Coverage | 13 | per use, no total |

### What the coverage sheet actually says

| use | ready | blocked | commonest blocker |
|---|---|---|---|
| `GROSS_PERIMETER` | **17** | 19 | scope |
| every other use (12 of them) | **0** | 36 | scope, then trade_rule |

Seventeen of thirty-six spaces have a releasable gross perimeter. Nothing else
is releasable at all, and there are no net quantities anywhere.

### A bug this export found in itself

The first run came out with **no release statuses at all** — every column
`NOT_ESTABLISHED`. The exporter had asked for friendlier use names
(`FLOORING`, `CERAMIC_WALL`, `PERIMETER`, `MASONRY`) that are not release-matrix
uses, and the lookup skipped them silently. It now uses the engine's own names
and **raises** on an unknown one. A silently dropped status is worse than a
crash: it reads as "nothing is established" when the truth was "nobody asked".

Plus a "How to read this" sheet in front carrying the read-only warning, the
`NOT_ESTABLISHED` definition and the provenance.

**Manual qiyal is not a production dependency, and the column for it is still
always there.** `manual_expected_count` is an empty human column; while it is
empty the verdict is `NOT_COMPARED`, never `AGREES`. A workbook that printed
agreement against a blank column would have invented a confirmation.

**The sample is seeded** (`sha256(project_id:seed)`), so the same drawing draws
the same rooms every run and a disagreement cannot be made to disappear by
exporting again. Blocked spaces are eligible on purpose: checking only what the
engine is already confident about measures nothing.

The workbook itself is gitignored (`*.xlsx`). The repository holds the code
that makes it, not a snapshot of a client's drawing.

---

## Open, unchanged from last round

- `EXTERNAL` classification: 0 of 703 segments. The envelope test is not built.
- Washroom `WASHROOM_GEOMETRY_UNRESOLVED`; BED-04's 1600 × 3000 bathroom not
  recovered.
- Zero validated openings, so **zero net quantities** anywhere.
- Six wall heights still missing from sections; `CEILING` blocks all 36 spaces.
- Scope still undecided on `COR-02`, `COR-03`, `REC-01`, `REC-02`, `SRV-01`,
  `STA-01`.
- Signed trade rules still absent for `MASTER_BEDROOM` and `OPEN_PLAN_LIVING`.
- Still needed from you: DXF/DWG of AR-00, the door/window schedule, sections
  for the six heights.
