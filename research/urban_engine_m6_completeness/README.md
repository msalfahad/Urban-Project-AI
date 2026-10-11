# M6 — Concrete completeness and discrepancy-detection engine

The takeoff answers *how much of what I recognised*. This engine answers the other question — *what does the
drawing show that the takeoff does not hold* — without being told what to look for. Every structural signal of a
drawing set (linework, fills, labels, schedule rows, storeys, notes) ends in one terminal state; every signal no
measured item explains becomes a located, typed finding (sheet, storey, box in sheet-local metres, ASCII evidence,
plan magnitude, a volume only from drawn geometry × a printed section or thickness, an action). **A finding never
enters a total.**

| | |
|---|---|
| Engine | `engine/source/concrete_completeness.py` (stdlib + engine helpers, project-agnostic) |
| In the BOQ | `tools/urban_boq_m2.py run --route G` writes `COMPLETENESS_*.csv/json`, `COMPLETENESS_REVIEW.html/pdf`, BOQ section E (`--no-completeness` turns it off) |
| Synthetic truth | `tools/synthetic_villa_m6.py` (V1 cases; V2 cases with `m6v2=True`), `tools/m6_evaluate.py` |
| Tests | `tests/m6_completeness/` |

## How this package was built (in order — each step frozen before the next one read anything new)

| Step | What | Record |
|---|---|---|
| 1 | V1 engine written from the drawing model and synthetic villas; frozen | `00_ENGINE_FREEZE.json` (commit `090a470`) |
| 2 | V1 held-out synthetic evaluation, seeds 101–140, run once | `heldout/HELDOUT_V1_*.json` |
| 3 | **Blind** run on ST7757; outputs hashed before any external record was opened | `blind/`, `01_BLIND_RUN_FREEZE.json` |
| 4 | Reconciliation of the blind run against the freelancer BOQ and both MCP reports (through the M5 crosswalk) | `reconcile.py` |
| 5 | Each miss traced **on the drawing itself** → four generic weaknesses (W1–W4); V2 written; frozen | `02_ENGINE_FREEZE_V2.json` (commit `6c20879`) |
| 6 | V2 held-out synthetic evaluation, seeds 201–240 (never generated before the V2 freeze), run once | `heldout/HELDOUT_V2_*.json`, `heldout/HELDOUT_V2_SUMMARY.json` |
| 7 | ST7757 V2 run — **post-discovery, not blind** (V1 blind files untouched) | `post_discovery_v2/`, `03_V2_RUN_FREEZE.json` |
| 8 | Reconciliation of both runs under two matchers | `reconciliation/` |
| 9 | Weakness register (before / after, open items) | `05_WEAKNESS_REGISTER.csv`, `04_EXECUTIVE_REPORT.md` |

External records were never used to choose a reading or tune a detector: they told us *which* elements were missed;
the reason was always found in the drawing geometry (a route state, a fill, lines inside a footing), and the fix is
a rule about drawings in general (no project mark, coordinate, layer list or quantity in the engine).

## Results

**Synthetic held-out (generalisation evidence).** Detection of every injected element and false findings per set
of 40 drawings. V2 engine on seeds 201–240: 470/470 detected in both vocabularies; the three V2 case kinds 73/73;
false findings 9 and 11 (8 and 10 of them already present in the same seeds without any V2 case — route slab
errors the engine correctly surfaces but the truth file does not model; 1 per set is a new engine weakness, W5).
The V1 engine on the same drawings: 422/470 and 436/470, 15 and 37 false findings. The V1 held-out seeds re-run on
V2 reproduce the V1 record exactly (383/384 with 2 false findings; 384/384 with 1).

**ST7757 (benchmark).** Completeness cases are elements an external source prices (or an Urban stage measures) that
the generic takeoff does not hold in full.

| Run | Matcher M1 (as first written) | Matcher M2 (item / entity level, candidates, RC only) | Findings |
|---|---|---|---|
| V1 blind (`090a470`) | 19 / 32 detected | 19 / 31 detected | 76 (36 HIGH, 40 MEDIUM) |
| V2 post-discovery (`6c20879`) | 20 / 32 detected | 20 identified + 10 unidentified = 30 / 31 | 93 (36 HIGH, 56 MEDIUM, 1 LOW) |

Of the 11 cases V2 adds under M2, one (CB10) is identified by its own labels; of the 10 unidentified ones, 6 link
to the very DXF entity the S9A stage recorded, 3 to the element's own route item and 1 (the lift pit) only to an
unidentified finding of its storey. The one remaining miss (beam B7 on
the ground floor) is not an omission: every B7 span is held; the difference is a measurement convention.
`reconcile.py` gained a match-basis column after the V2 freeze (reporting only: the matching conditions are the
ones frozen with `02_ENGINE_FREEZE_V2.json`, and M2 applies identically to V1 and V2).
**V2 on ST7757 is not blind** — its rules were written after the V1 misses were known. The generalisation
evidence is the held-out synthetic set.

## Reproduce

```
python3 -I research/urban_engine_m6_completeness/v2_run.py --reproduce-v1   # V1 engine from git -> blind/ byte for byte
python3 -I research/urban_engine_m6_completeness/v2_run.py --check          # V2 engine from git -> post_discovery_v2/
python3 -I research/urban_engine_m6_completeness/reconcile.py               # four tallies (V1/V2 x M1/M2)
python3 -I tools/m6_evaluate.py OUT.json 201 ... 240 --mixed --v2-cases     # held-out V2, development vocabulary
python3 -I tools/m6_evaluate.py OUT.json 201 ... 240 --mixed --hard --heldout-vocabulary --v2-cases
```
The ST7757 drawings are private inputs (`data/inputs/by_sha256/`); tests that need them skip without them.

## Limitations (stated plainly)

- Synthetic drawings share the generator author's drafting assumptions (one pattern per meaning, legend rows to the
  right of the building, pits inside the largest footing). They test that rules hold across arrangements, names and
  sizes, not real-drawing accuracy.
- The held-out vocabulary is new to the generator, but most of its words are in the engine's lexicon: it tests
  names the development seeds never drew, not words the engine does not know.
- W1 (unbound marks) has no synthetic case; it is covered by a hand-built fixture and by ST7757 (post-discovery).
- There is still only one real project. A second, independently estimated drawing set is the next real test.
- Family naming is weaker than detection: without a legend on the plan, fills stay UNKNOWN with candidates.
