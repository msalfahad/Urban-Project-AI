# T-064: controlled project data file for typed drawing values (owner Q-17 A)

Worker 2, 2026-10-20. New module, not wired into any released method: no released quantity, method, rule or
knowledge version changed. Development reference, not an accuracy claim.

## What was built

- `engine/source/project_data_file.py` (schema `URBAN_PROJECT_DATA_FILE_V1`): loader and validator of typed drawing
  values with the fields owner Q-17 A lists (drawing file, number, revision, sheet / page, exact note / dimension /
  detail reference, units, value, applies-to floors / members, status, reviewer or source, `entered_by: TYPED`). Status
  words exactly DRAWING-VERIFIED, OWNER-CONFIRMED, DESIGNER-CONFIRMED, INFERRED, ASSUMED, HELD.
  - Refused: a record without a source; any drawing reference field missing; INFERRED without logic, or citing an input
    that is not DRAWING-VERIFIED / OWNER-CONFIRMED / DESIGNER-CONFIRMED (or itself, or a key not in the file);
    `entered_by` other than TYPED; unknown status, unit or field; non-finite / bool numbers; a value missing on a
    non-HELD record; HELD without a reason; duplicate keys; a record of another project. A refused file lists every
    fault and loads nothing.
  - `quantity(keys, compute, floor, member)`: compute runs only when every input is usable; ASSUMED, HELD, a missing key
    or a record whose applies-to does not cover the floor / member gives state HELD, quantity None (never 0,
    UP-QTY-STATUS-001). Units m / cm / mm are normalised to metres.
  - Every result carries basis `TYPED_PROJECT_DATA`; `automatic_only(lines)` drops such lines so typed answers never
    count as automatic extraction (Q-17 A last sentence).
- `research/urban_engine_m4_correctness/project_data_st7757_t064.json`: the 17 keys of the typed route G profile
  `profile_st7757_m4.json` (left untouched) in this format, built by `research/agents_t064/build_st7757_project_data.py`.
- `tests/t064_project_data_file/`: synthetic villa SV-PDF (not a client project), one record of each status, cm / mm / m,
  hand-calculated quantities and every refusal; plus checks of the converted file. 63 tests.

## Re-check of the drawings (second reading, 2026-10-20)

Drive copies, read outside the clone: "ST7757 dxf.dxf" sha256 9f9d1179...38079 (= profile `drawing_sha256`),
"P7757_DXF_COMPRESSED.zip" -> P7757.dxf ab54dd55...31cc4, "ST7757.pdf" 74da1523...337e3 (p.13 rendered at 110 dpi).

| Value | Found again |
|---|---|
| GF / 1F / 2F levels | P7757 LEVEL texts `+1.00` (4), `+5.50` (5), `+9.70` (3); ST7757 `+1.00` (5), `+9.70` (2) |
| 2F storey 4.20 | P7757 elevation dimensions `1000`, `8700`, `4200`, `500`, `14400` (twice): 1000 + 8700 + 4200 + 500 = 14 400 |
| Outer ground | ST7757 `%%p0.00` (6) and `+0.15` (6); P7757 also `+0.30` (annex floor level) |
| Excavation note | ST7757 S-TEXT.SCH TEXT `1.5` beside the SHX Arabic note |
| Slab 16 cm | ST7757 S-NOTE SHX Arabic note with `16` (style AR) |
| CB typicals | `0.22 Ln` / `Ln1` / `Ln2` (6), `0.3 Ln2` (3), `7.5cm` (8) on S-DIM.SCH |
| p.13 details | ground-beam titles 30x30 / 30x40 / 30x60 ("without concentrated load" on the last two), exterior detail W 30 "FOLLOW ARCH.", `10cm Plain con.` under both footing details, `10 | 30 | 10` under the beam sections, lintel schedule 5 rows |
| Revision | none printed: ST7757.pdf title block has SCALE / DATE / FILE NO only; no revision text in either DXF |

## The converted file: every key, status and source

