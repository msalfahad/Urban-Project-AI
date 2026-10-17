# Window and opening schedule method (UP-OPEN-SCHED-001)

Output: `OPENING_SCHEDULE.json` / `.csv`, one record per door / window band opening. The columns:

- floor, opening id, kind, class, mark;
- plan width and schedule width;
- height and its source, sill and its source, head;
- area and area state, findings.

## 1. Reading

1. **Schedule sheets.**
   - A sheet whose title matches a schedule (DOOR / WINDOW / OPENING SCHEDULE, SCHEDULE OF …).
   - Its header row names MARK / WIDTH / HEIGHT / SILL. A unit in the header (`(mm)`) converts every value; without
     one, the unit is inferred per value (see the heights proof).
   - Rows are grouped by y, columns by the nearest header x.
   - A mark that repeats with different values is `SCHEDULE_MARK_REPEATED` and is not used.
2. **Marks** (`D1`, `W-01`, `SD 3` …) are normalised (W-01 = W1).
   - A mark binds to the nearest opening of its kind within 1.20 m, and is ambiguous if a second opening lies within
     0.10 m of the same distance.
   - A mark that names no schedule row is `MARK_NOT_IN_A_SCHEDULE`.
   - Two different marks on one opening is `TWO_MARKS_ON_ONE_OPENING`.
3. **Element annotations** next to an opening govern its schedule row: `SILL 0.90`, `H=2.20`, `1.50x1.20`.
4. **Notes.**
   - Floor notes such as `ALL WINDOW SILLS 1.00 M` give a floor-scope sill or height (rank 4).
   - Project facts give rank 5.
   - The Urban door default gives rank 6 and is always ASSUMED.

## 2. Checks before a value is used

- **Width.** The schedule width must agree with the plan width within 0.03 m.
  - For a **window**, a row of another width (`SCHEDULE_WIDTH_DIFFERS`) gives **neither its height nor its sill**:
    the mark may be wrong. An annotation on the window, or a note, can still govern.
  - For a **door** the difference is recorded but the height is kept, because a schedule often lists the leaf and
    the plan the structural opening.
- **Head.** Head = sill + height, only when both are established.

## 3. Class and its effect on each trade

| Class | Condition | Wall finish (each trade's band [0, H]) | Skirting | Reveal strip |
|---|---|---|---|---|
| DOOR | a door | deduct w × min(h, H) | not skirted | door jambs line (V2.3) |
| WINDOW | sill > 0.02 m established | deduct w × (min(head, H) − max(sill, 0)) | skirted under the sill | jambs 2 × d × band + head d × w if wall remains above; the internal sill surface d × w |
| FLOOR_GLAZING | sill ≤ 0.02 m | as above (the band starts at 0) | **not skirted** | jambs only up to the plaster height; the strip is **floor** (the room's floor finish) |
| WINDOW_SILL_NOT_ESTABLISHED | no sill | a **range** (full band to nothing) where the height is unknown; if only the height is known, full height in the band (`WINDOW_POSITION_ASSUMED`) | **a range** (certain part excludes it) | not measured (BLOCKED_RFI) |
| height not established | — | the deduction is a range | — | the window's **width released, area held** |

**Rule.** A window in a plan without a height is not evidence for its area. ARCH.WINDOW still counts the window
(1 no., width) and holds its area.

- The deduction depth `d` is the measured strip between the room face and the glazing (strip area / width), never a
  fixed reveal depth.
- **Curtain walls and aluminium-door / window distinctions** follow the existing door model: external doors are
  aluminium (UP-DOOR-CLS-002), lift doors go in the elevator schedule (UP-DOOR-CLS-005, UP-ELEV-SCHED-001). V2.8 adds the schedule height to the door
  BOQ line.
- A curtain wall without a schedule row is treated like any window without a height: width released, area held.

## 4. Proof

See `WALL_OPENING_REVEAL_PROOFS.md` §G and `test_p2b9_openings.py`:

- the sill window;
- floor glazing;
- a window head above the ceiling;
- an unknown sill;
- no height;
- a schedule row with the wrong width.

## 5. Not supported yet

- A turned schedule sheet (L-P9-01).
- A schedule drawn as a table block with merged cells.
- Elevation-derived window heights (the reference plan's elevations are ambiguous).
- An interior vs exterior side read from the glazing alone.
- Curved glazing without a wall gap, which loses its room (D-P9-01).
