# M8 brief — full-scope generic structural BOQ (self-written, 2026-10-11)

The owner asked for the engine to be finished towards the final goal: a BOQ engine as strong as a professional
freelance QS, and more accurate than the MCP tools — for any drawing, not for one project. This brief is the
milestone prompt written for that goal, in the M7 format. It is binding on M8.

## 1. Where M7 left the engine (measured, not assumed)

On ST7757, route G with conventions V5:
- measures footings, columns, necks, ground beams, ground slab, beams, slabs, lintels and blinding;
- leaves the following DETECTED_NOT_QUANTIFIED: stairs, pool, domes, water tank, parapets;
- reports lift and walls as NO_EVIDENCE_FOUND.

The completeness engine (M6) already locates most of this scope as findings with shape magnitudes:
- radial dome ribs, radius 2.21 m;
- stair flights with tread counts and going;
- pool wall strips (0.2 m) with a fill;
- a pit-sized closed outline (3.24 m²) inside a footing;
- a 0.2 m boundary strip;
- slab regions held for a detail.

**85 of 90 findings carry no volume, so the exposure is unbounded.** A freelance QS would:
- price every one of these elements, from the drawn plan dimension and a stated professional assumption for the
  dimension the drawing does not print;
- list what is not drawn as an allowance.

That is the gap M8 closes.

## 2. Goal

Every structural family that a QS BOQ for a reinforced-concrete villa carries ends, on any drawing where it is drawn,
in one of two states:

- **(a) measured:** a PROVISIONAL item from the drawn plan geometry. Each dimension the drawing does not print comes
  from a named professional convention with a low / base / high range, and the item records that assumption.
- **(b) bounded:** an UNRESOLVED item or an allowance with an exposure range. This applies when the family itself is
  uncertain (the classification is not settled) or when the element's existence is a scope question.

Nothing stays volume-less. The BOQ reports three figures:
- the measured total;
- the **bounded total range**: measured + every exposure, low and high;
- what is still unpriced, and why.

## 3. Principles (unchanged from M1–M7; stated again because M8 adds conventions)

1. **The engine, not the project.**
   - Every rule speaks about drawings in general: shapes, labels, layers, captions, plan positions.
   - Nothing reads ST7757 identities.
   - Convention values are general professional practice for Gulf RC villas. They are written with their rationale
     **before** any comparison and are never fitted to a reference figure.
2. **No uncertain detection becomes confirmed.**
   - A finding whose family is not settled ("could be DOMES or STAIRS") is quantified only as an exposure range
     under each candidate, never as a measured item.
   - Only a settled family (shape + label / caption / layer agree) becomes PROVISIONAL.
3. **No ratios.**
   - Concrete is measured from geometry × section.
   - Reinforcement for the new families is MISSING_DATA until bar details are read; never a kg/m³ ratio.
4. **Gated.**
   - Every M8 behaviour is a convention in `URBAN_M8_GENERIC_CONVENTIONS_V6.json` (V5 + the M8 rules).
   - V5 runs and the frozen M2–M7 packages reproduce byte for byte.
5. **Freeze before validation.** Engine freeze, then held-out seeds 401–440, generated for the first time and run
   once. ST7757 is post-discovery and reported as such.
6. **Post-freeze positions only.**
   - External figures (freelancer, MCPs) are read from the M5 records only after the M8 freeze, at category level, as
     positions — never as targets.
   - The developer saw M5's bridge figures in earlier milestones; ST7757 is therefore not blind evidence for any M8
     rule, and the brief says so in every report.

## 4. Work packages

| WP | What | Generic rule |
|---|---|---|
| WP1 | Stairs | A stair zone (tread family) or a stair flight finding is measured as flights + landings: flight plan from the drawn treads (count × going × width); landing = zone − flights. Volume = flights × (waist / cos θ + riser / 2) + landings × waist. Riser and waist come from printed values, else the conventions. The M4 storey-rise check stays a diagnostic and no longer blocks the measurement of what is drawn. |
| WP2 | Box structures (pool, pit, tank) | A closed outline / ring / wall strip whose family is settled. Walls = centreline length × drawn thickness (or convention) × height (printed depth / level, or convention). Base / cover slabs = inner area × thickness. A pit inside a measured footing uses the footing as its base. |
| WP3 | Domes | A ring (two circles) or radial ribs on the top roof plan, with a dome label or caption in the set. Spherical-cap shell: area π(r² + h²) × t; rise h = ratio × r (printed or convention), t printed or convention. Ring beams stay beam bands. |
| WP4 | Parapets, boundary walls, sunken / detail regions, unidentified drawn concrete | Bounded exposures only: roof free-edge length × parapet section range; boundary strip length × wall-foundation section range; region area × slab thickness range; unexplained linework × a stated maximum section. Each is a scope question for a person, with its range. |
| WP5 | Missing storey plan | The exposure range is bracketed by the measured slab + beam volume of the neighbouring storeys. |
| WP6 | Totals | BOQ section F "bounded total": measured, exposure low / high, and the number of findings still without a range (target 0 for concrete families). Completeness findings converted to items carry the item ids. A finding never adds to a total twice. |
| WP7 | Validation | The M6 generator gains design-truth volumes for its POOL, LIFT_PIT, WATER_TANK, DOME, STAIR and SUNKEN_SLAB elements: hidden design sections, printed on the drawing in some seeds and not in others. The evaluator scores detection, IN_RANGE (truth inside low–high) and base error per family. The M7 rows (silent, properties) must not move. |
| WP8 | ST7757 + positions | V5 → V6 by family with per-convention ablation. Post-freeze only: comparisons against the project-stage records (S8.x / S9, measured from the same drawings by the project-specific pipeline) and category-level positions of the freelancer and the two MCP runs (M5 records). |
| WP9 | Package | 00–15 deliverables, workbook, visual QA, tests, full suite, commit, push. |

## 5. Acceptance (reported whatever the outcome)

1. **Scope.**
   - Every family drawn on ST7757 and on the held-out villas is measured or bounded.
   - Concrete findings without a volume range: 0.
2. **Held-out (seeds 401–440, V6 frozen)**, per new family:
   - detection share;
   - truth IN_RANGE share;
   - median |base − truth| / truth, split by printed vs convention dimensions.

   Targets: detection ≥ 95 %; IN_RANGE ≥ 80 % where the dimension is a convention; base error ≤ 5 % where it is
   printed.
3. **No regression.**
   - The M7 held-out rows are unchanged under V6 for the M7 families.
   - Metamorphic properties hold for the new families (translate, rotate, mirror, units, duplicate text).
   - Frozen packages are byte-identical.
   - Full suite: 0 code failures.
4. **Honesty.**
   - The quotation verdict stays "not quotation-ready" unless engineer-released quantities and a blind second
     project exist. M8 adds neither.

## 6. What M8 cannot do (stated now, not discovered later)

- **Make the engine "as strong as a freelancer" in fact.** That claim needs a blind second villa and an engineer
  review. M8 removes the structural reasons it could not be, but it cannot supply that evidence.
- **Read architectural sections for parapet height or pool depth.** Route G reads the structural DXF and the
  architectural plans, not sections. Those dimensions stay conventions with ranges unless printed on a structural
  plan or detail.
- **Measure reinforcement for the new families without bar details.** Reinforcement for them stays MISSING_DATA.
