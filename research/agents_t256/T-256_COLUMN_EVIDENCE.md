# T-256 CONC.COLUMN: the 15 CONFLICT columns and the 5 NOT_DRAWN lines, narrowed to per-column evidence (Alsenan; every villa)

Worker 1 (lane S), 2026-10-24, run session_01BZYE1kYU3BhxhKPFvm8yGn. Research piece, unwired: no engine module, method,
candidate, route G or released line changed; nothing applied (lane I decides after the Checker). Development villa, not
an accuracy claim. Drawings named by Drive folder and title; members by DXF handle; no coordinates committed.

## 0. Inputs and runs (own, this task)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| 'ST7757 dxf.dxf' | 9f9d1179... (= manifest) | slab-plan outlines, schedule rows (INSERT CGT), CAP prints, every text, the beam schedules, slab-plan sections |
| 'ST7757.pdf' (16 pages, vector, A3, 1:100; p.8 the only raster) | 74da1523... | the issued plot: p.1 CAP, p.2 FP, p.3 GBP, p.4-6 slab plans, p.9 schedules, p.10-12 beam schedules, p.13-16 details |
| 'P7757_DXF_COMPRESSED.zip' -> P7757.dxf | ab54dd55... (= manifest) | the architectural plans GF / 1F / 2F (column layer, dimensions, wall lines) |

Files: `column_evidence.py` (COLUMN_EVIDENCE_V1, rule proposal R-COLUMN-EVIDENCE-1, stdlib), `t256_extract.py` (private
files -> values-only `ALSENAN_T256_EVIDENCE.json`; PDF part needs PyMuPDF), `t256_alsenan_check.py` -> `LEDGER_T256.csv`
(15 rows) + `summary.json`; tests `tests/t256_column_evidence` (21: Villa M hand fixture + adverse + Alsenan pinned).
Member list and heights: the merged T-248 ledger (LEDGER_T248.csv, MERGED 567dc972), not re-derived.

## 1. The physical element and the question (ERS s.2.1)

Each CONFLICT member is one storey column (C1: section x (slab top - base), datums DRAWING-CONFIRMED by T-214 / T-248:
GF 4.50 m, 1F 4.20 m). Its SECTION has two readings: the schedule band of its type (printed) and the outline its own
slab plan draws (not printed: no size text, no dimension at any column on p.4-6). The question is whether any THIRD
source, independent of those two and drawn for this member, prints its section.

## 2. Every sheet that could print a column section, searched (both formats)

| Sheet | What it gives at a GF / 1F column | Third source? |
|---|---|---|
| p.9 'Schedule of Columns' (DXF INSERT CGT; also DES. LOAD, REINF) | the type x band section: one of the two readings | it IS reading 1 |
| p.4 / p.5 slab plans (DXF GFRS / FFRS) | the drawn outline (reading 2); no size text, no dimension at any of the 15 (0 / 15) | it IS reading 2 |
| p.4 SECTION A-A, C-C, D-D; p.5 SECTION B-B | beam sections (B 40 x 75 bars, 'AS PER SCH.'): no column cut | no |
| p.1 CAP (texts 'WxD' + dimension chains) | the FOUNDATION member (neck) only, band FOU; nothing for GF / 1F | context only (another member) |
| p.10-12 beam schedules (simple, 2-span, 3-span) | supports drawn as schematic triangles; no column widths | no |
| p.13-16 details | typical only; p.15 'TYP. DETAIL OF TWISTED COLUMN' x2: 'column in ground' dimensioned 25, 'column in first' drawn narrower, unprinted | not member-specific |
| p.4-6 PDF plot | every SOLID outline re-measured from the vector fills at 1:100: 20 / 21 (1F), 30 / 34 (GF), 9 / 9 (2F) agree with the DXF within 10 mm; the 15 all agree; the unfilled ones are the P.C / T.C start outlines (hatched, not filled) | a plot of the same drawing: confirms what was issued, adds no reading |
| Architectural GF / 1F plans (P7757.dxf) | its ONLY column layer is the structural 'S-COL.BON': 59 outlines = 30 / 20 / 9, each on a structural outline by one translation per storey, spread 0.000 m, every size identical (the one GF mismatch is the C9 T.C pair: the plan copies the SOLID GF part 37A, not the turned 322) | a copy of the structural layer: not independent |
| Architectural dimensions at the 15 | 0 with both points on the column faces; 10 dimensions on 6 members touch one face. Example 1F C9 679: chain 1800 / 200 / 1470 where '200' runs from the column face to the far face of the 0.20 wall (wall lines on layer '1'), not across the 0.25 column | no |

