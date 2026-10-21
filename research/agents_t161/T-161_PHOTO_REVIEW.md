# T-161: photo review of the owner's 27 Alsenan images (2026-10-21) against the drawings

Worker 2, 2026-10-21 23:47 - 2026-10-22 UTC. Lane A, Gate 1, NO REPO CODE (text files only in this folder). Rules:
WORKFLOW_CONTROLS_2026-10-21 section 8 (photo review: a photo corroborates or questions the drawings, never produces or
silently changes a quantity, never scaled), section 5 (evidence statuses), MISSION drawing-first, UP-STAIR-002, owner
answers Q-27 A, Q-29, Q-44 A, Q-65 C, Q-67 A, OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 (incl. the 23:20 decisions),
OWNER_NOTES_SIGMA_2026-10-21 item 3. No image, client name, house number, address or title-strip text is copied here;
images are referred to by Drive file id (list in `IMAGES_T161.csv`, created order I01 .. I27).

## 0. What was read

| Source (Drive "Alsenan chalet project") | How | Used for |
|---|---|---|
| 27 JPGs "PHOTO-2026-06-15-11-31-14.jpg" (ids in IMAGES_T161.csv; sizes re-checked equal to Drive) | decoded into the private folder, every image looked at in full | description per image |
| Alsenan_Architectural_P7757_Pages_05-06 (p.5 2F plan, p.6 SOUTH EAST ELEVATION) | 60 / 110 / 220 dpi renders, rotated | dome positions R221, maid-room dome, street-side elevation, entrance arch, dewaneya section |
| Alsenan_Architectural_P7757_Pages_07-08 (p.7 SOUTH WEST, p.8 NORTH WEST ELEVATION) | same | sea-side elevation, pool-court face, annex side |
| p7757_arch_sheet03 (GF plan) | 110 dpi | street / sea edges, dewaneya windows, entrance steps, court, north strip |
| research T-150 (agents/task-T-150 8bbf39d), T-127 (merged), T-159 (READY f35bafb), board ELEMENT_REGISTER, OWNER_QUESTIONS(_ANSWERED) | read | opening ids, pool-court void, owner answers |

## 1. What the images are

All 27 are the designer's 3D RENDERS (design intent): 11 carry the consultant's title strip with the project code; none
is a site photograph, so none shows what is built. They fall into five views:

| Group | Images | Side, by the drawing sheet it matches |
|---|---|---|
| Sea-side elevation from the beach | I06, I07, I10, I11, I12 | NORTH WEST ELEVATION (p.8): two arched 1F French windows 155 with fanlights, wavy parapet with X railing, 1F arch 305 / 45 over the curved window, domes 172 and 215 |
| Sea side, high oblique / close | I03, I04, I08, I09, I13, I14, I16 (+ I02 looking up, I05 looking down) | same face and the pool court |
| Street-side elevation | I15, I18, I19, I20 | SOUTH EAST ELEVATION (p.6): stair tower with the double arched recess frame and stacked W01 / W13 / W26, 1F window with shutters and three beam ends, wavy parapet, domes 441 x 215 and 193 |
| Street close views | I01, I23, I24, I25, I26 | street edge of the GF plan (sheet03): dewaneya street face W11 / W12 (195 / 115 / 195) and the court frontage |
| West court | I17, I21, I22, I27 | sheet03 west court, entrance steps +0.15 to +1.00, dewaneya court face with its curved corner |

Orientation note: the side the plans label SEA VIEW is drawn on sheet p.8 "NORTH WEST ELEVATION" and the street side on
p.6 "SOUTH EAST ELEVATION" (matched by the printed openings: W15 / W17 / W18 cite NW, W01 / W13 / W14 / W26 cite SE in
T-150). T-127 / T-150 call the pool-court sea wall "east" in their local frames; same wall.

## 2. Findings: image -> plan element (one row per element; BOQ lines with units)

Status words per WORKFLOW_CONTROLS section 8: AGREES / DIFFERS / NOT IN THE DRAWING / NOT VISIBLE. No row changes a
quantity; every DIFFERS / NOT IN THE DRAWING row that touches a quantity keeps or puts that line HELD with this finding
as cause (or records an owner choice already made).

