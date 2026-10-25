# T-254 Integration package: ARCH_TAKEOFF_V3.0.17, the basis correction

Worker 3 (lane I), 2026-10-25, run session_01H97b2fAEPGDsWCdGqnzXM2. Integration package for Checker Gate B. ERS read:
s.2.1 (element first), s.2.3 (owner manual method beside the drawing method), s.3 (reconcile to the cause), s.4 (rule +
normal / adverse test), s.7 (lessons row). Nothing here is a new quantity: every figure is read from a checker-merged
file (T-289, T-287, T-253), line id by line id; (i) is the one geometric reading of this run and it drops a strip.

## 1. What changed

- `engine/source/arch_v3017.py` NEW: ARCH_TAKEOFF_V3.0.17 = V3.0.16 + piece BASIS_CORRECTION (URBAN_V3017_INPUTS_V1).
  Per record, in place (same line id, so a V2 verdict or a downgrade record stays bound): REBASE (SOURCE_DERIVED on the
  element's own printed basis, DRAWING-CONFIRMED; VERIFIED only with a checker run), HOLD / CONFLICT (BLOCKED_RFI,
  BLANK, named item; readings only in V3_0_17_SCENARIOS.json), NOT_PRESENT (NOT_APPLICABLE_WITH_EVIDENCE, a drawn
  absence; never a 0 line); a drawn element the candidate omits is ADDED only HELD. Refused: a stale 'before', a
  borrowed class depth / finished level / profile default / unmerged value as support, a held figure (0 included), a
  line twice, a group whose line ids do not sum to its declared totals, a correction list that misses a line holding a
  drawn exterior run, a drawn run bound to no line. Generic binding `bind_runs` / `check_correction_list` (the lessons
  row of T-289). Every other line byte-identical to V3.0.16, project identity block included (asserted per run).
- `tools/urban_boq_m9.py`: V3017 registration, `--v3017-inputs`, innermost step after V3.0.16.
- `research/agents_t254/`: `t254_inputs.py` (inputs from the merged files), `v3017_run.py` (the run), the 1.12.0
  builder, this report. `rules/coverage/BOQ_FAMILY_MASTER_1.12.0.json` (1.11.0 + pending V3.0.17, no family change) +
  RULES_MANIFEST by its tool. `tests/t254_basis_correction` (villa K254 hand fixture + family master).

RUN_SECTION

## 4. What is missing / open

- (ii) ring ARC:157+158 end closure: NOT closed in this package. Own readings on the drawing (shapely, private copy):
  band between the two arcs, columns 17BA / 17BD / 17C0 deducted: 1.7633 m2 with the outer-arc span (radial ends at the
  outer arc ends), 1.8536 m2 with the inner-arc span; the merged T-242 figure 1.8262 m2 and the Checker's own 1.8385 m2
  (+0.0123, +0.67 %) both lie between. The span of the ends moves the plan area by 0.09 m2: the end rule decides it, and
  'an arc end inside a neck closes on the neck face' does not settle it here because the necks (0.30 square, centred
  2.419 m from the arc centre) leave a 19 mm sliver against the inner arc. The ring line carries the merged 1.7349 m3;
  the rule + its tests stay a row for the Lead (ERS s.4).
- ST-03 (L-061e18cf35a4b6b33d68, 0.948267 PROVISIONAL): left byte-identical for T-266 (Lead 08:15).
- The 28 closable columns (18.3465 m3, VERIFIED as a component by the Checker 2026-10-24 03:19): the candidate lines
  are not touched (their figures are the verified ones or the T-256 / T-248 rows say so); no status text is written on
  them (a verdict is the Checker's record, not a line field).
- Cross-trade named, not changed (T-289 s.4): no formwork line and no ground-storey GB rebar line on these bands
  (T-293 / T-199); the 30 column rebar lines NOT_APPLICABLE take the same heights when built; buried WP 45.4682 m2 already
  reads D 0.95.
- F-T289-01: C1 is 0.20 x 0.50 (0.10 m2); this package cites no '0.30 x 0.30' C1 text (the T-289 report s.5 does: the
  Checker's own correction stands; the research file of a merged task is not edited here).
- Guard re-check (DEFAULT_GUARD) not re-run in V3.0.17: the piece adds no default value; every rebase names a printed
  basis and every other change is a hold.
