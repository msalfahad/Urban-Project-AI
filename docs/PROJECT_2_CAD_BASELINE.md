# Project 2 — CAD normalization and the frozen P7757 baseline

This is a **CAD-source generalisation test**. It is not evidence that the
vector-PDF pipeline generalises; the raster-PDF result stays frozen and
historical in `docs/PROJECT_2_RESULT.md`.

```
PROJECT_2_CAD_BASELINE_HASH      3edf12c66f0984330d77e248
```

**The headline, stated before the detail: the engine now READS authored CAD
correctly and does NOT yet MEASURE P7757 correctly.** 48 space candidates,
2 enclosed, and both of those two are the plot rather than the room. The
machinery is sound on synthetic rooms and the failure is localisation. Both
causes are named in §I and §K and neither was tuned away.

---

## A · Synthetic CADAdapter results and freeze hashes

```
CAD_ADAPTER_HASH          bd331c8074806e8b19711417
CAD_FIXTURE_FREEZE_HASH   b0bf6a13f057aa1578262e3c
CAD_NORMALIZATION_HASH    72bdb0a2bbb65c3c4c0e8ea6   (P7757's own output)
REGION_FREEZE_HASH        (engine.cad_regions.freeze_hash)
ENCLOSURE_FREEZE_HASH     01ff128e7ffdab820805dce1   unchanged
fixtures                  29 built by hand, 29 passing
tests                     29 fixtures + 12 profile/measure + 11 audit = 52
```

Every fixture is a LibreDWG-JSON-shaped decode, so the adapter under test is
the production path. Coverage: LINE, LWPOLYLINE (open, closed, bulged), ARC,
CIRCLE, HATCH, TEXT, MTEXT, DIMENSION_LINEAR (plain, DIMLFAC, author-
overridden), INSUNITS 0 and 4, INSERT (plain, translated, rotated, scaled,
scaled-then-rotated-then-moved, nested), block-defined-but-never-placed,
door block with two placements, room-name block, wall as two lines, mixed
wall thickness, doorway interruption, column inside room, unrelated
annotation geometry, two drawing areas in one model space.

### The four defects the fixtures caught before the client's drawing could

1. **A polyline's four sides all inherited the parent handle**, so one id
   named four different wall faces. Fixed with a part id derived from the
   span's own *local* coordinates — intrinsic, so a reordered vertex list
   still yields the same ids. ORDER IS NEVER IDENTITY applies to a part as
   much as to a whole.
2. **Paper-space geometry was normalized with model space.** Paper space
   has its own coordinate system near the origin; mixing them inflated the
   extent by 600 m on Y and would have put a title block inside a room.
3. **Block delimiters and custom-class entities fell through to
   `unhandled`**, where 68,139 of them would have drowned out anything
   genuinely surprising.
4. **`BLOCK_HEADER.entities` is wrong on this decoder.** For block `SAL` it
   names the block's own BEGIN and END delimiters instead of its two text
   entities. Trusting it produced **3** text observations from a drawing
   carrying 39, and every room-name stamp vanished. Ownership runs the
   other way and is reliable: inverting `ownerhandle` gives 152 entities
   across 31 definitions, and `SAL` comes back holding exactly `SALOON` and
   its Arabic counterpart. The fixture builder now reproduces the
   **defective list and the correct ownership together**, so an adapter
   that trusts the list fails on a synthetic case.

---

## B · Decoder and provenance architecture

```
DECODER          GNU LibreDWG 0.13.3, built from source in this container
INVOCATION       dwgread -O JSON -o <out> <dwg>
DECODE RESULT    SUCCESS   (its DXF writer aborts inside BLOCKS - not used)
SOURCE           P7757_ARCHITECTURAL.dwg   7f61f3acdd62d62d   2,655,476 B
DECODE JSON      51,902,848 B              c742657fab496d55
NORMALIZED       CAD_NORMALIZATION_HASH    72bdb0a2bbb65c3c4c0e8ea6
```

No DWG binary parser was written. When no decoder is found the run stops
with **`NO_DWG_CONVERTER_AVAILABLE`** and every metric `NOT_ESTABLISHED` —
never an empty drawing. A `/tmp` build path is deliberately *not* a default:
the decoder is named by `--converter`, `$URBAN_DWG_DECODER` or `PATH`, so a
run that works because of an ephemeral build says so.

