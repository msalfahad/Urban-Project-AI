# 01 Executive report (M8)

## Verdict

**Not quotation-ready.** Nothing in M8 is engineer-released, and there is still no blind second project
(`12_QUOTATION_STATUS.md`).

**The full-project regression gate stays INCOMPLETE.** The data that is still missing is the same as at M1–M7
(`TEST_GATE_M8.json`).

**What M8 achieved.** The structural reason the engine could not compete with a freelance QS is closed. A QS prices
every element on the drawing; when a dimension is not printed, the QS states an assumption. Route G with V6 now does
the same, for any drawing, from rules that know nothing about one project:
- every structural element it finds is measured, or carries a stated range;
- every dimension the drawing does not print is a named convention with a low / base / high.

## The goal, answered honestly

> "As strong as the freelancer, and stronger and more accurate than the MCPs — for the engine, not for one plan."

| Part of the goal | Where M8 stands | Evidence |
|---|---|---|
| The engine, not one plan | **Met by construction and tested** | No rule reads a project identity. All 37 M8 rules are conventions written before any comparison. The held-out villas were generated after the freeze, half of them in a vocabulary never used in development, and 80 of 80 ran with 0 crashes and 0 findings without a range |
| Scope as complete as a QS | **Met on structure; open on depth** | 0 findings without a range: on ST7757 (M7: 85 of 90) and on all 80 held-out villas. Stairs, domes, pool, pit, tank and boundary wall are measured when drawn and settled; parapets, a referenced tank and unsettled elements are allowances with ranges. Reinforcement of the new families is not measured (W8-09) |
| As accurate as the freelance QS | **Not provable yet** | ST7757 total RC is 6.0 % below the freelance QS, and the QS lies inside V6's range. By family, 5 of 14 are within ±10 %. Ground slab, ground beams, necks, columns and the pool still differ by 19–61 % (`08_ST7757_POSITIONS.md`). No released truth exists to say who is right |
| More accurate than the MCPs | **Not provable; the evidence leans that way** | Total RC is within 5.3 % and 4.0 % of the two MCP runs. On beams and slabs V6 is within 2 % of the freelance QS, while the MCPs differ from V6 by 27–39 %. On stairs V6 lies between the freelance QS and the MCPs. V6 measures or bounds 8 families the MCPs do not report. Agreement is not accuracy |

**What would turn "not provable" into an answer:**
- one blind second villa with an independent takeoff, run through a frozen engine;
- an engineer review of ST7757's measured items.

The protocol for both exists (M7 `09_SECOND_VILLA_BLIND_TEST.md`, `tools/urban_project_run.py`).

## Acceptance (brief §5)

| # | Criterion | Result | Met? |
|---|---|---|---|
| 1 | Every drawn family measured or bounded; 0 concrete findings without a range | ST7757: 0 of 89 rows without a range. Held-out S_A / S_B: 0. Coverage V6: domes, pool, walls QUANTIFIED; stairs PARTLY_QUANTIFIED; parapets, water tank BOUNDED_NOT_MEASURED. Lift NO_EVIDENCE_FOUND (the unsettled pit is bounded as a lift candidate) | **yes** |
| 2a | Detection ≥ 95 % per new family (held-out, frozen) | 100 % for all 9 element kinds, both vocabularies | **yes** |
| 2b | Truth in range ≥ 80 % where a dimension is a convention | 17 of 18 kind rows. Miss: pits drawn inside footings, development vocabulary, 75.0 %. The generator draws pits up to 1.70 m deep against a 1.60 m convention high, which was not changed after the freeze | **17 / 18** |
| 2c | Base error ≤ 5 % where the dimension is printed | max 0.73 % (one stair); 0 for every other kind | **yes** |
| 3a | M7 held-out rows unchanged under V6 | 572 rows: 0 moved, 0 SILENT | **yes** |
| 3b | Metamorphic properties hold for the new families | Measured items are invariant under every operation on 10 of 10 villas, except unrelated furniture (9 of 10; that villa changes in V5 too). Bounded totals pass translate, rotations, units, reorder, explode and duplicate text on 10 of 10 after P3. They fail under mirror on 10 of 10 (pre-existing intake: a mirrored hatch, W8-02) and under furniture noise on 7 of 10 (pre-existing completeness: possible columns, W8-03) | **partly** |
| 3c | Frozen packages unchanged | V5 on ST7757 identical before and after M8; core families of 80 villas, V5 against V6: 0 moved; the frozen M2–M7 package tests pass inside the full suite | **yes** |
| 3d | Full suite: 0 code failures | 0 code failures, 7512 passed (+36 = the M8 tests). The first run found 1 code failure: the new module was not declared in the rebar product registry. It was fixed in the test registry and the whole suite was run again (`TEST_GATE_M8.json`) | **yes** |
| 4 | Verdict "not quotation-ready" unless released quantities and a blind project exist | kept | **yes** |

## What the engine does now (V6, any drawing)

1. **Stairs are measured from the drawn run.**
   - Route stair zones that hold part of a stair are measured as flight + landing, instead of an unresolved slab
     zone.
   - Loose flights are decomposed into runs (with a missing tread and a winder found).
   - The riser comes from printed notes or the convention. Both riser-counting rules are kept inside the range.
   - A flight drawn on two plans is measured once.
