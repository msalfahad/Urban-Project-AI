# T-743: B12-01 sanitary fixtures and floor drains, per-room census (research only, nothing wired)

Worker 1, 2026-11-12. Method piece `research/agents_t743/t743_census.py` (SANITARY_FIXTURE_CENSUS_T743_V1); no engine,
tool, rule, knowledge or frozen file changed; no BOQ line produced or changed. MEP is last in the owner order: this is a
census so a later row can wire B12-01. Development villa: not an accuracy claim.

## Physical element and method

One installed fixture (WC, basin, shower tray, walk-in shower zone, bath, bidet, urinal, kitchen sink) or one floor
drain, counted ONCE in the room that holds it. The architectural plan and the sanitary plan are two representations of
one building: a symbol of one kind on both sheets within 0.30 m (after the sanitary sheet is fitted to the plan) is ONE
fixture; a symbol on one sheet only is still one fixture, and the reconciliation names why the other sheet lacks it
(`ARCH_PLAN_DRAWS_NO_SYMBOL_OF_THIS_KIND_ON_THIS_FLOOR`, `SYMBOL_MISSING_ON_THE_ARCH_PLAN_IN_THIS_ROOM`, the sanitary
mirror causes, `SANITARY_PLAN_OF_THIS_FLOOR_NOT_READ`). A block whose content is text only is a ROOM TAG, never a
fixture, whatever its name. An outline whose type is not shown = `HELD_UNTYPED` (never a default type). A kitchen with no
sink symbol / a laundry with no washing-machine point = HELD, pcs None (designer item, never 0). Sheet fit: least squares
(scale + offset, optional mirror) on objects drawn on both sheets; refused when the worst anchor is > 0.10 m (a rotated
or wrong-scale sheet places nothing).

## Development villa (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip + sanitary-7757.pdf p.1-3)

Reproduce: `bash scripts/agent_env.sh run --tree <tree> research/agents_t743/t743_alsenan.py <P7757.dxf> <sanitary.pdf>
<private reading.json> --out <scratch>.json` (the person's sheet reading with page points stays in `.work/private`;
committed result `out/T743_ALSENAN_COUNTS.json`: counts, kinds, engine room ids only).

Fits: GF 3 shared basin blocks, worst 0.032 m; 1F 4 bathroom corners, worst 0.092 m; 2F 2 corners, worst 0.064 m;
plotted scale 0.0275 m per 100-dpi pixel (1:108, the sheets say 1:100: plotted to fit). Every symbol lands inside its
room (distance 0.000 m); none unassigned.

| Kind | pcs MEASURED | on both sheets | sanitary sheet only | arch only |
|---|---|---|---|---|
| WC | 12 (GF 6, 1F 5, 2F 1) | 0 | 12 | 0 |
| Wash basin | 17 (GF 11, 1F 5, 2F 1) | 5 (the 3 hand-wash spaces) | 12 | 0 |
| Shower tray | 3 (GF 1, 1F 2) | 0 | 3 | 0 |
| Walk-in shower zone (screen + mixer, no tray) | 3 (1F 2, 2F 1) | 0 | 3 | 0 |
| Floor drain | 19 = 14 x 4 in + 5 x 3 in (GF 11, 1F 7, 2F 1) | 0 | 19 | 0 |
| Bath tub / bidet / urinal | none drawn on either sheet | | | |
| HELD | kitchen sink 1 (GF kitchen), washing-machine point 1 (1F laundry) | | | |

Floor drains, independent machine check: the FD squares of the PDF vector paths (4.3-5.0 pt, legend excluded) count
11 / 7 / 1 per sheet = the reading 11 / 7 / 1 (AGREE 19 = 19).

Per room (pcs): GF 4 bathrooms / WCs with WC + basin + FD (one also a shower tray), the W.C by the stair WC + basin + FD,
the hand-wash nook basin + FD3, two hand-wash spaces 2 basins + FD3 each, the kitchen FD4 (sink HELD), the open-plan
pantry FD3; 1F 2 bathrooms WC + basin + tray + FD4, 2 bathrooms WC + basin + walk-in zone (one with FD4 + FD3, one FD4),
the W.C WC + basin + FD4, the laundry FD4 (washing point HELD); 2F bathroom WC + basin + walk-in zone + FD4. Full table:
`out/T743_ALSENAN_COUNTS.json` rows.

### Reconciliation, arch vs sanitary, to named causes

