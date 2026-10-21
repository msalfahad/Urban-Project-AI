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

## Register state and Lead rulings (owner workflow controls 2026-10-21 §2; newest first)

Code: element_register_v0 is READY (T-134, 7053291, not merged). On the development villa V3.0 run: 652 elements,
1,504 of 1,530 lines linked, 26 UNLINKED with a reason; 0 double finishes, 0 double concrete, 0 held-released. The
checker verifies it before any ruling below becomes a code check. Evidence status per WORKFLOW_CONTROLS §5; a ruling
names the OWNER TRADE (the one trade whose line takes the quantity); every other trade lists the element without a
quantity.

### Lead 2026-10-21 20:20 (from T-119 r2, T-133 MERGED, T-149, T-150, T-153 MERGED, T-159, T-160)

| Element (Alsenan unless said) | Trades that touch it | Owner trade (ruling) | Status | Basis | Open item |
|---|---|---|---|---|---|
| 2F columns C2 / C3 at the water tank | column concrete, beam B15 / B3, rebar | COLUMN concrete, height range 3.00 .. 3.80 m (joint +0.160 m3 at the high end) | HELD (range) | T-119 r2; D-44 open | designer D-44 (B15 upstand or downstand) |
| 1F column C9 framing incl. B19 40 x 75 (oblique) | column, beam | COLUMN takes the joint once; B19 takes its span to the column face | DRAWING-CONFIRMED, not VERIFIED | URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1 | checker run A |
| 5 columns above the necks with no column on the slab plan above (2.268 m3) | column concrete, column steel | COLUMN: NOT APPLICABLE WITH EVIDENCE in V3.0.1; their 10 steel lines STALE until T-151 | VERIFIED (checker 17:40, by hand) | T-126 / T-133 Gate B | T-151 rewires steel |
| Blinding under footings 15.179 m3 | blinding concrete | BLINDING, released in the candidate only | VERIFIED (hand 15.213, -0.2 %) | T-126 / T-133 Gate B | ground-beam and strap blinding stay HELD; lower bounds over hand (T-142 D3) |
| Beam spans running over end columns (5 register spans) and GF CB7 (2 spans, not 1) | beam concrete, beam steel | BEAM: span to the column face, column takes the joint | DRAWING-CONFIRMED (T-149), not VERIFIED | URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1 | T-160 corrects the register with the dome rings |
| Dome ring beams (each dome opening) | slab, beam, ceiling | BEAM: in-square ring part only; the parts inside B6 / B25 / CB12 belong to those beams; the 8 dome corner pieces are SLAB | DRAWING-CONFIRMED (checker 16:45), not VERIFIED | owner Q-44 A; non-overlapping model | T-160 |
| Windows W01 .. W26 and doors (65 openings) | openings, block deduction, plaster / paint reveals, facade | OPENINGS trade owns count and size; block, plaster and facade list the opening and deduct only under their own rule | 8 windows DRAWING-CONFIRMED, 20 HELD (D-45), W16 HELD (no rule for a twin), doors ASSUMED — OWNER-APPROVED 2.20 m (Q-55 C) | T-150 | D-45, D-07 |
| Facade sides (exterior wall faces per side and storey) | facade plaster / paint, blockwork, openings | FACADE finish per side; openings listed apart; boundary / street fence NOT a facade (Q-65 HELD) | to be measured | owner request 2026-10-21; Q-64 B | T-159 |
| GF north court strip (21.021 checker vs 21.348 worker) and the 0.37 m2 duct outline in it | external area | EXTERNAL area; split with the west court HELD | HELD (split) | checker 18:40 on T-153 | T-157 |

### Lead 2026-10-21 16:20 (from the CLAIMED / READY tasks T-133, T-134, T-148, T-153, T-154, T-155)

