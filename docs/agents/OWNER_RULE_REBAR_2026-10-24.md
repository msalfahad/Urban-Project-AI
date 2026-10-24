# Reinforcement in metric tons and the proposed lap splice method (owner, main chat, 2026-10-24 14:23)

Recorded by the main chat from the owner's words. Section 1 is an owner DECISION; section 2 is an owner PROPOSAL
under assessment (not a rule until the owner approves the main chat's assessment). No engine, rule, quantity, V2.9 or
schedule change. Agents do not start work on it until the owner approves a task.

## 1. Owner decision: reinforcement BOQ unit is the metric ton (طن)

- "All reinforcement quantities in the final Urban Projects BOQ must use metric tons (طن), never kilograms as the
  displayed or contractual BOQ unit": columns, beams and ground beams, slabs, footings, stairs, starter bars (الأشاير),
  stirrups / ties (الكانات), lap splices (التشريك) and any other reinforcement. 1 t = 1,000 kg.
- Internal calculation may stay in kg at full precision; convert only at the BOQ reporting / export boundary. At least
  three decimals, more where needed so small valid quantities stay visible; never round bar weights before aggregation;
  no double conversion, no relabelled kg, no mixed units; subtotals and the total reconcile in t.
- Machine-readable exports / interfaces in kg keep their contracts or migrate explicitly with a schema / version change
  and regression tests.

## 2. Owner proposal under assessment: lap splices

- Stock 12 m; preliminary 40 d compression, 60 d tension, for fc = 250 kg/cm2 and Grade 60; owner classification
  columns / ordinary walls 40 d, beams / slabs / retaining walls / footings 60 d. "Treat 40d/60d as a proposed
  estimating convention, not an automatically verified structural design rule." Drawings, approved lap schedules, BBS
  and approved details take precedence.
- laps = 0 if L <= S, else ceil((L - S) / (S - lap)); total = L + laps x lap; kg = total x d^2 / 162; t = kg / 1000.

## 3. Main chat findings (repository, engine head 768ff1d)

- The proposed formula already exists: engine/source/bbs_optimiser.split_run (identical) and rebar_model.lap_parts
  (laps are BBS / procurement length, never net; BLOCKED_LAP_METHOD without a lap authority). column_rebar keeps
  LAP_SPLICE, STARTER, ANCHORAGE apart from the core run.
- DEFECT CANDIDATE (frozen, route G): engine/source/continuous_beams._with_laps uses n = ceil(L / S) - 1, which ignores
  the length each lap consumes: 23.8 m or 24 m runs get 1 lap where the formula needs 2; 35 m gets 2 instead of 3.
  Frozen module: never edited in place; magnitude on Alsenan not yet measured.
- Alsenan drawings (from the research records): p.8 note 9 development / anchorage of starter bars not less than
  70 d in tension zones, 40 d in compression zones (zone not printed); p.15 slab temperature bars lap 40 x DIA; no lap
  schedule. The engine applies note 9 as a HELD 40 d .. 70 d range at bar ends. The owner's 60 d tension is below the
  drawing's 70 d: the drawing governs.
- Units: engine and boq_line STR.REBAR are kg; tools/boq_export_v1 writes the engine unit (kg, 6 decimals);
  engine/reporting_v3/units.py already converts kg -> t at display with 3 decimals (hides 0.001280 t as 0.001) and has a
  UNIT_CONTROL gate refusing kg rebar in the final BOQ; tools/urban_structural_boq.py prints kg.

## 4. Owner decisions (main chat, 2026-10-24 15:31; essentials in the owner's words)

1. T-273 approved as a controlled task through Lead / Worker / Checker, behind the critical export, completeness and
   regression work; no change to released V2.9, frozen modules or verified quantities without an approved new method
   version and independent regression evidence.
2. Metric tons in T-235 r2: conditionally approved "if the change is small, isolated and does not delay its completion";
   t is the contractual unit; kg kept in audit data with Checker provenance; convert exactly once; up to six decimals
   where needed; sum unrounded before converting / rounding totals; no silent schema change, no invalidated verdict;
   "If the change creates material delay or risk, defer it to T-273."
3. Alsenan laps: "Do not treat 40d-70d as a universally verified lap range." Each drawing note only for the bar groups
   it governs: note 9 for the starter-bar situations it names (tension and compression distinguished), the slab
   temperature-bar 40 d detail where it applies, every other lap HELD until its detailing is established; "at least
   70d" is a minimum, not an exact value or a maximum; the owner 40 d / 60 d convention is never applied where it
   conflicts with the drawings or unresolved structural requirements; no duplicate laps, starters, anchorage or
   already-included BBS lengths.
4. continuous_beams._with_laps: a CONFIRMED formula defect under the continuous-run model; read-only impact assessment
   first; never edited in place; a prioritised isolated correction if it affects active quantities.
- Installed reinforcement, lap allowances and stock-bar procurement / cutting waste stay separate. Total installed =
  net + separately measured additional laps + other non-duplicated components; the lap tonnage is a review breakdown,
  never added twice.

## 5. Impact assessment of D-T273-01 (main chat, 15:31; read-only, in-memory instrumentation, engine head 768ff1d)

Method: route G (tools/urban_boq_m2.py, route "G") run on the Alsenan structural DXF with the V5 and V6 generic
conventions, every continuous_beams._with_laps call recorded in memory and recomputed with the lap-aware count
(bbs_optimiser.split_run model); no file in the repository written. Result:
- The defective function IS on the active route G path: 3,564 calls, 11 continuous-beam marks, 38 bar groups,
  lap factors 40 / 50 / 60 d (the convention triple).
- The longest bar run is 8.708 m (CB11 bottom bars, high reading); NO run exceeds the 12 m stock, so both formulas give
  0 laps everywhere: quantity difference 0.000 kg = 0.000000 t on Alsenan (V5 and V6 identical).
- It is the only copy of this formula in engine/ and tools/ (rebar_model.lap_parts and the column engine use split_run).
- Route G Alsenan reinforcement is PROVISIONAL only (VERIFIED 0 kg); the released frozen-replay route is not affected.
- Existing lap content: columns already carry LAP (54 provisional components, base 40 D; 70 D alternative +640.99 kg,
  flag STR-COL-026) and STARTER components (research/alsenan_column_rebar_s3); slab and pool laps are HELD /
  procurement only, never in the net. T-273 must not add a second column lap or starter.
Conclusion: a latent defect (wrong for any run between 12 m and the first correct lap boundary, e.g. 23.8 / 24 / 35 m),
no effect on current Alsenan quantities; correction belongs in T-273 as a new method version, not an urgent fix.
