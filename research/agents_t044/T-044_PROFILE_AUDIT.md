# T-044: audit of the typed route G profile `profile_st7757_m4.json` against the printed drawings (Alsenan, development villa)

Worker run 2026-10-19. Diagnostic only (owner Q-17 open): no engine, profile or scoreboard change. Development
reference, not an accuracy claim.

## Inputs (read outside the clone, never committed)

| Input | Where (Drive "Alsenan chalet project") | sha256 |
|---|---|---|
| ST7757.dxf (3 153 037 bytes) | "ST7757 dxf.dxf" | 9f9d1179...38079 (= profile `drawing_sha256`, = manifest) |
| P7757.dxf (17 227 946 bytes) | "P7757_DXF_COMPRESSED.zip", unzipped | ab54dd55...31cc4 (= manifest) |
| ST7757.pdf (16 pages, no text layer) | "ST7757.pdf" | read visually at 220-300 dpi + English OCR (Tesseract) of all 16 pages; no Arabic OCR model here, Arabic notes read visually |

Text census: every TEXT / MTEXT / ATTRIB / DIMENSION of both DXFs, nested block inserts included (ezdxf 1.4.4):
ST7757 2 630 strings, P7757 664. Sheet ids SH01-SH12 are route G's own frames (`structural/SUMMARY.json` sheets; same
order and boxes as `PROFILE_TEMPLATE.json` FR01-FR12). The 16-page PDF holds four detail sheets (p.13-16: typical
footing / ground-beam / lintel details, lift pit, columns, stairs) and the general notes page (p.8) that are NOT in
the DXF: the DXF has 12 frames only.

## Result per profile key (17 keys)

Class: PRINTED = the same value is printed in the drawing set; DIFFERENT = a printed value disagrees; NOT_PRINTED =
not found on any sheet. "Where" says whether the engine could read it (DXF text) or only a person (PDF glyphs).

| # | Key | Profile value | Printed evidence (sheet, text, value) | Class | Where | Notes |
|---|---|---|---|---|---|---|
| 1 | STOREY_HEIGHT_GF | 4.50 | P7757 GF plan level `+1.00` (LEVEL layer) and 1F plan `+5.50`; NW elevation dimensions `1000`, `4500` (and `5500` to the +5.50 level); ST7757 SH08 `+1.00` | PRINTED | DXF | floor-to-floor (level interval); source "VE-AA-09" is not a sheet title in either DXF (DWF sections, T-035) |
| 2 | STOREY_HEIGHT_1F | 4.20 | P7757 `+5.50` and 2F plan `+9.70`; ST7757 SH02 `+9.70` (2 texts); both elevations `8700` = 4500 + 4200 | PRINTED | DXF | as 1 |
| 3 | STOREY_HEIGHT_2F | 4.20 | P7757 SE and NW elevations, vertical chain `1000 / 8700 / 4200 / 500` = `14400` overall: 4200 is the top storey under the 500 parapet | PRINTED | DXF | no `+13.90` level text in either DXF (only in the DWF sections, T-035); the value rests on the elevation chain |
| 4 | GB_TYPICAL_SECTIONS | <2.5 m 30x30, <5 m 30x40, else 30x60 | PDF p.13: "Ground Beams. Less than 2.5m length" 30x30; "Ground Beams. Less than 5m length without concentrated load" 30x40; "Ground Beams. More than 5m length without concentrated load" 30x60 | PRINTED (values) | PDF only | the profile drops the printed condition "without concentrated load": a ground beam carrying a point load (e.g. a planted column) has no printed typical section; the exact-5.0 m edge is a reading |
| 5 | FOUNDING_DEPTH_M | base / low 1.50, high 2.00 | not found: no "1.50" / excavation / founding value in the 2 630 ST7757 strings or 664 P7757 strings; PDF p.8 general notes 1-24 read in full (note 12 only tells the contractor to confirm the founding level from the drawings and a soil test, no value); PDF p.1 notes (slab 16 cm, perimeter beams) have none; OCR of all 16 pages has none; p.13 prints only "more than / less than 2.5m" (level difference ground beam to footing, which picks the detail) | NOT_PRINTED (base 1.50 and high 2.00) | - | the profile's cited "general note (PDF, transcribed): excavation not less than 1.50 m" could not be located; 2.00 already known (OQ-13) |
| 6 | NECK_TOP_LEVEL_M | 1.00 | ST7757 SH08 `+1.00` (5 LEVEL texts), P7757 GF `+1.00` | PRINTED (value) | DXF | "neck top = GF level" is the profile's reading of the p.13 footing details, not a printed statement |
| 7 | GF_FLOOR_LEVEL_M | 1.00 | as 6 | PRINTED | DXF | |
| 8 | OUTER_GROUND_LEVEL_M | 0.00 (high 0.15) | ST7757 SH08 `%%p0.00` (6, block LEL) and `+0.15` (6); P7757 `+0.15`, `+0.30` | PRINTED | DXF | P7757 also prints `+0.30` on the GF plan (not in the profile range; its position not checked) |
| 9 | GB_EXTERIOR_DETAIL | W 0.30 | PDF p.13 "Ground Beams. for exterior walls": width `30`, depth "FOLLOW ARCH.", from "Ground Floor slab level" to "Outer Normal ground level" | PRINTED | PDF only | |
| 10 | BLINDING_THICKNESS_M | 0.10 | PDF p.13: "10cm Plain con." under both isolated-footing details; `10` dimensioned under all four ground-beam sections | PRINTED | PDF only | DXF has only "10cm PLAIN CONCRETE." on SH01, in the swimming-pool detail (pool, not footings) |
| 11 | BLINDING_UNDER | FOOTINGS_AND_GROUND_BEAMS | PDF p.13: the plain-concrete layer drawn and dimensioned under both footing details and all four ground-beam sections | PRINTED | PDF only | |
| 12 | CB_SUPPORT_BAR_EXTENT_FRAC | 0.22 | ST7757 SH03, SH05, SH07 (S-DIM.SCH) dimension overrides `0.22 Ln`, `0.22 Ln1`, `0.22 Ln2` **and** `0.3 Ln2` (one per detail on SH03, SH05, SH07) | DIFFERENT (partly) | DXF | rebar only: no concrete line uses it |
| 13 | CB_SUPPORT_BAR_SPAN_BASIS | AXIS | `Ln` / `Ln1` / `Ln2` dimensions carry no axis or face note; the basis is a reading of where the dimension lines end | NOT_PRINTED (as text) | - | rebar only |
| 14 | CB_BOTTOM_EXTENSION_M | 0.075 | `7.5cm` dimension overrides: SH03 2, SH05 2, SH07 4 | PRINTED | DXF | rebar only |
| 15 | SLAB_PROJECT_DEFAULT_THICKNESS_M | 0.16 | PDF p.8 general note 18 (Arabic): ordinary roof slab thickness 16 cm unless stated otherwise; PDF p.1 note: all slabs 16 cm unless stated otherwise | PRINTED | PDF only | |
| 16 | BLINDING_PROJECTION_M | 0.10 | PDF p.13: `10 | 30 | 10` under each ground-beam section; `10` each side of `L x W` on the second footing detail | PRINTED | PDF only | V6 generic base is also 0.10 (range 0.05-0.15) |
| 17 | LINTEL_SCHEDULE | 5 rows | PDF p.13 "LINTEL SCHEDULE": 0-100 Bx20 2Ø12/2Ø10; 101-200 Bx20 2Ø14/2Ø12; 201-300 Bx30 3Ø16/3Ø14; 301-500 Bx40 3Ø18/3Ø14; 501-750 Bx55 4Ø18/3Ø14; stirrups 5Ø8/M | PRINTED (all rows) | PDF only | no concrete line uses it in run B |

