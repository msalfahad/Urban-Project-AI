# Engineering audit report - constructability of the V2.5 waterproofing plans

## Scope and question

Three rooms of the Phase 2B-3 proof library were reviewed:
- the 3.00 x 4.00 m bathroom (WP-B);
- the 3.60 x 3.00 m wet area with two doors and a pipe sleeve (WP-E);
- the L-shaped bathroom (WP-D).

The question was whether each V2.5 cutting plan, which is mathematically optimised, describes a waterproofing
installation that can physically be built. Where it does not, the audit asks what the buildable alternatives require.

## Method

- **An independent construction calculator** (`tests/m9_p2b4/construct_reference.py`): stdlib only, integer
  millimetres, no engine import (an AST test checks this). It rebuilds a plan piece by piece: cut from a roll, ripped
  lengthwise, cross-cut, then laid at a place. It then checks:
  - that every piece fits the material it is cut from;
  - that every floor, upturn and doorway surface is covered on a 10 mm grid, and every joint laps;
  - that the material balances;
  - every lap, junction, corner and doorway condition, listed separately.

  It also searches every order of the band pieces for the best joint placement, and it holds planners for the
  junction alternatives.
- **Hand derivations, typed as literals**, for 14 plans. Two figures from my own first draft were corrected by the
  calculator and re-derived by hand (see below).
- **The V2.5 engine's own records**, read through the Phase 2B-3 adapter, compared with the rebuild.
- **No change to any method.** V1 - V2.5 are frozen: engine, CLI, rules and registry files are untouched (`git diff`
  empty). The corrections are a documented patch proposal (`PATCH_PROPOSAL_V2_6.md`) and are not applied.

## Findings

| # | Finding | Result |
|---|---|---|
| F-01 | **The floor-to-wall junction is assumed.** V2.5 models every upturn as a separate band strip whose flange laps 0.10 m onto the floor sheet - the joint lap of UP-WP-002, applied to a junction it was not written for. The junction is not among V2.5's open details | **FAIL** (model) |
| F-02 | **The cutting record is not a cutting plan.** Roll records give a length and a purpose only ("floor strip 5 3.00", "upturn lanes 2.80"): no rip, lane, piece, destination or joint position. The L-shape's cut-off 1.00 x 0.80 m corner is recorded as a 0.27 x 3.00 m "shaped trim" | **FAIL** (output) |
| F-03 | **Joint placement is not checked.** As listed:<br>- WP-B: 2 band joints sit exactly on floor-seam ends (four layers);<br>- WP-E: a joint ends 0.02 m short of an internal corner;<br>- WP-D: a band piece starts on an internal corner.<br>The same pieces rearranged give 0.30 / 0.20 m (WP-B), 0.14 m (WP-E) and 0.10 m (WP-D) with no material change; the acceptable distance is product data | **FAIL** (unchecked) |
| F-04 | **Doorway transitions are withheld (correct), but each doorway piece meets the band ends edge to edge at both jambs.** That is 8 open junctions in the three rooms, and the jamb reveals are uncovered. They belong to the open doorway detail and are not named by V2.5 | PASS, with note |
| F-05 | **Corners are counted and withheld (correct).** Internal corners fold a 0.10 x 0.10 flange pleat inside the band material. The external corner of the L leaves a 0.10 x 0.10 gap in the flange. Neither is completed work | PASS, with note |
| F-06 | **The pipe sleeve is counted (1) with its treatment withheld (correct).** Its position is only a text anchor. It lies 0.40 m from the nearest floor seam and 0.30 m from the band flanges, so a centred collar up to 0.60 m stays clear. Size and detail are unknown | PASS, with note |
| F-07 | **Offcuts.** V2.5 calls every leftover cutting waste until a minimum reusable size is set (N-7). Separated:<br>- WP-B: 0.28 true waste, 0 reusable;<br>- WP-E: 0.79 true waste, 0 reusable;<br>- WP-D: 0.48 true waste + 0.80 reusable.<br>Cutting the doorway piece from the L's step offcut gives 13.50 m2 instead of 13.80 m2 (same rolls and joints) | NOTE (V2.5 conservative) |
| F-08 | **Multi-layer points.**<br>- WP-B: 7 floor-seam ends under the flange + 1 under the doorway lap;<br>- WP-E: 5 + 1;<br>- WP-D: 6 + 0.<br>Their treatment is product-specific | NOTE |
| F-09 | **"17.80 m2 and 2 rolls" is valid only under V2.5's assumption** (separate upstand, 0.10 m flange accepted, no junction reinforcement).<br>- Continuous fold-up: 17.60 m2 / 2 rolls.<br>- Flange 0.11 - 0.15 m: 18.75 - 18.77 m2 / 2 rolls.<br>- Flange 0.16 m or more: 20.60 m2 / **3 rolls**.<br>V2.5's roll sensitivity ("changes_roll_count: false") tests only the doorway alternatives | **FAIL** (statement) |
| F-10 | **Scope of the selection order.** V2.5 applies UP-WP-LAY-001 (fewest rolls -> fewest seams -> least membrane) between strip directions only, and plans the band for least membrane. Applied to the band plan as well, the rule chooses fewer, longer pieces and more membrane: WP-B 18.44 m2 (3 joints), WP-E 16.80 m2 (1 joint), WP-D 16.60 m2 (1 joint, which then falls on a corner). Both readings are buildable; the owner defines the scope | NOTE (N-9) |
| F-11 | The ALONG_X alternative V2.5 reports for WP-B (18.40 m2) has a 18.20 m2 plan with the same rolls and seams. It is not selected and changes no reported quantity | NOTE (minor) |
| F-12 | **Every V2.5 quantity of the three rooms is reproduced by the independent rebuild**: piece lengths, roll cuts, laps, installed, consumed, waste and rolls. The rebuilt plans cover every required surface | **PASS** |

