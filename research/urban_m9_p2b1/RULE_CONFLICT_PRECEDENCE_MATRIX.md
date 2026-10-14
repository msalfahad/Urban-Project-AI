# Rule conflict and precedence matrix (deliverable 4)

Generated from the registry (`precedence`, `conflicts`, rule UP-KB-PREC-001).

## Precedence of evidence (UP-KB-PREC-001)

| Rank | Evidence | Use |
|---|---|---|
| 1 | APPROVED_DRAWING | a dimension, label or note on an approved drawing governs every rule below it |
| 2 | APPROVED_SPECIFICATION | a schedule or specification (door schedule, finish schedule, section heights) |
| 3 | VERIFIED_GEOMETRY | geometry the engine verifies itself (a strip that fits its opening, a closed face) |
| 4 | PROJECT_DECISION | a decision bound to one space of one project (URBAN_PROJECT_DECISIONS_V1) |
| 5 | OWNER_RULE | an owner-approved general rule (this registry) |
| 6 | ASSUMPTION | an owner fallback, labelled ASSUMED (HEIGHT_ASSUMED / AREA_ASSUMED); never confirmed |
| 7 | UNRESOLVED | no evidence: the item is withheld and asked for (B / C / D) or reported (E) |

Physical-fact hierarchy: 1 approved drawing dimensions and schedules > 2 approved project specifications and details > 3 verified geometric evidence > 4 project-specific owner decisions > 5 general owner rules > 6 labelled assumptions > 7 unresolved questions

## Conflict register

| Id | Between | State | Resolution |
|---|---|---|---|
| CF-01 | UP-DOOR-MIN-001; UP-DOOR-OPEN-002 | RESOLVED | the owner correction supersedes the Part C section 7 dimensional reading |
| CF-02 | data/registry/OWNER_METHOD_FACTS.json#/facts/2; URBAN-WET-SERVICE-MARBLE-THRESHOLD; UP-THR-001 | RESOLVED | the 'marble only if explicit' fact is project-specific (one other project's revision); the Urban-wide rule and the master prompt govern the reference project and new projects |
| CF-03 | URBAN-WET-SERVICE-MARBLE-THRESHOLD (pantry not applicable); UP-WET-001 (pantry is wet); UP-THR-001 | CONFLICTED | wet scope applies to an enclosed pantry; its doorway threshold is measured PROVISIONAL with the conflict named; owner question OQ-01 |
| CF-04 | URBAN-WET-WALL-TILE-FULL-HEIGHT@v1; UP-CER-009 | RESOLVED | full height is the face's own derived clear height (UP-FIN-WALL-001); no universal constant |
| CF-05 | data/registry/OWNER_METHOD_FACTS.json#/facts/1 (dry / wet split at the door plane); UP-THR-001 | RESOLVED | where a marble threshold is built the wet and dry floors end at the marble; the door-plane split is that other project's own method |
| CF-06 | UP-DOOR-MIN-001 main entrance 1.00 m minimum; UP-DOOR-CLS-004 | RESOLVED | the main entrance is measured as drawn and specified (owner correction) |
| CF-07 | arch_rooms LEXICON LAUNDRY = WET; UP-WET-001 laundry project-specific | RESOLVED | laundry keeps the wet scope with the flag WET_SCOPE_PROJECT_CONFIRMATION |
| CF-08 | URBAN-SKIRTING-OPENING-METHOD (doorless-opening jambs skirted); arch_measure skirting (passage jambs never skirted) | RESOLVED | category E: the rule was not implemented; ARCH_TAKEOFF_V2.3 adds PROVISIONAL passage-jamb skirting |
| CF-09 | UP-WP-002 v2.0.0 (0.20 m upturn); engine/source/waterproofing_policy.py wet() (0.15 m, the 1.4.0 value) | RESOLVED | the 1.5.0 owner decision (0.20 m) governs the M9 route; the lab policy keeps its frozen value |
| CF-10 | facts opening_heights.DOOR_ASSUMED (project fallback); UP-DOOR-HGT-001 owner reference heights | RESOLVED | the project fallback (precedence 4) is used before the general owner reference (5) |
| CF-11 | UP-DOOR-OPEN-002 (width + 0.10 m); wall-opening head height | OPEN | the rule covers the width only; the head allowance of the wall opening is not an owner rule: owner question OQ-02 (the head is taken at the door height, ASSUMED) |

