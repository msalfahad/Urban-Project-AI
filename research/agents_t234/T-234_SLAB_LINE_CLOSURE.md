# T-234 Whole-line closure: CONC.SLAB, every slab panel once (Alsenan; every villa)

Worker 1 (lane S), 2026-10-23, run session_01WtJy6f77K5X6JCMyFwWAaQ. Research piece, not wired: no engine, candidate or
released line changed; integration is a lane I package after the Checker's verdict. Development villa, not an accuracy
claim. Drawings named by Drive folder and title; entities by DXF handle; areas, thicknesses and counts only.

## 0. Inputs and runs (own, this task)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 (= manifest) | GF / 1F / 2F roof-slab sheets: T-139 face partition re-run, thickness tags, every S-OPENING mark |
| "P7757_DXF_COMPRESSED.zip" -> P7757.dxf | ab54dd55... (= manifest) | the released baseline run only |
| freelancer RC workbook | (committed cells) | tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, sheet 'بلاطات ' rows 11 / 16 / 23 / 24 / 27 ('ورقة1' row 21 = I27) |

Runs: T-139 `slab_faces.py` + `slab_ledger.py` on the Drive copy: **PANELS.csv byte-identical** to the merged file
(62 panels, 375.0481 m2, 60.2804 m3). Released baseline A `tools/release_baseline.py run
research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json` on the working head 63f4d90e: **REPRODUCED**, 1,455 lines,
BOQ_LINES.csv b96185d4. Candidate: `research/agents_t167/v304_run.py` then `research/agents_t231/v308_run.py` on the same copies: V3_0_7_BOQ_LINES.csv 197c5599 and V3_0_8_BOQ_LINES.csv 57fe219a **REPRODUCED** (= T-231).
Files: `slab_line.py` (pure rules), `t234_alsenan_check.py` (ledger + summary from committed inputs),
`LEDGER_T234.csv` (62 panels), `summary.json`; tests `tests/t234_slab_line` (32).

## 1. The physical element and the convention (ERS s.2.1, s.3)

- PANEL (BOQ CONC.SLAB = item STR.CONC.SLAB only, key map T001B): the suspended RC plate between the faces of the
  members carrying it, on one slab sheet (storey named by the slab sheet: 'GF' = GF roof = 1F floor; T-213 convention),
  thickness t; openings / voids deducted once; a sunken panel is the same plate lowered by its drop.
- The ground slab (STR.CONC.GROUND_SLAB, 0.10 m) is keyed to CONC.GROUND with the ground beams, not to CONC.SLAB: out
  of this line (released A: 17.127 m3 measured + bounded 4.767 + one UNRESOLVED face 39.30 m2 at 0.10).
- **Slab / beam ownership, stated on every side before comparing**: C1 'panel between beam faces, beam at full depth D'.
  Released route G (slab faces 'members' overlap deducted'; beam lines net plan x D), the beam register T-110 (B1 20x40
  billed 0.20 x 0.40 x L), the freelancer (slab lump 207.00 m2 ~ panels 206.68 m2; beams B x D x L at the schedule's
  full depth, e.g. B1 0.20 x 0.40) and this ledger all use C1. concrete_overlap_ownership.PRECEDENCE_ROUTE_G records it
  (BEAM 40 > SLAB 30). The method register's URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1 is C2 (slab = net plate x t over
  the beams, downstand = B x (D - t)): C1 -> C2 moves band area x t from CONC.BEAM to CONC.SLAB, slab + beam unchanged
  (`slab_line.convention`, 3-D proof in tests/t234 'c2_consistent_and_same_total_as_c1'). T-139 s.2 says 'the beam lines
  take D - t over their own footprint': that sentence is C2 wording on a C1 ledger (the beam register bills D); the
  quantities are C1 and consistent, the sentence is a text slip (no quantity changes).

## 2. Panel table per storey (each panel once; LEDGER_T234.csv)