**Result: no third independent, member-specific printed source exists for any of the 15. All 15 stay CONFLICT
(printed vs drawn).** The two derived copies (plot, architectural layer) were checked so that the next reader does not
count them as evidence: they repeat the drawn outline.

## 3. Per-column evidence (task item a)

Areas and volumes are the T-248 ledger's (re-computed equal). 'Differs in' = which side the two readings disagree on.
'Drawn = GR' = the 1F outline equals the GR (ground-floor) band of its type. Walls = the architectural wall faces that
run through the member (mm from the outline face).

| Member | Storey, mark | Neck | Schedule (row) | Drawn mm (DXF / PDF) | Arch copy | Differs in | Drawn = GR | Arch walls through it | m2 | m3 at h | Designer item |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GFRS 347 | GF C | 10A4 | GR 20x50 (1D03) | 200x400 / 199x398 | 2F99 same | long side | - | 0.20 both ways | 0.08 .. 0.10 | 0.360 .. 0.450 | NEW (band) |
| GFRS 359 | GF C | 10B7 | GR 20x50 (1D03) | 400x200 / 402x199 | 2FAB same | long side | - | 0.20 both ways | 0.08 .. 0.10 | 0.360 .. 0.450 | NEW |
| GFRS 344 | GF C3 | 10A0 | GR 25x50 (1D5A) | 200x500 / 199x500 | 2F96 same | short side | (drawn = 1ST 20x50) | 0.20 flush | 0.100 .. 0.125 | 0.450 .. 0.5625 | NEW |
| GFRS 380 | GF C8 | 10E0 | GR 25x90 (1DBE) | 800x250 / 800x250 | 2FD2 same | long side | - | 0.20 | 0.200 .. 0.225 | 0.900 .. 1.0125 | D-16 (CAP 101B prints 30X80 at its neck) |
| FFRS 691 | 1F C3 | 10CC | 1ST 20x50 (1D5A) | 250x500 / 250x504 | 3005 same | short side | yes | 0.20 flush one face, 0.05 nib | 0.100 .. 0.125 | 0.420 .. 0.525 | NEW |
| FFRS 676 | 1F C4 | 108D | 1ST 20x50 (1D6E) | 500x250 / 500x250 | 2FEA same | short side | yes | 0.20, 0.05 nib | 0.100 .. 0.125 | 0.420 .. 0.525 | NEW |
| FFRS 697 | 1F C4 | 10D7 | 1ST 20x50 (1D6E) | 500x250 / 500x250 | 300B same | short side | yes | 0.20, 0.05 nib | 0.100 .. 0.125 | 0.420 .. 0.525 | NEW |
| FFRS 673 | 1F C5 | 108A | 1ST 20x50 (1D82) | 600x250 / 601x250 | 2FE7 same | both | yes | 0.20, 0.05 nib | 0.100 .. 0.150 | 0.420 .. 0.630 | NEW |
| FFRS 685 | 1F C5 | 10BD | 1ST 20x50 (1D82) | 200x600 / 199x601 | 2FF9 same | long side | no (GR 25x60) | 0.20 flush both | 0.100 .. 0.120 | 0.420 .. 0.504 | NEW |
| FFRS 694 | 1F C5 | 10D3 | 1ST 20x50 (1D82) | 600x250 / 601x250 | 3008 same | both | yes | 0.20 flush one face | 0.100 .. 0.150 | 0.420 .. 0.630 | NEW |
| FFRS 688 | 1F C6 | 10C2 | 1ST 20x60 (1D96) | 250x700 / 250x698 | 2FFC same | both | yes | 0.15 inside | 0.120 .. 0.175 | 0.504 .. 0.735 | NEW |
| FFRS 68E | 1F C7 | 10C8 | 1ST 20x80 (1DAA) | 800x250 / 800x250 | 3002 same | short side | yes | 0.20, 0.05 nib | 0.160 .. 0.200 | 0.672 .. 0.840 | NEW |
| FFRS 69A | 1F C8 | 10E0 | 1ST 20x90 (1DBE) | 800x250 / 800x250 | 300E same | both | no (0.80 deep, as its stack) | 0.20 flush one face | 0.180 .. 0.200 | 0.756 .. 0.840 | D-16 |
| FFRS 679 | 1F C9 (lift) | 1090 | 1ST 20x90 (1DD2) | 250x1000 / 250x999 | 2FED same | both | yes | 0.20 both ways | 0.180 .. 0.250 | 0.756 .. 1.050 | NEW + D-63 (its neck) |
| FFRS 667 | 1F C9 T.C | 10DA | 1ST 20x90 (1DD2) | 200x1000 / 199x1003 | 2FDB same | long side | no (GR 25x100 turned: width = 1ST, depth = GR) | 0.15 | 0.180 .. 0.200 | 0.756 .. 0.840 | NEW |
| **15** | GF 4, 1F 11 | | | | 15 / 15 same | short 5, long 5, both 5 | 1F 8 / 11 | | | **8.034 .. 10.119** (GF 2.070 .. 2.475, 1F 5.964 .. 7.644) | |

