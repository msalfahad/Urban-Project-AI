# ELIGIBILITY_V0: which surfaces and trades each element kind must account for

**Status: an engineering proposal [ENGINEERING INFERENCE]. It is not an owner rule.**
- The ledger prototype (`scripts/q3_surface_ledger.py`) uses this table to decide which (element, surface, trade) pairs must have a status.
- Adopting it, and every entry marked *(owner)*, is an **[OWNER DECISION]**.
- Until then the ledger is a diagnostic only. **No completeness claim is made from it.**

A pair that is not in the table is NOT_APPLICABLE, and is not written to the ledger.

## Spaces, keyed by the space kind the engine established

| Kind | Surface | Trade | Item codes that satisfy it |
|---|---|---|---|
| DRY | FLOOR | floor finish | FIN.FLOOR.PORCELAIN, FIN.FLOOR.MARBLE |
| DRY | CEILING | ceiling | FIN.CEILING |
| DRY | WALLS | plaster | FIN.PLASTER |
| DRY | WALLS | paint | FIN.PAINT |
| DRY | SKIRTING | skirting | FIN.SKIRTING |
| WET (incl. SERVICE *(owner)*) | FLOOR | wet floor tile | FIN.FLOOR.WET_TILE |
| WET | FLOOR | floor waterproofing | FIN.WP.FLOOR |
| WET | WALL_BASE | waterproofing upturn (height *(owner)*) | FIN.WP.UPTURN |
| WET | CEILING | ceiling | FIN.CEILING |
| WET | WALLS | plaster | FIN.PLASTER |
| WET | WALLS | wall tile (height *(owner)*) | FIN.WALL.TILE |
| WET | WALLS_ABOVE_TILE | paint or tile (Q7 *(owner)*) | FIN.PAINT |
| WET | SKIRTING | skirting (UP-CER-004 *(owner)*) | FIN.SKIRTING |
| STAIR | TREADS / RISERS / LANDINGS | marble | FIN.MARBLE.TREAD / .RISER / .LANDING |
| STAIR | NOSINGS | step (lm) | FIN.STAIR.STEP_LM |
| STAIR | BALUSTRADE | railing | FIN.RAILING |
| STAIR | SOFFIT_CEILING, WALLS, SKIRTING | ceiling, plaster, paint, skirting | FIN.CEILING, FIN.PLASTER, FIN.PAINT, FIN.SKIRTING |
| EXTERIOR | GROUND | exterior scope (Q1 *(owner)*) | ARCH.EXTERIOR |
| UNKNOWN | FLOOR, CEILING, WALLS, SKIRTING | blocked until the kind is established | any of the above; a space-level ARCH.SPACE record counts as BLOCKED |
| SHAFT | — | **EXCLUDED**: a lift or service shaft carries no architectural finish in this scope *(owner)* | — |

## Openings

| Kind | Surface | Trade | Item codes |
|---|---|---|---|
| DOOR | OPENING | door item | ARCH.DOOR |
| DOOR | THRESHOLD | threshold finish (Q-S6-1 *(owner)*) | ARCH.THRESHOLD |
| DOOR / WINDOW / PASSAGE | REVEAL_JAMBS, HEAD_SOFFIT | reveal finish (whether reveals are measured *(owner)*) | **none today: no emitter** |
| WINDOW | OPENING | window item | ARCH.WINDOW |
| WINDOW | SILL_STRIP | sill / floor (needs the window schedule) | ARCH.WINDOW_REVEAL |
| PASSAGE | OPENING | passage item | ARCH.PASSAGE |
| PASSAGE | THRESHOLD | floor strip (Q-S6-1 *(owner)*) | ARCH.THRESHOLD |
| DOOR_PROVISIONAL, DOOR_UNRESOLVED | as DOOR | as DOOR | no line today. Q2 asks for a provisional door line with a bounded width |

## Wall groups

| Surface | Trade | Item codes |
|---|---|---|
| WALL_LINE | wall run | ARCH.WALL_RUN |
| WALL_BODY | masonry | MAS.BLOCK |

## Blocker classes

These are read from the reason codes of the existing RFI / unresolved records.

| Class | Reason codes |
|---|---|
| OWNER_DECISION | Q-S6-1, Q-S6-4, Q7, Q1, Q-OPN-1 |
| ENGINE | STRIP_NOT_ATTRIBUTED, STAIR_DRAWN_ON_TWO_PLANS, STAIR_LANDING_POLYGON |
| MISSING_SOURCE (sections / heights) | WALL_FINISH_HEIGHT, UP-CER-004, STAIR_RISER_NOT_ESTABLISHED, STAIRWELL_CEILING |
| MISSING_SOURCE (window schedule / elevations) | WINDOW_REVEAL_FLOOR_STATUS |
| MISSING_SOURCE (wall specification / legend) | BLOCK_WALL_NOT_ESTABLISHED |
| SPACE_KIND_NOT_ESTABLISHED | covered only by a space-level unresolved record (label missing or unread) |
