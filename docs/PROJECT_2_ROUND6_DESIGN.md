# Project 2 — round 6 DESIGN. Nothing is implemented yet

Round 5 stays frozen: `PROJECT_2_CAD_ROUND5_HASH 8a90def3ac70301a1398aed5`,
artefact and export unchanged. This document is §12's first deliverable and
the engine is untouched — `git diff -- engine/` is empty on the commit that
carries it.

---

# A · Root cause

**The five symptoms are not five faults. They are two upstream defects and
three absent capabilities**, and every number below comes from the frozen
round-5 state, re-derived read-only.

## A1 · Defect 1 — promiscuous face pairing invents 3,000 walls

`physical_wall.build()` pairs **every** two parallel lines whose separation
is 50–600 mm and which overlap by 500 mm. On a real plan the lines inside
any 600 mm band include both faces of the wall, the finish or skirting
line, a door frame, a fixture edge, a hatch boundary and the next room's
wall. So the pairing is promiscuous:

```
845   distinct face lines in P7757
3272  "physical wall bands" built from them
713   of the 845 lines (84%) belong to MORE THAN ONE band
      one line is paired into as many as 8 different "walls"

thickness histogram, as frozen (mm : bands)
  250:285  225:261  300:234   50:218  600:185  350:184
  200:172  450:167  575:167  475:159  550:150  125:128
```

A drawing has a few wall thicknesses. This is a flat distribution across
the entire admitted band — the signature of a rule that pairs whatever is
in range.

Each false band then has spans where only one of its two "faces" is drawn,
and `partition_continuity` correctly recovers those for topology. The
result is a phantom partition drawn parallel to a real wall at an arbitrary
offset:

```
8001  ONE_FACE_ONLY spans
4159  recovered partition lines
3743  metres of inferred partition
```

Those lines slice the floor. **This single defect produces four of the five
symptoms**, and the traces are direct:

| released polygon | bounded by recovered spans from bands of thickness |
|---|---|
| KITCHEN 3.85 m² | 575, 500, 500, 400, 200 mm |
| W.C 3.50 m² | 500, 500, 600, 300, 150 mm |
| "garden" 5.62 m² | 500, 200, **150, 50** mm |
| RECEPTION 17.08 m² | 575, **50**, 300 mm |

A 50 mm band is not a wall. KITCHEN's polygon is cut at x = −151145.8 and
−150289.9, which correspond to no wall on the drawing. W.C's polygon is a
1,000 mm-wide slot between a real face at x = −155889.9 and a phantom at
−154889.9 — which is why its area looked plausible while its shape sliced
across both the WASH and the W.C.

**A signal that was available and unused:** none of the four released
polygons has a single opening on its boundary. A room with no door is a
strong negative, and nothing asked.

## A2 · Defect 2 — absence of a label recorded as evidence of a void

`enclosure_role.classify` ends with `elif not obs: role = VOID_OR_SHAFT`.
All 43 arrived through that one branch:

```
43 polygons   role=VOID_OR_SHAFT  obs=0  nested=0  partitions=0  voids=0
 1 of the 43  contains any text at all, of any class
```

They contain no label because they are slivers of sliced rooms. But even
with perfect walls the branch would be wrong: `VOID_OR_SHAFT` is doing two
jobs — a real architectural role, and the bucket for "nothing named this".
**UNKNOWN identity must not name a space.** §6 is right, and the fix is a
split, not a threshold.

## A3 · Absent capability 1 — there is no interior/exterior model

DR-002's drawn lines bound **one connected component of 1,130 m²**, and all
four released polygons sit inside it. Across all nine regions the boundary
authority found **57 BUILDING_ENVELOPE bands and zero SITE_BOUNDARY bands**.

So the 5.616 m² strip was not misclassified as interior. **Nothing in the
engine can currently say "outside the building" at all.** I cannot confirm
from the geometry that the strip is a garden — the drawn lines offer no
evidence either way, which is exactly why §7's classifier has to be built
rather than corrected.

## A4 · Absent capability 2 — "room area" is the only quantity

There is no trade, no finish, no recess and no exclusion concept. Even with
perfect walls the kitchen's 1.05 × 1.50 entrance recess would be lost,
because the engine measures **faces of an arrangement**, and a recess
separated by a door jamb pair is its own face. Recovering the room does not
recover the measurement basis.

## A5 · Absent capability 3 — labels can only split, never group

