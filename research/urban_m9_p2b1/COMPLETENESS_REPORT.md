# Element and surface completeness (deliverable 10)

Source: the read-only surface ledger of every run (`SURFACE_LEDGER.json`, `engine/source/surface_ledger.py`):
element x surface x trade records, every BOQ line in exactly one record (conservation), every record with an
authority and a status. ARCH_TAKEOFF_V2.3 adds the owner-scope table `ELIGIBILITY_V0_2_OWNER_SCOPE` (wet floors accept
wet tile or porcelain - UP-WET-001; the doorway threshold accepts the marble threshold or the floor strip - UP-THR-001;
door reveals and head are plaster - UP-FIN-PLASTER-001; line-driven passage-jamb skirting and exterior waterproofing).

## 1. Ledger status by run (records)

| Status | Villa U V2.2 -> V2.3 | Villa A V2.2 -> V2.3 | Reference U V2.2 -> V2.3 | Reference A V2.2 -> V2.3 |
|---|---|---|---|---|
| MEASURED | 31 -> 39 | 47 -> 56 | 116 -> 130 | 154 -> 168 |
| PROVISIONAL | 12 -> 19 | 12 -> 19 | 70 -> 99 | 104 -> 134 |
| NOT_APPLICABLE (with evidence) | 0 -> 6 | 0 -> 0 | 0 -> 34 | 0 -> 0 |
| BLOCKED_MISSING_SOURCE | 29 -> 27 | 13 -> 13 | 117 -> 101 | 45 -> 45 |
| BLOCKED_OWNER_DECISION | 13 -> 4 | 13 -> 7 | 61 -> 22 | 61 -> 39 |
| UNRESOLVED_ELIGIBILITY | 29 -> 16 | 29 -> 16 | 130 -> 80 | 130 -> 80 |
| ENGINE_LIMIT | 0 -> 0 | 0 -> 0 | 4 -> 7 | 4 -> 7 |
| EXCLUDED | 0 -> 0 | 0 -> 0 | 3 -> 3 | 3 -> 3 |
| OUT_OF_LEDGER_SCOPE | 1 -> 1 | 1 -> 1 | 11 -> 11 | 11 -> 11 |
| NO_EMITTER | 0 -> 0 | 0 -> 0 | 0 -> 0 | 0 -> 0 |
| **CONFIRMED_MISSING** | **0 -> 0** | **0 -> 0** | **0 -> 0** | **0 -> 0** |
| Conservation (every line in one record) | ok -> ok | ok -> ok | ok -> ok | ok -> ok |

U = no heights given; A = the synthetic heights facts (plaster / paint 3.0 m, wall tile 2.4 m, doors 2.1 m).

Reading:
- **BLOCKED_OWNER_DECISION fell by 9 (villa) and 39 (reference, U)**: the threshold, wet-room band, wet scope and door
  height decisions are now answered by the registry. The remainder are named open decisions (stair halls OQ-03,
  exterior OQ-04, main entrance / class reviews awaiting a document).
- **UNRESOLVED_ELIGIBILITY fell from 130 to 80 (reference)**: each door had two PROPOSAL-only rows (reveal jambs,
  head soffit: 2 x 28); they are now one owner-rule row (door jambs and head, UP-FIN-PLASTER-001), measured
  PROVISIONAL at the 21 doors with a band opening and still unresolved at the 7 provisional doors without one.
  The doorway thresholds (16 door and 7 passage records) moved from BLOCKED_OWNER_DECISION to MEASURED / PROVISIONAL
  (UP-THR-001), and the kitchen moved from the dry SERVICE rows to the WET rows (UP-WET-001).
- **NOT_APPLICABLE rose** where an approved rule makes a surface zero with evidence (wet-room skirting and paint band
  on full-height porcelain). With an explicit lower tile height (A) those surfaces are measured instead (the tile does
  not run full height).
- **ENGINE_LIMIT +3 (reference)**: three doorless openings whose doorway strip is now measured (floor porcelain,
  UP-THR-001) but which also carry a strip face the engine cannot attribute to one opening; the record's blocker moves
  from an owner decision (the finish) to an engine limit (the attribution) - recorded, not hidden.
- No status moved a quantity into CONFIRMED_MISSING; nothing silently disappeared: the conservation check (every line
  in exactly one record, no duplicate) passes on every run. A defect of exactly this kind was found during this phase
  on the reference plan (several strip faces of one opening made duplicate lines) and fixed with a regression test
  (`test_several_strip_faces_of_one_opening_make_one_line`).

## 2. Door elements

Every door swing is in exactly one door element and every door element in exactly one scenario row (reference plan:
28 elements, 28 rows; villa: 6 / 6). Withheld doors are listed with their state and category (UNRESOLVED view); none
disappears from the run.

## 3. Coverage gate

The V2 finish-coverage gate (every m2 of the plan's physical floor accounted for: room floors, doorway strips,
exclusions) passes on every V2.3 run; the V2.3 threshold and doorway-strip lines account for their strips
(`arch_completeness.coverage` accepts them by strip id).

## 4. What completeness is not claimed

The ledger proves that every line produced is accounted for and that no approved-rule surface with a source and an
emitter is silently missing. It does not prove that the BOQ is complete against an independent take-off: BOQ
completeness stays NOT_ESTABLISHED (`boq_completeness.state`) until a blind comparison is run.
