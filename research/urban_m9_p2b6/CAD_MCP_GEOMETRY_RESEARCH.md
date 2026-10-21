# CAD, MCP and geometry-library research (Phase 2B-6, Part 8)

This extends `research/urban_m9_p2b5/MCP_SKILLS_AUDIT.md` (§1 MCP inventory, §2 - §4 benchmark).

**Rules followed tonight.**

- Nothing was added to the engine. It stays standard-library only, with ezdxf at the intake.
- One third-party package (`fastmcp`, needed to import the U-C4N code) was installed into an isolated virtual
  environment in the scratch area, never into the project environment.
- No CAD MCP is connected in this session. None was benchmarked as an MCP, and none is claimed.

## 1. MCP availability (verified in this session)

| server | what it offers | CAD geometry? | status |
|---|---|---|---|
| Autodesk_Product_Help | product catalogue, help-content search | no (documentation) | available; usable to look up AutoCAD behaviour (DIMLFAC, XREF binding, OCS), never as evidence of a drawing |
| github, Claude_Code_Remote, Claude_Docs, Google_Drive, Canva, Higgsfield | repository, sessions, documents, media | no | not for drawings or BOQ data |
| **any AutoCAD / DWG MCP** | - | - | **NOT_AVAILABLE**: none connected |
| christiannp-autocad | - | - | NOT_AVAILABLE: no public repository under that name was found tonight (a web search returned other AutoCAD MCP projects only); in earlier stages its outputs were an external estimate run by the owner |

## 2. The U-C4N/Autocad-MCP code, run as a library (`EXPERIMENT_RESULTS.md` H)

**What it is.**

- MIT licence, commit `cdb1063`.
- Its README lists 247 tools: drawing, annotation, mechanical, P&ID, architecture, takeoffs.
- It has a live-AutoCAD COM backend (Windows) and a headless ezdxf backend.
- Its "takeoffs" are pipe and cable takeoffs for P&IDs, not finishes.

**Its room reader `rooms_detect`.**

- It reads faces of the lines on layers whose *names* contain WALL / DUVAR.
- By its own docstring, it closes door gaps only for openings it drew itself: "a foreign plan's gaps stay open".
- On four synthetic plans with five rooms it found **1 room** (exact area, no label). Every room with a door to the
  outside leaked through the gap.

**Value for Urban.**

- Ideas already taken in earlier stages: the OCS reference, MINSERT / XREF record rules, plain-text cleanup.
- **No integration benefit** for room, opening or finish takeoff.

## 3. Libraries

Licences were read tonight from the projects' licence files. "Installed" means present in this environment.

| library | licence | installed | what Urban already has | where it could help | decision |
|---|---|---|---|---|---|
| **ezdxf** 1.4.4 | MIT | yes | the intake (K2 kernel): blocks (nested, mirrored, non-uniform), OCS / extrusion, MINSERT, bulges, ARC / CIRCLE / ELLIPSE, DIMENSION, text (SHX, \U+), XREF detection and refusal; the independent raw readers of this program | `ezdxf.addons.drawing` for raster renders of real drawings (vision cross-check); `ezdxf.bbox` / `ezdxf.path` for independent checks | **keep** (already the basis) |
| **Shapely** 2.2.0 (GEOS) | BSD-3 / LGPL-2.1 | yes (tests only) | the independent DXF reader and the vision prototype; never in `engine/` | independent verification of polygons, offsets, unions (finish zones, membrane pieces) | **keep in tests**; not in the engine (stdlib policy) |
| **Clipper2** | Boost Software License 1.0 | no | `engine/source` has its own exact clipping (`clip_rect`, `clip_convex`) and a robust-geometry layer (V2.1) | integer-robust offsets / booleans for complex finish zones and membrane laps | **not now**: no measured defect it would fix; reconsider if a non-convex clipping defect appears (Shapely already covers verification) |
| **Manifold** (manifold3d) | Apache-2.0 | no | the structural route computes volumes analytically per member, with ownership / conservation rules | an **independent** solid-boolean check of concrete volumes at beam-column-slab junctions (double counting), and formwork contact areas | **candidate for the verification tree** (isolated, tests only) when formwork is built (roadmap rank 4) |
| **build123d** | Apache-2.0 | no | - | B-rep modelling (OCCT): exact solids, sections | not needed: heavy (OCCT); Manifold covers the verification use |
| **CadQuery** | Apache-2.0 (OCCT LGPL-2.1) | no | - | as build123d | not needed |
| **IfcOpenShell** | LGPL-3.0 | no | - | reading / writing IFC; quantity sets from IFC geometry | **not now**: Urban's inputs are DWG / DXF. Becomes relevant if the owner receives IFC models or wants an IFC export |
| **ifc5d** (part of IfcOpenShell) | LGPL-3.0 | no | the BOQ exports (CSV, JSON, the room workbook) | converts cost schedules (BOQs, schedules of rates) between IFC and CSV / ODS / XLSX; it does **not** compute quantities from geometry | not now; an IFC cost-schedule export option later |
| OpenCV | Apache-2.0 | no | the vision prototype uses NumPy / SciPy / Pillow | - | not needed |
| PyMuPDF 1.28.2 | AGPL-3.0 / commercial | yes | PDF evidence; the vector-PDF reader | PDF-only drawing sets | owner decision D-08 (licence) |

