# Junction-flange sweep, the 3 x 4 m bathroom (generated)

Method A (separate upstand) with the flange on the floor j as a parameter. The values of j are sensitivity points, not standards: the membrane system's data sheet fixes j. Per direction: the least-membrane plan and the fewest-joints plan (rolls / m2 consumed / seams). **V25** = what V2.5 does (least membrane inside a direction, directions by rolls -> seams -> membrane); **RULE** = UP-WP-LAY-001 applied to every plan (rolls -> seams -> membrane). Hand-verified at j = 0.10, 0.11, 0.15, 0.16 (construct_cases.SWEEP_HAND); the other rows are calculator output.

| j (m) | Y least membrane | Y fewest joints | X least membrane | X fewest joints | V25 selects | RULE selects |
|---|---|---|---|---|---|---|
| 0.10 | 2 / 17.80 / 8 | 2 / 18.44 / 7 | 2 / 18.20 / 9 | 2 / 18.80 / 7 | Y: 2 rolls, 17.80 m2, 8 seams | Y: 2 rolls, 18.44 m2, 7 seams |
| 0.11 | 2 / 18.77 / 7 | 2 / 18.77 / 7 | 2 / 18.20 / 9 | 2 / 18.80 / 7 | Y: 2 rolls, 18.77 m2, 7 seams | Y: 2 rolls, 18.77 m2, 7 seams |
| 0.12 | 2 / 18.77 / 7 | 2 / 18.77 / 7 | 2 / 18.20 / 9 | 2 / 18.80 / 7 | Y: 2 rolls, 18.77 m2, 7 seams | Y: 2 rolls, 18.77 m2, 7 seams |
| 0.13 | 2 / 18.77 / 7 | 2 / 18.77 / 7 | 2 / 18.20 / 9 | 2 / 18.80 / 7 | Y: 2 rolls, 18.77 m2, 7 seams | Y: 2 rolls, 18.77 m2, 7 seams |
| 0.14 | 3 / 20.10 / 6 | 3 / 21.55 / 5 | 2 / 18.75 / 8 | 2 / 19.40 / 7 | X: 2 rolls, 18.75 m2, 8 seams | X: 2 rolls, 19.40 m2, 7 seams |
| 0.15 | 3 / 20.10 / 6 | 3 / 21.55 / 5 | 2 / 18.75 / 8 | 2 / 19.40 / 7 | X: 2 rolls, 18.75 m2, 8 seams | X: 2 rolls, 19.40 m2, 7 seams |
| 0.16 | 3 / 20.60 / 6 | 3 / 21.55 / 5 | 3 / 20.60 / 5 | 3 / 22.55 / 4 | X: 3 rolls, 20.60 m2, 5 seams | X: 3 rolls, 22.55 m2, 4 seams |
| 0.17 | 3 / 20.60 / 6 | 3 / 21.55 / 5 | 3 / 20.60 / 5 | 3 / 22.55 / 4 | X: 3 rolls, 20.60 m2, 5 seams | X: 3 rolls, 22.55 m2, 4 seams |
| 0.18 | 3 / 20.60 / 6 | 3 / 21.55 / 5 | 3 / 20.60 / 5 | 3 / 22.55 / 4 | X: 3 rolls, 20.60 m2, 5 seams | X: 3 rolls, 22.55 m2, 4 seams |
| 0.19 | 3 / 20.60 / 6 | 3 / 21.55 / 5 | 3 / 20.60 / 5 | 3 / 22.55 / 4 | X: 3 rolls, 20.60 m2, 5 seams | X: 3 rolls, 22.55 m2, 4 seams |
| 0.20 | 3 / 20.60 / 6 | 3 / 21.55 / 5 | 3 / 20.60 / 5 | 3 / 22.55 / 4 | X: 3 rolls, 20.60 m2, 5 seams | X: 3 rolls, 22.55 m2, 4 seams |

Continuous fold-up (method B) for comparison: see WPB-B in PLAN_TABLES.md (no flange, no band).
