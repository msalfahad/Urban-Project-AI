# Connectivity diagnosis, and a quantity that can be traced

Round report. Part A explains the wall graph before repairing it. Part B makes
every quantity traceable and revision-aware. Part C rebuilds the QA workbook.

---

# PART A — WHY THE GRAPH IS IN PIECES

The instruction was: do not assume 115 components is one bug, and do not touch
a tolerance until the dominant cause is known. Here is what the drawing
actually contains.

## A.1 The source population — measured, not assumed

`engine/vector_source.py` reads every mark on the page, classifies none of
them, and discards nothing.

| | |
|---|---|
| paths | 19,257 |
| line items | 73,716 (+ 120 rects, 2,399 curves, 105 quads) |
| **FILL paths** (glyph outlines, hatch) | 9,059 → **45,378 line items** |
| **STROKE paths** (drawn linework) | 10,198 → 28,338 line items |
| page rotation | **270°** — the coordinates are in the unrotated frame |

Stroke pen weights, axis-aligned items only:

| pen | items | total | mean | under 50 mm |
|---|---|---|---|---|
| **1.14 pt** | **462** | **739.1 m** | **1,600 mm** | **4** |
| 0.36 pt | 12,748 | 655.4 m | 51 mm | **11,077** |
| 0.30 pt | 1,701 | 568.0 m | 334 mm | 1,225 |
| 0.24 pt | 185 | 185.6 m | 1,003 mm | 23 |
| 0.12 pt | 786 | 121.3 m | 154 mm | 268 |

The 1.14 pt population is 739.1 m against the raster trace's 734.54 m.

**Discipline note.** A 1.14 pt pen is *not* a wall. It is a source property of
the mark, kept for exactly the reason `source_object_id` is kept: so a later
stage can use it as evidence. The module classifies nothing, excludes no band,
and a test parses its own AST to prove it contains no `is_wall` anything.

## A.2 The 15,396 sub-50 mm runs — answered

> Are these drawing noise, or fragments of larger paths we destroyed during
> extraction?

**Neither hypothesis about extraction survives. They were never fragmented.**

| | |
|---|---|
| short (<50 mm) marks | 55,144 |
| …in a path that **also holds a long run** | **993 (1.8%)** |
| …in a path with no long run | 54,151 |
| items in a heavy-pen wall path | **1** (256 of 265 paths) |

If flattening had broken architectural paths, short marks would cluster inside
paths that also hold long runs. They do the opposite. A wall line is one item
in one path. **There is nothing to reassemble**, and a path-reassembly stage
would have joined unrelated geometry — so it was not built. Recorded as a
measurement, because on another drawing the answer may differ.

The short marks are overwhelmingly glyph outlines (fill paths) and 0.36 pt fine
detail. **Category E — annotation/text/hatch contamination.**

## A.3 Is the plan orthogonal? — measured

| angle | stroke length |
|---|---|
| 0° | 1,070.9 m |
| 90° | 991.0 m |
| 30° | 94.9 m (905 marks, 105 mm mean) |
| 60° | 83.0 m |
| 45° | 31.5 m (1,960 marks, **16 mm mean**) |

Every off-axis bucket together is ~350 m of very short marks — flattened
curves (door swings, fixtures, north arrows), not architecture. **Category D
does not apply to AR-00.** The axis-aligned detector is losing no rotated wing.

The `DIAGONAL` axis is kept and labelled throughout anyway, and
`as_line()` *raises* rather than silently handing a diagonal to an
axis-aligned engine — so a future villa with a rotated wing fails loudly
instead of quietly dropping walls.

## A.4 The finding that actually explains the breaks: WALL END CAPS

**157 of 185 short heavy-pen marks touch a perpendicular long heavy-pen run.**

They are wall **ends** — the closure drawn across a wall's thickness at an
opening or a free end. A parallel-face pairing cannot represent one, because
a cap is perpendicular to the faces it closes. So every wall end was invisible
to the graph, **and an invisible end is a break.**

`end_caps()` recovers them as observations with their evidence. A cap is
recognised by geometry, never by being short: its span must lie in the range a
wall thickness can take, and **both** ends must touch a perpendicular run — a
mark touching one thing is a stub, not a closure.

On AR-00: **333 caps**, separations clustering at 180–260 (169), 60–120 (86),
120–180 (62) — the real block thicknesses. 108 at the wall pen.

## A.5 The 115 components — not 115 problems

| class | count | wall length | share |
|---|---|---|---|
| **MAJOR** | **7** | **210.5 m** | **57.9%** |
| SMALL_ISOLATED | 49 | 126.6 m | 34.8% |
| MICRO/NOISE | 59 | 26.7 m | 7.3% |

