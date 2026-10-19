# T-063 (with T-067): architectural sheet census, printed levels, pool, stairs, lift and domes (development villa)

Worker 1, 2026-10-19 12:25-12:50 UTC. Read-only: no engine, rule, test, fact file or quantity changed; nothing applied.
Development villa (Alsenan), not an accuracy claim. Values and sheet references only: no images, no client names, no
plot or address data. Every value is graded PRINTED (sheet, view, text), DERIVED (sum or difference of printed values,
named), VISUAL (seen on the image, no text), NOT_PRINTED, NOT_READ (sheet not available to this run) or a conflict
(DIFFERENT_FROM_DXF / DIFFERENT_FROM_STRUCTURAL / DIFFERENT_BETWEEN_REVISIONS). Rules: UP-KB-PREC-001 (precedence),
UP-HGT-001 (heights from the drawing by evidence), UP-QTY-STATUS-001 (held, never 0), UP-STAIR-009 (riser = rise /
counted risers; the typical range is a sanity check only); owner answers Q-14, Q-18, Q-19, Q-20, Q-21.

## Inputs (session scratchpad, never committed)

| Input (Drive "Alsenan chalet project") | Read | Note |
|---|---|---|
| Architectural PDF, six parts "..._P7757_Pages_01-02 ... 11-12" | 01-02, 05-06, 07-08, 11-12 (8 of 12 pages) | each page one 4672 x 6624 px JPEG at 400 dpi (A3, scanned / raster, no text layer): read visually at full resolution, pixel profiles for tread lines |
| same, Pages_03-04 (6 789 743 B) and Pages_09-10 (6 371 489 B) | **NOT_READ** | the Drive connector closed the connection on both ("message from the server was too large"), three tries; 6 225 932 B was the largest part that came through. The practical limit is about 6.2 MB per file (base64 about 8.3 M characters), not 10 MB |
| P7757_DXF_COMPRESSED.zip / P7757.dxf | yes | sha256 ab54dd55...31cc4 = SOURCE_MANIFEST; plans GF, 1F, 2F and SE, NW elevations; plans rendered with ezdxf 1.4.4, dimension measurements and end points read |
| architectural DWF (title ends 2026-05-06T113026.059.dwf) | text strings in drawing order | W2D stream; titles in stream order give the sheet set; created 26/04/2026 (an earlier plot than the PDF, see C-4) |
| ST7757 dxf.dxf | not re-read; cited from T-037 / T-035 / T-038 | sha256 9f9d1179...38079 |

## 1. Sheet list (12 PDF pages)

The DWF holds the whole set in one model plot; its titles in stream order are: SITE PLAN; GROUND / FIRST / SECOND FLOOR
AREA PLAN 1:100 (two "AREA PLAN" sheets); GROUND FLOOR PLAN 1:100; 1st.FLOOR PLAN 1:100; 2nd.FLOOR PLAN 1:100; SOUTH EAST,
SOUTH WEST, NORTH WEST, NORTH EAST ELEVATION; SECTION A-A; SECTION B-B; FENCE PLAN / FENCE ELEVATION / SECTION 1:100.
That is 13 drawings for 12 pages, so one page carries two of them.

