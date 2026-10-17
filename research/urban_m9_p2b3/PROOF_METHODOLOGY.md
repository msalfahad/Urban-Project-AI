# Proof methodology (deliverable 1)

"Every engineering measurement rule must be proven using an independently calculated, human-readable example before
it is accepted into the production quantity engine." This phase builds that proof library and the method it follows.

## 1. Three independent sources, one comparison

| Source | Where | What it may use | What it may not use |
|---|---|---|---|
| **Hand calculation** - the expected answer | `tests/m9_p2b3/proof_cases*.py`, the `hand` steps and the `expected` literals of each case | the scenario's coordinates, the approved owner rules (registry 1.1.0), stated assumptions | the engine, any engine output, any value computed in code |
| **Independent reference calculator** - an arithmetic cross-check of the hand calculation | `tests/m9_p2b3/proof_reference.py` | the Python standard library only; its own geometry, whole millimetres, exhaustive search | anything in `engine/` or `tools/` (an AST test refuses the import) |
| **Engine** - what is being proven | `engine/source/...` through `tests/m9_p2b3/proof_engine.py` (the only file of the library that imports the engine) | - | the expected values never pass through it |

The comparison (`proof_engine.compare`) gives for every expected quantity: the expected value, the engine value, the
difference, the tolerance (0.001 m and 0.001 m2; counts and states exact) and PASS / FAIL.
`proof_check.hand_vs_reference` gives AGREE / DISAGREE between the hand value and the reference value.

Rules kept throughout (tested):

- an expected value is a literal typed from the hand calculation: `test_every_expected_value_is_a_typed_literal`
  parses the case files and refuses any call, name or arithmetic in an `expected` block;
- the reference calculator and the case files never import the engine:
  `test_the_reference_and_the_cases_never_import_the_engine`;
- a failing comparison is diagnosed. Either the engine is fixed (V2.5 only) or the hand calculation is re-derived by
  hand. An expected value is never changed to match the engine without a new derivation written into the case:
  WP-CX, DR-09 and DR-10 record such re-derivations (DEFECT_REGISTER.md section 2);
- simplest first: `test_the_cases_pass_in_sequence_simplest_first` compares the cases in their sequence and stops at
  the first failure;
- every approved rule the library proves has a positive example, and a boundary and a conflict / exception example
  where the rule admits one: `test_every_proven_rule_has_positive_boundary_and_conflict_examples` (the rules without
  one are listed with the reason);
- the ten parts of a proof are present in every case: `test_every_case_carries_the_ten_parts_of_a_proof`.

## 2. The ten parts of a proof case

(1) a simple dimensioned scenario (`scenario` / `plan`); (2) the applicable Urban rules (`proves`, `URBAN_RULES`,
`DOOR_RULES`); (3) project overrides (`overrides` / project rules); (4) the independent hand calculation (`hand`); (5)
the expected quantities (`expected`); (6) the engine quantities, (7) the difference and tolerance and (8) PASS / FAIL
- produced at test and report time (`CALCULATION_SHEETS.md`, `EXPECTED_VS_ACTUAL.md`); (9) the coordinate explanation
(`coordinates`) and the diagrams (`diagrams/`); (10) the exclusions and why (`exclusions`).

## 3. The reference calculator - its formulas

All lengths are whole millimetres (the engine uses metres with tolerances, so a rounding slip on either side shows).

