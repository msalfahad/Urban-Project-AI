# T-147: Alsenan ceilings room by room under owner Q-57 A modified (NO REPO CODE)

Worker 2 (lane A, architectural and finishing), 2026-10-21 11:40-12:40 UTC. Gate 2 (architectural coverage: a missing
BOQ category). Development villa, not an accuracy claim; nothing is wired and no released quantity changes: a checked
piece for the consolidated ARCH_TAKEOFF_V3.0 candidate (lane I). Self-check of this run: clone, venv, codemap check
(stale: none), t061 (20 passed), freeze check (0 differing): all PASS. No engine module was changed or run.

Data (Drive "Alsenan chalet project", scratchpad copies, never committed): P7757_DXF_COMPRESSED.zip (architectural
DXF), "ST7757 dxf.dxf" (sha256 9f9d1179..., the T-110 / T-139 file), p7757_arch_sheet03.pdf (GF plan) and
p7757_arch_sheet04.pdf (1F plan) read at 200 dpi, the freelancer's finishes workbook rows already parsed in
tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (FIN "decor" sheet rows 13-75, PNT rows 46-51).
Merged / READY inputs used: T-074 wet-area hand table, T-088 printed room sizes, T-110 beam member register (depths),
T-139 roof-slab faces and classes (READY 84d156e: its `slab_faces.py` reproduced the 402 faces on the same file, 400
with identical areas), T-127 exterior soffits, T-091 printed-notes census, T-112 / T-128 heights and designer requests.

Rules: owner Q-57 A modified (gypsum decor ceilings: finishing + paint, no cement plaster; seven surfaces measured
apart; ceiling paint is not blindly the floor area; the freelancer's 452.33 m2 is comparison only; cove needs geometry
or an approved detail), Q-48 A (decor ceiling 0.15 m below the beam), Q-43 / G1 (owner manual line = slab top - 0.60 -
0.15), Q-52 C mod (a beam lowers the ceiling only where it is in the room; drawing-derived ceiling HELD / PROVISIONAL),
Q-61 C (CONFLICT and HELD beams stay held), Q-44 A (dome positions are open skylights), Q-68 C (soffits over outside air
apart), Q-37 A / Q-06 (pantry and basin spaces are wet), designer D-40 (no ceiling level printed), UP-QTY-STATUS-001.

## 1. Result in engineering terms (m2 of ceiling; the freelancer's decor rows for comparison)

| Floor | Plan area under the slab | No ceiling / HELD above it | **Horizontal decor ceiling** | Freelancer decor rows | Difference | Paintable gypsum, owner method | Bulkhead faces, owner method |
|---|---|---|---|---|---|---|---|
| GF (16 rooms + 1 unidentified face) | 232.70 | light well 23.24 + round-stair strips 2.45 | **207.01** | 232.81 (197.33 + 35.48) | -25.80 (-11.1 %) | 228.59 | 21.58 |
| 1F (12 rooms + 1 unidentified face) | 166.70 | dome openings 29.07 HELD | **137.63** | 143.87 (112.96 + 30.91) | -6.24 (-4.3 %) | 148.83 | 11.20 |
| 2F (3 rooms + stair-hall top) | 43.50 | - | **43.50** (30.53 without the stair-hall top 12.97) | 32.90 (27.28 + 5.62) | +10.60 (+32.2 %); -2.37 (-7.2 %) like for like | 43.50 | 0 |
| **Villa** | 442.90 | 54.76 | **388.14** | 409.58 | **-21.44 (-5.2 %)** | **420.92** | **32.78** |

Against the freelancer's paint line "decor paint with cove light" 452.33 m2 (= 409.58 decor + 42.75 cove strips): our
owner-method paintable gypsum 420.92 m2 is -31.41 m2 (-6.9 %); like for like without his cove strips (cove is HELD here:
no detail) it is +11.34 m2 (+2.8 %), the bulkhead faces he does not carry (32.78) less the openings he does not deduct.

Measured, held, unsupported, per type (the seven Q-57 surfaces):

