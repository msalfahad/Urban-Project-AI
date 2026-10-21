# Investigation C: completeness and area reconciliation

**Verdict: the Phase 1 gate proves less than its name suggests.**

It proves that **every plan-area face** is accounted for. It also proves that **every functional space has some line, RFI or exclusion** for floor, ceiling, walls and skirting.

It does **not** prove that every relevant *surface* or *element* is accounted for:
- **Doors are not conserved.** 8 of 29 drawn door swings on the reference plan have no door line.
- **Wall faces are not conserved per face.** WALLS "has an RFI" passes whatever the area.
- **Reveals, sills, stairwell walls and exterior surfaces are not modelled as surfaces.**

"Accounted" is also not "quantified". On the reference plan, plaster and paint have **zero** quantity lines (60 RFIs) and the gate says PASS.

## C.1 The terms, as the engine should use them

| Term | Definition | Where it lives today |
|---|---|---|
| Physical geometry | what is drawn: faces of the wall network, wall bands, openings, columns, flights, fills | `arch_rooms` faces, `ARCH_WALLS`, `ARCH_OPENINGS` |
| Functional space | a named / classified use area (room, open-plan zone, stair, wet room, exterior) made of one or more faces | `ARCH_ROOMS` |
| Finish zone | a part of a space with one finish family (dry / wet / exterior), split along drawn zone lines | S5 zones, `FINISH_COVERAGE.finish_zones` (totals only) |
| Eligible construction surface | a (surface, trade) pair that the rules say can carry work: floor × porcelain, wall face × plaster, wet wall × tile, reveal × plaster … | **missing**: implicit in `arch_measure` branches |
| BOQ quantity | a line with `measured_net`, a rule id and evidence | `BOQ_LINES` (quantity states) |
| Exclusion / unresolved | an eligible surface with no quantity, plus its reason: rule (NOT_APPLICABLE), source gap (RFI), engine gap (SOFTWARE) | BLOCKED_RFI lines and `UNRESOLVED`; exclusions in `FINISH_COVERAGE` |

The missing layer is the **eligible-surface ledger**: the explicit list of (surface, trade) pairs, derived from geometry × space kind × rule table. Without it, "complete" can only mean "something was emitted".

## C.2 Surface by surface on the reference plan (V2)

| Surface | Physical geometry | Functional / zone | BOQ today | Exclusion / unresolved | Completeness proven? |
|---|---|---|---|---|---|
| Floor finishes | faces (partition: Σ faces = Σ outer cycles, BALANCED on every floor) | rooms, open-plan zones, wet / dry | porcelain 12 lines, wet tile 16 lines (quantities) | merged / unlabelled spaces, landings: RFI | **Yes for plan area.** Floor finish lines = room + open-plan floor (BALANCED) |
| Thresholds | doorway strips inside openings | between two spaces | 38 BLOCKED_RFI lines (strip area in the inputs) | Q-S6-1 rule; 14 are engine defects (Investigation B) | **Partly.** Strips found only where an opening was measured or a door closure exists. **Doors with no opening have no strip** |
| Window reveals and sills | window-strip faces (plan) | — | 25 BLOCKED_RFI (plan area) | sill height missing | **No.** Jambs and heads are vertical surfaces (2 × depth × height, width × depth) and are not modelled. The method register makes reveals separate items (URBAN method V3), but the engine has no reveal surface |
| Plaster | wall bands × heights | per space (WALLS) | **0 quantity lines**, 30 RFIs | finish heights not established (UP-CER-009) | **No.** WALLS passes with one RFI, whatever the wall length. There is no per-face length conservation |
| Paint | the same as plaster | dry spaces; band above wet tile | **0 quantity lines**, 30 RFIs | heights; Q7; Q-S6-4 | **No** (as plaster) |
| Bathroom porcelain (wall tile) | wet-room wall faces | wet spaces | 16 BLOCKED_RFI | tile height (UP-CER-009 vs the full-height method: conflict S6R-B4) | **No** (as plaster) |
| Ceilings and double-height voids | faces minus voids; the void on the upper floor | per space | 29 lines; the GF ceiling excludes the void and 1F carries "ceiling over void" (consistent) | 2 stairwell-ceiling RFIs | **Plan area: yes.** Heights and soffits of the double-height walls: no (`double_height_region` keeps paint BLOCKED) |
| Stairwells | flights, landings, enclosure faces | the stair space per storey | treads / steps quantities; risers, flights, railings RFI | stair-hall walls (6 RFIs), landings (bounded exposure) | **No** vertical model: stairwell walls run through storeys, and per-storey "walls" is the wrong unit |
| Waterproofing and upturns | wet faces, doorway pieces | wet spaces | WP floor 16, upturn 16, doorway 13 quantities | — | **Plan area: yes.** Upturn length: computed per room, no face ledger. Doorway pieces exist even for the CLOSED doors whose door line is missing |
| Skirting | room perimeter minus openings | dry spaces | 12 quantities, 18 RFIs | UP-CER-004 (16), stair hall (2) | **Partly.** The perimeter is conserved per room, but the door deductions depend on the door census, which is incomplete |
| External garden / terrace | the EXTERNAL category (GF) | the exterior space | 1 `ARCH.EXTERIOR` area line | exterior scope Q1 (record only) | **No.** Hardscape, terraces, roofs, parapets and facades are out of the plan model. The roof plan is not read |

