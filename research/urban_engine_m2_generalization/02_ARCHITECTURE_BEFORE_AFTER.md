# Architecture: before and after M2

## Before M2

```
drawing set ─► tools/urban_structural_boq.py (M1, frozen)
                 ├─ ROUTE A  known sha256 ─► research/alsenan_m1_usable_boq/alsenan_adapter.py
                 │                            replays the frozen S1 … S9A registers (nothing re-measured)
                 ├─ ROUTE B  person-confirmed profile ─► engine/source/profile_takeoff.py
                 │                            footings and columns only, on layers the person names
                 └─ ROUTE C  no profile ─► inventory + profile template (everything UNRESOLVED)
```

Route A was a hand-built project. Each structural family had its own research stage (S1 to S9A), with sheet
names, layer names, beam-line ids and decisions specific to Alsenan.

A second villa could only get route B: footings and columns, with the layers named by a person. It had no beams, no slabs, no ground beams and no bar models.

## After M2

```
drawing set ─► tools/urban_boq_m2.py  (routes A / B / C delegated unchanged to the frozen M1 CLI)
                 └─ ROUTE G  (default for an unknown set)
                      tools/urban_intake.py        DXF (+ vector / raster PDF pages); DWG refused, never claimed
                        └ K2 kernel                 INSERT / MINSERT / mirror / OCS / bulge / nested blocks
                      engine/source/drawing_model  sheets (frames), roles + storeys (EN / AR titles), units,
                                                   normalised texts, rectangles
                      engine/source/schedule_reader attribute-row tables and drawn text tables; mark field by
                                                   content; units inferred; duplicate marks = conflicts
                      engine/source/member_detection footings (template outlines, states), columns, beam edge
                                                   layers by evidence, bands, supports, mark binding,
                                                   collinear inheritance, quantities under both depth readings
                      engine/source/cad_heal       collinear merge, dangling-end snap (reported when wide)
                      engine/source/slab_engine    topology faces: BEAM / COLUMN / OPENING / PANEL / DETAIL /
                                                   OPEN_BOUNDARY; thickness; unenclosed band sides
                      engine/source/bar_shapes     developed lengths (hooks, closed links) from bar diameter
                      engine/source/generic_route  detect() + items_from() -> items, rebar register, coverage
                                                   risk; scope scan for families it cannot quantify
                      engine/source/provisional_estimate  V / P / U categories, low / base / high, checks
                      tools/m2_overlay             source-coordinate overlays (engine marks only)
                      engine/boq_m1_xlsx + tools/m1_report  Excel workbook, HTML -> PDF (reused unchanged)
               profile (optional): printed values the drawing lacks (storey heights, GB classes)
               conventions: engine/profiles/URBAN_M2_GENERIC_CONVENTIONS_V1.json (20 named, reversible)
```

**Separate generic modules, not yet in route G's BOQ**
- `engine/source/room_slice.py`: architectural rooms (floor area, perimeter, skirting, waterproofing).
- `engine/source/stair_generic.py`: a straight flight from a counted riser number.

**Test and evaluation tools**
- `tools/synthetic_villa.py`: generator with independent truth (clean, defects, hard).
- `tools/m2_evaluate.py`: per-drawing precision and recall, per-family error, range sanity, silent slab loss.

## Boundaries kept

- `engine/source` stays stdlib-only. The ezdxf use is in `tools/` and in the K2 kernel's existing by-design path. The registry declares every module that mentions rebar, bbs or reinforcement.
- The frozen M1 files are byte-identical to the M1 freeze manifest. `tools/urban_structural_boq.py` was edited by mistake in 8c1e28e and restored in 180d9fc; a test now pins its sha256.
- **Frozen stages:** not modified. Route G reads no frozen register. The comparison and audit builder reads them only after route G was committed.
- **Benchmark firewall:** external values are read only by the post-freeze position comparison. The builder refuses to write any output that carries a firewalled number.

## What "generic" means here, and what it does not

**Generic: nothing in route G names a sheet, layer, mark list, beam line or coordinate of Alsenan.** Everything is chosen by evidence:
- edge layers are chosen by parallel pairs at scheduled widths that hold beam marks;
- footing outlines come from schedule sizes;
- sheet roles come from title lexicons;
- units come from member-size plausibility.

**Not generic yet:**
- **Families:** stairs, lifts, pools, domes, tanks, lintels, blinding, cantilevers, necks and walls are not quantified. They are listed in BOQ section C.
- **Ground-beam bars:** the typical detail lives in the PDF, and the PDF text is vector glyphs with no OCR.
- **Inputs:** DWG is not read (no pinned adapter). Raster PDFs are reported as RASTER_ONLY.
