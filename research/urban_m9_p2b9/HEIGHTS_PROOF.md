# Heights proof — wall-finish heights read from the drawing (ARCH_TAKEOFF_V2.8, UP-HGT-001)

## 1. The rule

Every height a quantity uses is a **candidate** that records five things:

- its source: the entity and its text;
- its value;
- its unit, stated or inferred;
- its scope: opening, room, floor or project;
- its rank.

The governing candidate is the one with the best rank; ties break to the most specific scope (opening, then room,
then floor, then project).

| Rank | Evidence | Read from |
|---|---|---|
| 1 | element annotation | a text on the element: next to an opening (`SILL 0.90`, `H=2.20`, `1.50x1.20`) or inside a room (`C.H. 2.70`, `WALL TILES 2.40`, `PLASTER TO 3.20`) |
| 2 | door / window schedule | a schedule sheet (title, header row MARK / WIDTH / HEIGHT / SILL, units in the header); a row is bound to an opening by the mark drawn next to it (within 1.20 m; ambiguous if a second opening is within 0.10 m of the same distance) |
| 3 | section / elevation | level texts on a section sheet (F.F.L., F.C.L., U/S SLAB, T.O.S., parapet), placed at their level lines (the y calibration must match the drawing unit within 1 %, residual ≤ 0.30 m); each band is bound to a plan floor by the floor name on the band, or an F.F.L. equal to the plan level, or one floor and one F.F.L. |
| 3.5 | derived | the plan-level interval minus every sourced component (the V2.2 derivation) |
| 4 | floor note | a general note on the floor's plan sheet (`ALL WINDOW SILLS 1.00 M`, `CEILING HEIGHT 3.00 M UNLESS NOTED`) |
| 4.5 | project note | a general note on another sheet |
| 5 | project rule | the project facts file (an approved project rule or owner project fact) |
| 6 | Urban default | the owner reference door heights (UP-DOOR-HGT-001), **always labelled HEIGHT_ASSUMED** |

Further rules:

- **Each trade uses its own height.**
  - Plaster runs to the structural soffit: U/S SLAB − F.F.L.
  - Paint and full-height wall tile run to the finished ceiling: F.C.L. − F.F.L.
  - A ceiling note is never taken as a soffit.
- **A floor-to-floor height is never a wall height.** It is recorded as evidence only.
- **Conflicts and overrides.**
  - Two governing candidates more than 5 mm apart are a **CONFLICT**: no value, the quantity is held, and the
    conflict is listed in `MISSING_HEIGHT_EVIDENCE.json`.
  - A lower-ranked candidate that disagrees is kept as **overridden**, with its difference.
- **Units.** A stated unit converts. Otherwise the m / cm / mm readings inside the physical range of the quantity are
  kept, and exactly one distinct value must remain; if more remain the reading is `UNIT_AMBIGUOUS` (nothing is
  guessed).
  - Ranges: width 0.3–8 m, opening height 0.3–6 m, sill 0–3 m, room height 1.8–9 m.

## 2. Proof on worked example 1

Example 1 is a 4.00 × 3.00 m room: run 14.00 m, door 1.00 × 2.20, window 1.50 × 1.20 with sill 1.00.

Every row below is a test in `tests/m9_p2b9/test_p2b9_heights.py`. "Hand" is `p2b9_truth.py`.

