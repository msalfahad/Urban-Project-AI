---
name: urban-floorplan-vision-review
description: Read a raster scan or a vector PDF plan with the isolated Urban vision prototype and reconcile it with the CAD reading under the hybrid rules (AGREE / REVIEW_CANDIDATE / DISAGREEMENT / CAD_ONLY / VISUAL_OMISSION) - vision corroborates or questions CAD, it never makes a BOQ quantity.
---

# Urban floorplan vision review

## Purpose
Use the drawings that have no CAD entities (scans, PDF sets) as a second, independent reading: confirm CAD rooms,
point at rooms CAD may have missed, and flag disagreements for a person to resolve.

## Trigger
Only a PDF or a scan exists for a sheet; a CAD reading needs an independent cross-check; a reviewer suspects a room
is missing.

## Inputs
- a PNG (or a page rendered to PNG) with its scale in mm per pixel and its origin, or a vector PDF with the drawing
  extent it shows; the CAD rooms of the same sheet when a reconciliation is wanted

## Tools
- `tests/m9_p2b5_bench/vision.py`: `raster_rooms(png, meta)` (deterministic morphology + Tesseract labels; deskew;
  scale check) and `vector_pdf_rooms(pdf, meta)` (vector strokes -> wall faces -> faces)
- `tests/m9_p2b5_bench/hybrid.py`: `reconcile(cad, vision, cad_source, vision_source)`
- measured performance on the synthetic set: vector PDF exact; raster at 10 mm / px within 1 % on area; a degraded
  25 mm / px scan within 5 % with spurious short gaps (`research/urban_m9_p2b5/bench/BENCHMARK_RESULTS.md`)

## Safety
- No BOQ quantity from vision: the BOQ basis is always CAD; a VISUAL_OMISSION is a candidate to look at, never a line.
- Never average CAD and vision values.
- Private plans are processed locally only; never sent to a hosted model or inference API. No trained model is
  deployed into the production pipeline.
- A missing capability is reported as NOT_SUPPORTED (no OCR, no scale, no PDF engine), never guessed.
- The scale must be stated; SCALE_SUSPECT stops the reading from being used.

## Outputs
Per room: the reconciliation record with both provenances (source kind, file digest, reader, version, method), the
IoU, the area difference, the status and the release state.

## Tests
`tests/m9_p2b5_bench/test_bench.py` (raster and scan bounds, hybrid rules, wrong scale, missing OCR, determinism).

## Escalation
Every DISAGREEMENT and every VISUAL_OMISSION goes to a person; any wish to use a trained model (licence, weights,
training data terms) is an owner decision (see `research/urban_m9_p2b5/FLOORPLAN_AI_RESEARCH.md`).