### 2.1 Domes (priority 1)

| Id | Element (register / task id) | Drawing | Images | Status | BOQ lines affected (unit) | Effect |
|---|---|---|---|---|---|---|
| F01 | Three domes: two on the 1F roof over the R221 openings (p.5 2F plan: west and sea-side, both on the B-B line), one on the 2F block (p.5 dashed circle over the maid room; p.6 441 wide x 215; p.8 215) | arch p.5 / p.6 / p.8; ST "DETAIL OF DOME" 442 / 190 / 10 covers only the two 1F-roof domes | 9 images: sea side I06 I07 I10 I11 I12 show the sea-side 1F dome (p.8 172) + the 2F dome; street side I15 I18 I19 I20 show the street-side 1F dome (p.6 193) + the 2F dome | AGREES with the drawings and with owner Q-27 A (3 domes: 2 on the 1F roof, 1 on the upper roof): each side shows its own 1F dome, so all three drawn domes are rendered (blue hemispheres) | dome concrete 6.78 m3 (freelancer), dome rebar, Sigma / exterior plaster "domes inside and outside" 181.81 m2 (freelancer), dome paint | NO CHANGE: the domes stay OUT of the BOQ by owner Q-29 (CLIENT CHANGE: no concrete domes, open skylight areas). The renders show the consultant's design before that change; they do NOT show "no domes". The main chat's note (4 images, "no dome") holds only for those 4 images; 9 of 27 show the domes. Owner's "no domes" stands on Q-29, not on these images |
| F02 | Dome ring beams B4 0.20 x 0.50 round each 1F-roof opening (owner Q-44 A: they stay) and the skylight closure (D-20) | ST 1F roof slab; D-20, D-28 open | none shows the openings uncovered | NOT VISIBLE (domes drawn closed) | ring beam B4 m3 (DRAWING-CONFIRMED, T-160), skylight glazing / frame (HELD D-20), membrane 0.20 upturn round each opening (Q-24) | none; D-20 stays HELD: renders cannot settle how the skylight is closed |
| F03 | The curved elements that are NOT domes: pool-court void in the 1F floor (B7 ring, 3.690 m2 inside the inner faces, T-127), curved GF glazing W03 6.57 (Q-38 A), curved 1F window W17 (outer arc 3.29, Q-39 C) | ST GF-roof slab (B7 ring, VOID on the 1F plan); sheet03 "657"; NW p.8 269 / 305 / 45 | I02 I03 I04 I05 I08 I09 I13 I14 I16 | AGREES: oval opening with a thick rounded edge in the 1F loggia floor over a round plunge pool; curved glazing at GF and 1F. The ST p.7 dome detail (442 / 190 / 10) belongs to the 1F-roof domes (R221), not to this ring | PL-03 pool-court soffit 12.834 m2 net of the void (T-127, accepted by the owner), W03 28.251 m2, W17 11.515 m2 (T-150) | none; renders corroborate the drawn opening (no dome over the pool court) |

### 2.2 Outdoor floors (priority 2)

