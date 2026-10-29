# T-315: INTEGRATION PACKAGE ARCH_TAKEOFF_V3.0.21, the WALL TILE family (FIN.WALL.TILE) face by face from the merged T-312 face ledger (development villa; every villa by R-WALL-TILE-FAMILY-1)

Worker 3 (lane I), claim 2026-10-29 01:01 UTC, run unknown. Gate B integration package: `integrates: T-312`. Base =
the candidate of record ARCH_TAKEOFF_V3.0.20 (T-244 Gate B PASS, MERGED 59dbfd0e). Released default stays V2.9 +
route G; nothing here is released, nothing is VERIFIED by this task. ERS 2026-10-22 applied: s.2.1 (the physical
element first), s.2.2 (owner manual method beside the drawing-derived method on every line), s.2.4 (reconcile in m2
to named causes), s.3 (one face, one owner trade; a rule's scope before its arithmetic), s.4 (rule + normal and
adverse tests), s.7 (lesson row, section 9).

## 1. The physical element and what the candidate carried

Wall tile = porcelain / ceramic on a WALL FACE (one drawn wall seen from one room) from the finished floor to the tile
top, less the part of each hole inside that band (UP-CER-005, Q-73). Scope by the owner rules: a wet room tiles every
face full height (UP-FIN-WALL-001; tile top = underside of the 0.15 decor ceiling, Q-48 A: GF 3.65, 1F / 2F 3.35);
an open pantry tiles only the host walls of its installation, each whole, the open edge nothing (UP-PANTRY-001 ..
004). A tiled face carries no paint (UP-FIN-PAINT-001); the substrate behind the tile is its own line
(UP-FIN-PAINT-001 logic `substrate`), never inside the tile figure.

V3.0.20 carried 17 FIN.WALL.TILE lines, ALL BLOCKED_RFI with no figure (WALL_FINISH_HEIGHT_NOT_ESTABLISHED), and no
tile line in the pantry engine room GF-RC06FED (T-312 NO_LINE, 6 faces, 32.3422 m2).

## 2. What V3.0.21 does (engine/source/arch_v3021.py, piece WALL_TILE_FAMILY)

- FILL (11 lines, same line ids): each line takes the sum of its faces, each face = length x its own height (with
  the height's source) - each opening's part inside the band, once per room side; the face lengths + open edges +
  not-tiled faces close to the room contour (0.0000 m on every room); state PROVISIONAL, evidence ASSUMED -
  OWNER-APPROVED with the owner source on the line (Q-48 A height, Q-55 C door heads; OWNER_RECONCILIATION G1).
- HELD (6 lines): asserted blank (BLOCKED_RFI, no figure, no range) and the record supplies none; the line is not
  changed (byte-identical), its reason is in the ledger: annex GF-02 / GF-03 / GF-05 / GF-06 (owner height not
  established: G2, Q-54 B HOLD, D-39), GF-10 / GF-11 (room level not drawn, T-088). Never 0.
- ADD (1 line): the open pantry (GF-07, engine room GF-RC06FED) gets ONE new FIN.WALL.TILE line, same item / trade /
  subtrade / documents as the family, element `GF-RC06FED#WALL_TILE:GF-07`, 32.3422 m2 on 6 faces (refused if the room
  already had a tile line).
- The whole family at once: every candidate FIN.WALL.TILE line is named by exactly one record (a line left out is
  refused). Cross-trade per face (section 5). The merged default guard (arch_v307) runs again over the result and may
  not flag a filled or added line. Every other line is byte-identical to V3.0.20 (asserted on every run).

RUN_RESULTS_PLACEHOLDER
