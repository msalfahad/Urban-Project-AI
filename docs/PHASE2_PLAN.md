# PHASE 2 PLAN — Automated Full-House Quantity Takeoff

Written before any code. Answers the eight questions asked after Run 1.

---

## A CORRECTION FIRST

After Run 1 I told you *"E25 produced a floor total, not a per-space breakdown."*
That was wrong about the code, and it matters because it changes the size of the
highest-priority job.

`engine/walls.py` already contains a per-space wall model. `SpaceWalls` holds
`segments[]` and `openings[]`; `WallSegment` already carries **10 of the 14
fields** you listed in section 6:

| you asked for | exists today | as |
|---|---|---|
| `wall_segment_id` | ✅ | `wall_id` |
| `start_coordinate` / `end_coordinate` | ⚠️ | `start_px` / `end_px` — **pixels, not mm** |
| `length_m` | ✅ | `length_mm` + `.length_m` |
| `boundary_type` | ⚠️ | split across `segment_type` (PHYSICAL_WALL / VIRTUAL_OPENING_CLOSURE / OPEN_TRANSITION) and `classification` (INTERNAL / EXTERNAL). **No SHAFT_BOUNDARY.** |
| `adjacent_space_id` | ✅ | `adjoining_space` |
| `wall_thickness` | ❌ | — |
| `opening_ids` | ✅ | `opening_ids` |
| `source_file` / `drawing_id` / `revision` | ✅ | `source_drawing`, `source_revision` |
| `measurement_basis` | ❌ | on the Region, not the segment |
| `validation_status` | ✅ | `validation` |
| `provenance` | ⚠️ | on `Opening` only |

And `SpaceWalls.gross_wall_perimeter_m` — your section 7 requirement — is already
implemented and already tested.

**So the real gap is not the model. It is the plumbing.** `VectorPdfSource`
computes the label array and wall mask inside `regions()` and throws them away;
nothing outside that method can reach them. No caller anywhere in the repo runs
`space_walls()` on a real drawing — the only callers are unit tests using
synthetic arrays. That is why Run 1 had no per-space wall numbers: not a missing
engine, a missing pipe and a missing persisted artifact.

This is good news. Phase 1 below is days of work, not weeks.

---

## 1. WHAT CAN BE REUSED UNCHANGED

| module | role | why it survives |
|---|---|---|
| `engine/geometry.py` (E23) | regions, calibration, hole filling, source ranking, measurement bases | Frozen and hash-verified through Run 1. The `MEASUREMENT_BASES` vocabulary and `choose_geometry()` source hierarchy are exactly what every new trade needs. |
| `engine/walls.py` (E25) | per-space boundary decomposition | See above — the model is right, it needs fields added and a caller. |
| `engine/group_registry.py` | canonical apartment/zone ids | Built in Run 1, generalises to any project. |
| `engine/semantic_compare.py` (E32) | A1/A2 comparison, registry gating, membership sets | Field-agnostic. New fields join `FIELD_MATERIALITY`. |
| `engine/quantities.py` | `Quantity` with full provenance | The `element` field is already free text (`FLOOR / WALL / SKIRTING / CEILING ...`). New elements need no schema change. |
| `engine/release.py` (E33) | release gating, exception queue, tri-state rule presence | Works on any `Quantity`. |
| `engine/trades.py` | 39-trade canonical registry + alias matcher | Already contains SKIRTING_PROFILE, BLOCKWORK, PAINT, PLASTER_INTERNAL/EXTERNAL, WATERPROOFING, CEILING, GYPSUM, DOORS, WINDOWS_ALUMINIUM. **No new trade ids needed for any trade in your list.** |
| `engine/units.py`, `unit_guard.py` | unit typing and guards | m² / m / m³ / count all present. |
| `engine/reconcile.py` (E30) | design vs site vs commercial | The three-truths split is unchanged. |
| `engine/waste.py` | waste factors by family | Feeds the material engine directly. |
| `pipeline/orchestrator.py` | event bus with causal log | Already the right shape for QS Controller progress events. |
| `agents/a1_extractor/semantic.py` | schema 3.0 | Extends; does not change shape. |
| `agents/a2_reviewer/` | blind pass + challenger | Both proved themselves in Run 1. |
| `engine/audit_log.py`, `revision_delta.py`, `completeness.py` | audit, revisions, coverage | Unchanged. |

**Roughly 70% of the engine is reusable as-is.**

---

## 2. WHAT NEEDS MODIFICATION

### 2.1 `engine/geometry.py` — expose what it already computes
`VectorPdfSource.regions()` builds `lab` (the label array) and the ink mask and
discards them. Add a `segmentation()` method returning a frozen
`Segmentation(labels, wall_mask, px_mm, outside_id)` so E25 can consume it.
No measurement logic changes, so the Run 1 hash stays valid.

