# T-134 element register v0 (worker 3, 2026-10-21)

Owner management decision 2026-10-20 §4; Lead design docs/agents/ELEMENT_REGISTER.md. Lane I.

## What it is

`engine/source/element_register_v0.py` (new, stdlib + shapely for the revision overlap only) reads the outputs of an
ARCH_TAKEOFF_V3.0 run (V3_0_BOQ_LINES.json, else BOQ_LINES.json, plus ARCH_ROOMS / ARCH_WALLS / ARCH_OPENINGS /
CURVED_OPENINGS / DOOR_SCHEDULE / MEMBRANE_PIECE_PLAN) and writes ELEMENT_REGISTER_V0.json / .csv beside them. It changes
no input file, no method, no line and no quantity; arch_v30.py and tools/urban_boq_m9.py are untouched (nothing imports
the module). Rollback: delete the two files.

* id `<project>/<rev>/<floor>/<kind>/<local>`; rev = first 12 hex of the source's revision_set_sha256 (the
  architectural and structural sets keep their own rev); local = printed label (room function codes read from TEXT,
  footing / column marks, roof zone label), repeats `.1 .2 ...` ordered by position (x, then y, numeric); else
  `G<hash>` of the outline / axis at 1 mm, else `E<hash>` of the engine key (label_basis says which).
* kinds v0: ROOM, EXT, WALL, OPEN (openings, curved openings, door assemblies without a band opening), STAIR-FLIGHT,
  LANDING, ZONE-WP (wet-room membrane zones and roof membrane zones), FTG, COL (columns and necks), GB, STRAP, BEAM, SLAB.
* statuses (DESIGNER_CLARIFICATIONS.md §3): architectural elements from their own source record; structural elements
  from their own concrete line (SOURCE_DERIVED -> CALCULATED, PROVISIONAL -> PROVISIONAL, BOUNDED / BLOCKED -> HELD,
  NOT_APPLICABLE_WITH_EVIDENCE -> NOT_APPLICABLE; a *_CONFLICT convention on the line -> CONFLICT). VERIFIED is never set
  (needs the verifier's own reconstruction). Steel lines link to the concrete element they read.
* links: role PRIMARY (the element the line measures), HOST (the room around an opening / flight / landing / wet zone),
  MEMBER (one of the elements an aggregate line sums: walls of a thickness, footings under the blinding line).
* checks: one floor finish per surface; one concrete item per element (column + neck allowed); a HELD /
  NOT_APPLICABLE element feeding a released line; duplicate lines of one surface; elements with no line; CONFLICT
  elements whose lines release a quantity; every line linked or UNLINKED with its reason.
* revision mapping `map_revisions(old, new)`: same local id, else same printed label, else outline / wall strip
  overlap >= 95 % of the larger; the rest NEW / REMOVED.

## Development villa (Drive DXFs: architectural sha ab54dd55..., structural "ST7757 dxf.dxf" sha 9f9d1179...)

Run: research/agents_t131/alsenan_v30_run.py (V2.9, V2.10-V2.12 history, V3.0 with the Q-67 decision) on working head
0dec24c, then research/agents_t134/run_t134_alsenan.py. V3.0: 1,530 lines (V2.9 1,455).

| kind | elements | status |
|---|---|---|
| ROOM / EXT | 37 / 1 | CALCULATED (outline) |
| WALL | 66 | CALCULATED |
| OPEN | 66 (27 windows incl. 1 curved, 22 band doors, 11 passages, 5 door closures, 1 unresolved door) | 60 CALCULATED, 5 PROVISIONAL (closures), 1 HELD |
| STAIR-FLIGHT / LANDING | 14 / 2 | CALCULATED (drawn) |
| ZONE-WP | 21 (17 wet-room plans + 4 roof zones) | 20 CALCULATED, 1 HELD (2F top roof, no outline) |
| FTG | 26 | 25 CALCULATED, 1 CONFLICT |
| COL (columns + necks) | 118 | 118 HELD (heights not printed; matches T-130: all 82 column lines held) |
| GB / STRAP | 59 / 5 | 59 HELD / 2 CALCULATED, 1 PROVISIONAL, 2 HELD (the V3.0 strap pieces inside open footing outlines) |
| BEAM | 136 | 107 PROVISIONAL, 24 HELD, 5 CONFLICT |
| SLAB | 101 | 7 CALCULATED, 91 PROVISIONAL, 3 HELD |

Links 2,022; 1,504 lines linked, 26 UNLINKED with reason: facade 13 (ARCH.FACADE 4, FACADE_RUN 6, FIN.EXT.FINISH 3:
facade outlines are build-order step 3), 5 ARCH.THRESHOLD strips the engine left unattributed (all BLOCKED_RFI, no
quantity), domes 2, pool 2, stair concrete 3, boundary wall 1 (later kinds). Every line accounted for (linked + unlinked =
1,530). Rerun on the same outputs: byte-identical register.

Checks on V3.0 (and on V2.9 the same): double finish 0, double concrete 0, HELD element releasing a quantity 0,
duplicate surface lines 0. Floor surfaces seen: 12 rooms porcelain, 16 rooms wet tile, 14 flights tread marble,
2 landings landing marble, 19 doorway strips porcelain, 10 doorway strips marble threshold, never two on one element.
Each aggregate ARCH.WALL_RUN line equals the sum of its member walls' own net runs (7 lines, 0.000 lm difference:
GF 0.20 66.704, 0.15 30.335, 0.40 0.600; 1F 0.20 44.032, 0.15 44.260; 2F 0.20 22.300, 0.15 8.700 lm).