| Page | Title (Arabic / English, as printed) | Kind | Status |
|---|---|---|---|
| 1 | مخطط مساحة للطابق الارضي / GROUND FLOOR AREA PLAN 1:200; مخطط مساحة للطابق الاول / FIRST FLOOR AREA PLAN 1:200 | area plan (2 views) | read: GF 319.99 m2 (68.00 %), 1F 211.44 - 3.24 = 208.20 m2 (44.24 %) |
| 2 | مخطط مساحة للطابق الثاني / SECOND FLOOR AREA PLAN 1:200 | area plan | read: 2F 8.10 x 6.80 = 55.08 m2 (11.70 %); TOTAL FLOORS AREA 583.27 m2 (123.95 %) |
| 3 | probably GROUND FLOOR PLAN 1:100 (and the SITE PLAN) | plan | NOT_READ (part 03-04); the same plan is in P7757.dxf frame GF |
| 4 | probably 1st.FLOOR PLAN 1:100 | plan | NOT_READ; the same plan is in P7757.dxf frame 1F |
| 5 | مسقط افقي للطابق الثاني / 2nd.FLOOR PLAN 1:100 | plan | read |
| 6 | واجهة جنوبية شرقية / SOUTH EAST ELEVATION 1:100 | elevation | read |
| 7 | واجهة غربية جنوبية / SOUTH WEST ELEVATION 1:100 | elevation | read (not in the DXF) |
| 8 | واجهة شمالية غربية / NORTH WEST ELEVATION 1:100 | elevation, cut through the court and the pool | read |
| 9 | probably NORTH EAST ELEVATION | elevation | NOT_READ; DWF text only |
| 10 | probably SECTION A-A | section (cuts the stair hall: the A-A line on the GF and 1F plans runs through the dog-leg stair) | NOT_READ; DWF text only |
| 11 | قطاع ب-ب / SECTION B-B 1:100 | section | read |
| 12 | مسقط افقي للسور / FENCE PLAN 1:100; سور واجهة / FENCE ELEVATION 1:100; قطاع / SECTION 1:100 | fence plan, elevation, section | read: fence 215 + 50 = 265 (section), plan runs 580, 250, 81, 195, 115, 195, 83 |

Pages 3, 4, 9, 10 are assigned from the DWF order ("probably"); not verified on the PDF.

## 2. Printed levels per floor (owner Q-14 format)

Ground ±0.00 everywhere. Sources: PDF B-B (p.11), NW (p.8), SE (p.6), SW (p.7) and 2F plan (p.5); P7757.dxf SE and NW
dimension measurements (end points converted to levels from ±0.00 at y = -805 246 mm); DWF text for A-A.

| Item | GF (main house) | 1F | 2F | Ground-floor annex (street side, B-B left) |
|---|---|---|---|---|
| FFL | **+1.00** PRINTED (plans, B-B, NW, A-A) | **+5.50** PRINTED (1F plan, B-B, NW, A-A) | **+9.70** PRINTED (2F plan "+9.70" in stair hall, on both roofs; B-B; A-A) | **+0.30** PRINTED (B-B, SE) |
| Level above | +5.50 | +9.70 | **+13.90** roof: PRINTED on A-A (DWF text only); DXF SE dimension 4200 from +9.70 to +13.90; PDF SE / B-B / NW chain "420" | +4.30 roof top PRINTED (B-B "+4.30", "400"; SE) |
| Floor-to-floor | **4.50** PRINTED ("450" on B-B and NW) | **4.20** PRINTED ("420" on B-B) | **4.20** PRINTED ("420" on SE, NW, B-B, A-A chains; DXF 4200) | **4.00** PRINTED ("400") |
| Parapet | +1.00 band: "100" ±0.00 to +1.00 | terrace parapet 0.50: +5.50 to +6.00 ("50", DXF 500) | roof parapet 0.50: +13.90 to +14.40 ("50", DXF 500); overall "1440" (DXF 14400) | 0.50: +4.30 to +4.80 ("480") |
| Structural slab thickness | NOT_PRINTED (T=10cm slab-on-grade note is structural, T-035) | **0.20 PRINTED once, kind not labelled**: NW elevation, vertical dimension "20" across the drawn floor band from +5.30 to +5.50 (DXF 200, layer 4, x -364 310), under the arched opening above the pool | NOT_PRINTED | NOT_PRINTED |
| Structural (slab top) level | NOT_PRINTED | NOT_PRINTED (the "20" band above gives +5.30 only if it is the slab, see C-5) | NOT_PRINTED | NOT_PRINTED |
| Soffit | NOT_PRINTED | NOT_PRINTED | NOT_PRINTED | NOT_PRINTED |
| Clear height | NOT_PRINTED | NOT_PRINTED | NOT_PRINTED | NOT_PRINTED |
| False ceiling | NOT_PRINTED (no ceiling line or note on any section read) | NOT_PRINTED | NOT_PRINTED | NOT_PRINTED |
| Plaster height | NOT_PRINTED: HOLD | NOT_PRINTED: HOLD | NOT_PRINTED: HOLD | NOT_PRINTED: HOLD |
| Paint height | NOT_PRINTED: HOLD | NOT_PRINTED: HOLD | NOT_PRINTED: HOLD | NOT_PRINTED: HOLD |

