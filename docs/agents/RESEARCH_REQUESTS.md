# Research requests (Lead writes; the research scout answers in RESEARCH_LOG.md "Answer to R-nn")

At most 3 open. Each: the problem in one sentence, the measured gap, what to look for, which task it unblocks.

## Open

(none; the Lead adds new requests here)

## Answered

### R-09 Reading footing reinforcement from CAD schedule tables (lead 2026-10-21 00:15)
Problem: rebar is the largest money at risk and is counted today from per-metre or merged-cell readings, never by bar
population; the footing schedule on the structural DXF is a drawn table (lines + MTEXT / TEXT cells, some merged) with
two notations, count ('n T d') and spacing ('T d @ s'). Gap: rebar earlier estimate 26.24 vs freelancer 44.19 t
(-40.6 %); route defects B3 (per-metre bars used as an absolute count) and B4 (a footing with zero rebar from a merged
cell, silent). Look for: robust ways to rebuild a table grid from DXF lines and text (cell detection, merged cells,
rotated tables, text that overflows a cell) with permissive code; how bar-bending-schedule tools and BS 8666 / ACI 315
practice turn 'T d @ s' into a bar count (end bars, first bar at cover or at s/2) and which convention a Kuwait drawing
implies when its notes are silent; test cases (tables with merged and empty cells). Unblocks T-136 (footing steel), then
T-009 (columns, beams).
Answered (scout 2026-10-23 17:50 UTC): RESEARCH_LOG.md "2026-10-23 (scout run 17:50 UTC)", "Answer to R-09". Supplement (scout one-off 2026-10-23 17:55 UTC, owner fire): same file, "Answer to R-09 (supplement)".

### R-10 Laps, development lengths and stock-length splicing in a bar schedule when the drawing gives only a rule (lead 2026-10-21 04:10)
Problem: the ground-beam / strap steel ledger was sent back because the structural general notes print only "development
length >= 70 d (tension) / 40 d (compression)" and the drawing does not say which bar is in which zone; continuous bars
run up to 18.57 m against 12 m stock. Gap: 1,479.86 kg net confirmed by the checker, but the procurement weight (laps at
splices, development at ends) is missing on every run over 12 m, and route G once carried 4,101.77 kg provisional
ground-beam steel with practice anchorage. Look for: how BS 8666 / ACI 315 / bar-bending-schedule tools compute laps
and splice counts for runs longer than stock (splice positions, staggering, minimum lap when the zone is unknown),
how estimators report a lap RANGE when tension / compression zones are not printed, permissive code that splits runs
into stock lengths with laps, and test cases. Unblocks T-138 r2 (ground beams and straps), T-141 (span splitter) and the
footing / slab steel lines in V3.0.2.
Answered (scout 2026-10-23 17:50 UTC): RESEARCH_LOG.md "2026-10-23 (scout run 17:50 UTC)", "Answer to R-10". Supplement (scout one-off 2026-10-23 17:55 UTC, owner fire): same file, "Answer to R-10 (supplement)".

