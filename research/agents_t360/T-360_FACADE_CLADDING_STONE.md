# T-360: FACADE CLADDING / STONE (BOQ family B4-11), sheet by sheet and face by face (development villa; every villa by R-T360-1 .. 5)

Worker 2 (lane A), claim 2026-10-30 06:44 UTC, run session_01E6cPneZzEXkC3ufBoJiB12. Investigation of a MISSING
category (B4-11 NOT_IMPLEMENTED, BOQ_FAMILY_MASTER 1.20.0). Research only: no engine module, rule or knowledge file,
candidate line, released line or V2.9 cell changed; nothing released, nothing VERIFIED by this task. ERS applied: s.2.1
(physical element first), s.2.2 (evidence hierarchy; owner method beside the drawing reading), s.2.3 (own reading of
every sheet and of the DXF), s.2.4 (cross-check in m2), s.2.7 (no owner question: the open item is a designer
material, already the RFI's subject), s.3 (one face one finish; a notation's meaning before its arithmetic), s.4
(rules + tests), s.7 (lesson row, section 8).

## 1. Identity and run

Own run, Python 3.11.18. Drive 'Alsenan chalet project' (read-only): P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256
`ab54dd55` = SOURCE_MANIFEST); Alsenan_Architectural_P7757_Pages_05-06 (6 225 932 B), Pages_07-08 (6 099 455 B),
Pages_11-12 (6 116 815 B), p7757_arch_sheet09.pdf (3 209 545 B), p7757_arch_sheet10.pdf (3 137 565 B), all decoded into
.work/private only and rendered there (120 dpi whole pages, 300 dpi crops). `t360_alsenan.py --geometry <P7757.dxf>`
re-reads the text census, the 8 elevation-frame hatches by handle and the porch-mouth arch surround (GEOMETRY OK);
`--write` builds the ledgers from the committed inputs (the sheet table in the builder, the merged T-337 face keys,
the freelancer's parsed rows); `--check` rebuilds byte for byte; tests `tests/t360_facade_cladding` (18 pass). No
coordinate, image, title-block text or client name is committed (a test asserts it).

## 2. The physical element and its evidence

A facade cladding is a LAYER (natural stone, tile, GRC, composite panel ...) on an exterior face that replaces or
covers the plaster / Sigma / paint system between a bottom and a top level, with its own returns at reveals and its
own fixings. It exists in a BOQ only when the set says what it is and where:

| Evidence (ERS s.2.2) | What it can do |
|---|---|
| (1) printed legend, a hatch the legend names, a text note, a schedule | names the material and the extent: a quantity (DRAWING-CONFIRMED) |
| (1) drawn unit outlines without a legend (voussoirs, quoins, coursing) | marks an ELEMENT and its geometry; the material is not printed: HELD by name (R-T360-2) |
| (2) specification | none issued (RFI-B-A12: no finishes schedule or specification in the set) |
| (3) owner rules | OWNER_NOTES_SIGMA_2026-10-21: the exterior finish measured is plaster + Sigma on the elevations; no owner rule names a cladding; OWNER_RULE_OUTDOOR_FLOORS covers floors, not faces |
| renders, photos, a 'typical' stone, the freelancer | design intent / reference only; never a source of material or extent (R-T360-1) |

## 3. Sheet by sheet (SHEET_CENSUS_T360.csv, HATCHES_T360.csv; acceptance a)

| Sheet | View | Legend / text naming a material | Hatch on an exterior face | Verdict |
|---|---|---|---|---|
| Pages_01-02 p.1, p.2 | area plans | none (T-091) | none | absent |
| sheet03, sheet04, Pages_05-06 p.5 | GF / 1F / 2F plans | none (T-091: 0 finish notes) | none | absent |
| **Pages_05-06 p.6** | **SE elevation** | none (levels, dimensions) | ground + section-cut bands only | **marks a FORM, no material**: the porch-mouth arch surround is drawn as voussoir / quoin block outlines (DXF SE frame, layer 1) |
| Pages_07-08 p.7 | SW elevation | none | ground only | absent; one field of 6 vertical lines at the annex junction, spacing 10 / 23 / 32 / 39 / 46 px at 300 dpi = a drum seen side-on (R-T360-3), not a hatch |
| Pages_07-08 p.8 | NW elevation | none | ground + cut bands | absent (W17 curved-glazing lines = a window, T-238; the arch band 20 / 30 = archivolt, T-238 / T-324) |
| sheet09 | NE elevation | none | ground + cut bands | absent (curved-face shading fields beside the annex and the hall) |
| sheet10, Pages_11-12 p.11 | sections A-A, B-B | none | cut bands | absent (dome ribs on B-B; the owner: no domes) |
| Pages_11-12 p.12 | fence plan / elevation / section | house number only | the section's cross-hatch = the cut base | absent |
| sanitary-7757 p.1-3 | drainage | none (T-091) | none | absent |
| P7757.dxf | plans + SE / NW frames | **0 of 675 texts** match a material keyword (Latin; Arabic SHX: T-091 decoded, 0 material notes) | 88 model-space hatches; the 8 in the elevation frames are LINE (section cut, 6) and AR-PARQ1 (ground, 2): 0 finishes | SE frame form only; NW absent |

**Result: no sheet of the set prints a cladding or stone material on any exterior face.** One element carries a
cladding-like drawn form (C-1 below); everything else is plain.

## 4. Face by face (FACE_STATE_T360.csv; acceptance b, c)

All **109 T-337 face keys** (46 storey, 29 plinth, 25 parapet, 9 slab edge; SW 34, NW 33, NE 20, SE 18, passage 4):
**NOT_MARKED, NOT IN DRAWN SCOPE, cladding m2 blank, double count 0.000 m2**; each face keeps its T-337 finish owner
(the three storey lines, the four PARAPET-OUTER lines, PLINTH GF, SLAB-EDGE 1F). B4-11 adds **0 faces, 0.000 m2** to
the candidate.

| Candidate | Evidence | State | Geometry | B4-11 |
|---|---|---|---|---|
| **C-1 porch-mouth arch surround (SE)** | p.6; DXF SE frame layer 1, bounded by handles 23A8 / 23FE / 2416 / 1CC8 | MARKED_FORM_MATERIAL_HELD | visible part **1.5149 m2** (r2; was 1.5102): 10 blocks (3 jamb quoins 0.35 x 0.30 + 7 arch voussoirs incl. the crown block), every one drawn as a double outline, face = its outer ring (R-T360-6, section 9), and 11 band pieces 0.20 wide (r2 adds the 0.0046 strip right of the crown, cut by 2416); height 4.383 above the band foot (crown outer top line 2230); jamb by hand 0.315 + 0.220 = **0.535** (= the polygon, 0.000); arch 0.9799 (hand 0.9791). **The other half lies behind the annex section line 2416: UNKNOWN** | **HELD, blank** (material not printed; whole element not drawn) |
| C-2 plinth band (29 faces) | the elevations draw the band and print no finish | NOT_MARKED | 71.689 .. 72.750 m2 already in NEW FIN.EXT.FINISH PLINTH GF (T-337, HELD) | not B4-11; stays in its own line, finish HELD, never a stone default |
| C-3 court 'crazy-paving' stone | renders only | REFUSED | outdoor floor, not a face (T-343) | not B4-11 |

C-1 is on **none of the 109 face keys**: the porch mouth is an open side, and T-238 recorded the arch (F-PORCH-ARCH)
as a wall piece no merged ledger measures (face, soffit, arrises UNKNOWN). So there is no plaster / Sigma / spatter-dash
face it could double count (0.000 m2 against T-337 and T-349). Named, not applied: if the designer says stone, C-1
replaces the plaster / Sigma on that piece; if the blocks are plaster-formed (one of the two render sets shows white
stepped blocks, the other grey cut stone: T-161 F11), C-1 is plaster / Sigma plus arrises and leaves B4-11.

Geometry method (for the Checker): layer 1 lines inside the handle box; regions between lines (6 mm pen tolerance,
CAD gaps up to 12 mm bridged); each block is drawn as a double outline 10 mm apart (jamb quoin inner 0.33 x 0.28,
outer 0.35 x 0.30) and its face is the OUTER outline; the 7.6 mm sliver between the crown block and the section line
is excluded; nothing beyond line 2416.

## 5. Drawing-derived reading beside the owner method

| Method | Facade cladding on Alsenan |
|---|---|
| Owner (OWNER_NOTES_SIGMA; Q-07 B bands, T-337) | none: every exterior face is plaster + Sigma (and paint), measured face by face in the T-337 lines |
| Drawing-derived (this task) | none printed; one drawn form (C-1) whose material the set does not give |

The two agree on every face key. C-1 is not a conflict between them: the owner method does not reach the porch-mouth
piece (no line, T-238) and the drawing gives no material, so it stays HELD by name for the designer (ERS s.2.7 is not
met for the owner: a genuinely unspecified finish is a designer item, and RFI-B-A12 already asks for the finishes
schedule and specification).

## 6. Engine vs freelancer

Freelancer: 885 parsed rows in 6 workbooks (FIN 197, BLK 190, PNT 77, RC 256, ALU 50, PLS 115): **0 cells name stone,
cladding, granite or GRC**; his exterior is the plaster + Sigma workbook (12 facade rows, net 1,469.97 m2, OWNER_NOTES_
SIGMA), whose SE row covers the entrance face as one plane (no surround item). Engine: B4-11 0.000 m2 established, C-1
HELD blank.

| Item | Engine | Freelancer | Difference | Verdict proposal |
|---|---|---|---|---|
| Facade cladding / stone, all faces | 0 faces, 0.000 m2 (NOT IN DRAWN SCOPE) | 0 rows | 0.000 m2 (0 %) | AGREE (no cladding scope printed or priced) |
| Porch-mouth arch surround | HELD blank (visible 1.5149 m2, half UNKNOWN) | inside his SE plaster plane, no own item | not comparable (HELD) | UNRESOLVED: material for the designer (proposed RFI line, section 7) |
| Plinth band | own HELD line (T-337) | inside his elevation rows | unchanged by this task | as T-337 |

## 7. Findings

- **F-T360-1 (for the Lead, RFI).** Proposed addition to RFI-B-A12 / A13 (architect), worded for the designer: 'SE
  elevation, porch-mouth arch: the jamb and arch are drawn with block outlines (quoins / voussoirs). Please state the
  material and finish of these blocks (natural stone, precast, or plaster-formed), their thickness / projection from
  the wall face, and the arch's other half, which the elevation hides behind the annex section.' Internal impact: C-1
  HELD blank; visible face 1.5149 m2 measured (r2). Not sent by this task.
- **F-T360-2 (for the Lead / lane I).** C-1 also leaves the porch-mouth wall piece itself (its face, soffit and
  arrises) in no line (T-238 F-PORCH-ARCH UNKNOWN): whichever finish the designer gives, the piece needs one owner
  line; nothing is applied here.
- **F-T360-3.** The fields of parallel lines on the SW / NE / B-B views fit a drum seen side-on (equal angular steps):
  curved faces, not a material hatch (R-T360-3). No line changes.

## 8. Rules (research, PROPOSED; scope every villa; provenance T-360), tests and lesson

R-T360-1 a cladding material only from a printed legend / named hatch / note / specification / owner rule; render,
photo, unnamed hatch, 'typical', default or the freelancer refused; R-T360-2 drawn unit outlines without a legend mark
the element (geometry measurable) but not its material: HELD by name, never a stone line, never 0; section-cut and
ground hatches are not finishes; R-T360-3 a parallel-line field with a cosine spacing is a curved face; R-T360-4 one
face part one finish: cladding names the plaster / Sigma / paint part it replaces, a part quantified in both refused;
R-T360-5 openings once by id inside the band, HELD = blank.
Tests (`tests/t360_facade_cladding/test_t360_cladding.py`, 18 pass): normal: a 12.40 m villa street face (not
Alsenan) with a printed 1.20 m stone plinth, hand 14.880 - 1.440 (door) - 0.300 (window part) = **13.140 m2**; the
same face drawn in mm, full height 52.080 - 2.880 - 2.100 = **47.100 m2**; an unmarked face NOT IN DRAWN SCOPE (blank,
not 0); cut / ground hatches not finishes; a 2.00 m drum at 15-degree steps (and mirrored) is curved shading, uniform
0.30 coursing is not. Adverse: a render refused; default / typical / freelancer / unnamed hatch / photo refused; a
legend without a name refused; form only -> HELD blank; two printed materials -> CONFLICT HELD; a material without a
printed band -> HELD; a held opening head -> blank; an opening twice refused; a band leaving the face refused; a face
in plaster and cladding refused (re-cut above the band 0, held plaster None). Development villa: outputs reproduce
byte for byte; 109 keys NOT_MARKED with 0.000 double count; C-1 HELD blank with the visible geometry; jamb hand
0.535; no coordinate or Arabic title-block text in any committed file.

Lessons-register row (ERS s.7, proposed): | 2026-10-30 | A drawn block pattern on one elevation (the porch-mouth arch
quoins / voussoirs) could be read as 'stone cladding' and priced as stone, while the renders show both white plaster
blocks and grey stone | a drawn FORM was taken for a MATERIAL; the set has no legend, finishes schedule or note | drawn
unit outlines without a legend mark an element and its geometry, never its material: HELD by name, never a stone line,
never 0; renders never decide the material (scope: every villa, facade finishes; provenance T-360) |
tests/t360_facade_cladding (form only -> HELD blank; render refused; default stone refused; face in plaster and
cladding refused) | PROPOSED |

## 9. r2 (Gate A rejection D-T360-1, 2026-10-30): drawn face of each block, decided per block

**The rejection.** The Checker re-measured C-1 at 1.4871 m2 against 1.5102 (+1.55 %): `geometry()` offset EVERY inner
block outline by the 10 mm pen distance, while (the Checker's reading) two blocks, voussoir 23B8..23BB and the crown
1CC8 / 23AC / 23AD, are drawn with ONE outline, so the offset would add face that is not drawn.

**Physical element first.** Each block is a unit of the surround; its visible face is bounded by the line where the
next piece (a joint, a band piece, the wall) begins. The drafter draws each block as two concentric outlines 10 mm apart;
the joint and band lines END on the OUTER outline, so the outer outline is the face edge.

**Re-examination by handle (own census, P7757.dxf sha ab54dd55, layer 1, SE frame).** For every block the own inner
outline polygonizes to one ring (that is true of all ten, so it does not decide single vs double); the decisive evidence
is whether a SECOND ring is drawn 10 mm outside, closed at its own corners. It is, for all ten (BLOCK_RINGS in
t360_alsenan.py):

| Block | Inner outline | Outer ring drawn 10 mm outside |
|---|---|---|
| voussoir 4 (large) | 23B8 / 23B9 / 23BA / 23BB, 0.0928 m2 | 23A9 / 1CDD / 23A7 / 1CB4, 0.1054 m2; joint lines 1CED and 1CEE end on 1CB4 / 1CDD (the outer ring) |
| crown | 1CC6 / 1CC7 / 1CC8 / 23AC / 23AD, 0.1199 m2 | 1CC3 / 2230 / 222F / 1CAB / 1CC2, 0.1349 m2 inside the view (the right side is cut by 2416); 2230 is the drawn top, 10 mm above 1CC8 |
| the other eight | (BLOCK_RINGS) | drawn the same way, with the same joint pattern |

Voussoir 4 is simply a LARGER block (inner outline 0.0928 m2 against 0.081 for its neighbours, as the jamb quoins
0.0924 are larger than the small voussoirs), which is why its inner outline (0.0928) is close to the neighbours' OUTER faces (0.093).
D-T360-1 therefore **does not reproduce**: no block is drawn with one outline, and the blanket offset happened to give
the right face on this drawing. The defect in the METHOD stands, and r2 fixes it: the face is now decided per block.

**Fix (R-T360-6, `t360_cladding_rules.block_face`).** The pen-offset ring is DRAWN when at least 95 % of its length
(inside the view) lies on drawn lines and every one of its corners inside the view is a drawn line end; then the face is
the outer ring, else the single outline itself. A neighbour's edge 10 mm away that runs past the block (a joint) fails
the corner test. On the real linework: all 10 DOUBLE; removing the four outer lines of voussoir 4, or the five of the
crown, or only one side (23A9), turns exactly that block SINGLE (own adverse run, not committed: it needs the private
DXF).

**Crown-side sliver (decided: IN).** A 0.0046 m2 strip right of the crown, bounded by 222F / 2231 / 2233 and the
section line 2416, was dropped by the thin-region filter (minimum width 16.7 mm < 20 mm). It is the visible start of the
band piece on the hidden side of the crown (2231 / 2233 mirror 1CD9 / 1CF0 on the visible side), truncated by the cut:
drawn face, so it is now kept (a thin region touching the section-cut line). Pieces 20 -> 21, band pieces 10 -> 11.

**Restated C-1 (geometry only; the element stays HELD blank, material not printed).**

| | r1 | r2 | change |
|---|---|---|---|
| visible face | 1.5102 m2 | **1.5149 m2** | +0.0047 m2 (+0.31 %): the crown-side strip |
| jamb (hand 3 x 0.35 x 0.30 + 0.20 x 1.10) | 0.535 | 0.535 | 0 |
| arch | 0.9752 | 0.9799 (hand piece sum 0.9791, -0.08 %: the closed 10 mm pen joints) | +0.0047 |
| height above the band foot | 4.383 m (2230) | 4.383 m | 0 |
| Checker r1 re-measure 1.4871 + outer rings of the two blocks (+0.0128 + 0.0151) | | 1.5150 | function 1.5149: -0.01 % |

Not changed by r2: B4-11 0.000 m2 on the 109 keys, C-1 HELD blank, F-T360-1 (proposed RFI, not sent), F-T360-2 / -3,
rules R-T360-1 .. 5. Tests: three added (double outline -> outer ring 0.096 m2; single outline with a neighbour 10 mm
away and a three-sided ring -> not offset 0.084 m2; a double block cut by a section line -> 0.0945 m2).