Other printed levels: court and external paving +0.15 (plans, B-B, NW, SE); GF entrance landing +0.30 (GF plan); roof over
the annex +4.30; 1F-roof drum / parapet top +11.00 (B-B "130" above +9.70: the line the two 1F-roof domes stand on);
1F-roof wavy parapet "110" above +9.70 (NW); B-B "535" = +0.15 to +5.50 (court to 1F FFL under the cantilever).

What this changes: T-035 recorded that the 2F has no level interval ("nothing printed above +9.70" on the plans). The
2F floor-to-floor 4.20 (+9.70 to +13.90) is printed on the elevations (PDF SE, NW; DXF 4200) and A-A. Under owner Q-14 a
floor-to-floor interval is still not a clear height, so plaster and paint stay held on every floor.

## 3. Pool

| # | Term | Value | Grade, where |
|---|---|---|---|
| P1 | Plan | D shape, 3.50 x 3.50 outer, walls 0.20 | PRINTED: GF plan (DXF) "350" / "350", "20"; label "swimming pool"; structural outline as T-037 |
| P2 | **Depth** | **1.15 m**, from the rim at +0.30 down to -0.85 | **PRINTED**: PDF p.8 NW elevation (the view cuts the court and the pool) "115"; DXF NW dimension measurement 1150, end points at +0.30 and -0.85; the next dimension up is "70" (+0.30 to +1.00). The lower end sits on the inner floor line (VISUAL): an inner (water) depth |
| P3 | Floor thickness | 0.40 | PRINTED on the structural pool detail (T-037) |
| P4 | Floor shape | conflict, see C-2 | architecture: flat floor at one depth in the NW cut (VISUAL); structural detail: a sloped floor with a step and both depths "AS PER ARCH" |
| P5 | Pump room, balance tank | none drawn | NOT drawn on any sheet read (2F, elevations, sections B-B, NW cut) nor in the DXF GF plan; owner Q-19: Alsenan has no pool pump room (checked by hand). Overflow channel: none drawn (owner: normal pool) |
| P6 | Pool step | not dimensioned | NOT_PRINTED |

Owner Q-19 sanity range 1.00 - 1.15 m: the printed 1.15 is inside it (a check, not the source).

## 4. Stairs (owner Q-20: read every stair detail first)

| Stair | What is printed | Grade |
|---|---|---|
| Entrance flight, court +0.15 to GF +1.00 | **5 risers** counted on PDF B-B (p.11), flight cut with its sloping waist drawn; rise 0.85 m from the two printed levels; width 2.80 (GF plan "280", DXF) | risers VISUAL (counted on a section); rise PRINTED; riser by UP-STAIR-009 = 0.85 / 5 = **0.170 m** (outside the 0.155 - 0.165 sanity range: flag, not an error); tread, waist and landing thickness NOT_PRINTED |
| Main dog-leg stair, GF +1.00 to 1F +5.50 (stair hall, both plans) | flight widths "120" / "120", well "10", flight plan run "330", landings "125" and "195" (2F plan; same set-out on the DXF GF and 1F plans); tread lines at 0.300 m spacing in the CAD | widths, run, landings PRINTED; tread 0.30 = CAD line spacing (not a printed dimension); **risers per flight NOT_PRINTED**: the plan shows 12 nosing lines over the 3.30 m run on 1F (DXF layer 5, -796 490 to -793 190) and 11 on the 2F image, solid and dashed (above / below the cut) mixed, so a riser count from the plan is not reliable. The section through this stair is A-A (page 10, NOT_READ) |
| Same stair, 1F +5.50 to 2F +9.70, and 2F to roof +13.90 | same set-out ("330", "120", "125", "195" on the 2F plan, p.5) | rise 4.20 per storey PRINTED; risers NOT_PRINTED (A-A not read) |
| Curved stair in the GF reception (GF +1.00 to 1F, void 5.87 x 4.00 above) | width "120", "157" on the GF plan (DXF) | risers, waist, landings NOT_PRINTED on the sheets read |
| Waist slab, landing thickness, stair beams | none | NOT_PRINTED on every sheet read (B-B draws the entrance flight waist without a dimension) |