| Q-57 surface | Quantity | Status |
|---|---|---|
| 1 horizontal gypsum, dry rooms | 305.63 m2 (GF 158.08, 1F 109.60, 2F 37.95 incl. the 2F stair-hall top 12.97) | MEASURED (plan); finish by Q-57 A |
| 2 board in wet rooms (moisture-resistant only where specified) | 82.51 m2 measured (GF 48.93 incl. pantry 13.50 and kitchen 9.63, 1F 28.03, 2F 5.55) | area MEASURED; **board type HELD**: no sheet specifies a ceiling board (T-091: 0 false-ceiling / cove notes on all sheets) |
| 3 other boards | none drawn | - |
| 4 vertical bulkhead faces | owner method **32.78 m2** CALCULATED on 198.79 m of free beam edge; drawing-derived **175.76 m2 PROVISIONAL**; **58.11 m of edge HELD** on CONFLICT / HELD beams | see section 3 |
| 5 cove returns and drops | cove / cornice runs HELD (closed rooms 302.88 m of wall perimeter listed, no length invented for the open zones); drops at slab openings: **47.00 m of edge, height HELD** (GF light well 21.32, 1F dome openings 25.68) | HELD (no detail drawn) |
| 6 paintable gypsum surfaces | owner method **420.92 m2** (horizontal + owner bulkhead faces) | CALCULATED; coves and drops HELD, not in it |
| 7 concrete ceiling plaster | none required by any sheet | NOT SPECIFIED (not a zero quantity: no item) |
| apart: no ceiling plane under the open dome positions | **29.07 m2 HELD** (west dome 14.24 over the 1F west master bed room and its two baths; east dome 14.83 over the living zone, the east master bed room and its bath) | HELD for the designer (DCR-4), never 0 |
| apart: spaces not identified | 4.34 m2 (GF face between the wedge W.C.s 1.37; 1F space by the arch, no label 2.97) | area MEASURED, type HELD |
| apart: stair shafts GF / 1F (stair soffits, not decor ceilings) | 25.45 m2 (flight soffits 21.45) | HELD (stair finish line, T-111) |
| apart: soffits over outside air (T-127) | 44.446 m2 | HELD (Q-68 C), not in this table |

## 2. What the drawings say, and where the freelancer differs (who-is-right proposals)

1. **GF light well over the reception: no GF ceiling exists over 23.24 m2.** The GF roof-slab plan (ST p.4) draws the
   VOID X box with the round stair inside (T-139 face GF-130, 23.237 m2); the 1F plan (sheet 04) prints the same opening
   "VOID" 400 x 587 = 23.48 m2 (second drawing; -0.24 m2 = the rounded corner the structural outline follows round the
   stair). The freelancer's "reception + dining" 137.50 m2 + "entrance" 10.46 m2 = 147.96 m2 equals our gross plan
   147.90 m2 (-0.06 m2, -0.04 %): he ceils the light well and the round-stair strips. Proposal **ENGINE_RIGHT** (hand,
   two drawings): 122.21 m2 of decor ceiling in the open room + pantry, -25.75 m2 (-17.4 %) vs his rows. Every other GF
   room agrees within 1 % (dewaneya 24.94 vs 24.84, +0.4 %; driver 7.875 vs 7.87; master bed room 16.557 vs 16.66,
   -0.6 %; kitchen 9.63 vs 9.55, +0.8 %): the whole GF difference (-25.80) is the light well and the stair strips (25.69).
2. **1F: the ceiling over the light well is at the 1F roof, and the freelancer leaves it out.** The 1F roof-slab plan
   (ST p.5) is closed over the void (no opening face there), so the 1F open zone has a ceiling over the double-height
   space: 1F zone plan 63.01 m2 (living + corridor + landing + connector 39.77 + the void footprint 23.24), less the
   east dome opening 14.04 HELD = 48.98 m2 vs his "living" 38.96 m2 (+10.02, +25.7 %). Proposal **ENGINE_RIGHT** on the
   void ceiling (ST p.5 closed slab), **UNRESOLVED** on the dome openings (no ceiling designed, DCR-4).
3. **Dome openings (Q-44 A open skylights) take 29.07 m2 out of the 1F ceilings**: west dome 11.58 m2 over the west
   master bed room (19.125 plan, 7.54 left), 1.24 / 1.42 m2 over its two baths; east dome 14.04 m2 over the living zone,
   0.34 / 0.45 m2 over the east master bed room and its bath. The freelancer ceils them in full (bed rooms 1-4 74.00 m2
   vs our plan 72.54, -2.0 %, and horizontal 60.62, -18.1 %). **UNRESOLVED** until the designer says what closes the
   openings (glazing at the slab, at the drum top +11.00, or a ceiling below: T-112 DCR-4).
4. **Cove strips 42.75 m2**: he takes 0.10 m x his cornice runs (282.85 m dry + 144.61 m wet). No sheet draws a cove or
   cornice (T-091). Our closed-room perimeters are 302.88 m (dry 164.51, wet 138.36; the open zones are not closed
   and carry no run); the cove stays HELD. **RULE_DIFFERENCE / UNRESOLVED** (Q-57: geometry or an approved detail first).
