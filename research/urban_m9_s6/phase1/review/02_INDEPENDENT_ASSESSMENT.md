# Independent assessment of S6 Phase 1 (commit c757d8a), including my own mistakes

## What Phase 1 got right (with evidence)

| Claim | Evidence |
|---|---|
| Silent admission failures removed | 31 synthetic variants through the production CLI: HEAD V1 has 22 silent results; V1 strict and V2 have 0. Every stop has a named reason and a remedy |
| DWG conversion made safe | empty / stale / garbage / same-name conversions blocked or kept apart (fake converter); hash-named outputs; earlier BOQ moved to `SUPERSEDED_<n>` |
| Merge tolerance made unit-relative | the synthetic villa measures the same in mm / cm / m / in; HEAD V1 lost 44 % of the lines on the reference plan in metres |
| Plan regions | two plans in one frame split along empty bands, never through geometry; frames drawn as lines read; the frame's own sides dropped |
| V1 and the freezes untouched | V1 byte-identical: synthetic 15 / 15 files, reference 16 / 16. Full suite: 8443 tests, 0 code failures, every freeze test green; gate INCOMPLETE |
| Previously silent surfaces made visible | 85 surfaces on the reference plan now have a line with their measured geometry (thresholds, reveals, stair-hall walls, the band above wet tile) |

## What Phase 1 got wrong: my mistakes

1. **I rejected a correct fix because it changed a frozen result.**
   - The threshold slack made metres equal millimetres. It was reverted because it "changed the mm result" by two openings.
   - Investigation A shows both openings are real: a drafted door and a drafted window.
   - The frozen millimetre result is the wrong one. I treated "unchanged" as "correct".
2. **I overstated the completeness gate.**
   - "Every surface is accounted for" is true for plan-area faces only.
   - 8 of 29 drawn door swings have no door line. Plaster and paint have zero quantities while the gate says PASS (Investigation C).
3. **I did not look at the door census I already had.**
   - `ARCH_PLAN.json` reported 7 doors CLOSED (GF 4, 1F 3) and 1 unresolved.
   - Phase 1 turned five of them into "threshold finish" RFIs, asking the owner about doors the engine never counted (Investigation B, S6R-B1).
4. **I sent engine defects to the client.** 14 of the 85 RFI lines are engine defects: set-back doors, a column-jambed open boundary, a zone-line sliver, the door the float defect drops. A client cannot answer them (S6R-B2).
5. **One RFI line per element, not per question.** 85 lines for 4 questions (S6R-B3). The RFI count rose and was easy to misread as progress.
6. **I emitted 16 "band above wet tile" RFIs without surfacing a rule conflict.**
   - The method register says wet-room tile runs full height, so there is no band.
   - The owner-approved UP-CER-009 says tile height is derived per face.
   - The two engine paths disagree, and the RFIs hide that (S6R-B4).
7. **The metamorphic coverage was too weak to find Investigation A.**
   - The harness rotated by 90° and translated by benign offsets: the one case where float thresholds behave.
   - At a random angle, a drafted 100 mm piece survives about 50 % of the time (S6R-A4).
8. **Process.** I edited files under other milestones' source digests during a full-suite run. The S8.6 double build rewrote frozen research files; they were restored with `git checkout`, and nothing from that run was committed. It should not have happened.
9. **Minor.** `gross_floor_plate_m2` reports the largest wall-network component only, without saying so (S6R-C5).

## Answers to the twelve questions

**1. Biggest architectural mistake.**
- *Measuring before modelling.* There is no explicit, conserved model of **elements** (doors, windows, columns) and **eligible surfaces** between the CAD reader and the BOQ lines.
- Each family's code decides for itself what exists, and conservation is checked only at the end, on 2D faces. That is how a door can be CLOSED without a line and every gate still passes.
- A close second: thresholds tested with raw float comparisons (Investigation A).

**2. Module to redesign first.**
- The **opening / wall-band census**: `opening_census.face_lines / wall_bands / band_gaps`, `lintel_measure.openings`, and the door-swing matching in `arch_rooms`.
- It is the common root of S6R-A1 (float drops), S6R-B1 (CLOSED doors), ENG-I1 / I2 (strip checks) and ENG-D3 (column rows read as passages).
- The redesign: an **element census** where a drawn door / window symbol is primary evidence, the wall gap confirms it, every threshold goes through a robust predicate, and every symbol is conserved.

