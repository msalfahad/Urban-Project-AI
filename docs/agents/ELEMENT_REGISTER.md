# Shared project element register: design v0 (Lead, 2026-10-20 20:10)

Owner management decision 2026-10-20 §4: one stable register that links every drawn element to its drawing evidence and
to the BOQ lines derived from it. Built incrementally from outputs that already exist; no working module is rewritten.
This file is the Lead's design. The code is plan item P-09 (week 2, lane I with the Lead), after the V3.0 skeleton.

## Element id

`<project>/<rev>/<floor>/<kind>/<local>`; stable across reruns of the same revision.

| Part | Values | Source today |
|---|---|---|
| project | short project key (never a client name) | run config |
| rev | drawing revision id = sha256 prefix of the source file (SOURCE_MANIFEST) | revision_set_sha256 in tools/urban_boq_m9.py |
| floor | FDN, GF, 1F, 2F, ROOF-1F, ROOF-2F, ANNEX | storey detection / room levels (finish height V2) |
| kind | ROOM, WALL, OPEN (door / window / passage), COL, BEAM, FTG, GB (ground beam), STRAP, SLAB, STAIR-FLIGHT, LANDING, ROOF, EXT (porch, passage, court), ZONE-FIN (finish zone), ZONE-WP (waterproofing zone) | room faces, wall runs, opening records, route G members, T-110 beam register, T-111 flight ledger, membrane zones |
| local | the drawing's own label when printed (B23, F10, CB10, D-03), else a geometry hash of the outline rounded to 1 mm | label census / member detection |

A label printed twice (two B7 spans) gets a span suffix `B7.1`, `B7.2` ordered by grid; a geometry-hash id survives a
rerun on the same revision only; a new revision maps old to new ids by label first, then by outline overlap >= 95 %.

## Record (one per element)

id, kind, floor, label, outline or axis (mm, project coordinates), drawing evidence (sheet, layer, entity handle or
printed text), status in the seven statuses (VERIFIED / CALCULATED / PROVISIONAL / ASSUMED / HELD / CONFLICT /
NOT APPLICABLE), conflict record or designer request id (DESIGNER_CLARIFICATIONS.md), and `boq_lines`: every BOQ line
key that takes a quantity from it, with the quantity and unit taken. Cross-trade check: the same element area may feed
one finish line per surface (for example a landing: marble OR porcelain, never both) and one concrete line.

## Build order (no rewrites)

1. V3.0 lines carry `element_ids` (T-131 extension): rooms, wall runs, openings, membrane zones first (they already have
   outlines).
2. Structural: T-110 beam register ids, T-119 column ids, T-111 flights / landings, footings and straps from route G.
3. External areas: porch, passage, pool court, roof edges (T-127 places).
4. Revision mapping test on a synthetic villa with one changed wall.

Acceptance for v0 (P-09): every V3.0 line has at least one element id and a drawing reference; no element feeds two
finish lines for the same surface; held elements stay HELD in every line they feed.
