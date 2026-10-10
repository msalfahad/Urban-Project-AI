# S9A structural completeness report

Correction layer over S9 (frozen). Date 2026-10-10. Released quantities are S9's, unchanged; S9A releases nothing. Records are S9's 560 with S9A's owner changes: 7 untagged spans superseded by their band rows, 8 band rows added (561 records).

## By family

| Family | Records | Released | Conditional | Conflict | Blocked | Owned elsewhere / n.a. | Released m3 | Released kg |
|---|---|---|---|---|---|---|---|---|
| BEAMS | 151 | 0 | 108 | 9 | 26 | 8 | - | 4,014.765 |
| COLUMNS | 95 | 32 | 24 | 7 | 32 | 0 | 20.584 | 4,657.725 |
| SLABS | 76 | 47 | 0 | 0 | 6 | 23 | 57.099 | 3,802.015 |
| LINTELS | 64 | 7 | 50 | 0 | 7 | 0 | 0.366 | 49.589 |
| GROUND_BEAMS | 63 | 6 | 33 | 1 | 23 | 0 | 3.879 | 1,436.232 |
| FOOTINGS | 26 | 25 | 0 | 1 | 0 | 0 | 64.304 | 3,629.600 |
| GROUND_SLAB | 23 | 2 | 19 | 0 | 0 | 2 | 3.786 | 233.695 |
| STAIRS | 15 | 3 | 0 | 3 | 9 | 0 | 0.517 | 59.021 |
| LIFT | 11 | 0 | 4 | 0 | 2 | 5 | - | - |
| DOMES | 9 | 2 | 0 | 3 | 2 | 2 | 5.081 | 602.111 |
| CANTILEVER_PORTIONS | 8 | 0 | 0 | 0 | 7 | 1 | - | - |
| POOL | 7 | 0 | 0 | 0 | 7 | 0 | - | - |
| WATER_TANK_ROOF | 4 | 2 | 0 | 0 | 2 | 0 | 2.454 | 361.209 |
| OTHER | 3 | 0 | 0 | 0 | 3 | 0 | - | - |
| PARAPETS | 3 | 0 | 0 | 0 | 3 | 0 | - | - |
| PLAIN_CONCRETE | 2 | 0 | 0 | 0 | 2 | 0 | - | - |
| BOUNDARY_WALL | 1 | 0 | 0 | 1 | 0 | 0 | - | - |
| **All** | 561 | 126 | 238 | 25 | 131 | 41 | 158.070 | 18,845.961 |

## Not released, with its range

These values are conditional. None enters a released total (C15).

| Item | Low m3 | High m3 | Note |
|---|---|---|---|
| BEAMS (conditional, never released) | 56.767 | 70.932 | 103 beams; low = H overall, high = H below the slab |
| CANTILEVER_PORTIONS (blocked) | - | - | 7 bands, 4.602 m2; thickness unknown (value at the adjacent slab thickness in 03, context only) |
| GROUND_BEAMS (p.13 title reading, never released) | 2.058 | 2.266 | 11 interior spans held only by the title / length-basis reading |
| COLUMNS (section mismatch, never released) | 10.650 | 13.480 | 22 mismatched GF / 1F / 2F occurrences (drawn vs schedule) |

## Interpretation versus missing information

| RFI | Problem type | Scope |
|---|---|---|
| RFI-A01 | INTERPRETATION (H is printed; the face it is measured from is not) | 103 beams |
| RFI-A02 | MISSING_SOURCE_INFORMATION (no bend radius, hook or closure printed) | 288 column tie parts + D1.1 link paths |
| RFI-A03 | MISSING_SOURCE_INFORMATION (only a minimum excavation depth is printed) | 36 foundation necks + lift pit walls |
| RFI-A04 | INTERPRETATION (19 occurrences match another schedule row or type) + SOURCE_CONFLICT (9 match nothing) | 22 occurrences |
| RFI-A05 | INTERPRETATION (18 spans: titles, length basis, exterior or interior) + MISSING_SOURCE_INFORMATION (30 spans: exterior depth 'FOLLOW ARCH.', concentrated-load detail) | 11 interior + 15 exterior spans |
| RFI-A06 | MISSING_SOURCE_INFORMATION (the note's extent is not zoned) | 19 slab-on-grade faces |
| RFI-A07 | MISSING_SOURCE_INFORMATION (bearings and head functions not drawn) | 57 lintels |
| RFI-A08 | MISSING_SOURCE_INFORMATION (no thickness, section or bars for the hatched portions) | 7 bands, 4.602 m2 |
| RFI-A09 | MISSING_SOURCE_INFORMATION (no tag, no schedule row) | 25 spans |
| RFI-A10 | INTERPRETATION (an ownership rule, not a dimension) | 10 corner ends |

## Not quantified at all

- Pool, parapets, blinding, the boundary wall, the dome rings, the lift tie beam and the overrun are unchanged from S9: blocked or not in the source.
- The 7 cantilever portions join them: blocked until a thickness is given.
- The sunken-slab drops (6 hatches at 250 mm) are unchanged S9 rows.

The visual QA package (`visual/S9A_VISUAL_QA.html`) shows each of these on the plans.

