# T-323 Slab hatches vs slab panels: census of every slab hatch on the roof-slab plans (F-T224-C1)

Worker 3, 2026-10-29. Lane S work taken under the Lead's 00:15 note ("a worker whose lane has no claimable TODO may take
another lane's TODO on disjoint files"). Development villa, not an accuracy claim. ERS s.2 (procedure), s.3 (one element,
several geometries; notation before arithmetic). Drawings cited by Drive title / layer / handle only; no coordinate,
drawing content or client name committed. Research only: **no candidate or released BOQ line moved.**

Files: `slab_hatch_edges.py` (any villa: edge classes, panel rebuild, refusals), `alsenan_t323.py` (private reader ->
`HATCH_CENSUS_T323.json`), `consumers_t323.py` (re-runs the T-213 and T-288 readers with the panel in place of the
hatch -> `CONSUMERS_T323.json`), tests `tests/t323_slab_hatch/` (hand fixture villa T323-H + development-villa pins).
Source: Drive "Alsenan chalet project" / "ST7757 dxf.dxf" (sha256 9f9d1179..., the Checker's copy) and, for the T-288
re-run only, "P7757_DXF_COMPRESSED.zip" (P7757.dxf).

## 1. The physical element and the notation

A suspended slab panel is the plate between the faces of the members that carry it (beam / column faces) and any free
slab edge (opening edge, cantilever tip). A hatch on a slab plan is a **region marker** (legend p.4 - p.6:
ANSI31 scale 2000 = "Sunken slab.", ANSI31 scale 800 = "Cantilever portion."). The drafter stops a hatch where an
annotation sits (slab-tag circle, label frame, bar line) and may close it with extra loops drawn by hand. The concrete
does not stop there. So the hatch tells WHICH panel is sunken / cantilevered; the panel's geometry comes from the drawn
member faces (UP-WALL-GEOM-001). Each piece of a hatch's outer boundary is classified:

| Class | Meaning | Panel edge? |
|---|---|---|
| MEMBER_FACE | on a drawn member line (T-139 EDGE layers 1, 5, S-COL.BON, S-BOUN, S-BEAM), running along it (5 degrees) | yes |
| FREE_EDGE | on a drawn opening edge (S-OPENING), not a member face | yes |
| ANNOTATION_CUT | on / inside an annotation's drawn extent (TEXT / MTEXT / INSERT / DIMENSION box, CIRCLE / ARC on a text layer, S-REIN-SLAB bar line, S-SEC.LINE) | **no** |
| UNEXPLAINED | none of these | panel HELD |

The panel is rebuilt from the T-139 face partition (the faces the Checker re-measured; reused by citation, polygonised
exactly as `research/agents_t139/slab_faces.py`), never from the hatch boundary. The hatch region = union of its region
loops, annotation islands not deducted (T-213 rules (a) / (b), reused).

## 2. Census: 43 hatches on S-HAT.BAT, 14 on the three roof-slab plans

29 are not on a roof-slab plan: 22 SOLID fills in the section details (bar dots) and 7 wall / ring hatches on the
foundation and ground sheets. **None of the 7 is a slab hatch** (the ground-bearing slab is not hatched); each was
checked against the merged ledger that measures its element from the drawn outlines, never from the hatch:

| Handle | Pattern | Ring net m2 (outer - island) | Element and ledger | Ledger m2 | Hatch - ledger |
|---|---|---|---|---|---|
| 7BD / 10E9 | ANSI37 | 4.8400 - 3.2400 = 1.6000 | lift-pit wall ring, foundation and ground sheets (T-322 / T-204, S-BW 10EB / 10EA) | 1.600 gross (1.100 net of C1 / C2 / C2 / C9) | 0.0000 |
| 7C4 | ANSI37 | 10.9364 - 8.5786 = 2.3578 | pool wall band (T-183 r2 / T-193 VERIFIED, S-BW 7C6 / 7C5) | 2.356726 | +0.0011 (+0.05 %, the hatch's own arc drafting; below every threshold) |
| 1657 | ANSI37 | 470.5500 - 452.1620 = 18.3880 | boundary-wall band on the foundation plan (S-BOUN outline) | not compared here (wall lane) | - |
| 7FD / 7FB / 80F | AR-B816C / AR-B816 | 8.3440 / 0.2300 / 0.2400 | block-wall bands on the ground sheet (S-BOUN outline) | not compared here (blockwork lane) | - |

So the slab-hatch question is confined to the 14 hatches on the three roof-slab plans.

| Handle | Sheet | Legend | Hatch m2 | Hatch P m | MEMBER m | ANNOT. m | Panel (T-139 face) | Panel m2 | Panel P m | Residual m2 | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 275 | GF roof | Sunken | 3.3250 | 7.300 | 7.300 | 0 | GF-016 SLAB | 3.3250 | 7.300 | 0.0000 | hatch = panel |
| 276 | GF roof | Sunken | 2.5725 | 6.440 | 6.440 | 0 | GF-015 SLAB | 2.5725 | 6.440 | 0.0000 | hatch = panel |
| 280 | GF roof | Sunken | 7.3009 | 11.6255 | 11.626 | 0 | GF-141 SLAB | 7.3009 | 11.6255 | 0.0000 | hatch = panel **only as the union of its 2 loops** |
| 287 | GF roof | Sunken | 2.0804 | 7.0778 | 7.078 | 0 | GF-128 SLAB | 2.0804 | 7.0778 | 0.0000 | hatch = panel |
| 298 | GF roof | Sunken | 4.1076 | 8.8426 | 8.052 | **0.791** (circle 31C) | GF-081 SLAB | **4.1176** | **8.8413** | **+0.0100** | **NOT the panel** |
| 5BF | 1F roof | Sunken | 5.4000 | 9.600 | 9.600 | 0 | 1F-018 SLAB | 5.4000 | 9.600 | 0.0000 | hatch = panel |
| 2B1 | GF roof | Cantilever | 0.1000 | 1.400 | 1.400 | 0 | GF-112 BEAM_OR_COLUMN | 0.1000 | 1.400 | 0.0000 | beam band (whole face) |
| 54D | GF roof | Cantilever | 0.3450 | 2.900 | 2.900 | 0 | GF-143 + 144 + 158 BEAM_OR_COLUMN | 0.3450 | 2.900 | 0.0000 | beam band (whole faces) |
| 38C | 2F roof | Cantilever | 0.2260 | 2.660 | 2.660 | 0 | 2F-007 BEAM_OR_COLUMN | 0.2260 | 2.660 | 0.0000 | beam band (whole face) |
| 390 | 2F roof | Cantilever | 0.6200 | 6.600 | 6.600 | 0 | 2F-032 BEAM_OR_COLUMN | 0.6200 | 6.600 | 0.0000 | beam band (whole face) |
| 391 | 2F roof | Cantilever | 0.3563 | 3.9635 | 3.963 | 0 | 2F-048 BEAM_OR_COLUMN | 0.3563 | 3.9635 | 0.0000 | beam band (whole face) |
| 273 | GF roof | Cantilever | 0.7500 | 4.000 | 3.750 | 0.250 (bar line 439) | portion of GF-011 BEAM (B24, 2.700 m2) | HELD | HELD | - | cantilever portion of a band |
| 2B4 | GF roof | Cantilever | 1.2000 | 6.800 | 6.650 | 0.150 (bar line 486) | portion of GF-066 BEAM_OR_COLUMN (2.640 m2) | HELD | HELD | - | cantilever portion of a band |
| 5E0 | 1F roof | Cantilever | 1.3500 | 6.900 | 6.700 | 0.200 (bar line 6E1) | portion of 1F-045 BEAM_OR_COLUMN (2.995 m2) | HELD | HELD | - | cantilever portion of a band |

FREE_EDGE 0 and UNEXPLAINED 0 on all 14. Answer to the engineering question: **of the 14 slab-plan hatches, 1 is not its
panel even after its loops are united (298), 1 is its panel only when its two loops are united (280), and the 8
"Cantilever portion." hatches are not slab panels at all** (they mark beam bands: 5 whole band faces, 3 the cantilever
portion of a longer band).

### 2.1 Hatch 298 (GF roof, 1F east wet room): the residual named to its cause

Loop 1 alone (what the Checker measured on 2026-10-28 23:01): 3.8808 m2, P 8.5594 m (= the Checker's 8.560). Loop 2
closes most of the cut that slab-tag circle 31C (S-TEXT-SLAB, r 0.515) makes; the union is 4.1076 m2, P 8.8426 m (=
T-213's figures; the Checker's pin "298 = 8.843 m" reproduces as this hatch-union perimeter). Inside circle 31C the
drafter redrew the column notch (column face GF-082, S-COL.BON) **0.050 m south of the column outline**: 0.791 m of the
union's boundary lies on the circle's extent, not on a member face. Panel by member faces (T-139 GF-081): 4.1176 m2,
P 8.8413 m. Residual panel - hatch = +0.0100 m2 = **+0.0225** (0.45 x 0.05 m strip of slab inside circle 31C / text
46C, not hatched) **- 0.0125** (0.25 x 0.05 m of hatch over column GF-082) ; residual other 0.0000. Perimeter -0.0013 m
(the notch is shifted, not resized; the skew of the B28 face is the same on both). T-288 measured the same 0.05 m as
its "hatch-to-column gap" for wall GF-W12 (concurs). T-213 named this residual "the B28 face and the column corner":
the column-corner part is right, the cause is the annotation-circle notch, not the B28 face.

### 2.2 Hatch 280: two loops, one panel

Loop 1: 7.1231 m2, P 11.6122 m (the Checker's "11.612 incl. arcs"); loop 2 (0.1778 m2) closes the cut of circle 389
(r 0.673). Union = panel GF-141 exactly (7.3009 m2, P 11.6255 m, symmetric difference 0.0000). A reader that takes the
first loop only would lose 0.1778 m2 (-2.4 %).

### 2.3 The "Cantilever portion." hatches are beam marks

Every face under them is a T-139 beam / column / junction face (width 0.20 - 0.50 m), none a slab panel. Three cover
part of a longer band: they close across the band on the **support-face alignment** (the column face extended), and
0.25 / 0.15 / 0.20 m of that closing edge is drawn coincident with a bar line (classified ANNOTATION_CUT, all of it on
the straight extension of a drawn member face). The beam lane already measures the B24 piece independently: T-241
BM-GF-059 band piece 1.501 m (route-G band partition) vs hatch 273 1.500 m (1 mm, not a hatch consumer). No slab line
carries any of the 8.

## 3. Consuming lines (V3.0.20) and research readers: effect, nothing moved

| Consumer | Reads the hatch outline? | Effect if it did / effect found |
|---|---|---|
| STR.CONC.SLAB, the six sunken lines L-c544aa98e09609150e4d (275), L-7117723666e439340d84 (276), L-abe0c36f94dba208300f (280), L-84ca57fea5c1db2a0076 (287), L-70830345ffdabc4cf7d5 (298), L-4baffcb95570ca418d0c (5BF) | **No**: route-G / T-139 member faces (V3.0.11 snapshot `research/agents_t146/CANDIDATE_V3011_BEAM_SLAB.json`; V3.0.12 SLAB_FACE_HOME keeps them, V3.0.13 - V3.0.20 have no STR.CONC.SLAB piece) | 298 carries 0.658817 m3 = 4.1176 x 0.16 (panel). The hatch would give 0.657216 m3 (-0.0016 m3, -0.24 %). **ENGINE_RIGHT.** |
| Soffit formwork (slab) | no candidate line (formwork NOT_IMPLEMENTED in the candidate); research ledger T-308 works by line / face, no hatch reader | 0 |
| Slab step (riser / beam side) | no candidate line; `engine/source/slab_step_v2.py` (T-224) is unwired; its tests use P_ext 5.550 / 4.690 / 9.600 m (275 / 276 / 5BF: hatch = panel) | 0 |
| Slab rebar panel spans | candidate rebar from route-G faces; T-307 / T-316 take only the SET of sunken face ids from T-213 | 0 |
| T-213 `SUNKEN_PANELS_T213.json` (research, merged) | **yes** (hatch union) | 298: A 4.1076 -> **4.1176 m2** (+0.0100, +0.24 %), P = P_ext 8.8426 -> **8.8413 m**; its HELD formulas become fill 4.1176 d, riser / beam side / WP upturn 8.8413 d. Its slab concrete 0.6572 m3 vs the candidate's 0.6588 m3: the candidate is right. Others unchanged. |
| T-288 `CLIP_T288.json` (research, merged; register v4 uses the census pieces, not this clip) | **yes** (hatch + island loops united back) | GF-W12 under GF-081: 0.40 in hatch + 0.05 gap = 0.45 m = panel (already corrected by T-288). **GF-W32 under GF-016: 0.6210 -> 0.6124 m** (-0.0086 m; a text-island loop of 275 extends 0.0066 m2 past the panel edge): of T-288's named junction difference +0.1404 m, 0.0086 m is this island, 0.1318 m the junction. Register v4 (0.7911 d for GF-W32) unchanged. |
| T-209 `SUNKEN_OVERLAY_T209.json` (research) | **yes** (every path united, arc edges as chords) | clip regions 275 3.3316 / 276 2.6048 / 287 2.1456 / 298 4.1096 vs panels 3.3250 / 2.5725 / 2.0804 / 4.1176 m2 (islands past the panel edge; 298 notch). Room "under sunken" m2 can move by at most +0.0652 m2 per panel; no room flag changes (smallest flagged room 0.3623 m2 under a panel). Not re-run (needs the T-147 room regions). |

Side finding (T-213 edge probe): for 280 the hatch union and the panel are the SAME polygon, yet T-213's
`classify_edges` gives P_ext 8.6418 vs 8.6527 m (P_shared 2.9838 vs 2.9728) depending on the vertex list: its 0.05 m
probe pieces at the oblique B27 end flip SHARED / EXTERNAL. Resolution of that reader is about +-0.011 m (0.13 %) on P_ext;
named, not changed (d-driven quantities stay HELD on D-41).

## 4. Owner manual method beside the drawing-derived method

No answered owner rule measures a slab from a hatch; the owner's slab method is panel between beam faces (convention C1,
T-234; Q-16 no copied depth). The drawing-derived panel here is that method; the hatch is only the legend tag of the
panel. Nothing ASSUMED. Evidence status: the 6 sunken panels and the 5 whole-face cantilever bands DRAWING-CONFIRMED
(T-139 faces, Checker re-measured T-139); the 3 cantilever portions HELD as panels (they are portions of beam faces;
their quantities belong to the beam lane, BM-GF-059 etc., HELD there under D-04).

## 5. Rule and lessons row (proposed, ERS s.7)

Rule (any villa, provenance T-323): a slab hatch never gives a panel's geometry; it tags which panel(s) it marks. Each
hatch boundary piece is MEMBER_FACE / FREE_EDGE / ANNOTATION_CUT / UNEXPLAINED; an annotation cut is never a slab
edge (no step, riser or edge form on it); a hatch that covers part of a face marks a portion (a cantilever starts at the
support-face alignment), not a panel; a hatch region is the union of all its region loops, never the first loop.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-29 | Slab hatch boundaries read as panel outlines: 298 P 8.560 / 280 P 11.612 (loop 1, cut by tag circles 31C / 389); 298 union still 0.0100 m2 off its panel | A hatch is a region marker: the drafter stops it at annotations and redraws notches by hand inside them (298: column notch 0.050 m off) | Panel geometry from drawn member faces; hatch only tags the panel; annotation cuts never slab edges; union of all region loops; a partial hatch marks a portion, not a panel (any villa) | tests/t323_slab_hatch (fixture T323-H: tag circle + label frame, residual 0.35635 m2 named; adverse: annotation edge as free edge refused, open panel HELD, portion HELD, mm refused, mirror / rotation) | proposed |

## 6. For the Checker (re-measure from the drawing)

1. 'ST7757 dxf.dxf', S-HAT.BAT HATCH 298: loop 1 P 8.5594 m; union of loops 1 + 2: 4.1076 m2, P 8.8426 m (pin 8.843);
   panel = T-139 face GF-081 4.1176 m2, P 8.8413 m; the notch of loop 2 vs column GF-082 (S-COL.BON): 0.050 m offset;
   +0.0225 / -0.0125 m2 inside S-TEXT-SLAB circle 31C (r 0.515).
2. HATCH 280: loops 1 + 2 = 7.1231 + 0.1778 = 7.3009 m2 = GF-141; circle 389 r 0.673.
3. The 8 ANSI31 scale-800 hatches: faces under them are T-139 BEAM / BEAM_OR_COLUMN (table, section 2); 273 / 2B4 / 5E0
   close on the column-face alignment (S-REIN-SLAB lines 439 / 486 / 6E1 on that alignment for 0.25 / 0.15 / 0.20 m).
4. Candidate line L-70830345ffdabc4cf7d5 = 0.658817 m3 = 4.1176 x 0.16 (panel, not hatch).
5. Random line suggestion: hatch 5E0 on 1F-045 (1.350 of 2.995 m2).

## 7. Not done / uncertain

- T-209 overlay not re-run (bound given); T-213 / T-288 JSONs are not edited here (a research ledger correction for the
  lane that owns them, or for lane I when it wires sunken panels: use panel 4.1176 m2 / P_ext 8.8413 m for 298).
- The 22 SOLID section fills are listed only; 1657 / 7FD / 7FB / 80F rings are recorded, not compared with the wall
  and blockwork ledgers (not slab elements).
- d (the drop) stays HELD on D-41; nothing here makes a d-driven quantity determinate.
