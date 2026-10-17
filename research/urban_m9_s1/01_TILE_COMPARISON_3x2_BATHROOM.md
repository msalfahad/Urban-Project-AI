# 01 Tile size comparison - synthetic 3.00 x 2.00 m bathroom

Synthetic room given by the owner for the S1 check (not a project room). Engine: `engine/source/tile_layout.py` (TILE_RECT_EXACT_V1, rectangle exact). Rebuilt by `build_examples.py`.

## Assumptions (every one a stated test parameter; nothing defaulted)

| Parameter | Value | Source |
|---|---|---|
| room | 3.00 x 2.00 m, net 6.000 m2 | owner S1 example (synthetic) |
| sizes | 120x60 (SELECTED), 60x60, 160x80 cm | owner-approved sizes, rules/materials 1.0.0 |
| joint | 2 mm | test parameter |
| minimum cut | 0.10 m (a smaller cut makes a layout infeasible) | test parameter |
| minimum reusable offcut | 0.10 m on both sides | test parameter |
| kerf | 0 m | test parameter |
| offcut rotation | not allowed | test parameter |
| layout search | orientations 0 / 90 deg x start CORNER / CENTRED_TILE / CENTRED_JOINT per axis (18; 9 for a square tile), the same for every size | tile_layout.best |
| objective | fewest tiles opened, then the least owner-defined cutting waste | S1 default (see note) |
| perimeter gap | not modelled (pieces run to the finished wall line) | S1 limit |
| falls to the drain | not modelled (flat plane) | S1 limit, flagged |
| packaging | the registry has no pieces-per-box: boxes UNRESOLVED | rules/materials 1.0.0 |

Definitions (owner, M9 S1 addendum): cutting waste = material consumed - placed tile area - reusable offcuts retained; waste % = cutting waste / net installed area x 100; packaging surplus, procurement and any spare allowance are kept apart.

## Result per candidate (same constraints)

| Size | Role | Layout | Full | Cut | Consumed | Material m2 | Placed m2 | Joint m2 | Reusable offcuts m2 | Cutting waste m2 | Waste % | Boxes | Recommendation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TILE-120x60 | SELECTED (BOQ basis) | 0deg CORNER/CORNER | 6 | 6 | 9 | 6.480 | 5.974 | 0.026 | 0.490 | 0.016 | 0.26 | UNRESOLVED | - |
| TILE-60x60 | ALTERNATIVE (recommendation only) | 0deg CORNER/CORNER | 12 | 8 | 17 | 6.120 | 5.966 | 0.034 | 0.127 | 0.027 | 0.45 | UNRESOLVED | RECOMMENDATION ONLY: +0.360 m2 less material consumed and -0.011 m2 less cutting waste than the selected TILE-120x60; the BOQ stays on TILE-120x60 unless the owner / designer changes the specification |
| TILE-160x80 | ALTERNATIVE (recommendation only) | 90deg CENTRED_TILE/CORNER | 3 | 7 | 5 | 6.400 | 5.978 | 0.022 | 0.417 | 0.005 | 0.08 | UNRESOLVED | RECOMMENDATION ONLY: +0.080 m2 less material consumed and +0.011 m2 less cutting waste than the selected TILE-120x60; the BOQ stays on TILE-120x60 unless the owner / designer changes the specification |

The selected size (120x60) stays the BOQ basis. An alternative that consumes less material is reported as a recommendation only; the engine never substitutes it.

## Cutting plans of the chosen layouts

**TILE-120x60** - 0deg CORNER/CORNER: pieces along 3.00 m [1.2, 1.2, 0.596], along 2.00 m [0.6, 0.6, 0.6, 0.194]; 12 positions = 6 full + 6 cut; 3 cut piece(s) taken from offcuts, 3 tile(s) opened for cuts; offcuts kept [[0.604, 0.6], [0.604, 0.212]]; scrap 0.016 m2.

**TILE-60x60** - 0deg CORNER/CORNER: pieces along 3.00 m [0.6, 0.6, 0.6, 0.6, 0.592], along 2.00 m [0.6, 0.6, 0.6, 0.194]; 20 positions = 12 full + 8 cut; 3 cut piece(s) taken from offcuts, 5 tile(s) opened for cuts; offcuts kept [[0.6, 0.212]]; scrap 0.027 m2.

**TILE-160x80** - 90deg CENTRED_TILE/CORNER: pieces along 3.00 m [0.296, 0.8, 0.8, 0.8, 0.296], along 2.00 m [1.6, 0.398]; 10 positions = 3 full + 7 cut; 5 cut piece(s) taken from offcuts, 2 tile(s) opened for cuts; offcuts kept [[0.208, 1.6], [0.208, 0.406]]; scrap 0.005 m2.

## The same rooms under two other readings (for the owner's decision Q-TILE-1)

| Size | Owner-waste objective: layout | consumed | cutting waste m2 | No offcut reuse (grid upper bound): consumed | cutting waste m2 |
|---|---|---|---|---|---|
| TILE-120x60 | 0deg CENTRED_TILE/CENTRED_JOINT | 12 | 0.000 | 10 | 1.222 |
| TILE-60x60 | 0deg CORNER/CENTRED_JOINT | 20 | 0.016 | 20 | 1.234 |
| TILE-160x80 | 0deg CORNER/CENTRED_TILE | 6 | 0.000 | 6 | 1.696 |

Ranking layouts by the owner-defined cutting waste alone credits retained offcuts as if they were saved, and so prefers layouts that open MORE tiles (120x60: 12 tiles against 9). Until cross-room offcut reuse is planned (S2), S1 ranks by the material consumed and reports the owner-defined waste of that layout.

## Illustrative packaging (TEST PARAMETERS - not product data)

| Size | pcs / box (test) | Consumed pcs | Boxes | Box area m2 | Packaging surplus m2 |
|---|---|---|---|---|---|
| TILE-120x60 | 2 | 9 | 5 | 1.440 | 0.720 |
| TILE-60x60 | 4 | 17 | 5 | 1.440 | 1.080 |
| TILE-160x80 | 2 | 5 | 3 | 2.560 | 1.280 |

## Reference only: the takeoff skill's flat percentages (unconfirmed defaults, never used)

| Size | Flat % (skill) | Net x (1 + %) m2 | Layout material consumed m2 |
|---|---|---|---|
| TILE-120x60 | 12 | 6.720 | 6.480 |
| TILE-60x60 | 10 | 6.600 | 6.120 |
| TILE-160x80 | 15 | 6.900 | 6.400 |

A flat percentage ignores the room: here it overstates the 120x60 and 160x80 material and cannot say how many tiles to open. UP-CER-010 keeps it as a reference only.
