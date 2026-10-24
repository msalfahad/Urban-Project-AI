# T-273 Reinforcement lap splices as their own rows, the lap-aware continuous-beam count, metric tons at the export boundary (Alsenan; every villa)

Worker 1 (lane S), 2026-10-24. Research piece + one unwired producer module + one opt-in export option. No released,
frozen or candidate quantity changes; integration (lane I) only after the Checker's verdict. Development villa, not an
accuracy claim. Drawings named by Drive folder and title only.

Acceptance: OWNER_RULE_REBAR_2026-10-24.md sections 1, 4, 5 (owner decisions 14:23 and 15:31) and the board row.

## 0. Inputs (all merged, cited; no private file read in this run)

| Input | Used for |
|---|---|
| research/agents_t265/LEDGER_T265.csv (MERGED dd08d6b2) | ground-beam bar populations and face-to-face runs: boundary G.B 5 runs, main-house exterior 16 runs + ring |
| research/agents_t138/T-138_GROUND_BEAM_STRAP_STEEL.md r2 (MERGED) | which bands carry their main bars THROUGH their interior columns (p.13): south 7D0 / FC 18.570 m, north 170 / 7C3 13.770 m; every other span two bar ends per piece; 7D4 / F8 10.10 m (interior family) |
| research/alsenan_column_rebar_s3/COLUMN_LAP_STARTER_REGISTER.json | the column LAP / STARTER / ANCHORAGE components already carried |
| research/alsenan_slab_rebar_s7/02_S7_BLOCKED_ITEMS.csv | slab TEMPERATURE (94) and TRANSITION_LAP_SPLICE (74) blocked items |
| research/d1_1_stirrup_authority_audit (merged source search) | the only lap print in the set: Drive "Alsenan chalet project" / "ST7757.pdf" p.15 temperature note 1 "LAP LENGTH FOR ALL TEMPERATURE BARS SHALL BE 40xDIA"; p.8 note 9 is development / tie length of STARTER bars, not less than 70 d tension / 40 d compression |
| rules/methods/URBAN_METHOD_REGISTER_V3.json URBAN-REBAR-NET-AND-PROCUREMENT@v1 | stock length 12.0 m (OD-V3-3) |

## 1. Physical element

A lap splice is the overlap of two bars of one continuous bar group where the run is longer than the stock bar. The
overlap is real, installed steel (owner 15:31: installed = net + separately measured laps; procurement / cutting waste
apart). It is NOT a starter bar, NOT a column splice the column ledger already carries, NOT an anchorage and NOT part of
a BBS length that already contains it. Its quantity has two independent facets, each with its own status: the splice
COUNT (from the run length, the continuity of the bars and the stock) and the lap LENGTH (from the lap authority).

## 2. Method (engine/source/rebar_laps_v1.py, REBAR_LAPS_V1 / CONTINUOUS_BEAM_LAPS_V2, unwired producer)

- Count: laps = 0 if L <= S, else ceil((L - S) / (S - lap)); lap >= S BLOCKED. The one formula already in the engine
  (bbs_optimiser.split_run); the module asserts equality with it on every call.
- Count window: for a run longer than the stock the count is the same for every lap length from 0 up to
  lap_max = S - (L - S) / n0 (n0 = ceil((L - S) / S)); a count is stated only with this window.