Cause histogram:

| cause | count |
|---|---|
| I — probable non-wall geometry | 59 |
| G — junction not stitched | 26 |
| **J — unresolved** | **23** |
| A — genuine separate physical geometry | 7 |

Seven components hold nearly 60% of the wall length. **23 components remain
genuinely unexplained** and that is a gate failure, reported as one.

## A.6 The 228 termini — classified

| kind | count |
|---|---|
| **UNRESOLVED** | **109** |
| DRAWING_FRAGMENT | 56 |
| EXPECTED_OPENING_END | 32 |
| **LIKELY_MISSING_CONNECTION** | **31** |
| EXTERIOR_END | 0 |
| PROBABLE_NON_WALL | 0 |

Each report carries the nearest compatible continuation, the gap, the
separation difference, and the reason it was not joined — a repair list, not a
count. **31 are repairable connections. 109 are still unexplained.**

`EXTERIOR_END = 0` is honest, not good: the building-envelope test still does
not exist, so nothing can be classified as an exterior end yet.

## A.7 Stitching — evidence, never proximity

`engine/wall_stitching.py`. Four evidence families (IDENTITY, GEOMETRY,
CLOSURE, CONTEXT); two independent families before anything is validated.
The rule it exists to avoid, written in its docstring: `gap < X mm → connect`.

| status | count |
|---|---|
| STITCH_AMBIGUOUS | 93 (18 because door-sized) |
| STITCH_REJECTED | 19 (**12 by an end cap**) |
| STITCH_VALIDATED | 17 (1.2 m recovered) |
| STITCH_PROBABLE | 2 |

**The end-cap veto fired 12 times.** Each is a gap a proximity rule would have
closed and that the drawing explicitly says is a wall end. That is the
mechanism working: an end cap is evidence *against* joining, and this module
never reads one as permission to join.

## A.8 The length invariant — unchanged and strict

`source = post-split + itemised duplicate overlap`, drift **0.2 mm** on 387 m.
No percentage tolerance was introduced and a test proves that length lost
without a duplicate to explain it still fails.

## A.9 E31A GATE — proposed, scored, NOT READY

Eight gates, each naming a number and the reason a face walk depends on it.
Scored against this run's own numbers:

| gate | status | observed |
|---|---|---|
| G1 · unexplained length drift = 0 | **PASS** | 0.2 mm |
| G2 · no rejected clusters | **PASS** | 0 |
| G3 · every terminus classified | **FAIL** | 109 of 228 unresolved |
| G4 · major components hold ≥80% of length | **FAIL** | 57.9% in 7 |
| G5 · every disconnect explained | **FAIL** | 23 unexplained |
| G6 · no systematic junction failure | **PASS** | 0 unresolved; 4 corner overlaps vs 1 true crossing |
| G7 · fragmentation understood | **PASS** | measured: 993 of 55,144 |
| G8 · cycles where the raster says rooms are | **NOT_MEASURED** | needs raster correspondence |

**Verdict: NOT READY — 3 failing, 1 not yet measurable.**

Deliberately **not** gates, and the docstring says so:

- `graph_components == 1` — a drawing legitimately contains shafts, detached
  walls, balconies and separate blocks. The gate is that every disconnect is
  *explained*.
- `zero termini` — a wall genuinely ends at an opening and at the building edge.
- a percentage length tolerance — it would hide the loss that matters.

An unmeasured gate reads NOT_MEASURED and never PASS.

## A.10 Dashed topology

`dashed_runs()` is not yet wired into connectivity. One prerequisite was
found and fixed here: a PDF writes a solid stroke as `[] 0`, and reading that
as a dash pattern would have made every line on the sheet a topology boundary
candidate. `VectorPath.is_dashed` now distinguishes them correctly, so the
dashed population can be isolated in the next round for the washroom defect.

---

# PART B — TRACEABILITY

## B.1 Persistent quantity IDs

```
Q-23010-2F-BTH03-CERWALL-GROSS-001
```

Readable by a person, matchable by a machine, and **never derived from list
position** — a test parses the generator for `enumerate`, `index`, `position`
and `row_number` and fails if any appears. A positional id loses Bathroom-03's
identity on the first inserted room, which is precisely what revision
comparison needs kept.

A basis nobody stated is refused: `GROSS`, `NET` or `DIRECT`. A gross figure
read as net is an under-measure nobody notices.

## B.2 Quantity trace

`QuantityTrace` carries the whole chain — drawing, revision, geometry source,
boundary edge ids, height id and truth domain, opening ids, trade rule id and
version, assembly id and version, calculation reference, validation status,
release status, blocker, plus `drawing_preview_reference` and
`highlight_geometry_reference` reserved for the viewer.

