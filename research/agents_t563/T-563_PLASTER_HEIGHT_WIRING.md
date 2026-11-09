# T-563 INTEGRATION PACKAGE (Gate B): PLASTER_HEIGHT_V1_WIRING -> ARCH_TAKEOFF_V3.0.61

Worker 3 (lane I), 2026-11-09, claim 13:01 UTC. Base: the working branch 2e80c03f + T-423 r3 READY bdbbb8db merged in
(V3.0.60 / master 1.60.0; the Lead's order: the Checker takes this package only after T-423 r3 is MERGED, version and
master number allotted at merge, expected V3.0.61 / 1.61.0). Not released; the released default (V2.9 + route G) is
untouched.

## 1. Files

| File | What |
|---|---|
| `engine/source/arch_v3061.py` | ARCH_TAKEOFF_V3.0.61, R-T563-1: PLASTER_HEIGHT piece, binding, checks, integrate / write |
| `tools/urban_boq_m9.py` | hub: a V3.0.61 run IS a V3.0.60 run first (same line), `--v3061-inputs` guard, branch nested in V3.0.60, choice + help |
| `research/agents_t563/t563_inputs.py` | URBAN_V3061_INPUTS_V1 from T-556 table + T-558 manifest + T-651 V3.0.59 line index (sha-pinned), T-634 beside |
| `research/agents_t563/v3061_run.py` | run of record: wraps T-423's v3060_run (asserts V3_0_59 75331a76, V3_0_60 8c8a9642) |
| `research/agents_t563/t563_summary.py`, `summary_t563.json` | numbers-only package summary: per-line before / after, diff, totals, 132 binding re-reads |
| `research/agents_t563/build_master_1_61_0.py`, `write_manifest.py` | BOQ_FAMILY_MASTER_1.61.0 = 1.60.0 + pending V3.0.61 (after pending V3.0.60) + B4-03 / B4-06 text; RULES_MANIFEST by its tool |
| `tests/t563_plaster_height/` | villa V563 by hand (20 tests: 4 normal, 16 adverse) + master 1.61.0 (11 tests: 6 normal, 5 adverse) |
| `research/agents_t459/T459_CANDIDATE_BINDING.json`, `tools/m9_rules_manifest.py`, maps | by their tools / one AUTHORED entry |

## 2. Physical element and rule

Dry plastered wall face, FFL to the soffit of the structural slab / roof over the room (owner Q-72; Q-14), net of every
actual opening re-cut at that height (Q-73) and of crossing-beam end sections (beam faces are ceiling, Q-57). Paint is a
separate layer at the finished ceiling G1 (3.65 / 3.35 / 3.15) and does not move. Owner manual method and drawing method
side by side in `PIECES` and in every ledger row. Every one of the 11 rooms has some face under a ROOF whose build-up is
not printed (D-39 / DCR-6, designer item; not an owner question, ERS 2.7 not met): each line is HELD
(BOUNDED_EXPOSURE) at the merged T-556 low / high with that RFI; none is released, none is 0.

## 3. Per line, before (V3.0.60) -> after (V3.0.61), m2

| Room | Line | Before | After (HELD) | Status (WORKFLOW_CONTROLS s.5) | Independent re-measure beside |
|---|---|---|---|---|---|
| GF-01 | L-b1529955 | HELD blank | 61.46433 .. 65.25433 | HELD (roof 3.79 scenario) | - |
| GF-04 | L-1ddc23d5 | HELD blank | 43.155 | HELD (roof scenario) | - |
| GF-15 | L-0d93f220 | 56.0131 REL | 66.52899 | HELD; floor part DRAWING-CONFIRMED | Checker by hand 66.529; T-634 +0.0068 |
| GF-08 | L-8cecb1d0 | 152.0505 .. 178.805 | 178.22057 .. 211.80527 | HELD (W02, lift door) | - |
| 1F-01 | L-af9621f4 | 51.415 REL | 62.573 .. 62.607 | HELD | T-634 +0.0004 |
| 1F-04 | L-971f0bda | 52.005 REL | 63.141 | HELD | Checker raw DXF 63.141 AGREE; T-634 -0.0035 |
| 1F-10 | L-2ba8077b | 48.94 .. 52.29 | 58.026 .. 62.05 | HELD (arch) | - |
| 1F-11 | L-31db3c83 | 61.4626 .. 61.7177 | 74.77651 .. 80.19841 | HELD (W17 crown, Q-76 A) | - |
| 1F-13 | L-9b4a7bab | 111.0177 .. 114.3677 | 135.6255 .. 139.6155 | HELD (lift door) | - |
| 2F-03 | L-4ce74fc3 | 57.775 REL | 69.775 | HELD | Checker raw DXF 69.775 AGREE; T-634 0.0000 |
| 2F-01 | L-ae0cdd79 | 22.6502 .. 26.0002 | 27.35991 .. 31.76591 | HELD (lift door, B15) | - |

