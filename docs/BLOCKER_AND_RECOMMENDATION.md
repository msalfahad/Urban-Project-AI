# URBAN PROJECTS — WHAT I NEED AND WHAT I RECOMMEND

Project 23010 · second floor · AR-00 rev MAR.2023 · commit `d4bb70b` · **800 tests passing**

This document is for external review. It states where the work is blocked, what I
believe the cause is, what I recommend doing about it, and what I need from the
owner. **Please attack the reasoning in sections 2 and 4** — those are the load-
bearing judgements, and if either is wrong the recommended plan is wrong.

---

## 1. WHERE THE WORK ACTUALLY IS

The deterministic geometry works. Per-space wall lengths exist for all 36 spaces
and reconcile with a prior independent run of the engine (95.39 m against
95.420 m on the nine ceramic-wall spaces). Semantics work: two blind agent
passes, 88.9%/100% label accuracy, zero false agreement, all safety counters
zero. Trade rules, heights and release gating are built and fail closed.

**What does not work is room topology.** Three known defects:

| defect | status |
|---|---|
| the polygon labelled WSH-01 is a duct, not the washroom | proven, **not fixed** |
| the true washroom (printed 1.500 × 2.400 m) has no polygon at all | **not recovered** |
| BED-04 still contains an unseparated printed 1600 × 3000 bathroom | **not recovered** |

Nothing downstream can be trusted past this. If a room polygon is wrong, perfect
door measurement afterwards cannot fix the takeoff.

Current release state: **15 of 36 spaces READY for gross perimeter, wall area,
plaster and ceiling; 8 for gross ceramic wall; ZERO net quantities anywhere.**

---

## 2. THE BLOCKER, AND WHAT I THINK CAUSES IT

Two detectors have now failed on the same cases, and the second failure produced
a number that I think explains both.

**Of 369 gaps found along proven wall pairs, ZERO have two different mapped
spaces on either side.**

Not few. Zero. Meanwhile 300 of 369 could not be resolved at all, and 45 landed
in the same region on both sides.

### My reading

The vector layer and the raster segmentation are two views of the same wall that
**do not correspond**. A break in a vector wall pair is not a break in the raster
region boundary:

- the raster regions were produced by flood fill stopping at ink, so two rooms
  are separated wherever ink is continuous
- a doorway in the vector layer is a break in two parallel lines
- if anything else closes that doorway in the raster — a threshold line, a dashed
  kerb, a door leaf drawn closed, a hatch — the regions stay separate and the
  break has no raster counterpart

So looking for openings by finding vector gaps and then asking the raster what is
either side is asking two sources that disagree about where the wall is.

**If this reading is right**, then adding more opening signals cannot help, and
the next thing to build is a reconciliation between the two views rather than a
seventh piece of evidence. **If it is wrong**, I am about to build the wrong
thing, which is why I would like it challenged.

### The alternative readings I considered

1. **The detector is too strict.** Tested and rejected: the rejection diagnostic
   shows 95.6% of lines fail on insufficient overlap, and 18,472 of 22,788 merged
   lines are under 100 mm — isolated text, hatch and fixture linework, not wall
   fragments. "No parallel partner" and "partner too thick" are both **zero**.
2. **Fragmented wall faces.** Tested and rejected: merging collinear fragments
   changed the rejection profile not at all (95.6% → 95.6%) and *reduced* pair
   count 358 → 284.
3. **Wrong thickness band.** Partly true and already acted on: 179 of 284 pairs
   were 60–120 mm, which is a door leaf or a fixture drawn as a thin box. The
   pass now requires ≥120 mm, leaving ~105 plausible partitions — about right
   for a villa floor.
4. **Corners masquerading as openings.** True, and named: 21 of the 45
   same-region candidates are wider than 2 m and 2 exceed 4 m. A wall ending at
   a corner interrupts both faces exactly as a doorway does. Perpendicular
   junction detection is **not built**, so those 21 are noise in the current
   candidate set.

