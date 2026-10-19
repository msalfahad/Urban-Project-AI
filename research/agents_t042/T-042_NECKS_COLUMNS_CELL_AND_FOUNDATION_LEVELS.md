# T-042: the 14 held column / neck / ground-cell lines, and the foundation level arrangement (development villa)

Worker 3, 2026-10-19 14:00-15:10 UTC. Hand reading only (NO REPO CODE row): no engine, rule, test, profile, fact file
or quantity changed. Development villa (Alsenan), not an accuracy claim. Values, sheet references and engine element ids
only; no images, no client names, no plot data. Rules: UP-QTY-STATUS-001 (held stays held, never 0), UP-HGT-001
(heights from the drawing with source), UP-KB-PREC-001 (a printed value wins); owner answers Q-12, Q-16, Q-17, Q-19,
Q-20, Q-21. Grades: PRINTED (sheet, text, value) / NOT_PRINTED / VISUAL (seen on the drawing, no text) / INFERRED
(from printed values, logic named) / CONFLICT.

## Inputs (read in the session scratchpad, never committed)

| Input (Drive "Alsenan chalet project") | sha256 | How read |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 (= profile and manifest) | ezdxf 1.4.4: 2 630 texts (TEXT / MTEXT / ATTRIB / DIMENSION, nested inserts) = T-044 count; line work per frame; frames FR08 (SH08 ground beams), FR10 (SH10 foundations), FR11 (SH11 schedules), FR12 (SH12 columns and axes) rendered and read visually |
| "ST7757.pdf" (16 pages, scanned glyphs) | 74da1523...337e3 | p.8 general notes (Arabic, visual), p.9 schedules (200 dpi), p.13 typical footing / ground-beam details (300 dpi) |
| "P7757_DXF_COMPRESSED.zip" / P7757.dxf | ab54dd55...31cc4 (= manifest) | ground floor plan rendered and read visually |
| "Alsenan_Architectural_P7757_Pages_11-12" | not hashed | p.11 SECTION B-B read visually at 150 dpi |
| "..._Pages_09-10" (SECTION A-A) | - | NOT_READ: the Drive connector closed the connection again ("message from the server was too large"), as for T-063 |
| Freelancer rows | `tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json` (committed) | concrete workbook sheets "footings", "walls + columns", "ground beams" |
| Engine lines | `research/agents_t044/T-044_RUN_B_LINE_DEPENDENCIES.csv`, `research/urban_engine_m4_correctness/st7757_route_g/*.csv` (committed) | the 14 held lines and their hold reasons; the engine was NOT run in this task |

## Part A: the 14 held lines

The 14 lines are T-036 causes C7 (5 column lines), C8 (8 neck lines) and C12 (1 ground-slab cell), the same ids in
run A and run B (T-044 CSV, status HELD).

### A1. Column type CN: it IS in the column schedule (ENGINE_MISSED_PRINTED_VALUE)

What the drawing prints:
- ST7757 schedules sheet (DXF frame SH11 = PDF p.9), "Schedule of Columns": after row C11 come four empty table rows and
  then a last row **CN | foundation 30 x 30, 4 Ø14 | ground floor, 1st floor, 2nd floor & top: struck through (no
  section, no bars) | design load: blank** (PRINTED, PDF p.9 read at 200 dpi; DXF the same text).
- ST7757 column and axis plan (SH12): five columns labelled **"CN 30X30"** (the section is printed on the plan too).
- ST7757 foundation plan (SH10): six CN columns: four labelled "CN/FN" (one written as "CN" over "FN"), one "CN" inside
  the C4/F4 footing outline, one "CN" inside the C8/F8 footing outline.
- Footing schedule (SH11 / p.9): **FN 100 x 100 x 30, 8 Ø12 short, 8 Ø12 long** (PRINTED; the engine reads this row
  and already measures the 4 FN footings: 0.300, 0.300, 0.258 (clipped by the F9 outline), 0.300 m3).