Every normalized object carries `dwg_handle`, `entity_type`, `layer`,
`block_path`, `instance_path`, `part` and `source_sha256_16`. The
`object_id` is built from the handle and its instance lineage, never from a
list position, and the normalization hash is computed over **sorted** rows
so a re-decode in another order yields the same hash.

### Two decoder limits, recorded rather than worked around

| limit | effect |
|---|---|
| **MTEXT content does not survive** — 389 entities, **0** strings | dimension text and some notes are unreadable through this decoder |
| **Arabic TEXT in SHX fonts returns mojibake** — `RaL‘n`, `M—HAe` | Arabic room names unusable; the English half of each stamp survives |

Neither is a property of the drawing. Both would be resolved by a different
decoder or by the DWF's W2D streams.

---

## C · P7757 source profile

`SOURCE_PROFILE_HASH 483314a55f04932564a9bac6`

No layer or block **name** influenced any proposal. A layer is proposed
wall-like when a **majority** of its axis-aligned length runs as one side of
a parallel pair 50–600 mm apart — the structural signature of a wall drawn
as two faces. The band comes from construction (thinner than 50 mm is not
built; thicker than 600 mm is a retaining wall or shaft), and "majority" is
an argument rather than a tuned fraction.

| layer | entities | axis length m | paired m | share | proposed role | status |
|---|---|---|---|---|---|---|
| **1** | 1342 | 2078.5 | 1051.1 | **0.51** | WALL_LIKE_PAIRED_FACES | PROPOSED |
| **2** | 254 | 293.2 | 209.0 | **0.71** | WALL_LIKE_PAIRED_FACES | PROPOSED |
| **5** | 999 | 1116.5 | 791.2 | **0.71** | WALL_LIKE_PAIRED_FACES | PROPOSED |
| **W** | 2446 | 581.8 | 385.1 | **0.66** | WALL_LIKE_PAIRED_FACES | PROPOSED |
| 4 | 1231 | 688.5 | 28.6 | 0.04 | DIMENSION_BEARING | OBSERVED |
| 3 | 28 | 0.0 | — | — | FILLED_REGION_BEARING | OBSERVED |
| S-COL.BON | 469 | 236.2 | 97.5 | 0.41 | LINEWORK_ROLE_UNRESOLVED | UNRESOLVED |
| D | 482 | 143.9 | 49.2 | 0.34 | LINEWORK_ROLE_UNRESOLVED | UNRESOLVED |
| 0 · LEVEL · ST · TEXT · TOI | 1694·145·32·120·215 | — | — | 0.00 | UNRESOLVED | UNRESOLVED |

**The result the name would have hidden: four layers pass the structural
test, not one.** And `W`'s commonest face separations are **80 mm and
63.2 mm**, which are less wall-like than layer 2's and layer 5's clean
**300 mm and 600 mm**. Had I written `if layer == "W": wall`, the engine
would have used the *least* convincing of the four.

Blocks are observations too. `D115` `D120` `D200` `D315` `d220` `arch120`
are recorded as `ARC_AND_LINE_SYMBOL` — "definition combines an arc with
straight linework, the shape of a leaf-and-swing door symbol, an
observation about its geometry, not an identification". `SAL` `kit` `din`
`WC` `WASH` `MB` `PAN` `GAR` `SWIM` `rec` `cou` `dwa` `DRI` are
`LABEL_BEARING_SYMBOL` with the text they carry. A block named `WC` is a
block named `WC`.

---

## D · Automatic drawing / floor localisation

**No clustering distance was chosen.** The sweep runs a fixed ladder from
100 mm to 102.4 m and reports where the partition is *stable*, because a
partition surviving a range of thresholds is a property of the drawing and
one appearing at a single threshold is a property of the threshold.

```
distance mm    100  200  400  800 1600 3200 6400 12800 25600 51200 102400
major regions   10    9   14   14   13    5    5     4     3     2      2
```

| plateau | major regions | stable across | octaves |
|---|---|---|---|
| fine | **14** | 400 – 800 mm | 1.0 |
| middle | 5 | 3200 – 6400 mm | 1.0 |
| coarse | 2 | 51200 – 102400 mm | 1.0 |

The finest stable partition is reported, because two sheets merged into one
region cannot be separated later while two halves of one sheet stay visible
as neighbours. Its five substantial regions:

| region | marks | size mm | dimensions | texts | dominant layers |
|---|---|---|---|---|---|
| REG-400-001 | 2660 | 18898 × 16709 | 49 | 0 | W, 1, 5 |
| REG-400-002 | 1856 | 34715 × 16059 | 118 | 59 | 4, 0, D |
| REG-400-003 | 1552 | 19416 × 17679 | 51 | 0 | W, 1, 5 |
| REG-400-004 | 1429 | 33270 × 15160 | 121 | 14 | 4, 0, D |
| REG-400-006 | 655 | 31530 × 15080 | 50 | 14 | 4, 5, 0 |

**GROUND / FIRST / SECOND FLOOR were NOT identified.** The evidence that
would name them is the sheet title, and **MTEXT content does not survive
this decoder** — so the title text is absent. Assigning floors from
position, size or ordering would be a guess dressed as a finding, and the
regions are returned as candidates with their evidence instead. `$EXTMIN`
and `$EXTMAX` in the header also disagree with the computed geometry extent
by 600 m on Y: the header's saved view is stale and the geometry is the
authority.

---

## E–F · Room/space table, areas, perimeters, dimensions

48 space candidates, each seeded from a **room-name block instance** — a
point the architect placed inside the room it names. Loose text is not used:
a street name or a level mark would seed the wrong space.

| | |
|---|---|
| space candidates | **48** |
| enclosed (complete) | **2** |
| partial | 0 |
| unresolved | **46** |
| identity established from authored text | **15** |
| identity ambiguous | 33 |
| wall-face candidates fed to the enclosure | from layers 1, 2, 5, W |

The identities the authored text does establish: `SALOON`, `RECEPTION`,
`DEWANEYA`, `KITCHEN`, `DINING`, `PANTRY`, `DRIVER`, `MASTER BED ROOM`,
`W.C` ×3, `Wash` ×2, `COURT` ×2, `GARDEN`, `swimming pool`. That is real
room identity from the drawing itself, where AR-00 needed 144 vision calls.

**Only two spaces produced an area, and both are wrong:**

| space | label | area m² | perimeter m | principal dims mm | support |
|---|---|---|---|---|---|
| CADSP-012 | W.C | 205.910 | 140.714 | 20770 × 13300 | 100% |
| CADSP-014 | W.C | 443.841 | 223.169 | **31370 × 15000** | 100% |

`31370 × 15000` is **the plot**. `31.37` and `15.00` are the plot dimensions
printed on the sheet. The flood escaped the washroom, ran through the
building and was stopped by the site boundary — which is fully drawn, hence
100% vector support. **These are geometrically valid enclosures of the wrong
thing.**

---

## G · CAD dimension cross-check

Geometry was measured first and compared second, with the three values kept
apart throughout and never averaged:

```
GEOMETRY_MEASURED_VALUE_MM      from the extension-line origins
DIMENSION_DISPLAY_VALUE         the number printed, in centimetres here
DIMENSION_NORMALIZED_VALUE_MM   display / DIMLFAC, for comparison
INSUNITS = 4 (mm)   DIMLFAC = 0.1
```

| verdict | count |
|---|---|
| AGREE | 0 |
| DISAGREE | 0 |
| AMBIGUOUS | 0 |
| **NOT_PRESENT** | **4** |

Four checks, all NOT_PRESENT, and the reason is the measurement failure
above rather than the drawing: a dimension is matched only when its
extension lines bracket the same interval, and nothing on the sheet
dimensions a plot-sized rectangle. **So the cross-check has not been
exercised on P7757 at all.** It is exercised on synthetic fixtures, where a
3000 mm span printing "300" returns display 300.0, normalized 3000.0,
geometry 3000.0 and `AGREE` — and a fixture asserts that display never
equals geometry when DIMLFAC is 0.1.

389 authored dimensions are available and unread for this purpose. No
dimension disagreement exists, so no exception was raised from one.

---

## H · Complete / partial / unresolved

```
complete      2   of 48     both measuring the plot, not the room
partial       0   of 48
unresolved   46   of 48     A_WHOLE_SIDE_HAS_NO_DRAWN_LINE
```

Every one of the 46 stopped for the same reason, which is the frozen
enclosure refusing to close a space one of whose sides no drawn line
supports. That refusal is correct behaviour; what is wrong is which lines it
was given.

