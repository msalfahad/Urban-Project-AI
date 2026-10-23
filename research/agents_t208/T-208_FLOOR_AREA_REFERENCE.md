# T-208: floor-area reference line made comparable (the 3 wet / dry review sets settled by answered rules)

Worker 2 (lane A), 2026-10-23 09:41-10:45 UTC. Gate 1. Development villa, not an accuracy claim; nothing wired, no
released quantity changed. ERS applied: s.2 steps 1-4 (element defined, evidence hierarchy, first-principles re-check of
the three spaces from printed dimensions, reconciliation in units), s.3 (scope before numbers; physical floor kept apart
from the line that bills it).

Run: the pinned released baseline `research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json` (ARCH_TAKEOFF_V2.9 + route
G) on Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (P7757.dxf sha256 ab54dd55...) + "ST7757 dxf.dxf"
(9f9d1179...), working head e081911c, Python 3.11.17: **REPRODUCED**, 1,455 lines, BOQ_LINES.csv b96185d4. Drawing check
of the three spaces: render of the GF plan around each and its outline vertices (scratch only; nothing private committed).

## 1. What the 3 review sets are (engine question answered)

The release report's CONDITIONAL category holds 4 sets; 3 are `REVIEW_CLASSIFICATION` (WET_SCOPE / DRY_SCOPE, mutually
exclusive, UP-WET-002 1.3.0 "a basin alone does not make a space wet"), 1 is DOOR_OWNER_MINIMUM (not floor; ignored).
All three are **unlabelled ground-floor spaces holding wash basins only** (no WC, shower, bath, appliance; the only
texts inside are the WASH basin block's own labels), i.e. exactly the "three basin-only hand-wash spaces (9.35 m2 in
all)" of owner question Q-06, answered (a) wet on 2026-10-18 (9.348 m2 wet tile here).

| Set subject | Space (drawing) | Printed check (first principles) | WET_SCOPE floor | Bound | Status |
|---|---|---|---|---|---|
| GF-R8496F0 | hand-wash room beside the diwaniya, 2 basins, doorless 1.00 m passage OP-027 | 1.50 x 2.10 = 3.150 less the drawn column notch 0.35 x 0.05 = 0.0175 -> **3.1325** = engine face; strip 1.00 x 0.15 = 0.150 | wet tile 3.1325 + strip porcelain 0.150 | WET by Q-06 A | ASSUMED — OWNER-APPROVED (Q-06 A); geometry DRAWING-CONFIRMED |
| GF-RD36087 | hand-wash niche by the stair hall, 1 basin, doorless 0.90 m passage OP-020 | printed 110 x 135 = **1.485** = engine face; strip 0.90 x 0.20 = 0.180 | wet tile 1.485 + strip porcelain 0.180 | WET by Q-06 A | as above |
| GF-RDBD4F9 | 45-degree hand-wash lobby between the two wedge W.C.s (doors OP-017 / OP-018, marble thresholds 0.12 each already released), 2 basins, open side to the GF open space | outline 2,050 mm on the open side = printed 205; arm between the two 45-degree wall faces (y - x = 230 / 2100 local mm) 1,870 / sqrt 2 = 1,322 mm = printed 132; area **4.7307** from the drawn wall faces | wet tile 4.7307 | WET by Q-06 A **with** the boundary confirmation (its ZONE_FROM_DRAWN_LINES line is the opening line on the wall face, `T208_BOUNDARY_CONFIRMATIONS.json`); without it HELD | as above |

Sum: wet tile 9.3482 + doorless-passage strips 0.330 (porcelain, PROVISIONAL: UP-THR-001 gives a marble threshold only
at a DOOR next to a wet room, `owner_finish_scope.threshold_lines`; Q-06's "marble threshold" is met at the doors
OP-017 / OP-018) = **9.6782 m2** in the floor key; the same binding unlocks membrane floor 9.348 m2 and upturn 3.049 m2
(FIN.WP.*, not scored here). D-C3 adverse check: no doorless cell is attached to any of the three (attached_cells empty).
The candidate methods already classify such spaces wet (engine/source/wet_room_evidence.py `classify`,
BASIN_ONLY_HAND_WASH, Q-06 a); the released V2.9 predates it, hence the sets.