Plan tread lines of the main dog-leg in P7757.dxf (each nosing drawn as a pair of 1.15 m lines 50 mm apart, one solid
layer 5 and one dashed layer 2, pitch 0.300 m): GF plan, flight next to the outer wall 10 nosings, inner flight 11 (21);
1F plan 12 and 11 (23). The plan gives MORE nosings on the storey with the SMALLER rise (1F 4.20 m) than on GF (4.50 m),
so the drawn treads are a set-out symbol and do not give the riser count: risers per flight stay NOT_PRINTED until
SECTION A-A is read. (Lesson for the engine: counting plan tread lines is not a riser count; UP-STAIR-009 needs counted
risers from a section or a schedule.)

So the owner's Q-20 order applies: steps of the entrance flight can follow UP-STAIR-009 (5 risers, 0.170 m) once its tread
is read; every other riser count, waist and landing stays HELD until section A-A is read.

## 5. Lift (correction to T-038)

A **square shaft, 1.80 x 1.80 inside, walls 0.20** ("180", "180", "20"), crossed by a diagonal on the 1F and 2F plans, is drawn next to the
stair hall on the GF, 1F and 2F plans (DXF render; PDF p.5 2F plan). It carries no label (no "LIFT", "مصعد" or "PIT"),
so the T-038 text search could not find it. Wall centreline perimeter 4 x 2.00 = **8.00 m**: the same 8.0 m the
freelancer uses for his "RC lift walls 20 cm, 8.0 x 0.20 x 1.50 = 2.40 m3". The 1.50 m (pit depth) is NOT_PRINTED on
any sheet read, and no section through the shaft was read. Verdict proposal for the 2.40 m3: stays **UNRESOLVED**, now
traceable to a drawn shaft (shaft VISUAL + CAD dimensions; height and wall material not printed).

## 6. Domes (owner Q-18: held and always visible)

| Dome | Architectural sheets | Structural set (T-037) |
|---|---|---|
| Two domes on the 1F roof (+9.70), plan circles "R221" | 2F plan p.5: two circles R221 on the roof; B-B: both drawn on a 1.30 m drum (+9.70 to +11.00); SE: top at +12.849 (DXF 1928.5 from +10.92 and 1550.6 to +14.40; PDF "193", "155"); NW: "172" above the parapet. Rise from +11.00 to +12.849 = 1.849 m DERIVED across two sheets (B-B, SE) | span 442, rise 190, shell 10 (DETAIL OF DOME, N.I.S) on two domes |
| **A third dome on top of the 2F block** | SE elevation: span "441" on the parapet line +14.40, "215" above it (DXF 4410 and 2149.4, top +16.549); NW elevation "215" (DXF 2149); B-B draws it behind the cut; 2F plan p.5: dashed circle (projection above) over the maid room | **not in the structural set**: the slab over 2F is flat there (T-037 D6) |

No architectural sheet read dimensions a dome to its inner or outer shell. Q-18 stays as answered: every dome line HELD
(DOME_SIZE_BASIS_NOT_CONFIRMED), now also the count (C-1).

## 7. Conflict register (recorded, not settled; MISSION.md: a drawing never settles a conflict between two drawings)

