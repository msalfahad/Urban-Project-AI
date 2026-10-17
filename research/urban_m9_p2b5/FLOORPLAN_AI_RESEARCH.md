# Floor-plan AI and computer vision: research, prototype and verdict (Phase 2B-5 Stages E / F)

**Question.** Does the workflow *PDF / image → room segmentation → wall-edge extraction → corner detection → polygon
reconstruction → structured coordinates* improve how Urban reads drawings, and can it be used legally and safely?

**Short answer.**

- **CAD input (DXF, or DWG converted to DXF).** No improvement is possible. The vector route is already exact on
  every benchmark case, and vision can only be an independent cross-check.
- **Vector PDF.** A deterministic vector reader (no model) is exact on the benchmark. This is the useful part of the
  workflow, for PDF-only drawing sets.
- **Raster images and scans.**
  - A deterministic image-processing baseline is good on clean renders: area within 0.75 %, perimeter within 1.6 %.
  - It only reaches review level on a degraded scan: area within 4.1 %, with spurious openings and unread room words.
  - No trained model was found whose code, weights and training data are all cleared for commercial use, and none
    accepts architectural raster plans with an engineering-grade claim.
- **Production.** Nothing from vision enters the production BOQ.

All figures are from the synthetic benchmark (`research/urban_m9_p2b5/bench/BENCHMARK_RESULTS.md`); no paper or video
was taken as evidence of quantity accuracy.

## 1. Candidates reviewed (availability, licence, weights, commercial use)

Licences were read from the repositories' own pages or licence files, as listed. Nothing was installed into the
engine; no weights were downloaded; no drawing was sent anywhere.

| candidate | what it does | input | code licence | data / weights | commercial use | stack / resources | verdict |
|---|---|---|---|---|---|---|---|
| CubiCasa5K (`CubiCasa/cubicasa5k`, commit c3444026, read-only clone in an earlier stage) | 5 000 annotated raster floor plans + a multi-task CNN (rooms, walls, icons) | raster plan images | CC BY-NC 4.0 (repository LICENSE text read) | dataset and model under the same non-commercial licence | **no** | PyTorch, GPU for training | reference only: its room / icon taxonomy was compared with Urban's lexicon; no data, weights or code used |
| RoomFormer (`ywyue/RoomFormer`, CVPR 2023) | two-level-query transformer: rooms as polygons in one pass | top-down **density maps of point clouds** (Structured3D, SceneCAD) - not drawings | MIT (repository label) | checkpoints provided; trained on Structured3D, whose terms limit use to non-commercial research and forbid redistribution | weights: **no** (data terms) | PyTorch, CUDA | not applicable (input domain) and not cleared (training data) |
| Floor-SP (`woodfrog/floor-sp`, ICCV 2019) | room-wise shortest-path polygon reconstruction | aligned **RGB-D scans** | MIT (repository label) | Mask R-CNN weights via a download link | code yes; weights / data unclear | PyTorch, GPU | not applicable (scans, not drawings); its authors point to HEAT as the successor |
| HEAT (`woodfrog/heat`, CVPR 2022) | holistic edge-attention transformer for planar graphs | satellite images; **point-density images** for floor plans | GPL-3.0, and the README says "for non-commercial research purposes only" | checkpoints provided | **no** | PyTorch, GPU | rejected (licence and input) |
| Raster-to-Vector / FloorplanTransformation (`art-programmer/FloorplanTransformation`, ICCV 2017) | CNN junction heat-maps + integer programming to a vector plan | raster plans | MIT (repository label) | trained model via a download link; its training data's terms not verified | code yes; weights not cleared | Torch7 + Python 2.7 + Gurobi (commercial solver); a PyTorch port with a free IP solver | ideas only - the closest to the owner's workflow (junctions → walls → rooms), on an obsolete stack |
| DeepFloorplan (`zlzeng/DeepFloorplan`, ICCV 2019) | multi-task network: room boundaries (walls, doors / windows) + room types | raster plans | GPL-3.0 | pretrained model via a link file | GPL obligations if distributed; weights not cleared | TensorFlow 1.10, Python 2.7 | reference only |
| Hosted floor-plan "vision" services (a LoRA adapter on a vision-language model; hosted recognition endpoints) | text descriptions or masks from an uploaded image | images uploaded to a third party | various | hosted | - | remote inference | rejected: private drawings may not be uploaded; outputs are descriptive, not measured geometry |
| OpenCV | line / contour / morphology toolbox | images | Apache-2.0 | - | yes | C++ / Python | usable; **not needed** - the prototype uses NumPy + SciPy `ndimage` (BSD-3) + Pillow + Shapely (BSD-3) |
| Tesseract OCR 5.3.4 | text recognition | images | Apache-2.0 | `eng`, `ara` traineddata installed locally | yes | local CLI | **used** by the prototype for room words (local, offline) |
| PyMuPDF 1.28.2 | PDF vector paths and text | PDF | AGPL-3.0 or Artifex commercial | - | AGPL obligations if the engine is distributed or offered as a network service; otherwise internal use | local | **used** (already an engine dependency for PDF evidence): licence choice is an owner decision |

