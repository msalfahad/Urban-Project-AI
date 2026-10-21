# Project 2 — source provenance, before anything else continues

The architectural P7757 PDF the engine read had been compressed from over
30 MB to 29 MB before it arrived. That was not known when the run was
frozen, and it mattered absolutely: if the compression had flattened vector
CAD content, the engine's stop would have been a fact about the copy and
nothing about the drawing.

The original has now been supplied, split losslessly by `pypdf` into two
halves. This is the comparison. **No measurement was performed and no
benchmark was opened.**

---

## A · Original vs compressed — source representation

| | ORIGINAL (split, as supplied) | COMPRESSED 29 MB |
|---|---|---|
| files | `…pages_01-06.pdf` `80b6a80428990db4`<br>`…pages_07-12.pdf` `281a0c3f8c1cdd8f` | `P7757_SCAN_20260506.pdf` `a5105c5ead214460` |
| total bytes | **37,528,494** | 29,558,720 |
| pages | 12 | 12 |
| page size | 842 × 1192 pt (A3) | 842 × 1192 pt (A3) |
| page rotation | 0 | 0 |
| PDF version | 1.4 | 1.7 |
| producer / creator | `pypdf` / — (the splitter overwrote it) | **`PDFlib+PDI 8.0.4p2` / `Xerox AltaLink C8045`** |
| **vector paths** | **0** | **0** |
| **vector segments** | **0** | **0** |
| **PDF text objects** | **0** | **0** |
| fonts | none | none |
| curves | none | none |
| pen populations | **none — there is no stroked linework to have a pen** | none |
| embedded images | 1 per page, 12 total | 1 per page, 12 total |
| image pixel size | **4672 × 6624**, every page | **4672 × 6624**, every page |
| encoding | baseline JPEG, 8 bpc, 4:2:2 | baseline JPEG, 8 bpc, 4:2:2 |
| image stream bytes | 37,516,362 | 29,551,497 |
| JPEG quantisation tables | **[30.89, 29.20] — identical on all 12** | **[15.02, 22.56] — identical on all 12** |
| effective resolution | 399.5 dpi across, 400.1 dpi down | same |

Per page, the compressed streams are **0.73–0.85×** the original's, with no
page departing from that band.

---

## B · Did compression destroy vector information?

**No. There was none to destroy.**

```
VERDICT   BOTH_RENDITIONS_ARE_RASTER_TRANSFORMATION_ONLY_RECOMPRESSED
```

Five independent lines of evidence, the first alone sufficient:

1. **The original carries zero vector paths and zero text objects.** This is
   the direct test, and it is not a matter of interpretation: the vector
   reader sees nothing on either rendition.

2. **Both renditions sit on the same pixel grid** — 4672 × 6624 on all 24
   page-images. A rasteriser flattening vector art chooses its own output
   size; it does not land on another rendition's grid by coincidence.

3. **That grid is not proportional to the page.** Image aspect is 0.705314,
   page aspect 0.706376 — 399.51 dpi across against 400.11 dpi down, a
   0.15% anisotropy. A rasteriser at 400 dpi would emit 4678 × 6622; the
   actual image is 4672 × 6624, six pixels and two pixels away. Independent
   optical and mechanical resolutions are a **scanner** signature.

4. **The scanner's own metadata survives in the compressed file**: creator
   `Xerox AltaLink C8045`, producer `PDFlib+PDI 8.0.4p2 (Linux)`, created
   2026-05-06 11:39 +03:00. A flattening step does not invent a Xerox MFP.
   (The `pypdf` split, by contrast, discarded that metadata — which is why
   the original half-files look anonymous.)

5. **Both are 4:2:2 chroma-subsampled colour JPEG.** Line art rasterised
   from CAD is emitted bilevel or as flate-compressed greyscale; a colour
   JPEG with subsampled chroma is what a document scanner produces.

### One result that reads backwards, and why

The compressed file uses a **finer** luminance quantisation table (15.02)
than the original (30.89), yet is 21% smaller. That is not a contradiction:
the original is a raw scan carrying sensor grain, which is expensive to
encode at any table; the compression pass smoothed it before re-encoding, so
a finer table still costs fewer bits.

It has a practical consequence worth recording. Over the sampled pages, ink
pixel counts at threshold 200 differ between the two renditions by
**−0.41% to +0.77%**, with a mean absolute grey difference of 3.7–7.5
levels. **The compression did not materially degrade the linework.** Had the
engine been able to read this source at all, the compressed copy would have
served about as well as the original.

### What must not be concluded

That a stamped Kuwaiti submission is *inherently* a scan. What is
established is narrower and firmer: **this** submission set reached us as a
scan, in both renditions, and the transformation is not what made it one.
The office plots to vector — its structural set proves that — so the scan is
a property of which copy was issued, not of the office.

---

## C · DWF source audit — Source B, frozen separately

```
FILE     P7757_ARCHITECTURAL_20260506.dwf
HASH     7d440a57aa893056
BYTES    2,655,253
HEADER   (DWF V06.20)    — a ZIP behind a 12-byte version header
```

