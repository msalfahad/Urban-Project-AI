# Project 2 — the gate result, frozen

Run at `e4c2a52` + input plumbing only. Nothing in the method was changed:
no threshold, no tolerance, no pen weight, no rule. The proof of that is
below and it is exact.

---

## Steps 1–3 · Frozen before anything was read

```
SOURCE (as supplied)     12-page PDF, 29,558,720 bytes
                         sha256/16   a5105c5ead214460
PRODUCER                 PDFlib+PDI 8.0.4p2 (Linux)
CREATOR                  Xerox AltaLink C8045
CREATED                  2026-05-06 11:39 +03:00

SPLIT (before any read)  tools/split_submission_set.py
  SEALED   pages 0-1     P7757_area_takeoff_benchmark.pdf   ad337b05496c9bbd
  DRAWINGS pages 2-11    P7757_DRAWINGS.pdf                 b672bcf2f5945342

FROZEN AUTOMATIC OUTPUT  data/runs/7757/P7757-GF_automatic.json
                         sha256/16   4c8135e566cea06c
```

The set is **VILLA P7757 — FAJMA ALSNYAN**, a municipality submission:
ground / 1st / 2nd floor plans at 1:100, four elevations, two sections, a
fence sheet, and — on the two sealed pages — the architect's own area
take-off with totals and percentages.

**That take-off was sealed, not read.** It is a KNOWN TOTAL, the same kind
of object as a previous BOQ or a manual كيال, and it is the only independent
check this project has. It is now refused by name in
`engine.reference_mapping.SEALED`, from any path (§44).

---

## Step 4 · Source-representation audit

`tools/audit_submission_set.py`, per page, before measurement:

| | Project 23010 (AR-00) | Project 7757 |
|---|---|---|
| pages audited | 1 | 10 |
| representation | VECTOR_LINEWORK | **RASTER_IMAGE_ONLY × 10** |
| vector paths | 19,257 | **0** |
| vector segments | 74,148 | **0** |
| axis-aligned segments | 35,835 | **0** |
| PDF text objects | 0 (glyph outlines) | **0 (no glyphs either)** |
| page content | plotted linework | one JPEG per page, 4672 × 6624, 8 bpc RGB |
| effective scan resolution | — | 399.5 dpi across an A3 sheet |

**Project 2 is a photograph of a drawing.** Not a differently-drawn vector
PDF — no vector content at all.

The gate asked five generalisation questions. The source answers three of
them and makes two unanswerable:

- *Does the glyph-ink test hold?* — **Unanswerable here.** There are no
  glyphs and no text objects. The test is neither confirmed nor refuted.
- *Does the wall-pen convention differ?* — **Unanswerable.** There is no pen.
- *Does a second sheet carry explicit open-plan evidence?* — **Not
  reachable**; no text was extracted.
- *Do door graphics close pixels there?* — invariant 41 is untested on this
  source, because no partition was built.
- *Is the wall solid porous in the same way?* — **The decisive question is
  not answered.** Whether AR-00's `A_WHOLE_SIDE_HAS_NO_DRAWN_LINE` is a
  property of that drawing or of the medium still has no second data point.

### The finding that reframes the question

The same project's **structural** set, in the same folder, is
`pdfplot11.hdi` output: **16 pages, all VECTOR_LINEWORK, with real PDF text
objects.** (Representation census only — no structural quantity was read,
and none is in scope.)

So readability is **a property of the file you were handed, not of the
office that drew it.** The architectural set reached us as the stamped
submission copy — scanned. The structural set reached us as the office plot
— vector, and with real text, which AR-00 did not have.

A second rendition of the same architectural set (`…p7757_under30MB.pdf`,
12 pages) was audited too: **also raster on all 12 pages.** Two independent
copies, same answer.

---

## Steps 5–6 · Topology and measurement results

```
run_outcome              STOPPED_BEFORE_COMPLETION
stopped at               stage 1 of the run — the frame
stopped with             FrameError: no segments to fit with; a frame
                         asserted without a measurement is the assumption
                         this module exists to replace
```

| metric | 23010 | 7757 |
|---|---|---|
| TOPOLOGY_RECALL_ALL | 27 / 36 · 75.0% | **NOT_ESTABLISHED** |
| TOPOLOGY_RECALL_IN_SCOPE | 13 / 17 · 76.5% | **NOT_ESTABLISHED** |
| ROOM_CANDIDATE_PRECISION | 27 / 27 · 100% | **NOT_ESTABLISHED** |
| UNCLASSIFIED_REGIONS | 39 / 66 | **NOT_ESTABLISHED** |
| COMPLETE_MEASUREMENT_ALL | 3 / 36 · 8.3% | **NOT_ESTABLISHED** |
| COMPLETE_MEASUREMENT_IN_SCOPE | 2 / 17 · 11.8% | **NOT_ESTABLISHED** |
| RELEASE_ELIGIBLE_ALL / _IN_SCOPE | 0 · 0.0% | **NOT_ESTABLISHED** |
| MEAN / MEDIAN VECTOR BOUNDARY SUPPORT | 20.0% / 0.0% | **NOT_ESTABLISHED** |
| DOCUMENT DIMENSION AGREEMENT | 28 / 0 / 16 / 1 | **NOT_ESTABLISHED** |
| EXCEPTION RATE | — | **NOT_ESTABLISHED** |

**Not one of these is zero.** Nothing was measured, so nothing scored badly.
A stopped run and a run that found nothing are different facts (§43), and
the frozen record says `STOPPED_BEFORE_COMPLETION` with
`every_metric_here: NOT_ESTABLISHED` rather than a column of `0.0%`.

