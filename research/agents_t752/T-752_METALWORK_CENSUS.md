# T-752 B13-07 special metalwork: missing-family census (development villa; method every villa)

Worker 1 (lane S), 2026-11-13. Research only (`METALWORK_CENSUS_T752_V1`, `t752_metalwork.py`); nothing wired, no
candidate line moved, released default untouched. No drawing, workbook, client name or coordinate in this folder;
files are named by their Drive folder 'Alsenan chalet project' and title, entities by DXF handle.

## 1. Physical element (ERS s.2.1)

B13-07 = a fixed, fabricated, drawn piece that is not a door, window, rebar, railing run, shutter or fence gate: a
canopy or pergola (plan m2 of the outline, lm of members, pcs), a louvre screen (face m2), a gate (pcs), a handrail
frame (lm), a projecting member (pcs + visible projection lm). kg only where a section is PRINTED, the member length
is measured and a mass per metre is printed or cited from a named table: all three, or kg HELD (never a default kg/m,
never kg from m2). Items another family already counts are EXCLUDED by id (counted once).

## 2. Sources read (every sheet of the set; absence is claimed only after all were read, R-RAIL-2)

| Source (Drive 'Alsenan chalet project') | Read how | Found |
|---|---|---|
| P7757_DXF_COMPRESSED.zip (GF / 1F / 2F plans, SE + NW elevations) | ezdxf by layer and handle; overhead layer '2' plotted per plan; text scan incl. blocks | 3 beam-end stubs (1F) + 3 end squares (SE); 0 metalwork words in 177 texts |
| ST7757 dxf.dxf (all structural sheets) | text scan incl. blocks | RC members only; 0 steel sections in 1934 texts |
| sheet03 (GF), Pages_01-02 (area plans), Pages_05-06 (2F plan, SE), Pages_07-08 (SW, NW), sheet09 (NE), sheet10 (A-A), Pages_11-12 (B-B, FENCE PLAN / ELEVATION / SECTION) | rendered 110-200 dpi, read by eye | 6 end squares on the annex face (p.12); beam ends in side view on p.7, p.9, B-B; no canopy, pergola, screen, frame; area plans list no covered area |
| Freelancer: aluminium (59 rows), buildings (230), paint, plaster / Sigma workbooks | openpyxl / xlrd keyword scan | no metalwork, canopy, pergola, timber or beam-end row; FIN workbook (23.6 MB) not readable (connector limit) |

## 3. Census (own units; nothing VERIFIED)

| Item | Floor | Kind | pcs | Geometry | kg | Status | Evidence |
|---|---|---|---|---|---|---|---|
| MW-1F-SE-BE | 1F street (SE) face above W14 | projecting member (beam end) | **3** DC | section drawn 0.10 x 0.10, visible projection 0.30 each = **0.900 lm** DC (to the 0.20 m facade outline C49); centres 0.80 m; level by DXF +8.788 .. +8.888 (not printed; 0.288 above the printed W14 head +8.50) | HELD | count + visible geometry DC; whole length, material, section designation, fixing HELD | 1F plan layer 2: C4A+C51+C52, C4B+C4F+C50, C4C+C4D+C4E; SE squares 21F8/21FA/21FC/21FF, 21FB/21FD/21FE/2200, 21F6/21F7/21F9/2201 |
| MW-GF-ANX-BE | annex street face, 3 over W11 + 3 over W12 | projecting member (beam end) | **6** DC (raster count) | HELD (raster only; GF plan draws no stub) | HELD | count DC; every size HELD | Pages_11-12 p.12 FENCE ELEVATION |

Totals: projecting members 9 pcs (all held in kg; 0.900 lm visible projection measured on 3 of them).
Checks run on the DXF: plan vs elevation agree (count 3 = 3, spacing 0.80 / 0.80 = 0.80 / 0.80, width 0.10 = 0.10);
completeness: the 9 stub lines are every overhead line within 2 m outside C49 on that face, the 12 square sides every
0.10 m layer-1 line in that height band (two far-away elevation lines were caught by the first run and excluded by the
2 m bound: they are in the elevations, not the plan).

NOT_DRAWN (value None, sheets of s.2): canopy; pergola; louvre screen other than the shutters; handrail frame other
than the railing runs; gate other than G-01 / G-02.

EXCLUDED by id (owned, not measured): RL-01 .. RL-12 (B7-09 / B7-11, T-164 / T-393 / T-480); shutters SH-W14, SH-W11,
SH-W12 (T-164); G-01, G-02 = D-GF-15 (B13-04, T-361 / T-400).

Not metalwork (cross-trade, named owner): 0.20 m facade-projection outline B3C / B3D / C49 (facade, T-159 / T-162);
0.50 m boxes on the annex roof (SE 2428 / 2429 / 242A / 242B / 2426) and 1F roof (NW 2563 / 27B4 / 27B5) = parapets seen
beyond (0.50 m = parapet height, T-162); NW pool-court arch glazing (layer W, windows); stools 174-177 (loose,
T-753); 'mecvent' A7A / A82 / A85 (text-only blocks, B12-04 label, never a unit); the 1.80 x 1.80 lift shaft.

## 4. Engine vs freelancer, verdict proposals

Candidate: no B13-07 line (before) -> census only (after; nothing wired). Freelancer: no row in the four readable
workbooks. Beam ends 9 pcs: HAND_FOUND (drawn, no freelancer row, no family); trade and material UNRESOLVED (render
T-161 F18 calls them timber, a render never makes a material: B13-07 only if metal). Canopy / pergola: ENGINE_RIGHT
that none is drawn (T-692 had read only the NE elevation; now every sheet).

## 5. Rules (research, every villa) and tests

- R-T752-1 a metalwork kg needs a printed section, a measured length and a sourced kg/m; otherwise HELD naming each
  missing piece; never kg from m2, never a default kg/m.
- R-T752-2 a raster-only item is counted, never scaled; geometry only from CAD or printed figures; units guarded
  (member > 60 m, outline > 400 m2, kg/m > 500 refused).
- R-T752-3 projecting members are confirmed by plan stubs vs elevation ends (count, spacing, width); the visible
  projection is measured to the drawn face, the embedded length stays HELD.
- R-T752-4 an item another family counts is EXCLUDED by id; NOT_DRAWN needs the list of sheets searched.

tests/t752_metalwork: 18 pass (synthetic villa N752: canopy with printed SHS section 4.500 m2 / 10.500 lm / 123.165 kg;
canopy without section kg HELD; rotation / mirror; raster pergola; beam ends agree / disagree; mm as m, kg/m without
source, held count 0, double count, NOT_DRAWN without sheets refused).

## 6. Designer items proposed (the Lead adds them to DESIGNER_QUESTIONS.md)

- D-M1 beam ends (1F SE 3 pcs, annex 6 pcs): material, section, back-span / embedment, fixing and finish; annex
  projection and size (drawn on p.12 only, not in any plan). Affects B13-07 (or carpentry) pcs / kg; no m3.

## 7. Lessons-register row proposed

| 2026-11-13 | T-752 | T-692 marked B13-07 "no label found" after one elevation; every sheet read finds no canopy / pergola but 9
drawn beam ends no family owned | absence needs every sheet and the overhead plan layer; a drawn piece with no family is
listed with its count even when its trade is unknown | R-T752-1..4, tests/t752_metalwork | PROPOSED |

Checker Gate A recount proposal: (1) 1F plan stub C4B + C4F + C50 (0.10 x 0.30) and SE square 21FB / 21FD / 21FE /
2200 (0.10 x 0.10), spacing 0.80 to its neighbours; (2) p.12 six squares over W11 / W12.
