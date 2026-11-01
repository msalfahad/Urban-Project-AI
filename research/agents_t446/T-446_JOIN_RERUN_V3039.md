# T-446 Ceiling and skirting completeness join re-run on the candidate of record ARCH_TAKEOFF_V3.0.39

Worker 2 (lane A), 2026-11-01. Development villa, not an accuracy claim; the method (R-T446-1) is for every villa.
Research only: `research/agents_t446/*`, `tests/t446_join_rerun/*`; no engine module, method, rule / knowledge version,
registry, candidate or released quantity changed; the T-435 module and table are imported / read, never edited. ERS
applied: s.2.1 element first, s.2.2 evidence, s.2.4 reconciliation in units, s.4 rule + test, s.7 lesson.

## 0. Run identity

Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (sha256 `ab54dd55`), "ST7757 dxf.dxf"
(`9f9d1179`), decoded by the wrapper into `.work/private` only. Own fresh `research/agents_t167/v304_run.py`, then
`research/agents_t429/v3039_run.py` (Python 3.11.18): **V3_0_37 `733f2efb`, V3_0_38 `57cca61c` and V3_0_39 `8d1bbe5d`
reproduced** (the T-420 / T-421 / T-429 Gate B pins). The merged T-435 driver re-run on that V3_0_37 gives its committed
table sha `f9d5087c` (baseline reproduces). `python3 -I research/agents_t446/t446_alsenan.py <dir> --write` ->
`JOIN_T446.csv` (152 rows, sha `71cb463f`), `DELTA_T446.csv` (sha `50157b2e`), `summary.json`. Only line ids, item
codes, face ids, states and quantities are committed.

## 1. The physical question and what changed in the census (ERS s.2.1)

Every walked floor surface has, physically, something above it and something (or nothing) along its wall faces at floor
level. T-435 built its census from the B3-01 floor-finish lines only (R-T435-1). V3.0.39 adds three things the task row
names, and they show that census is too narrow:

1. **Lift thresholds B6-07** (3 x 0.500 m2, FIN.MARBLE.LIFT_THRESHOLD, T-421): a floor surface valued in the MARBLE
   family, not FIN.FLOOR, so R-T435-1 would never see it. T-421 also took their certain floor part 0.300 m2 out of the
   host floor nets (GF L-7625f35c 109.778417 -> 109.478417, 1F L-b06400d4 33.711036 -> 33.411036, 2F lobby gross
   2.500 -> net 2.200).
2. **Stair-room floor parts** (T-421 from T-418): GF hall +1.00 4.805, back lobby +0.30 1.3225, strip GF-ST-CN HELD
   0 .. 0.230, 2F lobby 2.200 net. V3.0.39 puts them on their FACE's room id (GF-R31F8AE / 2F-R4D1B62), the same id as
   the parent ceiling / skirting lines, so a plain room-id join would merge the parts and let the BLOCKED parent "own"
   them silently. They differ physically (the +0.30 lobby lies under the +3.50 half landing; the hall does not).
3. **The corrected tread set** (T-429): the treads / steps are B7 lines (flight-owned), not floor-finish lines; see s.4.

Searching the same candidate for every other walked surface valued outside FIN.FLOOR found two more classes T-435 did not
census: **doorway marble thresholds** (14 FIN.MARBLE.THRESHOLD lines, 0.12 .. 0.20 m2 each: wet-room doors and the
door closures) and **opening threshold strips not NOT_APPLICABLE** (14 ARCH.THRESHOLD lines: 6 exterior-door strips
HELD 0.15 .. 0.40, 2 doorless passages OP-020 / OP-027 BLOCKED, 5 unattributed strips with floor not established, the
gate D-GF-15 BLOCKED). NOT_APPLICABLE threshold lines (owned elsewhere, e.g. the lift wall bands) are not spaces.

