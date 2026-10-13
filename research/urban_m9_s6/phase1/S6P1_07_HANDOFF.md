# S6 Phase 1: handoff (what worked, what did not, what to do next)

## What worked

**Silent failures removed.** On the 31 synthetic drawing variants, HEAD V1 has 22 silent failures. V2 and V1 `--strict-admission` have **none**:
- every unmeasurable drawing stops with exit 2 and a named reason;
- every reader limitation that changes a quantity is a REVIEW flag on the room it affects.

**DWG admission.** Empty, stale, garbage and same-name conversions are all blocked or kept apart, tested with a fake converter only:
- hash-named outputs;
- the stale target is removed;
- an earlier BOQ is moved to `SUPERSEDED_<n>`.

**Units.**
- Unit-relative tolerances: the villa measures the same in mm, cm, m and inches.
- On the reference plan rescaled to metres, V2 matches mm except one 0.20 m wall run (see "What did not work"). HEAD V1 silently lost 44 % of the lines.
- An undeclared or contradicted unit stops; `--units` is recorded.

**Plan regions.**
- Two plans in one frame are split along empty bands, never through geometry.
- Frames drawn as lines are read.
- The sheet frame's own sides are dropped. A frame drawn on the wall layer used to become the floor plate: 780 m² on the synthetic villa.

**Completeness.**
- Every face part and every room × {floor, ceiling, walls, skirting} has a LINE, RFI or EXCLUDED (with its reason). The gate passes on every floor of the synthetic villa and of the reference plan.
- Strips are reviewed individually:
  - thresholds;
  - window reveals (verified by geometry and glazing, never counted as floor or excluded);
  - unattributed strips, with `failed_checks`.
- The stair-hall walls and skirting, the band above partial wet tile, and the exterior scope get BLOCKED_RFI lines or records. No quantity and no material is assumed.

**V1 and route G untouched.**
- V1 is byte-identical: synthetic 15/15 files, reference 16/16.
- V1 strict adds only `DRAWING_DISCOVERY.json`.
- Route G, the rules and the M2–M8 freezes are unchanged. The full suite is green on every freeze test.

## What did not work, or is not done

**Readers not fixed (Phase 2).** Nested or MINSERT hatches, SOLID fills, layer-0 inheritance, rotated or exploded columns, fewer than three columns, non-uniform door blocks, Arabic diacritics and layer state. The quantities still differ; they are flagged, not silent.

**Threshold float fragility (S6P1-NEW-05).**
- What happens: a drafted 100 mm face piece, a 300 mm overlap, or a 0.4 / 0.5 m gap sitting exactly at its threshold is dropped once float rounding puts it 1e-14 below.
- Effect on the reference plan in metres: one GF wall run is 0.20 m short, and 0.07 m² moves between wall mass and doorway strips.
- A 1e-9 relative slack fixes it, but it also adds two openings to the **mm** reference plan. That breaks "mm unchanged", so it was reverted.
- A strict-xfail test records it.

**Strip geometry check.** A number of real door and passage strips fail the opening-box check: set-back thresholds, a face spanning two openings, a passage cut by zone lines. They are UNATTRIBUTED RFIs. A refined check is Phase 2.

**Freezes block shared-module fixes.**
- `opening_census.py` (the S8.6 lintel digest) and `urban_intake.py` (the M7/M8 freezes) cannot change, even neutrally.
- Phase 1 used a parallel module and a second K2 kernel run instead.
- The first full-suite run, with those files edited, rewrote frozen S8.6 / S8.6A / S8.8 research outputs. They were restored with `git checkout`; nothing from that run is committed.

**Discovery stages not implemented.** Stage 3 (drawing identity, title block, revision) and stage 8 (feature census) are `NOT_RUN`.

**Paper space.** A plan shown only through a paper-space viewport stops (or needs `--region`). Reading viewports is Phase 3.

## Recommended next steps

1. **Owner decisions** (in this order, each unblocks Phase 2 work):
   1. Freeze by behaviour (frozen-run output hashes) instead of source bytes, or approve a per-freeze post-change list. This is needed for the reader fixes in `urban_intake.py` and `drawing_model.py`.
   2. Review the two extra openings the threshold slack finds on the reference plan. If they are real, adopt the slack in V2.
   3. Make `--strict-admission` the V1 default.
   4. Allow a warning-only change in `urban_boq_m2.py` / `urban_project_run.py` for the structural defaults.
   5. The surface-eligibility table per space kind.
   6. The opening-deduction threshold (UP-CER-009).
   7. Q-S6-1 thresholds, Q-S6-4 stair hall, Q7 the band above tile, Q1 exterior.
2. **Phase 2, after Phase 1 is accepted.** Reader fixes, one per flag, each proven by its synthetic variant moving from FLAGGED to NOT_REPRODUCED, with the V1 byte tests kept:
   - nested, MINSERT and SOLID hatch reading;
   - layer-0 inheritance;
   - rotated and exploded column outlines and the at-least-three-columns rule;
   - door-swing reading for scaled blocks;
   - diacritic normalisation;
   - the refined strip check.
3. **Phase 3.** Paper-space viewports, rotated sheets, and a second real villa as a blind round.
