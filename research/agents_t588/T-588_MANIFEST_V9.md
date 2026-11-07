# T-588 WIRING MANIFEST V9 + OVERLAY DRY RUN on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate, backlog-permitted), 2026-11-07. Not an integration package: nothing is wired; no
candidate, released (V2.9 + route G), rule, knowledge or registry file is touched; no drawing read (every figure from the
committed, Checker-merged outputs of T-578, T-583, T-584, T-412 and the V8 manifest, sha256 in the JSON). Files:
`manifest_v9.py` (R-T588-1), `out/WIRING_MANIFEST_V9.json`, `tests/t588_manifest_v9/` (16). Rebuild:
`python3 -I research/agents_t588/manifest_v9.py` (`--check`).

## 1. Overlay (R-T580-1 code, read only)

A COPY of the V3.0.58 index (4,999 lines) takes the pending packages in the T-580 Gate B order (V2 .. V8, 5,123 lines),
with V8 REBAR_OMISSION replaced BY NAME by V9 REBAR_COMPONENTS (same 6 line ids), then RAILS_GUARDS and STAIR_STEPS:
**5,124 lines, 0 STALE, 0 two-package lines, 0 unexplained conflicts; every line V9 does not write is identical to the
V8 overlay.** The one flagged row is T-580's own NO_BEFORE (L-4ccc5dc2, answered by T-582 s.3), not a V9 row.
New ruling (2 FIN.STAIR conflicts, EXPLAINED): FIN.STAIR.FLIGHT (B7-01, pitch length, HELD blank) and
FIN.STAIR.STEP_LM (B7-06, step per tread) are two elements of one flight (coverage census B7-01 vs B7-06).

## 2. Rows (class from one fixed map; evidence from the verdict line printed in each row)

| Package | Line(s) | Before | After | Class | Evidence |
|---|---|---|---|---|---|
| REBAR_COMPONENTS (T-583) | DOME-A / DOME-B shell rebar (NEW, V8 ids) | HELD blank (V8) | HELD low 290.684 kg each, high open (bounded part 425.000 kg beside; anchorage / hoop laps by name) | AT_LEAST | PARTIALLY VERIFIED (lows re-derived AGREE) |
| | east ring / west ring | HELD blank | 122.518 / 63.897 kg low, high open (155.966 / 158.208 beside) | AT_LEAST | PARTIALLY VERIFIED; F-C-T583-1 tighter east low +21.771 kg not applied |
| | lift-pit walls | HELD blank | HELD blank, kg(h) = A h + B beside (A 156.642 .. 212.859 kg/m, B 0 .. 123.221 kg) | HELD | PARTIALLY VERIFIED (h not printed) |
| | DOME-3 | HELD blank | HELD blank (no structural drawing) | HELD | HELD |
| RAILS_GUARDS (T-578) | RL-04 / ST-01b band | HELD blank | 0 .. 7.500 / 0 .. 1.875 lm | HELD_RANGE | HELD |
| | T-MS1-N / T-MS2-LD | HELD blank | >= 0.856999 / >= 0.261197 lm (chords) | AT_LEAST | HELD |
| | RL-09 / RL-10 / RL-11 | HELD blank | unchanged (0 .. open: no bound formed) | HELD | HELD |
| | RL-01 .. 03, 05 .. 08 (valued), RL-12 | as index | unchanged, stated | RELEASED / EXCLUDED | RL-07 VERIFIED (T-578), RL-02 + 03 VERIFIED (T-164), rest DRAWING-CONFIRMED |
| STAIR_STEPS FR-T584-1 | NEW E1 FIN.STAIR.STEP_LM `GF-COURT#E1-STEPS` | no line | **11.200 lm** (4 x 2.800), nr 4 beside, binds E1 tread / riser | RELEASED | VERIFIED (T-584 04:05 (e)) |
| FR-T584-3 | 7 owned flight lines | 67.85 lm | unchanged, nr beside (9 / 3 / 11 / 11 / 11 / 10 / 4) | RELEASED | PARTIALLY VERIFIED |
| | MS1-T / RS-C owner lines | HELD blank | >= 4.14365 / 13.7964 .. 13.85 lm | AT_LEAST / HELD_RANGE | HELD |
| | 3 HELD second readings (RS-C, RS-S, RS-A) | HELD 0 .. 13.7964 / 11.5 / 4.6 | EXCLUDED with evidence (the flight is owned by its own line) | EXCLUDED | PARTIALLY VERIFIED |

Totals moved (V9 vs the V8 overlay): STEP_LM released 67.85 -> **79.05 lm** (+11.20, +16.5 %), HELD high 29.8964 ->
13.85 (the 29.8964 was three second readings of flights already owned: a double count inside the HELD sum), HELD low 0
-> 17.94005; STR.REBAR released 9,375.30576 kg unchanged, HELD low +767.783 kg (= T-583 0.767783 t), 4 more open highs;
FIN.RAILING released 33.319174 unchanged, HELD low 1.118196 (= T-578), high 1.875 + 2 open; MET.RAILING.GUARD HELD high
7.500. Freelancer: rails 18.95 lm typed constant, rebar 44.19 t TYPED_LUMP, steps in an area column: no % (NOT_COMPARABLE
/ SCOPE / HELD causes, as T-578 / T-583 / T-584).

## 3. Drawn edge census (R-T588-1 (d); register NOSING EDGE, T-412 s.7)

89 drawn edges (T-412 table; T-578 nosing = the same census, 87.35 lm / 69 confirmed + 20 HELD: one source). Each edge is
priced once: in-step-basis tread / winder edges (80) by the step line of their flight, landing / floor edges (9) by
B7-05 (T-424, not added here). **Before V9: 26 doubles (RS-C 12, RS-S 10, RS-A 4 claimed by second readings) and 4
orphans (E1 treads, the ENGINE_OMISSION); after V9: 0 / 0.** The E1 platform edge 30A stays a B7-05 landing nosing,
never in the step line. Rail lines claim no nosing id. Winder rule: the MS1-L winder edge belongs to the MS1-T turn
(5 winders on the MS1-T line).

## 4. Not in V9, findings

- FR-T584-2 (external door steps): the line pays ONE length (F-C-T584-1, visible 3.50 vs stone 3.80 lm) -> V10 after
  T-592. B7-05 nosing lines: T-424 must price only the 9 landing / floor edges outside the step basis (T-412 s.7).
- F-T588-1: three HELD second-reading STEP_LM lines carried bounds that repeat owned flights (29.8964 lm in the HELD
  high); the T-424 / Gate B package must take them out exactly as row FR-T584-3 states.
- F-T588-2: FIN.STAIR.FLIGHT (B7-01) and STEP_LM share each flight host; ruled as two elements here; the overlay had no
  ruling for that layer before.

## 5. Lesson proposal (ERS s.7)

"A drawn edge is priced by one line: before a stair package goes to Gate B, list every drawn nosing edge with the line
that prices it (step line for in-step-basis edges, nosing line for landing / floor edges); a second reading of a flight
never claims an edge, even inside a HELD bound" (any villa on the line-index scheme; provenance T-412 / T-584 / T-588;
test tests/t588_manifest_v9).
