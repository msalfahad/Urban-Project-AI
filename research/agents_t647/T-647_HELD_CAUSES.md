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
| B11 | PRINTED_VALUE_GAP | 39 + 3 | ST p.4 / p.5 / p.6: mesh rate, no first / last bar (count A .. B); 3 bare labels '5 o 10' |
| B11 | FIX_ROW | 17 | FR-T647-6 .. 22: count A = B at the edge-beam ends, bound degenerate: 51.574073 kg determinate |
| B10 | FIX_ROW | 5 | FR-T647-1 .. 5: CN columns, ST p.9 schedule CN GF / 1F / 2F struck (own re-read AGREE T-075): NOT_APPLICABLE |
| B10 | DESIGNER_ITEM | 4 | D-21 dome DOME-3; D-33 two loaded ground-beam runs; RFI-A02 pool steps |
| B10 | OWNER_DECISION | 4 | Q-65 C parapet material (+ D-39 edge build-up) |
| B9 | DESIGNER_ITEM | 7 | D-39 six 2F wall lines (roof datum); D-35 ANNEX_S below-ground block |
| B9 | PRINTED_VALUE_GAP | 6 | MAIN_S below-ground block (no thickness / bottom printed); 5 white-unit lines on released hosts (AAC face not selected) |
| B9 | DEPENDENCY | 19 | material lines whose host block line is HELD (host cause named) |

Census (trade x unit, unchanged): B11 kg 138 bounded 701.958 .. 1,629.410; B10 m3 10 blank + 3 bounded 1.134 .. 3.483;
B9 32 blank. If the 22 fix rows are wired: B11 bounded 138 -> 121, +51.574073 kg released (0.051574 t); B10 5 lines
leave as NOT_APPLICABLE (no value; bounded 1.134 .. 3.483 m3 leaves the HELD census). Freelancer: 0 CN columns (agree);
slab bar ends sit inside his single 5,400 kg slab lump (no line comparison).

## Findings and lessons

- F-T647-1: 17 slab development part lines carry low == high (count A and B reach the same edge-beam ends) yet are
  booked BOUNDED_EXPOSURE by R-T318-1: a degenerate bound is a determinate value. Proposal for lane I: wire as
  DRAWING-CONFIRMED values (FR-T647-6 .. 22).
- F-T647-2: 5 CN column lines HELD as TYPE_NOT_IN_SCHEDULE since the frozen reader; the schedule prints the member as
  absent above ground (T-075 merged 2026-10-19, never wired).
- Lesson (ERS s.7 proposal): "A bound whose two readings coincide on the line is not a hold: test low == high before
  booking BOUNDED_EXPOSURE, and re-check old TYPE_NOT_IN_SCHEDULE holds against merged schedule readers." Scope every
  villa; provenance T-318, T-075, this task.
