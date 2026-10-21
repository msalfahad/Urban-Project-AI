# T-080: reference-book checks for waterproofing, floors, wall tiles, plaster and paint

Worker 3, 2026-10-19 (run 17:00 UTC). NO REPO CODE task: reading only, no engine change, no quantity released.
A book is evidence, never a rule (docs/agents/REFERENCE_SOURCES.md): every item below either agrees with an Urban rule,
differs from it (the owner rule governs and the difference is recorded), or has NO RULE and becomes a test specification
or an owner question. Books are cited by Drive folder, title and page only; no page is copied.

## 0. What could be read (and what could not)

| Source (Drive "Engineering Sources - Urban Projects") | How read | Coverage |
|---|---|---|
| 02 Construction Books / "عين المشرف" (33 MB) | Drive text read (101,937 characters; Arabic glyphs stored in visual order, read line by line) | the WHOLE book: 140 pages, all 182 numbered errors in 12 stages. Stages read in full for this task: 04 backfill and ground slab (errors 048-062, pp. 39-47), 05 waterproofing (063-077, pp. 49-58), 08 masonry and plaster (108-122, pp. 81-89), 09 tiles and cladding (123-137, pp. 91-99), 10 gypsum and paint (138-152, pp. 102-111) |
| 01 Kuwait References / "المواصفات العامة للمباني والأشغال الهندسية - الكويت 1990" (11.8 MB) | Drive text read and full-text search snippet | NOT READABLE for this task. Both return the same first 97,008 characters only: the front matter, the table of contents and Division 01-02 up to chapter 02230 (asphalt paving), page 80. Chapters 07100 (waterproofing), 09200 (plaster), 09300 (floors), 09400 (wall cladding) and 09900 (paint) are listed in the table of contents but their text is past the cut. The file is over the ~6.2 MB download limit. Needed: those five chapters as separate PDFs under 6 MB (data request for the Lead, section 5) |
| 05 Technical Training / "Waterproofing Installation Training Manual" (3.1 MB; added because the Kuwait chapter 07100 could not be read: same topic, the owner's REFERENCE_SOURCES list) | downloaded to the session scratchpad and read as page images (its text layer is unreadable: wrong font mapping) | the whole 90-page manual scanned; the measurement chapter (unit 2, pp. 35-41) and the membrane / liquid / maintenance steps (pp. 7-21, 74) read in full. It is a Saudi vocational training manual (TVTC), not a Kuwait specification |

Page numbers below are the books' own printed page numbers.

## 1. Waterproofing (the chapter the task asks to list in full)

### 1a. Supervisor's eye, stage 05 "waterproofing" (errors 063-077), every item

| Err. | Page | What the book says (paraphrase) | Touches a quantity? | Urban rule | Agrees / differs | Test specification or question |
|---|---|---|---|---|---|---|
| intro | 49 | the system fails at one point, always an edge, a penetration or a drain; do not start before the falls are complete and the base is dry; do not cover before a documented flood test; do not hand over before a protection layer | no (sequence); the edge / penetration / drain list is the item list of UP-WP-004 | UP-WP-004 | agrees | none |
| 063 | 50 | flood test shortened or skipped; ask for the record with water depth, duration and photos | no (QA) | none needed | - | none (the manual, p. 42-43, gives 10-15 cm for at least 48 h, 48-72 h; QA, not a BOQ line) |
| 064 | 51 | membrane pierced by a later trade after the test (worst error of the stage) | no | - | - | none |
| 065 | 52 | falls made in the tile bedding instead of a falls layer under the membrane; measure the falls layer before waterproofing | YES: a falls screed under the membrane is its own layer | NO RULE (coverage family B13-01 "screed to falls" and B3-05 "screed / build-up" are NOT_IMPLEMENTED; no rule in rules/ or knowledge 1.6.0) | - | owner question Q-41 |
| 066 | 52 | membrane stops at the tile edge and does not rise up the wall in the shower zone; set the height in the detail and photograph it | YES: shower-zone wall tanking above the 0.20 m upturn | UP-WP-004 v1.1.0 in rules 1.5.0 is PROPOSED only ("higher tanking is separate", open Q-WP-4); knowledge UP-WP-003 gives 0.20 m on every wall | NO RULE for the shower height | owner question Q-40 |
| 067 | 53 | corners and wall-floor junctions without tape or reinforcement | YES (corner pieces, lm or pcs) | knowledge UP-WP-004 (corners counted from the polygon; quantity only from the system detail, else withheld and named) | agrees | test T80-WP-3 (count) |
| 068 | 53 | drain and pipe penetrations without collars; the most frequent leak point | YES (pcs) | knowledge UP-WP-004 (FLOOR_DRAIN / PIPE_PENETRATION counted from drawn symbols); rules UP-CER-008 (drains counted) | agrees | test T80-WP-3 (count) |
| 069 | 54 | one coat of liquid membrane instead of two crossed coats; compare consumption with the data sheet | material only (litres / kg of a liquid system) | UP-WP-MAT-001 (one procurement group per system; system BY_SPEC); no coat rule because the Urban default is a sheet membrane (MEM-URBAN-DEFAULT-1x10) | no conflict while the system is a sheet; NO RULE for a liquid system | listed for the Lead (L-4), no question now: Alsenan's system is not named |
| 070 | 54 | membrane on a wet or dusty base; clean, dry, use the system's primer | material: primer m2 / cans | NO RULE (UP-WP-MAT-001 B_installed lists no primer) | - | listed for the Lead (L-4) |
| 071 | 55 | products of different systems mixed | no (procurement grouping) | UP-WP-MAT-001 "incompatible membrane systems in one procurement total: never" | agrees | none |
| 072 | 55 | no protection layer before other trades walk on it; lay it right after the flood test | YES: protection screed over the membrane | NO RULE (same families as 065) | - | owner question Q-41 |
| 073 | 56 | bathroom floor level equal to or higher than the next space; set it lower in the levels | no quantity; a drawing check | none | - | check for the plan reader (L-5): printed FFL of each wet room vs its neighbour |
| 074 | 56 | one drain in a large bathroom, or a drain far from the shower | no quantity (count of drains is UP-CER-008) | UP-CER-008 | - | none |
| 075 | 57 | roof membrane with no UV protection or cover layer | YES: roof protection / cover layer | UP-WP-ROOF-001 (system by specification, PROVISIONAL); no cover-layer rule | NO RULE for the cover layer | inside owner question Q-41 (roofs) |
| 076 | 57 | no map of repair locations | no | - | - | none |
| 077 | 58 | membrane not continuous under the bathroom door threshold; water reaches the corridor floor; build an approved threshold detail | YES (doorway piece) | rules UP-WP-003 v1.1.0 (membrane continues through the doorway, door width x wall depth); knowledge UP-WP-DOOR-001 (transition by detail, withheld without one); owner Q-35 answer (option C: doorway transition line per door) | agrees | test T80-WP-2 |

### 1b. Waterproofing Installation Training Manual (05), quantity items

| Item | Page | What the manual says | Urban rule | Agrees / differs |
|---|---|---|---|---|
| Unit of measurement | 35 | horizontal waterproofing of bathrooms, kitchens, floors and roofs in m2 = length x width of the waterproofed surface | rules UP-WP-001 (wet-room floor m2) | agrees |
| Wall upturn of a wet room | 35 (note) | the vertical turn-up on the walls ("النعلة / الوزرة") is included in the m2 rate of the horizontal waterproofing and is NOT measured in the area or the cost | rules UP-WP-002 v2.0.0 (upturn = whole boundary x 0.20 m, reported as its own quantity); owner Q-30 example (14.80 m2 = 12.00 floor + 14.00 lm x 0.20); owner Q-35 answer (upturn per wet area, walls only + doorway line) | DIFFERS: RULE_DIFFERENCE. The owner rule governs. The freelancer also lists the upturn separately (his sheet has "نعلات العازل للحمامات" rows, 144.61 lm on Alsenan), so the engine, the owner and the freelancer agree and only the manual differs |
| Worked example | 36 | bathroom 4 x 3 m: 12 m2 | - | under Urban rules the same bathroom reports 12.00 m2 floor + 14.00 lm / 2.80 m2 upturn (+ doorway line per Q-35) |
| Vertical and sloped faces | 36-39 | tank walls: perimeter x height; sloped faces measured on the slope | UP-WP-ROOF-001 / UP-WP-003 (wall faces) | agrees (measured on the true face) |
| Raft example | 40 | raft 40 x 20 m with 0.60 m sides: 2 x (40 + 20) x 0.60 + 40 x 20 = 72 + 800 = 872 m2 | not a villa wet-area case | consistent: where a vertical face is itself waterproofed it is measured |
| Rolls to buy | 41 | roll 10 x 1 = 10 m2; with a 10 cm lap on each side the useful area is 9.9 x 0.9 = 8.91 m2; rolls = (area / 8.91) x 1.1, "10 % added when estimating materials"; 872 m2 -> 107.7 -> 108 rolls; primer cans = (area / coverage per can) x 1.1 | rules UP-WP-005 (strips from the roll layout, min lap 0.10 m; NEVER a fixed waste percentage, NEVER net area / roll area as the roll count); knowledge UP-WP-LAY-001, UP-WP-MAT-001 | DIFFERS: RULE_DIFFERENCE (the owner rule governs; the 0.10 m lap itself agrees) |
| Laps | 19, 74 | torch-on sheets: overlap 10-15 cm; repairs: at least 10 cm, and new membrane laps 25 cm onto the sound old membrane | UP-WP-002 knowledge / rules UP-WP-005 (0.10 m minimum, a larger data-sheet lap wins) | agrees (0.10 m is the lower end of the book's range) |
| Layers | 19-21, 74 | sheet systems in two layers, the second laid across the first after 24 h; liquid bitumen in two crossed coats | MEM-URBAN-DEFAULT-1x10 is one sheet layer; layers are a system choice (UP-WP-MAT-001) | no conflict; a two-layer system doubles the installed membrane and the rolls (L-4) |
| Protection layer | 7, 14, 18, 20, 21, 74 | cement mortar protection over the membrane, 2-3 cm ("not less than 2 cm", "= 3 cm", "average 3 cm"); vertical faces protected by a half-brick wall | NO RULE | owner question Q-41 |
| Flood test | 42-46 | 10-15 cm of water, 48-72 h; tanks full for 72 h / one week | QA only | none |

### 1c. What the manual's roll formula gives on the owner's own cases (hand calculation, for comparison only)

Manual formula (p. 41): rolls = ceil((A / 8.91) x 1.10). Urban method: strips of the 1.00 m roll with 0.10 m laps, upturn
folded from the same strip (owner Q-30), rolls from the cutting plan.

| Case | Manual basis A | Manual rolls | Urban (owner) result | Note |
|---|---|---|---|---|
| Owner's Q-30 kitchen 3.00 x 4.00 m | 12.00 m2 (floor only, upturn not measured) | 12.00 / 8.91 = 1.347; x 1.10 = 1.481 -> 2 | 16.28 m2 cut, 2 rolls, 3.72 m2 offcut (owner's own example) | same roll count, but the manual hides 4.28 m2 of cut membrane in its 10 % |
| Alsenan, 17 wet areas, floor only (T-074 hand table) | 72.122 m2 | 72.122 / 8.91 = 8.094; x 1.10 = 8.904 -> 9 | cut membrane 116.951 m2 (smaller direction per room); 12 rolls lower bound with every offcut reused, 19 if each area alone (T-074); T-072 engine table 13 provisional (board figure, not re-measured here) | the manual's 9 rolls cannot cover 116.95 m2 of cut strips (9 x 10 = 90 m2): it under-buys by at least 3 rolls (-25 % against the 12-roll lower bound) |
| Alsenan, floor + upturn surface | 72.122 + 144.729 x 0.20 = 101.067 m2 | 101.067 / 8.91 = 11.343; x 1.10 = 12.477 -> 13 | as above | coincides with the T-072 provisional 13, by chance: the 10 % is not a cutting plan |

Lesson: the textbook ratio method is exactly what UP-WP-005 forbids, and the Alsenan numbers show why: floor-only ratio
buys 9 rolls where the strips need at least 12.

## 2. Floors and wall tiles (supervisor's eye stages 04 and 09)

| Err. | Page | Book (paraphrase) | Quantity? | Urban rule | Agrees / differs | Test or question |
|---|---|---|---|---|---|---|
| 049 | 40 | backfill in layers thicker than the compactor can take; set the layer thickness by the equipment | layer count only (no number given) | none for villa finishes | - | none |
| 054 | 43 | damp-proof sheet under the ground slab torn or without enough overlap | YES: DPM m2 with laps | NO RULE (no ground-slab DPM rule; the 0.10 m lap rule is for waterproofing membranes) | - | listed for the Lead (L-3), not asked now: no Alsenan ground-bearing slab line is in scope of this task |
| 055 | 44 | ground slab without contraction joints | YES: joints lm | NO RULE | - | L-3 |
| 056 | 44 | ground-slab level not computed for all finish thicknesses: fix the final floor level first, then subtract the layers | heights (build-up) | owner Q-14 answer (never subtract an assumed build-up; use sections) | agrees in principle: the layers must come from the drawing / spec | see finding F-1 |
| 057 | 45 | slab flatness not suitable for sensitive finishes -> an extra levelling layer not in the budget | YES: levelling screed m2 | NO RULE (B3-05 NOT_IMPLEMENTED) | - | inside Q-41 (screeds) |
| 123 | 92 | tiling started from a random corner without a dry layout; narrow cuts at the entrance | YES: cutting waste | rules UP-CER-010 (waste from the room layout for the selected size); knowledge UP-WP-LAY-001 for membranes | agrees | test T80-TILE-1 |
| 124 | 93 | incomplete adhesive coverage behind tiles (worst error of stage 09) | material only | none | - | none |
| 125 | 94 | adhesive class not matched to tile size / location | material only | none | - | none |
| 126 | 94 | zero joints or joints narrower than the material allows; set the joint width before starting | YES: the layout pitch is tile + joint, so the tile count and the cut pieces change | UP-CER-010 and the TILE specs (rules/materials) carry no joint width | NO RULE | test T80-TILE-1 + draft question L-1 for the Lead |
| 127 | 95 | perimeter joint filled with mortar; leave it free before the skirting | no (detail) | - | - | none |
| 128 | 95 | no movement joints in large areas; approve a joint plan by area before starting | YES: movement joints lm (+ sealant) | NO RULE | - | draft question L-2 for the Lead |
| 129 | 96 | lippage between tiles over the tolerance | no | - | - | none |
| 132 | 97 | movement joints grouted rigid; fill with a flexible sealant | YES: sealant lm (same run as 128) | NO RULE | - | L-2 |
| 133 | 98 | falls measured only before tiling; measure after laying | no (QA) | - | - | none |
| 135 | 99 | external stone cladding by adhesive only for large / heavy pieces; require mechanical fixing | YES: anchors (facade) | NO RULE | - | outside this task's trades; noted |

## 3. Plaster and paint (supervisor's eye stages 08 and 10)

| Err. | Page | Book (paraphrase) | Quantity? | Urban rule | Agrees / differs | Test or question |
|---|---|---|---|---|---|---|
| 110 | 83 | no mesh where blockwork meets concrete; mesh of enough width on both sides | YES: mesh strip lm along every block / column and block / beam junction | NO RULE (URBAN-FINISH-EXTRAS-SEPARATE-ITEMS lists corner beads, spatter dash, reveals, not junction mesh) | - | listed for the Lead (L-6) |
| 111 | 83 | service chases closed without mesh before plaster | lm of chases (not drawn) | none | - | none (chases are not on drawings) |
| 113 | 85 | thick plaster in one coat to hide an out-of-plumb wall; extra thickness in two coats | coats / thickness: material only | none | - | none (m2 unchanged) |
| 114 | 85 | spatter dash and plaster on the same day | spatter dash is its own layer | URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1 (spatter dash m2 is its own item) | agrees (the freelancer also has "طرطشة" lines) | none |
| 117 | 87 | corners and edges not plumb; use approved metal corner beads | YES: corner beads lm | URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1 (plaster corner beads lm, separate item) | agrees (freelancer has "زوايا م.ط" lines) | none |
| 119-120 | 88 | joints not left where the material changes or the wall is long | mesh / joint lm | NO RULE | - | L-6 |
| 121 | 89 | lintels without enough bearing on both sides of the opening | lintel length = opening + 2 x bearing | not checked here (blockwork / lintel rules are outside the five trades of this task) | - | noted for a blockwork task |
| 138 | 103 | false-ceiling level fixed before the deepest service duct is known; take the level from an approved coordination section | YES: paint height and wall-tile height in rooms with a false ceiling | owner Q-14 answer (do not subtract an assumed false-ceiling depth; use sections and elevations) | agrees with the owner; DIFFERS from `engine/source/finish_height.py:31` (CEILING_ALLOWANCE_M = 0.150, method URBAN-PAINT-TO-FINISHED-CEILING@v1) | finding F-1 |
| 143 | 105 | no movement joints in large gypsum ceilings | lm | NO RULE | - | none now |
| 144 | 106 | paint on plaster that has not cured or dried | no | - | - | none |
| 146 | 108 | no primer, or the wrong primer | coats: material only | none (no coat rule for paint) | - | listed for the Lead (L-4): number of coats is a material quantity, not an m2 |
| 148-151 | 109-110 | colour from a catalogue, inspection light, dust, masking tape | no | - | - | none |

The supervisor's eye prints no coat counts, no plaster thickness and no paint coverage: it gives inspection points, not
measurement rules. Those numbers sit in the Kuwait specification chapters 09200 and 09900, which could not be read (section 0).

## 4. Findings and test specifications (for later code tasks)

**F-1 (defect candidate, no owner question needed: the owner already answered Q-14).** `engine/source/finish_height.py:31`
sets `CEILING_ALLOWANCE_M = 0.150` and line 72 computes the paint height as interval - build-up above - D_ctrl - 0.150
(method URBAN-PAINT-TO-FINISHED-CEILING@v1, register V1); register V3 adds URBAN-RESIDENTIAL-FLOOR-BUILDUP-FALLBACK@v1
(0.10 m build-up). Owner Q-14 (2026-10-19): "Do not subtract an assumed floor build-up or false-ceiling depth; use elevations
and sections". The supervisor's eye error 138 (p. 103) and error 056 (p. 44) point the same way: both levels come from
coordinated sections. The released V2.9 path does not import finish_height (grep: only finish_height_v3, wall_height and
the research labs under research/external_engine_lab do), so no released quantity is affected today; the wiring task for
plaster / paint heights (T-013 / T-035 follow-ups) must not use the 0.150 allowance or the 0.10 build-up fallback. Test
specification T80-HGT-1: interval 4.50 m, slab soffit D 0.16 m, no printed ceiling level, no printed build-up ->
paint height HELD (reason: ceiling level not printed), never 4.50 - 0.10 - 0.16 - 0.15 = 4.09 m.

**T80-WP-1 (roll count is never a ratio).** Owner's Q-30 kitchen 3.00 x 4.00 m, roll 1.00 x 10.00 m, lap 0.10 m, upturn
0.20 m: expected cut 16.28 m2, 2 rolls, offcut 3.72 m2 (owner). Adversarial: the manual's ratio (12 / 8.91 x 1.10 = 1.48 ->
2) must not be the code path: a 3.00 x 6.70 m room gives floor 20.10 m2 -> ratio 20.10 / 8.91 x 1.10 = 2.48 -> 3 rolls,
while the strips (4 strips 0.80 + 0.90 + 0.90 + 0.40 across 3.00 m, each 6.70 + 0.40 = 7.10 m long; 3 x 7.10 + 0.70 x 7.10
= 21.30 + 4.97 = 26.27 m2 cut) need 3 x 7.10 m pieces from 10 m rolls = 3 rolls for the full strips plus the 0.70 strip:
4 rolls if the room is done alone (a 7.10 m piece leaves a 2.90 m remainder that cannot hold another 7.10 m piece). Expected:
4 rolls alone; the ratio's 3 is wrong.

