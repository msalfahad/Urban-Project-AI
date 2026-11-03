# T-490: B3-03 entrance / stair-hall stone floor: applicability, measure and overlap (training villa; method every villa)

Worker 1, 2026-11-03, branch agents/task-T-490, base engine 1d311ee5. Lane A, non-candidate: no engine, rule-file or
candidate file changed. Files: `research/agents_t490/` + `tests/t490_stone_floor_census/` only.

Rules: UP-CER-001, UP-STAIR-001 / -005, OWNER_RULE_STAIRS_2026-10-24 s.1, OWNER_RULE_OUTDOOR_FLOORS (outside stairs
marble), Q-66 B, Q-70 A (conditional), R-T246 (by opening id), URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1, ENGINEERING_REASONING_STANDARD.

## 1. The physical element

B3-03 is a stone or marble FLOOR finish laid over a room or hall floor at a storey level: an entrance hall or a stair
hall, i.e. a FLOOR whose finish is stone. It is not:

- a stair landing, arrival or tread (B7: UP-STAIR-005 already makes those marble and never also porcelain floor);
- a door threshold piece in a wall's thickness (B3-04, listed by opening id, R-T246);
- a lift threshold or surround (B6-06 / B6-07).

So B3-03 applies only where a PROJECT source (finish schedule, legend or plan note) names stone for a room or hall
floor. No Urban owner rule makes a room floor marble, and the dry-floor default is porcelain. A floor at the foot or top
of a flight is a landing only where the stair's width x a PRINTED landing depth establishes it (Q-66 B / Q-70 A). Where
nothing establishes that, the element is FLOOR_OR_LANDING and its material stays HELD (between B3-01 and B7), never
guessed.

## 2. Evidence read this run

- Architectural DXF (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip): census of all 276 texts. The English
  labels are room names (DINING, RECEPTION, SALOON, PANTRY, ...). There is no ENTRANCE, HALL or LOBBY word and no finish
  word (marble, granite, stone, porcelain, ceramic, tile, floor finish). The legacy-encoded Arabic texts sit on the room
  labels (for example the DINING label carries its Arabic twin).
- p7757_arch_sheet03.pdf (GF plan, rendered this run): the D200 double main door opens straight into DINING. The
  entrance zone has no drawn edge of its own. Outside the door is the printed 140 x 370 landing at the top of the
  4-tread entrance flight (280 wide). The stair room is printed 250 x 500, with +1.00 at the foot of MS1-L and +0.30 in
  the back-door lobby. No note, legend or hatch for a floor finish appears on the sheet.
- p7757_arch_sheet04.pdf (1F plan, rendered this run): the main-stair arrival is printed 250 x 195 at +5.50. There is no
  finish note.
- Candidate ARCH_TAKEOFF_V3.0.46 line index (research/agents_t485/out/LINE_INDEX_V3_0_46.json): the carrier line of
  every space (section 3).

## 3. Census (CENSUS_T490.csv; summary.json; `python3 -I t490_alsenan.py --check` reproduces)