Round 4's functional zones live INSIDE one face. There is no object that
can say "these three physical spaces are one floor measurement". So
RECEPTION / SALOON / DINING can only ever be separate faces or one
under-segmented blob. **Subdivision and trade-zoning pull in opposite
directions, and round 5 only had the subdividing direction.**

---

# B · Proposed domain model

Three objects, not synonyms, and a fourth that is new in kind.

```
PHYSICAL_SPACE          a bounded piece of the building. Geometry.
  └ FUNCTIONAL_ZONE     what part of it is used for. Semantics.
TRADE_MEASUREMENT_ZONE  what one trade measures. Commerce.
```

A trade zone may contain **several physical spaces**; a physical space may
belong to a **different trade zone per trade**; and the grouping for
FLOOR_FINISH is not the grouping for BLOCKWORK.

## B1 · `TradeMeasurementZone` (new — `engine/trade_zone.py`)

```
zone_id · trade · rule_id · geometry (polygon or multipolygon)
included_physical_spaces[] · included_functional_zones[]
exclusions[]            columns, shafts, voids, stairs, ducts
measurement_basis       e.g. FLOOR_AREA_INSIDE_FINISHED_FACES
provenance[]            every space, opening and rule that built it
release_status          per trade, never a global boolean
MEASURED_NET_QUANTITY   unit, value, and what it is measured between
PROCUREMENT_QUANTITY    net x an APPROVED waste factor, or NOT_ESTABLISHED
CONTRACTOR_QUANTITY     by a contractor measurement rule, or NOT_ESTABLISHED
```

§8's separation is structural: `PROCUREMENT_QUANTITY` and
`CONTRACTOR_QUANTITY` are **absent unless a project or user rule supplies
the factor**. No waste factor is ever inferred, defaulted or guessed, and a
missing rule produces `NOT_ESTABLISHED` rather than the net figure wearing
a different name.

## B2 · `SpaceRole` (new — `engine/space_role.py`) supersedes the default

Every role requires POSITIVE evidence; the default is unresolved:

```
INTERIOR_SPACE_UNCLASSIFIED   bounded, inside the envelope, nothing else said
SPACE_ROLE_UNRESOLVED         not even that is established
INTERIOR_ROOM · CIRCULATION · WET_ROOM
EXTERIOR · COURTYARD · GARDEN · ROOF · TERRACE
VOID · SHAFT · DUCT
```

`VOID` and `SHAFT` become **claims needing evidence** — enclosed on all
sides with no door on any boundary, repeated at the same coordinates across
drawing regions (a shaft runs through floors), or a semantic observation.
"No label inside" stops being evidence of anything.

## B3 · `InteriorExterior` (new — `engine/interior_exterior.py`)

§7's evidence, each recorded separately and none decisive alone:

```
ENVELOPE_CONTAINMENT     inside the ring the authority calls the envelope
EXTERIOR_ADJACENCY       shares a boundary with unbounded outside space
DOOR_CONNECTIVITY        reachable from an interior space through a portal
WALL_TOPOLOGY            bounded by envelope bands rather than partitions
SITE_RELATIONSHIP        between the site boundary and the envelope
SEMANTIC_OBSERVATION     a GARDEN / TERRACE / COURTYARD label inside it
ROOF_RELATIONSHIP        repeated footprint with no floor below
```

**No area rule.** A 5 m² strip and a 500 m² strip are classified the same
way. The 5.616 m² polygon must come out EXTERIOR or UNRESOLVED from this
model or from none — never from a size.

This needs the envelope to exist first, and on P7757 it does not. So B3's
first job is to make `boundary_authority`'s envelope usable **per region**
including where the site ring is broken by a gate.

## B4 · `WallPairing` — the fix for defect 1

The current question is pairwise: "are these two lines a wall?" The correct
question is a **global assignment**:

```
EACH DRAWN FACE LINE BELONGS TO AT MOST ONE WALL.
```

with the partner chosen by mutual agreement and by the drawing's own
repeated thicknesses. A simulation on the frozen state, read-only:

```
bands as frozen                     3272
bands under mutual-nearest only       272
thickness under mutual-nearest   50:155  75:44  200:28  150:22  ...
```

Mutual-nearest alone is not enough — it pairs a wall face with the 50 mm
finish line beside it rather than the far face 200 mm away. So the rule has
two parts, both generic:

1. **Learn the drawing's wall thicknesses.** A plan repeats a small number
   of them. The profile already observes a source this way for layers; the
   same machinery reports the modes, with their support, as an OBSERVATION
   about this source and never as a constant.
2. **Assign globally**: each line takes at most one partner, preferring a
   separation at an observed mode, then mutual agreement, then overlap.

