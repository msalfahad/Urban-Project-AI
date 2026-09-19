# Material walls and space boundaries are not the same graph

You were right, and the gap map settled it before anything was built.

---

## The measurement that changed the architecture

| space | sides at 100% physical wall | gaps |
|---|---|---|
| **BTH-05** | 3 of 4 | one **1054 mm** |
| **BED-01** | 3 of 4 | one **1200 mm** (+148 mm junction noise) |
| **STR-01** | 2 of 4 | one **1148 mm** + east **2606 mm** |
| OPEN-01 | 1 of 4 | 1600, 6053, 1585, 1000, 897, 636, 1000, 1200, 6731 |

Those first two are **doors**. Wall extraction V2 had essentially succeeded on
BTH-05 and BED-01 and the old test called it failure, because the test asked
whether physical wall alone forms a closed polygon — the wrong question for a
room with a door in it.

## The two graphs

```
MATERIAL_WALL_GRAPH     what is built.      OPEN at every doorway.
SPACE_BOUNDARY_GRAPH    what encloses.      May cross a doorway on a
                                            VIRTUAL boundary, zero material.
```

**The hard invariant is in the type.** `BoundaryInterval` refuses to be
constructed as `VIRTUAL_SPACE_BOUNDARY` with non-zero `material_length_mm`, and
refuses `PHYSICAL_WALL` with zero. `material_length_mm` is the only length a
quantity engine may read, and on a virtual boundary it is always `0.0`.

---

## A · Run manifest — the workbook can no longer mix runs

You found a real and serious bug. The last workbook carried V2 wall extraction
beside V1 exceptions reporting *115 components, 228 termini* and *"planar face
extraction is not started"*. Every sheet was internally correct and the
workbook as a whole was false — the worst shape a report can take, because
nothing in it looks wrong.

It happened because each stage wrote its own JSON and the exporter read
whichever files were on disk. **Freshness was a property of the filesystem.**

Now: one pipeline (`tools/run_pipeline.py`), one output file, one manifest.
Each stage records the id and content hash of what it consumed.

| stage | run | hash |
|---|---|---|
| frame | V2 | `b5bbbf83…` |
| wall_extraction | V2 | `1e27ea06…` |
| wall_graph | V2 | `5f42987b…` |
| opening_detection | V2 | `a7a3e371…` |
| topology | V2 | `6e54e3bf…` |

`build_workbook` **raises** on an incoherent manifest, and on no manifest at
all. Verified:

```
BLOCKED: the workbook would mix analysis runs:
  - this workbook mixes 2 analysis runs: ['V1', 'V2']
  - topology was computed from wall_graph deadbeef…, but this run's
    wall_graph is a44fcf08… The topology numbers describe an earlier state
```

**Stale rows citing 115 components or 228 termini: 0.** The Exceptions sheet
now reads *"The wall graph is in 42 components, 8 of which contain closed
cycles"* and *"85 of 145 termini are unresolved"*, tagged run `V2`.

## B/C · Gap map — every unclosed interval, classified

See the table above. `Wall Extraction QA` carries all 156 rows: each band with
its faces, caps, pen evidence and raster support, each unpaired face with the
best mate it saw, and each room side with its coverage percentage and gap
widths.

## D · Portal candidates

| status | count |
|---|---|
| `PORTAL_PROBABLE` (two independent families) | **7** |
| `PORTAL_CANDIDATE` (one family — a hypothesis) | 10 |
| `PORTAL_UNRESOLVED` | 4 |

| gap class | count |
|---|---|
| `DOOR_OR_PORTAL_GAP` | 7 |
| `OPEN_PLAN_TRANSITION` | 4 |
| `UNRESOLVED` | 10 |

Evidence families: `GEOMETRY` (bands terminate facing each other, span in the
door range, end caps at both jambs), `SYMBOL` (swing arc), `TOPOLOGY` (the gap
closes an otherwise complete boundary). **Span alone is one geometric
observation, never a verdict** — it would classify a missing wall as a doorway
and a doorway as a missing wall with equal confidence.

## E/F/G · The new positive-control test

| space | MATERIAL WALL | SPACE TOPOLOGY | material | virtual material |
|---|---|---|---|---|
| **BTH-05** | 3 of 4 sides at 100% + one 1054 mm door | **CLOSES** | 6.54 m | **0.0 m** |
| **BED-01** | 3 of 4 sides at 100% + one 1200 mm door | **CLOSES** | 20.92 m | **0.0 m** |
| STR-01 | 2 of 4 + one 1148 mm door + a **2606 mm** east side missing | does not close | 5.67 m | 0.0 m |
| OPEN-01 | 1 of 4 — genuinely open-plan | does not close, **correctly** | 37.19 m | 0.0 m |

**BTH-05 and BED-01 meet the success criterion**: correct physical walls,
correct opening, a supported closed space boundary, and **no wall material
invented across the door**.

And BTH-01, BTH-02 and BTH-03 — the three G8 declared impossible under the
mirrored frame — now close too, each on one ~1.1 m portal.

STR-01's east side has **no wall extraction at all** across 2606 mm; that is
too wide for a portal and is left open rather than guessed. OPEN-01 remains one
physical space with its dining, saloon and circulation **functional zones** —
no walls invented between them.

## H · Fragmented mates — how many actually matter

259 faces report `FRAGMENTED_MATE` sheet-wide, but **none of them causes a
positive-control failure**. Every control gap is a door or a genuinely absent
wall. On this evidence a general multi-fragment interval optimiser is **not yet
justified** — you asked for diagnostics before expense, and the diagnostics say
no.

## I · Union-extension audit

The union change was necessary and is not yet fully safe. `extension_reason`
(`JUNCTION_OVERHANG`, `END_CAP_SUPPORTED`, `FRAGMENTED_MATE`,
`UNRESOLVED_EXTENSION`) and per-face occupied intervals are **designed and not
yet implemented** — I did not want to report them as done. No extension
currently crosses a `PORTAL_PROBABLE` gap in the four controls, but that is
observed rather than enforced. **This is the first item for next round.**

## J · Current graph health (V2, one run)

| | |
|---|---|
| bands | 243 (190 validated) |
| edges | 369 |
| components | **42**, 8 with cycles |
| independent cycles | **62** |
| termini | **145** |
| length drift | **0.0 mm** |

## K · Frame

`SWAP_FLIP_Y`, fit 1.000, runner-up 0.226 — recorded in the manifest as
**`FRAME_ALIGNMENT_VALIDATED` only**, with the note that the raster is rendered
from the same drawing, so vector–raster agreement is **not** independent
physical evidence that an object is a wall.

---

## Not done

Structural, materials, recipes, pricing, E34, BOQ — none started. No
space-boundary face is production geometry; migration stays explicit.