| Drawing evidence | Governing height (source) | Formula | Hand | Engine | Diff | Status |
|---|---|---|---|---|---|---|
| section F.C.L. +3.00, U/S SLAB +3.00; schedule D1 2200, W1 1200 sill 1000 | plaster 3.00 (SECTION, U/S SLAB); paint 3.00 (SECTION, F.C.L.) | 14.00 × 3.00 − 1.00 × 2.20 − 1.50 × (2.20 − 1.00) | 38.00 / 38.00 | 38.00 / 38.00 | 0 | VERIFIED (hand) |
| the same plus project facts (door 2.10, window 1.50) | door 2.20 (SCHEDULE, rank 2); facts 2.10 kept as overridden (rank 5) | as above | 38.00 | 38.00 | 0 | VERIFIED (hand) |
| a second section only: F.C.L. +2.80, U/S SLAB +3.00 | paint 2.80, plaster 3.00 | paint 14 × 2.80 − 2.20 − 1.80; plaster 42.00 − 2.20 − 1.80 | 35.20 / 38.00 | 35.20 / 38.00 | 0 | VERIFIED (hand) |
| room note `C.H. 2.70` + section | paint 2.70 (ELEMENT_ANNOTATION, room); plaster 3.00 (SECTION) | 14 × 2.70 − 2.20 − 1.80 | 33.80 | 33.80 | 0 | VERIFIED (hand) |
| `SILL 0.90` next to W1 + schedule sill 1.00 | sill 0.90 (ELEMENT_ANNOTATION); schedule 1.00 overridden, +0.10 | head 0.90 + 1.20 = 2.10 ≤ 3.00 → deduction 1.80 | 38.00 | 38.00 | 0 | VERIFIED (hand) |
| floor note only | paint 3.00 (FLOOR_NOTE); plaster BLOCKED (no soffit anywhere); window sill 1.00 (FLOOR_NOTE), height none | paint range: window deduction between 0 and 1.50 × 3.00 | [35.30, 39.80] | [35.30, 39.80] | 0 | VERIFIED (hand) |
| two sections: F.C.L. +3.00 and +2.80 | paint **CONFLICT** (no value); plaster 3.00 (both agree) | — | paint held; plaster 38.00 | BLOCKED_RFI; 38.00 | 0 | VERIFIED (hand) |
| a section with only F.F.L. ±0.00 (GF) and F.F.L. +3.60 (1F) | floor-to-floor 3.60 recorded; plaster and paint BLOCKED | — | held | held | 0 | VERIFIED (hand) |
| no evidence at all | everything BLOCKED; door 2.20 = Urban default, ASSUMED | — | held | held | 0 | VERIFIED (hand) |

Unit inference is tested by `test_units_are_inferred_only_when_unique`:

| Raw | Quantity | Result |
|---|---|---|
| `2200` | height | 2.20 m (mm) |
| `2.20` | height | 2.20 m (m) |
| `220` | height | 2.20 m (cm) |
| `1000` | sill | 1.00 m (mm) |
| `100` | sill | **UNIT_AMBIGUOUS** (1.00 or 0.10 m) |
| `9000` | height | OUT_OF_RANGE |

## 3. Invariance

The example-1 sill and floor-glazing drawings were transformed five ways:

- translated 1,000 km;
- mirrored, each sheet about its own centre;
- drawn in metres (`--units m` recorded: the only closed rectangles are the three sheet frames, which fit
  centimetres better, so the admission rightly refuses to guess);
- entities reordered;
- the plan alone turned 30°.

Every height, opening class, opening area and finish quantity is identical (`test_p2b9_invariance.py`, 10 tests).

**Limitation L-P9-01.** If the **schedule sheet itself** is turned 30°, its rows are not read
(`SCHEDULE_HEADER_NOT_READ`). The windows then hold their area and the door takes the labelled Urban default.
Nothing is invented.

## 4. The reference plan

The reference plan carries:

- no door / window schedule;
- no section the reader can bind to a floor: two elevation views carry level texts, but no finished-floor bands;
- no room or floor height notes;
- no opening marks.

So V2.8 finds **0 rooms with a drawing height** and **0 openings with a height from the drawing**.

- In Mode A (the stated project facts file), plaster and paint run to the facts' heights, labelled PROJECT_RULE.
- In Mode U (no facts), they stay blocked.

No reference-plan height was invented. What the owner must supply is listed room by room in
`MISSING_HEIGHT_EVIDENCE.json` and summarised in `DEFECT_AND_EVIDENCE_REGISTER.md` §3.

The elevation reader for opening heights is **not implemented**. The reference plan's elevations show arched
outlines, and windows drawn below the first-floor F.F.L. line make a sill reading ambiguous.