**R-T446-1** (any villa, provenance T-446; `join_rerun_v1.py`, no villa constant): (1) a walked floor surface valued
outside B3-01 (B6-07 lift threshold, doorway marble, opening strip) is a census space of its own, m2 or HELD (never 0),
keyed `<face>~<element>` when its face is floored or carries a ceiling / skirting line (a host's m2 never changes, a
host's line is never inherited); (2) a space whose layer is given to its host face AND that also has its own line of
that layer is DOUBLE_OWNED (the T-435 join accepted it as OWNED: proved in the adverse test); (3) a floor part's skirting
lm is the sum of its WALL / COLUMN stretches; a flight side (OPEN / STAIR_SIDE = B7-07 / B7-08) or an opening carrying
part skirting is refused; held stretches stay HELD, never added; (4) the delta classes NEW / GONE / SPLIT / SPLIT_FROM /
OWNER_CHANGED / FLOOR_M2_CHANGED.

## 2. Result on V3.0.39 (76 spaces, 152 rows; summary.json)

Census re-adds to the candidate: B3-01 floored lines **381.449050 m2 = census 381.449050 m2, residual 0.000000**, 1 held
line (GF-ST-CN 0 .. 0.230) held on both sides. Spaces: 45 B3-01, 14 doorway marble, 3 lift thresholds, 14 threshold
strips. No space DOUBLE_OWNED, no line owns two spaces (`overlap_line_ids: []`).

| Layer | OWNED | OWNED_NOT_APPLICABLE | PARTIAL | REASON | SILENT_OMISSION | UNKNOWN (floor / head not established) |
|---|---|---|---|---|---|---|
| Ceiling | 22 | 0 | 6 | 39 | **3 spaces, 7.345 m2** | 6 |
| Skirting | 10 | 18 | 0 | 39 | **3 spaces: 3.900 lm DRAWING-CONFIRMED + 0.700 lm HELD (jambs)** | 6 |

### 2.1 New floored elements and their owner / reason (each with its drawing evidence)

| Element (class) | m2 | Ceiling | Skirting | Evidence |
|---|---|---|---|---|
| GF-RC99C2A~LIFT:ELV-01-GF (B6-07) | 0.500 | CEILING_ON_HOST_FACE L-eb3be58f + OPENING_SOFFIT_IN_WALL | DOORWAY_STRIP | certain 0.300 m2 on the landing floor inside the face (T-421 s.2); the face ceiling is the face plan area 110.922696 less non-decor, so the threshold is under it; the 0 .. 0.200 band part is under the lift door head (register LIFT LANDING THRESHOLD); width = clear width between jambs, jambs = B6-06, front open: no wall face |
| 1F-R78C367~LIFT:ELV-01-1F (B6-07) | 0.500 | host L-43bf1f86 (the room's decor ceiling carried once) + door head | DOORWAY_STRIP | as above |
| 2F-R4D1B62~LIFT:ELV-01-2F (B6-07) | 0.500 | host L-dd6930fd (2F stair room parent, BLOCKED) + door head | DOORWAY_STRIP | OP-002 on the 2F lobby's north face (T-441 2F lobby table) |
| 14 doorway marble thresholds (GF OP-017 / 018 / 025 / 026, closures D-GF-02 / 10 / 14; 1F OP-004 / 008 / 010 / 018 / 019, D-1F-04; 2F OP-006) | 0.12 .. 0.20 | OPENING_SOFFIT_IN_WALL | DOORWAY_STRIP | each line's own input `opening_kind DOOR` or door id; strip in the wall thickness (UP-CEIL-001 eligible surfaces; UP-SKIRT-001 not across doors) |
| 6 exterior-door strips HL GF OP-005 / 008 / 009 / 013 / 021, 2F OP-001 | HELD 0.15 .. 0.40 (bounded, finish held) | OPENING_SOFFIT_IN_WALL | DOORWAY_STRIP | each line's formula 'one side exterior' (T-218 class) / roof door |
| GF-STRIP-OP-020, GF-STRIP-OP-027 (doorless passages) | HELD (strip 0.18 / 0.15 beside, finish not established) | OPENING_SOFFIT_IN_WALL | **SILENT: jamb returns 0.400 / 0.300 lm HELD** | `opening_kinds PASSAGE`, wall 0.20 / 0.15: URBAN-SKIRTING-OPENING-METHOD doorless jambs (PROVISIONAL); no skirting line names them; OP-020 is T-447's reveal item |
| 5 unattributed strips (GF SITE-19643bcc / e3b5d322 / f829b5b7, 1F SITE-29faecd8 / fd160ff8) | HELD | UNKNOWN_FLOOR_NOT_ESTABLISHED | same | each line's `floor_status NOT_ESTABLISHED` (BLOCKED_RFI): no layer question until the floor is read |
| gate D-GF-15 threshold strip | HELD | UNKNOWN_HEAD_NOT_ESTABLISHED | same | its formula: clear width and host wall not established (T-325 UNRESOLVED, T-326 holds jambs and head) |
| GF-R31F8AE~GF-ST-HALL +1.00 | 4.805 | CEILING_ON_HOST_FACE L-2175a965 (BLOCKED) | SKIRTING_ON_HOST_FACE L-47fa825d (BLOCKED); T-441: **4.650 lm DRAWING-CONFIRMED** + HELD 1.900 / 0.600 / 0.200 / 0.600 / 0.100 | the parent names the top and the flight undersides; the piece over the hall is not split out |
| GF-R31F8AE~GF-ST-LOBBY030 +0.30 | 1.3225 | **UNDER_FLIGHT_SOFFIT L-1fcec332** (ST-01 soffit, BLOCKED) | host L-47fa825d; T-441: **1.400 lm DC** + HELD 1.150 | under the +3.50 half landing (T-418 / T-421 s.1); L-2175a965's own formula: 'stair soffit pieces are the stair soffit lines' |
| GF-R31F8AE~GF-ST-CN | HELD 0 .. 0.230 | host L-2175a965 | host L-47fa825d, no face read | strip unread (T-418): lobby side or under the winders |
| 2F-R4D1B62~2F-ST-LOBBY +9.70 | 2.200 net | host L-dd6930fd (decor part L-10e79bd4 5.6258 beside) | host L-b8d4a7f0; T-441: **3.350 lm DC**, nothing held | T-441 table |

T-441's face table (merged ece154fe, `FACES_T441.csv` sha `084fdf8f`) re-summed under rule 3 reproduces its figures
(hall 4.650, lobby 1.400, 2F lobby 3.350, arrival 4.150 lm); no flight side and no opening carries part skirting.

### 2.2 Silent omissions (the finding) and the lane I proposals (nothing valued here)

| Space | Ceiling | Skirting | Status of the fix |
|---|---|---|---|
| GF dining piece GF-RFD4E1D 5.645 m2 (still no floor line in V3.0.39) | 5.645 m2 silent | 3.900 lm DRAWING-CONFIRMED silent | unchanged since T-435: T-431 (QUEUED) creates the floor line; its ceiling line must be created with it (T-435 s.2) |
| GF pantry strip SITE-0a31aaa1 1.100 m2 | 1.100 m2 silent | **now REASON**: WET_WALL_TILE_TO_FLOOR L-f5c5a1a9 (T-439 MERGED 2f63773e) | T-439 lane I proposal: one FIN.CEILING line 1.700 m2 for both strips (cross-referenced, not re-derived) |
| GF pantry strip GF-OP-003-NO-OPENING 0.600 m2 | 0.600 m2 silent | **now REASON**, as above | as above |
| GF-STRIP-OP-020 / OP-027 (new census) | REASON | 0.400 / 0.300 lm HELD silent | jamb returns: T-447 (OP-020 reveal); OP-027: one line in a lane A row (read the reveal: tile or skirting owner) |

Ceiling silent 7.345 m2 before and after (the same three spaces; T-439's line is not integrated yet). Skirting silent:
before 3 spaces (3.900 lm + 2 UNKNOWN), after 3 spaces (3.900 lm DC + 0.700 lm HELD): the two pantry strips left the
silent list by T-439's merged ruling; the two doorless passage strips entered it through the widened census.

## 3. Delta against the merged T-435 table on V3.0.37 (DELTA_T446.csv)

| Change | Rows | What |
|---|---|---|
| NEW | 62 | the 31 elements of s.2.1 outside B3-01 (3 lift thresholds, 14 doorway marble, 14 threshold strips), 2 layers each |
| SPLIT / SPLIT_FROM | 4 / 8 | GF-R31F8AE (T-435 EXTRA 6.1275 m2, OWNED_HELD by the parents) -> hall / lobby / CN parts; 2F-R4D1B62 (EXTRA 2.500) -> 2F-ST-LOBBY 2.200 net + its lift threshold. Owner changed from "the parent line on the same id" to a named host reason; the lobby's ceiling moved to the ST-01 landing soffit |
| OWNER_CHANGED | 2 | the two pantry strips' skirting: SILENT -> WET_WALL_TILE_TO_FLOOR (T-439) |
| FLOOR_M2_CHANGED | 4 | GF-RC99C2A 109.7784 -> 109.4784 and 1F-R78C367 33.711 -> 33.411 (both layers; owner unchanged): the threshold's certain 0.300 m2 left the floor net and is now its own space under the same host ceiling. Consequence: the GF-RC99C2A ceiling PARTIAL shortfall reads 8.3413 m2 (was 8.6413); it is the line's own non-decor list, not a floor reconciliation (T-435 s.2), and no ceiling m2 is lost |
| GONE | 0 | |

## 4. Cross-trade checks (no quantity changed)

- ONE m2 ONE LINE: the threshold's ceiling is the host's (no own ceiling line exists for any threshold; rule 2 would
  flag one as DOUBLE_OWNED); the host floor nets exclude the threshold's certain floor part exactly once (T-421 s.2);
  the census residual is 0.000000 m2.
- TREADS (T-429): B7-02 / B7-06 lines are flight-owned walking surfaces, not B3-01 floor; none is keyed as a floor line,
  and the stair-room floor parts are the T-418 partition beside the treads (no tread m2 in the census). Their layers
  are B7 lines: soffit FIN.STAIR.SOFFIT ST-01 L-1fcec332 / ST-02 L-c77e3887 (both BLOCKED_RFI) and the stair skirting
  B7-07 / B7-08, which has **no candidate line in V3.0.39** (T-410 measures it; T-443 QUEUED integrates the stair-room
  children). The FIN.STAIR.FLIGHT lm lines are pitch-line lengths, not skirting, and are not cited as such.
- The doorway marble thresholds sit on strips that carry no FIN.FLOOR line (the marble is their floor finish): no double
  floor finish found.

## 5. Freelancer

No quantity moves, so no new comparison: his ceiling row (409.58 m2, T-283) and skirting (T-106) stay as T-435 /
T-439 report. Verdict proposals unchanged: dining ceiling ENGINE_WRONG (missing line), pantry strip ceilings ENGINE_WRONG
(T-439), pantry strip skirting RULE_DIFFERENCE (T-439). New: passage jamb returns OP-020 / OP-027 UNRESOLVED (0.700 lm
HELD; whether he carries them is not traceable from his rows).

## 6. Lessons register row (proposed)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | the T-435 census missed 31 walked surfaces valued outside FIN.FLOOR (lift thresholds, doorway marble, threshold strips) and would merge stair-room parts with their BLOCKED parent | the census keyed on one family's item codes and one room id per face | R-T446-1 (any villa): census every walked floor surface whatever family values it, key elements / parts apart from their host, host reason + own line = DOUBLE_OWNED, part skirting only on WALL / COLUMN stretches | tests/t446_join_rerun | proposed |

## 7. For the Checker (re-measure, not from this file)

1. Reproduce V3_0_39_BOQ_LINES.json `8d1bbe5d`, run `python3 -I research/agents_t446/t446_alsenan.py <dir>`: 152 rows,
   table `71cb463f`, delta `50157b2e`, residual 0.000000 m2.
2. By hand: (a) L-c32effca's formula and L-7625f35c's deduction (0.300 m2) -> the threshold is under L-eb3be58f's plan
   (face plan area 110.922696) and has no ceiling line of its own; (b) GF-ST-LOBBY030 under the +3.50 half landing
   (T-418 / T-421 s.1) and L-1fcec332's formula 'flight / landing undersides'; (c) L-9bcc79e7 / L-868aee12 inputs
   `opening_kinds PASSAGE`, `wall_t_m 0.2 / 0.15` -> jamb returns 0.400 / 0.300 lm, no skirting line names them.
3. Search V3.0.39 for any FIN.CEILING line on GF-RFD4E1D, SITE-0a31aaa1 or GF-OP-003-NO-OPENING (expected none).

## 8. What is missing

Ceiling of the dining piece and the two pantry strips (lane I: T-431, T-439 proposal); jamb returns of OP-020 (T-447)
and OP-027 (no row yet); the floor of the 5 unattributed strips and the gate D-GF-15 head; the split of the stair-room
parents (T-443); stair skirting lines B7-07 / B7-08. No owner question: ERS s.2.7 is not met (drawing reads and lane I
line work).