| Storey (slab sheet) | Panels | Net m2 | Thickness (source) | m3 by hand | Sunken (full t) | Openings / voids (own faces, never in a panel) |
|---|---|---|---|---|---|---|
| GF roof, ST p.4 | 33 | 206.6845 | 0.16: 2 tags 'T 16' + 31 by general note 18 | **33.0695** | 5 (19.3964 m2) | lift shaft X 54F/550 1.80 x 1.80 (GF-048, 3.24); pool-court void X 42E/42F in the B7 ring (GF-040); light well X 2CF..2D2 + 54B/54C with the round stair (GF-130, stair ledger) |
| 1F roof, ST p.5 | 22 (incl. 4 dome-square corners) | 123.4786 | 0.16: 1 tag 'T 16' + 21 by note 18 | **19.7566** | 1 (5.40 m2) | lift shaft X 73F/740 1.80 x 1.80 (1F-036); two dome openings r 2.2111 (radial 604..617 / 64E..661; Q-44 A; ring bands = beams) |
| 2F roof, ST p.6 | 7 | 44.885 | 0.18 on the two tank panels ('T 18', 2F-011 / -013, 13.635 m2); 0.16 by note 18 on 5 panels (31.25 m2) | **7.4543** | 0 | none: the lift box 2F-025 is closed (bars 5 d10/m both ways; T-204: the +13.90 slab closes the shaft) = slab |
| **CONC.SLAB** | **62** | **375.0481** | | **60.2804** | 6 (24.7964 m2) | 6 opening sets, each deducted once (as its own face) |

- Outline: the drawn face between beam / column faces (the sheets print no panel chains; the sheet note forbids
  scaling). Second source for five panels (T-139 s.2: beam register centreline +- schedule width) equal to the mm;
  every released route G slab face was placed inside a T-139 face (72 of 75 placed by an overlay fit; the 3 unplaced
  are T-139's own named non-slab faces d54a5a / cf20e8 / 4c7ca8) and every SLAB panel area agrees within 0.005 m2.
- Thickness: one printed source per panel: the tag where printed, else general note 18 (ST p.8, read by eye, T-139 /
  T-213 / T-145). Searched for a second printed value this run: the DXF slab sheets carry only these tags (S-TEXT-SLAB
  'T' + '16' 768 / 769 on 1F, 'T' + '18' 7B3 / 7B4 and 1A7D / 1A7E on 2F, two GF tag inserts); sections A-A / C-C / D-D
  on the GF sheet are footing / beam sections ('AS PER SCH.', beam depth 800) with no slab dimension; the
  architectural sections draw one constant band (T-213). The freelancer's 'S.S 16 CM' / 0.18 agree but are not a source.
- Openings: census = every mark on layer S-OPENING of the three sheets (own DXF read): 6 plan sets, all void faces of
  the partition, so no panel deducts any and none is missed (`openings_not_deducted` = []); the other S-OPENING lines
  (172A-C, 1731-3, 1768 / 176A, 179E / 17A0) lie in section drawings; 256 / 25A / 25F and 62D / 62E / 633 are the
  stair-edge strips inside the stair zones. T-204's shaft openings = GF-048 / 1F-036 to the mm (centre 60.893 / 22.169,
  45.548).
- Sunken panels (T-213): GF-015 / -016 / -081 / -128 / -141, 1F-018 at the printed / note thickness over the full
  panel; T-145: every sunken edge is a beam face, so slab concrete does not depend on the drop d (HELD D-41) as long as
  d <= the 0.24 m downstand; fill / forms / upturns only depend on d (other lines).
- Stair zones GF-025 / 1F-016, the half landings and the winder slab (HELD 0.230 .. 0.250, T-139 s.5) belong to the stair
  ledger; the 1F / 2F arrival landings are slab + beam panels (R-STAIR-LAND-1, T-192), counted once here.
- Edges: every panel edge is a beam or column face (C1: the band belongs to the beam; T-189 precedence).

## 3. Ownership check (each intersection once)