None of 1–4 explains **zero** interior openings out of 369. Only a
correspondence failure does.

---

## 3. WHAT I NEED FROM THE OWNER

Ordered by how much each unblocks. The first would change the approach entirely.

### 3.1 A DXF or DWG export of AR-00 — the highest-value input by far

I checked what has been supplied. There are DWG files (`P7757.dwg`,
`ST7757.dwg`, `20230331-STR.dwg`) but **none of them is the architectural sheet
for project 23010** — the only 23010 source is the plotted PDF.
`20230331-STR.dwg` is dated the same month as AR-00 rev MAR.2023 and may be the
same project's *structural* sheet; if so, its architectural sibling probably
exists.

A DXF would very likely make this whole class of problem disappear, because door
and window blocks are explicit entities rather than something to infer from two
parallel lines. The agreed source hierarchy already puts a DWG/BIM door entity
above vector inference, and everything in section 4 is the fallback for not
having one.

**Ask: is a DXF/DWG of AR-00 available? Even an unclean export.**

### 3.2 The door and window schedule

Even without a DXF, a schedule tied to locations gives openings a stronger source
than geometry inference, and gives every opening a height. Right now
`height_mm` is `None` on every opening candidate, correctly.

### 3.3 A section drawing, for heights

**Six of the eight named heights are HEIGHT_REQUIRED.** Only ceramic (3.00 m) and
plaster (3.20 m) exist, and both are owner rules that explicitly record they were
*not* read from a section. Missing: structural wall, blockwork, paint,
waterproofing, clear and ceiling height. Paint and blockwork are needed before
those trades can produce anything at all.

### 3.4 A scope decision on six spaces

The owner's mark does not reach these, so AMBIGUOUS is the correct answer and
they are blocked rather than guessed: `COR-02`, `COR-03`, `REC-01`, `REC-02`,
`SRV-01`, `STA-01`.

### 3.5 Approved trade rules for two space types

Neither the ceramic nor the plaster rule set covers `MASTER_BEDROOM` or
`OPEN_PLAN_LIVING`. Eight decisions sit at RULE_REQUIRED. A model may propose
these; it may not sign them.

---

## 4. WHAT I RECOMMEND BUILDING, IN THIS ORDER

The judgement here is the ordering, not the items.

### 4.1 Reconcile the vector and raster views of a wall — FIRST

Build a correspondence: for every vector wall pair, which raster wall band does
it occupy, and vice versa. Then a gap in the vector pair can be tested against
what the raster actually does at that place, and the disagreement becomes
visible instead of producing zero results silently.

This also gives the by-product the geometry engine has needed all along:
**wall thickness from paired vector faces**, which is currently `None` on every
segment and blocks blockwork entirely. The pairs already carry the thickness —
120–180 mm (60 pairs), 180–260 (30), 260–400 (15) — they are simply not attached
to raster wall segments yet.

*Why first:* it is the only item that explains the zero, and it unblocks
thickness as a side effect.

### 4.2 Perpendicular junction detection

A gap bounded by a perpendicular wall pair is a corner, not an opening. Until
this exists, roughly half the candidate set is wall terminations. Cheap, and it
cleans up every later result.

### 4.3 The building-envelope test

`EXTERNAL` is 0 of 703 segments. The march crosses cavities correctly now but
exhausts its 600 mm reach in the dimension zone. The fix is an envelope test, not
a longer march — a longer march walks through whole rooms.

Per earlier review guidance this must **not** assume `union(mapped spaces)` is
the true envelope, since this segmentation is already known to miss a real room.
It should combine exterior wall chains, border-connected free space and the
mapped-space union, and return INTERNAL / EXTERNAL / UNRESOLVED with provenance
rather than forcing full coverage.

### 4.4 Dashed-run topology candidates

`engine/walls.dashed_runs()` already exists and the spike did not use it. The
washroom's threshold is recorded as a dashed line, so a paired-face detector
cannot see it by construction. A dashed run should be a
`TOPOLOGY_BOUNDARY_CANDIDATE`, **not** a door — a dashed line may be a
threshold, a shower kerb, an opening, a finish change or a bulkhead, and what
kind it is gets decided later.

