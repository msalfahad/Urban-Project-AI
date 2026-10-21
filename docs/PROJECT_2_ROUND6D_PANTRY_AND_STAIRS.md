# PROJECT 2 — ROUND 6D · TWO GEOMETRY REPAIRS, THE AMERICAN PANTRY, AND THE STAIR

Round 6C's register was exported and frozen before this round changed
anything: `P7757_ROUND6C_EXPORT.tar.gz`, manifest hash
`54003ad29e3863ceaa614c86`, written at commit `b5a2ce1`.

Round 6D does four things and prices none of them.

---

## §7A · A WALL OWNS STRETCHES, NOT THE SPAN BETWEEN THEM

A band used to report the interval from its first millimetre to its last
and claim everything in between — including stretches another wall is
drawn along. A wall now carries three different answers:

```
owned_mm      the stretches of its two lines this wall uses. Taken in
              EVIDENCE ORDER, with every stretch another wall holds
              blocked out. The gap a doorway leaves inside a wall stays
              with it; the wall next door's stretch does not
drawn_mm      where BOTH faces are drawn — where it IS a band
face_stretches(which)
              where THAT face is drawn, within what the wall owns. A
              face running past its partner is still a face, and it is
              the one the room on that side stops at
```

Three readers now ask three different questions, and getting them
crossed cost a room each time:

* **where a face is drawn** → face attribution, the flood, ownership.
  Reading `drawn_mm` here lost the kitchen's south side to a gap.
* **where a band IS a band** → the evidence a single line continues.
  Reading `face_stretches` here dissolved round 6B's cases F and I.
* **which stretches a wall uses** → openings, fittings, the invariant.

**One further defect this uncovered:** `_spans` joined two stretches of
the same coverage into one span — across a hole belonging to another
wall. That is how a wall reported continuous ownership of a line it does
not own, and it is fixed: spans are never joined across a blocked
stretch.

On P7757, with the audit run over every pair on every line:

| | before | after |
|---|---|---|
| two walls owning one stretch of one line | 75 | **0** |
| bands owning several disjoint stretches | — | 98 of 430 |

---

## §7B · A FITTING IS NOT A WALL, AND ITS FRONT FACE IS NOT A ROOM'S EDGE

`engine/fitting_band.py`. A band that shares a face line with another
band, stands on the opposite side of it, and is drawn over a shorter run
is a FITTING: a counter, a run of units, a wardrobe, a duct casing.

```
the SHARED face   is where it meets the wall. A space on that side is
                  bounded by the WALL BEHIND, which draws that line
the FRONT face    stands out into the room. No room ends there
```

A fitting now:

* gives no face to a room's clear internal finish face,
* is not the inside of a wall for the flood,
* **cannot become a single-line partition however much evidence it
  collects.** A counter runs wall to wall, continues an alignment and has
  an opening beside it; every one of those tokens is true of it.

**Which of two stacked bands is the wall is decided on how far each is
DRAWN**, not on how much of the shared line each ended up owning — after
§7A only one of them owns any given stretch of it, and that says nothing
about which is the wall.

Six bands on P7757 are fittings. **No room on the drawing is measured to
a fitting's front face.**

---

## §1–§6 · A PANTRY IS NOT ALWAYS A ROOM

`engine/functional_zone.py`, the layer between a space and a trade:

```
PHYSICAL_SPACE  ->  FUNCTIONAL_ZONE  ->  TRADE_MEASUREMENT_ZONE
                                         (a later round. Not here)
```

A zone creates **no wall, no room and no quantity**. One open space may
hold a saloon zone, a dining zone, an American pantry zone and a
circulation zone with nothing physical between them.

```
CLOSED_PANTRY            four sides of established wall face, sole label
OPEN_AMERICAN_PANTRY     it shares its space with a dining, saloon,
                         living or reception label
PANTRY_OPENNESS_UNKNOWN  a side no wall accounts for, and nothing named
                         beyond it. Open to WHAT, nobody says
```

### Wall tile on an open pantry

Measured on the host wall segments the UNITS stand on. The open edge
toward the dining or living space contributes **zero**, and the zone is
never closed virtually to produce a fourth wall.

```
ONE_WALL  L_SHAPE  U_SHAPE  CLOSED_ON_FOUR_SIDES
```