---

## I · Release-eligible count and the exact blockers

```
release-eligible    2      and BOTH are false positives
diagnostic only    46
```

| blocker | spaces |
|---|---|
| `A_WHOLE_SIDE_HAS_NO_DRAWN_LINE` | 46 |
| none — released | 2 |

**The release gate has a hole and it is mine.** CADSP-012 and CADSP-014
passed it because they satisfy every condition it tests: the enclosure is
complete, the identity is established from authored text, and no dimension
disagrees. Nothing in the gate asks whether the measured space is
**plausibly the space its label names**. A 443 m² W.C satisfies a gate that
never compares the result to its own seed.

Two structural causes, both source-general, neither tuned away:

1. **The wall-layer proposal is too inclusive.** Layer `1` carries 2078 m of
   axis-aligned length — more than any other layer — and is very likely the
   site and plot layer. Feeding the plot boundary to the enclosure as a wall
   face is what lets a flood that escapes a washroom still close, on the
   plot. The paired-majority test is a valid *wall* test and is not a *room
   wall* test.
2. **The seed filter admits annotation blocks.** `A$C662819C0`
   (`NEIGHBOUR`) ×12, `A$C60883738` (`SEA VIEW`, `15.00`) ×6,
   `A$C7BD10DAB` (`STREET`) ×3 and `LEL` (level marks) ×6 are blocks that
   carry text, so they passed the "text arrived through a block instance"
   rule. 27 of 48 candidates are not rooms.

A third, smaller defect: 33 of 48 read `IDENTITY_AMBIGUOUS_MULTIPLE_LABELS`
because each room stamp carries an English and an Arabic string, and the
grouping treats two different strings as two identities. They are **one
room's name in two languages**.

---

## J · Project-2 frozen baseline

```
source            7f61f3acdd62d62d
decoder JSON      c742657fab496d55
adapter           bd331c8074806e8b19711417
fixture freeze    b0bf6a13f057aa1578262e3c
normalization     72bdb0a2bbb65c3c4c0e8ea6
source profile    483314a55f04932564a9bac6
enclosure         01ff128e7ffdab820805dce1
baseline file     8323169dcad1053a   (data/runs/7757/P7757_CAD_baseline.json)

PROJECT_2_CAD_BASELINE_HASH   3edf12c66f0984330d77e248
```

Frozen before any human reference was opened. The record contains no
benchmark, no architect take-off total, no manual quantity, no Excel, no
structural or sanitary quantity.

---

## K · Anything that required a P7757-specific rule

**NOTHING. The list is empty, and that is the point of the round.**

- No layer name is matched anywhere in `engine/cad_adapter.py`,
  `cad_profile.py`, `cad_regions.py` or `cad_measure.py`. Tests assert a
  layer called `ZZ-NONSENSE-NAME` is proposed wall-like on its geometry and
  a layer called `WALL` is not proposed when its lines are unpaired.
- No block name is matched. `SAL` is not saloon, `MB` is not master bedroom.
- No clustering distance was chosen; stability across a fixed ladder is
  reported instead.
- No threshold was tuned against P7757. Every constant is justified from
  construction, from the CAD format, or from arithmetic, and each states its
  own reason in `frozen_parameters()`.
- Project 23010's `calibrate(887.82 pt = 40000 mm)` was **not used**. The
  unit is P7757's own `$INSUNITS = 4`.
- The enclosure freeze `01ff128e7ffdab820805dce1` is untouched, and the CAD
  path measures a synthetic 5 × 4 m room at exactly **20.0 m² and 18.0 m**
  through it.

**What I did NOT do, deliberately:** narrow the wall layers to exclude layer
`1`, or filter the annotation blocks out of the seeds. Both would make
P7757's numbers look far better and both would be chosen by looking at
P7757's numbers. They are the next round's work, and they must be done as
source-general rules — a room wall is not merely a paired face but one that
participates in a bounded circuit at room scale; a room stamp is not merely
text in a block but text in a block whose other placements also sit inside
bounded areas.

---

## Still not started

No structural quantities, columns, beams, footings, slabs or rebar. No
sanitary or drainage. No materials, paint, flooring, waterproofing or
aluminium. No pricing, no procurement. Architectural geometry first, and it
is not finished.
