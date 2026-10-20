# T-131: ARCH_TAKEOFF_V3.0, the one opt-in BOQ candidate (skeleton)

Worker 3 (lane I, integration), 2026-10-20. Development reference, not an accuracy claim. Not the released default
(owner management decision 2026-10-20 section 2); rollback = run the released ARCH_TAKEOFF_V2.9.

## What V3.0 is

`tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V3.0 [--structural S.dxf --conventions C.json] [--v30-decisions D.json]
[--v30-released V29/BOQ_LINES.json]`

1. The run is ARCH_TAKEOFF_V2.13 exactly, plus route G when a structural drawing is given. Its own outputs are written
   unchanged (on the development villa every one of the V2.13 run's files is byte-identical to a plain V2.13 run's).
2. Read-only captures (`engine/source/arch_v30.py` `capture()`) keep what each plan region's room builder saw and the
   arrangement of its facade outline.
3. Each integrated piece proposes changes of named BOQ lines; `integrate()` copies every other line unchanged (test
   asserted: `unchanged == unchanged_identical`, with the sha256 of the unchanged set in `V3_0_RUN.json`).
4. Files beside the base outputs: `V3_0_BOQ_LINES.json/.csv` (the candidate BOQ), `V3_0_INTEGRATION_LEDGER.json/.csv`
   (per changed line: V2.9 before, V2.13 before, V3.0 after, delta, drawing reference, owner manual method,
   drawing-derived method, verification evidence, held items, downstream lines, rollback), `V3_0_DOWNSTREAM.json`,
   `V3_0_RUN.json`.

`ARCH_METHODS` is unchanged (V2.13 stays its last entry): V3.0 is a `CANDIDATE_METHODS` entry of the CLI only, and
`arch_compute(method="ARCH_TAKEOFF_V3.0")` is refused, so no earlier method or check can reach it.

## Pieces integrated (each with a verifier MERGED verdict)

| Piece | Module | Task / merge / verifier | What V3.0 does with it |
|---|---|---|---|
| Straps | PLOT_EDGE_MEMBERS_V1 | T-073, c874c7b, run 33 | route G strap bands bound by their face handles and schedule row; footing outlines read on the strap layers (open outlines found); clear length x printed section replaces the band volume; the part inside an OPEN footing outline is its own BOUNDED_EXPOSURE line [0, L x W x H] (Q-31) |
| Open-air passage walls | FACADE_PASSAGE_WALLS_V1 | T-109, 4fddf74, 16:49 run; condition T-123, 6699bb6, run 45 | facade run = walked - mouths + the passage's building faces; a single-mouth passage whose roof the plan does not settle stays a range unless a project decision binds owner Q-67 A with its condition check; geometric and billable run in separate fields (Q-64 B) |
| Stair floor residue | STAIR_FLOOR_RESIDUE_V1 | T-116, 5592692, 16:49 run | a face a stair passes through gets its floor net of the tread union, opening and well; unsettled pieces make it a BOUNDED_EXPOSURE range, never one value |
| Membrane V2.13 | arch_v213 | T-120, 2264938, run 44 | as in the base run (listed in the ledger with V2.9 before: V2.9 has no roll lines) |

## Development villa (Drive "Alsenan chalet project": P7757_DXF_COMPRESSED.zip sha256 ab54dd55..., "ST7757 dxf.dxf" sha256 9f9d1179...)

Base 1528 lines (579 architectural + 949 route G); candidate 1530 = 1519 unchanged (identical) + 9 replaced + 2 added.

| Line (unit) | V2.9 released | V2.13 base | V3.0 candidate | Freelancer | Verdict basis |
|---|---|---|---|---|---|
| Strap SB3 (m3) | 0.654 | 0.654 | 0.652 (clear 3.258 m x 0.50 x 0.40) | | T-073 hand 0.650 |
| Strap SB1 (m3) | 1.995 | 1.995 | 1.593 (clear 4.55 m x 0.70 x 0.50) + HELD 0 .. 0.403 inside the open F10 + F outline | | T-073 hand 1.593, 1.15 m held |
| Strap SB2 (m3) | 1.132 PROVISIONAL | 1.132 | 1.146 (clear 2.293 m at the printed 1.00 x 0.50) + HELD 0 .. 1.406 inside the open F11 / F3 outlines | | T-073 hand 1.147 |
| **Straps (m3)** | **3.781** | **3.781** | **3.390** measured + 0 .. 1.809 held | 3.3925 | -0.07 % vs freelancer (was +11.5 %) |
| GF facade run (lm) | 98.887 | 98.887 | 105.887 (Q-67 A bound; geometric = billable, the 0.100 m notch returns are in no reveal line) | no run row | T-123 hand 105.887 HAND_RIGHT |
| GF facade run without the decision (lm) | | | 98.887 .. 105.887 BOUNDED_EXPOSURE | | |
| GF passages OP-001, OP-007 (pcs) | 1 + 1 | 1 + 1 | NOT_APPLICABLE_WITH_EVIDENCE (not building openings) | | T-109 |
| 1F living porcelain (m2) | 44.869 | 44.869 | 38.459 .. 38.979 BOUNDED_EXPOSURE | 38.96 (inside the range) | T-113 hand 38.588 .. 38.990 |
| Membrane rolls (nr) | no roll lines | wet 21, roofs 17 / 6 / 8 | as V2.13 | | T-114 / verifier run 44 |

Downstream (listed in `V3_0_DOWNSTREAM.json`, nothing recomputed that no verified piece covers): the GF facade area and
plinth lines take the new run as input (still no quantity until a facade height is printed, Q-07); the strap rebar
lines read the old clear spans (rebar stays its own family, unchanged, listed); the 1F living tile material result was
computed from 44.869 m2 (STALE until the range settles); the doorway strips at OP-001 / OP-007 (porcelain 0.28 +
0.24 m2, a threshold) sit at mouths that are no building openings: flagged for review, unchanged.

## Not done / waiting

- T-122 (1F porcelain / landing marble under Q-66 B), T-124 (MEMBRANE_FOLD_V5 offcut-once, verified), T-126 (blinding
  scope, undrawn columns) join as V3.0.x extensions of this candidate.
- The passage piece does not read the roof slab (structural sheet); on this villa the roof does not change the run
  because Q-67 A binds it, on another villa without a decision the run is a range.
- Q-64 B return faces are not identified by the engine: billable = geometric, listed as held.
- The strap footing outlines are read on the whole drawing's strap layers (only outlines the strap crosses matter).
- Checker: re-run `tools/alsenan_scoreboard.py` on V3.0 and V2.9 and re-measure 3 changed lines by hand.

Reproduce: `python3 -I research/agents_t131/alsenan_v30_run.py <plan.dxf> <structural.dxf> --out <scratch>/t131`.
