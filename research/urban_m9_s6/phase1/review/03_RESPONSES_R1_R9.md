# Responses to ChatGPT's recommendations R1–R9

Each recommendation is restated as I understand it, so a disagreement can be checked against what was meant.

## Summary

| # | Recommendation (as I understand it) | Verdict |
|---|---|---|
| R1 | canonical geometry: one unit, one representation, before interpretation | **PARTIALLY AGREE** |
| R2 | correctness over frozen mistakes; a corrected, versioned V2 | **AGREE** |
| R3 | a surface-to-BOQ ledger | **AGREE** (and extend it to elements first) |
| R4 | fewer duplicate RFIs, grouped | **AGREE**, with one condition |
| R5 | discovery before measurement | **PARTIALLY AGREE** |
| R6 | preserve CAD evidence | **AGREE** |
| R7 | AI boundaries: geometry stays deterministic | **AGREE** |
| R8 | independent validation on unseen drawings | **AGREE** (the most important of the nine) |
| R9 | no premature expansion | **AGREE**, with a definition |

## R1: canonical geometry. PARTIALLY AGREE

**Agree:**
- **One canonical entity model** fed by one reader: every kind through the K2 kernel, fills included.
- **One internal length unit**, for clarity and for one constant set.
- **Content ids** that do not depend on the drawing unit (S6R-A3: `SITE-<hash>` changes with the unit today).

**Disagree:** that canonical conversion (to mm, quantised or integer) removes the fragility that motivated it. Evidence from Investigation A, fixtures A5 / A6 and `a_method_comparison.py`:
- With canonical mm, a drafted 100 mm piece is still lost after a 30° block rotation in a millimetre drawing.
- At a random angle it is kept 49.6 % of the time, the same as without conversion.
- Quantising to 1 µm or using integer µm geometry keeps it **0 %** of the time at 45°.

The error is in the stored coordinates, from the decimal-to-binary conversion and the insert transform. A unit change keeps it.

**Better alternative:**
- canonical model + **tolerance-aware predicates** (ε = 1e-6 mm, in the unit), as the only way thresholds are tested;
- **metamorphic tests** at non-right angles and site offsets.

Canonical mm is useful but optional; the predicates are not optional.

## R2: correctness over frozen mistakes, versioned V2. AGREE

Evidence that it matters (Investigation A.2): the two openings the "slack" adds on the millimetre reference plan are real:
- a door with a door block, an 890 mm leaf and jamb lines;
- a window with four glazing lines and jamb lines.

Phase 1 rejected that fix *because it changed the millimetre result*. That was my mistake, and it is exactly the error R2 warns against.

**Conditions:**
- Frozen results are never edited. Known defects go in an append-only **errata** register (S6R-A2 for V1 and the route-G lintel evidence).
- The correction is a new method version with a before/after record (Investigation E).

## R3: a surface-to-BOQ ledger. AGREE, and put elements first

Investigation C shows that the Phase 1 gate proves plan-area accountability, not surface or element completeness:
- 8 of 29 door swings on the reference plan have no door line;
- plaster and paint have zero quantities, yet the gate says PASS.

**Better alternative:** the NSD chain, in this order:
1. entity → **element** (NSD-2: door, window and column conservation, the cheapest and the largest silent omission found);
2. element → **eligible surface** (NSD-4 wall-face ledger, NSD-6 an explicit eligibility table);
3. surface → line / RFI / NOT_APPLICABLE, with quantity conservation (NSD-7);
4. an independent total (NSD-8: dimensions, schedules, reference areas).

## R4: reduce duplicate RFIs and group them. AGREE, with one condition

Evidence (Investigation B): the 85 added lines are **4 client / owner questions and 14 engineering defects**; 23 overlap. One window schedule answers 25 lines; one owner rule answers 24.

**Condition:** grouping must not erase per-element traceability.
- The register is keyed by question and lists every affected element with its measured geometry and source entities.
- The BOQ keeps one line per element, each pointing at its question id.
- **Engine defects must leave the client channel entirely**: they are REVIEW findings with a SOFTWARE cause.

Grouping engine defects into "fewer RFIs" would still send a non-question to the client.

## R5: discovery before measurement. PARTIALLY AGREE

Phase 1 implements it: stages 0–5 stop on undeclared units, paper space, missing XREFs, cuts through geometry and failed conversions. 22 silent failure modes become 0.

**But discovery before measurement cannot find what only measurement reveals:**
- a door whose wall gap is not found (CLOSED);
- a face piece dropped by a float threshold;
- a balanced partition of the wrong wall network.

**Better alternative:** *admission before measurement, reconciliation after.*
- A post-measurement discovery pass: element conservation, independent totals, metamorphic self-checks on demand.
- It feeds the same report and the same exit codes.

## R6: preserve CAD evidence. AGREE

Today:
- lines and strips carry source entity ids (handles with the block path, door closures);
- the discovery report counts every entity kind.

Gaps:
1. strip ids hash raw coordinates (S6R-A3);
2. unread evidence is counted but not kept: 388 DIMENSION entities and 51 undecoded SHX texts on the reference plan;
3. RFIs carry no visual crop.

**Better alternative:**
- stable content ids;
- unread entities kept as first-class records (`UNREAD`, with handle and position);
- an SVG crop per RFI group. The private review crop for Investigation A took about 20 lines of code.

## R7: AI boundaries (deterministic geometry). AGREE

Geometry, topology, quantities and gates stay deterministic and reproducible. AI belongs where the source is unstructured:
- reading a PDF window / door schedule;
- decoding unmapped SHX text;
- proposing a room class for an unlabelled space;
- reading levels off a section.

Its output is always a **fact with provenance and confidence**, gated by a reviewer, and never a quantity.

One addition: **AI must never "repair" geometry** (snapping, closing gaps), because that turns a visible defect into an invisible one.

## R8: independent validation on unseen drawings. AGREE, and it is the most important

All real-drawing evidence so far comes from **one** villa. Every heuristic threshold was developed with it in view, and Phase 1's real-plan tests are tests on the development drawing.

**Better alternative (protocol):**
1. two or more villas from **different drafters**, never seen by the engine;
2. hand truth produced independently (element counts, areas per category, a surface list);
3. metrics fixed **before** the run: silent omissions, element-count error, area error per category, RFIs per question;
4. a blind freeze of the engine version before any comparison;
5. no tuning on the blind set. A failure becomes a new defect id and a fixture, then a new blind drawing.

## R9: no premature expansion. AGREE, with a definition

- **Stop:** new BOQ families, new output formats, new owner-facing workbooks, more V1 work.
- **Do not stop:** surfaces inside the declared scope that the engine does not yet model (reveals, wall faces, stairwell walls, doors in CLOSED gaps). These are completeness gaps, not expansion.
- **Test** for "premature": does it add a new kind of quantity before the existing kinds pass NSD and the blind round? If yes, defer it.

## Strongest disagreement

R1, if it is meant as the fix for the metres / millimetres difference. The difference is a float-threshold defect that exists in millimetres too and survives canonical conversion. Only a tolerance-aware predicate removed it in every case tested (Investigation A.4).