Not a profile key: PLANTED_COLUMN_LABELS (named in the task) is a generic V6 convention (READING_OF_PRINTED_VALUE);
its labels are printed in ST7757: `P.C 20x70` and `P.C 20x50` on SH06, `P.C 20x50` on SH04.

Summary: 14 PRINTED, 1 DIFFERENT (CB extent, rebar only), 2 NOT_PRINTED (FOUNDING_DEPTH_M; CB span basis, rebar
only). Of the 14 PRINTED, 8 exist only as PDF vector glyphs (p.1, p.8, p.13): a person can read them, the engine
cannot (UP-HGT-001 wants the source recorded; T-045 / T-046 are the reader tasks).

## Which run B lines depend on which value

Run B = the T-036 run (T-001b command + `--profile research/urban_engine_m4_correctness/profile_st7757_m4.json`) on
working head 56820cb, Python 3.11.17 (`.venv`, requirements.txt): exit 0, 439 concrete lines, 401 RELEASED, 38 HELD
(same counts as T-036; identical line by line to a Python 3.13 run).

Dependency of a line on a key = the key is in the line's own `calculation.inputs.assumptions` / `rule.conventions_used`,
or the line changes when the run is repeated with that one key removed from the profile (17 ablation runs, all exit 0).
Line by line: `T-044_RUN_B_LINE_DEPENDENCIES.csv` (item, element id, floor, status, m3, profile keys used, the
NOT_PRINTED / DIFFERENT ones, unprinted V6 conventions used, bucket).

Ablation (released run B lines that change when the key is removed):

