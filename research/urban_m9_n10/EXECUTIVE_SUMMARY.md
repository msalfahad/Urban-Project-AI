# Executive summary (Phase N10)

**Scope.** The work extends the Kuwait villa BOQ / QTO engine. Prices and Urban Projects Manager integration are excluded.

**Time.** The program allowed ten hours. The commit timestamps show about **3.5 hours** of elapsed work (19:55 → about 23:30 UTC):

- baseline 504b56a at 19:55 UTC;
- last engine change 9a52c34 at 22:13 UTC;
- final code commit 24db651 at 22:56 UTC: a test-side declaration that fixes the one regression the first full suite found (D-N10-05);
- deliverables, the second full suite (on 24db651) and the handoff ZIP after that, until about 23:30 UTC.

**This is not a ten-hour result.** The resumable checkpoint is in `NEXT_PHASE_PLAN.md`.

**Accuracy.** The 95 % accuracy target is **not achieved and not claimed**:

- every new rule is REQUIRES_CONFIRMATION;
- no blind evaluation was run;
- only one real villa exists.

## 1. What was implemented

All new behaviour is opt-in. V1 – V2.8 are byte-identical (2,170 files, 0 differ).

| Work | Where | Result |
|---|---|---|
| **ARCH_TAKEOFF_V2.9: curved openings** (D-P9-01, D-P9-02) | `engine/source/arch_v29.py`, `arch_rooms.py` | a jambed gap in a curved wall is an opening closed on both wall faces; the room ends at its own face; curved glazing on an unassigned layer is inferred under three guards |
| **V2.9: masonry by thickness** (UP-MAS-HEIGHT-001) | `arch_v29.py`, `tools/urban_boq_m9.py` | panel area and volume per thickness from the floor's section T.O.S. → U/S SLAB; beams → a range or held at the upper bound; material separate (MAS.BLOCK) |
| **V2.9: facade** (UP-FACADE-001) | same | exterior outline run per floor; area F.F.L. → next F.F.L. net of openings by their own bands; exterior finish only with a stated spec |
| **Structural N10** (UP-FW-001, UP-EXC-001) | `engine/source/struct_n10.py`, `tools/struct_n10.py` | formwork faces per element (MEASURED / CONDITIONAL / UPPER_BOUND / HELD); excavation footprints, volume only with stated levels; rebar audit (d²/162 vs 7,850 kg/m³: +0.12 %; 0 ratio-as-measured) |
| **Independent verification** | `tools/indep_reader.py`, `tools/arch_change_verify.py` | curved gaps, joined rooms, zone-bounded faces, opening counts, the facade outline |
| **Registry 1.5.0** | `knowledge/…1.5.0.json`, `tools/kb_build_1_5.py` | 5 new rules (all REQUIRES_CONFIRMATION) and owner questions OQ-06 – OQ-13 |
| **Baseline fix** | `tools/routing_topics.json`, `tools/codemap.py` | the one new baseline failure (session guard) fixed |

## 2. Real villa set: V2.8 → V2.9 (aggregates)

On the reference plan, Mode A, lines went from 487 to 517:

- **One curved window** is now an opening: windows 26 → 27.
- **The room behind it is measured on its own face.**
  - Plaster and paint each gain **57.9478 m²** of certain quantity, previously a range.
  - The independent reader agrees to within 0.00001 m².
- **Facade run** is measured on all 3 floors: 191.8556 m, PROVISIONAL.
  - Each floor also has a thin second outline, raised as an RFI and never added.
  - 2F verified exactly; 1F contradicted by +0.16 m (defect D-N10-01, reported, not tuned away); GF not established.
- **Masonry, facade area and exterior finish are held** on the real plans. The drawings do not bind section levels to floors, and nothing was defaulted.
- The villa and its mirror both gain a facade run of 78.40 m and agree exactly.

## 3. Synthetic and independent results

- **Proofs:** 27 of 27 worked-example rows pass against hand truth or the synthetic villa's design spec (`WORKED_EXAMPLES.md`).
- **Verifier on the reference plan:**

| Comparison | VERIFIED | EXPLAINED_UNVERIFIED | CONTRADICTED | UNEXPLAINED |
|---|---|---|---|---|
| V2.6 → V2.7.1 | 45 (was 32) | 10 | 0 | 0 |
| V2.8 → V2.9 | 5 | 14 | 1 | 0 |

- **Tests:** 70 new tests in `tests/m9_n10`, all passing.

## 4. What remains wrong or missing

1. **D-N10-01:** the facade run walks the recess of an undetected window, giving +0.16 m on one floor.
2. **D-N10-02:** the reader cannot close glazed gaps over 2.60 m, so one floor's outline is not independently checked.
3. **D-N10-03:** masonry has no independent reading.
4. **D-N10-04:** column formwork is an upper bound, because beam-column adjacency is not in the register.
5. **The real plans carry no bound section levels,** so masonry and facade areas stay held there.
6. **Formwork and excavation are not yet BOQ workbook lines;** they are separate files.
7. **Roofs, balconies and external works are unsupported.**
8. **The full suite is not green:** the known legacy failures remain. See `FULL_SUITE_COMPARISON.md`.
9. **A regression slipped past the targeted tests (D-N10-05, fixed).** The first full suite at 4b299ae found one pass → fail: the new structural module was not declared in the rebar product firewall. It was fixed in 24db651, and the full suite ran again.

## 5. Readiness

| Level | N10 items |
|---|---|
| EXPERIMENTAL | formwork, excavation, rebar audit |
| INTERNALLY VALIDATED | curved openings; facade run (one real floor verified) |
| READY FOR BLIND | none |
| PRODUCTION | none (not authorised) |

## 6. Next

Ranked in `NEXT_PHASE_PLAN.md`:

1. Bind section bands to plan floors on the real plan.
2. Obtain the owner's answers to OQ-06 – OQ-13.
3. Fix D-N10-01 and D-N10-02.
4. Bring formwork and excavation into the workbook.
