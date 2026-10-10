# PROJECT 2 — ROUND 6, STEPS 1–5

**GEOMETRY ONLY. §16 stops here so the geometry effect is visible on its own.**

Steps 6–12 (PHYSICAL_SPACE / FUNCTIONAL_ZONE separation, TradeMeasurementZone,
FLOOR_CERAMIC, WALL_CERAMIC, waste and procurement, `URBAN_BOQ_EXPORT_V1`, the
owner-rule request system) are **not started**. No trade zone, no ceramic, no
waste factor and no BOQ row exists in this commit. That is deliberate: the
addendum forbids hiding a geometry change underneath a BOQ layer.

Round 5 remains permanently frozen. `PROJECT_2_CAD_ROUND5_HASH
8a90def3ac70301a1398aed5` is not rewritten, and
`assert_no_artifact_was_rewritten()` passes on every historical artefact.

---

## 1 · WHAT WAS DONE, IN THE ORDER §16 GAVE

| step | | state |
|---|---|---|
| 1 | freeze-manifest update | done — `ROUND_5_PARTITION_CONTINUITY` entered, `PREDICTED_DIVERGENCES` added |
| 2 | failing synthetic tests first | done — 18 cases A–R written before any engine edit; 15 geometry, 3 trade |
| 3 | space-role UNKNOWN/VOID defect | done — `engine/cad_space_role.py`, `engine/interior_exterior.py` |
| 4 | physical wall pairing | done — `engine/physical_wall.py` rewritten to V2 |
| 5 | rerun the supervised P7757 geometry benchmark | done — `data/runs/7757/P7757_SUPERVISED_GEOMETRY.json` |
| 6–12 | trade, BOQ, owner rules | **NOT STARTED** |

Step 2 was written to FAIL first. The three trade cases (C, K and the
FLOOR_CERAMIC case) still return `NOT_YET_IMPLEMENTED` and can never pass in
this commit — the harness refuses to count them as passes.

---

## 2 · THE TWO DEFECTS, AND WHAT ACTUALLY CAUSED THEM

### 2.1 Defect A — 43 of 57 polygons called VOID_OR_SHAFT

The cause was not a bad threshold. Round 5 had **no space-role classifier at
all**: it reported the round-2 *enclosure role*, whose `VOID_OR_SHAFT` label
means "this closed figure is not a room seed", and read that as an
architectural claim. Nobody having written a name inside a space was being
treated as evidence that the space is a void.

`POSITIVE_EVIDENCE_CAD_SPACE_ROLE_V1` replaces the inference with a demand for
evidence:

```
UNNAMED_PENETRATION_NEEDS = (NO_OPENING_ANYWHERE_ON_ITS_BOUNDARY,
                             THE_SAME_FOOTPRINT_APPEARS_ON_ANOTHER_PLAN)
```

Both must hold. An unnamed bounded space with a door is
`INTERIOR_SPACE_UNCLASSIFIED` — an honest "I do not know yet", which is a
different statement from VOID and is not releasable as one. **No role in this
classifier is decided by how big a space is.** There is no area rule.

On P7757: 40 spaces have no opening anywhere on their boundary, and of those
13 also repeat their footprint on another plan. Those 13 are
`VOID_OR_SHAFT_ON_EVIDENCE`. The other 27 stay unclassified.

### 2.2 Defect B — the kitchen, the W.C slot, and 3,272 wall bands

Round 5's pairing accepted *any* two parallel lines a wall-like distance apart.
One drawn line could therefore act as a face of three or four different
"walls" over the same stretch. Those phantom bands were then handed to the
continuity model, which recovered spans across them, and the recovered spans
sliced rooms: the 1.00 × 3.50 m "W.C" was a slot cut across two separately
labelled spaces by a face that does not exist.

`ONE_LINE_ONE_WALL_PHYSICAL_BAND_V2` adds exactly one structural rule:

> **A line may face two walls over disjoint stretches, and never over the same
> stretch.**

That is explicit geometric evidence, not a tolerance, and it is the only new
rule. Everything else is an *ordering* of evidence already named:

```
AN_OPENING_IS_HOSTED_BETWEEN_THESE_TWO_FACES
A_REVEAL_CLOSES_THE_BAND_AT_BOTH_ENDS
A_REVEAL_CLOSES_THE_BAND_AT_ONE_END
EACH_FACE_IS_THE_OTHER_S_NEAREST_ADMISSIBLE_PARTNER
THE_SEPARATION_IS_A_THICKNESS_THIS_DRAWING_REPEATS
ANOTHER_WALL_MEETS_THIS_BAND
```

