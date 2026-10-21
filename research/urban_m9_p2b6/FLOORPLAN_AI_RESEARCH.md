# Floor-plan AI research (Phase 2B-6, Part 7)

This extends `research/urban_m9_p2b5/FLOORPLAN_AI_RESEARCH.md`, which holds the prototype, the benchmark and the hybrid
rules. Part 7's 14 questions are answered here for every candidate. It adds a graph-based reconstructor
(Raster-to-Graph) and a CAD-native symbol spotter (CADTransformer / FloorPlanCAD).

**How the facts were checked.** Licences were re-read tonight from the repositories' own licence files and pages
(sources at the end). Where a page states no licence, the answer is "not stated", never a guess. No weights were
downloaded and no private drawing left the work area. A research paper was never taken as a product.

**Verdict.**

- **Keep the CAD-native engine as the only quantity source.**
- None of the trained models is cleared for commercial use in its code, weights and data together.
- None reads a construction drawing to engineering tolerance.
- The one vision result worth keeping tonight: Urban's own deterministic raster prototype independently read a door
  as 0.80 m where CAD read 1.027 m (`EXPERIMENT_RESULTS.md` D). It is useful as a cross-check, never as a measurement.

## 1. Learned models

| question | CubiCasa5K | RoomFormer | HEAT | Floor-SP | DeepFloorplan |
|---|---|---|---|---|---|
| 1. what it does | multi-task CNN on raster plans: rooms, walls, icons (5 000 annotated plans) | transformer: rooms as polygons in one pass | holistic edge-attention transformer: planar graphs | room-wise shortest-path polygon reconstruction | multi-task network: room boundaries (walls, doors / windows) + room types |
| 2. usable code | yes | yes | yes | yes | yes (old stack) |
| 3. pretrained weights | yes (a Google Drive link) | yes | yes | Mask R-CNN weights via a link | yes (a link file) |
| 4. commercial use | **no**: CC BY-NC 4.0 (LICENSE read tonight) | code MIT; weights trained on Structured3D (non-commercial, no redistribution) → **no** | **no**: GPL-3.0 plus "non-commercial research only" | code MIT; weights / data unclear → not cleared | code GPL-3.0; weights not cleared |
| 5. dependencies | PyTorch, GPU for training | PyTorch, CUDA | PyTorch, GPU | PyTorch, GPU | TensorFlow 1.10, Python 2.7, OpenCV 3.1 |
| 6. inputs | raster plan images | density maps of point clouds | satellite / point-density images | aligned RGB-D scans | raster plan images |
| 7. output | segmentation masks + icon boxes | room polygons | planar graph | room polygons | per-pixel boundary + room-type maps |
| 8. rooms / walls / doors / windows | rooms, walls, doors, windows, icons | rooms only | corners / edges | rooms | walls, doors & windows (one class), room types |
| 9. curved / irregular rooms | as masks; vectorisation polygonal | polygons (straight) | straight edges | straight | masks |
| 10. Arabic labels | no (Finnish plans, no OCR) | no | no | no | no |
| 11. adaptable to Kuwait drawings | only by retraining on cleared data | no (input domain) | no (input domain) | no (scans) | only by retraining |
| 12. improves on the Urban engine | no: CAD is exact on straight walls, and this works on images | no | no | no | no |
| 13. independent validation | the Urban benchmark's rasters with hand truth (the slot exists) | not applicable | not applicable | not applicable | as CubiCasa5K |
| 14. integration cost / risk | high: licence blocks it; GPU; retraining needs Urban's own annotations | blocked | blocked | blocked | high: GPL, obsolete stack |

## 2. Reconstruction approaches and Urban's own routes