Observations (evidence for the designer, not resolutions): (1) on 1F, 8 of 11 outlines equal the GR band of their type
and 8 of the 9 0.25-wide 1F outlines sit in a 0.20 architectural wall flush with one face, leaving a 0.05 m nib on the
other: the schedule reading (0.20) would make them flush; the drawn reading makes a nib in each room the architect
copied but did not dimension. (2) On GF the four outlines are SMALLER than GR (C x2 0.40 vs 0.50 deep; C3 344 0.20 vs
0.25 wide, equal to its 1ST band; C8 0.80 vs 0.90, the same 0.80 the CAP prints at its neck). (3) 685 and 667 equal no
band: the 1F 0.20 width agrees with 1ST, the depth does not. The bar counts and DES. LOAD on p.9 fit either section and
are not used to choose one (a capacity check is design, not take-off, and X6 forbids choosing).

## 4. Settled / still-CONFLICT split and deltas for lane I (task item b; nothing applied)

| Group | Before (T-248) | After (T-256) | Delta for lane I |
|---|---|---|---|
| 15 section CONFLICT | 8.034 .. 10.119 m3, UNRESOLVED | **0 settled; 15 CONFLICT, 8.034 .. 10.119 m3**, every reading's sources listed | none (the range stands; the candidate's schedule-end values stay ENGINE_WRONG basis, T-248) |
| 5 route G lines no plan draws (2.268 m3) | UNKNOWN (D-65) | **NOT_PRESENT proposed**: absent on the storey's ST plan, its PDF plot (vector fills), the architectural plan of the storey, and no start / stop symbol on the plan below; nothing printed within 0.6 m; their only basis is a type-table band | remove the 5 lines (no line, never a 0 line) once the Checker confirms; V3.0.x already holds them (T-236 F2), released A / route G carry 2.268 |

