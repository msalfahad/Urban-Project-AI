# BOQ impact: ARCH_TAKEOFF_V2.6 → V2.7 (Phase 2B-7)

## Method: no unexplained change

`tools/arch_v27_explain.py --before <V2.6 run> --after <V2.7 run>` lists every BOQ total that differs, per item code
and location. Each difference is attributed to the V2.7 correction records (`CORRECTIONS_V2_7.json`) whose scope covers
it; a difference no record covers is **UNEXPLAINED**, and the tool exits 1.

The scopes:

| record | locations it can explain |
|---|---|
| DOOR_OPENING, DOOR_FRAME | the opening's rooms, its opening / strip locations |
| CURVED_WALL_BAND | the floor's walls |
| WET_EVIDENCE, ARC_POLYGON | the face's rooms, their openings |
| SLIVER_MERGE | its room |
| LAYER_ROLE, COLUMN_SHAPES | the whole floor (they change its topology) |

**Two guards make the attribution meaningful.**

- `tests/m9_p2b7/test_p2b7_explained.py` runs the explainer on 10 synthetic drawings with **declared** layer roles, so
  no floor-wide record can cover anything. Every difference must be covered by its own correction's record, of the
  kind expected for that drawing.
- With its log emptied, the same V2.7 output is all UNEXPLAINED.

**On the reference plan, no floor-wide record is used.** LAYER_ROLE / COLUMN_SHAPES covered every difference of the
draft V2.7. That cover hid D-P7-02 and D-P7-04 (`ENGINEERING_DEFECT_REGISTER.md`). Both were fixed; the final run
has neither record.

## The synthetic villa and its mirror (shareable fixtures)

V2.6 → V2.7, in Mode U and in Mode A (synthetic heights): **0 differences** in all four runs. Every correction leaves
an ordinary plan unchanged.

## Synthetic drawings (shareable; roles declared)

| drawing | differences | explained by | what changes (V2.6 → V2.7; truth in `INDEPENDENT_EVIDENCE.md`) |
|---|---|---|---|
| CROSSING | 26 totals | DOOR_OPENING | door 1.027 → 0.80 m. Bathroom plaster 26.2203 → 26.382 m2, wall tile 20.6079 → 20.7696, skirting 8.477 → 8.554 m, upturn 1.7031 → 1.7108 m2, threshold and doorway waterproofing 0.2054 → 0.16 m2, door-opening plaster 1.0454 → 1.00 m2. The door is released (external aluminium 0 → 1) |
| CROSSING turned 37°, metres | 26 | DOOR_OPENING | as CROSSING |
| PLAIN turned 37°, metres | 1 | SLIVER_MERGE | the zero-length waterproofing termination line is gone |
| B10 (curved wall) | 3 | ARC_POLYGON, CURVED_WALL_BAND | wall run 10.20 → 13.546206 m (+ the 3.346206 m band). False 3.0 m termination of kind OTHER gone. Upturn 2.683501 → 2.683417 m2: the boundary now follows the arc by ≤ 1 mm chords (−0.003 %) |
| W.C. + basin-only lobby | 16 | WET_EVIDENCE | lobby 10.20 m2: wet tile, waterproofing floor, ceiling, plaster 34.62, wall tile 26.94, skirting 11.00, upturn 2.20 → 0; ARCH.SPACE 10.20 (REVIEW). The W.C.'s doorway waterproofing 0.16 m2 moves to the W.C. The lobby's external doorway: marble 0.20 m2 → held (REVIEW question), never dry porcelain |
| W.C. + lobby with basin and a drawn WC | 0 | - | wet in both |
| Framed door in a group block / nested plan | 1 each | DOOR_FRAME | the door set is released (0 → 1); frame 2.40 / 4.40 m → 0.80 m |
| OPEN_SIDE (door in a wider opening) | 0 | - | the wider opening is kept, with its reason |
| B01 (rectangular bathroom) | 0 | - | - |

## The private reference plan (three floors; aggregates only, no room ids)

95 totals differ, **0 unexplained**, from 9 correction records.

### 1. One door narrowed to its jamb span (DOOR_OPENING, 50 totals)

The door's wall gap is 1.023 m; its symbol's jamb lines are 0.80 m apart, and the rest of the gap is a wall return
drawn on both faces.

| item | V2.6 | V2.7 | change |
|---|---|---|---|
| plaster (its two rooms and the opening) | 63.8657 | 64.1400 | +0.2743 m2 |
| wall tile | 48.9943 | 49.3020 | +0.3077 m2 |
| skirting | 19.6335 | 19.7800 | +0.1465 m |
| waterproofing upturn | 4.1667 | 4.1960 | +0.0293 m2 |
| marble threshold | 0.1535 | 0.1200 | −0.0335 m2 |
| doorway waterproofing | 0.3335 | 0.3000 | −0.0335 m2 |
| internal PVC door sets | 1 | 2 | +1: the held door is released |

The two rooms are re-identified, because their boundary changes at the door. Their floor, ceiling and waterproofing
floor are identical, which accounts for 30 of the 50 totals.

### 2. The curved wall band (CURVED_WALL_BAND, 1 total)

ARCH.WALL_RUN of the floor goes from 95.7539 to 97.6389 m: +1.884956 m, the band's mid arc. The raw-ezdxf census
finds the same band to 1e-6. The basis is owner decision D-07.

### 3. Three basin-only spaces to REVIEW (WET_EVIDENCE, 44 totals)

These are hand-wash spaces. Their only "second evidence" was their basins' own fittings, drawn loose on the sanitary
layer (D-P7-03).

| item | V2.6 | V2.7 |
|---|---|---|
| wet floor tile, waterproofing floor, ceiling | 9.3482 m2 each | 0 |
| ARCH.SPACE (REVIEW: one WET_CLASSIFICATION_REVIEW question per space) | 0 | 9.3482 m2 |
| plaster | 21.3696 m2 | 0 |
| wall tile | 16.4237 m2 | 0 |
| skirting | 15.2462 m | 0 |
| waterproofing upturn | 3.0492 m2 | 0 |
| doorway strip porcelain (two doorways) | 0.33 m2 | 0: held, with THRESHOLD_OF_SPACE_UNDER_WET_REVIEW |
| doorway waterproofing | 0.24 m2 | 0.24 m2. Unchanged in total; the W.C. now owns its own doorway piece |

**This is the largest V2.7 change on the plan, and it is a reduction of the released BOQ, not a correction of a
measured quantity.** The scope is held for the owner's answer (D-17). Under D-18, ceiling and plaster, which are the
same in both readings, could be released.

### 4. Arc polygons and the door frame

**ARC_POLYGON** (14 totals) overlaps item 3: one of the three spaces has an arc in its boundary.

**DOOR_FRAME** (0 totals): one door's frame was read across a whole block (2.0 m) and is now not drawn. No quantity
changes; one DOOR_CLOSURE_FRAME_DISAGREE review is gone.

### Questions and lines

- **Unresolved questions: 283 → 264.**
  - The three review spaces drop their 6 wet-finish questions each, and each gains one review question.
  - The released door drops its fit review; the frame correction drops one frame disagreement.
  - The narrowed door's strip is now attributed.
  - New: 2 doorway-strip reviews, 1 column-role refusal, 1 door-minimum-reference question (OQ-05).
- **BOQ lines: 511 → 484.** The three review spaces carry no finish lines.

### Stage C (five rooms read independently, 66 checks)

V2.6: 8 failing. V2.7: 0 failing.

Per the authorization this is not, by itself, success: the five rooms are one sample of one plan. Above, 44 of the
95 changes fall outside those five rooms: the three hand-wash spaces held for review.
