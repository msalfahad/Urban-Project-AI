# T-659 Small B10 elements: parapets, boundary pad / wall, blinding, dome, pool, lift (16 HELD lines of trial BOQ r4)

Worker 2, 2026-11-09, run session_01E6cPnbDqT2ThPQWetdgVZG, branch `agents/task-T-659`. Research only (no hub, no master,
no engine module; wiring is T-661). Development villa, not an accuracy claim. ERS s.2 - 5 applied; R-T572-1 .. 4, Q-27 A,
Q-28 A (provisional), Q-65 C, D-14 / D-15 / D-33 / D-35 / D-39 / D-43.

## 0. Sources

- Lines: `research/agents_t655/out/LINE_INDEX_V3_0_61.json` (V3.0.61, sha 10e5f116), trial BOQ r4
  `research/agents_t654/out/TRIAL_BOQ_R4_T654_LINES.csv` (39e55ea3), T-572 bounds (a39e7b4b), T-319 parapet floors.
- Own drawing reads this run (Drive 'Alsenan chalet project', decoded to `.work/private` only): ST7757.pdf p.7 (pool,
  dome), p.14 (lift with isolated footing, typical boundary wall plan + section A-A, the three parapet details);
  ST7757 dxf.dxf texts; P7757.dxf; p7757_arch_sheet03 (GF plan) along the plot boundary. Printed facts are listed in
  `t659_alsenan.py` READS; nothing is scaled from an image.
- Code: `t659_rules.py` (R-T659-1 .. 5), `t659_alsenan.py` -> `out/T659_LEDGER.json`; tests `tests/t659_small_b10`.

## 1. Line by line (m3; before = candidate V3.0.61 line / trial r4; after = this ledger)

| Line | Element | Before | After | Status | Why not valued (item) | Beside the line |
|---|---|---|---|---|---|---|
| L-1d419b64 / L-b5ffc172 / L-9a2c8116 / L-030538dd | parapet RC annex / GF terrace / 1F roof / 2F roof | blank x4 | blank x4 | HELD | Q-65 C material above the upstand; D-39 b_edge; no P1/P2/P3 keyed | AT_LEAST 1.799103 / 1.677887 / 2.949453 / 1.6245 = **8.050943** (DRAWING-CONFIRMED, T-319); + 6.04 / 5.67 / 9.85 / 5.42 m3 per m of b_edge |
| L-cda8f415 | boundary pads | blank | blank | HELD | pad count = boundary columns 'SEE ARCH PLAN': none drawn (own GF read, T-065) | **0.234 m3 per pad net** of the through G.B (0.312 gross) |
| L-6290a9f3 | boundary band | 7.2204 point (V3.0.61); 5.6392 .. 11.0328 (r4 overlay) | **5.6392 .. 11.0328** | HELD bounded | B.W 20x60 (p.10) vs typical 20x40 (p.14); founding level not printed, so the 21.45 m in footings may or may not share their elevation | Q-28 A 8.459 (owner provisional), freelancer 8.604 WITHIN |
| L-080c97f5 | blinding F10 + F | 0.435 .. 0.59 | same | HELD bounded | Q-31 C two footing readings | |
| L-10032bf9 | blinding beyond plot line | 0 .. 0.189 | same | HELD bounded (existence open) | D-14 | |
| L-16b95607 | blinding lift raft FF | 2.256 .. 2.352 | same | HELD bounded | projection not dimensioned; 10 cm now printed on the lift's own detail (p.14) | |
| L-35382b18 | blinding straps | 0 .. 0.912684 | same | HELD bounded (existence open) | D-15 (p.13 prints none under straps) | |
| L-7a5214a3 | blinding ground beams | 4.949374 .. 9.422514 | same | HELD bounded | D-33 / D-35 sections | |
| L-d0313e5d | blinding boundary base | blank | blank | HELD | pad count; between pads not drawn | AT_LEAST 0.117 m3 per pad (1.30 x 0.90 x 0.10) |
| L-d5401fa8 | dome 3 (upper roof) | blank | blank | HELD | Q-27 A: no structural detail; thickness, ring, meaning of '215' not printed | 29.7965 m3 per m of shell thickness (cap 4.41 / 2.15, arch envelope) |
| L-b62a7065 | pool steps | blank | blank | HELD | not drawn on ST p.7 (own read) nor dimensioned: consultant item | |
| L-5ae06fda | lift tie beam | blank | blank | HELD | D-43 section | 5.500 m3 per m2 of section (length 5.500 DC, T-419) |
| L-684fcad3 | lift pit walls | blank | blank | HELD | D-43 pit depth 'as per lift manufacturer' | AT_LEAST 1.903 (FLAGGED NOTE1_ON_LIFT_RAFT); 1.10 m3 per m height |