**3. Most misleading test.**
- The coverage-gate PASS assertions on the reference plan (`tests/m9_s6/test_s6_real_plan.py`) and on the synthetic villa. They are true, and they read as "complete" when they mean "every face has a state".
- Runner-up: the V1 byte-identity tests, which prove "unchanged" and are easy to read as "correct".

**4. Freeze overengineering?**
- **The mechanism, yes. The intent, no.**
- Source-byte digests over shared modules (`opening_census.py`, `urban_intake.py`) block behaviour-neutral fixes and force parallel copies (`opening_gaps.py`, a second K2 run). They also say nothing about correctness.
- Freeze by behaviour (output hashes of pinned runs) plus an errata register keeps reproducibility and removes the duplication (Investigation E).

**5. Is the kernel the best foundation?**
- For entity placement, yes. K2 handles nesting, MINSERT cells, OCS, reflections and bulges, with characterised library limitations.
- The weakness is what bypasses it: fills read from model space only in `urban_intake`, texts through `disassemble`. There is also nothing above it: no element model.
- Keep K2, route every kind through it, and build the element layer on top.

**6. Most important missing discovery capability.**
- **Cross-checking the drawing against its own redundant information:**
  - dimension values (388 DIMENSION entities on the reference plan, unread);
  - door and window schedules;
  - printed areas;
  - the structural plan's columns.
- This is the only way to detect a self-consistent but wrong model (NSD-8).

**7. How to reduce review time.**
1. An RFI register by question (85 lines → 4 questions).
2. Engineering findings out of the client channel.
3. An SVG crop per question group, showing each affected element.
4. "What changed since the last revision" reviews (the revision-set sha is already on every line).
5. Rank review items by quantity at stake, so the reviewer checks the 10 % that moves the BOQ.

**8. What to stop developing.**
- New BOQ families.
- Owner-facing workbook formatting.
- More synthetic variants of cases already blocked.
- Any further work on V1.
- Ad-hoc per-surface RFI emitters, replaced by one eligibility table (NSD-6).

**9. What I would build differently as technical founder.**
- Start from the conserved ledger (entities → elements → surfaces → lines) with NSD invariants and metamorphic tests at arbitrary angles from day one.
- A tolerance-aware predicate library before the first threshold.
- Freeze by behaviour.
- Three drawing sets from three drafters before the tenth feature.
- Success measured by **silent omissions on unseen drawings**, not by line or test counts.

**10. A one-day experiment.**
- Run V2 on the reference plan and the synthetic villa under 12 metamorphic transforms: rotate 30° / 45° / 90°; translate to the origin and by +1e6; mirror; metres, cm, inches; explode blocks; nest 2 deep; re-order entities.
- Run each twice, with the frozen comparisons and with the robust predicate (scratch only).
- Count differences in element counts and category areas.
- This measures, in a day, how much of the engine's instability is S6R-A1, and whether the predicate alone removes it.

**11. Strongest disagreement with ChatGPT.**
- R1, if canonical geometry is offered as the fix for the metres / millimetres difference.
- It is not a units problem. It reproduces in millimetres, and it survives canonical conversion, quantisation and integer geometry (Investigation A.4).

**12. What evidence would reverse my recommendations.**
- **Robust predicate:** on an unseen villa it produces openings or wall runs that an independent reviewer rejects. Then the thresholds themselves are wrong, and the fix is to move them off the drafted modules, not to add tolerance.
- **Freeze by behaviour:** output bytes cannot be made portable across environments: S6-ENV-01, where Python 3.11 and 3.13 agree within 1e-9 in value but not in bytes, and canonical formatting does not fix it. Then source digests stay.
- **Q7:** the owner confirms full-height wall tile in wet rooms. Then the RFIs are unnecessary, and the method register, not UP-CER-009, governs.
- **Door conservation (NSD-2):** CLOSED doors are counted elsewhere by design, for example from a door schedule. Then NSD-2 drops in priority.
- **V1 strict default:** the blind round shows admission blocking a large share of ordinary client drawings with no reviewer remedy. Then the stage-4 unit rules need a softer path.
