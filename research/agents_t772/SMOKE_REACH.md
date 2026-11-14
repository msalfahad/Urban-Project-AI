# T-772 smoke test: what reaches the BOQ directly from the drawings (training villa, 2026-11-14)

Command: `tools/urban_boq_run.py --manifest RUN_MANIFEST.json --out DIR` (manifest built by
`research/agents_t772/t772_smoke.py` from the decoded Drive drawings; outputs outside the repository).
Geometry stage = ARCH_TAKEOFF_V2.13 + route G, unchanged; 69 s wall time end to end; two identical runs gave identical
reach tables. Compared with the committed candidate index ARCH_TAKEOFF_V3.0.83 (5,280 lines) and family master 1.83.0.

Geometry run: 1,694 lines (architectural 579: 307 with a figure, 238 HELD, 34 excluded; structural 1,115: 1,043 with
a figure, 72 HELD). Both exported through boq_export_v1 (one workbook per drawing identity). Exceptions: inputs sheet
absent (T-782 not built), 4 rebar lines at 0 with no producing input exported HELD (engine lines unchanged),
36 HELD-by-geometry item codes listed.

Reach of the candidate lines (EXCLUDED lines not counted):

| | lines | geometry direct | restated by overlay | restated by fix row | overlay only | fix row only |
|---|---|---|---|---|---|---|
| all except rebar | 2,260 | 489 (21.6 %) | 96 | 159 | 830 | 686 |
| rebar (parked) | 2,067 | 24 | 56 | 0 | 1,987 | 0 |

Classes: GEOMETRY_DIRECT = same line id, class and figure in the geometry run; GEOMETRY_RESTATED = the geometry line's
figure or class changed by an arch_v30xx module; FILL_RESTATED / FILL_ONLY = the figure comes from a FILL fix row keyed
by line id (a restatement by construction); OVERLAY_ONLY = the line exists only because an arch_v30xx module adds it
(rule or restatement: traced per GENERALISE row). 29 geometry lines are not in the candidate (superseded).

Per family: out/REACH_BY_FAMILY.csv. GENERALISE backlog, one row per (family, item code, unit) = one rule to write and
test on the synthetic villas: out/GENERALISE_BACKLOG_BY_ITEM.csv (118 rows outside rebar). Largest by line count:
formwork B10-13 581 lines (298 overlay, 283 fix row), beams B10-07 65, plaster B4-03 61, window reveals B4-08 61,
lintels B9-02 52, ground beams B10-04 45, external paint edges B4-07 38, necks B10-03 36 (all fix rows),
columns B10-06 33, ceiling paint B4-06 31. Families reached at 100 %: B10-08, B6-01, B7-01; above 90 %: B10-02, B8-05.

Restated lines, geometry figure vs candidate figure (released lines only; geometry 0.0 = the geometry run leaves the
line HELD): beams B10-07 0.0 -> 48.81 m3, ground beams B10-04 20.37 -> 29.96 m3, ground slab 0.85 -> 5.25 m3, stair
concrete 5.50 -> 9.03 m3, internal plaster 0.0 -> 1,604.3 m2, block 0.0 -> 981.3 m2, wall tile 0.0 -> 340.3 m2,
roof WP 115.8 -> 168.0 m2, skirting 137.5 -> 163.3 lm, floor porcelain 163.6 -> 153.0 m2, stair step lm 60.0 -> 51.8.
These are the rules the geometry stage does not yet carry (column geometry_released_qty in the backlog file).
