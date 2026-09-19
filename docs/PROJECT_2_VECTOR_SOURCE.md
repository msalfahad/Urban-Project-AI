# Project 2 — Source C, the authored DWG

A correction first, because it changes the conclusion I gave last round.

> **I said the walls were AEC custom objects. They are not.**
> I probed the DWG's readable strings, found `AecDbDispRepPolygonTrueColour`,
> `WallSchem`, `WindowAssembly`, `DoorRcp` and the ARX modules
> `AecBase70`/`AecArchBase70`, and concluded the geometry was custom objects
> needing an ACA object enabler. The class table settles it the other way:
> **244 AEC classes are declared, every one with ZERO instances, and none of
> them is an entity class.** AutoCAD Architecture registers its class
> registry in any drawing it touches whether or not the drawing uses it. The
> walls are plain lines. Proxy objects: **0**. Unknown entities: **0**.
>
> Presence of a class name is not presence of an object, and I should have
> read the instance counts before saying otherwise.

---

## A · DWG source audit

```
FILE      P7757_ARCHITECTURAL.dwg
HASH      7f61f3acdd62d62d          2,655,476 bytes
FORMAT    AC1018 (AutoCAD 2004)
AUTHORED  AutoCAD Architecture 2014 - English (19.1s LMS Tech)
DECODER   LibreDWG 0.13.3, built from source here, JSON writer -> SUCCESS
```

**Two decoders, two answers, and the difference matters.** LibreDWG's *DXF*
writer aborts inside `BLOCKS` (`Invalid type 0x4, expected 0x5 ENDBLK`) and
emits **no ENTITIES section at all** — a 380 KB DXF with HEADER, CLASSES,
TABLES and nothing else. Its *JSON* writer reports `SUCCESS` and decodes
every object. Had the DXF been the only path tried, this source would have
looked as empty as the scan, for an entirely different reason.

### Entities

Model space, `$TILEMODE = 1`. Two paper layouts exist but carry no geometry.

| kind | count |
|---|---|
| LINE | **7,348** |
| POINT | 1,166 |
| INSERT (block references) | **931** |
| MTEXT | 389 |
| DIMENSION_LINEAR | 366 |
| TEXT | 177 |
| LWPOLYLINE | 139 |
| ARC | 109 |
| HATCH | 90 |
| CIRCLE | 55 |
| DIMENSION_ALIGNED | 20 |
| RTEXT (custom class, 3 instances declared) | 3 |
| DIMENSION_RADIUS | 2 |
| ARC_DIMENSION | 1 |
| **total** | **10,796** |

```
geometry   7,651     annotation   566     dimensions   389
symbols      931     points     1,166     hatches       90
```

**66,842 BLOCK_BEGIN/BLOCK_END records were excluded**, not counted. They are
the same decoder defect that killed the DXF writer: 33,388 block-begins for
a file whose block table has **33** entries and which holds 931 block
references. Counting them would have inflated the drawing thirtyfold.

Three independent cross-checks say the rest of the decode is sound — the
class table's declared instance counts match the decoded entities exactly:
`LWPOLYLINE` 139 declared / 139 decoded, `RTEXT` 3 / 3, `ARC_DIMENSION`
1 / 1.

### Layers — 15

```
0  1  2  3  4  5  ARNOTE  D  LEVEL  S-COL.BON  ST  TE  TEXT  TOI  W
```

| layer | entities | composition | reads as |
|---|---|---|---|
| **W** | 2,438 | **2,430 LINE**, 4 LWPOLYLINE, 4 ARC | walls — a dedicated layer, almost pure line |
| 4 | 2,809 | 1,228 LINE, 842 INSERT, 368 MTEXT, 347 DIM_LIN, 18 DIM_ALI | dimensioning |
| 1 | 1,377 | 1,314 LINE, 47 TEXT | — |
| *(unresolved)* | 1,172 | 1,166 POINT, 3 RTEXT | layer handle did not resolve |
| 5 | 985 | 855 LINE, 42 ARC, 40 TEXT, 34 LWPOLYLINE | — |
| 0 | 921 | 920 LINE | — |
| **S-COL.BON** | 372 | 174 LINE, 59 HATCH, 59 LWPOLYLINE, 42 INSERT | structural columns |
| 2 | 250 | 234 LINE, 11 ARC | — |
| **D** | 234 | 179 LINE, **35 ARC**, 8 TEXT | doors — arcs are swing arcs |
| TEXT | 112 | 52 TEXT, 40 CIRCLE, 20 LWPOLYLINE | tags in bubbles |
| LEVEL | 57 | 24 TEXT, 23 INSERT | level marks |
| TOI | 23 | 8 ARC, 7 LINE, 6 CIRCLE | sanitary fittings |
| ST / ARNOTE / TE / 3 | 7 / 3 / 2 / 34 | — | stairs, notes, hatch |