Errors in the audit's own work, caught by the calculator:
- **H-A1.** My hand fewest-joints plan for WP-B (18.65 m2) used both trim lanes in the band. Using one full trim lane
  plus three 3.44 m segment lanes needs only 18.44 m2. The figure was re-derived by hand.
- **H-A2.** A band joint that merely touches a seam end was first counted as "stacked". Stacked now means an overlap;
  touching is reported separately.

## Conclusions

1. **The quantities V2.5 reports are arithmetically right for the plan it models** (F-12).
2. **That plan is not yet a buildable installation:**
   - its floor-to-wall junction is an assumption (F-01);
   - its record cannot be cut from (F-02);
   - its joint positions are unchecked (F-03);
   - its doorway and corner details are open (F-04, F-05).
3. **Two buildable junction methods exist for the 3 x 4 m bathroom** (`WPB_FLOOR_TO_WALL_JUNCTION.md`):
   - a separate upstand: 17.80 m2 with a 0.10 m flange, up to 3 rolls with a wider one;
   - a continuous fold: 17.60 m2, 2 rolls, 3 seams.

   Which one applies is a product decision. The material figure stays CONDITIONAL until it is made. The proven
   subtotal (14.80 m2) is unchanged.
4. **Nothing unapproved is counted as completed work:** the corners, jambs, thresholds and the pipe collar stay
   withheld, with their counts, positions and limits.

## Recommendation

Hold the waterproofing material figures as CONDITIONAL on the junction detail. Obtain the membrane system's data sheet
for the items in `PRODUCT_AND_OWNER_CONFIRMATIONS.md`. Authorise, or decline, the opt-in V2.6 patch
(`PATCH_PROPOSAL_V2_6.md`), which makes the engine:
- carry the junction as an open detail with its alternatives;
- output a cuttable piece-level plan;
- check joint placement.

Floorplan AI research was not started.
