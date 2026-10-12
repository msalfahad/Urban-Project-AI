# M9 S3 — external research: adoption matrix

The external repositories were studied **read-only**, in clones outside the repository. None is installed, connected
or invoked by the pipeline, in production or in development. No MCP server is part of Urban.

Decisions:

- **COPY WITH LICENCE**: code copied with its notice.
- **ADAPT ALGORITHM**: the idea re-implemented in Urban's own code.
- **USE AS DEPENDENCY**: a library or program that Urban runs.
- **USE AS REFERENCE**: read for naming or test ideas.
- **REJECT**.

The R8 lock `research/external_engine_lab/DONORS.lock` stays the authority for the donors it already lists; this
matrix adds the S3 candidates and decisions. No candidate is called better than Urban's own engine: no repeatable
benchmark compared them. They are CAD automation servers, raster models or IFC tooling, not plan-takeoff engines over
the same inputs.

| Candidate | Commit / version | Licence | What it is (read) | Applicable to Urban? | Decision | In S3 |
|---|---|---|---|---|---|---|
| U-C4N/Autocad-MCP | cdb10638 | MIT | Python MCP over ezdxf / AutoCAD: OCS backend, labels, takeoff, room detection (`rooms_detect`) | Room detection skips arcs, old-style POLYLINE and walls inside blocks, which Urban's TS01 topology handles. The face-confidence score and minimum-room-width filter duplicate Urban's thin-face rule (2A/P < 0.45 m). | USE AS REFERENCE (R8: approved donor for OCS / text ideas) | Nothing copied. The room-graph idea (shared wall = adjacency, opening = passage) is re-implemented over TS01 faces and wall bands. |
| beiming183-cloud/AutoCAD-MCP | 11f7c47e | MIT | AutoCAD MCP fork: readback verification, revision anchors | Pattern only: a conversion is recorded with the tool's identity and checked against pins | USE AS REFERENCE (R8 pattern donor) | The DWG conversion record follows the existing `decoder_pins` pattern. |
| C48H74/autocad-mcp | b296bf05 | MIT | AutoCAD MCP for piping / P&ID authoring: entity index in sqlite, `read_attributes` | No plan takeoff. ATTRIB reading already exists in Urban. | USE AS REFERENCE / REJECT as dependency | The ATTRIB room-label variant test. |
| felixalmesberger/AUTOCAD-MCP | ae430dce | MIT | AutoCAD 2026 .NET plug-in driven by the command line and LISP | Needs Windows and an AutoCAD licence; could only serve as a native readback oracle in a lab | REJECT | — |
| christiannp/autocad | — | unknown | not reachable | — | UNRESOLVED (as in R8) | — |
| ezdxf | 1.4.4 | MIT | DXF reader / writer; K2 kernel; `addons.odafc` | Already the K2 kernel dependency | USE AS DEPENDENCY (existing) | `odafc` is used by the DWG adapter only when the ODA converter is installed. |
| LibreDWG `dwg2dxf` | 0.13.3 pinned in R8; not installed now | GPL-3.0 | DWG to DXF converter | Run as a separate program: no linking, so Urban is not a derivative work | USE AS DEPENDENCY (external program, optional) | `tools/dwg_adapter.py`, preferred converter, hash-pinned |
| ODA File Converter | not installed | proprietary freeware | DWG / DXF converter | Run as a separate program, never bundled; its licence terms apply to the user's installation | USE AS DEPENDENCY (external program, optional) | `tools/dwg_adapter.py`, through `ezdxf.addons.odafc` |
| Shapely / GEOS | 2.2.0 | BSD-3-Clause / LGPL-2.1 | Planar geometry | Not in `engine/source` (stdlib-only rule); valuable as an independent oracle | USE AS DEPENDENCY (tests only, `importorskip`) | Oracle for `plane_poly.clip_convex` (300 random cases, 1e-9 m²) |
| CubiCasa5K | c3444026 | CC BY-NC 4.0 | Raster floor-plan dataset and deep-learning model (rooms, icons) | Raster and non-commercial: no data or model may be used | REJECT as dependency; USE AS REFERENCE for the taxonomy | The fixture classes (WC, basin, shower / bath, kitchen appliance, washing machine) checked against its icon list; nothing copied. |
| IfcOpenShell / ifc5d | 9de807dd | LGPL-3.0 | IFC tooling; quantity take-off of IFC elements (Qto base quantities) | IFC export is not in scope; the base-quantity names are a naming reference | USE AS REFERENCE | Names are consistent with the Qto base quantities: wall net run by thickness, opening width (height when sourced), gross vs net floor. No code used. |
| "FloorPlanner", "FloorPlan Vision" | — | unclear | Names match several raster / vision-model projects (e.g. DeepFloorplan; a vision-LLM floor-plan describer) | No vector geometry, no measured quantities, unclear licences | REJECT for vector takeoff | — |
| Tesseract 5 (ara + eng) | installed | Apache-2.0 | OCR | Urban already has `engine/pdf_vector_evidence.ocr` for PDFs. A DXF has its text as data; an unmapped SHX big font cannot be OCR'd without its font file. | Not wired into the DXF route; kept for a scanned-drawing route | — |

## Why no external engine replaced Urban's

- The candidates automate a CAD program or describe images.
- None measures rooms, finishes, stairs or walls with traceable rules from a plan DXF.
- Their room detection is weaker than TS01 on the cases that matter here:
  - arcs (curved walls, door swings);
  - nested and mirrored blocks;
  - jambed openings;
  - door closures from the swing.

Adopting one would add a parallel engine, which the S3 brief rules out unless strictly necessary. The value taken is
the ideas, re-implemented and tested: the room graph, the conversion pinning and the fixture taxonomy.
