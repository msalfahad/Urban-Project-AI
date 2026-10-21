# Open-source licence assessment (Phase 2B-5)

How each item is used decides what its licence requires. Nothing new became an engine dependency in this program,
and no third-party code was copied.

| item | licence | how Urban uses it | obligation / risk | decision |
|---|---|---|---|---|
| ezdxf 1.4.4 | MIT | DXF reading (engine K2 kernel, readers); the benchmark's fixtures and independent reader | keep the notice with any redistribution | OK |
| PyMuPDF 1.28.2 | AGPL-3.0 or Artifex commercial | PDF evidence (engine); the vector-PDF prototype (tests) | AGPL obligations if the engine is distributed or offered as a network service to third parties | **owner decision** (`OWNER_DECISIONS.md` 7) |
| openpyxl | MIT | room BOQ workbook | notice | OK |
| Shapely / GEOS | BSD-3 / LGPL-2.1 | test tree and research only (never `engine/source`) | none for internal tests | OK |
| NumPy, SciPy | BSD-3 | raster prototype (tests) | none | OK |
| Pillow | MIT-CMU (HPND) | raster rendering / reading (tests) | none | OK |
| matplotlib | PSF-based (matplotlib licence) | synthetic PDF fixtures (tests) | none | OK |
| Tesseract 5.3.4 + eng / ara data | Apache-2.0 | OCR in the raster prototype, a local CLI | notice if redistributed | OK |
| LibreDWG `dwg2dxf` | GPL-3.0 | optional external converter, a separate process, never linked or bundled | obligations attach to redistributing the binary | OK as an external program |
| ODA File Converter | proprietary freeware | optional external converter, user-installed | its terms govern the user's installation | check before commercial deployment |
| CubiCasa5K | CC BY-NC 4.0 | reference only (taxonomy) | non-commercial: data / weights unusable in a product | rejected as a dependency |
| RoomFormer | MIT code; Structured3D training data non-commercial, no redistribution | not used | weights inherit the data terms | rejected |
| Floor-SP | MIT (label) | not used | input is RGB-D scans | not applicable |
| HEAT | GPL-3.0 + "non-commercial research only" | not used | non-commercial | rejected |
| Raster-to-Vector (FloorplanTransformation) | MIT (label); Gurobi (commercial solver) in the original | ideas only | the solver licence; weights' training data not verified | ideas only |
| DeepFloorplan | GPL-3.0 | not used | GPL if distributed | reference only |
| U-C4N / beiming183 / C48H74 / felixalmesberger MCP repositories | MIT | read-only research clones, ideas re-implemented (one small text-cleanup adaptation with notice, earlier stage) | notice for the adapted fragment | OK |
| synced `pdf` skill | proprietary (its LICENSE.txt) | not used | - | not used |
| synced `quantity-takeoff-rules` skill | (user-synced) | read as a secondary reference | contains the user's supplier prices: not reproduced | reference only |

Sources: the licence files or repository pages read in this and earlier stages (`FLOORPLAN_AI_RESEARCH.md` §1,
`URBAN_PROJECTS_CLAUDE_HANDOFF.md` §10).