- Lap authority in order: printed lap schedule > approved detail > drawing note ONLY for the bar groups it names ("not
  less than" = a minimum, never the lap; a note that splits tension / compression needs the splice zone) > owner
  40 d / 60 d convention (PROVISIONAL, only where the project allows it, never where a drawing note governs the group,
  a conflict is a finding) > HELD. No default lap length anywhere.
- Refused: a second lap on a group whose splices another ledger carries (LAP / STARTER / ANCHORAGE components), a lap on
  a BBS length that includes its laps, a lap >= stock. A top-storey / free-end group is NOT_REQUIRED.
- Units: kg is the calculation unit (rebar_unit_mass under the project's method); t = kg / 1000 is written once per row
  at 6 decimals; subtotals in t come from the unrounded kg sums.

### D-T273-01 (CONFIRMED formula defect, frozen continuous_beams._with_laps): before / after

| Run L (m), T16, 60 d = 0.96 m | Frozen ceil(L / 12) - 1 | V2 owner formula | Bar length frozen -> V2 (m) |
|---|---|---|---|
| 8.708 (longest Alsenan route G continuous-beam run, owner s.5) | 0 | 0 | 8.708 -> 8.708 (0.000) |
| 12.00 / 12.01 | 0 / 1 | 0 / 1 | unchanged |
| 23.80 | 1 | **2** | 24.76 -> 25.72 (+0.96) |
| 24.00 | 1 | **2** | 24.96 -> 25.92 (+0.96) |
| 35.00 | 2 | **3** | 36.92 -> 37.88 (+0.96) |

Alsenan effect: 0.000 kg = 0.000000 t (no run over 12 m in route G; main chat's instrumented run, s.5, and the 8.708 m
case above). The correction is the new method version CONTINUOUS_BEAM_LAPS_V2 (with_laps_v2); the frozen module is
untouched (freeze 0). Note for the Checker: the merged T-138 r2 fixture asserts "24.00 m -> 1 (exact multiple)", which is
the frozen formula; under the owner's formula a 24.00 m run needs 2 laps for any lap > 0. Its kg was HELD, so no released
quantity rests on it; the fixture text is a finding, not changed here (another task's test).

## 3. Alsenan lap rows (research/agents_t273/LAP_ROWS_T273.csv; 63 rows: 35 HELD, 28 NOT_REQUIRED, 0 released)

| Bar group | Run (m) | Bars | Splices (count window) | Lap length | Lap kg | Status |
|---|---|---|---|---|---|---|
| South band 7D0 / FC main bars (3 top + 3 + 3 bottom T16), through 3 interior columns (T-138 r2) | 18.570 | 9 | 9 = 1 per bar for any lap <= 5.43 m | no authority names ground-beam bars | - | HELD |
| North band 170 / 7C3 main bars (9 T16) | 13.770 | 9 | 9 = 1 per bar for any lap <= 10.23 m | same | - | HELD |
| Boundary G.B run 7FE#1 (2 T14 top + 3 T16 bottom), continuous through the boundary columns (T-265) | 31.370 | 5 | 10 = 2 per bar for any lap <= 2.315 m (this run only; corners not established) | same | - | HELD |
| Side bars 4 T12 of the two bands' runs | per run 1.20 .. 6.35 | 4 | continuity through the columns not printed | same | - | HELD |
| Boundary runs 7FE#2, 7FE#3, 7FC#1, 810#1 | 1.15 .. 8.10 | 5 | continuation round the corners not established | same | - | HELD |
| Ring ARC:157+158 and 145+7CA#1 | 6.087 / 1.90 | 13 | bar ends not established by a merged ledger | same | - | HELD |
| Other main-house exterior runs (T-138: two bar ends per piece) | 0.36 .. 4.40 | 13 | 0 for any lap (run <= 12 m) | - | 0 | NOT_REQUIRED |
| Slab temperature bars (94 blocked S7 items) | not quantified | - | waits on the group | p.15 40 x DIA printed, diameter not established | - | HELD |
| Slab main-bar transitions d10 (73) / d12 (1) | not quantified | - | waits on the group | p.15 names temperature bars only; note 9 starter bars only | - | HELD |
| Columns: 56 LAP + 36 STARTER + 59 ANCHORAGE components (column ledger S3) | - | - | already carried | - | not added | ALREADY CARRIED (a second lap is refused) |

Net steel under the ground-beam rows reconciles: 1,019.337 kg (HELD rows) + 344.247 kg (NOT_REQUIRED rows) =
1,363.584 kg = T-265 1,310.960 kg + the main bars through the six interior columns 9 x (2.30 + 1.40) m x 1.58025 =
52.622 kg (T-138 r2 scope). The lap rows change no net quantity.

Owner convention as INFORMATION ONLY (not a quantity, not released; owner 15:31 (3): every lap HELD until its detailing
is established): 60 d on the rows whose count is established = 0.96 m (T16) / 0.84 m (T14): south band 13.653 kg, north
band 13.653 kg, 7FE#1 13.167 kg; 40.474 kg = 0.040474 t in all. Note 9's 70 d tension minimum would give at least
1.12 / 0.98 m; neither is a lap length for beam bars.

### Columns: a finding on the existing column lap components (no change made)

The column ledger carries 56 LAP components at 40 D (496.986 kg PROVISIONAL / LOWER_BOUND) with "70 D alternative"
869.722 kg (flag STR-COL-026). Under the owner's 15:31 ruling note 9's values are both MINIMUMS ("not less than"): a
tension-zone splice is at least 70 d with no printed maximum, so 869.722 kg is a lower bound of the tension case, not an
upper bound of a 40 d .. 70 d range. The column lap stays HELD by zone; its labelling as a closed range is for the column
ledger's owner task (not this row's files).

## 4. Metric tons at the export boundary (tools/boq_export_v1.py, opt-in --contract-units)

- Canonical rows unchanged: BOQ.csv / sheet "BOQ" stay in engine units (kg), the unit every URBAN_CHECKER_VERDICT_V2
  record binds to, so no verdict is invalidated (test: the same V2 COMPONENT verdict binds identically with and
  without the option, BOQ.csv byte-identical).
- With --contract-units: BOQ_CONTRACT_UNITS.csv (schema URBAN_BOQ_CONTRACT_UNITS_V1; columns + engine_unit +
  conversion) and BOQ_CONTRACT_TOTALS.csv, two XLSX sheets, manifest schema raised to URBAN_BOQ_EXPORT_MANIFEST_V2 with
  the new files hashed. t = kg / 1000 once; 6 decimals (0.4 kg -> 0.000400 t visible); totals from unrounded kg sums
  (3 x 0.4004 kg: rows 0.000400 t each, total 0.001201 t, not 0.001200); kg and t rows of one BOQ line refused (mixed
  units); held cells empty, never 0. The factor equals engine/reporting_v3/units.py UNIT_POLICY (one conversion).
- Without the flag every byte written is as before (t235 suite unchanged and green).

## 5. Versus the freelancer

His reinforcement is a kg/m3 lump (44.19 t in all) with no lap row and no per-group split: no like-for-like line,
**RULE_DIFFERENCE, no %** (URBAN-REBAR-NET-AND-PROCUREMENT@v1: never kg/m3). Engine released / candidate lap lines:
none before, none after (all held or not required).

## 6. Rule proposed (every villa; provenance T-273; adopted only as a new rule version, the RULES_MANIFEST file waits for T-267 r2)

**R-LAP-1**: a lap splice is a row of its bar group, never inside the net: count = ceil((L - S) / (S - lap)) on the
continuous bar run (continuity read from the drawing; a run not shown continuous holds its count), stated with its lap
window; lap length only from a lap schedule, an approved detail or a note that names the group (a "not less than" value
is a minimum; a tension / compression note needs the splice zone); the owner 40 d / 60 d convention is PROVISIONAL and
never applied where a note governs; no second lap where another ledger carries the splice, starter or anchorage; t = kg /
1000 once at the reporting boundary from unrounded kg.

## 7. Lessons-register row (proposed)

2026-10-24 | The continuous-beam lap count gave 1 lap on a 24 m run that needs 2, and a merged hand fixture asserted the
same | The count ceil(L / S) - 1 ignores the length each lap consumes, and an exact multiple of the stock looked like
"no extra lap" | Splice count = ceil((L - S) / (S - lap)) (split_run, owner formula), stated with the lap window over
which it holds; a lap length the drawings do not print holds the lap kg, never a default (any villa) |
tests/t273_rebar_laps (23.8 / 24 / 35 m: frozen fails, V2 right; lap = stock BLOCKED; window 31.37 m -> 2 up to
2.315 m) | PROPOSED.

## 8. Not done / uncertain (designer items; no owner question: ERS 2.7 not met)

- Ground-beam lap length: no lap schedule, detail or note for beam bars (D-36 family): every ground-beam lap HELD.
- Continuity of side bars through columns, of the boundary band round its corners, of the ring and 145 / 7CA ends: not
  printed / not established by a merged ledger (counts HELD).
- Slab temperature bars: the bar group itself is blocked (no 160 / 180 mm table row): the printed 40 x DIA waits on it.
- Couplers, restricted splice zones: none printed in the set (no finding raised).
- Interior ground-beam families (7D4 / F8 10.10 m, no lap under 12 m stock), straps, footings, pool, stairs: not in
  this row's scope beyond the T-138 r2 statement; footing / pool / stair bars are shorter than the stock in the merged
  ledgers.