- Plan partition (`face_partition_check`, every face of the three sheets, 402 faces): each face has exactly one owner
  line by its class: SLAB -> CONC.SLAB; bands / columns / junction squares -> CONC.BEAM or CONC.COLUMN; ring bands ->
  beam; stair zones / the light-well stair -> stair; strips and boxes outside the outer beams -> beam lane HELD
  (D-05 / D-26); openings, break marks, section drawings, the repeated lower outline -> no concrete. GF / 1F / 2F PASS.
- 3-D (concrete_overlap_ownership, tests/t234 villa S): C1 panel + full-depth beams PASS; the plate over the beams
  with full-depth beams DOUBLE = band area x t (refused); C2 with SLAB precedence PASS with the same billed total.
- Dependency on the beam line (not this task's quantity): CB5 span 2 (GF-097, 0.20 x 0.40 x 3.70 = 0.296) is in no
  beam row of released A or the beam register (T-145 proposed BM-GF-035.2; T-146 QUEUED). Until it is wired the band is a
  GAP in CONC.BEAM (released A bills its 0.1184 as slab instead), not in CONC.SLAB.

## 4. Line totals vs released A, the candidate and the freelancer (m3)

| Storey | Drawing (this task) | Released A (b96185d4) | A - drawing, named causes | Freelancer | Drawing - freelancer, named causes |
|---|---|---|---|---|---|
| GF roof | 33.0695 | 33.4898 | +0.4203: CB5 span 2 band 0.1184 (beam); 0.20 strip north of B20 line L-0871738f 0.1372 (BM-GF-058 HELD, D-05); outer west strip 0.0784 (D-26); B7 ring piece 0.0322 (BM-GF-060, Q-61 C); two 0.20 junction pieces GF-062 / GF-106 0.0402 (band / column); break mark 0.0139; residual 0.000003 | 33.120 (207.00 x 0.16) | -0.0505: his lump area 207.00 vs 206.6845 m2 (no breakdown) |
| 1F roof | 19.7566 | 19.9178 (+ BOUNDED 2.7403 'SLAB_STAIR_ZONE') | +0.1612: SE box outside CB12 0.0992, strip outside CB12 0.0325 (D-05), unlabelled span past a column 0.0159 (D-04), break mark 0.0139; residual -0.00024 (panel areas rounded to 4 dp). The bounded 2.7403 is the west dome square, NOT slab (T-139 s.4) | 19.200 (120.00 x 0.16) | +0.5566: eight dome-square corners 3.8475 m2 drawn as slab outside the ring +0.6156; lump residual -0.0590 (not traceable) |
| 2F roof | 7.4543 | 8.1438 | +0.6895: **the two tank tags 'T 18' spread to the five untagged panels (SHEET_UNIFORM, 31.25 m2 x 0.02) +0.6250**; break mark 0.0156 + 0.10 strip west of B15 0.0489 at 0.18 | 7.4974 | -0.0431: panels at 0.16 31.25 vs his 31.84 m2 (-0.0944); tank panels 13.635 vs his 13.35 m2 (+0.0513) |
| **CONC.SLAB** | **60.2804** | **61.5514** (+ BOUNDED 2.7403) | **+1.2710 (+2.11 %)**: tag spread 0.6250, 13 named faces that are not slab 0.6462, residual -0.0002 | **59.8174** | **+0.4630 (+0.77 %)**, every storey reconciled to named causes; 1F lump residual -0.0590 named |

Candidate V3.0.7 / V3.0.8 (own run: V3_0_7 197c5599, V3_0_8 57fe219a REPRODUCED; all V3.0.x carry identical
STR.CONC.SLAB lines): **60.9192 m3** = GF 33.4898 + 1F 19.9178 + 2F 7.5116; no bounded line (the west dome square is
retired). Candidate - drawing = **+0.6388 (+1.06 %)**: the same 13 non-slab faces (GF 0.4203, 1F 0.1614, 2F 0.0573 at
0.16), residual -0.0002. The candidate's M4 project profile (ST7757_M4) gives the untagged 2F panels 0.16, so the tag
spread is a released / no-profile defect; the faces wait on T-146 (QUEUED). Candidate vs freelancer +1.1018 (+1.84 %).

Engine finding (new, every villa): **route G spreads a panel tag to every untagged panel of its sheet when all tags on
the sheet are equal** (engine/source/slab_engine.py 'uniform' -> SHEET_UNIFORM), although the set's general note gives
untagged panels their thickness. Alsenan 2F: the tank tags 'T 18 (T&B)' make the five ordinary panels 0.18 instead of
the note's 0.16: +0.625 m3 (+8.4 % of the 2F slab). On GF / 1F the tags equal the note, so no effect there. T-139
compared against the M5 panel table (60.966), not the released BOQ run, and so did not see it.

## 5. Verdict proposals (for the Checker)

| Item | Proposal |
|---|---|
| 62 panels 60.2804 m3 | DRAWING-CONFIRMED, CLOSABLE: no HELD component inside STR.CONC.SLAB; every opening once; every sunken panel at full t |
| released A 61.5514 | ENGINE_WRONG on 2F thickness (+0.6250, tag spread) and on 13 faces that are not slab (+0.6462); ENGINE_RIGHT on the 62 panels' areas (within 0.002 m2 each) |
| released bounded 2.7403 (1F) | NOT SLAB (west dome square; T-139 s.4); already retired in the candidate |
| candidate V3.0.8 60.9192 | ENGINE_WRONG on the 13 non-slab faces (+0.6388); ENGINE_RIGHT on the 62 panels and on 2F thickness (M4 profile) |
| freelancer 59.8174 | GF / 2F RULE_DIFFERENCE within 0.6 % (lump areas); 1F ENGINE_RIGHT on the eight dome-square corners (drawn slab), lump residual 0.059 m3 UNRESOLVED (no breakdown in his cell) |
| CONC.SLAB whole line | CLOSABLE at 60.2804 (C1) once the Checker re-measures every panel; the integration (lane I, T-146) removes the 13 non-slab faces (candidate 60.9192 -> 60.2804); the released no-profile 2F spread is a route G rule fix (new rule version) |

Checker re-measure list (whole line): every SLAB row of LEDGER_T234.csv against ST p.4 / p.5 / p.6 (T-139 face ids;
the five register-derived panels GF-032 / GF-137 / GF-098 / 1F-084 / 2F-013 first); the 2F tags 7B3 / 7B4 and
1A7D / 1A7E inside 2F-011 / 2F-013 only; general note 18 on p.8; the six S-OPENING sets; GF-062 / GF-106 as band pieces.

## 6. Rule, test, lessons row

General rule proposed (every villa; provenance T-234; a new rule version when adopted, R-SLAB-T-1): an untagged slab
panel takes the thickness of the set's general note; a tag printed in one panel never spreads to another; with no
note and no tag the panel is HELD (never a convention); a sunken panel keeps its printed thickness over the full panel;
openings are deducted once against an independent census of the opening marks; a slab total is compared only with the
slab / beam convention of both sides stated (C1 / C2) and converted by band area x t.
Test: tests/t234_slab_line (villa S: tag + note + sunken + duct opening, rotation / mirror / mm; adverse: opening
twice, opening in two panels, census opening not deducted, sunken at reduced depth, finished level as structural top,
tag spread with a general note, cm thickness, HELD never 0, band in slab and beam, band in no line, plate over
full-depth beams DOUBLE in 3-D; Alsenan ledger pinned).
Lessons row (proposed): 2026-10-23 | released 2F slab 0.18 on panels the note gives 0.16 (+0.625 m3) | a tag inside one
panel was generalised to the sheet because every tag on that sheet was equal; the general note was not read | an
untagged panel takes the general note's value, never a neighbour's tag (every villa) | tests/t234_slab_line
test_tag_spread_to_untagged_panel_refused (adverse) + test_hand_total_and_panels (normal) | PROPOSED.

## 7. Not done / uncertain

- No second printed source for the note-18 thickness on untagged panels (none exists in the set; one printed source).
- Beam-band GAP for CB5 span 2 lies in CONC.BEAM (T-146), stated, not fixed here.
- No engine or candidate line changed; nothing released.