Why the engine held them (a reader defect, not a missing value): route G builds the schedule from block attributes
(`engine/source/generic_route.py:288`, `SR.from_attribute_rows`) and reads the text table only when fewer than 3
attribute rows exist (`:289-297`). Every row C ... C11 of the column schedule is an ATTRIB of a schedule block; the CN
row is plain TEXT (style S-ITALICT, layer S-TEXT.SCH, below four empty rows), so it never reaches the schedule library.
The footing schedule row FN is an ATTRIB and is read. General lesson: a schedule row typed as plain TEXT inside a
block-attribute table is silently dropped; the reader must take TEXT cells that sit inside the table's own frame too.

What CN is, from the schedule: a column type with a FOUNDATION (neck) section only; the ground, first and second floor
cells are struck through, so **CN has no column above the ground beams**. The freelancer reads it the same way: six
"CN 0.3 x 0.3 x 1.5" necks (0.81 m3) and no CN in his ground, first or second floor column lists.

Neck-to-plan check (frame-relative positions of the 300 x 300 CN outlines, S-COL.BON): SH10 has 6, SH08 has the same 6
(one shifted 100 mm in x), SH12 has 5: the one beside the C9/F9 footing (labelled CN/FN on SH10) is not drawn on the
column plan. Since CN has no column above ground, the column plan omission changes no quantity; it is a drafting
inconsistency (recorded, not settled).

| # | Engine line (as the engine names it) | Engine now | What the drawing prints | Classification | Correct output |
|---|---|---|---|---|---|
| 1-5 | STR.CONC.COLUMN `COL:SH12:CN@...` x5 (storey UNKNOWN; TYPE_NOT_IN_SCHEDULE; 3 with exposure 0.378-1.161 m3 each, 2 none) | HELD | schedule row CN: no section on GF / 1F / 2F (struck); plan label "CN 30X30" | ENGINE_MISSED_PRINTED_VALUE | no superstructure column line: these 5 plan symbols are the CN necks seen on the column plan (counting them as columns would double count the necks). Not a freelancer item either |
| 6-11 | STR.CONC.NECK `NECK:COL:SH10:CN@...` x6 (NECK_SECTION_OR_FOOTING: "no FOUNDATION band in the schedule for CN") | HELD (5 with exposure 0.045-0.225 m3, 1 none) | section 0.30 x 0.30 = 0.090 m2 (schedule + plan); footing under each: FN 0.30 deep (4), F4 0.40 deep (1), F8 0.50 deep (1) | ENGINE_MISSED_PRINTED_VALUE for the section and the footing; height still HELD (Part B, owner Q-21) | 6 neck lines, section 0.090 m2 each, footing depth as listed, height HELD (FOUNDATION_DATUM_NOT_VERIFIED); 0.090 m3 per metre of neck height |

### A2. The 2 scheduled necks "with no footing under them": the footing is drawn (engine binding defect)

