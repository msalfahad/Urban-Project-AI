# TEST_RUN: source recovery delta (S4 / S5 / S6)

## Targeted

```
python3 -m pytest -q -p no:cacheprovider tests/source_recovery_delta \
    tests/structural_comparison_engine/test_rebar_product_firewall.py \
    tests/footing_rebar_s4/test_alsenan_s4_package.py::test_freeze_manifest_still_matches \
    tests/ground_system_rebar_s5/test_alsenan_s5_package.py::test_freeze_manifest_still_matches \
    tests/superstructure_beam_rebar_s6/test_alsenan_s6_package.py::test_freeze_manifest_still_matches
```

Result: **53 passed** (20 new, 30 firewall, 3 freeze-manifest checks).

What `tests/source_recovery_delta/test_source_recovery_delta.py` (20 tests) covers:
- **Package and freeze:**
  - every deliverable exists;
  - the frozen S4 / S5 / S6 code, inputs and outputs still hash to their manifests, and the summary records each manifest sha and engine stamp;
  - `kg_recalculated` and `s7_started` are false.
- **Claim:** the engineer claim is versioned and does not authorise assumptions; the workflow text is recorded.
- **Register:**
  - exactly one of the six terminal states per item, in exactly one per-stage file;
  - the counts match the summary.
- **Engineer routing:**
  - F / F10 is `PENDING_ENGINEER_CLARIFICATION`;
  - SB2 stays a `SOURCE_CONFLICT`, carrying the new issued-sheet evidence;
  - no candidate touches a conflict;
  - every conflict or pending item reaches `10_PENDING_ENGINEER_CONFLICTS.csv`, including all nine conflicting occurrences (R2, R3, R5);
  - `11_SOURCE_EXPECTED_NOT_LOCATED.csv` mirrors the register.
- **No quantities:**
  - no kg column and `KG_RECALCULATED = NO` everywhere;
  - candidates carry all the brief's §8 columns, are never VERIFIED, and unlock only from a found source;
  - T/M stays a design load and appears in no candidate.
- **Graph:** the connection graph covers every item; FOLLOW ARCH reaches the architectural set.
- **Evidence:** every evidence id cited exists, and every new derived item rests on a DXF or PDF-vector fact. The tests check these facts:
  - footing U / inverted-U bars and their leaders;
  - four single-link GB sections, with the 30x30 link unlabelled;
  - lift 2 + 2 Ø16 bars in each cut wall, and four plan walls;
  - six CB end legs reaching the bottom-bar level, and the N.T.S. ratios;
  - STR2 / str3 rows;
  - SB2 rows against the sheet frame;
  - WITH STAIR = B3.
- **Builder:**
  - blind: no reference, comparison, donor or benchmark strings;
  - no `fitz`, PyMuPDF or `pdf_vector_evidence` import;
  - registered as an accurate-side builder;
  - the rebuild is byte-identical.

## Full suite at `5184c63`

`python3 -m pytest -o addopts="" -q -p no:cacheprovider` gave
**6621 passed, 4 skipped, 100 xfailed, 2 warnings in 386.96 s, exit 0**.
- That is S6's 6601 plus the 20 new source-recovery tests.
- The run used the clean committed tree, and no file was edited during it.
- The S4, S5 and S6 freeze-manifest tests all still match.