What the papers report is segmentation quality: room and corner F1 or IoU on their own datasets. None reports
quantity accuracy against a construction tolerance, and none claims engineering-grade measurement.

## 2. The prototype (isolated; `tests/m9_p2b5_bench/vision.py`)

It is deterministic image processing on the owner's workflow, with no model and no training. It sits in the test tree
and is never imported by `engine/`.

| step of the workflow | raster prototype (`raster_rooms`) | vector-PDF prototype (`vector_pdf_rooms`) |
|---|---|---|
| input normalisation | deskew from the gradient orientation (applied only at 2 degrees or more, refined by profile search); scans: threshold + speck removal | PyMuPDF `get_drawings`: lines, rectangles (the page background skipped), quads |
| text | Tesseract on a 3x upscale; words of 2+ letters at confidence 60+ and plausible height are blanked so they do not become walls | not drawn as paths (text objects ignored) |
| wall-edge extraction | closing at the wall pen, opening below a wall thickness, isolated marks under 0.6 m removed, hollow squares filled (columns) | wall faces kept when a parallel partner lies 30 - 320 mm away; jambs and small closed rectangles kept |
| opening closure (corners / gaps) | 1 x L and L x 1 line closing (L = 1.10 m); a gap thicker than 320 mm is rejected | the same closure rules as the independent DXF reader |
| polygon reconstruction | free components of 1.2 m2 or more; small pockets merged into the room they touch; polygon = union of pixel runs, buffered by half the pen, simplified | Shapely `polygonize` of faces + closures |
| structured coordinates | pixel → mm by the stated scale; the scale is checked against the measured wall thickness (`scale_check` OK / SCALE_SUSPECT) | page units → mm by the stated drawing scale |
| openings | WINDOW when thin lines fill 30 % of the gap; DOOR when thin linework lies beside it; width jamb centre to jamb centre | not supported (NOT_SUPPORTED) |
| labels | the OCR word inside the room | the text object inside the room |

A missing capability is reported, not guessed: no OCR installed → `ocr: NOT_SUPPORTED`, rooms unlabelled; a wrong
scale → `SCALE_SUSPECT`.

## 3. Results on the benchmark (ten plans with hand-derived truth)

The ten cases are B01 - B10: rectangle, mirrored door block, L-shape, column, adjacent rooms, a 27-degree turn, a
splay, an unlabelled lobby with a passage, a whole mirrored plan, and an arc wall.

