# T-036: census of the 205 HELD concrete lines (Alsenan, ARCH_TAKEOFF_V2.9 + route G)

Worker 2, 2026-10-19. Docs only: no engine, rule, knowledge, test or data file changed. Development reference, not an
accuracy claim. Drawing coordinates, labels and client data are left out; lines are named by cause, sheet number and
counts only.

## Inputs and runs (outside the clone, nothing private committed)

| Input | Where | sha256 |
|---|---|---|
| architectural DXF | Drive "Alsenan chalet project" / "P7757_DXF_COMPRESSED.zip", unzipped | ab54dd55...31cc4 (= SOURCE_MANIFEST.json) |
| structural DXF | Drive "Alsenan chalet project" / "ST7757 dxf.dxf" | 9f9d1179...38079 (= SOURCE_MANIFEST.json) |

Working branch b35c944, Python 3.11.17 venv from requirements.txt.

- **Run A** (the T-001b command, unchanged): `tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.9 --structural ST7757.dxf
  --conventions engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json --no-m9-xlsx --no-svg`. Exit 0. Concrete lines of
  the 13 keyed item codes: 452; HELD (T-001b release class: not MEASURED / SOURCE_DERIVED / PROVISIONAL with a
  quantity, not an exclusion): **205** = columns + necks 118, ground beams + ground slab 61, beams 24, slab 1,
  blinding 1. Same counts as T-001b.
- **Run B** (diagnostic only, never a scoreboard row): run A + `--profile
  research/urban_engine_m4_correctness/profile_st7757_m4.json`, the committed person-confirmed route G drawing profile
  for this structural set (drawing_sha256 = 9f9d1179..., M4; every value carries provenance PRINTED_VALUE /
  READING_OF_PRINTED_VALUE / PRINTED_MINIMUM and its sheet). Exit 0. Concrete lines 439, HELD **38**.

Main finding: **167 of the 205 held lines (81 %) are held only because the T-001b command did not pass the
structural drawing profile.** Route G reads storey heights, neck levels, founding depth, the ground-beam typical
sections and the blinding thickness from the profile (`engine/source/generic_route.py:58`, `:1274`, `:1382`, `:936`);
`tools/urban_boq_m9.py:3022` accepts `--profile` and forwards it (`:2831`), but T-001b ran without it. None of these
values is read from the drawing by the engine itself: they were typed from the printed drawings in M2-M4.

Urban rules: no UP-* rule decides any route G concrete hold. Every held line cites
`URBAN_M8_GENERIC_CONVENTIONS_V6` (the convention set) as its rule; the governing Urban rules are UP-QTY-STATUS-001
(held stays held, never 0) and UP-HGT-001 (heights are read from the drawing by an evidence hierarchy, with source).
`engine/source/generic_route.py` and `member_detection.py` are FROZEN (T-025a row): every fix below is a new module /
route version, never an in-place edit.

## Census by cause (run A; run B column = the same component with the profile)