Two rules are enforced, not documented:

- **A value with no release status is refused.** A figure printed without the
  status that governs it gets quoted.
- **`record()` emits empty provenance fields rather than omitting them.** An
  absent key reads as "not applicable"; an empty one reads as "nobody
  established this".

`gaps()` reports what a trace *cannot* answer — the honest half of provenance.
On 23010, every one of the 36 traces reports gaps.

## B.3 Room templates and trade assemblies

`engine/templates.py`. A room template says which trades **could** apply and
what they would need. It never invents a quantity. An assembly declares
**requirements**, and `formula_reference` must *name* an engine function —
passing arithmetic raises, because an assembly that can compute is a second
source of truth for a quantity.

Versioning is enforced: `V1`/`V2`/`V3`, and an `APPROVED` version without
`approved_by` **and** `approved_on` raises. An LLM may propose a rule; only a
person approves one.

**The library for 23010 is empty, on purpose.** No template and no assembly has
been signed. `room_template()` returns `None`, and the test that matters says
what `None` means: *NULL RULE SET MUST NEVER MEAN DEFAULT RULE.*

## B.4 Revision entity identity

`engine/revision_entities.py` — the layer E11 (`revision_delta`) assumes.
E11 compares BOQ snapshots keyed by item id; this is the level below, where
that key is established for spaces, walls, openings and quantities.

Matching is by stable id first, geometry second, and **never by list position**
(again tested against the source). A room whose centroid moved 100 mm keeps its
identity and the report records *which* evidence decided it.

With one revision it returns `NO_PRIOR_REVISION_AVAILABLE` — not an empty
change list. "Nothing changed" and "nothing to compare" look identical in a
report and mean opposite things.

---

# PART C — THE QA WORKBOOK, UPGRADED

Eleven sheets. All 36 spaces measured.

| sheet | rows | what changed |
|---|---|---|
| **Dashboard** | 19 | new — readable in under a minute |
| Room Register | 36 | + `semantic_source` |
| Room Count Summary | 12 | **two** manual checks |
| **Quantity Trace** | 36 | new |
| Flooring and Ceramic QA | 36 | — |
| Wall Quantities | 36 | — |
| Exceptions | 46 | + impact ranking |
| **QA Samples** | 45 | **three** populations |
| **Rules and Assemblies** | 0 | new — empty means unsigned |
| Takeoff Coverage | 13 | — |
| **Revision Delta** | 0 | new — no baseline, stated |

**Dashboard** counts sheets that already own their numbers — a test forbids
`*`, `/` and `round(` inside it, so it cannot become a second source of truth
sitting in front of the first. Takeoff status on 23010: **BLOCKED**.

**Two manual checks** (§19) because "what rooms exist on the drawing" and "what
rooms are in the contract" are different questions and one count agrees with
neither. A manual total that is right with a scope count that is wrong still
reads DIFFERS.

**Three QA populations** (§21): in-scope stratified (contracted work only, so
the owner is not measuring excluded rooms), risk-based (largest area, largest
perimeter, irregular geometry, unresolved status, weakest semantic provenance,
unclassified wall segments — each row carries **why** it was chosen, because
"largest area on the sheet" tells a surveyor what to bring a tape for and a
risk score does not), and scope audit (a few excluded rooms, because a wrong
exclusion is invisible in every other sheet).

**Exception impact ranking** (§22): affected spaces, affected uses, affected
BOQ sections, coverage unlocked, owner action, priority. Ranked by spaces and
uses, **never by money** — a cost on an unvalidated quantity gets quoted long
before the quantity does. The top row on 23010 is the wall graph: 36 spaces,
13 uses, owner action "supply the DXF/DWG of AR-00".

**Semantic provenance** (§23): every 23010 label is `HUMAN_VERIFIED`, stated on
the dashboard with the note that it is **not** evidence of automatic semantic
extraction.

The read-only contract is unchanged and extended: manual entries are declared
**validation evidence only** in the workbook's own warnings.

---

# What is still true

- No net quantity anywhere. No opening validated.
- `GROSS_PERIMETER` ready on 17 of 36 spaces; every other use 0 ready.
- 6 wall heights still missing from sections; `CEILING` blocks all 36.
- Scope undecided on COR-02, COR-03, REC-01, REC-02, SRV-01, STA-01.
- No trade rule or assembly signed for any room type.
- Still needed from you: **DXF/DWG of AR-00**, the door/window schedule,
  sections for the six heights.

No pricing. No material recipes. E31A not started.