Lines: STR.CONC.NECK `NECK:COL:SH10:C10@...` and `NECK:COL:SH10:C@...` (NECK_SECTION_OR_FOOTING, "no footing found
under the column"; exposure 0.105-0.525 and 0.075-0.375 m3).

What the drawing prints (SH10, bottom right corner of the plot, on the neighbour-side boundary):
- One footing outline on layer S-FOOTINGS (handle 1B1B), an OPEN polyline: 3.25 x 1.40 m, broken where the two strap
  lines of S.B1 (handles 1689, 1B1C) enter it. Both columns stand inside it at its bottom edge: C10 (0.70 x 0.30,
  schedule foundation 30 x 70) and C (0.30 x 0.50, schedule foundation 30 x 50, at the plot corner).
- The outline carries two footing labels: "F10" (left part) and "F" (right part). Schedule: F10 = 280 x 140 x 50,
  F = 90 x 80 x 30.
- The left end of the outline is exactly 1.40 m from the C10 centre, so F10 (2.80 long) centred on C10 runs from that
  end to 0.45 m short of the outline's right end (INFERRED from the printed F10 length and the drawn C10 position);
  the right 0.45 m and the corner column C lie outside F10. F (0.90 x 0.80) cannot produce a 1.40 m wide part, so the
  drawn union does not match either schedule size alone: **CONFLICT** (drawn combined outline 3.25 x 1.40 vs two
  schedule types; depth 0.50 for F10 vs 0.30 for F).
- Engine: the footing is already measured once as a PROVISIONAL label-conflict line (`FTG:SH10:T652:10A5`, "one footing
  labelled with two types and no outline found", taken at F10 1.960 m3; the freelancer also lists F10 1.96 m3 and four
  F footings 0.216 m3 each). The neck code does not find "a footing under the column" because the outline is open.

| # | Line | Classification | Correct output |
|---|---|---|---|
| 12 | NECK C10 | ENGINE_HELD for the wrong reason: section PRINTED (0.30 x 0.70 = 0.210 m2), footing DRAWN (F10, 0.50 deep, INFERRED as above); height HELD on the datum (Q-21) | hold with reason FOUNDATION_DATUM_NOT_VERIFIED, not "no footing" |
| 13 | NECK C (corner) | as 12: section 0.30 x 0.50 = 0.150 m2; footing depth 0.30 (F) or 0.50 (F10 outline) is the CONFLICT above; height HELD (Q-21) | hold; the footing-depth conflict is an RFI (wording below) |

### A3. The 39.30 m2 ground cell with free columns (C12)

Engine line: STR.CONC.GROUND_SLAB `GROUND_SLAB:GROUND:SITE-c1089bdb4cfcdc4a`, SLAB_CELL_FREE_COLUMNS, 39.298 m2 x 0.10
= 3.930 m3 held. Its position is not in any committed output (the engine was not run here). The only committed
SLAB_CELL_FREE_COLUMNS ground cell with a position is the M4 run's `SITE-f65941a3e35ac31e` (49.07 m2 gross, 44.92 net,
SH08, at the stair hall), whose overlay splits it into a cell between members 29.06 m2, a stair flight zone 11.52 m2, a
pit opening 3.24 m2 (the 1.80 x 1.80 shaft) and beam / wall strips. Taking the 39.30 m2 cell to be this stair-hall
cell is a **probable identification, not verified**: the verifier (who can run route G) should confirm by the cell's
position before using the verdict below.

What the drawings print at the stair hall:
- ST7757 SH08: the cell is bounded by ground beams; inside it stand the four columns at the corners of a hatched
  1.80 x 1.80 box (C1, C2, C2, C9 on the column plan), i.e. the columns stand on the shaft walls, not on ground beams.
  SH08 prints the ground slab as "T=10cm, 5Ø10/m E.W." (two callouts, main house and annex) and the level "+1.00".
- P7757 ground floor plan: the area is the internal stair hall (main dog-leg stair, flights 1.20), corridor and W.C. /
  bath at FFL +1.00, and the unlabelled 1.80 x 1.80 shaft (lift, T-063 section 5). Courts are outside, at +0.15. No
  "VOID" or "COURT" label in this cell (the two VOID labels of the set are on the first floor plan).
- Architectural SECTION B-B (p.11): the ground floor at +1.00 is drawn on hatched earth fill above ±0.00.
- ST7757 p.8 note 19: lift columns are tied by beams around the lift shaft (a lift shaft is intended there).

Classification: **ENGINE_MISSED_PRINTED_VALUE** for the floor part: the cell is an internal ground-bearing slab
(T = 0.10 m printed on SH08), not a court and not a void; the "free columns" are the lift-shaft corner columns standing
on the shaft walls. Two parts stay out of the slab: the shaft footprint (lift pit: depth NOT_PRINTED on every sheet
read, T-063; held as its own item, never 0) and the stair flight footprint (already a separate stair-zone line).
Rule for the engine (general, every villa): a ground cell whose free columns sit at the corners of a closed shaft
outline is a slab with a shaft opening, decided by the architectural plan label / shaft symbol; with no architectural
evidence it stays held as today.

### A4. Summary of the 14 lines

