# T-082: opening heights from PDF elevations and sections (method piece, not wired)

Worker 1, 2026-10-19 21:20-22:20 UTC. New files only: `engine/source/opening_height_pdf.py` (OPENING_HEIGHT_PDF_V1,
imported by no released method), `tests/t082_opening_height_pdf/` (hand villa SV-T082, 25 cases), this note. No frozen
file, rule or knowledge version, key map or released quantity changed; `engine/source/opening_area.py` (T-078) is read
and called unchanged. Development villa (Alsenan), not an accuracy claim. Rules: UP-OPEN-SCHED-001, UP-DOOR-AREA-001,
UP-DOOR-HGT-001, UP-QTY-STATUS-001, owner Q-32 = A (arched: to the top of the arch), Q-33 = A (windows aluminium),
Q-17 = A (a typed drawing value only through the controlled project data file), Q-38 = A / Q-39 = C (curved widths,
carried by opening_area's `curved_width_basis`), L-P9-02.

## What the piece does

A vector PDF elevation or section carries the same evidence as a DXF elevation, without dimension entities. The piece
rebuilds LINEAR dimension records from the printed numbers and hands `opening_area.measure` an ordinary view, so the
binding rules (width + position mapping on two places, jamb pairs, stacks, arch to the crown, schedule first, stale
prints never used) are exactly T-078's.

1. Scale: exactly one printed scale in the view ("1:100", "SCALE 1:50"), or one the caller read from the sheet title;
   none or two -> no dimension is used (never a scale-ruler value).
2. Dimension = a number along an axis-parallel line, ended on both sides by a tick / arrow / dot stroke; a chain drawn
   as one line is split at its ticks; a stroke that is part of a longer curve (an arch crossing the line) is never a
   tick; a plain corner (jamb meets sill) is never a dimension; two lines equally near -> AMBIGUOUS, not used.
3. Witness origins = far ends of the extension lines that END at the line (a ground line or sill passing through is
   not an extension line).
4. Printed unit (m / cm / mm) proven by at least two numbers agreeing with the geometry under one unit, strictly more
   than any other unit; else UNITS_NOT_PROVEN.
5. Sections also show interior doors: they run through `opening_area.measure` a second time with no opening skipped
   as interior, and are merged: one measured height -> released with its source; elevation and section differ ->
   HELD HEIGHT_CONFLICT (both values); none -> the elevation's hold reason with the section notes.
6. A RASTER_ONLY page (a scan) is never read (no OCR, no scaling): every held record names the scanned sheets and the
   route "a person reads the printed height into the controlled project data file (owner Q-17 = A)".

## Alsenan (development villa): what the PDF set can and cannot give

All 12 architectural PDF pages are SCANS: each page is one 4672 x 6624 px image with no text layer and no vectors.
Checked this run with `tools/urban_intake.read_pdf` on p7757_arch_sheet09.pdf (sha ff539473...) and
p7757_arch_sheet10.pdf (sha e20fcf2c...): `RASTER_ONLY`, 0 words, 0 segments; pages 1-2, 5-8, 11-12 recorded as the same
kind of scan by T-063. So this piece reads NOTHING from the Alsenan PDF, by design:

| Trade (Alsenan, aluminium workbook) | Engine | Freelancer | Difference | Change this run |
|---|---|---|---|---|
| Windows m2, measured | 4 of 29 windows, 13.892 m2 (T-078, DXF elevations) | 14.350 m2 for the same four | -0.458 m2 (-3.2 %) | none: the PDF elevations are scans |
| Windows m2, all | the other 25 not measured: 23 HELD in T-078's run, 2 recovered by T-077 and held; none at 0 m2 | 116.9 m2 | not comparable | hold reason now names the scanned sheets and the Q-17 route |
| Doors m2 | 0 measured; 22 interior HELD, outdoor doors HELD | 12.0 m2 aluminium doors | not comparable | none |

Proof that the engine figures cannot move: with no PDF view and no section view `measure_pdf` returns
`opening_area.measure`'s records unchanged and only adds evidence to held records (test
`test_scan_face_held_with_route_never_zero`; code path `measure_pdf`, the merge loop). The Alsenan re-run itself
(`tools/urban_boq_m9.py arch` + the T-078 runner) was NOT made: that tool is outside this run's execution
authorization (clone, venv, codemap, freeze, pytest, scoreboard and key map only). The figures above are T-078's,
verifier-merged in 5f07bf0.