| # | Cause (hold code) | Item | Lines | Floors | State | m3 at stake (run A exposure) | Code that holds it | Urban rule | Run B (profile) |
|---|---|---|---|---|---|---|---|---|---|
| C1 | STOREY_HEIGHT_NOT_PRINTED | STR.CONC.COLUMN | 74 | GF 30, 1F 22, 2F 22 | BLOCKED_RFI | no range (missing, not 0) | `generic_route.py:696-707` (piece state NO_HEIGHT from `member_detection.py:600-605`; heights from profile `STOREY_HEIGHT_*`, `generic_route.py:58`) | UP-HGT-001 | 61 RELEASED 35.286 m3; 13 not counted, each recorded as COLUMN_ABSENT_ON_STOREY_PLAN (13 exception records, `generic_route.py:680-685`) |
| C2 | NECK_HEIGHT | STR.CONC.NECK | 28 | FOUNDATION | BOUNDED_EXPOSURE | 2.670 - 13.350 | `generic_route.py:1268-1316` (needs profile NECK_TOP_LEVEL_M + FOUNDING_DEPTH_M, `:1274`) | UP-HGT-001; founding level = OQ-13 | 28 RELEASED 10.855 m3 |
| C3 | UNBOUND ground band, no typical section | STR.CONC.GROUND_BEAM | 59 | GROUND | BOUNDED_EXPOSURE | 17.801 - 59.337 | `generic_route.py:1027-1046` (GB_DEPTH_EXPOSURE_M); the typical-class path `:936` needs profile GB_TYPICAL_SECTIONS, absent from the V6 convention set | none | 58 RELEASED 27.365 m3 (34 class depth, 24 perimeter class base); **1 band (SH08 BAND0044, 6.29 m x 0.30 m, 1.886 m2 plan) absent from every run B output** |
| C4 | SLAB_STAIR_ZONE | STR.CONC.GROUND_SLAB 1, STR.CONC.SLAB 1 | 2 | GROUND, 1F | BOUNDED_EXPOSURE | 3.577 | `generic_route.py:1195-1210`; stair rise needs `STOREY_HEIGHT_*` (`:1937-1939`) | UP-STAIR-002 | both replaced by measured stair runs (STAIR_ZONE_PARTIAL_MEASURED, riser convention): STR.CONC.STAIR 3 -> 4 lines, 4.635 -> 9.954 m3 |
| C5 | BLINDING_THICKNESS_NOT_PRINTED | STR.CONC.BLINDING | 1 | FOUNDATION | BOUNDED_EXPOSURE | 7.276 - 16.887 | `generic_route.py:1377-1382`, `:1460-1466` (profile BLINDING_THICKNESS_M) | none | 2 RELEASED 22.155 m3 (under footings 15.659, under ground beams 6.496) |
| C6 | PLANTED_COLUMN_STOREY | STR.CONC.COLUMN | 3 | UNKNOWN | BLOCKED_RFI | no range | `generic_route.py:2420-2430` (needs `STOREY_HEIGHT_*` + profile PLANTED_COLUMN_LABELS, `:761`) | UP-HGT-001 | 3 RELEASED 1.428 m3 (re-filed on 1F / 2F) |
| C7 | TYPE_NOT_IN_SCHEDULE | STR.CONC.COLUMN | 5 | UNKNOWN | BLOCKED_RFI | 3 with a drawn-section exposure, 2 none | `generic_route.py:696-707` (state from `member_detection.py:392`, `:584`, `:819`) | none | still HELD 5 (3 with exposure 0.378 - 1.161 each) |
| C8 | NECK_SECTION_OR_FOOTING | STR.CONC.NECK | 8 | FOUNDATION | 7 BOUNDED_EXPOSURE, 1 BLOCKED_RFI | 0.405 - 2.025 (1 no range) | `generic_route.py:1306-1316` (6 necks of the same unscheduled column type as C7 with no section; 2 scheduled necks with no footing under them) | none | still HELD 8 |
| C9 | UNBOUND beam band (no mark reaches it) | STR.CONC.BEAM | 12 | 1F 9, GF 3 | BOUNDED_EXPOSURE | 3.572 - 7.800 | `member_detection.py:1105-1111`; exposure `generic_route.py:1027-1046` (schedule depths at the drawn width, else UNTAGGED_BEAM_DEPTH_RANGE_M) | none | still HELD 12 |
| C10 | UNLABELLED_SPAN_ACROSS_SUPPORT | STR.CONC.BEAM | 11 | GF 5, 1F 2, 2F 4 | BOUNDED_EXPOSURE | 4.665 - 5.998 (neighbour-section alternative 5.250) | `generic_route.py:885-905`; convention COLLINEAR_INHERITANCE = SPAN_EVIDENCE_ONLY (V6 profile line 203) | none | still HELD 11 |
| C11 | MULTIPLE_MARKS | STR.CONC.BEAM | 1 | GF | BOUNDED_EXPOSURE | 0.212 - 0.636 | `member_detection.py:1099` | none | still HELD 1 |
| C12 | SLAB_CELL_FREE_COLUMNS | STR.CONC.GROUND_SLAB | 1 | GROUND | BOUNDED_EXPOSURE | 3.930 (39.30 m2 x 0.10) | `generic_route.py:1195-1210` | none | still HELD 1 |
| | **Total** | | **205** | | | | | | 167 released / replaced / recorded, 38 held, 1 lost |

Count check: 74 + 28 + 59 + 2 + 1 + 3 + 5 + 8 + 12 + 11 + 1 + 1 = 205.
Hold reason codes are the canonical lines' `rfi.question`; the run B column matches components by element id without
its U-C / P-C prefix.

## Scoreboard effect of run B (diagnostic, T-001b key map and scorer from 3f47ec2, unchanged)

| Key | Freelancer m3 | Run A | Run B |
|---|---|---|---|
| CONC.BLINDING | 47.055 | HELD | COMPARED 22.155 (-24.900) |
| CONC.FOOTING | 77.6305 | 77.265 | 77.265 (unchanged) |
| CONC.GROUND | 75.09 | HELD | HELD (C12: 1 ground slab line) |
| CONC.COLUMN | 39.7515 | HELD | HELD (C7, C8: 13 lines) |
| CONC.BEAM | 65.966 | HELD | HELD (C9-C11: 24 lines) |
| CONC.SLAB | 59.817 | HELD | COMPARED 60.919 (+1.102) |
| CONC.STAIR_DOME | 21.8328 | 12.007 | 17.326 (-4.507) |
| CONC.POOL | 12.348 | 3.495 | 3.495 (unchanged) |
| CONCRETE m3 row | | 3 compared, WAPE 17.03 % | 5 compared, WAPE 18.17 % (signed -17.16 %) |

