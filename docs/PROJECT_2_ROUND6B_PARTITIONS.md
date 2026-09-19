# PROJECT 2 — ROUND 6B: SINGLE-LINE PARTITIONS AND GEOMETRY COVERAGE

**Geometry only.** No TradeMeasurementZone, no floor ceramic, no wall
ceramic, no waste, no pricing, no BOQ export. The kitchen's 1.05 × 1.50
recess is still not merged.

Round 6A (`b646fb6`) is preserved and is now a Freeze in the manifest,
`ROUND_6A_WALL_FACE_OWNERSHIP`.

---

## 1 · FIRST, A CORRECTION TO WHAT I TOLD YOU

Round 6A's report said the 34 unresolved polygons were dominated by
single unpaired partition lines. Measured properly, that was an
over-generalisation. The actual distribution of the 117 unattributed
sides was:

```
70   a line round 6A set aside as standing inside a space
47   nothing drawn there at all
```

and by polygon:

```
 7   whole-drawing faces of 50-1,072 m2 — not rooms at all
27   rooms with a handful of unattributed sides
     of which 6 were ONE side short, four of those by a 50 mm stub
```

So round 6B had two jobs, not one: the single-line partition (§2–§6), and
the corner stub where a wall's two runs do not quite meet.

---

## 2 · THE ONTOLOGY (§1)

One drawn line, three questions that are **not** the same question:

```
TOPOLOGY_AUTHORITY        are these two spaces separate?
CLEAR_FACE_AUTHORITY      where exactly does each room's floor stop?
MATERIAL_WALL_AUTHORITY   how much blockwork, plaster, paint is there?
```

`POSITIVE_EVIDENCE_SINGLE_LINE_PARTITION_V1` answers all three separately
and returns one of §4's three results, never collapsed:

| | topology | clear face | material |
|---|---|---|---|
| **A** | established | established | **NOT** |
| **B** | established | **NOT** | **NOT** |
| **C** | unresolved | — | — |

**A SECOND WALL FACE IS NEVER INVENTED.** Where the thickness is unknown
the answer is that it is unknown; the centreline is not substituted,
because half of an unknown number is still unknown. A test asserts the
module's code contains no `/ 2`, no `* 0.5` and no "centre".

## 3 · POSITIVE EVIDENCE (§3), AND WHY WALL-TO-WALL IS NOT ENOUGH

```
STRONG       an opening hosted on it or aligned with it
             the same line on another plan (region-local, never absolute)
             it continues an established partition's alignment
             it separates two independently supported space observations
SUPPORTING   both ends meet an established wall band
             one end meets an established wall band
             another line meets it at a T or L junction
             an authored dimension ends on it
```

A partition needs **one strong token and two in total**. Dividing a region
is not evidence of being a partition — that is circular, and it would turn
every dimension line, hatch boundary and worktop into blockwork.

**Running from wall to wall is SUPPORTING, not strong.** A worktop is
fitted between two walls; so is a wardrobe and so is a bath. The first
version of this module had it as strong, and P7757's kitchen counter came
straight back as a partition, undoing round 6A. Synthetic case C now holds
that line.

Two other defects the twelve cases caught before P7757 did:

- **"Separates two observations" was asking the wrong question.** It
  compared half-planes: anything named anywhere to the west, anything
  named anywhere to the east. That is true of every line in a building.
  Each side now reaches only as far as the next parallel line the drawing
  puts there — a worktop has nothing named in its 500 mm.
- **A crossing wall was counting as a reveal.** `_capped` accepted any
  perpendicular line spanning the band, so a worktop between two walls was
  "closed at both ends" by those walls and outranked the wall it stands
  against. A reveal spans the band **and stops**; a wall's face runs on
  past it.

And one thing the cases required that P7757 alone would not have shown: a
partition with a door in it is drawn as **two pieces**, and neither piece
has a room on each side of it. Collinear pieces are now merged into one
run across a gap that an opening on that very line explains — and only
such a gap. The doorway inside an established run is then closed by a
`PORTAL-` candidate carrying zero material, or the flood walks through it
and the two rooms are measured as one.

## 4 · THE CLEAR FACE (§5)

A topology-only partition does **not** release an area. The face is taken
only from evidence outside the line itself:

```
FACE_FROM_A_CONTINUING_BAND   the line is collinear with an established
                              band's face that runs on past it
FACE_FROM_A_JAMB              an opening drawn in it names two faces, so
                              the architect has stated its construction
FACE_FROM_A_DIMENSION         an authored dimension ends on it
```

The jamb rule is what turned this round from a net loss into a net gain:
before it, 33 of 69 polygons released; after it, **40 of 69**.

## 5 · THE MATERIAL RULE (§6) — MANDATORY, AND NOT A THRESHOLD

Every candidate carries `MATERIAL_WALL_NOT_ESTABLISHED`. It is not a bar
that could be cleared: a line has no thickness. Every millimetre of a
space's boundary held by a partition is reported as
`SINGLE_LINE_PARTITION_LENGTH_MM` and subtracted from
`MATERIAL_AUTHORITY_ESTABLISHED_LENGTH_MM`, exactly as an opening and a
recovered span are.

On P7757: **213.4 m of boundary is held by single-line partitions and
contributes 0 m of measurable material.** No blockwork, plaster, paint,
wall ceramic or waterproofing can come from any of it.

## 6 · THE CORNER RETURN

Separately from partitions: a side no longer than the thinnest wall this
project recognises, collinear with a face of a band **already bounding
this space**, is that band's own corner return — where the wall turns,
not an unaccounted side. It asserts no new geometry; the polygon is
unchanged and one side is named. This is what released the four spaces
that were one 50 mm stub short, the WASH among them.