| question | Raster-to-Vector (FloorplanTransformation) | Raster-to-Graph (HSZVIS, CGF 2024) | CADTransformer on FloorPlanCAD (CAD-native symbol spotting) | Urban CAD-native engine (`ARCH_TAKEOFF_V2.6`) | Urban hybrid (vector-PDF reader + raster prototype, test tree) |
|---|---|---|---|---|---|
| 1. what it does | CNN junction heat-maps + integer programming → vector plan | autoregressive wall-junction / segment graph prediction | panoptic symbol spotting on vector CAD drawings (doors, windows, furniture, walls ... as primitives) | DXF → layer roles → wall bands → topology → rooms / openings → deterministic measurement → BOQ lines | vector PDF: deterministic reading of paths; raster: image processing (no model) |
| 2. usable code | yes (Torch7 / Py2.7; a PyTorch port) | yes | yes | yes (repository) | yes (`tests/m9_p2b5_bench/vision.py`, `hybrid.py`) |
| 3. pretrained weights | via a link; training data not verified | yes (a Google Drive link) | no CADTransformer weights published (an ImageNet HRNet backbone only) | - (no learning) | - |
| 4. commercial use | code MIT; Gurobi (commercial solver) in the original; weights not cleared | **code GPL-3.0**; images need an application (LIFULL HOME'S via NII); annotations under their own terms | code MIT; the FloorPlanCAD dataset's terms could not be read tonight (its site did not resolve) → not cleared | Urban's own | Urban's own; PyMuPDF AGPL / commercial (owner decision D-08) |
| 5. dependencies | Torch, Gurobi or a free IP solver | PyTorch, CUDA 11.1, a compiled deformable-attention op | PyTorch ≥ 1.5, HRNet | stdlib engine; ezdxf intake | PyMuPDF; NumPy / SciPy / Pillow / Shapely; Tesseract |
| 6. inputs | raster plans | 512 x 512 raster plans | SVG vector drawings (rasterised in preprocessing) | DXF (DWG through a converter) | vector PDF; raster / scan |
| 7. output | walls, doors, windows, rooms (vector) | vector graph + semantics | labelled primitives (symbol instances) | rooms, openings, walls, BOQ lines with provenance | room polygons, openings (raster), hybrid statuses |
| 8. rooms / walls / doors / windows | all four | walls + room semantics | doors / windows / furniture as symbols; rooms not measured | all four, plus columns, stairs, shafts, thresholds | rooms; raster openings |
| 9. curved / irregular | straight (Manhattan) | straight segments | arcs as primitives | irregular exact; arcs exact in area and boundary, chord in polygon / wall run (D-D2) | the vector PDF flattens arcs; the raster approximates them |
| 10. Arabic labels | no | no | no (symbols, not text) | yes (Arabic text, SHX, \U+ escapes) | Tesseract `ara` installed; not tested on Arabic |
| 11. adaptable to Kuwait drawings | retraining | retraining + data access | possibly, as a **symbol classifier** for single-instance or unknown layers (D-D1) - needs cleared training data | yes: project-agnostic rules; the remaining weak points are layer semantics (D-D1, D-P6-02 - 08) | yes, for PDF-only sets |
| 12. improves on the Urban engine | no | no | **maybe, narrowly**: symbol recognition where layer roles fail; not for measurement | - | as a cross-check (it caught the D-P6-01 width tonight) |
| 13. independent validation | the benchmark rasters | the benchmark rasters | the benchmark's CAD fixtures exported to SVG, with hand-truth symbols | Stage C real rooms, benchmark, worked examples | hybrid rules against CAD (never averaged) |
| 14. integration cost / risk | high, obsolete | high; GPL | medium-high: a GPU model, data licence unknown, symbol-level only | - | low (exists); licence decision for PyMuPDF |

## 3. Did any of it help tonight?

| question | answer |
|---|---|
| measurement | no: none of the candidates reads a construction drawing to BOQ tolerance; vision is never a BOQ basis |
| cross-check | yes, Urban's deterministic raster prototype. It disagreed with CAD on the crossing door's width (0.80 vs 1.027 m), which is the real defect D-P6-01 / D-V26-06. It also failed (no rooms on the double door; −2.7 % bath area), which is why it stays a review aid |
| the one plausible future use | a CAD-native **symbol classifier** (in the CADTransformer family) to type single-instance layers (D-D1). It would need cleared training data (Urban's own annotated drawings), local inference only, and a held-out evaluation against hand truth. For now, the geometry signatures of Experiment C already solve doors and windows without learning; only columns remain, and those need structural cross-reference more than vision |

## Sources (read 2026-10-17)

- CubiCasa5K licence: <https://raw.githubusercontent.com/CubiCasa/CubiCasa5k/master/LICENSE> (CC BY-NC 4.0); weights
  link: <https://github.com/CubiCasa/CubiCasa5k>
- DeepFloorplan: <https://github.com/zlzeng/DeepFloorplan> (GPL-3.0; TensorFlow 1.10, Python 2.7)
- CADTransformer: <https://github.com/VITA-Group/CADTransformer> (MIT; SVG input; no released weights)
- FloorPlanCAD paper: <https://arxiv.org/abs/2105.07147>; dataset site <https://floorplancad.github.io/> (did not resolve
  tonight: terms not verified)
- Raster-to-Graph: <https://github.com/HSZVIS/Raster-to-Graph> (GPL-3.0); paper <https://diglib.eg.org/handle/10.1111/cgf15007>
- RoomFormer, HEAT, Floor-SP, FloorplanTransformation: as cited in the Phase 2B-5 report (repository pages read
  2026-10-17), unchanged.
