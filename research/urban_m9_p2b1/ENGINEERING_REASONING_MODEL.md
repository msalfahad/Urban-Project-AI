# Engineering reasoning model (WP-2; deliverable 5 - construction reasoning model)

ARCH_TAKEOFF_V2.3. The engine reasons from evidence in a fixed order and records, for every space, door and line, the
evidence it used, the rule it applied and the state of the result. It never fills a gap with an invented fact: a gap
is a labelled assumption (an owner fallback), a document request, an owner question or an engineering defect.

## 1. Model

```
drawing --> faces (spaces) --+--> SPACE node: function (room word), interior status + evidence + confidence,
                             |                enclosure, finish scope, building part, level, area
openings (wall-band gaps) ---+--> EDGE: DOOR element (typed sides, CAD wall opening, frame, leaf, state, class)
door symbols (swings) -------+          PASSAGE (doorless opening)
                             |
knowledge registry ----------+--> rules (applicability, precedence) --> BOQ lines (rule id, state, inputs, notes)
project decisions -----------+                                      --> scenario views (AS_DRAWN / OWNER_REQUIRED)
                                                                    --> unresolved items --> question register (A..E)
```

| Module | Role |
|---|---|
| `engine/source/space_model.py` (SPACE_MODEL_V1) | spaces as nodes, doors and passages as edges; interior status; building parts (union-find over interior spaces); connecting-space candidates; project decisions bound to one space |
| `engine/source/door_model.py` (V2.1 .. V2.3) | one element per physical door, typed sides (SPACE / FACADE / EXTERIOR_SPACE), class from the sides, main-entrance reconciliation, release guards |
| `engine/source/door_standards.py` | door category, owner opening standard, heights, scenarios, dependency map, elevator schedule |
| `engine/source/owner_finish_scope.py` | finish scope (WET / DRY / NONE / REVIEW), wall-tile height, thresholds, jamb plaster, passage-jamb skirting, exterior waterproofing |
| `engine/source/knowledge.py` | the registry: rule lookup, precedence, wet codes, door standards, reference heights, question classification and grouping |
| `engine/source/surface_ledger.py` | element x surface x trade ledger: every line in exactly one record, every record with an authority and a status |

## 2. Space status: evidence order (UP-SPACE-001)

1. a project decision bound to this space (UP-SPACE-002, precedence PROJECT_DECISION) - confidence HIGH;
2. an exterior room word (balcony, terrace, roof, garden, court, pool) -> EXTERIOR - HIGH;
3. an interior room word (a room function implies an enclosed room) -> INTERIOR - HIGH;
4. an unlabelled space with a doorless opening to the facade -> POSSIBLY_EXTERIOR - MEDIUM;
5. an unlabelled space every connection of which leads to interior spaces and with no facade door -> INTERIOR by
   enclosure - MEDIUM, recorded as an inference;
6. otherwise UNKNOWN - never assumed interior.

A non-interior space that joins two otherwise separate interior building parts is reported as a **connecting space**:
evidence for a project decision (for example an outdoor service corridor), never applied automatically. On the
reference plan the model finds one such space (POSSIBLY_EXTERIOR, joining two building parts) - the corridor the
owner describes - and leaves it to the bound project decision.

## 3. Door classification: evidence order

| Step | Evidence | Result |
|---|---|---|
| 1 | a lift space on a side, or a lift door block | ELEVATOR - excluded from door quantities; on the elevator schedule |
| 2 | two interior spaces | PVC; BATHROOM_PVC when a side is a bathroom (bathroom standard) |
| 3 | one interior space and the facade or an exterior space | ALUMINIUM (external standard) |
| 4 | a side that is an unlabelled space with a doorless facade opening (V2.2 F-20) | CLASS_REVIEW, withheld - unless a project decision settles the space (EXTERIOR -> aluminium; INTERIOR -> PVC) |
| 5 | a door into a shaft (V2.2 F-22) | CLASS_REVIEW / lift-entrance candidate, withheld |
| 6 | the external door of the entrance floor with an entrance word in or near its space | MAIN_ENTRANCE (as drawn) |
| 7 | an external door opening into a hall / living space without an entrance word | MAIN_ENTRANCE_CANDIDATE, withheld; **V2.3: never a door to a balcony or roof** |

Each element row of `DOOR_SCENARIOS.json` carries `category_basis` (the sentence that justified the category), the
sides and their evidence, and `flags` (OPENING_BELOW_OWNER_STANDARD, HEIGHT_ASSUMED, WIDTH_HELD, PROVISIONAL_WIDTH,
CLASS_NOT_SETTLED_SAME_STANDARD ...).