Sums: 4 released 217.2081 -> HELD 262.01799 .. 262.05199 (+20.63 .. +20.65 %); 11 lines 840.64581 .. 895.89641 =
the T-558 manifest exactly (asserted in the inputs builder and in `changes_for`). Each restated line keeps its old
value, gross, deduction list and the V3.0.36 list record (`NET_RECORDS`) inside `plaster_height_v3061.was`.

## 4. Whole BOQ, diff and regression (run of record on the Drive copies)

- Chain: t167 v304_run -> v3061_run (exit 0): V3_0_59 75331a76 (candidate of record) -> V3_0_60 8c8a9642 (T-423 r3)
  -> V3_0_61 **2bc99980**: 5,073 lines, 5,062 SAME, 11 CHANGED, 0 ADDED.
- Code totals: only FIN.PLASTER|m2 moves: released 580.5819 -> 363.3738; held 488.201 .. 544.0606 -> 932.72581 ..
  1,006.77641; bounded lines 8 -> 14; blocked 12 -> 10; lines 62. FIN.PAINT|m2: 45 lines byte-identical, released
  217.2081, held 487.121 .. 542.8606 unchanged.
- Against the released V2.9 + route G: SAME_QUANTITY 576, QUANTITY_DIFFERS 1,016, NOT_IN_RELEASED 3,481, unchanged
  from V3.0.60 (the 4 released plaster lines already differed from V2.9).
- Downstream (outside the candidate): the 132 T-454 / T-489 bindings of the 11 lines re-built by the merged tables on
  line indexes of V3.0.60 and V3.0.61: only the 11 rows move per table; 22 WALL_PLASTER mortar bounds = held range x
  0.020 m (T-454 bound 16.8129162 .. 17.9179282 m3 per table, never added across tables), estimate beside 4.344162 -> 0,
  110 stay blank (bond coat: no thickness; cement / sand: NEEDS_MIX); 0 values; all = the manifest's expected_after.
  Reconciled statement / scorecard / trial BOQ: next manifest (T-654) carries these 11 lines.
- Tests: tests/t563_plaster_height 31 pass; t423, t498, t651, t485, t479, t463, t212, t637, t459 pass; m9_s6, t131,
  m9_s2_arch pass (L3); freeze 0; codemap stale none.

## 5. Freelancer and verdicts

Gross to gross on the same 11 rooms (T-556): engine 1,006.05 m2 at the plaster height vs freelancer 924.205 m2
(+81.85, +8.9 %): his flat 3.60 / 3.40 / 3.50 stop below the soffit (4.29 / 3.99 / 3.79). Verdict proposals: old
candidate (paint height) ENGINE_WRONG (T-552 / T-556); new height ENGINE_RIGHT under Q-72 (his height
RULE_DIFFERENCE); roof-face share UNRESOLVED (D-39 / DCR-6, designer).

## 6. Missing, held, lessons

Missing / HELD: roof build-up (D-39 / DCR-6) on every line; W02 / lift door / arch heights; beam-end counts in open
rooms; dry plaster rooms outside the T-556 table are not restated (`WAITING.T563_OTHER_DRY_PLASTER`). Independent
re-measure: 4 / 11 rooms (Checker 2 raw DXF + 1 by hand; T-634 own on 4, max |diff| 0.0068 m2); the other 7 rest on
T-556 only: PARTIAL 4 / 11.

Lessons row proposed (ERS s.7): | 2026-11-09 | the first wiring run stopped in the V3.0.36 list check: a released line
moved to HELD still carried a record whose check presupposes a valued net | a restatement copied the line and changed
its state only | a version that moves a line's state moves the earlier records whose checks need the old state into its
own 'was' record (kept, never deleted) and asserts the chain checks on the result | tests/t563_plaster_height | proposed |