### 4.5 Only then, openings (E34)

With correspondence, junctions, envelope and dashed runs in place, re-assess
whether vector evidence is sufficient. If it is not, openings fall back down the
source hierarchy: DWG entity → vector block → validated jamb geometry →
schedule → raster/vision → human review.

### What I recommend NOT doing

- **Not** adding more opening signals before 4.1. Six signals produced zero
  interior openings; a seventh will produce zero too.
- **Not** loosening the pairing tolerances. The diagnostic shows the drawing
  genuinely contains ~18,000 sub-100 mm non-wall segments.
- **Not** tuning toward the printed dimensions. 1.500 × 2.400 m and
  1600 × 3000 mm are how a recovered polygon gets **validated**, never a
  correction factor applied to reach them.
- **Not** starting material quantities or pricing. Nothing is close to ready.

---

## 5. QUESTIONS FOR THE REVIEWER

1. **Is the correspondence-failure diagnosis in section 2 sound?** Zero interior
   openings out of 369 is the whole basis for the recommended ordering. What
   else could produce exactly zero?
2. Is there a way to recover a merged room boundary that does not depend on
   vector/raster correspondence at all — something purely raster, or purely
   vector, that I have missed?
3. **Is asking for a DXF the right call, or a way of avoiding a solvable
   problem?** Different architects draw differently, and a method that needs
   clean CAD may not generalise.
4. The washroom's threshold is dashed. Is treating a dashed run as a *topology*
   boundary rather than a door the right abstraction, or does it over-generalise?
5. Wall thickness currently comes from marching across raster ink, capped at
   600 mm and stopping at the first non-ink pixel. Section 4.1 proposes taking it
   from paired vector faces instead. Is that the stronger source, or does it
   inherit the same correspondence problem?
6. Is there a case for accepting `VALIDATED_PARTIAL` output — 15 spaces of gross
   quantities — as useful to the business now, or does partial output do more
   harm than good in a quantity surveying context?

---

## 6. FACTS, SO THE REASONING CAN BE CHECKED

| | |
|---|---|
| source | one plotted vector PDF, sha256 `bddb175c…a47bfa74`. No architectural DXF/DWG |
| raster | 3509 × 4963 px at 300 dpi, 10.813 mm/px, scale proven on a second printed dimension (residual 2.37 mm over 25 m) |
| vector | 19,257 drawing objects · 73,716 line segments · 2,399 bezier curves |
| axis-aligned lines | 35,355 → 22,788 after collinear merge; **18,472 still under 100 mm** |
| paired wall faces | 863 kept (2.6%); rejection 95.6% insufficient overlap, 0% no-partner, 0% too-thick |
| wall pairs | 284; **179 are 60–120 mm** (not masonry); ~105 plausible partitions |
| gaps along pairs ≥120 mm | 369 |
| gap classes | 0 interior · 45 intra-region · 21 unmapped · 3 exterior · 300 unresolved |
| of the 45 intra-region | 17 door-scale (≤1100 mm), 21 wider than 2 m (**corners, not openings**) |
| wall segments classified | 564 internal · 139 unresolved · **0 external** of 703 |
| heights | 2 releasable of 8; 6 HEIGHT_REQUIRED |
| release | 15/36 READY gross; 8/36 gross ceramic wall; **0 net anywhere** |
| tests | 800 passing |

### What is NOT claimed

- Not that the per-space wall lengths are *correct*. They reproduce a prior run
  of the same engine; both could share an error. The manual site figure
  (102.70 m) has never been used to calibrate anything.
- Not that the 15 READY spaces are verified — only that their stated
  dependencies are satisfied.
- Not that any opening has been found. Zero validated openings exist.
- Not that the washroom or BED-04 bathroom has been recovered. Both are
  `UNRESOLVED` and all their trade quantities are blocked.
