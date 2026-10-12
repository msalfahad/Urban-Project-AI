# 04 Implemented in S1 versus future interfaces

The addendum allows a simple exact rectangular fixture. It must not be presented as a polygon optimiser. This table
separates what S1 calculates from what is only an interface, a BLOCKED state or a rule record.

## Calculated in S1 (and tested)

| Area | What is calculated | Limits |
|---|---|---|
| Rule store | Effective rule sets 1.4.0 and 1.5.0; overlay precedence; superseded list; digests; drift check | Convention profiles V1–V6 are referenced in place, not copied (frozen packages pin them) |
| Material specs | Membrane default and overrides; stricter-lap-wins from a data sheet; tile registry; custom tiles; packaging from a supplier input | No product database; corner / penetration systems are not modelled |
| Canonical line | Schema, validation, adapters for 7 legacy vocabularies, like-unit totals, bounded ranges, measure pairs, CSV / JSON | Approval workflow (review records, invalidation on revision) is validated, not driven |
| Route G lines | Every route G item becomes a canonical line with its own numbers; totals reconcile to the route summary | Structural only; no new structural measurement |
| Tile layout | Rectangle (or 4-vertex right-angled polygon): exact pieces per axis, three start alignments, two orientations, guillotine offcut reuse (best fit), kerf, minimum cut, minimum reusable offcut, packaging, spare | Straight pattern only; uniform joint; no perimeter gap; flat plane (no falls); offcuts never carried to another room; the cutting plan is a feasible heuristic, not a proven minimum |
| Membrane roll plan | Rectangle: floor strips, side and end laps, splicing, upturn band lanes, doorway pieces, whole rolls (first-fit), untouched tails as packaging surplus; full balance | Separate-band method only (no turned-up floor sheet); corners and penetrations counted, not quantified; roll tails never pooled across rooms |
| Waterproofing net surfaces | Floor, doorway pieces, upturn 0.20 m on the full boundary (UP-WP-002 v2.0.0), three doorway details (UP-WP-003 v1.1.0) | Rectangles only; door positions only needed for open band runs |
| Room BOQ | Schedule → lines, material results, comparisons, unresolved list; missing data → BLOCKED with the question | Rooms come from a schedule (synthetic or owner list), not from drawings |
| Workbook | 18 sheets; formula subtotals per room / floor / project; PARTIAL text when any row is unresolved; balance check per row; procurement per size with pooled boxes | Trades not measured in S1 list their families with the run state, no number |
| Coverage census | 99 families, terminal run state and reason per run | Capability column is the M9A audit's reading (8177ccf) |

## Interfaces only (BLOCKED or NOT_RUN in S1, by design)

| Interface | State in S1 | Planned |
|---|---|---|
| Polygon / L-shaped / holed rooms: tile and membrane layout | `BLOCKED: POLYGON_OPTIMIZER_NOT_IMPLEMENTED (S2)`; the net area is still exact (shoelace) | S2 |
| Patterns other than straight (brick bond, herringbone, diagonal) | `BLOCKED: PATTERN_NOT_IMPLEMENTED` | S2 |
| Rooms read from drawings (TS01 topology / room_slice wiring) | NOT_RUN; `rooms-check` validates a schedule only | S2 (room_slice still carries the v1.0.0 waterproofing rules: conflict C01) |
| Cross-room offcut reuse and roll-tail pooling | Reported per room; never credited | S2 |
| Wall tile height ladder (UP-CER-009) and wall-tile layouts with openings | Rule stored; no calculation | S3 |
| Skirting, ceilings, plaster / paint, marble, stairs finishes, railings 3D path, doors / windows, aluminium | Families listed with their state; no number | S3–S4 per roadmap |
| Membrane corner / penetration pieces | Counted, `NOT_QUANTIFIED` until a system defines them | When a system is named (Q-WP-2) |
| Turned-up floor sheet method | Not offered | S2 if the owner uses it |
| Formwork, earthworks, masonry, MEP | NOT_IMPLEMENTED / BLOCKED_BY_SOURCE | S4–S6 |
| Engineer review / approval records driving `RELEASED_FOR_PRICING` | Schema enforces the rules; no workflow | Later (M7 release policy) |