The layer names are not self-documenting and **`W` is not yet established as
the wall layer** — 2,430 lines on one layer is evidence, not a finding.

### Blocks — 33 definitions, 931 references

```
A$C60883738  A$C662819C0  A$C7BD10DAB  AR1  D115  D120  D200  D315
DRI  GAR  GF  LE  LEL  MARK  MB  PAN  SAL  SWIM  WASH  WASH2  WC
_DOT  _OBLIQUE  arch120  cou  cut  d220  din  dwa  kit  rec
```

| block | inserts | reads as |
|---|---|---|
| `_OBLIQUE` | **776** | dimension tick mark — not building content |
| *(unresolved)* | 48 | — |
| `LE` / `LEL` | 23 / 6 | level marks |
| **`D315`** | **11** | door, apparently 315 |
| **`D120`** | **6** | door, apparently 120 |
| **`D115`** | **4** | door, apparently 115 |
| **`d220`** / **`arch120`** / **`D200`** | 3 / 2 / 1 | door / arch opening |
| `WC` `WASH2` `WASH` `MB` `SAL` `kit` `din` `PAN` `DRI` `GAR` `SWIM` `rec` `cou` `dwa` | 7·5·2·2·1 each | **room-name stamps** |
| `AR1` `MARK` `cut` `GF` `_DOT` | 9·1·1·1 | sheet furniture |

**Door and window symbols are blocks named by width, and room names are
blocks.** That is categorically better opening and identity evidence than
AR-00 had, where both came from raster ink.

### Text and dimensions

**566 real text objects** (177 TEXT + 389 MTEXT) and **389 real dimension
entities**. AR-00 had zero of either — its room names and dimension
numerals were glyph outlines, which cost 144 vision calls to read. This
source needs none.

---

## B · Scale and unit establishment

**The drawing unit is the millimetre, established from this source alone.
Project 23010's `calibrate(887.82 pt = 40000 mm)` is not used and is not
applicable.**

One declaration, proven on two independent facts — the project's own
discipline for any measurement:

| evidence | value | what it gives |
|---|---|---|
| **declaration** | `$INSUNITS = 4` | the author says millimetres |
| **corroboration 1** | `$LIMMAX = 84100 × 59400` | **exactly A1 (841 × 594 mm) × 100.** Drawing limits set for an A1 sheet at 1:100 — which only divides cleanly if the unit is the millimetre |
| **corroboration 2** | `$DIMLFAC = 0.1` + block names `D115` `D120` `D200` `D315` | dimension text is one tenth of drawing distance, i.e. **centimetres**; door blocks named 115/120/200/315 are then cm widths — 1.15 m to 3.15 m, correct for doors |
| `$LUNITS = 2`, `$DIMLUNIT = 2` | decimal | not feet-and-inches |
| `$MEASUREMENT` | **NOT_PRESENT_IN_THIS_DECODE** | absent from the JSON writer's output. The DXF writer on the same file reported `1` (metric), recorded as a cross-check and not as this decode's reading |

### The 10× trap, named before it can be walked into

`$DIMLFAC = 0.1` means **the numbers printed on this drawing are in
centimetres while its geometry is in millimetres.** Section G — printed
against CAD dimension agreement — must apply that factor. Comparing the two
directly would be wrong by exactly ten, in a way that passes review because
both numbers look plausible.

### Extents, and what they imply about the sheet layout