**Without the units' own geometry the tiled length is NOT ESTABLISHED.**
Which stretch of an open space's perimeter belongs to the pantry is a
question the units answer; the perimeter belongs to the dining room as
much as to the pantry.

**No tile height is ever assumed.** No 3.00 m, no 2.40 m. Without an
owner rule the height — and every area resting on it — is an
`OWNER_RULE_REQUEST`.

### P7757's pantry

```
pantry_openness        PANTRY_OPENNESS_UNKNOWN
exceptions             NO_PHYSICAL_SPACE_CARRIES_THIS_PANTRY_LABEL
                       WALL_TILE_LENGTH_NOT_ESTABLISHED
                       OWNER_RULE_REQUEST
wall_tile_height_m     null          height_source  OWNER_RULE_REQUEST
```

The PANTRY label still resolves to no physical space: the 0.90 × 2.50 m
strip is gone (it is now 2.7 m² with its clear face not established, and
it releases nothing), and no larger room has formed around the label.
Per §4 that is no longer counted as a geometry failure — but the label
is carried into the report as a pantry question rather than dropped,
because leaving it out would make the hardest case the invisible one.

---

## §8–§14 · THE STAIR

`engine/stair_assembly.py`. A stair is not a room-floor polygon:

```
STAIR_ASSEMBLY -> STAIR_FLIGHT -> STAIR_TREAD / STAIR_RISER
               -> STAIR_LANDING
```

and five quantities that are never added to one another:

```
TREAD_M2   every tread measured from ITS OWN polygon
RISER_M2   width by height — and a plan carries no height
LANDING_M2 what the flights leave between them
NOSING_LM  the exposed front edges
STAIR_SKIRTING_LM   separately again, where the drawing establishes it
```

### What a run of parallel lines has to have

A stair in plan is a run of parallel lines at a tread's going. So is a
louvre, a grating and a run of shelving, so a run becomes a stair only
with evidence around it: the cell it stands in, or a stair label. Four
rules the P7757 run forced, all stated as shares or as the module's own
figures:

* **A STAIR FILLS ITS CELL.** A run covering less than a quarter of the
  cell it stands in, with no stair label, is refused. Without this a
  0.29 m² patch of hatching in a 1,020 m² plate was a staircase.
* **TWO LINES LESS THAN A GOING APART ARE ONE STEP'S EDGE.** A stair is
  often drawn with a nosing line in front of each riser line; read as
  two tracks it becomes two overlapping flights measuring the same
  marble twice.
* **A WALK IS CUT WHERE THE SPANS JUMP.** A room's own wall sits a going
  away from the first tread and joins the walk. A tread does not reach
  past its neighbour by more than a going.
* **RUNS IN ONE CELL ARE FLIGHTS OF ONE STAIR.** Two flights and a
  landing are one staircase, not two.

### What a plan cannot say

`RISER_QUANTITY_NOT_ESTABLISHED` on every riser of every stair on P7757:
no section was supplied, and **no standard rise is borrowed from
anywhere**. Neither `treads = risers` nor `treads = risers - 1` appears
in this engine.

Where two flights of one stair overlap, their treads cannot both be
marble and neither is chosen: `TREAD_QUANTITY_NOT_ESTABLISHED`, and the
total is reported as `null` with the established assemblies totalled
separately.

### P7757's stairs

| | |
|---|---|
| assemblies | 2 |
| flights | 3 |
| treads | 10 |
| risers | 10, all NOT ESTABLISHED |
| runs refused as not a stair | 140 |

```
SA-DR-001-001  U_SHAPED   footprint 2.0511 m2   TREAD_M2 null
               FLIGHTS_OF_ONE_STAIR_OVERLAP_EACH_OTHER
SA-DR-002-002  STRAIGHT   footprint 3.9200 m2   TREAD_M2 3.2854
               4 treads, 2.800 m wide, NOSING_LM 11.200
```

`STAIR FINISH = MARBLE, SURROUNDING FLOOR = PORCELAIN` is carried as
`P7757`'s **project rule**, on the report and not in the engine.

**No released room shares a square metre with a stair footprint: 0.**

---

## §17C · WHAT CHANGED IN THE REGISTER