| Cause | Lines | Engine now | Drawing | Verdict proposal |
|---|---|---|---|---|
| C7 CN "columns" on SH12 | 5 | HELD (3 x 0.378-1.161 m3 exposure) | CN has no column above ground (schedule, PRINTED) | ENGINE_MISSED_PRINTED_VALUE: should be no column line (0 lines, not 0 m3 of a held line); freelancer agrees (no CN column) |
| C8 CN necks | 6 | HELD | section 0.30 x 0.30 PRINTED twice; footings FN x4, F4, F8 | ENGINE_MISSED_PRINTED_VALUE (section); height HELD (Q-21) |
| C8 C10 and C necks | 2 | HELD ("no footing") | footing drawn (open outline), F10 / F label conflict | held correctly in result, wrong reason; footing depth conflict for C = RFI |
| C12 ground cell | 1 | HELD 39.30 m2 | internal floor at +1.00, slab T=0.10 printed, lift shaft inside | ENGINE_MISSED_PRINTED_VALUE (identification to be confirmed by the verifier) |

Engine vs freelancer, necks (m3, development reference): freelancer necks 8.805 m3 = 34 necks x 1.50 m (C1 1, C2 4,
C3 5, C4 2, C5 3, C6 1, C7 1, C8 2, C9 2, C10 1, C11 1, C 5, CN 6); his 1.50 m height is printed nowhere (it equals
the "not less than 1.5 m" excavation note, Part B). Engine run B: 28 necks released 10.856 m3 on the datum the owner
has held (Q-21), 8 held. Count: the foundation plan shows 30 non-CN necks (C 5, C1 1, C2 4, C3 6, C4 2, C5 3, C6 1,
C7 1, C8 2, C9 2, C10 1, C11 2) + 6 CN = 36 = engine 28 + 8; the freelancer has 34 (one C3 and one C11 fewer: plan
count by label, VISUAL, to be checked by the verifier). CN neck concrete itself: freelancer 0.810 m3 (6 x 0.09 x 1.50);
engine held; hand: 6 x 0.090 m2 x (neck height, HELD) = 0.540 m3 per metre of height. Not compared until Q-21 is
resolved by the designer.

## Part B: foundation level arrangement (owner answer Q-21)

### B1. Level table

| Level / term | Value | Grade, where |
|---|---|---|
| Existing ground (plot) level | ±0.00 at the plot corners and boundary; +0.15 courts; +0.30 entrance and annex floor | PRINTED: SH08 level symbols "%%p0.00" (6), "+0.15", "+0.30"; P7757 GF plan the same; B-B "±0.00" |
| Excavation (formation) level | "not less than 1.5 m below the existing plot level" | PRINTED as a MINIMUM: SH11 / p.9 boxed note 1 (Arabic). Which surface it is (bottom of the plain concrete, of the footing, or neither) is NOT_PRINTED |
| Founding level | to be confirmed by the contractor from the architectural and structural drawings and a soil inspection, approved by the supervising engineer before work starts | PRINTED as an instruction, no value: p.8 note 12; p.8 note 10: no foundation on made (filled) ground, contractor to test the soil bearing (2.20 kg/cm2, note 2 of p.9) at his cost |
| Bottom / top of blinding | thickness 10 cm ("10cm Plain con."), projection 10 cm each side of footing and ground beam | PRINTED (p.13, both footing details, all four ground-beam sections); its LEVEL is NOT_PRINTED |
| Layers between blinding and footing | **"5cm Screed" and "Insulation membrane" / "Water proofing membrane"** under the footing, dimensions "10", "5" and "2" stacked at the footing base | PRINTED p.13, both typical footing details (new: not in the route G profile and in no engine or freelancer line). The "2" carries no unit or label (membrane? NOT read) |
| Bottom of footing | NOT_PRINTED as a level | p.13 dimensions the footing depth "D" only; schedule H per type (0.30 - 0.70) |
| Top of footing | NOT_PRINTED as a level | = bottom + H, needs the bottom |
| Column neck start / end | start = top of footing (drawn, p.13); end = the ground beam (detail 2) or the upper ground beam (detail 1): NOT_PRINTED as levels | p.13 |
| Ground beam top | "Ground Floor slab level" for the exterior ground beam | PRINTED for the exterior beam only (p.13 "Ground Beams for exterior walls", depth "FOLLOW ARCH.", bottom at "Outer Normal ground level"); interior beams: NOT_PRINTED |
| Upper GB top to footing bottom | detail 1 "MORE THAN 2.5m" (two rows of ground beams, upper and lower) / detail 2 "LESS THAN 2.5m" (one row) | PRINTED as a condition, not a value (p.13): **which detail applies depends on the unprinted datum** (see B3) |
| Finished floor (GF) | +1.00 (main house), +0.30 (annex) | PRINTED: SH08 "+1.00", P7757 plans, B-B |
| Finished ground outside | ±0.00, courts +0.15 | PRINTED as above |
| Backfill material | "Well graded clean compacted fill from excavation material"; "COMPACTED SOIL" under the ground beam | PRINTED p.13 details 1 and 2 |
| Waterproofing | "Two layers liquid water proofing to be applied to all surfaces in contact with earth" | PRINTED p.13 |
| Ground water | at 4.5 m | PRINTED p.9 note 4 |
| Architectural sections | B-B: GF +1.00 drawn on hatched earth fill above ±0.00; no foundation drawn | p.11; A-A not read (connector limit) |