## C.3 The reconciliation that does balance, and what it hides

On every floor of the reference plan:
- faces = categories;
- faces = Σ outer cycles of the wall network;
- floor-finish lines = room + open-plan floor.

All three are BALANCED. Two observations:
1. `gross_floor_plate_m2` reports only the **largest** wall-network component. A detached second component, identical on every floor, sits inside the faces but outside that figure. The partition still balances; the summary figure needs a label or the total (S6R-C5, reporting).
2. The partition is tied to the **wall network found by the reader**.
   - When the reader misses wall pieces (Investigation A), the partition stays BALANCED; the faces just change shape (a small space +0.08 m², a door and a window gone).
   - **A balanced partition is self-consistent, not correct.** It needs an independent total: printed reference areas (already an input), the structural slab outline, or the plan's own area texts.

## C.4 Proposed invariant: no silent disappearance (NSD)

**For every drawing admitted, every source entity that can carry work ends in exactly one of LINE, RFI(question), NOT_APPLICABLE(rule) or UNREAD(reason), through a chain of conserved records.**

| Invariant | Statement | Check | Today |
|---|---|---|---|
| NSD-1 entity | every model-space entity, after block / MINSERT expansion, is consumed by a reader, classified non-quantity (annotation, dimension, pattern) or flagged UNREAD | census count = consumed + non-quantity + unread | partial: stage 1 covers top-level kinds; `shapes()` covers fills only |
| NSD-2 element | every detected symbol (door swing, window block, column outline, flight, fixture) ends in one element record. Each record is matched to a line, an RFI or an exclusion with a reason | per kind: symbols = matched + RFI + excluded; **no state like CLOSED without a line** | **missing** (8 doors) |
| NSD-3 plan area | Σ faces = Σ outer cycles; each face has exactly one category and state | BALANCED ± 1e-4 m² | exists |
| NSD-4 wall face | every wall-band segment contributes two faces (or one face and the exterior) × its length. Every face piece is assigned to a space or the exterior. Caps, column faces and reveal sides are listed | Σ assigned face length = 2 × Σ band length + caps + reveals − openings, per floor | **missing** |
| NSD-5 vertical | every space has a height record per trade (ESTABLISHED / BLOCKED with reason). Every void has an upper ceiling owner. Every stairwell has a full-height wall record | one record per (space, storey, trade) | partial (voids yes; stairwells no) |
| NSD-6 eligibility | the rule table (space kind × surface × trade) is explicit and versioned. Every eligible pair resolves to LINE / RFI(question id) / NOT_APPLICABLE(rule id) | no missing pair | **missing** (implicit) |
| NSD-7 quantity | per trade: Σ line quantities + Σ RFI measured geometry + Σ exclusions = Σ eligible surface geometry | balanced per floor | missing (it exists only for floor finish) |
| NSD-8 independent total | the partition and the element counts are compared with at least one independent source: reference areas, slab outline, printed areas or schedules (door / window schedule counts) | difference reported, never forced | partial (reference areas only) |
| NSD-9 stability | translate, rotate 30° / 45°, rescale the unit, explode blocks, re-order entities: NSD-1..7 outcomes unchanged | metamorphic suite | partial (Investigation A shows the gap) |

Severity:
- NSD-2, NSD-4 and NSD-6 failures should be **exit 3** (completeness failed) in V2.
- NSD-8 differences are REVIEW.
- NSD-9 is a test-suite gate, not a run gate.

## C.5 What the gate should claim today

Proposed wording, replacing "every surface accounted":

> **Plan-area faces and space × surface-type presence are accounted for. Elements (doors, windows, columns) are not yet conserved. Wall, reveal and vertical surfaces are not yet a per-face ledger. Accounted is not quantified.**