### Hand reading of the two sheets the task names for door heights (read visually at full resolution)

| Sheet | View | What is printed | Opening heights printed |
|---|---|---|---|
| p7757_arch_sheet10.pdf | SECTION A-A 1:100 (through the stair hall, drawn turned 90 deg on the sheet) | levels +-0.00, +0.15, +0.30, +1.00, +5.50, +9.70, +13.90; chains 450 / 420 / 420 / 50 (left), 100 / 870 / 420 / 50 = 1440 (right), 550 / 50 (annex edge), 320 (from +0.30 to the soffit of the stair landing over the entrance lobby) | NONE. Drawn beyond the cut: a GF double door (panelled), two 1F doors, a 2F arched window, the dog-leg stair. No door or window height, sill or head is printed. The "320" ends at the landing soffit, not at a door head (no jamb pair is drawn there): it is not a door height |
| p7757_arch_sheet09.pdf | titled NORTH EAST ELEVATION 1:100, drawn as a cut through the GF annex and the GF hall | levels +-0.00, +0.15, +0.30, +1.00, +4.30, +5.50; chains 480, 400, 450, 550 / 50, 100 / 870 / 420 / 50 = 1440, 130 | NONE. Drawn: 3 annex doors, 3 GF hall doors, the curved stair, 3 windows on the 1F block face (two small, one larger). No opening height, sill or head is printed |

Verdict proposals from this reading: every door seen on A-A and on sheet 9 stays HELD NO_PRINTED_HEIGHT (UNRESOLVED,
not a freelancer error: the drawing prints nothing; a drawn size would be a scaled value, which the owner's
no-assumptions rule forbids). The freelancer's door heights (2.00 m class rows) therefore have no drawing source on
these two sheets. The hand table of every printed opening height on the elevations (sheets 6-8) is T-083's
(worker 2, claimed 20:42); it is the check for any Alsenan figure this piece would feed through the project data file.

## Tests (non-Alsenan hand villa SV-T082, tests/t082_opening_height_pdf, 25 cases)

South elevation 1:100 in cm (stacked windows, an outdoor door with its dimension outside and extension lines, an arched
window drawn with Bezier curves whose arch crosses the crown dimension line), a north elevation that is a scan (held
with the route) and in a variant a vector north elevation 1:50 in MILLIMETRES seen MIRRORED, a section A-A that gives
two interior doors. Hand total: windows 10.035 m2, outdoor door 2.880 m2, interior doors 1.890 + 2.200 m2 from the
section; mm variant adds 0.960 + 0.600 m2. Adversarial: no scale (nothing used), scale from the title by the caller,
two scales, caller scale against a printed one, stale print, missing height print, missing width, one number only
(units not proven), a number between two lines (ambiguous), a chain drawn as one line (split), a number beside a jamb
(corner is no dimension), plan rotated 30 / -123 deg and mirrored, section agrees / conflicts with the elevation
(HELD HEIGHT_CONFLICT 1.50 vs 1.55), an outside window on the same range as a section door (door held), a raster page,
inputs not mutated, a REAL PDF round trip through `page_primitives` (pymupdf writes lines, Beziers and rotated text;
same hand areas) and a scanned PDF read as RASTER_ONLY. A mutation check (curve guard switched off) turns the arched
window into ARCH_TOP_NOT_PRINTED, so the guard is load-bearing and covered.

## Learned / missing

- Alsenan's whole architectural PDF set is scanned: no code path can read its printed heights without OCR, and the
  engine policy keeps RASTER_ONLY out of released millimetres (engine/space_objects.py UNMEASURED_SOURCES). The only
  owner-approved route for those 25 windows and the doors is a person typing each PRINTED value into the controlled
  project data file (Q-17 = A, task T-064), checked against T-083's hand table. No owner question is needed for that.
- Sections A-A and sheet 9 print storey chains only; door heights on Alsenan are not printed anywhere read so far.
- opening_area projects every opening parallel to a view onto it, so a north-face window is reported on the south
  elevation as NOT_DRAWN_ON_THIS_ELEVATION (not NO_ELEVATION_OF_THIS_FACE); a section sees openings of several
  depths on one range, which the stack rule holds (test of D3 with a window behind it).
- Not done: wiring (a new ARCH_TAKEOFF version, T-079 queue); OCR of scans (out of policy); dimension styles without
  ticks / arrows / dots (their numbers stay unbound, never guessed); text-only dimensions with no drawn line.