### R-12 What "n ø d / m" means on Gulf / Arab-region structural foundation schedules (lead 2026-10-22 08:20)
Problem: footing schedules print reinforcement as "n ø d/m" (for example "9 ø 14/m"); the team must establish from
evidence whether it means a bar density, a maximum spacing s = 1/n, or a count in a 1 m module, before any rounding
(owner directive 2026-10-22, ENGINEERING_REASONING_STANDARD section 3: "a notation's meaning before its arithmetic").
Gap: about 6.7 .. 7.2 t of footing, column-link, slab and stair steel is HELD on this one meaning (footings 2,742.51 ..
2,836.40 kg alone). Look for: published detailing manuals, code commentaries or ministry / consultant standard notes used
in Kuwait and the Gulf (or Egyptian / Saudi practice they follow) that define the "/m" notation on schedules, and how
bar-bending-schedule practice counts bars from it (end bars, first bar at cover or at s/2, rounding up). Cite only pages
actually read; an engineering reference is evidence level 4, below the project's own schedule, sections and notes. Feeds
T-171 (footings only; no extension to columns, slabs or stairs without their own evidence).
NARROWED (lead 2026-10-22 20:20): for FOOTINGS the team settled the meaning by investigation (T-171 MERGED 701d227: '/m'
= maximum c/c spacing, N = ceil(L_eff / s) + 1). Still open, and the reason R-12 stays open: whether the same notation on
SLAB and STAIR plans means the same thing (the V3.0.5 candidate holds slab steel 4,643.77 .. 6,832.33 kg and stair steel
1,039.16 .. 1,378.63 kg on counts A..B for exactly this reason). Evidence for slabs / stairs only; footings need nothing more.
Answered (scout 2026-10-23 17:50 UTC): RESEARCH_LOG.md "2026-10-23 (scout run 17:50 UTC)", "Answer to R-12". Supplement (scout one-off 2026-10-23 17:55 UTC, owner fire): same file, "Answer to R-12 (supplement)".


### R-11 Named measurement-standard clauses for (a) opening deductions in blockwork and (b) the measured length of strap / oblique ground beams (lead 2026-10-21 08:20) — CLOSED (lead 2026-10-22 08:20): (a) and (b) answered by the owner himself in his directive of 2026-10-22 (Q-73: full openings deducted subject to physical scope, T-175; Q-74: actual beam-axis length, T-174); (c) settled by the owner-notes correction 07:10 (corners are a separate m.l line paid at half, never m2; T-172); (d) moot for the engine (Q-73 deducts full openings); the freelancer's half deduction stays a comparison note in T-162. No scout work needed.
Problem: two owner questions (Q-73, Q-74) carry the Lead's recommendation as "practice, not a code clause"; the owner
decides better with the exact clause of the standards Gulf QS practice uses. Gap: block net area HELD on every wall
(gross 955.63 m2 measured, freelancer 1,094.50 m2, -12.7 %); two oblique straps 2.293 / 3.258 m (axis face to face) vs
1.829 / 2.838 m (projected), both HELD. Look for: NRM2 (work sections for masonry and in-situ concrete), POMI and
SMM7 / CESMM4 text on (a) which voids are deducted from masonry and the size threshold, and whether lintels / bond
beams are measured separately; (b) how beams between foundations (strap / tie / ground beams) are measured, between
which faces, and whether the length is along the axis; plus any Kuwait MPW or Gulf BOQ preamble wording that adopts
one of them. Cite the clause number only from a page actually read. Unblocks the owner's answers to Q-73 / Q-74 and then
T-108 (block counts) and the strap lines of T-141.
ADDED (lead 2026-10-22 00:20, owner notes on exterior Sigma 2026-10-21, item 2 "look for it then I can decide, flag it"):
(c) external plaster CORNERS / arrises / rounded edges: is there a published convention that measures them in linear metres
and converts "2 m.l = 1 m2" (the freelancer adds 1,297.35 m.l as 648.68 m2 to 1,469.97 m2 net), or are arrises an
enumerated / linear labour item only, never added to the m2 (NRM2 / POMI / SMM7 internal and external angles, beads and
arrises; Kuwait MPW or Gulf BOQ preamble wording); and (d) the freelancer's practice of deducting openings at HALF their
area in external plaster: which standard, if any, states it. Owner decides; the team only reports the sources. Unblocks T-162.


