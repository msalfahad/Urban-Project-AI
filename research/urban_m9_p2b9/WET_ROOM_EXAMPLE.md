# Wet-room example — worked example 2 (a 4.00 × 3.00 m bathroom)

Fixture: `p2b9_fixtures.example2`. Hand truth: `p2b9_truth.E2_*`. Tests: `test_p2b9_wet_room.py`.

## Situation and evidence

- A bathroom with inner faces 4.00 × 3.00 m, 0.20 m walls, and door D1 1.00 m (schedule D1 1000 × 2200).
- Section F.C.L. +3.00 and U/S SLAB +3.00 on the GROUND FLOOR band.
- Owner rules applied, already recorded and not asked again:
  - full-height wall porcelain in wet rooms (UP-FIN-WALL-001);
  - no skirting with full-height porcelain (UP-CER-004);
  - no paint over it (UP-FIN-PAINT-001);
  - membrane rolls 1 × 10 m, laps 0.10 m, upturn 0.20 m (UP-WP-001..004);
  - doorway continuation = door width × wall depth (UP-WP-DOOR-001).
- No corner, drain or penetration detail is drawn, and none is invented.

## Drawing evidence → formula → hand → engine → difference → status

| Quantity | Evidence | Formula | Hand | Engine | Diff | Status |
|---|---|---|---|---|---|---|
| wet floor tile | plan | 4.00 × 3.00 | 12.00 m² | 12.00 | 0 | VERIFIED (hand) |
| wall tile, full height to F.C.L. | section F.C.L. +3.00 (owner full height) | 14.00 × 3.00 − 1.00 × 2.20 | 39.80 m² | 39.80 | 0 | VERIFIED (hand) |
| plaster behind the tile, to the soffit | section U/S SLAB +3.00 | 14.00 × 3.00 − 2.20 | 39.80 m² | 39.80 | 0 | VERIFIED (hand) |
| skirting | full-height porcelain | none | — | NOT_APPLICABLE_WITH_EVIDENCE | — | VERIFIED (rule) |
| paint above the tile | full-height porcelain | none | — | NOT_APPLICABLE_WITH_EVIDENCE | — | VERIFIED (rule) |
| WP floor | plan | 12.00 | 12.00 m² | 12.00 | 0 | VERIFIED (hand) |
| WP wall upturn | 13.00 m of wall (the doorway is not wall) | 13.00 × 0.20 | 2.60 m² | 2.60 | 0 | VERIFIED (hand) |
| WP doorway continuation | door 1.00 × wall 0.20 | 1.00 × 0.20 | 0.20 m² | 0.20 | 0 | VERIFIED (hand) |
| proven subtotal | | 12.00 + 2.60 + 0.20 | 14.80 m² | 14.80 | 0 | VERIFIED (hand) |
| laps (the WP-B cutting plan, 5 strips ALONG_Y) | | 4 × 3.00 × 0.10 + 13.00 × 0.10 + 4 × 0.30 × 0.10 + 1.00 × 0.10 | 2.72 m² | 2.72 | 0 | VERIFIED (V2.5 proof) |
| installed | | 14.80 + 2.72 | 17.52 m² | 17.52 | 0 | VERIFIED (V2.5 proof) |
| consumed | | 5 × 3.00 + 2.80 | 17.80 m² | 17.80 | 0 | VERIFIED (V2.5 proof) |
| cutting waste | | 17.80 − 17.52 | 0.28 m² | 0.28 | 0 | VERIFIED (V2.5 proof) |
| rolls | | 17.80 m of a 10 m roll, cut 9.00 + 8.80 | 2 | 2 (first-fit-decreasing, proven lower bound) | 0 | VERIFIED (V2.5 proof) |
| internal corners | 4 | treatment WITHHELD (no detail) | — | count 4, quantity none | — | held, not invented |
| penetrations | none drawn | NOT_SHOWN | — | none | — | held, not invented |
| floor / wall junction | method not given | UNRESOLVED: rolls range 2–3 | — | [2, 3] | — | open (owner detail) |

## What changed from V2.7.1

Only the source of the heights changed. V2.7.1 needs the project facts file for every height; V2.8 reads them from
the section and the schedule, and the missing-evidence report lists nothing for this room.

A false alarm was found and fixed during this phase. The report first asked for a printed wall-tile height even
though the owner full-height rule already resolves it from the section's F.C.L.; it now uses the tile height actually
applied.