Per the addendum: **a repeated thickness never defines a wall.** It ranks a
contested pair and nothing else. It cannot admit a pair the structural test
rejects and cannot reject one the structural test admits. Nothing in this
engine says 50 mm is or is not a wall — 50 mm is in fact the most repeated
separation on P7757 (5 occurrences), and it is ranked, not judged.

The band pairing also feeds back into continuity. A band whose only evidence
is `THE_FACES_RUN_ALONGSIDE_EACH_OTHER` now carries
`has_pairing_evidence = False`, and `partition_continuity` refuses to recover
anything across it:

```
Z_THE_BAND_ITSELF_IS_PAIRED_ON_NOTHING_BUT_PROXIMITY  ->  UNRESOLVED_GAP
```

---

## 3 · THE GEOMETRY RESULT

`data/runs/7757/P7757_SUPERVISED_GEOMETRY.json`, stage
`ROUND_6_STEP_5_GEOMETRY_ONLY`.

| | round 5 (frozen) | round 6 steps 3+4 |
|---|---|---|
| observed wall bands | 3,272 | **389** |
| pairs offered | — | 3,272 |
| pairs refused because the line was taken | — | **2,883** |
| recovered partition spans | 4,159 | **511** |
| recovered partition length | 3,743.0 m | **566.1 m** |
| unresolved gaps | 4,212 | **299** |
| physical-space polygons | 57 | **67** |
| release eligible | 4 | **6** |

The 3,272 figure was never 3,272 walls. It was 3,272 *offers*, of which 2,883
were the same lines being reused. The engine now refuses them by name.

Fewer bands producing MORE spaces (57 → 67) is the expected direction: phantom
bands were previously merging and slicing real spaces at the same time.

**Space roles** (67 spaces): `INTERIOR_SPACE_UNCLASSIFIED` 45,
`VOID_OR_SHAFT_ON_EVIDENCE` 13, `INTERIOR_ROOM` 9. Interior 54, **exterior 0**,
vertical penetrations 13, regions with an established envelope 5 of 9.
Identity established 6, unknown 56, functional-zone groups 5.

---

## 4 · THE THREE SCOREBOARDS, KEPT SEPARATE

### 4.1 HISTORICAL / FROZEN

Read-only. Never recomputed as though it were this run. Rounds 1–5 all carry
their four objects; `assert_no_artifact_was_rewritten()` passes.

One replay divergence exists and it is **predicted**:
`ROUND_2_ENCLOSURE_ROLE` diverges on `ROUND_2_SYNTHETIC_HASH` and
`SEMANTIC_SEED_CLASSIFIER_HASH`, because round 3 rewrote the semantic seed
classifier. `UNPREDICTED_DIVERGENCE` is empty. A replay is a different object
from a freeze; a divergence is information, not a failure.

### 4.2 SUPERVISED P7757 (`P7757_SUPERVISED_DEVELOPMENT_BENCHMARK_V1`, hash `3047a37c2c8a7c5a45cfe44f`)

Each example scores a **structural assertion**. The disclosed figures are
reported beside the engine's own and are never a target.

| example | board | status |
|---|---|---|
| P7757-KITCHEN | GEOMETRY | **HELD** |
| P7757-WC-WASH | GEOMETRY | **HELD** |
| P7757-GARDEN-STRIP | SPACE_ROLE | **HELD** |
| P7757-VOID-OVERUSE | SPACE_ROLE | **HELD** |
| P7757-OPEN-RECEPTION | TRADE_ZONE | AWAITING_A_LATER_STEP |

### 4.3 SYNTHETIC

round 2 12/12 · round 3 16/16 · round 4 22/22 · round 5 23/23 ·
round 6 geometry 15/15, 3 trade cases awaiting the trade layer.
`ROUND_6_SYNTHETIC_HASH ac4752e4fc44ce02932586a3`. pytest: 2,081 passed, of
which 39 are `tests/test_round6_geometry.py` — including three that assert the
trade cases still CANNOT pass.

---

## 5 · WHAT IS STILL WRONG, STATED PLAINLY

### 5.1 The kitchen is 5.553 m², not 9.675 m²

