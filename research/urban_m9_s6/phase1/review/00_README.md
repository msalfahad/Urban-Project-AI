# M9 S6 Phase 1: independent engineering review (public-safe notes)

Reviewed commit: `c757d8a`. S5 baseline: `6eba0d2`. S6 pre-change review: `6b7a2e4`.

**No production code, owner rule, frozen output or repository setting was changed.** Every experiment ran on a scratch export of the committed source. The human benchmark was not opened.

These notes carry no drawing identity, no client figure beyond engine counts, and no benchmark value. The reference-plan evidence (per-record RFI audit, crops, outputs, hashes) is in the PRIVATE archive, which is never committed.

## Read first

1. `01_EXECUTIVE_SUMMARY.md`
2. `05_INVESTIGATION_A_UNITS_AND_FLOAT.md`. Metres vs mm: one strict float comparison at a drafted threshold. The frozen mm result misses a drafted door and window.
3. `06_INVESTIGATION_B_RFI_AUDIT.md`. The 85 added RFI lines are 4 questions and 14 engine defects.
4. `07_INVESTIGATION_C_COMPLETENESS.md`. The gate proves plan-area accountability. 8 of 29 drawn doors have no door line.
5. `04_PHASE2_PLAN_RANKED.md`: the plan only, not implemented.
6. `03_RESPONSES_R1_R9.md`, `02_INDEPENDENT_ASSESSMENT.md`, `08_*`, `09_*`, `10_*`, `11_*`.

## The review package (outside the repository)

| Archive | Bytes | SHA-256 |
|---|---|---|
| `URBAN_M9_S6_PHASE1_INDEPENDENT_REVIEW.zip` (public-safe: these notes plus source, diffs, tests, fixtures, scripts, synthetic evidence; `18_ALL_IN_ONE.md` for single-file readers) | 723,176 | `071222e2daf6734877e430c0e459cdb21aa45a458678621d018de38f25aefc49` |
| `URBAN_M9_S6_PHASE1_INDEPENDENT_REVIEW_PRIVATE.zip` (`PRIVATE_DO_NOT_COMMIT/`: reference-plan evidence) | 607,151 | `19c914e0d18c4e66be7f3ecdcf941b111b7916c458f99436f97c0a498c0a7403` |

Each archive carries its own `SHA256SUMS.txt`. The builder is `scripts/build_review_zip.py REPO SCRATCH OUT_DIR c757d8a`; its entry timestamps are fixed, so a rebuild from the same inputs reproduces the archive bytes.

## Here

- `fixtures_investigation_A/`: a generator for the minimal DXF fixtures, the census evaluation, and the decision-procedure comparison, with their results. The DXFs regenerate with new header timestamps; the results are byte-stable.
- `scripts/`: the review harnesses (instrumented threshold probe, quantity diff, RFI audit, route-G lintel probe, package builder).
- `17_HASHES_V1_V2.json`: the frozen V1 outputs (synthetic villa, taken at `6b7a2e4`) against V1 now, 15 / 15 identical, plus the V2 output hashes. The reference-plan hashes (16 / 16 identical) are PRIVATE.