2. **Box structures are measured when the family is settled.**
   - Pools, lift pits and tanks: walls from the ring, strip or outline; floor, base and cover.
   - A pit inside a measured footing takes no base.
   - The nearest printed depth, height or thickness wins; otherwise the convention applies.
3. **Domes** on the top roof plan are measured from radial ribs or a ring: spherical cap π (r² + h²) × t, plus the
   ring.
4. **Boundary walls** are measured by the schedule row whose width the drawing shows.
5. **Everything else gets a range**, with a stated basis:
   - parapets (from the free roof edge);
   - referenced, undrawn elements (allowances);
   - unsettled shapes ("could be LIFT or WALLS or WATER_TANK": 0 .. the largest candidate);
   - sunken and unknown outlines;
   - members detected but not itemised;
   - missing storey plans (bracketed by the neighbouring storeys);
   - unresolved items with no exposure.
6. **The BOQ prints a bounded total (section F):** measured + every exposure + every bound, low and high. On 80 of 80
   held-out villas the whole RC design truth lay inside it.
7. **Gating.** Every M8 rule is a V6 convention, and each can be removed alone (P4). The ablation on ST7757 shows
   what each one adds (`09_ABLATION.md`).

## ST7757 (post-discovery, not blind)

| | V5 (M7) | V6 (M8) |
|---|---|---|
| RC measured, m³ | 291.758 | 319.800 (+28.042: stairs 9.954, domes 7.372, boundary wall 7.220, pool 3.495) |
| RC bounded total, m³ | – | 313.235 – 476.110 |
| Findings without a range | 85 of 90 | 0 of 89 rows |
| Core families (footings … lintels) | | unchanged |

**The largest open bounds** are RFIs a QS would raise first:
- parapets: RC or block, 0 – 44.4 m³;
- the roof tank: RC or GRP, 0 – 10 m³;
- a footing of unknown depth: 0 – 7.9 m³;
- the unsettled pit: 0 – 6.7 m³;
- the 2F column band: 0 – 5.9 m³.

Details: `07_ST7757_BEFORE_AFTER.md`, `08_ST7757_POSITIONS.md`, `09_ABLATION.md`.

## Post-freeze fixes (kept apart from the frozen record)

| Fix | What it does | Effect |
|---|---|---|
| P1 | stair flights read one layer at a time, never from a non-structural layer | 7 held-out stairs moved closer to the truth, all still in range |
| P2 | a referenced family is "possibly drawn" only by a structural group on the noted plan | no held-out or ST7757 change |
| P3 | the harness compares bounded totals at their 1-litre precision | rotations and units pass 10 / 10 |
| P4 | every scope rule has its own switch | no change with V6 complete |

The frozen record (`heldout/`) is never rewritten. The post-freeze record is `heldout_postfix/`.

## What is still wrong or weak (`11_WEAKNESS_REGISTER.csv`)

| ID | Severity | Weakness |
|---|---|---|
| W8-01 | HIGH | **Pool**: only the strip on the ground-beam plan is read. ST7757 pool is about half of the stage record |
| W8-09 | HIGH | **Reinforcement** of stairs, pool, domes, tank, pit and boundary wall: MISSING_DATA (no bar details read; no ratio used) |
| W8-10 | HIGH | **Core families on ST7757** (pre-existing): ground slab and ground beams well below every external position |
| W8-02 | MEDIUM | **Mirrored hatches** lose their boundary (intake, pre-existing): the bounded low moves under mirror |
| W8-03 | MEDIUM | **Furniture rectangles** reported as possible columns widen the bounded high (pre-existing) |
| W8-05 | MEDIUM | **Convention ranges** do not cover every design (pit depth 1.70 m against a 1.60 m high; boundary wall 0.435 m²/m against 0.36) |
| W8-06 | MEDIUM | **Dome rule**: a radial stair to the roof on the top plan would be read as a dome |
| W8-07, W8-08 | MEDIUM | **Parapets, lift and tank** are ranges, not measurements |
| W8-11 | MEDIUM | **The bounded range is wide** on ST7757 (high = 1.49 × measured) |
| W8-04, W8-12, W8-13 | LOW | detection metric artifact; partial-run riser; coupling to completeness internals |

## What to do next (in order)

1. **A blind second villa** with an independent BOQ, through `tools/urban_project_run.py`, frozen V6. This is the
   only evidence that can answer the goal.
2. **Engineer / QS review of ST7757**, using the release policy (M7):
   - approve or reject the measured scope items;
   - answer the five largest RFIs (parapets, tank, footing depth, pit, 2F columns).
3. **Read detail sheets (sections)** for the pool, the parapets and the stair waist. This is W8-01 / W8-07: the
   largest remaining under-measure and the widest bound.
4. **Reinforcement for the new families** from bar details (W8-09).
5. **Fix the two pre-existing property failures** behind gated conventions:
   - OCS hatch paths to world coordinates (W8-02);
   - layer evidence for column-presence findings (W8-03).
6. **Revisit the core-family gaps** on ST7757 that the M5 bridge listed (W8-10): perimeter tie beam, slab under
   the stairs, levels. Do it on the evidence of a second villa, not by tuning to ST7757.
