# T-435 Ceiling and skirting completeness join for every floored space (CEILING_SKIRTING_JOIN_V1)

Worker 2 (lane A), 2026-11-01, run session_01E6cPnbyW1vJdsHk9vuCjQu. Development villa, not an accuracy claim. Research only:
research/agents_t435/* and tests/t435_ceiling_skirting_join/*; no engine module, method, rule / knowledge version, registry,
candidate or released quantity changed. ERS read: s.2.1 (element first), s.2.2 (evidence), s.2.4 (reconcile in units),
s.7 (lesson). Candidate of record ARCH_TAKEOFF_V3.0.37 reproduced on the Drive copies ("Alsenan chalet project":
P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256 ab54dd55, "ST7757 dxf.dxf" sha256 9f9d1179, decoded into .work/private only)
by research/agents_t167/v304_run.py then research/agents_t420/v3037_run.py: V3_0_37_BOQ_LINES.json sha256 **733f2efb**
(= the T-420 merged pin named in the T-421 row). Only line ids, item codes, face ids, states and quantities are committed.

## 1. The physical question (ERS s.2.1) and the rule

Every floored space has, physically, something over it (a decor ceiling, a flight or landing underside, the sky, a void,
or, for a strip in the wall thickness, the opening head) and something along its wall faces at floor level (skirting, a
wall tile run to the floor in a wet room, a door frame, nothing on an open edge). The ceiling (B10) and skirting (B3)
families are built per room face; the floor-finish family (B3-01) has, since T-414 / T-418 / T-427, more spaces than
faces (sub-face parts, stair-room parts, the dining piece). R-T435-1 (any villa, provenance T-435; rules UP-CEIL-001,
UP-SKIRT-001 at their own scope; module `ceiling_skirting_join_v1.py`, no villa constant in it):

1. the census starts from the floor-finish lines (every FIN.FLOOR.* m2 line not NOT_APPLICABLE and not a bed line) plus
   the floored parts an integration row adds (cited by task), never from the ceiling or skirting room list;
2. per space and layer exactly one of: OWNED (line ids on the same face; a NOT_APPLICABLE line with evidence owns too:
   OWNED_NOT_APPLICABLE; a BLOCKED / HELD line owns without a figure: OWNED_HELD), REASON (a named reason with evidence;
   a reason that gives the layer to another family must cite an existing line of that family, else REFUSED), or
   SILENT_OMISSION (named in m2 for the ceiling = the floor area, in lm for skirting = the drawn wall-face length or
   UNKNOWN, never 0); an owning line plus a reason giving the layer away = DOUBLE_OWNED (never summed);
3. a ceiling line smaller than its face's floor by more than 0.005 m2 with no reason is PARTIAL with the shortfall named.

## 2. Result in engineering terms (43 spaces, 86 rows, JOIN_T435.csv; summary.json)

| Layer | OWNED | OWNED_HELD | OWNED_NOT_APPLICABLE | REASON | PARTIAL | SILENT_OMISSION | DOUBLE_OWNED |
|---|---|---|---|---|---|---|---|
| Ceiling | 23 | 1 | 0 | 10 | 6 | **3 spaces, 7.345 m2** | 0 |
| Skirting | 10 | 2 | 18 | 10 | 0 | **3 spaces: 3.90 lm DRAWING-CONFIRMED + 2 UNKNOWN** | 0 |

One line owns one space in each layer (`overlap_line_ids: []`); no space is double-owned.

**Silent omissions (the finding):**

| Space | Floor m2 | Ceiling | Skirting | Cause | Lane I proposal |
|---|---|---|---|---|---|
| GF dining piece along the south facade (face GF-RFD4E1D, T-427 / T-431) | 5.645 | **no FIN.CEILING line on the face in V3.0.37**: 5.645 m2 silent. The T-283 ledger carries the face as HELD_CLASS 4.885 m2 ('plan area under the slab, ceiling type not decidable'), but no candidate line was ever built from it (the face appears in V3.0.37 only as ARCH.SPACE L-6b6412e8 4.885). The 0.760 m2 west strip (OP-003 3.80 x 0.20) has no ceiling reading at all. | 3.90 lm (wall 2.70 + column 2FCF faces 1.20, Checker-verified T-427) silent until T-431 adds it to L-71e2e002 | T-431 says "ceiling GF-RFD4E1D 4.885 HELD_CLASS -> the dining ceiling class", but there is no line to re-class: T-431 must CREATE a FIN.CEILING line for the face (4.885 m2 from the T-283 ledger, in the dining class) and carry the 0.760 m2 strip HELD (ceiling over it not read); its skirting +3.90 lm as planned. |
| GF pantry strip SITE-0a31aaa10796d33a (wet, T-427) | 1.100 | no ceiling line, no reason | no skirting line, lm UNKNOWN | the strip is a floor line only (pantry wet scope, Q-37 A); what is over it (opening head or the pantry ceiling) is not read | one row: read the strip's position (wall thickness or room) and give it the opening-soffit reason or a ceiling line; skirting: door / jamb (UP-SKIRT-001 doorless jambs) or none |
| GF pantry opening strip GF-OP-003-NO-OPENING (wet) | 0.600 | as above | as above, UNKNOWN | as above | as above |

Ceiling silent total 7.345 m2 = 5.645 + 1.100 + 0.600 (as floor area; the ceiling quantity itself stays HELD).

**PARTIAL ceilings (6 faces, shortfall 23.67 m2): not omissions.** Each is an R3 decor-ceiling line (T-283 / T-284 fill)
whose calculation names what is not decor (bulkhead undersides, dome openings, stair zones) in its own still_held list:
1F-RB72F22 19.050 vs 7.4692 (11.5808; T-283 names the west dome opening on this face), GF-RC99C2A 109.7784 vs 101.1371
(8.6413; the line's own basis is the face plan area 110.922696 less what is not decor, so its shortfall is not a floor
reconciliation and is not closed here), 1F-R8BDA49 1.4227, 1F-R48AA46 1.2410, 1F-R48CDA5 0.4472, 1F-R3CFCFD 0.3418.
Reported for the Checker, not re-derived.

**Covered by a held line (no figure, not an omission):** the GF stair room (T-421 parts 4.805 + 1.3225 = 6.1275 m2)
lies under the parent L-2175a965 'stairwell ceiling' BLOCKED_RFI whose held list names top 1.75 + ST01-MS1-L 3.755 +
MS1-T 1.495 + MS1-U 3.72 m2; skirting L-47fa825d BLOCKED_RFI. The 2F stair lobby 2.500 m2 lies in face 2F-R4D1B62:
decor part L-10e79bd4 5.6258 m2 DRAWING-CONFIRMED + parent L-dd6930fd BLOCKED (12.9742 beside); skirting L-b8d4a7f0
BLOCKED_RFI. Once T-421 lands these parts, their skirting stays HELD inside a BLOCKED line: the wall-face length of the
GF hall / lobby and the 2F lobby is not measured anywhere yet (UNKNOWN, never 0).

**Reasons used (10 per layer):** 8 valued doorway strips: ceiling OPENING_SOFFIT_IN_WALL, skirting DOORWAY_STRIP
(element 'doorway strip'; UP-SKIRT-001 'not across door openings'); GF under-stair 2.070 m2: UNDER_FLIGHT_SOFFIT
citing the ST-02 soffit line L-c77e3887 (BLOCKED_RFI) and SKIRTING_ON_HOST_FACE L-71e2e002; GF pantry part 8.9549 m2:
CEILING_ON_HOST_FACE L-eb3be58f (classes DRY + WET) and SKIRTING_ON_HOST_FACE L-71e2e002.

**Reverse join (ceiling lines on a face with no floor-finish line):** 1F-RFFE7AF ceiling 2.970 m2 (the enclosed 1F
dressing: floor area VERIFIED since V3.0.14 but no floor-finish line, already filed by the owner session 2026-10-31 to
the floor-FINISH group P-9b; no skirting line either: lm UNKNOWN); five slab soffits SOFFIT:GF:PL-01 .. 1F:PL-05
(44.446 m2, exterior soffits, no floor finish by nature).

## 3. Cross-trade checks (no quantity changed)

- ONE m2 ONE LINE: no ceiling line owns two spaces; the under-stair part's ceiling is given to the stair soffit, not to
  the open-room ceiling (no double count found: L-eb3be58f's fill already excludes stair zones).
- The pantry part's walls are inside the open-room skirting L-71e2e002 (face boundary). Whether the wet pantry walls take
  skirting or wall tile (Q-37 A wet scope) is NOT settled here: a possible over-count inside L-71e2e002, not an omission;
  for the Lead's wet-scope row.
- The GF stair room: its parent ceiling L-2175a965 and the ST-01 soffit L-1fcec332 both describe the flight underside
  over the same plan; both are BLOCKED (no figure), so no number is summed twice; lane I keeps them exclusive when either
  is valued.

## 4. Freelancer (quantities only)

Not re-compared here: the join moves no quantity. His ceiling row (409.58 m2, T-283) and the engine R3 total stay as
T-283 / T-335 report; the 5.645 m2 dining piece and 1.700 m2 pantry strips are inside his GF reception / pantry figures
by area (T-427), so the omission makes the engine's ceiling SHORT of a built surface, not a rule difference: verdict
proposal ENGINE_WRONG (missing line) for the ceiling of the dining piece, UNRESOLVED for the two strips until read.

## 5. Rule, test and lessons row (proposed)

R-T435-1 as section 1. Tests tests/t435_ceiling_skirting_join (13): hand villa K435 normal (owned, wet tile reason, open
to sky, flight soffit, host face, door strip, partial 1.50 m2, a READY part added) and adverse: the named 'floored space
with no ceiling counted 0' (stays SILENT 3.60 m2, line_qty None), a reason citing a missing / wrong-family line
(REFUSED), a ceiling line beside a flight-soffit reason (DOUBLE_OWNED), a ceiling beside open-to-sky (DOUBLE_OWNED), one
line on two spaces (overlap), an extra part already in the census (refused), a reason for the wrong layer / unknown
code (refused), a HELD floor area (HELD, never 0), units kept apart; plus the committed Alsenan table reproduces.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | the GF dining piece (5.645 m2) and two pantry strips (1.700 m2) have a floor-finish line and no ceiling line; the dining piece's ceiling exists only in a research ledger (T-283 HELD_CLASS 4.885) | the ceiling family is built from its own room-face list; floored parts added later (strips, re-classed zones) are never checked against it | R-T435-1 (any villa): every derived per-room layer is joined to the floor census, each floored space OWNED / REASON (with a cited line) / SILENT in m2 / lm, never 0 | tests/t435_ceiling_skirting_join | proposed |

## 6. For the Checker (re-measure, not from this file)

1. Reproduce V3_0_37_BOQ_LINES.json (sha 733f2efb) and run `python3 -I research/agents_t435/t435_alsenan.py <dir>`:
   86 rows, table sha in summary.json.
2. Two spaces by hand: (a) GF-RFD4E1D: search V3.0.37 for any FIN.CEILING line whose location.room_id or formula names
   the face (expected: none; only ARCH.SPACE L-6b6412e8 4.885), then the T-283 ledger row (CEILINGS_T283.csv, HELD_CLASS
   4.885); (b) the GF under-stair part 2.070 m2: L-224e2fa4 floor, the ST-02 soffit L-c77e3887 exists (BLOCKED_RFI), and
   no FIN.CEILING line carries the part.
3. The 2F stair lobby 2.500 m2 against L-10e79bd4 / L-dd6930fd (face lines cover it; the lobby's position in the
   decor part 5.6258 is not shown by the line and is not claimed here).

## 7. What is missing

The skirting wall-face lengths of the GF stair hall / lobby, the 2F lobby and the two pantry strips (UNKNOWN); the
ceiling over the 0.760 m2 west strip of the dining piece; the wet-pantry wall skirting / tile question (s.3). No owner
question: ERS s.2.7 is not met (all items are drawing reads or lane I line work).
