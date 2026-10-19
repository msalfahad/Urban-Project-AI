# T-075: column schedule rows typed as plain text, and struck-out cells (development villa + synthetic fixture)

Worker 2, 2026-10-19 21:44-22:05 UTC. New reader `engine/source/column_schedule_text_rows.py` (SCHEDULE_TEXT_ROWS_V1)
beside the frozen SCHEDULE_READER_V1; nothing frozen edited, nothing wired into route G (wiring is a new route version,
T-079-style follow-up). Development villa (Alsenan), not an accuracy claim. Rules: UP-KB-PREC-001 (a printed value
wins), UP-QTY-STATUS-001 (held never 0); owner answers Q-16 (exhaust the drawing), Q-19 (no usual sizes), Q-21 = C
(neck heights held until the founding arrangement is verified).

## What was wrong (general, every villa)

Route G builds the schedule from block ATTRIB rows and reads text tables only when fewer than 3 attribute rows exist
(`generic_route.py:288-297`). A row typed as plain TEXT inside an attribute table is therefore dropped silently, and its
plan marks become TYPE_NOT_IN_SCHEDULE. A struck-out cell and a blank cell both read as "no band": the reader cannot
tell "no member at this level" (drawn evidence) from "value missing" (must be held).

## Method (summary; full text in the module docstring)

Per attribute table (owners sharing one tag set with a mark field): row direction from the attribute positions,
snapped to the table's own drawn lines (the Alsenan attribute inserts are not exactly aligned); frame = the border
verticals on which the full-width rules end; bands = full-width rules inside the frame; a text binds to the tag
column whose grid cell holds it (nearest tag when count and diameter share one REINF cell); a band with a mark in the
mark column becomes a row parsed by the frozen attribute parser itself. A strike = a line through the middle half of a
band running at least 25 % into a cell. Per level: PRESENT / STRUCK / EMPTY / MISSING_CELL / CONFLICT; only STRUCK
means "none at this level". `classify()` turns this into the effect on plan occurrences.

Why not `schedule_table.py` (V1): it cuts bands at every distinct horizontal line, so a strike-out line would split a
row band in two.

## Alsenan result (ST7757 DXF, sha256 9f9d1179...; schedules sheet SH11 = PDF p.9)

Column schedule: 12 attribute rows (C ... C11) + 1 text row found: **CN | foundation 30 x 30, 4 Ø14 | GF, 1F, 2F
struck by one drawn line (segment D2:7041)**. Strike-outs also read on the attribute rows C, C10 and C11 (1F and 2F,
segments D2:7215, D2:10821, D2:10822). Cross-checked against the PDF p.9 schedule (100 dpi): same CN row, same struck
cells (C, C10, C11 from 1st floor; CN from ground floor). Every other schedule row is byte-for-byte the frozen reader's
(76 rows identical, COLUMN unit cm with 100 % plausible share; only the CN row is added). No other column / beam /
footing mark typed as text on any schedule sheet is outside the schedule (checked: only notes 'L1', 'L3', 'S-2', 'S-3').
Beam schedules: frame not found (warning, nothing read); footing schedules: read, no text row, the REMARKS texts
(the lift-footing remark on FF) are reported, not read.

### The 14 held lines of T-036 cause F5 (T-042 Part A), one by one (ids as in research/agents_t044 run B)

| # | Engine line | Before | With this reader | Freelancer | Verdict proposal |
|---|---|---|---|---|---|
| 1-5 | STR.CONC.COLUMN `COL:SH12:CN@257027,56053`, `@261568,56053`, `@262379,59868`, `@262935,63411`, `@265215,56248` | HELD, TYPE_NOT_IN_SCHEDULE (3 with exposure 0.378-1.161 m3) | NOT_PRESENT, NECK_ONLY_TYPE: schedule CN row, GF / 1F / 2F struck (drawn) | 0 CN columns | agree: 0 lines (ENGINE_RIGHT on the schedule, hand-read on DXF and PDF) |
| 6-11 | STR.CONC.NECK `NECK:COL:SH10:CN@222091,55786`, `@216858,57078`, `@225897,54910`, `@223972,59262`, `@224210,63411`, `@222815,61757` | HELD, NECK_SECTION_OR_FOOTING ("no FOUNDATION band for CN") | HELD, FOUNDATION_DATUM_NOT_VERIFIED; section 0.30 x 0.30 = 0.090 m2 each (6 x 0.090 = 0.540 m2), 4 Ø14 | 6 x 0.30 x 0.30 x 1.50 = 0.810 m3 | section: agree; height 1.50 m not printed: UNRESOLVED (Q-21 = C) |
| 12 | `NECK:COL:SH10:C10@224867,51226` | HELD, no footing found | unchanged (attribute row; only 1F / 2F strike evidence added) | in his neck list | UNRESOLVED: corner footing outline open + labelled F10 and F (T-042 A2 RFI) |
| 13 | `NECK:COL:SH10:C@226940,50955` | HELD, no footing found | unchanged (as 12) | in his neck list | UNRESOLVED (as 12) |
| 14 | ground-slab cell 39.30 m2 with free columns | HELD | unchanged (not a schedule question) | - | UNRESOLVED (T-042 Part C 3) |

Count check: CN on the foundation plan 6 = freelancer 6; on the column plan 5 (the one beside C9 / F9 is not drawn
there, a drafting inconsistency already recorded in T-042; no quantity: CN has no column above ground).

### Engine vs freelancer (concrete, m3)

Released concrete unchanged: the reader is not wired, so no released line moves (last scoreboard 92.77 vs 111.81 m3,
not re-measured this run). When wired: 5 held CN column lines leave the held list as NOT_PRESENT (they were never in
the released total; freelancer also 0), and 6 CN neck lines gain a printed section (0.540 m2 together) but stay HELD
on the founding datum (freelancer 0.810 m3 rests on an unprinted 1.50 m neck height).

## Tests

`tests/t075_schedule_text_rows` (18): hand schedule with one attribute row, two TEXT rows, one MTEXT row, one neck-only
row struck by one line, one row with a blank cell, an empty band and a remark in an untagged column; variants mm,
metres, rotated 90 deg and 37 deg, mirrored, 1e6 offset, all combined, whole table in mm values; adversarial: a mm
text row in a cm table (held), a struck cell with a value (CONFLICT, held), a diagonal strike, a strike only touching a
cell (not a strike), no strike drawn (EMPTY, held, never "none"), no frame (nothing read), two values in one cell,
a row below the frame, a text typed over an attribute row (reported, not read), empty input.

## Not done / uncertain

- Not wired into route G (frozen); a route version must consume `read()` / `classify()`.
- Beam schedule tables: frame not found (row direction of the small BEAM-NAME tables is off by 2.5-3.7 deg; their
  rows are not checked for text rows).
- C10 / C corner necks and the 39.30 m2 cell remain held for other causes (T-042 A2, C3).