### R-06 Arabic and English finishing notes and room tags on SCANNED villa plans (lead 2026-10-20 00:30)
Problem: the Alsenan architectural PDF sheets are raster scans, and the finishing facts (tile sizes, floor finish per
room, door heights, false-ceiling notes) are printed there in Arabic and English, so today only a person can read them.
Gap: 23 of 29 window heights and all but one door height held; tile size per room not known (tile counts HELD); plaster
1151.14 / paint 1191.13 m2 held partly for want of printed ceiling notes. The image has Tesseract with English only (no
Arabic data) and agents may not install packages. Look for: permissive OCR for Arabic + English mixed technical text on
200-300 dpi scans (Tesseract ara data licence and accuracy, PaddleOCR Arabic models, others), published accuracy on
architectural or engineering drawings, how to find note boxes and room tags on a scan before OCR, and a check that holds
a misread note (e.g. two engines must agree; a size must match a known tile format printed elsewhere on the set).
Unblocks T-091 (as a check of the hand census), T-092, T-003.
Answered (scout 2026-10-20 23:55 UTC): RESEARCH_LOG.md "2026-10-20 (scout run 23:55 UTC)", "Answer to R-06".

### R-07 Proving that a strip layout covers every piece of a membrane outline (lead 2026-10-20 06:20)
Problem: the engine lays 1.00 m membrane strips with 0.10 m laps over a room or roof outline widened by its 0.20 m
upturn, and its rule for where a strip goes missed the upturn of an outline step whose edge runs the same way as the
strips. Gap: Alsenan second-floor roof 0.84 m2 uncovered (4.20 x 0.20 m), released 17 rolls vs 18 by hand; dome-opening
upturn about 0.31 m2 left to patches; 0.003 - 0.010 m2 in four wet rooms. Look for: exact coverage checks of a polygon by
axis-aligned strips (polygon difference with exact or robust arithmetic, e.g. shapely 2 set operations with a stated grid
size), band / trapezoid decomposition of rectilinear and curved outlines so every residual piece is assigned to a strip
or named as a patch, how roofing and tanking take-off software or practitioners lay out sheet membranes round steps,
openings and splayed corners, and test-case generators for such outlines. Unblocks T-096 (step upturn fix), T-098.
Answered (scout 2026-10-20 23:55 UTC): RESEARCH_LOG.md "2026-10-20 (scout run 23:55 UTC)", "Answer to R-07".

### R-08 Masonry wall centreline metres from double-line CAD walls (lead 2026-10-20 08:20)
Problem: blockwork is billed on the wall CENTRELINE per thickness including corners, T-junctions and wall ends (owner rule
UP-WALL-GEOM-001), but the engine's wall run follows a face band, which leaves corners and ends out. Gap: synthetic villa
SV-A 44.4 m face run vs 46.2 m hand centreline (-3.9 %); Alsenan blockwork never measured, an old estimate about 140 m
short (-36.5 %). Look for: robust ways to turn pairs of parallel wall lines (and hatched wall polygons) in DXF into a
centreline graph with junctions (medial axis / straight skeleton of the wall polygon, wall-pair matching with thickness
classes, open-source floor-plan vectorisation code that outputs wall centrelines), how they treat columns inside a wall
line, curved walls, walls meeting at odd angles and gaps at openings, and how QS take-off tools report blockwork per
thickness; licence and maturity for each. Unblocks T-027 (engine piece) and checks T-103 (hand metres).
Answered (scout 2026-10-20 23:55 UTC): RESEARCH_LOG.md "2026-10-20 (scout run 23:55 UTC)", "Answer to R-08".

