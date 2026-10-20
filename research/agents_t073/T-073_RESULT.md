# T-073: plot-edge foundation members as separate lines (PLOT_EDGE_MEMBERS_V1)

Worker 3, 2026-10-20. Development reference, not an accuracy claim. New method piece
`engine/source/plot_edge_members.py` (not wired into any released method; CONCRETE_LEDGER_V2, the strip guard and every
frozen file untouched). Tests: `tests/t073_plot_edge_members/` (30, synthetic plot, not a client drawing).

## What the piece does (every villa)

| Step | Rule |
|---|---|
| Footing footprints | closed polylines on the footing layers; **block inserts on any layer whose geometry sits on a footing layer** (ezdxf `Insert.virtual_entities()`, mirrored / rotated / nested inserts transform correctly, OCS of a mirrored polyline converted); **loose LINE loops** closed at a gap of 1e-6 m only; **open outlines** (a side interrupted where a strap enters: the gap lies on the line of both end edges) kept as a footprint but HELD `FOOTING_OUTLINE_OPEN` with the gap length; an XCLIPped insert HELD; a curved outline HELD; branching or other open line chains listed, never members; the same footprint drawn twice used once (`merge_members`, also against CONCRETE_LEDGER_V2 members) |
| Band split | concrete_strip_guard pairs the band faces (centre line, corners once); every centre-line metre in exactly one record: FREE / IN_FOOTING (per footing) / IN_OPEN_FOOTING_OUTLINE / IN_COLUMN_ONLY; conservation printed |
| Band volume | section PROVEN -> MEASURED, in a total; CANDIDATE (two drawings disagree) -> PROVISIONAL, never in a total (owner Q-28 A); none -> HELD with length and area |
| Band at a footing | only the elevation overlap is already in the footing: band own depth = band depth - overlap, from printed levels of band and footing; levels not printed -> that crossing HELD `CROSSING_LEVELS_NOT_PRINTED` (owner Q-28) |
| Straps | centre line split into clear length (MEASURED at the schedule section when the drawn width is within 0.015 m of it), inside a closed footing (left to the footing, length only), inside an open outline (HELD); drawn width off the schedule -> HELD `STRAP_WIDTH_CONFLICT` (owner Q-16) |
| Natural-ground boundary beam | its own drawn band x its own printed section (MEASURED) or HELD; never reconciled with the band (owner Q-28) |
| Typical pads / boundary columns | a volume only with a printed count, else HELD `COUNT_NOT_PRINTED` |

Synthetic hand fixture (test docstring): 24 x 12 m plot band (71.20 m), footings as an insert on an annotation layer, a
mirrored insert, an open outline (gap 0.60 m), a closed polyline, a footing drawn twice (4 lines + polyline), columns on
and off a footing, an L and a U that are not footings, three straps (one into the open outline, one between two
footings, one with a width conflict), a natural-ground beam on two sides; run plain, rotated 37 degrees, in mm and in m:
free 63.30 m, in footings 4.60, in the open outline 3.00, in a column 0.30 (sum 71.20); band 7.596 m3 PROVISIONAL;
crossings 0.160 m3 (overlap 0.10 m deducted) and 0.120 m3 (different elevations, nothing deducted), one HELD; straps
1.140 + 0.560 m3, one HELD; natural-ground beam 35.80 m, 2.864 m3. All 30 tests pass.

## Alsenan by hand (Drive "Alsenan chalet project", "ST7757 dxf.dxf", sha256 9f9d1179...38079 = SOURCE_MANIFEST)

