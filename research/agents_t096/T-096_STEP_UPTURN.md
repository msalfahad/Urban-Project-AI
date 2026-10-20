# T-096 Membrane strips that missed the upturn at an outline step: fixed as ARCH_TAKEOFF_V2.12

Worker 3, 2026-10-20. Development villa (Alsenan) figures come from the engine run on the Drive DXF
("Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, P7757.dxf sha256 ab54dd55...; the file T-094 measured by hand),
with `research/agents_t096/alsenan_v212_run.py`. Only dimensions, counts and engine room ids are given here.
Not an accuracy claim: Alsenan is the development villa.

## The defect (T-094 hand plans, confirmed from the code)

MEMBRANE_FOLD_V2 `strips()` lays a strip only where a band's floor interval [s0 + lap, s1] holds floor, and an
upturn-only strip only at the far wall of the whole outline. At an outline STEP whose edge runs parallel to the strips,
the 0.20 m upturn of that edge can fall in the next band, where that part of the outline has no floor: nothing covers it.
V2 measured the gap (UPTURN_SHORTFALL) but ARCH_TAKEOFF_V2.11 counted the rolls without it. Any villa with a step edge
parallel to the strips can hit it (a geometric condition, either strip direction, either start wall).

## The fix (new versions; V2 fold, cutting plan V1 and ARCH_TAKEOFF_V2.11 untouched)

- `engine/source/membrane_fold_v3.py` (MEMBRANE_FOLD_V3): per layout, the V2 strips; the surface to cover = the outline
  widened 0.20 m with mitred corners (floor + upturn incl. the corner squares, Q-24 / UP-WP-003 - the T-094 hand method)
  less the openings, plus each opening's own 0.20 m flap; the residual is taken band by band (each band owns the slab its
  strip adds); a rectangular residual piece becomes an UPTURN-ONLY strip of its band (band width; length = the piece, plus
  the 0.10 m end lap where it meets another sheet of the band; need width = residual height + 0.10 m lap per joined side);
  every other residual (slanted / curved corner, opening ring) is a listed PATCH (m2, size along / across, position in the
  room frame and in drawing units). Residual after strips and patches is checked to be 0 (a code fault otherwise).
  Numerical limit: the existing MEMBRANE_FOLD_V2 limits only (1 cm2, 0.5 mm), named, no new tolerance.
- Roll counts per layout under the three readings of owner Q-58 (open): A = main strips from rolls, extra pieces and
  patches from this area's own leftover / side trim when one is big enough (no turning), else from a roll; B = every
  piece and patch from a roll; C = strips from rolls, patches by detail.
- `engine/source/membrane_cutting_plan_v2.py`: Q-49 A selection per reading (fewest rolls, tie shorter metres, then cut
  m2, then order). Same fewest count under A, B and C -> RELEASED with the layout reaching it under B (buyable without
  reusing an offcut); otherwise HELD_Q58 with low / high and both cutting plans. Each plan is re-packed and must give the
  fold's count.
- `engine/source/arch_v212.py` + `tools/urban_boq_m9.py`: ARCH_TAKEOFF_V2.12 = V2.11 with the V3 rows; a Q-58-dependent
  rolls line is BOUNDED_EXPOSURE (low / high, the readings named, RFI Q-58), never 0; files MEMBRANE_TABLE_V2_12.json /
  MEMBRANE_PURCHASE_V2_12.csv. Registry stays 1.7.0 (no rule record needed: Q-58 is open).

## Alsenan, engine V2.12 vs V2.11 vs hand (T-094) vs freelancer

