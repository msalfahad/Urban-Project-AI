# P2-00 Stage 2: proposed diff, for review only (NOT applied)

**Status: a proposal.** Nothing in this file has been applied to the repository.
- `engine/source/opening_census.py` is unchanged.
- No historical source pin, frozen manifest, frozen output or historical test has been relaxed or edited.
- Owner decision D2 applies: no change until Stage 1 has proven legacy behaviour is preserved, and the diff below has been reviewed.

## Recommendation: Stage 2 needs no change to any pinned file

Stage 2 was proposed so that the Phase 2A robust predicate (P2-01) could be added to `opening_census.py` without a parallel copy. The evidence now shows that this edit is not needed.

**1. Each of the three thresholds is used in exactly one strict comparison** (`engine/source/opening_census.py` at `c757d8a`):

| Function | Line | Comparison |
|---|---|---|
| `face_lines` | 95 | `if L < min_len: continue` |
| `wall_bands` | 143 | `if hi - lo < min_overlap: continue` |
| `band_gaps` | 217 | `if g < min_gap: continue` |

The V2 copy, `opening_gaps.band_gaps` (line 31), has the same single comparison. That module is not pinned by any freeze.

**2. Passing a lowered threshold gives the robust rule exactly.** Calling the frozen function with the threshold `T - m` keeps a value if and only if `value >= T - m`, which is the robust "at least T, within the margin" rule.
- `stage2_threshold_shift_check.py` (synthetic, read-only) checks this at all three sites.
- Coverage: mm and m drawings, rotations 0 / 90 / 30 / 45 deg, site offsets up to 10 km, drafted deltas from -1e-2 to +1e-3 mm.
- Result: **648 of 648 checks agree.**
- The round-2 Q1 threshold-site experiment already used this route and kept 100 % of drafted-exact values at every grid angle.

**3. Therefore Phase 2A P2-01 can be delivered entirely in unpinned callers**, opt-in under `ARCH_TAKEOFF_V2.1`:
- **The callers:** `arch_plan._bands`, the V2.1 branch of `lintel_measure.openings`, and `opening_gaps`.
- **What each caller does:** computes `m = max(1e-6 mm, 16 u M (d + 1))` from its own inputs, passes `T - m` to the frozen functions, and writes the AT_THRESHOLD records itself.
- **What does not change:**
  - no edit to `opening_census.py` and no parallel copy of it;
  - no relaxed source pin and no historical test change;
  - none of the 37 freeze manifests.
- **What still needs new code:** the mean-axis projection (P2-01b) is a different algorithm. It belongs in a new V2.1 function in a new module. The frozen `face_lines` stays the implementation for V1, V2 and S8.6. This is not a copy that must be kept equal: it is the new method, and it is versioned as such.

**Proposed Stage 2 diff to pinned files: none (0 lines).**

**4. Stage 1 then remains the protection.**
- The out-of-tree verifier shows every freeze is byte-identical after each Phase 2A change.
- The baseline index guard shows no frozen artefact was rewritten.
- Behaviour, not source digests, is the authority. This matters because the source pins do not cover the full import closure (finding F-5): a change to an unpinned module on a freeze's computation path is caught only by a rebuild.

## Alternative, if the owner prefers explicit predicates in the pinned file (not recommended)

`PROPOSED_STAGE2_ALTERNATIVE.diff` (17 changed lines, sha256 `05faf7f10f6e3a5f…`) is the exact diff.
- It adds keyword-only arguments `keep_length=`, `keep_overlap=` and `keep_gap=` to `face_lines`, `wall_bands` and `band_gaps`.
- The default `None` keeps the frozen comparison expression unchanged.

Its dry run in a disposable worktree, with the code pin re-pinned in the worktree only, is reported in `STAGE1_REPORT.md` (run S2-DRY).

**Its cost.** Any byte change to `opening_census.py` breaks the S8.6 code pin:
- 11 tests in 9 frozen packages fail (round 2, Q5 E6);
- the downstream rebuilds are refused by their builders' own pin checks (run MT-1b).

Landing it would therefore need one of the following, all worse than the recommendation:

| Option | What it requires | Problem |
|---|---|---|
| (a) | edit the S8.6 freeze manifest's code map | forbidden: frozen manifests are immutable (owner requirement 1) |
| (b) | re-point the pin-checking historical tests, and the downstream rebuild tests, to an errata-aware verification | edits about 20 historical test functions in about 12 files |
| (c) | change `engine/source/delta_release.verify_frozen` | pinned by 25 manifests; widens the problem |
