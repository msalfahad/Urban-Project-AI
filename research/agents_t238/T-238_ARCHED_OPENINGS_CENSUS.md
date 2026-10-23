# T-238: arched and banded openings re-read on their opening line (development villa; rule for every villa)

Worker 2, 2026-10-23 21:43 - 23:00 UTC, run session_01V6aB1v7TiYW7cfaZhPSBgA. Lane A, gate 1 FIX, backlog-permitted.
Research files only (`research/agents_t238/*`, `tests/t238_arch_census/*`); no engine file, rule file, registry, frozen
method, merged ledger or released quantity changed. The merged T-150 / T-175 / T-201 / T-128 files are read, never
edited: every correction is a row of `DELTA_T238.csv` (old -> new -> cause) for lane I (T-211 / T-232 / T-237).
`alsenan_t238.py --check` reproduces `CENSUS_T238.csv`, `DELTA_T238.csv`, `summary.json` from repository files.
ERS: read; s.2 steps 1-4, s.3 (a notation's meaning before its arithmetic; one element, several trades), s.4, s.7 row
below. Development villa, not an accuracy claim. Drawings cited by Drive title and DXF handle; no coordinate, image or
client name committed.

## 1. Result in engineering terms

| Opening | Was (merged) | Now (opening line) | Trades moved | Status |
|---|---|---|---|---|
| W15 (1F, NW) | 1.55 x 3.10 = 4.805 m2 in every ledger (band crown) | outline 1.5523 x 2.1609 + arch 1.0088 = **4.363 m2**; window Q-32 A 1.55 x 3.00 = **4.650** | window -0.155; plaster / paint int -0.442, ext -0.442 (deduction); reveal 9.300 -> 8.398 m; block already 4.363 (T-227) | outline VERIFIED (Checker 21:11, T-227); rest DRAWING-CONFIRMED |
| W16 (1F, NW, twin) | 4.805 (T-201) | same as W15 | as W15; T-128 room 1F-13: HELD -> 4.363 | as W15 |
| W26 (2F, SE) | 1.20 x 1.70 = 2.040 for masonry, plaster, paint | outline 1.20 x 1.05 + arch 0.6147 = **1.875 m2**; window Q-32 A 1.20 x 1.70 = 2.040 (unchanged) | block -0.165 (2F-W07, gross HELD); plaster / paint int -0.165, ext -0.165; reveal 5.800 -> 5.271 m | DRAWING-CONFIRMED |
| W17 (1F, NW, curved on plan) | 3.29 x 3.50 = 11.515 window; T-128 room 1F-11 11.008 / 11.501 | 3.50 is the **archivolt** crown; opening crown 3.000 .. 3.0505 | window -> **HELD 9.870 .. 11.515** (owner confirmation via Lead, s.9); plaster / paint deduction -> HELD, upper bound 10.024 | HELD |
| A-GF-01 (GF annex arch) | HELD | drawn segmental arch: 1.00 x 2.20 + 0.2131 = **2.413 m2 candidate** (never 1.00 x 2.50) | none now (stays HELD) | SOURCE-SUPPORTED candidate |
| A-1F-01 (1F arch) | HELD | not drawn on any view read | none | HELD |
| 52 other census openings | | rectangular, outline = jamb lines (= plan width), no arc, no outer chain | none | as merged |

Windows m2 (WINDOW.ALUMINIUM), T-150's 8 established windows: **56.771 -> 45.101 m2 on 7 + W17 HELD 9.870 .. 11.515**.
Freelancer on the same 7: 45.481 -> engine -0.380 m2 (-0.84 %; was +3.35 % on 8). T-201's 18: 22.730 -> 22.575 (W16).
Masonry: W26 deduction -0.165 m2 on a HELD gross (no established net moves); W15 / W16 applied by T-227 (1F-W00 net
12.863 unchanged). Plaster / paint deductions on established faces: -1.049 m2 per side (W15 0.442 + W16 0.442 + W26
0.165), i.e. the nets RISE by up to 1.049 m2 internal and 1.049 m2 external once lane I applies the delta. Reveals
-0.902 / -0.902 / -0.529 m. Sigma arrises: arched heads are at chord in T-162; the arch is longer by 0.972 / 0.972 /
0.771 m (information row). Nothing released moves.

## 2. The physical element (ERS s.2 step 1)

An arched opening is a hole in the masonry with straight jambs up to the springing and an arch above; the window frame
fills it. On this set three things are drawn around the hole and are NOT the hole: (a) a surround band on the wall face
(W15 / W16 0.10, W26 0.05) drawn as a parallel outer chain that runs down both jambs; (b) an archivolt on W17 (0.10 at the
jambs, 0.45 at the crown); (c) a recessed panel over the whole SE stair-window column. Masonry, plaster and paint are
physically built up to the hole's outline, so they deduct the outline (jamb rectangle + arch segment). The aluminium line
follows the owner's Q-32 A (enclosing rectangle on the opening line). A reveal / arris follows the arch, not a straight
head.

## 3. Own reads this run (Drive "Alsenan chalet project", read-only; decoded into .work/private only)

Views: P7757_DXF_COMPRESSED.zip (P7757.dxf, sha256 ab54dd55..: the SE and NW elevation frames; every LINE / ARC of
layers 1, W, 5, D; chains of >= 6 short oblique segments detected; datum = each frame's +-0.00 / +1.00 DIMENSION, 1 unit
= 1 mm) and the architectural .dwf (DWF 6 vector, read with research/agents_t201/w2d_reader.py: SW and NE elevations,
sections A-A and B-B rendered, their arcs listed).

1. **W15 / W16 (NW).** Opening line = layer-1 jambs 2889 / 288A (W15), 2566 / 256A (W16), +5.50 .. +7.661, and the arch
   chain springing from their tops (46 / 49 segments, crown +8.50 = the end of DIMENSION 3000, printed 300). Walked by
   shortest connected path (horizontal and below-springing lines excluded): width 1.5523, springing 2.1609, segment
   1.0088, arch length 2.5243, outline **4.3632 m2** (T-227 / Checker 4.3629: 0.0003 m2). The chain 0.10 outside
   (DIMENSIONs 100 each side, 101 above the crown; printed 10) runs down both jambs = the band. The printed 300 + 10 is
   opening + band, so 3.10 is the band crown (the T-150 / T-175 / T-201 / T-128 head).
2. **W26 (SE).** The stair-window column is one 1.200 jamb pair (2211 / 2229) from +0.15 to +11.85 carrying W01, W13, W26
   (T-194). W26: sill line 2319 at +10.80, springing +11.85 (jamb tops), 28-segment arch chain 1C67 .. 222E, apex +12.50
   = the end of DIMENSION 2AB8 1700 (printed 170). The next line 49.5 above (DIMENSION 2AC6) is a 1.300 chain on the
   column's outer edge lines = a 0.05 band. Outline: 1.20 x 1.05 + segment **0.6147** = **1.8747 m2**; arch 1.9709 m.
   The merged ledgers read 1.70 correctly as the crown (the window line is right) but deducted 1.20 x 1.70 from masonry
   and finishes. (The Q-32 question text read "170 to where the arch starts and 88 above it": the 876.4 dimension runs
   from W26's band to the stair-column panel arch, a facade relief.)
3. **W17 (NW, curved on plan, host GLAZED).** The vertical chain 4300 / 200 / 3050.5 / 454.3: the 3050.5 ends on the
   outer line of the opening arch pair (inner line +8.500, outer +8.5505: a 0.05 edge as on W26); the 454.3 runs to the
   outer line of an archivolt pair (+8.954 / +9.004) that stands 0.40 .. 0.45 above the opening crown and ~0.10 outside
   the jambs; the window frame lines (layer W 2A4D / 2A50) stop below the inner arch. So "305 + 45" = opening + archivolt,
   not springing + rise; the springing is ~1.4 m above +5.50 (the arch is tall). The census 3.50 (T-150, T-128, Q-32 / Q-39
   question texts) is the archivolt crown.
4. **A-GF-01 (SE annex section, wall beyond the cut).** One ARC 2422 (layer 5) r 0.5673, 28.2 .. 151.8 deg: chord 1.000,
   rise 0.2993, springing +2.50 on jamb lines 2420 / 2421 drawn from +0.30 (2.20 above the floor), crown +2.799. No
   dimension is printed (N09): the outline 2.4131 m2 is a candidate for the Checker, the opening stays HELD (D-45).
5. **Other views.** SW and NE elevations: every opening is a plain rectangle; T-201 bound each outline width to the plan
   width (0.599 .. 1.552 m), so no band was read as an opening; no arc on any opening. Section A-A draws W26 beyond (same
   arch). Section B-B: domes, rectangular doors, and ONE GF arc in a wall beyond the cut (chord 1.255, rise 0.269, from
   a wall line to the head of a drawn door frame, no jamb pair, no dimension): **not bound** to any census opening
   (`F-BB-GF-ARCH`, UNKNOWN); T-201 had reported "an arched head over one GF doorway" on B-B to the Lead: this is it, and
   it is in the DWF too. A binding by the B-B cut line (looking north, offset solved from the cut walls) is AMBIGUOUS: two offsets 1.85 m apart (6 of 30 wall lines within 0.01 m; 9 of 30 within 0.06 m, the latter fitting the W02 cut) put it on the front wall of the wash / basin space (P-GF-01 0.90, head HELD; the 45-degree W.C. doors) or on the wall east of it; no census opening is 1.255 wide. SE: the porch's stone voussoir arch (quarter arch r 1.90, half drawn) is the porch mouth, an
   open side, not a census opening (`F-PORCH-ARCH`): no ledger deducts it or measures its face / soffit / arrises
   (UNKNOWN, facade owner).

## 4. Census (`CENSUS_T238.csv`, 68 census r3 openings + 3 features)

RECT_ON_OPENING_LINE 52, BAND_CROWN_READ_AS_HEAD 2 (W15, W16), ARCH_READ_AS_RECTANGLE 1 (W26), CURVED_ON_PLAN 1 (W17),
ARCH_DRAWN_NOT_DIMENSIONED 1 (A-GF-01), NOT_DRAWN 1 (A-1F-01), HELD_ELSEWHERE 10 (W02 count, SX-01 / SX-03, lift
openings, U-01, P-GF-01 / P-1F-01 heads, D-GF-15 gate: held for their own causes; no arc at any of them on the views
read), features 3 (porch arch, stair panel, B-B arc).

## 5. Delta (`DELTA_T238.csv`, 30 rows; for lane I, NOT applied to any merged ledger)

Per affected opening and ledger: windows m2 (T-150 W15 / W17 / W26, T-201 W16); masonry deduction (T-175 W15 / W26,
T-201 W16, A-GF-01, A-1F-01; W15 / W16 marked "applied by T-227"); plaster / paint face A / B (T-175 / T-201
consequences); reveal m.l; Sigma arris information; T-128 r3 rooms (owner method band min(head, H) and drawing method)
for W15 (1F-13), W16 (1F-13 HELD -> 4.363), W26 (ST-2F; owner method HELD on Q-72), W17 (1F-11 -> HELD, bound 10.024),
A-GF-01 (GF-01 / GF-02 HELD, candidate 2.413). Downstream: 1F-W00 net 12.863 (T-227) unchanged; T-237 reads W15 / W16
as 4.363 (no longer "HELD 4.362 .. 4.805"); T-211 / T-232 wire W15 / W16 at 4.363 masonry / finishes and 4.650 window.

## 6. Reconciliation with the freelancer (ERS s.2 step 4)

Windows, the 7 comparable (W01, W03, W13, W14, W15, W18, W26): his 45.481 -> scope 0 -> widths 0 -> heights: W13 +0.360
(2.30 vs his 2.00), W14 -0.980 (1.60 vs 2.00), W18 +0.600 (0.50 x 2.16 vs 0.60 x 0.80), W26 -0.360 (1.70 vs 2.00), W15
0.000 (3.00 = his 3.00) -> engine 45.101; residual 0.000. Verdict proposals: W15 / W16 window **FREELANCER_RIGHT**
(3.00, the opening crown; our 3.10 was the band); W26 window ENGINE_RIGHT (1.70 drawn and printed vs his 2.00, unchanged);
W17 **UNRESOLVED** (rule application: his 3.15 x 3.00 = 9.450; the opening-line reading 3.29 x 3.00 .. 3.05 = 9.870 ..
10.036 differs from him only by the Q-39 C width; the owner example 11.515). Masonry and plaster / paint deductions have
no comparable freelancer row per opening (his block / plaster sheets deduct lump openings): NOT COMPARABLE.

## 7. General rule (proposed, any villa): UP-OPEN-ARCH-001 v1.1.0

Provenance: Checker ruling 2026-10-23 20:14 + owner Q-73 final + owner Q-32 A + ERS s.3; extends the v1 text T-227 r2
proposed (`research/agents_t227/datum_rules.py`); a NEW rule version when the Lead files it, never an edit in place.
A1 opening line (a dimension that ends on a band / archivolt / panel line is not the opening height); A2 masonry /
plaster / paint deduct the true outline, the window line keeps Q-32 A on the opening line; A3 reveals and arrises follow
the arch; A4 a finish ledger's height cap clips the outline; A5 an opening curved on plan is a developed surface, HELD
until developed, bounded by developed width x opening crown; A6 a drawn, undimensioned arc bound to a census opening is a
source-supported candidate; an unbound one is UNKNOWN. Functions: `research/agents_t238/arch_rules.py`.

## 8. Tests

`tests/t238_arch_census/test_t238.py`, 18 tests (non-Alsenan villa T238-M, hand truth in the docstring: semicircular
window 2.9655 m2 masonry / 3.120 window / 7.085 m reveal / 2.7444 m2 under a 2.30 cap; segmental arc chord 1.00 rise 0.30
segment 0.213736 m2 (checked by an independent strip integration), arc 1.224951 m; curved-on-plan bound 7.350 m2.
Adverse: band crown as head refused in both trades; width x crown for masonry refused; chord only refused; jamb rectangle
only refused; a band line given as the arch refused; a stray point outside the jambs refused; rectangle perimeter as
reveal refused; held outline never deducted, never 0; cap inside the arch without its profile HELD; impossible segments
refused. Development villa: --check reproduction, census covers all 68 openings with the named defects, outlines vs
T-227 (0.0005), windows 56.771 -> 45.101, freelancer -0.380, W17 HELD 9.870 .. 11.515, merged T-150 file unchanged.

## 9. Owner confirmation for the Lead (ERS s.2.7: an owner-stated figure would change; section 6 format)

Issue: W17's window height. Evidence: NW elevation chain 305 + 45 (DXF 3050.5 / 454.3): 305 ends on the opening arch
(inner pair +8.500 / +8.5505), 45 on an archivolt 0.40 .. 0.45 above it; the frame lines stop below the inner arch. The
Q-32 and Q-39 question texts described 305 as "sill to where the arch starts" and 45 as "the arch rise"; the owner's
answers kept the principle "enclosing rectangle to the top of the arch" and wrote the example 3.29 x 3.50 = 11.51 m2.
Investigation: the same reading on W15 (300 + 10 = opening + band) was ruled by the Checker as 3.00 (FREELANCER_RIGHT).
Alternatives: (A) top of the opening arch: 3.29 x 3.00 .. 3.05 = 9.870 .. 10.036 m2 (the rule's principle on the drawn
arch); (B) the owner's example figure 11.515 m2 (to the archivolt). Impact: 1.48 .. 1.65 m2 of WINDOW.ALUMINIUM.
Recommendation: (A), because the aluminium frame ends at the opening arch and the archivolt is a wall-face element (the
same ruling as W15). Status: W17 window HELD 9.870 .. 11.515, never 0. Next: everything else proceeds; the lane I wiring
carries W17 as HELD.

## 10. Lessons-register row (proposed, ERS s.7)

2026-10-23 | Three arched openings carried the wrong outline in four merged ledgers (W15 / W16 band crown as head; W26 and
W17 width x crown as the masonry / finish opening; W17's 3.50 is an archivolt) | the printed chain was read as a head
without asking which line it ends on, and an arched opening was treated as a rectangle in every trade | read an opening on
its opening line: a dimension that ends on a band, archivolt or panel line is not the opening; masonry / finishes deduct
the true outline, the window line Q-32 A on the opening crown; reveals follow the arch (any villa; UP-OPEN-ARCH-001 v1.1) |
t238 `test_band_crown_taken_as_head_is_refused_in_both_trades`, `test_width_times_crown_for_masonry_is_refused`,
`test_rectangle_perimeter_as_reveal_is_refused` (normal: `test_m1_outline_window_and_reveal_by_hand`) | READY (T-238),
Checker to verify.

## 11. Held / unknown / missing (never 0)

W17 window height (s.9) and its developed finish outline (A5: the arch on a curved wall is not drawn developed);
A-GF-01 outline pending the Checker / designer D-45; A-1F-01 (not drawn); the B-B GF arc's identity; the porch arch's
face / soffit / arrises and their trade; W26's T-128 owner-method row (Q-72 room height); the Sigma arris line's basis
for arched heads (T-162 owner).