| Area | V2.11 released | V2.12 | Hand T-094 | Note |
|---|---|---|---|---|
| 2F roof | 17 rolls, 158.09 m, 0.84 m2 uncovered | HELD 17 (Q-58 A) / 18 (B) / 18 (C); 162.69 m incl. the 4.60 m upturn-only strip (need 0.30 x 4.60, from the 0.70 x 6.97 side trim under A); residual 0 | 18 (strict), 17 if the piece may come from the side trim | the 4.60 m strip = hand exactly (4.20 + 2 x 0.20); residual before 0.92 m2 = 4.60 x 0.20 with the corner squares (V2 counted 0.84 without them) |
| 1F west roof | 8 | 8 (A = B = C) | 8 | curved-corner residual now a listed patch 0.011 m2 (hand extended the last strip 3.93 vs 3.76 m instead) |
| 1F south-east roof | 6 | 6 | 6 | identical |
| Roofs drawn, total | 31 | 14 released + 2F held 17-18 = 31 - 32 | 32 strict | the 2F top roof stays HELD (Q-34) |
| 17 wet areas | 19 rolls, 122.99 m | 19 rolls, 123.04 m | 19 (T-089 / T-074) | no count changes; two areas change layout at the same count: 1F laundry (across, other start wall, same 15.93 m) and one 1F bathroom (6.55 -> 6.60 m: V2.11's layout left 0.0025 m2 of a 0.15 m step upturn uncovered; under V3 it needs a 0.15 m upturn-only strip, so the clean layout wins the tie) |

- 2F roof openings: the 0.20 m ring round the two openings is 5.31 m2 laid flat (27.78 lm x 0.20 = 5.56 m2 measured on
  the opening face); the strips fold 5.24 m2 of it, 8 patches 0.063 m2 remain (listed with size and position). The
  0.31 m2 in V2 / Q-58 is 0.063 m2 uncovered + 0.25 m2 that is only the difference between lm x 0.20 and the flat ring
  (2 x pi x 0.20^2): not material. Under Q-58 A all 8 patches fit the roof's own leftovers; under B they are cut from
  the rolls without adding a roll.
- Leftover metres in V2.12 subtract the patch pieces cut from the rolls (reading B): wet areas 65.23 m (V2.11 67.01).
- BOQ lines: of 578 V2.12 lines exactly one differs from V2.11: FIN.WP.MEMBRANE_ROLLS of the 2F roof, 17 released ->
  bounded 17 - 18 (Q-58). No line added or lost; release report every line once.
- Freelancer: one roof line 285.00 m2 / 194.00 lm, no roll count: rolls not comparable. Roof membrane 204.11 vs
  285.00 m2 (-28.4 %), unchanged (2F top roof held, Q-34).

Verdict proposals for the verifier: 2F roof rolls ENGINE_RIGHT now that it is held 17 / 18 (hand: 6 x 10.00 + 2 x 9.37 +
8 x 6.97 + 3 x 4.60 needs >= 18 strict, 17 only with the side-trim piece, which is owner Q-58); 1F roofs and wet areas
unchanged (ENGINE = hand).

## Synthetic acceptance (tests/t096_step_upturn, none is Alsenan)

12.00 x 4.60 roof with a 4.00 x 2.10 notch: 0.40 m2 uncovered before, one 4.10 m upturn-only strip, 7 / 8 / 8 rolls in
that layout, released at 7 by a layout with no step; in mm, mirrored, turned 90 / 30 degrees and moved: same. 9.00 x 4.60
with a 2.00 x 2.00 notch: HELD 5 / 6 / 6 (bounded line 5 - 6, never 0). Plain 12 x 5 and the owner's 3 x 4 kitchen: V2
strips and counts exactly (kitchen 2 rolls, 2.40 m left). A round opening crossing bands and a 45 degree wall: listed
patches only. V2.11 vs V2.12 on the T-079 drawn roof (plain and turned / mirrored / mm): every BOQ line identical.
Note: the exact-boundary version of the notch (step exactly on a band edge) is decided in V2 by a sub-micron floor
sliver after rotation (V2 then lays one over-long strip); the fixture keeps the step 0.10 m inside the band.

## Missing / for the Lead

- Owner Q-58 decides the 2F roof (17 or 18) and roofs 31 or 32; nothing else on Alsenan depends on it.
- The 12.00 x 5.00 with a 4.00 x 2.00 step named in the task: along the long wall its step upturn stays inside a band
  (0 m2 uncovered); only across, from the opposite wall, 0.20 m2 is uncovered (one 2.00 m upturn-only strip, 14 rolls
  unchanged). The notch fixtures above reach the defect in the chosen direction; the Lead's 0.80 m2 needs the step
  exactly on a band edge.