| Id | Conflict | Sources |
|---|---|---|
| C-1 | Domes: architecture draws 3 (2 on the 1F roof + 1 on the 2F roof, span 4.41, visible rise 2.15); structure details 2 (442 / 190 / 10) and a flat slab over 2F | PDF p.5, 6, 8, 11 + DXF SE/NW vs ST7757.dxf (T-037). The freelancer counts 3 x 22.6 m2 x 0.10 = 6.78 m3 |
| C-2 | Pool floor: architecture one depth 1.15 on a flat floor in the NW cut; structural detail a sloped floor with a step, both depths "AS PER ARCH" | PDF p.8 + DXF NW vs ST7757.dxf pool detail |
| C-3 | 1F-roof dome rise: 1.849 (architecture, derived +11.00 to +12.849) vs 1.90 (structural detail) | B-B + SE vs DETAIL OF DOME |
| C-4 | Revisions: the DWF (26/04/2026) prints the overall height "1390" on every elevation and section (its own chain 100 + 870 + 420 + 50 = 1440) and none of 115 (pool), 441 / 215 / 193 (domes); the PDF (plotted 06/05/2026) and P7757.dxf print 1440 and all of them | DIFFERENT_BETWEEN_REVISIONS: the PDF and the DXF agree with each other (DXF = PDF revision); the DWF is the older plot and should not be used for heights |
| C-5 | The "20" at +5.30 to +5.50 on the NW elevation: slab thickness (then 0.20, not the owner's 0.16 default) or slab + finishes? Not labelled | PDF p.8, DXF NW |
| C-6 | Entrance riser 0.170 m (0.85 / 5) is outside the 0.155 - 0.165 sanity range of UP-STAIR-009 | B-B levels and count |

## 8. What each value could release (engine vs freelancer, development reference)

Engine figures are the last measured ones (T-037 run on 56820cb; the verifier's 12:12 re-measure on 8774071 found the
concrete lines identical). This run changed no engine line.

| Line | Engine now | Freelancer | Effect of this census |
|---|---|---|---|
| Pool concrete, m3 | 3.495 (half outline, 0.25 / 1.6 conventions) | 12.348 (incl. pump room 3.480 the owner says does not exist, step 0.228) | Printed basis now: floor 10.936 m2 x 0.40 = 4.374 (T-037) + walls 2.358 m2 x 1.15 = **2.712** (wall height = inner depth, the floor term already covers the plan under the walls) = **7.086 m3** if C-2 is decided "flat floor at 1.15" (owner question Q-26). Against the freelancer's pool without the pump room (8.868): -1.782 m3 (-20.1 %); his wall height 1.8 is not printed. Not applied |
| Stairs concrete, m3 | 4.635 (conventions) | 15.052 | Entrance flight: 5 risers, 0.170 m riser printed by levels; everything else HELD until A-A is read |
| Domes, m3 | 7.372 (conventions, 2 domes) | 6.780 (3 domes) | stays HELD (Q-18); count conflict C-1 asked (Q-27) |
| Lift walls, m3 | none | 2.400 | shaft found (8.00 m centreline matches); pit depth not printed: UNRESOLVED |
| Internal plaster, m2 | HELD | 1 151.14 | still HELD: no clear height, soffit, false ceiling or build-up printed (2F interval 4.20 is now known, not a wall height) |
| Internal paint, m2 | HELD | 1 191.13 | still HELD (same) |

## 9. Owner questions raised (OWNER_QUESTIONS.md Q-26, Q-27)

Q-26 pool floor flat at 1.15 or sloped (C-2); Q-27 is there a third dome on the 2F roof (C-1). C-5 (is the "20" at the
1F floor band the slab thickness) and C-6 are left to the lead: they block no quantity today (plaster and paint are held
for missing clear heights anyway; slab concrete comes from the structural route).

## 10. For the lead

1. Pages 03-04 (6.79 MB) and 09-10 (6.37 MB) do not pass the Drive connector (closed at about 6.2 MB); the owner can
   split them into single pages or zip them. Page 10 (probably SECTION A-A) is the only stair section: it decides the
   riser counts, waist and landings of the main stair (Q-20).
2. Correct T-038's "no lift drawn": the shaft is drawn, unlabelled (section 5). A general reader rule follows: an
   unlabelled square shaft with a diagonal that repeats in plan on every storey is a lift or service shaft candidate
   (held, never silent) - a gate-1 silent-omission check.
3. Proposed task: bind elevation and section dimension chains to levels (vertical dimension end points, as read here
   from P7757.dxf) so the 2F interval +9.70 to +13.90, the pool depth 1150 and the dome springing are read by the engine
   from CAD (T-013 section binding / T-049 detail dimensions), each value still subject to the owner answers above.
