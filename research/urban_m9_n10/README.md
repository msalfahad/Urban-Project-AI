# Phase N10: curved openings, masonry, facade, structural formwork and excavation, independent proof

**Methods.** **ARCH_TAKEOFF_V2.9** (opt-in; registry 1.5.0), plus the separate structural tool `tools/struct_n10.py`. V1 – V2.8 are unchanged byte for byte (`REGRESSION_AND_FROZEN_EVIDENCE.md`).

**Not claimed:**

- **Production freeze.** Nothing here is one.
- **Blind evaluation.** None was run.
- **Accuracy.** The 95 % target is **not achieved and not claimed**.

**Time.** About three hours of elapsed work, by the commit timestamps; not ten.

## Deliverables (program Part 14)

| # | Deliverable | Where |
|---|---|---|
| 1 | Executive summary | `EXECUTIVE_SUMMARY.md` |
| 2 | Baseline and gap audit | `BASELINE_AND_GAP_AUDIT.md` |
| 3 | Curved and topology defect report | `CURVED_AND_TOPOLOGY_DEFECT_REPORT.md` |
| 4 | Architectural report (masonry, facade) | `ARCHITECTURAL_REPORT.md` |
| 5 | Structural report (concrete, formwork, excavation, rebar audit) | `STRUCTURAL_REPORT.md` |
| 6 | Worked examples (27 rows, hand truth / design spec) | `WORKED_EXAMPLES.md` |
| 7 | Real-plan before / after (aggregates only) | `REAL_PLAN_BEFORE_AFTER.md` |
| 8 | Completeness matrix | `COMPLETENESS_MATRIX.md` |
| 9 | Defect register | `DEFECT_REGISTER.md` |
| 10 | Owner decisions register (OQ-06 – OQ-13) | `OWNER_DECISIONS_REGISTER.md` |
| 11 | Missing drawing evidence | `MISSING_DRAWING_EVIDENCE.md` |
| 12 | Independent verification report | `INDEPENDENT_VERIFICATION_REPORT.md` |
| 13 | Accuracy framework (proposal, unapproved) | `ACCURACY_FRAMEWORK.md` |
| 14 | Next-phase plan and resumable checkpoint | `NEXT_PHASE_PLAN.md` |
| 15 | Changed source files | ZIP `source/` (full files at the final code commit; `engine/source/arch_rooms.py` and `tools/routing_topics.json` as diffs in the patch only, see `CHANGED_FILES.md`) |
| 16 | New tests | ZIP `tests/m9_n10/`; in the repository at `tests/m9_n10/` |
| 17 | Fixtures | `tests/m9_n10/n10_fixtures.py` (synthetic DXF builders) and `n10_truth.py` (hand truth) |
| 18 | Test commands | `TEST_COMMANDS.md` |
| 19 | Frozen integrity evidence | `REGRESSION_AND_FROZEN_EVIDENCE.md` |
| 20 | Full-suite comparison | `FULL_SUITE_COMPARISON.md` |
| 21 | Changed-file manifest | `CHANGED_FILES.md` §2 |
| 22 | Commit ids | `CHANGED_FILES.md` §1 |
| 23 | Patch | ZIP `patch/n10_504b56a_4b299ae.patch` |
| 24 | README | this file |
| 25 | SHA-256 manifest | ZIP `SHA256SUMS.txt` |
| 26 | Archive checksum | `<zip>.sha256`, delivered beside the ZIP |
| 27 | Privacy scan | ZIP `PRIVACY_SCAN.txt` |
| 28 | Fresh extraction check | ZIP `EXTRACTION_CHECK.txt` (re-extracted, manifest re-verified, tests run from the extracted copy) |
| — | Brief for ChatGPT (what worked, what did not, recommendations) | `CHATGPT_BRIEF.md` |

## Reading order

1. `EXECUTIVE_SUMMARY.md`
2. `CHATGPT_BRIEF.md`
3. `DEFECT_REGISTER.md`
4. `COMPLETENESS_MATRIX.md`
5. the reports
6. `WORKED_EXAMPLES.md` for the numbers

Every important number is laid out as: **drawing evidence → rule → formula → hand calculation → engine result → difference → status → provenance**.

## Privacy

- No private drawing, private path, client identifier, room id or private layer name appears in this folder or in the ZIP.
- Real-plan results are aggregates.
- The generated maps under `docs/` carry pre-existing identifiers and are not in the ZIP or the patch. N10 added none (`CHANGED_FILES.md` §3).
