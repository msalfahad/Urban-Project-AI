# S9A post-freeze comparison

Read after the S9A freeze (`DATED_CORRECTION_LAYER`, manifest sha256 `58ed85f9ce327367...`). S9A, S9 and 30 frozen manifests verify before and after. Comparison only, after the freeze: S9A is not tuned, no beam reading is selected, nothing is released and no frozen quantity changes; a finding that needs a change goes to a separately approved release.

## Findings

| ID | CLASS | FINDING | ACTION |
|---|---|---|---|
| PF-01 | SAME_OBJECTS | the PRE-S8 census lists 8 HZ-* hatch zones; 8 have the handle and area of an S9A band (to 0.001 m2): S9A's independent detection found the same objects and no other | none |
| PF-02 | RESOLVED_BY_MEASUREMENT | the census records 'the legend draws the cantilever portion and the bearing wall with the same dense hatch'; on the plotted PDF the two legend boxes measure 98.78 and 86.81 mm, and all 8 bands match the cantilever-portion symbol (C05). The census's ambiguity is resolved by measurement; the thickness is still not printed | none to S9A; RFI-A08 (thickness) stands; confirm the classification with the engineer |
| PF-03 | SAME_OBJECT | V3b's residue row for the cantilever beam CA uses a drawn band extent of 1.15 m; S9A-CP-01 is 1.15 m long on the same beam line, so the band is CA's own footprint, as S9A bound it (no second object) | none |
| PF-04 | METHOD + POPULATION | V3b's computed beams (82) total 37.587 m3 by reading A's downstand B x (H - t) x L; S9A's 103 conditional beams give 42.60163 m3 downstand, 56.766582 m3 under reading A and 70.931534 m3 under reading B. The populations differ and V3b has no per-beam register | none; V3b's choice of reading A is not authority (RFI-A01 stands) |
| PF-05 | AUTHORITY + METHOD | V3b reads the p.13 ground-beam titles as exclusive bands (11.245 m3 interior); S9A shows the same reading as a conditional value only (2.05827 - 2.26596 m3 over 11 interior spans) on top of S9's 3.8791 m3 released | none; RFI-A05 stands |
| PF-06 | NO_DIFFERENCE | exterior ground beams: V3b blocks the depth technically and infers about 1.0 m from the elevations; S9A holds 1.0 m as an upper bound only. Both treat 'FOLLOW ARCH.' as missing | none |
| PF-07 | METHOD + POPULATION | columns: V3b measures clear of the beams plus joints on the schedule section for every bound column; S9 releases matched, S2-VERIFIED columns over the floor-to-floor; the 28 mismatches stay RFI-A04. Not decomposable per column | none |

## Beams against the old Urban V3b BOQ

| STOREY | V3B_COMPUTED_BEAMS | V3B_TECHNICAL_M3 | S9A_CONDITIONAL_BEAMS | S9A_READING_A_DOWNSTAND_M3 | S9A_READING_A_M3 | S9A_READING_B_M3 | V3B_MINUS_S9A_DOWNSTAND_M3 |
|---|---|---|---|---|---|---|---|
| GF | 41 | 21.414 | 55 | 25.523914 | 33.41457 | 41.305226 | -4.109914 |
| 1F | 26 | 13.523 | 33 | 14.370613 | 19.380813 | 24.391012 | -0.847613 |
| 2F | 15 | 2.65 | 15 | 2.707104 | 3.9712 | 5.235296 | -0.057104 |
| ALL | 82 | 37.587 | 103 | 42.60163 | 56.766582 | 70.931534 | -5.01463 |

V3b's method (clear length x B x (D - t)) is S9A reading A without the slab strip. Agreement or disagreement with V3b is never used to pick a reading.

## Ground beams and columns

| ITEM | V3B_STATUS | V3B_TECHNICAL_M3 | S9_RELEASED_M3 | CLASS |
|---|---|---|---|---|
| GROUND_BEAMS_INTERIOR | COMPUTED | 11.245 | 3.8791 | AUTHORITY + METHOD |
| GROUND_BEAMS_EXTERIOR | BLOCKED |  |  | NO_DIFFERENCE (both technically blocked) |
| COLUMNS_GF | PARTIAL | 15.298 | 13.6125 | METHOD + POPULATION |
| COLUMNS_1F | PARTIAL | 7.676 | 4.284 | METHOD + POPULATION |
| COLUMNS_2F | PARTIAL | 3.377 | 2.688 | METHOD + POPULATION |

## PRE-S8 census crosswalk

8 of 8 HZ-* rows are S9A bands (same handle, area within 0.001 m2). The CA row is bound to its band by V3b's own drawn band extent.

| PRE_S8_ID | DXF_HANDLE | PRE_S8_AREA_M2 | S9A_BAND | S9A_AREA_M2 | S9A_LEGEND_MATCH | CLASS |
|---|---|---|---|---|---|---|
| HZ-FFRS-5E0 | 5E0 | 1.35 | S9A-CP-05 | 1.35 | CANTILEVER_PORTION | SAME_OBJECT |
| HZ-GFRS-273 | 273 | 0.75 | S9A-CP-04 | 0.75 | CANTILEVER_PORTION | SAME_OBJECT |
| HZ-GFRS-2B1 | 2B1 | 0.1 | S9A-CP-02 | 0.1 | CANTILEVER_PORTION | SAME_OBJECT |
| HZ-GFRS-2B4 | 2B4 | 1.2 | S9A-CP-03 | 1.2 | CANTILEVER_PORTION | SAME_OBJECT |
| HZ-GFRS-54D | 54D | 0.345 | S9A-CP-01 | 0.345 | CANTILEVER_PORTION | SAME_OBJECT |
| HZ-SFRS-38C | 38C | 0.226 | S9A-CP-08 | 0.226 | CANTILEVER_PORTION | SAME_OBJECT |
| HZ-SFRS-390 | 390 | 0.62 | S9A-CP-07 | 0.62 | CANTILEVER_PORTION | SAME_OBJECT |
| HZ-SFRS-391 | 391 | 0.356 | S9A-CP-06 | 0.356346 | CANTILEVER_PORTION | SAME_OBJECT |
| BM-GF_ROOF-CA-BL015-69E | 54D |  | S9A-CP-01 |  |  | SAME_OBJECT |

Nothing here changes a released quantity. The released baseline stays S9's 158.070 m3 / 18,845.961 kg.