```
$EXTMIN   -568386.696, -862067.397, 0
$EXTMAX    239566.388, -645827.237, 1.241
model span 807,953 x 216,240 mm   =   808 m x 216 m
```

All twelve sheets are drawn side by side in **one model space 808 m wide**.
There is no per-sheet layout to read: isolating the ground-floor plan is a
localisation problem in model space, not a page selection. The DWF
(Source B) confirms the same shape from the other side — one `Model` sheet
on a 5800 × 450 mm custom paper.

---

## C–I · Not established, and why

| section | state |
|---|---|
| C · room/space localisation | **NOT_ESTABLISHED** |
| D · complete and partial measured spaces | **NOT_ESTABLISHED** |
| E · room dimensions and clear areas | **NOT_ESTABLISHED** |
| F · opening/portal observations | **NOT_ESTABLISHED** |
| G · printed/CAD dimension agreement | **NOT_ESTABLISHED** |
| H · diagnostic vs release-eligible spaces | **NOT_ESTABLISHED** |
| I · exceptions / unresolved geometry | **NOT_ESTABLISHED** |

Not zero, and not a failure of the drawing. **The normalisation layer asked
for in §4 does not exist yet.** Every stage of the current pipeline consumes
a `VectorDrawing` read from a PDF page by PyMuPDF and a raster rendered from
that same page; a CAD entity set is neither. The missing adapter is:

```
CAD entity  ->  Drawing  ->  Wall / wall face  ->  Opening
                         ->  Dimension  ->  Annotation
                         ->  SpaceCandidate  ->  PhysicalSpace
```

and it has to do three things this drawing makes possible and AR-00 never
did: take wall candidacy from **layer membership** instead of pen weight,
take openings from **named block references** instead of raster gaps, and
take dimensions and room names from **real text** instead of vision.

### The shortcut I did not take

The current pipeline could have been fed this geometry by plotting the DWG
to a vector PDF and running it unchanged. I did not, and would advise
against it: stage 1 selects wall candidates with
`stroke_width_pt == 1.14`, so the wall population would become an artefact
of **pen weights I chose in the export**. That produces a clean-looking run
whose central evidence I fabricated. The adapter reads the author's layer
instead, which is the actual evidence.

---

## J · Output hashes

```
SOURCE_A  compressed PDF        29,558,720   a5105c5ead214460   raster, stopped at stage 1
SOURCE_A  original 01-06        19,015,776   80b6a80428990db4   raster
SOURCE_A  original 07-12        18,512,718   281a0c3f8c1cdd8f   raster
SOURCE_B  DWF                    2,655,253   7d440a57aa893056   4 W2D streams, unread
SOURCE_C  DWG                    2,655,476   7f61f3acdd62d62d   10,796 entities, audited
SEALED    area take-off          4,570,733   ad337b05496c9bbd   never opened

FROZEN    stage-1 stop record                4c8135e566cea06c
FROZEN    DWG census                         2ce4bf8176a3e96b
          LibreDWG JSON decode  51,902,848   c742657fab496d55
```

The DWF re-sent this round is **byte-identical** to the one already frozen —
same 2,655,253 bytes, same `7d440a57aa893056`. No new source.

### One reproducibility caveat, stated rather than buried

LibreDWG was **built from source in this container**, which is ephemeral.
The audit is reproducible only where a `dwgread` exists; the tool finds it
via `--converter`, `$URBAN_DWG_DECODER`, or `PATH`, and **refuses with
`NO_DWG_CONVERTER_AVAILABLE` rather than reporting an empty drawing** when
it finds none. A `/tmp` build path was deliberately removed from the
defaults: a default that works today and vanishes tomorrow makes a run
irreproducible without saying so.

---

## Confirmation

No human Excel. No architect area take-off totals — the four figures were
not read, and the sealed file is refused by name from any path. No
structural or sanitary quantity. No manually measured room area. No كيال.
No expected total. Project 23010's scale constant was not applied to this
source. The raster PDF result stays frozen and historical, unedited.

No threshold was changed and no Project-2-specific rule was added. The
enclosure freeze `01ff128e7ffdab820805dce1` stands.
