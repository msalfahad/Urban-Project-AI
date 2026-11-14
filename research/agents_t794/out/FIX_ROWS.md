# T-794 F-26 roof upturn vs freelancer (fix rows on ARCH_TAKEOFF_V3.0.85)

Worker 3, 2026-11-14. Source: `research/agents_t794/fill_t794.py --write` -> `out/FIX_ROWS.json`. Drawings by Drive
title and handle only; no coordinate or client data stored.

Physical element: the 0.20 m membrane upturn on every solid vertical face bounding a waterproofed roof surface. Owner
Q-24: roofs "as the bathrooms" (membrane + 20 cm wall upturn) and a 20 cm upturn round a dome; Q-35 option C: the
upturn line is walls only, each doorway a transition line. R-T522-1: a frame standing on the slab is a transition.

Freelancer (re-read this run, waterproofing sheet): one typed row "roofs and annexes" 194.00 lm / 285.00 m2, no sub-rows.

## Per run (lm)

| run | before | after | basis |
|---|---|---|---|
| +5.50 strips AT216 | 52.940 | 52.940 | 18.97 + 7.50 + 1.30 + 6.20 + 17.67 + 1.30; opening 0.406 named, not fixed (<1 %) |
| +4.30 annex AT220 | 35.727 | 35.727 | 11.8 + 1.3 + 1.4 + 3.2 + 6.4 + 0.7 + arc 1.728 + 2.9 + 6.3 |
| +9.70 roof AT379 | 92.922 | **91.922** | boundary 65.14 - door D115 1.000 (walls 1280 / 1281 gap, swing r 0.89) + dome rings 27.782 |
| +13.90 top roof | 42.155 | 42.155 | 28.30 + DOME-3 ring 13.855 (ESTIMATE, Q-34) |
| pool court + ledge | 9.222 | **6.245** | ledge 3.528 -> 0.552 (walls BCD + BD0); glazing BCE 2.977 = transition |
| **total** | **232.965** | **228.989** | vs 194.00: +20.1 % -> +18.0 % |

New lines: FIN.WP.DOORWAY_TRANSITION 0.20 m2 + _NR 1 pcs (door D115, DRAWING-READ); FIN.WP.TERMINATION 2.977 lm
(ledge glazing BCE, ESTIMATE). Nothing dropped: 3.977 lm moved to transition / termination lines.

## Ours - his = +34.989 lm, by cause (exact, residual named)

| cause | lm | label |
|---|---|---|
| two +9.70 dome rings | +27.782 | RULE_DIFFERENCE (owner Q-24) |
| DOME-3 ring +13.90 | +13.855 | RULE_DIFFERENCE |
| pool court open sky + window wall + ledge walls | +6.245 | ENGINE_RIGHT |
| door D115 out of the upturn | -1.000 | ENGINE_RIGHT |
| his lump over the four inner boundaries (181.108 + 1.000) | -11.892 | UNRESOLVED (typed lump, no sub-rows) |
| annex arc chords | -0.001 | TOLERANCE |

Like for like (four roofs, walls only, no rings, no pool court): 181.108 vs 194.00 = -6.6 %.

Checker: re-measure the +9.70 boundary 65.14 by hand (largest run) and the 1.000 door gap (1280 end -> 1281 start).
Named, not fixed: terrace opening 0.406 lm (nature not printed); 5.857 lm of window openings on roof edges taken as solid
wall below a sill (only one sill printed, '84').