---

## 7 · SYNTHETIC CASES (§7), FROZEN BEFORE THE RERUN

Twelve, all holding. `ROUND_6B_SYNTHETIC_HASH 1010b2585e3d77fe4faa4c16`.

```
A  one partition line between two walls               established
B  a single line at a T junction                      established
C  a worktop that looks like a partition              REFUSED
D  a dimension line crossing a room                   REFUSED
E  a single partition with a door in it               established, 2 spaces
F  a single line continuing a 200 mm wall             clear face established
G  an isolated decorative line                        REFUSED
H  topology established, thickness unknown            area NOT released
I  clear face from continuation                       established
J  the same geometry with the evidence removed        REFUSED
K  a topology-only partition makes no material        0 m
L  two rooms separated, neither allowed blockwork     0 m
```

Four of the twelve exist to be refused. §6 is checked on **every** case,
including those.

---

## 8 · THE P7757 RERUN (§9)

```
total polygons                              69

MEASUREMENT BASIS
  CLEAR_INTERNAL_FINISH_FACE                40
  CLEAR_FACE_NOT_ESTABLISHED                 3
  MEASUREMENT_BASIS_NOT_ESTABLISHED         26

TOPOLOGY      established 43   unresolved 26
CLEAR FACE    established 40   unresolved 29
MATERIAL      established 42   unresolved 27
IDENTITY      established 10   unresolved 59

INSIDE BUILDING            61
OUTSIDE BUILDING            0
BUILDING RELATIONSHIP UNRESOLVED   8   (the vertical penetrations)

released clear floor area          269.18 m2
topology-established area          292.10 m2
measurable wall material         1,126.8 m
held by single-line partitions     213.4 m  → 0 m of material
held by recovered spans            375.2 m  → 0 m of material
```

**Partition candidates: 784.** 58 reached result A, 117 result B, 609
result C. **Zero** established material authority.

### Reason distribution for every unresolved polygon (29)

```
22  sides nothing accounts for
 4  a whole-drawing face, 200-1,072 m2 — not a room (§8: do not convert it)
 3  a partition of unknown thickness bounds it  (result B, working as designed)
```

### Coverage, against round 6A

| | round 6A | round 6B |
|---|---|---|
| polygons | 70 | 69 |
| clear floor released | 36 | **40** |
| released area | 188.74 m² | **269.18 m²** |
| topology established | 36 | **43** |
| material from partitions | — | **0 m of 213.4 m** |

Released area is up 43%, and material authority did not rise because of
it: every metre a partition holds is subtracted.

---

## 9 · THE THREE REFERENCES (§10) — NO REGRESSION

| | round 6A | **round 6B** | disclosed |
|---|---|---|---|
| KITCHEN main | 8.100 m², 2700 × 3000 | **8.100 m², 2700 × 3000** | 3.00 × 2.70 |
| W.C | 3.375 m², 1500 × 2250 | **3.375 m², 1500 × 2250** | 1.50 × 2.25 |
| WASH | 3.150 m², 1500 × 2100 | **3.150 m², 1500 × 2100** | 1.50 × 2.10 |

All three on `CLEAR_INTERNAL_FINISH_FACE` with every side attributed. The
1.05 × 1.50 kitchen recess is **not** included.

---

## 10 · THE EXPORTS (§11)

`data/runs/7757/round6b_export/`, five exports in CSV and JSON, each
hashed. `ROUND6B_EXPORT_MANIFEST_HASH 4127c38442d48ac1469ed0c0`.

```
P7757_ROUND6B_SPACE_EXPORT       69 rows   35d812744b670b14a348cd97
P7757_ROUND6B_BOUNDARY_EXPORT  5,813 rows   05dceae4a96fc2416825ff7a
P7757_ROUND6B_OPENING_EXPORT     340 rows   7dbba8379a33e8627ceca678
P7757_ROUND6B_IDENTITY_EXPORT     33 rows   684d0634e255c8b1a1814b68
P7757_ROUND6B_DIMENSION_EXPORT   134 rows   addbb42c18d895deeb42b53d
```

The space export carries every column §11 lists, with the three
authorities as three separate columns. `floor` reads
`FLOOR_LEVEL_NOT_ESTABLISHED` on every row: this engine has no floor
model, and saying so is more useful than omitting the column.

**These files are under `data/runs/`, which is gitignored by the standing
rule** — they are derived from the client's drawing and carry room
dimensions. They are produced on disk and not committed.

---

## 11 · WHAT IS STILL NOT RIGHT

**22 polygons still have sides nothing accounts for.** 49 of their
unattributed sides are under 0.5 m — more corner stubs that the return
rule does not reach because the neighbouring band is a different one. The
rest are genuine gaps in the drawing.

**Zero exterior spaces on P7757, still.** No site boundary in any region,
and no measured space falls outside the fabric ring either.

**Identity is established for 10 of 69.** Geometry has outrun naming by a
wide margin, and the SHX-font stamps are the reason.

**609 candidate lines were refused.** Some of those are certainly real
partitions whose evidence this drawing does not carry. They are listed
individually in the export with the evidence each one did have.

---

## 12 · FROZEN THIS ROUND

```
SINGLE_LINE_PARTITION_HASH   2b9480e67e799c2b3d1f837f
ROUND_6B_SYNTHETIC_HASH      1010b2585e3d77fe4faa4c16
ROUND6B_EXPORT_MANIFEST_HASH 4127c38442d48ac1469ed0c0
```

**STOP.** The next operation is the supervised reconciliation of §12 —
round 6B geometry against the drawing and against the human measurement
workbook, which is reference evidence and not absolute truth. The engine
is not altered during that comparison.