### 2.2 `engine/walls.py` — four field additions, one new boundary type
- `boundary_type` becomes one first-class field with your five values:
  `PHYSICAL_WALL · VIRTUAL_OPENING_CLOSURE · OPEN_TRANSITION · EXTERNAL_BOUNDARY · SHAFT_BOUNDARY`.
  The current `segment_type` + `classification` pair collapses into it; both stay
  as derived properties so nothing downstream breaks.
- `start_mm` / `end_mm` alongside the pixel coordinates. Pixels are a rendering
  artefact; mm is the drawing's own space and survives a re-render at a different dpi.
- `wall_thickness_mm: int | None` — **None, never a default.** Measured by marching
  across the wall body, which `space_walls()` already does to classify internal vs
  external; it currently throws the distance away.
- `measurement_basis` and `provenance` per segment.

### 2.3 `engine/trade_rules.py` (E27) — heights and elements
Two structural problems today:
- **One `height_m` per trade rule set.** Your section 9 needs eight named heights
  with independent provenance. `height_m` becomes a lookup into a project
  `HeightRegistry`; the single field stays as a deprecated shim that raises if the
  registry has a value.
- **Rules are floor/wall only.** `RoomRule` gains `skirting`, `ceiling`,
  `waterproofing_horizontal`, `waterproofing_vertical`, `blockwork` — each
  `str | None | RULE_REQUIRED`, and `decide_trade()` extends from 2 elements to 7.

### 2.4 `engine/quantities.py` — per-element inputs
`SpaceInputs` today carries two geometric facts (`floor_area_m2`,
`gross_wall_perimeter_m`) and one deduction. It becomes a `SpaceGeometry` record
holding the per-space wall model, ceiling area, opening schedule and each
applicable boundary length, so a trade asks for what it needs rather than
receiving one perimeter and guessing.

### 2.5 `agents/a1_extractor/` — fixture evidence as input, not output
A1 receives `detected_fixtures[]` (section 12) as another signal and must cite it
in `confidence_basis`. `SpaceSemantics` gains `fixture_evidence_used: list[str]`
so we can measure whether fixtures actually improved classification on a project
whose room names we have never seen.

### 2.6 `agents/a9_orchestrator/` — narrower, not wider
See question 4.

---

## 3. WHAT IS GENUINELY NEW

| id | module | what it does | why it cannot be folded into an existing one |
|---|---|---|---|
| **E25.2** | `engine/wall_model.py` | Runs E25 across every space of a real drawing, reconciles, persists the per-space wall model | The plumbing that does not exist |
| **E34** | `engine/openings.py` | Opening register: type, width, height, area, wall segment link, per-trade deduction rules | Openings are currently a by-product of wall tracing with width only |
| **E35** | `engine/fixtures.py` | Deterministic fixture detection — WC, basin, shower, bath, floor drain, counter, sink, washer, wardrobe | New detector class; symbol/geometry matching, not region filling |
| **E36** | `engine/materials.py` | Recipe engine: plaster, screed, blockwork → cement bags, sand m³, block count | Nothing in the repo converts area to material |
| **E37** | `engine/qa_sample.py` | Selects the QA sample, scores your manual answers against it, routes failures by engine | Section 29 |
| **E38** | `engine/heights.py` | Height registry: 8 named heights × value, unit, source, drawing, revision, validation | Section 9 |
| **E31** | `engine/planar.py` | Vector planar-face engine for irregular polygons | Already backlogged; kills the ~3% raster understatement on the 69.5% of area that is not a simple rectangle |
| **E23.2** | affine calibration in `geometry.py` | 2 horizontal + 2 vertical dimensions, scale_x/scale_y/rotation/translation, residuals | Section 26 |
| — | `pipeline/qs_controller.py` | The measurement pipeline as a deterministic stage graph | See question 4 |
| — | `engine/ceilings.py` | Ceiling area where it is not floor area — voids, shafts, double height, drops | Section 19 |

---

## 4. QS CONTROLLER — NEW AGENT, OR A9?

**Neither. It must be deterministic code, not an agent at all.**

A9 today is a thin LLM router: it takes an `Event` and returns a `Routing` with
`route_to`, `priority`, `escalate`. That is a judgement call and it is the right
job for a model.

Orchestrating a measurement pipeline is not a judgement call. It is a dependency
graph with gates: geometry before walls, walls before wall quantities, semantics
before trade rules, trade rules before assembly. Putting a language model in that
loop would inject non-determinism into the one chain whose entire value is being
reproducible — and it directly contradicts the project's own rule, *code
calculates*. Deciding "walls are done, start semantics" is control flow.

So:

