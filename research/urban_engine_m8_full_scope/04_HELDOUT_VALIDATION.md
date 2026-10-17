# 04 Held-out validation (synthetic seeds 401–440)

## Protocol

- **Freeze first.** The engine was frozen at `9d7aceb` (`00_ENGINE_FREEZE.json`, freeze commit `a772be1`).
- **Run once.** `heldout_run.py run` then generated seeds 401–440 for the first time and ran them once. That record
  is `heldout/`, with its own sha256 list in `HELDOUT_SUMMARY.json`.
- **Post-freeze fixes kept apart.** Fixes P1–P4 came after the held-out run. Their re-run is a separate record
  (`heldout_postfix/`), and the frozen record is never rewritten.

**The drawings.**
- Generator: `tools/synthetic_villa_m8.py` — the M6 cluttered villa plus the design of every scope element.
- Drafting distractors on (`hard`), plus the V2 cases.
- Two vocabularies: development (S_A) and held-out layer names and note words (S_B).
- In about half of the elements the generator prints the design dimensions beside the element.

**What the scores mean.** Synthetic drawings share the generator author's drafting assumptions. The design ranges
were written to be a little wider than the V6 conventions. So these scores test two things only:
- the rules read geometry and printed notes correctly;
- the convention ranges cover the author's design spread.

They are not real-drawing accuracy.

## Results per element kind

Source: `06A_ACCEPTANCE_FROZEN.csv` (frozen) and `06_ACCEPTANCE.csv` (post-freeze). Every element is in
`05_HELDOUT_BY_ELEMENT.csv`.

**Targets** (brief §5):
- detection ≥ 95 %;
- truth inside the range ≥ 80 % where a dimension is a convention;
- printed base error ≤ 5 %.

| Kind | Elements (A / B) | Detected | Measured / bounded (A) | In range, convention dims (A / B) | Printed error, max | Convention error, median (A / B) | Targets |
|---|---|---|---|---|---|---|---|
| Stair flight | 21 / 21 | 100 % | 21 / 0 | 100 / 100 % | 0.7 % | 0 / 0 (inside the landing-or-void truth range) | met |
| Lift pit | 35 / 35 | 100 % | 34 / 1 | 92.3 / 92.3 % | 0 | 7.4 / 7.4 % | met |
| Pit in a footing | 21 / 21 | 100 % | 17 / 4 | **75.0** / 83.3 % | 0 | 22.6 / 22.6 % | **missed (A)** |
| Pool | 31 / 31 | 100 % | 23 / 8 | 86.7 / 80.0 % | 0 | 9.7 / 14.4 % | met |
| Water tank | 21 / 21 | 100 % | 18 / 3 | 100 / 100 % | 0 | 13.5 / 11.5 % | met |
| Dome | 21 / 21 | 100 % | 19 / 2 | 93.3 / 100 % | 0 | 13.5 / 7.2 % | met |
| Boundary wall | 25 / 25 | 100 % | 0 / 25 (bounded) | 87.5 / 84.0 % | – | – | met |
| Sunken outline | 32 / 32 | 100 % | 0 / 32 (bounded) | 100 / 100 % | – | – | met |
| Unknown outline | 30 / 30 | 100 % | 0 / 30 (bounded) | 100 / 100 % | – | – | met |

**The one miss — pits drawn inside footings, development vocabulary: 75 % in range.**
- The generator draws pit depths up to 1.70 m. `PIT_DEPTH_M` high is 1.60 m.
- The convention was not changed after the freeze.

**One element measured as another family.** A pool in the held-out vocabulary (S_B, seed 419) was measured, but
as another family. Its range still contained the truth. It is the only one of 474 held-out elements
(`05_HELDOUT_BY_ELEMENT.csv`, outcome MEASURED_OTHER_FAMILY).

**How tight the ranges are.** The median ratio of engine high to truth is:
- 1.0–1.4 for measured families;
- 2.5–3.4 for sunken outlines;
- 5.5 for unknown outlines.

A bound from 0 is easy to satisfy. Unidentified elements are bounded, not estimated.

**Boundary walls.** None was measured on the held-out set: no drawn width matched a `B.W` schedule row. Every one
was bounded, at 84–88 % in range: designs reach 0.435 m²/m against a 0.36 high.

## Whole villa: RC truth against the bounded total

For each villa, the whole RC truth was compared with the bounded total (BOQ section F). The truth here is:
- the core design: footings, columns, beams, slabs;
- plus every scope element;
- with a stair bay's slab-or-void ambiguity carried as a truth range.

| Run | Villas with the truth inside [bounded low, bounded high] | Median measured / truth low | Median bounded low / truth low | Median bounded high / truth high |
|---|---|---|---|---|
| S_A | 40 / 40 | 0.904 | 0.890 | 1.277 |
| S_B | 40 / 40 | 0.902 | 0.900 | 1.254 |

**Findings without a range:** 0 in both runs.

## The M7 rows on the M7 held-out seeds (301–340) under V6

| Run | Rows | Moved against the stored M7 V5 rows | SILENT |
|---|---|---|---|
| M7Q_A (development vocabulary) | 286 | 0 | 0 |
| M7Q_B (held-out vocabulary) | 286 | 0 | 0 |

## The M6 detection metric under V6 (M7 held-out seeds)

| Run | Injected elements | Detected (V5 → V6) | Family right (V5 → V6) |
|---|---|---|---|
| M7C_A | 479 | 479 → 476 | 350 → 347 |
| M7C_B | 479 | 479 → 477 | 335 → 332 |

**Why the counts fell.**
- All six changes are stair elements, which V6 now measures as stairs (route stair zones).
- The M6 metric counts findings only, so a measured stair no longer counts as "detected". The S_A / S_B runs show
  every stair measured.
- One of the six (seed 330, held-out vocabulary) now matches a neighbouring finding of another family.

This is a metric artifact; the fix is listed in `11_WEAKNESS_REGISTER.csv` (W8-04).

## Post-freeze fixes and their effect

The fixes and the reason for each are in `postfix_run.py` and in `10_PROPERTIES_AND_REGRESSION.md`.

**Element changes.** Seven held-out stair elements changed: three in S_A and four in S_B.
- Before the fix (P1), lines of another layer joined the flight.
- The base moved closer to the flight truth (seed 411: +34 % → +7 %).
- All seven stay in range with the same outcome.
- No other element changed.
