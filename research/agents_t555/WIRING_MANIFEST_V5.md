# T-555 WIRING MANIFEST V5 on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate, backlog-permitted), 2026-11-06, engine base 47d74505. Not an integration package:
nothing is wired; no candidate, released (V2.9 + route G), rule, knowledge or registry file is touched. Files:
`manifest_v5.py` (builder; V4 / V3 / V2 / V1 builders and the T-544 / T-523 / T-546 functions imported read only),
`WIRING_MANIFEST_V5.json`, `tests/t555_wiring_manifest_v5/` (20 tests). Rebuild: `python3 -I
research/agents_t555/manifest_v5.py` (`--check`; `--stage` checks the T-498 stage glue line ids at e3e2ebb5 when
fetched: PASS this run, 5 / 5). Inputs are committed, numbers-only outputs (sha256 in `inputs`); no drawing read.

## 1. Coverage (R-T549-1, V4's own function)

Range (V4 base 3f3b580c, V5 base 47d74505] on the first-parent line: 7 merges, all covered: T-544 2dbfaf95, T-549
f91e917f, T-546 a615fa41, T-545 e533bc87, T-554 82136421, T-552 0106dbfb, T-547 47d74505. NO_WIRING: T-545, T-546,
T-547, T-554 (reconciliations / statement) and T-549 (V4 itself). Sources: T-544 and T-552. V4 is pinned by sha256.

## 2. Expectations that change V4 -> V5 (candidate lines moved: 0)

| item (line) | V4 expectation | V5 expectation | cause / owning package |
|---|---|---|---|
| 1F AAC glue host L-2fdc0f97 (stage L-4b9a29d4) | HELD blank, AT_MOST 451.60893 kg | **BOUNDED_EXPOSURE 437.88303 .. 451.60893 kg** = (101.976 - [4.66866, 1.61846]) x 4.5; 17.515321 .. 18.064357 bags | T-544 part 1 / T-498 step 5 |
| GF AAC host L-541cf721 (stage L-6989349a) | not stated (legacy 194.02875 .. 199.33875) | **190.94985 .. 199.33875 kg** (low end -3.0789 kg, no bound before) | T-544 part 2 / T-498 step 5 |
| 1F AAC host L-b7b4d784 (stage L-aa5532bb) | not stated (legacy 203.562 .. 210.762) | **199.944 .. 210.762 kg** (low end -3.618 kg) | T-544 part 2 / T-498 step 5 |
| 2F AAC host L-bbb82de2 (stage L-4ccc5dc2) | not stated | HELD by name (contract HELD, D-39); 63.82125 .. 71.62425 beside only | T-544 part 2 |
| AAC glue group (R-T523-1) | AT_LEAST 17.643906 .. 18.16227 (>= 18 .. 19), HELD | **AT_LEAST 34.891351 .. 36.226627 (>= 35 .. 37), HELD** (part 1 alone 35.159227 ..) | T-544 / T-498 step 7 |
| lintels W16 / W19 / W20 / W24 (L-53ef44d8, L-6057028f, L-6692d02c, L-40e8c259) | not stated (HELD) | HELD unchanged; concrete AT_MOST 0.1312 / 0.088 / 0.09948 / 0.2684 m3 beside | T-544 (D-45 existence) |
| 4 RELEASED dry FIN.PLASTER lines (GF-15, 1F-01, 1F-04, 2F-03) | not stated (217.2081 m2 released) | **HELD (BOUNDED) 261.77493 .. 269.32863 m2** (paint height -> slab underside) | T-552 ENGINE_WRONG / **no row** |
| 7 HELD dry FIN.PLASTER lines | not stated | HELD, T-552 corrected bounds beside | T-552 / no row |

Stale bindings: T-453 glue_kg / glue_bags on the 3 moved hosts (4 new vs V4: GF L-541cf721, 1F L-b7b4d784); 58 T-454 /
T-489 plaster bindings that read a paint-height net or bound (74 HELD-blank ones unchanged).

## 3. Reconciliation consistency (engine side = candidate V3.0.58)

T-545 beam 66.321054 m3 / 110 released, 27 HELD, 54 EXCLUDED; T-546 floor WP 85.57571 m2 (18), upturn 25.214585 m2 =
126.072925 lm at 0.20 (his 144.61 lm); T-547 wall tile 340.3038 m2 (12 + 6 HELD, bound 102.2085 .. 144.1735); T-552
plaster 580.5819 m2 (42 / 20 / 13); T-554 stair ENGINE_WRONG 1.4375 = the V4 MS1-LD landing part (T-502). All AGREE.

## 4. Findings

- **F-T555-1**: V4's 1F glue host and glue group are stale after T-544 (a package on V4 would hold a bounded host).
- **F-T555-2**: T-544 part 2 makes the staged glue ranges L-6989349a / L-aa5532bb stale; no manifest named them.
- **F-T555-3**: T-552's dry plaster ENGINE_WRONG (released 217.2081 m2 = the released paint 217.2081, same G1 height)
  has no owning wiring row; FIN.PAINT keeps G1, only FIN.PLASTER moves (T-423 r2 must not carry it). Lead to row it.

## 5. Packages

T-498: steps 5 / 7 per the table; T-509 and T-423 r2: no V5 change; T-363 / T-372 / T-513 / F package: no change.

## 6. Lessons row (proposed, ERS s.7)

| 2026-11-06 | a research piece re-bounded two hosts no manifest listed, and a Checker-confirmed ENGINE_WRONG had no wiring row |
a manifest carried only hosts an earlier manifest named; ENGINE_WRONG verdicts of reconciliations were not tracked as
wiring items | a manifest re-derives the host set from the merged piece (not from the previous manifest) and lists every
ENGINE_WRONG in its range with its owning row or NONE (every villa) | tests/t555_wiring_manifest_v5 | proposed |