- **`pipeline/qs_controller.py`** — a deterministic stage graph. Each stage
  declares its inputs, its outputs, and its gate. It emits progress events onto
  the existing `pipeline/orchestrator.py` bus, which already records causality.
  Your section 27 checklist (`Floors measured ✅ … 5 exceptions need review ⚠️`)
  falls out of the stage table for free — it *is* the stage table.
- **A9 keeps exception routing**, which is what it is good at: given an exception,
  who should see it and how urgently.

One more reason: a deterministic controller can be replayed. If a takeoff is
challenged six months from now, the controller re-runs the identical graph on the
identical frozen inputs and produces the identical numbers. A model-driven
controller cannot promise that.

---

## 5. DATABASE / SCHEMA CHANGES

### New collections
```
projects/{project}/drawings/{drawing}/revisions/{rev}
projects/{project}/spaces/{space_id}
projects/{project}/spaces/{space_id}/wall_segments/{wall_segment_id}
projects/{project}/openings/{opening_id}
projects/{project}/fixtures/{fixture_id}
projects/{project}/heights/{height_id}
projects/{project}/quantities/{quantity_id}
projects/{project}/materials/{material_id}
projects/{project}/exceptions/{exception_id}
projects/{project}/qa_samples/{sample_id}
projects/{project}/takeoff_runs/{run_id}
```

### Key records

**`wall_segment`** — your section 6 list in full, plus `boundary_type` as the
5-value enum, `wall_thickness_mm` nullable, `start_mm`/`end_mm`, and a
`geometry_hash` tying it to the frozen deterministic layer that produced it.

**`height`** — one document per named height per project:
`{height_id, name, value_m, unit, source, drawing_id, revision, source_type, validation_status}`.
`source_type ∈ {SECTION_DRAWING, SPECIFICATION, OWNER_RULE, SITE_MEASURED, ASSUMED}`
— and `ASSUMED` is refused by the quantity engine, so it can only ever sit in the
exception queue.

**`quantity`** — the existing `Quantity` plus `height_id`, `opening_rule_id` and
`wall_segment_ids[]`, so every number traces to the exact segments that made it.

**`space_result`** — your section 30 output, assembled from quantities rather than
stored independently, so it can never disagree with them.

### Migration
Run 0 and Run 1 records stay exactly as they are under `data/runs/`. Nothing
rewrites them; the golden test reads them as-is.

---

## 6. IMPLEMENTATION PHASES

### Phase 0 — Freeze 23010 as a golden regression test *(half a day)*
Pin Run 1's scored outputs as an expected-results fixture: 36 spaces, the label
key with its declared alternatives, the scope key, the apartment key with its
9 named exclusions, the geometry hash, and the safety counters. Every later phase
re-runs it. **This is the guard rail that stops us overfitting 23010** — the test
asserts the numbers do not get *worse*, and deliberately does not reward them
getting better through project-specific rules.

### Phase 1 — Per-space wall model *(the highest-priority gap)*
E23 `segmentation()` → E25.2 across all 36 spaces → persist per-space segments.
Add `boundary_type`, mm coordinates, `wall_thickness_mm`, basis, provenance.
**Deliverable: `gross_wall_length_m` for every space**, reconciled against the
95.42 m floor total, with every space that fails to close named rather than
patched. Answers "Bathroom 03: gross wall run = X m".

### Phase 2 — Heights (E38) + trade rule expansion (E27.2)
Eight named heights with provenance and no default anywhere. `RoomRule` extends
to 7 elements. Fill or explicitly `RULE_REQUIRED` the `MASTER_BEDROOM` and
`OPEN_PLAN_LIVING` gaps Run 1 found *(your section 24 — and where the honest
answer is project-specific, it stays RULE_REQUIRED rather than becoming a default)*.

### Phase 3 — Openings (E34)
Opening register, linked to wall segments, with type/width/height/area. Gross
geometry stays gross; each trade's deduction rule is a separate, named, per-trade
decision. **Nothing is ever permanently subtracted.**

### Phase 4 — The wall-family trades *(first real money)*
Ceramic wall · plaster gross/deduction/net · paint *(independently — never
plaster area)* · skirting *(linear metres from boundary length, never from floor
m²)* · blockwork by thickness. All arithmetic in code.

### Phase 5 — Ceilings and waterproofing
Ceiling area computed, not assumed equal to floor area where voids, shafts,
double height or drops exist. Waterproofing split horizontal / vertical with the
height from the project rule.

### Phase 6 — The three Run 1 challenger findings *(your section 25)*
Already layer-assigned by existing evidence rather than by guesswork:
- **WSH-01 → E23 geometry.** The E25 notes already record that the region called
  WSH-01 *is the shaft beside the wash room, not the wash room*. So A2 blind
  calling it `SERVICE_SHAFT` may have been right about the region and wrong about
  the room — a region-identity defect, not a semantic one. Fixing the label would
  have hidden a geometry bug.
