# Elevator exclusion and quotation-schedule validation (deliverable 9)

Rules UP-DOOR-CLS-005 (elevator entrances are not ordinary doors) and UP-ELEV-SCHED-001 (a separate elevator
quotation schedule); `engine/source/door_standards.py::elevator_schedule`, output `ELEVATOR_SCHEDULE.json`.

## 1. Behaviour

- A lift space on a side, or a lift door block, makes a door ELEVATOR: EXCLUDED from every door view and from the
  door BOQ lines; it appears on the elevator schedule only.
- A band opening into a stacked-footprint shaft (the same doorless footprint on every storey) is a
  LIFT_ENTRANCE_CANDIDATE (V2.2 F-22): neither an ordinary passage nor a confirmed lift door; withheld.
- The schedule has one row per shaft (a stacked footprint, or a LIFT-labelled space): the CAD shaft dimensions and
  area per floor, the landings with their opening widths and status, the floors served, the number of elevators, the
  evidence, what is missing for a quotation (car size and capacity, landing door height and type, pit depth, overrun /
  headroom, machine room, manufacturer data, and - for a candidate - a lift label or schedule) and `in_door_boq: false`.
- The 1.8 x 1.8 m reference shaft is a comparison only (`reference_comparison`), never an assumed size.

## 2. Validation

| Case | Expected | Result | Test |
|---|---|---|---|
| a lift door element | EXCLUDED, in no door view | EXCLUDED 1, AS_DRAWN / OWNER_REQUIRED empty | `test_no_elevator_entrance_reaches_the_door_quantities` |
| a stacked shaft with a 0.80 m access opening (door-guard floor) | CANDIDATE, CAD size 1.6 x 1.6 m, one landing 0.80 m, compared with 1.8 x 1.8 (-0.2, -0.2), not in the door BOQ | as expected | `test_the_elevator_schedule_uses_cad_geometry` |
| the candidate opening is not a door scenario row | not in the door rows | none | `test_no_elevator_entrance_reaches_the_door_quantities` |
| reference plan | one shaft | SHAFT-1: CANDIDATE, 3 floors, 3 landings (1.00 m each), CAD 1.8 x 1.8 m (equal to the reference), 1 elevator, not in the door BOQ; 0 elevator doors in the door views | aggregate run (V2.3 CLI) |
| synthetic villa | no shaft | empty schedule | aggregate run |

## 3. Limitation

A lift opening record names its floor but not its shaft face: it is attached to a LIFT-labelled shaft only when that
shaft is the floor's single lift-labelled space; otherwise the landing would be listed against no shaft. Confirming a
candidate needs a lift label, a lift schedule or an owner decision (a B request: LIFT_IDENTITY).