Round 5 produced 3.85 m². Round 6 produces **5.553 m²**, bounds 2,200 × 2,550
mm. The disclosed manual measurement is 3.00 × 2.70 + 1.05 × 1.50 = 9.675 m²
and the human workbook is ≈9.55 m².

The structural assertion HELD — there is exactly one space carrying the KITCHEN
concept and it is not bounded by a band paired on nothing. The number did not
converge, and **it was not supposed to**: §13 says the goal is not "get closer
to 9.675". The 2,200 × 2,550 polygon is the kitchen's enclosed floor between
its own wall faces. The 1.05 × 1.50 entrance recess is outside it because the
recess opens into the adjoining space — whether it belongs to the kitchen's
ceramic is a TRADE MEASUREMENT ZONE question, which is step 7. The remaining
difference against 3.00 × 2.70 is a face-selection question in the same region
and is not yet explained; it is logged, not patched.

No P7757 coordinate box, no expected room-size range and no "if KITCHEN"
branch exists anywhere in the engine.

### 5.2 P7757 yields ZERO exterior spaces

`ENVELOPE_EVIDENCE_INTERIOR_EXTERIOR_V1` establishes an envelope in 5 of 9
drawing regions and a **site boundary in none of them**. Exterior ground is
defined as `site.difference(envelope)`; with no site there is no difference to
take, so the engine enumerates 0 exterior faces and all 67 spaces read
INTERIOR.

The disclosed 5.616 m² garden strip therefore **cannot yet be separated from
the fabric on this drawing**. The GARDEN-STRIP assertion HELD only in its
negative half — nothing exterior was released as an interior room — and the
positive half is untested on P7757. Synthetic case F carries a real site ring
and does exercise it.

This is reported rather than forced. Inventing a site boundary where the
drafter drew none would be exactly the failure round 5 was frozen to expose.

### 5.3 Other open items

- 47 of 67 spaces are still closed with a recovered span, and only 20 carry
  material authority. Areas, not blockwork.
- Identity is unknown for 56 of 67 spaces.
- 6 dimension checks disagree, 14 agree, 111 are not applicable. No dimension
  has been used as a correction factor.
- `tools/export_round5_benchmark.py` now correctly **refuses to run** under
  round-6 code: its hash gate recomputes `8a90def3ac70301a1398aed5` and the
  engine has changed. That is the gate working. The round-5 export already on
  disk is the frozen one.

---

## 6 · BENCHMARK-INFORMED CHANGES, DISCLOSED

From round 6 onward P7757 is a development project and every
benchmark-informed change must be declared. These are all of them:

| change | what the benchmark told me | what I did NOT do |
|---|---|---|
| `physical_wall` V2 one-line-one-wall | the W.C slot proved a phantom face was slicing rooms | no P7757 coordinates, no room-size range, no thickness hardcode |
| `partition_continuity` `has_pairing_evidence` gate | the kitchen was bounded by a band paired on nothing | no per-project exception list |
| `cad_space_role` positive evidence | 43/57 VOID was disclosed as too aggressive | no area rule, no name-required rule |
| `interior_exterior` site/envelope | the 5.616 m² polygon was disclosed as external | no "large polygon = outside" rule |
| `portal_match` may-close-boundary gate | found by synthetic case D, not by P7757 | — |

Not opened, at any point: the Excel, the كيال, architect take-off totals,
manual measurements beyond the four figures the owner disclosed in writing,
structural quantities, sanitary quantities. The sealed 23010 site benchmark was
not read; `no_sealed_reference_was_opened: true`.

---

## 7 · FROZEN THIS ROUND

```
PHYSICAL_WALL_BAND_HASH        b6d79d2b5c5e2c13eb5d546d   ONE_LINE_ONE_WALL_PHYSICAL_BAND_V2
CAD_SPACE_ROLE_HASH            cf6191908829d6a7d3b022d1   POSITIVE_EVIDENCE_CAD_SPACE_ROLE_V1
INTERIOR_EXTERIOR_HASH         752d9d9cb8e5fb51f9145e2d   ENVELOPE_EVIDENCE_INTERIOR_EXTERIOR_V1
SUPERVISED_BENCHMARK_HASH      3047a37c2c8a7c5a45cfe44f   P7757_SUPERVISED_DEVELOPMENT_BENCHMARK_V1
ROUND_6_SYNTHETIC_HASH         ac4752e4fc44ce02932586a3
FREEZE_MANIFEST_SCHEMA_HASH    71df459e2520865be23091a4
```