| Space | Element | Area m2 (source) | Material (basis) | Family / status | Carried by (V3.0.46) | Overlap / note |
|---|---|---|---|---|---|---|
| GF entrance zone inside D-GF-07 (part of the open room) | ROOM_FLOOR | inside 109.4784 (no own edge) | porcelain (default; no project source) | B3-01, **NOT_APPLICABLE** | L-7625f35c porcelain 109.4784 | carried once; B3-03 adds 0 |
| GF entrance landing E1 outside the door | STAIR_LANDING | **5.1800** (printed 1.40 x 3.70) | marble (outdoor stairs owner rule) | B7, CARRIED_ELSEWHERE | L-3dd82a57 5.1794 | -0.0006 drawn vs printed; B3-03 0 |
| GF entrance flight E1, 4 treads | TREADS | 3.3600 (4 x 0.30 x 2.80) | marble | B7, CARRIED_ELSEWHERE | L-314c3ac6 3.3594 | B3-03 0 |
| Main-door threshold OP-021 (D-GF-07) | THRESHOLD | 0.4000 (2.00 x 0.20) | not printed | B3-04, CARRIED_ELSEWHERE | L-ad41b065 HELD 0.40 | porcelain strip L-e6e75fa6 EXCLUDED, so no double count |
| GF stair-room hall +1.00 (foot MS1-L / top D1) | FLOOR_OR_LANDING | **4.8050** (T-418 parts in 250 x 500) | **HELD**: no printed landing depth (Q-70 A condition not met); porcelain default not written for it | HELD (B3-01 or B7) | L-f53d4986 FINISH_HELD 4.805 | one line, area released; door OP-010 strip porcelain 0.20 |
| GF back-door lobby +0.30 | FLOOR_OR_LANDING | **1.3225** (1.15 x 1.15) | HELD, as above | HELD (B3-01 or B7) | L-b4441a1b FINISH_HELD 1.3225 | threshold OP-013 HELD 0.18 |
| GF strip north of the divider | UNREAD | HELD 0 .. 0.23 | - | HELD | L-a788de46 HELD | never 0 |
| GF stair-room landings bound | STAIR_LANDING | HELD 0 .. 2.9225 | marble | B7 | L-1983e89d HELD | - |
| 1F main-stair arrival +5.50 | STAIR_ARRIVAL | **4.8750** (printed 2.50 x 1.95) | marble (Q-66 B) | B7, CARRIED_ELSEWHERE | L-80118898 4.9225 | +0.0475 = -0.010 well end + 0.0575 nosing band (T-240 / T-269), RULE_DIFFERENCE; porcelain L-b06400d4 excludes it |
| 1F round-stair quarter landing | STAIR_LANDING | 1.3525 (T-345 R04, drawn; size not printed) | marble | B7 | **no line** | deducted from porcelain; no B7 line names it (finding F-2) |
| 1F living (open stair hall) | ROOM_FLOOR | 33.4110 | porcelain (default) | B3-01, NOT_APPLICABLE | L-b06400d4 33.4110 | - |
| 2F main-stair arrival +9.70 | STAIR_ARRIVAL | **4.8750** (printed 2.50 x 1.95) | marble (Q-70 A, condition met T-129) | B7, CARRIED_ELSEWHERE | only inside HELD L-5d2be30d 0 .. 9.225 | **no released line of its own** (finding F-1) |
| 2F lobby beyond the stair width | ROOM_FLOOR | 2.2000 = (4.50 - 2.50) x 1.25 - lift threshold 0.30 | porcelain (Q-70 A) | B3-01, NOT_APPLICABLE | L-9bd25c0c 2.200 | thresholds OP-001 HELD 0.15, OP-007 strip 0.18 |

**Result: B3-03 is NOT_APPLICABLE on the issued drawings. New area 0.000 m2, moved area 0.000 m2.** That is 13
candidate spaces with a status: 3 not applicable, 7 carried elsewhere, 3 held. By family: B3-01 145.0895, B7 19.6425
measured, B3-04 0.40, HELD 6.1275 m2. Nothing is counted twice: every measured space has exactly one carrier, or none
(F-2).

B3-03 reopens only if a project finish source arrives (the finishes-schedule RFI-B-A12). In that case:

- If the source names the GF stair hall stone, its 6.1275 m2 becomes B3-03 by a MOVE from the FINISH_HELD lines, not an
  addition.
- If it names the entrance zone stone, a drawn edge is needed first; until then that area stays in the porcelain line.

## 4. Engine vs freelancer (units; no new values copied)

- Entrance marble: the freelancer's "entrance marble" rows are the E1 steps and one landing (T-471 F-4). His landing
  5.10 vs 5.1794 m2 (-0.079, -1.5 %) is ENGINE_RIGHT (printed 1.40 x 3.70 = 5.18, T-343). So his entrance marble is
  B7, the same as ours, and no B3-03 row exists on his side either: **AGREE on applicability (B3-03 = 0)**.
- His entrance porcelain row (10.46 m2) is a zone of the open-room porcelain (T-427). Ours carries it inside 109.4784.
  This is RULE_DIFFERENCE in presentation only, with no quantity effect.
- GF stair hall 6.1275 m2: none of his floor rows holds it (T-427 s.3). This is an engine-only area with its material
  HELD: UNRESOLVED (material).

## 5. Findings for other rows (no quantity changed here)