Released sums on still-held keys (diagnostic only, never compared): column + neck 36.714 + 10.855 = 47.569 m3 released
with 13 lines held (ref 39.75: the freelancer's column row may not hold the necks; to check); ground 27.365 + 17.241
with 1 held (ref 75.09).

## Decision per cause

| # | Decision | Proposed task / question (one each) |
|---|---|---|
| C1, C2, C4, C5, C6 (110 lines) | **FIX TASK (scoreboard run, no code):** the profile already exists, is committed and person-confirmed. | T-036-F1: rerun the T-001b scoreboard with `--profile research/urban_engine_m4_correctness/profile_st7757_m4.json` and record the run-B rows; the lead decides whether a scoreboard row may use a typed profile (its provenance column says which values are PRINTED_VALUE vs PRINTED_MINIMUM: FOUNDING_DEPTH_M 1.5 base, 2.0 high not printed = OQ-13). |
| C1, C2, C4, C6 (general) | **FIX TASK (general, new route version):** on another villa nobody types a profile, so route G must read storey heights / GF level / neck top from the drawing itself under UP-HGT-001. | T-036-F2: new module (route G version) that reads floor-to-floor heights and the GF level from the architectural section levels (T-013 section binding supplies them) and hands them to route G as `STOREY_HEIGHT_*` / `NECK_TOP_LEVEL_M` with source; missing -> stays HELD. Hand fixture: 2-storey synthetic section, mm and m. After T-013. |
| C3 (59 lines) | **FIX TASK (general):** the typical ground-beam sections are printed as titles on the structural details sheet; route G reads them only from a typed profile. | T-036-F3: a reader of typical ground-beam section titles by span band (`< 2.5 m (30x30)` style, English / Arabic, cm / m) into GB_TYPICAL_SECTIONS with source; ambiguous or overlapping bands HELD. Synthetic fixture only. |
| C3 (1 band lost) | **FIX TASK (defect, first):** with the profile, ground band SH08 BAND0044 (1.886 m2 plan, 0.566 - 1.886 m3 in run A) appears in no run B output (lines, registers, exceptions, overlays): a possible silent omission introduced by a profile value. | T-036-F4: trace BAND0044 between run A and run B (stair-zone measurement or exterior class taking the band?); either it is inside a measured element (state which) or the new route version must hold it. Accept: every run A ground band is in run B as released, held or a named exclusion. |
| C5 | Covered by T-036-F1 (blinding 0.10 m read from the structural general notes, profile READING_OF_PRINTED_VALUE). Verdict proposal for run B's -24.90 m3: **UNRESOLVED** (the freelancer may include blinding under the ground slab / straps; needs a term-by-term hand calculation from the footing and ground-beam plans, as T-037). | fold into T-037 style hand calc (T-036-F5 below) |
| C7, C8 (13 lines) | **FIX TASK (hand reading, docs):** one column type mark on the column plan (sheet SH12) and the foundation plan (SH10) has no row in the column schedule; 6 necks of that type have no section, 2 scheduled necks have no footing under them. No Urban rule needed: either the drawing prints the type somewhere (schedule, detail, note) or it is an RFI to the designer. | T-036-F5: hand read of the structural sheets (DXF + ST PDF) for that column type and the 2 footing-less necks; each line ENGINE_HELD_CORRECTLY (not printed: RFI) or ENGINE_MISSED_PRINTED_VALUE (-> fix task). Also settles C12 (is the 39.30 m2 ground cell with one free column a slab, void or court, from the architectural ground floor plan). |
| C9, C11 (13 lines) | **FIX TASK (hand reading, docs):** a beam band with no mark, or with two marks, is held correctly unless the drawing prints a mark the binder missed. | T-036-F6: hand check of the 12 UNBOUND + 1 MULTIPLE_MARKS bands on the GF / 1F slab plans: label present and missed (binder defect -> new member_detection version task) or absent (RFI, held correctly). |
| C10 (11 lines) | **OWNER QUESTION (proposed, not added: lead decides; OQ-11 is about beam depth, not this):** "A beam span with no label sits in line with a labelled beam across a column or beam support. Which section should the BOQ use? (a) hold it until the designer labels it (today: 11 lines, 4.67 - 6.00 m3 held); (b) take the labelled neighbour's section (5.25 m3 on this villa) as a provisional line marked 'section from neighbour'; (c) take the neighbour's section only when the width drawn is the same." Example the owner can check: GF slab plan, a 3.0 m span at 0.40 m wide next to a labelled 0.75 m deep beam gives 0.90 m3 under (b). | Q-new (C10) |

Order by money at stake (run A upper exposure): C3 59.3 m3, C5 16.9, C2 13.4, C9 7.8, C10 6.0, C12 3.9, C4 3.6, C8 2.0,
C11 0.6; C1 / C6 / C7 carry no range (BLOCKED_RFI) but C1 is 35.3 m3 once released.

## Verdict proposals (for the verifier; run B is a diagnostic, not the scoreboard)

- CONC.BLINDING run B 22.155 vs 47.055: UNRESOLVED (no hand calculation).
- CONC.SLAB run B 60.919 vs 59.817 (+1.8 %): UNRESOLVED (no hand calculation).
- CONC.STAIR_DOME run B 17.326 vs 21.833: UNRESOLVED, still Q-12 / T-037 (the stair lines changed with the storey rise).

## Uncertain

- Run B uses a typed profile; whether a scoreboard row may rest on it is a lead / owner call (T-036-F1).
- 13 columns are "not counted" in run B because the roof-slab plan of that storey shows no column outline at the
  position; recorded as exceptions, not silent, but not checked by hand here.
- BAND0044 (C3) was not traced to a cause in this run.
