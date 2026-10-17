# The four-layer geometry model — forward terminology

**Normative for new work. Historical artifacts are preserved unchanged and
are not rewritten.**

Established by `QS_MEASUREMENT_REGION_EXPERIMENT_01`, frozen at
`c9d13a2c350b0d5ee8d050363afc6813880999ccc4773dbd5addf5846426f252`
(protocol `71eb8ec7cfe9c64c5c4ae1e9862d48b197b163f67f51d415798f0d5b8133ee8d`).
That experiment computed no area and no quantity, read E1.4 and did not
modify it.

---

## The pipeline

```
PHYSICAL_GEOMETRY          what material exists, and where
        ↓
TOPOLOGICAL_SITES          what is established BETWEEN physical entities
        ↓
TRADE_MEASUREMENT_REGIONS  a calculable region, for one trade and one basis
        ↓
QUANTITIES                 after deductions, additions and rules
```

Each arrow is one-way. A later layer may read an earlier one. **No later
layer may write to, repair, or lend its authority to an earlier one.**

---

## The four statuses

These are four different questions. They are never collapsed into one field
and never summed into one metric.

### `PHYSICAL_REGION_STATUS`

*Is this region enclosed by material that exists?*

Values: `ENCLOSED_BY_DRAWN_MATERIAL`, `OPEN`.

`ENCLOSED_BY_DRAWN_MATERIAL` means the ring is made of material and nothing
else. A ring completed by a portal, a barrier, or any span carrying
`material_present=false` **is not** enclosed by drawn material, however
tidily it closes. See invariant §120.

`OPEN` is a result, not a defect. A physical region may legitimately remain
open, and forcing it closed to satisfy a quantity engine is the error this
model exists to prevent.

### `TOPOLOGICAL_SITE_STATUS`

*What is established at this site between two physical entities?*

Types: `CONFIRMED_DOOR_OPENING`, `CONFIRMED_WINDOW_OPENING`,
`CONFIRMED_OPEN_PASSAGE`, `CONFIRMED_GLAZED_SEPARATOR`,
`MATERIAL_CONTINUITY`, `UNRESOLVED_GAP`.

**A topological site may represent an ABSENCE of geometry.** A site is
`wall termination A + the void + wall termination B`, and any door leaf,
swing arc or block inside the void is **evidence about the site, not the
site**. The void is a first-class site with no line in it.

This matters because an opening is frequently an absence. The
`SAFETY_SAMPLE_01/02/03` rounds established that a sampling unit built from
drawn intervals can only offer an opening where the drawing gives the
opening its own ink: across three independently designed samples a blind
reference established exactly one `OPENING_IN_SEPARATOR` each time. The site
representation removes that limitation. In
`QS_MEASUREMENT_REGION_EXPERIMENT_01`, **17 of 50 sites had no drawn entity
in the void** and were represented without difficulty.

### `MEASUREMENT_REGION_STATUS`

*Can a calculable region be formed, for a stated trade and basis?*

Values: `MEASUREMENT_REGION_CLOSED`, `MEASUREMENT_REGION_NOT_ESTABLISHED`
(with an exact reason).

Trade- and basis-dependent, never universal. The same doorway may be closed
for gross room perimeter and left open for a flooring finish zone. A region
that cannot be formed returns the reason; it is never closed heuristically,
never rescued by a semantic model, and never decided by a benchmark.

### `TRADE_QUANTITY_STATUS`

*Does this edge or opening contribute to this quantity?*

A statement about the **pair** `(edge, trade)`, held in the quantity layer —
never a property of the edge's geometry. A physical wall face contributes
plaster length; a synthetic measurement boundary contributes zero; a
confirmed opening contributes a deduction.

---

## The measurement closure

A synthetic, zero-material span across an **already-established** opening,
existing only so a measurement region can be formed.

Mandatory fields: `closure_id`, `source_opening_id`, `endpoint_a`,
`endpoint_b`, `source_evidence_ids`, `measurement_basis`,
`applicable_trade`, `physical_material_present=false`, `physical_wall=false`,
`physical_separator=false`, `changes_connectivity=false`,
`quantity_length_contribution=0`, `synthetic=true`, `reversible=true`,
`status`, `provenance`.

**An `UNRESOLVED_GAP` may never receive one.** A closure may never be
inferred because a polygon would otherwise stay open, because it produces a
plausible area, because it agrees with a benchmark, because it improves
room-release statistics, or because nearby geometry looks like a door
without established evidence.

**It may never be used as evidence that a physical wall exists.**

---

## Mandatory CI requirements

Both are enforced for any future `QS_MEASUREMENT_REGION_BUILDER`. See
invariant §121.

1. **Reversibility, proved not stored.** `HASH(A) == HASH(C)` after removing
   every measurement construct, over the physical claims specifically.
2. **Zero material contribution.** No synthetic, open or unresolved edge
   carries a material, plaster or wall-ceramic length contribution for any
   trade.

---

## The frozen result for P7757 ground floor

Recorded here so the corrected vocabulary has a worked example.
**Historical E1.4 artifacts are not rewritten.**

```
PHYSICAL_REGIONS_ENCLOSED_BY_DRAWN_MATERIAL      0
PHYSICAL_REGIONS_OPEN                           20
MEASUREMENT_REGIONS_CLOSED                       3
MEASUREMENT_REGIONS_WITH_UNRESOLVED_GAPS        16
MEASUREMENT_CLOSURES_CREATED                    31
CONFIRMED_OPENINGS_USED                         33
UNRESOLVED_GAPS_NOT_BRIDGED                     15
```

E1.4's frozen registers report 3 regions `CLOSED_BY_DRAWN_MATERIAL`. Under
the corrected vocabulary those 3 are `MEASUREMENT_REGIONS_CLOSED` and the
physical count is 0. Both records stand: E1.4's as run, this one as the
forward reading.

---

## On the door-evidence correlation

In this frozen experiment all 31 established openings rested on exactly one
evidence type — `A_DOOR_LEAF_OR_SWING_ARC_STANDS_IN_THE_GAP` — and all 15
unresolved gaps had no drawn entity in the void. The correlation was
perfect.

**That is `CURRENT_E1_4_CONFIRMATION_BEHAVIOUR_ON_THIS_DRAWING`. It is not a
`UNIVERSAL_DOOR_EVIDENCE_REQUIREMENT`.**

It describes how one confirmation rule behaved on one drawing. A future
independent method may establish an opening from other evidence — a raster
reading, a door schedule, a dimension chain, a second drawing, a surveyor.
Nothing in this model requires a leaf or a swing arc, and no code may be
written that assumes one.

The 15 unresolved gaps stay unresolved. The 12 among them carrying jamb
returns at both ends **and** a width matching a confirmed-door family are
**not promoted**: nothing stands in those gaps, and a wall-thickness-scale
gap with no occupancy is as likely a junction the cross wall did not reach
as it is a doorway. Closure success is never evidence, so the fact that
bridging them would close more regions is not an argument for bridging them.
