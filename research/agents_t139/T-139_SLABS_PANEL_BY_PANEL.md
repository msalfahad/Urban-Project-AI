# T-139 Alsenan roof slabs panel by panel, per floor, with openings and the slab under the winders (NO REPO CODE)

Worker 1 (structural lane), 2026-10-21. Development villa, not an accuracy claim. Nothing is wired and no released
quantity changes: a checked piece for the V3.0 candidate (lane I).

Sources (Drive "Alsenan chalet project", scratchpad copies, never committed): "ST7757 dxf.dxf" (sha256
9f9d1179...38079 = manifest) and "ST7757.pdf" (sha256 74da1523...37e3): p.4 GROUND FLOOR ROOF SLAB, p.5 FIRST FLOOR ROOF
SLAB, p.6 SECOND FLOOR ROOF SLAB (read at 220 dpi), p.8 general notes, p.3 dome detail, p.16 typical stair details.
Independent second source for the panel edges: the beam member register (research/agents_t110, merged), its
centrelines and schedule widths. Rules: URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1, owner Q-44 A (dome openings stay
open, ring beam stays), Q-62 A cond (stair / landing / slab concrete once), Q-61 C, UP-QTY-STATUS-001.

Files: `slab_faces.py` (polygonises the drawn edge lines of the three sheets; decides nothing), `slab_ledger.py` (one
decision per face, made by eye on the drawing; totals and re-add checks), `PANELS.csv` (every face of the three sheets,
402 rows, 62 slab rows), `ledger_summary.json`, `reconcile_engine.py` (hand rows against the engine's panel table).
Repeat: `python -I slab_faces.py <ST.dxf> faces.json && python -I slab_ledger.py faces.json <dir> && python -I
reconcile_engine.py <dir>/PANELS.csv research/urban_engine_m5_concrete_reconciliation/06A_SLAB_PANELS.csv`.

## 1. Result in engineering terms (suspended slabs, concrete m3)

| Slab (sheet) | Hand panels | Hand m2 | Hand m3 | Engine (route G panel table = release register) | Freelancer | Hand vs freelancer |
|---|---|---|---|---|---|---|
| GF roof (1F floor), p.4 | 33 | 206.685 | **33.069** | 33.449 (+0.380, +1.15 %) | 33.120 (207.00 m2 x 0.16) | -0.051 (-0.15 %) |
| 1F roof (2F floor), p.5 | 22 | 123.479 | **19.757** | 20.005 (+0.249, +1.26 %) + HELD face 2.740 | 19.200 (120.00 m2 x 0.16) | +0.557 (+2.90 %) |
| 2F roof (tank / stair core), p.6 | 7 | 44.885 (31.250 at 0.16 + 13.635 at 0.18) | **7.454** | 7.512 (+0.057, +0.77 %) | 7.497 (31.84 x 0.16 + 13.35 x 0.18) | -0.043 (-0.57 %) |
| **Total** | 62 | 375.048 | **60.280** | 60.966 (+0.686, +1.14 %) | 59.817 | **+0.463 (+0.77 %)** |

Engine vs freelancer today: 60.966 vs 59.817 m3, +1.149 (+1.92 %). Every hand panel matches one engine panel to within
0.002 m2; the whole engine excess (0.686 m3) is 13 faces that are not slab (section 3). The held 2.740 m3 face is
settled as NOT slab (section 4). Held, never 0: the slab under the main-stair winders (0.230 .. 0.250 m3, section 5).

## 2. How each panel was measured (one row per face in PANELS.csv)

- **Outline**: the structural sheets print no panel dimension chains (p.4-6 note "THE BUILDER TO WORK WITH STATED
  DIMENSIONS NOT TO SCALE DRAWING"), so each panel is the drawn face between beam faces. Checks against printed values:
  (a) the GF plate spans x 42.093 .. 73.463 = **31.370 m = printed "NEIGHBOUR 31.37"**; (b) the pool-court bay
  re-adds to T-127's printed-dimension bay 4.591 m2 (void 3.690 + B7 ring 0.666 + corners 0.234 = 4.5908, faces
  GF-040 + 034 + 035 + 036 + 059 + 060 + 061); (c) five panels re-derived from the independent beam register (T-110
  centreline +- schedule width / 2), all equal to the mm:

| Panel | Bounding members (register centreline, width) | Clear sizes | m2 | t | m3 |
|---|---|---|---|---|---|
| GF-032 (B8 bay) | B16 x 67.562 (0.30), B8 x 71.314 (0.20), B17 y 45.602 (0.45), B24 y 49.599 (0.50) | 3.500 x 3.520 | 12.3205 | 0.16 note | 1.9713 |
| GF-137 (west wing) | B4 x 46.392 / 49.594 (0.20), CB7 y 36.449, CB6 y 41.148 (0.20) | 3.000 x 4.500 - column notch 0.015 | 13.4850 | 0.16 note | 2.1576 |
| GF-098 (CB4 bay) | CB5 x 52.793 (0.20), CB4 x 57.193 (0.20), B1 y 41.148 (0.20), B20 y 45.148 (0.40) | 4.200 x 3.700 | 15.5400 | 0.16 note | 2.4864 |
| 1F-084 ('T 16') | CB13 x 18.518 (0.30), B18 x 23.143 (0.35), CB11 y 37.998 (0.30), B4 y 43.098 (0.20) | 4.300 x 4.850 | 20.8550 | 0.16 tag | 3.3368 |
| 2F-013 (tank, 'T 18') | B3 x -17.555 / -15.555 (0.20), B1 y 46.548, B3 y 49.748 (0.20) | 1.800 x 3.000 | 5.4000 | 0.18 tag | 0.9720 |

- **Thickness**: printed panel tag where drawn ('T 16': GF-078, GF-141, 1F-084; 'T 18 (T&B)': 2F-011, 2F-013); every
  other panel by **ST p.8 general note 18, read by eye this run: "سمك بلاطات الأسقف العادية 16 سم ما لم يذكر خلاف ذلك"
  (ordinary roof slabs 16 cm unless otherwise stated)**. This is the human reading the M5 audit asked for (RFI-M5-16:
  "printed twice, read by machine only"). No panel uses a default the drawing does not print.
- **Beams not in the slab**: each panel stops at the beam faces (URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1); the beam
  lines take D - t over their own footprint (T-110 / concrete ledger V3).
- **Openings deducted only where drawn**: GF 'Open to below' X box 3.240 m2 (GF-048) and the pool-court VOID 3.690 m2
  inside the B7 ring (GF-040, = verifier's T-121 / T-127 3.689); GF light well with the round stair 23.237 m2 (GF-130:
  VOID X + stair, the stair concrete is the stair ledger's); 1F X box 3.240 m2 (1F-036); 1F dome openings r 2.2111 m
  (Q-44 A: skylights; p.3 dome detail diameter 442 = the inner circle) with the B4 ring band r 2.2111 .. 2.4111 in the
  beam register (BM-1F-028 / -039). 2F: no opening (2F-025 is a closed box with bars both ways).
- **Drop panels / level steps**: no drop panel is drawn. Sunken slabs (hatch ANSI31 scale 2000 = legend "Sunken slab"):
  GF-015, GF-016, GF-081, GF-128, GF-141 (19.396 m2) and 1F-018 (5.400 m2), counted at the panel thickness; the drop
  depth and the step edges are not printed, so the step-edge concrete is **not measured** (listed, not 0).
- **Dome-square corners** (outside the ring r 2.4111, inside the beams): west dome 0.4677 / 0.3525 / 0.3517 / 0.4668,
  east dome 0.5814 / 0.5823 / 0.5223 / 0.5214 m2 = 3.846 m2, 0.615 m3, slab at the note thickness (no bar label is
  drawn in them; geometry outside every beam footprint). Pool-court bay corners 0.2343 m2 (T-127 called them "beam
  zone"; they are outside every beam footprint, so slab here; 0.037 m3 either way).

## 3. Engine lines that differ from the hand panels (every one over 0.05 m3 explained; all 13 below)

| Engine panel | Floor | m2 | m3 | What the drawing shows | Who is right |
|---|---|---|---|---|---|
| f9b0c2 | GF | 0.857 (1.072 less 0.14) | 0.137 | 0.20 strip north of B20 round the street corner: beam register BM-GF-058 HELD (designer D-05), no tag, no bars | HAND (not slab; held in the beam lane) |
| b41145 | GF | 0.740 | 0.118 | **CB5 span 2** (2-span schedule, printed spans 2.5 / 4.5 m; second CB5 label on it): a beam band 0.20 x 3.70 | HAND (beam); **beam register gap**: 0.20 x 0.40 x 3.70 = 0.296 m3 in no beam row |
| 02047c | GF | 0.490 | 0.078 | outer west strip 0.20 (BM-GF-061 HELD, D-26) | HAND (not slab) |
| 57ec39 | GF | 0.201 | 0.032 | piece of the B7 ring band in the pool-court bay (the contested ring piece BM-GF-060) | HAND (ring = beam) |
| 2597c9 / cf20e8 / ae2689 | GF / 1F / 2F | 0.0866 each | 0.014 each | the drafting break mark beside the stair (a wavy 0.10 x 1.25 sliver outside B2 / B15) | HAND (no concrete) |
| 4c7ca8 | 1F | 0.620 (0.890 less 0.27) | 0.099 | south-east box / 0.10 strip outside CB12 (BM-1F-035 / -038 HELD) | HAND |
| e100a6 | 1F | 0.385 | 0.062 | rounded box outside CB12 at mid length (BM-1F-037 HELD, D-26) | HAND |
| cfe47b | 1F | 0.203 | 0.033 | strip outside CB12, north part (BM-1F-036 HELD) | HAND |
| 785741 | 1F | 0.160 (0.366 less 0.206) | 0.026 | 0.20 strip north of B23, east piece (BM-1F-033 HELD) | HAND |
| d54a5a | 1F | 0.099 | 0.016 | unlabelled span past a column east of the stair (BM-1F-032 HELD, D-04) | HAND |
| 5a1792 | 2F | 0.272 | 0.044 | 0.10 strip west of the B15 bearing-wall band: no tag, no bars, depth not printed | HAND (held, not slab) |
| **sum** | | 4.288 m2 | **0.686** | = engine 60.966 - hand 60.280 | |

General engine defect (every villa, for lane I / route G): a slab face is released without slab evidence. Narrow
bands outside the outer beams (edge strips, boxes), unlabelled beam spans and break-mark slivers become slab panels at
the project default; when the beam register later releases those bands, the same plan area is concrete twice. Proposed
release test for the V3.0 slab line: a face is slab only if it carries a slab bar label ("/m") or a thickness tag, or
is a corner / panel whose every edge is a beam, column or opening face; any face under 0.45 m wide without bars goes
to the beam / edge family (HELD there when no section prints it). On Alsenan this moves 0.686 m3 out and nothing in.

## 4. The held 2.740 m3 face (release register U-C:SLABS:1F SITE-...b845e1e78b1f74a8, reason SLAB_STAIR_ZONE)

Settled from the drawings, NOT slab: it is the west dome square of the 1F roof (17.13 m2 x 0.16). The sheet that
settles it is ST p.5: the circles r 2.2111 / 2.4111 m about the dome centre with four "SEE DETAIL" labels (the radial
lines the census read as winder treads are the dome drawing), and p.3 DETAIL OF DOME: diameter 442 = the inner circle.
With owner Q-44 A the inside is an open skylight (14.982 m2 here) and the band 2.2111 .. 2.4111 is the B4 ring beam
(1.511 m2, beam register BM-1F-028); its four corners (1.639 m2, 0.262 m3) are already measured slab panels (engine
and hand). Proposal: close the line as NOT_SLAB_DOME_OPENING (the M5 audit dropped it, decision D-03; the release
register still lists it UNRESOLVED). No slab volume is lost: hand and engine both carry the corners.

## 5. Slab under the main-stair winders and the T 16 landings (Q-62 A cond, counted once)

- **Winder slab: stays HELD, candidate 0.230 .. 0.250 m3** (T-111). Sheets searched: ST p.4 (the GF->1F stair zone
  carries one 'T 16' tag and 8d16/m bars over the whole zone, no soffit for the turn), ST p.5 (same for 1F->2F), ST p.16
  (TYPICAL STEEL LAYOUT - STAIR SECTION and TYPICAL DETAIL OF STAIR BEAM: straight flights and a flat landing only,
  N.T.S., waist written "THICK" without a value), architectural section A-A (T-111). The low end 0.2304 = the turn plan
  1.20 x 1.20 x the zone's printed 'T 16' (horizontal projection); the sloped soffit is not drawn. It is in no slab
  line (the turn lies inside face GF-025, which neither the engine nor this ledger counts as slab) and in no stair
  line: it stays a HELD line for the stair ledger (designer detail point already open in T-111). No owner question.
- **Stair zones**: GF-025 (10.725 m2) and 1F-016 (11.265 m2) contain the flights, the turn and the half landings
  (T 16). No engine slab line includes them (route G panel table: both excluded, overlay faces 10.70 / 10.72 m2) and
  no hand slab row does: the half landings (1.44 m2 and 3.00 m2, T 16) are counted once, in the stair ledger.
- **Floor arrival landings** (2.50 x 1.95 each): 1F arrival = B20 band 0.40 + 1.55 m of panel GF-077; 2F arrival =
  B23 band 0.45 + 1.50 m of panel 1F-062. They are slab (and beam) only; the stair ledger counts no floor landing and
  deducts its arrival wedges (0.030 + 0.030 m3) to these slabs. Counted once.
- **Round stair**: its flights and corner landing lie inside the light-well face GF-130 and strips GF-131 / 132 / 145
  (stair ledger); the wedge GF-146 (0.456 m2) east of the flight edge, where the tread lines stop, is slab (engine and
  hand agree).

## 6. Owner manual method and drawing-derived method side by side

| Item | Owner / freelancer manual method | Drawing-derived (this ledger) | Difference explained |
|---|---|---|---|
| GF roof | one area 207.00 m2 x 0.16 = 33.120 | 33 panels 206.685 m2, all 0.16 (5 tags / note 18) = 33.069 | -0.315 m2: his lump area has no breakdown; within 0.15 % |
| 1F roof | 120.00 m2 x 0.16 = 19.200 (a 0.4 x 0.15 x 1.35 deduction written with count 0) | 22 panels 123.479 m2 = 19.757 | +3.479 m2. Not traceable (lump); it is close to the eight dome-square corners 3.846 m2, which the drawing shows as slab between the beams outside the ring. Proposal: HAND_RIGHT if he left them out (corners are drawn); else UNRESOLVED |
| 2F roof | 31.84 x 0.16 + 13.35 x 0.18 = 7.497 | 31.250 x 0.16 + 13.635 x 0.18 = 7.454 | tank panels drawn 2.50 x 3.30 + 1.80 x 3.00 = 13.635 (his 13.35, -0.285); other panels 31.25 (his 31.84, +0.59) |
| Thickness | 'S.S 16 CM' everywhere except the tank 18 | tags + note 18 (read by eye); tank 'T 18 (T&B)' | same values |

## 7. Who is right (proposals for the verifier)

- Engine slab 60.966 vs hand 60.280 m3 (+0.686, +1.14 %): **HAND_RIGHT** on 13 faces (section 3), each with the
  drawing evidence; ENGINE_RIGHT on the 62 matched panels (areas equal within 0.002 m2, thicknesses equal).
- Hand 60.280 vs freelancer 59.817 m3 (+0.463, +0.77 %): GF -0.15 % and 2F -0.57 % **RULE_DIFFERENCE / within
  tolerance** (lump areas); 1F +2.90 % **UNRESOLVED** (lump 120.00 m2), candidate cause the dome corners (HAND_RIGHT on
  the drawing if so).
- Held 2.740 m3 face: **settled NOT slab** (dome opening + ring beam; p.5 + p.3 + Q-44 A).
- Beam register gap (lane S / I): CB5 span 2 (0.20 x 0.40 x 3.70, 0.296 m3) is in no beam row and the engine measures
  its band as slab.

## 8. What we learned (every villa)

1. The project default thickness is printed in the general notes, not on the slab sheets: read it once by eye (p.8
   note 18) and cite it; tags on the plan override it panel by panel.
2. A slab face is not a slab panel until it carries slab evidence: edge strips, boxes outside the outer beams, an
   unlabelled beam span and a drafting break mark all close a face and were measured as slab (0.686 m3 here).
3. A second label of a continuous beam on another span (CB5 twice) is a span, not a duplicate: the 2-span schedule
   (2.5 / 4.5 m) says so; the band otherwise falls into the slab line.
4. The upper slab sheet repeats the lower roof outline around a small core (2F sheet): only the core is that slab.
5. Dome squares split into opening, ring beam and four slab corners; the corners are real slab in both engine and hand.

## 9. Held / not measured (never 0)

- Slab under the winders: HELD 0.230 .. 0.250 m3 (designer detail; no soffit on p.4 / p.5 / p.16).
- Sunken-slab step edges (GF 5 panels 19.396 m2, 1F 1 panel 5.400 m2): drop depth not printed; edges not measured.
- Edge strips and boxes (GF 1.562 m2, 1F 3.884 m2, 2F 0.272 m2): not slab; held in the beam lane (D-05 / D-26).
- Pool-court contested ring piece BM-GF-060 and CB3 / 'B3 (With Stair)' BM-GF-057: beam lane, HELD (Q-61 C).