| | round 6C | round 6D |
|---|---|---|
| MEASURED_CANDIDATE_AREA | 269.1838 m² (40) | 279.7944 m² (43) |
| RELEASE_ELIGIBLE_GEOMETRY | 26.3085 m² (6) | **26.3085 m² (6)** |
| UNRESOLVED candidates | 17 | 12 |
| labels mapped exactly once | 14 | 16 |

All six protected geometries HELD: KITCHEN 8.1000, DRIVER 7.8750, W.C
3.3750 / 2.3625 / 1.9500 and the first-floor W.C 2.6460.

### The four false negatives

| audit m² | round 6C | round 6D |
|---|---|---|
| 4.7250 | FALSE_NEGATIVE_RELEASE_GATE | FALSE_NEGATIVE_RELEASE_GATE |
| 5.0225 | FALSE_NEGATIVE_RELEASE_GATE | FALSE_NEGATIVE_RELEASE_GATE |
| 19.3500 | CORRECTLY_BLOCKED | **NOT_PRESENT_AS_A_CANDIDATE** |
| 5.5500 | CORRECTLY_BLOCKED | CORRECTLY_BLOCKED |

The roof polygon of 19.35 m² no longer forms at all. It never had an
established basis, so nothing that was releasable has been lost — but it
is a candidate fewer, and it is named here rather than left to be
noticed.

---

## §15 AND §16 · NINETEEN DRAWINGS, FROZEN BEFORE THE RERUN

```
PA closed pantry, four walls        SA straight single flight
PB open to the dining               SB two flights and a landing
PC a recess of the saloon           SC a U-shaped stair
PD an island, and no wall at it     SD an L-shaped stair
PE a counter against a wall         SE a winder of wedges
PF a counter against nothing        SF unequal tread polygons
PG a label in the counter           SG a stair beside a floor
PH openness that is unknown         SH no vertical information
PI the tiled shape from the units   SI plan and section disagree
                                    SJ decorative parallel lines
```

Five requirements are checked on every one of them: a zone creates no
wall; a fitting gives no room its clear face; a riser without a section
is NOT ESTABLISHED; m² and lm are never added; and **no released room
polygon overlaps a stair's footprint.**

All nineteen pass. Six failed on the first run, and the fixes they
forced are §7A's reader split, the stair-cell share, the nosing-line
merge and the overlapping-flight refusal.

---

## FROZEN THIS ROUND

```
PHYSICAL_WALL_BAND_HASH      8f17f155ca66db3f7970a5c4
WALL_FACE_OWNERSHIP_HASH     bc0eac5502ad84c53f8f2e13
SINGLE_LINE_PARTITION_HASH   1cdfe19e3fc2ff912a78d952
FITTING_BAND_HASH            cc45efc4267d957cba16e0f5
FUNCTIONAL_ZONE_HASH         8fe062953599bfa5d748ccb1
STAIR_ASSEMBLY_HASH          6d1282d8790ee49b06c97cae
ROUND_6D_SYNTHETIC_HASH      6ed47af8801d63e97e73778d
```

**The three geometry modules had their MODEL names bumped on purpose.**
Their hashes are computed from the model's vocabulary, not from its
code, so round 6D's behaviour changed while the hashes would not have —
and a replay that matches while the numbers move is worse than useless.
Rounds 6A, 6B and 6C now replay as `REPLAY_DIVERGED_UNDER_LATER_CODE`
with the reason recorded against each, and every one of their CASES
still passes.

---

## WHAT IS STILL NOT RIGHT

**One stair measures more tread than it covers** — DR-001's two flights
overlap, so its tread quantity is refused rather than reported. The
underlying question is whether those two tracks are one curved flight.

**No riser anywhere is established.** Section evidence has never been
supplied to this engine, and the architectural plan does not carry it.

**The pantry label still names no space.** §4 withdrew the requirement
that it should, and the strip it used to name is gone.

**The 19.35 m² roof candidate no longer forms.**

---

**STOP.** No TradeMeasurementZone engine, no floor ceramic, no wall
ceramic, no waste rule, no pricing, no contractor rates and no
Manager/Firebase integration, until physical-space completeness, the
American-pantry interpretation, the stair geometry and the marble/
porcelain separation have been independently reviewed.