- **OPEN-01 → E23 geometry.** The two `فتحة` openings sit inside the 127.72 m²
  region; hole-filling may have swallowed them. Measure, then decide.
- **BED-04 → E25 boundary.** Known: a 1600×3000 bathroom whose door is drawn as a
  gap, so it never separates from the bedroom.

None of the three is fixed by prompt wording.

### Phase 7 — Fixture evidence (E35) and label-independent semantics
Detect WC, basin, shower, bath, floor drain, counter, sink, washer, wardrobe.
Feed as evidence to A1/A2. **Test by renaming**: take 23010, replace every Arabic
room label with an unseen synonym or blank it entirely, and measure how far
accuracy falls. That is the real test of section 11, and it costs one drawing.

### Phase 8 — QS Controller + progress UX
The deterministic stage graph, the progress checklist, exception counts.

### Phase 9 — E31 vector planar faces
Removes the bounded ~3% raster understatement on the 69.5% of floor area that is
not a simple rectangle.

### Phase 10 — Material recipes (E36)
Plaster, screed, blockwork → cement bags, sand m³, block count. Every ratio,
thickness, waste factor and bag weight is visible configuration. **No LLM
anywhere near it.**

### Phase 11 — Scale hardening (E23.2) + QA sampling (E37)
Affine calibration with residuals; automatic QA sample selection.

### Phase 12 — A second completely unseen house
The only thing that can prove any of the above generalises.

**Pricing is not in any phase.** Per your section 23, nothing attaches a rate
until quantity accuracy is proven.

---

## 7. TESTS REQUIRED

Per phase, the tests that would have to fail for the phase to be wrong:

**Phase 0** — the golden test itself: 23010 label/scope/apartment keys, the
geometry hash, and every safety counter at zero.

**Phase 1** — a space whose boundary does not close is UNRESOLVED, never
silently summed · per-space lengths sum to the floor total within tolerance ·
`wall_thickness_mm` is `None` when unmeasurable and never a default · mm
coordinates survive a dpi change while pixel coordinates do not · a shaft
boundary is not counted as a room wall.

**Phase 2** — a missing height raises rather than defaulting to 3.0 · each of the
eight heights is independently settable · a height whose `source_type` is
`ASSUMED` cannot produce a releasable quantity · `MASTER_BEDROOM` with no rule
yields `RULE_REQUIRED` with a routable id.

**Phase 3** — gross geometry is never mutated by a deduction · two trades deduct
differently from the same opening · an opening with no wall segment is an error.

**Phase 4** — skirting is linear metres and is never derived from floor area ·
paint area may differ from plaster area on the same wall · plaster
gross − deductions = net, exactly · blockwork separates by thickness.

**Phase 5** — a room under a void has ceiling area ≠ floor area · vertical and
horizontal waterproofing are separate quantities.

**Phase 6** — one regression test per finding, asserting the fix landed in the
layer named above and not in a prompt.

**Phase 7** — accuracy on 23010 with every room label removed *(the number itself
is the finding, whatever it is)* · a fixture set alone never sets a quantity.

**Phase 8** — the stage graph refuses to run a stage whose inputs are not ready ·
replaying the controller on frozen inputs reproduces byte-identical quantities.

**Phase 10** — every recipe constant is reachable as configuration · no material
quantity can be produced without a stated ratio and waste factor.

**Standing, every phase** — the full suite (646 today) plus the 23010 golden test,
plus the fail-closed audit, which grows by one named conversion per phase.

---

## 8. WHAT SHIPS FIRST, WITHOUT WAITING FOR EVERYTHING

**Phases 0–4 are a complete, useful product on their own.** At the end of Phase 4
you can hand a villa's drawings in and get back, per space and fully traceable:

```
floor area · gross wall length · skirting length
ceramic floor · ceramic wall
plaster gross / deductions / net
paint area · blockwork by thickness
```

with no blockwork materials, no ceilings, no cement bags, no fixture detection
and no second project — and it would already be the largest single jump in
capability this system has had, because it closes the gap Run 1 named as the
biggest.

**Phase 1 alone** is shippable and answers the question you actually asked after
Run 1: *what is the wall run of Bathroom 03?*

The one thing I would not defer is **Phase 0**. Without the golden test pinned
first, every later phase risks quietly tuning 23010 — which is precisely what
your section 31 forbids.

---

## WHAT THIS PLAN DELIBERATELY DOES NOT DO

- Does not make the manual qiyal a production input anywhere. It appears only in
  the golden test, the QA sampler and calibration studies.
- Does not let A1 or A2 measure anything, in any phase.
- Does not add a default height, a default trade rule, or a default scope.
- Does not price anything.
- Does not tune 23010's numbers. The golden test is a floor, not a target.