## Question categories (UP-KB-QUES-001)

| Category | Meaning | Reaches the owner |
|---|---|---|
| A_ESTABLISHED | an approved rule applies: apply it, never ask | no |
| B_MISSING_DRAWING_EVIDENCE | a rule exists but the drawings do not show whether it applies: investigate geometry, connectivity, levels, annotations and other drawings; request the document (schedule, section, label), not a policy | no |
| C_RULE_CONFLICT | two approved rules, or a drawing and an owner requirement, disagree: keep both facts and explain the modification; ask only where precedence does not decide it | yes (with an OQ id) |
| D_MISSING_OWNER_POLICY | no approved rule resolves it: the only category that is an owner question | yes (with an OQ id) |
| E_ENGINEERING_DEFECT | the engine cannot read the geometry or has not implemented an existing rule: an engineering backlog item, never an owner question | no |

## Question catalogue (the reason patterns the engine raises -> category)

| Pattern | Item | Category | Group | Rule | Owner question |
|---|---|---|---|---|---|
| `^THRESHOLD_FINISH_NOT_ESTABLISHED` | - | A_ESTABLISHED | DOORWAY_STRIP_FINISH | UP-THR-001 | - |
| `^UP-CER-004` | - | A_ESTABLISHED | WET_ROOM_SKIRTING | UP-WET-001 | - |
| `^FINISH_ABOVE_WALL_TILE_NOT_ESTABLISHED` | - | A_ESTABLISHED | WET_ROOM_WALL_TILE_HEIGHT | UP-FIN-WALL-001 | - |
| `^MISSING_SOURCE` | ^DOOR HEIGHTS | A_ESTABLISHED | DOOR_HEIGHT | UP-DOOR-HGT-001 | - |
| `^WALL_FINISH_HEIGHT_NOT_ESTABLISHED` | - | B_MISSING_DRAWING_EVIDENCE | WALL_FINISH_HEIGHTS | URBAN-WALL-FINISH-HEIGHT-METHOD | - |
| `^(PLASTER|PAINT|WALL_TILE) net is a range` | - | B_MISSING_DRAWING_EVIDENCE | FACE_OPENING_DEDUCTION | UP-GEN-003 | - |
| `^WINDOW_REVEAL_FLOOR_STATUS_NOT_ESTABLISHED` | - | B_MISSING_DRAWING_EVIDENCE | WINDOW_TYPE_AND_SILL | URBAN-REVEAL-FINISH-METHOD | - |
| `^F-17` | - | B_MISSING_DRAWING_EVIDENCE | WINDOW_TYPE_AND_SILL | UP-SKIRT-001 | - |
| `^FLOOR_FINISH_SPEC_NOT_ESTABLISHED` | - | B_MISSING_DRAWING_EVIDENCE | FLOOR_FINISH_SPECIFICATION | UP-CER-010 | - |
| `^STAIR_(?!HALL_FINISH)` | - | B_MISSING_DRAWING_EVIDENCE | STAIR_SECTIONS | UP-STAIR-002 | - |
| `^BLOCK_WALL_NOT_ESTABLISHED` | - | B_MISSING_DRAWING_EVIDENCE | BLOCKWORK_SPECIFICATION | UP-GEN-001 | - |
| `^(UNLABELLED_SPACE|MERGED_SPACE|MIXED_SPACE|ATTACHED_THROUGH_OPEN_PASSAGE|ZONE_FROM_DRAWN_LINES)` | - | B_MISSING_DRAWING_EVIDENCE | SPACE_IDENTITY | UP-SPACE-001 | - |
| `^ROOM_TYPE_FROM_STACKED_FOOTPRINT` | - | B_MISSING_DRAWING_EVIDENCE | LIFT_IDENTITY | UP-DOOR-CLS-005 | - |
| `^STAIRWELL_CEILING_SCOPE_NOT_ESTABLISHED` | - | B_MISSING_DRAWING_EVIDENCE | STAIR_SECTIONS | UP-CEIL-001 | - |
| `^STAIR_HALL_FINISH_NOT_ESTABLISHED` | - | D_MISSING_OWNER_POLICY | STAIR_HALL_FINISHES | - | OQ-03 |
| `^EXTERIOR_FINISH_SCOPE_NOT_ESTABLISHED` | - | D_MISSING_OWNER_POLICY | EXTERIOR_SCOPE | - | OQ-04 |
| `^STRIP_NOT_ATTRIBUTED` | - | E_ENGINEERING_DEFECT | STRIP_ATTRIBUTION | UP-THR-001 | - |
| `^GEOMETRY_INCONSISTENT` | - | E_ENGINEERING_DEFECT | GEOMETRY_CHECKS | UP-KB-PREC-001 | - |
| `^(WARNING|ENGINEERING)` | - | E_ENGINEERING_DEFECT | READER_LIMITS | - | - |
| `^(DOOR_CLOSURE_UNRESOLVED|VOID_EXTENT_UNRESOLVED)` | - | E_ENGINEERING_DEFECT | READER_LIMITS | - | - |
| `^REVIEW` | ^DOORS:(DOOR_PROVISIONAL/DOOR_UNRESOLVED/DOOR_CLASS_UNRESOLVED) | B_MISSING_DRAWING_EVIDENCE | DOOR_EVIDENCE | UP-DOOR-CLS-001 | - |
| `^REVIEW` | ^DOORS:(DOOR_HELD_WIDTH_REVIEW/DOOR_CLOSURE_FRAME_DISAGREE) | B_MISSING_DRAWING_EVIDENCE | DOOR_WIDTH_CONFLICT | UP-DOOR-OPEN-002 | - |
| `^REVIEW` | ^DOORS:DOOR_CLASS_REVIEW | B_MISSING_DRAWING_EVIDENCE | SPACE_ENCLOSURE | UP-SPACE-001 | - |
| `^REVIEW` | ^DOORS:LIFT_ENTRANCE_CANDIDATE | B_MISSING_DRAWING_EVIDENCE | LIFT_IDENTITY | UP-DOOR-CLS-005 | - |
| `^REVIEW` | ^DOORS:MAIN_ENTRANCE | B_MISSING_DRAWING_EVIDENCE | MAIN_ENTRANCE | UP-DOOR-CLS-004 | - |
| `^OPENING_BELOW_OWNER_STANDARD` | - | C_RULE_CONFLICT | DOOR_ENLARGEMENT | UP-DOOR-OPEN-002 | - |
| `^WALL_TILE_BELOW_OWNER_FULL_HEIGHT` | - | C_RULE_CONFLICT | WET_ROOM_WALL_TILE_HEIGHT | UP-FIN-WALL-001 | - |
| `^WALL_BAND_ABOVE_EXPLICIT_TILE` | - | C_RULE_CONFLICT | WET_ROOM_WALL_TILE_HEIGHT | UP-FIN-WALL-001 | - |
| `^OPEN_PLAN_WET_SCOPE_EXTENT` | - | B_MISSING_DRAWING_EVIDENCE | WET_ZONE_EXTENT | UP-WET-001 | - |
| `^WET_SCOPE_PROJECT_CONFIRMATION` | - | B_MISSING_DRAWING_EVIDENCE | WET_SCOPE_CONFIRMATION | UP-WET-001 | - |
| `^EXTERIOR_WP_UPTURN_BY_SPECIFICATION` | - | B_MISSING_DRAWING_EVIDENCE | WATERPROOFING_SPECIFICATION | UP-WP-ROOF-001 | - |
| `^THRESHOLD_OF_PROVISIONAL_DOOR` | - | B_MISSING_DRAWING_EVIDENCE | DOOR_EVIDENCE | UP-THR-001 | - |
| `^THRESHOLD_STRIP_NOT_ATTRIBUTED` | - | E_ENGINEERING_DEFECT | STRIP_ATTRIBUTION | UP-THR-001 | - |
| `^PANTRY_THRESHOLD_RULE_CONFLICT` | - | C_RULE_CONFLICT | PANTRY_THRESHOLD | UP-THR-001 | OQ-01 |
| `^DOOR_OPENING_HEAD_ALLOWANCE` | - | D_MISSING_OWNER_POLICY | DOOR_HEAD_ALLOWANCE | UP-DOOR-OPEN-002 | OQ-02 |
