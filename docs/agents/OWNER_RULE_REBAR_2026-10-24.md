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