### R-01 Floor and ceiling heights from Kuwait villa section drawings (lead 2026-10-19)
Problem: plaster and paint cannot be released without per-floor wall heights, and the engine has no bound section
heights for real plans. Gap (Alsenan, T-001b): plaster 1151.14 m2 and paint 1191.13 m2 reference, 0 compared (29 and 13
lines HELD). Look for: methods to read level marks (+3.50, F.F.L., S.S.L., T.O.S.) and dimension chains from DXF section
and elevation sheets and bind them to plan storeys; level-symbol detection; open-source code (permissive licence) for
section parsing; how QS practice derives plaster height (slab soffit vs false ceiling). Unblocks T-035, T-013, T-031.
Update (lead 2026-10-19 10:15, owner answer Q-14): the owner set the structural slab at 0.16 m unless a drawing or detail
says otherwise and asked that each floor report ground level, FFL, structural slab top, soffit, floor-to-floor, clear
height, false-ceiling height, plaster height and paint height separately, nothing subtracted by assumption. The
architectural sections are now readable as six PDF parts (vector, read visually). Sharpest question: how to tell these
level kinds apart on Gulf section and elevation sheets (symbols, prefixes such as F.F.L., S.S.L., T.O.S., Arabic
equivalents) and how to bind them to plan storeys. Unblocks T-063, T-013, T-046.
Update (lead 2026-10-19 18:15, from T-078 / T-013): section binding now reads the Alsenan floor-to-floor heights (4.50 /
4.20 m); the gap moved to OPENING heights: only 4 of 29 windows have a printed height on the DXF elevations (13.89 vs
14.35 m2 measured; 15 windows on facades the DXF never draws, doors none). Look for: reading vertical dimension chains and
sill / head marks from vector PDF elevation sheets (pdfplumber / PyMuPDF word + line geometry, chain detection, binding a
chain to a plan opening by width and position), and how Gulf QS practice takes door heights when no schedule exists (only
as evidence for an owner question, never as a default). Unblocks T-082, T-081.

Update (lead 2026-10-19 22:20, from T-082 / verifier): the vector-PDF opening-height reader is merged, but every Alsenan
architectural PDF sheet is a raster scan (sheet 09: one 4672 x 6624 image, 0 words, 0 vectors), so windows stay 4 of 29
measured (13.89 vs 14.35 m2) and doors 0 of 12.0 m2. Floor-to-floor and room heights are now settled by the owner's rule.
Sharpest question now: reading dimension numbers, level marks (+1.00, +5.50) and their dimension lines from SCANNED
elevation and section sheets: OCR of small rotated digits (Tesseract settings, permissive alternatives), line and tick
detection on scans (OpenCV Hough, permissive), binding a scanned chain to a plan opening by position, and how reliable each
is (published error rates). Never fabricate a value: unread numbers stay HELD. Unblocks T-083 (as a check), T-003.
Answered (scout 2026-10-20 00:00 UTC): RESEARCH_LOG.md "2026-10-20 (scout run 00:00 UTC)", "Answer to R-01".

### R-02 Structural element populations from schedules and tables in DXF (lead 2026-10-19)
Problem: column and ground-beam concrete is held because element sizes and heights are not tied to every instance.
Gap (Alsenan, T-001b): columns 118 of 118 lines held (freelancer 39.75 m3), ground beams 61 of 84 held (freelancer
75.09 m3). Look for: reading column / beam schedules drawn as DXF text grids (cell detection, row / column binding),
linking a schedule mark to every plan instance, neck-column height from foundation sections; papers or tools with
permissive licences. Unblocks T-036 follow-ups, T-009.
Update (lead 2026-10-19 02:20, from T-036): 167 of the 205 held concrete lines release only when storey heights, neck
top level, founding depth, typical ground-beam sections by span band (printed as titles like `< 2.5 m (30x30)`) and the
blinding thickness come from a person-typed profile; so the sharpest question is how to read those printed values (level
marks, section titles, general notes) from structural DXF text reliably, in English and Arabic, cm and m. Unblocks
T-045, T-046, T-044.
Update (lead 2026-10-19 04:10, from T-044 / T-033): on two villas Arabic notes are drawn in SHX fonts and stored as Latin
keyboard codes (a printed founding depth was missed this way). Look for: how Arabic SHX fonts encode text in DXF, published
keyboard-to-Arabic maps and their variants per font, letter joining, open-source decoders (permissive licence), how to
detect an Arabic SHX style without a project's font names. Unblocks T-047, T-044, T-049.
Update (lead 2026-10-19 08:15, from T-004a): a second Arabic SHX family is unread: 47 room labels on the Alsenan
architectural plans (and 72 labels counted by T-044) use x-arab1b-style fonts whose codes match none of the Arabic (101)
keyboard maps T-047 uses. Look for: published code tables for the common Gulf / Middle East Arabic SHX fonts (ARABIC,
X-ARAB, XARAB1B, ARB, "Arial Arabic SHX" families), glyph-number to Unicode tables, and how to read an SHX font file's
glyph shapes to confirm a mapping (so a code is mapped only from a source, never inferred). Unblocks T-047 follow-ups,
T-053, T-062.
Answered (scout 2026-10-20 00:00 UTC): RESEARCH_LOG.md "2026-10-20 (scout run 00:00 UTC)", "Answer to R-02".

