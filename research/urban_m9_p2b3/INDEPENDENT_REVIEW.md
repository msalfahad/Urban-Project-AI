# Independent review of the V2.5 work

The work read as an independent quantity surveyor would read it: is the proof real, is any figure forced, is anything
over-claimed, what would I object to. The findings that led to fixes are in DEFECT_REGISTER.md.

## 1. Is the proof independent?

- **Hand calculations are typed, not computed.** An AST test refuses any non-literal in an `expected` block. Every
  sheet shows its arithmetic, including the negative check that proves a minimum (e.g. "2.79 m would cover 3 x 2.69 =
  8.07 < 8.10").
- **The reference calculator cannot see the engine.** It imports only `math` and `itertools`, as the AST test checks.
  It works in integer millimetres, searches instead of using formulas, and packs rolls by exhaustive search. It caught
  two of its own errors through its balance assertions (H-04, H-05), and it caught a wrong figure in my notes (H-03).
- **Three expected values were wrong at first (H-01, H-02).** The engine was right each time. Each correction was
  re-derived by hand and written into the sheet; none was copied from the engine output. This is the evidence that the
  comparison really can fail in both directions.
- **Weakness.** The hand calculations, the reference and the engine adapter were written by the same author. The
  construction method (lane choice, lap convention) is shared by design. A second reviewer re-deriving two sheets
  would close this (U-11).

## 2. Is anything forced?

- No expected value was moved to pass. Where V2.4 disagrees with the hand calculation, V2.4 stays frozen and is
  recorded as FAILED_VALIDATION, quantity by quantity (`V24_FAILS` in the tests). V2.5 carries the fix.
- No test was weakened. One V2.4 test docstring was corrected to say that it pins frozen behaviour (D-V25-06); its
  asserted values are unchanged.
- The 3.00 x 4.00 m figures the owner asked to prove (17.80 m2, 2 rolls) come out of the engine's own roll records in
  `test_the_3x4_bathroom_cut_inventory_strip_by_strip`, through the drawing route (PD-1) as well as the synthetic
  geometry.

## 3. Is anything over-claimed?

- **INDEPENDENTLY_VERIFIED is never given for a passing test.** On the villa and the reference plan it is 0 lines; on
  PD-1 it applies only to the lines with a supplied independent figure. A wrong figure turns its line
  FAILED_VALIDATION (tested).
- **No structural feasibility is claimed.** A door enlargement is "geometrically possible" at most, and every
  enlargement keeps the structural engineer's approval (tested).
- **A roll count is never CONFIRMED with an open detail.** The proven subtotal (A + upturn + continuation) is shown
  apart from the provisional final material requirement. The roll count is reported both as computed and with every
  open doorway upturned.
- **Roll packing does not exceed what can be installed.** Only full-width cuts from roll remainders that fit them;
  band lanes and narrow offcuts never travel between rooms; a part roll serving two floors is flagged. The exact
  packing only reorders which roll a straight cut comes from.

## 4. Objections

| # | Objection | Weight | Recommendation |
|---|---|---|---|
| O-1 | The owner's selection order (fewest seams before least membrane) costs membrane in three proofs (WP-CX +0.33, RS-02 +0.50, WP-LX +0.50 m2) | low; the rule is approved | confirm (N-9) |
| O-2 | The roll-remainder option of the band planner is a rule (largest remainder first), not a search; it can leave short band pieces (0.20 m in WP-B's ALONG_X alternative) | low; that layout is not selected | a minimum practical piece from the system data sheet (N-7) would let the planner refuse such pieces |
| O-3 | The V2.5 band topology fix is exact for an area with one doorway only; other areas keep the V2.4 model, flagged | medium for rooms with two doors and a resolved threshold detail | extend when a project selects a detail |
| O-4 | The patch of a PATCH treatment is assumed cut from the area's own membrane | low; the rule says "membrane area each" | the system data sheet decides (accessory vs. sheet) |
| O-5 | The real plans have no line-level independent values: V2.5 is proven on the method, not yet on a real drawing's lines | high for acceptance | R-2: an independent take-off of selected rooms as `--independent-checks` |
| O-6 | Door feasibility still rests on an inferred structure and an engine pier | high for doors | R-1 and N-2 |

## 5. What I would not change

- V2.5 is opt-in. V1 .. V2.4 outputs are byte-identical (747 of 747 files) and V2.5 is deterministic (254 of 254).
- Withholding over guessing: every doorway, corner, penetration and termination without a detail stays open with its
  range, and the roll sensitivity says whether it could change a roll.
- Expected values are literals typed from a written derivation, compared against an engine they never read.
