# S6 Phase 1: independent engineering review, executive summary

**Scope**
- Reviewed: commit `c757d8a` (S6 Phase 1, `ARCH_TAKEOFF_V2`) against the S5 baseline `6eba0d2`; the S6 pre-change review is `6b7a2e4`.
- Nothing in production code, owner rules, frozen outputs or repository visibility was changed.
- Every experiment ran on a scratch export of the committed source.
- The human benchmark was not opened.

## Findings

1. **Phase 1 delivered what it promised on admission.**
   - 31 synthetic failure modes; HEAD V1 is silent on 22 of them. V2 and V1 strict are silent on none.
   - V1 stays byte-identical (15 / 16 files).
   - Full suite: 8443 tests, 0 code failures, every freeze green; gate INCOMPLETE.
2. **The metres / millimetres difference is not a units problem** (Investigation A).
   - The cause is one strict float comparison at a threshold equal to a common drafted length: `opening_census.face_lines`, `L < 100 mm`.
   - At a random rotation, a drafted 100 mm wall-face piece survives about **50 %** of the time, in mm **and** in m.
   - Canonical mm conversion, quantisation and integer geometry do not fix it; quantisation and integer geometry give 0 % at 45°.
   - A tolerance-aware predicate (ε = 1e-6 mm) fixes it in 100 % of 32 000 placements.
3. **The frozen millimetre result is wrong.**
   - The two "extra" openings Phase 1 rejected are a drafted door (with swing, leaf and frame) and a drafted window (four glazing lines). Both have jamb lines on the wall layer.
   - V1 misses them. So does the route-G / M4 lintel evidence on the same plan (GF 27 → 29).
   - Phase 1 rejected the correct fix because it changed old results. That was my mistake.
4. **The 85 new RFI lines are 4 questions and 14 engine defects** (Investigation B).
   - The 4 questions: one window schedule, the threshold rule Q-S6-1, Q7 with heights, Q-S6-4 with heights.
   - 23 lines overlap another line. **V2 adds no quantity**: 210 quantity lines in V1 and V2 alike.
   - The RFI count is the wrong progress metric.
5. **The completeness gate proves plan-area accountability, not completeness** (Investigation C).
   - **8 of 29 drawn door swings have no door line**, in V1 and V2 (state CLOSED or unresolved).
   - Plaster and paint have **zero** quantities while the gate says PASS.
   - Proposed: the no-silent-disappearance chain NSD-1..9, with **element conservation (NSD-2) first**.
6. **CAD robustness** (Investigation D). Four flagged reader defects (nested, MINSERT, layer-0 and SOLID fills) share one root: fills are read from model space only. One V2 parser change addresses all four. Also unread:
   - 388 DIMENSION entities, a free independent check;
   - 51 undecoded Arabic SHX texts, with no discovery finding.
7. **Freeze policy** (Investigation E).
   - Freezing by source bytes blocked behaviour-neutral fixes and forced parallel copies of shared code, yet says nothing about correctness.
   - Recommended: freeze by behaviour plus an append-only errata register.
   - V1 strict as the default; exit codes 2 and 3 stay separate.

## Recommendations

| # | Recommendation |
|---|---|
| 1 | **Must fix first:** robust predicates (P2-01); errata and behaviour manifests (P2-00); metamorphic tests at arbitrary angles (P2-02); stable ids (P2-03) |
| 2 | **Smallest high-value Phase 2 set:** P2-01 + door / window conservation (P2-04) + fills from K2 (P2-05) + RFI register by question, with engine findings out of the client channel (P2-06). About 8–10 days, all behind `ARCH_TAKEOFF_V2.1`, V1 unchanged |
| 3 | **Then:** strip-check refinement, eligible-surface ledger, dimension evidence, text normalisation, linetype semantics (P2-07..P2-11) |
| 4 | **Then the blind round** on two unseen villas from different drafters (P2-12), with metrics fixed in advance. No generalisation claim before it |
| 5 | **Stop:** new BOQ families, workbook polish, V1 work, ad-hoc RFI emitters |

## Responses to R1–R9

- **AGREE:** R2, R3, R4 (with a traceability condition), R6, R7, R8, R9.
- **PARTIALLY AGREE:** R1 (canonical geometry is not the fix for the unit difference) and R5 (admission before measurement must be followed by reconciliation after it).

## Decisions needed from the owner

O1 to O10 (file 11). The most urgent:
- freeze by behaviour plus errata (O1);
- accepting a corrected V2.1 that differs from V1 (O3);
- the wet-tile rule conflict (O5);
- the window schedule and sections (O8);
- two unseen villas (O10).

## Next milestone

**S6 Phase 2A "reliability core"** (P2-00..P2-06), with the go / no-go criteria in file 04. No accuracy percentage is claimed. Nothing is quotation-ready.