| Step | Formula / rule |
|---|---|
| Strip count across a cross width D | count strips one at a time: n = 1, reach = W; while reach < D: n += 1, reach += W - s. The last strip is D - (n - 1)(W - s) wide (W roll width, s side lap) |
| Strip positions | strip i covers [y0 + i(W - s), y0 + i(W - s) + w_i] from the area's lowest edge |
| Strip pieces of a rectilinear area | the area is cut into horizontal slabs between vertex levels; the inside x-intervals of each slab come from the even-odd rule on the slab's mid level. A strip's piece covers the union of the intervals of the slabs it overlaps; one piece per connected stretch |
| Area under a piece (laid) | sum over the slabs it overlaps of (overlap height) x (inside length within the piece). What lies outside the area is cut off at the wall (cutting waste) |
| Splice | a piece longer than the roll: L_roll, then min(L_roll, rest + e) until the length is covered; each splice laps e (end lap) over the piece before |
| Side laps | the area covered twice: for each strip after the first, the band [its start, its start + s] intersected with the area |
| Band width, lanes | b = h + s (upturn height + lap onto the floor); a full-width segment gives floor(W / b) lanes; the rest is residue |
| Offcut lanes | the trim W - w_last of each last-strip piece gives floor(trim / b) lanes of that piece's length; the rest is scrap |
| Doorway piece | w x (t + s); taken from the shortest lane at least w long (the remainder goes back to the pool), else a new w-long segment (its other lanes join the pool) |
| Patch of a detail | a x b (a <= b): from a lane when a <= band width, else side by side across a full-width b-long segment (floor(W / a) patches; the rest cut into lanes) |
| Band covering | runs in order; a piece after the first of an open run, and every piece of a closed loop, laps e onto the piece before it; lane choice: the shortest lane that finishes the run, else the longest that covers something past its lap |
| New band segment | the offcut lanes first; then the smallest multiple of 10 mm, searched upward from (remaining need / lanes), whose lanes finish every remaining run - **a search, not a formula** |
| A split band (a case's hand calculation that sizes segments to roll remainders) | the listed segments, checked to cover the band |
| Laps by kind | floor side laps; floor end laps (splices x e x strip width); band to floor (eligible length x s); band joints (joints x b x e); doorway (door width x s) |
| B installed | A + upturn (eligible x h) + doorway continuation (w x t) + laps + patches; asserted equal to the laid area (floor + doorway pieces + band pieces x b + patches) |
| Consumed | sum of the cut lengths x W; asserted equal to laid + scrap |
| Rolls | the fewest rolls the cut lengths fit into: exhaustive branch and bound, not first fit |
| Doors (`door`) | CAD = s1 - s0; required opening = nominal (owner table) + 0.10; enlargement = max(0, required - CAD); the door that fits = CAD - 0.10; plain wall beyond each jamb to the nearest junction / column (reach 3.00 m inclusive); available = plain - 0.10 pier (0 at a column, never cut); placement SPLIT_EQUAL / START_SIDE / END_SIDE / UNEQUAL; swing CONFLICT when the required leaf exceeds the depth beyond; structure from a project rule, else MASONRY_INDICATED when a column frame is drawn; jamb plaster 2 t H + t w; area w H (ASSUMED height) |

Shared rules with the engine, stated openly: the lane choice and the band lap convention are the construction method
of the hand calculations (written into each sheet), not taken from the engine. The reference implements them
independently in integer millimetres and finds the minimum segment by search. The engine uses its own `_take_lane` and
its own minimum-segment search in metres. Agreement therefore proves the engine follows the stated construction
method. It does not prove that method globally optimal over every possible lane assignment (REMAINING_UNCERTAINTIES.md
U-03).

## 4. From proof to production: what a passing proof allows

- A method (an item code's measurement formula) proven on the cases is listed in `engine/source/traceability.py`
  METHOD_PROOFS, with its cases. `test_every_method_proof_listed_in_the_traceability_table_exists_and_passes`
  re-runs every listed case, so the table cannot claim a proof that does not pass.
- A BOQ line of a real drawing is **never** INDEPENDENTLY_VERIFIED because its method passed the proofs. It is
  INDEPENDENTLY_VERIFIED only when an independent value for that line is supplied (`--independent-checks`,
  URBAN_INDEPENDENT_CHECKS_V1: a hand calculation or an independently reviewed figure) and agrees. Otherwise its status
  is ENGINE_TESTED_ONLY, PROVISIONAL, BLOCKED_MISSING_EVIDENCE or FAILED_VALIDATION, with `method_status` saying
  whether its method is proven on the cases.
- A correction found by a proof goes into a new opt-in method (ARCH_TAKEOFF_V2.5). V1 .. V2.4 stay byte-identical,
  and the frozen V2.4 result is kept in the comparison as FAILED_VALIDATION.

## 5. Multi-drawing validation

The same proofs run at three levels:

1. **Synthetic geometry**: the area built straight from the coordinates (`wp_area`, `door_run`).
2. **A proof drawing**: PD-1, a DXF with two WP-B bathrooms and a corridor, through the whole architectural route.
   Both bathrooms reproduce the WP-B hand calculation exactly, and the rules-sheet cases run on it.
3. **The project drawings**: the synthetic villa, its mirror and the reference plan, in both modes. V2.5 is
   deterministic there (254 of 254 files identical across two runs). Its procurement counts are proven at the lower
   bound. No line-level independent values exist for these drawings yet (recommendation R-2).