- **F-1 (B7-04, stream S / T-424 owner)**: the 2F main-stair arrival is 4.875 m2 marble. Q-70 A's condition is met
  (T-129). Yet V3.0.46 carries it only inside the HELD landings bound 0 .. 9.225 of 2F-R4D1B62, with no released B7-04
  line. The landing family therefore under-releases 4.875 m2 against the owner answer. The fix belongs to a B7 package
  (a split-out line like the 1F one), not to B3-03.
- **F-2 (B7-04)**: the 1F round-stair quarter landing (1.3525 m2 drawn, T-345 R04) is correctly deducted from
  porcelain, but no B7 line names it, either released or held. This is a silent omission of a marble landing (its size
  is not printed, so it should be a HELD line with the drawn bound, never absent).
- **F-3 (EIMP / T-471 matrix, proposed, not written; the registry file is not this task's)**: C-B3-03 should read
  POSSIBLY_APPLICABLE -> **NOT_APPLICABLE (issued drawings; reopens on RFI-B-A12)**. The stair-hall floor parts are
  C-B3-01 FINISH_HELD 6.1275 m2 (material HELD between B3-01 and B7).

## 6. Rule R-T490-1 (any villa; floor finishes / stairs; provenance T-490; research module `stone_floor_census_v1.py`)

The element is defined first (ROOM_FLOOR / FLOOR_OR_LANDING / STAIR_* / THRESHOLD / UNREAD). Material follows the
evidence order project > owner rule > default:

- A default applies only to its own element.
- A conditional owner answer whose condition fails does not apply.
- Two materials at the top level make the space HELD.

Family follows from that. Stone on a room floor by a project source is B3-03. A marble stair part is B7. A threshold is
B3-04. FLOOR_OR_LANDING with a project stone source is B3-03, with an owner stair rule is B7, and with no source is
HELD.

Area comes from a polygon (m / mm, any rotation or mirror) less fixed SOLID items. A door changes no floor area: its
strip goes to B3-04 by opening id. A missing area is HELD, never 0. B3-03 adds new m2 only where no released line
carries the area. Over a porcelain line it is a MOVE, and a default-porcelain space adds 0.

## 7. Tests (`tests/t490_stone_floor_census`, 33 PASS)

Hand villa K490 (not Alsenan): an entrance hall 4.00 x 3.00 with a 0.90 door is **12.00 m2**, and its strip 0.18 is
listed to B3-04, not added. The fixture is run in m and mm, rotated 0 / 37 / 90 / 211 deg, plain and mirrored, with a
shift. A 0.30 x 0.30 column gives 11.91.

Adverse cases:

- a space already carried as porcelain is not added again (0);
- a stone note over a porcelain line is a MOVE (new 0, move 12.00);
- a missing area is HELD [0, None] and never 0;
- a stair arrival is B7 (and the porcelain default is ignored for a stair part);
- FLOOR_OR_LANDING without a printed depth is HELD (and becomes B7 once the condition is met, B3-03 with a project note);
- a same-level conflict is HELD;
- a threshold is B3-04.

Refusals: unit ft, an unknown element, fixed items larger than the face, an area without a source, an unknown evidence
kind or material, a duplicate id. The training-villa pin reproduces summary.json.

## 8. Checker re-measure proposal

Re-measure the 1F main-stair arrival from sheet04: printed 250 x 195 = 4.875 m2 against the line's 4.9225 (+0.0475,
named). Alternatively re-measure the E1 landing from sheet03 (printed 140 x 370 = 5.18 against the line's 5.1794).

## 9. Lessons-register row (proposed, ENGINEERING_REASONING_STANDARD s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-03 | "Entrance / stair-hall marble" scope item with no line (B3-03 POSSIBLY_APPLICABLE) | the scope list names a finish by a space type, but the drawings name no stone floor; the marble the freelancer prices at the entrance is the outside stair (B7) | R-T490-1: define the element first; B3-03 only by a project source; stair parts B7, thresholds B3-04; a floor at a flight foot without printed landing depth is FLOOR_OR_LANDING, HELD; never add over a carrier (MOVE) | tests/t490_stone_floor_census (normal 12.00 + adverse porcelain-not-added) | PROPOSED |
