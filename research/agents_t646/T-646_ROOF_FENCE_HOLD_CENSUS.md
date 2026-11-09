# T-646 B13 roof layers + fence finishes: the 43 HELD-blank lines to a quantity or a named cause (research, unwired)

Worker 2, lane A, 2026-11-09. Files: `t646_rules.py` (R-T646-1, every villa), `t646_alsenan.py` (builder, repository
files only, sha256-pinned), `out/ROOF_FENCE_HOLD_CENSUS_T646.json` / `.md` (one row per line), `tests/t646/` (10 tests).
No engine, rule / knowledge version, registry, frozen or candidate file changed; nothing wired or released.

## 1. Physical elements and evidence (ERS s.2.1 / s.2.2)

- ROOF BUILD-UP: on each roof, from the slab up: screed to falls (one volume, register SCREED TO FALLS), membrane (B8-06,
  T-626, not this row), insulation, protection, walking finish. ONE roof plan area per roof = the released
  FIN.ROOF.FINISH line (register ROOF BUILD-UP LAYERS): ROOF-430 54.9203, TERRACE-550 31.643, ROOF-970 115.65646,
  POOLCOURT-550 4.519172 = **206.738932 m2**.
- FENCE: each face of the site wall above N.G. per side (T-404 faces, Checker AGREE), and the plaster / paint layers on
  each face.
- Own read this run: architectural DXF (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip -> sha256 ab54dd55,
  decoded into .work/private only): all **675** TEXT / MTEXT / ATTRIB (model space + blocks) searched for insulation /
  screed / membrane / protection / tile / plaster / paint / sigma / render / finish / coping / cement / mortar / slope /
  fall / thickness / cm / mm and the Arabic terms: **0 hits** (agrees with T-321 and T-517). Hatches: layer 3 LINE 14,
  NET 11 (the finish extents already measured), no fence-face hatch.
- Owner manual method beside the drawing method: Q-41 'roof -> screed' (own line, thickness not given); Q-45 roof bed
  'thickness from the falls'; OWNER_NOTES_SIGMA item 3 (boundary wall in Sigma: not answered); Q-34 (top roof parked);
  Q-63 C (sea element held). No owner rule names a roof insulation, a separate protection layer or a fence finish.

## 2. Result (scope = T-630 per_line, B13 HELD with no bound in the seven codes: 43 lines, matches the row)

| Class | Lines | What happens |
|---|---|---|
| R_SCREED_BOUNDED | 3 | FIN.ROOF.SCREED HELD blank -> HELD **AT_LEAST .. OPEN**: TERRACE-550 2.512672, ROOF-430 3.324832, ROOF-970 4.791492 = **10.628996 m3** (scope ASSUMED - OWNER-APPROVED Q-41; fall 1 % printed; outlets drawn; t0 unprinted D-39 keeps the high end OPEN) |
| R_LAYER_UNPRINTED | 8 | insulation x4 + protection x4 (430, 550, 970, pool court): blank. Insulation printed nowhere, no owner rule (pool 'INSULATION' ST p.7 not extended, ERS s.3). Protection: Q-41 gives ONE screed line ('falls / protection'); a second layer would count it twice. Area if present shown beside = the roof finish area |
| R_ZONE_HELD | 9 | ROOF-1390 all 4 layers (Q-34 parked to 12-13 Nov; beside 49.665 m2 inside the parapet faces, dome 15.275 Q-29); POOLCOURT-550 screed (no outlet / slope drawn, T-494 RFI); LEDGE all 4 (covered zone, no hatch, at most 0.639573) |
| F_FACE_HELD | 7 | street outside / plot (profile undimensioned, at most 15.37 / 14.84), G-01 stop-end (at most 0.53), sea x2 (Q-63 C, 6.36 comparison only), passage x2 (no height printed) |
| F_LAYER_HELD | 16 | plaster x8 + paint x8: no finish printed on p.12 / anywhere, owner's site-wall finish scope open (Sigma item 3); at most the face: north 83.1305 + 82.0705 per layer = **330.402 m2** on the released faces; the house plaster + Sigma system is not carried to a site wall (R-T404-5) |

Hand checks (independent of the code): 2.7176 - (32.721 - 31.643) x 0.1901 = 2.7176 - 0.204928 = 2.512672;
3.4008 - (55.5603 - 54.9203) x 0.1187 = 3.4008 - 0.07597 = 3.32483; 8.089 - (146.532 - 115.65646) x 0.1068 = 8.089 -
3.297508 = 4.791492. V = the screed above the t0 plane under the EIKONAL (lowest) rise model of T-221 / T-321 (MERGED
59c82a05) on the falls outline; the removed strip (TERRACE finish hatch short of the wall faces 1.078; ROOF-430 D band
0.640; ROOF-970 two dome footprints 30.718 + D band 0.1575) holds at most its area x the highest rise. Each AT_LEAST
moves by area x t0 once t0 is printed: +0.316 / +0.549 / +1.157 m3 per cm.

Why the Lead's 'layer = the finish area where printed' gives no released m2 here: no layer is printed on any sheet, and
the screed's thickness is not printed; releasing insulation, protection or a fence finish would be an invented scope
(no-assumptions rule). Why the fence layers are not released 'on the released faces': the faces are geometry
(DRAWING-CONFIRMED), the layers on them are scope; scope needs a print or the owner.

## 3. Freelancer and who is right

Roof: one line 285.00 m2 (membrane basis, cells not read; T-071 / T-321): no screed / insulation / protection split ->
UNRESOLVED, nothing comparable in m3. Fence: plaster + Sigma 107.24 m2 at 2.40 on three faces (T-404): height
ENGINE_RIGHT (2.65 printed), scope RULE_DIFFERENCE (which faces are finished: the owner item).

## 4. For the Lead / Checker

- Effect if lane I wires the 3 fix rows after the Checker: B13 m3 HELD blank 6 -> 3 (3 bounded, low 10.628996, OPEN);
  B13 m2 HELD blank in these codes 37 stays 37, every one with a named cause (no released m2 moves).
- OWNER PACKAGE (not a new question; ERS 2.7 — already with the owner since 2026-10-21): fence finish scope (which faces,
  plaster + Sigma or other, the top). At stake 330.402 m2 of layers on the north faces alone (2 x 165.201).
- DESIGNER (rfi/B, nothing sent): D-39 t0 at the outlets + insulation / protection specification; street fence top profile.
- Checker re-measure picks: ROOF-430 screed bound (T-321 falls on the D-band strip) and F-NORTH plot face 30.97 x 2.65.

## 5. Lessons row (proposed, ERS s.7)

| 2026-11-09 | 18 roof-layer lines sat HELD blank although the screed's existence (Q-41), fall (1 %) and outlets were known | a quantity was held whole because one input (t0) was missing | R-T646-1: a layer with established scope and a missing thickness carries the part the drawings fix as AT_LEAST (above-t0 on the one roof area, lowest rise model); a layer with no print and no rule stays blank with its area beside (every villa) | tests/t646 (R646 by hand; adverse: unprinted thickness, mm as m, membrane row, bound > outline, no outlet, house Sigma on a site wall, held as 0) | proposed |