Conclusion: **the drawings do not print a complete foundation level arrangement.** They print the existing ground,
the finished levels, the layer thicknesses below the footing (10 cm plain concrete, membrane, 5 cm screed) and a
MINIMUM excavation depth of 1.5 m, but not which surface that 1.5 m refers to, nor any footing, neck or ground-beam
bottom level; the structural notes themselves leave the founding level to the contractor and supervising engineer
after a soil inspection (p.8 note 12).

### B2. Separate measurement items (owner Q-21 list)

| Item | Needs | Printed? | Status |
|---|---|---|---|
| Excavation | existing ground (PRINTED), formation level (NOT_PRINTED: only a 1.5 m minimum), plan extent (footings + blinding projection PRINTED; working space NOT_PRINTED) | partly | HELD (FOUNDATION_DATUM_NOT_VERIFIED) |
| Disposal of unsuitable material | soil report / designer instruction | NOT_PRINTED (p.8 notes 10, 12 require a soil test; no quantity) | HELD (needs soil investigation; never assumed) |
| Approved replacement fill | as above | NOT_PRINTED | HELD |
| Compaction | areas and layers of fill; "compacted soil" / "well graded clean compacted fill" PRINTED as a specification | spec only | HELD (depth needs the datum) |
| Blinding concrete | plan area of footings and ground beams + 10 cm each side, x 0.10 m | PRINTED (p.13) | RELEASABLE without any level (plan quantity). Engine run B 22.155 m3 on this basis; freelancer 47.055 m3 = whole plot 15.00 x 31.37 x 0.10 (a basis printed nowhere): verdict proposal RULE_DIFFERENCE, owner to confirm the Urban basis (no rule found here) |
| 5 cm screed + membrane under footings | footing plan areas | PRINTED (p.13) | measurable on footing plan area; in NO engine line and NO freelancer line: possible silent omission in both (proposed follow-up, not measured here) |
| Footings | L x W x H per schedule | PRINTED | RELEASABLE (level-independent); engine 77.27 m3 vs freelancer 77.63 m3 (split by member: T-065) |
| Column necks | section (PRINTED) x height (footing top to ground beam: NOT_PRINTED) | partly | HELD: do not compute the 28 (+8) necks on an unresolved datum (owner Q-21) |
| Backfill | excavation minus buried concrete, to the levels above | spec PRINTED, levels NOT_PRINTED | HELD |
| Lower ground beam row (detail 1) | the level difference upper GB top to footing bottom | condition PRINTED, value NOT_PRINTED | HELD as an open question of existence (B3) |

### B3. Why the datum matters more than 10 cm (illustration only, nothing applied)

With GB top at the GF slab level +1.00 (printed for the exterior beam) and the layers printed under the footing
(0.10 plain concrete + membrane + 0.05 screed):
- if 1.50 m is the excavation formation (bottom of the plain concrete), the footing underside is about -1.35 and the
  level difference GB top to footing bottom about 2.35 m: detail 2 (one ground-beam row);
- if 1.50 m is the footing underside, the excavation goes to about -1.65 and the difference is 2.50 m, exactly the
  boundary between "less than" and "more than 2.5 m": detail 1 would add a LOWER ground-beam row.