## 2. Floor-area reference line, like for like (key FLOOR.INTERNAL = FIN.FLOOR.PORCELAIN + FIN.FLOOR.WET_TILE)

Freelancer: 'total floors' FIN:الغلاف:15 = **409.58 m2** (dry 337.57 + wet 72.01; his tiles-sheet rows re-add to 409.58).

| | m2 | % of 409.58 |
|---|---|---|
| Engine released lines (PROVISIONAL / SOURCE_DERIVED, 44 lines) | 376.2857 | |
| + the 3 review sets bound WET (ASSUMED — OWNER-APPROVED, Q-06 A) | 9.6782 | |
| **Engine floor line** | **385.9639** | **-5.77 % (WAPE 5.77 %)**, -23.616 |
| Scope S1: garden band 1.30 x 10.82 (9.101 + 4.885): in his reception row; engine HELD CONFLICT outside the key (T-153 P-2, B9) | -13.986 | |
| Scope S2: GF round-stair treads inside the open space: in his reception row; engine bills FIN.MARBLE.TREAD | -8.194 | |
| Scope S3: 2F corridor (his 7.70): engine side inside the 2F stair room, FIN.MARBLE.LANDING HELD 0 .. 11.725 (T-129: 2.500 porcelain + 4.875 arrival marble) | -7.700 | |
| Scope S4: 1F stair footprint inside the engine's living porcelain (T-116 / T-122): his stair sheet | +5.890 | |
| Net scope | -23.990 | |
| **Residual, like for like** (409.58 - S1 - S2 - S3 = 379.70 compared) | **+0.374** | **+0.10 %** |

The residual, room by room (`RECONCILIATION_T208.csv`): GF open space +0.228 (incl. its 4.474 doorway strips, as
T-153 reads his reception row), diwaniya +0.100 (printed 400 x 630 less R1.10, ENGINE_RIGHT), master -0.110, driver
+0.005, kitchen +0.080, six GF W.C.s +0.098, the three hand-wash spaces +0.098; 1F living +0.019 after S4, bed rooms
-1.379 (UNRESOLVED as T-153: the 380 x 430 room's passage and the curved east room), 1F dry doorway strips +0.770
(engine-only lines), 1F wet +0.235; 2F maid -0.230, 2F strips +0.530 (engine-only), 2F W.C. -0.070. Named, no
unexplained remainder; the strips (1.300 on 1F / 2F, 4.474 on GF) are the one measurement-basis question left (Q-S6-1:
how a doorway strip is measured), not a defect.

Wet / dry kept apart: engine wet 53.1425 released + 9.3482 bound = 62.4907 vs his 72.01 (-9.519): the GF kitchen 9.630
is porcelain (dry) in V2.9 but wet by Q-30 A (T-074) and in his wet set; re-classed, wet = 72.1207 vs 72.01 = +0.111
(+0.15 %, = T-074). The pantry 13.500 is wet by Q-37 A on both owner-rule sides (T-153 85.62) but dry in V2.9 and in his
dry row: RULE_DIFFERENCE, area unchanged in this key. External floors (courts 167.714, side passage 5.640, roofs) are
other keys and stay apart.

## 3. Verdict proposals (for the Checker)

- Classification of the 3 sets: AGREE (his tiles sheet has them in the wet set: 4.73 / 1.70 / 3.15) and owner rule Q-06 A.
- Areas: GF-RDBD4F9 4.7307 vs 4.73 AGREE; GF-R8496F0 3.1325 (+0.150 strip) vs 3.15: ENGINE_RIGHT on the room (printed
  1.50 x 2.10 less the drawn column 0.0175); GF-RD36087 1.485 (+0.180 strip) vs 1.70: ENGINE_RIGHT on the room (printed
  1.10 x 1.35), his +0.215 untraceable (no dimensions). Pairing of his two 'diwaniya washroom' rows by area (his names do
  not follow the plan positions).
- Floor line: RULE_DIFFERENCE on S1-S4 (scope), residual +0.10 % like for like; the line is now scorable (raw WAPE
  5.77 %, which is scope, not accuracy).

## 4. For lane I (key mapping; no tool edited here)

`tools/alsenan_keymap.py` answers every CONDITIONAL set holding FLOOR.INTERNAL as one HELD row `COND:<set_id>:FLOOR.INTERNAL`.
Proposed: an opt-in `--set-bindings BINDINGS.json` (URBAN_REVIEW_SET_BINDING_V1 from `review_sets.bind_run`, rows from
`review_sets.key_rows`) that replaces a set's HELD row by its bound row (qty = the chosen scenario's FIN.FLOOR.PORCELAIN
[m2] + FIN.FLOOR.WET_TILE [m2], status ASSUMED_OWNER_APPROVED, rule id), counted apart from RELEASED in SCOREBOARD v2
(WORKFLOW_CONTROLS s.5: shown separately); a HELD binding keeps the HELD row. V3.0.x candidates: their own release report
must state their CONDITIONAL sets (T-177 finding 1); with wet_room_evidence the three spaces are not review sets there.
Scope items S1-S4 are lines of other keys (garden band HELD, FIN.MARBLE.TREAD, FIN.MARBLE.LANDING), not floor-key rows.