| Key removed | Lines changed | m3 of those lines in run B | What happens |
|---|---|---|---|
| STOREY_HEIGHT_GF | 32 column | 21.258 | 30 held, 2 not counted |
| STOREY_HEIGHT_1F | 22 column + 1 stair | 15.539 | 19 held, 4 not counted |
| STOREY_HEIGHT_2F | 13 column | 5.796 | 12 held, 1 not counted |
| GB_TYPICAL_SECTIONS | 58 ground beam | 27.365 | all held |
| FOUNDING_DEPTH_M | 28 neck | 10.855 | all held |
| NECK_TOP_LEVEL_M | 28 neck | 10.855 | all held |
| BLINDING_THICKNESS_M | 2 blinding | 22.155 | both held |
| BLINDING_UNDER | 2 blinding | 22.155 | under-beam line gone, footing line changes |
| SLAB_PROJECT_DEFAULT_THICKNESS_M | 7 slab | 5.057 | quantity changes (62 more slab lines name it but do not change) |
| GF_FLOOR_LEVEL_M, OUTER_GROUND_LEVEL_M | 1 stair each | 1.769 | ground stair re-filed |
| GB_EXTERIOR_DETAIL, BLINDING_PROJECTION_M, LINTEL_SCHEDULE, CB_* (3) | 0 | 0 | named by 24 / 2 / 0 / 0 lines; base unchanged without them |

Lines resting on a NOT_PRINTED or DIFFERENT value: **STR.CONC.NECK, all 28 released necks, 10.856 m3, through
FOUNDING_DEPTH_M** (base 1.50 not located, high 2.00 not printed). No concrete line uses the CB keys (12, 13).

### m3 of run B released lines by what they rest on, per item

A = uses no profile value (released without the profile too, or independent of it); B = uses profile values that are
all PRINTED and no unprinted generic convention; C = profile values all PRINTED, but the line also rests on an
unprinted V6 convention (STANDARD_PRACTICE / ENGINEERING_JUDGEMENT); D = uses a NOT_PRINTED or DIFFERENT profile value.

| Item | A: no profile value | B: PRINTED profile only | C: PRINTED profile + unprinted convention | D: NOT_PRINTED / DIFFERENT | HELD |
|---|---|---|---|---|---|
| STR.CONC.BEAM | 112 / 64.820 | - | - | - | 24 |
| STR.CONC.BLINDING | - | 2 / 22.155 | - | - | - |
| STR.CONC.BOUNDARY_WALL | 1 / 7.220 | - | - | - | - |
| STR.CONC.COLUMN | - | 64 / 36.714 | - | - | 5 |
| STR.CONC.DOME | 2 / 7.372 | - | - | - | - |
| STR.CONC.FOOTING | 26 / 66.264 | - | - | - | - |
| STR.CONC.GROUND_BEAM | - | - | 58 / 27.365 | - | - |
| STR.CONC.GROUND_SLAB | 24 / 17.241 | - | - | - | 1 |
| STR.CONC.NECK | - | - | - | 28 / 10.856 | 8 |
| STR.CONC.POOL | 2 / 3.495 | - | - | - | - |
| STR.CONC.SLAB | 6 / 8.968 | 69 / 51.951 | - | - | - |
| STR.CONC.STAIR | 2 / 3.734 | - | 2 / 6.220 | - | - |
| STR.CONC.STRAP | 3 / 3.781 | - | - | - | - |
| **Total (lines / m3)** | **178 / 182.895** | **135 / 110.820** | **60 / 33.585** | **28 / 10.856** | **38** |

401 released = 178 + 135 + 60 + 28. Column C: all 58 ground beams use GB_LENGTH_BASIS (centre to centre,
STANDARD_PRACTICE) and the 24 exterior ones also GB_EXTERIOR_BUILDUP_M 0.10 and GB_EXTERIOR_CANDIDATE (not printed);
the 2 stair runs use the riser / waist conventions (0.165 / 0.175, not printed). Column A is outside this audit (no
profile value), but 10 of its lines (boundary wall, dome, pool, 2 stairs, 1 footing label conflict at its larger type,
1 beam, 1 strap; 25.689 m3) also rest on unprinted V6 conventions.

## For the lead (Q-17)

- Under Q-17 choice (a) ("only values T-044 finds printed"): B (135 lines, 110.820 m3) qualifies; D (28 necks, 10.856 m3)
  stays held; C (60 lines, 33.585 m3) qualifies on the profile but rests on unprinted generic conventions, which is a
  separate question for the lead (GB_LENGTH_BASIS is a measurement basis; the build-up and stair values are not printed).
- GB_TYPICAL_SECTIONS: the printed titles carry "without concentrated load"; whether a beam under a planted column may
  use them is not decided by the profile. Worth one line in Q-17 or a follow-up check of the 58 beams.
- FOUNDING_DEPTH_M: the 1.50 m base itself was not found (not only the 2.00 high). If the owner knows the sheet that
  prints it, a worker can recheck; otherwise every neck stays held under choice (a).
- No who-is-right verdicts proposed: this is not a comparison with the freelancer.

## Reproduce

Run B as in T-036; then for each key a copy of the profile with that one convention removed, the same command with
`--profile <copy>`, and a line-by-line comparison of the STR.CONC lines keyed by (item code, element id without its
U-C / P-C prefix), release class from `tools/alsenan_keymap.py:line_status`.
