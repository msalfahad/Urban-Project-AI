# T-517 B8-06 pool-court slab: the build-up above the membrane, layer by layer (research, unwired)

Worker 2 (lane A), 2026-11-05. Files: `t517_poolcourt_buildup.py` (rules R-T517-1 .. 6, any villa), `t517_inputs.py`
(training-villa declarations, T-494 rows sha256-pinned), `t517_alsenan.py` (table + census check),
`tests/t517_poolcourt_buildup/` (20 tests). No engine, method, rule / knowledge version, registry, master or candidate
file changed; no candidate (V3.0.58) or released (V2.9 + route G) line moves. Drawings by Drive title / handle only
("Alsenan chalet project": P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256 ab54dd55..., decoded this run).

## 1. Physical element and evidence (ERS s.2.1, hierarchy)

The open-sky slab top round the oval void at +5.50 (POOLCOURT-550, 4.906867 m2 membrane plan, T-494, Checker 4.9069)
is a ROOF by function (no door, exposed: WP_APPLICABILITY_RULES_V1). Physically it is built as every other roof of the
candidate: screed to falls (the one falls volume), membrane (T-494 / T-507 lines, cross-reference only), insulation,
protection, walking finish (T-321 ledger / R-T328-1). The candidate carries the membrane only: the other four rows were
a silent omission.

Level 1 (drawing), own reads this run: all 675 TEXT / MTEXT / ATTRIB entities of the architectural DXF (model space +
blocks), searched for screed / insulation / membrane / protection / tile / porcelain / marble / mortar / cement / sand /
bed / slope / falls / 1:n / cm / mm and the Arabic terms: hits are '1:100' and room / sheet titles only. Within 0.5 m
of the zone: VOID label BBF, level 124F / 1251 '+5.50', and the designer finish hatches **1250 + 1253 (layer 3,
pattern LINE)** = the layer and pattern of the TERRACE-550 hatches AE0 / D1A / 1252 that carry FIN.ROOF.FINISH (1252
lies wholly outside this zone: no double count). Sanitary sheet 2: no outlet / slope on this slab (T-494 RFI). Section
A-A: constant drafting band (T-321). Level 3 (owner): Q-41 (roofs carry a screed, own line, thickness not given);
Q-45 ('roof depending on slope and manhole each 1 m 0.5 %': needs a drain); register 'SCREED TO FALLS' (one volume, a
finish bed above it only if printed). OWNER_RULE_OUTDOOR_FLOORS covers ground-level outdoor areas, not roofs.

## 2. Layer table (V3.0.58 basis; statuses WORKFLOW_CONTROLS s.5)

| Zone | Layer (code, trade) | Area m2 (source) | Thickness | Quantity | State / missing |
|---|---|---|---|---|---|
| open sky | FALLS_SCREED (FIN.ROOF.SCREED m3, SCREED) | 4.906867 face (T-494, cited) | t0 not printed | HELD | scope ASSUMED - OWNER-APPROVED (Q-41); THICKNESS, FALLS (no outlet: RFI) |
| open sky | INSULATION (FIN.ROOF.INSULATION m2) | 4.906867 basis | - | HELD | UNKNOWN: printed nowhere, no owner rule |
| open sky | PROTECTION (FIN.ROOF.PROTECTION m2) | 4.906867 basis | - | HELD | UNKNOWN (Q-41 = one screed line) |
| open sky | FINISH (FIN.ROOF.FINISH m2) | **4.519172** hatch 1250 + 1253 | - | **4.519172 MEASURED** | extent DRAWING-CONFIRMED; material HELD (BY_SPEC) |
| open sky | finish bed | - | - | no row | not printed; the falls are FALLS_SCREED once (refused from Q-45 band) |
| ledge | all four | bound 0.639573 | - | HELD | ZONE: covered 4.20 m above, open at the void (register); no hatch on it (0.000000) |
| open sky | upstand of each layer | 5.193544 lm (T-494 valued runs) | height not printed | length MEASURED | height HELD |
| open sky | edge terminations | slab edge 6.869158 + void edge 4.321407 lm | - | length MEASURED | treatment HELD (detail) |

Reconciliation: face 4.906867 - hatch 4.519172 = 0.387695 m2, the hatch gap measured directly (0.000000 unexplained):
the hatch's west boundary runs on the layer-2 lines B31 / CB4 / C7B / C7C (elements drawn below / beyond), 0.25 m short
of the 1F wall face and short of the pier faces (four pieces 0.145374 / 0.124130 / 0.108350 / 0.009787). Carried as a
range of one boundary (HATCH_EDGE_ON_LAYER_2), the row on the hatch (R-T328-1). Hatch outer 4.519183 - 0.000011 drafting
overlap on the pier / void lines = 4.519172.

## 3. Cement / sand (R-T517-5; T-511 census + T-514 rows)

Keys proposed: one FIN.ROOF.SCREED host per zone (open sky, ledge), both HELD: LAYER_TYPE, MIX, THICKNESS, FALLS (+ ZONE,
AREA on the ledge). FINISH / PROTECTION are SCOPE_OPEN, INSULATION NOT_A_KEY: no key. Census over the 1,546 T-511 + 6
T-514 rows with the proposed hosts: **0 two-producer keys, 0 fails**; no FIN.ROOF line on the zone in V3.0.57; closes
T-514 MISSING_HOSTS[0]. Project cement known part unchanged (>= 125.126280 .. 164.620992 bags; the new hosts HELD).
Sensitivity, NOT A QUANTITY: 0.049069 m3 per cm of screed = 0.392549 bags + 0.053976 m3 sand at 1:4.

## 4. Effect if wired (stream F, after the wrapper fix) and verdict

FIN.ROOF.FINISH 202.219760 -> 206.738932 m2 (+4.519172, +2.23 %); + 7 BLANK lines (screed x2, insulation x2,
protection x2, ledge finish), never 0. Freelancer: one roof line 285.00 m2, no screed / finish split (cells not read):
UNRESOLVED. Verdict proposal: ENGINE_WRONG (omission of the stack, fixed here), finish area DRAWING-CONFIRMED.

## 5. Findings

- F-T517-1 (Lead): the register row 'SCREED TO FALLS' says 'Q-45 governs that layer's mix / bags (1:4, PROVISIONAL)',
  while T-514 (Gate A PASS) holds every roof falls screed on LAYER_TYPE + MIX (UPC-TILE-BED-001 scope = floor-tile
  beds). This table follows T-514; no number depends on it here (thickness and falls HELD).
- F-T517-2: the hatch west edge on layer-2 lines (above): designer intent unprinted; named range, not chosen.
- F-T517-3: the designer hatched a no-door slab like the walkable terraces: extent MEASURED, material HELD.

## 6. Lessons row (proposed, ERS s.7)

| 2026-11-05 | an exposed slab got its membrane line but none of the layers above it | the build-up family was keyed to the four labelled roofs, not to the B8-06 roof function | R-T517-1..6 (every villa): a roof-function zone carries the complete stack, one falls volume, a bed only if printed, areas by own edge cited, held by name | tests/t517_poolcourt_buildup (K517 by hand; adverse: nothing printed, no outlet, missing layer, membrane row, Q-45 bed on a roof, finish over face, unnamed range, units, held zone, mix scope) | proposed |

Missing: t0, falls / outlets (designer D-39, RFI), finish material, edge and upstand details, the window run (sill).