- The architectural plan draws only 5 fixtures (WASH2 basin blocks, layer TOI, in the three hand-wash spaces); every
  one has its sanitary twin (AGREE, 5 / 5). It draws no WC, shower, drain or bathroom basin anywhere (bathrooms carry a
  tile grid and a room tag): 12 WCs, 6 showers, 19 drains are SANITARY_ONLY by `ARCH_PLAN_DRAWS_NO_SYMBOL_OF_THIS_KIND`;
  the 12 bathroom basins are SANITARY_ONLY by `SYMBOL_MISSING_ON_THE_ARCH_PLAN_IN_THIS_ROOM`. No ARCH_ONLY item.
- Against the earlier visual reading (T-010 `sanitary_reading.json`, 2026-10-19): WC 12 = 12; basins 17 vs 16 (+1: GF
  W.C engine room GF-RB28769, the upper of the two diagonal-counter basins sits on its side of the diagonal wall: own
  fit puts it 0.000 m inside, the lower one inside GF-RF38DAF); showers 6 vs 4 (+2: 1F rooms 1F-R48AA46 and
  1F-R8BDA49 have walk-in zones, screen line + mixer, no tray); drains 19 vs 18 (+1: the 3 in drain inside the walk-in
  zone of 1F-R8BDA49). No class changes (all are labelled bathrooms).

### Findings for the Lead

1. DEFECT PROPOSAL (rooms; `engine/source/wet_room_evidence.py:127` `_fixture_kind` over `arch_rooms.fixture_of`, by
   block NAME): the plan's room-tag blocks 'WC' (7, content TEXT 'W.C') and 'WASH' (2, TEXT 'Wash') are read as a WC
   and a basin. `plan_evidence` therefore reports 14 plan fixtures on this villa where 5 are drawn (7 phantom WCs, 2
   phantom basins). No quantity moves today (every affected room is labelled), but any fixture count or the Q-13
   fixture-only typing of an UNLABELLED space would be wrong. Fix in a new method version: type a fixture block from its
   content (`t743_census.is_tag_block`), never its name alone.
2. COORDINATION (no quantity): the 2F room tagged 'W.C' holds a walk-in shower zone on the sanitary sheet; that zone and
   the 1F-R48AA46 zone have no drain inside the screen (the room drain is outside it); the open-plan pantry has a floor
   drain and no sink on either sheet (no owner rule says a pantry has a sink, so nothing is held for it).
3. Freelancer: the Drive folder's workbooks (by title: masonry, aluminium, floors + waterproofing + decor + marble,
   paint, internal plaster) carry no sanitary fixture line: no freelancer comparison exists for B12-01.

## Verdict proposals

- B12-01 counts: ENGINE_RIGHT is not claimed (no engine line exists); census values MEASURED from the sanitary sheet,
  5 basins confirmed on both sheets; the Checker re-counts 2 wet rooms (suggested GF-RB28769 and 1F-R8BDA49, the two
  rooms where this census differs from T-010).
- T-010 reading vs this census: this census (GF-RB28769 basin, two 1F walk-in showers, one 1F 3 in drain).

## Lessons-register row (ERS section 7, proposed)

| lesson | scope | provenance |
|---|---|---|
| A block named like a fixture can be a room tag: type fixtures from block content, and count one physical fixture once across the arch and sanitary sheets (twin within 0.30 m after a checked fit) | every villa | T-743, development villa: 7 'WC' + 2 'WASH' text-only tag blocks |

## Synthetic proof (not Alsenan): `tests/t743_sanitary_count/` (21 cases)

Villa N743: two bathrooms mirrored about x = 2.50, a kitchen; hand truth WC 2, basin 2 (B1 basin on both sheets = one),
tray 2, FD 1 (4 in, sanitary sheet only), kitchen sink HELD (pcs None). Cases: normal counts and causes; mirrored rooms
alike; a mirrored sheet with the mirror fit = same census; double vanity 0.6 m apart + one arch basin = 2 (not 1, not
3); ADVERSE: rotated sheet refused, mirrored sheet without the mirror refused, a mm point passed as m = UNASSIGNED HELD
(not counted, not doubled), sanitary floor not read, untyped outline HELD, unknown kind refused, unprinted drain size
kept UNPRINTED, tag-by-content table, fit needs two objects.

## What is missing

- Not wired: B12-01 has no candidate line; a later Gate B row adds it (pcs per kind, drains by size) from this census.
- Fixture specification (wall-hung vs floor WC, basin size, tray size, mixer type) is not printed: a designer item for
  pricing; the counts do not depend on it.
- The sanitary symbols are typed by a person (outline at 300-800 dpi); only the drains have a machine check.
