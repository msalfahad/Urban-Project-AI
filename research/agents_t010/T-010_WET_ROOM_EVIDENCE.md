# T-010: wet, dry or held, from the room label first and the sanitary drawing second

Worker 1, 2026-10-19. New method piece `engine/source/wet_room_evidence.py` (WET_ROOM_EVIDENCE_V1), **not wired**:
no ARCH_TAKEOFF method, no frozen builder and no existing rule or knowledge file changed; no released quantity
changed. Development villa: not an accuracy claim.

## Rules applied (and nothing else)

| Source | What it decides here |
|---|---|
| Owner Q-13 = B (2026-10-19), label primary | the architectural label says what a room is; a toilet-like object in a dry-labelled room does not make it wet; loose lines are a toilet only on a plumbing / sanitary layer or with a drain or soil-pipe mark; no label + ambiguous evidence = HELD (no wet and no dry quantity); a labelled wet room missing a fixture in one drawing = COORDINATION_CHECK, class kept |
| Owner Q-06 = (a) (2026-10-18) | a basin-only hand-wash space is wet (porcelain floor, full-height wall porcelain, waterproofing, marble threshold); this supersedes, for such a space, the 'basin alone = REVIEW' reading of UP-WET-002 1.3.0 |
| UP-WET-001 | wet codes (bathroom, kitchen, pantry, ironing, laundry; laundry flagged for project confirmation) and the wet scope |
| UP-WET-002 1.3.0 | fixture-block vocabulary and the WC linework profile, used only as a CANDIDATE detector |
| UP-WP-001 / -002 / -003, UP-FIN-WALL-001, UP-CER-009 | the item formulas of the ARCH_TAKEOFF line items: floor face; one-sided boundary incl. doorways x 0.20 m; door width x wall thickness; wall run x full (clear) height - openings |
| UP-QTY-STATUS-001 | every item MEASURED or HELD with its reason; a missing input is never 0 |

Labels are read with ROOM_VOCAB_V2 (compounds first: 'حمام سباحة' is a pool, 'مغسلة سيارات' a held car wash), then
the hand-wash words ('مغسلة', 'مغاسل', 'HAND WASH', 'WASH BASIN', 'WASH AREA', 'WASH'), then room-tag block names
when no text types the space. A hand-wash word inside a space that another room word types and that holds no basin in
either drawing is read as the neighbour's label drawn across the wall (coordination check), never as a wet zone.

## Synthetic proof (not Alsenan): `tests/t010_wet_room_evidence/` (81 cases)

One 2.60 x 2.20 m room, layer names unlike any project (WALLS-150, M-FURNITURE, P-SANIT, ROOM-NAMES), each geometric
case drawn untransformed, rotated 37 degrees, mirrored, in metres, and all three at once, read back through the
architectural route's own reader composition. Hand truth:

| Case | Expected | Result |
|---|---|---|
| L-P8-01 chair (seat 0.40 x 0.55 on a 0.45 x 0.15 back at the wall) + basin, labelled LOBBY / موزع | DRY + coordination check | pass |
| same chair, no label, no basin (the strict xfail's case) | HELD | pass (old xfail test untouched) |
| exploded WC on the furniture layer, no label | HELD, no quantity | pass |
| same on the sanitary layer | WET | pass |
| same on the furniture layer + drain block / 'F.D' text / sanitary-drawing drain | WET | pass |
| labelled bathroom (BATH / حمام / W.C.), fixtures only on the sanitary drawing | WET, no check | pass |
| labelled bathroom, nothing in either drawing (or sanitary sheet not read) | WET + COORDINATION_CHECK | pass |
| bedroom with a WC on the sanitary drawing | DRY + coordination check | pass |
| basin only, unlabelled / مغسلة / HAND WASH / المغاسل | WET; floor 5.72, upturn 1.92, doorway 0.12, membrane 7.76, wall porcelain 26.56 m2 | pass (all transforms) |
| basin + cooker, no label; drain alone; nothing | HELD | pass |
| حمام سباحة / SWIMMING POOL; مغسلة سيارات; BATH + DRESSING | NONE; HELD; HELD | pass |
| clear height, door depth or opening height missing | that item HELD (m2 None), never 0 | pass |

## Alsenan read-only run (P7757 DXF, ARCH_TAKEOFF_V2.9 on 97c4bfc; sanitary-7757.pdf read visually)

`research/agents_t010/alsenan_wet_run.py` + `sanitary_reading.json` (kinds per engine room id). 37 spaces: WET 17,
DRY 9, NONE 6 (stair, shaft, garden), HELD 5 (the open-plan pantry zone and its zone group, three unlabelled
spaces with no fixture in either drawing: 3.60, 1.56, 2.97 m2). Only three spaces change class against V2.9, all
from REVIEW to WET under Q-06 (basins on the plan, basins + a 3" floor drain on the drainage plan):

| Space (GF) | V2.9 | Now | Floor m2 | Boundary lm | Membrane m2 (floor + upturn + doorways) | Freelancer (floor / boundary) | Verdict proposal |
|---|---|---|---|---|---|---|---|
| hand-wash space by the master suite | REVIEW | WET (hand-wash label) | 4.73 | 9.50 | 6.87 | 4.73 / 9.50 | agrees (0.0 %) |
| hand-wash space by the majlis | REVIEW | WET (basin only) | 3.13 | 7.20 | 4.57 | 3.15 / 7.20 | RULE_DIFFERENCE: engine deducts a 0.0175 m2 column corner (1.50 x 2.10 = 3.15 less the notch) |
| hand-wash space by the stair | REVIEW | WET (basin only) | 1.49 | 4.90 | 2.47 | 1.70 / 5.30 | RULE_DIFFERENCE: engine 1.35 x 1.10 = 1.485 (printed 110); freelancer 1.55 x 1.10 = 1.705 takes the 0.20 m passage reveal into the room; the strip is a threshold item (UP-THR-001) |

Wet-area waterproofing, whole villa, engine (wet spaces of this method) vs freelancer ('عازل ارضيات حمامات' 72.01
m2, 'نعلات العازل' 144.61 lm):
- floor: **72.12 m2 vs 72.01 m2, +0.11 m2 (+0.2 %)**; V2.9 had 62.77 m2 (-9.24 m2, -12.8 %).
- boundary (upturn run): **144.73 lm vs 144.61 lm, +0.12 lm (+0.1 %)**; V2.9 123.13 lm (-14.9 %). The engine's upturn
  item is that run x 0.20 m = 28.95 m2; the freelancer lists the run in lm only.
- membrane items (floor + upturn + doorway pieces): 102.77 m2 (no freelancer equivalent).
- wall porcelain: HELD (full height = clear height, not established in this run: no heights facts; Q-14 heights
  work). Wall run 144.73 lm vs the freelancer's 144.61 lm; the freelancer takes 3.00 m and no opening deduction
  (433.83 m2), a height no Urban rule fixes, so no engine m2 is given.

No labelled wet room lacks sanitary evidence on the drainage plans (0 coordination checks); one coordination check:
the majlis holds the 'Wash' label of its neighbour (read as a stray label; the majlis stays DRY).

## What is missing

- Not wired: a new ARCH_TAKEOFF version must call `classify` in the room builder and pass the sanitary reading; the
  scoreboard changes only then (the figures above are this run's, not a released line).
- The sanitary drawing is read by a person here (PDF); a reader that maps drainage-plan symbols to room faces is a
  gate-4 item.
- 47 Arabic SHX labels in x-arab fonts stay unread (T-004a); the hand-wash spaces here were typed by their basins and
  one English 'Wash'.