| Key | Value | Status | Source (sheet, printed text) |
|---|---|---|---|
| STOREY_HEIGHT_GF | 4.50 m | DRAWING-VERIFIED | P7757 levels `+1.00` / `+5.50`, elevation `4500` |
| STOREY_HEIGHT_1F | 4.20 m | DRAWING-VERIFIED | P7757 levels `+5.50` / `+9.70`, elevation `8700` = 4500 + 4200 |
| STOREY_HEIGHT_2F | 4.20 m | DRAWING-VERIFIED | P7757 elevation chain `1000 / 8700 / 4200 / 500` = `14400` (no +13.90 text in any DXF) |
| GB_TYPICAL_SECTIONS | <2.5 m 30x30, <5 m 30x40, >5 m 30x60 | DRAWING-VERIFIED, with the printed condition "without concentrated load" | ST7757 PDF p.13 titles |
| FOUNDING_DEPTH_M | 1.50 m shown, not used | HELD (owner Q-21 C) | ST7757 SH11 note 1: excavation level not less than 1.5 m below the existing plot level |
| GF_FLOOR_LEVEL_M | +1.00 m | DRAWING-VERIFIED | ST7757 SH08 and P7757 GF `+1.00` |
| NECK_TOP_LEVEL_M | +1.00 m | INFERRED from GF_FLOOR_LEVEL_M + GB_EXTERIOR_DETAIL | no neck level printed; p.13 details run the neck to the GF slab level |
| OUTER_GROUND_LEVEL_M | 0.00 m (+0.15 elsewhere, shown) | DRAWING-VERIFIED | ST7757 SH08 `%%p0.00`, `+0.15` |
| GB_EXTERIOR_DETAIL | W 0.30, depth "FOLLOW ARCH." | DRAWING-VERIFIED | ST7757 PDF p.13 "Ground Beams. for exterior walls"; SH12 neighbour-side block note recorded as a condition |
| BLINDING_THICKNESS_M | 0.10 m | DRAWING-VERIFIED | ST7757 PDF p.13 `10cm Plain con.` |
| BLINDING_UNDER | footings and ground beams | DRAWING-VERIFIED | ST7757 PDF p.13 layer under both footing details and all beam sections |
| BLINDING_PROJECTION_M | 0.10 m | DRAWING-VERIFIED | ST7757 PDF p.13 `10 | 30 | 10`, `10` each side of `L x W` |
| CB_SUPPORT_BAR_EXTENT_FRAC | 0.22 | HELD (T-044 DIFFERENT: `0.3 Ln2` also printed) | ST7757 SH03 / SH05 / SH07 |
| CB_SUPPORT_BAR_SPAN_BASIS | AXIS | HELD (T-044 NOT_PRINTED) | ST7757 SH03 / SH05 / SH07 |
| CB_BOTTOM_EXTENSION_M | 0.075 m | DRAWING-VERIFIED | ST7757 `7.5cm` (8 dimensions) |
| SLAB_PROJECT_DEFAULT_THICKNESS_M | 0.16 m | DRAWING-VERIFIED (owner Q-14) | ST7757 SH12 note "all slabs 16 cm unless stated otherwise"; PDF p.8 note 18, p.1 |
| LINTEL_SCHEDULE | 5 rows | DRAWING-VERIFIED | ST7757 PDF p.13 "LINTEL SCHEDULE" |

13 DRAWING-VERIFIED, 1 INFERRED, 3 HELD; 0 OWNER- / DESIGNER-CONFIRMED, 0 ASSUMED.

## The 167 concrete lines held without the profile (T-036): what the data file releases

Per-line profile keys from the T-044 r2 run B table (`research/agents_t044/T-044_RUN_B_LINE_DEPENDENCIES.csv`), classified
by `classify_run_b_lines.py` through the module (line by line: `T-064_RUN_B_LINE_STATUS.csv`). A line that also rests
on an unprinted V6 convention (not a typed drawing value, outside this file) stays held.

| T-036 cause | Lines | m3 (run B) | With the data file | Why |
|---|---|---|---|---|
| C1 columns, storey height | 61 | 35.283 | RESTS ONLY ON DRAWING-VERIFIED | STOREY_HEIGHT_GF / 1F / 2F |
| C6 planted columns | 3 | 1.428 | RESTS ON DRAWING-VERIFIED, flagged | each names two storey heights (filed on 1F / 2F, takes the storey below too): the planted-column storey binding is a route reading to check |
| C5 blinding | 2 | 22.155 | RESTS ONLY ON DRAWING-VERIFIED | thickness, projection, under footings and ground beams |
| C2 necks | 28 | 10.853 | HELD | FOUNDING_DEPTH_M HELD (owner Q-21 C) |
| C3 ground beams | 58 | 27.365 | HELD | the data values are usable, but every line rests on GB_LENGTH_BASIS (centre to centre, STANDARD_PRACTICE) and the 24 exterior ones also on GB_EXTERIOR_BUILDUP_M / GB_EXTERIOR_CANDIDATE (not printed); the 30x40 / 30x60 titles carry "without concentrated load" |
| C4 stair zones | 2 (now stair runs) | 6.220 | HELD | riser / waist conventions not printed (Q-19, Q-20) |
| C1 columns not counted | 13 | - | records, not quantities | COLUMN_ABSENT_ON_STOREY_PLAN |
| C3 band lost in run B | 1 | - | not a line | T-036-F4 trace (BAND0044) |
| **Total** | **167** | | **66 lines 58.866 m3 rest only on DRAWING-VERIFIED values; 88 lines 44.438 m3 stay held; 13 records + 1 lost** | |

The 69 slab lines that name SLAB_PROJECT_DEFAULT_THICKNESS_M (51.953 m3, mostly released without the profile too) now
rest on a DRAWING-VERIFIED value (Q-14). Sums are from the T-044 table (run B on head 56820cb); not re-run on this head.

Against the freelancer (diagnostic, T-036 run B scorer, not a scoreboard row): blinding 22.155 vs 47.055 m3, -24.900 m3
(-52.9 %), verdict proposal UNRESOLVED (unchanged from T-036: needs a term-by-term hand calculation; the freelancer may
include blinding under the ground slab / straps). Columns: CONC.COLUMN stays a held key (13 lines held by C7 / C8 and
the 28 necks held by Q-21 C); 36.711 m3 released columns vs the freelancer's 39.75 m3 column row is not comparable while
the necks are held. No quantity in the released ARCH_TAKEOFF methods moved.

## What is missing

- Not wired: a route G version that reads this file instead of the profile (and states basis TYPED per line) is the
  next step; route G (`generic_route.py`) is frozen, so it is a new route version.
- C3 ground beams need an owner / rule answer on GB_LENGTH_BASIS and the exterior build-up before they can release.
- Revision: neither structural nor architectural drawing prints a revision; the file says so in words.