Read with the project's ezdxf / shapely in throw-away scratchpad scripts (not committed: they hold drawing coordinates).
The engine itself (route G + CONCRETE_LEDGER_V2, and this piece) was NOT run on the Alsenan drawing this run: the
session permission check refused it ("Permission for this action was denied by the Claude Code auto mode classifier.
Reason: [Code from External]"). Entities are named by DXF handle; lengths and sizes only.

### 1. How the footings on the plot edge are drawn

| Footing | Drawn as | Band centre line inside |
|---|---|---|
| C/F pad (handle 1668) | insert of block F (unit square on the footing layer) on the dimension layer, 0.80 x 0.90 | 0.90 m |
| C/F pad (1669), plot corner | same block, 0.90 x 0.80 | 1.50 m (0.80 + 0.70, corner once) |
| C/F pad (166A) | same block, 0.90 x 0.80 | 0.90 m |
| F11 (1B07) | OPEN polyline 3.50 x 1.50, gap 1.006 m on its own side (strap SB2 enters) | 3.50 m |
| F14 (1B1A) | closed polyline 3.80 x 3.30 | 3.80 m |
| F10 + F (1B1B) | OPEN polyline 3.25 x 1.40, gap 0.70 m on its own side (strap SB1 enters); owner Q-31: HELD | 4.45 m (3.15 + 1.30) |
| F8 (1B24) | closed polyline 4.00 x 3.60 | 3.60 m |
| F15 (1B2A) | closed polyline 1.80 x 1.00 | 1.80 m |
| FN (lines 1100-1103) | four loose LINEs 1.00 x 1.00 | 1.00 m |
| **9 outlines (10 footings)** | 4 inserts, 2 open, 3 closed, 1 line loop | **21.45 m** |

All 10 column outlines the band crosses lie inside these footings (5.70 m of band inside columns, 0 m outside a
footing). Band centre line 91.94 m (2 x 31.17 + 2 x 14.80), so free = **70.49 m**.

### 2. Every metre explained: hand vs the merged pieces

| Band record | Hand (drawing) | CONCRETE_LEDGER_V2 (T-060 run) | Strip-guard probe (T-058) | This piece, expected |
|---|---|---|---|---|
| free (not in any member) | 70.49 m | 73.64 m MEMBER_TYPE_PENDING | 78.54 m MEASURED | 70.49 m |
| inside closed footings / inserts / line loop | 13.50 m (C/F 3.30, F14 3.80, F8 3.60, F15 1.80, FN 1.00) | | | 13.50 m HELD, levels not printed |
| inside open outlines | 7.95 m (F11 3.50, F10 + F 4.45) | | | 7.95 m HELD, gaps 1.006 / 0.70 m |
| inside members, total | 21.45 m | 18.30 m (17 members) | 13.40 m | 21.45 m |

Why V2 has 18.30 m and not 21.45 m (reconstructed from the drawing, not from a V2 re-run): its member list misses only
the open F10 + F outline; the 1.30 m of band under the two columns inside that outline is still held, the other
**3.15 m** inside the outline is counted as free band. 21.45 - 4.45 + 1.30 = 18.30 m and 70.49 + 3.15 = 73.64 m, both
exactly the T-060 figures. The T-058 probe used closed polylines and columns only (F14 3.80 + F8 3.60 + F15 1.80 = 9.20 m, plus
4.20 m under the columns that stand in the other outlines = 13.40 m): it measured the rest of the 3 C/F inserts, F11
and F10 + F, 21.45 - 13.40 = 8.05 m, on top of footings (0.966 m3 at 0.20 x 0.60), as T-065 found.

### 3. Straps: the +0.39 m3 found

| Strap | Drawn width | Schedule | Clear length (hand) | Hand m3 | Engine now (T-037 run) | Cause |
|---|---|---|---|---|---|---|
| SB1 (1689 / 1B1C) | 0.70 | 70 x 50 | 4.55 m (F8 face to the F10 + F outline face) | 1.593 | 1.995 = 5.70 m | the route does not see the open F10 + F outline, so SB1 runs 1.15 m into it: **+0.403 m3** |
| SB2 (1B08 / 1B09) | 0.987 | 100 x 50 | 2.294 m (F11 outline to F3 outline, both open) | 1.147 (schedule width) | 1.132 PROVISIONAL (= 2.294 x 0.987 x 0.50, drawn width) | drawn width used instead of the printed 1.00: **-0.015 m3** |
| SB3 (1B26 / 1B27) | 0.502 | 50 x 40 | 3.251 m (F15 to the F3 pad) | 0.650 | about 0.654 (2.649 - 1.995) | drawn width 0.502 vs 0.50 (+0.003) |
| **total** | | | | **3.390** | **3.781** | +0.390 m3 = +0.403 - 0.015 + 0.003 (rounding) |

This piece gives SB1 4.55 m MEASURED (1.593 m3) + 1.15 m HELD inside the open outline, SB2 at the schedule width
(1.147 m3), SB3 0.650 m3: 3.390 m3 vs freelancer 3.3925 m3 (-0.0025 m3, -0.07 %).

### 4. Separate lines vs the freelancer (concrete, m3)

| Line | Hand / this piece | Engine now | Freelancer | Difference vs freelancer | Verdict proposal |
|---|---|---|---|---|---|
| Isolated footings | 64.346 + F10 / F HELD (T-065, not re-measured) | 64.304 + 1.960 PROVISIONAL | 65.634 | -1.288 (-2.0 %); F3 count +0.672 | as T-065: F3 ENGINE_RIGHT, F10 UNRESOLVED (Q-31) |
| Strap beams | **3.390** (SB1 1.15 m held) | 3.781 | 3.3925 | -0.0025 (-0.07 %); engine now +0.389 (+11.5 %) | ENGINE (this piece) RIGHT vs the current run: SB1 must stop at the F10 + F outline (hand 4.55 m); agrees with freelancer |
| Foundation boundary band, free | 70.49 m: **8.459 PROVISIONAL**, not in a total (0.20 x 0.60 candidate: schedule B.W vs typical 20 x 40) | 7.220 (60.17 m, frozen) / V2 held 73.64 m | 8.604 (71.7 m) | -0.145 (-1.7 %) provisional only | UNRESOLVED (owner Q-28 conditions: section over the whole band, levels at each crossing) |
| Band inside footings | 13.50 m HELD (levels not printed: founding level owner Q-21 C) + 7.95 m HELD in open outlines | not separated | apparently deducted | not compared | UNRESOLVED |
| Natural-ground boundary beam (ground-beam plan band, 7FE + 7FC + 810) | 44.07 m x 0.20 x 0.40 printed = **3.526** | not measured this run (engine run refused): whether the released run has a line for it is still open | 7.560 (42 m x 0.30 x 0.60) | -4.034 (-53.4 %) | ENGINE_RIGHT on the section (20 x 40 printed twice on the typical boundary-wall sheet; 0.30 x 0.60 not printed for this member); his 42 m vs 44.07 m UNRESOLVED |
| Boundary-wall pads 1.30 x 0.80 x 0.30, columns 0.20 x 0.30 | HELD, count not printed | none | none | - | HELD (RFI) |

Natural-ground beam lengths from the drawn band areas at 0.20 m: 7FE 8.344 m2 = 41.72 m, 7FC 0.230 m2 = 1.15 m,
810 0.240 m2 = 1.20 m. The 20 x 40 section is printed only on the PDF typical boundary-wall sheet (page 14), not in
the DXF: this piece takes it as a passed-in printed section, never as a default.

## What the team learned

- One drawing habit explains three defects: a footing outline left OPEN where a strap enters. The route's member list
  misses it, so (a) the band inside it is counted as free band (V2 +3.15 m), (b) the strap runs on into it (SB1
  +1.15 m, +0.403 m3), and (c) a probe that reads closed polylines only measures band on top of footings. Open
  outlines are now found (gap on the outline's own side) and held with the gap shown.
- Footings drawn as block inserts sit on an annotation layer while their geometry is on the footing layer; a layer
  filter on the insert loses them.
- A strap's printed schedule width must govern its section (the route used the drawn 0.987 m for a 1.00 m strap).

## Not done / uncertain

- The piece was not run on Alsenan (refused, above): the "this piece, expected" column is the hand reading of the same
  geometry rules; the verifier can run it (`footing_outlines` on the foundation-plan region, then `band_records` with
  the band polylines and `strap_records`) and must get 70.49 / 13.50 / 7.95 m and 3.390 m3.
- Not wired: binding the band and strap pairs from the route's findings (CONCRETE_LEDGER_V2 `finding_geometry` gives
  the band lines and members; `merge_members` takes them) is the wiring step of a later method version.
- Footing levels at the crossings wait on the founding level (owner Q-21 C); the band section on Q-28's conditions.