For the verifier (listed, not changed): CONFLICT elements whose lines are released by a route convention: 1 footing
(FOOTING_LABEL_CONFLICT, 1.960 m3: the F10 footing T-126 holds) and 5 beams (WIDTH_CONFLICT_SECTION: 5.022 m3 concrete +
685.225 kg steel on 15 steel lines). One door assembly (GF, UNRESOLVED in DOOR_SCHEDULE) feeds no BOQ line: it is
reported in DOOR_FEASIBILITY / DOOR_SCENARIOS, so not silent, but it has no HELD line.

Revision mapping on the real outputs: V2.9 register -> V3.0 register (same drawings): 643 elements SAME_LOCAL, 0
removed, 9 new = the 2 V3.0 strap pieces (T-131), 4 roof zones and 3 GF wet zones that only the opt-in V2.13 base
waterproofs. Simulated revision (the longest straight GF wall moved along its normal): 5 mm -> remapped OVERLAP 0.975
(= 195 / 200 mm strip), 651 others SAME_LOCAL; 60 mm -> overlap 0.70 < 0.95 -> 1 NEW + 1 REMOVED, 651 SAME_LOCAL.

## Gaps (what v0 cannot see)

1. The 1F arrival landing (T-122: 4.875 m2 to marble under Q-66 B) is not an element: V3.0 keeps it inside the 1F living
   porcelain range 38.459..38.979 m2 with no landing outline, so the one-finish check cannot flag it from the outputs.
   Needs the landing / arrival outline reader proposed for T-133b; then the check catches it (the synthetic case does).
2. Beams, slabs, ground beams and straps carry engine keys (BAND0002, SITE-...), not printed marks: E-ids are stable on
   a rerun of one revision only and map across revisions only by label or overlap once outlines are exposed. The T-110
   beam register labels (B7.1 ...) are the next source for printed beam ids.
3. 11 of 28 door assemblies have no DOOR.* class line (5 provisional closures, 2 main-entrance candidates, 1 class
   unresolved, 1 class review, 1 aluminium not released, 1 unresolved); they are approvals in the door outputs. The
   register links their thresholds / transitions; class lines are a release decision, not a register defect.
4. Status of an architectural element is its geometry only (an opening with no measured height carries
   held_attributes ["height"]); attribute-level holds are not yet checked line by line.
5. Structural engine storeys GF / 1F / 2F / GROUND are kept verbatim (no mapping to ROOF-1F etc. invented).

## Tests

tests/t134_element_register (13 pass): non-Alsenan villa, two storeys, hand-expected: repeated label BEDROOM.1 / .2 by
x (engine ids deliberately in the other order), F1.1 / F1.2 numeric order (2000 before 12000), geometry-hash store,
landing fed to marble and porcelain flagged once, released window count on a width-HELD opening and released steel on
a HELD column flagged (2), footing with a declared label conflict -> CONFLICT, 1.2 m3 listed, strap held piece kept
apart, wall shares 7.20 + 3.00 = 10.20 lm, blinding member of 3 footings, 2 unlinked with reasons, duplicate surface
line flagged; mirror and quarter turn keep every count and finding; metres = mm ids; rerun identical; revision with
W3 moved 20 mm (0.867 -> NEW) and 5 mm (0.967 -> OVERLAP), new sha keeps every local id. 6 mutations, all caught
(finish check, overlap threshold, held check, repeat ordering, steel-sets-status, strap piece merge).