## 4. Would an integration improve the capabilities Part 8 lists?

| capability | current state (evidence) | would an integration help? |
|---|---|---|
| block transformations, mirrored inserts, nested blocks | exact on the benchmark (C01: nested, non-uniform, mirrored; B02, B09) | no |
| block nesting of the **whole plan** | quantities exact, but every door held (D-P6-05) | no: a door-model scoping fix |
| arc interpretation | exact in area and boundary; polygon and wall run on the chord (D-D2) | no: Experiment B fixed both with the existing primitives |
| XREF handling | detected and refused (C06) | no: binding an XREF needs the file, which is an owner input |
| door and window recognition | exact with declared or well-populated roles; single-instance and exploded symbols fail (D-D1, D-P6-02) | geometry signatures (Experiment C) solve doors / windows; a learned symbol spotter is the only external candidate, and it is not cleared |
| room topology | exact on straight walls, curved boundaries exact | no |
| CAD layer semantics | the weakest link (D-D1, D-P6-02 - 08) | the run audit (tonight) and geometry signatures; no library addresses it |
| structural geometry, volumes | route G (V6): measured or bounded families, conventions with ranges | Manifold as an independent check |
| formwork | **not implemented** (no measured item) | build it from the existing member geometry (deterministic); verify with Manifold |
| rebar extraction | schedule- and notation-based modules (footings, columns, ground system, beams, slabs) with completeness registers | no library; the inputs are schedules and notes |
| measurement verification | hand truth, raw-ezdxf readers, Shapely (tests) | keep this split: verification libraries stay outside the engine |

## 5. Recommendation

1. No new dependency in the engine.
2. Keep ezdxf + Shapely as the independent-verification pair.
3. Add Manifold to the **test tree only**, when formwork and junction ownership are built, as an independent volume
   and area check.
4. Treat CAD MCPs as untrusted readers. When one is connected, run it through the benchmark slot
   (`tests/m9_p2b5_bench/bench_run.py`, `MCP_ADAPTERS`) on the synthetic fixtures only. The library run tonight shows
   why: a room reader that leaves foreign door gaps open fails most rooms.

## Sources (read 2026-10-17)

- Clipper2 licence: <https://raw.githubusercontent.com/AngusJohnson/Clipper2/main/LICENSE> (Boost 1.0)
- Manifold: <https://raw.githubusercontent.com/elalish/manifold/master/LICENSE> (Apache-2.0)
- build123d: <https://raw.githubusercontent.com/gumyr/build123d/dev/LICENSE> (Apache-2.0)
- CadQuery: <https://raw.githubusercontent.com/CadQuery/cadquery/master/LICENSE> (Apache-2.0)
- IfcOpenShell: <https://raw.githubusercontent.com/IfcOpenShell/IfcOpenShell/v0.8.0/COPYING.LESSER> (LGPL-3.0); ifc5d:
  <https://github.com/IfcOpenShell/IfcOpenShell/tree/v0.8.0/src/ifc5d>
- U-C4N/Autocad-MCP: <https://github.com/U-C4N/Autocad-MCP> (MIT; read-only clone `cdb1063`)
- AutoCAD MCP search (no christiannp repository found): results included
  <https://github.com/ahmetcemkaraca/AutoCAD_MCP>, <https://glama.ai/mcp/servers/p8cf92x20y>