5. **Wet-room board**: he prices one "bathroom and kitchen decor" line (72.01 m2); our wet set is 82.51 m2 because the
   pantry (13.50, wet by Q-37 A) is in his dry "reception + dining" row. Room by room the identifiable wet rows agree:
   laundry 10.151 vs 10.00 (+1.5 %), 2F W.C. 5.55 vs 5.62 (-1.2 %), kitchen as above. Board type HELD.
6. **2F**: maid room 19.35 (printed 300 x 645) vs 19.58 (-1.2 %); his 2F corridor 7.70 vs our lobby outside the shaft
   box 5.63 (printed lobby 450 x 195 = 8.775 includes the 4.875 m2 stair arrival inside the box, Q-70); the 2F roof slab
   covers the whole shaft box (12.97 m2), which he does not ceil: listed as its own line, decision for the checker
   (ENGINE_RIGHT if the stair hall takes the decor ceiling like the rooms, Q-48 A making no exception).

## 3. Bulkheads: where a beam of the register is inside the room

Method (`scripts/ceil_ledger.py`): the roof-slab faces of the same floor (T-139) are moved onto the architectural plan by
a pure translation found from the column outlines (GF 30 / 30, 1F 20 / 20, 2F 9 / 9 columns coincide, spread 0.000 m);
each beam face is bound to its T-110 register span (span midpoint on the face's long axis within 0.12 m, drawn width =
register width); the piece of the beam inside the room polygon gives its free edge = the piece outline not lying on the
room's wall faces. A beam on a wall line leaves no piece (its side is part of the wall face, Q-52).

- Owner method (Q-43 line, Q-48 A): ceiling plane = slab top - 0.75; a beam deeper than 0.60 m needs the ceiling 0.15 m
  under its soffit, so each free edge carries a vertical face of D - 0.60 (0.15 m for the 0.75 beams, 0.25 m for B26 /
  B27 0.85). Beams of 0.40 / 0.50 m sit above the 0.15 decor depth: no face. **32.78 m2** in 13 rooms; the biggest:
  GF open room 14.44 m2 (B22 0.50 x 0.75 across 7.80 m, B26 0.65 x 0.85 across 7.45 m, B13, two CB3 spans, CB1 / CB8
  0.10-0.15 m overhangs along the facade), GF pantry 2.84 (B27 0.90 x 0.85), GF master bed room 2.01 (B16 across),
  1F living zone 7.56 (B18, B25, B11 across, CB11 along), 1F 380 x 430 1.84 (B19 across as T-112 found, and a B25 0.55 x 0.75 piece 1.69 m long that T-112 did not list; its B6 is the CONFLICT span, held),
  dewaneya 1.19 (CB6 across, as T-088 / T-112 found). Edge steps narrower than 0.06 m (beam face within 6 cm of the wall
  face) are counted and named: 1.34 m2 (1F zone CB12 0.93, 1F bath east 0.29, 1F east master bed room 0.13).
- Drawing-derived (ceiling 0.15 m under the slab soffit, the only drawn reference; no ceiling level printed, D-40):
  every registered beam piece makes a face of D - 0.16: **175.76 m2 PROVISIONAL**. The ring beams round the dome
  openings are not in it (their faces are listed under the openings: drop height HELD).
- HELD, never the larger value (Q-61 C): GF B21 (45 schedule / 40 drawn) and B29 (25 / 20) across the open room, CB2
  (20 / 25) at the core, GF CB3 'with stair' BM-GF-057, 1F CB10 (depth by candidates only), 1F B6 vertical span (25 /
  20), 2F unlabelled span BM-2F-018: **58.11 m of free edge**; the candidate owner-method face is written on each row
  (for example B29 2.09 m2, B21 2.46 m2).

## 4. Checks made (second drawing or independent route for every number used)

