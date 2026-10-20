# T-102: beam spans settled by a printed section cut (BEAM_SECTION_CUT_BINDING_V1)

Worker 1 (lane S), 2026-10-20. New policy `engine/source/beam_section_cut_binding.py`, **not wired**: no released
method calls it, so the released Alsenan run is unchanged by construction. It feeds the consolidated opt-in candidate
(ARCH_TAKEOFF_V3.0 + route G) through lane I; no new method version is opened here.

Data: Drive "Alsenan chalet project" / "ST7757 dxf.dxf" (sha256 9f9d1179...38079, the verifier's file), read in the
scratchpad, never copied here. Run: `python -I research/agents_t102/alsenan_t102.py <dxf>
engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json <out.json>` (route G with conventions V6, the scoreboard basis;
the route's own bands, marks and net plan areas are captured by a pass-through wrapper, as in T-085).
`SECTIONS_T102.csv` = one row per section letter per slab sheet (no coordinates).

## What the piece does (general, every villa)

1. Each title `SECTION X-X` on a sheet is paired with the dimensioned outline nearest to it on the SAME sheet, on the far
   side of the title baseline in the title's own frame (titles turned 90 / 180 / 270 deg are read in their frame);
   mutual pairing; a letter titled twice on one sheet, or a section on another sheet, is HELD (never borrowed).
2. Printed width / depth = the DIMENSION values shown on the beam part of the outline (override text > the dimension's
   own block text > measurement x DIMLFAC). The unit is proven by the plan: printed width x unit = drawn width of the
   crossed span (cm / mm / m, binder tolerance 0.015 m); one drawing scale for every value (V2 `section_profile`).
3. The cut line (V2 `section_cuts`: cut + view arrows + letter) must cross exactly ONE span of the printed width,
   straight or curved; none -> HELD, two or more -> HELD. The other crossed spans are listed: the section neither
   shows nor excludes them (owner Q-61 C(5)).
4. Schedule check on the span's mark (printed, or the mark the route only proposes along the line): row = printed
   width AND depth -> released DRAWING-VERIFIED (Q-17 A); a different row -> HELD CONFLICT with both volumes (Q-61
   C(1)); two marks -> HELD; no mark -> the printed section alone (SECTION_ONLY), never a neighbour's size (Q-16 A).
5. m3 = route net plan area (or printed width x clear length) x printed depth. Upstands are listed through V2
   `upstand_lines`, never added to the span. Held = no number in a total, candidates kept; missing never becomes 0.

## Alsenan result (route G, conventions V6)

| Sheet | Section | Span (route band) | Printed | Proposed mark / schedule row | Clear length | m3 | State |
|---|---|---|---|---|---|---|---|
| 1F roof slab (SH04) | B-B | BAND0031.1, B23 west span, 0.45 drawn | 45 / 75 cm (DIMLFAC 0.025 = 1:4 x cm) | B23 45 x 75 = printed | 3.000 m | **1.0125** | RELEASED, DRAWING-VERIFIED |
| GF roof slab (SH06) | A-A | BAND0043.1, B20 west span, 0.40 drawn | 40 / 75 cm | B20 40 x 75 = printed | 3.000 m | **0.900** | RELEASED, DRAWING-VERIFIED |
| GF roof slab | C-C | crosses CB1 (BAND0041.2, 0.35, printed mark, already released 1.339) | 55 + 20 = 75 deep, arched top (both top corners rounded); width NOT printed; bars 'AS PER SCH.' | CB1 35 x 75 (depth agrees) | - | - | HELD: outline not rectilinear; no change, CB1 is released by its own mark |
| GF roof slab | D-D | three cut lines lettered D: two cross CB1 (0.35), one (vertical, NE corner) crosses B24 (0.50) | 55 + 20 = 75 deep, one top corner rounded (20), width not printed, drawn 0.348 | - | - | - | HELD: CUT_AMBIGUOUS; the B24 line cannot be this profile (drawn 0.348 vs 0.50): designer D-30; no change (CB1, B24 released by marks) |
| Ground-beam plan (SH08) | "C" | column-type texts 'C' near ground-beam lines read as letters | - | - | - | - | HELD: CUT_AMBIGUOUS, no SECTION C-C on that sheet: nothing bound (a guard case, not a section) |

Also listed (not bound): B-B crosses BAND0013 (0.20, the strip north of B23, unbound) and BAND0019 (B6, 0.25, released
by its mark); A-A crosses BAND0031 (0.20 strip north of B20, unbound). Upstands from the same sections: 0.20 x 0.20 x
3.000 = 0.120 m3 each (B-B, A-A), listed apart (they are T-085's lines, not this task's).

### Second basis and second drawing

- Route G on the M4 basis (conventions V3 + the committed profile `research/urban_engine_m4_correctness/profile_st7757_m4.json`,
  `--profile`): identical states and volumes for all five letters.
- Drive "Alsenan chalet project" / ST7757.pdf (raster): page 5 (FIRST FLOOR ROOF SLAB) prints SECTION B-B 45 (25 + 20) x 75 with
  a 20 x 20 upstand, 11 dia 18 top and bottom, 3 dia 18 in the upstand; page 4 (GROUND FLOOR ROOF SLAB) prints SECTION A-A
  40 (20 + 20) x 75, the same bars, and SECTION C-C / D-D 55 + 20 with rounded tops and 'AS PER SCH.'; the east edge of
  page 4 shows the three D cut marks (two across CB1, one down through the B24 corner) and the C mark at the void. Same
  as the DXF.

### Hand check on the drawing (scratchpad DXF, mm)

- B23 west span: faces y 44.898 / 45.348 (0.450), west face of the span x 13.969 (CB10 inner face), column S-COL
  16.969 .. 17.769 -> clear 16.969 - 13.969 = **3.000 m**; cut B-B at x 15.667 runs y 42.977 .. 46.350, letter B at
  the north arrow. Section B-B (title at 6.571, 45.207): outline 7.177 .. 8.977 x 46.391 .. 50.191 (drawn 1.800 x
  3.800), dimensions 1800 -> "45", 3000 -> "75", 1000 -> "25", 800 -> "20", 800 -> "20" (DIMLFAC override 0.025);
  "11 T18" printed top and bottom. 3.000 x 0.45 x 0.75 = **1.0125 m3** = engine.
- B20 west span: faces y 44.948 / 45.348 (0.400), x 52.693 .. 55.693 (column east of it) -> **3.000 m**; cut A-A at
  x 54.744. Section A-A: outline 43.029 .. 44.629 x 46.391 .. 50.191, "40" / "75" / "20" / "20". 3.000 x 0.40 x
  0.75 = **0.900 m3** = engine.
- Both = T-043 (SPANS.csv SH04-09, SH06-05) and T-110 (BM-1F-026, BM-GF-043), done independently earlier.

## Owner manual method vs drawing-derived method (side by side)

| Span | Owner manual method (URBAN-BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN@v1: schedule row of the beam x clear length on the plan) | Drawing-derived (this piece: printed section on the span) | Difference |
|---|---|---|---|
| 1F B23 west | needs a mark on the span; the span has none, the B23 text is on the east span: by Q-16 A the manual method may not copy it -> HELD (route G today: UNLABELLED_SPAN_ACROSS_SUPPORT, exposure 1.0125) | 45 x 75 printed on the span, = B23 row -> 1.0125 m3 | the section supplies the evidence the manual method lacks; same number once settled |
| GF B20 west | same: HELD (exposure 0.900) | 40 x 75 printed, = B20 row -> 0.900 m3 | same |

## Before / after (beam concrete, Alsenan)

- Released route G today (unchanged, not wired): beams 64.820 m3 vs freelancer 65.97 m3 (-1.150 m3, -1.7 %); these two
  spans are HELD (exposure 1.0125 + 0.900 = 1.9125 m3).
- With this piece in the V3.0 candidate (lane I wiring): +1.9125 m3 released DRAWING-VERIFIED -> 66.7325 m3 vs freelancer
  65.97 (+0.763 m3, +1.2 %). The beam line is still NOT comparable as a whole: 19 HELD + 7 CONFLICT records remain
  (T-110: 4.12 .. 8.55 m3 held, conflict 5.12 / 6.09 m3), so no accuracy claim.
- The freelancer gives one beam total, no per-span figure: per-span verdict proposal **ENGINE_RIGHT** (hand calculation
  above from the printed sections and the drawn spans); against the freelancer total: UNRESOLVED until the held records
  are settled.

## Held items and what is missing

- C-C / D-D: the only sections with a rounded top (C-C arched, D-D one corner of 20); no printed width, so the profile
  reader (rectilinear only) holds them; the concrete the rounding removes from CB1 is not measured anywhere (CB1 is
  released as a full 0.35 x 0.75 rectangle; a few thousandths of a m3 per metre, not quantified here). Designer D-30: three cut lines carry the letter D, one of them through B24 (0.50) which the D-D outline
  (drawn 0.348) cannot be.
- The 0.20 strips north of B20 / B23 stay HELD (Q-61 C(5)): the sections draw only the beam outline.
- Not in scope (task row): CB10, CB3, the ring segments, unlabelled spans without a section, the 0.20 strips.
- The piece reads rectilinear sections only; curved / chamfered sections and sections whose width is printed as a
  leader note (not a DIMENSION) are HELD, never guessed.

## Tests

`tests/t102_section_cut_binding` (19): hand fixture NOT Alsenan (two sheets at 1:100 with 1:25 sections in cm, letters
restart per sheet): released span 0.540, unmarked span settled by its own section 0.500, letter A on sheet 2 1.120 with
its upstand 0.160 listed apart; HELD: one cut crossing two spans of the printed width, a section 30 x 70 vs its schedule
row 30 x 60 (0.840 / 0.720 both kept), depth not printed, section only on the other sheet, two cut lines of one letter,
a title with no cut, printed width that is no unit of the drawn span, a ring of the printed width crossed with a
straight span; mirrored, turned 90 deg, metres, turned + mirrored + metres, sections printed in mm: identical states and
volumes.