So the unresolved datum changes the neck heights by about 0.15 m (not 0.10), the excavation depth, the backfill, and
possibly the existence of a second ground-beam row. The structural set prints only one ground-beam plan (SH08).

### B4. Proposed owner / designer question (for the Lead; NOT added to OWNER_QUESTIONS.md)

The owner already answered Q-21 = C (hold until the arrangement is verified). This reading shows the drawings cannot
verify it, and p.8 note 12 makes the founding level a site decision of the supervising engineer, so the natural next
step is an RFI to the designer rather than an owner rule. Proposed wording (Lead decides):
"Alsenan structural set ST7757: the schedules sheet prints 'excavation level not less than 1.5 m below the existing
plot level'; the typical footing details (p.13) print under every footing 10 cm plain concrete, a membrane and 5 cm
screed, and two ground-beam arrangements (one row when the level difference between the upper ground beam and the
footing is less than 2.5 m, two rows when more). Please give the founding level (underside of footing) and the top of
ground beams, and say which ground-beam arrangement applies. Choices for the BOQ meanwhile: (a) hold necks, excavation,
backfill and any lower ground-beam row until the designer answers (today); (b) 1.50 m = bottom of the plain concrete
(footing underside about -1.35, one ground-beam row); (c) 1.50 m = footing underside (excavation about -1.65, check the
two-row detail). Recommendation: (a), because the founding level is safety-critical and the notes leave it to the
supervising engineer after a soil inspection (practice, not a code clause)."
Second RFI (corner footing): "SH10 bottom-right corner: one footing outline 3.25 x 1.40 m is labelled both F10
(2.80 x 1.40 x 0.50) and F (0.90 x 0.80 x 0.30) and carries columns C10 and C: is it one combined footing (depth?) or
F10 plus F?"

## Part C: proposed fix tasks (general, every villa; one each)

1. Schedule reader: read TEXT rows that sit inside a block-attribute schedule's table frame (the CN row here); a type
   whose upper-storey cells are struck through is a neck-only type, so its column-plan symbols produce no
   superstructure column line (new route version; `generic_route.py` is FROZEN). Synthetic fixture: attribute table
   + one TEXT row after empty rows, struck cells, mm and m.
2. Neck-to-footing binding: accept a footing outline that is open where a strap or ground beam enters it (close it
   along the strap faces) before reporting "no footing found"; two footing labels in one outline stay a conflict.
3. Ground cell with free columns: classify by the architectural plan (shaft symbol or label, room label, level) as
   slab with a shaft opening / void / court; no architectural evidence keeps it held.
4. Below-footing layers: measure the printed screed and membrane under footings as their own lines (plan area), held
   where not printed; never folded into blinding.

## Who-is-right proposals (for the verifier)

- CN superstructure columns (5 lines): ENGINE_HELD is wrong in kind; the printed schedule says none. With the fix the
  engine and the freelancer agree on 0 CN columns above ground. Proposal for the current line: ENGINE should not
  report them (counts against the engine only as a held false line, no m3 effect on released totals).
- CN necks: section 0.30 x 0.30 (PRINTED): freelancer section right, his 1.50 m height NOT_PRINTED: UNRESOLVED (Q-21).
- Necks overall (engine 10.856 released on the profile datum + 8 held vs freelancer 8.805 at 1.50 m): UNRESOLVED
  until the designer prints the founding level (both rest on unprinted heights).
- Blinding (engine 22.155 vs freelancer 47.055 m3, -53 %): RULE_DIFFERENCE proposal: the engine follows the printed
  detail (under footings and ground beams + 0.10), the freelancer covers the whole plot 15.00 x 31.37; no Urban rule
  found that decides it (owner to confirm the basis).

## Not done / uncertain

- SECTION A-A (p.10) not read: the Drive connector refuses the 6.37 MB part (as for T-063).
- The 39.30 m2 cell is identified by the M4 record, not by a run of the current engine.
- Freelancer neck counts per type compared with plan labels by eye; a C3 and a C11 difference (34 vs 36 necks)
  needs the verifier's count.
- The "2" in the stack at the footing base (p.13) is not read as a value.