| | |
|---|---|
| verdict | **`PACKAGE_CARRIES_W2D_VECTOR_STREAMS`** |
| W2D streams | **4** |
| W2D uncompressed total | **4,079,905 bytes** |
| published from | `P7757.dwg`, provider AutoCAD |
| authoring application | **AutoCAD Architecture 2014** |
| DWF toolkit | 7.7.0.15 |
| sheets | **1**, titled `Model` |
| paper | **units `mm`**, 5800 × 450, clip `13 13 5787 437` |
| graphics transform | `0.0211666…` mm per W2D unit (= 1/1200 inch) |
| viewport data | present (`.pia`), model-space window recorded |

**The DWF carries real linework**, not a picture of it — the drawing set as
a single model-space sheet 5.8 m wide.

Two things it does not carry, and both matter:

- **A W2D reader.** This project has none. W2D is Autodesk's binary 2D
  format; reading it is a new capability, not a configuration change. The
  audit establishes that geometry is *present*, never what it *is*.
- **A building scale.** The descriptor states **paper** millimetres. The
  step from paper to building needs the plot scale, and that step is not
  taken here.

Recorded as a **separate frozen source**. It has not been read, and it must
not repair, correct or supplement the PDF result — that result is frozen on
its own file.

---

## D · Which source is appropriate for the unchanged Project-2 gate

**None of the three, and this is now settled rather than open.**

| source | state | can the unchanged gate run on it? |
|---|---|---|
| P7757 compressed PDF | frozen, run, stopped at stage 1 | no — no vector input |
| P7757 original PDF | frozen, audited | **no — identical representation** |
| P7757 DWF | frozen, audited | **no — needs a W2D reader** |

Running the unchanged pipeline on the original would reproduce the same stop
for the same reason, on the same pixels. It is not worth the run, and doing
it would not make the gate execute.

So the gate's real question — does the enclosure generalise beyond AR-00 —
**still has no second data point**, and the choice is between two routes:

1. **A vector plot of P7757's architectural set** — `P7757.dwg` (AC1018) is
   in hand, and the office's structural set proves it plots to vector.
   Plotting it to PDF is the smallest step to a runnable second source, and
   it needs nothing built.
2. **A W2D reader for the DWF.** More work, and it buys a genuinely
   independent geometry path — but it is new capability, and building it
   before the gate has run once would repeat the mistake the gate exists to
   prevent.

**Route 1.** It answers the gate's questions against the same building whose
take-off is already sealed.

---

## E · Source-specific scale strategy

`px_mm` is currently `calibrate(887.82 pt = 40000 mm)` — **a printed
dimension off project 23010**, giving 10.813 mm/px. It is not a property of
any source but the first one, and it may not survive into Project 2.

The rule, stated once and for every source: **the scale of a drawing is
evidence carried by that drawing, established the same way any other
measurement is — one value, proven on a second.** That is what `calibrate`
already does; what is wrong is not the mechanism but that its two numbers
are hardcoded.

Per source type, in descending order of authority:

| source | where scale comes from | independent check |
|---|---|---|
| **DWG / DWF** | authored coordinates and the publisher's stated units — the DWF declares `units="mm"` and a transform per graphic resource | the viewport record, model window against paper extent |
| **vector PDF** | two printed dimensions read off *that* sheet, as AR-00's were | a third printed dimension on a different axis |
| **scanned PDF** | printed dimensions only, read by vision from the scan | a second dimension on the other axis; agreement or the scale is NOT_ESTABLISHED |

Two constraints follow, and neither is optional:

- **A drawing with no established scale is not measured at another
  drawing's scale.** It reports `SCALE_NOT_ESTABLISHED` and stops —
  the same discipline as an unestablished length basis, for the same
  reason. Inheriting project 1's constant silently would produce numbers
  that look like measurements.
- **A declared scale is not a measured one.** A title block reading
  "1:100" is a statement about the intended plot, and a reduced or
  re-plotted sheet keeps the note and loses the scale. It is evidence,
  ranked below a dimension actually checked on the sheet.

For the record, the arithmetic available on this source and **not** used for
anything: at 399.5 dpi, one pixel is 0.0636 mm of paper. Nothing converts
that to building millimetres until the plot scale is established from the
source itself.

**No scale for P7757 has been derived, and none is asserted.** This is the
strategy, not the answer.

---

## F · Confirmation — no benchmark or human quantity was opened

| | |
|---|---|
| architect's printed area take-off (pages 1–2) | **SEALED, not opened.** `ad337b05496c9bbd`, refused by name in `engine.reference_mapping.SEALED` |
| the four printed totals | **never read into any tool, and not used to construct, tune or choose anything** |
| manual room areas / dimensions | **not supplied, not requested, not received** |
| BOQ, كيال, contractor quantity, expected totals | **none received** |
| Excel of any kind | **none opened** |
| 23010's sealed site benchmark | untouched |
| structural (ST7757) and sanitary sets | **representation census only** — page counts and whether they carry vector. No sheet read, no discipline quantity, and they stay out of the architectural gate |

The four area figures appear in this repository in exactly one place: the
narrative of `docs/PROJECT_2_RESULT.md`, describing what the sealed pages
are. No tool reads them, and no geometry has been constructed, tuned or
chosen with them.

---

## What was not done

No threshold changed. No Project-2-specific fix. No AR-00 work. No geometry
tuning, no new tolerance, no W2D reader. The enclosure freeze
`01ff128e7ffdab820805dce1` stands, and the frozen results for the compressed
PDF, the original PDF and the DWF are three separate records with three
separate hashes.
