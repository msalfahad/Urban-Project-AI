# T-105: rebar-firewall declarations for concrete ledger V3 (T-097) and stair concrete V1 (T-056)

Worker 1, 2026-10-20. Branch `agents/task-T-105` = working head ecc09a3 + merge of `agents/task-T-097` (8691838) + merge
of `agents/task-T-056` (3b8c549); docs maps rebuilt with `tools/codemap.py build`. Neither module is wired into a
released method; no quantity of a released method changes.

## The rejection cause and the fix

Both pieces were rejected (verifier run 35) for one new L4 failure:
`tests/structural_comparison_engine/test_rebar_product_firewall.py::test_every_rebar_module_in_engine_is_declared`
(each module's text contains 'reinforc', and it was not declared). Reproduced on this branch before the fix:
`AssertionError: ['engine/source/concrete_ledger_v3.py', 'engine/source/stair_steps_concrete.py']`.

Decision FROM THE CODE (the Lead's rule: declare only a module that names reinforcement without computing or reading
steel):

| Module | Where the word occurs | Computes / reads steel? | Declared |
|---|---|---|---|
| `engine/source/concrete_ledger_v3.py` | docstring line 18 only ("reinforcement items stay the route's") | No. `measure` keeps only CONCRETE items of the beam families from its `items_from` rebuild (lines 446-459); neck lines filter `trade == "CONCRETE"` (line 388); `apply` passes every other route item through untouched. Checked by `check_ledger_v3_steel_passthrough.py` on the T-097 synthetic villas (seed 3 mm, seed 7 m, seed 3 mirrored): route reinforcement items 157 / 81 / 157 -> after V3 157 / 81 / 157, byte-identical; V3 emits 0 non-concrete items and supersedes 0 reinforcement items. | OTHER_REBAR_AWARE |
| `engine/source/stair_steps_concrete.py` | docstring line 2 and `LATER_ITEMS` (line 66) | No. REINFORCEMENT is written only as an `UNSUPPORTED_LATER_ITEM` line with no quantity (lines 381-383, owner Q-20). | OTHER_REBAR_AWARE |

Change: `tests/structural_comparison_engine/rebar_product_registry.py`, two entries with a one-line reason each, at the
end of `OTHER_REBAR_AWARE`. The test file is not edited; no word was removed from either module.

## Depth: three acceptance cases of each original row re-worked by hand

Hand truth is written in each script's docstring before the run, from the design / census numbers only.

`hand_recheck_t097.py` (synthetic villas, NOT a client drawing; seed 3 mm, seed 7 m, seed 3 mirrored):

| Case | Hand | Engine |
|---|---|---|
| Beam split by a planted column, seed 3: B1 0.20 x 0.50, clear 13.50 - 0.10 - (8.75 + 0.15) = 4.50 m | 0.450 m3 | 0.450 (one span) |
| same, seed 7: B5 0.25 x 0.50, clear 12.95 - 0.15 - (7.60 + 0.25) = 4.95 m | 0.61875 m3 | 0.61875 |
| Ring (arc band) with printed mark: pi (1.20^2 - 1.00^2) x 0.50 | 0.691150 m3 | 0.691146 (binder polygon, -4e-6 m3) |
| Printed upstand 0.10 x 0.15, seed 3 span 4.60 - 0.10 - 0.15 = 4.35 m | 0.06525 m3 | 0.06525 |
| same, seed 7 span 4.25 - 0.125 - 0.15 = 3.975 m | 0.059625 m3 | 0.059625 |
| Unmarked ring, no owner rule | HELD, annulus 1.382301 m2 listed | HELD, no number |

Mirrored seed 3 gives the same numbers.

`hand_recheck_t056.py` (three NEW stairs, not the T-056 test censuses):

| Case | Hand | Engine |
|---|---|---|
| Dog-leg, levels 0 / 2975 mm, 17 risers on the section -> riser 0.175: steps 17 x 1/2 x 0.175 x 0.30 x 1.20 | 0.5355 m3 | 0.5355 |
| waists F1 0.192 x hypot(2.40, 1.575) + F2 0.192 x hypot(2.10, 1.40) | 0.551165 + 0.484586 | 1.035751 |
| landing 1.20 x 1.30 x 0.16 | 0.2496 | 0.2496; total 1.820851 = hand; same in metres |
| F1 arrival wedge in the T16 landing (riser 0.175 > plate 0.16), check only | 0.031269 m3 | 0.031269, not deducted |
| Winder corner 3 risers, 1.44 m2 drawn, riser 3.20 / 20 | HELD (Q-51); candidate 1/2 x 0.16 x 1.44 = 0.1152 shown | HELD, 0.1152 shown, not in the total |
| Top level not printed | flight steps / waist HELD RISER_HEIGHT_NOT_ESTABLISHED; landing 0.2496 stays | same |

## Development villa, against the RELEASED route G run (structural DXF from Drive, sha256 9f9d1179...8079)

`research/agents_t097/run_v3.py ST.dxf OUT.json --ring-rule "BEAM:B4:1F:owner Q-44 A"` on this branch reproduces the
T-097 handoff exactly. Per concrete key, m3 (released sum / released lines / held lines), freelancer reference:

| Key | Released route G | Ledger V3 | Freelancer | Note |
|---|---|---|---|---|
| CONC.BEAM | 64.820 / 112 / 24 | 68.837 / 116 / 18 | 65.966 | -1.7 % -> +4.4 %, key still HELD (18 held spans), not compared |
| CONC.FOOTING | 77.265 / 30 / 0 | 70.045 / 29 / 2 | 77.631 | ledger V2 holds the footing band (-7.22, owner Q-12) |
| CONC.POOL | 3.495 / 2 / 0 | 0 / 0 / 2 | 12.348 | ledger V2 holds pool walls / floor (Q-19 / Q-26); HELD, not 0 |
| CONC.COLUMN | 0 / 0 / 118 | 0 / 0 / 113 | 39.752 | 5 CN columns NOT_PRESENT (listed) |
| CONC.GROUND | 17.127 / 23 / 61 | same | 75.090 | unchanged |
| CONC.SLAB | 61.551 / 75 / 1 | same | 59.817 | unchanged |
| CONC.STAIR_DOME | 12.007 / 5 / 0 | same | 21.833 | unchanged (stair piece not wired) |
| CONC.BLINDING | 0 / 0 / 1 | same | 47.055 | unchanged |

Lines 949 -> 943 (930 unchanged, 2 changed, 17 removed, 11 added); all four plan sheets replayed identically; side
effects 0.

Stairs (`research/agents_t056/alsenan_stair_census.py`, reproduced): main stair 5.011 m3 (steps 1.386, waists 2.885,
landings 0.740; GF->1F winders, 1F->2F turn riser and two stair beams HELD) vs freelancer 8.131 (-38.4 %); entrance 0.357
(waist HELD) vs 1.411 (-74.7 %); lobby flight 0.126 (freelancer no row); round stair all HELD vs 5.510; 15 held lines.
These stay CALCULATED: owner Q-62 A is conditional on T-111's intersection ledger (main 4.951 after the 0.060 m3
arrival overlap is not applied here); Q-50 / Q-51 answers are conditional too, so the module's holds stay.

## Not done / open

- Beam reinforcement items stay the route's V1 pieces (BAND0047.1 / .2, BAND0048.1 / .2): a rebar follow-up must
  rebuild them from the V2 records, as the ledger's docstring says.
- Wiring either piece is lane I's (V3.0 extension), not this task.
