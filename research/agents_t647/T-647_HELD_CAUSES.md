# T-647 structural HELD lines with no committed cause (F-T636-1, B9 / B10 / B11) to a named cause (R-T647-1)

Worker 1 (lane S), 2026-11-09, branch `agents/task-T-647`. Research ledger, unwired: no candidate, released, rule,
knowledge or registry file changed; no rebar calculation code changed (owner gate 2026-10-25 10:33). Development villa
only; drawings cited by Drive folder and title. Output (generated): `out/HELD_CAUSE_CENSUS_T647.json` / `.md`.

## Method

The 183 lines are read by id from the merged trial BOQ (T-636). Each gets ONE cause record (class + reference + the
committed source file and the exact text it was read on; the builder checks the text is in the file and pins its
sha256). Classes: OWNER_DECISION (Q-id), DESIGNER_ITEM (D-nn / RFI), CHECKER_DOWNGRADE, PRINTED_VALUE_GAP (sheet),
DEPENDENCY (HELD host line id), FIX_ROW (drawing-confirmed proposal with its own hand calculation, not wired).
B11: the 138 lines are the T-318 `#SLAB_BAR_ENDS:VALUED` part lines; each bound is re-derived through the engine's
read-only `arch_v3027.load_inputs` and must equal the line; every development part is re-added by hand from the
T-307 end ledger (sum of (w - 0.040) over the edge-beam ends x d^2/162), 59 / 59 reproduce the bound.

## Result: 183 / 183 with a cause; HELD census before = after

| Trade | Class | Lines | Reference |
|---|---|---|---|
| B11 | DESIGNER_ITEM | 79 | RFI-B-S10: top-bar extent, plan note 2 vs ST p.15 (both readings differ on every line) |
| B11 | PRINTED_VALUE_GAP | 39 + 3 + 17 | ST p.4 / p.5 / p.6: mesh rate, no first / last bar (count A .. B); 3 bare labels '5 o 10'; 17 COUNT-CONVENTION GAP (r2) |
| B10 | FIX_ROW | 5 | FR-T647-1 .. 5: CN columns, ST p.9 schedule CN GF / 1F / 2F struck (own re-read AGREE T-075): NOT_APPLICABLE |
| B10 | DESIGNER_ITEM | 4 | D-21 dome DOME-3; D-33 two loaded ground-beam runs; RFI-A02 pool steps |
| B10 | OWNER_DECISION | 4 | Q-65 C parapet material (+ D-39 edge build-up) |
| B9 | DESIGNER_ITEM | 7 | D-39 six 2F wall lines (roof datum); D-35 ANNEX_S below-ground block |
| B9 | PRINTED_VALUE_GAP | 6 | MAIN_S below-ground block (no thickness / bottom printed); 5 white-unit lines on released hosts (AAC face not selected) |
| B9 | DEPENDENCY | 19 | material lines whose host block line is HELD (host cause named) |

Census (trade x unit, unchanged): B11 kg 138 bounded 701.958 .. 1,629.410; B10 m3 10 blank + 3 bounded 1.134 .. 3.483;
B9 32 blank. If the 5 CN fix rows are wired: B11 unchanged (138 bounded, 0 kg released); B10 5 lines
leave as NOT_APPLICABLE (no value; bounded 1.134 .. 3.483 m3 leaves the HELD census). Freelancer: 0 CN columns (agree);
slab bar ends sit inside his single 5,400 kg slab lump (no line comparison).

## r2 (Verifier 2026-11-09 01:54, Gate A f + h on FR-T647-6 .. 22)

The 17 B11 development parts whose two readings coincide (low == high, 51.574073 kg over the 17 lines at either end)
are NOT drawing-confirmed: the mesh is a printed rate (R306-1), the TOTAL bar count is A or A + 1 on every one of the
17 parents (e.g. GF-016 y 10 / 11, 1F-025 x 31 / 32, GF-135 y 24 / 25), and which bars reach the edge-beam segment
depends on the unprinted boundary-bar position, so a sub-count on that segment can be n or n + 1 under an admissible
placement. Each line is now HELD, PRINTED_VALUE_GAP 'COUNT-CONVENTION GAP' with bars A, A + 1 and kg at each end
(`count_convention_gaps` in the census); the r1 fix rows are withdrawn. Rule R-T647-1 (e) refuses a DRAWING-CONFIRMED
fix row unless every input is printed (`inputs_printed`, no count convention attached); (f) a count-convention record
states both counts and both kg, B = A + 1, never 0. Tests: normal (printed '12 T10' count passes) and adverse
(coincident ends on an unprinted rate refused; missing flag refused; malformed / zero gap refused).

## Findings and lessons

- F-T647-1 (r1) WITHDRAWN and REFUSED as a general rule by the Verifier (it would release unprinted counts on every
  villa). Replacement lesson (ERS s.7 proposal): "Coincident endpoints of a bound prove a value only when the bracket
  covers every admissible reading of THAT quantity; a total-count bracket (A, A + 1) does not bracket a sub-count on
  one support segment; test that the inputs are printed, not that two readings agree." Scope every villa; provenance
  T-306, T-318, Verifier 2026-11-09 01:54.
- F-T647-2: 5 CN column lines HELD as TYPE_NOT_IN_SCHEDULE since the frozen reader; the schedule prints the member as
  absent above ground (T-075; CHECKER-CONFIRMED 2026-11-09: CN on no GF / 1F / 2F slab or roof plan).