A line that ends up in no wall stays a line, as it does today. Bands that
lose their partner simply stop generating phantom recoveries.

**This is the benchmark-informed change with the widest blast radius, and
it is disclosed as such.** What the benchmark told me is that four polygons
were wrong; what it did not tell me is any threshold, coordinate or
thickness. The 50 mm and 600 mm ends of the band stay exactly where round 1
put them.

## B5 · `FloorFinishZone` (new — `engine/floor_finish.py`)

FLOOR_FINISH is the only trade implemented in round 6.

1. Build the **material-bounded** arrangement: drawn wall bands only. **No
   recovered partition lines and no portal closures** — a floor runs
   through a doorway, so the subdivision machinery is the wrong input.
2. Faces of that arrangement are floor pieces.
3. **Merge** two adjacent pieces into one zone when they are connected
   (an opening, or no barrier at all) AND no finish-change evidence lies on
   the frontier.
4. **Recesses come back for free**: a piece separated from a room only by a
   wall return, with no partition between them, is the same floor. This is
   the kitchen's 1.05 × 1.50, and it needs no label and no special case.
5. **Exclusions** subtract: columns (round 5 already observes 235 of them),
   shafts, voids, stairs.

### The honest limit of step 3

P7757 currently offers **no finish evidence at all**. The adapter carries
hatches as entities with no geometry, and layer names may not be an
authority. So a round-6 floor zone built by merging across openings is
`FINISH_CONTINUITY_NOT_ESTABLISHED` and **diagnostic, not released**, until
a finish source exists. Proposed sources, in order of preference:

```
HATCH_GEOMETRY        decode hatch boundaries and patterns (adapter work)
FINISH_SCHEDULE       a schedule or legend in the drawing set
USER_DECLARED_RULE    the project states which zones take which finish
```

`USER_DECLARED_RULE` is the same category as the waste factor: a project
rule, supplied by a human, never inferred. It is also the fastest path to a
real quantity, and I would propose it as the first one built.

## B6 · Release classes extend, they do not change

Round 5's five stay exactly as they are. Round 6 adds one per trade:

```
AREA_GEOMETRY_RELEASE · ROOM_TOPOLOGY_RELEASE · IDENTITY_RELEASE
MATERIAL_WALL_RELEASE · OPENING_RELEASE          (round 5, unchanged)
FLOOR_FINISH_ZONE_RELEASE                        (round 6)
```

§9 is preserved structurally: a FLOOR_FINISH zone can be released while
`MATERIAL_WALL_RELEASE` stays NO, because the floor is bounded by drawn
material even where a wall's second face was only recovered.

---

# C · Modules affected

## C1 · Frozen — not edited, by rule

```
cad_adapter · space_enclosure · enclosure_role · boundary_authority
identity_reconcile · architectural_ontology · semantic_seed
cad_openings · portal_match · drawing_region · cad_profile
cad_fixtures · round2/3/4/5_fixtures · round2/3/4/5_selftest
```

`enclosure_role` is the round-2 safety gate and it **keeps firing exactly
as it does now**. `space_role` runs beside it and downstream of it: a space
that `enclosure_role` refuses still cannot release as a room. Round 6 can
only ever be more conservative than round 2 about room release.

## C2 · Edited

| module | change | consequence |
|---|---|---|
| `physical_wall.py` | global one-line-one-wall assignment; observed thickness modes | `PHYSICAL_WALL_BAND_HASH` changes → round-5 **replay** diverges |
| `partition_continuity.py` | unchanged rules; add "no opening on this boundary" as a DIAGNOSTIC, never a gate | `PARTITION_CONTINUITY_HASH` changes only if the record changes |
| `room_partition_graph.py` | also emit the material-only arrangement for trade zoning | `ROOM_PARTITION_GRAPH_HASH` changes |
| `cad_measure.py` | orchestration; attach space roles and trade zones | no hash of its own |
| `tools/run_cad_pipeline.py` | round-6 sections and freeze | — |

## C3 · New

```
engine/space_role.py            B2
engine/interior_exterior.py     B3
engine/trade_zone.py            B1
engine/floor_finish.py          B5
engine/boq_quantity.py          §8's three layers
engine/round6_fixtures.py       D
engine/round6_selftest.py       D
engine/supervised_benchmark.py  §10
tools/run_supervised_benchmark.py
```

---

# D · Synthetic tests

§11's thirteen, plus five generalisation guards the root cause demands.

