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
| D-11 | Neighbour-side ground beams: black block "above and below, built from foundation level" (structural set page 1, notes box, note 2) | the note does not say how far "above" reaches | only up to the GF slab, or the whole GF wall on the neighbour boundary (26.37 m, GF-W00 / GF-W01) and the full north fence (31.17 m) | BLACK PROVISIONAL on those rows (owner rule: office notes override the fallback) | worker 2, T-107 |
| D-12 | Walls that contain columns (structural set page 8, recommendation 20: built at the column thickness) | architectural plans draw and print 0.15 for three runs with a column inside (GF-W28, 1F-W18, 1F-W23), and 0.20 for GF walls round 0.25-wide columns C3-C11 (column schedule page 9) | build at column thickness or as drawn, run by run | thickness as drawn, flagged CONFLICT; block m3 of these runs CONFLICT | worker 2, T-107 |
| D-13 | Foot of the east main-stair flight on 1F, 0.4025 m2 | the 1F plan leaves it between the last tread line and the landing; no section dimension settles it | tread or landing (1F living / landing floor 38.588 or 38.990 m2) | range 38.588 .. 38.990 m2, HELD between the two | worker 2 T-113; T-116 |
| D-14 | Footing blinding at the 8 footings drawn on the plot line | structural set p.13 prints blinding 10 cm past each face; these footings sit on the plot line | does the blinding project beyond the plot line or stop at it | 0.189 m3 HELD (15.179 m3 footing blinding otherwise released-ready) | worker 1 T-100 |
| D-15 | Blinding under foundation straps | p.13 prints blinding under footings and the four ground-beam sections, none under straps | blinding under straps or not | 0.913 m3 HELD, visible | worker 1 T-100 |
| D-16 | Column C8 | plan prints 30X80 (dimensioned 70 + 10); column schedule 30 x 90 | which size is the structure | CONFLICT, both volumes | worker 1 T-100; T-119 |
| D-17 | Annex roof +4.30 | section B-B puts +4.30 on top of one undivided ~0.23 m band; plans print roof terraces at finished levels; drainage prints 1 % falls on that roof | structural slab top of the annex roof and the roof build-up (falls screed, insulation, protection) | drawing-derived annex heights HELD (owner Q-54 B) | worker 3 T-112 (DCR-1); refines D-06 |
| D-18 | GF master bed room pool-side glazing W03 | head printed +5.30, above beam B8 (0.75 m) drawn on the same line (soffit at most +4.75) | beam upturned / moved, or a lower glazing head | CONFLICT | worker 3 T-112 (DCR-2) |
| D-19 | 1F east master bed room window W17 | crown +9.20 against CB12 (0.75 m) near the void | beam position and depth on that wall | CONFLICT to check | worker 3 T-112 (DCR-3) |
| D-20 | 1F-roof dome openings (open skylights, owner Q-29 / Q-44) | the west opening (4.42 m) lies over the 1F west master bed room and part of its two baths, their partition under it; the east one over the living area | ceiling and wall treatment under each opening (glazing at slab, at drum top +11.00, or a closed ceiling) and how the partition ends | HELD | worker 3 T-112 (DCR-4) |
| D-21 | 2F maid room dome | architecture draws a dome over the room; the structural slab is flat with no opening or ring | is there an opening and dome here | CONFLICT | worker 3 T-112 (DCR-5) |
| D-22 | Ceiling levels and floor build-up (all floors) | no reflected ceiling plan, no ceiling level, no build-up printed | ceiling levels per room and floor build-up per floor | every drawing-derived plaster / paint height HELD | worker 3 T-112; refines D-09 |
| D-23 | Closed 0.05 m element beside the arriving flight of the round reception stair on 1F (0.05 x 2.35 = 0.1175 m2) | the 1F plan draws two parallel lines 0.05 apart along the flight's outer side, closed at the arrival end, on the stair's layer, outside the printed 115 stair box but inside the printed living 480 | what it is (balustrade, upstand, stringer) and whether the floor finish runs under it | range: 1F living floor 38.459 .. 38.979 m2 HELD between (0.1175 of it this element, 0.4025 D-13) | worker 3 T-116 |
| D-24 | Build-up under slabs over outside air: GF entrance porch 19.181, GF side passage 5.640, GF pool court 14.020, 1F roof edges 6.791 m2 (45.632 m2 in all); two WET floors over outside air (1F bathroom over the passage 2.940 m2, 1F bathroom over the pool court 0.986 m2) | no plan, section (sheet 10 A-A), elevation (sheet 9) or structural detail draws a soffit finish, insulation, waterproofing or a drip under any of these slabs; the only insulation note is the pool tank's 5 cm membrane | soffit finish and build-up per place; insulation / waterproofing under the two wet floors | soffit areas CALCULATED, finish and build-up HELD (no Urban rule; one owner question for the finish via the Lead) | worker 2 T-121 |
| D-25 | 1F roof slab edge bands beyond the 1F walls: 0.20 m on the west and north of the 1F master-bedroom block (2.417 m2) and strips 0.29-0.40 m east of CB12 (part of 4.374 m2) | drawn on the 1F roof slab plan beyond the edge beams and on the 1F plan as an outer line 0.20 m off the wall; no section cuts them | slab edge, part of the beam, or a decorative band; its depth | soffit area CALCULATED; concrete class HELD (route G reads them as beam-strip faces) | worker 2 T-121 |
| D-26 | Roof-edge projection bands (البروزات) on the GF and 1F roof slab plans: 0.20 strips north of B20 / B23, 1F outer west strip 7.50 m, 1F strip 0.30 x 4.51 and SE box 0.30 x 0.90 outside CB12 (already D-05), plus three pieces with no engine band: GF outer west strip 0.20 x 4.10 m (0.820 m2), 1F 0.10 strip outside CB12 over 5.69 m (about 0.569 m2), 1F rounded box outside CB12 about 0.40 x 1.00 m (about 0.39 m2) | drawn as bands with rounded corners round the roof edges; slab note 1 (Arabic) says the contractor matches the parapet and projection details to the architectural drawings before casting; Sections A-A / B-B draw only the beam outline (no slab), so they neither show nor exclude the strips | section, depth and material of each projection; is it cast with the slab | HELD, visible; plan areas listed, no m3 where no depth is printed (refines D-05) | worker 3 T-110 |
| D-27 | Released beam spans whose schedule width differs from the drawn width: GF B29 (schedule 25, drawn 0.20, 6.74 m), GF CB2 two spans (20 / 0.25), GF B21 (45 / 0.40, inclined), 1F B6 vertical span at x 26.37 (25 / 0.20; the other four B6 spans are drawn 0.25) | schedule row vs two edge lines on the roof slab plans; no section cuts them | which width is the structure (as D-02 for CB10) | CONFLICT, both volumes: 5.022 m3 at schedule width / 4.549 m3 at drawn width (the engine releases the schedule width today) | worker 3 T-110 |
| D-28 | East dome-opening ring on the 1F roof slab (centre about 30.83, 41.65; R 2.211 / 2.411 m, 1.799 m2 in its box) | the west ring prints two B4 texts; the east ring prints no mark at all (only SEE DETAIL; the dome detail's ring is 20 wide, depth AS PER ARCH) | the section of the east ring (B4 as the west one, or another) | HELD, candidate 0.900 m3 at B4 (owner Q-61 C(3): B4 only where identified) | worker 3 T-110 |

## 2. Missing-scope register (unknown is never zero)

| M | Element | Why it is missing | Kept as | Link |
|---|---|---|---|---|
| M-01 | Sea-side boundary element 7.00 m | undefined by the drawings | visible unresolved line | D-01 |
| M-02 | Unlabelled beam spans (6) | no label | HELD candidate volumes | D-04 |
| M-03 | Second-floor top roof outline (membrane) | owner answer: held | HELD line | Q-34 |
| M-04 | Expansion joints on roofs (spacing, BOQ line) | owner Q-42 correction leaves spacing open | HELD; ask the owner when roof tile counts are built | Q-42 |
| M-05 | Substructure black block under the neighbour-side ground beams (note of D-11) | neither the T-103 hand table (superstructure) nor the freelancer (no row below ground) has it | 2 x 31.17 m centreline (building south line incl. the 1.40 m passage; north fence line); height: fence line PROVISIONAL >= 0.70 m (minimum excavation 1.50 m - two 0.40 ground beams, boundary-wall detail page 14), building line HELD (footing levels) | D-11; T-107, T-108 |
| M-06 | Three unlabelled GF spaces 8.13 m2 (renumbered from a second M-05 by the Lead 14:20) | T-099 census; T-016b reads two of them as the outdoor side passage (exterior paving) | HELD | T-099, T-016b |
| M-07 | Exterior soffit and the 1F slab over the GF open-air side passage: 4.08 of 5.64 m2 under a 1F bathroom and a master-bedroom corner (Lead 16:20, from T-109) | no soffit line; slab inclusion in the concrete ledger not checked; finish not printed | NOT MEASURED; census of every slab over open air is T-121; soffit finish HELD (no Urban rule) | T-109, T-121 |
| M-08 | Exterior soffit of the GF entrance porch under the 1F master-bedroom block, 19.181 m2 (4.60 x 4.096 + 4.40 x 0.20 + 0.02 - 1.40 x 0.40) | no soffit line in the engine, no freelancer row | CALCULATED area, finish HELD; slab concrete is in route G (2.721 m3) | T-121, D-24 |
| M-09 | Exterior soffit over the GF pool court, 14.020 m2 (printed VOID 4.373 m2 excluded); freelancer 19.154 m2 (exterior plaster, UNRESOLVED) | no soffit line in the engine | CALCULATED area, finish HELD; slab concrete in route G (1.443 m3) | T-121, D-24 |
| M-10 | Soffit of the 1F roof slab edges beyond the 1F walls, 6.791 m2 (east 4.374, west / north band 2.417) | no line in the engine, no freelancer row | CALCULATED area, finish HELD, band concrete class HELD | T-121, D-25 |

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
