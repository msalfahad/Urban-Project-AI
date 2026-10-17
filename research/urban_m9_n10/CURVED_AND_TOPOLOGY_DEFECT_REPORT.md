# Curved geometry and room topology (Phase N10)

## 1. What was wrong (as found at 504b56a)

| id | Defect | Effect |
|---|---|---|
| D-P9-01 | curved glazing in a curved wall gap is not read as a window unless its layer is declared | the room it bounds is not closed: no quantity at all |
| D-P9-02 | with roles declared, the curved window is closed at the glazing line | floor and ceiling take the 0.438423 m² strip between the face and the glazing (7.507006 instead of 7.068583 m²); the wall finish becomes a range |
| D-P9-04 | the zone-bounded space on the reference plan cannot be verified | 13 differences unverified |

## 2. The V2.9 method (UP-OPEN-CURVED-001, REQUIRES_CONFIRMATION)

A **curved gap** is a gap in a curved wall band: concentric wall-layer arcs 0.10 – 0.45 m apart. It is an **opening** only if all of these hold:

- Both faces open over the same span. The outer face may stop up to 0.03 m further along the arc, for a splayed jamb.
- A jamb line on a wall layer joins the face ends at each end, within 0.01 m.
- The sweep is at most half a turn.
- The mid-band arc is at least 0.40 m.
- No wall arc runs inside the gap.

Kinds:

- **DOOR**: a free swing hinged within 0.30 m of a jamb end, with its radius fitting the mid chord within max(0.15 m, 25 %).
- **WINDOW**: glazing arcs over at least half the gap.
- **PASSAGE**: anything else.

Closure: an arc threshold on each wall face. The room ends at its own face.

Width: the arc of the face the room meets. Every basis is published (inner, mid-band, outer arc, chord).

The strip between the face and the glazing is a reveal / sill strip, measured radially:

- depth = area / (sweep × mid radius);
- the head soffit of a curved reveal is the strip's own area.

**Refused gaps are listed with their reason, never guessed.** The reasons are FACES_STOP_AT_DIFFERENT_ANGLES, SWEEP_OVER_HALF_A_TURN, NARROWER_THAN_MIN_GAP, WALL_ARC_INSIDE_THE_GAP and NO_JAMB_LINE_AT_BOTH_ENDS / ONE_END.

**Glazing-layer inference (D-P9-01).** A layer is read as glazing only when all three hold:

- it is an OTHER layer (a declared role is never changed);
- at least one of its arcs, concentric with a jambed curved gap, covers half of that gap;
- at least half of its linework lies in wall gaps.

## 3. Synthetic tests (`tests/m9_n10/test_n10_curved_openings.py`, 21 tests)

| Scenario | Result |
|---|---|
| curved external wall with sill glazing (W4) | room 7.068583 m², width 4.312389 m on the room face, plaster 24.7623 m², skirting 9.712389 m, reveals 0.678423 m² |
| curved floor-level glazing (W5) | plaster 17.00 m², skirting 5.40 m, the strip is floor |
| curved door (D2, owner fallback height 2.20 m) | plaster 27.737167 m², skirting 8.712389 m |
| curved passage | plaster 26.937167 m² (full height), skirting 8.712389 m |
| splayed jamb (outer face 20 mm further) | still an opening; same room |
| gap without jamb lines | not an opening (refused, reason listed) |
| wall arc inside the gap | wall, not an opening |
| furniture arcs and decoration arcs | change nothing |
| nested block turned 30° | same quantities |
| plan rotated 30° / 200°, mirrored, translated, in metres, entities reordered | same quantities |
| curved gap straddling 0° | handled |
| V2.8 as found | loses or overcounts the room (the defect reproduced first) |

## 4. Independent side (`tests/m9_n10/test_n10_indep_curved.py`, 6 tests)

`tools/indep_reader.py` reads the jambed curved gaps of the raw DXF itself (ezdxf + shapely, no engine module). With `curved_closures` (opt-in, so the earlier readings are unchanged) it closes them on both faces.

On example 4S, the V2.8 → V2.9 floor change (7.507006 → 7.068583 m²) is **VERIFIED** by INDEPENDENT_FACE.

## 5. Zone-bounded room (D-P9-04) — root cause

The reader's gap rule split two recesses (0.2617 + 0.6368 m²) off the space. The space itself was right.

The verifier now does two things:

- unions the reader's faces inside the room polygon (for rooms joined through passages);
- reads the zone lines the run used, by their handle (the run stores decimal handles; the reader uses hexadecimal).

The union equals the engine's polygon, with a symmetric difference of 0.0.

V2.6 → V2.7.1 now gives 45 VERIFIED, 10 EXPLAINED_UNVERIFIED and 0 CONTRADICTED; it was 32 of 55 verified.

## 6. Room topology invariants checked

- Opening closures are conservative: floor + strip = the room closed at the glazing, 7.068583 + 0.438423 = 7.507006 m².
- The facade outline's plate equals the engine's existing gross floor plate on every reference-plan floor (difference 0.000000 m²).
- V1 – V2.8 take no new code path: the `v29` flag is passed only by ARCH_TAKEOFF_V2.9. Their 2,170 snapshot files are byte-identical.