```
A rectangular kitchen plus entrance recess     -> ONE floor zone, recess in
B L-shaped tileable room                       -> one zone, correct area
C open Salon+Dining+Reception, no walls        -> one floor zone, 3 zones
D same labels WITH separating walls            -> three floor zones
E wet room adjacent to an open hall            -> separate zone at the door
F exterior garden strip inside the site        -> EXTERIOR, no floor zone
G unknown interior room                        -> INTERIOR_SPACE_UNCLASSIFIED
H an actual shaft                              -> SHAFT, on evidence
I an actual void                               -> VOID, on evidence
J stair in an otherwise tileable hall          -> excluded from the zone
K two zones sharing one finish                 -> one zone
L two adjacent spaces, different finishes      -> two zones
M unreadable identity, valid floor geometry    -> measured, identity UNKNOWN

N a 50 mm double line beside a wall            -> NOT a wall band
O one face line offered to three partners      -> belongs to ONE wall
P a room with no opening on its boundary       -> flagged, releases nothing
   on that basis alone
Q no waste factor supplied                     -> PROCUREMENT NOT_ESTABLISHED
R a drawing whose walls are 300 mm throughout  -> modes learned, not assumed
```

Required results, checked on every case:

```
UNKNOWN is never VOID
a semantic label never creates or moves a floor boundary
exterior geometry never becomes interior floor quantity
a legitimate recess is never lost
open-plan same-finish areas group; actual walls still split
no waste factor is ever invented
one drawn line never belongs to two walls
```

---

# E · Migration path

## E1 · What must not move, and how it is protected

```
rounds 1-5 HISTORICAL_ARTIFACT_HASH      never recomputed, never rewritten
rounds 2-5 synthetic PASS/FAIL           must stay 12/12, 16/16, 22/22, 23/23
round-5 benchmark export                 already written and hashed
```

The pass/fail score is the score. Round 5 §0 settled the rest: editing
`physical_wall` changes what a replay of round 5's self-test computes,
which is a `CURRENT_REPLAY_HASH` divergence — a fact about the code's
history, recorded in `freeze_manifest`, and not a change to any freeze.

Three concrete steps:

1. **Add round 5 to `freeze_manifest.ROUNDS`** before any edit, with its
   artefact hash, code hashes and the export manifest hash. It currently
   covers rounds 1–4 only.
2. **Record the expected divergences** — `PHYSICAL_WALL_BAND_HASH`,
   `ROUND_5_SYNTHETIC_HASH`, `ROOM_PARTITION_GRAPH_HASH` — as predicted, so
   an unexpected one is visible.
3. **The round-5 export can no longer be regenerated once round 6 lands.**
   The export tool's hash gate will refuse, which is correct behaviour and
   is the reason it was exported and hashed first.

## E2 · Three scoreboards, never mixed (§13)

```
docs/PROJECT_2_CAD_ROUND[1-5]*.md   historical blind predictions. Read-only
docs/PROJECT_2_SUPERVISED_*.md      P7757 as a development set
engine/round[2-6]_selftest.py       synthetic generalisation
```

`engine/supervised_benchmark.py` holds the disclosed P7757 truths as
labelled training examples with, for each: before, after, reason, rule
changed, which example motivated it, and which synthetic test protects the
generalisation. **A synthetic test may never be weakened to make a
supervised example pass.**

## E3 · Order of work

```
1  freeze manifest gains round 5                      no behaviour change
2  round-6 synthetics A-R, written to FAIL first      the spec, executable
3  space_role + interior_exterior                     fixes A2 and A3
4  physical_wall global assignment                    fixes A1
5  trade_zone + floor_finish + boq_quantity           fixes A4 and A5
6  supervised benchmark harness                       §10
7  P7757 rerun, three scoreboards reported apart      §13
```

Steps 3 and 4 are separable on purpose: 3 is safe and narrow, 4 is the
wide one, and running P7757 between them tells us how much of the damage
was the role classifier and how much was the pairing.

---

## Benchmark-informed disclosure

Everything in this document was written after being told the four releases
are wrong. What the benchmark supplied is **that they are wrong and in
which direction**. What it did not supply, and what does not appear here:
no coordinate, no expected area, no room-size range, no target total, no
thickness, and no tolerance. The one quantitative thing the benchmark
changed is the direction of the enquiry — from "why did nothing release" to
"why did these four release" — and that question is what found 713 lines
belonging to more than one wall.

§13's goal is taken as written: not 9.675, but a measurement basis that
would produce it on any drawing. **The design is complete and nothing is
implemented. Awaiting approval before step 1.**
