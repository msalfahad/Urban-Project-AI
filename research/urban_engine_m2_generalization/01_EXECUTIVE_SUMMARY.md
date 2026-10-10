# M2: from Alsenan-specific research to a reusable BOQ engine (executive summary)

**Status: PLANNING ESTIMATE ENGINE, NOT ENGINEERING-APPROVED. The gate stays INCOMPLETE. No prices.**

## What changed

Before M2, a structural BOQ came from one of three routes:
- **Route A** replayed the frozen Alsenan stage registers (S1 to S9A).
- **Route B** read footings and columns through a person-confirmed profile.
- **Route C** only made an inventory.

Nothing could measure beams, slabs, ground beams or bars on a drawing the project registry did not already know.

M2 adds **route G, a generic engine**. It reads any DXF:
- sheets and titles (EN / AR), units, schedules (attribute rows and drawn tables);
- footings, columns, beams (straight and curved, under both depth readings), slab panels, openings and the slab-on-grade;
- bar models from the schedules (diameter-aware hooks, closed links, laps and anchorage as named conventions; never a kg/m³ ratio).

It produces a BOQ with four categories:
- **VERIFIED**: never for a new project.
- **PROVISIONAL**: measured with stated, reversible assumptions.
- **UNRESOLVED**: insufficient source data; never in a total.
- **NOT DETECTED / COVERAGE RISK**: what the engine may have missed.

Outputs are Excel, PDF, source-coordinate overlays and full registers.

One command: `python3 -I tools/urban_boq_m2.py run --drawings NEW.dxf --out OUT [--profile P.json]`.

## Headline results (honest)

**Synthetic villas, independent truth.**
- The truth is computed from the design spec by `tools/synthetic_villa.py`, which imports no engine code.
- Four held-out sets were each run once on a frozen commit: 70 clean drawings, 60 with drafting defects and 40 with face gaps beyond any snap tolerance.
- Results:
  - every drawing processed end to end;
  - every quantity family within 1e-6 of truth;
  - footing, beam and slab-panel detection precision and recall 1.0;
  - no silent slab loss, even with face gaps beyond the snap tolerance.
- **Limit:** the generator and the engine share one author's drafting assumptions. This proves consistency and robustness to the listed defects. It does **not** prove accuracy on real drawings from other offices.

**The defect sets earned their place.** They found five real bugs that clean synthetic drawings never showed:
- intake keyed block-layer inheritance by hex handles, while the kernel uses decimal ids;
- any ELLIPSE crashed the intake;
- 1–2 mm gaps at junctions lost about 95% of slab panels;
- an Arabic "schedule of footings" title read as a foundation plan;
- columns bound to footing outlines and inflated the high bound.

All five are fixed, with regression tests.

**Alsenan (ST7757) through the generic route, with no frozen register**
- Six families are in generic scope: footings, columns, beams, ground beams, slabs and the ground slab.
  - Concrete: generic **263.4 m³** against the frozen replay's **287.4 m³** (−8.3%).
  - Steel: **19.74 t** against **22.96 t** (−14%).
- Beams come out at −2% and slabs at +5%. Every other difference has an evidenced cause:
  - footings: 4 have no outline (−24%);
  - columns: 35 occurrences have no schedule type (−13%);
  - ground beams: no exterior depths, and no bar model because the detail is only in the PDF;
  - ground slab: the generic route counts a 49 m² face with free-standing columns inside it, for which S8.1 holds no face, and an 8 m² stair-flight zone that S8.1 excluded (+32%).
- The frozen replay holds 43.2 m³ and 1.9 t outside generic scope: stairs, domes, lift, pool, tank, lintels, blinding and cantilevers. The generic BOQ lists those families in section C, either with their drawing evidence or as "no label found – confirm absent", never as a zero.

**M1's 89 bar-less components**, each listed with its generic state:
- 11 now carry a generic bar model (741 kg);
- 46 are explicitly MISSING_DATA (28 ground beams, 10 continuous-beam spans, 8 bands with no section);
- 6 are outside scope (lift);
- 26 could not be matched to a generic band, and are listed, not hidden.

**Ground-slab gap audit:** 19 of S8.1's 21 faces match a generic face, each within 0.001 m² (7.3 cm² at most).
- One is missed, and that miss is reported.
- One is misread as a beam strip (a width-mode flaw).
- The generic route adds the stair-flight zone S8.1 excluded, and a 49 m² face with free-standing columns inside it.

## Is it 95% accurate?

**No such claim is made.**
- On synthetic villas the error is essentially zero, but those drawings share the generator's drafting assumptions.
- On the one real villa, in-scope concrete is within 8% of our own frozen replay, which is a comparison, not ground truth.
- External estimates are positions only (09_BENCHMARK_POSITIONS.csv).

A defensible accuracy figure needs a second real villa with an independently checked quantity takeoff. That is the next step.

## Where to look

- `00_README.md`: the 16 deliverables.
- `17_SUCCESS_CRITERIA.md`: the ten questions of the brief.
- `13_TECHNICAL_DEBT.md` and `14_ENGINEERING_RFIS.csv`: what is still open.