| Element (Alsenan unless said) | Trades that touch it | Owner trade (ruling) | Status | Basis | Open item |
|---|---|---|---|---|---|
| 1F arrival landing 4.875 m2 | floor finish (porcelain, marble), stair | floor finish: MARBLE line only, once; porcelain total excludes it | DRAWING-CONFIRMED area, not VERIFIED | owner Q-66 B | V3.0 has no outline for it, so the one-finish check cannot see it (T-133b landing reader) |
| 1F east-flight foot piece 0.4025 m2, closed element 0.1175 m2 | floor finish | HELD until D-13 / D-23 settle landing or flight | HELD | owner instruction 2026-10-20 17:54 (4) | D-13, D-23 |
| Pool-court soffit PL-03 12.834 m2 (net of void 3.690) | ceiling, slab soffit paint | CEILING trade (area); finish HELD | DRAWING-CONFIRMED (T-127 merged, T-154 READY) | owner Q-68 C | the CAD census basis 14.704 m2 must never feed a ceiling line: it holds the opening heads and wall tops below (1.665 + 0.276 m2 would be counted twice) |
| Pool-court wall openings SX-01 (4.521 x 0.200 head, under CB1) and SX-03 (1.000 x 0.200, under B24) | ceiling census, plaster / paint reveals, openings | PLASTER / PAINT as opening-head reveal lines; listed as OPENINGS in T-150 | HELD (jamb heights not printed) | UP-GEN-003 opening table | neither V2.9 nor V3.0 records them as openings (T-150 scope; D-45) |
| Curved-glazing outer reveal SX-02 0.561 m2 | ceiling census, external plaster / paint | external PLASTER / PAINT reveal strip (T-123 family) | HELD | Q-64 B reveal treatment | which finish item the reveal belongs to in CAD (owner 2026-10-20 17:54 (3)) |
| Court wall tops 0.276 m2 (east piers, north pier, NE corner) | ceiling census | none: NOT APPLICABLE (no finish line) | NOT APPLICABLE | T-154 classification | checker confirms on Gate A |
| Turned 1F column 0.200 x 0.900 over the pool court (face 0.065 m2) | structure, soffit census | COLUMN concrete (structure); the B28 soffit around it stays in the ceiling line | DRAWING-CONFIRMED | ST GF roof-slab sheet column mark | a soffit census must test slab-sheet column faces against the plan below |
| GF side passage 5.640 m2 (3.600 + 1.560 strip) | floor area, soffit, external plaster | EXTERNAL area (floor and soffit as external lines); NOT internal floor | PROVISIONAL (Q-67 A conditional until the drawings confirm open to air) | owner Q-67 A | V2.9 counts it internal (defect, T-153); D-48; T-157 |
| GF garden band 13.986 m2 | floor area, landscape | none until classified | HELD, CONFLICT | label "garden" vs enclosed and roofed drawing (defect B9) | D-48; T-157 |
| Courts 167.714 m2 (west court 138.761 incl. porch 19.181 and E1 footprint 3.360; north strip 21.348; pool deck 7.605; pool water 7.548 is NOT a floor) | external works, waterproofing, pool | EXTERNAL area line; finish HELD | DRAWING-CONFIRMED area | OQ-04 (open, re-asked 2026-10-21) | his yard 151.80 m2: UNRESOLVED until OQ-04 sets the scope |
| Pantry 13.50 m2 | floor finish, waterproofing | WET floor (waterproofing zone + one floor finish line) | DRAWING-CONFIRMED | owner Q-37 A | none |
| Footing F10-type (FOOTING_LABEL_CONFLICT, 1.960 m3) and 5 beams (WIDTH_CONFLICT_SECTION, 5.022 m3 + 685.225 kg) | structure, rebar | STRUCTURE; status CONFLICT | CONFLICT, released by a route convention in V2.9 and V3.0 | none found: no owner rule names the convention | checker (Gate A on T-134) states whether an owner rule backs the convention; if none, lane I holds these lines in the next V3.0 package (a new task, never an edit of V2.9) |
| 3 planted columns (172.56 kg released by frozen S3.1 from a duplicated schedule row) | structure, rebar | REBAR line HELD in V3.0 | HELD | T-148 finding; D-46 | T-151 wires the hold |
| Footing bars printed per metre (F8, F12, F13, F14, FF) | rebar | REBAR; count rule HELD (A / B / C = 2,742.51 / 2,836.40 / 2,797.81 kg) | DRAWING-CONFIRMED notation (bars per metre); count UNKNOWN | owner Q-71 open | FF lift footing top / bottom legs drawn but not dimensioned: HELD |