**T80-WP-2 (doorway continuation, owner Q-35 option C).** 2.45 x 2.05 m bathroom, one 0.80 m door in a 0.20 m wall:
floor 5.0225 m2; doorway floor piece 0.80 x 0.20 = 0.16 m2 (rules UP-WP-003 v1.1.0); wall upturn on the walls only
(9.00 - 0.80) x 0.20 = 1.64 m2; doorway transition: 1 pcs, width 0.80 m, quantity HELD until the project's threshold detail
(UP-WP-DOOR-001). Supervisor's eye error 077 (p. 58) is the site reason for the separate line.

**T80-WP-3 (corners and penetrations are counted, never priced without a detail).** L-shaped bathroom 3.00 x 2.00 m with a
1.00 x 1.00 m corner removed, one floor drain, one WC outlet: internal corners where two upturned walls meet = 5 (the L has
6 corners: 5 internal at 90 deg seen from inside, 1 external), external 1, FLOOR_DRAIN 1, PIPE_PENETRATION 1; extra membrane
m2 for them: HELD (named: system detail missing), never 0 and never in a total (knowledge UP-WP-004).

**T80-TILE-1 (layout with joints).** 3.00 m wall-to-wall run, 60 x 60 cm tiles: joint 0 -> 3.00 / 0.60 = 5.000 tiles, no cut;
joint 3 mm -> pitch 0.603 m, 3.00 / 0.603 = 4.975 -> 4 full tiles + one cut of 3.00 - 4 x 0.603 = 0.588 m, i.e. 5 pieces with a
cut, 0.012 m of offcut per row. A layout without a joint width therefore says "no cutting" where there is one. Expected:
joint width is an input; missing -> the layout is reported AS IF ZERO JOINT, labelled, or held (owner choice, draft L-1).

