# Designer clarifications, missing-scope register and status mapping (directive 2026-10-20, parts 2.2, 2.3, 4 (3))

Lead, 2026-10-20 12:20 UTC. A designer clarification is a question for the architect or the structural engineer (a drawing
conflict, an undefined element, a missing detail); it is never put to the owner as a multiple-choice decision (directive 2.3).
The owner forwards these to the designer when he chooses; until answered, each affected quantity stays HELD or CONFLICT and
VISIBLE in the BOQ, never 0. Workers add rows (next free D- number) with the evidence; the Lead keeps the list. No client names.

## 1. Designer clarification list (Alsenan)

| D | Element | What the documents show | What is needed | Quantity kept as | Raised by / task |
|---|---|---|---|---|---|
| D-01 | Sea-side boundary element, 7.00 m overall (6.00 solid + 1.00 gate, 0.20 m drawn) | GF plan draws it; the fence drawing does not | material, height, structure, foundation, finishes, railing / glazing, gate | HELD, visible line (owner Q-63 C) | verifier 11:35; T-103 |
| D-02 | Beam CB10 | schedule 0.25 x 0.50; drawn 0.30 wide (0.744 / 0.893 m3) | which width is the structure | CONFLICT, both volumes | owner Q-61 (1); T-110 |
| D-03 | GF CB3 and "B3 (with stair)" | two labels on one line | same beam, different types, or an extra member | HELD, never duplicated | owner Q-61 (2); T-110 |
| D-04 | Six unlabelled beam spans | drawn, no label | type and section of each | HELD with location, length and candidate volume | owner Q-61 (4); T-110 |
| D-05 | West outer strip, SE box, CB12 outer strip; strips north of B23 / B20 | drawn bands, sections incomplete | concrete beams or not | HELD | owner Q-61 (5), (6); T-110 |
| D-06 | Annex roof level +4.30 | one level mark | slab top, finished roof, waterproofing or screed | drawing-derived annex heights HELD | owner Q-54 B; T-112 |
| D-07 | Door schedule | no schedule; one printed height (main entrance 2.00 x 2.50) | door heights and types | heights ASSUMED 2.20 m (Urban fallback, owner Q-55) | T-091 |
| D-08 | Round reception stair | no section cuts it | section / riser count / landing levels | straight flights CALCULATED after check, curved HELD | owner Q-50; T-111 |
| D-09 | Ceilings | no ceiling layout, no cove detail | ceiling types, levels, coves | HELD | owner Q-57; T-112 |
| D-10 | Tile sizes and floor finishes | none printed on any sheet | finish schedule | areas measured, counts HELD | T-091; owner Q-59 |

## 2. Missing-scope register (unknown is never zero)

| M | Element | Why it is missing | Kept as | Link |
|---|---|---|---|---|
| M-01 | Sea-side boundary element 7.00 m | undefined by the drawings | visible unresolved line | D-01 |
| M-02 | Unlabelled beam spans (6) | no label | HELD candidate volumes | D-04 |
| M-03 | Second-floor top roof outline (membrane) | owner answer: held | HELD line | Q-34 |
| M-04 | Expansion joints on roofs (spacing, BOQ line) | owner Q-42 correction leaves spacing open | HELD; ask the owner when roof tile counts are built | Q-42 |
| M-05 | Three unlabelled GF spaces 8.13 m2 | T-099 census; T-016b reads two of them as the outdoor side passage (exterior paving) | HELD | T-099, T-016b |

## 3. Status mapping (directive 2.2; frozen outputs are not renamed)

New outputs use the seven statuses. Existing engine words are read this way when they are reported (Lead proposal for the
verifier to check against the engine's own definitions in UP-QTY-STATUS-001; it changes no quantity and no frozen output):

| Engine / board word | Directive status |
|---|---|
| RELEASED, not independently checked | CALCULATED |
| RELEASED and independently reconstructed by the verifier | VERIFIED |
| PROVISIONAL | PROVISIONAL |
| OWNER_STANDARD_ASSUMED (e.g. door 2.20 m) | ASSUMED |
| HELD, BLOCKED | HELD |
| UNRESOLVED where two applicable documents disagree | CONFLICT (otherwise HELD) |
| NOT_PRESENT with drawing evidence | NOT APPLICABLE (without evidence: HELD) |

Each quantity also names its basis when two exist (owner correction 12:15): OWNER MANUAL METHOD or DRAWING-DERIVED.