### Why it stopped, exactly

Stage 1 asks for the sheet's frame, and the frame is fitted to the drawn
wall-pen strokes:

```python
heavy = [s for s in drawing.axis_aligned()
         if s.stroke_width_pt == 1.14 and s.length_mm > 1000]
frame = fit_frame(heavy, seg.wall_mask, px)
```

| | 23010 | 7757 |
|---|---|---|
| axis-aligned segments | 35,835 | 0 |
| at the 1.14 pt pen, over 1 m | 206 | 0 |

Two independent reasons, and the first alone is fatal: there are **no
segments of any pen**. `engine/frames.py` refused rather than assuming an
identity frame, which is the correct behaviour and is now held by a test.

Every stage after it consumes that empty population — wall faces, bands,
the material graph, the wall solid, the enclosure's supported lines — so
none of them would have produced anything either.

### The raster is not blocked, and that matters

The render is fine. At 300 dpi the ink threshold behaves sensibly on this
scan:

```
                      23010 (plot)      7757 (400 dpi scan)
raster shape (h x w)  3509 x 4963       4967 x 3509
page rotation         270 deg           0 deg
ink at threshold 200    8.206%            6.199%
modal grey level          —              254 (57.8% of pixels)
```

The scan is clean: a hard white background, no grey wash, no threshold
crisis. **The raster topology stage has a usable input on this sheet.** What
it does not have is the vector layer that every stage downstream of it
depends on for a coordinate, and the architecture is explicit that raster
may not be the authoritative source of a wall coordinate, a wall thickness,
an opening width, a released area or a released perimeter.

### One further blocker, named but not reached

`px_mm` comes from `calibrate(887.82 pt = 40000 mm)` — a **printed dimension
off AR-00, hardcoded**, giving 10.813 mm/px. Project 7757 is a different
sheet size at a different scale, so even a source with vector content would
have been measured at project 1's scale. The run stopped before this could
do any harm, and it is recorded here so it is not discovered later as a
surprise: **scale is currently a project-1 constant, not a property of the
source.**

---

## The proof that the method did not change

The pipeline previously named one file in three places. Pointing it at a
second source required input paths to become inputs. Nothing else was
touched, and the claim is checked rather than asserted: AR-00 was re-run
through the re-plumbed pipeline and the full report diffed against the
frozen `e4c2a52` output, key by key, to the leaf.

```
top-level keys differing                       1  (manifest)
values differing inside it                     1
  manifest/workbook_generated_at   19:41:30 -> 20:39:20
```

**One timestamp. Every other value in the AR-00 report is identical.**

Changes made, all of them outside the method:

| file | change |
|---|---|
| `tools/run_pipeline.py` | `--pdf / --space-map / --doc-cache / --topology-overlay / --project-id / --drawing-id / --revision / --floor-id`, defaults identical to today; `NoSpaceMap`; a stopped run recorded as a result, caught **outside** `run()` |
| `tools/freeze_new_source.py` | imported `engine.vector_pdf`, which does not exist — the intake tool had never been executed. Now `engine.vector_source` |
| `engine/reference_mapping.py` | the P7757 take-off added to `SEALED` |
| `tools/split_submission_set.py` | new — splits a submission set into DRAWINGS and SEALED |
| `tools/audit_submission_set.py` | new — per-page representation census |
| `tests/test_source_representation_gate.py` | new — 7 assertions |

No threshold, tolerance, pen weight, grade, tier or geometric rule was
changed. The enclosure freeze `01ff128e7ffdab820805dce1` is untouched.

---

## What this does and does not decide

**Decided.** The engine's input assumption is narrower than the work. It
reads *plotted vector PDFs*. It read project 23010 because 23010 arrived as
one. A stamped municipality submission — which is what a Kuwaiti
quantity surveyor is usually handed — carries no vector content, and on it
the engine produces nothing at all. That is not a tuning gap; there is
nothing to tune.

**Not decided.** Everything the gate was actually built to test. Whether the
enclosure generalises, whether `A_WHOLE_SIDE_HAS_NO_DRAWN_LINE` is a
property of AR-00 or of the medium, whether the glyph-ink test holds on
another office's plot — **none of these has a second data point yet.** The
gate has not been passed and it has not been failed. It has not been run.

The three sources that would run it, in order of what they settle:

1. **A vector plot of P7757's architectural set.** `P7757.dwg`
   (AC1018 — AutoCAD 2004 format) and a DWF V6 of the same project are
   already in the uploads — signatures checked, geometry **not opened** —
   and the structural set proves this office plots to vector. A CAD-plotted
   AR-equivalent would answer every question the gate asks, against a
   building whose sealed take-off is already frozen and unread.
   Per the standing rule, CAD geometry must not be fed into a PDF run being
   evaluated; this would be a **new frozen run on a new source**, not a
   correction to this one.
2. **Any second office's plotted architectural PDF** — the cleanest test of
   the pen and glyph assumptions.
3. **This scan**, only if the decision is that scanned submissions are the
   product's real input. That is a different engine — raster-authoritative
   measurement, which the current architecture explicitly forbids — and it
   is a product decision, not an engineering one.

**Recommendation: (1).** It is the smallest step, the evidence is already in
the folder, and it keeps the sealed benchmark intact.

Still NO: architectural BOQ release, structural quantities, material
recipes, pricing, procurement. Nothing on Project 7757 was measured and no
quantity of any kind was produced.