### R-05 Footings and other members drawn as block inserts or open outlines, and membrane rolls with offcuts reused (lead 2026-10-19 14:30)
Problem (a): the engine recognises a footing only when it is a closed outline on the expected layer; footings drawn as
block inserts on another layer, mirrored inserts or open outlines are not seen as members. Gap (Alsenan, T-065): 8.05 m
of the foundation band (0.966 m3 at 0.20 x 0.60) is measured where it actually runs inside such footings; the band
inside members reads 18.30 m in the new ledger against 21.45 m by hand. Look for: robust member detection in structural
DXF from INSERT geometry (exploded virtual entities, mirrored / negative-scale inserts), closing open outlines with
evidence (tolerances, gap closure that is reported, never silent), matching a plan outline to a schedule mark; permissive
open-source code. Unblocks T-073.
Problem (b): the owner wants the rolls to buy for the whole project, reusing offcuts across rooms (1.00 x 10.00 m roll,
0.10 m laps, whole strips with cut edges). Look for: one-dimensional cutting-stock / bin-packing methods that give an
exact or provably near-optimal roll count for strip lists, with a printable cutting plan; how sheet-membrane installers
plan rolls in practice; permissive open-source solvers that need no network. Unblocks T-072.
Answered (scout 2026-10-20 00:00 UTC): RESEARCH_LOG.md "2026-10-20 (scout run 00:00 UTC)", "Answer to R-05".


## Withdrawn

### R-04 Comparing an old building (PDF only) with its new design (CAD) for a renovation BOQ (lead 2026-10-19 12:20)
Problem: the owner's sealed test villa is a renovation: the old building exists only as a PDF, the new design as DWG / DXF
and PDF, and the engine must say for every wall and space whether it is retained, demolished or new before it can measure
flooring (wet / dry), plaster, paint and inner / outer blocks. Gap: the engine has no old-vs-new comparison and no plan
reader yet (0 of these classes produced today); synthetic old / new pairs are being built (T-068). Look for: registering a
scanned or vector PDF plan to a CAD plan (scale from printed dimensions, rotation, translation; ICP or feature matching on
wall lines), wall-level change detection between two plan versions, demolition / new-wall drawing conventions (hatch,
dashed lines, Arabic and English notes such as "هدم" / "يزال" / "جديد" / "TO BE DEMOLISHED"), QS practice for measuring
renovation items in the Gulf, open-source code with a permissive licence. Unblocks T-068 follow-ups, T-003, and the
measuring tasks that follow owner Q-23.
Withdrawn (lead 2026-10-19 14:30): owner Q-23 answer 14:15: no renovation test villa will be sent; renovation preparation dropped.

### R-03 Storey / sheet detection in multi-sheet villa DXF (lead 2026-10-19)
Problem: a storey whose title the engine does not recognise is not measured. Gap: Alsenan run found GF / 1F / 2F only
while the reference includes a basement; T-029 still holds PENTHOUSE, LEVEL nn, 12th-floor Arabic titles. Look for:
title-block and frame detection in model-space sheets, bilingual (Arabic / English) storey naming conventions in Gulf
drawings, level-number conventions (LEVEL 00 = ground?), tools that split one DXF into sheets. Unblocks T-038, T-039.
Withdrawn (lead 2026-10-19 12:20): no longer the biggest gap: Alsenan has no basement (T-038, verified from the drawings) and storey titles beyond GF / 1F / 2F are merged (980e489); slot given to R-04.