Why the 5 are absent and not merely undrawn (ERS s.2.3, from first principles): (a) the schedule's upper bands are a
TYPE table: C4, C6, C7 and C8 print a '2nd floor & Top' band and the 2F plan draws no member of any of the four, so a band
is not evidence that a member of that type exists at a given stack; (b) T-220 (merged): no slab is drawn over the four 2F
positions and the 1F position is 1.45 m outside the 1F roof slab edge, so a column there would carry nothing; (c) the
only remaining physical possibility the set names, a parapet stub ('CHECK ARCHITECTURAL DETAIL OF PARAPET BEFORE
CASTING', p.4-6), is answered by p.14 'DETAIL OF PARAPET SECTION': a continuous RC upstand 105 high, 15 + 15, 6ø12/m,
with no column. Per stack: 10E4 1F (GF 383 below, stops at the GF roof), 10C5 2F (1F 68B below), 10E4 2F (nothing on 1F
either), 10BD 2F (1F 685 below), 10E0 2F (1F 69A below).

## 5. Cross-trade (task item d)

Under C1 slabs stop at the DRAWN column faces (T-234 / T-241 partition, merged). Ownership is unchanged by this task (no
reading applied). But the two readings are not single-line facts: if a designer answer picks the schedule section, the
slab line must move with the column line inside the 0.16 slab plate, (A_sched - A_drawn) x 0.16:

| Storey | Schedule reading vs drawn faces | m3 in the plate |
|---|---|---|
| GF (4) | schedule larger: DOUBLE (slab and column both bill it) | +0.0144 |
| 1F (11) | schedule smaller: GAP (neither bills it) | -0.0640 |

The beam ends framing into the changed faces move the same way over the beam depth (not computed: it needs the T-241
band-to-face pairs per member; named). Column vs beam / slab ownership (R-CONC-OWN-1) is otherwise unchanged; no
ownership claim in T-248 section 2 changes.

## 6. Consultant text proposals (task item c; the Lead edits CLARIFICATIONS_CONSULTANT / DESIGNER_CLARIFICATIONS)

- **Numbering defect found:** T-217 proposed the per-storey band question as 'D-64', but DESIGNER_CLARIFICATIONS D-64 is the
  opening P-1F-01. The column band question has no register number; it needs the next free D number.
- **D-16 (narrowed to members):** 'Column C8 at F14 (neck FP 10E0, GF GFRS 380, 1F FFRS 69A): the CAP prints 30X80 with
  dimensions 70 + 10 and every plan draws 0.80 deep (GF 0.25 x 0.80, 1F 0.25 x 0.80); the schedule gives 90 deep in every
  band (FOU 30 x 90, GR 25 x 90, 1ST 20 x 90). Which section is built on each storey?' Impact: GF 0.900 .. 1.0125, 1F
  0.756 .. 0.840 m3.
- **NEW (column band per storey), narrowed to 13 members:** 'GF: C at 10A4 / 10B7 drawn 0.20 x 0.40 (GR 20 x 50); C3 at
  10A0 drawn 0.20 x 0.50 (GR 25 x 50). 1F: C3 10CC, C4 108D / 10D7, C5 108A / 10D3, C6 10C2, C7 10C8, C9 1090 drawn 0.25
  wide (8 equal the GR band; 1ST prints 0.20), C5 10BD 0.20 x 0.60 and C9 T.C 10DA 0.20 x 1.00 (1ST 20 x 50 / 20 x 90).
  For each, is the column built to the schedule band of its storey or to the slab-plan outline? (1F outlines 0.25 leave a
  0.05 nib beside every 0.20 wall.)' Impact: GF 1.170 .. 1.4625, 1F 5.208 .. 6.804 m3 (with D-16: 8.034 .. 10.119).
- **D-63 (lift C9 1F, FFRS 679):** add 'and the 1F column above it, drawn 0.25 x 1.00 vs 1ST 20 x 90 (0.756 .. 1.050 m3)'.
- **D-65 (narrowed to a confirmation, not a hold):** 'The schedule's upper-floor bands are a type table. We read that no
  column exists at 10E4 (1F, 2F), 10C5, 10BD, 10E0 (2F): no plan draws one, no slab is over them, the parapet detail
  is a continuous RC upstand. Please confirm.' Impact: 2.268 m3 of route G / released lines that the drawings do not support.

## 7. Verdict proposals (for the Checker)

| Item | Proposal |
|---|---|
| 15 CONFLICT, 8.034 .. 10.119 m3 | UNRESOLVED (designer): no third independent source on any sheet; never the schedule end, never the larger |
| PDF plot and architectural column layer | NOT a third source (copies; 15 / 15 identical); rule R-COLUMN-EVIDENCE-1 (1) |
| 5 route G / released lines 2.268 m3 | NOT_PRESENT (DRAWING-CONFIRMED absence): ENGINE_RIGHT for the V3.0.x hold direction; route G and released A carry 2.268 m3 on members the set does not have |
| freelancer | not affected: his columns are per type x count; his 2F count (9) equals the drawn 9 (T-248), so he carries none of the 5 |
| designer register | numbering collision 'D-64' (T-217) vs D-64 (opening): a NEW D number for the band question |

No owner question: ERS 2.7 is met only as 'two authoritative documents conflict', which this project routes to the
designer list (T-217, T-248 precedent); no owner method, contract or release decision is involved.

## 8. Rule, test, lessons row

R-COLUMN-EVIDENCE-1 (proposed; any villa; a new rule version when adopted): see `column_evidence.py` docstring: count a
source once per document (a plot or a copied layer is its original); a section CONFLICT is settled only by an
independent member-specific print that agrees with the printed reading against a drawn-only reading; a third print that
agrees with the drawn reading makes it PRINTED_VS_PRINTED, never a vote; an upper line no sheet draws is NOT_PRESENT
(line removed) only after every sheet that could draw it was searched and only a type band suggests it, otherwise
UNKNOWN; a reading other than the drawn one moves (A_reading - A_drawn) x t_plate between the column and slab lines.
Test: tests/t256_column_evidence (Villa M: settled by a third print, P-v-P by a third print, copies not counted, typical
detail not counted, drafting note, rotation / units, metamorphic order, plate transfer, NOT_PRESENT; adverse: larger /
schedule / freelancer preference refused, schedule-only release refused, missing section and missing height never 0,
existence UNKNOWN when a sheet is not searched or a print names it, unknown search key, copy of an absent document).

Lessons row (proposed): 2026-10-24 | 15 column section conflicts and 5 upper lines stayed open across T-217 / T-220 /
T-248 with 'search the other sheets' as the next step | the derived documents (the PDF plot, the architectural plan
carrying the structural column layer) looked like extra sources; the schedule's upper bands looked like evidence of
existence | count a source once per document (a plot or a copied layer is its original); a type table is not evidence
that a member exists; search every sheet that could print the member, record the list, then either settle or narrow the
designer question to member ids (any villa; columns, any scheduled element) | tests/t256_column_evidence
test_copies_of_the_same_drawing_are_not_a_third_source, test_existence_not_present_removes_the_line_never_a_zero | PROPOSED.

## 9. Checker re-measure list

1. Independence: P7757.dxf has one column layer 'S-COL.BON' with 59 LWPOLYLINE outlines; GF 2F99 / 2FAB / 2F96 / 2FD2,
   1F 3005 / 2FEA / 300B / 2FE7 / 2FF9 / 3008 / 2FFC / 3002 / 300E / 2FED / 2FDB = the 15 ST outlines in size.
2. PDF p.5 at 1:100: the filled outlines of 679 (7.08 x 28.32 pt = 0.25 x 1.00 m), 685 (5.64 x 17.04 pt = 0.20 x 0.60),
   688 (7.08 x 19.8 pt = 0.25 x 0.70); p.4: 347 (5.64 x 11.28 pt = 0.20 x 0.40), 380 (22.68 x 7.08 pt = 0.80 x 0.25).
3. Sections on p.4 / p.5 (A-A, B-B, C-C, D-D: texts 1727, 1730, 176C, 17A2) cut beams only; p.15 twisted-column details typical.
4. 1F C9 679: architectural dimensions D3D 1800 / E94 200 / EA1 1470; E94 ends on the wall line 'layer 1' 0.20 from the
   column face (B05 / B06), not on the column's second face.
5. The 5 NOT_DRAWN stacks (necks 10E4, 10C5, 10BD, 10E0): nothing on S-COL.* within 0.6 m on FFRS / SFRS, no PDF fill on
   p.5 / p.6, no architectural outline; p.9 schedule 2ND bands for C4 / C6 / C7 / C8 with no 2F member of those types.
6. Re-run: `python3 -I research/agents_t256/t256_extract.py <ST dxf> <P7757 dxf> <ST pdf> --write` (PyMuPDF for the PDF
   part), then `python3 -I research/agents_t256/t256_alsenan_check.py --write`.

## 10. Not done / uncertain

- Beam-end transfer at the changed faces for each conflict reading (named in section 5, not computed).
- The PDF p.9 schedule was read visually at 220 dpi (values = the DXF CGT rows); its vector text was not parsed.
- The architectural sections / elevations were not searched for column cuts: the architectural set carries no column
  layer outside the three plans (59 outlines, all on the plans), so a section would draw at most an uncoloured line.
