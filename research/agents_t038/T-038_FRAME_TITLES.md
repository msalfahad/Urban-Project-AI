# T-038: frame titles and storeys on Alsenan, is a basement lost? (read-only diagnostic)

Worker 2, 2026-10-19. Docs only: no engine, rule, test or quantity change. Development villa: not an accuracy claim.

## Answer

**No basement plan exists in the drawing.** The architectural DXF holds exactly five sheet frames: two elevations and
three floor plans (GF, 1F, 2F), and ARCH_PLAN_V1 reads all three plans. No readable text anywhere in the drawing (model
space, every block, the three RTEXT fields) names a basement in English or Arabic, and no level mark below ±0.00 is printed
on any plan or elevation (lowest marks: ±0.00 / +0.15 on GF and the elevations). The structural DXF agrees: 12
frames, no basement title, no negative level, no lift text. No storey is lost, so UP-QTY-STATUS-001 is not broken by
the storey reading on this villa. T-001b cause 3 ("the freelancer's sheets include a basement") is a label in the
freelancer's concrete workbook, not a storey (see "Where the freelancer's basement comes from").

## Inputs (read outside the clone, never committed)

| Input | Where | sha256 | = tests/alsenan/registers/SOURCE_MANIFEST.json |
|---|---|---|---|
| P7757.dxf (17 227 946 bytes, AC1032, mm) | Drive "Alsenan chalet project" / "P7757_DXF_COMPRESSED.zip", unzipped | ab54dd55...31cc4 | yes |
| ST7757.dxf (3 153 037 bytes, mm) | Drive "Alsenan chalet project" / "ST7757 dxf.dxf" | 9f9d1179...38079 | yes |
| T-029 vocabulary | `engine/source/storey_vocab.py` at agents/task-T-029 28df9f2 (loaded from a scratch copy; not merged here) | - | - |

Reading as ARCH_TAKEOFF_V2.9 does (`tools/urban_boq_m9.py:385-415`): `urban_intake.read` + `arch_intake.read_arch`
texts (SHX decoding, ATTRIB, nested inserts), then `arch_plan.plan_regions` with both splits (TITLE_MIDPOINTS, and
EMPTY_BANDS with the frames-from-lines fallback). Working branch 56820cb, Python 3.11, ezdxf 1.4.4, shapely 2.2.0.
The scratch script (not committed: it only wraps the calls above) printed the per-frame texts that either reader
classifies.

## Every frame of the architectural drawing (P7757)

665 texts, all inside the five frames (0 outside); 36 of 9 411 segments lie outside the frames.

| Frame (drawing_model id, handle) | Title text in the frame | ARCH_PLAN_V1 (`floor_of_title`) | STOREY_VOCAB_V1 (`classify`) | Region V2.9 (both splits) |
|---|---|---|---|---|
| SH01 (132) | NORTH WEST ELEVATION | none (NOT_A_PLAN word ELEVATION) | NOT_A_PLAN | other frame, "no floor-plan title" |
| SH02 (131) | SOUTH EAST ELEVATION | none (ELEVATION) | NOT_A_PLAN | other frame |
| SH03 (130) | 2nd.FLOOR PLAN 1:100 | 2F | RECOGNISED 2F (basis ARCH_PLAN_V1) | SH03:2F |
| SH04 (129) | 1st.FLOOR PLAN 1:100 | 1F | RECOGNISED 1F (basis ARCH_PLAN_V1) | SH04:1F |
| SH05 (125) | GROUND FLOOR PLAN 1:100 | GF | RECOGNISED GF (basis ARCH_PLAN_V1) | SH05:GF |

No frame is HELD_UNRECOGNISED and no region is blocked or unassigned. Each plan frame holds one drawn plan: along x
its segments form one cluster (38.0 m), along y one 19.5 m plan plus the 2.9 m title-block strip, so no second,
untitled plan sits inside a frame. The two readers agree on every frame: T-029 changes nothing on this villa.

Level marks printed (layer LEVEL on the plans, text on the elevations): GF ±0.00, +0.15, +0.30, +1.00; 1F +4.30, +5.50;
2F +9.70; elevations +0.15, +0.30, +1.00, +4.30, +5.50. None is negative. The GF plan's English room labels (SALOON,
RECEPTION, DEWANEYA, DINING, KITCHEN, PANTRY, MASTER BED ROOM, DRIVER, W.C, BATH, Wash, COURT, GARDEN, swimming pool)
include no basement, store-below or stair-down label. About 20 GF texts are SHX-encoded Arabic that the reader does
not decode (16 with non-ASCII bytes, a few that look like ASCII); they could not be read in this check.

The committed register `tests/alsenan/registers/FLOOR_PLAN_REGISTER.json` (floors.BASEMENT = "NONE in any source")
says the same; this run reproduces it independently from the drawing.

## The structural drawing (ST7757), for completeness

2 630 texts in 12 frames. Not read by the architectural route (route G has its own storey reading); listed because
the freelancer's "basement" lines are concrete.

