# T-222: block-wall HELD bounds, part 2: the 1F bay basis, P-GF-05 and P-1F-01 (development villa; rule for every villa)

Worker 2, 2026-10-23 18:41 - 20:05 UTC per `date -u`, run session_01Qtfih85hRgtwsK5USREfUo. Lane A, gate 2, blockwork
programme row (BLOCKWORK_RESOLUTION_PROGRAMME.md). Files: research/agents_t222/*, tests/t222_bay_and_heads/* only (no
engine, rule, registry, frozen or released file changed; T-108 / T-215 / T-226 files untouched; masonry_centreline_v2
used read-only). ERS: read; s.2 steps 1-4 (element, evidence hierarchy, reconstruction, reconciliation), s.3 (one element
counted once; what is built before what is deducted), s.4 (rule + test), s.7 rows below. Drawings cited by Drive title,
view and DXF handle only; no coordinate, image or client name is committed. Development villa, not an accuracy claim.

## 1. Result in engineering terms (before -> after; units first)

| Item | Before (T-108 r2 / T-215 / T-207) | After (this run) | Status class (programme s.2) |
|---|---|---|---|
| 1F concave bay ends, 0.20 white (1F-W25 + the straight 1F-W00 / W01 ends) | 1F-W25 0.169 m / 0.581 m2 established; **0 .. 0.4769 m (0 .. 1.645 m2) HELD** | **+0.4124 m, +1.481 m2 (+0.296 m3); 0 HELD**: 1F-W25 0.415 m / 1.490 m2 (+0.247 m, +0.909 m2), 1F-W00 / W01 +0.166 m / +0.572 m2 | length and height SOURCE-SUPPORTED PENDING INDEPENDENT CHECK; white = PROJECT-SPECIFIC (Q-60 fallback, external) |
| 1F-W14 + W15 (0.15 black) junction piece at the bay end | in no run, in no bound | **+0.077 m, +0.302 m2 gross (+0.045 m3)**; net stays HELD on P-1F-01: 10.971 .. 16.223 -> **11.273 .. 16.525 m2** | SOURCE-SUPPORTED; net HELD |
| P-GF-05 masonry above the lintel (court wall, 0.20 white) | **HELD 2.232 .. 2.700 m2** | **2.640 m2 (0.528 m3)** = 1.20 x (B1 soffit +5.05 - lintel top +2.85) | SOURCE-SUPPORTED; white PROJECT-SPECIFIC |
| P-1F-01 'drawing CONFLICT' (designer D-64) | section B-B 'draws two leafed doors there' | **no conflict**: B-B looks north and draws the nearer wall WB-FL0013-FL0014 with D-1F-08 / D-1F-09, 2.25 m in front of P-1F-01's wall, which it hides | D-64 withdrawn (proposal) |
| P-1F-01 head; masonry above its lintel | HELD; 0 .. 4.992 m2 | **unchanged HELD** (head drawn on no sheet: R15 search list); 0 .. 4.992 m2, never 0 | HELD on D-60 (consultant row 9, send-ready) |

Black / white established m2 move: 1F 0.20 white +1.481 m2 (HELD bound closed inside the bound, see s.2), 1F 0.15 black
gross +0.302 m2 (net still HELD), GF 0.20 white +2.640 m2 of scope that is in no run (the open side was split out; it is a
scope item, never a deduction). HELD removed: 1.645 m2 bound (1F bay) and 2.232 .. 2.700 m2 (P-GF-05). Nothing is
integrated here (Worker 3 integrates; T-228 carries the register v2).

Engine vs freelancer: the section totals stay not like-for-like while other HELD items remain (T-108 s.3). One direct
check: he deducts the W17 bay as 3.15 x 3.00 m (T-175), i.e. a 3.15 m glazing width; the glazing between the drawn caps is
3.133 m on the band's mid circle (the hand row's drawn arc 3.136 m), so his width agrees within 0.017 m and he too keeps
the bay ends as wall. The engine's V2 basis (3.579 m of glazing on a 2.075 m circle carried to the centrelines) is the
one that differs: verdict proposal for the bay length basis ENGINE (V2) WRONG / drawing basis RIGHT; the freelancer's
width AGREES (comparison column only, never an input).

## 2. The 1F bay (s.2 steps 1-4)

Element: the W17 window, curved on plan with an arched head, in the 1F sea-side wall WB-FL0041-FL0042 (1F-W00 below,
1F-W01 above, the curved band = 1F-W25); 0.20 white; height under CB12 (25 x 75) 4.20 - 0.75 = 3.45 m, under the
0.16 slab 4.04 m (owner Q-60 A; storey 4.20, T-143 / T-108).

Evidence (P7757.dxf 1F plan, wall layer '1', window layer 'W'; handles):
- The band's faces are concentric arcs r 1.935 (D2:3021 / 3022 / 3024) and r 2.135 (D2:3025 / 3026 / 3030), t 0.20.
- Each end has a FULL-thickness radial cap on the wall layer (D2:3031 bottom, D2:3033 top, r 2.135 -> 1.935) and a
  0.12 frame line on the window layer (D2:3032, D2:3034) inside it: the glazing (three W arcs r 2.095 / 2.055 / 2.015)
  stops at the full caps. Between each cap and the straight wall the wall layer draws both faces: the pieces are wall.
- The architect's DWF NW elevation (vector; same revision as the DXF, T-201) confirms it without scaling: the frame
  lines stand at along-wall 7.871 / 10.563 m = the full caps' outer ends 7.8722 / 10.5637, and the facade jambs at
  7.670 / 10.728 = where the arc's outer face meets the straight outer face 7.6703 / 10.7297 (W15 / W16 reproduce the plan
  spacing to 1 mm): between jamb and frame the elevation draws wall surface (READINGS R12, R13). AGREES.
- No column in the window (S-COL.BON columns end 0.14 m below and 0.015 m above it).

Reconstruction (alsenan_t222.py, module bay_and_heads.py): drawn masonry in the window = arc band less the glazing sector
between the full caps + the straight band outside the arc's inner face + the 1F-W14 + W15 end region up to the straight
wall's face = 0.550 m2; the V2 run's own counted strips (its identity union, read-only) cover 0.422 m2 of it; the rest
(0.1275 m2) is assigned once by the UP-MAS-JUNCTION-001 band rule extended to arcs: through bands (the arc band and the
straight band; neither ends the other, so the most-central rule splits their overlap as a mitre) before the stem (1F-W14 +
W15 stops on their face). Heights by zone: the CB12 band of the FIRST FLOOR ROOF SLAB (ST handles 5DE / 5DF, 0.25 wide,
placed by the T-108 translation, 20 / 20 columns) -> 3.45; elsewhere slab 0.16 -> 4.04. Unassigned 0.

Reconciliation (units): T-108's bound 0.4769 m = hand 8.037 - V2 7.5601 m (0.443 glass basis + 0.034 arc vs chord) was
a comparison of two runs, not a physical length. Physical: +0.4124 m of 0.20 wall in the bay group (0.0645 m less than
the bound: the hand row's L2a 0.537 carried the ends to the centrelines), +0.077 m of 0.15 wall at the stem (outside any
bound: a junction piece in no run, as T-215's G-T108-1). m2: 0.4124 m at the CB12 height would be 1.423 m2; of the bay
group's plan area (0.1162 m2 incl. the stub strip) 0.0966 m2 lies under the CB12 band (3.45) and 0.0196 m2 under the
slab only (4.04), hence 2.062 m2 less the stub's established 0.581 = 1.481 m2. The T-108 1F-W25 stub (1F-STUB-001, 0.1685 m) stays established and inside the new 0.415 m (counted once).

For T-228: the total wall length changes by these two listed resolutions only: +0.4124 m inside a HELD bound (0.20 white,
1F) and +0.077 m of junction piece (0.15 black, 1F); a test that the total length is unchanged must list them.

## 3. P-GF-05 (court-wall passage mouth), masonry above the lintel

Element: the 1.20 m mouth of the GF side passage in the 0.20 court wall WB-FL0017-FL0018 (GF-W04 / GF-W05 line, external,
white by the Q-60 fallback), between two column jambs; floor +0.15 both sides; head +2.65 (T-201, DRAWING-CONFIRMED);
lintel L2 0.20 deep (S8.6 lintel schedule row, T-207).

What is above it (the two T-215 conditions):
(a) the zone over it is 1F DRY floor: the 1F plan above the court-wall line at P-GF-05 is the west master bed room (the
    bath's sunken zone begins 0.4 m further south); section B-B draws the 1F structural top +5.45 (0.05 under the +5.50
    floor) unbroken over the whole covered-court overhang (R2 = T-214, 0 mm).
(b) the 'B-B stub +4.95' is not this wall: P-GF-05's wall line lies 1.1 m SOUTH of the B-B cut and the section looks
    north, so it is not drawn at all; the +4.95 member stands at the main house's west wall, 2.8 m east (R6); the band
    cut at the overhang's west edge and the band beyond the cut (the overhang's north edge) both soffit at +4.70 (R4,
    R5). The SW elevation is drawn from the court side and its +4.70 line over P-GF-05 is that north-edge band, 3.0 m in
    front of the court wall, hiding the wall above +4.70 (R7, R9): an occluding soffit, never the top of this wall
    (`masonry_above` refuses it; it would give 2.220 m2).
The member on the wall line: the GROUND FLOOR ROOF SLAB draws the B1 band (handles 2AE / 2AF, 0.20 wide) unbroken over the
opening, its axis on the opening's centre (0.000 m), label B1 over the span; B1 20 x 40 (T-110 schedule row). Soffit
+5.45 - 0.40 = +5.05 -> masonry above the lintel 1.20 x (5.05 - 2.85) = **2.640 m2**, 0.528 m3. Evidence hierarchy: two
project drawings (ST plan + architectural section / plan) and an owner rule (Q-60 A); no fallback height.

FOR THE LEAD (not this task): the architectural section draws the overhang's west and north edges as a 0.75 m deep
rounded band (soffit +4.70) where the ST plan puts CB5 (schedule 20 x 40) and nothing on the north edge: concrete /
fascia scope (T-110 D-26 family).

## 4. P-1F-01 (1.30 m doorless opening, 1F-W14 + W15, 0.15 black)

The 'two leafed doors' of section B-B are D-1F-08 / D-1F-09 (engine 1F OP-005 / OP-006, 0.90 x 2.20): their positions
in the section reproduce OP-005 / OP-006 within 0.066 / 0.061 m, and their wall WB-FL0013-FL0014 stands between the cut
and P-1F-01's wall, 2.25 m in front of it; P-1F-01's centre lies 0.063 m from D-1F-09's in plan, which is why the two read
as one place. B-B is therefore OCCLUDED for P-1F-01, not in conflict with the plan (R14). Every sheet was searched for
the head, frame and leaf (R15): the DWF's every view, the PDF pages 1-12 (T-201 / T-207 reads) and the ST lintel
schedule (L2 150 x 200, no level): the head is drawn on no sheet. The interior wall cannot appear in an elevation; A-A runs
parallel 10.2 m west. **HELD**, never 0: net 11.273 .. 16.525 m2 (with the +0.302 m2 junction piece), masonry above the
lintel 0 .. 4.992 m2. Owner Q-55 C (internal DOOR 2.20 m, ASSUMED, drawings silent) is not applied: P-1F-01 is classed
a leafless passage (census OPENING.PASSAGE_NO_LEAF), and an owner fallback is not extended to another element type
(ERS s.3); whether it covers a leafless doorway is a Lead / owner scope ruling, listed, not assumed.

Consultant row 9 (D-64 / D-60): P-GF-05 resolved from the drawings (remove it); D-64 withdrawn (occlusion, not a
conflict); row 9 send-ready for P-1F-01 only: "head (or lintel soffit) level of the 1.30 m doorless opening between the
1F east master bed room and its entry, and what is built above it", with R15 as the search list.

## 5. Rule (proposed, any villa; new files when adopted, never edits)

UP-MAS-JUNCTION-001 v1.1.0 (extends T-215's v1.0.0): (1) a band may be an arc (d = |r - r_mid|); (2) a glazed curved
bay's glazing ends at the FULL-thickness caps on the wall layer; a partial cap is a frame line; the glazing length is the
mid-circle arc between the full caps, never the centreline-meeting arc; (3) where several bands contain a point, a band
drawn continuous across the junction (through) takes it before a stem; between through bands the most-central rule
applies; a stem's band runs to the face it stops on.
UP-VIEW-PLANE-001 v1.0.0: an element drawn in a section or elevation is evidence about an opening only when it lies on
the opening's own wall plane (depth along the view within 0.05 m) over the opening's plan range; an element on a nearer
plane covering the range OCCLUDES the opening (no evidence, no conflict); a same-plane disagreement with the plan is a
CONFLICT kept as a range. The masonry above an opening stops at the member on the opening's own wall line (structure
plan, Q-60 A), never at a soffit line of a member in front of it.

## 6. Tests and validation

- tests/t222_bay_and_heads/test_bay_and_heads.py (18): villa T222-F, NOT Alsenan, hand truth in the docstring: F1 arc
  ends 2 x 0.209440 m2 = 2 x 1.047198 m, gross 7.330383 m2 under two zones; glazing pi / 3 on r 2.00 = 2.094395 m; F2 L
  corner mitre 2.000 / 1.500 m; F3 stem against a through arc; mirror, 37 / 90 deg rotation and shift invariance;
  counted strip skipped once. Adverse: partial cap (frame line) refused; non-radial cap refused; masonry in no band ->
  PARTLY_HELD with its area; masonry under no member or slab zone -> HELD (ValueError); deepest member governs; mm
  refused; a wall listed twice refused; glazing-only window -> HELD never 0; without the through mark the stem takes
  arc masonry (shows why the mark is needed). Heads: F4 2.640 / HELD (0 .. 5.640) / RANGE (2.640 .. 3.120); occluding
  soffit refused as the top; F5 nearer wall OCCLUDES (no conflict), door on the own plane = CONFLICT (never a value),
  head line on the own plane = HEAD, two heads = CONFLICT, a partial nearer door without a face = NOT_SHOWN.
- tests/t222_bay_and_heads/test_t222_alsenan_ledger.py (6): bay closed inside its bound, nothing unassigned, stub counted
  once, glazing basis = drawn arc 3.136 +- 0.005, translations 20 / 20 and 30 / 30, P-GF-05 = 1.20 x 2.20 and never the
  occluded 2.220, P-1F-01 OCCLUDED and HELD 0 .. 4.992, no coordinates or client names in the files.
- `alsenan_t222.py --check` re-makes T222_RESULTS.csv from the private capture (T-125 dump of P7757.dxf) and ST7757 dxf.dxf:
  PASS. The DWF readings (READINGS_T222.csv) were read as vector geometry with one datum per view (no raster scaling).

## 7. For the Checker (re-measure from the drawings)

1. Bay: P7757.dxf 1F, caps D2:3031 / D2:3033 (full) vs D2:3032 / D2:3034 (frame); faces D2:3021-3030, straight faces
   D2:2913 / 2914 / 2922 / 2923, stem faces D2:3082 / 3084; your own once-only split of the two end regions (the total
   0.1275 m2 less the 1F-STUB-001 strip is the check); CB12 faces 5DE / 5DF on ST7757 dxf.dxf FIRST FLOOR ROOF SLAB.
   Expected 0.20 group +0.4124 m, +1.481 m2; stem +0.077 m, +0.302 m2.
2. P-GF-05: ST GROUND FLOOR ROOF SLAB B1 faces 2AE / 2AF over the opening between the column jambs; B-B (DWF or PDF
   sheet 10) structural top +5.45 over the overhang; confirm the +4.70 lines (B-B west edge cut, beyond-cut band; SW
   elevation over the opening) belong to the overhang's edges, not to the court-wall line. Expected 2.640 m2.
3. P-1F-01: B-B 1F doors vs engine OP-005 / OP-006 positions; their wall in front of P-1F-01's (2.25 m).

## 8. Lessons-register rows (proposed, s.7)

2026-10-23 | A section's door was read as a doorless opening's own (P-1F-01, 'CONFLICT' D-64) and an elevation's soffit
line as the member over an opening (P-GF-05 +4.70 / +4.95, 2.232 .. 2.700 m2 HELD) | views read by plan position only,
ignoring which wall plane along the view an element lies on | an element in a view is evidence for an opening only on the
opening's own wall plane; a nearer element occludes; the masonry top is the member on the opening's own wall line
(UP-VIEW-PLANE-001; every villa) | tests/t222_bay_and_heads (occluded vs conflict; occluding soffit refused) | proposed
(T-222 READY).
2026-10-23 | 1F bay ends held as 0 .. 0.4769 m for a day | glazing taken on the centreline-meeting arc instead of between
the full-thickness caps the wall layer draws | the glazing of a curved bay ends at the full caps; the band between cap and
straight wall is masonry, split once with the straight wall (UP-MAS-JUNCTION-001 v1.1.0; every villa) |
tests/t222_bay_and_heads (partial cap refused; F1 hand truth) | proposed (T-222 READY).