## 4. Rule applicability and precedence (UP-KB-PREC-001)

APPROVED_DRAWING (1) > APPROVED_SPECIFICATION (2) > VERIFIED_GEOMETRY (3) > PROJECT_DECISION (4) > OWNER_RULE (5) >
ASSUMPTION (6) > UNRESOLVED (7).

Applied cases:
- **Wall-tile height**: an explicit source or project height governs the owner full-height rule; when lower it is
  flagged WALL_TILE_BELOW_OWNER_FULL_HEIGHT (C, resolved by precedence, not asked).
- **Door width**: the CAD wall opening is never overwritten; the owner standard is a separate OWNER_REQUIRED view.
- **Door height**: facts height (schedule / section / elevation, SOURCE) > project fallback DOOR_ASSUMED > owner
  reference height (ASSUMED). An assumed height never produces a CONFIRMED area.
- **Wet scope**: the owner wet-area list applies to a closed room whose functions are all wet; an open plan of a wet
  and a dry function keeps the dry treatment and asks for the zone line (B), never spreading the wet scope.

## 5. Question register (UP-KB-QUES-001)

Every unresolved item is classified against the catalogue (35 reason patterns, first match wins, each pattern proved
reachable by its own example):

| Category | Meaning | What the engine does |
|---|---|---|
| A_ESTABLISHED | an approved rule answers it | applies the rule; an A item left in a V2.3 run is a defect (`established_but_still_raised` must be 0) |
| B_MISSING_DRAWING_EVIDENCE | a rule exists, the drawings do not show whether it applies | a document request (schedule, section, label), not a policy question |
| C_RULE_CONFLICT | two approved statements, or a drawing and an owner rule, disagree | keeps both facts; resolved by precedence (flagged) or an owner question when precedence is silent |
| D_MISSING_OWNER_POLICY | no approved policy exists | one owner question per group (OQ id) |
| E_ENGINEERING_DEFECT | the engine cannot read / attribute something | engineering backlog, never an owner question |

Repeated instances are grouped: one group per underlying question with its instance count, floors, items and three
examples. An item no pattern matches is reported as unclassified (never dropped). On the reference plan the 213
unresolved items (no heights) become 13 B groups, 3 D groups (3 owner questions) and 2 E groups.

## 6. Per-element reasoning record (what an auditor can read)

| Object | Where | Reasoning recorded |
|---|---|---|
| space | `SPACE_MODEL.json` | status, basis, evidence sentences, confidence, finish scope, building part, connecting parts |
| door | `DOOR_SCENARIOS.json` | category + basis, sides, CAD / frame / leaf widths, height + source + state, owner standard, enlargement, flags, dependency impacts |
| BOQ line | `BOQ_LINES.json` | rule id + rule-set digest, evidence state, formula, inputs (height state, strips, sides), notes |
| surface | `SURFACE_LEDGER.json` | authority, status, blocker or conditions, line ids (every line in exactly one record) |
| question | `OWNER_QUESTIONS.json` | category, group, rule, request / question id, instances, floors, examples, history (earlier ids) |

## 7. What the model never does (tested)

- infer interior status from a label alone for an unlabelled corridor, or default an unlabelled space to interior
  (`test_an_unlabelled_space_is_never_assumed_interior`);
- apply a project decision to more than the one space containing its point
  (`test_a_project_decision_binds_one_space_only`);
- let an INTERIOR project decision make a door aluminium (a defect found and fixed in this phase;
  `test_a_pantry_door_to_an_indoor_corridor_stays_pvc`);
- ask an established rule, or put an engine defect on the owner list
  (`test_established_rules_are_never_asked`, `test_engine_defects_are_never_owner_questions`);
- change any V1 .. V2.2 output (308 of 308 snapshot files byte-identical; `test_v2_2_never_reads_the_registry`).

## 8. Acceptance (WP-2)

"The engine must explain why it classifies a door or surface without inventing facts" - met for doors
(`category_basis`, side evidence, flags), spaces (status basis and evidence), surfaces (ledger authority and blocker)
and lines (rule id, formula, inputs, notes). Limits: room function still comes from room words, tags or fixtures; a
space with no word and no decisive connectivity stays UNKNOWN / POSSIBLY_EXTERIOR and its doors are withheld - the
engine asks for the label rather than guessing.