| method | rooms found | max area error | max perimeter error | openings | runtime per case |
|---|---|---|---|---|---|
| vector PDF | 10 / 10 cases, all rooms | 0.002 % (arc flattened at 1 degree) | 0.0 % | not supported | about 0.01 s |
| raster 10 mm / px (about 250 dpi at 1:100) | all | 0.75 % | 1.6 % (the arc); 0.4 % straight walls | exact on 8 straight unrotated cases; B06 (turned) 1 of 2 with 5 spurious; B10 1 spurious | about 0.6 s |
| degraded scan 25 mm / px (blur, noise, 0.4-degree skew) | all | 4.1 % | 23 % on one room (B09), otherwise under 2 % | spurious gaps in every case (4 - 9) | about 0.25 s |

Label recall (OCR) was 8 of 12 labelled rooms on the clean renders and 0 of 12 on the scans; the vector PDF read all 12
labels from its text objects.

The B09 failure on the scan is instructive. The unread room word in the mirrored plan runs into the east wall and is
taken as a 1.45 m wall spur. This failure mode is invisible in the area figure (−4.1 %) and obvious in the perimeter
(+23 %). It is the reason a vision polygon is never a BOQ quantity.

Hybrid reconciliation (`tests/m9_p2b5_bench/hybrid.py`; the rules are in §5) gives these statuses:

| vision source | AGREE | REVIEW_CANDIDATE | VISUAL_OMISSION |
|---|---|---|---|
| vector PDF | every room | - | - |
| clean raster | every labelled room | - | the unlabelled lobby (B08) |
| degraded scan | none | every room | the unlabelled lobby (B08) |

The BOQ basis is always the CAD reading. Values are never averaged.

## 4. Did computer vision help?

- **CAD drawings.** No accuracy gain is possible: the native engine and the independent reader are exact, and every
  CAD-encoding case passes (nested, mirrored and non-uniform blocks, metres, polylines, Arabic words, DIMENSIONs,
  window blocks). Vision found **none** of the engine's real defects. Those came from CAD-level checks:
  - D-D1, a layer drawn once;
  - D-D2, the arc chord;
  - D-C1, a door drawn two ways.
- **PDF-only sets.** Yes, as a cross-check. The vector reader agrees with CAD exactly and needs no model. It is the
  route to adopt when only PDFs exist, subject to the PyMuPDF licence decision.
- **Scans.** It can produce review candidates, nothing more. A trained model would need commercially cleared training
  data; the realistic source is Urban's own annotated drawings, which makes it an owner-approved project, not a
  download.

## 5. Hybrid architecture (Part 6 of the program; implemented in `hybrid.py`)

- **Provenance** is kept for every polygon: source kind, reader, version, method, input hash, coordinate system and
  scale evidence, vertices, label, openings, status and flags.
- **Rules:**

  | status | condition |
  |---|---|
  | AGREE | IoU of 0.98 or more and area within 1 % |
  | REVIEW_CANDIDATE | IoU from 0.80 to 0.98, or area within 1 - 5 % |
  | DISAGREEMENT | IoU under 0.80, area off by more than 5 %, or a label conflict |
  | CAD_ONLY | CAD has the room, vision does not |
  | VISUAL_OMISSION | vision has a room CAD does not; never a BOQ line, `release: NO_BOQ_CANDIDATE_ONLY` |

- **Never.** The engine never averages CAD and vision, never lets a vision polygon overwrite a CAD polygon, and never
  releases a quantity from vision.

## 6. Recommendation

1. Keep the CAD-first engine as the only quantity source.
2. Adopt the vector-PDF reader as a cross-check route for PDF-only drawing sets once the PyMuPDF licence question is
   decided (AGPL compliance or a commercial licence).
3. Keep the raster prototype as a review tool for scans only.
4. Do not adopt any of the reviewed trained models. Their licences or training data are non-commercial, and their
   input domains (point clouds, scans) do not match drawings.
5. If a trained model is wanted later, the owner decides on:
   - a commercially licensed or self-annotated training set;
   - local inference only;
   - a held-out evaluation against hand truth before any use.

Sources: the repositories named above (their README / licence pages as read on 2026-10-17); Structured3D access
terms (non-commercial research and education, no redistribution).
