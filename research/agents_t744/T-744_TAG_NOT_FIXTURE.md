# T-744: room-tag blocks are text, not fixtures (WET_ROOM_EVIDENCE_V2; research + new functions, nothing wired)

Worker 1, 2026-11-12. Development villa: not an accuracy claim.

## Physical element

A sanitary fixture is a drawn symbol (fixture geometry) of a legend type; a room-name tag is text. T-743 found the
plan's text-only blocks 'WC' (7, content TEXT x2) and 'WASH' (2, TEXT x2) read as a WC / a basin by NAME
(`engine/source/wet_room_evidence.py` `_fixture_kind` over `arch_rooms.fixture_of`).

## Change (engine/source/wet_room_evidence.py, additive; V1 unchanged)

- `DEFAULT_GUARD_CLASS = "GUARDED_VIA_V3.0.6"` (line 47): the T-212 guard property requires every modified module to
  classify itself; V1 is read by arch_v211 in the chain inherited by V3.0.6.
- `block_content` (481), `fixture_reading` (494), `plan_evidence_v2` (524), `classify_v2` (569), METHOD_ID_V2
  `WET_ROOM_EVIDENCE_V2`. Content from the drawing's block table (flattened; `research/agents_t744/t744_alsenan.py
  block_types`), else the intake's non-text extents box; text-only -> TAG (to the room tags), drawn -> FIXTURE,
  empty -> nothing, not read -> UNCONFIRMED (a candidate only; an unlabelled space with only that is
  WET_DRY_NOT_ESTABLISHED, HELD). A block nested in a kept fixture block of the same kind is that fixture (counted
  once). V1 `plan_evidence` / `classify` untouched: the candidate chain (V2.11 .. V3.0.75) keeps reading them.

## Alsenan census (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip; ARCH_TAKEOFF_V2.11 with the chain's
T-131 facts; `out/T744_ALSENAN_CENSUS.json`)

- V1 recomputed = the chain's own classes (37 spaces) exactly.
- Fixture-named inserts: 14 = 9 TAG (WC handles 1C8, 1F7, 2DA, 322, 323 on GF, C19 on 1F, 12B6 on 2F; WASH 1F0, 2C5 on
  GF) + 5 FIXTURE (WASH2 basins 1CF, 1EE, 2C0, 2C1, 33B). AGREES with T-743 (7 + 2 phantom, 5 drawn).
- Classes V1 vs V2: WET 17 / DRY 9 / HELD 5 / NONE 6 both; class, reason and basis identical in all 37 spaces. 7 spaces
  lose a phantom WC from their evidence record (all labelled BATHROOM by text: LABEL_WET kept); the two WASH tags sit in
  spaces that also hold drawn basins (GF-R8496F0 BASIN_ONLY_HAND_WASH, GF-RDBD4F9 LABEL_WET HAND_WASH): unchanged.
- Lines: 0 of 5,159 lines of LINE_INDEX_V3_0_75 change (lines read class / reason / basis only; plan_fixtures sits in
  the run record). Before / after: 0 m2, 0 pcs on every line. The room builder typed no space by fixtures here
  (label sources TEXT 25, none 8, stacked 3, zone 2).

## Verdict proposal

ENGINE_WRONG in the evidence record (9 phantom fixtures), no quantity effect on this villa; on a villa whose space is
labelled only by such a tag, V1 would make it WET by a phantom basin / WC (adverse tests pin it). Who is right vs the
freelancer: NOT_COMPARABLE (no freelancer line reads fixtures).

## Tests: tests/t744_tag_not_fixture (19), synthetic villa N744 (two mirrored bathrooms, whole sheet mirrored)

Normal: drawn WC in labelled bathrooms (V1 = V2); nested wrapper = one WC. Adverse: tag 'WC' with no WC symbol (V2 0 WC,
WET kept, coordination check raised that V1 hid); unlabelled space with only a 'WASH' tag (V1 WET phantom, V2 HELD, no
quantity); unlabelled 'WC' tag not FIXTURES_TOILET; WC symbol in a room labelled STORE (DRY + check); empty block; no
content read -> HELD; V1 surface unchanged.

## Lessons row (ERS section 7, proposed)

| lesson | scope | provenance |
|---|---|---|
| A fix to an evidence reader is proven by the census of the CLASS / REASON / BASIS it feeds per space, not by the fixture count alone: here 9 phantom fixtures moved 0 classes and 0 lines | every villa | T-744 |

## Missing

Wiring V2 into a candidate (a later hub version replacing arch_v211.wet_classes' reader); the room builder's own
FIXTURES label source (arch_rooms) still reads names (not exercised on this villa).