| Id | Element | Drawing / rule | Images | Status | BOQ lines affected (unit) | Effect |
|---|---|---|---|---|---|---|
| F04 | Covered porch (about 4.60 x 4.10 = 19.181 m2, T-153; inside the west court 138.761 m2) | sheet03: at court level, no railing or level change drawn (owner 23:20: "in plan its the level") | I17 I22 I24 I27 | DIFFERS: rendered as a RAISED terrace behind a blue turned-baluster balustrade, floor in stone crazy paving | porch floor m2 (own line, finish HELD), court interlock m2 (porch deducted), balustrade lm (no line) | NO CHANGE: owner 23:20 decision governs (court level, area measured as its own line, finish HELD). The balustrade is NOT IN THE DRAWING: no railing line is added; if the owner builds the rendered terrace, a step / riser and a balustrade line would be new scope (owner) |
| F05 | Court street frontage: low wall + railing + free-standing round-topped number pier | sheet03 street edge of the court (830 printed); Q-65 C: street fence 8.20 lm = 5.70 solid + 2.50 gate, material HELD | I01 I15 I18 I19 I20 I23 I24 I25 | Re-read on sheet03 at 300 dpi: the court's street edge is drawn as a thin solid wall from the north corner for its upper part and a DASHED line (an opening, no leaf drawn) for the last part against the dewaneya corner, which fits Q-65's 5.70 solid + 2.50 gate. Position AGREES (the renders show the open path beside the dewaneya, no gate leaf); TYPE DIFFERS: the solid part is rendered as a LOW planter wall with a blue X railing on top, not a full-height block fence; the round-topped number pier at the gate jamb is NOT IN THE DRAWING (the wall is drawn uniform, no pier) | street fence block m2 / blocks (5.70 lm, height HELD), fence exterior plaster / paint m2, gate 2.50 m (pcs), fence railing lm (no line) | street fence stays HELD (Q-65) with this finding added: designer to give the fence section (height, railing, pier) |
| F06 | West court floor (138.761 m2 incl. porch 19.181 and E1 3.360, T-153) | owner rule: chalet court = interlock; owner 23:20 decision | I17 I22 I27 (court), I05 | DIFFERS from the render: natural-stone crazy paving | COURT interlock m2 = 138.761 - 19.181 porch (- footprints as measured) | NO CHANGE: line says "owner choice (interlock, cheaper and available), differs from render (crazy-paving stone)" |
| F07 | Entrance steps +0.15 -> +1.00 (rise 0.85 printed on p.6; width 2.80, T-150) and the main entrance door D-GF-07 (2.00 x 2.50 double, printed) | p.6 SE (voussoir arch, 85, door 250); sheet03; owner: outside stairs marble | I17 I21 I22 I27 (court), I18 I23 I24 (street) | DIFFERS on three points, none used: (a) risers: 5 visible in I21 / I27, 3-4 in I18 / I23 (the renders disagree with each other; drawing governs, UP-STAIR-002; 0.85 / 5 = 0.170 > the owner's 0.16 maximum, so the owner stair rule would give 6); (b) tread finish: grey stone with white nosing (I27) vs white (I21); (c) door: a SINGLE six-panel leaf (I21 I23 I24) where sheet03 / p.6 print a 2.00 DOUBLE door | entrance steps marble m2 (treads + risers), riser count (pcs), DOOR.MAIN_ENTRANCE 5.000 m2 DRAWING-CONFIRMED (T-150) | NO CHANGE: printed 200 x 250 double door and the drawn flight govern; marble by the owner rule. Door leaf count to the designer list (render single vs printed double) |
| F08 | Pool water and its edge (pool 3.50 dia, water 7.548 m2 is NOT a floor) and pool deck 7.605 m2 | sheet03 pool 350 dia; owner: pool deck HELD | I03 I04 I05 I08 I13 I14 | AGREES: round plunge pool under the 1F void; NOT VISIBLE: the deck around it (only a narrow white coping and a gravel strip show) | pool deck m2 (HELD), pool coping (no line) | none; pool deck stays HELD (owner not sure) |
| F09 | Front of the pool court on the sea side: opening SX-01 4.521 m under beam CB1 (T-150, filling HELD) | NW p.8: straight head at the 1F slab, curved glazing W03 430 high behind, no arch, no railing, no low wall | I03 I04 I06 I07 I08 I10 I11 I12 I13 I14 | DIFFERS: rendered as a ROUND-HEADED sculpted arch with a low curved wall (about knee height) and a blue X railing across the pool; the arch infill, the low wall and the railing are NOT IN THE DRAWING | SX-01 opening (filling HELD), pool-court wall plaster / paint and reveals m2 (T-154 / T-159), block m2 of the infill (none), railing lm (no line) | SX-01 stays HELD; finding added as cause: designer to say whether the arch infill, low wall and railing are built (they would add block, exterior plaster / paint and a railing line) |
| F10 | Beach in front of the sea face: sand, and a gravel band against the wall | sheet03: nothing drawn beyond the frontage | I06 I07 I10 I11 I12 I13 I14 I16 | NOT IN THE DRAWING (landscape outside the measured areas) | none in Urban scope | listed only |
| F16 | North side strip (side walk) beside the pool court (owner manual 1.50 x 15.97 = 23.955 m2; T-153 21.348, checker 21.021) | owner rule: sides never interlock, porcelain / ceramic, part of the house | I09 I13 I14 I16 | DIFFERS from the render: crazy-paving stone along the strip; location AGREES (strip beside the pool court, low end wall at the sea frontage, I07 I12 I14) | north side walk porcelain m2 (owner 23.955 / drawing 21.348 .. 21.021, T-157) | NO CHANGE: owner side rule governs; record "differs from render" |
| F17 | Side passage between the annex and the house (5.640 m2, Q-67 A conditional) | sheet03 | none | NOT VISIBLE | side passage porcelain / ceramic m2 | none |

### 2.3 Facade (priority 3)

| Id | Element | Drawing | Images | Status | BOQ lines affected (unit) | Effect |
|---|---|---|---|---|---|---|
| F11 | Entrance arch surround (voussoir blocks) | p.6 SE draws a block (voussoir / quoin) outline round the entrance arch | I17 I21 I22 I27 (grey cut stone), I01 I18 I23 I24 I25 (white stepped blocks) | AGREES in form; DIFFERS in material between the two render sets; material not printed | stone cladding of the arch (no line), exterior plaster / paint deduction m2 (T-159) | HELD: no stone line exists; designer / owner to name the surround material |
| F12 | Dewaneya street face: W11 / W12 1.95 each (sheet03 83 / 195 / 115 / 195 / 81), heights not printed (D-45) | the face is on NO elevation: p.6 cuts the dewaneya in section (+0.30, 400, roof +4.30, parapet 50) | I01 I15 I18 I19 I20 I23 I25 I26 | AGREES on two windows side by side; heights NOT taken (never scaled) | WINDOW.ALUMINIUM GF W11 / W12 (width 1.95 each, area HELD), facade net | W11 / W12 stay HELD on D-45 |
| F13 | Parapets and roof railings: wavy parapet with blue X railing on the 1F roofs (p.6 SE, p.8 NW 110), railing bay at the street end of the annex roof (p.7 SW); dewaneya street parapet straight 50 (p.6 section) | p.6 / p.7 / p.8 | all elevations; I23 I26 I27 for the dewaneya | AGREES on the 1F roofs; DIFFERS on the dewaneya: rendered with a WAVY parapet and an X railing along its whole street face and its curved court corner (I23 I26 I27) | parapet facade m2 (T-159 wavy parapets HELD 6.822 .. 13.261 m2), roof parapet block 104.25 lm (Q-65), railings lm (no line exists for any railing) | no quantity; railings are a missing BOQ category (all railings: 1F roof terraces, pool, porch, dewaneya roof) |
| F14 | 1F sea-side arched French windows W15 / W16 (155, fanlights) and the 1F arch round W17 | p.8 NW | I06 I07 I09 I10 I11 I12 I13 I14 I16 | AGREES (two arched windows with sunburst fanlights; W16 the twin of W15, still INFERRED in T-150) | W15 4.805 m2, W16 INFERRED 4.805 m2, W17 11.515 m2 | none (the render does not make W16 printed) |
| F15 | Louvred shutters (a pair per window) | drawn only on p.6 at the 1F street window W14; not drawn for W02, W11, W12 | I01 I06 I07 I10 I11 I12 I13 I14 I15 I16 I18 I19 I20 I23 I25 I26 | AGREES for W14 (drawn); NOT IN THE DRAWING for the saloon sea windows and the dewaneya windows | no shutter line in T-150 or V2.9 (pcs / m2) | new category for the owner: W14 shutters 2 leaves DRAWING-CONFIRMED (count only, size not printed); others NOT IN THE DRAWING |
| F18 | Timber beam ends (decorative) | p.6: three squares above the 1F window W14 | I01 I15 I18 I19 I20 I23 I25 I26 (1F three; dewaneya about five to seven) | AGREES at 1F (3); NOT IN THE DRAWING on the dewaneya face (no elevation of it) | no line (pcs) | listed only |
| F19 | Roof terrace floors: 1F sea-side terrace in front of W15 / W16, dewaneya roof | no finish drawn; roof finish is an open owner item (ROOF-FIN in the decisions queue) | I09 I13 I14 I16 I27 | NOT IN THE DRAWING (finish): rendered natural-stone crazy paving | roof membrane m2 (UP-WP-ROOF-001) unchanged; roof finish / protection m2 (no line, HELD) | listed for the owner's ROOF-FIN decision |
| F20 | Planting on the 1F roof by the tower, planter box at the 2F corner | none | I06 I07 I10 I11 I12 I15 I18 I19 I20 | NOT IN THE DRAWING | none (landscape); if built, roof planters would need membrane detail | listed only |
| F21 | Cladding vs plaster | no cladding printed on any elevation | all exterior images | AGREES: every wall face is white textured plaster (no stone or tile cladding except the arch surround F11) | exterior plaster / Sigma m2 (T-159 1,022.534 m2 measured), paint m2 | none |

### 2.4 Openings against the census (priority 4; T-150, 65 rows)

| Id | Element | Census | Images | Status | BOQ lines affected (unit) | Effect |
|---|---|---|---|---|---|---|
| F07c | Main entrance D-GF-07 | printed 2.00 x 2.50 double | I21 I23 I24 | DIFFERS (single leaf rendered) | DOOR.MAIN_ENTRANCE 5.000 m2 | see F07; designer list |
| F22 | Second round-headed arch with a blue reveal and a blue door on the porch / landing (left of the entrance flight) | probably D-GF-06 pantry door onto the +1.00 landing (1.00 x 2.20 ASSUMED); arched head not in the census | I17 I22 I27 | NOT IN THE DRAWING for the arched head; identity of the door PROBABLE only | DOOR.EXTERNAL.ALUMINIUM D-GF-06 2.200 m2 ASSUMED; reveal plaster / paint | none; listed for the designer |
| F23 | Saloon sea-side glazing W02 6.33 (sheet03 "633", height not printed; freelancer 6.33 x 4.30) | one opening | I06 I07 I10 I11 I12 I13 I14 I16 | DIFFERS: rendered as TWO separate gridded windows with a pier between them, each with a pair of shutters | WINDOW.ALUMINIUM GF W02 (width 6.33, area HELD); facade net; block / plaster reveals of a pier | W02 stays HELD (D-45) with this finding: designer to confirm one 6.33 glazing or two windows with a pier |
| F24 | Triangular pierced vents: six round the dewaneya court door (I27), three in the court wall (I17) | not in the census; p.7 SW draws the court-side doors without them | I17 I27 | NOT IN THE DRAWING | none (small decorative openings: plaster reveals) | listed only |
| F25 | Narrow vertical window between the 1F blocks on the sea face | W18 0.50 x 2.16 (NW 84 / 216 / 230) | I06 I07 I10 I11 I12 | AGREES | W18 1.080 m2 | none |
| F26 | Stair-tower windows (street face): W01 GF, W13 1F, W26 2F arched, inside a double arched recess frame | p.6 SE (5 / 72 / 5 bands, 170 crown, 230, 200, 185) | I01 I15 I18 I19 I20 I24 I25 | AGREES | W01 2.400, W13 2.760, W26 2.040 m2; recess-frame plaster lm / corners (Sigma corners measured in m.l) | none |

(F07c repeats F07 (c) in the opening table so the census reader sees it; it is not a separate finding.)

## 3. BOQ lines this review touches (no quantity changed)

| BOQ line | Quantity now | Status after this review | Cause added |
|---|---|---|---|
| Dome concrete / rebar / dome Sigma | excluded (Q-29 client change); freelancer 6.78 m3 and 181.81 m2 | unchanged, excluded | renders show the 3 drawn domes (design before the client change): F01 |
| Skylight closure at the 2 dome openings | HELD D-20 | HELD | F02 NOT VISIBLE |
| Court interlock | 138.761 m2 - porch 19.181 (T-153 areas, checker pending) | owner choice, differs from render | F06 |
| Porch floor | about 19.181 m2, finish HELD | unchanged | F04: render raised + balustrade; owner: court level |
| North side walk porcelain | owner 23.955 / drawing 21.348 (checker 21.021) m2 | unchanged (T-157 explains the 2.6 m2) | F16: render stone |
| Entrance steps marble | geometry from the drawing (T-111 / T-158) | unchanged | F07: render 3-5 risers, ignored |
| Main entrance door | 5.000 m2 DRAWING-CONFIRMED | unchanged; designer list | F07 (c) single leaf rendered |
| Street fence (Q-65) | 8.20 lm (5.70 + 2.50), height / material HELD | HELD | F05: low wall + railing + pier rendered |
| SX-01 pool-court sea opening | 4.521 m, filling HELD | HELD | F09: arch infill, low wall, railing rendered, not drawn |
| W02 saloon glazing | 6.33 m, area HELD | HELD | F23: two windows + pier rendered |
| W11 / W12, W15 / W16 / W17, W18, W01 / W13 / W26 | as T-150 | unchanged | F12, F14, F25, F26 AGREE |
| Railings (all) | no BOQ line | missing category | F04, F05, F09, F13 |
| Shutters | no BOQ line | missing category | F15 (W14 drawn; others not) |
| Roof terrace finish | no line (ROOF-FIN) | HELD | F19 |
| Arch surround cladding | no line | HELD | F11 |

Freelancer, engine and hand quantities are unchanged by this package: images are design intent and never a quantity source.

## 4. Proposals for the Lead (designer list; no new owner question)

No new owner question: the dome question is answered (Q-27 A three domes, Q-29 client change, Q-44 A ring beams), the
court / porch / sides by the 2026-10-21 owner rule and decisions, the fence by Q-65 (designer). Open owner questions
are at the limit. Proposed designer items (the Lead files them):
1. Street fence section: low planter wall + railing + number pier as rendered, or the 5.70 m solid fence (Q-65).
2. Pool-court sea front SX-01: arch infill, low curved wall and railing as rendered, or open straight-headed as on p.8.
3. Saloon sea glazing W02: one 6.33 m opening (sheet03) or two windows with a pier (renders); sill / head (D-45).
4. Main entrance: printed 2.00 double door vs the single leaf rendered.
5. Shutters and railings: which windows get louvred shutters (only W14 is drawn), and the railing type / length on each
   roof terrace, the porch, the pool and the dewaneya roof.
For the owner's package (information, not a question): the 27 images are renders, and 9 of them show the three drawn
domes; the "no domes" scope rests on his Q-29 client change, which these renders predate.

## 5. Learned

- The renders follow the issued elevations closely (domes, arched windows, wavy parapets, tower frame, beam ends, W18,
  the voussoir arch): where they differ, it is on things the elevations do not draw (the dewaneya street face, the saloon
  sea face and the pool-court front are all drawn in section or not at all) and on finishes the drawings never specify.
- Two render sets of the same entrance disagree with each other (white stepped surround vs grey stone voussoirs; 3-4 vs
  5 risers): renders cannot settle a count or a material even against each other.
- A 4-image sample can mislead: the main chat's "no dome" came from the court and pool-court views, which happen to show
  no roof.

## 6. Missing / not done

- No quantity was or can be derived from the images (section 8). Railings, shutters, beam ends, vents and roof-terrace
  finishes have no BOQ category yet.
- The court frontage was re-read on sheet03 at 300 dpi (PDF), not in the DXF; the fence height is printed nowhere read.
- Dewaneya court face (I27): sheet03 at 300 dpi draws D-GF-01, a plain wall piece, a column and the curved corner;
  no window there, so the render's single door AGREES and the census needs no new row.
- Image capture date in the file title (2026-06-15) is the messaging export name, not a render date.