| Frame | Title text(s) | ARCH_PLAN_V1 | STOREY_VOCAB_V1 |
|---|---|---|---|
| SH01 | DETAIL OF SWIMMING POOL / DETAIL OF DOME | none | NOT_A_PLAN |
| SH02 | سقف الدور الثاني (slab over 2F) | 2F | RECOGNISED 2F |
| SH03, SH05, SH07 | SCHEDULE OF CONTINUES BEAMS (2 / 3 SPAN) | none | NOT_A_PLAN |
| SH04 | سقف الدور الاول (slab over 1F), SECTION B-B | none (alef without hamza) | RECOGNISED 1F |
| SH06 | سقف الدور الارضي (slab over GF), SECTIONS A-A, C-C, D-D | none (alef without hamza) | RECOGNISED GF |
| SH08 | GROUND BEAMS PLAN | none | HELD_UNRECOGNISED |
| SH09 | Schedule of Simple Beams | none | NOT_A_PLAN |
| SH10 | FOUNDATION PLAN. | none | HELD_UNRECOGNISED |
| SH11 | Schedule of Columns / Schedule of Footings | none | NOT_A_PLAN |
| SH12 | COLUMN & AXIS PLAN. | none | HELD_UNRECOGNISED |

No basement title, no negative level text, no lift (مصعد / LIFT / PIT) text.

## Where the freelancer's basement comes from (committed registers, no client data)

`tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json`: the word السرداب (basement) appears in exactly two section
headings of the concrete workbook (RC), both normalised to floor FOUNDATION, and in no finishes, blockwork, plaster,
paint or aluminium section (those have GF, 1F and ROOF sections only):

| Heading (RC workbook) | Rows under it | m3 |
|---|---|---|
| حصر الحوائط المسلحة السرداب ("RC walls, basement") | 1 row: lift walls 20 cm, 8.0 x 0.20 x 1.50 | 2.40 |
| حصر خرسانة السلالم السرداب الفرعية ("stairs, basement / secondary") | entrance stair slab + steps 1.41; stair 2 slab + steps 5.51 (16.4 m run); domes 3 x 2.26 = 6.78 | 13.70 |

So the "basement sub-stair 13.70 m3" of T-001b is an entrance stair, a second stair and three domes under a heading
that names a basement; no basement floor area, wall or finish is measured anywhere. The only element that could be
below ground is the 1.50 m high lift wall (a lift pit), and neither drawing prints a lift.

## Verdict proposals for the verifier

- Storeys (T-001b cause 3): **ENGINE_RIGHT**. GF, 1F, 2F are every floor plan in P7757; the freelancer has no basement
  storey either (floor area, plaster and paint shortfalls are not caused by a missing storey). Note for the key map:
  the freelancer's ROOF sections ("طابق السطح", "ارضيات السطح") correspond to the engine's 2F plan (2nd.FLOOR PLAN,
  level +9.70); there is no separate roof plan.
- RC lift walls 2.40 m3 under the basement heading: **UNRESOLVED**. No lift and no pit is drawn or labelled in either
  DXF read here; the verifier should check the PDF sets (architectural PDF is 37.5 MB, above the 10 MB connector
  limit, not read by this run) before the engine is asked for it.
- Stair / dome 13.70 m3 under the basement heading: not a basement element; it belongs to T-037 (Q-12 stair and dome
  hand calculation), unchanged here.

## Proposed general fixes (for the lead; none is needed to read Alsenan)

1. **Storey completeness check (gate 1, UP-QTY-STATUS-001).** Today a basement plan whose title no vocabulary reads, or
   a basement drawn in another file, is simply absent: nothing says a storey is missing. Proposal: a new read-only
   module that collects the finished-floor levels printed on elevations and sections (level marks, e.g. "+4.30",
   "-3.20", "%%p0.00") and checks that each distinct storey level band, and any level below ±0.00, maps to a plan
   region; a level band with no plan becomes a HELD storey (reason MISSING_STOREY_PLAN) in the run report. Fixture
   (synthetic, not Alsenan): one DXF with an elevation printing -3.00 / ±0.00 / +3.60 and plans titled GF and 1F only
   -> one HELD storey at -3.00; the same with a "BASEMENT PLAN" frame -> none held; mm and m units; a mirrored
   elevation.
2. **Structural titles in STOREY_VOCAB (only if the vocabulary is ever used on structural sheets).** "FOUNDATION PLAN",
   "GROUND BEAMS PLAN" and "COLUMN & AXIS PLAN" are HELD_UNRECOGNISED, and "سقف الدور X" (the slab over storey X) is
   read as the storey X plan itself, one storey low for a slab. A structural reading needs its own classes
   (FOUNDATION, GROUND_BEAMS, COLUMN_LAYOUT, SLAB_OVER:<storey>) in a new vocabulary version, never a change to V1.
   Not urgent: route G does not use the vocabulary today.

## What was not done / uncertain

- The architectural and structural PDFs were not opened (37.5 MB and 2.2 MB; the architectural one is above the
  connector limit). The DXF is the drawing the engine reads; a basement sheet existing only in a PDF would not be
  read by the engine either, and the committed register says "NONE in any source".
- About 20 SHX-encoded Arabic texts on the GF plan are not decoded (a reader limit, not part of this task); the
  English labels, the level marks and the frame titles were all readable.