Totals of the 16 lines (m3): valued 0; bounded 6 lines carry **13.279574 .. 24.498998** (unchanged vs trial r4; vs the
V3.0.61 line index the band moves from the point 7.2204 to 5.6392 .. 11.0328); 10 blank, none summed; AT_LEAST floors
beside 9.953943 (8.050943 confirmed + 1.903 flagged). No family total is stateable (R-T659-5). **No line can be valued
from the issued drawings: every remaining factor is a designer item already on the lists; no new owner question
(ERS s.2.7 not met).**

## 2. Findings

- **F-T659-1 (pad ownership, ENGINE_WRONG in the coefficient, not in any line quantity):** ST p.14 section A-A draws the
  lower G.B 0.20 x 0.40 on the pad soffit inside the 0.80 base, so the band (which carries 0.20 x 0.40 through) and a
  gross pad 1.30 x 0.80 x 0.30 share 0.20 x 1.30 x 0.30 = **0.078 m3 per pad**. Pad coefficient net 0.234, not 0.312
  (T-400). Rule R-T659-3.
- **F-T659-2:** the V3.0.61 band line still carries one reading (7.2204) as a closed range; the drawn bound is 5.6392 ..
  11.0328 (trial r4 overlay F-T628-1). T-661 wires the bound; Q-28 A 8.459 stays beside.
- **MISSING (named, never 0): pool blinding.** ST p.7 prints '10cm PLAIN CONCRETE' under the pool base and slope; no line
  of V3.0.61 carries it (T-347 'pool blinding x2 MISSING'; T-183 B >= 1.222 m3). Needs a lane S row.
- Lift raft FF blinding: the 10 cm is printed on the lift detail itself (p.14), not only the general p.13 note.

## 3. Engine vs freelancer (m3)

| Element | Engine | Freelancer | Class / verdict proposal |
|---|---|---|---|
| boundary band | HELD 5.6392 .. 11.0328 | 8.604 (71.7 m x 0.20 x 0.60) | WITHIN; UNRESOLVED (section + elevation RFI); his 71.7 m vs drawn 70.49 net / 91.94 gross |
| parapet RC | HELD, >= 8.050943 | no row | ENGINE_RIGHT scope (>= 0.30 RC in every printed alternative), quantity UNRESOLVED |
| lift pit walls | HELD, >= 1.903 flagged | 1.650 | BELOW_DRAWN_LOWER if note 1 applies to the raft |
| dome 3 | HELD blank | 2.26 (22.6 m2 x 0.10, borrowed 1F detail) | RULE_DIFFERENCE: thickness borrowed from another dome's detail (refused, Q-18 / Q-27) |
| blinding | 7.640374 .. 13.466198 held + 12.734438 released | one plate 47.055 | NOT_LIKE_FOR_LIKE (T-478) |
| pads, pool steps, tie beam | HELD blank | none identified | not compared |

## 4. Rules, tests, lessons row

R-T659-1 .. 5 in `t659_rules.py`. `tests/t659_small_b10` (hand villa V659: pads 1.20 x 0.70 x 0.30 with a 0.20 x 0.40
beam through -> net 0.180, 8 printed pads -> 1.440 VALUED; band 4.0 .. 6.0 from two sections with 5.0 beside; dome cap
6.00 / 1.00 -> 31.415927 m2; rotation / order; adverse: 'AS PER ARCH' / 'SEE ARCH PLAN' / manufacturer / default /
freelancer sources, mm, 0, %, blank with a figure, blank without item, 0 low without existence open, coefficient x an
unprinted count, provisional reading as the bound, floor on a bounded line, beam wider than pad, a line twice; Alsenan
rebuild = committed, 16 lines once, key figures, an edited input stops the build).

Lessons row (ERS s.7, PROPOSED): | 2026-11-09 | a pad coefficient (0.312 m3) was stated gross of the ground beam that the
typical section runs through the pad on the same soffit | the plan's N.I.S. rectangle was read without the section | a
member crossing another on a shared soffit keeps its full section and the other owns its solid net of the shared prism
(every villa; R-T659-3) | tests/t659_small_b10 test_hand_pad_net_of_through_beam | PROPOSED |

## 5. For the Checker

Re-measure: the band 0.20 x 0.40 x 70.49 = 5.6392 and 0.20 x 0.60 x 91.94 = 11.0328 (plot 31.37 x 15.00 printed);
one parapet floor (2F 5.415 x 0.30 = 1.6245); the pool detail p.7 (no step drawn, 10 cm plain concrete printed); the
A-A pad / G.B soffit reading behind F-T659-1.