## 5. For the Lead: data request, questions not asked, and the two asked

Data request (Kuwait specification 1990): the Drive text read stops at page 80 (chapter 02230); chapters 07100, 09200,
09300, 09400 and 09900 are not reachable and the file is over the download limit. Ask the owner to put those five
chapters on Drive as separate PDFs under 6 MB (page ranges from the table of contents), like the single architectural
sheets. Until then every Kuwait-specification check of this task is NOT DONE (not "agrees").

Asked (OWNER_QUESTIONS.md, most money first): Q-40 shower-zone wall tanking height (every bathroom with a shower;
Alsenan first floor: at least two shower zones of about 3.5-3.7 lm of wall each); Q-41 falls screed under and protection
screed over the membrane, wet areas and roofs (Alsenan: 72.12 m2 of wet floors and 204-285 m2 of roof).

Not asked (drafts, lower money or no Alsenan line yet):
- L-1 tile joint width in the layout (T80-TILE-1): owner choice between a project joint width, a stated default, or the
  zero-joint layout labelled.
- L-2 movement joints in large tiled floors (supervisor's eye 128, 132): lm of joint and sealant per joint plan; NO RULE.
- L-3 ground-slab damp-proof sheet and contraction joints (054, 055).
- L-4 material lines of a named system: primer, number of coats or layers of a liquid or two-layer membrane, paint primer
  and coats (069, 070, 146; manual pp. 19-21): material quantities, not m2; ask when a project names its systems.
- L-5 plan-reader check: wet-room FFL lower than the neighbour (073).
- L-6 junction mesh (110, 119-120): lm along every block / concrete junction to be plastered.

## 6. Engine vs freelancer effect

None: research only, no engine quantity changes. The freelancer comparison above (upturn listed separately on both sides,
no screed or protection lines on either side, his "طرطشة تحت نعلة" spatter dash and "زوايا" corner bead lines present) is
read from tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json labels, not re-measured.