| Check | Result |
|---|---|
| DXF room regions against printed sizes and the verified T-074 table | 26 of the 28 rooms with a reference agree to 0.000-0.089 m2 (dewaneya 24.939 / 24.94; driver 7.875; kitchen 9.630; pantry 13.411 / 13.50; 1F beds 19.05 / 18.215 / 16.340 against printed 19.125 / 18.25 / 16.34; GF wedge B 2.3445 / 2.3676; maid 19.350). Two differ and the reference area is used: GF wash lobby region 4.477 vs 4.732 (-0.255: my closing line at the hall sits inside T-074's; the B11 bulkhead there, 0.72 m2, may be a little short) and GF master bath region 4.596 vs 3.717 (+0.879: the region takes in the space east of the bath; T-074's printed 2.10 x 2.00 less the corner governs; no beam deeper than 0.60 in it, so the owner method is unchanged). Checker items |
| GF open room + pantry gross | 147.90 m2 vs the freelancer's 147.96 (two independent routes to the same outline) |
| Light well | ST p.4 face 23.237 m2 vs printed 1F "VOID" 400 x 587 = 23.48 m2 |
| Dome openings | circle r 2.2111 m (p.3 dome detail diameter 442, T-139) = 15.359 m2 each; inside rooms 14.24 / 14.83 m2, the rest over walls and the partition under the west opening |
| Beam crossings | dewaneya CB6 piece 0.20 x 4.00 = printed room width 4.00 (owner face 2 x 4.00 x 0.15 = 1.20; the tool gives 1.193: the free edge stops 12 mm short at each wall, -0.6 %, conservative and stated); 1F 380 x 430 B19 and B6 (T-112), GF open room B26 / B27 (T-088), pantry B27 (T-128) all found again by the overlay |
| Synthetic fixture (not Alsenan) | `python3 -I scripts/t147_calc.py --selftest <dir>`: a 5.00 x 4.00 hall with a crossing 0.30 x 0.85 beam, an edge 0.75 beam, a shallow 0.50 beam, a CONFLICT beam, a junction piece without a register row and a dome opening; a wet 2.00 x 2.00 bath; a living with a light well and a stair strip; an unidentified face: 15 hand values, **15 PASS**, and no HELD row shown as 0 |
| Prior work disagreeing | T-128 lists "2F lobby B15 1.20 (0.89)" as crossing the lobby: the overlay finds no B15 piece inside the 2F lobby outline (B15 is on the west band; the only member inside the lobby is the unlabelled HELD span BM-2F-018). Checker item |

What I learned: (1) the ceiling is a SLAB-side quantity, not a floor-side one: two openings (the light well and the
dome skylights) move 52 m2 between floors or out of the BOQ, while room plans agree with the freelancer within 1-2 %;
(2) with the owner's 0.60 allowance only beams deeper than 0.60 m make bulkheads, and on Alsenan every one of them is a
0.75 or 0.85 beam of the register; the drawing-derived reference turns every downstand into a bulkhead (5.4 x more
face); (3) the structural and architectural plans of this villa coincide by pure translation, so room-by-slab overlays
are exact here (a rotated or scaled set would need the same column fit with rotation; the fit reports its spread).

## 5. What is missing / held (designer requests already filed, no new owner question)

- D-40 ceiling level per room (every drawing-derived bulkhead face PROVISIONAL), DCR-4 dome openings (29.07 m2 HELD),
  DCR-5 the 2F maid room dome conflict (architecture draws a dome, the structure is flat: measured on the structure, 19.35
  m2, conflict stands), Q-61 C members (58.11 m of bulkhead edge), wet-room board type, cove / cornice detail, the drop
  heights at the light well and dome edges, the stair soffits (T-111 line), exterior soffits (Q-68).
- No owner question: Q-57 A mod and Q-48 A answer the method; the open points are designer information (D-40, DCR-4).
- Checker re-measure proposal (3 rooms): GF dewaneya (printed 400 x 630 + CB6), GF pantry (printed 450 x 300 + B27
  0.90 x 0.85) and the 1F master bed room 380 x 430 (B19 / B25 / B6 conflict).

Files: `CEILINGS_T147.csv` (291 rows: one per room and surface type), `CEILINGS_T147_FLOORS.csv` (per floor and kind),
`CEILINGS_T147_VS_FREELANCER.csv` (rows naming the same room), `summary.json`, `rooms_geom.json` (areas and lengths per
room from the overlay, no coordinates), `scripts/` (rooms.py room regions, align.py column fit, ceil_ledger.py overlay,
t147_calc.py rules + self-test; T-139's slab_faces.py makes the faces). Repeat: `python -I rooms.py <arch.dxf> <box>
<json>` per floor, `python -I align.py <arch.dxf> <st.dxf> align.json`, `python -I slab_faces.py <st.dxf>
st_faces.json`, `python -I ceil_ledger.py <scratch> <T-139 PANELS.csv> <T-110 register> <out>`, `python3 -I
t147_calc.py rooms_geom.json <out>`.