## 5. General rule, test, lessons row

Rule (scope: any villa, any released run with review sets; provenance: owner Q-06 A, UP-WET-002, UP-QTY-STATUS-001):
a wet / dry review set is bound to a scenario only by an answered owner rule whose predicate the space's own evidence
meets (basin-only: >= 1 basin, no other fixture, no room word other than hand-wash, no fixture conflict); a doorless
attached cell (D-C3) or a zone cut by non-wall drawn lines needs a boundary confirmation with its drawing check; anything
else stays HELD, never dry by default, and a held set keeps the whole line UNKNOWN (never a partial sum).
Tests: `tests/t208_floor_review_sets` (villa T208-V hand fixture 21.380 m2; adverse: D-C3 cell, basin + WC, no fixture,
drawn-line zone, non-exclusive set, missing room, fixture conflict, no WET scenario, labelled pantry, non-floor set kind,
held line; Alsenan ledger reproduces).
Lessons-register row proposal: 2026-10-23 | floor-area line NOT YET MEASURED for days in every state | 3 review sets of the
released run were never matched against the answered Q-06 although the question named them (9.35 m2) | bind review sets
by answered rules with the space's evidence, boundary-confirmed; unbound = HELD, never dry (every villa) |
tests/t208_floor_review_sets | READY.

## 6. Missing / held / found

- HELD outside this key (unchanged): garden band 13.986 (P-2), 1F unlabelled space 2.970 and GF closed face 1.373 (type),
  1F living range 0.1175 (D-23), the strips' measurement basis (Q-S6-1).
- FOUND (for the Lead): V2.9 floors the GF kitchen 9.630 as dry porcelain against Q-30 A (wet); the candidate's
  wet_room_evidence path should be checked on it when floors are integrated. `tests/t202_guard_sweep::
  test_guard_host_and_unwired_producers` fails on the working head e081911c itself (masonry_centreline_v2 now has the
  importer masonry_area_v1, merged with T-108 r2): not this task's, the same on the base.
- Checker re-measure proposal: GF-R8496F0 (printed 1.50 x 2.10 less 0.35 x 0.05 = 3.1325; strip 1.00 x 0.15) and
  GF-RD36087 (printed 1.10 x 1.35 = 1.485; strip 0.90 x 0.20); optionally GF-RDBD4F9 (205 / 132 against the outline).

Files: `review_sets.py` (module), `alsenan_t208.py` (ledger, `--check`), `ALSENAN_T208_INPUT.json` (sets, the three room
records without coordinates, the floor / threshold lines and floor-area facts of the pinned run),
`T208_BOUNDARY_CONFIRMATIONS.json`, `SETS_T208.csv`, `RECONCILIATION_T208.csv`, `summary.json`.
Repeat: `python3 -I tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json --plan P7757.dxf
--structural ST7757.dxf --out RUN` then `python3 -I research/agents_t208/review_sets.py RUN --confirmations
research/agents_t208/T208_BOUNDARY_CONFIRMATIONS.json`.
